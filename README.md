# ⛅ SkyGeo 🗺️

Utforskning av cloud native formater og STAC metadata for norske geografiske datasett.

## Demoer og Eksperimenter

Se ulike måter å produsere, konvertere og bruke Cloud Native Geo-formater på gjennom kode-eksempler og interaktive demoer.

**Interaktive demoer:**

| Demo | Beskrivelse | Kildekode |
|------|-------------|-----------|
| GeoNorge CSW til STAC | Konvertering av GeoNorge metadatakatalog til STAC-format (JSON og GeoParquet) | [`/src/geonorge2stac`](src/geonorge2stac) |
| Tematisk bakgrunnskart (PMTiles) | Interaktivt kart med lag fra N5000 og N250 ved hjelp av PMTiles og MapLibre | [`/src/planetiles2pmtiles`](src/planetiles2pmtiles) |
| FlatGeobuf veinett | Veinettsdata (N250) i FlatGeobuf-format for effektiv vektor-streaming | [`/src/flatgeobuf`](src/flatgeobuf) |

Alle demoer finnes på [`/docs`](docs/).

**Oversikt over kode-eksempler og eksperimenter:**

| Eksempel | Mappe | Beskrivelse |
|----------|-------|-------------|
| Cloud Optimized GeoTiff (COG) | [`/src/cog`](src/cog) | Konvertering og produksjon av Cloud Optimized GeoTIFF |
| COPC (Point Cloud) | [`/src/copc`](src/copc) | Konvertering av LAS/LAZ til COPC-format |
| FlatGeobuf | [`/src/flatgeobuf`](src/flatgeobuf) | Konvertering til FlatGeobuf-vektorformat |
| GeoParquet | [`/src/geoparquet`](src/geoparquet) | Konvertering av N50 til GeoParquet, benchmarking med DuckDB |
| GeoNorge2STAC | [`/src/geonorge2stac`](src/geonorge2stac) | STAC-katalog fra GeoNorge CSW-metadata |
| N50 til STAC | [`/src/N50TilSTAC`](src/N50TilSTAC) | STAC-metadata fra N50 GeoTIFF-kartblader |
| PMTiles | [`/src/pmtiles`](src/pmtiles) | Konvertering av N50 til PMTiles med Docker og webklient |
| Planetiler → PMTiles | [`/src/planetiles2pmtiles`](src/planetiles2pmtiles) | Generering av vector tiles fra N5000/N250 |
| Webklient | [`/src/webclient`](src/webclient) | OpenLayers-eksempel for COG-visning |
| Demo-webapp | [`/src/demo`](src/demo) | Webapp med Parquet, FlatGeobuf, DuckDB og kartvisning |
| GeoNorge2GeoParquet Skred | [`/src/geonorge2geoparquet_skred`](src/geonorge2geoparquet_skred) | Skreddata fra GeoNorge til GeoParquet |
| GIS-søk | [`/src/gis-sok`](src/gis-sok) | Algoritme for sammenstilling av OSM og FKB data |

## Hva er Cloud Native Geospatial?

Cloud Native Geospatial (CNG) er et paradigmeskifte i hvordan vi håndterer geografiske data. I stedet for å laste ned store ZIP-filer fra FTP-servere, jobber CNG-formater med "partial" og "parallel reads" over HTTP – som streaming av en film. Du får kun den delen av dataene du trenger.

### Nøkkelbegreper

**Partial Reads & Parallel Reads:** 
Cloud-native formater som Cloud Optimized GeoTIFF (COG) har en intern indeks som gjør det mulig å hente kun relevante deler av filen via HTTP Range Requests. Dette gjør dataene tilgjengelige uten å måtte laste ned hele filen.

**Serverless tilnærming:** 
I stedet for å vedlikeholde aktive servere (som MapServer/GeoServer), legger du statiske Cloud Native-filer (COG, GeoParquet, FlatGeobuf) i skylagring (S3, Azure Blob) og lar klienten (QGIS, MapLibre, OpenLayers) gjøre jobben.

### Formater

- **COG (Cloud Optimized GeoTIFF):** For rasterdata
- **GeoParquet:** For vektordata, optimalisert for spørringer
- **FlatGeobuf:** Moderne, åpent vektorformat
- **PMTiles:** Pakker vector tiles i én fil for enkel distribusjon
- **Zarr:** For multidimensjonale vitenskapelige datasett

Les mer om [Cloud Native formater](docs/formater.md).

### Metadata med STAC

**STAC (SpatioTemporal Asset Catalog)** er en standardisert JSON-spesifikasjon som fungerer som "limet" i CNG-økosystemet. Det beskriver hva dataene er, geografisk dekningsområde, tidsstempel og – viktigst av alt – lenker direkte til Cloud Native-filene.

En STAC-fil inneholder `links` og `assets` som peker til dine CN-filer. Klienten leser STAC først, deretter streamer den dataene den trenger.

## Vanlige spørsmål

**Hvilket format skal jeg bruke for mitt webkart?**

- **Raster:** COG (Cloud Optimized GeoTIFF) for effektiv streaming. Eller pre-render til raster tiles (PMTiles).
- **Vektor:** Vector tiles i PMTiles-format. Alternativt GeoParquet eller FlatGeobuf for server-side spørring.

**Hvordan kombinerer jeg STAC-metadata med Cloud Native-filer?**

STAC-filer (JSON) inneholder `assets` som peker direkte til dine CN-filer (COG, GeoParquet, PMTiles). Klienten leser STAC først, deretter streamer dataene.

**Hvordan visualiserer jeg COG eller PMTiles raskt?**

- **COG:** OpenLayers eller MapLibre GL JS med raster-layer
- **PMTiles:** MapLibre GL JS med pmtiles-adapter

**Hva er hovedfordelene?**

- Raskere tilgang via partial/parallel reads
- Serverless, skyvennlig arkitektur
- Åpne standarder (støttet av QGIS, MapLibre, OpenLayers, Python)
- STAC-integrasjon for metadata og søk
- Fleksibel: kombiner raster og vektor i samme applikasjon
