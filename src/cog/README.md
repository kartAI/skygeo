# Cloud Optimized GeoTIFF (COG)

## Format/teknologi
Cloud Optimized GeoTIFF (COG) er et rasterformat optimalisert for cloud-lagring og streaming. Eksemplene her bruker Python, rasterio og rio-cogeo.

## Formål
Demonstrere konvertering av vanlige GeoTIFF og rasterdata til COG, inkludert håndtering av NODATA og optimalisering for web.

## Getting started
- Installer avhengigheter: `pip install rasterio rio-cogeo numpy pyproj shapely`
- Se på notebookene `gebco.ipynb` og `n-raster.ipynb` for eksempler på nedlasting og konvertering.

## Struktur
- `gebco.ipynb`: Nedlasting og konvertering av GEBCO-data til COG
- `n-raster.ipynb`: Konvertering av N-serie GeoTIFF til COG
- `requirements.txt`: Python-avhengigheter
- `data/`, `img/`: Eksempeldata og bilder
