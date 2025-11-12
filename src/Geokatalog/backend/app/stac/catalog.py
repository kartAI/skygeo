"""STAC Catalog generation and management"""
from typing import Dict, List, Optional
from pathlib import Path
import pystac
from pystac import Catalog

from app.scanner.file_scanner import FileScanner
from app.stac.item import STACItemGenerator
from app.stac.collection import STACCollectionManager


class STACCatalogGenerator:
    """Generator and manager for STAC Catalog"""
    
    def __init__(self, data_directory: Path, base_url: str = "http://localhost:8000", 
                 title: str = "STAC Catalog", description: str = "Dynamic STAC Catalog"):
        self.data_directory = data_directory
        self.base_url = base_url
        self.title = title
        self.description = description
        
        self.scanner = FileScanner(data_directory, base_url)
        self.item_generator = STACItemGenerator(base_url)
        self.collection_manager = STACCollectionManager(base_url)
        
        self.catalog: Optional[Catalog] = None
        self.items_by_collection: Dict[str, List[pystac.Item]] = {}
    
    def build_catalog(self) -> Catalog:
        """Build the complete STAC catalog by scanning files"""
        # Create root catalog
        self.catalog = Catalog(
            id='root',
            title=self.title,
            description=self.description
        )
        
        self.catalog.add_link(pystac.Link(
            rel='self',
            target=f"{self.base_url}/"
        ))
        
        # Scan files
        files_by_type = self.scanner.scan_directory()
        
        # Process each file type as a collection
        for collection_id, file_paths in files_by_type.items():
            if not file_paths:
                continue
            
            # Create items for this collection
            items = []
            for file_path in file_paths:
                metadata = self.scanner.extract_metadata(file_path)
                if metadata:
                    item = self.item_generator.create_item(file_path, metadata, collection_id)
                    if item:
                        items.append(item)
            
            if items:
                # Store items
                self.items_by_collection[collection_id] = items
                
                # Create collection
                collection = self.collection_manager.create_collection(collection_id, items)
                
                # Add collection to catalog
                self.catalog.add_child(collection)
                
                # Add items to collection
                for item in items:
                    collection.add_item(item)
        
        return self.catalog
    
    def get_catalog(self) -> Optional[Catalog]:
        """Get the current catalog"""
        return self.catalog
    
    def get_collection(self, collection_id: str) -> Optional[pystac.Collection]:
        """Get a specific collection"""
        return self.collection_manager.get_collection(collection_id)
    
    def get_collections(self) -> List[pystac.Collection]:
        """Get all collections"""
        return self.collection_manager.get_all_collections()
    
    def get_items(self, collection_id: str, limit: int = 100, offset: int = 0) -> List[pystac.Item]:
        """Get items from a collection with pagination"""
        items = self.items_by_collection.get(collection_id, [])
        return items[offset:offset + limit]
    
    def get_item(self, collection_id: str, item_id: str) -> Optional[pystac.Item]:
        """Get a specific item"""
        items = self.items_by_collection.get(collection_id, [])
        for item in items:
            if item.id == item_id:
                return item
        return None
    
    def search_items(self, bbox: Optional[List[float]] = None, 
                    datetime_range: Optional[str] = None,
                    collections: Optional[List[str]] = None,
                    limit: int = 100) -> List[pystac.Item]:
        """Search items with filters"""
        results = []
        
        # Determine which collections to search
        if collections:
            search_collections = collections
        else:
            search_collections = list(self.items_by_collection.keys())
        
        for collection_id in search_collections:
            items = self.items_by_collection.get(collection_id, [])
            
            for item in items:
                # Apply bbox filter
                if bbox and item.bbox:
                    if not self._bbox_intersects(item.bbox, bbox):
                        continue
                
                # Apply datetime filter (simplified)
                # TODO: Implement proper datetime range filtering
                
                results.append(item)
                
                if len(results) >= limit:
                    return results
        
        return results
    
    def _bbox_intersects(self, bbox1: List[float], bbox2: List[float]) -> bool:
        """Check if two bounding boxes intersect"""
        return not (bbox1[2] < bbox2[0] or  # bbox1 is left of bbox2
                   bbox1[0] > bbox2[2] or  # bbox1 is right of bbox2
                   bbox1[3] < bbox2[1] or  # bbox1 is below bbox2
                   bbox1[1] > bbox2[3])    # bbox1 is above bbox2
    
    def refresh_catalog(self):
        """Refresh the catalog by re-scanning files"""
        self.items_by_collection.clear()
        self.collection_manager.collections.clear()
        return self.build_catalog()

