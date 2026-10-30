"""2.5D layer separation. Depth Anything V2 (ViT-S, ONNX) -> near/far mask -> FG RGBA + inpainted BG plate.
Results are cached per asset in build/layers/<id>.npz. Real museum photos become a photo panel (FG)
over a blurred, darkened extension of the same photo (BG)."""
import pathlib, numpy as np, cv2

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
    alpha = cv2.GaussianBlur(mask, (0, 0), 6).astype(np.float32) / 255
    # background plate: remove the FG (dilated) and inpaint at quarter res, then blend back
    hole = cv2.dilate(mask, np.ones((61, 61), np.uint8))
    small = cv2.resize(img, (PW // 4, PH // 4), interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (PW // 4, PH // 4), interpolation=cv2.INTER_NEAREST)
    fill = cv2.resize(cv2.inpaint(small, hs, 9, cv2.INPAINT_TELEA), (PW, PH), interpolation=cv2.INTER_CUBIC)
    fill = cv2.GaussianBlur(fill, (0, 0), 3)
    h = cv2.GaussianBlur(hole, (0, 0), 8).astype(np.float32)[..., None] / 255
    bg = (img * (1 - h) + fill * h).astype(np.uint8)
    return {"bg": bg, "fg": img, "alpha": alpha, "fg_area": float(alpha.mean()), "q": q}

def real_layers(path, scale_h=1.18):
    """Museum or excavation photo: unaltered photo panel (FG) over a blurred extension (BG). The photo itself
    is never cropped for meaning or retouched; only scaled."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:  # webp via PIL fallback
        from PIL import Image
        img = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    bg = cv2.GaussianBlur(cover(img, PW // 4, PH // 4), (0, 0), 6)
    bg = (cv2.resize(bg, (PW, PH), interpolation=cv2.INTER_CUBIC) * 0.38).astype(np.uint8)
    ph = int(1080 * scale_h); pw = int(img.shape[1] * ph / img.shape[0])
    if pw > PW * 0.9: pw = int(PW * 0.9); ph = int(img.shape[0] * pw / img.shape[1])
    panel = cv2.resize(img, (pw, ph), interpolation=cv2.INTER_AREA)
    fg = np.zeros((max(PH, ph), PW, 3), np.uint8); alpha = np.zeros(fg.shape[:2], np.float32)
    x = (PW - pw) // 2; y = (fg.shape[0] - ph) // 2
    fg[y:y + ph, x:x + pw] = panel; alpha[y:y + ph, x:x + pw] = 1
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.5)
    if fg.shape[0] != PH:   # tall panel: keep full height so a tilt can travel along it
        bg = cv2.resize(bg, (PW, fg.shape[0]), interpolation=cv2.INTER_CUBIC)
    return {"bg": bg, "fg": fg, "alpha": alpha, "fg_area": float(alpha.mean()), "q": None}

def get(shot):
    key = shot.get("real") or shot["line"]
    cache = ROOT / "build/layers" / f"{key}.npz"
    if cache.exists():
        z = np.load(cache); return {k: z[k] for k in z.files}
    path = ROOT / shot["asset"]
    L = real_layers(path) if shot["kind"] == "real" else ai_layers(path)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, bg=L["bg"], fg=L["fg"], alpha=L["alpha"].astype(np.float16))
    return L
