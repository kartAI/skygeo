# GeoParquet

## Format/teknologi
GeoParquet er et åpent, kolonnebasert vektorformat for geodata, optimalisert for analyse og lagring. Demoen bruker Python, DuckDB, GDAL og GeoPandas.

## Formål
Konvertere N50 vektordata til GeoParquet, vise bruk av formatet for analyse og benchmarking mot tradisjonelle formater.

## Getting started
- Installer avhengigheter: `pip install -r requirements.txt`
- Last ned N50-data fra Geonorge og pakk ut i `src/geoparquet`
- Åpne `main.ipynb` for stegvis konvertering og analyse

## Struktur
- `main.ipynb`: Notebook for konvertering og demo
- `requirements.txt`: Python-avhengigheter
- `utils.py`: Hjelpefunksjoner
- `img/`: Bilder og illustrasjoner
