# pgstac

Dette prosjektet er en eksperimentering for å bli bedre kjent med **pgstac** og hvordan
den brukes. Målet er å katalogisere geospatiale filer som ligger i et lokalt kjørende
S3-lager, og gjøre dem søkbare og browsbare som en STAC-katalog. I stedet for å skrive
katalogen som statiske JSON-filer lagrer vi alt i Postgres med pgstac, og serverer det med
en ekte STAC API. Så scanner vi S3-lageret for filer, leser ut metadata fra hver fil, og
fyller katalogen.

Tanken er: en mappe i S3 = en STAC Collection. Du peker scanneren mot en bucket og et
prefix, og den bygger opp en collection med ett item per fil. Kjører du den på nytt holder
den katalogen i synk med mappa (legger til nye filer, fjerner de som er borte).

For å kjøre dette trenger du en Postgres-database med PostGIS og pgstac (`db`), en STAC API
oppå den (`api`), og en viewer (`viewer`) for å browse i nettleser. Scanneren (`scanner`)
kjøres bare når du skal fylle eller oppdatere katalogen. Se [Hva vi har satt opp](#hva-vi-har-satt-opp)
for detaljer.

### Hvordan dette skiller seg fra en statisk JSON-katalog på S3

En enklere variant er å skrive STAC-katalogen som statiske JSON-filer rett på S3. Det
krever ingen database og er billig å hoste, men du får ingen søk eller API ut av det, bare
filer en klient må laste ned og bla gjennom selv.

pgstac-oppsettet ser ut til å gi flere fordeler. Du får søk og et ekte STAC API rett ut av
boksen, så klienter (STAC Browser, QGIS, egne script) kan filtrere på tid, område og
properties uten å laste ned hele katalogen. Til gjengjeld krever det at du har en
PostgreSQL-database kjørende som brukerne/klientene har tilgang til. Men når den først er
oppe, gjør den jobben kjempebra.

## Hva vi har satt opp

Fire containere, der de tre første kjører hele tiden og scanneren kjøres ved behov:

| Tjeneste | Hva | Levetid |
|----------|-----|---------|
| `db` | PostgreSQL 17 + PostGIS 3 + pgstac (`ghcr.io/stac-utils/pgstac:v0.9.11`) | kjører fast |
| `api` | STAC API (`ghcr.io/stac-utils/stac-fastapi-pgstac:6.2.1`) | kjører fast |
| `viewer` | STAC Browser + en `/s3`-proxy som signerer asset-kall | kjører fast |
| `scanner` | scanner en S3-mappe og laster en Collection inn i pgstac | **ved behov** |

- **db** er der hele katalogen bor. pgstac legger til sitt eget skjema (collections, items,
  søk) oppå PostGIS. Databasen restartes aldri når vi oppdaterer katalogen.
- **api** er stac-fastapi-pgstac. STAC Browser kan ikke snakke med Postgres direkte, så
  denne serverer katalogen som JSON over HTTP (med CORS på, så nettleseren kan kalle den).
- **viewer** serverer STAC Browser (SPA-en) og har i tillegg en `/s3`-proxy. Bucketen er
  privat, så nettleseren kan ikke hente filene direkte. Proxyen signerer kallene med SigV4
  og støtter Range-requests, slik at f.eks. PMTiles kan leses bit for bit.
- **scanner** er den vi bygger selv. Den lister opp filene i en S3-mappe, leser metadata,
  bygger STAC-items og laster dem rett inn i pgstac med `pypgstac`.

## Slik henger det sammen

Overordnet er det to veier: en scan-vei som fyller databasen on-demand, og en serve-vei der
katalogen leses ut. Scanneren bygger STAC-items og gjør upsert + prune mot pgstac. API-et
serverer collections og items, og vieweren henter fil-bytene gjennom `/s3`-proxyen med
signerte range-reads.

<img src="screenshots/pgstac%20%E2%80%94%20scan%20%26%20view%20workflow.jpg" width="420" alt="Flytdiagram: scan-vei og serve-vei">

Mer detaljert med containere, porter og `.env`: db, api og viewer er den faste stacken på
det delte `pgstac`-nettverket, scanneren kjøres on-demand, og alle deler samme `.env`.
Katalog-JSON går rett fra nettleser til API (CORS), mens fil-bytene går via viewerens
`/s3`-proxy som signerer mot privat S3.

<img src="screenshots/pgstac%20%E2%80%94%20scan%20%26%20view%20workflow2.jpg" width="850" alt="Arkitekturdiagram med containere, porter, nettverk og .env">

Tjenestene i diagrammene er forklart i [Hva vi har satt opp](#hva-vi-har-satt-opp).

## Hvordan scanningen fungerer

Scanneren tar en bucket + prefix og gjør dette per kjøring:

1. Lister opp filene under prefixet (boto3).
2. For hver fil leser den ut metadata. Den laster ikke ned hele fila der det går an, den
   leser bare header/footer (PMTiles-header, parquet-footer, COG-header) for å holde det
   billig.
3. Bygger ett STAC-item per fil, med asset-href som peker på viewerens `/s3`-proxy
   (`<ASSET_BASE_URL>/s3/<bucket>/<key>`).
4. Upserter collection + alle items i pgstac med `pypgstac`.
5. Pruner: sammenligner item-id-ene i scanet mot de som ligger i databasen, og sletter de
   som ikke lenger finnes i mappa. (`--no-prune` skrur det av, `--drop` tømmer collectionen
   først.)

Resultatet er idempotent. Kjører du samme `--collection-id` på nytt speiler collectionen
det som faktisk ligger i S3-mappa akkurat nå. Støttede filtyper: COG/GeoTIFF, GeoJSON,
GeoParquet og PMTiles.

Slik ser katalogen ut i STAC Browser, med en collection per scannet mappe:

<img src="screenshots/Screenshot%202026-06-16%20at%2010.17.03.png" width="700" alt="STAC Browser katalogoversikt med to collections">

Inni en collection ligger items med bbox-kart og liste:

<img src="screenshots/Screenshot%202026-06-16%20at%2010.17.49.png" width="700" alt="Collection-visning med bbox-kart og item-liste">

### Slik ser det ut i databasen

Alt dette ligger i Postgres. pgstac lager sitt eget skjema med blant annet `collections`-
og `items`-tabellene. Hver scannet mappe blir en rad i `collections`, og hver fil blir en
rad i `items` (med geometri, collection-referanse og datetime). Du trenger ikke å gå inn i
databasen for å bruke systemet, men det er greit å se hvor dataene faktisk havner:

<img src="screenshots/Screenshot%202026-06-16%20at%2010.36.24.png" width="700" alt="pgstac-skjemaet i databasen med collections-tabellen">

<img src="screenshots/Screenshot%202026-06-16%20at%2010.36.43.png" width="700" alt="items-tabellen med geometri, collection og datetime per fil">

## Ekstra metadata per filtype

Utover det vanlige (bbox, projeksjon, datetime) leser vi ut felter som er nyttige å se i
browseren. Alle items får `file:size` (filstørrelse i bytes). Resten avhenger av filtype.
Der det finnes en standard STAC-extension bruker vi den, ellers et eget namespace.

**GeoParquet / GeoJSON**
- `table:columns` (kolonnenavn + datatype) og `table:row_count` (antall rader)
- `vector:geometry_types`, f.eks. `LineString Z`, `Polygon`
- `vector:encoding`, f.eks. `WKB`
- `proj:epsg` utledet fra geo-metadataen
- noen `proc:sample`-rader som forhåndsvisning av dataene

For parquet leses dette fra footeren, så vi slipper å lese hele fila.

<img src="screenshots/Screenshot%202026-06-16%20at%2010.18.30.png" width="700" alt="GeoParquet-item med kolonner, radantall, geometritype og sample-rader">

**PMTiles**
- `pmtiles:tile_type` (vector/raster), min/max zoom, center
- `pmtiles:name` og `pmtiles:vector_layers` (lagene + feltskjemaet i hvert lag)
- `pmtiles:clustered`, `pmtiles:tile_compression`
- teller for tiles (`pmtiles:addressed_tiles_count` osv.). Merk at dette er antall tiles,
  ikke antall features (features dupliseres på tvers av zoomnivåer).

Alt dette leses gratis fra PMTiles-headeren.

<img src="screenshots/Screenshot%202026-06-16%20at%2010.19.15.png" width="700" alt="PMTiles-item med navn, zoom, tile type og vector layers">

**COG / GeoTIFF**
- bånd, dtype, nodata og statistikk (via rio-stac)
- `cog:compression`, `cog:blocksize`, `cog:overview_count`, `cog:predictor` fra
  COG-headeren

## MapLibre-preview for PMTiles

For PMTiles-items får du en egen "Data preview"-fane i vieweren som rendrer tile-ene
direkte med MapLibre. Den henter PMTiles via `/s3`-proxyen (med Range, så den laster bare
de tile-ene den trenger) og tegner vektorlagene oppå et basiskart. Da ser du faktisk
innholdet i fila uten å laste den ned.

<img src="screenshots/Screenshot%202026-06-16%20at%2010.18.57.png" width="700" alt="MapLibre-preview som rendrer PMTiles-vektorlag">

Basiskart-stilen settes med `BASEMAP_STYLE_URL` (default er MapLibre sin demo-stil, kan
byttes til f.eks. Norkart-stilen).

## Bruke katalogen i QGIS

Siden `api` er en helt vanlig STAC API kan du også koble deg på fra QGIS med STAC
API Browser-pluginen. Legg inn API-URL-en som en STAC-tilkobling, så dukker collections og
items opp i Browser-panelet og kan lastes rett inn i kartet:

<img src="screenshots/Screenshot%202026-06-16%20at%2010.49.35.png" width="700" alt="QGIS Browser med STAC-tilkobling som viser collections og items">

Hvert item viser metadataene vi har lagt på, inkludert projeksjon, bbox og extensions:

<img src="screenshots/Screenshot%202026-06-16%20at%2010.49.51.png" width="500" alt="STAC Object Details-dialogen i QGIS for et item">

## Kom i gang lokalt

Du trenger Docker. Så er det tre steg: lag `.env`, lag det delte nettverket, og start
stacken.

```sh
cp example.env .env            # fyll inn verdiene (se under)
docker network create pgstac   # engangs, delt nettverk som alle tjenestene henger på
docker compose --env-file .env up -d   # starter db + api + viewer (ikke scanner)
```

Sjekk at det lever:

```sh
docker compose ps
curl -s localhost:8082/collections | jq .   # STAC API (tom til en scan har kjørt)
curl -s localhost:8080/healthz              # viewer
open http://localhost:8080                  # STAC Browser
```

Nå kjører db, api og viewer. Katalogen er tom til du har kjørt en scan (se neste seksjon).

### Hva du må fylle ut i `.env`

`example.env` har alle variablene med kommentarer. De som står til `changeme` må du sette
selv, resten har fornuftige defaults for lokal kjøring og kan stå som de er.

| Variabel | Må settes? | Hva det er |
|----------|------------|------------|
| `POSTGRES_USER` | nei | DB-bruker (default `pgstac`) |
| `POSTGRES_PASSWORD` | **ja** | DB-passord, bytt fra `changeme` |
| `POSTGRES_DB` | nei | DB-navn (default `postgis`) |
| `DB_HOST_PORT` | nei | host-port for Postgres (default `5439`) |
| `API_HOST_PORT` | nei | host-port for STAC API (default `8082`) |
| `CORS_ORIGINS` | nei | hvilke origins som får kalle API-et fra nettleser. Må inkludere viewer-origin (default `http://localhost:8080`) |
| `S3_ENDPOINT` | **ja** | S3-host uten scheme, f.eks. `s3.example.no` (https legges på internt) |
| `S3_ACCESS_KEY` | **ja** | S3-nøkkel |
| `S3_SECRET_KEY` | **ja** | S3-secret |
| `S3_REGION` | nei | signeringsregion (default `us-east-1`) |
| `ASSET_BASE_URL` | nei | base for asset-href som lagres i DB, `<ASSET_BASE_URL>/s3/<bucket>/<key>`. Må matche hvordan nettleseren når vieweren (default `http://localhost:8080`) |
| `STAC_API_URL` | nei | hvordan nettleseren når API-et (default `http://localhost:8082`). Må stå i `CORS_ORIGINS` |
| `VIEWER_HOST_PORT` | nei | host-port for vieweren (default `8080`) |
| `STAC_BROWSER_VERSION` | nei | STAC Browser-versjon som bakes inn (default `v4.0.1`) |
| `BASEMAP_STYLE_URL` | nei | MapLibre basiskart-stil for preview-fanen (default MapLibre sin demo-stil) |

S3-feltene brukes både av scanneren (lese data) og vieweren (signere asset-kall).
Scanneren utleder DB-koblingen fra `POSTGRES_*`, så den holder seg i synk automatisk. Sett
`PGSTAC_DSN` bare hvis du vil peke scanneren på en helt annen database.

## Sette opp en scan med scanner-containeren

Når stacken kjører fyller du katalogen ved å kjøre scanner-containeren mot en S3-mappe.
Den kjøres on-demand (`run --rm`) mot den allerede oppe-kjørende stacken, så databasen
restartes aldri. S3-credentials og DB-kobling kommer fra `.env`, resten er CLI-flagg.

Den raskeste måten er å peke rett på en bucket + prefix:

```sh
docker compose -f scanner/docker-compose.yml --env-file .env run --rm scanner \
  --bucket my-bucket --prefix area/sub/ \
  --collection-id area-sub --collection-title "Area Sub"
```

- `--bucket` er bucket-navnet (uten skråstrek)
- `--prefix` er mappa inni bucketen som blir til én collection
- `--collection-id` er en stabil id. Kjør samme id igjen for å re-scanne (upsert + prune)
- `--collection-title` er tittelen som vises i browseren

Nyttige flagg: `--no-recursive` (bare toppnivået), `--no-prune` (behold items som er borte
fra S3), `--drop` (tøm collectionen først), `--datetime` (tving én dato på alle items),
`--fail-on-error`. `--help` viser alle.

### Faste scan-jobber i en fil

Vil du lagre oppsettet for en scan i stedet for å skrive flagg hver gang, bruk en
per-collection-fil (én fil = én Collection). Kopier `scanner/collection-nseries.yml` til
`scanner/collection-<navn>.yml`, gi servicen et eget navn, og fyll inn `--bucket`,
`--prefix`, `--collection-id` og `--collection-title` i `command`-lista. Secrets og DB
holdes fortsatt i `.env`, aldri i denne fila. Så kjører du uten CLI-args:

```sh
docker compose -f scanner/collection-<navn>.yml --env-file .env run --rm <service>
```

Vil du kjøre flere på en gang, legg hver fil inn i
`scanner/docker-compose-all-collections.yml` (én `include:`-linje per fil) og:

```sh
docker compose -f scanner/docker-compose-all-collections.yml --env-file .env up --abort-on-container-exit
```

Kjører du samme `--collection-id` på nytt **upserter** den fant-items og **pruner** items
som ikke lenger ligger i mappa. Refresh så browseren, og den nye collectionen dukker opp
under API-roten.

## Porter

- Viewer / STAC Browser: `localhost:${VIEWER_HOST_PORT:-8080}`
- STAC API: `localhost:${API_HOST_PORT:-8082}`
- Postgres: `localhost:${DB_HOST_PORT:-5439}` (container-port 5432)

## Kjøre tjenestene hver for seg

`pgstac`-nettverket er delt og eksternt, så hver tjeneste kan kjøre alene, f.eks.
`docker compose -f db/docker-compose.yml --env-file .env up -d`. Scanneren når `db` over
det nettverket uten å restarte noe.
