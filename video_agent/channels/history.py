"""History channel preset: cinematic 16:9, slow pace, sepia grade."""
from __future__ import annotations

from .base import CaptionStyle, ChannelPreset

HISTORY = ChannelPreset(
    name="history",
    width=1920,
    height=1080,
    fps=30,

    # Slow, documentary pacing.
    seconds_per_image=8.0,

    # Gentle, cinematic Ken Burns.
    zoom_start=1.0,
    zoom_end=1.15,
    default_pans=(
        "zoom-in",
        "left-to-right",
        "right-to-left",
        "top-to-bottom",
    ),

    # Long, smooth crossfades.
    crossfade_seconds=1.5,
    transition="fade",

    # Subtle sepia grade: desaturate slightly, warm the mids, darken shadows.
    #   eq          — saturation / brightness / contrast / gamma
    #   colorbalance — shift mid-tones toward red / yellow for sepia warmth
    color_grade=(
        "eq=saturation=0.75:contrast=1.05:brightness=-0.02,"
        "colorbalance=rm=0.05:gm=0.00:bm=-0.05"
    ),

    caption=CaptionStyle(
        font="DejaVu Serif",       # swap to "EB Garamond" if installed
        font_size=48,
        primary_color="white",
        outline_color="black",
        outline_width=3,
        box=False,
        y_position="h-th-100",
    ),

    music_gain_db=-20.0,          # music sits well behind narration
    video_crf=18,
    video_preset="slow",          # quality over encode speed
)
