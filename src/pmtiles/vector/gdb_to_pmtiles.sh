
#!/bin/bash

# Usage: ./gdb_to_pmtiles.sh path_to.gdb layer_name output.pmtiles

set -e

# --- Arguments ---
GDB_PATH="$1"
LAYER_NAME="$2"
OUTPUT_PMTILES="$3"

# --- Temporary filenames ---
GEOJSON_FILE="temp_${LAYER_NAME}.geojson"
MBTILES_FILE="temp_${LAYER_NAME}.mbtiles"

# --- Check requirements ---
command -v ogr2ogr >/dev/null 2>&1 || { echo >&2 "ogr2ogr is required but not installed."; exit 1; }
command -v tippecanoe >/dev/null 2>&1 || { echo >&2 "tippecanoe is required but not installed."; exit 1; }
command -v pmtiles >/dev/null 2>&1 || { echo >&2 "pmtiles CLI is required (npm install -g @maplibre/pmtiles)"; exit 1; }

echo "🧩 Converting GDB to GeoJSON..."
ogr2ogr -f GeoJSON "$GEOJSON_FILE" "$GDB_PATH" "$LAYER_NAME" -t_srs EPSG:4326

echo "🗺️ Creating MBTiles with tippecanoe..."
tippecanoe -o "$MBTILES_FILE" -l "$LAYER_NAME" -zg --drop-densest-as-needed "$GEOJSON_FILE"

echo "📦 Converting MBTiles to PMTiles..."
pmtiles convert "$MBTILES_FILE" "$OUTPUT_PMTILES"

echo "✅ Done! PMTiles file created at: $OUTPUT_PMTILES"

# Optional: Clean up
rm "$GEOJSON_FILE" "$MBTILES_FILE"
