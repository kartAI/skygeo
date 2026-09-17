# GDAL official base — system GDAL/GEOS/PROJ for rio-stac + geopandas stack.
# TODO: pin to an explicit version tag (e.g. ubuntu-small-3.10.3) once confirmed.
FROM ghcr.io/osgeo/gdal:ubuntu-small-latest

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt

COPY stac_scan ./stac_scan

ENTRYPOINT ["python3", "-m", "stac_scan.cli"]
