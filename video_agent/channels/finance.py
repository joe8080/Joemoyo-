"""AI-finance channel presets: punchy, saturated, chart-friendly.

Two sub-presets are exported:

- ``FINANCE_LONG``  — 1920x1080 for long-form YouTube episodes.
- ``FINANCE_SHORT`` — 1080x1920 @ 60fps for Shorts / TikTok / Reels.
"""
from __future__ import annotations

from .base import CaptionStyle, ChannelPreset

# Shared look for both long and short finance variants.
_FINANCE_GRADE = (
    "eq=saturation=1.20:contrast=1.10:brightness=0.02,"
    "unsharp=3:3:0.6"             # subtle sharpen — charts read better
)

_FINANCE_CAPTION = CaptionStyle(
    font="DejaVu Sans",            # swap to "Inter Bold" if installed
    font_size=56,
    primary_color="white",
    outline_color="black",
    outline_width=4,
    box=True,
    box_color="black@0.55",
    y_position="h-th-120",
)


FINANCE_LONG = ChannelPreset(
    name="finance.long",
    width=1920,
    height=1080,
    fps=30,

    seconds_per_image=4.0,

    zoom_start=1.0,
    zoom_end=1.25,
    default_pans=(
        "zoom-in",
        "left-to-right",
        "right-to-left",
        "zoom-out",
    ),

    crossfade_seconds=0.35,
    transition="fade",

    color_grade=_FINANCE_GRADE,
    caption=_FINANCE_CAPTION,

    music_gain_db=-16.0,           # bed sits a bit hotter than history
    video_crf=19,
    video_preset="medium",
)


FINANCE_SHORT = ChannelPreset(
    name="finance.short",
    width=1080,
    height=1920,                   # vertical 9:16
    fps=60,                        # smoother motion for phones

    seconds_per_image=3.0,

    zoom_start=1.0,
    zoom_end=1.30,
    default_pans=(
        "zoom-in",
        "zoom-out",
        "top-to-bottom",
        "bottom-to-top",
    ),

    crossfade_seconds=0.25,
    transition="fade",

    color_grade=_FINANCE_GRADE,
    caption=CaptionStyle(
        font=_FINANCE_CAPTION.font,
        font_size=72,              # bigger on vertical
        primary_color="white",
        outline_color="black",
        outline_width=5,
        box=True,
        box_color="black@0.55",
        y_position="h/2-th/2",     # center on vertical — reads above thumb
    ),

    music_gain_db=-14.0,
    video_crf=20,
    video_preset="fast",
)
