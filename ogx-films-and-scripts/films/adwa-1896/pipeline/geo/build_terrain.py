# Shaded-relief colour maps from AWS Terrain Tiles (terrarium) + Natural Earth lakes.
import json, math, sys
import numpy as np, cv2

R0 = 2 * math.pi * 6378137 / 256
LAND = [(-1, (178, 170, 132)), (0, (178, 170, 132)), (400, (170, 158, 116)), (900, (160, 140, 100)),
        (1600, (142, 116, 84)), (2400, (122, 98, 74)), (3300, (146, 132, 118)), (4400, (222, 216, 208))]
SEA = [(-7000, (20, 48, 92)), (-3000, (34, 74, 124)), (-1000, (52, 100, 150)), (-200, (82, 136, 178)), (0, (118, 166, 198))]
EXAG = {"L0": 18.0, "L1": 7.0, "L2": 2.6, "L3": 1.6}

def ramp(e, stops):
    xs = np.array([s[0] for s in stops], np.float32)
    out = np.zeros(e.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(e, xs, np.array([s[1][c] for s in stops], np.float32))
    return out

def lat_of_rows(oy, H, z):
    py = oy + np.arange(H) + 0.5
    n = math.pi - 2 * math.pi * py / 256 / 2 ** z
    return np.degrees(np.arctan(np.sinh(n)))

def lakes_mask(name, z, ox, oy, Wd, Hd):
    m = np.zeros((Hd, Wd), np.uint8)
    g = json.load(open("geo/ne_50m_lakes.geojson"))
    def P(lon, lat):
        x = (lon + 180) / 360 * 2 ** z * 256 - ox
        r = math.radians(max(-85, min(85, lat)))
        y = (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z * 256 - oy
        return [x * 4, y * 4]
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            pts = [np.array([P(*c) for c in ring], np.int32) for ring in poly]
            cv2.fillPoly(m, [pts[0]], 255, lineType=cv2.LINE_AA, shift=2)
            for h in pts[1:]:
                cv2.fillPoly(m, [h], 0, lineType=cv2.LINE_AA, shift=2)
    return m.astype(np.float32) / 255

def build(name):
    z, ox, oy, Wd, Hd = map(int, open(f"geo/elev_{name}.txt").read().split())
    e = np.load(f"geo/elev_{name}.npy").astype(np.float32)
    e = np.clip(e, -8000, 6000)
    e = cv2.medianBlur(e, 3)
    lat = lat_of_rows(oy, Hd, z)
    px = (R0 / 2 ** z) * np.cos(np.radians(lat))[:, None]  # metres per pixel on the ground
    ee = cv2.GaussianBlur(e, (0, 0), 0.8)
    gx = cv2.Sobel(ee, cv2.CV_32F, 1, 0, ksize=3) / (8 * px)
    gy = cv2.Sobel(ee, cv2.CV_32F, 0, 1, ksize=3) / (8 * px)
    ex = EXAG[name]
    gx, gy = gx * ex, gy * ex
    # light from the north-west, 45 degrees up
    az, alt = math.radians(315), math.radians(45)
    lx, ly, lz = math.cos(alt) * math.sin(az), -math.cos(alt) * math.cos(az), math.sin(alt)
    nz = 1 / np.sqrt(1 + gx * gx + gy * gy)
    shade = (-gx * lx * nz + gy * ly * nz * -1 + lz * nz)
    shade = np.clip(shade, 0, 1)
    land = e > 0
    col = np.where(land[..., None], ramp(e, LAND), ramp(e, SEA))
    # relief: multiply on land, soft on sea
    s_land = 0.35 + 0.85 * shade
    s_sea = 0.85 + 0.2 * shade
    col *= np.where(land, s_land, s_sea)[..., None]
    lk = lakes_mask(name, z, ox, oy, Wd, Hd)[..., None]
    col = col * (1 - lk) + np.array([96, 146, 182], np.float32) * lk
    col = np.clip(col, 0, 255).astype(np.uint8)
    np.save(f"geo/terr_{name}.npy", col)
    np.save(f"geo/shade_{name}.npy", (shade * 255).astype(np.uint8))
    cv2.imwrite(f"geo/terr_{name}_preview.jpg", cv2.resize(col[..., ::-1], (Wd // 4, Hd // 4), interpolation=cv2.INTER_AREA))
    print(name, col.shape)

if __name__ == "__main__":
    for n in sys.argv[1:]:
        build(n)
