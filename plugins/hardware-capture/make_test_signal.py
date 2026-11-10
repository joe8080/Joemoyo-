#!/usr/bin/env python3
"""Generate the MOYO hardware capture test signal.

Plays through a piece of outboard gear (compressor, saturator, preamp) and is
recorded back. Each section measures one thing, and the manifest records where
each section starts so the recordings can be analysed automatically.

    python3 make_test_signal.py OUT_DIR          # writes the WAV + manifest
    python3 make_test_signal.py --selftest       # checks the file can be analysed

Output: 48 kHz, 24-bit, mono, peaks at -3 dBFS.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

FS = 48000
SEED = 20261110
WAV_NAME = "MOYO_capture_test_48k.wav"
MANIFEST_NAME = "MOYO_capture_test_manifest.json"


def db(x):
    return 10.0 ** (x / 20.0)


def fade(x, ms=5.0):
    n = min(int(FS * ms / 1000), len(x) // 2)
    if n > 0:
        w = 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)
        x[:n] *= w
        x[-n:] *= w[::-1]
    return x


def silence(sec):
    return np.zeros(int(FS * sec))


def tone(freq, sec, level_db, phase=0.0):
    t = np.arange(int(FS * sec)) / FS
    return db(level_db) * np.sin(2 * np.pi * freq * t + phase)


def lin_chirp(f0, f1, sec, level_db):
    t = np.arange(int(FS * sec)) / FS
    ph = 2 * np.pi * (f0 * t + (f1 - f0) * t * t / (2 * sec))
    return fade(db(level_db) * np.sin(ph), 10)


def log_sweep(f0, f1, sec, level_db):
    """Exponential sine sweep (Farina). Harmonics separate cleanly on deconvolution."""
    t = np.arange(int(FS * sec)) / FS
    k = np.log(f1 / f0)
    ph = 2 * np.pi * f0 * sec / k * (np.exp(t / sec * k) - 1.0)
    return fade(db(level_db) * np.sin(ph), 20)


def pink(n, rng):
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / FS)
    spec[1:] /= np.sqrt(f[1:])
    spec[0] = 0
    x = np.fft.irfft(spec, n)
    return x / np.max(np.abs(x))


def bandlimit(x, lo, hi):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / FS)
    spec[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(spec, len(x))


def program_material(sec, rng):
    """Vocal-like material: pitched harmonics + breath noise under a syllable envelope.

    Used to check the finished model against the hardware on something closer to
    a real performance than test tones.
    """
    n = int(FS * sec)
    t = np.arange(n) / FS

    # Syllable envelope: random on/off blocks at varying loudness.
    env = np.zeros(n)
    pos = 0
    while pos < n:
        on = int(FS * rng.uniform(0.08, 0.45))
        off = int(FS * rng.uniform(0.03, 0.30))
        level = db(rng.uniform(-30, -5))
        seg = np.ones(min(on, n - pos)) * level
        env[pos:pos + len(seg)] = fade(seg, 12)
        pos += on + off
    # A few long held notes so slow release behaviour shows up.
    for start in (0.22, 0.55, 0.8):
        a = int(n * start)
        b = min(n, a + int(FS * rng.uniform(1.2, 2.2)))
        env[a:b] = np.maximum(env[a:b], fade(np.ones(b - a) * db(rng.uniform(-12, -5)), 30))

    # Gliding pitch, 12 harmonics with a vocal-ish rolloff.
    f0 = 140 + 70 * np.sin(2 * np.pi * 0.13 * t) + 25 * np.sin(2 * np.pi * 0.71 * t + 1.0)
    ph = 2 * np.pi * np.cumsum(f0) / FS
    voiced = sum(np.sin(h * ph + rng.uniform(0, 6.28)) / h ** 1.2 for h in range(1, 13))
    voiced /= np.max(np.abs(voiced))

    breath = bandlimit(pink(n, rng), 1500, 12000)
    breath /= np.max(np.abs(breath))
    sib_gate = (np.sin(2 * np.pi * 0.9 * t + 0.4) > 0.75).astype(float)  # occasional "s" sounds

    x = env * (0.8 * voiced + 0.12 * breath + 0.5 * sib_gate * breath)
    return x / np.max(np.abs(x)) * db(-4)


def build():
    rng = np.random.default_rng(SEED)
    parts, manifest = [], []

    def add(name, x, **meta):
        start = sum(len(p) for p in parts)
        parts.append(np.asarray(x, dtype=np.float64))
        manifest.append({"name": name, "start": start, "length": len(x), **meta})

    add("lead_in", silence(0.5))
    add("sync_start", lin_chirp(1000, 8000, 0.25, -12), f0=1000, f1=8000)
    add("gap", silence(0.5))

    # Reference tone: used to set the unit's gain and to calibrate levels.
    add("ref_tone", fade(tone(1000, 6.0, -18)), freq=1000, level_db=-18)
    add("noise_floor", silence(2.0))

    # Frequency response + harmonics at four drive levels.
    for lvl in (-36, -24, -12, -3):
        add(f"sweep_{abs(lvl)}", log_sweep(20, 22000, 8.0, lvl), f0=20, f1=22000, level_db=lvl)
        add("gap", silence(2.0))

    # Static compression curve: 1 kHz rising in 3 dB steps.
    levels = list(range(-48, 0, 3))
    stair = np.concatenate([tone(1000, 1.5, l) for l in levels])
    add("stairs_1k", fade(stair), freq=1000, levels_db=levels, step_sec=1.5)
    add("gap", silence(3.0))

    # Attack and release: loud bursts sitting on a quiet probe tone, so the
    # gain recovery is visible after each burst. Opto release depends on how
    # long the unit was compressing, hence the different burst lengths.
    probe = -30
    bursts = [(-6, 0.05, 5.0), (-6, 0.25, 5.0), (-6, 1.0, 5.0), (-6, 4.0, 10.0), (-15, 1.0, 5.0)]
    chunks, burst_meta, cursor = [tone(1000, 2.0, probe)], [], int(FS * 2.0)
    for lvl, dur, rec in bursts:
        chunks += [tone(1000, dur, lvl), tone(1000, rec, probe)]
        burst_meta.append({"level_db": lvl, "start": cursor, "length": int(FS * dur), "recovery": int(FS * rec)})
        cursor += int(FS * dur) + int(FS * rec)
    add("bursts_1k", fade(np.concatenate(chunks)), freq=1000, probe_db=probe, bursts=burst_meta)
    add("gap", silence(3.0))

    # Does it compress bass and treble as hard as mids? (sidechain response)
    for f in (100, 300, 1000, 3000, 10000):
        add(f"sc_tone_{f}", fade(tone(f, 2.0, -9), 10), freq=f, level_db=-9)
        add("gap", silence(2.0))

    # Intermodulation: low tone + high tone together.
    imd = 0.8 * np.sin(2 * np.pi * 60 * np.arange(FS * 3) / FS) + 0.2 * np.sin(2 * np.pi * 7000 * np.arange(FS * 3) / FS)
    add("imd_60_7k", fade(imd * db(-12)), f_low=60, f_high=7000, level_db=-12)
    add("gap", silence(2.0))

    add("program", fade(program_material(30.0, rng), 20))
    add("gap", silence(3.0))
    add("sync_end", lin_chirp(8000, 1000, 0.25, -12), f0=8000, f1=1000)
    add("lead_out", silence(0.5))

    x = np.concatenate(parts)
    assert np.max(np.abs(x)) <= db(-3) + 1e-9, "peak above -3 dBFS"
    return x, manifest


def write_wav24(path, x):
    ints = np.clip(np.round(x * (2 ** 23 - 1)), -(2 ** 23), 2 ** 23 - 1).astype(np.int32)
    raw = ints.astype("<i4").tobytes()
    # drop the top byte of every little-endian int32 -> 24-bit samples
    data = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)[:, :3].tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(FS)
        w.writeframes(data)


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        assert w.getsampwidth() == 3 and w.getnchannels() == 1 and w.getframerate() == FS
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.uint8).reshape(-1, 3)
    ints = raw[:, 0].astype(np.int32) | (raw[:, 1].astype(np.int32) << 8) | (raw[:, 2].astype(np.int8).astype(np.int32) << 16)
    return ints / float(2 ** 23 - 1)


def find_marker(rec, marker):
    """Sample offset of `marker` inside `rec`, by FFT cross-correlation."""
    n = len(rec) + len(marker)
    corr = np.fft.irfft(np.fft.rfft(rec, n) * np.conj(np.fft.rfft(marker, n)), n)
    return int(np.argmax(np.abs(corr[:len(rec)])))


def selftest():
    """Push the signal through a fake compressor and check the analysis recovers it."""
    x, manifest = build()
    seg = {m["name"]: m for m in manifest if m["name"] != "gap"}

    # Fake hardware: 3:1 above -20 dBFS, 10 ms attack / 300 ms release, 1.5 dB loss, 737-sample delay.
    thr, ratio, delay, trim = -20.0, 3.0, 737, db(-1.5)
    a_att, a_rel = np.exp(-1 / (0.010 * FS)), np.exp(-1 / (0.300 * FS))
    env, y = 0.0, np.empty_like(x)
    for i, s in enumerate(x):
        r = abs(s)
        env = r + (a_att if r > env else a_rel) * (env - r)
        over = 20 * np.log10(max(env, 1e-9)) - thr
        y[i] = s * (db(-over * (1 - 1 / ratio)) if over > 0 else 1.0)
    rec = np.concatenate([np.zeros(delay), y * trim, np.zeros(1000)])

    ok = True

    def check(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(("ok:   " if cond else "FAIL: ") + msg)

    # 1. Alignment from the two sync chirps (also detects speed/stretch errors).
    s0, s1 = seg["sync_start"], seg["sync_end"]
    d0 = find_marker(rec, x[s0["start"]:s0["start"] + s0["length"]]) - s0["start"]
    d1 = find_marker(rec, x[s1["start"]:s1["start"] + s1["length"]]) - s1["start"]
    check(d0 == delay and d1 == delay, f"sync chirps recover the delay: start {d0}, end {d1} (true {delay})")
    aligned = rec[d0:d0 + len(x)]

    # 2. Static curve from the stairs: threshold and ratio.
    st = seg["stairs_1k"]
    step = int(st["step_sec"] * FS)
    out_db = []
    for i, _ in enumerate(st["levels_db"]):
        a = st["start"] + i * step + step // 2  # second half of each step = settled
        out_db.append(20 * np.log10(np.sqrt(2) * np.sqrt(np.mean(aligned[a:a + step // 2 - 100] ** 2))))
    in_db = np.array(st["levels_db"], float)
    out_db = np.array(out_db) + 1.5  # remove the known trim
    low = in_db < thr - 3
    high = in_db > thr + 3
    slope_low = np.polyfit(in_db[low], out_db[low], 1)[0]
    slope_high = np.polyfit(in_db[high], out_db[high], 1)[0]
    check(abs(slope_low - 1) < 0.02, f"below threshold the curve is 1:1 (slope {slope_low:.3f})")
    check(abs(1 / slope_high - ratio) < 0.15, f"above threshold ratio = {1 / slope_high:.2f}:1 (true {ratio}:1)")

    # 3. Release time from gain recovery after the 1 s burst.
    b = seg["bursts_1k"]
    burst = b["bursts"][2]
    a = b["start"] + burst["start"] + burst["length"]
    win = int(0.01 * FS)
    rms = np.array([np.sqrt(np.mean(aligned[a + k * win:a + (k + 1) * win] ** 2)) for k in range(int(2.0 / 0.01))])
    gain_db = 20 * np.log10(rms * np.sqrt(2)) - b["probe_db"] + 1.5
    t63 = np.argmax(gain_db > gain_db[0] * (1 - 0.63)) * 0.01
    check(0.1 < t63 < 0.6, f"release visible on the probe tone: 63% recovery in {t63 * 1000:.0f} ms (fake unit: ~300 ms)")

    # 4. Round-trip through the 24-bit WAV writer.
    tmp = Path("/tmp") / "moyo_selftest.wav" if len(sys.argv) < 3 else Path(sys.argv[2]) / "moyo_selftest.wav"
    write_wav24(tmp, x)
    back = read_wav(tmp)
    tmp.unlink()
    check(len(back) == len(x) and np.max(np.abs(back - x)) < 2 ** -22, "24-bit WAV round-trips exactly")

    print("\nSELF-TEST PASSED" if ok else "\nSELF-TEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        return selftest()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    x, manifest = build()
    write_wav24(out / WAV_NAME, x)
    (out / MANIFEST_NAME).write_text(json.dumps({"fs": FS, "seed": SEED, "samples": len(x), "segments": manifest}, indent=1))
    print(f"{WAV_NAME}: {len(x) / FS:.1f} s, peak {20 * np.log10(np.max(np.abs(x))):.2f} dBFS, "
          f"{(out / WAV_NAME).stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
