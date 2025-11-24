# Vector tiles med PMTiles fra Kartverket sin N-serie-kart

Dette prosjektet konverterer norske kartdata (N5000/N250) til PMTiles-format ved hjelp av Planetiler og Docker. Prosessen innebærer konvertering fra FGDB til GeoPackage, generering av YAML-schema, og til slutt opprettelse av PMTiles.

## Fungerende eksempler

Du kan teste PMTiles-demo direkte i nettleseren via GitHub Pages:

- [Hovedkart-demo](https://kartai.github.io/skygeo/pmtiles_bakgrunnskart/)
- [N250-demo](https://kartai.github.io/skygeo/pmtiles_bakgrunnskart/n250/)

Disse sidene viser interaktivt kart med PMTiles uten behov for egen server.

## Forutsetninger
- Docker installert
- Node.js installert (for enkel HTTP-server)
- Kildedata: FGDB (File Geodatabase)

## Arbeidsflyt

### 1. Konverter FGDB til GeoPackage
Bruk GDAL Docker-image for å konvertere FGDB til GeoPackage:

**N5000 til GeoPackage:**
```powershell
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:alpine-small-latest `
ogr2ogr -f GPKG /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gpkg /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress -skipfailures
```

**N250 til GeoPackage:**
```powershell
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:ubuntu-full-latest `
ogr2ogr -gt 65536 -f GPKG /data/Basisdata_0000_Norge_25833_N250Kartdata.gpkg /data/Basisdata_0000_Norge_25833_N250Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress
```

### 2. Generer YAML-schema
Du kan bruke eksisterende YAML (f.eks. `N5000_dynamic_yaml.yml`) eller generere en ny med:
```powershell
python create_planetiler_yaml.py <geopackage_path> <output_yaml_path>
```

### 3. Generer PMTiles med Planetiler
Eksempel for N5000:
```powershell
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest generate-custom --schema=/data/n5000_dynamic.yaml --output=/data/n5000_dynamic.pmtiles
```
Eksempel for N250:
```powershell
docker run -e JAVA_TOOL_OPTIONS="-Xmx5g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest generate-custom --schema=/data/n250.yml --output=/data/n250.pmtiles
```

### 4. Test PMTiles med lokal HTTP-server
Installer og start server med støtte for range requests:
```powershell
npm install -g http-server
http-server . --cors --gzip
```
Test med f.eks. `demo_n5000_tiles.html`.

---




## Ekstra eksempler og tips


#### Parquet-konvertering
For Parquet-støtte:
```powershell
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:ubuntu-full-latest `
ogr2ogr -f Parquet /data/parquet_out /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gdb `
-lco GEOMETRY_NAME=geom -progress -skipfailures
```

#### Test med Monaco-data
```powershell
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest --water-polygons-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/water-polygons-split-3857.zip --natural-earth-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/natural_earth_vector.sqlite.zip --osm-path=monaco-251112.osm.pbf --download --output=/data/monaco.pmtiles
```

#### Konverter N250 med høy ytelse (uten skipfailures)
```powershell
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:ubuntu-full-latest `
ogr2ogr -gt 65536 -f GPKG /data/Basisdata_0000_Norge_25833_N250Kartdata.gpkg /data/Basisdata_0000_Norge_25833_N250Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress
```

---

## Nyttige lenker
- [Planetiler custom schema](https://github.com/onthegomap/planetiler/tree/main/planetiler-custommap)
- [Overture Parquet override](https://github.com/OvertureMaps/overture-tiles/blob/main/profiles/Base.java)

---

## Feilsøking
- Sjekk at stier i YAML-filer stemmer med filplassering.
- Bruk `-skipfailures` for å ignorere feil i GDAL-konvertering.
- For store datasett, øk minne med `JAVA_TOOL_OPTIONS`.
```sh
docker run -e JAVA_TOOL_OPTIONS="-Xmx5g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest generate-custom --schema=/data/n250.yml --output=/data/n250.pmtiles
```

n5000 - 4 layers - geopackage
* Move the geopackage to the /sources folder in the PWD. The geopackage is referenced from the yaml file
```sh
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest generate-custom --schema=/data/n5000_dynamic.yaml --output=/data/n5000_dynamic.pmtiles
```

test - monaco
```sh
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest --water-polygons-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/water-polygons-split-3857.zip --natural-earth-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/natural_earth_vector.sqlite.zip --osm-path=monaco-251112.osm.pbf --download --output=/data/monaco.pmtiles
```

windows - ogr2ogr docker
```sh
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:alpine-small-latest `
ogr2ogr -f GPKG /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gpkg /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress -skipfailures
```

windows - ogr2ogr docker that supports Parquet
```sh
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:ubuntu-full-latest `
ogr2ogr -f Parquet /data/parquet_out /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gdb `
-lco GEOMETRY_NAME=geom -progress -skipfailures
```

Convert to geopackage with high performance - but no skipfailures
```sh
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:ubuntu-full-latest `
ogr2ogr -gt 65536 -f GPKG /data/Basisdata_0000_Norge_25833_N250Kartdata.gpkg /data/Basisdata_0000_Norge_25833_N250Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress
```