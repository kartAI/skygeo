"""Load a Collection + Items into pgstac via pypgstac, then prune removed items.

pypgstac's load modes (insert/upsert/delsert) never prune items that are absent from
the load set, so 'upsert + prune' is two steps: upsert everything found, then delete
items present in the Collection but not in this scan (mirrors the S3 folder).
"""

from __future__ import annotations

from pypgstac.db import PgstacDB
from pypgstac.load import Loader, Methods


class PgLoader:
    def __init__(self, dsn: str):
        self.db = PgstacDB(dsn=dsn, commit_on_exit=True)
        self.loader = Loader(db=self.db)

    def upsert_collection(self, collection: dict) -> None:
        self.loader.load_collections([collection], insert_mode=Methods.upsert)

    def upsert_items(self, items: list[dict]) -> None:
        # iter() so pypgstac's chunked reader consumes it as a stream.
        self.loader.load_items(iter(items), insert_mode=Methods.upsert)

    def drop_collection(self, collection_id: str) -> bool:
        """Delete the collection (and all its items, via pgstac) if it exists.

        Returns True if a collection was dropped, False if it didn't exist. Used by
        --drop to fully recreate a previously scanned dataset instead of upsert+prune.
        """
        rows = self.db.query(
            "SELECT 1 FROM pgstac.collections WHERE id = %s", [collection_id]
        )
        if not list(rows):
            return False
        # delete_collection cascades to the collection's items/partitions.
        list(self.db.query("SELECT pgstac.delete_collection(%s)", [collection_id]))
        return True

    def existing_item_ids(self, collection_id: str) -> set[str]:
        rows = self.db.query(
            "SELECT id FROM pgstac.items WHERE collection = %s", [collection_id]
        )
        return {row[0] for row in rows}

    def prune(self, collection_id: str, keep_ids) -> list[str]:
        """Delete items in the Collection whose id is not in keep_ids. Returns deleted ids."""
        keep = set(keep_ids)
        stale = [i for i in self.existing_item_ids(collection_id) if i not in keep]
        for sid in stale:
            # delete_item returns void; consume the generator to execute it.
            list(self.db.query("SELECT pgstac.delete_item(%s, %s)", [sid, collection_id]))
        return stale

    def close(self) -> None:
        self.db.close()
