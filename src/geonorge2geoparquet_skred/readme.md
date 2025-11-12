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
Unngå overlaps mellom Aktsomhetskartet og Skredfaresonene. Der det finnes Skredfaresonener (Definert av objekttype = Analyseområde) skal ikke aktsomhetskartet benyttes

## Getting started
- Installer avhengigheter: `pip install -r requirements.txt`
- Last ned N50-data fra Geonorge og pakk ut i `src/geoparquet`
- Åpne `main.ipynb` for stegvis konvertering og analyse

## Struktur
- `main.ipynb`: Notebook for konvertering og demo
- `requirements.txt`: Python-avhengigheter
- `utils.py`: Hjelpefunksjoner
- `img/`: Bilder og illustrasjoner