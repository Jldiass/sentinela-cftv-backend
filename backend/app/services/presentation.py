from urllib.parse import urlencode

from ..config import settings
from ..models import Camera, Event
from ..schemas import CameraOut, EventOut, RecordingOut, StreamCredentials


def stream_credentials(camera: Camera) -> StreamCredentials:
    return StreamCredentials(
        camera_id=camera.id,
        stream_key=camera.stream_key,
        rtmp_url=(
            f"{settings.clean_base_url(settings.public_rtmp_base_url)}/"
            f"{camera.stream_key}"
        ),
        hls_url=(
            f"{settings.clean_base_url(settings.public_hls_base_url)}/"
            f"{camera.stream_key}/index.m3u8"
        ),
    )


def camera_output(camera: Camera, status: str = "offline") -> CameraOut:
    credentials = stream_credentials(camera)
    return CameraOut(
        id=camera.id,
        name=camera.name,
        location=camera.location,
        audio_enabled=camera.audio_enabled,
        retention_days=camera.retention_days,
        pre_alarm_seconds=camera.pre_alarm_seconds,
        post_alarm_seconds=camera.post_alarm_seconds,
        stream_key=camera.stream_key,
        enabled=camera.enabled,
        created_at=camera.created_at,
        status=status,
        rtmp_url=credentials.rtmp_url,
        hls_url=credentials.hls_url,
        effective_retention_hours=settings.effective_retention_hours,
    )


def playback_url(path: str, start, duration: float) -> str:
    start_value = start.isoformat() if hasattr(start, "isoformat") else start
    query = urlencode(
        {"path": path, "start": start_value, "duration": duration, "format": "mp4"}
    )
    base_url = settings.clean_base_url(settings.public_playback_base_url)
    return f"{base_url}/get?{query}"


def recording_output(camera: Camera, row: dict) -> RecordingOut:
    return RecordingOut(
        start=row["start"],
        duration=row["duration"],
        url=playback_url(camera.stream_key, row["start"], row["duration"]),
    )


def event_output(event: Event, camera: Camera) -> EventOut:
    return EventOut(
        id=event.id,
        camera_id=event.camera_id,
        kind=event.kind,
        note=event.note,
        happened_at=event.happened_at,
        clip_start=event.clip_start,
        clip_duration=event.clip_duration,
        playback_url=playback_url(
            camera.stream_key, event.clip_start, event.clip_duration
        ),
    )
