"""On-screen graphics: titles, stats, quotes, bullets, lower thirds, labels, charts, images.

Every overlay is laid out in relative units, so the same project renders in 16:9, 9:16 or 1:1.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import text as T
from .util import (StudioError, clamp, ease_in_cubic, ease_out_cubic, ease_out_expo, hexrgb,
                   lerp, luminance, mix, rgba)


class Ctx:
    """Frame geometry plus the brand kit; shared by overlays and captions."""

    def __init__(self, W, H, fps, kit, captions_on=False):
        self.W, self.H, self.fps, self.kit = W, H, fps, kit
        self.u = min(W, H) / 1080.0
        self.portrait = H > W * 1.1
        self.mx = int(round(W * (0.075 if self.portrait else 0.065)))
        self.top = int(round(H * (0.11 if self.portrait else 0.08)))
        self.bottom = int(round(H * (0.19 if self.portrait else 0.09)))
        self.captions_on = captions_on
        # Where burned-in captions sit (centre line, as a fraction of height).
        self.caption_y = 0.72 if self.portrait else 0.84

    def px(self, v):
        return max(1, int(round(v * self.u)))

    def fnt(self, role):
        try:
            name, weight = self.kit["fonts"][role]
        except KeyError:
            raise StudioError(f"Brand kit has no font role '{role}'.")
        return name, weight

    def col(self, key, a=255):
        return rgba(self.kit.get(key, key), a)

    def content_bottom(self):
        """Lowest y that graphics should use without colliding with captions."""
        if self.captions_on:
            return int(self.H * self.caption_y - self.px(110))
        return self.H - self.bottom


def fmt_num(v, prefix="", suffix="", decimals=0, compact=False):
    if isinstance(v, str):
        return f"{prefix}{v}{suffix}"
    if compact:
        a = abs(v)
        for lim, unit in ((1e9, "bn"), (1e6, "m"), (1e3, "k")):
            if a >= lim:
                s = f"{v / lim:.1f}".rstrip("0").rstrip(".")
                return f"{prefix}{s}{unit}{suffix}"
    return f"{prefix}{v:,.{int(decimals)}f}{suffix}"


class Overlay:
    def __init__(self, spec, ctx, dur, has_media=False):
        self.spec, self.ctx, self.dur, self.has_media = spec, ctx, dur, has_media
        self.at = float(spec.get("at", 0.25))
        self.end = self.at + float(spec["for"]) if "for" in spec else None
        self.shadow = 0.6 if has_media else 0.0
        self.build()

    def build(self):
        pass

    def out(self, t):
        if self.end is None:
            return 1.0
        return 1.0 - ease_in_cubic((t - self.end) / 0.3)

    def stage(self, t, k=0, stagger=0.09, dur=0.5):
        return ease_out_cubic((t - self.at - k * stagger) / dur)

    def scrim(self, canvas, t, strength):
        a = strength * self.stage(t, 0, dur=0.4) * self.out(t)
        if a > 0.01:
            W, H = canvas.size
            canvas.paste((0, 0, 0), (0, 0, W, H), Image.new("L", (W, H), int(255 * clamp(a))))

    def draw(self, canvas, t):
        raise NotImplementedError


class _Stack(Overlay):
    """A vertical stack of rows (text sprites / rules) that reveal one after another."""
    align = "center"
    scrim_strength = 0.5

    def rows(self):
        return []

    def build(self):
        c = self.ctx
        self.align = self.spec.get("align", self.align)
        self._rows = self.rows()            # each: dict(img, w, h, gap, pad, kind)
        self.block_h = sum(r["h"] + r["gap"] for r in self._rows) - (self._rows[-1]["gap"] if self._rows else 0)
        self.block_w = max((r["w"] for r in self._rows), default=0)
        pos = self.spec.get("pos", "center")
        top, bot = c.top, c.content_bottom()
        if pos == "upper":
            self.y0 = top + c.px(30)
        elif pos == "lower":
            self.y0 = bot - self.block_h
        else:
            self.y0 = top + (bot - top - self.block_h) / 2
        self.y0 = max(c.px(20), self.y0)
        self.col_x = self.spec.get("_col_x")

    def row_x(self, r):
        c = self.ctx
        if self.align == "left":
            return self.col_x if self.col_x is not None else c.mx
        return (c.W - r["w"]) / 2

    def draw(self, canvas, t):
        if t < self.at:
            return
        c = self.ctx
        if self.has_media and self.spec.get("scrim", True):
            self.scrim(canvas, t, self.scrim_strength)
        o = self.out(t)
        y = self.y0
        for k, r in enumerate(self._rows):
            p = self.stage(t, r.get("order", k))
            a = p * o
            if a > 0.004:
                x = self.row_x(r)
                if r["kind"] == "rule":
                    w = max(1, int(r["w"] * p))
                    xx = x if self.align == "left" else (c.W - w) / 2
                    T.paste(canvas, r["img"].crop((0, 0, w, r["h"])), xx, y, o)
                else:
                    dy = (1 - p) * c.px(26)
                    T.paste(canvas, r["img"], x - r["pad"], y - r["pad"] + dy, a)
            y += r["h"] + r["gap"]

    # helpers for subclasses
    def text_row(self, txt, role, size, color, gap, tracking=0.0, leading=None, weight=None, order=None):
        c = self.ctx
        fname, wt = c.fnt(role)
        sp = T.sprite(txt, fname, size, weight or wt, color, None, 0, self.shadow, tracking)
        h = int(leading) if leading else sp.h
        r = {"img": sp.img, "w": sp.w, "h": h, "gap": gap, "pad": sp.pad, "kind": "text"}
        if order is not None:
            r["order"] = order
        return r

    def rule_row(self, w, h, color, gap):
        return {"img": Image.new("RGBA", (w, h), color), "w": w, "h": h, "gap": gap, "pad": 0, "kind": "rule"}


class Title(_Stack):
    """Big headline with optional kicker (small label above) and sub line."""

    def rows(self):
        c, s = self.ctx, self.spec
        maxw = c.W - 2 * c.mx
        rows = []
        if s.get("kicker"):
            sz = c.px(30)
            rows.append(self.text_row(str(s["kicker"]).upper(), "heading", sz, c.col(s.get("kicker_color", "accent")),
                                      c.px(22), tracking=sz * 0.18))
            rows.append(self.rule_row(c.px(90), c.px(5), c.col("accent"), c.px(30)))
        txt = str(s.get("text", ""))
        if c.kit.get("uppercase_titles"):
            txt = txt.upper()
        fname, wt = c.fnt("display")
        base = c.px(s.get("size", 100 if c.portrait else 122))
        size, lines = T.fit(txt, fname, wt, maxw, s.get("max_lines", 5 if c.portrait else 3), base, c.px(44))
        for i, ln in enumerate(lines):
            last = i == len(lines) - 1
            rows.append(self.text_row(ln, "display", size, c.col(s.get("color", "text")),
                                      c.px(30) if last else 0, leading=size * 1.14))
        if s.get("sub"):
            sz = c.px(40)
            f = T.font(*c.fnt("body")[:1], sz, c.fnt("body")[1])
            for ln in T.wrap(str(s["sub"]), f, min(maxw, c.px(1300))):
                rows.append(self.text_row(ln, "body", sz, c.col("muted" if not self.has_media else "text"),
                                          0, leading=sz * 1.38))
        return rows


class Stat(_Stack):
    """One huge number that counts up, with a label underneath."""
    scrim_strength = 0.55

    def rows(self):
        c, s = self.ctx, self.spec
        self.maxw = c.W - 2 * c.mx
        self.value = s.get("value", 0)
        self.numeric = isinstance(self.value, (int, float)) and not isinstance(self.value, bool)
        self.count = float(s.get("count", 1.4))
        final = self.fmt(self.value)
        fname, wt = c.fnt("display")
        self.size, _ = T.fit(final, fname, wt, self.maxw, 1, c.px(s.get("size", 210 if c.portrait else 250)), c.px(70))
        self.num_color = c.col(s.get("color", "accent"))
        sp = T.sprite(final, fname, self.size, wt, self.num_color, None, 0, self.shadow, 0.0)
        rows = [{"img": sp.img, "w": sp.w, "h": max(int(self.size * 1.12), int(sp.h * 0.94)), "gap": c.px(18),
                 "pad": sp.pad, "kind": "num"}]
        if s.get("label"):
            sz = c.px(38)
            f = T.font(c.fnt("heading")[0], sz, c.fnt("heading")[1])
            for ln in T.wrap(str(s["label"]).upper(), f, min(self.maxw, c.px(1400)), sz * 0.12):
                rows.append(self.text_row(ln, "heading", sz, c.col("text"), 0, tracking=sz * 0.12,
                                          leading=sz * 1.4, order=2))
            rows[-1]["gap"] = c.px(10)
        if s.get("sub"):
            sz = c.px(36)
            f = T.font(c.fnt("body")[0], sz, c.fnt("body")[1])
            for ln in T.wrap(str(s["sub"]), f, min(self.maxw, c.px(1300))):
                rows.append(self.text_row(ln, "body", sz, c.col("muted" if not self.has_media else "text"),
                                          0, leading=sz * 1.38, order=3))
        return rows

    def fmt(self, v):
        s = self.spec
        return fmt_num(v, s.get("prefix", ""), s.get("suffix", ""), s.get("decimals", 0))

    def draw(self, canvas, t):
        if t < self.at:
            return
        if self.numeric:
            p = ease_out_expo((t - self.at) / max(0.05, self.count))
            v = lerp(float(self.spec.get("from", 0)), float(self.value), p)
            if p >= 0.999:
                v = self.value
            fname, wt = self.ctx.fnt("display")
            sp = T.sprite(self.fmt(v), fname, self.size, wt, self.num_color, None, 0, self.shadow, 0.0)
            r = self._rows[0]
            r["img"], r["w"], r["pad"] = sp.img, sp.w, sp.pad
        super().draw(canvas, t)


class Quote(_Stack):
    align = "left"
    scrim_strength = 0.6

    def rows(self):
        c, s = self.ctx, self.spec
        colw = min(c.W - 2 * c.mx, c.px(1320))
        self.spec["_col_x"] = (c.W - colw) / 2
        rows = []
        msz = c.px(200)
        mark = self.text_row("“", "quote", msz, c.col("accent"), 0, leading=msz * 0.64, weight=700)
        rows.append(mark)
        fname, wt = c.fnt("quote")
        size, lines = T.fit(str(s.get("text", "")), fname, wt, colw, s.get("max_lines", 9 if c.portrait else 5),
                            c.px(s.get("size", 62)), c.px(34))
        for i, ln in enumerate(lines):
            rows.append(self.text_row(ln, "quote", size, c.col("text"),
                                      c.px(34) if i == len(lines) - 1 else 0, leading=size * 1.34, order=1 + i))
        if s.get("by"):
            sz = c.px(30)
            rows.append(self.text_row("— " + str(s["by"]).upper(), "heading", sz, c.col("accent"), 0,
                                      tracking=sz * 0.14, order=len(lines) + 2))
        return rows


class Bullets(_Stack):
    align = "left"
    scrim_strength = 0.62

    def rows(self):
        c, s = self.ctx, self.spec
        items = [str(i) for i in s.get("items", [])]
        if not items:
            raise StudioError("A 'bullets' overlay needs a non-empty 'items' list.")
        colw = min(c.W - 2 * c.mx, c.px(1300))
        self.spec["_col_x"] = (c.W - colw) / 2
        rows, order = [], 0
        if s.get("title"):
            sz = c.px(56)
            f = T.font(c.fnt("heading")[0], sz, c.fnt("heading")[1])
            for ln in T.wrap(str(s["title"]), f, colw):
                rows.append(self.text_row(ln, "heading", sz, c.col("text"), 0, leading=sz * 1.2, order=0))
            rows[-1]["gap"] = c.px(20)
            rows.append(self.rule_row(c.px(90), c.px(5), c.col("accent"), c.px(40)))
            rows[-1]["order"] = 1
            order = 2
        every = float(s.get("every", clamp((self.dur - self.at - 1.4) / len(items), 0.45, 2.5)))
        self.steps = max(1.0, every / 0.09)        # stage() staggers in 0.09s units
        sz = c.px(s.get("size", 46))
        fname, wt = c.fnt("body")
        f = T.font(fname, sz, wt)
        indent = c.px(64)
        numbered = bool(s.get("numbered"))
        for i, it in enumerate(items):
            lines = T.wrap(it, f, colw - indent)
            for j, ln in enumerate(lines):
                sp = T.sprite(ln, fname, sz, wt, c.col("text"), None, 0, self.shadow, 0.0)
                img = Image.new("RGBA", (indent + sp.w + 2 * sp.pad, sp.img.height), (0, 0, 0, 0))
                img.paste(sp.img, (indent, 0))
                if j == 0:
                    if numbered:
                        m = T.sprite(f"{i + 1:02d}", c.fnt("heading")[0], int(sz * 0.72), 800,
                                     c.col("accent"), None, 0, self.shadow, 0.0)
                        img.alpha_composite(m.img, (sp.pad - m.pad, sp.pad - m.pad + int(sz * 0.2)))
                    else:
                        d = c.px(16)
                        box = T.rounded_box(d, d, c.px(4), c.col("accent"))
                        img.alpha_composite(box, (sp.pad, sp.pad + int(sp.asc * 0.5)))
                rows.append({"img": img, "w": indent + sp.w, "h": int(sz * 1.36),
                             "gap": c.px(26) if j == len(lines) - 1 else 0, "pad": sp.pad, "kind": "text",
                             "order": order + 3 + i * self.steps})
        return rows


class LowerThird(Overlay):
    """Name plate that wipes in from the left."""

    def build(self):
        c, s = self.ctx, self.spec
        name = str(s.get("text", ""))
        sub = s.get("sub")
        nsz, ssz = c.px(46), c.px(32)
        maxw = int(c.W * (0.84 if c.portrait else 0.6))
        hn, hw = c.fnt("heading")
        nsz, nlines = T.fit(name, hn, hw, maxw, 1, nsz, c.px(26))
        n = T.sprite(nlines[0], hn, nsz, hw, c.col("text"))
        sb = T.sprite(str(sub), c.fnt("body")[0], ssz, c.fnt("body")[1], c.col("muted")) if sub else None
        padx, pady, bar = c.px(26), c.px(18), c.px(8)
        w = bar + padx * 2 + max(n.w, sb.w if sb else 0)
        h = pady * 2 + int(nsz * 1.15) + (int(ssz * 1.35) if sb else 0)
        plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        plate.alpha_composite(T.rounded_box(w, h, c.px(10), c.col("bg", 224)))
        plate.alpha_composite(Image.new("RGBA", (bar, h), c.col("accent")))
        plate.alpha_composite(n.img, (bar + padx - n.pad, pady - n.pad))
        if sb:
            plate.alpha_composite(sb.img, (bar + padx - sb.pad, pady + int(nsz * 1.15) - sb.pad))
        self.plate = plate
        self.x = c.mx
        self.y = c.content_bottom() - h if s.get("pos", "lower") == "lower" else c.top

    def draw(self, canvas, t):
        if t < self.at:
            return
        p = ease_out_expo((t - self.at) / 0.6)
        w = max(1, int(self.plate.width * p))
        T.paste(canvas, self.plate.crop((0, 0, w, self.plate.height)), self.x, self.y, self.out(t))


class Label(Overlay):
    """Small pill in a corner: sources, dates, 'CONTESTED' flags."""

    def build(self):
        c, s = self.ctx, self.spec
        tone = s.get("tone", "accent")
        sz = c.px(s.get("size", 26))
        solid = bool(s.get("solid", tone == "alert"))
        key = {"accent": "accent", "alert": "alert", "muted": "muted"}.get(tone, tone)
        fg = c.col("bg") if solid and luminance(c.kit.get(key, key)) > 0.45 else c.col("text" if solid else key)
        sp = T.sprite(str(s.get("text", "")).upper(), c.fnt("heading")[0], sz, 800, fg, None, 0, 0.0, sz * 0.14)
        padx, pady = c.px(20), c.px(11)
        w, h = sp.w + 2 * padx, int(sz * 1.25) + 2 * pady
        box = T.rounded_box(w, h, h // 2, c.col(key) if solid else c.col("bg", 214),
                            None if solid else c.col(key), 0 if solid else max(2, c.px(2)))
        pill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pill.alpha_composite(box)
        pill.alpha_composite(sp.img, (padx - sp.pad, pady - sp.pad))
        self.pill = pill
        corner = s.get("corner", "tl")
        self.x = c.mx if "l" in corner else c.W - c.mx - w
        self.y = c.top if "t" in corner else c.content_bottom() - h
        self.dx = -1 if "l" in corner else 1

    def draw(self, canvas, t):
        if t < self.at:
            return
        p = self.stage(t, 0, dur=0.45)
        T.paste(canvas, self.pill, self.x + self.dx * (1 - p) * self.ctx.px(30), self.y, p * self.out(t))


class Text(Overlay):
    """Free text block. x/y are fractions of the frame for the block's centre."""

    def build(self):
        c, s = self.ctx, self.spec
        role = s.get("role", "body")
        fname, wt = c.fnt(role)
        wt = s.get("weight", wt)
        maxw = int(c.W * float(s.get("max_width", 0.84)))
        size, lines = T.fit(str(s.get("text", "")), fname, wt, maxw, int(s.get("max_lines", 6)),
                            c.px(s.get("size", 48)), c.px(22))
        col = c.col(s.get("color", "text"))
        self.sprites = [T.sprite(ln, fname, size, wt, col, None, 0, self.shadow, 0.0) for ln in lines]
        self.lh = int(size * 1.3)
        self.cx, self.cy = c.W * float(s.get("x", 0.5)), c.H * float(s.get("y", 0.5))
        self.align = s.get("align", "center")
        self.bw = max(sp.w for sp in self.sprites)

    def draw(self, canvas, t):
        if t < self.at:
            return
        o = self.out(t)
        y = self.cy - self.lh * len(self.sprites) / 2
        for k, sp in enumerate(self.sprites):
            p = self.stage(t, k)
            x = self.cx - self.bw / 2 if self.align == "left" else self.cx - sp.w / 2
            T.paste_sprite(canvas, sp, x, y + (1 - p) * self.ctx.px(22), p * o)
            y += self.lh


class Picture(Overlay):
    """A logo or framed picture placed over the scene."""

    def build(self):
        c, s = self.ctx, self.spec
        src = s.get("src")
        if not src or not Path(src).is_file():
            raise StudioError(f"Overlay image not found: {src}")
        img = Image.open(src).convert("RGBA")
        w = max(8, int(c.W * float(s.get("width", 0.3))))
        h = max(8, int(img.height * w / img.width))
        mh = int(c.H * float(s.get("max_height", 0.7)))
        if h > mh:
            w, h = int(w * mh / h), mh
        img = img.resize((w, h), Image.LANCZOS)
        if s.get("frame"):
            b = c.px(10)
            sh = c.px(26)
            card = Image.new("RGBA", (w + 2 * b + 2 * sh, h + 2 * b + 2 * sh), (0, 0, 0, 0))
            shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
            shadow.paste((0, 0, 0, 150), (sh, sh + c.px(8), sh + w + 2 * b, sh + h + 2 * b + c.px(8)))
            card.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sh / 2.2)))
            card.paste(c.col(s.get("frame_color", "text")), (sh, sh, sh + w + 2 * b, sh + h + 2 * b))
            card.alpha_composite(img, (sh + b, sh + b))
            rot = float(s.get("rotate", 0))
            img = card.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else card
        op = clamp(float(s.get("opacity", 1.0)))
        if op < 1:
            img.putalpha(img.getchannel("A").point(lambda v: int(v * op)))
        self.img = img
        self.cx, self.cy = c.W * float(s.get("x", 0.5)), c.H * float(s.get("y", 0.5))

    def draw(self, canvas, t):
        if t < self.at:
            return
        p = self.stage(t, 0, dur=0.55)
        a = p * self.out(t)
        img = self.img
        if p < 0.999:
            k = 0.94 + 0.06 * p
            img = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.BILINEAR)
        T.paste(canvas, img, self.cx - img.width / 2, self.cy - img.height / 2, a)


class Chart(Overlay):
    """Animated line or bar chart drawn in the brand colours."""

    def build(self):
        c, s = self.ctx, self.spec
        self.kind = s.get("kind", "line")
        if self.kind not in ("line", "bar"):
            raise StudioError("Chart 'kind' must be 'line' or 'bar'.")
        pts = []
        for d in s.get("data", []):
            if isinstance(d, dict):
                pts.append((str(d.get("label", "")), float(d["value"])))
            elif isinstance(d, (list, tuple)):
                pts.append((str(d[0]), float(d[1])))
            else:
                pts.append(("", float(d)))
        if len(pts) < 2:
            raise StudioError("A chart needs at least two data points.")
        self.pts = pts
        self.fmt = lambda v: fmt_num(v, s.get("prefix", ""), s.get("suffix", ""), s.get("decimals", 0),
                                     compact=s.get("compact", True))
        self.draw_secs = float(s.get("draw", 2.2))
        self.bw = min(c.W - 2 * c.mx, c.px(1500))
        self.bh = c.px(s.get("height", 720 if c.portrait else 520))
        self.title = None
        th = 0
        if s.get("title"):
            sz = c.px(46)
            sz, lines = T.fit(str(s["title"]), c.fnt("heading")[0], c.fnt("heading")[1], self.bw, 2, sz, c.px(26))
            self.title = [T.sprite(ln, c.fnt("heading")[0], sz, c.fnt("heading")[1], c.col("text"),
                                   None, 0, self.shadow, 0.0) for ln in lines]
            self.tlh = int(sz * 1.25)
            th = self.tlh * len(lines) + c.px(34)
        top, bot = c.top, c.content_bottom()
        total = th + self.bh
        self.y0 = max(c.px(20), top + (bot - top - total) / 2)
        self.x0 = (c.W - self.bw) / 2
        self.th = th
        self.vmax = max(v for _, v in pts) * 1.14 or 1.0
        self.vmin = min(0.0, min(v for _, v in pts))
        self.lab = c.px(62)                 # room for x labels
        self.acc = hexrgb(c.kit.get(s.get("color", "accent"), s.get("color", "accent")))
        self._final = None

    def _xy(self, i, v, k=1):
        n = len(self.pts)
        pw, ph = self.bw * k, (self.bh - self.lab) * k
        inset = 0.03 * pw
        x = inset + (pw - 2 * inset) * (i / (n - 1))
        y = ph - ph * 0.04 - (ph * 0.92) * ((v - self.vmin) / (self.vmax - self.vmin))
        return x, y

    def _grid(self, d, k):
        c = self.ctx
        pw, ph = self.bw * k, (self.bh - self.lab) * k
        col = c.col("text", 28)
        for g in range(4):
            y = ph * 0.04 + (ph * 0.92) * g / 3
            d.line([(0, y), (pw, y)], fill=col, width=max(1, k))
        d.line([(0, ph - ph * 0.04 + k), (pw, ph - ph * 0.04 + k)], fill=c.col("text", 90), width=max(2, 2 * k))

    def _labels(self, img, k, idxs):
        c = self.ctx
        sz = c.px(30) * k
        for i in idxs:
            lab = self.pts[i][0]
            if not lab:
                continue
            sp = T.sprite(lab, c.fnt("body")[0], sz, c.fnt("body")[1], c.col("muted"))
            x, _ = self._xy(i, 0, k)
            x = clamp(x - sp.w / 2, 0, self.bw * k - sp.w)
            img.alpha_composite(sp.img, (int(x) - sp.pad, int((self.bh - self.lab) * k + c.px(12) * k) - sp.pad))

    def _render(self, p):
        c = self.ctx
        if self.kind == "line":
            return self._line(p)
        return self._bars(p)

    def _line(self, p):
        c, k = self.ctx, 2
        img = Image.new("RGBA", (int(self.bw * k), int(self.bh * k)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        self._grid(d, k)
        n = len(self.pts)
        pos = p * (n - 1)
        i0 = min(int(pos), n - 2)
        frac = pos - i0
        xy = [self._xy(i, self.pts[i][1], k) for i in range(i0 + 1)]
        xa, ya = self._xy(i0, self.pts[i0][1], k)
        xb, yb = self._xy(i0 + 1, self.pts[i0 + 1][1], k)
        head = (lerp(xa, xb, frac), lerp(ya, yb, frac))
        xy.append(head)
        base = (self.bh - self.lab) * k * 0.96
        fill = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(fill).polygon(xy + [(head[0], base), (xy[0][0], base)], fill=self.acc + (46,))
        img.alpha_composite(fill)
        lw = c.px(7) * k
        d.line(xy, fill=self.acc + (255,), width=lw, joint="curve")
        r = lw * 0.5
        for x, y in (xy[0], head):
            d.ellipse([x - r, y - r, x + r, y + r], fill=self.acc + (255,))
        r = c.px(13) * k
        d.ellipse([head[0] - r * 1.9, head[1] - r * 1.9, head[0] + r * 1.9, head[1] + r * 1.9], fill=self.acc + (60,))
        d.ellipse([head[0] - r, head[1] - r, head[0] + r, head[1] + r], fill=self.acc + (255,))
        v = lerp(self.pts[i0][1], self.pts[i0 + 1][1], frac)
        sp = T.sprite(self.fmt(v), c.fnt("heading")[0], c.px(44) * k, 800, c.col("text"), None, 0, 0.5, 0.0)
        lx = clamp(head[0] - sp.w - r * 2.2, 0, self.bw * k - sp.w)
        ly = max(0, head[1] - sp.h - r * 1.2)
        img.alpha_composite(sp.img, (int(lx) - sp.pad, int(ly) - sp.pad))
        self._labels(img, k, sorted({0, n - 1} | ({n // 2} if n >= 5 else set())))
        return img.resize((int(self.bw), int(self.bh)), Image.LANCZOS)

    def _bars(self, p):
        c, k = self.ctx, 2
        img = Image.new("RGBA", (int(self.bw * k), int(self.bh * k)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        self._grid(d, k)
        n = len(self.pts)
        pw, ph = self.bw * k, (self.bh - self.lab) * k
        slot = pw / n
        bw = min(slot * 0.62, c.px(190) * k)
        base = ph * 0.96
        hi = self.spec.get("highlight", n - 1)
        dim = mix(c.kit["surface"], self.acc, 0.42)
        for i, (lab, v) in enumerate(self.pts):
            q = ease_out_cubic(clamp(p * (1 + 0.6) - 0.6 * i / max(1, n - 1)))
            if q <= 0:
                continue
            x = slot * i + (slot - bw) / 2
            top = base - (ph * 0.92) * ((v - self.vmin) / (self.vmax - self.vmin)) * q
            col = (self.acc if i == hi else dim) + (255,)
            d.rounded_rectangle([x, top, x + bw, base], radius=min(bw / 6, c.px(12) * k), fill=col)
            d.rectangle([x, max(top, base - c.px(12) * k), x + bw, base], fill=col)
            if q > 0.55:
                sp = T.sprite(self.fmt(v), c.fnt("heading")[0], c.px(34) * k, 800,
                              c.col("text", int(255 * clamp((q - 0.55) / 0.3))), None, 0, 0.0, 0.0)
                img.alpha_composite(sp.img, (int(x + bw / 2 - sp.w / 2) - sp.pad,
                                             int(max(0, top - sp.h - c.px(4) * k)) - sp.pad))
            if lab:
                sp = T.sprite(lab, c.fnt("body")[0], c.px(30) * k, c.fnt("body")[1], c.col("muted"))
                img.alpha_composite(sp.img, (int(clamp(x + bw / 2 - sp.w / 2, 0, pw - sp.w)) - sp.pad,
                                             int(ph + c.px(12) * k) - sp.pad))
        return img.resize((int(self.bw), int(self.bh)), Image.LANCZOS)

    def draw(self, canvas, t):
        if t < self.at:
            return
        c = self.ctx
        if self.has_media and self.spec.get("scrim", True):
            self.scrim(canvas, t, 0.66)
        o = self.out(t)
        y = self.y0
        if self.title:
            for k, sp in enumerate(self.title):
                p = self.stage(t, k)
                T.paste_sprite(canvas, sp, (c.W - sp.w) / 2, y + (1 - p) * c.px(22), p * o)
                y += self.tlh
        p = clamp((t - self.at - 0.35) / self.draw_secs)
        p = lerp(p, ease_out_cubic(p), 0.5)
        if p >= 1 and self._final is not None:
            img = self._final
        else:
            img = self._render(p)
            if p >= 1:
                self._final = img
        T.paste(canvas, img, self.x0, self.y0 + self.th, self.stage(t, 0, dur=0.4) * o)


OVERLAYS = {
    "title": Title, "stat": Stat, "quote": Quote, "bullets": Bullets, "lower_third": LowerThird,
    "label": Label, "text": Text, "image": Picture, "chart": Chart,
}


def make(spec, ctx, dur, has_media):
    kind = spec.get("type")
    if kind not in OVERLAYS:
        raise StudioError(f"Unknown overlay type '{kind}'. Options: {', '.join(OVERLAYS)}.")
    return OVERLAYS[kind](dict(spec), ctx, dur, has_media)
