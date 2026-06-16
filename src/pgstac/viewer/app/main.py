"""FastAPI app: serves the STAC Browser SPA + a signing S3 asset proxy.

The catalog is served by the STAC API (stac-fastapi-pgstac) directly — the browser
talks to it cross-origin (CORS) — so this app only needs to: serve the SPA, inject
runtime config (pointing catalogUrl at the API), and sign asset reads from the private
bucket. There is NO /catalog rewrite route (that was for the static-catalog variant).

Routes (origin-relative; PATH_PREFIX-aware via uvicorn root_path):
  GET /healthz              liveness
  GET /config.js            runtime STAC Browser config injected from env
  GET /s3/{bucket}/{key}    asset bytes from S3, signed, Range-aware (COG/PMTiles)
  GET /*                    STAC Browser static SPA (hash-routed)
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import load_settings
from .s3proxy import S3Reader, stream_body

settings = load_settings()
reader = S3Reader(settings)

STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")

# Full default config extracted from the pinned STAC Browser at build time. In
# DYNAMIC_CONFIG mode the app reads the entire config from window.STAC_BROWSER_CONFIG,
# so we must serve a complete object (not just our overrides) or it crashes on boot.
_DEFAULTS_PATH = os.environ.get("DEFAULT_CONFIG_PATH", "/app/config.default.json")
try:
    with open(_DEFAULTS_PATH, encoding="utf-8") as fh:
        DEFAULT_CONFIG = json.load(fh)
except FileNotFoundError:
    DEFAULT_CONFIG = {}

app = FastAPI(title="pgstac viewer", root_path=settings.path_prefix.rstrip("/"))


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "api": settings.stac_api_url}


@app.get("/config.js")
def config_js() -> Response:
    """STAC Browser runtime config. Opens the STAC API directly, hash history mode.

    catalogUrl is the STAC API root (absolute) — the browser fetches catalog/collection/
    item JSON from it cross-origin (the API enables CORS for this origin). Asset hrefs in
    that JSON already point at this viewer's /s3 proxy (written by the scanner).
    """
    cfg = dict(DEFAULT_CONFIG)
    cfg.update({
        "catalogUrl": settings.stac_api_url,
        "historyMode": "hash",
        "pathPrefix": settings.path_prefix,
        # Real S3 base (https://<endpoint>/) so the client-side "Open in Protomaps"
        # action can map a proxied /s3/<bucket>/<key> href back to the real S3 URL.
        "s3Base": settings.s3_base,
        # MapLibre basemap style for the inline "Data preview" tab (MapLibrePreview.vue).
        "basemapStyleUrl": settings.basemap_style_url,
    })
    body = f"window.STAC_BROWSER_CONFIG = {json.dumps(cfg)};\n"
    return Response(content=body, media_type="application/javascript",
                    headers={"Cache-Control": "no-store"})


@app.get("/s3/{bucket}/{key:path}")
def get_asset(bucket: str, key: str, range: str | None = Header(default=None)) -> Response:
    try:
        obj = reader.get_object(bucket, key, range)
    except KeyError:
        return JSONResponse({"error": "not found", "bucket": bucket, "key": key},
                            status_code=404)
    return StreamingResponse(
        stream_body(obj["body"]),
        status_code=obj["status"],
        headers=obj["headers"],
    )


# Static SPA last so explicit API routes win. html=True serves index.html at "/".
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
