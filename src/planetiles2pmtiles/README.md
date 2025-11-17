# Steps
1. Convert N5000 to geopackage
1. Use `N5000_dynamic_yaml.yml` or generate a yaml schema using `create_planetiler_yaml.py`
1. Run planetiler docker command. Check paths in yml... 
1. Run http server and test with `demo_n5000_tiles.html` 

# notes
Planetiler custom schema
* YAML schema: https://github.com/onthegomap/planetiler/tree/main/planetiler-custommap
* Overture override enabling Parquet: https://github.com/OvertureMaps/overture-tiles/blob/main/profiles/Base.java

Run a local http server with range request support
```sh
#install server
npm install -g http-server

#run in folder
http-server . --cors --gzip
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