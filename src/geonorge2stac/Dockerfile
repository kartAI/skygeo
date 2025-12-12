FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/stac-utils/stac-fastapi-geoparquet.git . && \
    uv sync

ENV PATH="/app/.venv/bin:$PATH"

#ENV STAC_FASTAPI_GEOPARQUET_HREF=https://kartaistorage.blob.core.windows.net/skygeo/geonorge_stac_experiments/publisher_collection/geonorge_stac.parquet

EXPOSE 8000 
#correct?

CMD ["/app/.venv/bin/uvicorn", "stac_fastapi.geoparquet.main:app", "--host", "0.0.0.0", "--port", "8000"]

