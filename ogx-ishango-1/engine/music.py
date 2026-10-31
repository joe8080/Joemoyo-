"""Procedural review-cut music and ambience stems (zero credits, original, no samples).

music_bed.wav : low drone + slowly drifting pad; thins out between the 'thin' markers
                (the readings section) and swells at the end.
ambience.wav  : soft lake ambience (filtered noise 'water' + occasional bird-like chirps).
Usage: python3 music.py OUT_DIR TOTAL_SECONDS THIN_START THIN_END
"""
import sys
import wave

import numpy as np

SR = 48000


def write(path, x):
    x = np.clip(x, -1, 1)
    st = (np.stack([x[0], x[1]], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def lowpass(x, cutoff):
    from scipy.signal import lfilter   # one-pole low-pass
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def env(t, total, fade=4.0):
    return np.clip(t / fade, 0, 1) * np.clip((total - t) / fade, 0, 1)


def bed(total, thin0, thin1, rng):
    t = np.arange(int(total * SR)) / SR
    out = np.zeros((2, len(t)))
    # D minor-ish modal drone: D2, A2, D3, F3, C4 with slow detune and pan
    notes = [73.42, 110.0, 146.83, 174.61, 261.63]
    amps = [0.30, 0.20, 0.12, 0.07, 0.035]
    for k, (f, a) in enumerate(zip(notes, amps)):
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.013 + 0.007 * k) * t + k)
        for ch, det in ((0, -0.15), (1, 0.15)):
            ph = 2 * np.pi * (f + det) * t + 0.3 * np.sin(2 * np.pi * 0.05 * t + k)
            out[ch] += a * (0.6 + 0.4 * lfo) * (np.sin(ph) + 0.18 * np.sin(2 * ph))
    # sparse soft plucks (struck-wood colour), slow and irregular
    pl = np.zeros(len(t))
    scale = [293.66, 349.23, 392.0, 440.0, 523.25]
    tt = 3.0
    while tt < total - 3:
        f = scale[rng.integers(len(scale))]
        n0 = int(tt * SR)
        n = int(2.5 * SR)
        seg = np.arange(min(n, len(t) - n0)) / SR
        pl[n0:n0 + len(seg)] += 0.09 * np.exp(-seg * 2.2) * (np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(2 * np.pi * 2.01 * f * seg))
        tt += rng.uniform(4.5, 9.0)
    # dynamics: thin section, end swell
    g = np.ones(len(t))
    thin = (t > thin0) & (t < thin1)
    g[thin] = 0.62
    g = np.convolve(g, np.ones(SR) / SR, mode="same")
    swell = 1 + 0.35 * np.clip((t - (total - 22)) / 14, 0, 1) * np.clip((total - t) / 4, 0, 1)
    plk = pl * np.where(thin, 0.35, 1.0)
    out[0] = (out[0] + 0.8 * plk) * g * swell
    out[1] = (out[1] + 0.8 * np.roll(plk, int(0.011 * SR))) * g * swell
    out *= env(t, total)
    return out / (np.abs(out).max() + 1e-9) * 0.5


def ambience(total, rng):
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    for ch in (0, 1):
        w = rng.normal(0, 1, n)
        w = lowpass(w, 500.0)
        mod = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t + ch) * np.sin(2 * np.pi * 0.023 * t)
        out[ch] = w * mod
    # distant chirps
    tt = 5.0
    while tt < total - 2:
        n0 = int(tt * SR)
        d = int(0.12 * SR)
        s = np.arange(d) / SR
        f = rng.uniform(2400, 3600)
        ch = rng.integers(2)
        out[ch, n0:n0 + d] += 0.25 * np.sin(2 * np.pi * (f + 900 * s / 0.12) * s) * np.hanning(d)
        tt += rng.uniform(7, 16)
    out *= env(t, total)
    return out / (np.abs(out).max() + 1e-9) * 0.35


if __name__ == "__main__":
    od, total, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    rng = np.random.default_rng(1950)
    write(f"{od}/music_bed.wav", bed(total, a, b, rng))
    write(f"{od}/ambience.wav", ambience(total, rng))
    print("ok", total)
