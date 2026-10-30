"""OGX Nok renderer: a slice timing file -> MP4 segment.
  python3 tools/render.py slice build/slices/slice_03.json [--qa]
  python3 tools/render.py still <t> [<t> ...]          (preview JPEGs to build/preview/)
Every shot = FG/BG depth layers with independent travel (real parallax) + a camera move + one overlay.
--qa renders with overlays OFF so QA can prove the plates themselves move (overlays don't count as motion)."""
import json, sys, math, pathlib, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import layers

ROOT = pathlib.Path(__file__).resolve().parents[1]
W, H = 1920, 1080
FPS = 24

# Rule-breaking overlays from earlier builds. All OFF; this build has no drawing code for them, so turning one on
# fails loudly instead of quietly adding text to the picture (Lessons 27 Oct: config claims don't count).
BANNED_OVERLAYS = {"chapter_cards": False, "lower_thirds": False, "ai_label": False,
                   "subscribe_badge": False, "map_tags": False, "credit_pages": False}
for k, v in BANNED_OVERLAYS.items():
    if v: raise NotImplementedError(f"overlay '{k}' is banned by the Nok brief and is not implemented")

# Motion floors (Lessons 28-29 Oct): FG travel >= 3% of width, FG/BG >= 2.
FG_TRAVEL = 0.035          # of plate width per shot (FG-only parallax, on top of the shared camera)
FG_TRAVEL_REAL = 0.060     # photo panels over a blurred plate
BG_TRAVEL = 0.006
CAM_PAN = 0.012            # shared pan kept small so FG/BG stays >= 2 (QA 30 Oct: 0.035 gave ratios 1.2-1.9)
# Shots that measured under the floors in QA round 2 (flat/dark plates) get a stronger FG-only push.
FG_BOOST = {"L08": 1.6, "L20": 1.5, "L54": 1.5, "L24": 1.3}
BG_ZOOM_SHARE = 0.3        # BG takes 30 % of the camera's push/pull: a dolly, not a flat zoom
CAM = {"push": (1.00, 1.09, 0, 0), "pull": (1.09, 1.00, 0, 0), "pan_r": (1.05, 1.05, -1, 0),
       "pan_l": (1.05, 1.05, 1, 0), "push_l": (1.00, 1.08, 0.6, 0), "push_r": (1.00, 1.08, -0.6, 0),
       "pull_r": (1.08, 1.00, -0.6, 0), "tilt_up": (1.04, 1.04, 0, 1)}

GOLD, CREAM, GREEN = (92, 164, 201), (210, 230, 239), (33, 33, 21)     # BGR (house style)
FONT = ROOT / "assets/fonts"

def ease(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)

@functools.lru_cache(maxsize=None)
def font(name, size): return ImageFont.truetype(str(FONT / name), size)

# ---------- overlays (procedural, deterministic in t; no third-party footage) ----------
_rng = np.random.default_rng(1928)
_DUST = _rng.random((140, 5))            # x, y, size, speed, phase
_EMB = _rng.random((90, 5))
_RAIN = _rng.random((260, 3))
@functools.lru_cache(maxsize=1)
def _mist_tex():
    r = np.random.default_rng(7)
    t = sum(cv2.resize(r.random((4 * 2 ** k, 7 * 2 ** k)).astype(np.float32), (W * 2, H), interpolation=cv2.INTER_CUBIC) / 2 ** k for k in range(4))
    t = cv2.GaussianBlur(t, (0, 0), 25); return (t - t.min()) / np.ptp(t)

def overlay(frame, kind, t, strength=1.0):
    f = frame.astype(np.float32)
    if kind == "mist":
        tex = _mist_tex(); off = int((t * 18) % W)
        m = tex[:, off:off + W][..., None] * 0.20 * strength
        f = f * (1 - m) + 225 * m
    if kind in ("dust", "mist"):
        lay = np.zeros((H, W), np.float32)
        for x, y, s, sp, ph in _DUST:
            px = int(((x + 0.006 * t * (0.4 + sp)) % 1) * W); py = int(((y - 0.004 * t * sp + 0.01 * math.sin(t * 0.7 + ph * 6)) % 1) * H)
            cv2.circle(lay, (px, py), 1 + int(s * 2.5), 0.25 + 0.5 * s, -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 1.2)[..., None] * 0.55 * strength
        f = f + (255 - f) * lay
    if kind == "embers":
        lay = np.zeros((H, W, 3), np.float32)
        for x, y, s, sp, ph in _EMB:
            py = ((y - t * 0.05 * (0.5 + sp)) % 1) * H; px = (x + 0.02 * math.sin(t * 1.3 + ph * 9)) % 1 * W
            a = 0.5 + 0.5 * math.sin(t * 6 + ph * 20)
            cv2.circle(lay, (int(px), int(py)), 1 + int(s * 2), (40 * a, 140 * a, 255 * a), -1, cv2.LINE_AA)
        f = f + cv2.GaussianBlur(lay, (0, 0), 1.6) * 0.8 * strength
    if kind == "rain":
        lay = np.zeros((H, W), np.float32)
        for x, y, s in _RAIN:
            px = int(((x + t * 0.08) % 1) * W); py = int(((y + t * 1.1 * (0.8 + s)) % 1) * H)
            cv2.line(lay, (px, py), (px - 8, py + 34), 0.35 + 0.3 * s, 1, cv2.LINE_AA)
        f = f + (255 - f) * cv2.GaussianBlur(lay, (0, 0), 0.8)[..., None] * 0.35 * strength
    return np.clip(f, 0, 255).astype(np.uint8)

# ---------- layered plate with camera move + parallax ----------
def warp(img, scale, dx, dy, out=(W, H), border=cv2.BORDER_REFLECT101):
    h, w = img.shape[:2]
    M = np.float32([[scale, 0, out[0] / 2 - scale * (w / 2 + dx)], [0, scale, out[1] / 2 - scale * (h / 2 + dy)]])
    return cv2.warpAffine(img, M, out, flags=cv2.INTER_LINEAR, borderMode=border)

def cam_params(shot, u):
    s0, s1, px, py = CAM[shot["move"]]
    e = ease(u)
    scale = (s0 + (s1 - s0) * e) * (W / layers.PW) * 1.0
    return scale, e, px, py

@functools.lru_cache(maxsize=None)
def _guard(line, move, kind, h, slide=False, boost=None):
    """Smallest constant zoom (>= 1) that keeps both layers inside the plate for the whole shot. In v1.0 the
    frame at scale 1.0 showed the full plate width, so any FG shift smeared the replicated edge pixels."""
    PW = layers.PW; g = 1.0
    for u in np.linspace(0, 1, 49):
        e = ease(u); s0, s1, px, py = CAM[move]; sc = s0 + (s1 - s0) * e
        cam_x = px * CAM_PAN * PW * (e - 0.5)
        dirx = 1 if px >= 0 else -1
        if move in ("push", "pull") or py: dirx = 1 if line < "L32" else -1
        fg_dx = dirx * (FG_TRAVEL_REAL if kind == "real" else FG_TRAVEL) * (boost or FG_BOOST.get(line, 1.0)) * PW * (e - 0.5)
        bg_dx = dirx * BG_TRAVEL * PW * (e - 0.5)
        fg_sc = sc * (1 + 0.035 * (e - 0.5) * (1 if move != "pull" else -1)); sc_bg = 1 + (sc - 1) * BG_ZOOM_SHARE
        if slide: fg_sc = sc_bg = sc
        cam_y = py * 0.03 * h * (0.5 - e)
        for lsc, dx in ((fg_sc, cam_x + fg_dx), (sc_bg, cam_x + bg_dx)):
            need_x = 1 / max(1e-3, 1 - 2 * abs(dx) / PW); need_y = 1 / max(1e-3, 1 - 2 * abs(cam_y) / h)
            g = max(g, max(need_x, need_y) / lsc)
    return g * 1.004

def edge_guard(shot): return _guard(shot["line"], shot["move"], shot["kind"], layers.PH, bool(shot.get("slide")), shot.get("fg_boost"))

FLAT_PAN = 0.06            # v1.1 flat 2D shots: whole-still pan, % of plate width over the shot
FLAT_ZOOM = (1.07, 1.10)   # slow push under the pan; 1.07 leaves margin so the pan never reaches the plate edge

@functools.lru_cache(maxsize=4)
def _flat_plate(asset): return layers.cover(cv2.imread(str(ROOT / asset), cv2.IMREAD_COLOR), layers.PW, layers.PH)

def flat_frame(shot, u, want_mask=False):
    """v1.1 (QA 30 Oct): no depth split at all. One layer = the whole still, a 2D camera pan with a slow push.
    The mask is the whole frame (there is no background layer)."""
    img = _flat_plate(shot["asset"]); e = ease(u)
    dirx = -1 if shot["move"].endswith("_l") else 1
    sc = FLAT_ZOOM[0] + (FLAT_ZOOM[1] - FLAT_ZOOM[0]) * e
    out = warp(img, (W / layers.PW) * sc, dirx * FLAT_PAN * layers.PW * (e - 0.5), 0)
    return (out, np.ones((H, W), np.float32)) if want_mask else out

def plate_frame(shot, u, qa=False, want_mask=False):
    if shot.get("flat"): return flat_frame(shot, u, want_mask)
    L = layers.get(shot)
    bg, fg, a = L["bg"], L["fg"], L["alpha"].astype(np.float32)
    scale, e, px, py = cam_params(shot, u)
    base = W / layers.PW
    sc = scale / base
    # camera drift (shared) + parallax offsets (layer-specific), in plate pixels
    cam_x = px * CAM_PAN * layers.PW * (e - 0.5)
    tall = fg.shape[0] > layers.PH
    cam_y = (py * (fg.shape[0] - layers.PH / sc) * (0.5 - e) * 0.9) if tall else py * 0.03 * layers.PH * (0.5 - e)
    dirx = 1 if px >= 0 else -1
    if shot["move"] in ("push", "pull") or py: dirx = 1 if shot["line"] < "L32" else -1
    fg_dx = dirx * (FG_TRAVEL_REAL if shot["kind"] == "real" else FG_TRAVEL) * shot.get("fg_boost", FG_BOOST.get(shot["line"], 1.0)) * layers.PW * (e - 0.5)
    bg_dx = dirx * BG_TRAVEL * layers.PW * (e - 0.5)
    fg_sc = sc * (1 + 0.035 * (e - 0.5) * (1 if shot["move"] != "pull" else -1))   # FG also scales a touch faster
    sc_bg = 1 + (sc - 1) * BG_ZOOM_SHARE
    if shot.get("slide"):          # v1.1 seam fix: both layers share one zoom, parallax is sideways only, so a
        fg_sc = sc_bg = sc         # near-horizontal ground edge never opens a gap under the FG
    if shot.get("edge_guard"):     # v1.1: constant per-shot zoom so neither layer ever runs off the plate edge
        g = edge_guard(shot); fg_sc *= g; sc_bg *= g
    B = warp(bg, base * sc_bg, cam_x + bg_dx, cam_y)
    # replicate the FG edge outwards so a parallax shift never exposes an empty strip at the frame edge
    F = warp(fg, base * fg_sc, cam_x + fg_dx, cam_y, border=cv2.BORDER_REPLICATE)
    A = warp(a, base * fg_sc, cam_x + fg_dx, cam_y, border=cv2.BORDER_REPLICATE)[..., None]
    out = (B * (1 - A) + F * A).astype(np.uint8)
    return (out, A[..., 0]) if want_mask else out

# ---------- text-free graphics ----------
@functools.lru_cache(maxsize=1)
def _geo():
    gj = json.load(open(ROOT / "assets/geo/ne_50m_admin_0_countries.geojson"))
    polys, ng = [], []
    for f in gj["features"]:
        g = f["geometry"]; rings = g["coordinates"] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        if g["type"] == "Polygon": rings = [rings[0]]
        for r in rings:
            (ng if f["properties"]["ADMIN"] == "Nigeria" else polys).append(np.array(r))
    return polys, ng

def map_layers(u):
    """Africa -> central Nigeria. BG: sea + faint graticule (slow). FG: land + Nigeria glow (faster)."""
    polys, ng = _geo()
    e = ease(u)
    # view centre/zoom (lon, lat, px per degree): Africa wide -> Nigeria
    c0, c1 = (17.0, 3.0, 13.0), (8.2, 9.0, 70.0)
    lon = c0[0] + (c1[0] - c0[0]) * e; lat = c0[1] + (c1[1] - c0[1]) * e; k = c0[2] * (c1[2] / c0[2]) ** e
    def P(arr, kk, dx=0.0):
        return np.stack([(arr[:, 0] - lon) * kk + W / 2 + dx, (lat - arr[:, 1]) * kk + H / 2], 1).astype(np.int32)
    bg = np.zeros((H, W, 3), np.uint8); bg[:] = (40, 30, 18)
    kb = k * 0.985
    for g in range(-40, 61, 10):
        x = int((g - lon) * kb + W / 2 - 0.01 * W * (e - 0.5)); cv2.line(bg, (x, 0), (x, H), (60, 48, 30), 1, cv2.LINE_AA)
        y = int((lat - g) * kb + H / 2); cv2.line(bg, (0, y), (W, y), (60, 48, 30), 1, cv2.LINE_AA)
    fg = np.zeros((H, W, 3), np.uint8); a = np.zeros((H, W), np.float32)
    dx = -0.045 * W * (e - 0.5)
    for r in polys:
        p = P(r, k, dx); cv2.fillPoly(fg, [p], (52, 70, 62), cv2.LINE_AA); cv2.fillPoly(a, [p], 1.0, cv2.LINE_AA)
        cv2.polylines(fg, [p], True, (80, 100, 92), 1, cv2.LINE_AA)
    glow = min(1.0, max(0.0, (u - 0.35) / 0.4))
    for r in ng:
        p = P(r, k, dx)
        col = tuple(int(c0_ + (c1_ - c0_) * glow) for c0_, c1_ in zip((52, 70, 62), (70, 140, 175)))
        cv2.fillPoly(fg, [p], col, cv2.LINE_AA); cv2.fillPoly(a, [p], 1.0, cv2.LINE_AA)
        cv2.polylines(fg, [p], True, GOLD, 2, cv2.LINE_AA)
    if glow > 0:   # soft pulse over the middle of Nigeria ("central Nigeria"; no exact find-spot)
        cx, cy = P(np.array([[8.2, 9.3]]), k, dx)[0]
        pul = np.zeros((H, W), np.float32)
        cv2.circle(pul, (int(cx), int(cy)), int(18 + 10 * math.sin(u * 12)), 1.0, -1, cv2.LINE_AA)
        pul = cv2.GaussianBlur(pul, (0, 0), 14)[..., None] * glow
        fg = np.clip(fg + pul * np.array(GOLD) * 1.6, 0, 255).astype(np.uint8)
    A = cv2.GaussianBlur(a, (0, 0), 1)[..., None]
    return (bg * (1 - A) + fg * A).astype(np.uint8), A[..., 0]

@functools.lru_cache(maxsize=1)
def _grain():
    """Soft procedural paper/terrain grain (2W x 2H), used on graphics so their layers carry visible texture."""
    r = np.random.default_rng(1500)
    t = sum(cv2.resize(r.random((9 * 2 ** k, 16 * 2 ** k)).astype(np.float32), (2 * W, 2 * H), interpolation=cv2.INTER_CUBIC) / 2 ** k
            for k in range(5))
    t = cv2.GaussianBlur(t, (0, 0), 2.0); return ((t - t.min()) / np.ptp(t) - 0.5).astype(np.float32)

def grain_layer(scale, dx, dy):
    return warp(_grain(), scale, dx, dy)[..., None]

CHRONO_X0, CHRONO_X1 = -1600, 700        # years (negative = BC)
def yx(y, dx): return int(180 + (y - CHRONO_X0) / (CHRONO_X1 - CHRONO_X0) * (W - 360) + dx)

def chrono_layers(stage, u):
    """Text-free chronology. Bar A (Britannica, c. 500 BCE-200 CE) above; bar B (Frankfurt) below:
    early from c. 1500 BC, main 9th-4th c. BC (bright), end around the turn of the era. 800 BC tick for iron."""
    e = ease(u)
    bdx = -0.03 * W * (e - 0.5); fdx = -0.10 * W * (e - 0.5) * (1.3 if stage == "A" else 1.0)
    bg = np.zeros((H, W, 3), np.uint8); bg[:] = GREEN
    bg = np.clip(bg + grain_layer(1.0 + 0.03 * e, -bdx, 0) * 40, 0, 255).astype(np.uint8)
    for gx in range(-200, W + 200, 64):          # BG: faint dot field, slow layer (no data on it)
        for gy in range(40, H, 64):
            cv2.circle(bg, (int(gx + bdx), gy), 1, (48, 60, 60), -1, cv2.LINE_AA)
    fg = np.zeros((H, W, 3), np.uint8); a = np.zeros((H, W), np.float32)
    def ln(p0, p1, col, th):
        cv2.line(fg, p0, p1, col, th, cv2.LINE_AA); cv2.line(a, p0, p1, 1.0, th, cv2.LINE_AA)
    for yr in range(-1600, 701, 100):            # FG: axis, century ticks and era line move WITH the bars
        x = yx(yr, fdx); hgt = 26 if yr % 500 == 0 else 12
        ln((x, 760 - hgt), (x, 760 + hgt), (95, 120, 125), 2 if yr == 0 else 1)
    ln((yx(CHRONO_X0, fdx), 760), (yx(CHRONO_X1, fdx), 760), (95, 120, 125), 2)
    ln((yx(0, fdx), 330), (yx(0, fdx), 790), (85, 105, 110), 1)
    def bar(y0, y1, row, col, grow=1.0, h=60):
        x0 = yx(y0, fdx); x1 = x0 + int((yx(y1, fdx) - x0) * grow)
        if x1 > x0:
            cv2.rectangle(fg, (x0, row - h // 2), (x1, row + h // 2), col, -1, cv2.LINE_AA)
            cv2.rectangle(a, (x0, row - h // 2), (x1, row + h // 2), 1.0, -1, cv2.LINE_AA)
    A_COL, A_DIM = (190, 205, 215), (110, 120, 125)
    E_COL, M_COL, L_COL = (60, 110, 135), GOLD, (60, 110, 135)
    order = ["A", "B_start", "B_main", "B_end", "B_iron"]; si = order.index(stage)
    bar(-500, 200, 420, A_COL if si == 0 else A_DIM, e if si == 0 else 1.0)
    if si >= 1: bar(-1500, -900, 600, E_COL, e if si == 1 else 1.0)
    if si >= 2: bar(-900, -400, 600, M_COL, e if si == 2 else 1.0)
    if si >= 3: bar(-400, 0, 600, L_COL, e if si == 3 else 1.0)
    if si >= 4:   # iron by about 800 BC cannot yet be confirmed: a dotted, pulsing outline, never a solid mark
        x = yx(-800, fdx); r = 30 + int(4 * math.sin(u * 10))
        for ang in range(0, 360, 24):
            p = (int(x + r * math.cos(math.radians(ang))), int(600 + r * math.sin(math.radians(ang))))
            cv2.circle(fg, p, 4, CREAM, -1, cv2.LINE_AA); cv2.circle(a, p, 4, 1.0, -1, cv2.LINE_AA)
    z = 1.0 + 0.12 * e                                    # FG pushes in while the BG barely moves
    fg = warp(fg, z, 0, 0, border=cv2.BORDER_CONSTANT); a = warp(a, z, 0, 0, border=cv2.BORDER_CONSTANT)
    fg = np.clip(fg + grain_layer(z, -fdx / z, 0) * 40 * (a[..., None] > 0), 0, 255).astype(np.uint8)
    A = cv2.GaussianBlur(a, (0, 0), 1)[..., None]
    return (bg * (1 - A) + fg * A).astype(np.uint8), A[..., 0]

def gfx_frame(shot, u, want_mask=False):
    out, m = map_layers(u) if shot["gfx"] == "map" else chrono_layers(shot["gfx_opts"]["stage"], u)
    return (out, m) if want_mask else out

# ---------- text: the one allowed credit line, and the one end card ----------
def credit(frame, text):
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, "RGBA")
    f = font("Lora[wght].ttf", 24); tw = d.textlength(text, font=f); pad = 14
    x, y = 60, H - 60 - (24 + 2 * pad)
    d.rounded_rectangle((x, y, x + tw + 2 * pad, y + 24 + 2 * pad), 6, fill=(10, 14, 14, 175))
    d.text((x + pad, y + pad - 2), text, font=f, fill=(239, 230, 210, 255))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

def name_sub(frame, text, k):
    """Small name subtitle (producer rule 30 Oct): only for names the VO doesn't carry clearly. No box."""
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(im, "RGBA")
    f = font("Lora-Italic[wght].ttf", 34); tw = d.textlength(text, font=f); x, y = (W - tw) / 2, H - 132
    a = int(255 * k)
    for ox, oy in ((2, 2), (0, 2), (2, 0)): d.text((x + ox, y + oy), text, font=f, fill=(0, 0, 0, int(a * 0.6)))
    d.text((x, y), text, font=f, fill=(239, 230, 210, a))
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

def end_card(u):
    e = ease(u)
    im = Image.new("RGB", (W, H), (21, 33, 33)); d = ImageDraw.Draw(im)
    f = font("Cinzel[wght].ttf", 54); txt = "ORIGINEX HUMAN ARCHIVES"
    spaced = " ".join(txt)  # letter-spaced kicker
    tw = d.textlength(spaced, font=f); d.text(((W - tw) / 2, 470), spaced, font=f, fill=(201, 164, 92))
    rw = int(260 + 140 * e); d.line(((W - rw) / 2, 560, (W + rw) / 2, 560), fill=(201, 164, 92), width=2)
    fr = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    return warp(fr, 1.0 + 0.04 * e, 0, 0)

# ---------- timeline ----------
import os
FILM = json.load(open(ROOT / os.environ.get("OGX_SHOTS", "build/shots.json")))   # v1.1: OGX_SHOTS=build/v1.1/shots.json
XF = FILM["xfade"]

def shot_frame(s, t, qa=False, want_mask=False):
    u = (t - (s["t0"] - XF / 2)) / ((s["t1"] + XF / 2) - (s["t0"] - XF / 2))
    if s["kind"] == "gfx":
        out = gfx_frame(s, u, want_mask)
    else:
        out = plate_frame(s, u, qa, want_mask)
    fr, m = out if want_mask else (out, None)
    if not qa: fr = overlay(fr, s["overlay"], t, 0.6 if s["kind"] == "real" else 1.0)
    return (fr, m) if want_mask else fr

def frame_at(t, shots, qa=False):
    ec = FILM["end_card"]
    if t >= ec["t0"] + XF / 2:
        fr = end_card((t - ec["t0"]) / (ec["t1"] - ec["t0"]))
        return fr if qa else overlay(fr, "dust", t, 0.5)
    i = max(j for j, s in enumerate(shots) if s["t0"] - 1e-6 <= t or j == 0)
    s = shots[i]
    fr = shot_frame(s, t, qa)
    if s["credit"]: fr = credit(fr, s["credit"])
    nm = s.get("name")
    if nm and nm["t0"] <= t <= nm["t1"]:
        fr = name_sub(fr, nm["text"], min(1.0, (t - nm["t0"]) / 0.25, (nm["t1"] - t) / 0.25))
    # dissolve: previous shot fades out over the first XF/2 s, next one over the last XF/2 s
    if i > 0 and t < s["t0"] + XF / 2:
        p = shots[i - 1]; pf = shot_frame(p, t, qa)
        if p["credit"]: pf = credit(pf, p["credit"])
        k = ease((t - (s["t0"] - XF / 2)) / XF); fr = cv2.addWeighted(pf, 1 - k, fr, k, 0)
    if s is shots[-1] and t > ec["t0"] - XF / 2:
        k = ease((t - (ec["t0"] - XF / 2)) / XF)
        fr = cv2.addWeighted(fr, 1 - k, end_card(0) if qa else overlay(end_card(0), "dust", t, 0.5), k, 0)
    return fr

def render_slice(path, qa=False):
    sl = json.load(open(path))
    shots = sl["shots"]                     # only this slice's shots (+ dissolve neighbours)
    out = pathlib.Path(sl["out_qa" if qa else "out"]); out.parent.mkdir(parents=True, exist_ok=True)
    w, h = (960, 540) if qa else (W, H)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18" if not qa else "23",
                          "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for f in range(sl["f0"], sl["f1"]):
        fr = frame_at(f / FPS, shots, qa)
        if qa: fr = cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    print(f"ok {out} frames {sl['f0']}-{sl['f1']}")

if __name__ == "__main__":
    if sys.argv[1] == "slice":
        render_slice(sys.argv[2], qa="--qa" in sys.argv)
    elif sys.argv[1] == "still":
        (ROOT / "build/preview").mkdir(parents=True, exist_ok=True)
        for t in map(float, sys.argv[2:]):
            cv2.imwrite(str(ROOT / f"build/preview/t{t:07.2f}.jpg"), frame_at(t, FILM["shots"]), [cv2.IMWRITE_JPEG_QUALITY, 88])
