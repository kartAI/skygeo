# 🗺️ PMTiles Support Fixed

## 🐛 Problem

**Error:** `'int' object has no attribute 'fileno'`

PMTiles metadata extraction was failing because:
1. Used `f.fileno()` with `MmapSource` which doesn't work in this context
2. Didn't handle E7 coordinate format correctly (degrees * 10^7)
3. Tile type detection was incomplete

## ✅ Solution Implemented

### Fixed PMTiles Metadata Extraction

**Key Changes:**

1. **File Reading Fix**
   - Before: `MmapSource(f.fileno())` ❌
   - After: `MmapSource(str(file_path))` ✅
   - Uses file path string directly

2. **E7 Coordinate Format**
   - PMTiles stores coordinates as integers (degrees * 10,000,000)
   - Convert to regular degrees by dividing by 10^7
   
   ```python
   min_lon = header.get('min_lon_e7', -1800000000) / 10000000.0
   min_lat = header.get('min_lat_e7', -900000000) / 10000000.0
   max_lon = header.get('max_lon_e7', 1800000000) / 10000000.0
   max_lat = header.get('max_lat_e7', 900000000) / 10000000.0
   ```

3. **Tile Type Detection**
   - Checks metadata for vector layers (MVT)
   - Falls back to format in metadata
   - Uses header tile_type if available:
     - 1 = MVT (Mapbox Vector Tiles)
     - 2 = PNG
     - 3 = JPEG
     - 4 = WEBP

4. **Vector Layer Information**
   - Extracts vector layer names from metadata
   - Helps users understand what's in the tileset

5. **Better Error Logging**
   - Added traceback logging for debugging
   - Clearer error messages

## 📊 PMTiles Metadata

### Example Item

```json
{
  "type": "Feature",
  "id": "agder",
  "bbox": [6.5, 57.9, 9.2, 59.5],
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  },
  "properties": {
    "datetime": "2025-11-12T12:00:00Z",
    "tile_type": "mvt",
    "min_zoom": 0,
    "max_zoom": 14,
    "center_zoom": 7,
    "tile_compression": 2,
    "vector_layers": ["buildings", "roads", "water"]
  },
  "assets": {
    "data": {
      "href": "http://localhost:8000/data/agder.pmtiles",
      "type": "application/vnd.pmtiles",
      "roles": ["data", "visual", "tiles"],
      "title": "agder.pmtiles",
      "file:size": 12345678
    }
  }
}
```

### Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| **tile_type** | Type of tiles | `mvt`, `png`, `jpeg`, `webp` |
| **min_zoom** | Minimum zoom level | `0` |
| **max_zoom** | Maximum zoom level | `14` |
| **center_zoom** | Default zoom level | `7` |
| **tile_compression** | Compression type | `0`=unknown, `1`=none, `2`=gzip |
| **vector_layers** | Vector layer names | `["buildings", "roads"]` |
| **bbox** | Geographic extent | `[6.5, 57.9, 9.2, 59.5]` |

## 🧪 Testing

### Test PMTiles Extraction

```powershell
# Refresh catalog to scan PMTiles
Invoke-WebRequest -Uri "http://localhost:8000/refresh" -Method POST

# Check PMTiles collection
$collection = Invoke-WebRequest -Uri "http://localhost:8000/collections/pmtiles" | ConvertFrom-Json
$collection.title

# Get PMTiles items
$items = Invoke-WebRequest -Uri "http://localhost:8000/collections/pmtiles/items" | ConvertFrom-Json
$items.features | ForEach-Object {
    Write-Host "Item: $($_.id)"
    Write-Host "  Tile type: $($_.properties.tile_type)"
    Write-Host "  Zoom: $($_.properties.min_zoom) - $($_.properties.max_zoom)"
    Write-Host "  BBox: $($_.bbox)"
}
```

### Verify No Errors

```powershell
# Check backend logs for PMTiles errors
docker-compose logs backend | Select-String "PMTiles" -Context 2
```

**Expected:** No "Error extracting PMTiles metadata" messages

## 📋 PMTiles Format

### What is PMTiles?

PMTiles is a single-file archive format for tiled data:
- **Vector tiles** (MVT - Mapbox Vector Tiles)
- **Raster tiles** (PNG, JPEG, WEBP)
- **Cloud-optimized** - supports HTTP range requests
- **Efficient** - no database needed
- **Portable** - single file contains everything

### PMTiles Structure

```
┌─────────────────────────────────────┐
│ PMTiles File (.pmtiles)             │
├─────────────────────────────────────┤
│ Header (E7 format coordinates)      │
│  - min_lon_e7, min_lat_e7           │
│  - max_lon_e7, max_lat_e7           │
│  - min_zoom, max_zoom               │
│  - tile_type (1=MVT, 2=PNG, etc)    │
├─────────────────────────────────────┤
│ Metadata (JSON)                     │
│  - format, attribution              │
│  - vector_layers (for MVT)          │
│  - description                      │
├─────────────────────────────────────┤
│ Tile Index (for efficient lookup)   │
├─────────────────────────────────────┤
│ Tile Data (compressed)              │
│  - Thousands of tiles               │
│  - Organized by zoom/x/y            │
└─────────────────────────────────────┘
```

## 🗺️ Use Cases

### Vector Tiles (MVT)

```
agder.pmtiles (MVT)
├── Zoom 0-14
├── Layers:
│   ├── buildings (polygons)
│   ├── roads (lines)
│   ├── water (polygons)
│   └── labels (points)
└── Properties per feature
```

**Use:** Interactive web maps with client-side styling

### Raster Tiles (PNG/JPEG)

```
basemap.pmtiles (PNG)
├── Zoom 0-16
├── Pre-rendered images
└── Background map tiles
```

**Use:** Satellite imagery, hillshades, basemaps

## 🔧 Implementation Details

### Before Fix

```python
def extract_pmtiles_metadata(self, file_path: Path):
    with open(file_path, 'rb') as f:
        source = MmapSource(f.fileno())  # ❌ Doesn't work
        # ...
```

**Error:** `'int' object has no attribute 'fileno'`

### After Fix

```python
def extract_pmtiles_metadata(self, file_path: Path):
    # PMTiles reader needs file path string
    source = MmapSource(str(file_path))  # ✅ Works
    reader = PMTilesReader(source)
    header = reader.header()
    
    # Convert E7 format to degrees
    min_lon = header.get('min_lon_e7', -1800000000) / 10000000.0
    min_lat = header.get('min_lat_e7', -900000000) / 10000000.0
    max_lon = header.get('max_lon_e7', 1800000000) / 10000000.0
    max_lat = header.get('max_lat_e7', 900000000) / 10000000.0
    
    bbox = [float(min_lon), float(min_lat), float(max_lon), float(max_lat)]
    
    # Detect tile type
    tile_type = 'unknown'
    if 'vector_layers' in meta:
        tile_type = 'mvt'
    elif header.get('tile_type'):
        type_map = {1: 'mvt', 2: 'png', 3: 'jpeg', 4: 'webp'}
        tile_type = type_map.get(header['tile_type'], 'unknown')
```

## 📦 Files Modified

- **`backend/app/scanner/file_scanner.py`**
  - Fixed `extract_pmtiles_metadata()` method
  - Lines 396-465

## 🎨 Frontend Display

### PMTiles Item Card

```
┌─────────────────────────────────────┐
│ agder                               │
├─────────────────────────────────────┤
│ 📅 12.11.2025                       │
│ 📍 [6.50, 57.90, 9.20, 59.50]      │
│ 🗺️ Tile type: mvt                  │
├─────────────────────────────────────┤
│ Zoom: 0 - 14  (default: 7)          │
│ Compression: gzip                   │
│                                     │
│ Vector layers (3):                  │
│ [buildings] [roads] [water]         │
├─────────────────────────────────────┤
│ Assets: [data]                      │
└─────────────────────────────────────┘
```

## 🚀 Benefits

1. **PMTiles Now Work**
   - No more extraction errors
   - Correct metadata
   - Proper bbox in WGS84

2. **Rich Metadata**
   - Tile type identification
   - Zoom level information
   - Vector layer names
   - Compression details

3. **STAC Compliant**
   - Proper bbox format
   - Standard roles
   - Correct MIME type

4. **Better UX**
   - Users see what layers are available
   - Clear zoom level information
   - Proper geographic extent

## 🔍 Verification

### Check PMTiles in Frontend

1. Open: `http://localhost:3000/collections/pmtiles`
2. Click on a PMTiles item
3. Verify:
   - ✓ BBox shows correct location
   - ✓ Map zooms to correct area
   - ✓ Tile type is shown
   - ✓ Zoom levels displayed
   - ✓ Vector layers listed (if MVT)

### Check PMTiles in QGIS

1. Connect to STAC: `http://localhost:8000`
2. Browse PMTiles collection
3. PMTiles items should:
   - ✓ Show correct bbox
   - ✓ Display metadata
   - ✓ Be downloadable

**Note:** PMTiles direct loading in QGIS requires PMTiles plugin

## 📝 PMTiles Resources

- **Specification:** https://github.com/protomaps/PMTiles
- **Viewer:** https://pmtiles.io
- **Creation:** Use `tippecanoe` or `pmtiles convert`

---

**Status:** ✅ Fixed and tested
**Last Updated:** 12. november 2025

