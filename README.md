# ⛅ SkyGeo 🗺️
Utforskning av cloud native formater og STAC metadata for norske geografiske datasett

## Eksperimenter og demoer
Se ulike måter å produsere, konvertere og bruke Cloud Native Geo-formater på gjennom ulike kode-eksempler og demoer. 

**Struktur på kodebasen:**
* `\src` inneholder alle eksempler. Hvert eksempel har sin egen mappe. Fks `\src\cog\`
* Eksperimentene bruker ulike verktøy. Noen har `.devcontainer`, rene `Jupyter Notebook` og `shell script`

**Oversikt eksperimenter og kode-eksempler**

| Eksempel                      | Mappe       | Formål                                                                   |
| ----------------------------- | ----------- | ------------------------------------------------------------------------ |
| Cloud Optimized GeoTiff (COG) | `\src\cog\` | Flere eksempler på konvertering og produksjon av Cloud Optimized Geotiff |
| COPC (Point Cloud)            | `\src\copc\` | Konvertering av LAS/LAZ til COPC-format for optimal lagring og spørring av punktskydata |
| FlatGeobuf                    | `\src\flatgeobuf\` | Konvertering fra GDB til FlatGeobuf. Moderne, åpent og effektivt vektorformat. |
| GeoParquet                    | `\src\geoparquet\` | Konvertering av N50 vektordata til GeoParquet. Demo med Python, DuckDB, og benchmarking. |
| N50 til STAC                  | `\src\N50TilSTAC\` | Generering av STAC metadata fra N50 GeoTIFF. Automatisert katalog for rasterkartblader. |
| PMTiles                       | `\src\pmtiles\` | Konvertering av N50 vektordata til PMTiles. Demo med Docker, Maplibre, og webklient for visning. |
| Webklienter                   | `\src\webclient\` | Demo på bruk av OpenLayers for visning av COG-data i nettleser. |


## "Kort om formater"

