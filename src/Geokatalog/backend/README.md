# STAC Catalog Backend

Backend for the STAC (SpatioTemporal Asset Catalog) system built with FastAPI.

## Supported Formats

- **COG** (Cloud Optimized GeoTIFF) - `.tif`, `.tiff`
- **GeoParquet** - `.parquet`, `.geoparquet`
- **FlatGeobuf** - `.fgb`
- **PMTiles** - `.pmtiles`
- **COPC** (Cloud Optimized Point Cloud) - `.copc.laz`, `.laz`

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

2. Create a `.env` file (or copy from `.env.example`):
```
DATA_DIRECTORY=./data
CATALOG_TITLE=My STAC Catalog
CATALOG_DESCRIPTION=Dynamic STAC catalog for geospatial data
API_HOST=0.0.0.0
API_PORT=8000
```

3. Create a data directory and add your geospatial files:
```powershell
mkdir data
# Copy your geospatial files to the data directory
```

## Running the Server

Start the development server:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or run directly:

```powershell
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Endpoints

### STAC API Endpoints

- `GET /` - Root catalog
- `GET /collections` - List all collections
- `GET /collections/{collection_id}` - Get a specific collection
- `GET /collections/{collection_id}/items` - List items in a collection
  - Query params: `limit` (default: 100), `offset` (default: 0)
- `GET /collections/{collection_id}/items/{item_id}` - Get a specific item
- `GET /search` - Search items across collections
  - Query params: `bbox`, `datetime`, `collections`, `limit`

### Admin Endpoints

- `POST /refresh` - Refresh the catalog by re-scanning the data directory
- `GET /health` - Health check

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models/
│   │   └── config.py        # Configuration management
│   ├── scanner/
│   │   └── file_scanner.py  # File scanning and metadata extraction
│   └── stac/
│       ├── catalog.py       # STAC Catalog generator
│       ├── collection.py    # STAC Collection manager
│       └── item.py          # STAC Item generator
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development

### Testing with curl

Get root catalog:
```powershell
curl http://localhost:8000/
```

List collections:
```powershell
curl http://localhost:8000/collections
```

Search items:
```powershell
curl "http://localhost:8000/search?limit=10"
```

Refresh catalog:
```powershell
curl -X POST http://localhost:8000/refresh
```

## Notes

- The catalog is built in-memory on startup by scanning the data directory
- Use the `/refresh` endpoint to re-scan the directory after adding new files
- All geospatial files must have valid spatial metadata to be included in the catalog
- The API follows the STAC specification version 1.0.0

