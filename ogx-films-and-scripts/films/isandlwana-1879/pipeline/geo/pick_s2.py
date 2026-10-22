# Rank full-coverage Sentinel-2 scenes of tile 36JTP by cloud over the L3 battlefield window (bright-pixel fraction).
import os, re, subprocess, numpy as np, rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt"); os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
B = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
scenes = re.findall(r"cand (S2\w+_36JTP_\d+_\d_L2A) \(0\.0, -100\.0\)", open("geo/s2_L3.log").read())
out = []
for sc in scenes:
    sat, tile, date, n, _ = sc.split("_")
    url = f"/vsicurl/{B}/sentinel-s2-l2a-cogs/36/J/TP/{date[:4]}/{int(date[4:6])}/{sc}/TCI.tif"
    try:
        with rasterio.open(url) as s:
            bx = transform_bounds("EPSG:4326", s.crs, 30.47, -28.46, 30.90, -28.24)
            win = from_bounds(*bx, transform=s.transform)
            co = s.overviews(1)[-2]
            a = s.read(window=win, out_shape=(3, int(win.height // co), int(win.width // co))).astype(np.float32)
            valid = a.sum(0) > 0
            bright = (a.min(0) > 170) & valid
            print(sc, round(float(bright.sum() / max(valid.sum(), 1)), 4), round(float(valid.mean()), 3), flush=True)
            out.append((bright.sum() / max(valid.sum(), 1), sc))
    except Exception as e:
        print(sc, "ERR", str(e)[:80])
out.sort(); print("BEST", out[:5])
