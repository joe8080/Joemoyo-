"""Audio utilities: probing duration. Audio filter-graph composition lives
in ``pipeline.py`` where it needs to reference the video input indices.
"""
from __future__ import annotations

from pathlib import Path

from .utils.ffmpeg import ffprobe_json


def probe_duration(path: str | Path) -> float:
    """Return the duration of an audio (or video) file in seconds."""
    meta = ffprobe_json(path)
    # Prefer the container-level duration; fall back to the first stream.
    fmt = meta.get("format") or {}
    if "duration" in fmt:
        return float(fmt["duration"])
    for stream in meta.get("streams", []):
        if "duration" in stream:
            return float(stream["duration"])
    raise ValueError(f"Could not determine duration of {path!r}")
