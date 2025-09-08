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
INPUT=$1
LAYER=$2 
OUTPUT=$LAYER.pmtiles

# Bygger docker image med gdal, tippecanoe og pmtiles
docker build -t $IMAGE .

# Kjører containeren
docker run --name $CONTAINER -d $IMAGE

# Kopierer data til containeren
docker cp ./data/$INPUT $CONTAINER:/app/$INPUT 

# Kjør scriptet for å konvertere til pmtiles i containeren
docker exec $CONTAINER bash gdb_to_pmtiles.sh $INPUT $LAYER $OUTPUT

# Pass på at out mappen finnes
mkdir -p out

# Kopierer pmtiles filen ut av containeren
docker cp $CONTAINER:/app/$OUTPUT ./out/$OUTPUT
