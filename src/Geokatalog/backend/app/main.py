"""FastAPI application with STAC API endpoints"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from pathlib import Path
import logging
import mimetypes
import os
import re
from datetime import datetime

from app.models.config import settings
from app.stac.catalog import STACCatalogGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="STAC API",
    description="SpatioTemporal Asset Catalog API for geospatial data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize catalog generator
# Use localhost for base_url so external clients (like QGIS) can access the data
# The API binds to 0.0.0.0 for Docker, but external URL should be localhost
catalog_generator = STACCatalogGenerator(
    data_directory=settings.data_directory,
    base_url="http://localhost:8000",  # External-facing URL
    title=settings.catalog_title,
    description=settings.catalog_description
)

# Track refresh status
refresh_status = {
    "is_running": False,
    "last_refresh": None,
    "last_duration": None,
    "collections_count": None,
    "error": None
}

# Build initial catalog
logger.info(f"Scanning data directory: {settings.data_directory}")
catalog_generator.build_catalog()
logger.info("Initial catalog build complete")
refresh_status["last_refresh"] = datetime.now().isoformat()

# Register custom MIME types for geospatial formats
mimetypes.add_type('application/flatgeobuf', '.fgb')
mimetypes.add_type('application/geoparquet', '.parquet')
mimetypes.add_type('application/geoparquet', '.geoparquet')
mimetypes.add_type('application/vnd.pmtiles', '.pmtiles')
mimetypes.add_type('application/vnd.laszip+copc', '.laz')
mimetypes.add_type('application/vnd.laszip+copc', '.copc.laz')
mimetypes.add_type('image/tiff; application=geotiff', '.tif')
mimetypes.add_type('image/tiff; application=geotiff', '.tiff')

# Custom file serving endpoint with range request support for COG
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import os
import re

async def serve_file_with_range(request: Request, file_path: str):
    """Serve files with HTTP range request support for COG streaming"""
    full_path = settings.data_directory / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is within data directory (security)
    try:
        full_path.resolve().relative_to(settings.data_directory.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_size = full_path.stat().st_size
    range_header = request.headers.get("range")
    
    # Determine content type
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "application/octet-stream"
    
    # Handle range request
    if range_header:
        # Parse range header (e.g., "bytes=0-1023")
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            content_length = end - start + 1
            
            def iterfile():
                with open(full_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(content_length),
                'Content-Type': content_type,
            }
            
            return StreamingResponse(
                iterfile(),
                status_code=206,
                headers=headers,
                media_type=content_type
            )
    
    # Full file response (no range request)
    def iterfile():
        with open(full_path, 'rb') as f:
            while chunk := f.read(8192):
                yield chunk
    
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(file_size),
        'Content-Type': content_type,
    }
    
    return StreamingResponse(
        iterfile(),
        headers=headers,
        media_type=content_type
    )

# Register file serving endpoint
@app.get("/data/{file_path:path}")
async def get_data_file(request: Request, file_path: str):
    """Serve data files with range request support"""
    return await serve_file_with_range(request, file_path)

logger.info(f"Registered /data endpoint with range request support for COG streaming")


@app.get("/")
async def get_root_catalog():
    """Get the root STAC catalog - STAC API compliant"""
    catalog = catalog_generator.get_catalog()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    # Convert to dict
    catalog_dict = catalog.to_dict()
    
    # Filter links - keep only self and root, exclude pystac-generated child links
    filtered_links = [
        link for link in catalog_dict.get("links", [])
        if link.get("rel") not in ["child", "item"]
    ]
    
    # Add conformance classes for QGIS compatibility
    response = {
        "stac_version": "1.0.0",
        "type": "Catalog",
        "id": catalog_dict.get("id"),
        "title": catalog_dict.get("title"),
        "description": catalog_dict.get("description"),
        "conformsTo": [
            "https://api.stacspec.org/v1.0.0/core",
            "https://api.stacspec.org/v1.0.0/collections",
            "https://api.stacspec.org/v1.0.0/item-search",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
        ],
        "links": filtered_links
    }
    
    # Add service info link
    response["links"].append({
        "rel": "service-desc",
        "href": f"{catalog_generator.base_url}/api",
        "type": "application/vnd.oai.openapi+json;version=3.0",
        "title": "OpenAPI service description"
    })
    
    # Add data link for direct file access
    response["links"].append({
        "rel": "data",
        "href": f"{catalog_generator.base_url}/data/",
        "type": "text/html",
        "title": "Direct file access"
    })
    
    # Add our custom collection links (STAC API format)
    collections = catalog_generator.get_collections()
    for collection in collections:
        response["links"].append({
            "rel": "child",
            "href": f"{catalog_generator.base_url}/collections/{collection.id}",
            "type": "application/json",
            "title": collection.title
        })
    
    return JSONResponse(content=response)


@app.get("/collections")
async def get_collections():
    """Get all STAC collections"""
    collections = catalog_generator.get_collections()
    
    collections_list = []
    for collection in collections:
        col_dict = collection.to_dict()
        collections_list.append(col_dict)
    
    return JSONResponse(content={
        "collections": collections_list,
        "links": [
            {
                "rel": "root",
                "href": "/",
                "type": "application/json"
            },
            {
                "rel": "self",
                "href": "/collections",
                "type": "application/json"
            }
        ]
    })


@app.get("/collections/{collection_id}")
async def get_collection(collection_id: str):
    """Get a specific STAC collection"""
    collection = catalog_generator.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found")
    
    collection_dict = collection.to_dict()
    
    # Ensure links use correct URLs (not pystac defaults)
    # Filter and update links to use STAC API format
    filtered_links = []
    for link in collection_dict.get("links", []):
        rel = link.get("rel")
        if rel == "self":
            link["href"] = f"{catalog_generator.base_url}/collections/{collection_id}"
        elif rel == "items":
            link["href"] = f"{catalog_generator.base_url}/collections/{collection_id}/items"
        elif rel == "root":
            link["href"] = f"{catalog_generator.base_url}/"
        elif rel == "parent":
            link["href"] = f"{catalog_generator.base_url}/"
        # Skip pystac-generated child/item links
        if rel not in ["child", "item"]:
            filtered_links.append(link)
    
    collection_dict["links"] = filtered_links
    return JSONResponse(content=collection_dict)


@app.get("/collections/{collection_id}/items")
async def get_collection_items(
    collection_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """Get items from a collection with pagination"""
    collection = catalog_generator.get_collection(collection_id)
    
    if not collection:
        raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found")
    
    items = catalog_generator.get_items(collection_id, limit=limit, offset=offset)
    
    items_list = []
    for item in items:
        item_dict = item.to_dict()
        items_list.append(item_dict)
    
    return JSONResponse(content={
        "type": "FeatureCollection",
        "features": items_list,
        "links": [
            {
                "rel": "root",
                "href": "/",
                "type": "application/json"
            },
            {
                "rel": "self",
                "href": f"/collections/{collection_id}/items",
                "type": "application/json"
            },
            {
                "rel": "collection",
                "href": f"/collections/{collection_id}",
                "type": "application/json"
            }
        ]
    })


@app.get("/collections/{collection_id}/items/{item_id}")
async def get_item(collection_id: str, item_id: str):
    """Get a specific item from a collection - Enhanced for QGIS"""
    item = catalog_generator.get_item(collection_id, item_id)
    
    if not item:
        raise HTTPException(
            status_code=404, 
            detail=f"Item {item_id} not found in collection {collection_id}"
        )
    
    item_dict = item.to_dict()
    
    # Enhance links for QGIS
    if "links" not in item_dict:
        item_dict["links"] = []
    
    # Add collection link for context
    item_dict["links"].append({
        "rel": "collection",
        "href": f"{catalog_generator.base_url}/collections/{collection_id}",
        "type": "application/json",
        "title": f"{collection_id} collection"
    })
    
    return JSONResponse(content=item_dict)


@app.get("/search")
async def search_items(
    bbox: Optional[str] = Query(None, description="Bounding box: minx,miny,maxx,maxy"),
    datetime: Optional[str] = Query(None, description="Datetime range"),
    collections: Optional[str] = Query(None, description="Comma-separated collection IDs"),
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Search for items across collections"""
    
    # Parse bbox
    bbox_list = None
    if bbox:
        try:
            bbox_list = [float(x) for x in bbox.split(',')]
            if len(bbox_list) != 4:
                raise ValueError("Bbox must have 4 values")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid bbox format: {e}")
    
    # Parse collections
    collections_list = None
    if collections:
        collections_list = [c.strip() for c in collections.split(',')]
    
    # Search items
    items = catalog_generator.search_items(
        bbox=bbox_list,
        datetime_range=datetime,
        collections=collections_list,
        limit=limit
    )
    
    items_list = []
    for item in items:
        item_dict = item.to_dict()
        items_list.append(item_dict)
    
    return JSONResponse(content={
        "type": "FeatureCollection",
        "features": items_list,
        "links": [
            {
                "rel": "root",
                "href": "/",
                "type": "application/json"
            },
            {
                "rel": "self",
                "href": "/search",
                "type": "application/json"
            }
        ],
        "context": {
            "returned": len(items_list),
            "limit": limit
        }
    })


def refresh_catalog_background():
    """Background task to refresh the catalog"""
    global refresh_status
    try:
        refresh_status["is_running"] = True
        refresh_status["error"] = None
        start_time = datetime.now()
        
        logger.info("Starting background catalog refresh...")
        catalog_generator.refresh_catalog()
        
        # Get updated collection count
        collections = catalog_generator.get_collections()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        refresh_status["last_refresh"] = end_time.isoformat()
        refresh_status["last_duration"] = duration
        refresh_status["collections_count"] = len(collections)
        logger.info(f"Catalog refresh complete. Took {duration:.2f} seconds. Found {len(collections)} collections.")
    except Exception as e:
        logger.error(f"Error during catalog refresh: {e}")
        refresh_status["error"] = str(e)
    finally:
        refresh_status["is_running"] = False

@app.post("/refresh")
async def refresh_catalog(background_tasks: BackgroundTasks):
    """Refresh the STAC catalog by re-scanning the data directory (async)"""
    if refresh_status["is_running"]:
        return JSONResponse(content={
            "status": "running",
            "message": "Catalog refresh already in progress",
            "is_running": True
        })
    
    # Start refresh in background
    background_tasks.add_task(refresh_catalog_background)
    
    return JSONResponse(content={
        "status": "started",
        "message": "Catalog refresh started in background. Use GET /refresh/status to check progress.",
        "is_running": True
    })

@app.get("/refresh/status")
async def get_refresh_status():
    """Get the status of the catalog refresh process"""
    return JSONResponse(content={
        "is_running": refresh_status["is_running"],
        "last_refresh": refresh_status["last_refresh"],
        "last_duration_seconds": refresh_status["last_duration"],
        "collections_count": refresh_status.get("collections_count"),
        "error": refresh_status["error"]
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "data_directory": str(settings.data_directory),
        "catalog_title": settings.catalog_title
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)

