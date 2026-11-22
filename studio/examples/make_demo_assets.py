"""Draw the demo's placeholder pictures and clip, so the repo carries no binary media.

    python studio/examples/make_demo_assets.py

Real projects use your own photos, footage and AI-generated shots instead.
"""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).parent / "demo" / "assets"


def bokeh(path, base, tints, seed, size=(2400, 1600)):
    rng = np.random.default_rng(seed)
    w, h = size
    yy = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(base[0])[None, None, :] * (1 - yy) + np.array(base[1])[None, None, :] * yy
    arr = np.broadcast_to(arr, (h, w, 3)).copy()
    img = Image.fromarray(arr.astype(np.uint8))
    for layer, (count, rmin, rmax, blur, alpha) in enumerate([(26, 70, 190, 26, 70), (40, 24, 80, 9, 120), (60, 6, 22, 2, 200)]):
        ov = Image.new("RGBA", size, (0, 0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(ov)
        for _ in range(count):
            x, y = rng.uniform(0, w), rng.uniform(h * 0.15, h)
            r = rng.uniform(rmin, rmax)
            c = tints[rng.integers(len(tints))]
            d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(c) + (int(alpha * rng.uniform(0.4, 1)),))
        img = Image.alpha_composite(img.convert("RGBA"), ov.filter(ImageFilter.GaussianBlur(blur))).convert("RGB")
    a = np.asarray(img, dtype=np.int16) + rng.integers(-5, 6, size=(h, w, 3), dtype=np.int16)
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(path, quality=90)


def ridges(path, sky, hills, seed, size=(2400, 1600)):
    rng = np.random.default_rng(seed)
    w, h = size
    yy = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(sky[0])[None, None, :] * (1 - yy) + np.array(sky[1])[None, None, :] * yy
    arr = np.broadcast_to(arr, (h, w, 3)).copy()
    x = np.arange(w)
    sx, sy = int(w * 0.68), int(h * 0.3)
    gy, gx = np.mgrid[0:h, 0:w]
    glow = np.exp(-(((gx - sx) / (w * 0.22)) ** 2 + ((gy - sy) / (h * 0.3)) ** 2))[..., None]
    arr = arr + (np.array([255, 214, 150]) - arr) * glow * 0.75
    for i, col in enumerate(hills):
        base = h * (0.5 + 0.11 * i)
        y = base + sum(rng.uniform(20, 70) / (k + 1) * np.sin(x / w * np.pi * 2 * (k + 1) * rng.uniform(0.6, 1.6) + rng.uniform(0, 6))
                       for k in range(5))
        mask = gy >= y[None, :]
        arr[mask] = np.array(col)
    a = arr + rng.integers(-4, 5, size=(h, w, 3))
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)).save(path, quality=90)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bokeh(OUT / "city_lights.jpg", [(8, 12, 28), (26, 20, 44)], [(255, 196, 110), (255, 150, 90), (120, 200, 255)], 3)
    bokeh(OUT / "market_glow.jpg", [(4, 18, 24), (10, 34, 40)], [(45, 212, 167), (120, 230, 255), (255, 209, 102)], 11)
    ridges(OUT / "horizon.jpg", [(30, 44, 84), (240, 150, 100)],
           [(70, 62, 100), (48, 44, 78), (30, 30, 56), (16, 18, 34)], 5)
    clip = OUT / "flow.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "gradients=s=1280x720:c0=0x0A1424:c1=0x2DD4A7:c2=0x12213B:c3=0xFFD166:n=4:speed=0.018:d=8:r=30",
                    "-vf", "gblur=sigma=30,eq=brightness=-0.12:saturation=0.9", "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    print("Demo assets written to", OUT)


if __name__ == "__main__":
    main()
