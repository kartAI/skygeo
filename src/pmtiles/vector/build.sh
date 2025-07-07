#!/bin/bash

# Script for å konvertere .gdb vektor til PMTiles

# Avslutt scriptet umiddelbart hvis noen kommandoer feiler
set -e 

clean_exit(){
    # Stop containeren
    docker stop $CONTAINER

    # Slett containeren
    docker rm $CONTAINER
}
trap clean_exit EXIT

# Set script variabler
IMAGE=pmtiles
CONTAINER=pmtiles-converter
INPUT=Basisdata_42_Agder_25832_N50Kartdata_FGDB.gdb
# INPUT=Basisdata_0000_Norge_25833_N50Kartdata_FGDB.gdb 
LAYER=N50_Samferdsel_senterlinje 
OUTPUT=$INPUT.pmtiles

# Bygger docker image med gdal, tippecanoe og pmtiles
docker build -t $IMAGE .

# Kjører containeren
docker run --name $CONTAINER -d $IMAGE

# Kopierer data til containeren
docker cp ./data/$INPUT $CONTAINER:/app/$INPUT 

# Kjør scriptet for å konvertere til pmtiles i containeren
# docker exec $CONTAINER bash gdb_to_pmtiles.sh $INPUT $LAYER $OUTPUT
docker exec $CONTAINER bash all_layers_gdb_to_pmtiles.sh $INPUT $OUTPUT

# Pass på at out mappen finnes
mkdir -p out

# Kopierer pmtiles filen ut av containeren
docker cp $CONTAINER:/app/$OUTPUT ./out/$OUTPUT
