# pip install owslib pillow pyproj rasterio numpy
from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import rasterio
import numpy as np
from rasterio.transform import from_bounds
from rasterio.crs import CRS

WMS_URL = "https://wms.geonorge.no/skwms1/wms.historiskekart?"

# 1) Load capabilities
wms = WebMapService(WMS_URL, version="1.3.0")

# Peek at available layer names
print("Layer count:", len(list(wms.contents)))
print("First 10 layers:", list(wms.contents)[:10])

# 2) Pick a layer (replace with one you want)
layer = list(wms.contents)[0]  # or e.g. 'HistoriskeKart' if present

# 3) Check supported CRS & formats
print("CRS:", wms[layer].crsOptions)
print("Formats:", wms.getOperationByName("GetMap").formatOptions)

# 4) Make a GetMap request for PNG
crs = "EPSG:3857"  # Web Mercator - good for web display
bbox = (1061715, 8373188, 1191695, 8476199)  # example bbox around Oslo in EPSG:3857
size = (2048, 2048)  # Higher resolution for better quality

# Request as PNG since TIFF not supported
img_bytes = wms.getmap(
    layers=[layer],
    styles=[""],
    srs=crs,
    bbox=bbox,
    size=size,
    format="image/png",
    transparent=True,
)

# 5) Convert PNG to GeoTIFF first, then to COG
def png_to_geotiff_to_cog(png_bytes, bbox, crs, size, output_path):
    """Convert PNG WMS response to GeoTIFF, then to COG format"""
    
    # Read PNG image
    img = Image.open(BytesIO(png_bytes.read()))
    img_array = np.array(img)
    
    # Handle RGBA vs RGB
    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
        # RGBA - convert to RGB by compositing on white background
        alpha = img_array[:, :, 3:4] / 255.0
        rgb = img_array[:, :, :3] / 255.0
        white_background = np.ones_like(rgb)
        img_array = (rgb * alpha + white_background * (1 - alpha)) * 255
        img_array = img_array.astype(np.uint8)
        bands = 3
    else:
        bands = img_array.shape[2] if len(img_array.shape) == 3 else 1
    
    # Reshape for rasterio (bands, height, width)
    if len(img_array.shape) == 3:
        data = np.transpose(img_array, (2, 0, 1))
    else:
        data = img_array[np.newaxis, :, :]
    
    # Step 1: Create GeoTIFF profile
    geotiff_profile = {
        "driver": "GTiff",
        "height": size[1],
        "width": size[0],
        "count": bands,
        "dtype": data.dtype,
        "crs": CRS.from_string(crs),
        "transform": from_bounds(bbox[0], bbox[1], bbox[2], bbox[3], size[0], size[1]),
        "nodata": 0,
        "compress": "lzw",
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
    }
    
    # Write intermediate GeoTIFF
    temp_geotiff = "temp_historiske_oslo.tif"
    with rasterio.open(temp_geotiff, "w", **geotiff_profile) as dst:
        dst.write(data)
    
    print(f"Intermediate GeoTIFF saved to: {temp_geotiff}")
    
    # Step 2: Convert GeoTIFF to COG
    with rasterio.open(temp_geotiff) as src:
        # Read data BEFORE closing the file
        cog_data = src.read()
        cog_profile = src.profile.copy()
        cog_profile["driver"] = "COG"
        cog_profile["compress"] = "lzw"
        cog_profile["tiled"] = True
        cog_profile["blockxsize"] = 512
        cog_profile["blockysize"] = 512
    
    # Write COG
    with rasterio.open(output_path, "w", **cog_profile) as dst:
        dst.write(cog_data)
    
    print(f"COG saved to: {output_path}")
    print(f"Image dimensions: {size[0]}x{size[1]}, Bands: {bands}")
    
    # Clean up temporary file
    import os
    os.remove(temp_geotiff)
    print("Temporary GeoTIFF removed")

# Convert PNG to GeoTIFF to COG
png_to_geotiff_to_cog(img_bytes, bbox, crs, size, "historiske_oslo.cog.tif")

# Also save original PNG for comparison
img = Image.open(BytesIO(img_bytes.read()))
img.save("historiske_oslo_original.png")
print("Original PNG saved to historiske_oslo_original.png")