# N50 til STAC

## Format/teknologi
STAC (SpatioTemporal Asset Catalog) er en åpen standard for metadata og katalogisering av geodata. Eksempelet bruker Python, rasterio og pystac.

## Formål
Automatisere generering av STAC metadata fra N50 GeoTIFF-rasterdata. Lager katalog med oversikt og metadata for hvert kartblad.

## Getting started
- Installer avhengigheter: `pip install rasterio pystac shapely`
- Åpne `N50_GeoTiffTilSTAC.ipynb` for stegvis konvertering og kataloggenerering

## Struktur
- `N50_GeoTiffTilSTAC.ipynb`: Notebook for konvertering og katalog
- `requirements.txt`: Python-avhengigheter
- `utils.py`: Hjelpefunksjoner
