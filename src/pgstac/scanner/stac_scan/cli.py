"""CLI: scan an S3/VersityGW prefix and load a STAC Collection into pgstac.

One run = one source = one Collection. Re-runs upsert found items and prune items no
longer in the S3 folder. Secrets + DB DSN + asset base come from env, never CLI flags.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote

import click

from . import build, discover
from .extract_common import FILE_EXT, SkipFile, item_id_from_key
from .extract_pmtiles import build_pmtiles_item
from .extract_raster import build_raster_item
from .extract_vector import build_vector_item
from .pgload import PgLoader
from .s3io import S3Store

VECTOR_MEDIA = {
    "geojson": "application/geo+json",
    "geojson_candidate": "application/geo+json",
    "geoparquet": "application/x-parquet",
}


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise click.ClickException(f"Missing required env var: {name}")
    return val


def _pgstac_dsn() -> str:
    """Connection string for pgstac.

    Single source of truth: derived from the same POSTGRES_* vars the db/api use, so the
    password can never drift. PGHOST/PGPORT default to the db service on the shared net.
    Set PGSTAC_DSN explicitly only to point at an external/non-default database.
    """
    override = os.environ.get("PGSTAC_DSN")
    if override:
        return override
    user = quote(_env("POSTGRES_USER"), safe="")
    password = quote(_env("POSTGRES_PASSWORD"), safe="")
    db = _env("POSTGRES_DB")
    host = os.environ.get("PGHOST", "db")
    port = os.environ.get("PGPORT", "5432")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


@click.command()
@click.option("--bucket", required=True, help="S3 bucket to scan.")
@click.option("--prefix", required=True, help="Data folder (key prefix) to scan.")
@click.option("--collection-id", required=True, help="STAC Collection id (the source).")
@click.option("--collection-title", default=None, help="Human-readable Collection title.")
@click.option("--collection-description", default=None, help="Collection description.")
@click.option("--datetime", "datetime_override", default=None,
              help="ISO datetime applied to all Items (default: S3 LastModified).")
@click.option("--recursive/--no-recursive", default=True, help="Recurse into subfolders.")
@click.option("--fail-on-error", is_flag=True, default=False,
              help="Fail the whole run if any file errors (default: skip + warn).")
@click.option("--no-prune", is_flag=True, default=False,
              help="Do not delete items missing from the S3 folder (default: prune).")
@click.option("--drop", "drop", is_flag=True, default=False,
              help="Drop the collection (and all its items) before loading, then recreate. "
                   "Use to fully refresh a previously scanned dataset; makes prune moot.")
@click.option("--region", default=None, help="S3 region (overrides S3_REGION env).")
def main(bucket, prefix, collection_id, collection_title, collection_description,
         datetime_override, recursive, fail_on_error, no_prune, drop, region):
    prefix = prefix if prefix.endswith("/") else prefix + "/"

    store = S3Store(
        endpoint=_env("S3_ENDPOINT"),
        access_key=_env("S3_ACCESS_KEY"),
        secret_key=_env("S3_SECRET_KEY"),
        region=region or os.environ.get("S3_REGION", "us-east-1"),
    )
    dsn = _pgstac_dsn()
    # Base for asset hrefs stored in the DB: <ASSET_BASE_URL>/s3/<bucket>/<key>.
    # The viewer's /s3 proxy signs + fetches these; bucket in the path => multi-source.
    asset_base = _env("ASSET_BASE_URL").rstrip("/")

    override_dt = _parse_datetime(datetime_override) if datetime_override else None

    # --- Discover ----------------------------------------------------------
    files, skipped = discover.discover(store, bucket, prefix, recursive)
    click.echo(f"Discovered {len(files)} candidate file(s), skipped {skipped}.")

    # --- Extract -----------------------------------------------------------
    items = []
    failed = []
    seen_ids: dict[str, int] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            key = f["key"]
            base_id = item_id_from_key(key)
            n = seen_ids.get(base_id, 0)
            seen_ids[base_id] = n + 1
            item_id = base_id if n == 0 else f"{base_id}-{n}"
            try:
                item = _extract_one(store, bucket, key, item_id, f, tmp,
                                    override_dt, asset_base)
                items.append(item)
                click.echo(f"  built  {key}")
            except SkipFile as exc:
                failed.append({"key": key, "reason": f"skipped: {exc}"})
                click.echo(f"  skip   {key} ({exc})", err=True)
            except Exception as exc:  # noqa: BLE001 - skip-and-warn by default
                failed.append({"key": key, "reason": f"{type(exc).__name__}: {exc}"})
                click.echo(f"  ERROR  {key} ({exc})", err=True)

    if not items:
        raise click.ClickException("No items built — run unsuccessful.")
    if fail_on_error and failed:
        raise click.ClickException(f"{len(failed)} file(s) errored and --fail-on-error set.")

    # --- Validate (before assembly) ---------------------------------------
    # Validate items while they are standalone. We validate here, BEFORE build_collection
    # adds tree links: we never normalize hrefs (pgstac/stac-fastapi regenerate links), so
    # added links carry None hrefs that fail schema validation spuriously. Those links are
    # stripped before load anyway, so this checks the real content (geometry/proj/etc).
    invalid = 0
    for item in items:
        try:
            item.validate()
        except Exception as exc:  # noqa: BLE001
            invalid += 1
            click.echo(f"  invalid  {item.id} ({exc})", err=True)
    if invalid:
        click.echo(f"Warning: {invalid} item(s) failed STAC validation (loaded anyway).",
                   err=True)

    # --- Assemble ----------------------------------------------------------
    collection = build.build_collection(
        collection_id, collection_title, collection_description, items)
    coll_dict, item_dicts = build.to_jsons(collection, items)

    # --- Load into pgstac (upsert) + prune --------------------------------
    loader = PgLoader(dsn)
    try:
        if drop:
            dropped = loader.drop_collection(collection_id)
            click.echo(
                f"Dropped existing collection '{collection_id}' (and its items)."
                if dropped else
                f"--drop: collection '{collection_id}' did not exist; creating fresh."
            )
        loader.upsert_collection(coll_dict)
        loader.upsert_items(item_dicts)
        click.echo(f"Upserted collection '{collection_id}' + {len(item_dicts)} item(s).")
        if drop:
            click.echo("Prune skipped (--drop already recreated the collection).")
        elif no_prune:
            click.echo("Prune skipped (--no-prune).")
        else:
            keep = {d["id"] for d in item_dicts}
            stale = loader.prune(collection_id, keep)
            if stale:
                click.echo(f"Pruned {len(stale)} item(s) no longer in S3.")
    finally:
        loader.close()

    click.echo(f"Done. built={len(items)} skipped={skipped} failed={len(failed)}")


def _extract_one(store, bucket, key, item_id, meta, tmp, override_dt, asset_base):
    dt = override_dt or meta["last_modified"]
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    source = "override" if override_dt else "s3_last_modified"
    asset_href = f"{asset_base}/s3/{bucket}/{key.lstrip('/')}"
    # file:size (File extension) applies to every format; size is known from S3 listing.
    extra = {"proc:datetime_source": source, "proc:source_key": key}
    if meta.get("size"):
        extra["file:size"] = int(meta["size"])
    kind = meta["kind"]

    # PMTiles: header-only via byte-range reads, no full download.
    if kind == "pmtiles":
        item = build_pmtiles_item(store, bucket, key, item_id, dt, asset_href, extra)
    else:
        local_path = os.path.join(tmp, os.path.basename(key) or item_id)
        store.download(bucket, key, local_path)
        if kind == "cog":
            item = build_raster_item(local_path, item_id, dt, asset_href, extra)
        else:
            item = build_vector_item(local_path, kind, item_id, dt, asset_href,
                                     VECTOR_MEDIA[kind], extra)

    if "file:size" in item.properties and FILE_EXT not in item.stac_extensions:
        item.stac_extensions.append(FILE_EXT)
    return item


if __name__ == "__main__":
    main()
