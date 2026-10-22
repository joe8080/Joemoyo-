# Pre-render the 3D terrain flights for the two proofs (1280x720 -> 1920x1080).
import sys, math, json, subprocess, numpy as np, cv2
from multiprocessing import Pool
HERE = "/tmp/claude-0/-home-user/c8a2a160-21fc-57ae-b255-e46475a247d7/scratchpad/isa2/proof"
sys.path.insert(0, HERE)
from plate import P
import terrain3d as T
FPS = 24
def ease(u): return u * u * (3 - 2 * u)
def heading(a, b):
    return math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))
FLIGHTS = {
    # name: (dur, start(lon,lat,h), end(lon,lat,h), look-at start, look-at end, pitch0, pitch1, fov, sky)
    "O1": (7.0, (30.748, -28.292, 900), (30.712, -28.318, 560), (30.655, -28.352), (30.655, -28.353), 0.30, 0.27, 56, "dawn"),
    "O11": (8.5, (30.676, -28.334, 420), (30.664, -28.343, 300), (30.650, -28.356), (30.651, -28.355), 0.27, 0.24, 50, "day"),
    "B1": (6.0, (30.690, -28.331, 560), (30.680, -28.337, 470), (30.656, -28.355), (30.654, -28.356), 0.30, 0.28, 52, "smoke"),
}
SKIES = {
    "dawn": (np.array([96, 112, 140], np.float32), np.array([200, 182, 160], np.float32), 0.9),
    "day": (np.array([128, 150, 170], np.float32), np.array([222, 214, 196], np.float32), 0.7),
    "smoke": (np.array([92, 88, 84], np.float32), np.array([176, 160, 140], np.float32), 0.85),
}
def cam_at(name, u):
    dur, a, b, la, lb, p0, p1, fov, sky = FLIGHTS[name]
    e = ease(u)
    lon = a[0] + (b[0] - a[0]) * e; lat = a[1] + (b[1] - a[1]) * e; h = a[2] + (b[2] - a[2]) * e
    tl = (la[0] + (lb[0] - la[0]) * e, la[1] + (lb[1] - la[1]) * e)
    cx, cy = P(lon, lat); tx, ty = P(*tl)
    return dict(cx=cx, cy=cy, h=h, yaw=heading((cx, cy), (tx, ty)), pitch=p0 + (p1 - p0) * e, fov=fov, exag=1.6, sky=sky)
def job(args):
    name, i, n = args
    c = cam_at(name, i / max(n - 1, 1))
    st, sl, hz = SKIES[c["sky"]]
    img = T.render(c["cx"], c["cy"], c["h"], c["yaw"], pitch=c["pitch"], fov=c["fov"], exag=c["exag"],
                   sky_top=st, sky_low=sl, haze=hz)
    img = cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (1920, 1080), interpolation=cv2.INTER_CUBIC)
    bl = cv2.GaussianBlur(img, (0, 0), 2.0)
    img = cv2.addWeighted(img, 1.5, bl, -0.5, 0)
    cv2.imwrite(f"{HERE}/fl/{name}_{i:04d}.jpg", img[..., ::-1], [1, 94])
    return i
if __name__ == "__main__":
    import os
    os.makedirs(f"{HERE}/fl", exist_ok=True)
    names = sys.argv[1:] or list(FLIGHTS)
    cams = {}
    for name in names:
        n = int(round(FLIGHTS[name][0] * FPS))
        todo = [(name, i, n) for i in range(n) if not os.path.exists(f"{HERE}/fl/{name}_{i:04d}.jpg")]
        with Pool(4) as p:
            for _ in p.imap_unordered(job, todo, chunksize=2):
                pass
        cams[name] = [cam_at(name, i / max(n - 1, 1)) for i in range(n)]
        print(name, "done", n, flush=True)
    json.dump(cams, open(f"{HERE}/fl/cams_{'_'.join(names)}.json", "w"))
