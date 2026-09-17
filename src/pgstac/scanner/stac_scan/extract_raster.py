"""COG / GeoTIFF -> pystac.Item via rio-stac (proj + raster extensions)."""

from __future__ import annotations

from datetime import datetime

import pystac
import rasterio
from rio_stac.stac import create_stac_item


def _cog_internals(local_path: str) -> dict:
    """Cheap header-only COG internals (compression, tiling, overviews). Best-effort."""
    out = {}
    try:
        with rasterio.open(local_path) as ds:
            if ds.compression is not None:
                out["cog:compression"] = ds.compression.value
            prof = ds.profile
            if prof.get("tiled") and prof.get("blockxsize"):
                out["cog:blocksize"] = [int(prof["blockxsize"]), int(prof["blockysize"])]
            out["cog:overview_count"] = len(ds.overviews(1)) if ds.count else 0
            struct = ds.tags(ns="IMAGE_STRUCTURE")
            if struct.get("PREDICTOR"):
                out["cog:predictor"] = int(struct["PREDICTOR"])
    except Exception:  # noqa: BLE001 - internals are optional, never fail the item
        pass
    return out


def build_raster_item(
    local_path: str,
    item_id: str,
    dt: datetime,
    asset_href: str,
    extra_props: dict,
) -> pystac.Item:
    item = create_stac_item(
        source=local_path,
        id=item_id,
        input_datetime=dt,
        asset_name="data",
        asset_href=asset_href,
        asset_media_type=pystac.MediaType.COG,
        with_proj=True,
        with_raster=True,
    )
    if "data" in item.assets:
        item.assets["data"].roles = ["data"]
    item.properties.update(_cog_internals(local_path))
    item.properties.update(extra_props)
    return item
