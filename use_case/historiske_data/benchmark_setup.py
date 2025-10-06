# pip install fastapi uvicorn aiofiles python-multipart
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
import time
import requests
from PIL import Image
import io
import json

app = FastAPI(title="COG vs WMS Benchmark")

# Mount static files for serving COGs
app.mount("/cogs", StaticFiles(directory="cogs"), name="cogs")

# Benchmark configuration
WMS_URL = "https://wms.geonorge.no/skwms1/wms.historiskekart?"
TEST_AREAS = [
    {
        "name": "oslo_small",
        "bbox": (1061715, 8373188, 1191695, 8476199),
        "size": (1024, 1024)
    },
    {
        "name": "oslo_medium", 
        "bbox": (1061715, 8373188, 1191695, 8476199),
        "size": (2048, 2048)
    },
    {
        "name": "oslo_large",
        "bbox": (1000000, 8300000, 1250000, 8550000),
        "size": (4096, 4096)
    }
]

@app.get("/")
async def root():
    return {
        "message": "COG vs WMS Benchmark Server",
        "endpoints": {
            "wms_test": "/wms/{area_name}",
            "cog_test": "/cog/{area_name}",
            "benchmark": "/benchmark/{area_name}",
            "comparison": "/compare/{area_name}",
            "demo_tiles": "/demo_tiles",
            "demo_tile": "/demo_tile/{tile_id}",
            "tiling_benchmark": "/tiling_benchmark"
        }
    }

@app.get("/wms/{area_name}")
async def test_wms(area_name: str):
    """Test WMS performance for a specific area"""
    area = next((a for a in TEST_AREAS if a["name"] == area_name), None)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    start_time = time.time()
    
    # Make WMS request
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": "historiskekart",
        "styles": "",
        "crs": "EPSG:3857",
        "bbox": ",".join(map(str, area["bbox"])),
        "width": area["size"][0],
        "height": area["size"][1],
        "format": "image/png",
        "transparent": "true"
    }
    
    response = requests.get(WMS_URL, params=params)
    load_time = time.time() - start_time
    
    return {
        "area": area_name,
        "source": "WMS",
        "load_time": round(load_time, 3),
        "file_size": len(response.content),
        "dimensions": area["size"],
        "bbox": area["bbox"]
    }

@app.get("/cog/{area_name}")
async def test_cog(area_name: str):
    """Test COG performance for a specific area"""
    area = next((a for a in TEST_AREAS if a["name"] == area_name), None)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    cog_path = f"cogs/{area_name}.cog.tif"
    if not os.path.exists(cog_path):
        raise HTTPException(status_code=404, detail="COG file not found")
    
    start_time = time.time()
    
    # Get file info
    file_size = os.path.getsize(cog_path)
    load_time = time.time() - start_time
    
    return {
        "area": area_name,
        "source": "COG",
        "load_time": round(load_time, 3),
        "file_size": file_size,
        "dimensions": area["size"],
        "bbox": area["bbox"],
        "file_path": cog_path
    }

@app.get("/demo_tiles")
async def list_demo_tiles():
    """List all available demonstration tiles"""
    tile_index_path = "cogs/demo_tiles/tile_index.json"
    if not os.path.exists(tile_index_path):
        raise HTTPException(status_code=404, detail="Demo tiles not found. Run prepare_benchmark_data.py first.")
    
    with open(tile_index_path, "r") as f:
        tile_index = json.load(f)
    
    return {
        "tile_count": len(tile_index["tiles"]),
        "total_extent": tile_index["total_extent"],
        "tile_size": tile_index["tile_size"],
        "tiling_strategy": tile_index["tiling_strategy"],
        "use_case": tile_index["use_case"],
        "tiles": tile_index["tiles"][:10],  # Show first 10 tiles
        "message": f"Showing first 10 of {len(tile_index['tiles'])} tiles. Use /demo_tile/{{tile_id}} to access specific tiles."
    }

@app.get("/demo_tile/{tile_id}")
async def get_demo_tile(tile_id: str):
    """Get a specific demonstration tile by ID (e.g., '00_00', '01_02')"""
    tile_path = f"cogs/demo_tiles/demo_tile_{tile_id}.cog.tif"
    if not os.path.exists(tile_path):
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found")
    
    start_time = time.time()
    file_size = os.path.getsize(tile_path)
    load_time = time.time() - start_time
    
    return {
        "tile_id": tile_id,
        "source": "COG_Tile",
        "load_time": round(load_time, 3),
        "file_size": file_size,
        "file_path": tile_path,
        "message": "This demonstrates how individual tiles can be served efficiently"
    }

@app.get("/tiling_benchmark")
async def benchmark_tiling_approach():
    """Demonstrate the benefits of tiled COGs vs WMS for larger areas"""
    
    # Simulate requesting a larger area (e.g., 4 tiles covering a region)
    # This shows how tiled COGs can be more efficient than single large WMS requests
    
    # Get tile index
    tile_index_path = "cogs/demo_tiles/tile_index.json"
    if not os.path.exists(tile_index_path):
        raise HTTPException(status_code=404, detail="Demo tiles not found. Run prepare_benchmark_data.py first.")
    
    with open(tile_index_path, "r") as f:
        tile_index = json.load(f)
    
    # Simulate requesting first 4 tiles (2x2 grid)
    sample_tiles = tile_index["tiles"][:4]
    
    # Calculate total area covered by these tiles
    min_x = min(tile["bbox"][0] for tile in sample_tiles)
    min_y = min(tile["bbox"][1] for tile in sample_tiles)
    max_x = max(tile["bbox"][2] for tile in sample_tiles)
    max_y = max(tile["bbox"][3] for tile in sample_tiles)
    
    combined_bbox = (min_x, min_y, max_x, max_y)
    combined_size = (4096, 4096)  # 2x2 tiles of 2048x2048
    
    # Simulate WMS request for this combined area
    wms_start = time.time()
    wms_params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": "historiskekart",
        "styles": "",
        "crs": "EPSG:3857",
        "bbox": ",".join(map(str, combined_bbox)),
        "width": combined_size[0],
        "height": combined_size[1],
        "format": "image/png",
        "transparent": "true"
    }
    
    try:
        wms_response = requests.get(WMS_URL, params=wms_params)
        wms_load_time = time.time() - wms_start
        wms_size = len(wms_response.content)
    except Exception as e:
        wms_load_time = 999  # Error case
        wms_size = 0
    
    # Calculate COG tile performance
    cog_start = time.time()
    cog_total_size = 0
    for tile in sample_tiles:
        tile_path = f"cogs/demo_tiles/{tile['filename']}"
        if os.path.exists(tile_path):
            cog_total_size += os.path.getsize(tile_path)
    
    cog_load_time = time.time() - cog_start
    
    # Calculate improvements
    if wms_load_time < 999:  # Only if WMS succeeded
        time_improvement = ((wms_load_time - cog_load_time) / wms_load_time) * 100
        size_improvement = ((wms_size - cog_total_size) / wms_size) * 100
    else:
        time_improvement = 100  # WMS failed, COG wins
        size_improvement = 100
    
    return {
        "scenario": "Larger Area Coverage (4 tiles)",
        "area_covered": combined_bbox,
        "wms_approach": {
            "description": "Single large WMS request",
            "load_time": round(wms_load_time, 3),
            "file_size": wms_size,
            "success": wms_load_time < 999
        },
        "cog_approach": {
            "description": "Multiple tiled COG requests",
            "load_time": round(cog_load_time, 3),
            "total_file_size": cog_total_size,
            "tiles_used": len(sample_tiles),
            "tile_details": sample_tiles
        },
        "benefits": {
            "time_saved_percent": round(time_improvement, 1),
            "size_reduction_percent": round(size_improvement, 1),
            "scalability": "Tiled approach scales better for larger areas",
            "reliability": "Individual tiles can be cached and served independently"
        }
    }

@app.get("/benchmark/{area_name}")
async def run_benchmark(area_name: str):
    """Run full benchmark comparison for an area"""
    area = next((a for a in TEST_AREAS if a["name"] == area_name), None)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    # Test WMS
    wms_start = time.time()
    wms_response = requests.get(f"http://localhost:8000/wms/{area_name}")
    wms_result = wms_response.json()
    wms_total_time = time.time() - wms_start
    
    # Test COG
    cog_start = time.time()
    cog_response = requests.get(f"http://localhost:8000/cog/{area_name}")
    cog_result = cog_response.json()
    cog_total_time = time.time() - cog_start
    
    # Calculate improvements
    time_improvement = ((wms_result["load_time"] - cog_result["load_time"]) / wms_result["load_time"]) * 100
    size_improvement = ((wms_result["file_size"] - cog_result["file_size"]) / wms_result["file_size"]) * 100
    
    return {
        "area": area_name,
        "wms": wms_result,
        "cog": cog_result,
        "improvements": {
            "time_saved_percent": round(time_improvement, 1),
            "size_reduction_percent": round(size_improvement, 1),
            "wms_vs_cog_ratio": round(wms_result["load_time"] / cog_result["load_time"], 2)
        }
    }

@app.get("/compare/{area_name}")
async def compare_formats(area_name: str):
    """Return comparison data for frontend visualization"""
    benchmark = await run_benchmark(area_name)
    
    return {
        "labels": ["WMS", "COG"],
        "load_times": [benchmark["wms"]["load_time"], benchmark["cog"]["load_time"]],
        "file_sizes": [benchmark["wms"]["file_size"], benchmark["cog"]["file_size"]],
        "improvements": benchmark["improvements"]
    }

if __name__ == "__main__":
    print("Starting COG vs WMS Benchmark Server...")
    print("Available test areas:", [a["name"] for a in TEST_AREAS])
    print("Server will run on http://localhost:8000")
    print("\nNew endpoints for tiled COG demonstration:")
    print("- /demo_tiles - List available demonstration tiles")
    print("- /demo_tile/{tile_id} - Access specific tile")
    print("- /tiling_benchmark - Compare tiled approach vs WMS")
    print("\nThis demonstrates how to efficiently serve large areas using multiple COG files!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 