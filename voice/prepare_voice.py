#!/usr/bin/env python3
"""
Turn any audio or video clip into a VibeVoice voice sample.

    python voice/prepare_voice.py --input me_talking.mp4 --name Joe --gender man
    python voice/prepare_voice.py --input host.wav --name Maya --gender woman --start 12 --duration 25

Writes voice/voices/en-<Name>_<gender>.wav as 24 kHz mono, which is what the
model expects. Then use the name with generate.py: --voices Joe Maya
"""

import argparse
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

VOICE_DIR = Path(__file__).parent / "voices"
SAMPLE_RATE = 24000
IDEAL_MIN, IDEAL_MAX = 8, 30


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def probe_duration(path):
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        )
        return float(out.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Create a voice sample for cloning.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", required=True, help="source audio or video file")
    parser.add_argument("--name", required=True, help="voice name, e.g. Joe")
    parser.add_argument(
        "--gender",
        default="man",
        choices=["man", "woman"],
        help="used only in the filename, matching VibeVoice's preset convention",
    )
    parser.add_argument("--lang", default="en", help="language tag for the filename")
    parser.add_argument("--start", type=float, default=0.0, help="start offset in seconds")
    parser.add_argument(
        "--duration", type=float, default=20.0, help="sample length in seconds (default 20)"
    )
    parser.add_argument(
        "--no-denoise",
        action="store_true",
        help="skip the light high-pass + loudness normalisation",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing sample")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        die("ffmpeg not found. Install it: apt-get install ffmpeg (or brew install ffmpeg)")

    source = Path(args.input)
    if not source.is_file():
        die(f"input not found: {source}")

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", args.name):
        die("--name must be a single alphanumeric word starting with a letter, e.g. Joe")

    if not IDEAL_MIN <= args.duration <= IDEAL_MAX:
        print(
            f"note: {args.duration:.0f}s is outside the {IDEAL_MIN}-{IDEAL_MAX}s sweet spot; "
            f"clones are usually best around 15-25s of clean, continuous speech."
        )

    total = probe_duration(source)
    if total and args.start >= total:
        die(f"--start {args.start}s is past the end of the file ({total:.1f}s)")

    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    destination = VOICE_DIR / f"{args.lang}-{args.name}_{args.gender}.wav"
    if destination.exists() and not args.force:
        die(f"{destination} already exists — pass --force to overwrite")

    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(args.start),
        "-t", str(args.duration),
        "-i", str(source),
        "-vn",
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-c:a", "pcm_s16le",
    ]
    if not args.no_denoise:
        # Gentle cleanup only: rumble removal plus broadcast loudness levelling.
        # Anything heavier tends to smear the timbre the model is trying to copy.
        command += ["-af", "highpass=f=70,loudnorm=I=-18:TP=-2:LRA=11"]
    command.append(str(destination))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        die(f"ffmpeg failed:\n{result.stderr.strip()}")

    with wave.open(str(destination), "rb") as wav:
        seconds = wav.getnframes() / wav.getframerate()

    if seconds < 3:
        die(
            f"only got {seconds:.1f}s of audio — check --start/--duration "
            f"against the source length"
        )

    print(f"created {destination}")
    print(f"  {seconds:.1f}s, mono, {SAMPLE_RATE} Hz")
    print(f"\nuse it with:  python voice/generate.py --script yourscript.txt --voices {args.name}")


if __name__ == "__main__":
    main()
