"""GeoJSON / GeoParquet -> pystac.Item with proj + table:columns + geometry breakdown.

GeoParquet is read CHEAPLY: row count, column schema, geometry types, CRS, encoding and
bbox all come from the parquet footer + the GeoParquet `geo` metadata key — no full row
scan. Only when the footer lacks a bbox/geometry-types do we fall back to reading the single
geometry column. GeoJSON has no footer, so it is still fully loaded (then enriched in-memory).
"""

from __future__ import annotations

import json
import math
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pystac
from pyproj import CRS, Transformer
from shapely import wkb
from shapely.geometry import box, mapping

from .extract_common import PROJ_EXT, TABLE_EXT, SkipFile

SAMPLE_ROWS = 5
FIELD_CAP = 500  # max chars per sampled field value


# --------------------------------------------------------------------------- shared


def _safe(value):
    if value is None:
        return None
    try:
        if np.isscalar(value) and pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        f = float(value)
        return None if math.isnan(f) else f
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (bytes, bytearray)):
        # WKB geometry column in a sampled parquet row.
        try:
            return wkb.loads(bytes(value)).wkt[:FIELD_CAP]
        except Exception:  # noqa: BLE001
            return None
    return str(value)[:FIELD_CAP]


def _assemble(item_id, dt, geometry, bbox, epsg, props, asset_href, media_type, extra_props):
    props["proj:epsg"] = epsg
    props.update(extra_props)
    item = pystac.Item(
        id=item_id, geometry=geometry, bbox=bbox, datetime=dt, properties=props,
    )
    item.stac_extensions.extend([PROJ_EXT, TABLE_EXT])
    item.add_asset(
        "data", pystac.Asset(href=asset_href, media_type=media_type, roles=["data"]),
    )
    return item


def _bbox_to_4326(bbox, epsg):
    if epsg == 4326 or bbox is None:
        return bbox
    t = Transformer.from_crs(epsg, 4326, always_xy=True)
    minx, miny, maxx, maxy = bbox
    xs, ys = t.transform([minx, maxx, minx, maxx], [miny, miny, maxy, maxy])
    return [min(xs), min(ys), max(xs), max(ys)]


# --------------------------------------------------------------------------- geoparquet


def _arrow_col_type(t: pa.DataType, is_geom: bool) -> str:
    if is_geom:
        return "geometry"
    if pa.types.is_integer(t):
        return "int64"
    if pa.types.is_floating(t):
        return "float64"
    if pa.types.is_boolean(t):
        return "boolean"
    if pa.types.is_temporal(t):
        return "datetime"
    if pa.types.is_string(t) or pa.types.is_large_string(t):
        return "string"
    return str(t)


def _epsg_from_geo(col_meta: dict) -> int:
    crs = col_meta.get("crs")
    if not crs:
        return 4326  # GeoParquet default is OGC:CRS84 (== EPSG:4326 lon/lat)
    try:
        # LIMITATION: a custom CRS with no EPSG code falls back to 4326, which would
        # then skip bbox reprojection. Doesn't trigger for our data (EPSG:25833).
        return CRS.from_user_input(crs).to_epsg() or 4326
    except Exception:  # noqa: BLE001
        return 4326


def _parquet_sample(pf: pq.ParquetFile) -> list[dict]:
    """First SAMPLE_ROWS rows only — iter_batches stops after the first batch."""
    try:
        batch = next(pf.iter_batches(batch_size=SAMPLE_ROWS))
    except StopIteration:
        return []
    df = pa.Table.from_batches([batch]).to_pandas()
    return [{col: _safe(val) for col, val in row.items()} for _, row in df.iterrows()]


def _build_parquet(local_path, item_id, dt, asset_href, media_type, extra_props):
    pf = pq.ParquetFile(local_path)
    if pf.metadata.num_rows == 0:
        raise SkipFile("no features")

    schema = pf.schema_arrow
    md = schema.metadata or {}
    geo = json.loads(md[b"geo"]) if b"geo" in md else None
    if geo is None:
        # Not a GeoParquet (no spatial metadata) — fall back to the geopandas path.
        return _build_geojson(local_path, "geoparquet", item_id, dt, asset_href,
                              media_type, extra_props)

    primary = geo.get("primary_column") or next(iter(geo["columns"]))
    geom_cols = set(geo.get("columns", {}).keys()) or {primary}
    col_meta = geo["columns"][primary]
    epsg = _epsg_from_geo(col_meta)

    columns = [
        {"name": f.name, "type": _arrow_col_type(f.type, f.name in geom_cols)}
        for f in schema
    ]

    geom_types = col_meta.get("geometry_types")
    bbox = col_meta.get("bbox")  # native CRS, lon/lat order; both optional in the spec.

    if bbox is None or not geom_types:
        # Footer lacks bbox/types — read ONLY the geometry column (cheap vs full table).
        gs = gpd.read_parquet(local_path, columns=[primary])
        if gs.crs is not None:
            epsg = gs.crs.to_epsg() or epsg
        if bbox is None:
            # We have the geometries: reproject for an exact lon/lat envelope (a
            # 4-corner transform underestimates the envelope for projected CRS).
            gs_ll = gs.to_crs(4326) if (gs.crs is not None and epsg != 4326) else gs
            bbox = [float(v) for v in gs_ll.total_bounds]
        else:
            bbox = _bbox_to_4326(bbox, epsg)  # STAC bbox is always lon/lat 4326.
        if not geom_types:
            geom_types = sorted(gs.geom_type.dropna().unique().tolist())
    else:
        bbox = _bbox_to_4326(bbox, epsg)  # proj:epsg keeps the data's native CRS.

    minx, miny, maxx, maxy = bbox
    geometry = mapping(box(minx, miny, maxx, maxy))

    props = {
        "table:columns": columns,
        "table:row_count": int(pf.metadata.num_rows),
        "table:primary_geometry": primary,
        "vector:geometry_types": geom_types,
        "proc:sample": _parquet_sample(pf),
    }
    if col_meta.get("encoding"):
        props["vector:encoding"] = col_meta["encoding"]
    return _assemble(item_id, dt, geometry, bbox, epsg, props, asset_href,
                     media_type, extra_props)


# --------------------------------------------------------------------------- geojson


def _validate_geojson(local_path: str) -> None:
    """Raise SkipFile if a .json is not a GeoJSON Feature/FeatureCollection/geometry."""
    try:
        with open(local_path, "rb") as fh:
            head = fh.read(4096).decode("utf-8", errors="ignore")
    except OSError as exc:
        raise SkipFile(f"unreadable: {exc}")
    valid = (
        '"FeatureCollection"' in head
        or '"Feature"' in head
        or '"coordinates"' in head
    )
    if not valid:
        raise SkipFile("not GeoJSON")


def _gpd_col_type(dtype, is_geom: bool) -> str:
    if is_geom:
        return "geometry"
    kind = getattr(dtype, "kind", "O")
    return {
        "i": "int64", "u": "int64", "f": "float64",
        "b": "boolean", "O": "string", "M": "datetime",
    }.get(kind, str(dtype))


def _gpd_sample(gdf: gpd.GeoDataFrame) -> list[dict]:
    geom_col = gdf.geometry.name if gdf.geometry is not None else None
    rows = []
    for _, row in gdf.head(SAMPLE_ROWS).iterrows():
        record = {}
        for col, val in row.items():
            if col == geom_col:
                record[col] = (val.wkt[:FIELD_CAP] if val is not None else None)
            else:
                record[col] = _safe(val)
        rows.append(record)
    return rows


def _build_geojson(local_path, kind, item_id, dt, asset_href, media_type, extra_props):
    if kind == "geojson_candidate":
        _validate_geojson(local_path)

    gdf = gpd.read_parquet(local_path) if kind == "geoparquet" else gpd.read_file(local_path)
    if gdf.empty:
        raise SkipFile("no features")

    epsg = gdf.crs.to_epsg() if gdf.crs is not None else 4326
    gdf_ll = gdf.to_crs(4326) if (gdf.crs is not None and epsg != 4326) else gdf
    minx, miny, maxx, maxy = (float(v) for v in gdf_ll.total_bounds)
    bbox = [minx, miny, maxx, maxy]
    geometry = mapping(box(minx, miny, maxx, maxy))

    geom_col = gdf.geometry.name
    columns = [
        {"name": col, "type": _gpd_col_type(dtype, col == geom_col)}
        for col, dtype in gdf.dtypes.items()
    ]
    props = {
        "table:columns": columns,
        "table:row_count": int(len(gdf)),
        "table:primary_geometry": geom_col,
        "vector:geometry_types": sorted(gdf.geom_type.dropna().unique().tolist()),
        "proc:sample": _gpd_sample(gdf),
    }
    return _assemble(item_id, dt, geometry, bbox, epsg, props, asset_href,
                     media_type, extra_props)


# --------------------------------------------------------------------------- entry


def build_vector_item(
    local_path: str,
    kind: str,
    item_id: str,
    dt: datetime,
    asset_href: str,
    media_type: str,
    extra_props: dict,
) -> pystac.Item:
    if kind == "geoparquet":
        return _build_parquet(local_path, item_id, dt, asset_href, media_type, extra_props)
    return _build_geojson(local_path, kind, item_id, dt, asset_href, media_type, extra_props)
