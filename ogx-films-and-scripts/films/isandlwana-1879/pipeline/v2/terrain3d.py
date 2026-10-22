# Heightfield ("voxel space") renderer over the battlefield plate. Camera in plate pixels; heights in metres.
import numpy as np, cv2, math
from functools import lru_cache
HERE = "/tmp/claude-0/-home-user/c8a2a160-21fc-57ae-b255-e46475a247d7/scratchpad/isa2/proof"
MPX = 8.4 / 2.5          # metres per plate pixel
@lru_cache(None)
def data():
    rgb = np.load(f"{HERE}/plate_rgb.npy").astype(np.float32)
    el = np.load(f"{HERE}/plate_elev.npy")
    el = cv2.GaussianBlur(el, (0, 0), 2.0)
    return rgb, el
SKY_TOP = np.array([118, 136, 150], np.float32); SKY_LOW = np.array([214, 200, 172], np.float32)
def render(cx, cy, h_above, yaw_deg, pitch=0.18, fov=58, W=1280, H=720, exag=1.6, far_m=14000, n=900,
           sky_top=SKY_TOP, sky_low=SKY_LOW, haze=0.75, h_abs=None):
    rgb, el = data()
    yaw = math.radians(yaw_deg)
    ground = float(el[int(np.clip(cy, 0, el.shape[0] - 1)), int(np.clip(cx, 0, el.shape[1] - 1))])
    camh = (h_abs if h_abs is not None else ground + h_above) * exag
    # depth samples (metres -> plate px)
    d = np.geomspace(25, far_m, n).astype(np.float32)
    ang = np.linspace(-math.radians(fov / 2), math.radians(fov / 2), W).astype(np.float32)
    dirx = np.sin(yaw + ang); diry = -np.cos(yaw + ang)
    corr = np.cos(ang)  # fisheye correction
    dd = d[:, None] / corr[None, :]
    mx = (cx + dirx[None, :] * dd / MPX).astype(np.float32)
    my = (cy + diry[None, :] * dd / MPX).astype(np.float32)
    hz = cv2.remap(el, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) * exag
    col = cv2.remap(rgb, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    focal = (W / 2) / math.tan(math.radians(fov / 2))
    horizon = H * (0.5 - pitch)
    sy = (camh - hz) / d[:, None] * focal + horizon          # screen y of each sample (rows,cols)
    m = np.minimum.accumulate(sy, axis=0)                       # visible top envelope
    # fog by distance
    fog = (1 - np.exp(-(d / far_m) * 2.6 * haze))[:, None, None]
    col = col * (1 - fog) + sky_low[None, None, :] * fog
    rows = np.arange(H, dtype=np.float32) + 0.5
    out = np.empty((H, W, 3), np.float32)
    t = np.clip((rows - 0) / max(horizon, 1), 0, 1)[:, None]
    sky = sky_top[None, :] * (1 - t) + sky_low[None, :] * t
    for c in range(W):
        rev = m[::-1, c]
        k = n - np.searchsorted(rev, rows, side="right")       # first sample index whose envelope <= row
        valid = k < n
        o = sky.copy()
        o[valid] = col[k[valid], c]
        out[:, c] = o
    return out
if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    from plate import P
    hx, hy = P(30.6513, -28.3530)
    # camera ~3.2 km east of the hill, looking west
    cx, cy = P(30.6840, -28.3560)
    yaw = math.degrees(math.atan2(hx - cx, -(hy - cy)))
    import time; t = time.time()
    img = render(cx, cy, 260, yaw, pitch=0.08, fov=50)
    print(time.time() - t)
    cv2.imwrite(f"{HERE}/t3d.jpg", np.clip(img, 0, 255).astype(np.uint8)[..., ::-1], [1, 88])

def ground_h(px, py):
    _, el = data()
    return float(el[int(np.clip(py, 0, el.shape[0] - 1)), int(np.clip(px, 0, el.shape[1] - 1))])

def project(px, py, cam, lift=0.0, W=1920, H=1080):
    """Screen position of plate point (px,py) at ground height + lift metres, for camera dict cam."""
    _, el = data()
    exag = cam.get("exag", 1.6)
    camh = (ground_h(cam["cx"], cam["cy"]) + cam["h"]) * exag if cam.get("h_abs") is None else cam["h_abs"] * exag
    yaw = math.radians(cam["yaw"])
    dx, dy = (px - cam["cx"]) * MPX, (py - cam["cy"]) * MPX
    fwd = dx * math.sin(yaw) - dy * math.cos(yaw)
    right = dx * math.cos(yaw) + dy * math.sin(yaw)
    if fwd < 50:
        return None
    focal = (W / 2) / math.tan(math.radians(cam.get("fov", 58) / 2))
    x = W / 2 + right / fwd * focal
    h = (ground_h(px, py) + lift) * exag
    y = (camh - h) / fwd * focal + H * (0.5 - cam.get("pitch", 0.18))
    return x, y, fwd
