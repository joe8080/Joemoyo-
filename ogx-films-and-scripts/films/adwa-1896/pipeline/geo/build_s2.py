# Sentinel-2 L2A true-colour (TCI) mosaics, reprojected onto the Web Mercator grid of a terrain level.
# Source: Copernicus Sentinel-2 data (2025), via the public sentinel-cogs bucket on AWS.
import json, math, os, re, subprocess, sys
import numpy as np, mgrs, rasterio, cv2
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin

os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
B = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
R0 = 2 * math.pi * 6378137 / 256  # metres per pixel at zoom 0
ORG = 20037508.342789244

def scenes(tile, months=((2025, 1), (2025, 2), (2024, 12), (2025, 3))):
    zone, band, sq = tile[:2], tile[2], tile[3:]
    out = []
    for y, m in months:
        pre = f"sentinel-s2-l2a-cogs/{int(zone)}/{band}/{sq}/{y}/{m}/"
        t = subprocess.run(["curl", "-s", "-m", "60", f"{B}/?list-type=2&prefix={pre}&delimiter=/"],
                           capture_output=True, text=True).stdout
        for p in re.findall(r"<Prefix>([^<]+_L2A/)</Prefix>", t):
            j = subprocess.run(["curl", "-s", "-m", "60", f"{B}/{p}tileinfo_metadata.json"], capture_output=True, text=True).stdout
            try:
                d = json.loads(j)
            except Exception:
                continue
            out.append((d.get("cloudyPixelPercentage", 100), -d.get("dataCoveragePercentage", 0), p))
            print("    cand", p.split("/")[-2], out[-1][:2], flush=True)
    out.sort(key=lambda r: (-r[1] < 99, r[0], r[1]))
    return out

def build(name, ovr_res):
    z, ox, oy, Wd, Hd = map(int, open(f"geo/elev_{name}.txt").read().split())
    res = R0 / 2 ** z
    dst_t = from_origin(ox * res - ORG, ORG - oy * res, res, res)
    # tiles touching the level extent
    lon0 = ox / 256 / 2 ** z * 360 - 180; lon1 = (ox + Wd) / 256 / 2 ** z * 360 - 180
    def lat(py):
        n = math.pi - 2 * math.pi * py / 256 / 2 ** z
        return math.degrees(math.atan(math.sinh(n)))
    la1, la0 = lat(oy), lat(oy + Hd)
    m = mgrs.MGRS()
    tiles = sorted({m.toMGRS(la, lo, MGRSPrecision=0) for la in np.linspace(la0, la1, 25) for lo in np.linspace(lon0, lon1, 25)})
    print(name, "tiles", tiles)
    acc = np.zeros((3, Hd, Wd), np.float32); cnt = np.zeros((Hd, Wd), np.float32)
    log = []
    from rasterio.windows import from_bounds
    from rasterio.warp import transform_bounds
    ext = (ox * res - ORG, ORG - (oy + Hd) * res, (ox + Wd) * res - ORG, ORG - oy * res)
    for tl in tiles:
        sc = scenes(tl)
        if not sc:
            print("  no scene", tl); continue
        used = 0
        for cloud, ncov, pre in sc[:40]:
            if cloud > 5:
                continue
            if (cnt > 0).all():
                break
            url = f"/vsicurl/{B}/{pre}TCI.tif"
            with rasterio.open(url) as s:
                f = max(1, int(round(ovr_res / 10)))
                ovr = [o for o in [1] + s.overviews(1) if o <= f][-1]
                bx = transform_bounds("EPSG:3857", s.crs, *ext)
                bx = (max(bx[0], s.bounds.left), max(bx[1], s.bounds.bottom), min(bx[2], s.bounds.right), min(bx[3], s.bounds.top))
                if bx[0] >= bx[2] or bx[1] >= bx[3]:
                    break
                win = from_bounds(*bx, transform=s.transform).round_offsets().round_lengths()
                co = s.overviews(1)[-1]
                pv = s.read(1, window=win, out_shape=(max(1, int(win.height // co)), max(1, int(win.width // co))))
                if (pv > 0).mean() < 0.02:
                    continue
                pc = np.zeros((Hd // 16 + 1, Wd // 16 + 1), np.float32)
                pwt = s.window_transform(win)
                reproject((pv > 0).astype(np.float32), pc, src_transform=pwt * pwt.scale(win.width / pv.shape[1], win.height / pv.shape[0]),
                          src_crs=s.crs, dst_transform=dst_t * dst_t.scale(16, 16), dst_crs="EPSG:3857", resampling=Resampling.nearest)
                small = cv2.resize((cnt == 0).astype(np.uint8), (pc.shape[1], pc.shape[0]), interpolation=cv2.INTER_NEAREST)
                if ((pc > 0.5) & (small > 0)).sum() < 4:
                    continue
                h, w = max(1, int(win.height // ovr)), max(1, int(win.width // ovr))
                src = s.read(window=win, out_shape=(3, h, w), resampling=Resampling.average)
                wt = s.window_transform(win)
                st = wt * wt.scale(win.width / w, win.height / h)
                dst = np.zeros((3, Hd, Wd), np.float32)
                valid = (src.sum(0) > 0).astype(np.float32)
                reproject(src.astype(np.float32), dst, src_transform=st, src_crs=s.crs, dst_transform=dst_t,
                          dst_crs="EPSG:3857", resampling=Resampling.bilinear)
                vm = np.zeros((Hd, Wd), np.float32)
                reproject(valid, vm, src_transform=st, src_crs=s.crs, dst_transform=dst_t, dst_crs="EPSG:3857",
                          resampling=Resampling.bilinear)
            vm = vm > 0.99
            new = vm & (cnt == 0)
            if new.sum() < 500:
                continue
            ov = vm & (cnt > 0)
            if ov.sum() > 2000:  # match colour to what is already there
                have = acc[:, ov] / cnt[ov]
                g = have.mean(1) / np.maximum(dst[:, ov].mean(1), 1)
                dst *= g[:, None, None]
            acc[:, new] += dst[:, new]; cnt[new] += 1
            log.append({"tile": tl, "scene": pre.rstrip("/").split("/")[-1], "cloud_pct": cloud, "new_px": int(new.sum())})
            print("  ", tl, pre.split("/")[-2], "cloud", cloud, "ovr", ovr, "new", int(new.sum()), flush=True)
            used += 1
    img = acc / np.maximum(cnt, 1)
    np.save(f"geo/s2_{name}.npy", np.transpose(img, (1, 2, 0)).astype(np.uint8))
    np.save(f"geo/s2mask_{name}.npy", (cnt > 0))
    json.dump(log, open(f"geo/s2_{name}_scenes.json", "w"), indent=1)

if __name__ == "__main__":
    build(sys.argv[1], float(sys.argv[2]))
