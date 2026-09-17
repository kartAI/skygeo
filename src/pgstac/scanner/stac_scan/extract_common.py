"""Shared helpers + extension URLs for extractors."""

from __future__ import annotations

import os

# STAC extension schema URLs (STAC 1.0.0 compatible).
PROJ_EXT = "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
TABLE_EXT = "https://stac-extensions.github.io/table/v1.2.0/schema.json"
FILE_EXT = "https://stac-extensions.github.io/file/v2.1.0/schema.json"

# PMTiles spec v3 compression enum -> name.
PMTILES_COMPRESSION = {0: "unknown", 1: "none", 2: "gzip", 3: "brotli", 4: "zstd"}


class SkipFile(Exception):
    """Raised when a file should be skipped (e.g. .json that isn't GeoJSON)."""


def item_id_from_key(key: str) -> str:
    """Short, filesystem-safe Item id = the file's basename without extension."""
    base = os.path.basename(key.rstrip("/"))
    stem = os.path.splitext(base)[0].replace(" ", "_")
    # Fallback to the flattened path if a basename can't be derived.
    return stem or key.strip("/").replace("/", "_")
