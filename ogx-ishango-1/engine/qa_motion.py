"""Per-shot parallax stats from RENDERED frames (L2, L4, L9, L16).

For each shot video + its rendered matte: Farneback optical flow between consecutive
frames at 480p. FG = matte > 0.6, BG = matte < 0.1 (BG falls back to the whole frame
when the matte covers too little of the frame to separate). Travel is the summed median
per-frame flow magnitude, as a percentage of frame width. Overlays don't drive the
statistic, because medians ignore sparse dust and grain.
"""
import csv
import glob
import json
import os
import sys

import cv2
import numpy as np


def frames(path, w=480):
    cap = cv2.VideoCapture(path)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        h = int(f.shape[0] * w / f.shape[1])
        yield cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA)
    cap.release()


def shot_stats(video, matte):
    fg_t = bg_t = 0.0
    n = 0
    prev = None
    fg_area = []
    for f, m in zip(frames(video), frames(matte)):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        mm = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        if prev is not None:
            flow = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 21, 3, 5, 1.1, 0)
            mag = np.linalg.norm(flow, axis=2)
            fg = mm > 0.6
            bg = mm < 0.1
            fg_area.append(fg.mean())
            if fg.mean() > 0.02:
                fg_t += float(np.median(mag[fg]))
            bg_t += float(np.median(mag[bg])) if bg.mean() > 0.05 else float(np.median(mag))
            n += 1
        prev = g
    w = 480.0
    fg_pct, bg_pct = 100 * fg_t / w, 100 * bg_t / w
    return {"frames": n + 1, "fg_area": round(float(np.mean(fg_area)) if fg_area else 0, 3),
            "fg_travel_pct": round(fg_pct, 2), "bg_travel_pct": round(bg_pct, 2),
            "fg_bg_ratio": round(fg_pct / bg_pct, 2) if bg_pct > 1e-6 else None}


if __name__ == "__main__":
    d = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(d, "parallax_stats.csv")
    floor_fg, floor_ratio = 3.0, 2.0
    rows = []
    for v in sorted(glob.glob(os.path.join(d, "*.mp4"))):
        if v.endswith("_matte.mp4"):
            continue
        m = v[:-4] + "_matte.mp4"
        if not os.path.exists(m):
            continue
        s = shot_stats(v, m)
        s["shot"] = os.path.basename(v)[:-4]
        card = s["fg_area"] < 0.01
        flat = s["fg_area"] > 0.97          # MAP: whole frame is one flat plane
        if card:
            s["pass"] = "CARD"
        elif flat:
            s["pass"] = "MAP-OVERRIDE" if s["fg_travel_pct"] >= floor_fg else "FAIL"
        else:
            s["pass"] = "PASS" if s["fg_travel_pct"] >= floor_fg and (s["fg_bg_ratio"] or 0) >= floor_ratio else "FAIL"
        rows.append(s)
        print(json.dumps(s), flush=True)
    with open(out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["shot", "frames", "fg_area", "fg_travel_pct", "bg_travel_pct", "fg_bg_ratio", "pass"])
        wr.writeheader()
        wr.writerows(rows)
