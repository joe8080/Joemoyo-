"""OGX motion engine (rebuilt 31 Oct 2026 for ogx-ishango-1).

The Nok engine code was not reachable from this session, so this is a compact rebuild
from the Night Build Lessons (L1-L37) and the Nok motion settings (L33):
  * true 2.5D: separate FG (matted subject) and BG (inpainted plate) layers
  * smaller shared pan, BG dolly share 0.3, parallax on the FG only
  * motion floors on by default (FG travel >= 3 % of frame width, FG/BG >= 2)
  * moving texture overlays (dust, haze, grain) never count as motion
  * every banned overlay sits behind a flag that defaults OFF (L1, L4)
  * AI label ON (Chief ruling, 31 Oct), one credit line per real image (L20-L22)
Each shot also writes a matte video (FG alpha as rendered) so QA can measure parallax
from rendered pixels instead of trusting this config (L4).
"""
import json
import math
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 25

# --- Overlay flags (L1/L4). Banned overlays default OFF and refuse to render. ---
FLAGS = {
    "chapter_cards": False,
    "lower_third_boxes": False,
    "source_cards": False,
    "subscribe_badge": False,
    "map_tags": False,
    "credit_pages": False,
    # allowed text
    "ai_label": True,           # Chief ruling 1, 31 Oct 2026
    "credit_lines": True,       # one short line per real image (L20-L22)
    "name_subtitles": True,     # L25
}
BANNED = ["chapter_cards", "lower_third_boxes", "source_cards", "subscribe_badge",
          "map_tags", "credit_pages"]

AI_LABEL_TEXT = "Reconstruction (AI)"

# Nok starting settings (L33), as fractions of frame width.
MOTION = {
    "shared_pan": 0.012,        # small shared camera pan
    "bg_dolly_share": 0.3,      # BG gets 30 % of the camera dolly
    "fg_parallax": 0.032,       # extra FG-only travel
    "zoom": 0.06,               # camera push over the shot
    "min_fg_travel_pct": 3.0,   # floor (L9)
    "min_fg_bg_ratio": 2.0,     # floor (L16)
}

FONT_DIR = "/usr/share/fonts/opentype/inter"
F_LABEL = os.path.join(FONT_DIR, "Inter-Medium.otf")
F_SUB = os.path.join(FONT_DIR, "Inter-SemiBold.otf")
F_TITLE = os.path.join(FONT_DIR, "InterDisplay-Light.otf")


def check_flags():
    on = [k for k in BANNED if FLAGS.get(k)]
    if on:
        raise SystemExit(f"Banned overlay flag(s) switched on: {on}. Refusing to render.")


def font(path, size):
    if not os.path.exists(path):
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def ease(x):
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- layers

def cover(img, w, h):
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    nw, nh = int(math.ceil(iw * s)), int(math.ceil(ih * s))
    r = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
    x0, y0 = (nw - w) // 2, (nh - h) // 2
    return r[y0:y0 + h, x0:x0 + w]


def matte_subject(rgb):
    """FG alpha via rembg (isnet-general-use). Returns float32 0..1."""
    from rembg import new_session, remove
    global _SESSION
    try:
        _SESSION
    except NameError:
        _SESSION = new_session("isnet-general-use")
    pil = Image.fromarray(rgb)
    small = pil.copy()
    small.thumbnail((1600, 1600))
    a = remove(small, session=_SESSION, only_mask=True)
    a = np.array(a.resize(pil.size, Image.BILINEAR)).astype(np.float32) / 255.0
    return a


def matte_ground(rgb, split=0.58, soft=0.18):
    """For landscapes: FG = lower ground plane, BG = sky/distance, soft horizon blend."""
    h = rgb.shape[0]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    a = np.clip((y - (split - soft / 2)) / soft, 0, 1)
    return np.repeat(a, rgb.shape[1], axis=1)


def build_layers(rgb, mode):
    if mode == "subject":
        a = matte_subject(rgb)
        if a.mean() < 0.02 or a.mean() > 0.85:   # matting failed -> ground split
            a = matte_ground(rgb)
            mode = "ground"
    else:
        a = matte_ground(rgb)
    # BG plate: inpaint the FG so revealed areas are plausible (avoid seam smears, L34)
    if mode == "subject":
        m = (a > 0.15).astype(np.uint8) * 255
        m = cv2.dilate(m, np.ones((25, 25), np.uint8))
        sm = cv2.resize(m, (rgb.shape[1] // 2, rgb.shape[0] // 2))
        srgb = cv2.resize(rgb, (rgb.shape[1] // 2, rgb.shape[0] // 2))
        inp = cv2.inpaint(srgb, sm, 9, cv2.INPAINT_TELEA)
        inp = cv2.resize(inp, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
        blur = cv2.GaussianBlur(inp, (0, 0), 6)
        mf = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 12)[..., None]
        bg = (rgb * (1 - mf) + blur * mf).astype(np.uint8)
    else:
        bg = rgb.copy()
    a = cv2.GaussianBlur(a, (0, 0), 1.5)
    return bg, a, mode


# ---------------------------------------------------------------- overlays (texture only)

class Overlays:
    def __init__(self, kinds, n, seed):
        self.kinds = kinds or []
        rng = np.random.default_rng(seed)
        self.p = rng.random((140, 4)).astype(np.float32)       # x, y, size, speed
        self.n = n
        g = rng.normal(0, 1, (H // 8, W // 8)).astype(np.float32)
        self.haze = cv2.resize(cv2.GaussianBlur(g, (0, 0), 6), (W * 2, H), interpolation=cv2.INTER_CUBIC)
        self.haze = (self.haze - self.haze.min()) / (np.ptp(self.haze) + 1e-6)
        self.rng = rng

    def apply(self, frame, i):
        f = frame.astype(np.float32)
        t = i / max(1, self.n - 1)
        if "haze" in self.kinds:
            off = int(t * W * 0.25)
            hz = self.haze[:, off:off + W][..., None]
            f = f * (1 - 0.10 * hz) + 235 * 0.10 * hz
        if "dust" in self.kinds:
            layer = np.zeros((H, W), np.float32)
            for x, y, s, v in self.p:
                px = int(((x + 0.05 * v * t) % 1) * W)
                py = int(((y - 0.08 * v * t + 0.01 * math.sin(6 * t + x * 9)) % 1) * H)
                cv2.circle(layer, (px, py), 1 + int(s * 2.5), 1.0, -1, cv2.LINE_AA)
            layer = cv2.GaussianBlur(layer, (0, 0), 1.2)[..., None]
            f = f * (1 - 0.35 * layer) + 245 * 0.35 * layer
        if "embers" in self.kinds:
            layer = np.zeros((H, W), np.float32)
            for x, y, s, v in self.p[:50]:
                px = int(((x + 0.03 * math.sin(4 * t + y * 7)) % 1) * W)
                py = int(((y - 0.25 * v * t) % 1) * H)
                cv2.circle(layer, (px, py), 1 + int(s * 2), 1.0, -1, cv2.LINE_AA)
            layer = cv2.GaussianBlur(layer, (0, 0), 1.6)[..., None]
            f = f + layer * np.array([255, 150, 60], np.float32) * 0.55
        # film grain, always
        grain = self.rng.normal(0, 3.2, (H // 2, W // 2)).astype(np.float32)
        grain = cv2.resize(grain, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        f = f + grain
        return np.clip(f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- text (allowed only)

def draw_text_layers(frame, spec, tsec, dur):
    img = Image.fromarray(frame)
    d = ImageDraw.Draw(img, "RGBA")
    if spec.get("ai") and FLAGS["ai_label"]:
        f = font(F_LABEL, 26)
        txt = AI_LABEL_TEXT
        tw = d.textlength(txt, font=f)
        x, y = W - tw - 46, 38
        d.rounded_rectangle([x - 12, y - 6, x + tw + 12, y + 34], 8, fill=(0, 0, 0, 110))
        d.text((x, y), txt, font=f, fill=(255, 255, 255, 225))
    if spec.get("credit") and FLAGS["credit_lines"]:
        f = font(F_LABEL, 24)
        txt = spec["credit"]
        x, y = 46, H - 62
        tw = d.textlength(txt, font=f)
        d.rounded_rectangle([x - 12, y - 6, x + tw + 12, y + 32], 8, fill=(0, 0, 0, 120))
        d.text((x, y), txt, font=f, fill=(255, 255, 255, 230))
    sub = spec.get("subtitle")
    if sub and FLAGS["name_subtitles"]:
        s0, s1 = sub.get("start", 0.0), sub.get("end", min(dur, 3.5))
        if s0 <= tsec <= s1:
            a = min(1, (tsec - s0) / 0.3, (s1 - tsec) / 0.3)
            f = font(F_SUB, 40)
            txt = sub["text"]
            tw = d.textlength(txt, font=f)
            x, y = (W - tw) / 2, H - 150
            d.text((x + 2, y + 2), txt, font=f, fill=(0, 0, 0, int(170 * a)))
            d.text((x, y), txt, font=f, fill=(255, 255, 255, int(255 * a)))
    return np.array(img)


# ---------------------------------------------------------------- shot render

def ffmpeg_writer(path, gray=False):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt",
           "gray" if gray else "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17" if not gray else "24",
           "-pix_fmt", "yuv420p", path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def affine(scale, dx, dy):
    # scale about frame centre, then translate (pixels)
    cx, cy = W / 2, H / 2
    return np.float32([[scale, 0, cx - scale * cx + dx], [0, scale, cy - scale * cy + dy]])


def render_card(spec, out, matte_out):
    """Minimal title / end card (allowed): slow drift on a dark textured ground."""
    n = int(round(spec["dur"] * FPS))
    wr, mw = ffmpeg_writer(out), ffmpeg_writer(matte_out, gray=True)
    rng = np.random.default_rng(7)
    g = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (H // 6, W // 6)).astype(np.float32), (0, 0), 4),
                   (int(W * 1.2), int(H * 1.2)), interpolation=cv2.INTER_CUBIC)
    g = (g - g.min()) / (np.ptp(g) + 1e-6)
    base = np.stack([14 + 18 * g, 12 + 14 * g, 10 + 10 * g], -1).astype(np.uint8)
    ov = Overlays(["dust"], n, 3)
    ft = font(F_TITLE, 74)
    fs = font(F_LABEL, 30)
    for i in range(n):
        t = ease(i / max(1, n - 1))
        M = affine(1.0 + 0.04 * t, -40 * t, 0)
        bg = cv2.warpAffine(base, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        fr = ov.apply(bg, i)
        img = Image.fromarray(fr)
        d = ImageDraw.Draw(img, "RGBA")
        a = int(255 * min(1, i / 12, (n - 1 - i) / 12))
        lines = spec["card_lines"]
        y = H / 2 - 50 if len(lines) > 1 else H / 2 - 40
        for k, ln in enumerate(lines):
            f = ft if k == 0 else fs
            tw = d.textlength(ln, font=f)
            d.text(((W - tw) / 2 + 30 * (1 - t) * (1 if k == 0 else -1), y), ln, font=f,
                   fill=(240, 232, 220, a if k == 0 else int(a * 0.8)))
            y += 100
        wr.stdin.write(np.array(img).tobytes())
        mw.stdin.write(np.zeros((H, W), np.uint8).tobytes())
    for p in (wr, mw):
        p.stdin.close()
        p.wait()
    return {"id": spec["id"], "frames": n, "mode": "card"}


def render_map(spec, out, matte_out, assets_dir):
    """Animated locator on a real (PD) satellite image: push in toward the site, plain ring marker,
    no text (map tags stay banned). A flat image has no depth, so the motion floor is logged as a
    documented override (L9) rather than faked parallax."""
    n = int(round(spec["dur"] * FPS))
    src = cv2.cvtColor(cv2.imread(os.path.join(assets_dir, spec["image"])), cv2.COLOR_BGR2RGB)
    src = cv2.resize(src, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    src = cv2.convertScaleAbs(src, alpha=1.08, beta=-6)
    ih, iw = src.shape[:2]
    tx, ty = spec["target"]
    z0, z1 = spec.get("zoom_from", 1.0), spec.get("zoom_to", 2.2)
    base = max(W / iw, H / ih)
    ov = Overlays(spec.get("overlays", ["haze"]), n, 11)
    wr, mw = ffmpeg_writer(out), ffmpeg_writer(matte_out, gray=True)
    for i in range(n):
        t = ease(i / max(1, n - 1))
        z = base * (z0 + (z1 - z0) * t)
        cx = iw * (0.5 + (tx - 0.5) * t)
        cy = ih * (0.5 + (ty - 0.5) * t)
        M = np.float32([[z, 0, W / 2 - z * cx], [0, z, H / 2 - z * cy]])
        fr = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if t > 0.35:
            k = min(1.0, (t - 0.35) / 0.2)
            mx, my = int(z * iw * tx + M[0, 2]), int(z * ih * ty + M[1, 2])
            pulse = 0.5 + 0.5 * math.sin(i / FPS * 4.0)
            ring = np.zeros((H, W), np.float32)
            cv2.circle(ring, (mx, my), int(18 + 10 * pulse), 1.0, 3, cv2.LINE_AA)
            cv2.circle(ring, (mx, my), 6, 1.0, -1, cv2.LINE_AA)
            ring = cv2.GaussianBlur(ring, (0, 0), 1.2)[..., None] * k
            fr = np.clip(fr * (1 - ring) + np.array([255, 196, 90], np.float32) * ring, 0, 255).astype(np.uint8)
        fr = ov.apply(fr, i)
        fr = draw_text_layers(fr, spec, i / FPS, spec["dur"])
        wr.stdin.write(fr.tobytes())
        mw.stdin.write(np.full((H, W), 255, np.uint8).tobytes())
    for p in (wr, mw):
        p.stdin.close()
        p.wait()
    return {"id": spec["id"], "frames": n, "mode": "map"}


def render_shot(spec, out, matte_out, assets_dir):
    if spec["type"] in ("TITLE", "END"):
        return render_card(spec, out, matte_out)
    if spec["type"] == "MAP":
        return render_map(spec, out, matte_out, assets_dir)
    n = int(round(spec["dur"] * FPS))
    src = cv2.cvtColor(cv2.imread(os.path.join(assets_dir, spec["image"])), cv2.COLOR_BGR2RGB)
    over = 1.18
    if spec["type"] in ("REAL", "SCH"):
        # portrait/small real images: blurred cover background + contained subject plate
        bsrc = src
        if spec.get("bg_image"):
            bsrc = cv2.cvtColor(cv2.imread(os.path.join(assets_dir, spec["bg_image"])), cv2.COLOR_BGR2RGB)
        bgc = cover(bsrc, int(W * over), int(H * over))
        bgc = cv2.GaussianBlur(bgc, (0, 0), 28)
        bgc = (bgc.astype(np.float32) * spec.get("bg_dim", 0.45)).astype(np.uint8)
        ih, iw = src.shape[:2]
        target_h = int(H * spec.get("fit", 0.86))
        s = min(target_h / ih, int(W * 0.86) / iw)
        interp = cv2.INTER_NEAREST if spec["type"] == "SCH" and s > 3 else cv2.INTER_LANCZOS4
        fg = cv2.resize(src, (int(iw * s), int(ih * s)), interpolation=interp)
        if spec["type"] == "SCH":
            fg = cv2.GaussianBlur(fg, (0, 0), 0.8)
            fg = np.clip(fg.astype(np.float32) * np.array([0.97, 0.93, 0.84]), 0, 255).astype(np.uint8)
        canvas = bgc.copy()
        alpha = np.zeros(bgc.shape[:2], np.float32)
        y0, x0 = (canvas.shape[0] - fg.shape[0]) // 2, (canvas.shape[1] - fg.shape[1]) // 2
        canvas[y0:y0 + fg.shape[0], x0:x0 + fg.shape[1]] = fg
        alpha[y0:y0 + fg.shape[0], x0:x0 + fg.shape[1]] = 1.0
        alpha = cv2.GaussianBlur(alpha, (0, 0), 2)
        fg_rgb, bg_rgb, mode = canvas, bgc, "contained"
        # SCH: per-group masks (plate x-fractions -> canvas pixels), lit in time with the VO
        gmasks = []
        for g in spec.get("groups", []):
            gm = np.zeros(bgc.shape[:2], np.float32)
            gx0 = x0 + int(g[0] * fg.shape[1]) - 6
            gx1 = x0 + int(g[1] * fg.shape[1]) + 6
            gm[y0:y0 + fg.shape[0], max(0, gx0):gx1] = 1.0
            gmasks.append((cv2.GaussianBlur(gm, (0, 0), 5), g[2], g[3]))
        # soft drop shadow on the BG so the plate reads as a separate layer
        sh = cv2.GaussianBlur(alpha, (0, 0), 30)[..., None]
        bg_rgb = (bg_rgb * (1 - 0.55 * sh)).astype(np.uint8)
    else:
        gmasks = []
        plate = cover(src, int(W * over), int(H * over))
        bg_rgb, alpha, mode = build_layers(plate, spec.get("layer_mode", "subject"))
        fg_rgb = plate
    hl = spec.get("highlight")   # SCH: optional travelling highlight band (texture, not motion)
    ph, pw = fg_rgb.shape[:2]
    offx, offy = (pw - W) / 2, (ph - H) / 2
    mv = dict(MOTION)
    mv.update(spec.get("motion", {}))
    dirx, diry = spec.get("dir", (1, 0))
    push = 1 if spec.get("push", "in") == "in" else -1
    ov = Overlays(spec.get("overlays", ["dust"]), n, hash(spec["id"]) % 1000)
    wr, mw = ffmpeg_writer(out), ffmpeg_writer(matte_out, gray=True)
    fg_alpha_u8 = (alpha * 255).astype(np.uint8)
    for i in range(n):
        t = ease(i / max(1, n - 1))
        z = 1 + mv["zoom"] * (t if push > 0 else 1 - t)
        cam_x = mv["shared_pan"] * W * (t - 0.5) * dirx
        cam_y = mv["shared_pan"] * W * (t - 0.5) * diry * 0.5
        par = mv["fg_parallax"] * W * (t - 0.5)
        zb = 1 + mv["bg_dolly_share"] * (z - 1)
        Mb = affine(zb, -offx + mv["bg_dolly_share"] * cam_x, -offy + mv["bg_dolly_share"] * cam_y)
        Mf = affine(z, -offx + cam_x + par * dirx, -offy + cam_y + par * diry * 0.4)
        # warp in plate space: translate plate so its centre maps to the frame centre
        bgf = cv2.warpAffine(bg_rgb, Mb, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fgf = cv2.warpAffine(fg_rgb, Mf, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        af = cv2.warpAffine(fg_alpha_u8, Mf, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        a = (af.astype(np.float32) / 255)[..., None]
        fr = (fgf * a + bgf * (1 - a)).astype(np.uint8)
        if gmasks:
            tsec = i / FPS
            lit = np.zeros((H, W), np.float32)
            for gm, g0, g1 in gmasks:
                if g0 - 0.15 <= tsec <= g1 + 0.35:
                    k = min(1.0, (tsec - g0 + 0.15) / 0.2, (g1 + 0.35 - tsec) / 0.3)
                    lit = np.maximum(lit, k * cv2.warpAffine(gm, Mf, (W, H), flags=cv2.INTER_LINEAR))
            if lit.max() > 0:
                ink = (fr.astype(np.float32).mean(2) < 110).astype(np.float32)  # notch strokes
                warm = np.array([214, 120, 40], np.float32)
                l3 = (lit * ink)[..., None]
                paper = (lit * (1 - ink))[..., None]
                fr = fr * (1 - 0.85 * l3) + warm * 0.85 * l3
                fr = fr * (1 - 0.10 * paper) + np.array([255, 236, 200], np.float32) * 0.10 * paper
                fr = np.clip(fr, 0, 255).astype(np.uint8)
        if hl:
            # brighten a band that sweeps across the plate (helps follow the counting)
            band = np.zeros((H, W), np.float32)
            bx = int(W * (hl[0] + (hl[1] - hl[0]) * (i / max(1, n - 1))))
            cv2.rectangle(band, (bx - 70, 0), (bx + 70, H), 1.0, -1)
            band = cv2.GaussianBlur(band, (0, 0), 40)[..., None] * a
            fr = np.clip(fr * (1 + 0.35 * band), 0, 255).astype(np.uint8)
        fr = ov.apply(fr, i)
        fr = draw_text_layers(fr, spec, i / FPS, spec["dur"])
        wr.stdin.write(fr.tobytes())
        mw.stdin.write(af.tobytes())
    for p in (wr, mw):
        p.stdin.close()
        p.wait()
    return {"id": spec["id"], "frames": n, "mode": mode}


if __name__ == "__main__":
    import sys
    check_flags()
    shots = json.load(open(sys.argv[1]))
    assets, outdir = sys.argv[2], sys.argv[3]
    only = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else None
    os.makedirs(outdir, exist_ok=True)
    log = []
    for s in shots:
        if only and s["id"] not in only:
            continue
        r = render_shot(s, f"{outdir}/{s['id']}.mp4", f"{outdir}/{s['id']}_matte.mp4", assets)
        print(json.dumps(r), flush=True)
        log.append(r)
