# GeoNorge2GeoParquet

##Bakgrunn
GeoNorges nedlastingsapi tilbyr alle datasett på ett eller flere av formatene gml,sosi,shape,FGDB og postgis. Api'et framstår som noe knotete i bruk, og kunne vært enklere å bruker
for personer uten GIS-kunnskap med et standardisert endepunkt som gir et standardisertformat, område og koordinatsystem uten en rekke valgmuligheter.

I tilleg krever mange av datasettene i GeoNorge grundig kjennskap til datastrukturen for å kunne gi nyttig informasjon. Vi har en hypotese (inspirert av Miljødirektoratets innføring av KU-verdi) om at det går an å standardisere
'alvorlighetsgraden' av et objekt i et temadatasett på tvers av alle datasett, f.esk en skal fra 1-5 der 1 er minst og 5 er mest alvorlig. Flere av datasettene har også avhengigheter mellom hverandre, uten at dette er enkelt å avlede
eller går fram av dataene direkte. For å finne ut av om et område f.eks er utsatt for snøskred må man sjekke to uavhengige datasett med ulik datamodell, og vurdere disse mot hverandre. Vi har derfor laget et sammenstil datasett som gjør denne jobben,
og som forsøker å vise alvorlighetsgrad med en kvantifisert verdi fra 1-5.      

## Grunnlag
GeoNorge API: 
Skredfaresoner:https://kartkatalog.geonorge.no/api/getdata/b2d5aaf8-79ac-40f3-9cd6-fdc30bc42ea1
Aktsomhetskart for snøskred https://kartkatalog.geonorge.no/api/getdata/b2d5aaf8-79ac-40f3-9cd6-fdc30bc42ea1


## Formål
Unngå overlaps mellom Aktsomhetskartet og Skredfaresonene. Der det finnes Skredfaresonener (Definert av objekttype = Analyseområde) skal ikke aktsomhetskartet benyttes. Dette er et automatisk generert datasett med lavere
beregningskavlitet enn skredfaresonene.

## Getting started
OBS: Hardkodede stier for destinasjon og lesing i steg 2, dette rakk vi ikke å fikse :-)
- Kjør fila cli_skred_workshop.py - oppgi uuid i påkrevd parameter --dataset-uuid. Kjør fila en gang for hvert datasett, Se 'grunnlag' over for verdi. Filene lagres til geoparquet(optimized, tilesize 10000)
- Kjør så fila skred2duckdb.py. Begge filene leses direkte fra parquet gjennom duckdb, som utfører overlay mellom Analyseområder og alle data i aktsomhetskartet. Overlayspørringen kjører uten geografisk index i duckdb og tar ca 20 sekunder. Selve overlayqueryet ser slik ut:

## Overlay query
```sql
WITH analyseomrade_union AS (
                SELECT ST_Union_Agg(geometry) as clip_geom
                FROM read_parquet('{skredfaresoner_path}')
                WHERE source_layer = 'Analyseområde'
            ),
            clipped_aktsomhet AS (
                SELECT 
                    {aktsom_non_geom_str},
                    CASE 
                        WHEN ST_Intersects(a.geometry, ao.clip_geom) 
                        THEN ST_Difference(a.geometry, ao.clip_geom)
                        ELSE a.geometry
                    END as clipped_geometry
                FROM read_parquet('{aktsomhetskart_path}') a
                CROSS JOIN analyseomrade_union ao
            )
            SELECT 
                NULL as skredStatistikkSannsynlighet,
                source_layer,
                clipped_geometry as geometry,
                skogeffekt,
                sikkerhetsklasse,
                CASE 
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 1
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 2
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 3
                    ELSE NULL
                END as risk_factor,
                CASE 
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S3' THEN 'Automatisk beregnet'
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Ja' THEN 'Automatisk beregnet med skogeffekt'
                    WHEN source_layer = 'PotensieltSkredfareOmr' AND sikkerhetsklasse = 'S2' AND skogeffekt = 'Nei' THEN 'Automatisk beregnet uten skogeffekt'
                    ELSE NULL
                END as data_quality,
                'aktsomhetskart_clipped' as data_source
            FROM clipped_aktsomhet
            WHERE clipped_geometry IS NOT NULL 
            AND ST_Area(clipped_geometry) > 0
            ```



Alle filer leses og skrives lokalt: /temp_debug/workshop

## Struktur

- `img/`: Bilder og illustrasjoner
