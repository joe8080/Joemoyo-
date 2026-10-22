# Real-map shots for OGX Isandlwana 1879 (engine from Adwa v1.5): shaded relief (AWS Terrain Tiles) and Sentinel-2
# Web Mercator camera that can fly from a continent down to a battlefield. Vectors (Natural Earth
# borders) and labels are drawn per frame so lines and type stay crisp at every zoom.
import json, math, os
from functools import lru_cache
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, "geo")
GOLD = (201, 164, 92)
CREAM = (239, 230, 210)
BRIT = (214, 64, 46)      # British moves
ZULU = (250, 204, 64)     # Zulu moves
INK = (18, 14, 10)

# ---------------- projection (Web Mercator, 256 px tiles) ----------------
def X(lon, z):
    return (lon + 180.0) / 360.0 * 256.0 * 2 ** z

def Y(lat, z):
    r = math.radians(max(-85.0, min(85.0, lat)))
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 256.0 * 2 ** z

def to_screen(lon, lat, cam):
    lonc, latc, zc = cam
    return (X(lon, zc) - X(lonc, zc) + W / 2, Y(lat, zc) - Y(latc, zc) + H / 2)

# ---------------- raster levels ----------------
class Level:
    def __init__(self, name):
        self.name = name
        self.z, self.ox, self.oy, self.w, self.h = map(int, open(os.path.join(GEO, f"elev_{name}.txt")).read().split())
        img = np.load(os.path.join(GEO, f"terr_{name}.npy")).astype(np.float32)
        s2p = os.path.join(GEO, f"s2_{name}.npy")
        if os.path.exists(s2p):
            s2 = np.load(s2p).astype(np.float32)
            m = np.load(os.path.join(GEO, f"s2mask_{name}.npy")).astype(np.float32)
            m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]
            shade = np.load(os.path.join(GEO, f"shade_{name}.npy")).astype(np.float32)[..., None] / 255
            # Sentinel TCI is dark and flat: lift it, warm it slightly, add a little relief
            s2 = 255 * (np.clip(s2 / 255 * 1.35, 0, 1) ** 0.82)
            g = s2.mean(2, keepdims=True)
            s2 = g + (s2 - g) * 1.15
            s2 = s2 * (0.82 + 0.3 * shade)
            img = img * (1 - m) + s2 * m
        img = np.clip(img, 0, 255).astype(np.uint8)
        self.mips = [img]
        while min(self.mips[-1].shape[:2]) > 600 and len(self.mips) < 6:
            self.mips.append(cv2.pyrDown(self.mips[-1]))

    def view(self, cam):
        """Visible rectangle of the camera in this level's pixel space."""
        lonc, latc, zc = cam
        f = 2 ** (self.z - zc)
        cx, cy = X(lonc, self.z) - self.ox, Y(latc, self.z) - self.oy
        return cx - W / 2 * f, cy - H / 2 * f, cx + W / 2 * f, cy + H / 2 * f

    def cover(self, cam):
        x0, y0, x1, y1 = self.view(cam)
        m = min(x0, y0, self.w - x1, self.h - y1)
        return float(np.clip(m / (0.06 * (x1 - x0)), 0, 1))

    def sample(self, cam):
        lonc, latc, zc = cam
        k = int(np.clip(math.floor(self.z - zc), 0, len(self.mips) - 1))
        src = self.mips[k]
        zm = self.z - k
        s = 2 ** (zm - zc)
        cx = (X(lonc, zm) - self.ox / 2 ** k)
        cy = (Y(latc, zm) - self.oy / 2 ** k)
        M = np.array([[s, 0, cx - W / 2 * s], [0, s, cy - H / 2 * s]], np.float32)
        return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REPLICATE)

@lru_cache(None)
def levels():
    return [Level(n) for n in ("L0", "L1", "L2", "L3")]

def base_image(cam):
    L = levels()
    img = None
    for lv in L:  # coarse to fine
        c = 1.0 if lv.name == "L0" else lv.cover(cam)
        # a finer level is only worth sampling once the camera is near its native zoom
        c *= float(np.clip((cam[2] - (lv.z - 3.2)) / 0.8, 0, 1)) if lv.name != "L0" else 1.0
        if c <= 0:
            continue
        smp = lv.sample(cam).astype(np.float32)
        img = smp if img is None or c >= 1 else img * (1 - c) + smp * c
    return img

# ---------------- vectors ----------------
@lru_cache(None)
def border_lines():
    g = json.load(open(os.path.join(GEO, "ne_50m_admin_0_boundary_lines_land.geojson")))
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        lines = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for ln in lines:
            a = np.array([[X(lo, 0), Y(la, 0)] for lo, la in ln], np.float64)
            out.append((a, a.min(0), a.max(0)))
    return out

@lru_cache(None)
def country(name):
    g = json.load(open(os.path.join(GEO, "ne_10m_admin_0_countries.geojson")))
    for f in g["features"]:
        if f["properties"]["ADMIN"] == name:
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            return [np.array([[X(lo, 0), Y(la, 0)] for lo, la in poly[0]], np.float64) for poly in polys]
    raise KeyError(name)

def project0(a, cam):
    lonc, latc, zc = cam
    s = 2 ** zc
    return (a - np.array([X(lonc, 0), Y(latc, 0)])) * s + np.array([W / 2, H / 2])

def draw_borders(img, cam, alpha=0.55):
    lonc, latc, zc = cam
    s = 2 ** zc
    c0 = np.array([X(lonc, 0), Y(latc, 0)])
    half = np.array([W / 2, H / 2]) / s
    lay = np.zeros((H, W), np.uint8)
    for a, mn, mx in border_lines():
        if (mx < c0 - half * 1.2).any() or (mn > c0 + half * 1.2).any():
            continue
        p = np.round(project0(a, cam) * 4).astype(np.int32)
        cv2.polylines(lay, [p], False, 255, 2, cv2.LINE_AA, shift=2)
    m = (lay.astype(np.float32) / 255 * alpha)[..., None]
    return img * (1 - m) + np.array(CREAM, np.float32) * m

def fill_country(img, cam, name, col, fill=0.22, line=0.9, width=3):
    lay = np.zeros((H, W), np.uint8)
    edge = np.zeros((H, W), np.uint8)
    for a in country(name):
        p = np.round(project0(a, cam) * 4).astype(np.int32)
        cv2.fillPoly(lay, [p], 255, cv2.LINE_AA, shift=2)
        cv2.polylines(edge, [p], True, 255, width, cv2.LINE_AA, shift=2)
    m = (lay.astype(np.float32) / 255 * fill)[..., None]
    e = (edge.astype(np.float32) / 255 * line)[..., None]
    c = np.array(col, np.float32)
    img = img * (1 - m) + c * m
    return img * (1 - e) + c * e

# ---------------- type ----------------
@lru_cache(None)
def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
    if weight:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f

def spaced(d, xy, text, f, fill, spacing, anchor="m", stroke=0):
    w = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
    x, y = xy
    if anchor == "m":
        x -= w / 2
    elif anchor == "r":
        x -= w
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="lm", stroke_width=stroke, stroke_fill=INK + (fill[3] if len(fill) > 3 else 255,))
        x += d.textlength(ch, font=f) + spacing

def ramp(v, a, b):
    return float(np.clip((v - a) / max(b - a, 1e-6), 0, 1))

def window(v, lo, hi, f=0.35):
    """1 inside [lo, hi] with soft edges of width f (zoom levels)."""
    return ramp(v, lo - f, lo) * (1 - ramp(v, hi, hi + f))

# ---------------- arrows ----------------
def path_px(pts, cam):
    return np.array([to_screen(lo, la, cam) for lo, la in pts], np.float64)

def partial(p, frac):
    if frac >= 1:
        return p
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    L = seg.sum() * max(frac, 0)
    out, acc = [p[0]], 0.0
    for i, s in enumerate(seg):
        if acc + s >= L:
            t = (L - acc) / max(s, 1e-9)
            out.append(p[i] + (p[i + 1] - p[i]) * t)
            return np.array(out)
        out.append(p[i + 1]); acc += s
    return np.array(out)

def smooth_path(p, n=24):
    if len(p) < 3:
        return p
    # Catmull-Rom through the control points
    P = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)

def draw_arrow(d, pts, col, frac=1.0, width=12, dash=None, alpha=255, head=True):
    if frac <= 0.001:
        return
    p = partial(smooth_path(pts), frac)
    if len(p) < 2:
        return
    seq = [tuple(map(float, q)) for q in p]
    if dash:
        segs, acc, on = [], 0.0, True
        cur = [seq[0]]
        for a, b in zip(seq, seq[1:]):
            L = math.dist(a, b)
            cur.append(b); acc += L
            if acc > dash:
                if on:
                    segs.append(cur)
                cur, acc, on = [b], 0.0, not on
        if on and len(cur) > 1:
            segs.append(cur)
    else:
        segs = [seq]
    for s in segs:
        d.line(s, fill=INK + (int(alpha * 0.8),), width=width + 6, joint="curve")
    for s in segs:
        d.line(s, fill=col + (alpha,), width=width, joint="curve")
    if head:
        (x0, y0), (x1, y1) = p[-2], p[-1]
        if math.dist((x0, y0), (x1, y1)) < 1e-3 and len(p) > 2:
            x0, y0 = p[-3]
        ang = math.atan2(y1 - y0, x1 - x0)
        hl = width * 3.0
        a1 = (x1 + math.cos(ang) * hl * 0.35, y1 + math.sin(ang) * hl * 0.35)
        l = (x1 - math.cos(ang - 0.5) * hl, y1 - math.sin(ang - 0.5) * hl)
        r = (x1 - math.cos(ang + 0.5) * hl, y1 - math.sin(ang + 0.5) * hl)
        d.polygon([a1, l, r], fill=col + (alpha,), outline=INK + (alpha,))


@lru_cache(None)
def river(name):
    g = json.load(open(os.path.join(GEO, "ne_10m_rivers_lake_centerlines.geojson")))
    out = []
    for f in g["features"]:
        if (f["properties"].get("name") or "") != name:
            continue
        geom = f["geometry"]
        lines = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for ln in lines:
            out.append(np.array([[X(lo, 0), Y(la, 0)] for lo, la in ln], np.float64))
    return out

def draw_river(img, cam, name, alpha=0.8, width=3):
    lay = np.zeros((H, W), np.uint8)
    for a in river(name):
        p = np.round(project0(a, cam) * 4).astype(np.int32)
        cv2.polylines(lay, [p], False, 255, width, cv2.LINE_AA, shift=2)
    m = (lay.astype(np.float32) / 255 * alpha)[..., None]
    return img * (1 - m) + np.array((120, 172, 205), np.float32) * m

# ---------------- places (lon, lat) ----------------
# Positions are approximate, taken from published battle maps and modern mapping of the site.
PL = {
    "Isandlwana": (30.6510, -28.3575), "Rorke's Drift": (30.5370, -28.3510), "Ulundi": (31.4200, -28.3150),
    "Eshowe": (31.4600, -28.8900), "Durban": (31.0300, -29.8600), "Pietermaritzburg": (30.3800, -29.6000),
    "Johannesburg": (28.0400, -26.2000), "Cape Town": (18.4200, -33.9200),
}
B = {
    "camp": (30.6575, -28.3570), "nek": (30.6520, -28.3628), "ngwebeni": (30.7450, -28.2950),
    "loins": (30.7650, -28.2880),
}
ROUTE = {
    "road": [B["camp"], B["nek"], (30.6300, -28.3640), (30.6000, -28.3600), (30.5650, -28.3560), PL["Rorke's Drift"]],
    "chelmsford": [B["camp"], (30.6850, -28.3780), (30.7300, -28.4050), (30.7800, -28.4400)],
    "chest0": [B["ngwebeni"], (30.7300, -28.3120), (30.7150, -28.3270)],
    "chest1": [(30.7150, -28.3270), (30.6950, -28.3400), (30.6780, -28.3500)],
    "left0": [(30.7550, -28.3000), (30.7600, -28.3200), (30.7550, -28.3400)],
    "left1": [(30.7550, -28.3400), (30.7350, -28.3720), (30.7000, -28.3810), (30.6740, -28.3700)],
    "right0": [(30.7350, -28.2900), (30.7150, -28.2900), (30.6950, -28.2960)],
    "right1": [(30.6950, -28.2960), (30.6650, -28.3080), (30.6420, -28.3280), (30.6380, -28.3500), (30.6420, -28.3615)],
    "fireline": [(30.6650, -28.3480), (30.6700, -28.3550), (30.6700, -28.3640)],
    # Columns, January 1879 (simplified): Pearson on the coast, Glyn with Chelmsford in the centre, Wood in the north
    "col_coast": [(31.4000, -29.1900), (31.4400, -29.0400), (31.4600, -28.9000)],
    "col_centre": [(30.3700, -28.4700), PL["Rorke's Drift"], (30.6500, -28.3600)],  # from Helpmekaar
    "col_north": [(30.3000, -27.7000), (30.5600, -27.7600), (30.8000, -27.7800)],
    "second": [(30.5000, -28.0000), (30.8500, -28.1300), (31.1500, -28.2500), (31.3800, -28.3050)],
}

def lerp(a, b, u):
    return a + (b - a) * u

def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def fly(a, b, u, centre_lead=0.6):
    """Camera between two (lon, lat, zoom) keys: zoom eases over the whole shot, the centre leads."""
    uz = ease(u)
    uc = ease(u / centre_lead)
    xa, ya, xb, yb = X(a[0], 0), Y(a[1], 0), X(b[0], 0), Y(b[1], 0)
    x, y = lerp(xa, xb, uc), lerp(ya, yb, uc)
    lon = x / 256 * 360 - 180
    n = math.pi - 2 * math.pi * y / 256
    lat = math.degrees(math.atan(math.sinh(n)))
    return lon, lat, lerp(a[2], b[2], uz)

SHOTS = {
    "zoom_isa": dict(a=(25.5, -29.0, 4.7), b=(30.660, -28.350, 12.75)),
    "columns": dict(a=(30.90, -28.45, 9.30), b=(30.85, -28.42, 9.45)),
    "horns_doctrine": dict(a=(30.70, -28.34, 12.6), b=(30.70, -28.34, 12.62)),
    "horns_doctrine2": dict(a=(30.70, -28.34, 12.62), b=(30.70, -28.34, 12.7)),
    "ngwebeni": dict(a=(30.690, -28.330, 12.75), b=(30.700, -28.325, 12.95)),
    "split": dict(a=(30.700, -28.370, 12.90), b=(30.712, -28.385, 12.78)),
    "horns_open": dict(a=(30.700, -28.330, 12.85), b=(30.698, -28.333, 13.00)),
    "left_horn": dict(a=(30.700, -28.345, 13.00), b=(30.695, -28.350, 13.10)),
    "right_horn": dict(a=(30.680, -28.335, 13.05), b=(30.668, -28.338, 13.15)),
    "closed": dict(a=(30.640, -28.350, 13.05), b=(30.625, -28.352, 12.95)),
    "ulundi": dict(a=(30.90, -28.25, 9.55), b=(31.00, -28.27, 9.75)),
}
BATTLE = ["ngwebeni", "split", "horns_open", "left_horn", "right_horn", "closed"]
DOCTRINE = {"horns_doctrine", "horns_doctrine2"}

def tag_for(name):
    if name in DOCTRINE:
        return "SCHEMATIC  ·  THE DOCTRINE, NOT A RECORD OF THE BATTLE"
    if name.startswith("zoom"):
        return "MAP  ·  REAL TERRAIN AND SATELLITE  ·  MODERN BORDERS SHOWN"
    if name in BATTLE:
        return "SATELLITE IMAGE, 2025  ·  MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE"
    return "MAP  ·  REAL TERRAIN  ·  ROUTES SIMPLIFIED"

def credit_key(name):
    if name == "zoom_isa":
        return "MAPA"
    return "MAPS" if name in BATTLE or name in DOCTRINE else "MAPT"

CREDITS = {
    "MAPA": "Relief: AWS Terrain Tiles (SRTM, GMTED2010, ETOPO1)  |  Contains modified Copernicus Sentinel-2 data (2025)  |  Borders: Natural Earth",
    "MAPT": "Relief: AWS Terrain Tiles (SRTM, GMTED2010, ETOPO1)  |  Borders and rivers: Natural Earth",
    "MAPS": "Contains modified Copernicus Sentinel-2 data (2025)  |  Relief: AWS Terrain Tiles",
}

def name_tag(d, xy, txt, col, a=1.0, size=40, anchor="mm"):
    """Name on a dark plate so it reads on a phone over satellite imagery."""
    if a <= 0.01:
        return
    al = int(255 * a)
    f = font("Cinzel.ttf", size, 700)
    x, y = xy
    tw = d.textlength(txt, font=f) + 3 * (len(txt) - 1)
    x0 = x - tw / 2 if anchor == "mm" else (x - tw if anchor == "r" else x)
    d.rounded_rectangle((x0 - 14, y - size * 0.62, x0 + tw + 14, y + size * 0.62), 8, fill=INK + (int(170 * a),))
    spaced(d, (x0, y), txt, f, col + (al,), 3, anchor="l", stroke=2)

def legend(d, road=False):
    f = font("Lora.ttf", 30, 600); fi = font("Lora-Italic.ttf", 25, 500)
    x1, y0 = W - 48, 34
    rows = [("Zulu army", ZULU, False), ("British", BRIT, False)]
    if road:
        rows.append(("Road to Rorke's Drift", CREAM, True))
    bw = max(max(d.textlength(r[0], font=f) for r in rows) + 110, d.textlength("Schematic  ·  positions approximate", font=fi) + 40)
    d.rounded_rectangle((x1 - bw, y0, x1, y0 + 44 * len(rows) + 58), 10, fill=INK + (185,), outline=GOLD + (200,), width=2)
    for k, (txt, col, dash) in enumerate(rows):
        y = y0 + 34 + 44 * k
        xs = x1 - bw + 22
        if dash:
            for s in range(3):
                d.line((xs + s * 22, y, xs + s * 22 + 12, y), fill=col + (255,), width=5)
        else:
            d.line((xs, y, xs + 56, y), fill=INK + (230,), width=15)
            d.line((xs, y, xs + 56, y), fill=col + (255,), width=10)
        d.text((xs + 76, y), txt, font=f, fill=CREAM + (255,), anchor="lm")
    d.text((x1 - bw / 2, y0 + 44 * len(rows) + 30), "Schematic  ·  positions approximate", font=fi,
           fill=CREAM + (230,), anchor="mm")

def blob(d, xy, rx, ry, col, a=1.0, fill=80):
    if a <= 0.01:
        return
    x, y = xy
    d.ellipse((x - rx, y - ry, x + rx, y + ry), outline=INK + (int(220 * a),), width=10)
    d.ellipse((x - rx, y - ry, x + rx, y + ry), outline=col + (int(245 * a),), width=6, fill=col + (int(fill * a),))

def battle_layer(d, cam, name, u):
    """One movement at a time: earlier moves step back while the new one draws; the right horn comes last."""
    P = lambda k: to_screen(*k, cam)
    i = BATTLE.index(name)
    def st(k, lo=0.0, hi=0.7):
        j = BATTLE.index(k)
        return 1.0 if i > j else (ease((u - lo) / (hi - lo)) if i == j else 0.0)
    def al(k):
        return 255 if BATTLE.index(k) == i else 140
    # the hill and the camp
    hx, hy = P(PL["Isandlwana"])
    d.polygon([(hx - 30, hy + 18), (hx, hy - 26), (hx + 30, hy + 18)], fill=CREAM + (230,), outline=INK + (230,))
    cx, cy = P(B["camp"])
    blob(d, (cx + 18, cy + 4), 38, 30, BRIT)
    # the Zulu army in the Ngwebeni valley
    zx, zy = P(B["ngwebeni"])
    a0 = st("ngwebeni", 0.0, 0.35)
    if i < BATTLE.index("horns_open"):
        blob(d, (zx, zy), 120, 62, ZULU, a=a0)
        name_tag(d, (zx, zy - 98), "ZULU ARMY", ZULU, a=a0, size=36)
        d.text((zx, zy + 96), "Ngwebeni valley", font=font("Lora-Italic.ttf", 36, 500), fill=CREAM + (int(245 * a0),),
               anchor="mm", stroke_width=4, stroke_fill=INK + (int(245 * a0),))
    if name == "ngwebeni":
        rx, ry = P(PL["Rorke's Drift"])
        if -50 < rx < W + 50:
            d.ellipse((rx - 10, ry - 10, rx + 10, ry + 10), fill=GOLD + (255,), outline=INK + (255,), width=3)
            d.text((rx + 22, ry), "Rorke's Drift", font=font("Lora.ttf", 38, 600), fill=CREAM + (250,), anchor="lm",
                   stroke_width=3, stroke_fill=INK + (250,))
    # Chelmsford leaves before dawn
    if i >= BATTLE.index("split"):
        f = st("split", 0.05, 0.75)
        draw_arrow(d, path_px(ROUTE["chelmsford"], cam), BRIT, frac=f, width=13, alpha=255 if name == "split" else 90)
        ex, ey = P(ROUTE["chelmsford"][-1])
        if name == "split":
            name_tag(d, (ex - 30, ey - 70), "CHELMSFORD", CREAM, a=ramp(u, 0.4, 0.7), size=36, anchor="r")
            d.text((ex - 30, ey - 22), "out of camp, south-east", font=font("Lora-Italic.ttf", 32, 500),
                   fill=CREAM + (int(240 * ramp(u, 0.45, 0.75)),), anchor="rm", stroke_width=3,
                   stroke_fill=INK + (int(240 * ramp(u, 0.45, 0.75)),))
    # the horns open: chest, both horns and the loins deploy from the valley
    if i >= BATTLE.index("horns_open"):
        f = st("horns_open", 0.0, 0.6)
        lx, ly = P(B["loins"])
        blob(d, (lx + 40, ly - 10), 70, 40, ZULU, a=0.85 if i > 2 else ramp(u, 0, 0.2), fill=60)
        draw_arrow(d, path_px(ROUTE["chest0"], cam), ZULU, frac=f, width=17, alpha=al("horns_open"))
        draw_arrow(d, path_px(ROUTE["left0"], cam), ZULU, frac=f, width=15, alpha=al("horns_open"))
        draw_arrow(d, path_px(ROUTE["right0"], cam), ZULU, frac=f, width=15, alpha=al("horns_open"))
        if name == "horns_open":
            ta = ramp(u, 0.45, 0.7)
            for key, txt, off in (("chest0", "CHEST", (-10, 52)), ("left0", "LEFT HORN", (70, 0)), ("right0", "RIGHT HORN", (0, -56))):
                x, y = P(ROUTE[key][-1])
                name_tag(d, (x + off[0], y + off[1]), txt, ZULU, a=ta, size=32, anchor="l" if key == "left0" else "mm")
            name_tag(d, (lx + 40, ly + 52), "LOINS · RESERVE", ZULU, a=ta, size=30)
    if i >= BATTLE.index("left_horn"):
        # the British firing line in front of the camp, and the chest held at a distance
        draw_arrow(d, path_px(ROUTE["fireline"], cam), BRIT, frac=1, width=11, alpha=200, head=False)
        draw_arrow(d, path_px(ROUTE["chest1"], cam), ZULU, frac=1, width=17, alpha=150)
        draw_arrow(d, path_px(ROUTE["left1"], cam), ZULU, frac=st("left_horn", 0.05, 0.8), width=15, alpha=al("left_horn"))
        if name == "left_horn":
            x, y = P(ROUTE["left1"][2])
            name_tag(d, (x, y + 60), "LEFT HORN", ZULU, a=ramp(u, 0.3, 0.6), size=34)
    if i >= BATTLE.index("right_horn"):
        draw_arrow(d, path_px(ROUTE["right1"], cam), ZULU, frac=st("right_horn", 0.05, 0.85), width=15, alpha=al("right_horn"))
        if name == "right_horn":
            x, y = P(ROUTE["right1"][1])
            name_tag(d, (x - 30, y - 56), "RIGHT HORN", ZULU, a=ramp(u, 0.25, 0.55), size=34)
            d.text((x - 30, y - 10), "behind the hill, out of sight", font=font("Lora-Italic.ttf", 32, 500),
                   fill=CREAM + (int(240 * ramp(u, 0.35, 0.65)),), anchor="mm", stroke_width=3,
                   stroke_fill=INK + (int(240 * ramp(u, 0.35, 0.65)),))
    if name == "closed":
        f = ease(u / 0.35)
        draw_arrow(d, path_px(ROUTE["road"], cam), CREAM, frac=f, width=6, dash=16, alpha=235, head=False)
        rx, ry = P(PL["Rorke's Drift"])
        d.ellipse((rx - 11, ry - 11, rx + 11, ry + 11), fill=GOLD + (255,), outline=INK + (255,), width=3)
        d.text((rx, ry + 44), "Rorke's Drift", font=font("Lora.ttf", 38, 600), fill=CREAM + (250,), anchor="mm",
               stroke_width=3, stroke_fill=INK + (250,))
        k = ramp(u, 0.4, 0.6)
        nx, ny = P(ROUTE["right1"][-1])
        s = 30
        for sx in (-1, 1):
            d.line((nx - s, ny - s * sx, nx + s, ny + s * sx), fill=INK + (int(255 * k),), width=16)
            d.line((nx - s, ny - s * sx, nx + s, ny + s * sx), fill=ZULU + (int(255 * k),), width=10)
        name_tag(d, (nx - 50, ny + 66), "ROAD CUT", ZULU, a=k, size=34)
    # camp label last, on a plate, so no route line runs through it
    fl = font("Lora.ttf", 40, 600)
    tw = d.textlength("British camp", font=fl)
    d.rounded_rectangle((cx + 62, cy + 52, cx + 90 + tw, cy + 104), 8, fill=INK + (190,))
    d.text((cx + 76, cy + 78), "British camp", font=fl, fill=CREAM + (250,), anchor="lm")
    name_tag(d, (hx, hy - 58), "ISANDLWANA", CREAM, a=1.0, size=34)
    legend(d, road=(name == "closed"))

def doctrine_layer(d, name, u):
    """The horns of the buffalo as a diagram, not tied to the ground."""
    cx, cy = W * 0.40, H * 0.52
    ex0, ey0, ex1, ey1 = cx - 150, cy - 70, cx + 150, cy + 70
    d.rounded_rectangle((ex0, ey0, ex1, ey1), 10, fill=BRIT + (110,), outline=BRIT + (255,), width=6)
    d.text((cx, cy), "ENEMY", font=font("Cinzel.ttf", 42, 700), fill=CREAM + (255,), anchor="mm", stroke_width=3,
           stroke_fill=INK + (255,))
    second = name == "horns_doctrine2"
    a = 1.0 if second else ramp(u, 0, 0.3)
    f = ease((u - 0.0) / 0.3) if second else 0.0
    fh = ease((u - 0.28) / 0.4) if second else 0.0
    # chest
    chx = cx + 520
    d.rounded_rectangle((chx - 70, cy - 120, chx + 70, cy + 120), 14, fill=ZULU + (int(90 * a),), outline=ZULU + (int(255 * a),), width=6)
    name_tag(d, (chx, cy + 222), "CHEST", ZULU, a=a, size=38)
    draw_arrow(d, np.array([(chx - 80, cy), (ex1 + 30, cy)]), ZULU, frac=f, width=20)
    # horns
    for sgn, txt in ((-1, "RIGHT HORN"), (1, "LEFT HORN")):
        y0 = cy + sgn * 150
        pts = np.array([(chx - 40, y0), (cx + 240, cy + sgn * 300), (cx - 40, cy + sgn * 320), (cx - 300, cy + sgn * 210), (ex0 - 40, cy + sgn * 40)])
        d.ellipse((chx - 60, y0 - 26, chx + 20, y0 + 26), fill=ZULU + (int(90 * a),), outline=ZULU + (int(255 * a),), width=5)
        draw_arrow(d, pts, ZULU, frac=fh, width=16)
        name_tag(d, (cx + 120, cy + sgn * 380), txt, ZULU, a=max(a * (0.35 if not second else 1.0), ramp(u, 0.4, 0.6) if second else 0), size=36)
    # loins
    lx = chx + 300
    d.rounded_rectangle((lx - 70, cy - 80, lx + 70, cy + 80), 14, fill=ZULU + (int(50 * a),), outline=ZULU + (int(200 * a),), width=5)
    name_tag(d, (lx, cy - 130), "LOINS", ZULU, a=a, size=36)
    if second:
        d.text((lx, cy + 130), "in reserve", font=font("Lora-Italic.ttf", 34, 500), fill=CREAM + (int(240 * ramp(u, 0.7, 0.9)),),
               anchor="mm", stroke_width=3, stroke_fill=INK + (int(240 * ramp(u, 0.7, 0.9)),))

def labels_layer(d, cam, name, u):
    zc = cam[2]
    def pin(key, txt=None, size=38, side="r", a=1.0, col=GOLD):
        if a <= 0.01:
            return
        lon, lat = PL[key]
        x, y = to_screen(lon, lat, cam)
        if not (-200 < x < W + 200 and -200 < y < H + 200):
            return
        al = int(255 * a)
        r = 9
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (al,), outline=INK + (al,), width=3)
        dx = 22 if side == "r" else -22
        d.text((x + dx, y), txt or key, font=font("Lora.ttf", size, 600), fill=CREAM + (al,),
               anchor="lm" if side == "r" else "rm", stroke_width=3, stroke_fill=INK + (al,))
    def area(txt, lon, lat, size=44, a=1.0, col=CREAM, sub=None):
        if a <= 0.01:
            return
        x, y = to_screen(lon, lat, cam)
        al = int(235 * a)
        spaced(d, (x, y), txt, font("Cinzel.ttf", size, 700), col + (al,), max(4, size // 6), stroke=3)
        if sub:
            d.text((x, y + size * 0.95), sub, font=font("Lora-Italic.ttf", int(size * 0.62), 500), fill=CREAM + (al,),
                   anchor="mm", stroke_width=3, stroke_fill=INK + (al,))
    def sea(txt, lon, lat, size=40, a=1.0):
        if a <= 0.01:
            return
        x, y = to_screen(lon, lat, cam)
        al = int(220 * a)
        d.text((x, y), txt, font=font("Lora-Italic.ttf", size, 500), fill=(200, 222, 236, al), anchor="mm")

    if name == "zoom_isa":
        area("SOUTH AFRICA", 24.0, -30.5, 46, window(zc, 4.0, 6.6), sub="modern borders")
        sea("Indian Ocean", 34.5, -31.5, 40, window(zc, 4.0, 7.0))
        sea("Atlantic Ocean", 13.5, -31.0, 40, window(zc, 4.0, 5.8))
        area("KWAZULU-NATAL", 30.9, -28.9, 40, window(zc, 6.4, 8.8), col=GOLD, sub="today")
        pin("Durban", a=window(zc, 6.6, 9.2))
        pin("Rorke's Drift", side="l", a=window(zc, 9.6, 13.2))
        pin("Isandlwana", size=44, a=ramp(zc, 6.4, 7.0) * (1 - ramp(zc, 11.8, 12.4)))
        if zc > 11.8:
            hx, hy = to_screen(*PL["Isandlwana"], cam)
            name_tag(d, (hx, hy - 70), "ISANDLWANA", CREAM, a=ramp(zc, 11.9, 12.5), size=44)
    elif name == "columns":
        area("ZULULAND", 31.35, -28.05, 46, 1.0, col=GOLD, sub="the Zulu kingdom, 1879")
        area("NATAL", 30.0, -29.25, 42, 1.0, sub="British colony")
        sea("Indian Ocean", 32.2, -29.4, 40, 1.0)
        d.text(to_screen(30.95, -28.93, cam), "Thukela river", font=font("Lora-Italic.ttf", 30, 500), fill=(200, 222, 236, 230),
               anchor="mm", stroke_width=3, stroke_fill=INK + (200,))
        f = ease(u / 0.6)
        for k, w in (("col_coast", 11), ("col_north", 11), ("col_centre", 15)):
            draw_arrow(d, path_px(ROUTE[k], cam), BRIT, frac=f, width=w, alpha=255 if k == "col_centre" else 170)
        pin("Rorke's Drift", size=42, side="l", a=1.0, col=BRIT)
        pin("Ulundi", "oNdini (Ulundi) · royal homestead", size=36, a=1.0)
        name_tag(d, to_screen(30.56, -28.22, cam), "CHELMSFORD", CREAM, a=ramp(u, 0.3, 0.55), size=34)
        d.text((W / 2 - 260, H - 132), "British invasion columns, January 1879  ·  simplified", font=font("Lora-Italic.ttf", 32, 500),
               fill=CREAM + (230,), anchor="mm", stroke_width=3, stroke_fill=INK + (230,))
    elif name == "ulundi":
        area("ZULULAND", 31.0, -27.95, 42, 1.0, col=GOLD)
        pin("Isandlwana", a=1.0, side="l")
        pin("Rorke's Drift", a=1.0, side="l")
        draw_arrow(d, path_px(ROUTE["second"], cam), BRIT, frac=ease(u / 0.65), width=14)
        pin("Ulundi", "oNdini (Ulundi)", size=46, a=ramp(u, 0.5, 0.7), col=BRIT)
        d.text((W / 2, H - 132), "Second British invasion, June–July 1879  ·  simplified", font=font("Lora-Italic.ttf", 32, 500),
               fill=CREAM + (230,), anchor="mm", stroke_width=3, stroke_fill=INK + (230,))

DUR = {}

def render(name, t, dur):
    """Map frame (float32 HxWx3) for shot `name` at local time t of a shot lasting dur seconds."""
    DUR[name] = dur
    spec = SHOTS[name]
    u = min(1.0, max(0.0, t / max(dur, 0.1)))
    cam = fly(spec["a"], spec["b"], u, centre_lead=0.55 if name.startswith("zoom") else 1.0)
    img = base_image(cam)
    if name in ("columns", "ulundi", "zoom_isa") and cam[2] < 11:
        img = draw_river(img, cam, "Tugela", alpha=0.85 * (1 - ramp(cam[2], 10, 11)), width=4)
    if cam[2] < 10.5:
        img = draw_borders(img, cam, alpha=0.5 * (1 - ramp(cam[2], 9.5, 10.5)))
    img = img * vignette()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if name in DOCTRINE:
        img = cv2.GaussianBlur(img, (0, 0), 9) * 0.42
        doctrine_layer(d, name, u)
    elif name in BATTLE:
        img = img * 0.74
        battle_layer(d, cam, name, u)
    labels_layer(d, cam, name, u)
    o = np.asarray(ov, dtype=np.float32)
    a = o[..., 3:4] / 255
    return img * (1 - a) + o[..., :3] * a

@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return (1 - 0.28 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
