"""Assemble a pgstac Collection + Item JSON from extracted pystac Items.

Unlike the static-catalog variant, we do NOT normalize hrefs into a tree: items go
straight into pgstac, which (via stac-fastapi) regenerates self/root/parent/collection
links on output. We only need each item's `collection` field + a Collection with an
extent unioned from its items.
"""

from __future__ import annotations

import pystac


def build_collection(collection_id, title, description, items):
    """Build a pystac.Collection with spatial+temporal extent unioned from items."""
    collection = pystac.Collection(
        id=collection_id,
        title=title or collection_id,
        description=description or collection_id,
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            temporal=pystac.TemporalExtent([[None, None]]),
        ),
        license="proprietary",
    )
    for item in items:
        collection.add_item(item)
    collection.update_extent_from_items()
    return collection


def to_jsons(collection, items):
    """Return (collection_dict, [item_dict, ...]) ready for pypgstac load.

    Links are stripped: pgstac/stac-fastapi regenerate them, and any tree links we'd
    emit here point nowhere (we never normalized hrefs). Asset hrefs are preserved.
    """
    coll = collection.to_dict(include_self_link=False)
    coll["links"] = []

    item_dicts = []
    for item in items:
        d = item.to_dict(include_self_link=False, transform_hrefs=False)
        d["collection"] = collection.id
        d["links"] = []
        item_dicts.append(d)
    return coll, item_dicts
