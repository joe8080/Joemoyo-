# OGX Isandlwana picture renderer (from Adwa v1.5): timeline.json -> 1920x1080 24 fps H.264 (silent).
# House style per OGX Production OS v2.0 s.2.3: Ken Burns on every picture, text cards on
# #152121, gold kickers, Lora titles, Cinzel main title, credit strips, AI labels, wordmark.
import json, math, os, subprocess, sys
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import geomap

W, H, FPS = 1920, 1080, 24
PW, PH = 2304, 1296
GREEN = (21, 33, 33)
GOLD = (201, 164, 92)
CREAM = (239, 230, 210)
RED = (142, 42, 32)
HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n: os.path.join(HERE, "fonts", n)

def font(name, size, weight=None):
    f = ImageFont.truetype(F(name), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f

CREDITS = {
    "I01": "The Graphic, 15 March 1879, after J. C. Dollman (Melvill and Coghill with the Colours)  |  Public domain  |  Wikimedia Commons",
    "I02": "Cetshwayo kaMpande, photographed by Alexander Bassano, London (published 1885)  |  Public domain  |  Wikimedia Commons",
    "I03": "Sir Bartle Frere, by Sir George Reid, 1881  |  Public domain  |  Wikimedia Commons",
    "I04": "Sketch of the battle of Isandhlwana, Holden, 1879  |  British Library  |  Public domain",
    "I06": "'Last Sleep of the Brave', oleograph after Alphonse de Neuville, 1881  |  Public domain",
    "I07": "Isandlwana Zulu memorial (isiqu)  |  Photo: Betsy kee, CC BY-SA 3.0  |  Wikimedia Commons",
    "I08": "Isandlwana hill and battlefield, 2010  |  Photo: Michael Gundelfinger, CC BY-SA 4.0  |  Wikimedia Commons",
    "I09": "Isandlwana battlefield, 2012  |  Photo: RedNovember82, CC BY-SA 3.0  |  Wikimedia Commons",
    "I10": "Cetshwayo, c. 1875, from a magic-lantern slide  |  Public domain  |  Wikimedia Commons",
}
ARCH_FILES = {
    "I01": "I01_graphic_1879_colours", "I02": "I02_cetshwayo_bassano", "I03": "I03_frere_reid_1881",
    "I04": "I04_holden_sketch_1879", "I06": "I06_last_sleep_brave", "I07": "I07_isiqu_memorial",
    "I08": "I08_hill_panorama_2010", "I09": "I09_hill_cairns_2012", "I10": "I10_cetshwayo_c1875",
}
NAMED_CROPS = {}

def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

@lru_cache(None)
def parchment():
    im = Image.open(os.path.join(HERE, "ai", "PARCH.png")).convert("RGB")
    return cover(im, PW, PH)

@lru_cache(None)
def green_ground():
    tex = parchment().convert("L").filter(ImageFilter.GaussianBlur(3))
    tex = np.asarray(tex, dtype=np.float32) / 255.0
    base = np.ones((PH, PW, 3), np.float32) * np.array(GREEN, np.float32)
    base *= (0.82 + 0.36 * tex[..., None])
    yy, xx = np.mgrid[0:PH, 0:PW]
    d = np.sqrt(((xx - PW / 2) / (PW / 2)) ** 2 + ((yy - PH / 2) / (PH / 2)) ** 2)
    base *= np.clip(1.15 - 0.45 * d, 0.45, 1.0)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))

def arch_image(key, crop):
    im = Image.open(os.path.join(HERE, "archive", ARCH_FILES[key] + ".png")).convert("RGB")
    if isinstance(crop, str):
        crop = NAMED_CROPS[(key, crop)]
    if crop:
        x0, y0, x1, y1 = crop
        im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
    return im

@lru_cache(None)
def plate_arch(key, crop):
    im = arch_image(key, crop)
    bg = cover(im, PW, PH).filter(ImageFilter.GaussianBlur(40))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    bg = Image.blend(bg, green_ground(), 0.55)
    maxw, maxh = int(PW * 0.70), int(PH * 0.80)
    s = min(maxw / im.width, maxh / im.height, 3.2)
    fg = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if s > 1.6:
        fg = fg.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    x, y = (PW - fg.width) // 2, (PH - fg.height) // 2 - 10
    sh = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(sh).rectangle((x + 14, y + 18, x + fg.width + 14, y + fg.height + 18), fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    bg.paste(Image.new("RGB", (PW, PH), (0, 0, 0)), (0, 0), sh)
    d = ImageDraw.Draw(bg)
    d.rectangle((x - 6, y - 6, x + fg.width + 5, y + fg.height + 5), outline=GOLD, width=3)
    bg.paste(fg, (x, y))
    return bg

@lru_cache(None)
def plate_ai(key):
    return cover(Image.open(os.path.join(HERE, "ai", key + ".png")).convert("RGB"), PW, PH)

@lru_cache(None)
def plate_card():
    return green_ground()

# ---------------- maps ----------------
def proj(lat, lon, box):
    la0, la1, lo0, lo1 = box
    return ((lon - lo0) / (lo1 - lo0) * PW, (la1 - lat) / (la1 - la0) * PH)

def map_base(dark=0.55):
    p = parchment()
    p = ImageEnhance.Brightness(p).enhance(dark)
    return Image.blend(p, green_ground(), 0.25)

def label(d, xy, text, size=40, fill=CREAM, anchor="la", italic=False, stroke=True):
    f = font("Lora-Italic.ttf" if italic else "Lora.ttf", size, 600 if not italic else 500)
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=3 if stroke else 0, stroke_fill=(20, 16, 10))

def pin(d, xy, r=11, fill=GOLD):
    x, y = xy
    d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=(20, 16, 10), width=3)

def tri(d, xy, s=16, fill=CREAM):
    x, y = xy
    d.polygon([(x, y - s), (x - s, y + s * 0.7), (x + s, y + s * 0.7)], fill=fill, outline=(20, 16, 10))

def arrow(d, pts, col=GOLD, width=9, head=34, dash=None):
    pts = [tuple(map(float, p)) for p in pts]
    if dash:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L // dash))
            for i in range(0, n, 2):
                a, b = i / n, min(1, (i + 1) / n)
                d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=col, width=width)
    else:
        d.line(pts, fill=col, width=width, joint="curve")
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    ang = math.atan2(y1 - y0, x1 - x0)
    h1 = (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45))
    h2 = (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))
    d.polygon([(x1, y1), h1, h2], fill=col)

BOX_N = (8.2, 16.6, 33.0, 47.9)   # lat0, lat1, lon0, lon1 (approx 16:9)
BOX_S = (4.3, 15.0, 30.5, 49.5)
COAST = [(16.6, 38.9), (16.0, 39.2), (15.6, 39.45), (15.0, 40.0), (14.4, 40.8), (13.5, 41.6), (12.7, 42.7),
         (12.4, 43.3), (11.6, 43.2), (11.5, 43.6), (11.2, 44.5), (11.3, 46.0), (11.6, 47.9)]

def sea(d, box):
    pts = [proj(a, b, box) for a, b in COAST] + [(PW, 0), (proj(16.6, 38.9, box)[0], 0)]
    d.polygon(pts, fill=(28, 46, 52))
    d.line([proj(a, b, box) for a, b in COAST], fill=GOLD, width=4)

def eritrea(d, box):
    pts = [(16.6, 36.4), (15.1, 36.5), (14.6, 37.4), (14.8, 38.4), (14.5, 39.0), (14.6, 39.9), (14.4, 40.8),
           (15.0, 40.0), (15.6, 39.45), (16.0, 39.2), (16.6, 38.9)]
    ov = Image.new("RGBA", (PW, PH)); od = ImageDraw.Draw(ov)
    od.polygon([proj(a, b, box) for a, b in pts], fill=RED + (95,), outline=RED + (255,))
    return ov

@lru_cache(None)
def plate_map(name):
    img = map_base().convert("RGBA")
    d = ImageDraw.Draw(img)
    if name in ("region", "provinces"):
        box = BOX_N
        sea(d, box)
        img.alpha_composite(eritrea(d, box)); d = ImageDraw.Draw(img)
        label(d, proj(15.9, 38.0, box), "ERITREA", 44, fill=CREAM, anchor="mm")
        label(d, proj(15.4, 42.3, box), "Red Sea", 46, fill=(170, 190, 190), anchor="mm", italic=True)
        cx, cy = proj(12.0, 37.3, box)
        d.ellipse((cx - 40, cy - 55, cx + 40, cy + 55), fill=(28, 46, 52), outline=GOLD, width=3)
        for nm, la, lo, anc in (("Massawa", 15.61, 39.45, "ld"), ("Adwa", 14.16, 38.9, "rm"), ("Mekelle", 13.5, 39.47, "lm"),
                                ("Addis Ababa", 9.03, 38.74, "lm")):
            x, y = proj(la, lo, box); pin(d, (x, y))
            label(d, (x + (24 if anc[0] == "l" else -24), y), nm, 44, anchor=anc)
        if name == "region":
            label(d, proj(13.9, 39.9, box), "TIGRAY", 40, fill=GOLD, anchor="lm")
            arrow(d, [proj(15.2, 39.1, box), proj(14.5, 39.3, box), proj(13.8, 39.5, box)], col=RED, width=10, dash=28)
        else:
            for nm, la, lo in (("SHEWA", 9.7, 39.6), ("GOJJAM", 10.6, 37.4), ("WOLLO", 11.4, 39.9), ("TIGRAY", 13.9, 39.95)):
                label(d, proj(la, lo, box), nm, 40, fill=GOLD, anchor="mm")
            for a in ([(9.9, 39.2), (11.5, 39.4), (12.9, 39.4)], [(10.9, 37.6), (12.2, 38.4), (13.0, 39.1)],
                      [(11.7, 39.7), (12.8, 39.55)]):
                arrow(d, [proj(la, lo, box) for la, lo in a], col=CREAM, width=9)
    elif name == "south":
        box = BOX_S
        sea(d, box)
        x, y = proj(9.03, 38.74, box)
        d.ellipse((x - 150, y - 110, x + 150, y + 110), outline=GOLD, width=4)
        label(d, (x, y - 140), "SHEWA", 44, fill=GOLD, anchor="mm")
        pin(d, (x, y)); label(d, (x + 22, y + 4), "Addis Ababa", 40, anchor="lm")
        for nm, la, lo, anc in (("Wolaita", 6.85, 37.75, "rm"), ("Kaffa", 7.3, 36.2, "rm")):
            tx, ty = proj(la, lo, box)
            arrow(d, [(x - 20, y + 30), ((x + tx) / 2 - 30, (y + ty) / 2), (tx + 12, ty - 12)], col=RED, width=10)
            pin(d, (tx, ty), fill=RED); label(d, (tx - 26, ty), nm, 44, anchor=anc)
        x2, y2 = proj(14.16, 38.9, box); pin(d, (x2, y2)); label(d, (x2 + 22, y2), "Adwa", 40, anchor="lm")
        label(d, (PW * 0.5, PH * 0.93), "Conquests of the 1880s-1890s  ·  selected", 34, fill=CREAM, anchor="mm", italic=True)
    else:
        # battle area schematic, landmarks traced from a terrain map of Adwa (approximate)
        def P(x, y):  # normalised (0-1) battlefield coords -> plate
            return (180 + x * (PW - 360), 140 + y * (PH - 300))
        L = {"Adwa": (0.045, 0.81), "Mariam Shewito": (0.205, 0.42), "Mt Beleh": (0.50, 0.33), "Mt Raio": (0.57, 0.42),
             "Rebbi Arayeni": (0.69, 0.34), "Kidane Mehret": (0.68, 0.52), "Enda Kidane Mehret": (0.33, 0.63),
             "Mt Semayata": (0.46, 0.67), "Enda Gerima": (0.23, 0.83), "Sauria": (0.99, 0.30)}
        for nm in ("Mt Semayata", "Enda Gerima"):
            tri(d, P(*L[nm])); label(d, (P(*L[nm])[0] + 24, P(*L[nm])[1]), nm, 34, anchor="lm", italic=True)
        x, y = P(*L["Adwa"]); pin(d, (x, y), 14); label(d, (x + 24, y + 30), "Adwa", 44, anchor="lm")
        # Ethiopian camp (approximate area west of the ridge)
        ov = Image.new("RGBA", (PW, PH)); od = ImageDraw.Draw(ov)
        cx, cy = P(0.14, 0.66)
        od.ellipse((cx - 230, cy - 170, cx + 230, cy + 170), fill=RED + (80,), outline=RED + (230,), width=4)
        img.alpha_composite(ov); d = ImageDraw.Draw(img)
        label(d, (cx, cy - 10), "ETHIOPIAN", 36, fill=CREAM, anchor="mm")
        label(d, (cx, cy + 32), "CAMP", 36, fill=CREAM, anchor="mm")
        sx, sy = P(*L["Sauria"])
        label(d, (sx - 10, sy - 50), "from Sauria", 34, anchor="rm", italic=True)
        cols = {"Albertone": GOLD, "Arimondi": CREAM, "Dabormida": (214, 196, 150)}
        # schematic objectives on the ridge line (left = south, right = north, facing west)
        OBJ = {"Dabormida": (0.64, 0.25), "Arimondi": (0.70, 0.36), "Albertone": (0.68, 0.53)}
        tracks = {"Albertone": [L["Sauria"], (0.86, 0.46), OBJ["Albertone"]],
                  "Arimondi": [L["Sauria"], (0.85, 0.35), OBJ["Arimondi"]],
                  "Dabormida": [L["Sauria"], (0.84, 0.25), OBJ["Dabormida"]]}
        lab_off = {"Dabormida": (-10, 50), "Arimondi": (-150, -6), "Albertone": (-40, 56)}
        if name in ("plan", "standoff"):
            if name == "standoff":
                tx, ty = P(0.92, 0.33)
                d.rectangle((tx - 70, ty - 40, tx + 70, ty + 40), fill=GOLD, outline=(20, 16, 10), width=3)
                label(d, (tx, ty + 80), "ITALIAN CAMP", 34, anchor="mm")
            else:
                for nm, tr in tracks.items():
                    arrow(d, [P(*p) for p in tr], col=cols[nm], width=9, dash=26)
                    ex, ey = P(*tr[-1]); ox, oy = lab_off[nm]
                    label(d, (ex + ox, ey + oy), nm, 38, fill=cols[nm], anchor="mm")
                label(d, (P(0.9, 0.62)[0], P(0.9, 0.62)[1]), "Reserve follows", 32, anchor="mm", italic=True)
        else:
            alb_end = L["Enda Kidane Mehret"]
            arrow(d, [P(*p) for p in tracks["Arimondi"]], col=cols["Arimondi"], width=9)
            ax, ay = P(*OBJ["Arimondi"]); label(d, (ax - 150, ay - 6), "Arimondi", 38, fill=CREAM, anchor="mm")
            arrow(d, [P(*p) for p in tracks["Albertone"] + [(0.50, 0.60), alb_end]], col=GOLD, width=10)
            ex, ey = P(*alb_end); label(d, (ex - 10, ey + 56), "Albertone", 38, fill=GOLD, anchor="mm")
            kx, ky = P(*OBJ["Albertone"])
            d.ellipse((kx - 16, ky - 16, kx + 16, ky + 16), outline=GOLD, width=4)
            label(d, (kx + 26, ky + 34), "ordered position", 30, anchor="lm", italic=True)
            if name in ("dabormida", "pieces"):
                arrow(d, [P(*p) for p in tracks["Dabormida"] + [(0.45, 0.27), L["Mariam Shewito"]]], col=cols["Dabormida"], width=9)
                mx, my = P(*L["Mariam Shewito"]); label(d, (mx, my - 52), "Dabormida", 38, fill=cols["Dabormida"], anchor="mm")
            else:
                arrow(d, [P(*p) for p in tracks["Dabormida"]], col=cols["Dabormida"], width=9)
                dx, dy = P(*OBJ["Dabormida"]); label(d, (dx - 10, dy + 50), "Dabormida", 38, fill=cols["Dabormida"], anchor="mm")
            if name in ("gap", "dabormida", "pieces"):
                gx, gy = P(0.52, 0.52)
                ov = Image.new("RGBA", (PW, PH)); od = ImageDraw.Draw(ov)
                od.ellipse((gx - 150, gy - 95, gx + 150, gy + 95), fill=RED + (70,), outline=RED + (255,), width=5)
                img.alpha_composite(ov); d = ImageDraw.Draw(img)
                label(d, (gx, gy), "GAP", 44, fill=CREAM, anchor="mm")
            if name == "pieces":
                for (px, py) in (L["Enda Kidane Mehret"], OBJ["Arimondi"], L["Mariam Shewito"]):
                    cx, cy = P(px, py)
                    d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), outline=RED, width=6)
    return img.convert("RGB")

# ---------------- overlays (static per shot) ----------------
def text_spaced(d, xy, text, f, fill, spacing=4, anchor="l"):
    w = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
    x, y = xy
    if anchor == "c":
        x -= w / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing
    return w

def overlay_static(shot):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    k = shot["vis"][0]
    if hf_clip(shot["vis"]):  # the sting carries its own type
        return np.asarray(ov, dtype=np.float32)
    if k == "card":
        _, kick, title = shot["vis"]
        fk = font("Cinzel.ttf", 36, 600)
        text_spaced(d, (W / 2, 400), kick.upper(), fk, GOLD, 6, "c")
        d.line((W / 2 - 70, 470, W / 2 + 70, 470), fill=GOLD, width=2)
        size = 104 if len(title) <= 18 else 84
        d.text((W / 2, 560), title, font=font("Lora.ttf", size, 500), fill=CREAM, anchor="mm")
    elif k == "title":
        text_spaced(d, (W / 2, 330), "ORIGINEX HUMAN ARCHIVES", font("Cinzel.ttf", 30, 600), GOLD, 8, "c")
        d.text((W / 2, 520), "ISANDLWANA", font=font("Cinzel.ttf", 168, 700), fill=GOLD, anchor="mm",
               stroke_width=2, stroke_fill=(30, 22, 10))
        d.line((W / 2 - 160, 660, W / 2 + 160, 660), fill=GOLD, width=2)
        d.text((W / 2, 720), "1879", font=font("Cinzel.ttf", 72, 500), fill=CREAM, anchor="mm")
    elif k == "endcard":
        if shot["text"].startswith("This has been"):
            d.text((W / 2, 500), "ORIGINEX", font=font("Cinzel.ttf", 150, 700), fill=GOLD, anchor="mm")
            text_spaced(d, (W / 2, 610), "HUMAN ARCHIVES", font("Cinzel.ttf", 46, 600), CREAM, 14, "c")
        else:  # v1.3: no next-episode tease; the glass subscribe badge is drawn over this card in shot_frame
            text_spaced(d, (W / 2, 330), "ORIGINEX HUMAN ARCHIVES", font("Cinzel.ttf", 30, 600), GOLD, 8, "c")
            d.line((W / 2 - 90, 380, W / 2 + 90, 380), fill=GOLD, width=2)
            d.text((W / 2, 455), "If this record is worth keeping,", font=font("Lora-Italic.ttf", 64, 500), fill=CREAM, anchor="mm")
    else:
        if k == "ai":
            animated = os.path.exists(os.path.join(HERE, "motion", shot["vis"][1] + ".mp4"))
            tag = ("AI RECONSTRUCTION, ANIMATED  ·  ILLUSTRATIVE, NOT A RECORD" if animated
                   else "AI RECONSTRUCTION  ·  ILLUSTRATIVE, NOT A RECORD")
        elif k == "map":
            tag = geomap.tag_for(shot["vis"][1])
        else:
            tag = None
        if tag:
            f = font("Lora.ttf", 21, 600)
            tw = d.textlength(tag, font=f)
            d.rounded_rectangle((40, 36, 40 + tw + 32, 36 + 40), 8, fill=(10, 14, 14, 150))
            d.text((56, 56), tag, font=f, fill=CREAM + (215,), anchor="lm")
        if shot["ost"]:
            fo = font("Cinzel.ttf", 42, 600)
            y = 905
            bw = text_spaced(ImageDraw.Draw(Image.new("RGBA", (10, 10))), (0, 0), shot["ost"], fo, GOLD, 5)
            d.rounded_rectangle((90, y - 22, 90 + bw + 70, y + 66), 6, fill=(8, 12, 12, 160))
            d.line((110, y - 6, 110, y + 50), fill=GOLD, width=3)
            text_spaced(d, (132, y - 2), shot["ost"], fo, CREAM, 5)
    if k not in ("title", "endcard"):
        text_spaced(d, (W - 60, 1018), "", font("Cinzel.ttf", 10), GOLD)
        f = font("Cinzel.ttf", 26, 700)
        tw = d.textlength("ORIGINEX", font=f) + 3 * 7
        text_spaced(d, (W - 60 - tw, 1012), "ORIGINEX", f, GOLD + (190,), 3)
    return np.asarray(ov, dtype=np.float32)

# ---------------- subscribe badge (v1.3) ----------------
# Black glass panel with a gold rim; a soft lime glow pulses on the rim three times. Moderate alpha by design.
LIME = (170, 255, 70)
BW, BH, BR = 600, 150, 30

@lru_cache(4)
def badge_layers():
    base = Image.new("RGBA", (BW + 80, BH + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    o = 40
    d.rounded_rectangle((o, o, o + BW, o + BH), BR, outline=GOLD + (255,), width=3)
    d.line((o + BR, o + 7, o + BW - BR, o + 7), fill=(255, 255, 255, 34), width=2)  # glass sheen
    # gold play tile
    d.rounded_rectangle((o + 34, o + 41, o + 124, o + 109), 16, fill=GOLD + (235,))
    d.polygon([(o + 68, o + 56), (o + 68, o + 94), (o + 98, o + 75)], fill=(16, 22, 22, 255))
    text_spaced(d, (o + 150, o + 40), "SUBSCRIBE", font("Cinzel.ttf", 56, 700), CREAM, 6)
    text_spaced(d, (o + 153, o + 108), "ORIGINEX HUMAN ARCHIVES", font("Lora.ttf", 19, 600), GOLD, 3)
    rim = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle((o - 2, o - 2, o + BW + 2, o + BH + 2), BR + 2, outline=LIME + (255,), width=5)
    glow = rim.filter(ImageFilter.GaussianBlur(9))
    rim = Image.alpha_composite(glow, rim)
    mask = Image.new("L", (BW, BH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, BW - 1, BH - 1), BR, fill=255)
    return (np.asarray(base, np.float32), np.asarray(rim, np.float32), np.asarray(mask, np.float32)[..., None] / 255.0)

def draw_badge(img, t, dur, cx, cy, slide=True, peaks=(0.75, 1.6, 2.45)):
    """Composite the badge onto img at local time t (0..dur). Returns img."""
    if t < 0 or t > dur:
        return img
    base, rim, mask = badge_layers()
    if slide:
        a_in, a_out = min(1.0, t / 0.4), min(1.0, (dur - t) / 0.4)
        k = ease(min(a_in, a_out))
        x0 = int(cx - BW / 2 + (1 - k) * 260)
        alpha = k
    else:
        x0, alpha = int(cx - BW / 2), min(1.0, t / 0.5)
    y0 = int(cy - BH / 2)
    x0 = max(0, min(W - BW, x0))
    out = img.copy()
    # glass: blurred, darkened backdrop inside the rounded panel
    reg = out[y0:y0 + BH, x0:x0 + BW]
    glass = cv2.GaussianBlur(reg, (0, 0), 16) * 0.30 + np.array([4, 6, 6], np.float32)
    reg[:] = reg * (1 - mask * alpha) + glass * mask * alpha
    # gold rim, text, lime pulses (gaussian pulses, peak alpha 0.6)
    lx, ly = x0 - 40, y0 - 40
    def comp(layer, a):
        h, w = layer.shape[:2]
        X0, Y0 = max(0, lx), max(0, ly)
        X1, Y1 = min(W, lx + w), min(H, ly + h)
        L = layer[Y0 - ly:Y1 - ly, X0 - lx:X1 - lx]
        A = L[..., 3:4] / 255.0 * a
        out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - A) + L[..., :3] * A
    comp(base, alpha)
    pulse = sum(math.exp(-((t - p) / 0.16) ** 2) for p in peaks)
    if pulse > 0.01:
        comp(rim, alpha * min(1.0, pulse) * 0.6)
    return out

SUB_AT, SUB_DUR = 120.0, 3.8  # mid-film subscribe prompt (~2:00), three lime flashes

def overlay_credit(key):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = font("Lora.ttf", 22, 500)
    t = CREDITS.get(key) or geomap.CREDITS[key]
    tw = d.textlength(t, font=f)
    d.rounded_rectangle((40, H - 76, 40 + tw + 36, H - 36), 8, fill=(10, 14, 14, 170))
    d.text((58, H - 56), t, font=f, fill=CREAM + (225,), anchor="lm")
    return np.asarray(ov, dtype=np.float32)

def overlay_act(num, title):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    s = f"{num}  ·  {title}"
    f = font("Cinzel.ttf", 50, 700)
    tw = text_spaced(ImageDraw.Draw(Image.new("RGBA", (10, 10))), (0, 0), s, f, GOLD, 6)
    d.rounded_rectangle((W / 2 - tw / 2 - 60, 108, W / 2 + tw / 2 + 60, 196), 8, fill=(8, 12, 12, 175))
    text_spaced(d, (W / 2, 124), s, f, GOLD, 6, "c")
    return np.asarray(ov, dtype=np.float32)

# ---------------- motion ----------------
def plate_for(vis):
    k = vis[0]
    if k == "ai":
        return plate_ai(vis[1])
    if k == "arch":
        return plate_arch(vis[1], vis[2] if not isinstance(vis[2], list) else tuple(vis[2]))
    if k == "map":
        return plate_map(vis[1])
    if k == "title":
        p = ImageEnhance.Brightness(plate_ai("Z01")).enhance(0.42)
        return Image.blend(p, green_ground(), 0.35)
    return plate_card()

@lru_cache(64)
def plate_np(vis_key):
    vis = json.loads(vis_key)
    return np.asarray(plate_for(vis), dtype=np.float32)

MOVES = ["push", "pan_r", "pull", "pan_l", "tilt_d", "push_l"]

# ---------------- motion clips (v1.3) ----------------
# Each AI still has an image-to-video clip in motion/<key>.mp4. A still used more than once plays a
# different stretch of its clip each time, in timeline order; if the clip runs short it is slowed.
def _motion_plan():
    shots = json.load(open(os.path.join(HERE, "timeline.json")))
    plan, used = {}, {}
    for s in shots:
        parts = [(0, s["vis"], s["switch"] if "vis2" in s else s["dur"])]
        if "vis2" in s:
            parts.append((2, s["vis2"], s["dur"] - s["switch"]))
        for off, vis, dur in parts:
            if vis[0] != "ai" or not os.path.exists(os.path.join(HERE, "motion", vis[1] + ".mp4")):
                continue
            cap = cv2.VideoCapture(os.path.join(HERE, "motion", vis[1] + ".mp4"))
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
            length = n / FPS
            start = used.get(vis[1], 0.0)
            if start + dur > length:
                start = max(0.0, length - dur)
            rate = min(1.0, (length - start - 0.05) / max(dur, 0.1))
            plan[(s["n"] + off, vis[1])] = (start, rate, n)
            used[vis[1]] = start + dur * rate
    return plan

MOTION = _motion_plan()

class ClipReader:
    """Sequential-friendly reader: one capture per (shot, clip) use, seeking only when not sequential."""
    def __init__(self):
        self.caps = {}
    def get(self, use, key, fi, nframes):
        fi = int(min(max(fi, 0), nframes - 1))
        c = self.caps.get(use)
        if c is None:
            if len(self.caps) > 6:
                for k in list(self.caps)[:3]:
                    self.caps.pop(k)[0].release()
            c = [cv2.VideoCapture(os.path.join(HERE, "motion", key + ".mp4")), -1, None]
            self.caps[use] = c
        cap, pos, last = c
        if fi == pos and last is not None:
            return last
        if fi != pos + 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, fr = cap.read()
        if not ok:
            return last
        if fr.shape[1] != W or fr.shape[0] != H:
            fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
        fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB).astype(np.float32)
        c[1], c[2] = fi, fr
        return fr

READER = ClipReader()

def ease(u):
    return u * u * (3 - 2 * u)

# HyperFrames stings (title, the question card): rendered HTML motion clips that replace the static cards
def hf_clip(vis):
    if vis[0] == "title":
        key = "HF_title"
    elif vis[0] == "card" and vis[1] == "THE QUESTION":
        key = "HF_question"
    else:
        return None
    return key if os.path.exists(os.path.join(HERE, "motion", key + ".mp4")) else None

def frame_of(shot, t):
    """Render one shot at local time t (seconds since shot start; may exceed bounds during dissolves)."""
    vis = shot["vis"]
    hk = hf_clip(vis)
    if hk:
        cap = cv2.VideoCapture(os.path.join(HERE, "motion", hk + ".mp4"))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
        return READER.get(("hf", shot["n"]), hk, round(min(max(t, 0.0), shot["dur"]) * FPS), n)
    if vis[0] == "map":
        return geomap.render(vis[1], t, shot["dur"])
    mk = (shot["n"], vis[1]) if vis[0] == "ai" else None
    if mk in MOTION:
        start, rate, n = MOTION[mk]
        tt = min(max(t, 0.0), shot["dur"])
        return READER.get(mk, vis[1], round((start + tt * rate) * FPS), n)
    pl = plate_np(json.dumps(vis))
    u = ease(min(1.0, max(0.0, t / max(shot["dur"], 0.1))))
    k = vis[0]
    if k in ("card", "endcard"):
        mv, amt = "push", 0.03
    elif k == "title":
        mv, amt = "push", 0.06
    else:
        mv, amt = MOVES[shot["n"] % len(MOVES)], 0.12
    # window size in plate pixels (scale of 1920x1080 window); base window = full plate
    if mv == "push":
        s = 1.0 - amt * u; cx, cy = 0.5, 0.5
    elif mv == "pull":
        s = 1.0 - amt * (1 - u); cx, cy = 0.5, 0.5
    elif mv == "push_l":
        s = 1.0 - amt * u; cx, cy = 0.5 - 0.04 * u, 0.5
    elif mv == "pan_r":
        s = 1.0 - amt; cx, cy = 0.5 - 0.05 + 0.10 * u, 0.5
    elif mv == "pan_l":
        s = 1.0 - amt; cx, cy = 0.5 + 0.05 - 0.10 * u, 0.5
    else:  # tilt_d
        s = 1.0 - amt; cx, cy = 0.5, 0.5 - 0.04 + 0.08 * u
    ww, wh = PW * s, PH * s
    x0 = min(max(cx * PW - ww / 2, 0), PW - ww)
    y0 = min(max(cy * PH - wh / 2, 0), PH - wh)
    sc = W / ww
    M = np.array([[sc, 0, -x0 * sc], [0, sc, -y0 * sc]], np.float32)
    return cv2.warpAffine(pl, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def composite(img, ov, alpha_mul=1.0):
    a = ov[..., 3:4] / 255.0 * alpha_mul
    return img * (1 - a) + ov[..., :3] * a

class Renderer:
    def __init__(self, shots):
        self.shots = shots
        self.ov_cache = {}
        self.new_arch = set()
        seen = set()
        self.credit_of = {}
        for s in shots:  # credit shows where an archive picture or map source first appears
            ck = s["vis"][1] if s["vis"][0] == "arch" else (geomap.credit_key(s["vis"][1]) if s["vis"][0] == "map" else None)
            if ck and ck not in seen:
                seen.add(ck); self.new_arch.add(s["n"]); self.credit_of[s["n"]] = ck

    def ov(self, key, fn):
        if key not in self.ov_cache:
            self.ov_cache[key] = fn()
        return self.ov_cache[key]

    def part_frame(self, s, t):
        """A shot with a second picture is two parts: the first carries the caption, each its own label."""
        if "vis2" not in s:
            img = frame_of(s, t)
            return composite(img, self.ov(("s", s["n"]), lambda: overlay_static(s)))
        sw, xf = s["switch"], 0.5
        a = min(1.0, max(0.0, (t - (sw - xf / 2)) / xf))
        p1 = dict(s, dur=sw)
        p2 = dict(s, vis=s["vis2"], ost=None, dur=max(0.5, s["dur"] - sw), n=s["n"] + 2)
        out = None
        if a < 1:
            out = composite(frame_of(p1, t), self.ov(("s", s["n"]), lambda: overlay_static(p1)))
        if a > 0:
            b = composite(frame_of(p2, t - sw), self.ov(("s2", s["n"]), lambda: overlay_static(p2)))
            out = b if out is None else out * (1 - a) + b * a
        return out

    def shot_frame(self, i, t):
        s = self.shots[i]
        img = self.part_frame(s, t)
        if s["n"] in self.new_arch:
            end = min(5.3, s["switch"] - 0.25) if "vis2" in s else 5.3  # never over a second picture
            a = min(1.0, max(0.0, (t - 0.3) / 0.4)) * min(1.0, max(0.0, (end - t) / 0.5))
            if a > 0:
                ck = self.credit_of[s["n"]]
                img = composite(img, self.ov(("c", ck), lambda: overlay_credit(ck)), a)
        if s["vis"][0] == "endcard" and not s["text"].startswith("This has been"):
            img = draw_badge(img, t, s["dur"] + 1.0, W / 2, 610, slide=False, peaks=(1.0, 1.9, 2.8))
        if s["act_first"] and s["act_title"] and s["act"][0].isdigit():
            a = min(1.0, max(0.0, (t - 0.2) / 0.5)) * min(1.0, max(0.0, (3.8 - t) / 0.6))
            if a > 0:
                img = composite(img, self.ov(("a", s["act"]), lambda: overlay_act(s["act"], s["act_title"])), a)
        return img

    def frame(self, fi):
        T = fi / FPS
        # find shot containing T
        i = 0
        while i + 1 < len(self.shots) and self.shots[i + 1]["start"] <= T:
            i += 1
        s = self.shots[i]
        t = T - s["start"]
        img = self.shot_frame(i, t)
        # dissolve into next shot near the boundary
        if i + 1 < len(self.shots):
            nxt = self.shots[i + 1]
            xd = 1.5 if s["vis"][0] == "title" else (0.8 if nxt["act_first"] else 0.4)
            rem = nxt["start"] - T
            if rem < xd / 2:
                a = 0.5 - rem / xd
                img = img * (1 - a) + self.shot_frame(i + 1, T - nxt["start"]) * a
        if i > 0 and t < 0.6:
            prv = self.shots[i - 1]
            xd = 1.5 if prv["vis"][0] == "title" else (0.8 if s["act_first"] else 0.4)
            if t < xd / 2:
                a = 0.5 + t / xd
                img = img * a + self.shot_frame(i - 1, T - prv["start"]) * (1 - a)
        img = draw_badge(img, T - SUB_AT, SUB_DUR, W - 60 - BW / 2, 880)
        # fade from black at the start, to black over the final second
        total = self.shots[-1]["start"] + self.shots[-1]["dur"]
        img = img * min(1.0, T / 0.6) * min(1.0, max(0.0, (total - T) / 1.0))
        return np.clip(img, 0, 255).astype(np.uint8)

def render_range(f0, f1, out):
    shots = json.load(open(os.path.join(HERE, "timeline.json")))
    r = Renderer(shots)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", "-g", "48", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(r.frame(fi).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":  # render preview stills at given seconds
        shots = json.load(open(os.path.join(HERE, "timeline.json")))
        r = Renderer(shots)
        for sec in sys.argv[2:]:
            Image.fromarray(r.frame(int(float(sec) * FPS))).save(os.path.join(HERE, "preview", f"still_{float(sec):07.2f}.jpg"), quality=88)
    else:
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
