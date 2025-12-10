# GeoNorge CSW til STAC Catalog – Eksperiment

Dette prosjektet demonstrerer hvordan metadatakatalogen fra GeoNorge (CSW) kan konverteres til en STAC-katalog, både som JSON og GeoParquet. Målet er å gjøre norske geodata enklere tilgjengelig og mer brukervennlig for både mennesker og maskiner.

## Om STAC-standarden

STAC (SpatioTemporal Asset Catalog) er en åpen standard for beskrivelse av geodata. Den gir:
- **Enklere bruk:** Standardisert struktur gjør det lett å søke, filtrere og hente data.
- **Maskinlesbarhet:** STAC er optimalisert for automatiserte prosesser, LLMs og MCP.
- **Interoperabilitet:** Kan brukes med moderne verktøy og API-er, som STAC Browser

Les mer om STAC:
* https://www.ogc.org/announcement/ogc-announces-publication-of-the-spatiotemporal-asset-catalog-community-standards/
* https://stacspec.org/
* https://stacindex.org/
* https://radiantearth.github.io/stac-browser/
* https://developmentseed.org/blog/2025-05-07-stac-geoparquet/

## Resultater

- [Demo av enkelt datasett](https://radiantearth.github.io/stac-browser/#/external/kartaistorage.blob.core.windows.net/skygeo/geonorge_stac_experiments/publisher_collection/stac_output_dynamic/collection-kartverket/006fa78d-b067-48f1-ba57-f91bd2c4af45/006fa78d-b067-48f1-ba57-f91bd2c4af45.json?.asset=asset-asset_0)
- [Demo av hele katalogen](https://radiantearth.github.io/stac-browser/#/external/kartaistorage.blob.core.windows.net/skygeo/geonorge_stac_experiments/publisher_collection/stac_output_dynamic/catalog.json)
- [STAC katalog i JSON](https://kartaistorage.blob.core.windows.net/skygeo/geonorge_stac_experiments/publisher_collection/stac_output_dynamic/catalog.json)
- [STAC katalog i GeoParquet](https://kartaistorage.blob.core.windows.net/skygeo/geonorge_stac_experiments/publisher_collection/geonorge_stac.parquet)

## Forbedringsforslag

- Mer dynamisk mapping mellom CSW og STAC
- Bedre håndtering av aggregeringer mellom collections og datasett
- Automatisk sjekk av metadata, f.eks. døde lenker
- STAC API-demo med docker-container (f.eks. https://github.com/stac-utils/stac-fastapi-geoparquet)

## Teknisk gjennomgang

Notebooken `iso2stac_experiment.ipynb` viser hele prosessen:
- Henter metadata fra GeoNorge CSW med OWSLib
- Mapper metadata til STAC-format med dynamisk utvidelse av egenskaper
- Oppretter STAC-katalog og collections basert på publisher
- Eksporterer katalogen til både JSON og GeoParquet
- Viser hvordan resultatene kan visualiseres og analyseres

## Viktige notater

- Sjekk at CRS-konvertering for bounding box (bbox) håndteres korrekt, spesielt akse-rekkefølge.
- Verifiser at alle assets (ressurser) blir med i STAC-elementene.
- Vurder om normaliseringen av publisher-navn er robust nok for alle varianter.

---

For mer informasjon, se notebooken og test gjerne demoene i STAC Browser.
