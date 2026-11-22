"""Scene backgrounds: stills with camera moves, video clips, and generated brand cards."""
from __future__ import annotations

import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from .util import FFMPEG, StudioError, clamp, ease_in_out_sine, ease_out_cubic, hexrgb, lerp, run, video_size

# Colour grades, written once as ffmpeg filters so stills and video match.
GRADES = {
    "none": "",
    "cinematic": "eq=contrast=1.08:saturation=0.92:gamma=0.97,"
                 "colorbalance=rs=-0.06:bs=0.07:rh=0.06:bh=-0.05",
    "warm": "eq=saturation=1.05:contrast=1.04,colorbalance=rm=0.05:bm=-0.05:rh=0.04:bh=-0.04",
    "cool": "eq=saturation=0.95:contrast=1.05,colorbalance=rm=-0.04:bm=0.06",
    "noir": "hue=s=0,eq=contrast=1.18:brightness=-0.02",
    "archive": "hue=s=0.35,eq=contrast=1.06:gamma=1.02,colorbalance=rm=0.06:gm=0.02:bm=-0.06",
    "vivid": "eq=saturation=1.25:contrast=1.08",
}

# Camera moves for stills: (zoom_start, zoom_end, pan_x, pan_y) where pan is the
# direction of travel in units of the available slack (-1..1).
MOTIONS = {
    "static": (1.0, 1.0, 0, 0),
    "push_in": (1.0, 1.16, 0, 0),
    "pull_out": (1.16, 1.0, 0, 0),
    "pan_left": (1.12, 1.12, -1, 0),
    "pan_right": (1.12, 1.12, 1, 0),
    "pan_up": (1.12, 1.12, 0, -1),
    "pan_down": (1.12, 1.12, 0, 1),
    "drift": (1.06, 1.14, 0.6, -0.4),
    "punch": (1.0, 1.2, 0, 0),
}
AUTO_CYCLE = ["push_in", "pan_right", "pull_out", "drift", "pan_left", "push_in", "pan_up", "pull_out"]


def grade_filter(name):
    if not name:
        return ""
    if name not in GRADES:
        raise StudioError(f"Unknown grade '{name}'. Options: {', '.join(GRADES)}.")
    return GRADES[name]


def apply_grade(img, grade):
    flt = grade_filter(grade)
    if not flt:
        return img
    w, h = img.size
    out = run([FFMPEG, "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
               "-i", "-", "-vf", flt + ",format=rgb24", "-frames:v", "1", "-f", "rawvideo", "-"],
              data=img.tobytes())
    return Image.frombytes("RGB", (w, h), out)


class StillSource:
    """A still image with a smooth, sub-pixel camera move (Ken Burns)."""

    def __init__(self, img, W, H, fps, motion="push_in", focus=(0.5, 0.5), duration=5.0, index=0):
        self.W, self.H, self.fps = W, H, fps
        if motion in (None, "auto"):
            motion = AUTO_CYCLE[index % len(AUTO_CYCLE)]
        if motion not in MOTIONS:
            raise StudioError(f"Unknown motion '{motion}'. Options: auto, {', '.join(MOTIONS)}.")
        self.motion = motion
        z0, z1, self.px, self.py = MOTIONS[motion]
        self.z0, self.z1 = z0, z1
        self.zmax = max(z0, z1)
        self.duration = max(0.1, duration)
        iw, ih = img.size
        cover = max(W / iw, H / ih)
        # Working image: zmax times bigger than a plain cover fit, so zooming never upsamples much.
        s = cover * self.zmax
        ww, wh = max(W, int(round(iw * s))), max(H, int(round(ih * s)))
        self.work = img.resize((ww, wh), Image.LANCZOS) if (ww, wh) != (iw, ih) else img
        self.ww, self.wh = ww, wh
        self.fx, self.fy = clamp(focus[0]), clamp(focus[1])

    def frame(self, t):
        p = clamp(t / self.duration)
        p = ease_out_cubic(p) if self.motion == "punch" else lerp(p, ease_in_out_sine(p), 0.35)
        z = lerp(self.z0, self.z1, p)
        a = self.zmax / z                      # working px per output px
        vw, vh = self.W * a, self.H * a        # view window in working px
        slack_x, slack_y = self.ww - vw, self.wh - vh
        # Travel: at most ~12% of the view, and never outside the picture.
        tx = min(slack_x, 0.12 * vw) * self.px
        ty = min(slack_y, 0.12 * vh) * self.py
        cx = self.fx * self.ww + tx * (p - 0.5)
        cy = self.fy * self.wh + ty * (p - 0.5)
        x0 = clamp(cx - vw / 2, 0, max(0.0, slack_x))
        y0 = clamp(cy - vh / 2, 0, max(0.0, slack_y))
        # resize() with a fractional box is a sub-pixel crop + scale: smooth motion, no shimmer.
        return self.work.resize((self.W, self.H), Image.BICUBIC,
                                box=(x0, y0, min(self.ww, x0 + vw), min(self.wh, y0 + vh)))

    def frames(self, t0, n):
        for k in range(n):
            yield self.frame(t0 + k / self.fps)


class VideoSource:
    """A video clip decoded through ffmpeg, fitted to the frame (cover crop or blurred fill)."""

    def __init__(self, path, W, H, fps, start=0.0, speed=1.0, fit="cover", focus=(0.5, 0.5),
                 grade="none", loop=False):
        self.path, self.W, self.H, self.fps = str(path), W, H, fps
        self.start, self.speed, self.loop = float(start), float(speed) or 1.0, loop
        fx, fy = clamp(focus[0]), clamp(focus[1])
        sw, sh = video_size(path)
        g = grade_filter(grade)
        if fit == "blur" and abs(sw / sh - W / H) > 0.02:
            vf = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"boxblur=24:4,eq=brightness=-0.12[bg];"
                  f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
                  f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
        elif fit in ("cover", "blur"):
            vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                  f"crop={W}:{H}:(iw-{W})*{fx:.4f}:(ih-{H})*{fy:.4f}")
        else:
            raise StudioError(f"Unknown fit '{fit}'. Use 'cover' or 'blur'.")
        pts = f"setpts=PTS/{self.speed}," if abs(self.speed - 1) > 1e-3 else ""
        self.vf = f"{pts}fps={fps},{vf}" + (f",{g}" if g else "") + ",format=rgb24"

    def frames(self, t0, n):
        size = self.W * self.H * 3
        seek = self.start + t0 * self.speed
        cmd = [FFMPEG, "-v", "error"]
        if self.loop:
            cmd += ["-stream_loop", "-1"]
        cmd += ["-ss", f"{max(0.0, seek):.4f}", "-i", self.path, "-an", "-vf", self.vf,
                "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        last = None
        try:
            for _ in range(n):
                buf = proc.stdout.read(size) if proc.stdout else b""
                if len(buf) == size:
                    last = Image.frombytes("RGB", (self.W, self.H), buf)
                elif last is None:
                    last = Image.new("RGB", (self.W, self.H), (0, 0, 0))
                yield last.copy()      # clip ran out: hold the final frame
        finally:
            if proc.stdout:
                proc.stdout.close()
            proc.kill()
            proc.wait()


# ---------------------------------------------------------------- generated cards

CARD_STYLES = ("gradient", "grid", "spotlight", "solid")


def card_image(style, kit, W, H, seed=0):
    """A branded background plate, drawn slightly oversize so it can drift."""
    if style not in CARD_STYLES:
        raise StudioError(f"Unknown card style '{style}'. Options: {', '.join(CARD_STYLES)}.")
    ow, oh = int(W * 1.14), int(H * 1.14)
    w, h = max(8, ow // 6), max(8, oh // 6)
    rng = np.random.default_rng(1234 + seed * 7919)
    bg = np.array(hexrgb(kit["bg"]), dtype=np.float32)
    acc = np.array(hexrgb(kit["accent"]), dtype=np.float32)
    acc2 = np.array(hexrgb(kit["accent2"]), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx, yy = xx / w, yy / h
    arr = np.broadcast_to(bg, (h, w, 3)).copy()
    asp = w / h

    def glow(cx, cy, r, col, strength):
        g = np.exp(-(((xx - cx) * asp) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None]
        arr[:] = arr + (col - arr) * g * strength

    if style == "spotlight":
        glow(0.5, 0.42, 0.42, acc, 0.10)
        glow(0.5, 0.42, 0.20, acc2, 0.07)
    elif style in ("gradient", "grid"):
        spots = [(0.16, 0.2, 0.36, acc, 0.26), (0.88, 0.86, 0.42, acc2, 0.14),
                 (0.72, 0.1, 0.28, acc, 0.10)]
        j = rng.uniform(-0.07, 0.07, size=(len(spots), 2))
        for (cx, cy, r, col, st), (dx, dy) in zip(spots, j):
            glow(cx + dx, cy + dy, r, col, st * (0.75 if style == "grid" else 1.0))
    if style != "solid":
        d = np.sqrt(((xx - 0.5) * 1.15) ** 2 + (yy - 0.5) ** 2)
        arr *= (1.0 - 0.30 * np.clip(d - 0.28, 0, 1) ** 1.3 * 2.2)[..., None].clip(0.55, 1)
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((ow, oh), Image.BICUBIC)
    if style == "grid":
        ov = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        step = max(24, int(min(W, H) / 13))
        col = tuple(int(v) for v in hexrgb(kit["text"])) + (13,)
        for x in range(0, ow, step):
            d.line([(x, 0), (x, oh)], fill=col, width=1)
        for y in range(0, oh, step):
            d.line([(0, y), (ow, y)], fill=col, width=1)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    # Fine dither so dark gradients do not band after compression.
    a = np.asarray(img, dtype=np.int16)
    a = a + rng.integers(-2, 3, size=a.shape, dtype=np.int16)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def load_image(path, grade="none"):
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Exception as e:
        raise StudioError(f"Could not open image {path}: {e}")
    return apply_grade(img, grade)
