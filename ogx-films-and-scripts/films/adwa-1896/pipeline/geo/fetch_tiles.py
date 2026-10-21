# Fetch AWS Terrain Tiles (terrarium encoding) for each map level and stitch to elevation arrays.
import math, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image

LEVELS = {  # name: (zoom, lon0, lat0(south), lon1, lat1(north))
    "L0": (5, -80.0, -58.0, 125.0, 66.0),
    "L1": (8, 30.0, 2.0, 54.0, 22.0),
    "L2": (11, 37.4, 12.4, 40.6, 15.7),
    "L3": (14, 38.70, 13.98, 39.20, 14.32),
}

def tx(lon, z): return (lon + 180) / 360 * 2 ** z
def ty(lat, z):
    r = math.radians(lat)
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z

def fetch(z, x, y):
    p = f"geo/tiles/{z}/{x}_{y}.png"
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    for _ in range(3):
        r = subprocess.run(["curl", "-sS", "-m", "60", "-o", p, "-w", "%{http_code}",
                            f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
                           capture_output=True, text=True)
        if r.stdout == "200":
            return p
    raise RuntimeError(f"tile {z}/{x}/{y}: {r.stdout} {r.stderr}")

def build(name):
    z, lo0, la0, lo1, la1 = LEVELS[name]
    x0, x1 = int(tx(lo0, z)), int(tx(lo1, z))
    y0, y1 = int(ty(la1, z)), int(ty(la0, z))
    jobs = [(z, x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
    with ThreadPoolExecutor(16) as ex:
        paths = list(ex.map(lambda a: fetch(*a), jobs))
    W, H = (x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256
    elev = np.zeros((H, W), np.float32)
    for (zz, x, y), p in zip(jobs, paths):
        a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        e = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        elev[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = e
    np.save(f"geo/elev_{name}.npy", elev)
    # pixel origin (global pixel coords at zoom z) of the array's top-left corner
    open(f"geo/elev_{name}.txt", "w").write(f"{z} {x0 * 256} {y0 * 256} {W} {H}\n")
    print(name, len(jobs), "tiles", W, H, float(elev.min()), float(elev.max()))

if __name__ == "__main__":
    for n in sys.argv[1:] or LEVELS:
        build(n)
