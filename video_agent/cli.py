"""Command-line interface for video_agent."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .channels import available_channels, get_preset
from .pipeline import plan_render, render
from .utils.manifest import load_manifest


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="video-agent",
        description=(
            "Turn a folder of images + an audio track into a cinematic "
            "video with Ken Burns motion."
        ),
    )
    p.add_argument("--version", action="version", version=f"video-agent {__version__}")
    p.add_argument(
        "--channel",
        required=True,
        choices=available_channels(),
        help="Channel preset (resolution, pace, grade, caption style).",
    )
    p.add_argument("--images", required=True, help="Directory of input images.")
    p.add_argument("--audio", required=True, help="Narration audio file.")
    p.add_argument("--music", default=None, help="Optional background music bed.")
    p.add_argument("--captions", default=None, help="Optional .srt subtitle file.")
    p.add_argument("--manifest", default=None, help="Optional JSON manifest.")
    p.add_argument("--out", required=True, help="Output .mp4 path.")
    p.add_argument("--seconds-per-image", type=float, default=None,
                   help="Override per-image pace; otherwise auto-fit to audio.")
    p.add_argument("--seed", type=int, default=None,
                   help="Random seed for pan-direction choice.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the plan summary and exit without rendering.")
    return p


def _print_plan(plan) -> None:
    preset = plan.preset
    print(f"Channel preset : {preset.name} ({preset.width}x{preset.height} @ {preset.fps}fps)")
    print(f"Output         : {plan.output}")
    print(f"Narration      : {plan.narration}")
    if plan.music:
        print(f"Music bed      : {plan.music} @ {plan.music_gain_db:g} dB")
    if plan.srt:
        print(f"Captions (SRT) : {plan.srt}")
    print(f"Clips          : {len(plan.clips)}")
    print(f"Crossfade      : {plan.crossfade:g}s")
    print(f"Expected length: {plan.expected_duration:.2f}s")
    print()
    for i, c in enumerate(plan.clips):
        cap = f"  — {c.caption}" if c.caption else ""
        print(f"  [{i:02d}] {c.image.name:<30} {c.duration:6.2f}s  pan={c.pan}{cap}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    preset = get_preset(args.channel)
    manifest = load_manifest(args.manifest) if args.manifest else None

    plan = plan_render(
        preset=preset,
        images_dir=args.images,
        narration=args.audio,
        output=args.out,
        music=args.music,
        captions_srt=args.captions,
        manifest=manifest,
        seconds_per_image=args.seconds_per_image,
        seed=args.seed,
    )

    _print_plan(plan)

    if args.dry_run:
        print("\n(dry run — not rendering)")
        return 0

    print("\nRendering...")
    out = render(plan)
    print(f"Done: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
