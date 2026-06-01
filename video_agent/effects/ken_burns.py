"""Build the ffmpeg filter string that applies a Ken Burns effect to a still image.

The classic zoompan jitter problem: zoompan operates at integer pixel
positions on the *input* frame, so small per-frame zoom increments on a
1080p still produce visible stepping. The fix used throughout this module
is to **pre-upscale the input by 4x** before feeding it into zoompan, then
let zoompan output at the target resolution. The large source frame gives
zoompan plenty of sub-pixel headroom to produce smooth motion.
"""
from __future__ import annotations

from typing import Literal

from ..channels.base import ChannelPreset, PanDirection

# Factor we pre-upscale the still by before zoompan. 4x is enough to make
# motion appear sub-pixel smooth without blowing up memory. Must be >= 2.
UPSCALE_FACTOR = 4


def _zoom_expr(start: float, end: float, total_frames: int) -> str:
    """Return a zoompan ``z=`` expression ramping from start to end.

    ``on`` is the 0-indexed output frame counter; we clamp with ``min`` so a
    rounding overrun on the last frame doesn't pop past the target zoom.
    """
    delta = end - start
    # Guard against zero-frame clips (fractional durations rounded down).
    frames = max(total_frames - 1, 1)
    return f"'min({start:.4f}+{delta:.6f}*on/{frames},{end:.4f})'"


def _pan_expressions(pan: PanDirection) -> tuple[str, str]:
    """Return (x_expr, y_expr) for zoompan for a given pan direction.

    Coordinate system: zoompan's x/y expressions reference ``iw``/``ih``
    (input width/height) and ``zoom`` (current zoom factor). The visible
    window is ``iw/zoom`` wide by ``ih/zoom`` tall.
    """
    if pan == "zoom-in" or pan == "zoom-out":
        # Centered zoom.
        return ("iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")

    if pan == "left-to-right":
        # x sweeps from 0 (left edge) to iw-iw/zoom (right edge) over the clip.
        return ("(iw-iw/zoom)*on/max(1,d-1)", "ih/2-(ih/zoom/2)")

    if pan == "right-to-left":
        return ("(iw-iw/zoom)*(1-on/max(1,d-1))", "ih/2-(ih/zoom/2)")

    if pan == "top-to-bottom":
        return ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*on/max(1,d-1)")

    if pan == "bottom-to-top":
        return ("iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/max(1,d-1))")

    raise ValueError(f"Unknown pan direction: {pan!r}")


def build_ken_burns_filter(
    *,
    preset: ChannelPreset,
    duration: float,
    pan: PanDirection,
    reverse_zoom: bool = False,
) -> str:
    """Return a filter-graph string for a single Ken Burns still clip.

    The returned string is meant to be used as the value of ``-vf`` on a
    single-input ffmpeg invocation that reads one image at ``-loop 1``.

    Args:
      preset: Channel preset providing resolution, fps, and zoom range.
      duration: Clip duration in seconds.
      pan: Direction of motion.
      reverse_zoom: If True, zoom from ``zoom_end`` down to ``zoom_start``
        (used for zoom-out motion).
    """
    if duration <= 0:
        raise ValueError(f"duration must be > 0, got {duration}")

    fps = preset.fps
    w, h = preset.resolution
    total_frames = max(int(round(duration * fps)), 1)

    if reverse_zoom or pan == "zoom-out":
        z_start, z_end = preset.zoom_end, preset.zoom_start
    else:
        z_start, z_end = preset.zoom_start, preset.zoom_end

    z_expr = _zoom_expr(z_start, z_end, total_frames)
    x_expr, y_expr = _pan_expressions(pan)

    # Build the filter chain:
    #   1. scale up by UPSCALE_FACTOR for sub-pixel smoothness
    #   2. zoompan with our motion expressions, rendering directly at target size
    #   3. setsar=1 so downstream concat/xfade doesn't complain about SAR drift
    #   4. optional color grade from the preset
    parts = [
        f"scale=iw*{UPSCALE_FACTOR}:ih*{UPSCALE_FACTOR}:flags=lanczos",
        (
            f"zoompan=z={z_expr}"
            f":x='{x_expr}'"
            f":y='{y_expr}'"
            f":d={total_frames}"
            f":s={w}x{h}"
            f":fps={fps}"
        ),
        "setsar=1",
    ]
    if preset.color_grade:
        parts.append(preset.color_grade)
    return ",".join(parts)


def build_clip_ffmpeg_args(
    *,
    image: str,
    output: str,
    preset: ChannelPreset,
    duration: float,
    pan: PanDirection,
) -> list[str]:
    """Return the full ffmpeg arg list to render one Ken Burns clip."""
    vf = build_ken_burns_filter(preset=preset, duration=duration, pan=pan)
    return [
        "-loop", "1",
        "-t", f"{duration:.3f}",
        "-i", image,
        "-vf", vf,
        "-r", str(preset.fps),
        "-c:v", preset.video_codec,
        "-preset", preset.video_preset,
        "-crf", str(preset.video_crf),
        "-pix_fmt", preset.pixel_format,
        "-an",
        output,
    ]
