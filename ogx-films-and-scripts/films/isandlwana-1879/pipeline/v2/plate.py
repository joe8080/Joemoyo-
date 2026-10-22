# Battlefield relief plate: Sentinel-2 colour x multi-light hillshade x contours, from AWS terrain tiles (z14).
import numpy as np, math, cv2, json
S = "/tmp/claude-0/-home-user/c8a2a160-21fc-57ae-b255-e46475a247d7/scratchpad"
G = f"{S}/isa/build11/geo"
Z, OX, OY = 14, 2451712, 2439936
LON0, LON1, LAT0, LAT1 = 30.52, 30.80, -28.27, -28.41
F = 2.5
def X(lon): return (lon + 180) / 360 * 256 * 2 ** Z - OX
def Y(lat):
    r = math.radians(lat); return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 256 * 2 ** Z - OY
x0, x1, y0, y1 = int(X(LON0)), int(X(LON1)), int(Y(LAT0)), int(Y(LAT1))
def P(lon, lat):  # plate pixel
    return ((X(lon) - x0) * F, (Y(lat) - y0) * F)
if __name__ == "__main__":
    E = np.load(f"{G}/elev_L3.npy").astype(np.float32)
    E = cv2.GaussianBlur(cv2.medianBlur(E, 5), (0, 0), 1.4)[y0:y1, x0:x1]
    s2 = np.load(f"{G}/s2_L3.npy")[y0:y1, x0:x1].astype(np.float32)
    e = cv2.resize(E, None, fx=F, fy=F, interpolation=cv2.INTER_CUBIC)
    s2 = cv2.resize(s2, (e.shape[1], e.shape[0]), interpolation=cv2.INTER_CUBIC)
    s2 = cv2.bilateralFilter(s2, 7, 18, 5)
    px = 8.4 / F
    es = cv2.GaussianBlur(e, (0, 0), 5.0)
    def shade(az, alt, ex):
        gx = cv2.Sobel(es, cv2.CV_32F, 1, 0, ksize=5) / (128 * px) * 4 * ex
        gy = cv2.Sobel(es, cv2.CV_32F, 0, 1, ksize=5) / (128 * px) * 4 * ex
        a, b = math.radians(az), math.radians(alt)
        lx, ly, lz = math.cos(b) * math.sin(a), -math.cos(b) * math.cos(a), math.sin(b)
        return np.clip((-gx * lx - gy * ly + lz) / np.sqrt(1 + gx * gx + gy * gy), 0, 1)
    sh = 0.55 * shade(315, 40, 2.6) + 0.25 * shade(270, 55, 2.0) + 0.20 * shade(0, 60, 2.0)
    # local relief (valleys darker, ridges lifted)
    loc = es - cv2.GaussianBlur(es, (0, 0), 60)
    ao = np.clip(0.5 + loc / 120, 0.25, 1.0)
    col = 255 * np.clip(s2 / 255 * 1.4, 0, 1) ** 0.85
    g = col.mean(2, keepdims=True); col = g + (col - g) * 0.62       # BGR? s2 stored RGB
    col = col * (0.42 + 0.85 * sh[..., None]) * (0.78 + 0.28 * ao[..., None])
    # warm archival grade
    col[..., 0] *= 1.05; col[..., 2] *= 0.90
    img = np.clip(col, 0, 255)
    lines = np.zeros(e.shape, np.float32); lines100 = np.zeros(e.shape, np.float32)
    for lv in range(760, 1640, 20):
        m = (es >= lv).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(lines100 if lv % 100 == 0 else lines, cs, -1, 1.0, 2 if lv % 100 == 0 else 1, cv2.LINE_AA)
    lines = cv2.GaussianBlur(lines, (0, 0), 0.6); lines100 = cv2.GaussianBlur(lines100, (0, 0), 0.8)
    img = img * (1 - 0.16 * lines[..., None] - 0.30 * lines100[..., None]) + np.array([40, 30, 18]) * 0.0
    np.save(f"{S}/isa2/proof/plate_rgb.npy", img.astype(np.uint8))
    np.save(f"{S}/isa2/proof/plate_elev.npy", e.astype(np.float32))
    prev = cv2.resize(img.astype(np.uint8), None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    cv2.imwrite(f"{S}/isa2/proof/plate_preview.jpg", prev[..., ::-1], [1, 85])
    print(img.shape)
