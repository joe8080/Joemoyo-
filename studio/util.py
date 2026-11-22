"""Shared helpers: ffmpeg access, colours, easing, hashing."""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess

ENGINE_VERSION = "1.0.0"

FFMPEG = os.environ.get("STUDIO_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = os.environ.get("STUDIO_FFPROBE") or shutil.which("ffprobe") or "ffprobe"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}


class StudioError(Exception):
    """A problem the person running the studio can fix (bad project, missing file)."""


def run(cmd, data=None):
    """Run a command, return stdout bytes, raise StudioError with the tail of stderr."""
    try:
        p = subprocess.run(cmd, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise StudioError(f"'{cmd[0]}' was not found. Install ffmpeg and make sure it is on PATH.")
    if p.returncode:
        tail = p.stderr.decode("utf-8", "replace")[-900:]
        raise StudioError(f"{os.path.basename(str(cmd[0]))} failed:\n{tail}")
    return p.stdout


def probe(path):
    out = run([FFPROBE, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def media_duration(path):
    info = probe(path)
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError):
        raise StudioError(f"Could not read the length of {path}")


def video_size(path):
    for s in probe(path).get("streams", []):
        if s.get("codec_type") == "video":
            w, h = int(s["width"]), int(s["height"])
            rot = 0
            for sd in s.get("side_data_list", []):
                if "rotation" in sd:
                    rot = int(sd["rotation"])
            if abs(rot) in (90, 270):
                w, h = h, w
            return w, h
    raise StudioError(f"No video stream in {path}")


def digest(obj):
    blob = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha1(blob).hexdigest()[:16]


def file_sig(path):
    try:
        st = os.stat(path)
        return [str(path), st.st_size, int(st.st_mtime)]
    except OSError:
        return [str(path), -1, -1]


# ---------------------------------------------------------------- colours

def hexrgb(c):
    if isinstance(c, (tuple, list)):
        return tuple(int(v) for v in c[:3])
    c = str(c).strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise StudioError(f"Bad colour '{c}'. Use hex like #C9A84C.")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def rgba(c, a=255):
    r, g, b = hexrgb(c)
    return (r, g, b, int(a))


def mix(c1, c2, t):
    a, b = hexrgb(c1), hexrgb(c2)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def luminance(c):
    r, g, b = hexrgb(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


# ---------------------------------------------------------------- maths

def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def linear(t):
    return clamp(t)


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    t = clamp(t)
    return t ** 3


def ease_in_out_cubic(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_expo(t):
    t = clamp(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def ease_in_out_sine(t):
    t = clamp(t)
    return -(math.cos(math.pi * t) - 1) / 2


def fmt_time(t):
    t = max(0.0, t)
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def slugify(s):
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(s))
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")[:60] or "video"
