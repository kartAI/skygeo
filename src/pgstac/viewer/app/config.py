"""Runtime configuration, all from environment (k8s-friendly, no baked secrets)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _require(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        raise RuntimeError(f"required env var {name} is not set")
    return val


@dataclass(frozen=True)
class Settings:
    endpoint_host: str          # S3 host, no scheme (e.g. s3.example.no)
    endpoint_url: str           # https://<host>
    access_key: str
    secret_key: str
    region: str
    stac_api_url: str           # STAC API root the browser opens (e.g. http://localhost:8082)
    path_prefix: str            # sub-path the app is served under (default "/")
    port: int
    basemap_style_url: str      # MapLibre style URL for the inline "Data preview" basemap

    @property
    def s3_base(self) -> str:
        """Absolute S3 URL prefix (https://host/). Asset keys carry the bucket, so the
        proxied /s3/<bucket>/<key> maps back to <endpoint>/<bucket>/<key> for the
        client-side 'Open in Protomaps' action."""
        return f"{self.endpoint_url}/"


def load_settings() -> Settings:
    raw_host = _require("S3_ENDPOINT")
    host = raw_host.replace("https://", "").replace("http://", "").rstrip("/")

    prefix = os.environ.get("PATH_PREFIX", "/").strip() or "/"
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    return Settings(
        endpoint_host=host,
        endpoint_url=f"https://{host}",
        access_key=_require("S3_ACCESS_KEY"),
        secret_key=_require("S3_SECRET_KEY"),
        region=os.environ.get("S3_REGION", "us-east-1").strip() or "us-east-1",
        stac_api_url=_require("STAC_API_URL").rstrip("/"),
        path_prefix=prefix,
        port=int(os.environ.get("PORT", "8080")),
        # Free MapLibre demo style by default; override (e.g. the Norkart style) via env.
        basemap_style_url=(
            os.environ.get("BASEMAP_STYLE_URL", "").strip()
            or "https://demotiles.maplibre.org/style.json"
        ),
    )
