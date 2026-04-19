"""Channel preset dataclass.

A ChannelPreset fully describes the visual + audio identity of an output
video: its aspect ratio, pacing, motion style, color grade, caption style,
and music behavior. The pipeline consumes a preset and produces a render
plan from it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PanDirection = Literal[
    "zoom-in",
    "zoom-out",
    "left-to-right",
    "right-to-left",
    "top-to-bottom",
    "bottom-to-top",
]


@dataclass(frozen=True)
class CaptionStyle:
    """Typography for burnt-in captions (drawtext / subtitles filter)."""

    font: str = "DejaVu Sans"
    font_size: int = 42
    primary_color: str = "white"       # drawtext fontcolor
    outline_color: str = "black"
    outline_width: int = 3
    box: bool = False                  # translucent background box
    box_color: str = "black@0.4"
    y_position: str = "h-th-80"        # drawtext y= expression (bottom padded)


@dataclass(frozen=True)
class ChannelPreset:
    name: str
    width: int
    height: int
    fps: int = 30

    # Pacing (seconds per image when no manifest is supplied)
    seconds_per_image: float = 6.0

    # Ken Burns motion
    zoom_start: float = 1.0
    zoom_end: float = 1.15
    default_pans: tuple[PanDirection, ...] = (
        "zoom-in", "left-to-right", "right-to-left", "zoom-out",
    )

    # Transitions between clips
    crossfade_seconds: float = 1.0
    # See https://ffmpeg.org/ffmpeg-filters.html#xfade for valid transitions.
    transition: str = "fade"

    # Color grade — any ffmpeg filter string applied after scaling.
    # Empty string means "no grade".
    color_grade: str = ""

    # Captions
    caption: CaptionStyle = field(default_factory=CaptionStyle)

    # Background music
    music_gain_db: float = -18.0

    # Output encoder knobs
    video_codec: str = "libx264"
    video_crf: int = 18          # lower = higher quality
    video_preset: str = "medium"
    pixel_format: str = "yuv420p"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    @property
    def resolution(self) -> tuple[int, int]:
        return (self.width, self.height)

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    def __repr__(self) -> str:
        return (
            f"ChannelPreset(name={self.name!r}, "
            f"{self.width}x{self.height}@{self.fps}fps, "
            f"seconds_per_image={self.seconds_per_image})"
        )
