"""Command line for the studio."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .util import ENGINE_VERSION, StudioError, fmt_time


def _plan(args):
    from . import project as P, text as T
    pr = P.load(args.project)
    T.add_font_dir(Path(pr["_dir"]) / "fonts")
    plan = P.prepare(pr, print)
    print(f"\n{plan['title']}  |  brand: {plan['kit']['name']}  |  {plan['fps']} fps  |  "
          f"formats: {', '.join(plan['formats'])}")
    print(f"{'#':>3}  {'start':>7}  {'length':>6}  {'voice':>6}  {'in':<11} {'visual':<8} id / first words")
    for i, sc in enumerate(plan["scenes"]):
        vo = f"{sc['vo']['duration']:.1f}s" if sc["vo"] else "-"
        v = sc["visual"]
        vis = v["type"] if v["type"] != "card" else f"card"
        print(f"{i + 1:>3}  {fmt_time(sc['start']):>7}  {sc['dur']:>5.1f}s  {vo:>6}  {sc['transition']:<11} "
              f"{vis:<8} {sc['id']}: {sc['say'][:46]}")
    print(f"\nTotal length {fmt_time(plan['total'])} ({plan['total']:.1f}s), {len(plan['words'])} caption words")
    for n in plan["notes"]:
        print("note: " + n)


def _render(args):
    from .render import render
    res = render(args.project, formats=args.format or None, draft=args.draft, jobs=args.jobs,
                 use_cache=not args.no_cache, out_dir=args.out)
    print("\nFiles:")
    for p in res["outputs"]:
        print("  " + p)
    for k, p in res["extras"].items():
        print(f"  {p}  ({k})")


def _frames(args):
    from .render import stills
    times = [float(x) for x in args.at.split(",")] if args.at else None
    stills(args.project, fmt=args.format, times=times, out_dir=args.out)


def _voices(args):
    from . import voice as V
    print("Free offline voices (provider 'piper'). Any voice from the Piper catalogue also works:")
    for k, v in V.PIPER_VOICES.items():
        print(f"  {k:<40} {v}")
    print("\nFree online voices (provider 'edge', needs internet):")
    for k, v in V.EDGE_VOICES.items():
        print(f"  {k:<40} {v}")
    print("\nYour own audio: set \"audio\" on a scene, or \"voice\": {\"file\": \"narration.mp3\"} for one file.")
    print("Word timing from Whisper is", "ON" if V.whisper_available() else "off (pip install faster-whisper)")


def _options(args):
    from . import brands, captions, layers, project, sources, transitions
    from .audio import SFX_NAMES
    print("brands:      " + ", ".join(brands.KITS))
    print("formats:     " + ", ".join(project.FORMATS))
    print("captions:    " + ", ".join(captions.STYLES))
    print("overlays:    " + ", ".join(layers.OVERLAYS))
    print("motions:     auto, " + ", ".join(sources.MOTIONS))
    print("grades:      " + ", ".join(sources.GRADES))
    print("cards:       " + ", ".join(sources.CARD_STYLES))
    print("transitions: " + ", ".join(transitions.DEFAULT_DURATION))
    print("sfx:         " + ", ".join(SFX_NAMES))


def _new(args):
    from . import brands
    d = Path(args.name)
    if (d / "project.json").exists():
        raise StudioError(f"{d / 'project.json'} already exists.")
    if args.brand not in brands.KITS:
        raise StudioError(f"Unknown brand '{args.brand}'. Options: {', '.join(brands.KITS)}.")
    (d / "assets").mkdir(parents=True, exist_ok=True)
    pr = {
        "title": d.name.replace("-", " ").replace("_", " ").title(),
        "brand": args.brand,
        "formats": ["16:9", "9:16"],
        "voice": {"provider": "piper", "voice": "en_GB-alan-medium"},
        "captions": True,
        "music": "ambient",
        "scenes": [
            {"id": "hook", "say": "Write the opening line here. Make it a question or a bold claim.",
             "overlays": [{"type": "title", "kicker": "Episode 1", "text": "Your headline here"}]},
            {"id": "point", "say": "Each scene has words to say and something to look at.",
             "visual": "gradient",
             "overlays": [{"type": "stat", "value": 1000, "prefix": "£", "label": "A number worth remembering"}]},
            {"id": "close", "say": "Finish with one clear takeaway.",
             "overlays": [{"type": "title", "text": "One clear takeaway", "sub": "Education only. Not financial advice."}]},
        ],
    }
    (d / "project.json").write_text(json.dumps(pr, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created {d / 'project.json'}. Put images and clips in {d / 'assets'}.")
    print(f"Next:  python -m studio render {d}")


def _fix(args):
    from . import fix as F
    res = F.fix(args.input, out=args.out, audio=not args.no_audio, video=not args.no_video,
                strength=args.strength, stabilize=args.stabilize, upscale=args.upscale,
                target_lufs=args.lufs, music=args.music, report_only=args.check)
    print(F.format_report(res))


def _demo(args):
    here = Path(__file__).parent / "examples"
    if not (here / "demo" / "assets" / "flow.mp4").is_file():
        import runpy
        runpy.run_path(str(here / "make_demo_assets.py"), run_name="__main__")
    from .render import render
    res = render(here / "demo", draft=args.draft, out_dir=args.out)
    print("\nFiles:")
    for p in res["outputs"]:
        print("  " + p)


def _clean(args):
    from .render import clear_cache
    clear_cache(args.project)
    print("Cache cleared.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m studio",
                                 description=f"Studio {ENGINE_VERSION}: script-to-video engine and media repair.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("render", help="render a project to finished video(s)")
    p.add_argument("project")
    p.add_argument("--format", action="append", help="16:9, 9:16, 1:1 or 4:5 (repeatable; default: project setting)")
    p.add_argument("--draft", action="store_true", help="fast half-size preview")
    p.add_argument("--jobs", type=int, help="parallel workers")
    p.add_argument("--no-cache", action="store_true", help="redraw every scene")
    p.add_argument("--out", help="output folder (default: <project>/out)")
    p.set_defaults(fn=_render)

    p = sub.add_parser("plan", help="check a project and print its timeline (no render)")
    p.add_argument("project")
    p.set_defaults(fn=_plan)

    p = sub.add_parser("frames", help="save review stills and a contact sheet")
    p.add_argument("project")
    p.add_argument("--format")
    p.add_argument("--at", help="comma-separated times in seconds (default: one per scene)")
    p.add_argument("--out")
    p.set_defaults(fn=_frames)

    p = sub.add_parser("fix", help="repair bad audio and video in a clip or recording")
    p.add_argument("input")
    p.add_argument("--out", help="output file (default: <name>_fixed.<ext>)")
    p.add_argument("--check", action="store_true", help="only diagnose; do not write a file")
    p.add_argument("--strength", choices=["light", "normal", "strong"], default="normal")
    p.add_argument("--no-audio", action="store_true", help="leave the audio untouched")
    p.add_argument("--no-video", action="store_true", help="leave the picture untouched")
    p.add_argument("--stabilize", choices=["auto", "on", "off"], default="auto")
    p.add_argument("--upscale", help="target height, e.g. 1080 or 2160")
    p.add_argument("--lufs", type=float, default=-16.0, help="target loudness (default -16)")
    p.add_argument("--music", action="store_true", help="the audio is music, not speech (skip voice clean-up)")
    p.set_defaults(fn=_fix)

    p = sub.add_parser("new", help="start a new project folder")
    p.add_argument("name")
    p.add_argument("--brand", default="wealth")
    p.set_defaults(fn=_new)

    p = sub.add_parser("demo", help="render the bundled 36-second example")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--out")
    p.set_defaults(fn=_demo)

    p = sub.add_parser("voices", help="list narration voices")
    p.set_defaults(fn=_voices)
    p = sub.add_parser("options", help="list every brand, style, overlay, motion and transition")
    p.set_defaults(fn=_options)
    p = sub.add_parser("clean", help="delete a project's render cache")
    p.add_argument("project")
    p.set_defaults(fn=_clean)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except StudioError as e:
        print(f"\nStudio: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
