"""Kongo v1.1 compositor (runs in the Higgsfield sandbox).

python3 film.py map            -> build/map_locator.png
python3 film.py render A B N   -> build/part_N.mp4 for timeline seconds [A, B)
Shots are anchored to narration words (build/timeline.json from audio_build.py).
Look: black, gold and sepia. Every AI image carries an on-screen AI label.
"""
import json, os, re, subprocess, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 25
XF = 0.6                       # dissolve length
GOLD = (205, 166, 82); CREAM = (236, 226, 204); GREY = (168, 160, 146); DIM = (120, 112, 98)
SERIF = "fonts/EBGaramond.ttf"; SANS = "fonts/Montserrat.ttf"
B = "build"

AI = "AI RECONSTRUCTION · ILLUSTRATIVE, NOT A RECORD"
L_JUL = "LETTER OF 6 JULY 1526 · ARQUIVO NACIONAL TORRE DO TOMBO · PT/TT/CC/1/34/94"
L_OCT = "LETTER OF 18 OCTOBER 1526 · TORRE DO TOMBO · PT/TT/CC/1/35/21 · MICROFILM"
TR = "TRANSLATED FROM PORTUGUESE (OGX WORKING TRANSLATION)"
MAPNOTE = "MODERN BORDERS FOR ORIENTATION ONLY · KINGDOM EXTENT APPROXIMATE (AFTER THORNTON 2020)"

P1 = dict(src="letters/10759224.jpg", pre=(0.0, 0.0, 0.745, 1.0))
P2 = dict(src="letters/10759223.jpg")
P4 = dict(src="letters/10759222.jpg")
O1 = dict(src="letters/10730360.jpg", pre=(0.0, 0.14, 1.0, 1.0))
O2 = dict(src="letters/10730361.jpg", pre=(0.0, 0.12, 1.0, 1.0))


def fnt(path, size, var="Regular"):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name(var)
    except Exception:
        pass
    return f


# ---------------------------------------------------------------- shot plan
def doc(p, r0, r1=None, label=L_JUL, **kw):
    d = dict(kind="fill", r0=r0, r1=r1 or r0, label=label); d.update(p); d.update(kw); return d

def page(p, z0=1.0, z1=1.07, label=L_JUL, **kw):
    d = dict(kind="fit", z0=z0, z1=z1, label=label); d.update(p); d.update(kw); return d

def still(src, r0=(0.03, 0.03, 0.97), r1=(0.0, 0.0, 1.0), label=None, **kw):
    d = dict(kind="fill", src=src, r0=r0, r1=r1, label=label); d.update(kw); return d

def clip(name, label=AI, off=0.0, dark=None, fallback_r0=(0.0, 0.0, 1.0), fallback_r1=(0.06, 0.06, 0.94)):
    """name like 'K1a': motion clip clips/K1a.mp4 (v1.1: every AI image is a real motion clip)."""
    path = f"clips/{name}.mp4"
    if os.path.exists(path):
        d = dict(kind="clip", src=path, label=label, off=off)
    else:
        d = still(f"ai/{name[:2]}.png", fallback_r0, fallback_r1, label=label)
    if dark:
        d["dark"] = dark
    return d

def card(style, **kw):
    d = dict(kind="card", style=style); d.update(kw); return d

ARCH = {k: f"arch/{k}.jpg" for k in ["MAP1668", "MAP1690", "BANSA1670", "SHIPS", "CAVAZZI", "CUSHION",
                                       "NZIMBU", "TT", "JOAO3", "CRUCIFIX", "BAPTISM"]}

PLAN = {
 "R0": [   # v1.1 cold open: the king's warning first
  (None, card("quote", text="“Our kingdom is being lost…”",
              attr="AFONSO I, KING OF KONGO, TO JOÃO III OF PORTUGAL, 6 JULY 1526 · " + TR, bg=P2)),
  ("Merchants are taking", card("quote", text="“…our people, sons of the land, sons of our nobles and vassals, and our relatives.”",
                                attr="AFONSO I TO JOÃO III, 6 JULY 1526 · " + TR, bg=P2)),
  ("And the land, he says", clip("K1b")),
 ],
 "R1": [
  (None, page(P1, 1.0, 1.10)),
  ("It was written down", doc(P2, (0.30, 0.74, 0.86), (0.36, 0.78, 0.80))),
  ("His Christian name", card("person", title="AFONSO I", sub="MVEMBA A NZINGA · KING OF KONGO, c. 1506–1542",
                              note="No portrait of him made in his lifetime survives.")),
  ("It starts politely", clip("K1a")),
  ("And he's sorry", clip("K3a")),
 ],
 "R2": [
  (None, card("question", text="Why would a king in Central Africa send that warning to Portugal?")),
  ("His letters give us", page(O1, 1.0, 1.08, label=L_OCT)),
  ("Slavery existed in Kongo", still(ARCH["SHIPS"], (0.0, 0.05, 1.0), (0.1, 0.12, 0.8),
                                      label="PORTUGUESE SHIPS · LIVRO DAS ARMADAS, c. 1568 · ACADEMIA DAS CIÊNCIAS DE LISBOA")),
  ("What his letters complain", clip("K5a")),
  ("To see why", clip("K2a")),
 ],
 "R3": [
  (None, clip("K2b")),
  ("It wasn't Kinshasa", still("build/map_locator.png", (0.0, 0.0, 1.0), (0.035, 0.035, 0.965), label=MAPNOTE)),
  ("By the late fourteen hundreds", still(ARCH["MAP1668"], (0.25, 0.25, 0.80), (0.30, 0.32, 0.70),
                                          label="‘REGNA CONGO ET ANGOLA’ · OLFERT DAPPER, 1668 · DRAWN 140 YEARS LATER · CC BY-SA 4.0")),
  ("Its kings weren't", still(ARCH["BANSA1670"], (0.0, 0.0, 1.0), (0.15, 0.1, 0.75),
                              label="THE CAPITAL AS IMAGINED BY A EUROPEAN ENGRAVER, 1670 · NOT DRAWN FROM LIFE")),
  ("People paid tribute", still(ARCH["CUSHION"], (0.05, 0.05, 0.95), (0.2, 0.15, 0.8),
                                label="KONGO RAFFIA CLOTH (CUSHION COVER), 17TH CENTURY · ETNOGRAFISKA MUSEET, STOCKHOLM · CC BY-SA")),
  ("Their money included", still(ARCH["NZIMBU"], (0.1, 0.05, 0.9), (0.25, 0.2, 0.75),
                                 label="NZIMBU SHELL (OLIVANCILLARIA NANA) · NATURALIS BIODIVERSITY CENTER · CC0")),
  ("So long before", clip("K6a")),
  ("The Portuguese joined", still(ARCH["BANSA1670"], (0.2, 0.2, 0.8), (0.0, 0.0, 1.0),
                                  label="THE CAPITAL AS IMAGINED BY A EUROPEAN ENGRAVER, 1670")),
 ],
 "R4": [
  (None, still(ARCH["SHIPS"], (0.1, 0.12, 0.8), (0.0, 0.05, 1.0), label="PORTUGUESE SHIPS · LIVRO DAS ARMADAS, c. 1568")),
  ("In 1491", page(dict(src=ARCH["BAPTISM"]), 1.0, 1.08,
                  label="THE 1491 BAPTISM AS IMAGINED BY A FRENCH ENGRAVER, 1780 · NOT DRAWN FROM LIFE")),
  ("When the old king", card("date", title="c. 1506", sub="Afonso fights a rival from the royal family for the throne — and wins.")),
  ("He won, and he", still(ARCH["BANSA1670"], (0.45, 0.15, 0.95), (0.35, 0.1, 0.95), label="THE CAPITAL AS IMAGINED BY A EUROPEAN ENGRAVER, 1670")),
  ("He wrote to the Pope", page(dict(src=ARCH["CRUCIFIX"]), 1.0, 1.08,
                               label="KONGO CRUCIFIX, 16TH–17TH CENTURY · THE METROPOLITAN MUSEUM OF ART · CC0")),
  ("And in 1518", card("date", title="1518", sub="Pope Leo X names Afonso’s son Henrique a bishop.")),
  ("In 1516", clip("K4a")),
  ("That's a missionary", card("quote", text="“…he knows the Prophets and the Gospel … better than we do.”",
                               attr="RUI DE AGUIAR, PORTUGUESE PRIEST, TO KING MANUEL, 1516 · " + TR)),
  ("But it also tells you", clip("K4b")),
  ("None of this came free", card("date", title="1512", sub="King Manuel’s orders: load the ships with “slaves, copper and ivory”.")),
  ("to cover the cost", still(ARCH["SHIPS"], (0.05, 0.3, 0.6), (0.0, 0.2, 0.75), label="PORTUGUESE SHIPS · LIVRO DAS ARMADAS, c. 1568")),
  ("And Afonso paid", card("date", title="1514", sub="Afonso describes sending more than 400 war captives to load one Portuguese ship.")),
  ("he describes sending", clip("K1a", off=3.0)),
  ("In Kongo, people captured", page(dict(src=ARCH["CAVAZZI"]), 1.0, 1.08, label="GIOVANNI CAVAZZI, CAPUCHIN MISSIONARY · KONGO–ANGOLA SCENE, 1650s · CC BY 4.0")),
 ],
 "R5": [
  (None, doc(P2, (0.04, 0.02, 0.96), (0.10, 0.06, 0.76))),
  ("The first was goods", clip("K6b")),
  ("Those goods were spreading", clip("K6a", off=3.0)),
  ("For a king who held", still(ARCH["BANSA1670"], (0.3, 0.25, 0.8), (0.1, 0.1, 0.9),
                                 label="THE CAPITAL AS IMAGINED BY A EUROPEAN ENGRAVER, 1670")),
  ("The second was people", clip("K5b")),
  ("and selling them", clip("K1b", off=5.0, dark=0.8)),
  ("In July, Afonso's answer", doc(P2, (0.05, 0.55, 0.95), (0.10, 0.60, 0.80))),
  ("Send us priests", page(P2, 1.0, 1.06)),
  ("It is our will", card("quote", text="“…it is our will that in these kingdoms there should be no trade in slaves, nor any outlet for them.”",
                          attr="AFONSO I TO JOÃO III, 6 JULY 1526 · " + TR, bg=P2)),
 ],
 "R6": [
  (None, page(O1, 1.0, 1.10, label=L_OCT)),
  ("Free people were being taken", clip("K5c", dark=0.8)),
  ("Afonso's guards caught", doc(O1, (0.05, 0.30, 0.95), (0.10, 0.38, 0.85), label=L_OCT)),
  ("So he made a law", page(O2, 1.0, 1.06, label=L_OCT)),
  ("Dom Pedro Manipunzo", card("names", names=["DOM PEDRO MANIPUNZO", "DOM MANUEL MANISSABA · CHIEF BAILIFF",
                                               "GONÇALO PIRES · CHIEF OUTFITTER"],
                               head="THREE OFFICIALS OF THE ROYAL COURT · 18 OCTOBER 1526", bg=O2, bgk=0.30)),
  ("The three would decide", card("names", names=["FREE?", "OR LAWFULLY ENSLAVED?"],
                                  head="EVERY PERSON BOUGHT HAD TO BE SHOWN FIRST", static=True, bg=O1, bgk=0.30)),
  ("If they passed", doc(O2, (0.05, 0.30, 0.95), (0.12, 0.40, 0.82), label=L_OCT)),
  ("So in July", card("names", names=["JULY: “NO TRADE IN SLAVES”", "OCTOBER: SOME SALES, AFTER ROYAL CHECKS"],
                      head="TWO LETTERS, THREE MONTHS APART · 1526", bg=P2, bgk=0.30)),
 ],
 "R7": [
  (None, page(dict(src=ARCH["JOAO3"]), 1.0, 1.06, label="JOÃO III OF PORTUGAL · ANTONIS MOR, 1552 · PUBLIC DOMAIN")),
  ("In a letter written", card("date", title="c. 1529", sub="João III replies to the king of Kongo.")),
  ("it seemed not a single", still(ARCH["MAP1668"], (0.1, 0.4, 0.6), (0.2, 0.45, 0.6), label="‘REGNA CONGO ET ANGOLA’ · OLFERT DAPPER, 1668 · CC BY-SA 4.0")),
  ("He suggested a fixed", still(ARCH["BANSA1670"], (0.35, 0.35, 0.85), (0.2, 0.2, 0.9),
                                 label="THE CAPITAL AS IMAGINED BY A EUROPEAN ENGRAVER, 1670")),
  ("Then he added this", page(dict(src=ARCH["JOAO3"]), 1.06, 1.14, label="JOÃO III OF PORTUGAL · ANTONIS MOR, 1552")),
  ("But that wouldn't do", still(ARCH["SHIPS"], (0.4, 0.3, 1.0), (0.3, 0.25, 0.95), label="PORTUGUESE SHIPS · LIVRO DAS ARMADAS, c. 1568")),
  ("Better, he wrote", card("quote", text="“…more praiseworthy that 10,000 slaves … be taken from Kongo each year … than that it be said there is no trade.”",
                            attr="JOÃO III TO THE KING OF KONGO, c. 1529 · " + TR)),
  ("The same letter told", page(dict(src=ARCH["CRUCIFIX"]), 1.08, 1.0, label="KONGO CRUCIFIX, 16TH–17TH CENTURY · THE MET · CC0")),
  ("So the trade went on", clip("K1a", off=4.0)),
  ("There's a lot these letters", page(dict(src=ARCH["TT"]), 1.0, 1.06,
                                       label="ARQUIVO NACIONAL DA TORRE DO TOMBO, LISBON · PHOTO CC0")),
  ("We don't have the voices", page(P4, 1.0, 1.05, label=L_JUL + " · ADDRESS SIDE", dark=0.55)),
 ],
 "R8": [
  (None, page(P1, 1.10, 1.0)),
  ("We can't know", clip("K3a", off=3.0)),
  ("Free people, his nobles", clip("K5b", off=3.0)),
  ("Foreign goods were buying", clip("K6b", off=4.0)),
  ("In July, he asked", page(P2, 1.0, 1.06)),
  ("By October, he was", page(O2, 1.04, 1.0, label=L_OCT)),
  ("What his letters show", clip("K2a", off=3.0)),
  ("And they show how fast", doc(P2, (0.36, 0.78, 0.80), (0.05, 0.40, 0.95))),
 ],
}
TITLE = card("title", title="KONGO, 1526", sub="WHAT THE KING’S LETTERS REVEAL")
END = card("end")


# ---------------------------------------------------------------- helpers
def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("ç", "c").replace("ã", "a").replace("’", "'"))


def build_shots(tl):
    shots = []
    for sec, items in PLAN.items():
        d = tl["sections"][sec]
        toks = [norm(w[0]) for w in d["words"]]
        pos = 0
        for anchor, spec in items:
            if anchor is None:
                t = d["start"] - (0.25 if shots else 2.0)
            else:
                a = [norm(x) for x in anchor.split()]
                found = None
                for i in range(pos, len(toks) - len(a) + 1):
                    if toks[i:i + len(a)] == a:
                        found = i; break
                if found is None:
                    raise SystemExit(f"anchor not found {sec}: {anchor}")
                pos = found + 1
                t = d["words"][found][1] - 0.15
            shots.append(dict(spec, t=max(0.0, t)))
        if sec == "R0":
            shots.append(dict(TITLE, t=d["start"] + d["dur"] + 0.4))
    shots.append(dict(END, t=tl["end_card"]))
    shots.sort(key=lambda s: s["t"])
    for i, s in enumerate(shots):
        s["end"] = shots[i + 1]["t"] if i + 1 < len(shots) else tl["total"]
        s["i"] = i
    return shots


_img = {}
def load(spec):
    key = (spec["src"], spec.get("pre"))
    if key not in _img:
        im = Image.open(spec["src"]).convert("RGB")
        if spec.get("pre"):
            x0, y0, x1, y1 = spec["pre"]; w, h = im.size
            im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        _img[key] = im
    return _img[key]


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def rect16(im, r):
    """r = (x0, y0, x1) normalised; height derived for 16:9; clamp inside image."""
    w, h = im.size
    x0, y0, x1 = r[0] * w, r[1] * h, r[2] * w
    cw = x1 - x0; ch = cw * 9 / 16
    if ch > h:
        ch = h; cw = ch * 16 / 9; x0 = max(0, (x0 + x1) / 2 - cw / 2)
    y0 = min(max(0, y0), h - ch); x0 = min(max(0, x0), w - cw)
    return x0, y0, cw, ch


def render_fill(spec, u):
    im = load(spec)
    a = rect16(im, spec["r0"]); b = rect16(im, spec["r1"]); e = ease(u)
    x, y, cw, ch = [a[k] + (b[k] - a[k]) * e for k in range(4)]
    fr = im.resize((W, H), Image.BICUBIC, box=(x, y, x + cw, y + ch))
    return np.asarray(fr, dtype=np.float32)


_bg = {}
def page_bg(spec):
    key = (spec["src"], spec.get("pre"))
    if key not in _bg:
        im = load(spec)
        bg = im.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(40))
        _bg[key] = np.asarray(bg, dtype=np.float32) * 0.22
    return _bg[key]


def render_fit(spec, u):
    im = load(spec)
    z = spec["z0"] + (spec["z1"] - spec["z0"]) * ease(u)
    w, h = im.size
    s = min(W * 0.92 / w, H * 0.92 / h) * z
    nw, nh = int(w * s), int(h * s)
    out = page_bg(spec).copy()
    fr = np.asarray(im.resize((nw, nh), Image.BICUBIC), dtype=np.float32)
    x0, y0 = (W - nw) // 2, (H - nh) // 2
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    cw, ch = min(nw - sx0, W - dx0), min(nh - sy0, H - dy0)
    out[dy0:dy0 + ch, dx0:dx0 + cw] = fr[sy0:sy0 + ch, sx0:sx0 + cw]
    return out


class ClipReader:
    def __init__(self, spec, start_local):
        self.spec = spec
        dur = spec["end"] - spec["t"] + XF
        src_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                        spec["src"]], capture_output=True, text=True).stdout.strip() or 6)
        off = spec.get("off", 0.0)
        src_len = max(src_len - off, 1.0)
        f = min(max(dur / src_len, 1.0), 1.8)          # slow down up to 1.8x, then hold
        vf = (f"trim=start={off:.2f},setpts=PTS-STARTPTS,setpts={f:.4f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"tpad=stop_mode=clone:stop_duration=60")
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", spec["src"], "-vf", vf,
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.n = 0; self.last = np.zeros((H, W, 3), np.float32)
        skip = int(round(start_local * FPS))
        for _ in range(skip):
            self._read()

    def _read(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
        self.n += 1
        return self.last

    def frame(self, local):
        target = int(round(local * FPS))
        while self.n <= target:
            self._read()
        return self.last


# ---------------------------------------------------------------- cards
def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def spaced(draw, xy, text, font, fill, spacing=4, anchor_center=False):
    x, y = xy
    total = sum(draw.textlength(c, font=font) + spacing for c in text) - spacing
    if anchor_center:
        x -= total / 2
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + spacing
    return total


_card = {}
def card_layers(spec):
    """Returns (bg float array, list of (rgba overlay, reveal_time))."""
    k = spec["i"]
    if k in _card:
        return _card[k]
    if spec.get("bg"):
        bgsrc = load(spec["bg"])
        bg = np.asarray(bgsrc.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6)),
                        dtype=np.float32) * spec.get("bgk", 0.16)
    else:
        bg = np.zeros((H, W, 3), np.float32) + np.array([10, 8, 6], np.float32)
    layers = []
    st = spec["style"]

    def new():
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); return im, ImageDraw.Draw(im)

    if st in ("quote", "question", "statement"):
        im, d = new()
        size = 70 if st == "quote" else 84
        f = fnt(SERIF, size, "Regular")
        lines = wrap(d, spec["text"], f, 1400)
        lh = int(size * 1.28); y = H // 2 - len(lines) * lh // 2 - (30 if spec.get("attr") else 0)
        for ln in lines:
            d.text((W // 2, y), ln, font=f, fill=CREAM if st == "quote" else GOLD, anchor="ma"); y += lh
        if spec.get("attr"):
            d.line([(W // 2 - 60, y + 26), (W // 2 + 60, y + 26)], fill=GOLD, width=2)
            spaced(d, (W // 2, y + 50), spec["attr"], fnt(SANS, 20, "Medium"), GREY, 2, True)
        layers.append((im, 0.0))
    elif st == "person":
        im, d = new()
        d.text((W // 2, 380), spec["title"], font=fnt(SERIF, 120, "Medium"), fill=GOLD, anchor="ma")
        spaced(d, (W // 2, 540), spec["sub"], fnt(SANS, 28, "Medium"), CREAM, 4, True)
        d.text((W // 2, 640), spec["note"], font=fnt(SERIF, 38, "Regular"), fill=GREY, anchor="ma")
        layers.append((im, 0.0))
    elif st == "date":
        im, d = new()
        d.text((W // 2, 330), spec["title"], font=fnt(SERIF, 150, "Medium"), fill=GOLD, anchor="ma")
        f = fnt(SERIF, 52, "Regular")
        y = 560
        for ln in wrap(d, spec["sub"], f, 1300):
            d.text((W // 2, y), ln, font=f, fill=CREAM, anchor="ma"); y += 68
        layers.append((im, 0.0))
    elif st == "names":
        im, d = new()
        spaced(d, (W // 2, 300), spec["head"], fnt(SANS, 24, "Medium"), GREY, 4, True)
        layers.append((im, 0.0))
        f = fnt(SERIF, 66, "Medium")
        for n, name in enumerate(spec["names"]):
            im, d = new()
            d.text((W // 2, 420 + n * 110), name, font=f, fill=GOLD, anchor="ma")
            layers.append((im, 0.0 if spec.get("static") else 0.5 + n * 1.6))
    elif st == "title":
        im, d = new()
        d.text((W // 2, 400), spec["title"], font=fnt(SERIF, 150, "Medium"), fill=GOLD, anchor="ma")
        spaced(d, (W // 2, 600), spec["sub"], fnt(SANS, 30, "Medium"), CREAM, 8, True)
        layers.append((im, 0.0))
    elif st == "end":
        # v1.3: clean end screen (no private-preview line, no source list; credits go in the description)
        im, d = new()
        d.text((W // 2, 420), "KONGO, 1526", font=fnt(SERIF, 110, "Medium"), fill=GOLD, anchor="ma")
        spaced(d, (W // 2, 590), "ORIGINEX HUMAN ARCHIVES", fnt(SANS, 30, "Medium"), CREAM, 8, True)
        layers.append((im, 0.0))
    out = (bg, [(np.asarray(l, dtype=np.float32), t) for l, t in layers])
    _card[k] = out
    return out


def render_card(spec, local):
    bg, layers = card_layers(spec)
    fr = bg.copy()
    for arr, t0 in layers:
        a = min(max((local - t0) / 0.7, 0.0), 1.0)
        if a <= 0:
            continue
        al = arr[..., 3:4] / 255.0 * a
        fr = fr * (1 - al) + arr[..., :3] * al
    return fr


# ---------------------------------------------------------------- labels, grade
_lab = {}
def label_overlay(text):
    if text not in _lab:
        f = fnt(SANS, 19, "Medium")
        im = Image.new("RGBA", (W, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        tw = sum(d.textlength(c, font=f) + 2 for c in text)
        d.rectangle([40, 12, 40 + tw + 28, 50], fill=(0, 0, 0, 150))
        spaced(d, (54, 20), text, f, (226, 212, 180), 2)
        _lab[text] = np.asarray(im, dtype=np.float32)
    return _lab[text]


yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.38 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.4).clip(0.35, 1)[..., None].astype(np.float32)
del yy, xx
RNG = np.random.default_rng(7)
GRAIN = [RNG.normal(0, 5.0, (H, W, 1)).astype(np.float32) for _ in range(6)]
TONE = np.array([1.04, 0.99, 0.90], np.float32)    # warm sepia lean


def render_shot(spec, t, readers):
    local = t - spec["t"]
    dur = spec["end"] - spec["t"] + XF
    u = local / max(dur, 0.1)
    k = spec["kind"]
    if k == "fill":
        fr = render_fill(spec, u)
    elif k == "fit":
        fr = render_fit(spec, u)
    elif k == "clip":
        r = readers.get(spec["i"])
        if r is None:
            r = readers[spec["i"]] = ClipReader(spec, max(local, 0))
        fr = r.frame(max(local, 0))
    else:
        fr = render_card(spec, local)
    if spec.get("dark"):
        fr = fr * spec["dark"]
    if spec.get("label") and k != "card":
        lab = label_overlay(spec["label"])
        a = min(max((local - 0.4) / 0.5, 0), 1) * (lab[..., 3:4] / 255.0)
        region = fr[H - 92:H - 32]
        fr[H - 92:H - 32] = region * (1 - a) + lab[..., :3] * a
    return fr


def render(a, b, part):
    tl = json.load(open(f"{B}/timeline.json"))
    shots = build_shots(tl)
    readers = {}
    out = f"{B}/part_{part:02d}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                            "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n0, n1 = int(round(a * FPS)), int(round(b * FPS))
    for n in range(n0, n1):
        t = n / FPS
        cur = max((s for s in shots if s["t"] <= t), key=lambda s: s["t"], default=shots[0])
        fr = render_shot(cur, t, readers)
        if cur["i"] > 0 and t - cur["t"] < XF:
            prev = shots[cur["i"] - 1]
            al = ease((t - cur["t"]) / XF)
            fr = render_shot(prev, t, readers) * (1 - al) + fr * al
        if t < 1.2:
            fr = fr * (t / 1.2)
        if t > tl["total"] - 2.0:
            fr = fr * max(0.0, (tl["total"] - t) / 2.0)
        fr = fr * TONE * VIG + GRAIN[n % 6]
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
        if n % 250 == 0:
            print(part, f"{t:.1f}", flush=True)
    enc.stdin.close(); enc.wait()
    for r in readers.values():
        r.p.kill()
    print("done", out, flush=True)


# ---------------------------------------------------------------- locator map
def build_map():
    import json as js
    MW, MH = 2560, 1440
    lon0, lon1, lat0, lat1 = 8.8, 21.2, -10.5, -3.5
    def P(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * MW, (lat1 - lat) / (lat1 - lat0) * MH)
    im = Image.new("RGB", (MW, MH), (8, 10, 12)); d = ImageDraw.Draw(im, "RGBA")
    gj = js.load(open("geo/countries.geojson"))
    def polys(geom):
        if geom["type"] == "Polygon":
            return [geom["coordinates"]]
        return geom["coordinates"]
    for ft in gj["features"]:
        for poly in polys(ft["geometry"]):
            ring = [P(x, y) for x, y in poly[0]]
            d.polygon(ring, fill=(38, 33, 24))
    for ft in gj["features"]:
        for poly in polys(ft["geometry"]):
            ring = [P(x, y) for x, y in poly[0]]
            d.line(ring + [ring[0]], fill=(110, 100, 80), width=3)
    try:
        rv = js.load(open("geo/rivers.geojson"))
        for ft in rv["features"]:
            g = ft["geometry"]; lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
            for ln in lines:
                d.line([P(x, y) for x, y in ln], fill=(70, 92, 104), width=4)
    except Exception as e:
        print("rivers skipped", e)
    kongo = [(12.25, -5.95), (12.9, -5.85), (13.6, -5.7), (14.4, -5.0), (15.2, -4.45), (16.0, -4.6), (16.9, -5.2),
             (17.2, -6.5), (17.2, -8.0), (16.0, -8.4), (14.8, -8.6), (13.4, -8.7), (13.0, -8.0), (12.7, -7.2), (12.3, -6.5)]
    ring = [P(*p) for p in kongo]
    d.polygon(ring, fill=(205, 166, 82, 70)); d.line(ring + [ring[0]], fill=(205, 166, 82, 255), width=5)
    fs = fnt(SANS, 34, "SemiBold"); fl = fnt(SANS, 30, "Medium"); fsm = fnt(SANS, 26, "Medium")
    def dot(lon, lat, col, r=12):
        x, y = P(lon, lat); d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        return x, y
    x, y = dot(14.25, -6.27, (240, 200, 110)); spaced(d, (x + 24, y - 20), "MBANZA KONGO · THE CAPITAL", fs, (245, 215, 140), 3)
    x, y = dot(12.35, -6.12, (220, 190, 120), 9); spaced(d, (x - 10, y + 22), "SOYO", fl, (230, 205, 150), 3)
    x, y = dot(13.23, -8.84, (180, 175, 165), 9); spaced(d, (x + 20, y - 16), "LUANDA", fl, (200, 195, 185), 3)
    x, y = dot(15.31, -4.32, (150, 150, 150), 10)
    spaced(d, (x + 22, y - 44), "KINSHASA", fl, (200, 200, 200), 3)
    spaced(d, (x + 22, y - 6), "NOT KONGO'S CAPITAL", fsm, (220, 120, 100), 3)
    # v1.1: every label sits inside the safe area of the zoom's last frame (x 8-92%, y 9-84%);
    # the borders note moved to the on-screen label strip so the zoom can't crop it.
    for lab, lon, lat in [("ANGOLA (TODAY)", 16.4, -9.15), ("DR CONGO (TODAY)", 18.1, -6.4),
                          ("REPUBLIC OF THE CONGO (TODAY)", 11.0, -4.2)]:
        spaced(d, P(lon, lat), lab, fsm, (150, 145, 135), 4)
    spaced(d, P(17.35, -7.3), "KINGDOM OF KONGO", fs, (240, 205, 120), 4)
    spaced(d, P(17.35, -7.75), "APPROXIMATE CORE, c. 1500", fsm, (220, 190, 120), 3)
    spaced(d, P(9.7, -8.9), "ATLANTIC OCEAN", fsm, (90, 110, 120), 6)
    im.save(f"{B}/map_locator.png")
    print("map ok")


if __name__ == "__main__":
    os.makedirs(B, exist_ok=True)
    if sys.argv[1] == "map":
        build_map()
    elif sys.argv[1] == "shots":
        tl = json.load(open(f"{B}/timeline.json"))
        for s in build_shots(tl):
            print(f"{s['t']:7.2f}-{s['end']:7.2f} {s['kind']:5s} {s.get('src', s.get('style'))} | {s.get('label') or s.get('title') or s.get('text','')[:50]}")
    elif sys.argv[1] == "render":
        render(float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]))
