# OGX Isandlwana v2 - zero-credit proof compositor (opening + battle).
# Picture: 3D terrain flights, relief battle maps with named regiments, archive, regraded existing Kling clips,
# testimony cards. Sound: existing approved-voice takes, existing score cues, procedural SFX.
import os, sys, json, math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
S = "/tmp/claude-0/-home-user/c8a2a160-21fc-57ae-b255-e46475a247d7/scratchpad"
from plate import P as PL
import terrain3d as T
import sfx
sys.path.append(f"{S}/isa/build11")
import geomap as OLD

W, H, FPS = 1920, 1080, 24
GOLD = (201, 164, 92); CREAM = (239, 230, 210); BRIT = (222, 70, 50); ZULU = (250, 204, 64); INK = (10, 14, 14)
MOTION = f"{S}/isa/build/motion"; ARCH = f"{S}/isa2/arch"; VOW = f"{S}/isa/build/vowav"; MUS = f"{S}/isa/build/music"

def font(name, size, weight=None):
    f = ImageFont.truetype(f"{HERE}/fonts/{name}", size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f
def spaced(d, xy, text, f, fill, sp, anchor="l"):
    x, y = xy
    tw = sum(d.textlength(c, font=f) for c in text) + sp * (len(text) - 1)
    if anchor == "c": x -= tw / 2
    elif anchor == "r": x -= tw
    for c in text:
        d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + sp
    return tw
def ease(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)
def ramp(t, a, b): return ease((t - a) / max(b - a, 1e-6))
def win(t, a, b, f=0.4): return min(ramp(t, a, a + f), 1 - ramp(t, b - f, b))

# ---------------------------------------------------------------- grading
def grade(img, mode, k=1.0):
    x = img.astype(np.float32) / 255
    if mode == "none": return img.astype(np.float32)
    g = x.mean(2, keepdims=True)
    if mode == "morning":
        x = g + (x - g) * 0.82; x = x * np.array([0.90, 0.97, 1.10]); x = x + np.array([0.0, 0.01, 0.04]) * (1 - x)
    elif mode == "midday":
        x = g + (x - g) * 0.80; x = x * np.array([0.93, 1.0, 1.07]); x = np.clip((x - 0.5) * 1.12 + 0.52, 0, 1)
    elif mode == "battle":
        x = g + (x - g) * 0.55; x = x * np.array([1.0, 0.97, 0.93]); x = np.clip((x - 0.5) * 1.18 + 0.5, 0, 1)
        x = x * 0.92 + 0.05
    elif mode == "eclipse":   # k: 0 = battle look, 1 = darkened, cold
        x = g + (x - g) * (0.55 - 0.3 * k); x = x * np.array([1.0, 0.97 + 0.02 * k, 0.93 + 0.12 * k])
        x = np.clip((x - 0.5) * 1.18 + 0.5, 0, 1) * (1 - 0.68 * k)
    elif mode == "dusk_map":
        x = x * np.array([1.02, 0.98, 0.92])
    return np.clip(x, 0, 1) * 255
def vignette_mask():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return np.clip(1 - 0.38 * np.clip(r - 0.55, 0, 1) ** 1.4, 0, 1)[..., None]
VIG = vignette_mask()
GRAIN = [(np.random.default_rng(i).standard_normal((H // 2, W // 2)).astype(np.float32)) for i in range(8)]

# ---------------------------------------------------------------- sources
class Clip:
    cache = {}
    @classmethod
    def frames(cls, name):
        if name not in cls.cache:
            if len(cls.cache) > 3: cls.cache.pop(next(iter(cls.cache)))
            cap = cv2.VideoCapture(f"{MOTION}/{name}.mp4"); fr = []
            while True:
                ok, f = cap.read()
                if not ok: break
                fr.append(f[..., ::-1])
            cls.cache[name] = fr
        return cls.cache[name]
def clip_frame(name, t, speed=1.0, start=0.0, punch=1.0, cx=0.5, cy=0.5, drift=(0, 0, 0), dur=5.0):
    fr = Clip.frames(name)
    s = (start + t * speed) * FPS
    i0 = int(np.clip(math.floor(s), 0, len(fr) - 1)); i1 = min(i0 + 1, len(fr) - 1); a = s - math.floor(s)
    f = fr[i0].astype(np.float32) if (a < 0.05 or i0 == i1) else fr[i0] * (1 - a) + fr[i1].astype(np.float32) * a
    u = t / max(dur, 1e-3)
    z = punch * (1 + drift[2] * u)
    if z > 1.001 or drift[0] or drift[1]:
        ccx = (cx + drift[0] * u) * W; ccy = (cy + drift[1] * u) * H
        cw, ch = W / z, H / z
        ccx = np.clip(ccx, cw / 2, W - cw / 2); ccy = np.clip(ccy, ch / 2, H - ch / 2)
        M = np.array([[1 / z, 0, ccx - cw / 2], [0, 1 / z, ccy - ch / 2]], np.float32)
        f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    return f

_flcache = {}
def flight_frame(name, t):
    n = len(CAMS[name]); i = int(np.clip(round(t * FPS), 0, n - 1))
    key = (name, i)
    if key not in _flcache:
        if len(_flcache) > 6: _flcache.pop(next(iter(_flcache)))
        _flcache[key] = cv2.imread(f"{HERE}/fl/{name}_{i:04d}.jpg")[..., ::-1].astype(np.float32)
    f = _flcache[key]
    # restore contrast lost to haze
    x = f / 255; x = np.clip((x - 0.47) * 1.42 + 0.47, 0, 1)
    return x * 255, CAMS[name][i]
CAMS = json.load(open(f"{HERE}/fl/cams_O1_O11_B1.json"))

PLATE = None
def plate():
    global PLATE
    if PLATE is None: PLATE = np.load(f"{HERE}/plate_rgb.npy")
    return PLATE
def map_cam(keys, t):
    """keys: list of (time, lon, lat, zoom)  zoom = screen px per plate px."""
    if t <= keys[0][0]: k = keys[0][1:]
    elif t >= keys[-1][0]: k = keys[-1][1:]
    else:
        for a, b in zip(keys, keys[1:]):
            if a[0] <= t <= b[0]:
                u = ease((t - a[0]) / (b[0] - a[0])); k = tuple(a[i] + (b[i] - a[i]) * u for i in (1, 2, 3)); break
    return k
def map_frame(cam):
    lon, lat, z = cam; cx, cy = PL(lon, lat)
    M = np.array([[1 / z, 0, cx - W / 2 / z], [0, 1 / z, cy - H / 2 / z]], np.float32)
    f = cv2.warpAffine(plate(), M, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    x = f.astype(np.float32) / 255
    x = np.clip((x - 0.45) * 1.15 + 0.47, 0, 1)
    return x * 255
def to_scr(lon, lat, cam):
    px, py = PL(lon, lat); cx, cy = PL(cam[0], cam[1]); z = cam[2]
    return ((px - cx) * z + W / 2, (py - cy) * z + H / 2)

_arch = {}
def arch_frame(name, t, dur, z0=1.0, z1=1.12, c0=(0.5, 0.5), c1=(0.5, 0.5), frame_h=900):
    if name not in _arch:
        im = Image.open(f"{ARCH}/{name}.png").convert("RGB"); _arch[name] = im
    im = _arch[name]
    u = ease(t / dur); z = z0 + (z1 - z0) * u; c = (c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u)
    # print sits on a dark paper ground; the print itself is panned/zoomed inside its frame
    iw, ih = im.size; fh = frame_h; fw = int(fh * iw / ih)
    if fw > 1500: fw = 1500; fh = int(fw * ih / iw)
    cw, ch = iw / z, ih / z
    x0 = np.clip(c[0] * iw - cw / 2, 0, iw - cw); y0 = np.clip(c[1] * ih - ch / 2, 0, ih - ch)
    crop = im.resize((fw, fh), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    bg = np.zeros((H, W, 3), np.float32) + np.array([24, 21, 17], np.float32)
    bg += (GRAIN[3].repeat(2, 0).repeat(2, 1)[..., None] * 3)
    ox, oy = (W - fw) // 2, (H - fh) // 2 - 30
    sh = np.zeros((H, W), np.float32); sh[oy + 14:oy + fh + 14, ox + 10:ox + fw + 10] = 1
    sh = cv2.GaussianBlur(sh, (0, 0), 18)[..., None]
    bg = bg * (1 - 0.6 * sh)
    a = np.asarray(crop).astype(np.float32)
    g = a.mean(2, keepdims=True); a = g + (a - g) * 0.6; a = a * np.array([1.02, 0.98, 0.90])  # warm the print slightly
    bg[oy:oy + fh, ox:ox + fw] = a
    cv2.rectangle(bg, (ox - 2, oy - 2), (ox + fw + 1, oy + fh + 1), (150, 125, 80), 2)
    return bg

# ---------------------------------------------------------------- overlay helpers (draw on RGBA PIL layer)
def pill(d, xy, text, f, fg=CREAM, a=1.0, anchor="mm", sp=3, bg=INK + (175,), pad=(18, 10)):
    if a <= 0.01: return
    tw = sum(d.textlength(c, font=f) for c in text) + sp * (len(text) - 1)
    bb = f.getbbox("ÉQ"); th = bb[3] - bb[1]
    x, y = xy
    if anchor == "mm": x0, y0 = x - tw / 2 - pad[0], y - th / 2 - pad[1]
    elif anchor == "lm": x0, y0 = x, y - th / 2 - pad[1]
    else: x0, y0 = x - tw - 2 * pad[0], y - th / 2 - pad[1]
    d.rounded_rectangle((x0, y0, x0 + tw + 2 * pad[0], y0 + th + 2 * pad[1]), 7, fill=bg[:3] + (int(bg[3] * a),))
    spaced(d, (x0 + pad[0], y0 + pad[1] - bb[1] + 1), text, f, fg + (int(255 * a),), sp)
def tag(d, text, a=1.0):
    f = font("Lora.ttf", 21, 600); tw = d.textlength(text, font=f)
    d.rounded_rectangle((40, 36, 40 + tw + 32, 76), 8, fill=(10, 14, 14, int(150 * a)))
    d.text((56, 56), text, font=f, fill=CREAM + (int(215 * a),), anchor="lm")
def marker(d, text, a=1.0):
    if a <= 0.01: return
    f = font("Cinzel.ttf", 26, 600)
    tw = spaced(ImageDraw.Draw(Image.new("RGBA", (4, 4))), (0, 0), text, f, GOLD, 4)
    x1 = W - 48; x0 = x1 - tw - 44
    d.rounded_rectangle((x0, 34, x1, 82), 7, fill=(10, 14, 14, int(165 * a)))
    spaced(d, (x0 + 22, 44), text, f, GOLD + (int(255 * a),), 4)
def watermark(d):
    f = font("Cinzel.ttf", 26, 700)
    tw = sum(d.textlength(c, font=f) for c in "ORIGINEX") + 21
    spaced(d, (W - 60 - tw, 1012), "ORIGINEX", f, GOLD + (190,), 3)
def ost(d, text, a=1.0, sub=None):
    if a <= 0.01: return
    fo = font("Cinzel.ttf", 38, 600); y = 900
    bw = spaced(ImageDraw.Draw(Image.new("RGBA", (4, 4))), (0, 0), text, fo, GOLD, 5)
    h = 66 if not sub else 104
    d.rounded_rectangle((90, y - 22, 90 + max(bw, 0) + 70, y - 22 + h + 22), 6, fill=(8, 12, 12, int(165 * a)))
    d.line((110, y - 6, 110, y + h - 16), fill=GOLD + (int(255 * a),), width=3)
    spaced(d, (132, y - 4), text, fo, CREAM + (int(255 * a),), 5)
    if sub: d.text((132, y + 48), sub, font=font("Lora-Italic.ttf", 25, 500), fill=CREAM + (int(220 * a),))
def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        tryl = (cur + " " + w_).strip()
        if d.textlength(tryl, font=f) > maxw and cur: lines.append(cur); cur = w_
        else: cur = tryl
    lines.append(cur); return lines
def testimony(d, t, q, who, src, t0, t1, mode="full"):
    """Zulu testimony card. full: centred over darkened picture. lower: band over action."""
    a = win(t, t0, t1, 0.45)
    if a <= 0.01: return 0.0
    if mode == "full":
        spaced(d, (W / 2, 250), "IN THEIR WORDS  ·  ZULU TESTIMONY", font("Cinzel.ttf", 25, 600), GOLD + (int(230 * a),), 6, "c")
        fq = font("Lora-Italic.ttf", 56, 500)
        lines = wrap(d, "“" + q + "”", fq, 1320)
        lh = 76; y0 = 470 - (len(lines) - 1) * lh / 2
        nwords = sum(len(l.split()) for l in lines); k = 0
        reveal = max(1.4, min(3.0, nwords * 0.09))
        for i, l in enumerate(lines):
            # word-by-word fade reveal
            ws = l.split(); x = W / 2 - d.textlength(l, font=fq) / 2
            for w_ in ws:
                wa = a * ramp(t, t0 + 0.2 + reveal * k / max(nwords, 1), t0 + 0.55 + reveal * k / max(nwords, 1))
                d.text((x, y0 + i * lh), w_, font=fq, fill=CREAM + (int(255 * wa),), anchor="lm")
                x += d.textlength(w_ + " ", font=fq); k += 1
        yb = y0 + len(lines) * lh + 10
        d.line((W / 2 - 70, yb, W / 2 + 70, yb), fill=GOLD + (int(220 * a),), width=2)
        spaced(d, (W / 2, yb + 30), who, font("Cinzel.ttf", 29, 600), CREAM + (int(240 * a),), 4, "c")
        fs = font("Lora-Italic.ttf", 26, 500)
        d.text((W / 2, yb + 96), src, font=fs, fill=GOLD + (int(235 * a),), anchor="mm")
        return a * 0.74
    else:
        fq = font("Lora-Italic.ttf", 46, 500)
        lines = wrap(d, "“" + q + "”", fq, 1500)
        y = 860 - (len(lines) - 1) * 60
        d.rectangle((0, y - 50, W, H), fill=(6, 8, 8, int(150 * a)))
        for i, l in enumerate(lines):
            d.text((W / 2, y + i * 60), l, font=fq, fill=CREAM + (int(255 * a),), anchor="mm")
        spaced(d, (W / 2, y + len(lines) * 60 + 2), who + "  ·  " + src, font("Cinzel.ttf", 22, 600), GOLD + (int(240 * a),), 3, "c")
        return a * 0.35

def smooth(pts, n=20):
    p = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = map(np.array, (p[i - 1], p[i], p[i + 1], p[i + 2]))
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(np.array(pts[-1])); return np.array(out)
def arrow(d, pts, col, frac, width=16, a=1.0, head=True, dash=False):
    if frac <= 0.005 or a <= 0.01: return
    p = smooth(pts); seg = np.linalg.norm(np.diff(p, axis=0), axis=1); L = seg.sum()
    cum = np.concatenate([[0], np.cumsum(seg)]); stop = L * min(frac, 1)
    k = np.searchsorted(cum, stop); q = list(map(tuple, p[:k]))
    if k < len(p) and k > 0:
        u = (stop - cum[k - 1]) / max(seg[k - 1], 1e-6); q.append(tuple(p[k - 1] + (p[k] - p[k - 1]) * u))
    if len(q) < 2: return
    al = int(255 * a)
    if dash:
        for i in range(0, len(q) - 1, 2): d.line([q[i], q[i + 1]], fill=col + (al,), width=width // 2)
        return
    d.line(q, fill=(20, 16, 10, int(170 * a)), width=width + 8, joint="curve")
    d.line(q, fill=col + (al,), width=width, joint="curve")
    if head:
        (x0, y0), (x1, y1) = q[-2] if len(q) > 2 else q[0], q[-1]
        ang = math.atan2(y1 - y0, x1 - x0); s = width * 2.0
        tri = [(x1 + math.cos(ang) * s * 0.9, y1 + math.sin(ang) * s * 0.9),
               (x1 + math.cos(ang + 2.4) * s, y1 + math.sin(ang + 2.4) * s),
               (x1 + math.cos(ang - 2.4) * s, y1 + math.sin(ang - 2.4) * s)]
        d.polygon(tri, fill=col + (al,), outline=(20, 16, 10, int(170 * a)))
def blob(d, xy, rx, ry, col, a=1.0):
    if a <= 0.01: return
    x, y = xy
    d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=col + (int(70 * a),), outline=col + (int(230 * a),), width=4)
def hill_mark(d, xy, a=1.0):
    x, y = xy
    d.polygon([(x, y - 20), (x - 18, y + 12), (x + 18, y + 12)], fill=CREAM + (int(235 * a),), outline=(20, 16, 10, int(200 * a)))
def tents(d, xy, a=1.0, n=14, spread=(70, 34)):
    rg = np.random.default_rng(7); x, y = xy
    for i in range(n):
        tx = x + rg.uniform(-spread[0], spread[0]); ty = y + rg.uniform(-spread[1], spread[1])
        d.polygon([(tx, ty - 7), (tx - 6, ty + 5), (tx + 6, ty + 5)], fill=(245, 240, 228, int(230 * a)), outline=(120, 40, 30, int(220 * a)))

# ---------------------------------------------------------------- places (lon, lat) — derived from the terrain model; schematic
PLACE = {
    "hill": (30.6513, -28.3530), "nek": (30.6514, -28.3561), "camp": (30.6562, -28.3536), "conical": (30.6745, -28.3530),
    "ngwebeni": (30.7450, -28.2950), "inyoni": (30.6700, -28.3405), "manz": (30.6385, -28.3480), "rorkes": (30.5370, -28.3510),
    "guns": (30.6615, -28.3500), "rockets": (30.6705, -28.3468),
}
FIRELINE = [(30.6585, -28.3448), (30.6625, -28.3478), (30.6648, -28.3530), (30.6650, -28.3590)]
CHEST_A = [(30.6655, -28.3395), (30.6668, -28.3428), (30.6676, -28.3462)]   # Umcityu
CHEST_B = [(30.6735, -28.3410), (30.6728, -28.3460), (30.6712, -28.3505)]   # Mbonambi
LEFT = [(30.7020, -28.3440), (30.6900, -28.3560), (30.6780, -28.3615), (30.6640, -28.3625), (30.6560, -28.3600)]
RIGHT = [(30.6620, -28.3360), (30.6480, -28.3395), (30.6400, -28.3455), (30.6395, -28.3530), (30.6470, -28.3575)]
ROAD = [(30.6562, -28.3536), (30.6514, -28.3561), (30.6420, -28.3605), (30.6300, -28.3640), (30.6000, -28.3600), (30.5650, -28.3560), (30.5370, -28.3510)]
PATROL = [(30.6800, -28.3360), (30.7000, -28.3240), (30.7200, -28.3100), (30.7330, -28.3020)]

# ---------------------------------------------------------------- shot renderers
def ov_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def compose(base, layer, dim=0.0):
    if dim > 0: base = base * (1 - dim)
    ov = np.asarray(layer).astype(np.float32); a = ov[..., 3:4] / 255
    return base * (1 - a) + ov[..., :3] * a

def render_shot(sh, t):
    """Returns float32 RGB frame for shot sh at local time t (may exceed duration during transitions)."""
    k = sh["k"]; L = ov_layer(); d = ImageDraw.Draw(L); dim = 0.0; dur = sh["dur"]
    if k == "flight":
        img, cam = flight_frame(sh["name"], t)
        img = grade(img, sh.get("grade", "none")) if sh.get("grade") else img
        for lab in sh.get("labels", []):
            name, lon, lat, lift, t0, col = lab[:6]
            t1 = lab[6] if len(lab) > 6 else 1e9
            p = T.project(*PL(lon, lat), cam, lift=lift)
            if p:
                a = min(ramp(t, t0, t0 + 0.6), 1 - ramp(t, t1 - 0.5, t1))
                d.line((p[0], p[1], p[0], p[1] - 46), fill=(20, 16, 10, int(200 * a)), width=4)
                d.line((p[0], p[1], p[0], p[1] - 46), fill=col + (int(230 * a),), width=2)
                pill(d, (p[0], p[1] - 70), name, font("Cinzel.ttf", 30, 600), fg=col, a=a)
        tag(d, sh.get("tag", "TERRAIN MODEL, HEIGHTS ×1.6  ·  SATELLITE IMAGE 2025  ·  TODAY'S LANDSCAPE"))
    elif k == "map":
        cam = map_cam(sh["cam"], t); img = map_frame(cam)
        sh["draw"](d, t, cam)
        tag(d, "TERRAIN MODEL + SATELLITE IMAGE 2025  ·  MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE")
    elif k == "oldmap":
        img = OLD.render(sh["name"], t, dur)
        tag(d, OLD.tag_for(sh["name"]))
        d.text((40, 1040), OLD.CREDITS[OLD.credit_key(sh["name"])], font=font("Lora.ttf", 18, 500), fill=CREAM + (165,), anchor="lm")
    elif k == "clip":
        img = clip_frame(sh["name"], t, sh.get("speed", 1.0), sh.get("start", 0.0), sh.get("punch", 1.0),
                         sh.get("cx", 0.5), sh.get("cy", 0.5), sh.get("drift", (0, 0, 0)), dur)
        gm = sh.get("grade", "midday")
        if gm == "eclipse": img = grade(img, "eclipse", ramp(t, sh.get("e0", 1.0), sh.get("e1", 5.0)))
        else: img = grade(img, gm)
        tag(d, "AI RECONSTRUCTION, ANIMATED  ·  ILLUSTRATIVE, NOT A RECORD")
    elif k == "arch":
        img = arch_frame(sh["name"], t, dur, *sh.get("kb", (1.0, 1.12, (0.5, 0.5), (0.5, 0.5))), frame_h=sh.get("fh", 880))
        if sh.get("cap"):
            a = ramp(t, 0.5, 1.1)
            f1 = font("Cinzel.ttf", 30, 600); f2 = font("Lora-Italic.ttf", 24, 500)
            spaced(d, (W / 2, 984), sh["cap"], f1, CREAM + (int(240 * a),), 4, "c")
            d.text((W / 2, 1040), sh["credit"], font=f2, fill=GOLD + (int(220 * a),), anchor="mm")
    else:
        img = np.zeros((H, W, 3), np.float32)
    # shot-level text
    for m in sh.get("marker", []):
        marker(d, m[0], win(t, m[1], m[2], 0.5))
    for o in sh.get("ost", []):
        ost(d, o[0], win(t, o[1], o[2], 0.4), o[3] if len(o) > 3 else None)
    for c in sh.get("cards", []):
        dim = max(dim, testimony(d, t, *c))
    if "title" in sh:
        ti = sh["title"]; a = win(t, ti[0], ti[1], 0.9)
        if a > 0.01:
            spaced(d, (W / 2, 330), "ORIGINEX HUMAN ARCHIVES", font("Cinzel.ttf", 30, 600), GOLD + (int(240 * a),), 8, "c")
            tl = ImageDraw.Draw(L)
            tl.text((W / 2 + 3, 523), "ISANDLWANA", font=font("Cinzel.ttf", 168, 700), fill=(10, 8, 6, int(170 * a)), anchor="mm")
            tl.text((W / 2, 520), "ISANDLWANA", font=font("Cinzel.ttf", 168, 700), fill=GOLD + (int(255 * a),), anchor="mm")
            spaced(d, (W / 2, 640), "22 JANUARY 1879", font("Cinzel.ttf", 46, 600), CREAM + (int(250 * a),), 10, "c")
            dim = max(dim, 0.25 * a)
    if k != "title": watermark(d)
    return compose(img, L, dim)

# ---------------------------------------------------------------- map drawers
def d_approach(d, t, cam):
    s = lambda k: to_scr(*PLACE[k], cam)
    f = font("Cinzel.ttf", 30, 600); fs = font("Cinzel.ttf", 25, 600)
    # distance line
    a = ramp(t, 0.8, 1.6)
    p0, p1 = s("ngwebeni"), s("camp")
    arrow(d, [p0, p1], CREAM, ramp(t, 0.8, 2.0), width=6, a=0.9 * a, head=False, dash=True)
    mid = ((p0[0] + p1[0]) / 2 + 40, (p0[1] + p1[1]) / 2 - 10)
    pill(d, mid, "ABOUT 11 KM  ·  7 MILES", fs, fg=CREAM, a=ramp(t, 1.6, 2.2), anchor="lm")
    blob(d, p0, 120, 62, ZULU, ramp(t, 0.2, 0.9))
    pill(d, (p0[0], p0[1] - 100), "THE ZULU ARMY", f, fg=ZULU, a=ramp(t, 0.3, 0.9))
    pill(d, (p0[0], p0[1] + 92), "NGWEBENI VALLEY", fs, fg=CREAM, a=ramp(t, 0.5, 1.1))
    hill_mark(d, s("hill"), ramp(t, 0.0, 0.5)); tents(d, s("camp"), ramp(t, 0.0, 0.5), n=10, spread=(30, 16))
    pill(d, (s("hill")[0] - 40, s("hill")[1] - 64), "ISANDLWANA", f, a=ramp(t, 0.0, 0.5))
    pill(d, (s("camp")[0] + 30, s("camp")[1] + 60), "BRITISH CAMP", fs, fg=BRIT, a=ramp(t, 0.2, 0.7), anchor="lm")
    pill(d, s("inyoni"), "iNYONI HEIGHTS", fs, a=ramp(t, 1.0, 1.6))
def d_patrol(d, t, cam):
    s = lambda k: to_scr(*PLACE[k], cam)
    f = font("Cinzel.ttf", 30, 600); fs = font("Cinzel.ttf", 25, 600)
    p0 = s("ngwebeni")
    blob(d, p0, 150, 76, ZULU, 1.0); pill(d, (p0[0] + 60, p0[1] + 110), "NGWEBENI VALLEY", fs)
    hill_mark(d, s("hill")); tents(d, s("camp"), n=12, spread=(40, 20))
    pill(d, (s("hill")[0] - 40, s("hill")[1] - 64), "ISANDLWANA", f)
    pts = [to_scr(*q, cam) for q in PATROL]
    arrow(d, pts, BRIT, ramp(t, 0.2, 2.4), width=12)
    pill(d, (pts[1][0] - 30, pts[1][1] + 60), "MOUNTED PATROL", fs, fg=BRIT, a=ramp(t, 0.6, 1.2))
    rg = np.random.default_rng(3)
    sc = (p0[0] - 150, p0[1] + 40)
    for i in range(9):
        x = sc[0] + rg.uniform(-40, 40); y = sc[1] + rg.uniform(-20, 20)
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=ZULU + (int(240 * ramp(t, 0.4, 0.9)),))
    pill(d, (sc[0] - 30, sc[1] - 60), "SCOUTS DRIVING CATTLE", fs, fg=ZULU, a=ramp(t, 0.8, 1.4), anchor="rm")
def d_fireline(d, t, cam):
    s = lambda k: to_scr(*PLACE[k], cam); sc = lambda pts: [to_scr(*q, cam) for q in pts]
    f = font("Cinzel.ttf", 30, 600); fs = font("Cinzel.ttf", 24, 600)
    hill_mark(d, s("hill")); tents(d, s("camp"), n=26, spread=(60, 70))
    pill(d, (s("hill")[0] - 150, s("hill")[1] - 20), "ISANDLWANA", f)
    pill(d, (s("camp")[0], s("camp")[1] + 120), "CAMP", fs, fg=BRIT)
    pill(d, (s("conical")[0], s("conical")[1] + 60), "CONICAL HILL", fs, a=ramp(t, 0.2, 0.8))
    pill(d, (s("inyoni")[0] - 60, s("inyoni")[1] - 50), "iNYONI HEIGHTS", fs, a=ramp(t, 0.2, 0.8))
    fl = sc(FIRELINE)
    arrow(d, fl, BRIT, ramp(t, 0.3, 1.3), width=12, head=False)
    pill(d, (fl[3][0] - 30, fl[3][1] - 10), "BRITISH FIRING LINE", fs, fg=BRIT, a=ramp(t, 0.9, 1.5), anchor="rm")
    g = s("guns"); a = ramp(t, 1.0, 1.5)
    for dx in (-12, 12):
        d.ellipse((g[0] + dx - 9, g[1] - 9, g[0] + dx + 9, g[1] + 9), fill=BRIT + (int(255 * a),), outline=(20, 16, 10, int(200 * a)), width=3)
    pill(d, (g[0] - 30, g[1] - 52), "TWO 7-POUNDERS", fs, fg=BRIT, a=a, anchor="rm")
    ca, cb = sc(CHEST_A), sc(CHEST_B)
    arrow(d, ca, ZULU, ramp(t, 1.4, 3.4) * 0.92, width=16)
    arrow(d, cb, ZULU, ramp(t, 1.8, 3.8) * 0.92, width=16)
    pill(d, (ca[0][0] - 20, ca[0][1] - 44), "UMCITYU (KANDAMPEMVU)", fs, fg=ZULU, a=ramp(t, 1.6, 2.2), anchor="rm")
    pill(d, (cb[0][0] + 20, cb[0][1] - 44), "MBONAMBI", fs, fg=ZULU, a=ramp(t, 2.0, 2.6), anchor="lm")
    # fire zone: the chest goes to ground
    a = ramp(t, 4.0, 4.8)
    if a > 0:
        for q in (ca[-1], cb[-1]):
            for k_ in range(7):
                x = q[0] - 60 + k_ * 20; d.line((x - 7, q[1] + 26 - 7, x + 7, q[1] + 26 + 7), fill=ZULU + (int(220 * a),), width=3)
        pill(d, ((ca[-1][0] + cb[-1][0]) / 2, ca[-1][1] + 80), "HELD AT A DISTANCE  ·  WENT TO GROUND", fs, fg=ZULU, a=a)
def d_horns(d, t, cam):
    s = lambda k: to_scr(*PLACE[k], cam); sc = lambda pts: [to_scr(*q, cam) for q in pts]
    f = font("Cinzel.ttf", 30, 600); fs = font("Cinzel.ttf", 24, 600)
    hill_mark(d, s("hill")); tents(d, s("camp"), n=22, spread=(36, 42))
    pill(d, (s("hill")[0] + 10, s("hill")[1] - 62), "ISANDLWANA", f)
    pill(d, (s("conical")[0] + 30, s("conical")[1] - 40), "CONICAL HILL", fs, anchor="lm")
    fl = sc(FIRELINE); arrow(d, fl, BRIT, 1.0, width=10, head=False, a=1 - 0.5 * ramp(t, 8.6, 10.5))
    ca, cb = sc(CHEST_A), sc(CHEST_B)
    arrow(d, ca, ZULU, 0.92 + 0.08 * ramp(t, 8.6, 10), width=16); arrow(d, cb, ZULU, 0.92 + 0.08 * ramp(t, 8.6, 10), width=16)
    # beat 1: left horn + rocket battery
    lp = sc(LEFT); arrow(d, lp, ZULU, ramp(t, 0.2, 3.0), width=18)
    pill(d, (lp[2][0] + 10, lp[2][1] + 56), "NGOBAMAKOSI  ·  LEFT HORN", fs, fg=ZULU, a=ramp(t, 0.5, 1.1))
    r = s("rockets"); a = ramp(t, 1.4, 1.9)
    if a > 0:
        d.line((r[0] - 14, r[1] - 14, r[0] + 14, r[1] + 14), fill=BRIT + (int(255 * a),), width=6)
        d.line((r[0] - 14, r[1] + 14, r[0] + 14, r[1] - 14), fill=BRIT + (int(255 * a),), width=6)
        pill(d, (r[0] + 24, r[1] - 36), "ROCKET BATTERY OVERRUN", fs, fg=BRIT, a=a, anchor="lm")
    # beat 2: right horn behind the hill
    rp = sc(RIGHT); arrow(d, rp, ZULU, ramp(t, 4.0, 7.2), width=18)
    pill(d, (rp[2][0] - 34, rp[2][1] - 6), "NOKENKE  ·  RIGHT HORN", fs, fg=ZULU, a=ramp(t, 4.3, 4.9), anchor="rm")
    m = s("manz"); pill(d, (m[0] - 40, m[1] + 80), "MANZIMNYAMA VALLEY", font("Lora-Italic.ttf", 26, 500), fg=CREAM, a=ramp(t, 4.8, 5.4), anchor="rm",
                        bg=(10, 14, 14, 120), sp=1)
    # beat 3: the nek closed
    road = sc(ROAD); a = ramp(t, 7.4, 8.0)
    arrow(d, road, BRIT, a, width=8, head=False, dash=True)
    n = s("nek")
    pill(d, (road[3][0], road[3][1] + 44), "ROAD TO RORKE'S DRIFT", fs, fg=BRIT, a=a)
    a2 = ramp(t, 8.4, 9.0)
    if a2 > 0:
        d.ellipse((n[0] - 26, n[1] - 26, n[0] + 26, n[1] + 26), outline=ZULU + (int(255 * a2),), width=6)
        pill(d, (n[0] - 40, n[1] + 66), "THE NEK  ·  CLOSED", f, fg=ZULU, a=a2, anchor="rm")

# ---------------------------------------------------------------- the two proofs
CRED_N01 = "Public domain  ·  Wikimedia Commons  ·  identification as given there, not independently confirmed"
OPENING = dict(name="opening", total=56.0, shots=[
    dict(k="oldmap", name="zoom_isa", start=0.0, dur=7.0, tin=("fade", 0.8),
         marker=[("22 JANUARY 1879  ·  MORNING", 0.6, 6.8)]),
    dict(k="oldmap", name="ngwebeni", start=7.0, dur=4.0, tin=("dissolve", 0.8)),
    dict(k="arch", name="N01", start=11.0, dur=6.5, tin=("dissolve", 0.6), kb=(1.0, 1.55, (0.5, 0.5), (0.57, 0.46)),
         cap="IDENTIFIED AS NTSHINGWAYO KAMAHOLE (SEATED)  ·  PHOTOGRAPH, c. 1879", credit=CRED_N01),
    dict(k="clip", name="Z33", start=17.5, dur=9.5, tin=("dissolve", 0.5), speed=0.53, grade="morning", punch=1.05, drift=(0.02, 0, 0.06),
         cards=[("At first we had not intended attacking the camp that day, as the moon was 'wrong'.",
                 "AN UMBONAMBI VETERAN, INTERVIEWED ON THE FIELD", "Bertram Mitford, Through the Zulu Country (1883), p. 93", 22.4 - 17.5, 27.2 - 17.5)]),
    dict(k="clip", name="Z15", start=27.0, dur=6.6, tin=("dissolve", 0.5), grade="midday", punch=1.06, drift=(0.0, 0, 0.07), speed=0.75,
         marker=[("AROUND MIDDAY  ·  TIMES APPROXIMATE", 0.3, 6.6)]),
    dict(k="clip", name="Z11", start=33.6, dur=2.3, tin=("cut", 0), grade="midday", punch=1.1, drift=(0, 0, 0.12)),
    dict(k="clip", name="Z16", start=35.9, dur=4.7, tin=("flash", 0.25), grade="midday", punch=1.08, drift=(0, -0.02, 0.08),
         cards=[("Then the whole impi became very excited and sprang up.", "AN UMBONAMBI VETERAN", "Mitford, 1883, p. 90", 0.4, 4.6, "lower")]),
    dict(k="clip", name="Z05", start=40.6, dur=3.8, tin=("cut", 0), grade="midday", punch=1.04),
    dict(k="clip", name="Z32", start=44.4, dur=2.8, tin=("cut", 0), grade="midday", punch=1.12, drift=(0, 0, 0.1), speed=0.8),
    dict(k="clip", name="Z01", start=46.6, dur=9.4, tin=("smoke", 0.9), grade="midday", speed=0.53, punch=1.02, drift=(0, 0, 0.08),
         title=(1.6, 9.0)),
], vo=[("a3_l02", 1.2), ("a2_l07", 11.4), ("vo/a3_l07_trim", 17.8), ("a4_l00", 27.2), ("a4_l01", 33.8), ("a4_l02", 40.8)],
   music=[("C03", 0.3, 35.0, 0.0, 3.0, 0.8), ("C05", 35.9, 56.0, 0.0, 0.05, 2.5)],
   sfx=lambda: [("wind", 0.0, 56.0), ("rush", 36.0, 11.0), ("volley_near", 35.85), ("sub", 49.1), ("whoosh", 46.3)],
   fade_out=(55.0, 56.0))

BATTLE = dict(name="battle", total=60.0, shots=[
    dict(k="oldmap", name="horns_open", start=0.0, dur=6.0, tin=("fade", 0.6)),
    dict(k="clip", name="Z19", start=6.0, dur=7.5, tin=("dissolve", 0.6), grade="battle", speed=0.68, punch=1.05, drift=(0.02, 0, 0.06),
         marker=[("MIDDAY TO EARLY AFTERNOON  ·  TIMES APPROXIMATE", 0.6, 7.4)]),
    dict(k="clip", name="Z18", start=13.5, dur=4.5, tin=("cut", 0), grade="battle", punch=1.05, drift=(0.02, 0, 0.05),
         cards=[("They kept tumbling over one upon another.", "AN UMBONAMBI VETERAN, ON THE BRITISH VOLLEYS", "Mitford, 1883, p. 90", 0.4, 4.4, "lower")]),
    dict(k="arch", name="N06", start=18.0, dur=3.8, tin=("dissolve", 0.5), kb=(1.05, 1.22, (0.45, 0.55), (0.55, 0.5)), fh=860,
         cap="A ZULU REGIMENT ATTACKING  ·  SKETCH BY C. E. FRIPP, c. 1879", credit="Public domain  ·  Wikimedia Commons"),
    dict(k="clip", name="Z20", start=21.8, dur=4.4, tin=("dissolve", 0.4), grade="battle", punch=1.06, drift=(0, 0, 0.06),
         ost=[("MKHOSANA KAMVUNDLANA", 0.8, 4.4, "named in later accounts; unnamed in the 1883 testimony")]),
    dict(k="clip", name="Z21", start=26.2, dur=6.0, tin=("cut", 0), grade="battle", speed=0.62, punch=1.05,
         cards=[("The chief was shot through the forehead and dropped down dead, but the Kandampemvu rushed over his body.",
                 "AN UMBONAMBI VETERAN, ON THE KANDAMPEMVU'S CHARGE", "Bertram Mitford, Through the Zulu Country (1883), p. 91", 0.6, 6.0)]),
    dict(k="oldmap", name="left_horn", start=32.2, dur=4.2, tin=("smoke", 0.7)),
    dict(k="oldmap", name="right_horn", start=36.4, dur=4.0, tin=("dissolve", 0.4)),
    dict(k="oldmap", name="closed", start=40.4, dur=4.4, tin=("dissolve", 0.4)),
    dict(k="clip", name="Z24", start=44.8, dur=3.8, tin=("cut", 0), grade="battle", punch=1.05, drift=(0, 0, 0.06),
         marker=[("EARLY AFTERNOON", 0.3, 3.8)]),
    dict(k="clip", name="Z22", start=48.6, dur=3.0, tin=("cut", 0), grade="battle", punch=1.08),
    dict(k="clip", name="Z23", start=51.6, dur=8.4, tin=("dissolve", 0.4), grade="eclipse", e0=0.2, e1=3.2, speed=0.58, punch=1.04, drift=(0, 0, 0.08),
         cards=[("The sun got very dark, like night, with the smoke. The English fought long and hard.",
                 "AN UMBONAMBI VETERAN", "Bertram Mitford, Through the Zulu Country (1883), p. 92  ·  original wording", 3.4, 8.2)],
         ost=[("PARTIAL ECLIPSE  ·  THAT AFTERNOON", 0.4, 3.2)]),
], vo=[("a5_l00", 0.8), ("a5_l01", 6.6), ("a5_l02", 18.4), ("a5_l04", 32.6), ("a5_l05", 36.6), ("a5_l06", 40.6), ("a5_l08", 45.0),
       ("v11/L44_trim", 51.9)],
   music=[("C05", 0.0, 51.8, 0.0, 1.5, 1.6)],
   sfx=lambda: [("wind", 0.0, 60.0), ("fire", 0.0, 51.0), ("cannon", 2.0), ("cannon", 4.8), ("cannon", 7.2), ("volley", 8.4),
                ("cannon", 9.6), ("volley", 11.0), ("volley_near", 13.6), ("volley_near", 15.9), ("cannon", 19.0),
                ("rush", 26.0, 6.5), ("volley", 27.5), ("whoosh", 31.9), ("volley", 33.5), ("cannon", 37.0), ("volley", 41.5),
                ("rush", 44.6, 7.0), ("volley_near", 45.2), ("volley", 48.8), ("drone", 51.4, 8.6)],
   fade_out=(59.4, 60.0))

# ---------------------------------------------------------------- picture render
def smoke_mask(t, u, seed=5):
    rg = np.random.default_rng(seed)
    n = cv2.resize(rg.random((9, 16)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.resize(rg.random((36, 64)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    xx = np.linspace(0, 1, W)[None, :]
    field = 0.55 * n + 0.25 * n2 + 0.2 * xx
    return np.clip((u * 1.4 - field) / 0.18 + 0.5, 0, 1)[..., None]

def frame_at(pf, t):
    shots = pf["shots"]
    cur = [s for s in shots if s["start"] <= t]
    sh = cur[-1]; i = shots.index(sh); lt = t - sh["start"]
    img = render_shot(sh, lt)
    kind, dd = sh["tin"]
    if dd > 0 and lt < dd:
        u = lt / dd
        if kind == "fade" and i == 0: img = img * ease(u)
        elif i > 0:
            prev = shots[i - 1]; pimg = render_shot(prev, t - prev["start"])
            if kind == "dissolve": img = pimg * (1 - ease(u)) + img * ease(u)
            elif kind == "smoke":
                m = smoke_mask(t, ease(u)); haze = np.array([92, 84, 74], np.float32)
                mid = 1 - abs(2 * u - 1)
                img = (pimg * (1 - m) + img * m) * (1 - 0.35 * mid) + haze * 0.35 * mid
            elif kind == "flash":
                img = img + (255 - img) * (1 - u) ** 2 * 0.85
    fo = pf.get("fade_out")
    if fo and t > fo[0]: img = img * (1 - ramp(t, fo[0], fo[1]))
    img = img * VIG
    gr = GRAIN[int(t * FPS) % 8]; gr = cv2.resize(gr, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    img = img + gr * 3.2
    return np.clip(img, 0, 255).astype(np.uint8)

def render_picture(pf, out, t0=0.0, t1=None):
    t1 = t1 or pf["total"]
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(n0, n1):
        p.stdin.write(frame_at(pf, fi / FPS).tobytes())
        if fi % 48 == 0: print(pf["name"], f"{fi / FPS:5.1f}s", flush=True)
    p.stdin.close(); p.wait()

# ---------------------------------------------------------------- audio
SR = 48000
def load_wav(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()
def lufs_gain(x, target):
    # quick K-weighted-free RMS proxy is adequate for bed balancing; final master uses loudnorm
    rms = np.sqrt(np.mean(x ** 2) + 1e-12); return 10 ** ((target - 20 * np.log10(rms)) / 20)
def place(buf, x, t, g=1.0):
    s = int(t * SR); e = min(len(buf), s + len(x))
    if e > s: buf[s:e] += x[: e - s] * g
def render_audio(pf, out_wav):
    N = int(pf["total"] * SR); vo = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32); fx = np.zeros((N, 2), np.float32)
    voice_mask = np.zeros(N, np.float32)
    for name, t in pf["vo"]:
        if name.startswith("vo/"): path = f"{HERE}/{name}.wav"
        elif name.startswith("v11/"): path = f"{S}/isa/build11/vowav11/{name[4:]}.wav"
        else: path = f"{VOW}/{name}.wav"
        x = load_wav(path); x = x * lufs_gain(x, -18.0)
        place(vo, x, t); s = int(t * SR); voice_mask[s:s + len(x)] = 1
    for cue, t0, t1, off, fi, fo in pf["music"]:
        x = load_wav(f"{MUS}/{cue}.mp3"); x = x[int(off * SR):]
        x = x * lufs_gain(x, -22.0)
        n = min(len(x), int((t1 - t0) * SR)); x = x[:n].copy()
        e = np.ones(n, np.float32)
        nfi, nfo = max(1, int(fi * SR)), max(1, int(fo * SR))
        e[:nfi] *= np.linspace(0, 1, nfi); e[-nfo:] *= np.linspace(1, 0, nfo)
        place(mus, x * e[:, None], t0)
    for ev in pf["sfx"]():
        kind, t = ev[0], ev[1]
        if kind == "wind": x = sfx.wind(ev[2]); g = 0.22
        elif kind == "fire": x = sfx.ragged_fire(ev[2], rate=5, dist=3.0); g = 0.16
        elif kind == "rush": x = sfx.rush(ev[2]); g = 0.30
        elif kind == "volley": x = sfx.volley(26, 0.5, 2.6); g = 0.30
        elif kind == "volley_near": x = sfx.volley(34, 0.35, 1.2, 1.4); g = 0.42
        elif kind == "cannon": x = sfx.cannon(1.8); g = 0.34
        elif kind == "whoosh": x = sfx.whoosh(1.1); g = 0.25
        elif kind == "sub": x = sfx.sub_hit(); g = 0.45
        elif kind == "drone": x = sfx.drone(ev[2]); g = 0.30
        place(fx, x, t, g)
    # duck music + sfx under voice (smoothed)
    k = int(0.25 * SR); vm = np.convolve(voice_mask, np.ones(k) / k, mode="same")
    duck_m = 10 ** (-9.0 * vm / 20); duck_f = 10 ** (-6.0 * vm / 20)
    mix = vo + mus * duck_m[:, None] + fx * duck_f[:, None]
    fo = pf.get("fade_out")
    if fo:
        a, b = int(fo[0] * SR), int(fo[1] * SR); env = np.ones(N, np.float32); env[a:b] = np.linspace(1, 0, b - a); env[b:] = 0
        mix *= env[:, None]
    pre = out_wav.replace(".wav", "_pre.wav")
    y = (np.clip(mix / max(1.0, np.abs(mix).max() / 0.95), -1, 1) * 32767).astype(np.int16)
    w = wave.open(pre, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes()); w.close()
    m = subprocess.run(["ffmpeg", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", af, "-ar", str(SR), out_wav], check=True)

if __name__ == "__main__":
    which = sys.argv[1]; pf = {"opening": OPENING, "battle": BATTLE}[which]
    os.makedirs(f"{HERE}/out", exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "still":
        for tt in map(float, sys.argv[3:]):
            cv2.imwrite(f"{HERE}/out/{which}_{tt:05.1f}.jpg", frame_at(pf, tt)[..., ::-1], [1, 88])
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[2] == "audio":
        render_audio(pf, f"{HERE}/out/{which}_mix.wav"); sys.exit()
    render_picture(pf, f"{HERE}/out/{which}_pic_r2.mp4")
    render_audio(pf, f"{HERE}/out/{which}_mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{HERE}/out/{which}_pic_r2.mp4", "-i", f"{HERE}/out/{which}_mix.wav",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", f"{HERE}/out/OGX_Isandlwana_v2_proof_{which}_r2.mp4"], check=True)
    print("done", which)
