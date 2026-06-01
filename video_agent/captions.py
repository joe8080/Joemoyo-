"""Caption rendering. Two modes:

1. ``.srt`` subtitle file → burn in with the ``subtitles`` filter.
2. Per-clip captions from a manifest → ``drawtext`` overlay on each clip.
"""
from __future__ import annotations

from pathlib import Path

from .channels.base import CaptionStyle
from .utils.ffmpeg import quote_filter_path


def build_subtitles_filter(srt_path: str | Path, style: CaptionStyle) -> str:
    """Return a ``subtitles=...`` filter that burns an SRT into the video.

    We pass ``force_style`` so the SRT's own styling is overridden by the
    channel preset's caption style — this keeps the look consistent even
    if a script editor hand-authored the SRT with arbitrary formatting.
    """
    # force_style uses ASS color format: &HBBGGRR (BGR, no alpha). We keep
    # the user-facing API in terms of simple named colors by only wiring
    # through the font + size + outline; a fuller mapping can be added later.
    force_style = (
        f"FontName={style.font},"
        f"FontSize={style.font_size},"
        f"Outline={style.outline_width},"
        f"BorderStyle=1"
    )
    escaped_path = quote_filter_path(srt_path)
    escaped_style = force_style.replace(",", "\\,")
    return f"subtitles='{escaped_path}':force_style='{escaped_style}'"


def build_drawtext_filter(text: str, style: CaptionStyle) -> str:
    """Return a ``drawtext=...`` filter rendering a single caption string."""
    # drawtext's text= value needs colons and backslashes and single quotes
    # escaped. We wrap the text in single quotes and escape as needed.
    escaped_text = (
        text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\\\\\'")
    )
    parts = [
        f"text='{escaped_text}'",
        f"font='{style.font}'",
        f"fontsize={style.font_size}",
        f"fontcolor={style.primary_color}",
        f"bordercolor={style.outline_color}",
        f"borderw={style.outline_width}",
        "x=(w-text_w)/2",
        f"y={style.y_position}",
    ]
    if style.box:
        parts += ["box=1", f"boxcolor={style.box_color}", "boxborderw=20"]
    return "drawtext=" + ":".join(parts)
