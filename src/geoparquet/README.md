# GeoParquet

## Bakgrunn
GeoParquet er en standard for lagring av geografisk informasjon på toppen av Parquet-formatet. Parquet er en 
kolonnebasert format for lagring av data, og er langt på vei førstevalget for skybaserte plattformer og store 
datamengder.

Både Kartverket og Kystverket er blant norske offentlige aktører som utforsker formatet for å enklere distribuere 
data uten å gå via bestillingsskjema eller store nedlastinger av enkeltfiler.


## Kort om Parquet
Kolonnebasert vil si at data lagres kolonnevis i stedet for radvis, som i tradisjonelle databaser. Dette gir store 
fordeler ved lesing, fordi applikasjonene kan lese bare de kolonner de trenger. Tenk at du skal lese ut tre av åtte 
kolonner fra en CSV-fil - applikasjonen din (Python, Excel, you name it) må lese linje-for-linje for så å filtrere 
ut den faktiske dataen. Med Parquet kan man spesifikt velge kolonner ved innlesing, og disse kan leses direkte 
fra filen.  Filen inneholder metadata på flere nivåer: en footer på slutten av filen med skjemainformasjon 
og plasseringen til alle radgrupper, samt statistikk per kolonneblokk som min/max-verdier, null-count og antall 
_unike_ verdier. Dette gjør at spørringsmotorer kan gjøre _predicate pushdown_ – de leser footeren først, sjekker 
statistikken, og skipper hele radgrupper dersom filteret ikke matcher. For eksempel: spør du etter lat > 70.0 
og en radgruppe har max(lat) = 68.5, kan hele blokken hoppes over uten å lese selve dataene.

Plattformer som Databricks og Snowflake har Parquet som sitt interne lagringsformat, men med hver sin tilnærming. 
Databricks utvikler Delta Lake (https://delta.io/), mens Snowflake har støttet utvikling av Iceberg (https://iceberg.apache.org/) - begge disse formatene er bygget på Parquet.

## GeoParquet

### Geoparquet 1.1.0
GeoParquet 1.1.0 utvider Parquet-formatet med ekstra metadata for å gjøre romlige spørringer mer effektive. Dette 
skjer i dag med en `geo`-kolonne som inneholder informasjon om hvilke kolonner som inneholder geometry, samt 
informasjon om hvilken CRS, hvilke geometri-typer (`LINESTRING`, `POLYGON`, `MULTIPOLYGON` etc) er å finne.
Les mer på informasjonssiden: https://geoparquet.org/releases/v1.1.0/

### Geoparquet 2.0.0
I 2025 ble `GEOMETRY`og `GEOGRAPHY`-typer introdusert i 
[Parquet-spesifikasjonen ](https://github.com/apache/parquet-format/pull/240). Nå kan geometri-typer lagres som 
førsteklasses kolonner fremfor å måtte kodes frem og tilbake mellom `BINARY`eller `STRING`. Det aller gjeveste er at 
kolonnestatistikk blir generert på lik linje med andre typer. For hver kolonne med geometri-typen `GEOMETRY` eller 
`GEOGRAPHY` vil det blir generert `bbox` som inneholder en struct med `minx`, `miny`, 
`maxx` og `maxy`-verdier. Dette kan brukes av `ST_INTERSECT` og `ST_WITHIN` til å filtrere ut data med fire 
koordinatpar når man leser ut av filen, og kjøre en finere filtrering etterpå (ikke ulikt PostGIS). I tillegg 
inneholder kolonne-dataen en liste med unike WKT-typer (`POINT`, `LINESTRING` etc).


## GeoParquet-støtte per verktøy (UNDER UTVIKLING ⚠️)

| Verktøy           | Read | Write | 1.1.0 | 2.0 | `GEOMETRY` | Merknad                                                                                                            |
|-------------------|:----:|:-----:|:-----:|:---:|:----------:|--------------------------------------------------------------------------------------------------------------------|
| **GeoPandas**     | ✅   | ✅    | ✅    |  ❌  |       ❌     | `read_parquet()` / `to_parquet()`.                                                                                 |
| **DuckDB**        | ✅   | ✅    | ⚠️    |  ❌  |     ❌       | Native fra v1.1.0 med spatial extension.                                                                           |
| **Apache Sedona** | ✅   | ✅    | ✅    |  ❌  |   ❌         | `format("geoparquet")` fra v1.3.0. Støtter covering/bbox fra v1.6.1. Deaktiver Photon på Databricks.               |
| **Sedona DB**     |   ✅   |  ✅     |       |     |            |                                                                                                                    |
| **Databricks**    | ✅   | ✅    | ✅    |  ❌  |       ✅     | |
| **QGIS**          | ✅   | ⚠️    | ✅    |  ❌  |            |                                                       | |
| **GDAL/OGR**      | ✅   | ✅    | ✅    |  ❌  |     ✅      | Stabilt fra v3.8+.                                                                                                 |
| **Polars**        | ⚠️   | ⚠️    | ❌    |  ❌  |            | Leser Parquet, men begrenset geo-støtte. <br/>Lovende bibliotek: [Polars ST](https://github.com/oreilles/polars-st) |
