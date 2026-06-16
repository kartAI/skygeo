"""S3 / VersityGW access: list, download, write JSON, delete, build https URLs."""

from __future__ import annotations

import json
from typing import Iterator

import boto3
from botocore.config import Config


class S3Store:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, region: str = "us-east-1"):
        host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        self.endpoint_url = f"https://{host}"
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            # VersityGW (and most S3-compatible gateways) need path-style addressing.
            config=Config(s3={"addressing_style": "path"}),
        )

    # ---- URLs -----------------------------------------------------------
    def http_url(self, bucket: str, key: str) -> str:
        return f"{self.endpoint_url}/{bucket}/{key.lstrip('/')}"

    def key_from_url(self, bucket: str, url: str) -> str:
        prefix = f"{self.endpoint_url}/{bucket}/"
        return url[len(prefix):] if url.startswith(prefix) else url

    # ---- Reads ----------------------------------------------------------
    def list_objects(self, bucket: str, prefix: str) -> Iterator[dict]:
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                yield obj

    def list_json_keys(self, bucket: str, prefix: str) -> set[str]:
        return {
            obj["Key"]
            for obj in self.list_objects(bucket, prefix)
            if obj["Key"].endswith(".json")
        }

    def download(self, bucket: str, key: str, dest: str) -> None:
        self.client.download_file(bucket, key, dest)

    def presign(self, bucket: str, key: str, expires: int) -> str:
        """Time-limited GET URL — fetchable without credentials (for STAC clients)."""
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
        )

    def get_range(self, bucket: str, key: str, offset: int, length: int) -> bytes:
        """Read `length` bytes starting at `offset` (for header-only reads, e.g. PMTiles)."""
        resp = self.client.get_object(
            Bucket=bucket, Key=key, Range=f"bytes={offset}-{offset + length - 1}"
        )
        return resp["Body"].read()

    # ---- Writes ---------------------------------------------------------
    def put_json(self, bucket: str, key: str, obj: dict) -> None:
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(obj, default=str).encode("utf-8"),
            ContentType="application/json",
        )

    def delete_keys(self, bucket: str, keys: list[str]) -> None:
        for i in range(0, len(keys), 1000):
            batch = keys[i:i + 1000]
            if not batch:
                continue
            self.client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": k} for k in batch]},
            )
