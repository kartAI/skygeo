"""PMTiles -> pystac.Item by reading only the header + metadata (byte-range reads)."""

from __future__ import annotations

from datetime import datetime

import pystac
from pmtiles.reader import Reader
from shapely.geometry import box, mapping

from .extract_common import PMTILES_COMPRESSION, PROJ_EXT

PMTILES_MEDIA_TYPE = "application/vnd.pmtiles"

# pmtiles header tile_type enum -> name (PMTiles spec v3).
TILE_TYPES = {0: "unknown", 1: "mvt", 2: "png", 3: "jpeg", 4: "webp", 5: "avif", 6: "mlt"}


def _enum_int(value) -> int:
    """Header enums come back as IntEnum (.value) or plain int depending on lib version."""
    return value.value if hasattr(value, "value") else int(value)


def build_item_from_reader(get_bytes, item_id, dt, asset_href, extra_props) -> pystac.Item:
    reader = Reader(get_bytes)
    header = reader.header()
    try:
        metadata = reader.metadata() or {}
    except Exception:  # noqa: BLE001 - metadata is optional
        metadata = {}

    min_lon = header["min_lon_e7"] / 1e7
    min_lat = header["min_lat_e7"] / 1e7
    max_lon = header["max_lon_e7"] / 1e7
    max_lat = header["max_lat_e7"] / 1e7
    bbox = [min_lon, min_lat, max_lon, max_lat]
    geometry = mapping(box(min_lon, min_lat, max_lon, max_lat))

    tt = header["tile_type"]
    tt_int = tt.value if hasattr(tt, "value") else int(tt)
    tile_type = TILE_TYPES.get(tt_int, "unknown")
    props = {
        "proj:epsg": 4326,
        "pmtiles:tile_type": tile_type,
        "pmtiles:minzoom": int(header["min_zoom"]),
        "pmtiles:maxzoom": int(header["max_zoom"]),
        "pmtiles:center": [
            header["center_lon_e7"] / 1e7,
            header["center_lat_e7"] / 1e7,
            int(header["center_zoom"]),
        ],
    }
    if metadata.get("name"):
        props["pmtiles:name"] = metadata["name"]
    if metadata.get("vector_layers"):
        # TileJSON-style layer + field schema (vector tiles only).
        props["pmtiles:vector_layers"] = metadata["vector_layers"]

    # Tile-archive internals (free from the header). NOTE: these are TILE counts, not
    # feature counts — vector features are duplicated across zoom levels, so a feature
    # count is neither cheap nor meaningful here.
    for src_key, prop in (
        ("addressed_tiles_count", "pmtiles:addressed_tiles_count"),
        ("tile_entries_count", "pmtiles:tile_entries_count"),
        ("tile_contents_count", "pmtiles:tile_contents_count"),
    ):
        if header.get(src_key) is not None:
            props[prop] = int(header[src_key])
    if header.get("tile_compression") is not None:
        props["pmtiles:tile_compression"] = PMTILES_COMPRESSION.get(
            _enum_int(header["tile_compression"]), "unknown"
        )
    if header.get("clustered") is not None:
        props["pmtiles:clustered"] = bool(header["clustered"])
    if header.get("tile_data_length") is not None:
        props["pmtiles:tile_data_bytes"] = int(header["tile_data_length"])

    props.update(extra_props)

    item = pystac.Item(
        id=item_id,
        geometry=geometry,
        bbox=bbox,
        datetime=dt,
        properties=props,
    )
    item.stac_extensions.append(PROJ_EXT)
    item.add_asset(
        "data",
        pystac.Asset(href=asset_href, media_type=PMTILES_MEDIA_TYPE, roles=["data"]),
    )
    return item


def build_pmtiles_item(store, bucket, key, item_id, dt, asset_href, extra_props) -> pystac.Item:
    def get_bytes(offset: int, length: int) -> bytes:
        return store.get_range(bucket, key, offset, length)

    return build_item_from_reader(get_bytes, item_id, dt, asset_href, extra_props)
