"""Optional JSON manifest describing per-clip overrides.

Format:

    {
      "clips": [
        {"image": "01.jpg", "duration": 8.0, "pan": "left-to-right", "caption": "..."},
        {"image": "02.jpg", "duration": 6.5, "pan": "zoom-in"}
      ]
    }

All per-clip fields are optional except ``image``. Missing values fall back
to the channel preset defaults and the auto-distributed durations.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..channels.base import PanDirection

_VALID_PANS: frozenset[str] = frozenset({
    "zoom-in", "zoom-out",
    "left-to-right", "right-to-left",
    "top-to-bottom", "bottom-to-top",
})


@dataclass
class ClipSpec:
    image: str
    duration: float | None = None
    pan: PanDirection | None = None
    caption: str | None = None


@dataclass
class Manifest:
    clips: list[ClipSpec]


class ManifestError(ValueError):
    pass


def load_manifest(path: str | Path) -> Manifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_manifest(data)


def parse_manifest(data: dict) -> Manifest:
    if not isinstance(data, dict) or "clips" not in data:
        raise ManifestError("manifest must be an object with a 'clips' array")
    raw_clips = data["clips"]
    if not isinstance(raw_clips, list) or not raw_clips:
        raise ManifestError("'clips' must be a non-empty array")

    out: list[ClipSpec] = []
    for i, raw in enumerate(raw_clips):
        if not isinstance(raw, dict) or "image" not in raw:
            raise ManifestError(f"clip[{i}] must be an object with an 'image' field")
        pan = raw.get("pan")
        if pan is not None and pan not in _VALID_PANS:
            raise ManifestError(
                f"clip[{i}] has invalid pan {pan!r}. "
                f"Valid options: {sorted(_VALID_PANS)}"
            )
        duration = raw.get("duration")
        if duration is not None:
            try:
                duration = float(duration)
            except (TypeError, ValueError):
                raise ManifestError(f"clip[{i}].duration must be a number")
            if duration <= 0:
                raise ManifestError(f"clip[{i}].duration must be > 0")
        out.append(
            ClipSpec(
                image=str(raw["image"]),
                duration=duration,
                pan=pan,
                caption=raw.get("caption"),
            )
        )
    return Manifest(clips=out)
