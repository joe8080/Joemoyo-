"""Word-by-word animated captions (the CapCut look), plus SRT export.

Styles:
  pop   - bold uppercase, thick outline, the spoken word pops in the accent colour
  box   - a rounded highlight box slides from word to word
  clean - calm sentence-case line on a dark pill, spoken words light up (documentary)
"""
from __future__ import annotations

import bisect

from PIL import Image

from . import text as T
from .util import StudioError, clamp, ease_out_cubic, lerp, luminance

STYLES = ("pop", "box", "clean")
_KEEP = "£$€%?!'’"


def _display(word, style):
    if style == "clean":
        return word
    w = word.strip()
    while w and not w[0].isalnum() and w[0] not in "£$€":
        w = w[1:]
    while w and not w[-1].isalnum() and w[-1] not in _KEEP:
        w = w[:-1]
    return w.upper()


class Captions:
    def __init__(self, cfg, ctx, words):
        """words: [{"t": text, "s": start, "e": end}] in absolute timeline seconds."""
        self.ctx = c = ctx
        cfg = dict(cfg or {})
        self.style = cfg.get("style") or c.kit.get("captions", "pop")
        if self.style not in STYLES:
            raise StudioError(f"Unknown caption style '{self.style}'. Options: {', '.join(STYLES)}.")
        scale = float(cfg.get("scale", 1.0))
        st = self.style
        base = {"pop": (84, 72), "box": (78, 66), "clean": (50, 44)}[st]
        self.size = c.px(base[0 if c.portrait else 1] * scale)
        self.fname, kit_w = c.fnt("caption")
        self.weight = int(cfg.get("weight", kit_w if st != "clean" else min(kit_w, 600)))
        self.max_words = int(cfg.get("max_words", {"pop": (3, 4), "box": (3, 4), "clean": (7, 10)}[st][0 if c.portrait else 1]))
        self.max_w = c.W * float(cfg.get("max_width", {"pop": (0.84, 0.62), "box": (0.84, 0.62),
                                                       "clean": (0.84, 0.66)}[st][0 if c.portrait else 1]))
        pos = cfg.get("position", "bottom")
        if isinstance(pos, (int, float)):
            self.cy = c.H * float(pos)
        else:
            self.cy = c.H * {"bottom": c.caption_y + (0.03 if st == "clean" and not c.portrait else 0.0),
                             "center": 0.5, "top": 0.15}.get(pos, c.caption_y)
        accent = cfg.get("color", "accent")
        self.accent = c.col(accent)
        self.accent_light = luminance(c.kit.get(accent, accent)) > 0.55
        self.f = T.font(self.fname, self.size, self.weight)
        self.stroke_w = {"pop": max(3, int(self.size * 0.105)), "box": max(2, int(self.size * 0.05)), "clean": 0}[st]
        self.space = self.f.getlength(" ") * (1.0 if st == "clean" else 1.15) + self.stroke_w * (1.3 if st == "pop" else 0.6)
        self.groups = self._group(words)
        self.starts = [g["s"] for g in self.groups]
        self._steady = {}

    # ------------------------------------------------------------ grouping
    def _group(self, words):
        groups, cur, cur_w = [], [], 0.0

        def flush():
            nonlocal cur, cur_w
            if cur:
                groups.append(cur)
            cur, cur_w = [], 0.0

        prev_raw, prev_e = "", None
        for w in words:
            disp = _display(w["t"], self.style)
            if not disp:
                continue
            ww = self.f.getlength(disp)
            brk = False
            if cur:
                if cur_w + self.space + ww > self.max_w or len(cur) >= self.max_words:
                    brk = True
                elif prev_raw[-1:] in ".?!":
                    brk = True
                elif prev_raw[-1:] in ",;:—" and len(cur) >= 2:
                    brk = True
                elif prev_e is not None and w["s"] - prev_e > 0.6:
                    brk = True
            if brk:
                flush()
            cur.append({"t": disp, "s": w["s"], "e": w["e"], "w": ww})
            cur_w = cur_w + (self.space if len(cur) > 1 else 0) + ww
            prev_raw, prev_e = w["t"], w["e"]
        flush()
        out = []
        for i, ws in enumerate(groups):
            total = sum(x["w"] for x in ws) + self.space * (len(ws) - 1)
            x = (self.ctx.W - total) / 2
            for wd in ws:
                wd["x"] = x
                x += wd["w"] + self.space
            g = {"s": ws[0]["s"], "e": ws[-1]["e"] + 0.15, "words": ws, "w": total, "x": (self.ctx.W - total) / 2}
            out.append(g)
        for i in range(len(out) - 1):
            nxt = out[i + 1]["s"]
            if nxt - out[i]["e"] < 0.45 or nxt < out[i]["e"]:
                out[i]["e"] = nxt
        return out

    # ------------------------------------------------------------ drawing
    def _spr(self, txt, fill, stroke=True, shadow=0.55):
        c = self.ctx
        if self.style == "clean":
            return T.sprite(txt, self.fname, self.size, self.weight, fill)
        return T.sprite(txt, self.fname, self.size, self.weight, fill,
                        (0, 0, 0, 255) if stroke else None, self.stroke_w if stroke else 0, shadow, 0.0)

    def draw(self, canvas, t):
        i = bisect.bisect_right(self.starts, t + 0.02) - 1
        if i < 0:
            return
        g = self.groups[i]
        if t >= g["e"]:
            return
        c = self.ctx
        age = t - g["s"] + 0.02
        ent = ease_out_cubic(age / 0.1)
        a = ent
        rise = (1 - ent) * c.px(10)
        ws = g["words"]
        act = 0
        for k, wd in enumerate(ws):
            if wd["s"] <= t + 0.02:
                act = k
        asc, desc = self.f.getmetrics()
        y = self.cy - (asc + desc) / 2 + rise
        white = (255, 255, 255, 255)

        if self.style == "clean":
            padx, pady = c.px(26), c.px(13)
            box = T.rounded_box(int(g["w"] + 2 * padx), int(asc + desc + 2 * pady), c.px(14), c.col("bg", 190))
            T.paste(canvas, box, g["x"] - padx, y - pady, a)
            for k, wd in enumerate(ws):
                fill = self.accent if k == act else (c.col("text") if k < act else c.col("text", 130))
                T.paste_sprite(canvas, self._spr(wd["t"], fill), wd["x"], y, a)
            return

        if self.style == "box":
            padx, pady = c.px(14), c.px(4)
            cur = ws[act]
            bx, bw = cur["x"], cur["w"]
            if act > 0:
                prv = ws[act - 1]
                q = ease_out_cubic((t + 0.02 - cur["s"]) / 0.12)
                bx, bw = lerp(prv["x"], bx, q), lerp(prv["w"], bw, q)
            box = T.rounded_box(int(round(bw + 2 * padx)), int(asc + desc + 2 * pady), c.px(16), self.accent)
            T.paste(canvas, box, bx - padx, y - pady, a)
            for k, wd in enumerate(ws):
                if k == act and self.accent_light:
                    sp = self._spr(wd["t"], (12, 12, 16, 255), stroke=False, shadow=0.0)
                else:
                    sp = self._spr(wd["t"], white, stroke=k != act, shadow=0.5 if k != act else 0.0)
                T.paste_sprite(canvas, sp, wd["x"], y, a)
            return

        # pop
        for k, wd in enumerate(ws):
            if k != act:
                T.paste_sprite(canvas, self._spr(wd["t"], white), wd["x"], y, a)
        wd = ws[act]
        sp = self._spr(wd["t"], self.accent)
        since = t + 0.02 - wd["s"]
        scale = 1.05 + 0.10 * max(0.0, 1 - since / 0.14)
        steady = scale <= 1.0501
        key = (i, act)
        img = self._steady.get(key) if steady else None
        if img is None:
            img = sp.img.resize((max(1, int(sp.img.width * scale)), max(1, int(sp.img.height * scale))),
                                Image.BICUBIC)
            if steady:
                if len(self._steady) > 64:
                    self._steady.clear()
                self._steady[key] = img
        cx = wd["x"] + wd["w"] / 2
        cyy = y + (asc + desc) / 2
        T.paste(canvas, img, cx - img.width / 2, cyy - img.height / 2, a)


# ---------------------------------------------------------------- SRT

def _ts(t):
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt(words, max_chars=42):
    """Readable sentence-case subtitles for YouTube upload (not the burned-in style)."""
    cues, cur = [], []

    def flush():
        nonlocal cur
        if cur:
            cues.append((cur[0]["s"], cur[-1]["e"], " ".join(w["t"] for w in cur)))
        cur = []

    for w in words:
        trial = " ".join(x["t"] for x in cur + [w])
        if cur and (len(trial) > max_chars or w["s"] - cur[-1]["e"] > 0.7):
            flush()
        cur.append(w)
        if w["t"][-1:] in ".?!":
            flush()
    flush()
    out = []
    for n, (s, e, txt) in enumerate(cues, 1):
        nxt = cues[n][0] if n < len(cues) else None
        e = max(e, s + 0.7)
        if nxt is not None:
            e = min(e, nxt - 0.02)
        out.append(f"{n}\n{_ts(s)} --> {_ts(e)}\n{txt}\n")
    return "\n".join(out)
