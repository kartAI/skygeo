# ⛅ SkyGeo 🗺️

Utforskning av cloud native formater og STAC metadata for norske geografiske datasett.

## Demoer og Eksperimenter

Se ulike måter å produsere, konvertere og bruke Cloud Native Geo-formater på gjennom kode-eksempler og interaktive demoer.

**Interaktive demoer:**

| Demo | Beskrivelse | Kildekode |
|------|-------------|-----------|
| [GeoNorge CSW til STAC](https://kartai.github.io/skygeo/geonorge2stac/index.html) | Konvertering av GeoNorge metadatakatalog til STAC-format (JSON og GeoParquet) | [`/src/geonorge2stac`](src/geonorge2stac) |
| [PMTiles bakgrunnskart N5000](https://kartai.github.io/skygeo/pmtiles_bakgrunnskart/index.html) | Interaktivt kart med lag fra N5000 ved hjelp av PMTiles og MapLibre | [`/src/planetiles2pmtiles`](src/planetiles2pmtiles) |
| [PMTiles bakgrunnskart N250](https://kartai.github.io/skygeo/pmtiles_bakgrunnskart/n250/index.html) | Interaktivt kart med lag fra N250 ved hjelp av PMTiles og MapLibre | [`/src/planetiles2pmtiles`](src/planetiles2pmtiles) |
| [FlatGeobuf veinett](https://kartai.github.io/skygeo/flatgeobuf/fgb.html) | Veinettsdata (N250) i FlatGeobuf-format for effektiv vektor-streaming | [`/src/flatgeobuf`](src/flatgeobuf) |
| [GeoParquet: Er E6 den strakaste vegan?](https://kartai.github.io/skygeo/parquet/parquet.html) | DuckDB WASM-demo som analyserer veiretthet i GeoParquet-data | [`/src/geoparquet`](src/geoparquet) |

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

## Hva er egentlig Cloud Native Geospatial?
Les mer utdypende introduksjon til [cloud native formater](docs/formater.md)

### Introduksjon og Motivasjon

"Cloud-Native Geospatial" (CNG) er et paradigmeskifte i hvordan vi håndterer og aksesserer geospatiale data. Glem den tradisjonelle arbeidsflyten med å finne en ZIP-fil på en FTP-server, laste ned 3 GB med GML-filer, pakke ut, og så endelig laste det inn i GIS-programvaren – bare for å oppdage at du ser på feil område. Motivasjonen bak CNG er å fjerne denne unødvendige dataoverføringen og ventetiden.

### Problem og Løsning: "Partial" og "Parallel Reads"

Det tradisjonelle problemet er at filformater som en standard GeoTIFF eller Shapefil er designet for å bli lest fra en rask, lokal harddisk. De er ikke "stream-bare". Hvis du trenger pikslene i nedre høyre hjørne av en 10 GB GeoTIFF, må du kanskje lese gjennom nesten hele filen for å finne dem.

"Cloud-native"-løsningen er å internt strukturere filene slik at de kan leses effektivt over HTTP. "Magien" ligger i å utnytte **HTTP Range Requests**. Tenk på det som å streame en 80GB 4K-film: du trenger ikke laste ned hele filen for å hoppe til de siste fem minuttene. En CNG-fil (som en **Cloud Optimized GeoTIFF, COG**) har en intern indeks i starten. En klient (som QGIS) leser denne lille indeksen først, og ber deretter serveren om kun de spesifikke bytene den trenger for å vise kartutsnittet ditt. Dette muliggjør:

- **Partial Reads:** Hente bare en del av filen (f.eks. ett zoom-nivå, ett tidssteg).
- **Parallel Reads:** Flere prosesser som henter forskjellige deler av samme fil samtidig, noe som er kritisk for høy ytelse

### Forholdet til andre standarder

CNG-formater erstatter ikke nødvendigvis tradisjonelle OGC-tjenester (som WMS/WFS), men de tilbyr et kraftig, "server-løst" alternativ. I stedet for å vedlikeholde en aktiv server-applikasjon (som MapServer/GeoServer) som dynamisk genererer bilder eller features, kan du legge en statisk COG- eller FlatGeobuf-fil i en "dum" skylagringsbøtte (som S3 eller Azure Blob). Klienten (QGIS, MapLibre, OpenLayers) gjør jobben. Dette er ofte dramatisk billigere, mer skalerbart og enklere å vedlikeholde. Web-standarder som GeoJSON og Vector Tiles er nært beslektet; PMTiles er for eksempel en måte å samle `vector tiles` i én enkelt, cloud native fil.

Dokumentasjon om ulike Cloud Native-formater finnes under `\docs\formater\`.

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
