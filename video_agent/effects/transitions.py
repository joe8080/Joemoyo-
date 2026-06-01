"""Build the filter_complex graph that crossfades a sequence of clips.

Given N rendered Ken Burns clips with individual durations d0..d(N-1) and
a desired crossfade length ``x`` seconds, the final video length is:

    total = sum(d_i) - (N - 1) * x

Each consecutive pair is joined with an ``xfade`` filter whose ``offset``
is the point at which the next clip should start fading in, measured on
the accumulated timeline of everything already joined.
"""
from __future__ import annotations

from typing import Iterable


def total_duration(durations: Iterable[float], crossfade: float) -> float:
    """Compute the final timeline length after N-1 crossfades."""
    d = list(durations)
    if not d:
        return 0.0
    return sum(d) - crossfade * (len(d) - 1)


def build_xfade_graph(
    durations: list[float],
    *,
    crossfade: float,
    transition: str = "fade",
) -> tuple[str, str]:
    """Return (filter_complex, final_video_label).

    Inputs are expected to be the first ``len(durations)`` ffmpeg ``-i``
    inputs, each a rendered Ken Burns clip. The returned filter_complex
    chains xfade operations and labels the final stream so the outer
    command can map it with ``-map '[vout]'``.
    """
    n = len(durations)
    if n == 0:
        raise ValueError("need at least one clip")
    if n == 1:
        # Single clip — no fades needed. Just pass through with a label.
        return ("[0:v]copy[vout]", "vout")

    if crossfade <= 0:
        # Hard cuts: use concat rather than xfade.
        chain = "".join(f"[{i}:v]" for i in range(n))
        return (f"{chain}concat=n={n}:v=1:a=0[vout]", "vout")

    # Build the xfade chain. ``offset_i`` is the absolute time on the
    # running-joined timeline at which clip i+1 should start fading in.
    lines: list[str] = []
    prev_label = "0:v"
    running = durations[0]
    for i in range(1, n):
        offset = running - crossfade
        out_label = "vout" if i == n - 1 else f"vx{i}"
        lines.append(
            f"[{prev_label}][{i}:v]"
            f"xfade=transition={transition}:duration={crossfade:g}:offset={offset:g}"
            f"[{out_label}]"
        )
        # After the fade, the joined clip's effective length is:
        #   running + durations[i] - crossfade
        running = running + durations[i] - crossfade
        prev_label = out_label

    return (";".join(lines), "vout")
