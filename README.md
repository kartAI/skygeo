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


## Bakgrunn
Dagens arkitektur for koordinering og deling av geografiske data i Norge bygger på gammel teknologi. Det er flere ulemper med dagens arkitektur:
* Datakopiering: Data kopieres fra originaldata til GeoNorge for å kopieres flere ganger (klippes, transformeres) for deretter lastes ned i "bulk". 
* Brukeropplevelsen: Bruken av geografiske kartdata er vanskelig med dagens arkitektur. Data må i stor grad lastes ned i bulk og delete/insert for å oppdatere. Det er få moderne maskin-maskin grensesnitt for integrasjon med geografiske data.
* Metadata: Det er vesentlig enklere å finne og laste ned oppdaterte "open source" kartdata programmatisk enn det er å finne autorative åpne, norske data. Metadata-standarder og tilhørende API er i stor grad lagd for kompletthet og forvaltning heller enn enkelhet og brukervennlighet. 
* Skaleringskostnad: Dagens GIS-arkitektur krever stor grad av "compute"-ressurser, som databaseservere, OGC-servere (WMS,WFS m.m.) og prosesseringsjobber (FME). Ved økt bruk av infrastrukturen øker også "compute"-kostnader. "Compute"-ressurser har større vedlikeholdsbehov, større driftskostnader og høyere sikkerhetsrisiko knyttet til seg enn ren "storage". 

Nyere teknologi som utnytter moderne cloud-arkitektur har vist seg svært effektivt for lagring og deling av geografiske data på tvers av organisasjoner og brukere. Cloud Native for Geospatial er teknologi med formål om å i størst mulig grad benytte "storage"-ressurser fremfor "compute"-ressurser. Dette gjør skalering av bruk svært mye mer effektivt. Arkitekturen legger til rette for minimalt med kopiering for optimalisering og distribusjon. Nyere metadata-standarder er i større grad utviklet med brukeropplevelse og utviklervennlighet først. Eksempler på suksess finnes hos de store internasjonale dataeiere og cloud-leverandører - og har i stor grad blitt utviklet rundt satellittdata og "big data"-miljøer. Eksempler på dette er:
* 

## Prosjektmål
_Etablere kompetanse og teknisk erfaring med anvendelser av STAC og Cloud Native-formater på norske autorative geografiske kartdata_

### Delmål
1. Utforske og dokumentere status på STAC og cloud native formater for vektordata og rasterdata
1. Lage proof-of-concepts på STAC og cloud native på norske kartdata
1. Benchmarke og teste fordeler/ulemper mot "SkyGeo" og dagens arkitektur for koordinering av geografiske data
1. Konkrete anbefalinger og potensielle gevinster

-----------------
# Resultater:
## Erfaringer
* Dokumentere og oppsummere erfaringer, benchmarks, innsikt

# Usage

## Sånn konverterer du N50 til cloud native formater
* Geoparquet. 
    * Python notebooks. Basic, optimalisert, partisjonert
    * Tools
    * gdal/ogr2ogr, geopandas, duckdb, sedona/spark, databricks
* Validerings-tool på geoparquet
    * Utvide eksisterende cli-tools
* Flatgeobuf
    * Python notebooks
    * GDAL/ogr2ogr, geopandas
* Apache Iceberg
    * Sedona, Databricks?
* DuckLake
* PMTiles
    * tippecanoe, planetiler?
* Schema-utforskning
    * N50-schema til Overture-schema
    * N50-schema til OpenStreetMap-schema(?)

## Hvordan lage STAC metadata fra N50 datasettet
* Python-notebook for å konvertere fra GeoNorge-metadata til STAC
* Python-notebook for å konvertere fra "andre" metadata til STAC

## Sånn konverterer du flyfoto til cloud native formater
* COG
* Raster-tiles på mbtiles-format og pmtiles-format

## Demodata og demoservere
* dockerfiles
* S3-compatible bucket

## Eksempler på bruk av SkyGeo

### Webklienter
* Maplibre og bakgrunnskart N50 på PMTiles
    * Styling? Lage maplibre-style med LLM-konvertering av SLD fra Kartverket?
* Leaflet og flatgeobuf - hent data fra et layer for et utsnitt
* Leaflet og COG-bilder
* STAC-katalog. 
    * Lage automatisk katalog-nettside
    * Eksempler på oppslag ved å bruke STAC-API

### Data science

* DuckDB
    * Hent ut med filter på column og bbox fra N50-overture-style
    * Hent ut data med filter på bbox fra flatgeobuf

* Python - søke i STAC-kataloger
    * LLMs og STAC(?)

* Databricks

* Trino

