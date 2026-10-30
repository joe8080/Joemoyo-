"""2.5D layer separation. Depth Anything V2 (ViT-S, ONNX) -> near/far mask -> FG RGBA + inpainted BG plate.
Results are cached per asset in build/layers/<id>.npz. Real museum photos become a photo panel (FG)
over a blurred, darkened extension of the same photo (BG)."""
import pathlib, json, numpy as np, cv2

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEPTH_ONNX = pathlib.Path("/tmp/claude-0/-home-user-Joemoyo-/312bc74c-7d59-509c-b717-3fa491a69736/scratchpad/models/depth_anything_v2_vits.onnx")
PW, PH = 2304, 1296          # plate: 1.2x the 1920x1080 frame, room for camera moves
_sess = None

def depth(img):
    global _sess
    import onnxruntime as ort
    if _sess is None:
        _sess = ort.InferenceSession(str(DEPTH_ONNX), providers=["CPUExecutionProvider"])
    x = cv2.resize(img, (518, 518), interpolation=cv2.INTER_CUBIC)[:, :, ::-1].astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    d = _sess.run(None, {_sess.get_inputs()[0].name: x})[0].squeeze()
    d = cv2.resize(d, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    return (d - d.min()) / (np.ptp(d) + 1e-6)          # 1 = near

def cover(img, w, h):
    s = max(w / img.shape[1], h / img.shape[0])
    r = cv2.resize(img, (int(np.ceil(img.shape[1] * s)), int(np.ceil(img.shape[0] * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y, x = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y:y + h, x:x + w]

def ai_layers(path, target=(0.22, 0.45)):
    img = cover(cv2.imread(str(path), cv2.IMREAD_COLOR), PW, PH)
    d = depth(img)
    # choose the near-threshold so the FG covers a usable share of the frame
    q = 0.70
    for _ in range(12):
        m = (d >= np.quantile(d, q)).astype(np.uint8)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
        keep = np.zeros_like(m)
        for k in range(1, n):
            if stats[k, cv2.CC_STAT_AREA] > 0.01 * m.size: keep[lab == k] = 1
        area = keep.mean()
        if area < target[0]: q -= 0.05
        elif area > target[1]: q += 0.04
        else: break
    mask = cv2.morphologyEx(keep * 255, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    alpha = cv2.GaussianBlur(mask, (0, 0), 11).astype(np.float32) / 255   # wide feather hides the parallax seam
    # background plate: remove the FG (dilated) and inpaint at quarter res, then blend back
    hole = cv2.dilate(mask, np.ones((41, 41), np.uint8))
    small = cv2.resize(img, (PW // 2, PH // 2), interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (PW // 2, PH // 2), interpolation=cv2.INTER_NEAREST)
    fill = cv2.resize(cv2.inpaint(small, hs, 15, cv2.INPAINT_TELEA), (PW, PH), interpolation=cv2.INTER_CUBIC)
    fill = cv2.GaussianBlur(fill, (0, 0), 2)
    h = cv2.GaussianBlur(hole, (0, 0), 8).astype(np.float32)[..., None] / 255
    bg = (img * (1 - h) + fill * h).astype(np.uint8)
    return {"bg": bg, "fg": img, "alpha": alpha, "fg_area": float(alpha.mean()), "q": q}

def _clone_fill(img, hole, period=56):
    """v1.1 seam-safe BG: fill the hole under the FG with sharp texture mirrored from just above it, column by
    column, instead of a blurred inpaint (the blur read as a smear band when the FG slid off it)."""
    h = hole > 0
    out = img.copy(); top = np.full(img.shape[1], -1, np.int32); prev = np.zeros(img.shape[1], bool)
    cols = np.arange(img.shape[1])
    for y in range(img.shape[0]):
        r = h[y]; start = r & ~prev; top[start] = y; prev = r
        if not r.any(): continue
        i = y - top[r]; k = i % period; flip = (i // period) % 2 == 0
        src = np.where(flip, top[r] - 1 - k, top[r] - period + k)
        out[y, cols[r]] = img[np.clip(src, 0, img.shape[0] - 1), cols[r]]
    return out

def _reflect_fill(img, hole):
    """v1.1 seam-safe BG for any edge direction: each hole pixel takes the pixel mirrored across its nearest
    non-hole pixel, so the strip the FG uncovers shows sharp nearby texture instead of a blurred inpaint."""
    src = (hole == 0).astype(np.uint8)
    _, lab = cv2.distanceTransformWithLabels(1 - src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    zy, zx = np.where(src > 0); lz = lab[zy, zx]
    my = np.zeros(lab.max() + 1, np.int32); mx = np.zeros_like(my); my[lz] = zy; mx[lz] = zx
    hy, hx = np.where(src == 0); qy, qx = my[lab[hy, hx]], mx[lab[hy, hx]]
    ry = np.clip(2 * qy - hy, 0, img.shape[0] - 1); rx = np.clip(2 * qx - hx, 0, img.shape[1] - 1)
    bad = src[ry, rx] == 0                      # mirrored point fell back into the hole: use the edge pixel
    ry[bad], rx[bad] = qy[bad], qx[bad]
    out = img.copy(); out[hy, hx] = img[ry, rx]
    return out

def ai_layers_v11(path, ground_only=False, hole_dilate=21, feather=11, edge=None, fill="reflect"):
    """v1.1 layer split (opt-in per shot; v1.0 shots keep ai_layers): FG = near regions that touch the bottom of
    the frame only (no floating islands such as a lone patch of tree crown), BG = the photo with the FG hole
    filled by mirrored texture from just above it. `edge` (optional) = hand-drawn FG top edge as
    [[x, y], ...] in 0-1 plate coordinates; everything below it is FG."""
    img = cover(cv2.imread(str(path), cv2.IMREAD_COLOR), PW, PH)
    if edge:
        pts = np.array([[int(x * PW), int(y * PH)] for x, y in edge] + [[PW, PH], [0, PH]], np.int32)
        mask = np.zeros((PH, PW), np.uint8); cv2.fillPoly(mask, [pts], 255, cv2.LINE_AA)
    else:
        mask = (ai_layers(path)["alpha"] > 0.5).astype(np.uint8) * 255
        if ground_only:
            n, lab, st, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8))
            keep = np.zeros_like(mask)
            for k in range(1, n):
                if st[k, cv2.CC_STAT_TOP] + st[k, cv2.CC_STAT_HEIGHT] >= PH - 2: keep[lab == k] = 255
            mask = keep
    alpha = cv2.GaussianBlur(mask, (0, 0), feather).astype(np.float32) / 255
    hole = cv2.dilate(mask, np.ones((hole_dilate, hole_dilate), np.uint8))
    bg = _reflect_fill(img, hole) if fill == "reflect" else _clone_fill(img, hole)
    return {"bg": bg, "fg": img, "alpha": alpha, "fg_area": float(alpha.mean()), "q": None}

def real_layers(path, scale_h=1.18, crop=None, max_up=1.25):
    """Museum or excavation photo: unaltered photo panel (FG) over a blurred extension (BG). The photo itself
    is never cropped for meaning or retouched; only scaled."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:  # webp via PIL fallback
        from PIL import Image
        img = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    if crop: img = img[crop[1]:crop[3], crop[0]:crop[2]]
    bg = cv2.GaussianBlur(cover(img, PW // 4, PH // 4), (0, 0), 6)
    bg = (cv2.resize(bg, (PW, PH), interpolation=cv2.INTER_CUBIC) * 0.38).astype(np.uint8)
    ph = int(1080 * scale_h); pw = int(img.shape[1] * ph / img.shape[0])
    if pw > PW * 0.9: pw = int(PW * 0.9); ph = int(img.shape[0] * pw / img.shape[1])
    # never upscale a real image more than 1.25x in the delivered 1920x1080 frame (plate->frame is W/PW)
    up = (pw / img.shape[1]) * (1920 / PW)
    if up > max_up: k = max_up / up; pw, ph = int(pw * k), int(ph * k)
    panel = cv2.resize(img, (pw, ph), interpolation=cv2.INTER_AREA)
    fg = np.zeros((max(PH, ph), PW, 3), np.uint8); alpha = np.zeros(fg.shape[:2], np.float32)
    x = (PW - pw) // 2; y = (fg.shape[0] - ph) // 2
    fg[y:y + ph, x:x + pw] = panel; alpha[y:y + ph, x:x + pw] = 1
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.5)
    if fg.shape[0] != PH:   # tall panel: keep full height so a tilt can travel along it
        bg = cv2.resize(bg, (PW, fg.shape[0]), interpolation=cv2.INTER_CUBIC)
    return {"bg": bg, "fg": fg, "alpha": alpha, "fg_area": float(alpha.mean()), "q": None}

def get(shot):
    v = shot.get("view", {}); lo = shot.get("layer")      # "layer" = v1.1 seam-safe split options (opt-in)
    key = (shot.get("real") or shot["line"]) + ("_" + "_".join(f"{k}{v[k]}" for k in sorted(v)).replace(" ", "").replace(",", "-") if v else "")
    if lo is not None:
        import hashlib; key += "_v11_" + hashlib.md5(json.dumps(lo, sort_keys=True).encode()).hexdigest()[:8]
    cache = ROOT / "build/layers" / f"{key}.npz"
    if cache.exists():
        z = np.load(cache); return {k: z[k] for k in z.files}
    path = ROOT / shot["asset"]
    L = real_layers(path, **v) if shot["kind"] == "real" else (ai_layers_v11(path, **lo) if lo is not None else ai_layers(path))
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, bg=L["bg"], fg=L["fg"], alpha=L["alpha"].astype(np.float16))
    return L
