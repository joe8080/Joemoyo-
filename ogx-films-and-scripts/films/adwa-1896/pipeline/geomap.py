# Real-map shots for OGX Adwa v1.1: shaded relief (AWS Terrain Tiles) and Sentinel-2 imagery on a
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
ITAL = (214, 64, 46)      # Italian moves
ETH = (250, 204, 64)      # Ethiopian moves
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

# ---------------- places (lon, lat) ----------------
PL = {
    "Adwa": (38.896, 14.164), "Aksum": (38.718, 14.121), "Mekelle": (39.475, 13.497),
    "Amba Alagi": (39.55, 12.98), "Massawa": (39.45, 15.609), "Addis Ababa": (38.74, 9.03),
    "Rome": (12.496, 41.903), "Wolaita": (37.75, 6.85), "Kaffa": (36.24, 7.27),
}
# Battle sketch, schematic and approximate (after standard published battle maps: Italian columns
# march west from the Sauria camp by night; the Ethiopian army is camped around Adwa).
B = {
    "it_camp": (39.075, 14.085), "eth_camp": (38.915, 14.158),
    "alb_obj": (38.988, 14.112), "ari_obj": (38.995, 14.140), "dab_obj": (39.002, 14.166),
    "alb_far": (38.938, 14.128),
}
ROUTE = {
    "alb": [B["it_camp"], (39.035, 14.088), (39.008, 14.100), B["alb_obj"]],
    "alb_over": [B["alb_obj"], (38.965, 14.120), B["alb_far"]],
    "ari": [B["it_camp"], (39.040, 14.108), (39.015, 14.128), B["ari_obj"]],
    "dab": [B["it_camp"], (39.045, 14.128), (39.022, 14.152), B["dab_obj"]],
    "dab_veer": [B["dab_obj"], (38.988, 14.182), (38.965, 14.200)],
    "res": [B["it_camp"], (39.048, 14.100), (39.030, 14.112)],
    "eth_alb": [(38.925, 14.150), (38.930, 14.140), (38.934, 14.133)],
    "eth_gap": [(38.932, 14.152), (38.950, 14.142), (38.968, 14.128)],
    "eth_dab": [(38.925, 14.175), (38.945, 14.195), (38.958, 14.200)],
    "eth_ctr_n": [(38.960, 14.175), (38.985, 14.158), (38.992, 14.148)],
    "eth_ctr_s": [(38.955, 14.110), (38.978, 14.122), (38.988, 14.134)],
}

# ---------------- shots ----------------
def lerp(a, b, u):
    return a + (b - a) * u

def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def fly(a, b, u, centre_lead=0.6):
    """Camera between two (lon, lat, zoom) keys: zoom eases over the whole shot, the centre leads."""
    uz = ease(u)
    uc = ease(u / centre_lead)
    # interpolate the centre in Mercator space
    xa, ya, xb, yb = X(a[0], 0), Y(a[1], 0), X(b[0], 0), Y(b[1], 0)
    x, y = lerp(xa, xb, uc), lerp(ya, yb, uc)
    lon = x / 256 * 360 - 180
    n = math.pi - 2 * math.pi * y / 256
    lat = math.degrees(math.atan(math.sinh(n)))
    return lon, lat, lerp(a[2], b[2], uz)

BATTLE_CAM = (38.988, 14.128, 13.2)
SHOTS = {
    "zoom_adwa": dict(a=(22.0, 6.0, 4.35), b=(38.93, 14.15, 12.85), kind="terrain"),
    "south": dict(a=(38.2, 9.9, 6.95), b=(38.2, 9.6, 7.2), kind="terrain"),
    "region": dict(a=(27.0, 29.0, 5.35), b=(39.3, 15.0, 7.55), kind="terrain"),
    "provinces": dict(a=(38.6, 11.7, 7.0), b=(38.7, 11.9, 7.2), kind="terrain"),
    "zoom_tigray": dict(a=(39.25, 13.55, 8.55), b=(38.985, 14.14, 12.9), kind="mixed"),
    "standoff": dict(a=(38.985, 14.136, 12.9), b=(38.988, 14.132, 13.15), kind="sat"),
    "plan_a": dict(a=(38.988, 14.132, 13.15), b=BATTLE_CAM, kind="sat"),
    "plan_b": dict(a=BATTLE_CAM, b=(38.992, 14.128, 13.3), kind="sat"),
    "plan_c": dict(a=(38.992, 14.128, 13.3), b=(38.992, 14.130, 13.38), kind="sat"),
    "albertone_a": dict(a=(38.985, 14.132, 13.35), b=(38.965, 14.130, 13.6), kind="sat"),
    "albertone_b": dict(a=(38.965, 14.130, 13.6), b=(38.958, 14.132, 13.7), kind="sat"),
    "gap": dict(a=(38.960, 14.138, 13.55), b=(38.962, 14.140, 13.45), kind="sat"),
    "dabormida": dict(a=(38.980, 14.160, 13.45), b=(38.978, 14.172, 13.6), kind="sat"),
    "pieces": dict(a=(38.975, 14.152, 13.4), b=(38.978, 14.150, 13.25), kind="sat"),
    "amba": dict(a=(39.25, 13.6, 8.3), b=(39.45, 13.2, 9.3), kind="terrain"),
    "coast": dict(a=(39.15, 14.75, 8.35), b=(39.2, 14.95, 8.25), kind="terrain"),
    "africa": dict(a=(20.0, 7.0, 4.15), b=(21.0, 7.0, 4.3), kind="terrain"),
}
BATTLE = {"standoff", "plan_a", "plan_b", "plan_c", "albertone_a", "albertone_b", "gap", "dabormida", "pieces"}

def tag_for(name):
    if name.startswith("zoom"):
        return "MAP  ·  REAL TERRAIN AND SATELLITE  ·  MODERN BORDERS SHOWN"
    if name in BATTLE:
        return "SATELLITE IMAGE, 2025  ·  MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE"
    return "MAP  ·  REAL TERRAIN  ·  MODERN BORDERS SHOWN"

def credit_key(name):
    if name == "zoom_adwa":
        return "MAPA"
    return "MAPS" if name in BATTLE or name == "zoom_tigray" else "MAPT"

CREDITS = {
    "MAPA": "Relief: AWS Terrain Tiles (SRTM, GMTED2010, ETOPO1)  |  Contains modified Copernicus Sentinel-2 data (2025)  |  Borders: Natural Earth",
    "MAPT": "Relief: AWS Terrain Tiles (SRTM, GMTED2010, ETOPO1)  |  Borders: Natural Earth",
    "MAPS": "Contains modified Copernicus Sentinel-2 data (2025)  |  Relief: AWS Terrain Tiles",
}

def name_tag(d, xy, txt, col, a=1.0, size=40, anchor="mm"):
    """Brigade / place name on a dark plate so it reads on a phone over satellite imagery."""
    if a <= 0.01:
        return
    al = int(255 * a)
    f = font("Cinzel.ttf", size, 700)
    x, y = xy
    tw = d.textlength(txt, font=f) + 3 * (len(txt) - 1)
    x0 = x - tw / 2 if anchor == "mm" else x
    d.rounded_rectangle((x0 - 14, y - size * 0.62, x0 + tw + 14, y + size * 0.62), 8, fill=INK + (int(170 * a),))
    spaced(d, (x0, y), txt, f, col + (al,), 3, anchor="l", stroke=2)

def legend(d):
    """Key for the battle maps (v1.5): colours, planned line, and the schematic disclaimer."""
    f = font("Lora.ttf", 30, 600); fi = font("Lora-Italic.ttf", 25, 500)
    x1, y0 = W - 48, 34
    rows = [("Italian-led brigades", ITAL, False), ("Ethiopian forces", ETH, False), ("Planned Italian line", CREAM, True)]
    bw = max(d.textlength(r[0], font=f) for r in rows) + 110
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

def battle_layer(d, cam, name, u):
    """Arrows and markers for the battle sequence. v1.5 (MJ readability notes): one movement at a time,
    earlier moves dimmed while the new one draws, persistent brigade names, larger type, legend."""
    P = lambda k: to_screen(*k, cam)
    order = ["standoff", "plan_a", "plan_b", "plan_c", "albertone_a", "albertone_b", "gap", "dabormida", "pieces"]
    i = order.index(name)
    def st(k, lo=0.0, hi=0.7):  # progress of an element introduced in shot k, optionally staggered within it
        j = order.index(k)
        return 1.0 if i > j else (ease((u - lo) / (hi - lo)) if i == j else 0.0)
    def al(k):  # elements from earlier shots step back so the new movement stands out
        return 255 if order.index(k) == i else 150
    # camps
    for key, col, txt in (("it_camp", ITAL, "Italian camp"), ("eth_camp", ETH, "Ethiopian camp")):
        x, y = P(B[key])
        r = 52 if key == "eth_camp" else 30
        box = (x - r * 2.2, y - r, x + r * 2.2, y + r)
        d.ellipse(box, outline=INK + (220,), width=10)
        d.ellipse(box, outline=col + (245,), width=6, fill=col + (80,))
        ly = y - r - 34 if key == "eth_camp" else y + r + 34
        d.text((x, ly), txt, font=font("Lora.ttf", 44, 600), fill=CREAM + (250,), anchor="mm",
               stroke_width=4, stroke_fill=INK + (250,))
    # intended line
    if i >= order.index("plan_b"):
        a = st("plan_b", 0.0, 0.25)
        line = [B["alb_obj"], B["ari_obj"], B["dab_obj"]]
        draw_arrow(d, path_px(line, cam), CREAM, frac=1, width=5, dash=16, alpha=int(220 * a), head=False)
        x, y = P(B["dab_obj"])
        d.text((x, y - 52), "planned line", font=font("Lora-Italic.ttf", 36, 500), fill=CREAM + (int(240 * a),),
               anchor="mm", stroke_width=4, stroke_fill=INK + (int(240 * a),))
    # Italian columns: drawn one after another in plan_b, each name appearing with its column
    stagger = {"alb": (0.05, 0.40), "ari": (0.35, 0.68), "dab": (0.62, 0.95)}
    names = {"alb": ("ALBERTONE", "alb_obj", (0, 58)), "ari": ("ARIMONDI", "ari_obj", (34, 0)),
             "dab": ("DABORMIDA", "dab_obj", (34, 8))}
    if i >= order.index("plan_b"):
        for k in ("alb", "ari", "dab"):
            f = st("plan_b", *stagger[k])
            draw_arrow(d, path_px(ROUTE[k], cam), ITAL, frac=f, width=13, alpha=al("plan_b"))
    if i >= order.index("plan_c"):
        f = st("plan_c", 0.1, 0.7)
        draw_arrow(d, path_px(ROUTE["res"], cam), ITAL, frac=f, width=9, dash=18, alpha=al("plan_c"))
        x, y = P(ROUTE["res"][-1])
        name_tag(d, (x, y + 52), "RESERVE", CREAM, a=f, size=32)
    if i >= order.index("albertone_a"):
        draw_arrow(d, path_px(ROUTE["alb_over"], cam), ITAL, frac=st("albertone_a"), width=13, alpha=al("albertone_a"))
    if i >= order.index("albertone_b"):
        draw_arrow(d, path_px(ROUTE["eth_alb"], cam), ETH, frac=st("albertone_b"), width=17, alpha=al("albertone_b"))
    if i >= order.index("gap"):
        f = st("gap")
        x0, y0 = P(B["alb_far"]); x1, y1 = P(B["ari_obj"])
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        d.text((mx, my - 80), "GAP", font=font("Cinzel.ttf", 58, 700), fill=ETH + (int(255 * f),), anchor="mm",
               stroke_width=4, stroke_fill=INK + (int(255 * f),))
        draw_arrow(d, path_px(ROUTE["eth_gap"], cam), ETH, frac=f, width=19, alpha=al("gap"))
    if i >= order.index("dabormida"):
        draw_arrow(d, path_px(ROUTE["dab_veer"], cam), ITAL, frac=st("dabormida"), width=13, alpha=al("dabormida"))
    if i >= order.index("pieces"):
        f = st("pieces")
        for k in ("eth_dab", "eth_ctr_n", "eth_ctr_s"):
            draw_arrow(d, path_px(ROUTE[k], cam), ETH, frac=f, width=17)
        for k in (B["alb_far"], B["ari_obj"], ROUTE["dab_veer"][-1]):
            x, y = P(k)
            r = 66
            d.ellipse((x - r, y - r, x + r, y + r), outline=INK + (int(200 * f),), width=10)
            d.ellipse((x - r, y - r, x + r, y + r), outline=ITAL + (int(240 * f),), width=6)
    # persistent brigade names, drawn last so nothing covers them
    if i >= order.index("plan_b"):
        for k in ("alb", "ari", "dab"):
            txt, key, off = names[k]
            pos = B[key]
            if k == "alb" and i > order.index("albertone_a"):
                pos = B["alb_far"]
            if k == "dab" and i > order.index("dabormida"):
                pos = ROUTE["dab_veer"][-1]
            x, y = P(pos)
            a = st("plan_b", stagger[k][0] + 0.15, stagger[k][1]) if name == "plan_b" else 1.0
            name_tag(d, (x + off[0], y + off[1]), txt, CREAM, a=a, size=40, anchor="mm" if off[0] == 0 else "l")
    legend(d)

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

    if name == "zoom_adwa":
        area("ETHIOPIA", 39.6, 8.6, 46, window(zc, 4.0, 7.0))
        area("ERITREA", 38.6, 16.0, 34, window(zc, 5.6, 8.4))
        sea("Red Sea", 38.6, 20.5, 40, window(zc, 4.0, 6.8))
        area("TIGRAY", 39.3, 13.6, 40, window(zc, 7.6, 9.8), col=GOLD)
        pin("Mekelle", a=window(zc, 7.8, 9.8))
        pin("Aksum", side="l", a=window(zc, 9.2, 13))
        pin("Adwa", size=44, a=ramp(zc, 6.6, 7.2))
    elif name == "south":
        # v1.5: Kaffa was conquered in 1897, after Adwa (MJ brief, S2); it now arrives on its own, dated
        tt = u * DUR.get("south", 10.0)
        area("SHEWA", 39.6, 9.9, 40, ramp(u, 0.0, 0.15), col=GOLD)
        pin("Addis Ababa", a=ramp(u, 0, 0.1))
        pin("Adwa", a=ramp(u, 0, 0.1))
        a0 = to_screen(*PL["Addis Ababa"], cam)
        for k, side, t0, txt in (("Wolaita", "r", 1.2, "Wolaita"), ("Kaffa", "l", 5.4, "Kaffa · 1897")):
            b0 = to_screen(*PL[k], cam)
            mid = ((a0[0] + b0[0]) / 2 + (25 if k == "Wolaita" else -40), (a0[1] + b0[1]) / 2)
            f = ease((tt - t0) / 1.6)
            draw_arrow(d, np.array([a0, mid, b0]), ITAL, frac=f, width=12)
            pin(k, txt, size=42, side=side, a=ramp(tt, t0 + 1.0, t0 + 1.5), col=ITAL)
        d.text((W / 2, H - 132), "Southern conquests  ·  two examples  ·  Kaffa after Adwa", font=font("Lora-Italic.ttf", 32, 500),
               fill=CREAM + (230,), anchor="mm", stroke_width=3, stroke_fill=INK + (230,))
    elif name == "region":
        area("ITALY", 13.2, 43.4, 44, window(zc, 4.5, 6.5))
        pin("Rome", a=window(zc, 4.5, 6.3))
        sea("Mediterranean Sea", 20.0, 34.6, 40, window(zc, 4.5, 6.3))
        sea("Red Sea", 39.6, 18.6, 40, ramp(zc, 5.0, 5.6))
        area("ERITREA", 38.4, 16.25, 44, ramp(zc, 6.4, 7.0), sub="Italian colony")
        area("ETHIOPIA", 39.2, 12.4, 40, ramp(zc, 6.6, 7.2))
        pin("Massawa", a=ramp(zc, 6.8, 7.3))
    elif name == "provinces":
        for txt, lon, lat in (("SHEWA", 39.5, 9.7), ("GOJJAM", 37.5, 10.6), ("WOLLO", 39.75, 11.35), ("TIGRAY", 39.3, 13.85)):
            area(txt, lon, lat, 40, ramp(u, 0, 0.12), col=GOLD)
        f = ease((u - 0.12) / 0.6)
        for pts in ([(39.3, 10.0), (39.4, 11.6), (39.35, 12.9)], [(37.7, 10.9), (38.4, 12.2), (39.0, 13.1)],
                    [(39.7, 11.7), (39.5, 12.95)]):
            draw_arrow(d, path_px(pts, cam), CREAM, frac=f, width=10)
        pin("Addis Ababa", a=1)
    elif name == "zoom_tigray":
        area("TIGRAY", 39.4, 13.75, 42, window(zc, 8.0, 9.6), col=GOLD)
        pin("Mekelle", a=window(zc, 8.0, 10.0))
        pin("Amba Alagi", side="r", a=window(zc, 8.0, 9.6))
        pin("Aksum", side="l", a=window(zc, 8.4, 11.2))
        pin("Adwa", size=44, a=1.0)
    elif name in ("coast",):
        fill_args = None
        area("ERITREA", 38.7, 15.75, 42, 1.0, sub="Italian colony")
        sea("Red Sea", 40.3, 15.9, 40, 1.0)
        pin("Massawa", a=1.0)
        pin("Adwa", a=1.0, side="l")
        a0 = to_screen(*PL["Adwa"], cam); b0 = to_screen(*PL["Massawa"], cam)
        draw_arrow(d, np.array([a0, ((a0[0] + b0[0]) / 2 - 30, (a0[1] + b0[1]) / 2), b0]), ETH, frac=ease(u / 0.6),
                   width=6, dash=18, alpha=210, head=False)
    elif name == "africa":
        area("ETHIOPIA", 40.0, 8.4, 34, 1.0, col=GOLD)
        area("ERITREA", 38.0, 17.6, 26, 1.0, sub="Italian colony")
        d.text((W / 2, H - 132), "Modern borders shown", font=font("Lora-Italic.ttf", 30, 500), fill=CREAM + (220,),
               anchor="mm", stroke_width=3, stroke_fill=INK + (220,))
    elif name == "amba":
        area("TIGRAY", 39.05, 13.95, 42, 1.0, col=GOLD)
        pin("Mekelle", size=40, a=1.0)
        pin("Adwa", size=40, a=1.0, side="l")
        pin("Amba Alagi", size=48, a=ramp(u, 0.15, 0.35), col=ETH)
    elif name in BATTLE:
        pin("Adwa", size=50, a=1.0, side="l")

DUR = {}

def render(name, t, dur):
    """Map frame (float32 HxWx3) for shot `name` at local time t of a shot lasting dur seconds."""
    DUR[name] = dur
    spec = SHOTS[name]
    u = min(1.0, max(0.0, t / max(dur, 0.1)))
    cam = fly(spec["a"], spec["b"], u, centre_lead=0.55 if name.startswith("zoom") or name == "region" else 1.0)
    img = base_image(cam)
    if name in ("region", "coast"):
        img = fill_country(img, cam, "Eritrea", ITAL, fill=0.18, line=0.75, width=3)
    if name == "africa":
        img = fill_country(img, cam, "Ethiopia", ETH, fill=0.5, line=1.0, width=4)
        img = fill_country(img, cam, "Eritrea", ITAL, fill=0.55, line=1.0, width=4)
    if cam[2] < 10.5:
        img = draw_borders(img, cam, alpha=0.5 * (1 - ramp(cam[2], 9.5, 10.5)))
    # gentle vignette keeps type readable
    img = img * vignette()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if name in BATTLE:
        img = img * 0.74  # v1.5: darker satellite base so routes and names read on a phone
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
