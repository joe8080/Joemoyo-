"""Text rendering: fonts (with weight control), cached text sprites, wrapping and fitting."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from .util import StudioError, clamp

FONT_DIR = Path(__file__).parent / "fonts"
_extra_dirs: list[Path] = []


def add_font_dir(path):
    p = Path(path)
    if p.is_dir() and p not in _extra_dirs:
        _extra_dirs.append(p)
        font.cache_clear()


def _find(name):
    p = Path(name)
    if p.is_file():
        return p
    for d in [*_extra_dirs, FONT_DIR]:
        for ext in (".ttf", ".otf"):
            c = d / f"{name}{ext}"
            if c.is_file():
                return c
    have = sorted(f.stem for f in FONT_DIR.glob("*.ttf"))
    raise StudioError(f"Font '{name}' not found. Bundled fonts: {', '.join(have)}. "
                      "Drop extra .ttf files in a 'fonts' folder next to the project.")


@lru_cache(maxsize=512)
def font(name, size, weight=None):
    size = max(6, int(round(size)))
    f = ImageFont.truetype(str(_find(name)), size)
    try:
        axes = f.get_variation_axes()
    except Exception:
        axes = None
    if axes:
        vals = []
        for a in axes:
            nm = a.get("name", b"")
            nm = nm.decode("utf-8", "replace") if isinstance(nm, bytes) else str(nm)
            if "eight" in nm:
                vals.append(clamp(weight or a["default"], a["minimum"], a["maximum"]))
            elif "ptical" in nm:
                vals.append(clamp(size, a["minimum"], a["maximum"]))
            else:
                vals.append(a["default"])
        f.set_variation_by_axes(vals)
    return f


def text_width(text, f, tracking=0.0):
    if not text:
        return 0.0
    if tracking:
        return sum(f.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    return f.getlength(text)


class Sprite:
    """A pre-rendered piece of text. `w`/`h` are the text box; `pad` is the bleed around it."""
    __slots__ = ("img", "pad", "w", "h", "asc")

    def __init__(self, img, pad, w, h, asc):
        self.img, self.pad, self.w, self.h, self.asc = img, pad, w, h, asc


@lru_cache(maxsize=6000)
def sprite(text, fname, size, weight, fill, stroke=None, stroke_w=0, shadow=0.0, tracking=0.0):
    """Render one line of text to an RGBA sprite. All arguments must be hashable.

    fill/stroke are RGBA tuples. shadow is 0..1 strength of a soft drop shadow.
    """
    f = font(fname, size, weight)
    asc, desc = f.getmetrics()
    w = int(math.ceil(text_width(text, f, tracking)))
    blur = max(2, int(size * 0.07)) if shadow else 0
    off = max(1, int(size * 0.045)) if shadow else 0
    pad = int(stroke_w + blur * 2 + off + 4)
    img = Image.new("RGBA", (max(1, w) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    kw = {}
    if stroke and stroke_w:
        kw = {"stroke_width": int(stroke_w), "stroke_fill": stroke}
    if tracking:
        x = float(pad)
        for ch in text:
            d.text((x, pad + asc), ch, font=f, fill=fill, anchor="ls", **kw)
            x += f.getlength(ch) + tracking
        if kw:  # redraw fills so neighbouring strokes never cover a glyph
            x = float(pad)
            for ch in text:
                d.text((x, pad + asc), ch, font=f, fill=fill, anchor="ls")
                x += f.getlength(ch) + tracking
    else:
        d.text((pad, pad + asc), text, font=f, fill=fill, anchor="ls", **kw)
    if shadow:
        a = img.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
        a = ImageChops.offset(a, 0, off)
        a = a.point(lambda v: int(v * clamp(shadow)))
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(a)
        img = Image.alpha_composite(sh, img)
    return Sprite(img, pad, w, asc + desc, asc)


def wrap(text, f, max_w, tracking=0.0):
    """Greedy word wrap. Honours explicit newlines."""
    lines = []
    for para in str(text).split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for wd in words[1:]:
            trial = cur + " " + wd
            if text_width(trial, f, tracking) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
    return lines


def fit(text, fname, weight, max_w, max_lines, size, min_size, tracking_em=0.0):
    """Largest size (<= size) at which text wraps into max_lines within max_w."""
    s = int(size)
    while True:
        f = font(fname, s, weight)
        lines = wrap(text, f, max_w, tracking_em * s)
        widest = max((text_width(ln, f, tracking_em * s) for ln in lines), default=0)
        if (len(lines) <= max_lines and widest <= max_w) or s <= min_size:
            return s, lines
        s = max(int(min_size), int(s * 0.93))


@lru_cache(maxsize=512)
def rounded_box(w, h, r, fill, outline=None, outline_w=0):
    """Anti-aliased rounded rectangle sprite (drawn at 3x and reduced)."""
    w, h = max(2, int(w)), max(2, int(h))
    k = 3
    big = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    r = int(min(r, w / 2, h / 2) * k)
    d.rounded_rectangle([0, 0, w * k - 1, h * k - 1], radius=r, fill=fill,
                        outline=outline, width=int(outline_w * k) if outline else 0)
    return big.resize((w, h), Image.LANCZOS)


def paste(canvas, spr_img, x, y, alpha=1.0):
    """Composite an RGBA sprite on an RGB canvas at (x, y) with overall alpha."""
    if alpha <= 0.004:
        return
    pos = (int(round(x)), int(round(y)))
    if alpha >= 0.996:
        canvas.paste(spr_img, pos, spr_img)
    else:
        k = clamp(alpha)
        mask = spr_img.getchannel("A").point(lambda v: int(v * k))
        canvas.paste(spr_img, pos, mask)


def paste_sprite(canvas, sp, x, y, alpha=1.0):
    """Place a text Sprite so its text box's top-left sits at (x, y)."""
    paste(canvas, sp.img, x - sp.pad, y - sp.pad, alpha)
