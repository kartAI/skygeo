# pip install owslib pillow rasterio numpy
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import rasterio
import numpy as np
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import os
from pathlib import Path

def prepare_benchmark_data():
    """Prepare COG files for all test areas"""
    
    WMS_URL = "https://wms.geonorge.no/skwms1/wms.historiskekart?"
    wms = WebMapService(WMS_URL, version="1.3.0")
    
    # Test areas with different sizes for comprehensive benchmarking
    test_areas = [
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
    
    # Create cogs directory
    os.makedirs("cogs", exist_ok=True)
    
    for area in test_areas:
        print(f"Processing {area['name']}...")
        
        # Get WMS data
        img_bytes = wms.getmap(
            layers=["historiskekart"],
            styles=[""],
            srs="EPSG:3857",
            bbox=area["bbox"],
            size=area["size"],
            format="image/png",
            transparent=True,
        )
        
        # Convert to COG
        create_cog_from_png(img_bytes, area, f"cogs/{area['name']}.cog.tif")
        
        print(f"✓ {area['name']} completed")

def prepare_norway_tiles():
    """Prepare tiled COGs for a larger area - demonstrating multi-COG approach"""
    
    WMS_URL = "https://wms.geonorge.no/skwms1/wms.historiskekart?"
    wms = WebMapService(WMS_URL, version="1.3.0")
    
    # Define a larger area around Oslo/Østfold region for demonstration
    # This is big enough to show tiling benefits but manageable to process
    demo_bbox = (800000, 8000000, 1400000, 8600000)  # Covers Oslo + surrounding areas
    
    # Create a 3x3 grid of tiles for demonstration
    # Each tile will be 2048x2048 pixels
    tile_size = (2048, 2048)
    num_tiles_x = 3
    num_tiles_y = 3
    
    # Calculate tile dimensions in meters
    bbox_width = demo_bbox[2] - demo_bbox[0]
    bbox_height = demo_bbox[3] - demo_bbox[1]
    tile_width_meters = bbox_width / num_tiles_x
    tile_height_meters = bbox_height / num_tiles_y
    
    print(f"Creating {num_tiles_x} x {num_tiles_y} = {num_tiles_x * num_tiles_y} tiles for demonstration")
    print(f"Each tile: {tile_size[0]}x{tile_size[1]} pixels")
    print(f"Coverage area: {bbox_width/1000:.1f}km x {bbox_height/1000:.1f}km")
    print(f"Each tile covers: {tile_width_meters/1000:.1f}km x {tile_height_meters/1000:.1f}km")
    
    # Create tiles directory
    os.makedirs("cogs/demo_tiles", exist_ok=True)
    
    tile_count = 0
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            # Calculate tile bbox
            tile_bbox = (
                demo_bbox[0] + i * tile_width_meters,
                demo_bbox[1] + j * tile_height_meters,
                demo_bbox[0] + (i + 1) * tile_width_meters,
                demo_bbox[1] + (j + 1) * tile_height_meters
            )
            
            tile_name = f"demo_tile_{i:02d}_{j:02d}"
            
            try:
                print(f"Processing tile {tile_count + 1}/{num_tiles_x * num_tiles_y}: {tile_name}")
                
                # Get WMS data for this tile
                img_bytes = wms.getmap(
                    layers=["historiskekart"],
                    styles=[""],
                    srs="EPSG:3857",
                    bbox=tile_bbox,
                    size=tile_size,
                    format="image/png",
                    transparent=True,
                )
                
                # Convert to COG
                output_path = f"cogs/demo_tiles/{tile_name}.cog.tif"
                create_cog_from_png(img_bytes, {"bbox": tile_bbox, "size": tile_size}, output_path)
                
                print(f"✓ {tile_name} completed")
                tile_count += 1
                
            except Exception as e:
                print(f"✗ Error processing {tile_name}: {e}")
                continue
    
    print(f"\nCompleted {tile_count} tiles for demonstration area")
    
    # Create a tile index file for easy access
    create_tile_index(num_tiles_x, num_tiles_y, tile_width_meters, tile_height_meters, demo_bbox, "demo_tiles")

def create_tile_index(num_tiles_x, num_tiles_y, tile_width_meters, tile_height_meters, demo_bbox, tile_dir):
    """Create a JSON index file describing all tiles for easy client-side access"""
    
    import json
    
    tile_index = {
        "name": "Historical Maps - Tiled Demonstration",
        "description": "Tiled COG files demonstrating multi-COG approach for larger areas",
        "crs": "EPSG:3857",
        "tile_size": [2048, 2048],
        "tile_dimensions_meters": [tile_width_meters, tile_height_meters],
        "total_extent": demo_bbox,
        "tiling_strategy": f"{num_tiles_x}x{num_tiles_y} grid",
        "use_case": "Demonstrates how to serve large areas efficiently using multiple COG files",
        "tiles": []
    }
    
    for i in range(num_tiles_x):
        for j in range(num_tiles_y):
            tile_bbox = (
                demo_bbox[0] + i * tile_width_meters,
                demo_bbox[1] + j * tile_height_meters,
                demo_bbox[0] + (i + 1) * tile_width_meters,
                demo_bbox[1] + (j + 1) * tile_height_meters
            )
            
            tile_info = {
                "name": f"demo_tile_{i:02d}_{j:02d}",
                "filename": f"demo_tile_{i:02d}_{j:02d}.cog.tif",
                "bbox": tile_bbox,
                "position": [i, j],
                "url": f"/cogs/{tile_dir}/demo_tile_{i:02d}_{j:02d}.cog.tif"
            }
            
            tile_index["tiles"].append(tile_info)
    
    # Save tile index
    with open(f"cogs/{tile_dir}/tile_index.json", "w") as f:
        json.dump(tile_index, f, indent=2)
    
    print(f"✓ Tile index created: cogs/{tile_dir}/tile_index.json")

def create_cog_from_png(png_bytes, area, output_path):
    """Convert PNG WMS response to COG format"""
    
    # Read PNG image
    img = Image.open(BytesIO(png_bytes.read()))
    img_array = np.array(img)
    
    # Handle RGBA vs RGB
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        alpha = img_array[:, :, 3:4] / 255.0
        rgb = img_array[:, :, :3] / 255.0
        white_background = np.ones_like(rgb)
        img_array = (rgb * alpha + white_background * (1 - alpha)) * 255
        img_array = img_array.astype(np.uint8)
        bands = 3
    else:
        bands = img_array.shape[2] if len(img_array.shape) == 3 else 1
    
    # Reshape for rasterio
    if len(img_array.shape) == 3:
        data = np.transpose(img_array, (2, 0, 1))
    else:
        data = img_array[np.newaxis, :, :]
    
    # Create COG profile
    cog_profile = {
        "driver": "COG",
        "height": area["size"][1],
        "width": area["size"][0],
        "count": bands,
        "dtype": data.dtype,
        "crs": CRS.from_string("EPSG:3857"),
        "transform": from_bounds(area["bbox"][0], area["bbox"][1], 
                                area["bbox"][2], area["bbox"][3], 
                                area["size"][0], area["size"][1]),
        "nodata": 0,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }
    
    # Write COG
    with rasterio.open(output_path, "w", **cog_profile) as dst:
        dst.write(data)

if __name__ == "__main__":
    print("=== COG Data Preparation ===")
    print("1. Preparing benchmark data (small areas)...")
    prepare_benchmark_data()
    
    print("\n2. Preparing tiled COG demonstration (larger area)...")
    prepare_norway_tiles()
    
    print("\n=== Data Preparation Complete ===")
    print("Files created:")
    print("- cogs/oslo_small.cog.tif")
    print("- cogs/oslo_medium.cog.tif") 
    print("- cogs/oslo_large.cog.tif")
    print("- cogs/demo_tiles/ (directory with 9 tiled COGs)")
    print("- cogs/demo_tiles/tile_index.json (tile metadata)")
    print("\nThis demonstrates:")
    print("- Single COG approach for small areas")
    print("- Multi-COG tiling approach for larger areas")
    print("- How to efficiently serve large datasets") 