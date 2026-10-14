"""List objects under a prefix and classify by extension."""

from __future__ import annotations

import os

# extension -> kind. ".json" is a *candidate* — validated as GeoJSON at extract time.
EXT_MAP = {
    ".tif": "cog",
    ".tiff": "cog",
    ".geojson": "geojson",
    ".json": "geojson_candidate",
    ".parquet": "geoparquet",
    ".geoparquet": "geoparquet",
    ".pmtiles": "pmtiles",
}


def discover(store, bucket: str, prefix: str, recursive: bool, exclude_prefix: str | None = None):
    """Return (files, skipped_count). files = list of dicts with key/kind/last_modified/size.

    Keys under exclude_prefix (the catalog output prefix) are ignored so the scanner
    never ingests its own generated catalog JSON.
    """
    files = []
    skipped = 0
    for obj in store.list_objects(bucket, prefix):
        key = obj["Key"]
        if key.endswith("/"):
            continue
        if exclude_prefix and key.startswith(exclude_prefix):
            continue
        rel = key[len(prefix):]
        if not recursive and "/" in rel.strip("/"):
            skipped += 1
            continue
        ext = os.path.splitext(key)[1].lower()
        kind = EXT_MAP.get(ext)
        if not kind:
            skipped += 1
            continue
        files.append(
            {
                "key": key,
                "kind": kind,
                "last_modified": obj["LastModified"],
                "size": obj.get("Size", 0),
            }
        )
    return files, skipped
