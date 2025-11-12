"""STAC Item generation for different geospatial formats"""
from pathlib import Path
from typing import Dict, Optional
import pystac
from datetime import datetime


class STACItemGenerator:
    """Generator for STAC Items from geospatial files"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_item(self, file_path: Path, metadata: Dict, collection_id: str) -> Optional[pystac.Item]:
        """Create a STAC Item from file metadata"""
        if not metadata:
            return None
        
        try:
            # Create item ID from file path
            item_id = self._create_item_id(file_path)
            
            # Extract required fields from metadata
            bbox = metadata.get('bbox')
            geometry = metadata.get('geometry')
            properties = metadata.get('properties', {})
            assets_data = metadata.get('assets', {})
            
            # Create the STAC Item
            item = pystac.Item(
                id=item_id,
                geometry=geometry,
                bbox=bbox,
                datetime=self._parse_datetime(properties.get('datetime')),
                properties=properties,
                collection=collection_id
            )
            
            # Add assets with enhanced metadata for QGIS
            for asset_key, asset_data in assets_data.items():
                asset_href = asset_data.get('href')
                media_type = asset_data.get('type')
                
                # Create asset
                asset = pystac.Asset(
                    href=asset_href,
                    media_type=media_type,
                    roles=asset_data.get('roles', []),
                    title=asset_data.get('title'),
                    extra_fields={
                        # Add alternate representations for QGIS
                        "alternate": {
                            "vsicurl": f"/vsicurl/{asset_href}",  # GDAL virtual file system
                        }
                    }
                )
                
                item.add_asset(asset_key, asset)
            
            # Add projection extension if CRS is available
            if properties.get('crs'):
                item.stac_extensions.append(
                    "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
                )
                item.properties['proj:epsg'] = self._extract_epsg(properties['crs'])
            
            # Set self link
            item.add_link(pystac.Link(
                rel='self',
                target=f"{self.base_url}/collections/{collection_id}/items/{item_id}"
            ))
            
            # Add alternate link for direct download (helps QGIS)
            for asset_key, asset_data in assets_data.items():
                item.add_link(pystac.Link(
                    rel='alternate',
                    target=asset_data.get('href'),
                    media_type=asset_data.get('type'),
                    title=f"Direct download - {asset_data.get('title')}"
                ))
            
            return item
            
        except Exception as e:
            print(f"Error creating STAC item for {file_path}: {e}")
            return None
    
    def _create_item_id(self, file_path: Path) -> str:
        """Create a unique item ID from file path"""
        # Remove extension and use stem as ID
        return file_path.stem.replace(' ', '_').replace('.', '_')
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not datetime_str:
            return datetime.utcnow()
        
        try:
            # Remove 'Z' suffix if present
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1]
            return datetime.fromisoformat(datetime_str)
        except:
            return datetime.utcnow()
    
    def _extract_epsg(self, crs_str: str) -> Optional[int]:
        """Extract EPSG code from CRS string"""
        try:
            # Handle various CRS string formats
            if 'EPSG:' in crs_str.upper():
                return int(crs_str.upper().split('EPSG:')[1].split()[0])
            elif 'epsg:' in crs_str.lower():
                return int(crs_str.lower().split('epsg:')[1].split()[0])
        except:
            pass
        return None

