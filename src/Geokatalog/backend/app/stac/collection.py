"""STAC Collection management"""
from typing import List, Dict, Optional
from pathlib import Path
import pystac
from pystac import Collection, Extent, SpatialExtent, TemporalExtent
from datetime import datetime


class STACCollectionManager:
    """Manager for STAC Collections"""
    
    COLLECTION_METADATA = {
        'cog': {
            'title': 'Cloud Optimized GeoTIFF (COG)',
            'description': 'Collection of Cloud Optimized GeoTIFF raster files',
            'keywords': ['raster', 'cog', 'geotiff', 'imagery']
        },
        'geoparquet': {
            'title': 'GeoParquet',
            'description': 'Collection of GeoParquet vector files',
            'keywords': ['vector', 'parquet', 'geoparquet', 'features']
        },
        'flatgeobuf': {
            'title': 'FlatGeobuf',
            'description': 'Collection of FlatGeobuf vector files',
            'keywords': ['vector', 'flatgeobuf', 'fgb', 'features']
        },
        'pmtiles': {
            'title': 'PMTiles',
            'description': 'Collection of PMTiles vector tiles',
            'keywords': ['tiles', 'pmtiles', 'vector tiles', 'mvt']
        },
        'copc': {
            'title': 'Cloud Optimized Point Cloud (COPC)',
            'description': 'Collection of COPC point cloud files',
            'keywords': ['point cloud', 'copc', 'lidar', '3d']
        }
    }
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.collections: Dict[str, Collection] = {}
    
    def create_collection(self, collection_id: str, items: List[pystac.Item]) -> Collection:
        """Create a STAC Collection for a specific format"""
        
        metadata = self.COLLECTION_METADATA.get(collection_id, {
            'title': collection_id.upper(),
            'description': f'Collection of {collection_id} files',
            'keywords': [collection_id]
        })
        
        # Calculate spatial and temporal extents from items
        spatial_extent, temporal_extent = self._calculate_extents(items)
        
        extent = Extent(
            spatial=spatial_extent,
            temporal=temporal_extent
        )
        
        collection = Collection(
            id=collection_id,
            title=metadata['title'],
            description=metadata['description'],
            keywords=metadata['keywords'],
            extent=extent,
            license='proprietary'
        )
        
        # Add links
        collection.add_link(pystac.Link(
            rel='self',
            target=f"{self.base_url}/collections/{collection_id}"
        ))
        collection.add_link(pystac.Link(
            rel='items',
            target=f"{self.base_url}/collections/{collection_id}/items"
        ))
        collection.add_link(pystac.Link(
            rel='root',
            target=f"{self.base_url}/"
        ))
        
        self.collections[collection_id] = collection
        return collection
    
    def _calculate_extents(self, items: List[pystac.Item]) -> tuple:
        """Calculate spatial and temporal extents from items"""
        if not items:
            # Default extents if no items
            spatial_extent = SpatialExtent(bboxes=[[-180, -90, 180, 90]])
            temporal_extent = TemporalExtent(intervals=[[None, None]])
            return spatial_extent, temporal_extent
        
        # Calculate bounding box
        min_x = min(item.bbox[0] for item in items if item.bbox)
        min_y = min(item.bbox[1] for item in items if item.bbox)
        max_x = max(item.bbox[2] for item in items if item.bbox)
        max_y = max(item.bbox[3] for item in items if item.bbox)
        
        spatial_extent = SpatialExtent(bboxes=[[min_x, min_y, max_x, max_y]])
        
        # Calculate temporal extent
        datetimes = [item.datetime for item in items if item.datetime]
        if datetimes:
            min_datetime = min(datetimes)
            max_datetime = max(datetimes)
            temporal_extent = TemporalExtent(intervals=[[min_datetime, max_datetime]])
        else:
            temporal_extent = TemporalExtent(intervals=[[None, None]])
        
        return spatial_extent, temporal_extent
    
    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get a collection by ID"""
        return self.collections.get(collection_id)
    
    def get_all_collections(self) -> List[Collection]:
        """Get all collections"""
        return list(self.collections.values())

