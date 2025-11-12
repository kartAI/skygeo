# ⛅ SkyGeo 🗺️

Utforskning av cloud native formater og STAC metadata for norske geografiske datasett.

## Eksperimenter og demoer

Se ulike måter å produsere, konvertere og bruke Cloud Native Geo-formater på gjennom ulike kode-eksempler og demoer.

**Struktur på kodebasen:**

- `\src` inneholder alle eksempler. Hvert eksempel har sin egen mappe. Fks `\src\cog\`
- Eksperimentene bruker ulike verktøy. Noen har `.devcontainer`, rene `Jupyter Notebook` og `shell script`

**Oversikt eksperimenter og kode-eksempler**

| Eksempel                      | Mappe              | Formål                                                                                           |
| ----------------------------- | ------------------ | ------------------------------------------------------------------------------------------------ |
| Cloud Optimized GeoTiff (COG) | `\src\cog\`        | Flere eksempler på konvertering og produksjon av Cloud Optimized Geotiff                         |
| COPC (Point Cloud)            | `\src\copc\`       | Konvertering av LAS/LAZ til COPC-format for optimal lagring og spørring av punktskydata          |
| FlatGeobuf                    | `\src\flatgeobuf\` | Konvertering fra GDB til FlatGeobuf. Moderne, åpent og effektivt vektorformat.                   |
| GeoParquet                    | `\src\geoparquet\` | Konvertering av N50 vektordata til GeoParquet. Demo med Python, DuckDB, og benchmarking.         |
| N50 til STAC                  | `\src\N50TilSTAC\` | Generering av STAC metadata fra N50 GeoTIFF. Automatisert katalog for rasterkartblader.          |
| PMTiles                       | `\src\pmtiles\`    | Konvertering av N50 vektordata til PMTiles. Demo med Docker, Maplibre, og webklient for visning. |
| Webklienter                   | `\src\webclient\`  | Demo på bruk av OpenLayers for visning av COG-data i nettleser.                                  |
| Demo-webapp                   | `\src\demo\`        | Webapp som demonstrerer CloudNative-formater (Parquet, Flatgeobuf) med DuckDB og streaming til kart. |
| GeoNorge2GeoParquet Skred     | `\src\geonorge2geoparquet_skred\` | Sammenstilling og analyse av skreddata fra GeoNorge til GeoParquet. Python, DuckDB, overlay-spørringer. |
| GIS-søk                       | `\src\gis-sok\`     | Rask algoritme for sammenstilling av bygninger mellom OSM og FKB i store Parquet-datasett fra skyen. |

## Hva er egentlig Cloud Native Geospatial?
Les mer utdypende introduksjon til [cloud native formater](docs\formater.md)

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

### Hva med Metadata? => STAC

Hvis alle dataene dine bare er statiske filer, hvordan kan brukere finne dem? Svaret er **STAC (SpatioTemporal Asset Catalog)**. STAC er en enkel, standardisert JSON-spesifikasjon som fungerer som "limet" i dette økosystemet. Det er en metadata-standard som beskriver hva dataene er, hvor de dekker, når de er fra, og viktigst av alt: lenker direkte til de sky-native filene (f.eks. COG, GeoParquet, Zarr) som utgjør ressursen.

## FAQ:

### Jeg skal lage et web-kart. Hvilket format bør det være på?

- Raster: Bruk COG (Cloud Optimized GeoTIFF) for enkel, effektiv hosting og streaming via HTTP Range Requests. Alternativt pre-render til raster tiles (PMTiles) hvis du trenger mange hurtigtjenester for ulike zoomnivåer.

- Vektor: Bruk vector tiles (MVT). Pakk som PMTiles for enkel én‑fil hosting i skyen. For server-side spørring og analyse kan GeoParquet eller FlatGeobuf være aktuelt.

### Hvordan kobler jeg STAC-metadataen til Cloud Native-filer?

STAC (SpatioTemporal Asset Catalog) er en standard for å beskrive geodata med metadata.
Den hjelper brukere og klienter å finne filer i skyen, forstå innholdet og koble til CN-formater som COG, GeoParquet og PMTiles.

En STAC-fil (JSON) inneholder `links` og `assets` som peker direkte til dine CN-filer (COG, GeoParquet, PMTiles osv.). Klienten leser STAC-filen først og bruker så filstiene til å streame dataene.

### Hvordan visualiserer jeg COG eller PMTiles raskt i nettleser?

- COG (raster): OpenLayers ol/source/TileImage eller MapLibre GL JS med raster-dem.

- PMTiles (vektor): MapLibre GL JS + pmtiles-adapter.

### Kan jeg kombinere flere formater i ett webkart?

Ja! For eksempel: COG-bakgrunn + PMTiles-vektorlag
Effektivt for web, raskt å laste, serverless.

STAC-kataloger kan hjelpe med å holde oversikt over hvilke filer som hører sammen.

### Hva er de største fordelene med Cloud Native Geospatial?

- Raskere tilgang: Partial og parallel reads gjør store filer raskt tilgjengelige.
- Serverless / skyvennlig: Lagring i S3/Azure, ingen tunge servere.
- Standardiserte åpne formater: Støttes av QGIS, MapLibre, OpenLayers, Python.
- STAC-integrasjon: Enkel metadata, søk og kobling til CN-filer.
- Fleksibel arkitektur: Kombiner raster og vektor i samme webkart eller analysepipeline.

