#!/bin/bash

# Usage: ./gdb_to_pmtiles_all.sh path_to.gdb output.pmtiles

set -e

GDB_PATH="$1"
OUTPUT_PMTILES="$2"

# Check arguments
if [[ -z "$GDB_PATH" || -z "$OUTPUT_PMTILES" ]]; then
  echo "Usage: $0 path_to.gdb output.pmtiles"
  exit 1
fi

# Check requirements
command -v ogrinfo >/dev/null 2>&1 || { echo >&2 "ogrinfo is required but not installed."; exit 1; }
command -v ogr2ogr >/dev/null 2>&1 || { echo >&2 "ogr2ogr is required but not installed."; exit 1; }
command -v tippecanoe >/dev/null 2>&1 || { echo >&2 "tippecanoe is required but not installed."; exit 1; }
command -v pmtiles >/dev/null 2>&1 || { echo >&2 "pmtiles CLI is required (npm install -g @maplibre/pmtiles)"; exit 1; }

# Create a temporary working directory
TMPDIR=$(mktemp -d)
echo "Working directory: $TMPDIR"

# Get all layers from the GDB
LAYERS=$(ogrinfo -ro -q "$GDB_PATH" | grep "^Layer:" | awk '{print $2}')

echo "Found layers:"
echo "$LAYERS"

# Export each layer to GeoJSON
for LAYER in $LAYERS; do
  echo "Exporting layer $LAYER to GeoJSON..."
  ogr2ogr -f GeoJSON -t_srs EPSG:4326 "$TMPDIR/${LAYER}.geojson" "$GDB_PATH" "$LAYER"
done

# Build tippecanoe command with all layers
TIPPECANOE_CMD="tippecanoe -o $TMPDIR/temp.mbtiles --force --drop-densest-as-needed -zg"

for LAYER in $LAYERS; do
  TIPPECANOE_CMD+=" -L $LAYER:$TMPDIR/${LAYER}.geojson"
done

echo "Running tippecanoe to create MBTiles..."
eval "$TIPPECANOE_CMD"

echo "Converting MBTiles to PMTiles..."
pmtiles convert "$TMPDIR/temp.mbtiles" "$OUTPUT_PMTILES"

echo "✅ Done! PMTiles created at: $OUTPUT_PMTILES"

# Cleanup
rm -rf "$TMPDIR"
