"""End-to-end render pipeline.

The pipeline is split into three pure planning functions and one
side-effecting ``render`` function. The planning functions are easy to
unit-test without needing ffmpeg installed; ``render`` just executes the
plan.
"""
from __future__ import annotations

import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .audio import probe_duration
from .captions import build_subtitles_filter
from .channels.base import ChannelPreset, PanDirection
from .effects.ken_burns import build_clip_ffmpeg_args
from .effects.transitions import build_xfade_graph, total_duration
from .utils.ffmpeg import run_ffmpeg
from .utils.manifest import ClipSpec, Manifest

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


@dataclass
class PlannedClip:
    image: Path
    duration: float
    pan: PanDirection
    caption: str | None = None


@dataclass
class RenderPlan:
    preset: ChannelPreset
    clips: list[PlannedClip]
    narration: Path
    music: Path | None
    srt: Path | None
    output: Path
    crossfade: float
    music_gain_db: float

    @property
    def expected_duration(self) -> float:
        return total_duration(
            [c.duration for c in self.clips], self.crossfade
        )


def discover_images(folder: str | Path) -> list[Path]:
    """Return a sorted list of image paths in ``folder``."""
    p = Path(folder)
    if not p.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")
    imgs = sorted(
        x for x in p.iterdir()
        if x.is_file() and x.suffix.lower() in IMAGE_EXTS
    )
    if not imgs:
        raise ValueError(f"No images found in {folder}")
    return imgs


def distribute_durations(
    *,
    narration_seconds: float,
    n_clips: int,
    preset: ChannelPreset,
    crossfade: float,
    seconds_per_image: float | None = None,
) -> list[float]:
    """Spread per-image durations so the joined video matches the narration.

    The total timeline after N-1 crossfades equals
    ``sum(durations) - (N-1)*crossfade``. We want that to equal the
    narration length, so each image gets:

        d = (narration + (N-1)*crossfade) / N

    If the user supplied an explicit ``seconds_per_image`` we honor it
    directly and ignore narration length (the narration may end early and
    the tail of the video will play silent — that's the user's choice).
    """
    if n_clips <= 0:
        raise ValueError("n_clips must be positive")

    if seconds_per_image is not None:
        return [seconds_per_image] * n_clips

    # Auto-fit to narration length, with a sanity floor.
    fitted = (narration_seconds + crossfade * (n_clips - 1)) / n_clips
    min_d = max(1.0, crossfade * 2 + 0.5)
    return [max(fitted, min_d)] * n_clips


def plan_clips(
    *,
    images: Sequence[Path],
    preset: ChannelPreset,
    durations: Sequence[float],
    manifest: Manifest | None,
    seed: int | None,
) -> list[PlannedClip]:
    """Combine discovered images, auto durations, and manifest overrides."""
    rng = random.Random(seed)
    pans_cycle = list(preset.default_pans)

    if manifest is None:
        planned: list[PlannedClip] = []
        for i, img in enumerate(images):
            # Deterministic pick when seed is provided, otherwise round-robin.
            pan = rng.choice(pans_cycle) if seed is not None else pans_cycle[i % len(pans_cycle)]
            planned.append(PlannedClip(image=img, duration=durations[i], pan=pan))
        return planned

    # Manifest drives the clip list (order + count). Images are resolved
    # relative to each manifest clip's ``image`` field; if it's a bare
    # filename we look it up inside the images directory.
    images_by_name = {p.name: p for p in images}
    images_dir = images[0].parent if images else None

    planned: list[PlannedClip] = []
    for i, spec in enumerate(manifest.clips):
        img_path = Path(spec.image)
        if not img_path.is_absolute() and not img_path.exists():
            if images_dir is not None:
                candidate = images_dir / spec.image
                if candidate.exists():
                    img_path = candidate
                elif spec.image in images_by_name:
                    img_path = images_by_name[spec.image]
        pan = spec.pan or (
            rng.choice(pans_cycle) if seed is not None else pans_cycle[i % len(pans_cycle)]
        )
        duration = spec.duration if spec.duration is not None else durations[i % len(durations)]
        planned.append(
            PlannedClip(image=img_path, duration=duration, pan=pan, caption=spec.caption)
        )
    return planned


def plan_render(
    *,
    preset: ChannelPreset,
    images_dir: str | Path,
    narration: str | Path,
    output: str | Path,
    music: str | Path | None = None,
    captions_srt: str | Path | None = None,
    manifest: Manifest | None = None,
    seconds_per_image: float | None = None,
    seed: int | None = None,
) -> RenderPlan:
    """Build a RenderPlan without touching ffmpeg (except ffprobe for duration)."""
    images = discover_images(images_dir)
    narration_path = Path(narration)
    narration_seconds = probe_duration(narration_path)

    n_clips = len(manifest.clips) if manifest is not None else len(images)
    durations = distribute_durations(
        narration_seconds=narration_seconds,
        n_clips=n_clips,
        preset=preset,
        crossfade=preset.crossfade_seconds,
        seconds_per_image=seconds_per_image,
    )

    clips = plan_clips(
        images=images,
        preset=preset,
        durations=durations,
        manifest=manifest,
        seed=seed,
    )

    return RenderPlan(
        preset=preset,
        clips=clips,
        narration=narration_path,
        music=Path(music) if music else None,
        srt=Path(captions_srt) if captions_srt else None,
        output=Path(output),
        crossfade=preset.crossfade_seconds,
        music_gain_db=preset.music_gain_db,
    )


def _build_final_ffmpeg_args(
    plan: RenderPlan,
    clip_files: list[Path],
    work_dir: Path,
) -> list[str]:
    """Build the ffmpeg invocation that joins clips and muxes audio."""
    preset = plan.preset
    inputs: list[str] = []
    for cf in clip_files:
        inputs.extend(["-i", str(cf)])

    n_video_inputs = len(clip_files)

    # Audio inputs after the video clips.
    narration_idx = n_video_inputs
    inputs.extend(["-i", str(plan.narration)])
    music_idx: int | None = None
    if plan.music is not None:
        music_idx = n_video_inputs + 1
        inputs.extend(["-i", str(plan.music)])

    # --- Video filter graph -------------------------------------------------
    video_graph, v_label = build_xfade_graph(
        [c.duration for c in plan.clips],
        crossfade=plan.crossfade,
        transition=preset.transition,
    )

    if plan.srt is not None:
        # Burn subtitles after the fades so they appear on the joined stream.
        sub_filter = build_subtitles_filter(plan.srt, preset.caption)
        video_graph = f"{video_graph};[{v_label}]{sub_filter}[vsub]"
        v_label = "vsub"

    # --- Audio filter graph -------------------------------------------------
    total = plan.expected_duration
    if music_idx is None:
        audio_graph = (
            f"[{narration_idx}:a]apad,atrim=0:{total:g},asetpts=PTS-STARTPTS[aout]"
        )
    else:
        audio_graph = (
            f"[{narration_idx}:a]apad,atrim=0:{total:g},asetpts=PTS-STARTPTS[narr];"
            f"[{music_idx}:a]volume={plan.music_gain_db:g}dB,"
            f"aloop=loop=-1:size=2e+09,atrim=0:{total:g},asetpts=PTS-STARTPTS[bed];"
            f"[narr][bed]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
        )

    filter_complex = f"{video_graph};{audio_graph}"

    args: list[str] = []
    args.extend(inputs)
    args.extend([
        "-filter_complex", filter_complex,
        "-map", f"[{v_label}]",
        "-map", "[aout]",
        "-c:v", preset.video_codec,
        "-preset", preset.video_preset,
        "-crf", str(preset.video_crf),
        "-pix_fmt", preset.pixel_format,
        "-c:a", preset.audio_codec,
        "-b:a", preset.audio_bitrate,
        "-movflags", "+faststart",
        "-r", str(preset.fps),
        str(plan.output),
    ])
    _ = work_dir  # work_dir not needed for the final mux but kept for symmetry
    return args


def render(plan: RenderPlan, *, work_dir: Path | None = None) -> Path:
    """Execute a RenderPlan: render per-clip mp4s, then join with audio."""
    plan.output.parent.mkdir(parents=True, exist_ok=True)

    ctx_wd: tempfile.TemporaryDirectory | None = None
    if work_dir is None:
        ctx_wd = tempfile.TemporaryDirectory(prefix="video_agent_")
        wd = Path(ctx_wd.name)
    else:
        wd = Path(work_dir)
        wd.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Render each Ken Burns clip individually.
        clip_files: list[Path] = []
        for i, clip in enumerate(plan.clips):
            out = wd / f"clip_{i:04d}.mp4"
            run_ffmpeg(
                build_clip_ffmpeg_args(
                    image=str(clip.image),
                    output=str(out),
                    preset=plan.preset,
                    duration=clip.duration,
                    pan=clip.pan,
                )
            )
            clip_files.append(out)

        # 2. Join clips with xfades and mux audio in a single ffmpeg call.
        run_ffmpeg(_build_final_ffmpeg_args(plan, clip_files, wd))
    finally:
        if ctx_wd is not None:
            ctx_wd.cleanup()

    return plan.output
