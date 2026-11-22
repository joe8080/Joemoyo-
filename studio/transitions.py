"""Scene-to-scene transitions. Each takes the outgoing frame, incoming frame and progress 0..1."""
from __future__ import annotations

import numpy as np
from PIL import Image

from .util import StudioError, ease_in_out_cubic, ease_out_cubic

DEFAULT_DURATION = {
    "cut": 0.0, "fade": 0.5, "dip": 0.7, "flash": 0.35, "zoom": 0.45,
    "slide_left": 0.45, "slide_right": 0.45, "slide_up": 0.45, "slide_down": 0.45,
    "wipe_left": 0.55, "wipe_right": 0.55,
}
WHOOSH = {"zoom", "slide_left", "slide_right", "slide_up", "slide_down", "wipe_left", "wipe_right"}


def check(kind):
    if kind not in DEFAULT_DURATION:
        raise StudioError(f"Unknown transition '{kind}'. Options: {', '.join(DEFAULT_DURATION)}.")
    return kind


def _zoomed(img, z):
    W, H = img.size
    a = 1.0 / z
    x0, y0 = W * (1 - a) / 2, H * (1 - a) / 2
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + W * a, y0 + H * a))


def blend(kind, a, b, p):
    """a = outgoing frame (or None for the very first scene), b = incoming frame."""
    W, H = b.size
    if a is None:
        return Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), b, ease_out_cubic(p))
    if kind == "fade":
        return Image.blend(a, b, ease_in_out_cubic(p))
    if kind == "dip":
        black = Image.new("RGB", (W, H), (0, 0, 0))
        return Image.blend(a, black, ease_in_out_cubic(p * 2)) if p < 0.5 else \
            Image.blend(black, b, ease_in_out_cubic((p - 0.5) * 2))
    if kind == "flash":
        white = Image.new("RGB", (W, H), (255, 255, 255))
        return Image.blend(a, white, ease_out_cubic(p / 0.35)) if p < 0.35 else \
            Image.blend(white, b, ease_out_cubic((p - 0.35) / 0.65))
    e = ease_in_out_cubic(p)
    if kind.startswith("slide_"):
        out = Image.new("RGB", (W, H))
        dx, dy = {"slide_left": (-1, 0), "slide_right": (1, 0),
                  "slide_up": (0, -1), "slide_down": (0, 1)}[kind]
        ox, oy = int(round(dx * e * W)), int(round(dy * e * H))
        out.paste(a, (ox, oy))
        out.paste(b, (ox - dx * W, oy - dy * H))
        return out
    if kind in ("wipe_left", "wipe_right"):
        soft = 0.12
        x = np.linspace(0, 1, max(2, W // 4), dtype=np.float32)
        if kind == "wipe_left":
            x = 1 - x
        edge = e * (1 + soft)
        m = np.clip((edge - x) / soft, 0, 1)
        mask = Image.fromarray((m * 255).astype(np.uint8)[None, :]).resize((W, H), Image.BILINEAR)
        return Image.composite(b, a, mask)
    if kind == "zoom":
        return Image.blend(_zoomed(a, 1 + 0.35 * e), _zoomed(b, 1.18 - 0.18 * e), e)
    return b
