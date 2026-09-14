#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "stac-fastapi-api>=3.0,<4",
#   "uvicorn[standard]>=0.29",
#   "typer>=0.12",
#   "pystac[validation]>=1.10",
# ]
# ///
"""
Stacyserve: serve a local or remote static STAC catalog as a STAC API.

Usage:
  uv run stacyserve.py                                      # local ./catalog/catalog.json
  uv run stacyserve.py --catalog-path ./collections
  uv run stacyserve.py --catalog-url https://example.com/catalog.json
  STAC_CATALOG_URL=https://example.com/catalog.json uv run stacyserve.py

Search supports free-text via ?q=<term> on GET /search and {"q": "term"} on POST /search.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Annotated, Any, List, Optional

import attr
import pystac
import typer
import uvicorn
from pydantic import Field
from stac_fastapi.api.app import StacApi
from stac_fastapi.types.config import ApiSettings
from stac_fastapi.types.core import BaseCoreClient
from stac_fastapi.types.errors import NotFoundError
from stac_fastapi.types.search import BaseSearchPostRequest
from starlette.middleware.cors import CORSMiddleware

app = typer.Typer(name="stacyserve", add_completion=False)


# ---------------------------------------------------------------------------
# Loader — pystac handles URL resolution, recursive traversal, and validation
# ---------------------------------------------------------------------------

def _load_catalog(
    path: Optional[Path], url: Optional[str]
) -> tuple[dict[str, dict], dict[str, dict[str, dict]]]:
    if url:
        typer.echo(f"Fetching remote catalog: {url}")
        root = pystac.Catalog.from_file(url)
    else:
        catalog_json = path or Path("catalog")
        if catalog_json.suffix != ".json":
            catalog_json = catalog_json / "catalog.json"
        typer.echo(f"Loading local catalog: {catalog_json.resolve()}")
        root = pystac.Catalog.from_file(str(catalog_json.resolve()))

    collections: dict[str, dict] = {}
    items: dict[str, dict[str, dict]] = {}

    for col in root.get_collections():
        col_id = col.id
        collections[col_id] = col.to_dict()
        col_items = {item.id: item.to_dict() for item in col.get_items()}
        items[col_id] = col_items
        typer.echo(f"  Collection: {col_id} — {len(col_items)} item(s)")

    typer.echo(
        f"Ready: {len(collections)} collection(s), "
        f"{sum(len(v) for v in items.values())} item(s)"
    )
    return collections, items


# ---------------------------------------------------------------------------
# Free-text search
# ---------------------------------------------------------------------------

def _item_text(item: dict) -> str:
    """Flatten an item to a single lowercase string for text matching."""
    parts = [
        item.get("id", ""),
        item.get("collection", ""),
        json.dumps(item.get("properties", {})),
        json.dumps({k: v.get("title", "") for k, v in item.get("assets", {}).items()}),
    ]
    return " ".join(parts).lower()


def _matches_q(item: dict, q: Optional[str]) -> bool:
    if not q:
        return True
    return q.lower() in _item_text(item)


# ---------------------------------------------------------------------------
# Custom search request that accepts `q`
# ---------------------------------------------------------------------------

class SearchPostRequest(BaseSearchPostRequest):
    q: Optional[str] = Field(None, description="Free-text search term")


# ---------------------------------------------------------------------------
# STAC client
# ---------------------------------------------------------------------------

@attr.s
class StaticCatalogClient(BaseCoreClient):
    _collections: dict[str, dict] = attr.ib(factory=dict)
    _items: dict[str, dict[str, dict]] = attr.ib(factory=dict)

    def all_collections(self, **kwargs) -> Any:
        return {"collections": list(self._collections.values()), "links": []}

    def get_collection(self, collection_id: str, **kwargs) -> Any:
        if collection_id not in self._collections:
            raise NotFoundError(f"Collection '{collection_id}' not found")
        return self._collections[collection_id]

    def item_collection(
        self,
        collection_id: str,
        bbox=None,
        datetime=None,
        limit: int = 10,
        token: str = None,
        **kwargs,
    ) -> Any:
        if collection_id not in self._items:
            raise NotFoundError(f"Collection '{collection_id}' not found")
        all_items = list(self._items[collection_id].values())
        offset = int(base64.b64decode(token).decode()) if token else 0
        page = all_items[offset : offset + limit]
        links = []
        if offset + limit < len(all_items):
            next_token = base64.b64encode(str(offset + limit).encode()).decode()
            links.append({"rel": "next", "href": f"?token={next_token}&limit={limit}"})
        return {
            "type": "FeatureCollection",
            "features": page,
            "links": links,
            "numberMatched": len(all_items),
            "numberReturned": len(page),
        }

    def get_item(self, item_id: str, collection_id: str, **kwargs) -> Any:
        col_items = self._items.get(collection_id, {})
        if item_id not in col_items:
            raise NotFoundError(f"Item '{item_id}' not found in '{collection_id}'")
        return col_items[item_id]

    def get_search(
        self,
        collections: Optional[List[str]] = None,
        ids: Optional[List[str]] = None,
        bbox=None,
        intersects=None,
        datetime=None,
        limit: Optional[int] = 10,
        q: Optional[str] = None,
        **kwargs,
    ) -> Any:
        features = [
            item
            for col_id, col_items in self._items.items()
            if not collections or col_id in collections
            for item in col_items.values()
            if (not ids or item["id"] in ids) and _matches_q(item, q)
        ]
        return {"type": "FeatureCollection", "features": features[:limit], "links": []}

    def post_search(self, search_request: SearchPostRequest, **kwargs) -> Any:
        collections = getattr(search_request, "collections", None) or []
        ids = getattr(search_request, "ids", None) or []
        limit = getattr(search_request, "limit", 10) or 10
        q = getattr(search_request, "q", None)
        features = [
            item
            for col_id, col_items in self._items.items()
            if not collections or col_id in collections
            for item in col_items.values()
            if (not ids or item["id"] in ids) and _matches_q(item, q)
        ]
        return {"type": "FeatureCollection", "features": features[:limit], "links": []}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@app.command()
def serve(
    catalog_path: Annotated[
        Optional[Path],
        typer.Option(
            envvar="STAC_CATALOG_PATH",
            help="Path to catalog.json or its parent directory (local)",
        ),
    ] = None,
    catalog_url: Annotated[
        Optional[str],
        typer.Option(
            envvar="STAC_CATALOG_URL",
            help="URL of a remote catalog.json to load into memory",
        ),
    ] = None,
    port: Annotated[int, typer.Option(help="Port to listen on")] = 8080,
    host: Annotated[str, typer.Option(help="Host to bind")] = "127.0.0.1",
) -> None:
    """Serve a local or remote static STAC catalog as a STAC API."""
    if catalog_url and catalog_path:
        typer.echo("Error: specify --catalog-url or --catalog-path, not both.", err=True)
        raise typer.Exit(1)

    collections, items = _load_catalog(catalog_path, catalog_url)
    client = StaticCatalogClient(collections=collections, items=items)
    stac_api = StacApi(
        settings=ApiSettings(
            stac_fastapi_title="Stacyserve",
            stac_fastapi_description="Local/remote static STAC catalog",
        ),
        client=client,
        search_post_request_model=SearchPostRequest,
        middlewares=[],
    )
    stac_api.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    typer.echo(f"Serving at http://{host}:{port}")
    uvicorn.run(stac_api.app, host=host, port=port)


if __name__ == "__main__":
    app()
