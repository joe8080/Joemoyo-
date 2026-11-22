"""Repair bad audio and video.

    python -m studio fix clip.mp4            # diagnose, repair, re-measure
    python -m studio fix clip.mp4 --check    # diagnose only

It measures the file first, applies only the repairs the measurements call for,
then measures the result so the report shows before and after.

Audio: hiss/background noise, mains hum (50/60 Hz), clipping, one dead channel,
       rumble, harsh "s" sounds, uneven levels, too quiet / too loud.
Video: camera shake, under/over-exposure, flat contrast, colour cast, grain,
       interlacing, variable frame rate, optional upscale.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .util import FFMPEG, StudioError, clamp, digest, file_sig, lerp, probe, run

# Octave bands and where a finished music mix normally sits in each (dB relative to the mids).
BANDS = (63, 125, 250, 500, 1000, 2000, 4000, 8000, 14000)
MUSIC_TARGET = (1.0, 2.0, 1.5, 0.5, -0.5, -2.0, -5.0, -9.0, -14.0)

AUDIO_ONLY_EXT = {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg", ".opus"}
STRENGTH = {"light": 0.6, "normal": 1.0, "strong": 1.5}


# ================================================================ measuring

def _streams(path):
    info = probe(path)
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"
              and s.get("disposition", {}).get("attached_pic", 0) == 0), None)
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    dur = float(info.get("format", {}).get("duration") or 0)
    return info, v, a, dur


def _rate(s):
    try:
        n, d = str(s).split("/")
        return float(n) / float(d) if float(d) else 0.0
    except Exception:
        return 0.0


def _loudness(path, chain=None):
    """EBU R128 numbers via ffmpeg's loudnorm analysis (optionally after a filter chain)."""
    af = (chain + "," if chain else "") + "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json"
    p = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", af, "-f", "null", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode("utf-8", "replace"), re.S)
    if not m:
        return None
    try:
        d = {k: float(v) for k, v in json.loads(m.group(0)).items() if k != "normalization_type"}
    except ValueError:
        return None
    return d if math.isfinite(d.get("input_i", float("-inf"))) and d["input_i"] > -70 else None


def measure_audio(path, max_seconds=600):
    """Numbers that describe what is wrong with a soundtrack."""
    sr = 48000
    raw = run([FFMPEG, "-v", "error", "-i", str(path), "-vn", "-t", str(max_seconds),
               "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"])
    a = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
    if len(a) < sr // 4:
        return {"silent": True}
    m = {"seconds": len(a) / sr}
    rms = np.sqrt((a.astype(np.float64) ** 2).mean(axis=0)) + 1e-12
    db = 20 * np.log10(rms)
    m["left_db"], m["right_db"] = float(db[0]), float(db[1])
    m["dead_channel"] = None
    if abs(db[0] - db[1]) > 14:
        m["dead_channel"] = "right" if db[0] > db[1] else "left"
    mono = a[:, 0] if m["dead_channel"] == "right" else a[:, 1] if m["dead_channel"] == "left" else a.mean(axis=1)
    peak = float(np.abs(a).max())
    m["peak_db"] = 20 * math.log10(peak + 1e-12)
    # Clipping: flat tops, i.e. runs of identical loud samples (found even if turned down later).
    flat = (np.abs(np.diff(mono)) <= 1e-4 * max(peak, 1e-3)) & (np.abs(mono[1:]) > 0.4 * peak)
    m["clipped_pct"] = 100.0 * float(np.count_nonzero(flat[1:] & flat[:-1])) / len(mono)
    # Noise floor vs programme level, from 20 ms windows. Steady noise shows as a
    # plateau: the quietest moments all sit at the same level instead of falling away.
    win = sr // 50
    n = len(mono) // win
    w = mono[: n * win].reshape(n, win).astype(np.float64)
    wdb = np.maximum(10 * np.log10((w ** 2).mean(axis=1) + 1e-12), -100.0)
    m["level_db"] = float(np.percentile(wdb, 95))
    live = wdb[wdb > -95]
    if n < 10 or live.size < 10 or m["level_db"] < -70:
        return {"silent": True}
    m["floor_db"] = float(np.percentile(live, 3))
    m["snr_db"] = m["level_db"] - m["floor_db"]
    m["noise_steady"] = bool(float(np.percentile(live, 15)) - m["floor_db"] < 10.0)
    # Mains hum: narrow peaks at 50 or 60 Hz and their harmonics.
    seg = 1 << 16
    k = min(40, len(mono) // seg)
    m["hum_hz"], m["hum_db"] = None, 0.0
    if k >= 1:
        win_fn = np.hanning(seg)
        P = np.zeros(seg // 2 + 1)
        for i in range(k):
            P += np.abs(np.fft.rfft(mono[i * seg:(i + 1) * seg] * win_fn)) ** 2
        f = np.fft.rfftfreq(seg, 1 / sr)
        best = (0.0, None)
        for base in (50.0, 60.0):
            scores = []
            for h in (1, 2, 3):
                c = base * h
                pk = P[(f > c - 1.5) & (f < c + 1.5)].max()
                ring = P[((f > c - 14) & (f < c - 4)) | ((f > c + 4) & (f < c + 14))]
                scores.append(10 * math.log10((pk + 1e-20) / (np.median(ring) + 1e-20)))
            s = float(np.mean(sorted(scores)[1:]))        # two strongest harmonics
            if s > best[0]:
                best = (s, base)
        m["hum_db"] = best[0]
        if best[0] > 12:
            m["hum_hz"] = best[1]
        # Harsh sibilance: energy around 5-9 kHz against the speech body.
        hi = P[(f > 5000) & (f < 9000)].mean()
        mid = P[(f > 300) & (f < 3500)].mean()
        m["sibilance_db"] = 10 * math.log10((hi + 1e-20) / (mid + 1e-20))
        # Tonal balance: octave-band levels relative to the midrange (250 Hz - 2 kHz).
        lv = []
        for c in BANDS:
            sel = (f >= c / 1.414) & (f < c * 1.414)
            lv.append(10 * math.log10(P[sel].sum() + 1e-20))
        ref = float(np.mean(lv[2:6]))
        m["bands"] = [round(x - ref, 2) for x in lv]
        lowp = P[(f > 12) & (f < 44)].mean()
        m["rumble_db"] = 10 * math.log10((lowp + 1e-20) / (mid + 1e-20))
    ln = _loudness(path)
    m["lufs"] = ln["input_i"] if ln else None
    m["true_peak"] = ln["input_tp"] if ln else None
    m["lra"] = ln["input_lra"] if ln else None
    return m


def _gray(path, t, n, vf, w, h):
    raw = run([FFMPEG, "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(path), "-an", "-frames:v", str(n),
               "-vf", vf + ",format=gray", "-f", "rawvideo", "-"])
    k = len(raw) // (w * h)
    return np.frombuffer(raw[: k * w * h], dtype=np.uint8).reshape(k, h, w).astype(np.float32)


def _shift(a, b, win):
    """Sub-pixel translation between two frames by phase correlation. Returns (dx, dy, confidence)."""
    A, B = np.fft.rfft2((a - a.mean()) * win), np.fft.rfft2((b - b.mean()) * win)
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-9
    c = np.fft.irfft2(R, s=a.shape)
    h, w = c.shape
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    conf = float(c[iy, ix])

    def sub(vm, v0, vp):
        d = vm - 2 * v0 + vp
        return 0.0 if abs(d) < 1e-9 else clamp(0.5 * (vm - vp) / d, -0.5, 0.5)

    dx = ix + sub(c[iy, (ix - 1) % w], c[iy, ix], c[iy, (ix + 1) % w])
    dy = iy + sub(c[(iy - 1) % h, ix], c[iy, ix], c[(iy + 1) % h, ix])
    if dx > w / 2:
        dx -= w
    if dy > h / 2:
        dy -= h
    return dx, dy, conf


def measure_video(path, v, dur, pre=""):
    """Picture measurements. `pre` is a filter applied first (to judge a planned correction)."""
    pre = pre + "," if pre else ""
    W, H = int(v["width"]), int(v["height"])
    m = {"width": W, "height": H}
    r, avg = _rate(v.get("r_frame_rate")), _rate(v.get("avg_frame_rate"))
    m["fps"] = avg or r
    m["variable_rate"] = bool(r and avg and abs(r - avg) / max(r, avg) > 0.02)
    dur = dur or float(v.get("duration") or 0) or 1.0

    # Exposure, contrast and colour cast (sampled about 40 times across the clip).
    step = max(0.25, dur / 40)
    out = run([FFMPEG, "-v", "error", "-i", str(path), "-an",
               "-vf", f"fps=1/{step:.3f},{pre}scale=320:-2,signalstats,metadata=mode=print:file=-",
               "-f", "null", "-"]).decode("utf-8", "replace")
    vals = {}
    for key, val in re.findall(r"lavfi\.signalstats\.(\w+)=([\d.eE+-]+)", out):
        vals.setdefault(key, []).append(float(val))
    med = lambda k, d: float(np.median(vals[k])) if vals.get(k) else d
    m["sat"] = med("SATAVG", 40.0)
    m["u"], m["v"] = med("UAVG", 128.0), med("VAVG", 128.0)
    raw = run([FFMPEG, "-v", "error", "-i", str(path), "-an", "-frames:v", "40",
               "-vf", f"fps=1/{step:.3f},{pre}scale=64:36,format=rgb24", "-f", "rawvideo", "-"])
    rgb = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.float64)
    # Colour of the brightest 5% of the picture: whites and highlights should be neutral.
    m["white_rgb"] = [200.0, 200.0, 200.0]
    if len(rgb) > 100:
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
        top = rgb[lum >= np.percentile(lum, 95)]
        if len(top) and top.mean() > 40:
            m["white_rgb"] = [float(x) for x in top.mean(axis=0)]

    # Interlacing.
    p = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-an", "-frames:v", "240",
                        "-vf", "idet", "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mm = re.findall(r"Multi frame detection: TFF:\s*(\d+)\s*BFF:\s*(\d+)\s*Progressive:\s*(\d+)",
                    p.stderr.decode("utf-8", "replace"))
    m["interlaced"] = False
    if mm:
        tff, bff, prog = (int(x) for x in mm[-1])
        m["interlaced"] = (tff + bff) > 2 * max(1, prog) and (tff + bff) > 30

    aw = 320
    ah = max(2, int(round(H * aw / W / 2)) * 2)
    # Brightness: black point, average and white point over the whole clip (0-255).
    fr = _gray(path, 0, 40, f"fps=1/{step:.3f},{pre}scale={aw}:{ah}", aw, ah)
    if len(fr):
        m["black"], m["white"] = (float(x) for x in np.percentile(fr, [2, 98]))
        m["luma"] = float(fr.mean())
    else:
        m["black"], m["luma"], m["white"] = 10.0, 110.0, 235.0

    # Camera shake: how far the picture jitters around its own smoothed path.
    win = np.outer(np.hanning(ah), np.hanning(aw)).astype(np.float32)
    jit = []
    stamps = [dur * q for q in (0.12, 0.3, 0.5, 0.7, 0.86)] if dur > 3 else [0.0]
    for t in stamps:
        try:
            fr = _gray(path, t, 26, f"scale={aw}:{ah}", aw, ah)
        except StudioError:
            continue
        if len(fr) < 12:
            continue
        pos, cur, ok = [], np.zeros(2), 0
        for i in range(1, len(fr)):
            dx, dy, conf = _shift(fr[i - 1], fr[i], win)
            if conf > 0.06 and abs(dx) < aw * 0.2 and abs(dy) < ah * 0.2:
                cur = cur + (dx, dy)
                ok += 1
            pos.append(cur.copy())
        if ok < 0.7 * len(pos):
            continue
        pos = np.array(pos)
        ker = np.ones(9) / 9
        pad = np.pad(pos, ((4, 4), (0, 0)), mode="edge")
        smooth = np.stack([np.convolve(pad[:, j], ker, mode="valid") for j in (0, 1)], axis=1)
        resid = pos - smooth
        jit.append(float(np.sqrt((resid ** 2).sum(axis=1).mean())) / aw * 100)
    m["shake_pct"] = float(np.median(jit)) if jit else 0.0

    # Grain: frame-to-frame change in the calmest blocks of a centre crop.
    cw, ch = min(512, W - W % 2), min(512, H - H % 2)
    sig = []
    for t in ([dur * q for q in (0.15, 0.35, 0.55, 0.75, 0.9)] if dur > 2 else [0.0]):
        try:
            fr = _gray(path, t, 2, f"{pre}crop={cw}:{ch}", cw, ch)
        except StudioError:
            continue
        if len(fr) < 2:
            continue
        d = fr[1] - fr[0]
        b = 16
        blocks = d[: ch // b * b, : cw // b * b].reshape(ch // b, b, cw // b, b).swapaxes(1, 2).reshape(-1, b * b)
        sig.append(float(np.percentile(blocks.std(axis=1), 15)) / math.sqrt(2))
    m["noise"] = float(np.median(sig)) if sig else 0.0
    return m


# ================================================================ deciding

def plan_audio(m, strength="normal", music=False, target_lufs=-16.0):
    """Turn measurements into (findings, ffmpeg filter chain)."""
    k = STRENGTH[strength]
    finds, chain = [], []
    if m.get("silent"):
        return [("audio", "The soundtrack is silent", "nothing to repair")], []
    if m["dead_channel"]:
        live = "c0" if m["dead_channel"] == "right" else "c1"
        chain.append(f"pan=stereo|c0={live}|c1={live}")
        finds.append(("audio", f"Sound only in the {'left' if live == 'c0' else 'right'} channel",
                      "copied to both sides"))
    if m["clipped_pct"] > 0.01:
        chain.append("adeclip=window=55:overlap=75:arorder=8:threshold=8:hsize=1000:method=add")
        finds.append(("audio", f"Clipping / distortion on {m['clipped_pct']:.2f}% of samples",
                      "rebuilt the clipped peaks"))
    if not music and m.get("rumble_db", -99) > 0:
        chain.append("highpass=f=75")
        finds.append(("audio", "Low rumble (handling, traffic, wind)", "filtered below 75 Hz"))
    elif not music:
        chain.append("highpass=f=60")
    if m["hum_hz"]:
        base = m["hum_hz"]
        for h in (1, 2, 3, 4):
            chain.append(f"bandreject=f={base * h:.0f}:width_type=q:w=28")
        finds.append(("audio", f"Mains hum at {base:.0f} Hz ({m['hum_db']:.0f} dB above its surroundings)",
                      f"notched {base:.0f} Hz and three harmonics"))
    if not music and m["noise_steady"] and m["floor_db"] > -72 and m["snr_db"] < 45:
        gap = clamp((45 - m["snr_db"]) / 25, 0.25, 1.0)
        nr = clamp(round((8 + 16 * gap) * k), 6, 34)
        nf = clamp(round(m["floor_db"] - 2), -80, -20)
        chain.append(f"afftdn=nr={nr}:nf={nf}:tn=1")
        if strength == "strong":
            chain.append(f"afftdn=nr={max(6, nr // 2)}:nf={clamp(nf - 8, -80, -20)}:tn=1")
        # A gentle expander tucks what is left of the noise down between words.
        thr = 10 ** (clamp(m["floor_db"] - nr * 0.6 + 9, -75, -30) / 20)
        chain.append(f"agate=threshold={thr:.5f}:ratio=1.7:range=0.22:attack=4:release=160:knee=6")
        finds.append(("audio", f"Background noise / hiss (floor {m['floor_db']:.0f} dB, "
                               f"only {m['snr_db']:.0f} dB under the voice)", f"reduced by about {nr} dB"))
    if not music and strength == "strong" and m.get("sibilance_db", -99) > -12 and m["snr_db"] > 35:
        chain.append(f"deesser=i={clamp(0.3 * k, 0.15, 0.6):.2f}:m=0.5:f=0.5")
        finds.append(("audio", "Harsh 's' sounds", "softened"))
    if music and m.get("bands"):
        # Phone mics at gigs come out thin and fizzy: pull each band part-way to a normal mix balance.
        amt = min(0.85, 0.65 * k)
        gains = [clamp((t - b) * amt, -12.0, 5.0) for t, b in zip(MUSIC_TARGET, m["bands"])]
        if max(abs(g) for g in gains) > 3.0:
            bits = []                      # the correction itself is done by the matchtone + deharsh plugins
            treble = max(m["bands"][6] - MUSIC_TARGET[6], m["bands"][7] - MUSIC_TARGET[7])
            bass = MUSIC_TARGET[0] - m["bands"][0]
            mud = max(m["bands"][1] - MUSIC_TARGET[1], m["bands"][2] - MUSIC_TARGET[2])
            if treble > 4:
                bits.append(f"harsh treble ({treble:.0f} dB too strong)")
            if bass > 6:
                bits.append(f"thin bass ({bass:.0f} dB short)")
            if mud > 4:
                bits.append(f"boomy low-mids ({mud:.0f} dB too strong)")
            finds.append(("audio", "Unbalanced tone: " + (", ".join(bits) or "uneven frequency balance"),
                          "matched to a finished-mix balance and dynamically de-harshed"))
    if music and (m.get("true_peak") or -9) > -0.3:
        finds.append(("audio", f"Overloaded peaks ({m['true_peak']:+.1f} dB true peak)",
                      "level brought down under the ceiling (distortion already recorded cannot be undone)"))
    if not music and (m.get("lra") or 0) > 11:
        chain.append("dynaudnorm=f=300:g=17:p=0.9:m=6")
        finds.append(("audio", f"Uneven volume (swings of {m['lra']:.0f} LU)", "levelled"))
    elif not music:
        chain.append("acompressor=threshold=-22dB:ratio=2:attack=10:release=150:makeup=1")
    if m.get("lufs") is not None and abs(m["lufs"] - target_lufs) > 1.0:
        word = "quiet" if m["lufs"] < target_lufs else "loud"
        finds.append(("audio", f"Too {word} ({m['lufs']:.1f} LUFS)", f"set to {target_lufs:.0f} LUFS"))
    return finds, chain


def plan_tone(m, strength="normal"):
    """Exposure and contrast: one tone curve that moves black, average and white to sane places."""
    k = STRENGTH[strength]
    finds = []
    kk = min(1.0, 0.75 * k)
    lo, mid, hi = m["black"] / 255, m["luma"] / 255, m["white"] / 255
    t_lo = lo if lo < 0.10 else lerp(lo, 0.04, kk)
    t_hi = hi if hi > 0.80 else min(lerp(hi, 0.88, kk), hi * 4 + 0.02)
    m_lin = t_lo + (mid - lo) * (t_hi - t_lo) / max(hi - lo, 1e-3)
    t_mid = m_lin
    if m_lin < 0.28:
        t_mid = min(lerp(m_lin, 0.36, kk * 0.85), max(m_lin, mid) * 6 + 0.02)
    elif m_lin > 0.70:
        t_mid = lerp(m_lin, 0.60, kk * 0.85)
    pts = [(0.0, 0.0)]
    for x, y in ((lo, t_lo), (mid, t_mid), (hi, t_hi)):
        if x - pts[-1][0] >= 0.03 and x <= 0.96:
            pts.append((x, clamp(max(y, pts[-1][1] + 0.005), 0.0, 0.99)))
    pts.append((1.0, 1.0))
    if max(abs(y - x) for x, y in pts) <= 0.04:
        return finds, None
    if mid < 0.28 and t_mid > mid + 0.04:
        finds.append(("video", f"Too dark (average brightness {m['luma']:.0f} of 255)", "lifted"))
    elif mid > 0.70 and t_mid < mid - 0.04:
        finds.append(("video", f"Too bright (average brightness {m['luma']:.0f} of 255)", "pulled down"))
    if hi - lo < 0.5 and (t_hi - t_lo) > (hi - lo) + 0.05:
        finds.append(("video", f"Flat, washed-out contrast (range {m['white'] - m['black']:.0f} of 255)",
                      "stretched toward full range"))
    if not finds:
        finds.append(("video", "Dull tones", "tone curve adjusted"))
    return finds, "curves=interp=pchip:master='" + " ".join(f"{x:.3f}/{y:.3f}" for x, y in pts) + "'"


def plan_video(m, m2, curve, strength="normal", stabilize="auto", upscale=None):
    """m = the file as it is; m2 = measured with the tone curve applied.

    Returns (findings, filter list, needs_stabilize, force_fps)."""
    k = STRENGTH[strength]
    finds, vf = [], []
    if m["interlaced"]:
        vf.append("bwdif=mode=send_frame")
        finds.append(("video", "Interlaced (combing lines on movement)", "deinterlaced"))
    stab = stabilize == "on" or (stabilize == "auto" and m["shake_pct"] > 0.22)
    if stab:
        finds.append(("video", f"Camera shake ({m['shake_pct']:.2f}% of frame width)", "stabilised"))
    # Denoise before brightening: grain is far easier to remove while it is still small.
    if m2["noise"] > 1.8:
        sp = clamp(max(m["noise"], m2["noise"] * 0.3) * 1.3 * k, 1.5, 14.0)
        if strength == "strong" and m2["noise"] > 6:
            vf.append(f"nlmeans=s={clamp(m['noise'] * 0.8, 1.5, 10):.1f}:p=3:r=5")
            sp *= 0.5
        vf.append(f"hqdn3d={sp:.1f}:{sp * 0.8:.1f}:{sp * 2:.1f}:{sp * 1.5:.1f}")
        why = " once brightened" if curve and m2["noise"] > m["noise"] * 1.3 else ""
        finds.append(("video", f"Grain / sensor noise (level {m2['noise']:.1f}{why})", "denoised"))
    if curve:
        vf.append(curve)
    r, g, b = (max(1.0, c) for c in m2["white_rgb"])
    grey = (r + g + b) / 3
    dev = max(abs(c - grey) / grey for c in (r, g, b))
    if dev > 0.08 and m2["sat"] > 6:
        f = min(0.85, 0.6 * k)
        gains = [clamp(lerp(1.0, grey / c, f), 0.78, 1.28) for c in (r, g, b)]
        lum = 0.2126 * gains[0] * r + 0.7152 * gains[1] * g + 0.0722 * gains[2] * b
        norm = (0.2126 * r + 0.7152 * g + 0.0722 * b) / lum
        gains = [x * norm for x in gains]
        vf.append(f"colorchannelmixer=rr={gains[0]:.3f}:gg={gains[1]:.3f}:bb={gains[2]:.3f}")
        tint = ["red", "green", "blue"][int(np.argmax([r, g, b]))]
        finds.append(("video", f"Colour cast toward {tint} (whites {dev * 100:.0f}% off neutral)",
                      f"white balance corrected by {int(f * 100)}%"))
    if any(x.startswith("hqdn3d") for x in vf) or stab or upscale:
        vf.append(f"cas={clamp(0.35 * k, 0.2, 0.7):.2f}")
    if upscale:
        th = int(upscale)
        if th > m["height"]:
            tw = int(round(m["width"] * th / m["height"] / 2)) * 2
            vf.append(f"scale={tw}:{th}:flags=lanczos")
            finds.append(("video", f"Low resolution ({m['width']}x{m['height']})",
                          f"upscaled to {tw}x{th} (sharp resize, not AI detail)"))
    fps = None
    if m["variable_rate"]:
        fps = round(m["fps"] or 30)
        fps = min((24, 25, 30, 50, 60), key=lambda r_: abs(r_ - fps))
        finds.append(("video", "Variable frame rate (causes sound drifting out of sync in editors)",
                      f"locked to {fps} fps"))
    return finds, vf, stab, fps


# ================================================================ doing

def fix(src, out=None, audio=True, video=True, strength="normal", stabilize="auto", upscale=None,
        target_lufs=-16.0, music=False, report_only=False, log=print, frame="full"):
    """frame: 'full' stabilises without cropping the picture; 'crop' zooms in slightly instead."""
    src = Path(src)
    if not src.is_file():
        raise StudioError(f"File not found: {src}")
    if strength not in STRENGTH:
        raise StudioError("strength must be light, normal or strong.")
    info, v, a, dur = _streams(src)
    if not v and not a:
        raise StudioError(f"{src.name} has no audio or video to repair.")
    res = {"input": str(src), "output": None, "findings": [], "before": {}, "after": {}, "music": music}
    af, vf, stab, fps = [], [], False, None
    if a and audio:
        log("Listening to the audio...")
        ma = measure_audio(src)
        res["before"]["audio"] = ma
        finds, af = plan_audio(ma, strength, music, target_lufs)
        res["findings"] += finds
    if v and video:
        log("Looking at the picture...")
        mv = measure_video(src, v, dur)
        tone_finds, curve = plan_tone(mv, strength)
        mv2 = measure_video(src, v, dur, pre=curve) if curve else mv
        res["before"]["video"] = mv
        res["before"]["video_lifted"] = mv2
        finds, vf, stab, fps = plan_video(mv, mv2, curve, strength, stabilize, upscale)
        res["findings"] += tone_finds + finds
    real = [f for f in res["findings"] if f[2] != "nothing to repair"]
    if report_only:
        return res
    if not real:
        res["note"] = "Nothing needed repairing."
        return res

    if out is None:
        ext = ".mp4" if v else (src.suffix.lower() if src.suffix.lower() in (".wav", ".mp3", ".m4a", ".flac") else ".wav")
        out = src.with_name(f"{src.stem}_fixed{ext}")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="studiofix_") as tmp:
        fix_audio = bool(a and audio and any(f[0] == "audio" for f in real))
        fix_video = bool(v and video and (vf or stab or fps))
        if stab:
            log("Studying the camera movement...")
            pre = ",".join(x for x in vf if x.startswith("bwdif"))
            p = subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(src.resolve()), "-an",
                                "-vf", (pre + "," if pre else "") + "format=yuv420p,vidstabdetect=shakiness=7:accuracy=15:result=t.trf",
                                "-f", "null", "-"], cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if p.returncode or not (Path(tmp) / "t.trf").is_file():
                raise StudioError("Stabiliser analysis failed:\n" + p.stderr.decode("utf-8", "replace")[-500:])
            rate = res["before"]["video"]["fps"] or 30
            smooth = int(clamp(round(rate * 0.6 * STRENGTH[strength]), 8, 60))
            # The stabiliser only accepts planar YUV; pin the format on both sides so later
            # colour filters cannot make ffmpeg hand it RGB.
            how = "optzoom=0:zoom=0:interpol=bicubic:crop=keep" if frame == "full" else \
                "optzoom=1:interpol=bicubic:crop=black"
            tr = f"format=yuv420p,vidstabtransform=input=t.trf:smoothing={smooth}:{how},format=yuv420p"
            i = 1 if vf and vf[0].startswith("bwdif") else 0
            vf.insert(i, tr)
        cmd = [FFMPEG, "-v", "error", "-y", "-i", str(src.resolve())]
        a_map = "0:a:0"
        if fix_audio:
            log("Repairing the audio...")
            a_src = src
            if music and any("Unbalanced tone" in f[1] for f in real):
                from . import plugins as PL
                from .voice import read_audio, write_wav
                y, notes = PL.run_audio(read_audio(src), PL.resolve("matchtone,deharsh"))
                res["plugin_notes"] = notes
                a_src = Path(tmp) / "music.wav"
                write_wav(a_src, y)
                cmd += ["-i", str(a_src)]
                a_map = "1:a:0"
            chain = ",".join(af)
            ln = _loudness(a_src, chain or None)
            if ln:
                norm = (f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:measured_I={ln['input_i']}:"
                        f"measured_TP={ln['input_tp']}:measured_LRA={ln['input_lra']}:"
                        f"measured_thresh={ln['input_thresh']}:offset={ln['target_offset']}:linear=true")
            else:
                norm = f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"
            chain = (chain + "," if chain else "") + norm + ",alimiter=limit=0.84:level=false"
            cmd += ["-af", chain, "-ar", "48000"]
        if v:
            cmd += ["-map", "0:v:0"]
            if fix_video:
                log("Repairing the picture..." + (" (stabilising takes a little longer)" if stab else ""))
                if vf:
                    cmd += ["-vf", ",".join(vf)]
                if fps:
                    cmd += ["-r", str(fps), "-fps_mode", "cfr"]
                cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p"]
            else:
                cmd += ["-c:v", "copy"]
            if a:
                cmd += ["-map", a_map, "-c:a", "aac", "-b:a", "256k"] if fix_audio else ["-map", "0:a:0", "-c:a", "copy"]
            cmd += ["-movflags", "+faststart"]
        else:
            codec = {".mp3": ["-c:a", "libmp3lame", "-b:a", "192k"], ".m4a": ["-c:a", "aac", "-b:a", "192k"],
                     ".flac": ["-c:a", "flac"]}.get(out.suffix.lower(), ["-c:a", "pcm_s16le"])
            cmd += ["-map", a_map, "-vn", *codec]
        tmp_out = out.with_name(out.stem + ".part" + out.suffix)
        p = subprocess.run(cmd + [str(tmp_out.resolve())], cwd=tmp, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode:
            tmp_out.unlink(missing_ok=True)
            raise StudioError("Repair failed:\n" + p.stderr.decode("utf-8", "replace")[-700:])
        tmp_out.replace(out)
    res["output"] = str(out)

    log("Checking the result...")
    _, v2, a2, dur2 = _streams(out)
    if a2 and audio and "audio" in res["before"]:
        res["after"]["audio"] = measure_audio(out)
    if v2 and video and "video" in res["before"]:
        res["after"]["video"] = measure_video(out, v2, dur2)
    return res


def fixed_copy(src, cache_dir, **kw):
    """Repair into a cache folder (used by projects). Returns the path to use."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    src = Path(src)
    is_audio = src.suffix.lower() in AUDIO_ONLY_EXT
    out = cache_dir / f"fixed_{digest([file_sig(src), sorted(kw.items())])}{'.wav' if is_audio else '.mp4'}"
    marker = out.with_suffix(".same")
    if out.is_file():
        return str(out)
    if marker.is_file():
        return str(src)
    res = fix(src, out=out, log=lambda *_: None, **kw)
    if not res["output"]:
        marker.write_text("clean")
        return str(src)
    return res["output"]


# ================================================================ reporting

def format_report(res):
    L = [f"\nRepair report: {Path(res['input']).name}", "-" * 60]
    if not res["findings"]:
        L.append("No problems found. The file is fine as it is.")
    for area, issue, action in res["findings"]:
        L.append(f"  [{area}] {issue}  ->  {action}")
    b, a = res["before"], res["after"]
    rows = []
    if "audio" in b and "audio" in a and not b["audio"].get("silent") and not a["audio"].get("silent"):
        x, y = b["audio"], a["audio"]
        if x.get("lufs") is not None and y.get("lufs") is not None:
            rows.append(("Loudness (LUFS)", f"{x['lufs']:.1f}", f"{y['lufs']:.1f}"))
        if not res.get("music"):
            rows.append(("Noise floor (dB)", f"{x['floor_db']:.0f}", f"{y['floor_db']:.0f}"))
            rows.append(("Voice above noise (dB)", f"{x['snr_db']:.0f}", f"{y['snr_db']:.0f}"))
        rows.append(("Hum (dB over surroundings)", f"{x['hum_db']:.0f}", f"{y['hum_db']:.0f}"))
        rows.append(("Clipped samples (%)", f"{x['clipped_pct']:.2f}", f"{y['clipped_pct']:.2f}"))
        if x.get("bands") and y.get("bands"):
            rows.append(("Treble vs mids at 8 kHz (dB)", f"{x['bands'][7]:+.0f}", f"{y['bands'][7]:+.0f}"))
            rows.append(("Bass vs mids at 63 Hz (dB)", f"{x['bands'][0]:+.0f}", f"{y['bands'][0]:+.0f}"))
        if x.get("true_peak") is not None and y.get("true_peak") is not None:
            rows.append(("True peak (dB)", f"{x['true_peak']:+.1f}", f"{y['true_peak']:+.1f}"))
    if "video" in b and "video" in a:
        x, y = b["video"], a["video"]
        rows.append(("Brightness (0-255)", f"{x['luma']:.0f}", f"{y['luma']:.0f}"))
        rows.append(("Black to white range", f"{x['white'] - x['black']:.0f}", f"{y['white'] - y['black']:.0f}"))
        rows.append(("Shake (% of width)", f"{x['shake_pct']:.2f}", f"{y['shake_pct']:.2f}"))
        x2 = b.get("video_lifted", x)
        cast = lambda q: 100 * max(abs(c - sum(q["white_rgb"]) / 3) for c in q["white_rgb"]) / max(1.0, sum(q["white_rgb"]) / 3)
        same = " (at corrected brightness)" if x2 is not x else ""
        rows.append(("Grain level" + same, f"{x2['noise']:.1f}", f"{y['noise']:.1f}"))
        rows.append(("Colour cast in whites (% off neutral)", f"{cast(x2):.0f}", f"{cast(y):.0f}"))
    if rows:
        L.append("")
        L.append(f"  {'Measure':<44}{'before':>9}{'after':>9}")
        for name, x, y in rows:
            L.append(f"  {name:<44}{x:>9}{y:>9}")
    for n in res.get("plugin_notes", []):
        L.append("  plugin " + n)
    if res.get("note"):
        L.append(res["note"])
    if res.get("output"):
        L.append(f"\nFixed file: {res['output']}")
    return "\n".join(L)
