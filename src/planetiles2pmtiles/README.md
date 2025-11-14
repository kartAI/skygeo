

# notes
n5000 - 4 layers - geopackage
```
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest generate-custom --schema=/data/n5000_dynamic.yaml --output=/data/n5000_dynamic.pmtiles
```

test - monaco
```
docker run -e JAVA_TOOL_OPTIONS="-Xmx1g" -v "${PWD}\data:/data" ghcr.io/onthegomap/planetiler:latest --water-polygons-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/water-polygons-split-3857.zip --natural-earth-url=https://github.com/onthegomap/planetiler/raw/main/planetiler-core/src/test/resources/natural_earth_vector.sqlite.zip --osm-path=monaco-251112.osm.pbf --download --output=/data/monaco.pmtiles
```

windows - ogr2ogr docker
```
docker run --rm -v "${PWD}:/data" ghcr.io/osgeo/gdal:alpine-small-latest `
ogr2ogr -f GPKG /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gpkg /data/Basisdata_0000_Norge_25833_N5000Kartdata_FGDB.gdb `
-lco SPATIAL_INDEX=YES -lco GEOMETRY_NAME=geom -progress -skipfailures
```