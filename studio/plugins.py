"""Plugins: small single-purpose processors you can chain, tune and extend.

    python -m studio plugins                         # list them
    python -m studio plug gig clip.mp4               # run a ready-made chain
    python -m studio plug matchtone,deharsh,level song.wav --set level.lufs=-14
    python -m studio plug matchtone take.wav --set matchtone.ref=record_i_love.wav

Add your own: drop a .py file in `studio_plugins/` (next to the `studio` folder) or in
`~/.studio/plugins/`. See `studio_plugins/example_plugin.py`.

Audio plugins take and return stereo float32 audio. Video plugins return ffmpeg filters.
"""
from __future__ import annotations

import importlib.util
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .util import FFMPEG, StudioError, clamp, probe

SR = 48000
REGISTRY: dict = {}
CHAINS: dict = {}

# Third-octave band centres and tonal targets (dB relative to the 500-1250 Hz average).
THIRDS = (50, 80, 125, 200, 315, 500, 800, 1250, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000)
TARGETS = {
    # A finished live-band / rock mix. Chosen by ear on real gig footage (option "B").
    "live": (0, 2, 2, 2, 1, 0.5, 0, -1, -3, -4, -5, -6, -8, -9, -11, -13, -15, -18),
    # Spoken voice: less low end, a touch more presence.
    "voice": (-12, -6, -1, 1, 1, 0.5, 0, -1, -2, -3, -4, -6, -8, -10, -13, -16, -19, -22),
}


class Plugin:
    def __init__(self, name, kind, summary, params, fn):
        self.name, self.kind, self.summary, self.params, self.fn = name, kind, summary, params, fn


def plugin(name, kind, summary, **params):
    """Register a plugin. `params` maps each setting to (default, description)."""
    if kind not in ("audio", "video"):
        raise ValueError("kind must be 'audio' or 'video'")

    def deco(fn):
        REGISTRY[name] = Plugin(name, kind, summary, params, fn)
        return fn
    return deco


def chain(name, summary, steps):
    """Register a ready-made chain: steps is a list of plugin names or (name, {settings})."""
    CHAINS[name] = (summary, [(s, {}) if isinstance(s, str) else (s[0], dict(s[1])) for s in steps])


# ================================================================ audio helpers

def third_octave(x, sr=SR):
    """Long-term third-octave levels of mono audio, relative to the 500-1250 Hz average."""
    seg = 1 << 14
    if len(x) < seg:
        x = np.pad(x, (0, seg - len(x)))
    k = len(x) // seg
    w = np.hanning(seg)
    P = np.zeros(seg // 2 + 1)
    for i in range(k):
        P += np.abs(np.fft.rfft(x[i * seg:(i + 1) * seg] * w)) ** 2
    f = np.fft.rfftfreq(seg, 1 / sr)
    lv = np.array([10 * math.log10(P[(f >= c / 1.122) & (f < c * 1.122)].sum() + 1e-20) for c in THIRDS])
    return lv - lv[5:8].mean()


def stft_apply(x, gain_fn, n=4096, hop=1024):
    """Run stereo audio through a frequency-domain gain. gain_fn(power[frames,bins], freqs) -> gains."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    w = np.hanning(n).astype(np.float32)
    pad = np.pad(x, ((n, n + hop), (0, 0)))
    idx = np.arange(0, len(pad) - n, hop)
    spec = []
    for ch in range(x.shape[1]):
        fr = np.lib.stride_tricks.sliding_window_view(pad[:, ch], n)[idx]
        spec.append(np.fft.rfft(fr * w, axis=1))
    power = sum(np.abs(s) ** 2 for s in spec) / len(spec)
    gains = gain_fn(power, np.fft.rfftfreq(n, 1 / SR)).astype(np.float32)
    out = np.zeros_like(pad)
    norm = np.zeros(len(pad), dtype=np.float32)
    ww = w * w
    for ch, s in enumerate(spec):
        y = np.fft.irfft(s * gains, n, axis=1).astype(np.float32) * w
        for i, start in enumerate(idx):
            out[start:start + n, ch] += y[i]
    for start in idx:
        norm[start:start + n] += ww
    out /= np.maximum(norm, 1e-6)[:, None]
    return out[n:n + len(x)]


def _ffmpeg_audio(x, filters):
    from .audio import process
    y = process(x, filters)
    if len(y) < len(x):
        y = np.pad(y, ((0, len(x) - len(y)), (0, 0)))
    return y[:len(x)]


def _read(path):
    from .voice import read_audio
    return read_audio(path, sr=SR)


# ================================================================ audio plugins

@plugin("matchtone", "audio", "Match the tonal balance to a finished-mix target, or to a reference track you like.",
        target=("live", "built-in target: " + ", ".join(TARGETS)),
        ref=("", "path to a reference track to match instead of a built-in target"),
        amount=(0.85, "how far to move toward the target, 0 to 1"),
        max_boost=(3.0, "largest boost in dB (kept small: boosting what a mic missed adds mud)"),
        max_cut=(16.0, "largest cut in dB"),
        protect=(True, "never boost 2-4 kHz, where harshness lives"),
        voice_guard=(16.0, "largest cut allowed in the vocal range 1.8-4.5 kHz, in dB (lower keeps voices clearer)"),
        lowcut=(45.0, "remove rumble below this frequency in Hz (0 = off)"))
def matchtone(x, sr, target="live", ref="", amount=0.85, max_boost=3.0, max_cut=16.0, protect=True,
              voice_guard=16.0, lowcut=45.0):
    if ref:
        if not Path(ref).is_file():
            raise StudioError(f"matchtone: reference track not found: {ref}")
        tgt = third_octave(_read(ref).mean(axis=1))
        name = Path(ref).name
    else:
        if target not in TARGETS:
            raise StudioError(f"matchtone: unknown target '{target}'. Options: {', '.join(TARGETS)}.")
        tgt, name = np.array(TARGETS[target], dtype=float), target
    cur = third_octave(x.mean(axis=1))
    g = np.clip((tgt - cur) * clamp(float(amount)), -abs(float(max_cut)), abs(float(max_boost)))
    if protect:
        g[8:12] = np.minimum(g[8:12], 0.0)
    g[8:12] = np.maximum(g[8:12], -abs(float(voice_guard)))        # 2 kHz to 4 kHz bands
    lf = np.log2(np.array(THIRDS, dtype=float))

    def gain_fn(power, f):
        ff = np.log2(np.maximum(f, 1.0))
        db = np.interp(ff, lf, g, left=g[0] * 0.3, right=g[-1])
        if lowcut:
            db = db + np.minimum(0.0, 24.0 * np.log2(np.maximum(f, 1.0) / float(lowcut)))
        return np.broadcast_to(10 ** (db / 20), power.shape)

    y = stft_apply(x, gain_fn)
    after = third_octave(y.mean(axis=1))
    err = lambda v: float(np.sqrt(np.mean((v[2:] - tgt[2:]) ** 2)))
    worst = int(np.argmax(np.abs(cur - tgt)))
    return y, {"note": f"matched tone to '{name}': average error {err(cur):.1f} dB -> {err(after):.1f} dB "
                       f"(largest correction at {THIRDS[worst]} Hz, was {cur[worst] - tgt[worst]:+.0f} dB off)",
               "error_before": err(cur), "error_after": err(after), "gains": [round(float(v), 1) for v in g]}


@plugin("deharsh", "audio", "Dynamic treble tamer: pulls harsh highs down only in the moments they swamp the mids.",
        low=(4200.0, "bottom of the band to control, Hz"),
        high=(11000.0, "top of the band to control, Hz"),
        threshold=(-9.0, "start working when the band is this many dB above/below the mids"),
        ratio=(0.75, "how much of the excess to remove, 0 to 1"),
        max_cut=(12.0, "never cut more than this many dB"))
def deharsh(x, sr, low=4200.0, high=11000.0, threshold=-9.0, ratio=0.75, max_cut=12.0):
    low, high = float(low), float(high)
    stats = {}

    def gain_fn(power, f):
        band = (f >= low) & (f <= high)
        mid = (f >= 350) & (f <= 3000)
        edge = np.clip(np.minimum((f - low * 0.8) / (low * 0.2), (high * 1.25 - f) / (high * 0.25)), 0, 1)
        excess = 10 * np.log10(power[:, band].sum(1) + 1e-12) - 10 * np.log10(power[:, mid].sum(1) + 1e-12)
        cut = np.clip((excess - float(threshold)) * clamp(float(ratio)), 0, abs(float(max_cut)))
        sm = np.empty_like(cut)
        c = 0.0
        for i, v in enumerate(cut):                   # instant attack, roughly 90 ms release
            c = v if v > c else c + (v - c) * 0.11
            sm[i] = c
        stats["mean"], stats["peak"] = float(sm.mean()), float(sm.max())
        stats["busy"] = float((sm > 1.0).mean() * 100)
        return 10 ** (-(sm[:, None] * edge[None, :]) / 20)

    y = stft_apply(x, gain_fn, n=2048, hop=512)
    return y, {"note": f"tamed harsh treble: average cut {stats['mean']:.1f} dB, up to {stats['peak']:.1f} dB, "
                       f"working {stats['busy']:.0f}% of the time", **stats}


@plugin("presence", "audio", "Bring voices forward (or push them back): a smooth lift centred on the vocal range.",
        amount=(2.5, "lift in dB; negative pushes voices back"),
        centre=(2800.0, "centre frequency in Hz"),
        width=(1.3, "width in octaves"))
def presence(x, sr, amount=2.5, centre=2800.0, width=1.3):
    amount, centre, width = float(amount), float(centre), max(0.3, float(width))

    def gain_fn(power, f):
        octs = np.log2(np.maximum(f, 20.0) / centre)
        db = amount * np.exp(-0.5 * (octs / (width / 2.355)) ** 2)
        return np.broadcast_to(10 ** (db / 20), power.shape)

    return stft_apply(x, gain_fn), {"note": f"vocal range {'lifted' if amount >= 0 else 'cut'} {abs(amount):.1f} dB around {centre:.0f} Hz"}


@plugin("declip", "audio", "Rebuild flattened (clipped) peaks. Works best on original, uncompressed recordings.",
        threshold=(8.0, "sensitivity, lower finds more"))
def declip(x, sr, threshold=8.0):
    y = _ffmpeg_audio(x * 0.7, f"adeclip=window=55:overlap=75:arorder=8:threshold={float(threshold)}:hsize=1000:method=add")
    return y, {"note": "rebuilt clipped peaks"}


@plugin("dehum", "audio", "Remove mains hum (50 or 60 Hz and its harmonics).",
        freq=(0.0, "hum frequency in Hz; 0 = detect"),
        harmonics=(4, "how many harmonics to notch"))
def dehum(x, sr, freq=0.0, harmonics=4):
    freq = float(freq)
    if not freq:
        mono = x.mean(axis=1)
        seg = 1 << 16
        k = min(40, len(mono) // seg)
        if k < 1:
            return x, {"note": "too short to check for hum"}
        w = np.hanning(seg)
        P = np.zeros(seg // 2 + 1)
        for i in range(k):
            P += np.abs(np.fft.rfft(mono[i * seg:(i + 1) * seg] * w)) ** 2
        f = np.fft.rfftfreq(seg, 1 / sr)
        best = (0.0, 0.0)
        for base in (50.0, 60.0):
            sc = []
            for h in (1, 2, 3):
                c = base * h
                pk = P[(f > c - 1.5) & (f < c + 1.5)].max()
                ring = P[((f > c - 14) & (f < c - 4)) | ((f > c + 4) & (f < c + 14))]
                sc.append(10 * math.log10((pk + 1e-20) / (np.median(ring) + 1e-20)))
            s = float(np.mean(sorted(sc)[1:]))
            if s > best[0]:
                best = (s, base)
        if best[0] < 12:
            return x, {"note": "no mains hum found"}
        freq = best[1]
    flt = ",".join(f"bandreject=f={freq * h:.0f}:width_type=q:w=28" for h in range(1, int(harmonics) + 1))
    return _ffmpeg_audio(x, flt), {"note": f"notched hum at {freq:.0f} Hz and {int(harmonics) - 1} harmonics"}


@plugin("denoise", "audio", "Reduce steady background noise and hiss under speech.",
        amount=(14.0, "noise reduction in dB"),
        gate=(True, "gently tuck remaining noise down between words"))
def denoise(x, sr, amount=14.0, gate=True):
    mono = x.mean(axis=1)
    win = sr // 50
    n = len(mono) // win
    if n < 10:
        return x, {"note": "too short to denoise"}
    wdb = np.maximum(10 * np.log10((mono[:n * win].reshape(n, win).astype(np.float64) ** 2).mean(axis=1) + 1e-12), -100)
    live = wdb[wdb > -95]
    floor = float(np.percentile(live, 3)) if live.size else -80.0
    nr = clamp(float(amount), 3, 36)
    flt = f"afftdn=nr={nr:.0f}:nf={clamp(round(floor - 2), -80, -20):.0f}:tn=1"
    if gate:
        thr = 10 ** (clamp(floor - nr * 0.6 + 9, -75, -30) / 20)
        flt += f",agate=threshold={thr:.5f}:ratio=1.7:range=0.22:attack=4:release=160:knee=6"
    return _ffmpeg_audio(x, flt), {"note": f"reduced noise by about {nr:.0f} dB (floor was {floor:.0f} dB)"}


@plugin("level", "audio", "Set loudness to a broadcast target and keep peaks under the ceiling.",
        lufs=(-14.0, "target loudness (-14 for music online, -16 for speech)"),
        ceiling=(-1.0, "peak ceiling in dB"))
def level(x, sr, lufs=-14.0, ceiling=-1.0):
    from .audio import lufs as measure
    cur = measure(x)
    if cur is None:
        return x, {"note": "too quiet or short to measure loudness"}
    y = x * float(10 ** (clamp(float(lufs) - cur, -40, 40) / 20))
    lim = 10 ** (float(ceiling) / 20)
    if float(np.abs(y).max()) > lim:
        y = _ffmpeg_audio(y, f"alimiter=limit={lim:.3f}:level=false:attack=3:release=60")
    return y, {"note": f"loudness {cur:.1f} -> {float(lufs):.1f} LUFS", "before": cur}


# ================================================================ video plugins

@plugin("steady", "video", "Stabilise shaky footage. 'full' keeps the whole picture (no zoom-in crop).",
        frame=("crop", "'crop' zooms in slightly to hide the moving edges; 'full' keeps every pixel of the stage"),
        smooth=(18, "how many frames of movement to smooth over (higher = steadier, floatier)"))
def steady(info, workdir, frame="crop", smooth=18):
    if frame not in ("crop", "full"):
        raise StudioError("steady: frame must be 'crop' or 'full'.")
    src = info["path"]
    p = subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", src, "-an",
                        "-vf", "format=yuv420p,vidstabdetect=shakiness=7:accuracy=15:result=t.trf", "-f", "null", "-"],
                       cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode or not (Path(workdir) / "t.trf").is_file():
        raise StudioError("steady: movement analysis failed:\n" + p.stderr.decode("utf-8", "replace")[-400:])
    sm = int(clamp(int(smooth), 4, 90))
    if frame == "full":
        # No zoom: the picture floats inside the frame and the gap is filled from neighbouring frames.
        tr = f"vidstabtransform=input=t.trf:smoothing={sm}:optzoom=0:zoom=0:interpol=bicubic:crop=keep"
    else:
        tr = f"vidstabtransform=input=t.trf:smoothing={sm}:optzoom=1:interpol=bicubic:crop=black"
    return {"vf": ["format=yuv420p", tr, "format=yuv420p"],
            "note": f"stabilised ({'full frame, nothing cropped' if frame == 'full' else 'slight zoom to hide edges'})"}


@plugin("sharpen", "video", "Crisp up soft footage. It cannot undo motion blur.",
        amount=(0.4, "strength, 0 to 1"))
def sharpen(info, workdir, amount=0.4):
    return {"vf": [f"cas={clamp(float(amount), 0.05, 1.0):.2f}"], "note": "sharpened"}


@plugin("fps", "video", "Lock a wobbly frame rate, or smooth choppy low-frame-rate footage.",
        rate=(30, "output frames per second"),
        mode=("lock", "'lock' repeats frames, 'blend' cross-fades them, 'flow' invents in-between frames (can warp)"))
def fps(info, workdir, rate=30, mode="lock"):
    rate = int(rate)
    if mode == "lock":
        return {"vf": [f"fps={rate}"], "note": f"frame rate locked to {rate}"}
    if mode == "blend":
        return {"vf": [f"minterpolate=fps={rate}:mi_mode=blend"], "note": f"smoothed to {rate} fps by blending frames"}
    if mode == "flow":
        return {"vf": [f"minterpolate=fps={rate}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"],
                "note": f"smoothed to {rate} fps with motion estimation"}
    raise StudioError("fps: mode must be lock, blend or flow.")


# ================================================================ ready-made chains

chain("gig", "Live music filmed on a phone: fix the tone, tame the harshness, set the level.",
      ["matchtone", "deharsh", ("level", {"lufs": -14.0})])
chain("gig-video", "The 'gig' sound chain plus full-frame stabilisation.",
      [("steady", {"frame": "full"}), "matchtone", "deharsh", ("level", {"lufs": -14.0})])
chain("voice", "Spoken word: remove hum and noise, set the level.",
      ["dehum", "denoise", ("level", {"lufs": -16.0})])


# ================================================================ running

_loaded_user = False


def load_user_plugins():
    """Import the user's own plugin files (they register themselves with @plugin / chain)."""
    global _loaded_user
    if _loaded_user:
        return
    _loaded_user = True
    for d in (Path(__file__).resolve().parent.parent / "studio_plugins", Path.home() / ".studio" / "plugins"):
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(f"studio_user_{f.stem}", f)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                raise StudioError(f"Your plugin file {f} failed to load: {type(e).__name__}: {e}")


def _coerce(default, value):
    if isinstance(default, bool):
        return str(value).lower() in ("1", "true", "yes", "on") if not isinstance(value, bool) else value
    if isinstance(default, int) and not isinstance(default, bool):
        return int(float(value))
    if isinstance(default, float):
        return float(value)
    return str(value)


def resolve(spec, overrides=None):
    """'gig' or 'matchtone,deharsh' -> [(Plugin, settings)], applying 'plugin.setting=value' overrides."""
    load_user_plugins()
    steps = []
    for part in [s.strip() for s in str(spec).split(",") if s.strip()]:
        if part in CHAINS:
            steps += [(n, dict(p)) for n, p in CHAINS[part][1]]
        elif part in REGISTRY:
            steps.append((part, {}))
        else:
            raise StudioError(f"No plugin or chain called '{part}'. Run: python -m studio plugins")
    for key, val in (overrides or {}).items():
        if "." not in key:
            raise StudioError(f"Settings look like plugin.setting=value (got '{key}').")
        pname, setting = key.split(".", 1)
        hit = [s for s in steps if s[0] == pname]
        if not hit:
            raise StudioError(f"'{pname}' is not in this chain.")
        if setting not in REGISTRY[pname].params:
            raise StudioError(f"'{pname}' has no setting '{setting}'. Options: {', '.join(REGISTRY[pname].params)}.")
        for s in hit:
            s[1][setting] = val
    out = []
    for name, params in steps:
        pl = REGISTRY[name]
        full = {k: v[0] for k, v in pl.params.items()}
        for k, v in params.items():
            if k not in pl.params:
                raise StudioError(f"'{name}' has no setting '{k}'.")
            full[k] = _coerce(pl.params[k][0], v)
        out.append((pl, full))
    return out


def run_audio(x, steps, log=None):
    """Apply audio plugins in order to stereo float32 audio. Returns (audio, notes)."""
    notes = []
    for pl, params in steps:
        if pl.kind != "audio":
            continue
        x, rep = pl.fn(x, SR, **params)
        x = np.asarray(x, dtype=np.float32)
        notes.append(f"{pl.name}: {rep.get('note', 'done')}")
        if log:
            log("  " + notes[-1])
    return x, notes


def run(src, spec, out=None, overrides=None, log=print):
    """Run a chain on a file. Video stays untouched unless the chain has video plugins."""
    from .voice import write_wav
    src = Path(src)
    if not src.is_file():
        raise StudioError(f"File not found: {src}")
    steps = resolve(spec, overrides)
    info = probe(src)
    has_v = any(s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")
                for s in info["streams"])
    has_a = any(s.get("codec_type") == "audio" for s in info["streams"])
    a_steps = [s for s in steps if s[0].kind == "audio"]
    v_steps = [s for s in steps if s[0].kind == "video"]
    if a_steps and not has_a:
        raise StudioError(f"{src.name} has no sound for the audio plugins to work on.")
    if v_steps and not has_v:
        raise StudioError(f"{src.name} has no picture for the video plugins to work on.")
    if out is None:
        out = src.with_name(f"{src.stem}_plug{'.mp4' if has_v else '.wav'}")
    out = Path(out)
    notes = []
    with tempfile.TemporaryDirectory(prefix="studioplug_") as tmp:
        wav = None
        if a_steps:
            log("Working on the sound...")
            y, n = run_audio(_read(src), a_steps, log)
            notes += n
            wav = Path(tmp) / "audio.wav"
            write_wav(wav, y, SR)
        if not has_v:
            if out.suffix.lower() == ".wav":
                Path(wav).replace(out) if wav else None
            else:
                subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(wav), str(out.resolve())], check=True)
            return {"output": str(out), "notes": notes}
        vf = []
        for pl, params in v_steps:
            log(f"Working on the picture ({pl.name})...")
            rep = pl.fn({"path": str(src.resolve()), "probe": info}, tmp, **params)
            vf += rep.get("vf", [])
            notes.append(f"{pl.name}: {rep.get('note', 'done')}")
            log("  " + notes[-1])
        cmd = [FFMPEG, "-nostdin", "-v", "error", "-y", "-i", str(src.resolve())]
        if wav:
            cmd += ["-i", str(wav)]
        cmd += ["-map", "0:v:0"]
        cmd += (["-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p"]
                if vf else ["-c:v", "copy"])
        if wav:
            cmd += ["-map", "1:a:0", "-c:a", "aac", "-b:a", "256k", "-shortest"]
        elif has_a:
            cmd += ["-map", "0:a:0", "-c:a", "copy"]
        tmp_out = out.with_name(out.stem + ".part" + out.suffix)
        p = subprocess.run(cmd + ["-movflags", "+faststart", str(tmp_out.resolve())], cwd=tmp,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode:
            tmp_out.unlink(missing_ok=True)
            raise StudioError("Plugin chain failed:\n" + p.stderr.decode("utf-8", "replace")[-600:])
        tmp_out.replace(out)
    return {"output": str(out), "notes": notes}


def describe():
    load_user_plugins()
    L = ["Chains (ready-made):"]
    for name, (summary, steps) in CHAINS.items():
        L.append(f"  {name:<12} {summary}")
        L.append(f"  {'':<12} = " + " -> ".join(n for n, _ in steps))
    for kind in ("audio", "video"):
        L.append(f"\n{kind.capitalize()} plugins:")
        for pl in REGISTRY.values():
            if pl.kind != kind:
                continue
            L.append(f"  {pl.name:<12} {pl.summary}")
            for k, (default, desc) in pl.params.items():
                L.append(f"  {'':<12}   {k}={default!r}: {desc}")
    return "\n".join(L)
