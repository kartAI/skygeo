# Planetiler-based GeoPackage to PMTiles converter
# Multi-threaded alternative to the tippecanoe pipeline
#
# Build:
#   docker build -f Dockerfile -t gpkg-planetiler .
# docker run --rm -it -v "${PWD}:/data" gpkg-planetiler
# java -Xmx4g -XX:+UseG1GC -XX:+ParallelRefProcEnabled -jar /app/planetiler.jar n100.yml --output=n100.pmtiles

FROM eclipse-temurin:21-jre-jammy

# Install GDAL for ogr2ogr (preprocessing reprojection)
RUN apt-get update && apt-get install -y --no-install-recommends gdal-bin && rm -rf /var/lib/apt/lists/*

# Download latest Planetiler release
ADD https://github.com/onthegomap/planetiler/releases/latest/download/planetiler.jar /app/planetiler.jar

WORKDIR /data



ENTRYPOINT ["/bin/bash"]

