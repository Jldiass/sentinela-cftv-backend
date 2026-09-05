#!/usr/bin/env python3
"""Invoked by MediaMTX's runOnRecordSegmentComplete for each finished segment.

Uploads the segment to Cloudflare R2 and deletes the local copy on success,
so the Railway volume only ever holds a short safety buffer instead of a
full hour of footage. If R2 is unreachable or unconfigured, the local file
is left in place and MediaMTX's own recordDeleteAfter eventually reclaims
the disk space.

Environment variables (set by MediaMTX): MTX_PATH, MTX_SEGMENT_PATH,
MTX_SEGMENT_DURATION.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.storage import StorageUnavailable, storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cftv.upload_segment")


def main() -> int:
    path = os.environ.get("MTX_PATH")
    segment_path = os.environ.get("MTX_SEGMENT_PATH")
    duration = os.environ.get("MTX_SEGMENT_DURATION", "0")
    if not path or not segment_path:
        logger.error("MTX_PATH/MTX_SEGMENT_PATH ausentes; nada a enviar")
        return 1
    if not storage.is_configured:
        logger.info("R2 não configurado; mantendo segmento local %s", segment_path)
        return 0

    key = f"{path}/{os.path.basename(segment_path)}"
    try:
        storage.upload_segment(segment_path, key, duration)
    except StorageUnavailable as exc:
        logger.warning("upload falhou, mantendo cópia local: %s", exc)
        return 0

    try:
        os.remove(segment_path)
    except OSError as exc:
        logger.warning("upload ok mas falha ao remover cópia local: %s", exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
