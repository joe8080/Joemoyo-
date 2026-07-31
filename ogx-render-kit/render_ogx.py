#!/usr/bin/env python3
"""
OGX Ken Burns render — generalized, one command for any video in the batch.

This is the reusable version of build_meroe_kenburns.py: pass the slug, and it
auto-discovers the audio, enforces the safety guards, renders the locked house
spec, verifies the result, and updates _pipeline_state.json.

Run on the machine where the batch lives (ffmpeg + ffprobe on PATH, Python 3):

    python render_ogx.py 23_Kingdom_of_Meroe
    python render_ogx.py 24_Toussaint_Louverture

Place this file directly inside your _OGX_BATCH folder (alongside the
01_audio_inbox / 02_images_inbox / 03_finished_packs folders), the same place
the old build_*_kenburns.py scripts lived. Override the batch root if needed:

    python render_ogx.py 23_Kingdom_of_Meroe --root "D:\\some\\other\\_OGX_BATCH"

Resumable: each scene renders to its own .ts chunk. Re-run the same command to
skip chunks already done.

Output: 03_finished_packs/<slug>/FINAL.mp4
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Locked house render spec (do not change without a reason) ---
W, H, FPS = 1920, 1080, 30
ENC_FLAGS = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
             "-maxrate", "1500k", "-bufsize", "3000k", "-pix_fmt", "yuv420p"]
ZOOM = "min(zoom+0.0008,1.15)"   # gentle slow zoom-in
MIN_SCENES = 15                  # never render with fewer scene images
AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac"}


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def find_audio(audio_dir):
    """Auto-discover the single narration file — no hard-coded filename."""
    cands = sorted(p for p in audio_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    if not cands:
        sys.exit(f"ERROR: no audio ({'/'.join(AUDIO_EXTS)}) found in {audio_dir}")
    if len(cands) > 1:
        print(f"WARNING: {len(cands)} audio files in {audio_dir}; using {cands[0].name}")
    return cands[0]


def find_scenes(img_dir):
    """Numbered scene PNGs only — THUMBNAIL.png is excluded by the digit test."""
    imgs = sorted(p for p in img_dir.iterdir()
                  if p.suffix.lower() == ".png" and p.name[:2].isdigit())
    if len(imgs) < MIN_SCENES:
        sys.exit(f"ERROR: only {len(imgs)} numbered scene PNGs in {img_dir} "
                 f"(need >= {MIN_SCENES}). Refusing to render.")
    return imgs


def update_pipeline_state(root, slug, final_path, dur):
    state_path = root / "_pipeline_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except (json.JSONDecodeError, OSError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    entry = state.get(slug, {}) if isinstance(state.get(slug), dict) else {}
    entry.update({
        "render_status": "rendered",
        "final_video": str(final_path),
        "render_completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_seconds": round(dur, 1),
    })
    state[slug] = entry
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Updated {state_path.name} -> {slug}: rendered")


def main():
    ap = argparse.ArgumentParser(description="OGX Ken Burns render for one slug.")
    ap.add_argument("slug", help="e.g. 23_Kingdom_of_Meroe")
    ap.add_argument("--root", default=os.environ.get("OGX_BATCH_ROOT"),
                    help="_OGX_BATCH folder (defaults to this script's folder)")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent
    slug = args.slug
    img_dir = root / "02_images_inbox" / slug
    audio_dir = root / "01_audio_inbox" / slug
    out_dir = root / "03_finished_packs" / slug
    for d in (img_dir, audio_dir):
        if not d.is_dir():
            sys.exit(f"ERROR: missing folder {d}")
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "FINAL.mp4.work"
    work.mkdir(exist_ok=True)
    final = out_dir / "FINAL.mp4"

    audio = find_audio(audio_dir)
    images = find_scenes(img_dir)
    dur_total = probe_duration(audio)
    per_img = dur_total / len(images)
    print(f"Slug: {slug}")
    print(f"Audio: {audio.name}  {dur_total:.1f}s")
    print(f"Images: {len(images)}  ->  per-image {per_img:.2f}s")

    # --- Render each image as a Ken Burns TS chunk (resumable) ---
    chunks = []
    for i, img in enumerate(images, 1):
        out_ts = work / f"chunk_{i:02d}.ts"
        chunks.append(out_ts)
        if out_ts.exists() and out_ts.stat().st_size > 0:
            print(f"[{i:02d}/{len(images)}] skip (exists): {img.name}")
            continue
        zoom_expr = f"zoompan=z='{ZOOM}':d={int(per_img * FPS)}:s={W}x{H}:fps={FPS}"
        print(f"[{i:02d}/{len(images)}] render: {img.name}")
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(img),
             "-t", f"{per_img:.3f}", "-vf", zoom_expr,
             *ENC_FLAGS, "-r", str(FPS),
             "-f", "mpegts", "-bsf:v", "h264_mp4toannexb", str(out_ts)])

    # --- Concat (demuxer = path-safe for spaces + Windows drive letters) ---
    print("Concatenating...")
    list_file = work / "concat_list.txt"
    list_file.write_text(
        "".join(f"file '{c.resolve().as_posix()}'\n" for c in chunks),
        encoding="utf-8")
    silent = work / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(silent)])

    # --- Optional: overlay OGX 'DECLASSIFIED' evidence cards as pop-up beats ---
    # Drop card PNGs in 02_images_inbox/<slug>/evidence-cards/ (any name); optional
    # evidence-cards/cards.json = [{"file":"01.png","at":0.08,"dur":6}, ...] with
    # `at` as a fraction (0-1) of total duration, or absolute seconds if >1.
    cards_dir = img_dir / "evidence-cards"
    cards = sorted(cards_dir.glob("*.png")) if cards_dir.is_dir() else []
    base_for_mux = silent
    if cards:
        import json as _json
        cfg_path = cards_dir / "cards.json"
        cfg = _json.loads(cfg_path.read_text()) if cfg_path.exists() else []
        cfgmap = {c.get("file"): c for c in cfg} if cfg else {}
        CARD_DUR = 6.0
        specs = []
        for i, cp in enumerate(cards):
            c = cfgmap.get(cp.name, {})
            at = c.get("at", (i + 1) / (len(cards) + 1))
            t = at * dur_total if at <= 1 else at
            specs.append((cp, t, c.get("dur", CARD_DUR)))
        inputs = ["-i", str(silent)]
        for cp, _, d in specs:
            inputs += ["-loop", "1", "-t", str(d), "-i", str(cp)]
        fc = []
        for i, (cp, t, d) in enumerate(specs):
            df = int(d * FPS)
            fc.append(
                f"[{i+1}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                f"zoompan=z='min(zoom+0.0008,1.05)':d={df}:s={W}x{H}:fps={FPS},"
                f"format=rgba,fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st={d-0.35:.2f}:d=0.35:alpha=1,"
                f"setpts=PTS-STARTPTS+{t}/TB[ov{i}]")
        prev = "0:v"
        for i, (cp, t, d) in enumerate(specs):
            out = f"b{i}" if i < len(specs) - 1 else "vout"
            fc.append(f"[{prev}][ov{i}]overlay=enable='between(t,{t:.2f},{t+d:.2f})':x=0:y=0[{out}]")
            prev = out
        carded = work / "carded.mp4"
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
             "-map", "[vout]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
             "-pix_fmt", "yuv420p", "-r", str(FPS), str(carded)])
        base_for_mux = carded
        print(f"Overlaid {len(specs)} evidence cards.")

    # --- Mux audio ---
    print("Muxing audio...")
    run(["ffmpeg", "-y", "-i", str(base_for_mux),
         "-i", str(audio), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", str(final)])

    # --- Verify ---
    final_dur = probe_duration(final)
    size_mb = final.stat().st_size / 1_000_000
    drift = final_dur - dur_total
    print(f"\nDone: {final}")
    print(f"   Duration: {final_dur:.1f}s (audio {dur_total:.1f}s, drift {drift:+.1f}s)")
    print(f"   Size: {size_mb:.1f} MB")
    if abs(drift) > 2.0:
        print("   WARNING: duration drift > 2s vs audio — scrub before shipping.")
    if not (200 <= size_mb <= 900):
        print(f"   NOTE: size {size_mb:.0f} MB outside the usual ~400-600 MB band.")

    update_pipeline_state(root, slug, final, final_dur)


if __name__ == "__main__":
    main()
