"""Cloth-on-wood wipe foley, driven by the on-screen motion of the hand.

Usage: python3 cloth_foley.py <clip.mp4> <in_s> <out_s> <x0,y0,x1,y1 as 0-1 fractions> <out.wav>
Frame-difference energy inside the box gives the stroke envelope; it shapes
band-passed pink noise (the swish) plus a little low rumble (the drag on wood).
"""
import subprocess
import sys

import numpy as np

SR = 48000


def motion(path, t0, t1, box):
    w, h = 320, 180
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", path,
                          "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    x0, y0, x1, y1 = (int(v * s) for v, s in zip(box, (w, h, w, h)))
    roi = f[:, y0:y1, x0:x1]
    e = np.abs(np.diff(roi, axis=0)).mean(axis=(1, 2))
    return np.concatenate([[e[0]], e])  # one value per frame (24 fps)


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[1:] /= np.sqrt(f[1:])
    return np.fft.irfft(X, n)


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def main():
    path, t0, t1, box, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), \
        [float(v) for v in sys.argv[4].split(",")], sys.argv[5]
    e = motion(path, t0, t1, box)
    e = np.convolve(e, np.ones(5) / 5, mode="same")           # smooth over ~0.2s
    e = np.clip((e - np.percentile(e, 20)) / (np.percentile(e, 95) - np.percentile(e, 20) + 1e-6), 0, 1)
    n = int((t1 - t0) * SR)
    env = np.interp(np.arange(n) / SR, np.arange(len(e)) / 24, e) ** 1.5
    rng = np.random.default_rng(7)
    swish = bandpass(pink(n, rng), 700, 6000)
    drag = bandpass(pink(n, rng), 120, 500)
    # slow random grain so it doesn't sound like steady hiss
    grain = 0.75 + 0.25 * np.interp(np.arange(n), np.linspace(0, n, 200), rng.random(200))
    y = env * grain * (swish / np.abs(swish).max() + 0.5 * drag / np.abs(drag).max())
    y = 0.5 * y / (np.abs(y).max() + 1e-9)
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", out],
                   input=pcm.tobytes(), check=True)
    print(out, f"{t1 - t0:.2f}s, motion frames {len(e)}")


if __name__ == "__main__":
    main()
