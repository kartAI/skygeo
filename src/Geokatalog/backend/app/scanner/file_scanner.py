"""File scanner for detecting and extracting metadata from geospatial files"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

import rasterio
import geopandas as gpd
import pyarrow.parquet as pq
import fiona
from pmtiles.reader import Reader as PMTilesReader
from pmtiles.reader import MmapSource
import laspy
from shapely.geometry import box, mapping
import json

logger = logging.getLogger(__name__)

# PDAL is optional - only needed for advanced COPC features
try:
    import pdal
    HAS_PDAL = True
except ImportError:
    HAS_PDAL = False
    logger.warning("PDAL not installed. COPC support will use laspy only.")


class FileScanner:
    """Scanner for geospatial files"""
    
    SUPPORTED_EXTENSIONS = {
        'cog': ['.tif', '.tiff'],
        'geoparquet': ['.parquet', '.geoparquet'],
        'flatgeobuf': ['.fgb'],
        'pmtiles': ['.pmtiles'],
        'copc': ['.copc.laz', '.laz']
    }
    
    def __init__(self, data_directory: Path, base_url: str = "http://localhost:8000"):
        self.data_directory = Path(data_directory)
        self.base_url = base_url
        if not self.data_directory.exists():
            logger.warning(f"Data directory {self.data_directory} does not exist")
    
    def _get_file_url(self, file_path: Path) -> str:
        """Convert file path to accessible HTTP URL"""
        # Get relative path from data directory
        try:
            relative_path = file_path.relative_to(self.data_directory)
            # Convert to URL-friendly path with forward slashes
            url_path = str(relative_path).replace('\\', '/')
            return f"{self.base_url}/data/{url_path}"
        except ValueError:
            # If file is not relative to data directory, return file path as string
            return str(file_path)
    
    def _format_crs_info(self, crs) -> Dict:
        """Format CRS information in a more readable way"""
        try:
            epsg_code = None
            crs_name = None
            
            # Handle different CRS formats
            if isinstance(crs, dict):
                # PROJ JSON format (from GeoParquet)
                # Try to extract EPSG code from id
                if 'id' in crs:
                    crs_id = crs['id']
                    if isinstance(crs_id, dict):
                        authority = crs_id.get('authority', '').upper()
                        code = crs_id.get('code')
                        
                        # Handle OGC:CRS84 → EPSG:4326 mapping
                        if authority == 'OGC' and code == 'CRS84':
                            epsg_code = 4326
                        elif authority == 'EPSG' and code:
                            try:
                                epsg_code = int(code) if isinstance(code, (int, str)) and str(code).isdigit() else None
                            except:
                                pass
                
                # Extract name from PROJ JSON
                if 'name' in crs:
                    crs_name = crs['name']
                    # Clean up name (remove CRS84 suffix if EPSG is known)
                    if epsg_code and '(CRS84)' in crs_name:
                        crs_name = crs_name.replace(' (CRS84)', '').strip()
            else:
                # String format (from rasterio)
                crs_str = str(crs)
                
                # Try to extract EPSG code from string
                if 'EPSG:' in crs_str.upper():
                    try:
                        epsg_code = int(crs_str.upper().split('EPSG:')[1].split()[0])
                    except:
                        pass
                elif ':' in crs_str:
                    # Format like "EPSG:4326"
                    try:
                        parts = crs_str.split(':')
                        if parts[0].upper() in ['EPSG', 'OGC']:
                            epsg_code = int(parts[1])
                    except:
                        pass
                
                crs_name = crs_str
            
            # Create a cleaner CRS representation
            crs_info = {
                'type': 'name',
                'properties': {}
            }
            
            # Common CRS descriptions
            common_names = {
                4326: 'WGS 84',
                3857: 'Web Mercator',
                32633: 'WGS 84 / UTM zone 33N',
                32636: 'WGS 84 / UTM zone 36N',
                25833: 'ETRS89 / UTM zone 33N',
            }
            
            if epsg_code:
                crs_info['properties']['name'] = f'EPSG:{epsg_code}'
                if epsg_code in common_names:
                    crs_info['properties']['description'] = common_names[epsg_code]
                elif crs_name and crs_name != str(crs):
                    # Use the name from PROJ JSON if available
                    crs_info['properties']['description'] = crs_name
            else:
                # No EPSG code found, use name or string representation
                if crs_name:
                    crs_info['properties']['name'] = crs_name
                else:
                    crs_info['properties']['name'] = str(crs)[:100]  # Limit length
            
            return crs_info
        except Exception as e:
            logger.warning(f"Could not format CRS info: {e}")
            return {'type': 'name', 'properties': {'name': str(crs)[:100]}}
    
    def _get_data_outline(self, src, bbox: List[float]) -> Dict:
        """Get convex hull outline of actual data for better visualization"""
        try:
            from shapely.ops import unary_union
            from shapely.geometry import shape
            
            # Sample features to create outline (limit to avoid performance issues)
            sample_size = min(1000, len(src))
            step = max(1, len(src) // sample_size)
            
            geometries = []
            for i, feature in enumerate(src):
                if i % step == 0:
                    try:
                        geom = shape(feature['geometry'])
                        if geom.is_valid:
                            geometries.append(geom)
                    except:
                        continue
                
                if len(geometries) >= sample_size:
                    break
            
            if geometries:
                # Create convex hull of all sampled geometries
                combined = unary_union(geometries)
                convex_hull = combined.convex_hull
                
                # Simplify to reduce complexity
                simplified = convex_hull.simplify(tolerance=0.01, preserve_topology=True)
                
                return mapping(simplified)
            else:
                # Fallback to bounding box
                return mapping(box(*bbox))
                
        except Exception as e:
            logger.warning(f"Could not create convex hull, using bbox: {e}")
            return mapping(box(*bbox))
    
    def scan_directory(self) -> Dict[str, List[Path]]:
        """Scan directory for supported geospatial files"""
        files_by_type = {fmt: [] for fmt in self.SUPPORTED_EXTENSIONS.keys()}
        
        if not self.data_directory.exists():
            return files_by_type
        
        for root, _, files in os.walk(self.data_directory):
            for file in files:
                file_path = Path(root) / file
                file_type = self._get_file_type(file_path)
                if file_type:
                    files_by_type[file_type].append(file_path)
        
        return files_by_type
    
    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """Determine file type from extension"""
        file_str = str(file_path).lower()
        
        # Check for COPC first (more specific)
        if file_str.endswith('.copc.laz'):
            return 'copc'
        
        for file_type, extensions in self.SUPPORTED_EXTENSIONS.items():
            for ext in extensions:
                if file_str.endswith(ext):
                    return file_type
        
        return None
    
    def extract_cog_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from Cloud Optimized GeoTIFF"""
        try:
            with rasterio.open(file_path) as src:
                bounds = src.bounds
                
                # Transform bounds to WGS84 if not already
                from rasterio.warp import transform_bounds
                if src.crs and src.crs != 'EPSG:4326':
                    # Transform to WGS84 for STAC compliance
                    try:
                        wgs84_bounds = transform_bounds(src.crs, 'EPSG:4326', *bounds)
                        bbox = [wgs84_bounds[0], wgs84_bounds[1], wgs84_bounds[2], wgs84_bounds[3]]
                    except Exception as e:
                        logger.warning(f"Could not transform bounds to WGS84 for {file_path}: {e}")
                        bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                else:
                    bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                
                # Create geometry from WGS84 bounds
                geometry = mapping(box(*bbox))
                
                # Format CRS info
                crs_info = self._format_crs_info(src.crs) if src.crs else None
                
                metadata = {
                    'bbox': bbox,
                    'geometry': geometry,
                    'properties': {
                        'datetime': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() + 'Z',
                        'width': src.width,
                        'height': src.height,
                        'crs': crs_info,
                        'bands': src.count,
                        'dtype': str(src.dtypes[0]),
                        'nodata': src.nodata,
                    },
                    'assets': {
                        'data': {
                            'href': self._get_file_url(file_path),
                            'type': 'image/tiff; application=geotiff; profile=cloud-optimized',
                            'roles': ['data', 'visual'],
                            'title': file_path.name,
                            'file:size': os.path.getsize(file_path)
                        }
                    }
                }
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting COG metadata from {file_path}: {e}")
            return None
    
    def extract_geoparquet_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from GeoParquet file"""
        try:
            # Read with geopandas to get geometry info
            gdf = gpd.read_parquet(file_path)
            
            if gdf.empty:
                return None
            
            bounds = gdf.total_bounds
            bbox = [float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])]
            
            # Create convex hull for better visual representation
            try:
                # Sample geometries for convex hull (to avoid performance issues)
                sample_size = min(1000, len(gdf))
                if len(gdf) > sample_size:
                    sampled = gdf.sample(n=sample_size)
                else:
                    sampled = gdf
                
                from shapely.ops import unary_union
                combined = unary_union(sampled.geometry)
                convex_hull = combined.convex_hull
                simplified = convex_hull.simplify(tolerance=0.01, preserve_topology=True)
                geometry = mapping(simplified)
            except Exception as e:
                logger.warning(f"Could not create convex hull for {file_path}, using bbox: {e}")
                geometry = mapping(box(*bbox))
            
            # Get CRS from GeoParquet - try to parse PROJ JSON from metadata
            crs_info = None
            if gdf.crs:
                # gdf.crs is a pyproj.CRS object
                try:
                    # Try to get PROJ JSON dict from pyproj CRS
                    crs_dict = gdf.crs.to_json_dict() if hasattr(gdf.crs, 'to_json_dict') else None
                    if crs_dict:
                        crs_info = self._format_crs_info(crs_dict)
                    else:
                        # Fallback to string representation
                        crs_info = self._format_crs_info(gdf.crs)
                except Exception as e:
                    logger.warning(f"Could not parse CRS for {file_path}, using string: {e}")
                    crs_info = self._format_crs_info(str(gdf.crs))
            
            # Get column info with types (exclude geometry column)
            columns_info = []
            geom_col_name = gdf.geometry.name
            for col in gdf.columns:
                if col != geom_col_name:
                    columns_info.append({
                        'name': col,
                        'type': str(gdf[col].dtype)
                    })
            
            # Get geometry type
            geom_type = 'Unknown'
            if not gdf.empty:
                try:
                    geom_type = gdf.geometry.geom_type.mode()[0]
                except:
                    geom_type = str(gdf.geometry.iloc[0].geom_type) if len(gdf) > 0 else 'Unknown'
            
            metadata = {
                'bbox': bbox,
                'geometry': geometry,
                'properties': {
                    'datetime': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() + 'Z',
                    'feature_count': len(gdf),
                    'crs': crs_info,
                    'columns': columns_info,
                    'geometry_type': geom_type
                },
                'assets': {
                    'data': {
                        'href': self._get_file_url(file_path),
                        'type': 'application/x-parquet',
                        'roles': ['data', 'visual'],
                        'title': file_path.name,
                        'file:size': os.path.getsize(file_path)
                    }
                }
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting GeoParquet metadata from {file_path}: {e}")
            return None
    
    def extract_flatgeobuf_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from FlatGeobuf file"""
        try:
            with fiona.open(file_path) as src:
                bounds = src.bounds
                bbox = [bounds[0], bounds[1], bounds[2], bounds[3]]
                
                # Create convex hull for better visual representation of data extent
                geometry = self._get_data_outline(src, bbox)
                
                # Format CRS information better
                crs_info = self._format_crs_info(src.crs) if src.crs else None
                
                metadata = {
                    'bbox': bbox,
                    'geometry': geometry,
                    'properties': {
                        'datetime': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() + 'Z',
                        'feature_count': len(src),
                        'crs': crs_info,
                        'schema': dict(src.schema),
                    },
                    'assets': {
                        'data': {
                            'href': self._get_file_url(file_path),
                            'type': 'application/flatgeobuf',
                            'roles': ['data', 'visual'],
                            'title': file_path.name,
                            'file:size': os.path.getsize(file_path)
                        }
                    }
                }
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting FlatGeobuf metadata from {file_path}: {e}")
            return None
    
    def extract_pmtiles_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from PMTiles file"""
        try:
            # Read PMTiles using a simpler approach without mmap
            import struct
            
            with open(file_path, 'rb') as f:
                # Read PMTiles header (first 127 bytes)
                header_bytes = f.read(127)
                if len(header_bytes) < 127:
                    logger.warning(f"PMTiles file too small: {file_path}")
                    return None
                
                # Parse header manually (simplified - just get bounds and zoom)
                # PMTiles v3 header format
                version = struct.unpack('<H', header_bytes[0:2])[0]
                if version != 3:
                    logger.warning(f"Unsupported PMTiles version {version}: {file_path}")
                    return None
                
                # Extract bounds (E7 format - degrees * 10^7)
                min_lon_e7 = struct.unpack('<i', header_bytes[84:88])[0]
                min_lat_e7 = struct.unpack('<i', header_bytes[88:92])[0]
                max_lon_e7 = struct.unpack('<i', header_bytes[92:96])[0]
                max_lat_e7 = struct.unpack('<i', header_bytes[96:100])[0]
                
                # Convert E7 to decimal degrees
                min_lon = min_lon_e7 / 10000000.0
                min_lat = min_lat_e7 / 10000000.0
                max_lon = max_lon_e7 / 10000000.0
                max_lat = max_lat_e7 / 10000000.0
                
                # Extract zoom levels
                min_zoom = header_bytes[18]
                max_zoom = header_bytes[19]
                center_zoom = header_bytes[20]
                
                # Extract tile type
                tile_type_byte = header_bytes[21]
                type_map = {0: 'unknown', 1: 'mvt', 2: 'png', 3: 'jpeg', 4: 'webp'}
                tile_type = type_map.get(tile_type_byte, 'unknown')
                
                # Extract compression type
                tile_compression_byte = header_bytes[23]
            
            # Create bbox and geometry
            bbox = [float(min_lon), float(min_lat), float(max_lon), float(max_lat)]
            geometry = mapping(box(*bbox))
            
            metadata = {
                'bbox': bbox,
                'geometry': geometry,
                'properties': {
                    'datetime': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() + 'Z',
                    'tile_type': tile_type,
                    'min_zoom': int(min_zoom),
                    'max_zoom': int(max_zoom),
                    'center_zoom': int(center_zoom),
                    'tile_compression': int(tile_compression_byte),  # 0=unknown, 1=none, 2=gzip
                },
                'assets': {
                    'data': {
                        'href': self._get_file_url(file_path),
                        'type': 'application/vnd.pmtiles',
                        'roles': ['data', 'visual', 'tiles'],
                        'title': file_path.name,
                        'file:size': os.path.getsize(file_path)
                    }
                }
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting PMTiles metadata from {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def extract_copc_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from COPC (Cloud Optimized Point Cloud) file"""
        try:
            las = laspy.read(file_path)
            
            # Get bounds
            min_x, min_y, min_z = las.header.mins
            max_x, max_y, max_z = las.header.maxs
            
            bbox = [min_x, min_y, max_x, max_y]
            geometry = mapping(box(min_x, min_y, max_x, max_y))
            
            metadata = {
                'bbox': bbox,
                'geometry': geometry,
                'properties': {
                    'datetime': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat() + 'Z',
                    'point_count': las.header.point_count,
                    'point_format': las.header.point_format.id,
                    'version': f"{las.header.version.major}.{las.header.version.minor}",
                    'min_z': min_z,
                    'max_z': max_z,
                },
                    'assets': {
                        'data': {
                            'href': self._get_file_url(file_path),
                            'type': 'application/vnd.laszip+copc',
                            'roles': ['data', 'visual'],
                            'title': file_path.name,
                            'file:size': os.path.getsize(file_path)
                        }
                    }
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting COPC metadata from {file_path}: {e}")
            return None
    
    def extract_metadata(self, file_path: Path) -> Optional[Dict]:
        """Extract metadata from a file based on its type"""
        file_type = self._get_file_type(file_path)
        
        if file_type == 'cog':
            return self.extract_cog_metadata(file_path)
        elif file_type == 'geoparquet':
            return self.extract_geoparquet_metadata(file_path)
        elif file_type == 'flatgeobuf':
            return self.extract_flatgeobuf_metadata(file_path)
        elif file_type == 'pmtiles':
            return self.extract_pmtiles_metadata(file_path)
        elif file_type == 'copc':
            return self.extract_copc_metadata(file_path)
        
        return None

