# Procedural sound design for the zero-credit proofs (placeholders for licensed/generated SFX in the full build).
import numpy as np
SR = 48000
rng = np.random.default_rng(1879)
def _fft_filter(x, lo=None, hi=None, tilt=0.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo: g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: g *= 1 / (1 + (f / hi) ** 4)
    if tilt: g *= (np.maximum(f, 20) / 1000) ** tilt
    return np.fft.irfft(X * g, len(x)).astype(np.float32)
def norm(x, peak=1.0):
    m = np.abs(x).max() + 1e-9; return (x / m * peak).astype(np.float32)
def env_adsr(n, a, d, s_level, r):
    e = np.ones(n, np.float32) * s_level
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[na:na + nd] = np.linspace(1, s_level, nd)[: max(0, min(nd, n - na))]
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def reverb(x, t60=1.6, mix=0.35, pre=0.02):
    n = int(t60 * SR); ir = rng.standard_normal(n).astype(np.float32) * np.exp(-6.9 * np.arange(n) / n)
    ir = _fft_filter(ir, hi=5000); ir = np.concatenate([np.zeros(int(pre * SR), np.float32), ir])
    L = len(x) + len(ir) - 1; N = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:L]
    y = norm(y, np.abs(x).max()) * mix
    out = np.zeros(L, np.float32); out[: len(x)] += x * (1 - mix * 0.5); out += y
    return out
def stereo(m, width=0.3):
    d = int(0.011 * SR)
    l = m; r = np.concatenate([np.zeros(d, np.float32), m[:-d]])
    return np.stack([l * (1 - width / 2) + r * width / 2, r * (1 - width / 2) + l * width / 2], 1)
# ---- beds ----
def wind(dur, strength=1.0, gust=0.5):
    n = int(dur * SR)
    out = []
    for ch in range(2):
        b = _fft_filter(rng.standard_normal(n).astype(np.float32), lo=60, hi=900, tilt=-0.8)
        whistle = _fft_filter(rng.standard_normal(n).astype(np.float32), lo=600, hi=1600) * 0.25
        t = np.arange(n) / SR
        lfo = 0.6 + gust * 0.4 * np.sin(2 * np.pi * (0.07 + 0.02 * ch) * t + ch) + 0.2 * np.sin(2 * np.pi * 0.23 * t)
        out.append((b + whistle * (lfo - 0.5).clip(0)) * lfo)
    return norm(np.stack(out, 1), 0.5 * strength)
def drone(dur, base=55.0, swell=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t + p) for f, a, p in [(base, 1, 0), (base * 1.5, 0.5, 1), (base * 2.003, 0.35, 2), (base * 0.5, 0.6, 0.5)])
    x = x * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * t))
    e = np.linspace(0, 1, n) ** 1.5 if swell else np.ones(n)
    return stereo(norm(x * e, 0.5).astype(np.float32), 0.6)
# ---- events ----
def crack(dist=1.0):
    n = int(0.09 * SR); x = rng.standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / (0.006 * SR))
    body = np.sin(2 * np.pi * 95 * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.03 * SR))
    x = _fft_filter(x, lo=250, hi=9000 / dist) + 0.5 * body.astype(np.float32)
    return norm(x, 1.0 / dist)
def volley(n_shots=30, spread=0.5, dist=2.0, t60=1.8):
    L = int((spread + 0.2) * SR); out = np.zeros(L, np.float32)
    for _ in range(n_shots):
        c = crack(dist * rng.uniform(0.8, 1.4)); s = int(rng.uniform(0, spread) * SR)
        out[s:s + len(c)] += c[: L - s] * rng.uniform(0.4, 1.0)
    return stereo(reverb(norm(out, 0.9), t60, 0.5), 0.8)
def ragged_fire(dur, rate=6.0, dist=2.5):
    L = int(dur * SR); out = np.zeros(L, np.float32)
    k = int(dur * rate)
    for _ in range(k):
        c = crack(dist * rng.uniform(0.8, 1.6)); s = int(rng.uniform(0, dur - 0.1) * SR)
        out[s:s + len(c)] += c[: L - s] * rng.uniform(0.2, 0.8)
    return stereo(reverb(norm(out, 0.7), 2.0, 0.55), 0.9)
def cannon(dist=1.5):
    n = int(2.5 * SR); t = np.arange(n) / SR
    f = 55 * np.exp(-t * 1.2) + 28
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.0)
    blast = _fft_filter(rng.standard_normal(n).astype(np.float32), lo=30, hi=1800 / dist) * np.exp(-t * 6.0)
    x = norm(thump.astype(np.float32) + 0.7 * norm(blast), 1.0)
    return stereo(reverb(x, 3.2, 0.5, 0.05), 0.7)
def rush(dur, build=True):
    """Massed movement through grass: rustle swell plus irregular low footfalls."""
    n = int(dur * SR); t = np.arange(n) / SR
    rust = _fft_filter(rng.standard_normal(n).astype(np.float32), lo=1500, hi=7000)
    am = np.abs(_fft_filter(rng.standard_normal(n).astype(np.float32), hi=12)); am = am / am.max()
    rust *= 0.4 + am
    feet = np.zeros(n, np.float32)
    for s in rng.uniform(0, dur - 0.1, int(dur * 40)):
        k = int(s * SR); m = int(0.08 * SR)
        thud = np.sin(2 * np.pi * rng.uniform(50, 90) * np.arange(m) / SR) * np.exp(-np.arange(m) / (0.015 * SR))
        feet[k:k + m] += thud[: n - k] * rng.uniform(0.3, 1)
    x = norm(rust, 0.5) + norm(_fft_filter(feet, hi=400), 0.7)
    e = (np.linspace(0.15, 1, n) ** 1.2) if build else np.ones(n)
    return stereo(norm(x * e, 0.8), 0.9)
def whoosh(dur=1.2, up=True):
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float32)
    seg = 32; out = np.zeros(n, np.float32); step = n // seg
    for i in range(seg):
        u = i / seg; fc = 300 + (4000 if up else 1500) * (u if up else 1 - u)
        out[i * step:(i + 1) * step] = _fft_filter(x[i * step:(i + 1) * step], lo=fc * 0.5, hi=fc * 1.5)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return stereo(norm(out * e, 0.6), 0.8)
def sub_hit(dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (48 * np.exp(-t * 2) + 30) * t) * np.exp(-t * 2.2)
    return stereo(reverb(norm(x.astype(np.float32), 1.0), 2.5, 0.4), 0.5)
