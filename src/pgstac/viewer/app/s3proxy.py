"""Signed reads against VersityGW/S3 — mirrors the scanner's client conventions.

Asset hrefs stored in pgstac carry the bucket in the path (/s3/<bucket>/<key>), so the
proxy signs reads against whatever bucket the request names — supporting multiple source
buckets behind one viewer.
"""

from __future__ import annotations

from typing import Iterator, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import Settings


class S3Reader:
    def __init__(self, s: Settings):
        self.client = boto3.client(
            "s3",
            endpoint_url=s.endpoint_url,
            aws_access_key_id=s.access_key,
            aws_secret_access_key=s.secret_key,
            region_name=s.region,
            # VersityGW (and most S3-compatible gateways) need path-style addressing.
            config=Config(s3={"addressing_style": "path"}),
        )

    def get_object(self, bucket: str, key: str, range_header: Optional[str]) -> dict:
        """Range-aware passthrough for asset bytes (COG/PMTiles need ranges).

        Returns dict with: body (StreamingBody), status, headers (dict to forward).
        """
        kwargs: dict = {"Bucket": bucket, "Key": key}
        if range_header:
            kwargs["Range"] = range_header
        try:
            resp = self.client.get_object(**kwargs)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404", "NoSuchBucket"):
                raise KeyError(key) from e
            raise

        meta = resp["ResponseMetadata"]
        status = meta.get("HTTPStatusCode", 200)
        headers: dict[str, str] = {"Accept-Ranges": "bytes"}
        for src, dst in (
            ("ContentType", "Content-Type"),
            ("ContentLength", "Content-Length"),
            ("ContentRange", "Content-Range"),
            ("ETag", "ETag"),
        ):
            val = resp.get(src)
            if val is not None:
                headers[dst] = str(val)
        return {"body": resp["Body"], "status": status, "headers": headers}


def stream_body(body, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    while True:
        chunk = body.read(chunk_size)
        if not chunk:
            break
        yield chunk
