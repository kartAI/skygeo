# Hva er egentlig Cloud Native?
* Introduksojn
* motivasjon
* Problem og løsning
* Hva menes med "cloud native"? "partial reads, parallell reads
* Forholdet til andre standarder
    * OGC standarder
    * "web-standarder" (tilecache, vector tiles, geojson)
* Hva med metadata => STAC

## Formater
### Oversikt over aktuelle formater

| Format | Datatype | Primær bruk | Fordeler / Ulemper | Eksempel | “Server-alternativet” |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Cloud Optimized GeoTIFF (COG)** | Raster (2D) | Effektiv streaming av 2D-bilder (ortofoto, DEM) | **\+** Utnytter HTTP Range Requests<br>**\+** Bred støtte (Web, GDAL, QGIS, ArcGIS)<br>**\+** Bakoverkompatibel (er en gyldig GeoTIFF)<br>**\-** Ineffektiv for \>3 dimensjoner (fks tidsserier) | Streaming av flyfoto eller høydedata (DEM) direkte inn i webklienter eller GIS-klienter (QGIS/ArcGIS Pro) uten full nedlasting eller WMS-servere | OGC WMS<br>OGC WCS |
| **GeoParquet** | Vektor (Punkt, linjer, polygoner) | Storskala *analyse* av vektordata | **\+** Columnar format (raske analytiske spørringer, aggregates)<br>**\+** Høy kompresjon<br>**\+** Standard i data science-økosystemet (Spark, DuckDB, Pandas)<br>**\-** Ikke optimalisert for rask *visualisering* (FGB er ofte raskere)<br>**\-** V1.0 mangler native spatial index (Bruker bbox på row groups)<br>**\-** Ikke designet for transaksjonelle updates | Laste ned alle polygoner med “artype=myr” fra AR50 i Agder. Uten å laste ned hele datasettet eller en database/API-server | OGC API Features<br>OGC WPS<br>OGC WFS |
| **FlatGeobuf (FGB)** | Vektor (Punkt, linjer, polygoner) | Rask *streaming* og visualisering av vektordata (web/desktop) | **\+** Ekstremt rask read-ytelse<br>**\+** Innebygd spatial index (R-tree)<br>**\+** Kan streame data *progressivt* (vise features før hele filen er lastet)<br>**\-** Ikke et analytisk format (GeoParquet er bedre)<br>**\-** Støtter ikke transaksjoner eller updates<br>**\-** En geometritype per fil (fks point, line, polygon) | Hente ut geografiske data for et kartutsnitt på web uten behov for en dedikert feature server. | OGC API Features<br>OGC WFS |
| **PMTiles** | Vector Tiles / Raster Tiles | "Server-løs" distribusjon av vector tiles for web-kart | **\+** Enkeltfil-format<br>**\+** Krever ingen server-applikasjon (kan hostes på statisk object storage som S3/Blob)<br>**\+** Billig og skalerbart<br>**\-** Read-only; data må forhåndsprosesseres<br>**\-** Ikke et analyseformat. Data er optimalisert for visualisering i MVT/PBF.<br>**\-** Begrenset til Mercator-projeksjon for de fleste web-biblioteker. | Publisere Kartverkets "Norgeskart" (f.eks. Topo-data) som et interaktivt bakgrunnskart for en web-app, hostet direkte fra object storage uten en tile-server. | OGC API Tiles<br>OGC WMTS |
| **Cloud Optimized Point Cloud (COPC)** | Punktsky (LiDAR) | Streaming og analyse av massive punktsky-datasett | **\+** Basert på LAZ (god kompresjon)<br>**\+** Octree-struktur gir effektiv romlig indeksering og LOD (Level of Detail)<br>**\+** Enkeltfil-format<br>**\-** Nyere format, støtte er under utvikling (men god i PDAL) | Visualisering og analyse av Kartverkets nasjonale detaljerte høydedata (LiDAR-punktsky) i en web-viewer eller QGIS uten å laste ned terabytes med LAZ-filer. | OGC I3S<br>OGC API 3D GeoVolumes |
| **Zarr** | N-dimensjonal Array (Data Cube) | Håndtering av multidimensjonale vitenskapelige data | **\+** Håndterer N-dimensjoner (x, y, tid, dybde)<br>**\+** Chunked lagring, perfekt for parallellprosessering (Dask, xarray)<br>**\+** Fleksible codecs (kompresjon)<br>**\-** Mer komplekst. Støtte i tradisjonelt GIS er mindre modent enn COG. | Lagring og analyse av tidsserier med meteorologiske data | OGC WCS<br>OGC API Coverage |


## Dypdykk i formater

### Cloud Optimized GeoTIFF (COG)

### GeoParquet

### FlatGeobuf (FGB)

### PMTiles

## Referanser
