"""Sound: narration track, music bed with automatic ducking, built-in sound effects, final mix."""
from __future__ import annotations

import json
import re
import subprocess

import numpy as np

from .util import FFMPEG, StudioError, clamp, run
from .voice import SR, read_audio, write_wav

SFX_NAMES = ("whoosh", "impact", "pop", "riser", "tick")


# ---------------------------------------------------------------- synthesis

def _band_noise(n, lo, hi, rng, tilt=-0.5):
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    mask *= np.maximum(f, 20) ** tilt
    x = np.fft.irfft(spec * mask, n)
    return x / (np.abs(x).max() + 1e-9)


def sfx(name, seed=0):
    """Royalty-free effects generated on the spot. Returns float32 stereo."""
    rng = np.random.default_rng(100 + seed)
    if name == "whoosh":
        n = int(0.6 * SR)
        t = np.linspace(0, 1, n)
        env = np.sin(np.pi * t) ** 2.6
        x = _band_noise(n, 350, 5200, rng) * env
        x += 0.25 * _band_noise(n, 90, 400, rng) * env
        pan = t
        st = np.stack([x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2)], axis=1)
        return (st * 0.55).astype(np.float32)
    if name == "impact":
        n = int(1.1 * SR)
        t = np.arange(n) / SR
        f = 46 + 60 * np.exp(-t * 18)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
        click = _band_noise(n, 800, 7000, rng) * np.exp(-t * 60) * 0.35
        tail = _band_noise(n, 60, 500, rng) * np.exp(-t * 6) * 0.25
        x = np.tanh((body + click + tail) * 1.4)
        return np.stack([x, x], axis=1).astype(np.float32) * 0.7
    if name == "pop":
        n = int(0.14 * SR)
        t = np.arange(n) / SR
        f = 520 + 700 * np.exp(-t * 55)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
        return np.stack([x, x], axis=1).astype(np.float32) * 0.5
    if name == "riser":
        n = int(1.6 * SR)
        t = np.linspace(0, 1, n)
        env = t ** 2.4
        x = _band_noise(n, 600, 9000, rng, tilt=0.0) * env * 0.7
        f = 180 * (7.0 ** t)
        x += np.sin(2 * np.pi * np.cumsum(f) / SR) * env * 0.25
        x[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
        return np.stack([x, x], axis=1).astype(np.float32) * 0.5
    if name == "tick":
        n = int(0.05 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 160)
        return np.stack([x, x], axis=1).astype(np.float32) * 0.4
    raise StudioError(f"Unknown sound effect '{name}'. Built-in: {', '.join(SFX_NAMES)} (or give a file path).")


def ambient_bed(seconds, seed=0):
    """A simple evolving pad so demos and drafts are not silent. Bring real music for finals."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    chords = [(110.0, 164.81, 220.0, 261.63), (87.31, 130.81, 174.61, 261.63),
              (130.81, 164.81, 196.0, 329.63), (98.0, 146.83, 196.0, 293.66)]
    bar = 6.0
    out = np.zeros((n, 2), dtype=np.float64)
    rng = np.random.default_rng(7 + seed)
    for ci in range(int(seconds / bar) + 2):
        start = ci * bar - 1.5
        env = np.clip((t - start) / 2.5, 0, 1) * np.clip((start + bar + 2.5 - t) / 2.5, 0, 1)
        env = np.sin(env * np.pi / 2) ** 2
        if not env.any():
            continue
        for f in chords[ci % len(chords)]:
            for det, pan in ((-0.35, 0.3), (0.35, 0.7)):
                ph = rng.uniform(0, 2 * np.pi)
                fr = f * (1 + det / 100)
                v = np.sin(2 * np.pi * fr * t + ph) + 0.28 * np.sin(4 * np.pi * fr * t + ph) \
                    + 0.10 * np.sin(6 * np.pi * fr * t)
                v *= env * (0.9 + 0.1 * np.sin(2 * np.pi * 0.11 * t + ph))
                out[:, 0] += v * (1 - pan)
                out[:, 1] += v * pan
    out /= np.abs(out).max() + 1e-9
    return (out * 0.5).astype(np.float32)


# ---------------------------------------------------------------- processing

def process(audio, filters):
    """Run float32 stereo audio through an ffmpeg filter chain."""
    raw = run([FFMPEG, "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-",
               "-af", filters, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
              data=audio.astype(np.float32).tobytes())
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def lufs(audio):
    """Integrated loudness (LUFS) measured by ffmpeg."""
    if len(audio) < SR // 2:
        return None
    p = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-",
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       input=audio.astype(np.float32).tobytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr.decode("utf-8", "replace"), re.S)
    if not m:
        return None
    try:
        v = float(json.loads(m.group(0))["input_i"])
    except (ValueError, KeyError):
        return None
    return v if v > -70 else None


def _gain_to(audio, target):
    cur = lufs(audio)
    if cur is None:
        return audio
    return audio * float(10 ** (clamp(target - cur, -30, 30) / 20))


def _place(mix, clip, start):
    i = int(round(start * SR))
    if i < 0:
        clip, i = clip[-i:], 0
    j = min(len(mix), i + len(clip))
    if j > i:
        mix[i:j] += clip[: j - i]


def _fade(clip, fin, fout):
    a, b = int(fin * SR), int(fout * SR)
    if a > 1 and len(clip) > a:
        clip[:a] *= np.linspace(0, 1, a, dtype=np.float32)[:, None]
    if b > 1 and len(clip) > b:
        clip[-b:] *= np.linspace(1, 0, b, dtype=np.float32)[:, None]
    return clip


def build_mix(total, voices, music=None, effects=(), voice_lufs=-16.0, progress=None):
    """Assemble the soundtrack.

    voices:  [(path, start_seconds)]
    music:   {"file"| "synth", "level_lufs", "duck_db", "start", "fade_in", "fade_out"} or None
    effects: [(name_or_path, start_seconds, gain_db)]
    """
    n = int(round(total * SR))
    vo = np.zeros((n, 2), dtype=np.float32)
    active = np.zeros(n // 480 + 2, dtype=np.float32)       # 10 ms grid: is someone speaking?
    for path, start in voices:
        clip = _fade(read_audio(path), 0.012, 0.045)
        _place(vo, clip, start)
        a, b = int(start * 100), int((start + len(clip) / SR) * 100) + 1
        active[max(0, a): min(len(active), b)] = 1.0
    if voices:
        vo = process(vo, "highpass=f=75,acompressor=threshold=-21dB:ratio=2.2:attack=8:release=140:makeup=1")[:n]
        if len(vo) < n:
            vo = np.pad(vo, ((0, n - len(vo)), (0, 0)))
        vo = _gain_to(vo, voice_lufs)
    mix = vo.copy()

    if music:
        if music.get("file"):
            bed = read_audio(music["file"])
            off = int(float(music.get("start", 0)) * SR)
            bed = bed[off:] if off < len(bed) else bed
            if len(bed) < SR:
                raise StudioError(f"Music file is too short: {music['file']}")
        else:
            bed = ambient_bed(total + 2)
        if len(bed) < n:                                   # loop with a 2 s crossfade
            x = min(2 * SR, len(bed) // 4)
            out = bed.copy()
            ramp = np.linspace(0, 1, x, dtype=np.float32)[:, None]
            while len(out) < n:
                tail = out[-x:] * (1 - ramp) + bed[:x] * ramp
                out = np.concatenate([out[:-x], tail, bed[x:]])
            bed = out
        bed = bed[:n].copy()
        bed = _gain_to(bed, float(music.get("level_lufs", -22.0)))
        duck = float(music.get("duck_db", -11.0))
        if voices and duck:
            env = active.copy()
            lead, hold = 20, 35                             # open 0.2 s early, hold 0.35 s
            idx = np.nonzero(env)[0]
            spread_env = np.zeros_like(env)
            for i in idx:
                spread_env[max(0, i - lead): i + hold] = 1.0
            k = np.hanning(61)
            sm = np.convolve(spread_env, k / k.sum(), mode="same")
            g = 10 ** (duck * np.interp(np.arange(n), np.arange(len(sm)) * 480, sm) / 20)
            bed *= g.astype(np.float32)[:, None]
        _fade(bed, float(music.get("fade_in", 0.8)), float(music.get("fade_out", 2.0)))
        mix += bed

    for i, (name, start, gain_db) in enumerate(effects):
        clip = sfx(name, i) if name in SFX_NAMES else read_audio(name)
        _place(mix, clip * float(10 ** (gain_db / 20)), start)

    peak = float(np.abs(mix).max()) if n else 0.0
    if peak > 0.97:
        mix = process(mix, "alimiter=limit=0.89:level=false:attack=3:release=60")[:n]
    return mix


def save(path, mix):
    write_wav(path, mix)
