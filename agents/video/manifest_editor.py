"""ManifestEditorAgent: deterministic assembly of the render contract.

Takes the Visual Director's shot list (+ optional narration length) and emits:
  - manifest.json  — the video_agent clips[] schema (image/duration/pan/caption)
  - captions.srt   — burnt-in captions timed to the joined (xfaded) timeline

This is pure Python (no LLM) so it is fully testable and never "pops": each
clip is clamped to >= 2*crossfade + 0.5s, matching the Ken Burns guard.
"""

from __future__ import annotations

from agents.video._utils import slugify

_VALID_PANS = {
    "zoom-in", "zoom-out", "left-to-right",
    "right-to-left", "top-to-bottom", "bottom-to-top",
}


def _image_filename(clip: dict) -> str:
    """Stable NN_slug.png filename for a shot."""
    seq = int(clip.get("sequence", 0))
    hint = clip.get("entity_hint") or clip.get("caption") or f"shot{seq}"
    return f"{seq:02d}_{slugify(str(hint), 40)}.png"


def _fmt_ts(seconds: float) -> str:
    """Seconds -> SRT timestamp HH:MM:SS,mmm."""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class ManifestEditorAgent:
    """Deterministic editor — owns manifest.json + captions.srt."""

    def __init__(self, crossfade: float = 1.0):
        self.crossfade = crossfade
        self.min_duration = max(1.0, crossfade * 2 + 0.5)

    def assemble(self, shotlist: dict, narration_seconds: float | None = None) -> dict:
        """Return {'manifest': {...}, 'srt': '...', 'image_plan': [...]}.

        image_plan pairs each clip's target filename with its image_prompt so the
        producer can generate the stills.
        """
        clips = shotlist.get("clips", [])
        if not clips:
            raise ValueError("shotlist has no clips")

        durations = [float(c.get("duration") or self.min_duration) for c in clips]

        # Fit total visible timeline to the narration length, if known.
        if narration_seconds and narration_seconds > 0:
            n = len(clips)
            current_total = sum(durations) - self.crossfade * (n - 1)
            if current_total > 0:
                scale = (narration_seconds + self.crossfade * (n - 1)) / (
                    sum(durations)
                )
                durations = [d * scale for d in durations]

        durations = [max(d, self.min_duration) for d in durations]

        manifest_clips = []
        image_plan = []
        for clip, dur in zip(clips, durations):
            pan = clip.get("pan")
            if pan not in _VALID_PANS:
                pan = "zoom-in"
            fname = _image_filename(clip)
            manifest_clips.append({
                "image": fname,
                "duration": round(dur, 2),
                "pan": pan,
                "caption": clip.get("caption", ""),
            })
            image_plan.append({
                "image": fname,
                "image_prompt": clip.get("image_prompt", ""),
                "entity_hint": clip.get("entity_hint"),
            })

        srt = self._build_srt(manifest_clips)
        return {
            "manifest": {"clips": manifest_clips},
            "srt": srt,
            "image_plan": image_plan,
        }

    def _build_srt(self, clips: list[dict]) -> str:
        """Caption each clip across its window on the xfaded timeline."""
        entries = []
        idx = 1
        cumulative = 0.0
        for i, clip in enumerate(clips):
            # offset_i = sum(dur[:i]) - i*crossfade
            start = cumulative - i * self.crossfade
            start = max(start, 0.0)
            end = start + clip["duration"]
            cumulative += clip["duration"]
            caption = (clip.get("caption") or "").strip()
            if not caption:
                continue
            entries.append(
                f"{idx}\n{_fmt_ts(start)} --> {_fmt_ts(end)}\n{caption}\n"
            )
            idx += 1
        return "\n".join(entries)
