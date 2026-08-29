import logging
from datetime import datetime, timezone

import httpx

from ..config import settings

logger = logging.getLogger("cftv.mediamtx")


class MediaMTXUnavailable(RuntimeError):
    pass


class MediaMTXClient:
    def __init__(self, api_url: str | None = None, playback_url: str | None = None):
        self.api_url = (api_url or settings.mediamtx_api_url).rstrip("/")
        self.playback_url = (playback_url or settings.mediamtx_playback_url).rstrip("/")

    async def path_statuses(self) -> dict[str, str]:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"{self.api_url}/v3/paths/list")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("control API unavailable: %s", exc)
            raise MediaMTXUnavailable from exc

        now = datetime.now(timezone.utc)
        statuses: dict[str, str] = {}
        for item in response.json().get("items", []):
            if not item.get("ready"):
                continue
            status = "online"
            ready_time = item.get("readyTime")
            if ready_time:
                try:
                    connected_at = datetime.fromisoformat(
                        ready_time.replace("Z", "+00:00")
                    )
                    if (
                        now - connected_at
                    ).total_seconds() < settings.unstable_after_seconds:
                        status = "unstable"
                except ValueError:
                    logger.debug("invalid readyTime for path %s", item.get("name"))
            statuses[item["name"]] = status
        return statuses

    async def list_recordings(
        self, path: str, start: datetime | None, end: datetime | None
    ) -> list[dict]:
        params: dict[str, str] = {"path": path}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.playback_url}/list", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.warning("playback API unavailable: %s", exc)
            raise MediaMTXUnavailable from exc


mediamtx = MediaMTXClient()
