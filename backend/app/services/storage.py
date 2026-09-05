import logging
import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError

from ..config import settings

logger = logging.getLogger("cftv.storage")

# MediaMTX recordFormat "fmp4" always writes this extension; see mediamtx.yml.
SEGMENT_EXTENSION = ".mp4"
# Matches the recordPath timestamp pattern %Y-%m-%d_%H-%M-%S-%f.
SEGMENT_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"


class StorageUnavailable(RuntimeError):
    pass


def _parse_segment_start(key: str) -> datetime | None:
    filename = os.path.basename(key)
    stem = filename.removesuffix(SEGMENT_EXTENSION)
    try:
        return datetime.strptime(stem, SEGMENT_TIMESTAMP_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


class R2Storage:
    """Thin wrapper around a Cloudflare R2 bucket (S3-compatible).

    Recordings live here instead of the MediaMTX local playback server so
    storage isn't capped by the Railway volume plan. Local disk only keeps a
    short safety buffer (see mediamtx recordDeleteAfter) in case an upload is
    delayed or fails.
    """

    def __init__(self) -> None:
        self.bucket = settings.r2_bucket_name
        self._client = None
        if self.is_configured:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=(
                    settings.r2_secret_access_key.get_secret_value()
                    if settings.r2_secret_access_key
                    else None
                ),
                config=BotoConfig(signature_version="s3v4"),
                region_name="auto",
            )

    @property
    def is_configured(self) -> bool:
        return bool(
            settings.r2_account_id
            and settings.r2_access_key_id
            and settings.r2_secret_access_key
            and settings.r2_bucket_name
        )

    def upload_segment(self, local_path: str, key: str, duration_seconds: str) -> None:
        if not self._client:
            raise StorageUnavailable("R2 não está configurado")
        try:
            self._client.upload_file(
                local_path,
                self.bucket,
                key,
                ExtraArgs={"Metadata": {"duration": duration_seconds}},
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable(f"falha ao enviar segmento para R2: {exc}") from exc

    def list_recordings(
        self, camera_path: str, start: datetime | None, end: datetime | None
    ) -> list[dict]:
        if not self._client:
            raise StorageUnavailable("R2 não está configurado")
        prefix = f"{camera_path}/"
        results: list[dict] = []
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for item in page.get("Contents", []):
                    key = item["Key"]
                    segment_start = _parse_segment_start(key)
                    if segment_start is None:
                        continue
                    if start and segment_start < start:
                        continue
                    if end and segment_start > end:
                        continue
                    duration = self._segment_duration(key)
                    url = self._client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket, "Key": key},
                        ExpiresIn=3600,
                    )
                    results.append(
                        {"start": segment_start, "duration": duration, "url": url}
                    )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable(f"falha ao listar gravações no R2: {exc}") from exc
        results.sort(key=lambda item: item["start"])
        return results

    def _segment_duration(self, key: str) -> float:
        try:
            head = self._client.head_object(Bucket=self.bucket, Key=key)
            return float(head.get("Metadata", {}).get("duration", 0) or 0)
        except (BotoCoreError, ClientError):
            return 0.0

    def purge_expired(self, retention_hours: int) -> int:
        if not self._client:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
        removed = 0
        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket):
                stale = [
                    {"Key": item["Key"]}
                    for item in page.get("Contents", [])
                    if item["LastModified"] < cutoff
                ]
                if not stale:
                    continue
                self._client.delete_objects(
                    Bucket=self.bucket, Delete={"Objects": stale}
                )
                removed += len(stale)
        except (BotoCoreError, ClientError) as exc:
            logger.warning("falha ao expurgar gravações antigas no R2: %s", exc)
        return removed


storage = R2Storage()
