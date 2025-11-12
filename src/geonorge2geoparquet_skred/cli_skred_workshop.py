from datetime import datetime
import os
import requests
import json
import gzip
import time
import logging
import argparse
import sys

# Configuration - baseurl og output-dir
GEONORGE_BASE_URL = "https://nedlasting.geonorge.no/api"
OUTPUT_DIR = "temp_debug/workshop"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Download CLI Skred dataset from Geonorge')
    parser.add_argument('--dataset-uuid', 
                       required=True,
                       help='UUID of the dataset to download (required)')
    parser.add_argument('--output-dir', 
                       default=OUTPUT_DIR,
                       help=f'Output directory (default: {OUTPUT_DIR})')
    return parser.parse_args()

def setup_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

def get_dataset_info(dataset_uuid):
    """Fetch dataset metadata from Geonorge API"""
    logger.info("Fetching dataset information...")
    
    info_url = f"https://kartkatalog.geonorge.no/api/getdata/{dataset_uuid}"
    
    try:
        response = requests.get(info_url, timeout=30)
        response.raise_for_status()
        dataset_info = response.json()
        
        logger.info(f"Dataset: {dataset_info.get('title', 'Unknown')}")
        logger.info(f"Description: {dataset_info.get('description', 'No description')}")
        logger.info(f"Format: {dataset_info.get('distributionFormat', 'Unknown')}")
        
        return {
            "uuid": dataset_uuid,
            "title": dataset_info.get('title'),
            "format": dataset_info.get('distributionFormat'),
            "projection": dataset_info.get('projection'),
            "size_mb": dataset_info.get('sizeInMb', 0)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch dataset info: {e}")
        raise

def request_download(dataset_uuid):
    """Request download URL from Geonorge API"""
    logger.info("Requesting download from Geonorge API...")
    
    order_url = f"{GEONORGE_BASE_URL}/order"
    
    # Request body following the format you provided
    order_payload = {
        "downloadAsBundle": False,
        "email": "hans.gunnar.steen@norkart.no",
        "orderLines": [
            {
                "areas": [
                    {
                        "code": "0000",
                        "name": "Landsdekkende",
                        "type": "landsdekkende"
                    }
                ],
                "formats": [
                    {
                        "name": "GML"
                    }
                ],
                "metadataUuid": dataset_uuid,
                "projections": [
                    {
                        "code": "25833",
                        "name": "UTM Sone 33 - Euref89",
                        "codespace": "http://www.opengis.net/def/crs/EPSG/0/25833"
                    }
                ]
            }
        ]
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.info(f"📞 ORDER URL: {order_url}")
        logger.info(f"Order payload: {json.dumps(order_payload, indent=2)}")
        
        response = requests.post(order_url, json=order_payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        order_response = response.json()
        
        # Extract order ID
        order_id = order_response.get('referenceNumber')
        
        logger.info(f"🎯 ORDER RESPONSE: {json.dumps(order_response, indent=2)}")
        
        if not order_id:
            logger.error(f"No order ID received from API")
            raise ValueError("No order ID received from Geonorge API")
        
        # Parse downloadUrl from files array
        files = order_response.get('files', [])
        if not files:
            logger.error(f"No files array in response")
            raise ValueError("No files found in order response")
        
        # Get the first file's download URL
        download_url = files[0].get('downloadUrl')
        if not download_url:
            logger.error(f"No downloadUrl in first file: {files[0]}")
            raise ValueError("No download URL found in files array")
        
        logger.info(f"✅ ORDER ID: {order_id}")
        logger.info(f"📥 DOWNLOAD URL: {download_url}")
        logger.info(f"📁 FILES COUNT: {len(files)}")
        
        return {
            "order_id": order_id,
            "download_url": download_url,
            "status": "ready",
            "request_time": datetime.now().isoformat(),
            "response": order_response,
            "files_count": len(files)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to request download: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        raise

def download_and_store(download_info, dataset_uuid, output_dir):
    """Download file and store locally"""
    logger.info("Downloading and storing file...")
    
    download_url = download_info['download_url']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Download file
        logger.info(f"🚀 Starting download from: {download_url}")
        response = requests.get(download_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Read content
        content = response.content
        logger.info(f"Downloaded {len(content)} bytes")
        
        # Determine file extension based on content type or format
        content_type = response.headers.get('content-type', '')
        if 'xml' in content_type.lower() or 'gml' in content_type.lower():
            file_ext = 'gml'
        elif 'zip' in content_type.lower():
            file_ext = 'zip'
        else:
            file_ext = 'data'  # fallback
        
        # Store original file
        original_filename = f"cli_skred_{timestamp}.{file_ext}"
        original_path = os.path.join(output_dir, original_filename)
        
        with open(original_path, 'wb') as f:
            f.write(content)
        
        # Store metadata
        metadata = {
            "source": "geonorge",
            "dataset_uuid": dataset_uuid,
            "download_time": datetime.now().isoformat(),
            "order_id": download_info['order_id'],
            "download_url": download_info['download_url'],
            "file_size_bytes": len(content),
            "content_type": content_type,
            "original_filename": original_filename,
            "format": "GML",
            "projection": "EPSG:25833",
            "files_count": download_info.get('files_count', 1)
        }
        
        metadata_filename = f"cli_skred_{timestamp}_metadata.json.gz"
        metadata_path = os.path.join(output_dir, metadata_filename)
        
        with gzip.open(metadata_path, 'wt') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Files stored:")
        logger.info(f"  Data: {original_path}")
        logger.info(f"  Metadata: {metadata_path}")
        
        return {
            "data_path": original_path,
            "metadata_path": metadata_path,
            "file_size_bytes": len(content),
            "status": "success"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise

def convert_to_geoparquet(storage_info, dataset_uuid, output_dir):
    """Convert GML file to optimized GeoParquet format"""
    logger.info("Converting GML to GeoParquet...")
    
    # Import libraries inside function following guidelines
    import geopandas as gpd
    import zipfile
    import fiona
    import pandas as pd
    
    data_path = storage_info['data_path']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # Handle different file types
        if data_path.endswith('.zip'):
            # Extract ZIP file to output directory
            logger.info("Extracting ZIP file...")
            extract_dir = os.path.join(output_dir, f"extracted_{timestamp}")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(data_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                logger.info(f"Extracted ZIP to: {extract_dir}")
            
            # Find GML files in extracted directory
            gml_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith(('.gml', '.xml')):
                        gml_files.append(os.path.join(root, file))
            
            if not gml_files:
                raise ValueError("No GML files found in ZIP archive")
            
            # Process first GML file
            gml_path = gml_files[0]
            logger.info(f"Processing GML file: {os.path.basename(gml_path)}")
        
        elif data_path.endswith('.gml'):
            # Direct GML file
            logger.info("Reading GML file...")
            gml_path = data_path
        
        else:
            raise ValueError(f"Unsupported file format: {data_path}")
        
        # Get all layers from GML file
        try:
            layers = fiona.listlayers(gml_path)
            logger.info(f"Found {len(layers)} layers: {layers}")
        except Exception as e:
            logger.warning(f"Could not list layers: {e}, trying to read as single layer")
            layers = [None]  # Default layer
        
        # Read all layers and combine them
        all_gdfs = []
        for i, layer in enumerate(layers):
            try:
                logger.info(f"Reading layer {i+1}/{len(layers)}: {layer}")
                
                if layer:
                    gdf = gpd.read_file(gml_path, layer=layer)
                else:
                    gdf = gpd.read_file(gml_path)
                
                if not gdf.empty:
                    # Add layer info as column
                    gdf['source_layer'] = layer if layer else 'default'
                    all_gdfs.append(gdf)
                    logger.info(f"  Layer {layer}: {len(gdf)} features")
                else:
                    logger.info(f"  Layer {layer}: empty, skipping")
                    
            except Exception as e:
                logger.warning(f"  Could not read layer {layer}: {e}")
                continue
        
        if not all_gdfs:
            raise ValueError("No valid layers found in GML file")
        
        # Combine all layers
        if len(all_gdfs) == 1:
            gdf = all_gdfs[0]
        else:
            logger.info("Combining multiple layers...")
            # Combine layers with same CRS
            combined_gdf = None
            for layer_gdf in all_gdfs:
                if combined_gdf is None:
                    combined_gdf = layer_gdf.copy()
                else:
                    # Ensure same CRS before combining
                    if layer_gdf.crs != combined_gdf.crs:
                        layer_gdf = layer_gdf.to_crs(combined_gdf.crs)
                    
                    # Combine with ignore_index to avoid index conflicts
                    combined_gdf = gpd.GeoDataFrame(
                        pd.concat([combined_gdf, layer_gdf], ignore_index=True)
                    )
            gdf = combined_gdf
        
        logger.info(f"Combined dataset: {len(gdf)} features")
        logger.info(f"Original CRS: {gdf.crs}")
        logger.info(f"Columns: {list(gdf.columns)}")
        
        # Ensure correct projection (EPSG:25833)
        if gdf.crs != 'EPSG:25833':
            logger.info("Reprojecting to EPSG:25833...")
            gdf = gdf.to_crs('EPSG:25833')
        
        # Create optimized GeoParquet file
        parquet_filename = f"cli_skred_{timestamp}.parquet"
        parquet_path = os.path.join(output_dir, parquet_filename)
        
        logger.info(f"Writing GeoParquet to: {parquet_path}")
        
        # Write with optimized settings
        gdf.to_parquet(
            parquet_path,
            compression='snappy',
            row_group_size=10000
        )
        
        # Get file size for logging
        parquet_size = os.path.getsize(parquet_path)
        original_size = storage_info['file_size_bytes']
        compression_ratio = (1 - parquet_size / original_size) * 100 if original_size > 0 else 0
        
        logger.info(f"GeoParquet conversion completed:")
        logger.info(f"  Original size: {original_size:,} bytes")
        logger.info(f"  Parquet size: {parquet_size:,} bytes")
        logger.info(f"  Compression: {compression_ratio:.1f}%")
        logger.info(f"  Features: {len(gdf):,}")
        logger.info(f"  Layers processed: {len(all_gdfs)}")
        logger.info(f"  CRS: {gdf.crs}")
        
        return {
            "parquet_path": parquet_path,
            "features_count": len(gdf),
            "file_size_bytes": parquet_size,
            "compression_ratio": compression_ratio,
            "crs": str(gdf.crs),
            "columns": list(gdf.columns),
            "layers_processed": len(all_gdfs),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"GeoParquet conversion failed: {e}")
        raise

def validate_data(storage_info):
    """Validate the downloaded data"""
    logger.info("Validating downloaded data...")
    
    data_path = storage_info['data_path']
    
    try:
        # Check if file exists
        if not os.path.exists(data_path):
            raise ValueError(f"Data file not found: {data_path}")
        
        # Get file info
        file_size = os.path.getsize(data_path)
        
        if file_size == 0:
            raise ValueError("Data file is empty")
        
        # Basic content validation for GML
        is_valid_content = False
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                first_lines = f.read(1000)
                if '<?xml' in first_lines or '<gml' in first_lines.lower():
                    is_valid_content = True
        except UnicodeDecodeError:
            # Might be binary (ZIP) - that's also valid
            is_valid_content = True
        
        # Quality report
        quality_report = {
            "dataset": "geonorge_cli_skred",
            "validation_time": datetime.now().isoformat(),
            "file_path": data_path,
            "file_size_bytes": file_size,
            "checks": {
                "file_exists": True,
                "file_readable": True,
                "non_empty": file_size > 0,
                "valid_content": is_valid_content
            },
            "status": "pass" if is_valid_content else "warning"
        }
        
        logger.info(f"Validation result: {json.dumps(quality_report, indent=2)}")
        
        return quality_report
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise ValueError(f"Data validation failed: {e}")

def validate_geoparquet(parquet_info):
    """Validate the converted GeoParquet file"""
    logger.info("Validating GeoParquet file...")
    
    # Import libraries inside function following guidelines
    import geopandas as gpd
    
    parquet_path = parquet_info['parquet_path']
    
    try:
        # Basic validation
        if not os.path.exists(parquet_path):
            raise ValueError(f"GeoParquet file not found: {parquet_path}")
        
        file_size = os.path.getsize(parquet_path)
        if file_size == 0:
            raise ValueError("GeoParquet file is empty")
        
        # Test reading the file
        gdf = gpd.read_parquet(parquet_path)
        
        # Validate geospatial properties
        if gdf.empty:
            raise ValueError("GeoParquet contains no features")
        
        if not hasattr(gdf, 'geometry') or 'geometry' not in gdf.columns:
            raise ValueError("GeoParquet missing geometry column")
        
        # Check CRS
        crs_match = str(gdf.crs) == 'EPSG:25833'
        
        # Basic geometry validation
        invalid_geom_count = gdf.geometry.isna().sum()
        total_features = len(gdf)
        
        quality_report = {
            "dataset": "geonorge_cli_skred_parquet",
            "validation_time": datetime.now().isoformat(),
            "file_path": parquet_path,
            "file_size_bytes": file_size,
            "features_count": total_features,
            "crs": str(gdf.crs),
            "checks": {
                "file_exists": True,
                "file_readable": True,
                "non_empty": file_size > 0,
                "has_geometry": 'geometry' in gdf.columns,
                "correct_crs": crs_match,
                "features_present": total_features > 0
            },
            "invalid_geometry_count": int(invalid_geom_count),
            "valid_geometries": int(invalid_geom_count) == 0,
            "status": "pass" if invalid_geom_count == 0 else "warning"
        }
        
        logger.info(f"GeoParquet validation result: {json.dumps(quality_report, indent=2)}")
        
        return quality_report
        
    except Exception as e:
        logger.error(f"GeoParquet validation failed: {e}")
        raise ValueError(f"GeoParquet validation failed: {e}")

def main():
    """Main function to run the complete pipeline"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        dataset_uuid = getattr(args, 'dataset_uuid', None)
        
        if not dataset_uuid:
            logger.error("No dataset UUID provided")
            sys.exit(1)
            
        output_dir = args.output_dir
        
        logger.info(f"Starting Geonorge CLI Skred download pipeline...")
        logger.info(f"Dataset UUID: {dataset_uuid}")
        logger.info(f"Output directory: {output_dir}")
        
        # Setup
        setup_output_directory(output_dir)
        
        # Get dataset info
        dataset_info = get_dataset_info(dataset_uuid)
        
        # Request download
        download_info = request_download(dataset_uuid)
        
        # Download and store
        storage_result = download_and_store(download_info, dataset_uuid, output_dir)
        
        # Validate original data
        validation_result = validate_data(storage_result)
        
        # Convert to GeoParquet
        parquet_result = convert_to_geoparquet(storage_result, dataset_uuid, output_dir)
        
        # Validate GeoParquet
        parquet_validation = validate_geoparquet(parquet_result)
        
        logger.info("Pipeline completed successfully!")
        logger.info(f"Original data: {storage_result['data_path']}")
        logger.info(f"GeoParquet: {parquet_result['parquet_path']}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()