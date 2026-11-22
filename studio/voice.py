"""Narration: turn each scene's words into audio plus per-word timings.

Providers
  piper   free, runs offline on this machine (British voices included)          [default]
  edge    free Microsoft neural voices (needs internet; exact word timings)
  file    audio you already have (ElevenLabs export, a recording) per scene
  none    no voice: scenes are timed by reading speed (silent drafts / music-only)

Word timings come from the engine when it provides them, from Whisper when the
optional `faster-whisper` package is installed, and from a phoneme-weighted
estimate otherwise.
"""
from __future__ import annotations

import asyncio
import difflib
import json
import os
import re
import urllib.request
import wave
from pathlib import Path

import numpy as np

from .util import FFMPEG, StudioError, digest, file_sig, media_duration, run

VOICE_DIR = Path(os.environ.get("STUDIO_VOICES", Path.home() / ".cache" / "studio" / "voices"))
PIPER_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
PIPER_VOICES = {
    "en_GB-alan-medium": "British male, measured (default)",
    "en_GB-northern_english_male-medium": "British male, northern, warm",
    "en_GB-cori-high": "British female, clear",
    "en_GB-jenny_dioco-medium": "British female, soft",
    "en_US-ryan-high": "American male, energetic",
    "en_US-lessac-high": "American female, neutral",
}
EDGE_VOICES = {
    "en-GB-RyanNeural": "British male, natural",
    "en-GB-SoniaNeural": "British female, natural",
    "en-GB-ThomasNeural": "British male, deeper",
    "en-US-AndrewNeural": "American male, warm",
    "en-US-AvaNeural": "American female, bright",
}
SR = 48000


# ---------------------------------------------------------------- text helpers

def tokens(text):
    return str(text).split()


def split_sentences(text):
    parts = re.split(r"(?<=[.!?…])[\"'”’)]*\s+", str(text).strip())
    return [p for p in (s.strip() for s in parts) if p]


def _norm(w):
    return re.sub(r"[^a-z0-9]+", "", w.lower())


def _weight(word):
    """Rough spoken length of a word (used when no better timing is available)."""
    core = re.sub(r"[^A-Za-z0-9]", "", word)
    if not core:
        return 0.5, 0.0
    if core.isdigit():
        units = 2.5 + 2.2 * len(core)
    else:
        vowels = len(re.findall(r"[aeiouyAEIOUY]+", core))
        units = max(1.0, vowels) * 2.2 + len(core) * 0.55
    pause = 0.0
    if word[-1:] in ",;:":
        pause = 2.6
    elif word[-1:] in ".?!…":
        pause = 4.5
    elif word in ("—", "-", "–"):
        pause = 3.0
    return units, pause


def spread(words, t0, t1, weights=None):
    """Lay words out between t0 and t1 in proportion to their spoken weight."""
    if not words:
        return []
    ws = weights or [_weight(w) for w in words]
    ws = list(ws)
    ws[-1] = (ws[-1][0], 0.0)
    total = sum(u + p for u, p in ws) or 1.0
    out, t = [], t0
    for w, (u, p) in zip(words, ws):
        d = (t1 - t0) * u / total
        out.append({"t": w, "s": round(t, 3), "e": round(t + d, 3)})
        t += d + (t1 - t0) * p / total
    return out


def map_times(script_words, timed):
    """Put the script's own spelling on timings heard by a recogniser/engine.

    timed: [(text, start, end)]. Words the engine merged or missed are interpolated.
    """
    if not script_words:
        return []
    if not timed:
        return []
    a = [_norm(w) for w in script_words]
    b = [_norm(w) for w, _, _ in timed]
    out = [None] * len(script_words)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k] = (timed[j1 + k][1], timed[j1 + k][2])
        elif tag == "replace" and j2 > j1:
            seg = spread(script_words[i1:i2], timed[j1][1], timed[j2 - 1][2])
            for k, s in enumerate(seg):
                out[i1 + k] = (s["s"], s["e"])
    end_all = timed[-1][2]
    i = 0
    while i < len(out):
        if out[i] is None:
            j = i
            while j < len(out) and out[j] is None:
                j += 1
            t0 = out[i - 1][1] if i > 0 else max(0.0, timed[0][1] - 0.3 * (j - i))
            t1 = out[j][0] if j < len(out) else max(end_all, t0 + 0.25 * (j - i))
            if t1 <= t0:
                t1 = t0 + 0.05 * (j - i)
            for k, s in enumerate(spread(script_words[i:j], t0, t1)):
                out[i + k] = (s["s"], s["e"])
            i = j
        else:
            i += 1
    res, last = [], 0.0
    for w, (s, e) in zip(script_words, out):
        s = max(s, last)
        e = max(e, s + 0.04)
        res.append({"t": w, "s": round(s, 3), "e": round(e, 3)})
        last = s
    return res


# ---------------------------------------------------------------- audio io

def read_audio(path, sr=SR, filters=None):
    """Decode any audio file to float32 stereo at `sr`."""
    cmd = [FFMPEG, "-v", "error", "-i", str(path)]
    if filters:
        cmd += ["-af", filters]
    cmd += ["-f", "f32le", "-ac", "2", "-ar", str(sr), "-"]
    raw = run(cmd)
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def write_wav(path, audio, sr=SR):
    a = np.clip(audio, -1.0, 1.0)
    pcm = (a * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def speech_bounds(path):
    """(start, end) seconds of the audible part of a clip."""
    a = read_audio(path, sr=16000).mean(axis=1)
    if a.size == 0:
        return 0.0, 0.0
    env = np.abs(a)
    thr = max(0.012, float(env.max()) * 0.04)
    idx = np.nonzero(env > thr)[0]
    if idx.size == 0:
        return 0.0, len(a) / 16000
    return max(0.0, idx[0] / 16000 - 0.02), min(len(a) / 16000, idx[-1] / 16000 + 0.05)


# ---------------------------------------------------------------- whisper (optional)

_whisper = None


def whisper_available():
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def whisper_words(path, model="base.en"):
    """Word timings heard in an audio file: [(text, start, end)]."""
    global _whisper
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")     # plain download works behind strict proxies
    from faster_whisper import WhisperModel
    if _whisper is None or _whisper[0] != model:
        _whisper = (model, WhisperModel(model, device="cpu", compute_type="int8"))
    # Decode with ffmpeg ourselves: no dependence on the audio library Whisper bundles.
    pcm = np.frombuffer(run([FFMPEG, "-v", "error", "-i", str(path), "-vn", "-f", "f32le", "-ac", "1",
                             "-ar", "16000", "-"]), dtype=np.float32)
    segs, _ = _whisper[1].transcribe(pcm, word_timestamps=True, vad_filter=False, language="en")
    out = []
    for s in segs:
        for w in s.words or []:
            out.append((w.word.strip(), float(w.start), float(w.end)))
    return out


TIMING_NOTES = []          # why timing fell back to an estimate (shown by `plan` and `render`)


def align(path, text, method="auto", model="base.en"):
    """Per-word timings for `text` spoken in the audio at `path`."""
    words = tokens(text)
    if not words:
        return []
    if method in ("auto", "whisper") and whisper_available():
        try:
            heard = whisper_words(path, model)
            if heard:
                return map_times(words, heard)
        except Exception as e:
            if method == "whisper":
                raise StudioError(f"Whisper alignment failed: {e}")
            note = f"Whisper timing failed ({type(e).__name__}: {str(e)[:90]}); caption timing is estimated."
            if note not in TIMING_NOTES:
                TIMING_NOTES.append(note)
    elif method == "whisper":
        raise StudioError("Whisper alignment needs:  pip install faster-whisper")
    elif method == "auto":
        note = ("Caption timing for your audio files is estimated. "
                "For exact word timing:  pip install faster-whisper")
        if note not in TIMING_NOTES:
            TIMING_NOTES.append(note)
    t0, t1 = speech_bounds(path)
    return spread(words, t0, t1)


# ---------------------------------------------------------------- providers

def _piper_model(name):
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    onnx = VOICE_DIR / f"{name}.onnx"
    cfg = VOICE_DIR / f"{name}.onnx.json"
    if onnx.is_file() and cfg.is_file() and onnx.stat().st_size > 1_000_000:
        return onnx
    m = re.match(r"^([a-z]{2})_([A-Z]{2})-(.+)-(x_low|low|medium|high)$", name)
    if not m:
        raise StudioError(f"'{name}' is not a Piper voice name (expected e.g. en_GB-alan-medium).")
    lang, region, speaker, quality = m.groups()
    base = f"{PIPER_URL}/{lang}/{lang}_{region}/{speaker}/{quality}/{name}"
    for url, dst in ((base + ".onnx.json", cfg), (base + ".onnx", onnx)):
        try:
            tmp = dst.with_suffix(dst.suffix + ".part")
            urllib.request.urlretrieve(url, tmp)
            tmp.replace(dst)
        except Exception as e:
            raise StudioError(f"Could not download voice '{name}' ({e}). "
                              f"Check the name with: python -m studio voices")
    return onnx


_piper_cache = {}


def _piper(text, voice, speed, out_wav):
    try:
        from piper import PiperVoice, SynthesisConfig
    except ImportError:
        raise StudioError("The free offline voice needs:  pip install piper-tts")
    if voice not in _piper_cache:
        _piper_cache[voice] = PiperVoice.load(str(_piper_model(voice)))
    pv = _piper_cache[voice]
    cfg = SynthesisConfig(length_scale=1.0 / max(0.5, min(2.0, speed)))
    gap_sentence, sr = 0.24, None
    pieces, words, t = [], [], 0.0
    sentences = split_sentences(text)
    for si, sent in enumerate(sentences):
        chunks = list(pv.synthesize(sent, cfg))
        if not chunks:
            continue
        sr = chunks[0].sample_rate
        audio = np.concatenate([np.asarray(c.audio_float_array, dtype=np.float32).reshape(-1) for c in chunks])
        # Trim the silence the model leaves at either end, so timings are tight.
        env = np.abs(audio)
        idx = np.nonzero(env > max(0.01, float(env.max()) * 0.03))[0]
        if idx.size:
            audio = audio[max(0, idx[0] - int(0.015 * sr)): idx[-1] + int(0.05 * sr)]
        dur = len(audio) / sr
        sw = tokens(sent)
        phon = [p for c in chunks for p in (c.phonemes or [])]
        groups = "".join(phon).split(" ") if phon else []
        weights = None
        if len(groups) == len(sw):
            weights = []
            for gph in groups:
                core = [p for p in gph if p not in "ˈˌː,.;:!?"]
                pause = 2.6 if any(p in ",;:" for p in gph) else 0.0
                weights.append((max(1.0, float(len(core))), pause))
        for w in spread(sw, t, t + dur, weights):
            words.append(w)
        pieces.append(audio)
        t += dur
        if si < len(sentences) - 1:
            pieces.append(np.zeros(int(gap_sentence * sr), dtype=np.float32))
            t += gap_sentence
    if not pieces:
        raise StudioError("The voice produced no audio for: " + text[:60])
    audio = np.concatenate(pieces)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    return words


def _edge(text, voice, speed, out_mp3):
    try:
        import edge_tts
    except ImportError:
        raise StudioError("Edge voices need:  pip install edge-tts")
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    timed = []

    async def go():
        com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        with open(out_mp3, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    s = ch["offset"] / 1e7
                    timed.append((ch["text"], s, s + ch["duration"] / 1e7))

    try:
        asyncio.run(go())
    except Exception as e:
        raise StudioError(f"Edge voice failed ({type(e).__name__}: {e}). It needs internet access to "
                          "speech.platform.bing.com. Use provider 'piper' to stay offline.")
    if not os.path.exists(out_mp3) or os.path.getsize(out_mp3) < 500:
        raise StudioError("Edge voice returned no audio.")
    return map_times(tokens(text), timed) if timed else None


def synthesize(text, cfg, cache_dir, on_work=None):
    """Speak `text`. Returns {"path", "duration", "words"}; cached by content."""
    provider = cfg.get("provider", "piper")
    speed = float(cfg.get("speed", 1.0))
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if provider == "piper":
        voice, ext = cfg.get("voice", "en_GB-alan-medium"), ".wav"
    elif provider == "edge":
        voice, ext = cfg.get("voice", "en-GB-RyanNeural"), ".mp3"
    else:
        raise StudioError(f"Unknown voice provider '{provider}'. Options: piper, edge, file, none.")
    key = digest(["tts2", provider, voice, speed, text])
    path = cache_dir / f"vo_{key}{ext}"
    meta = cache_dir / f"vo_{key}.json"
    if path.is_file() and meta.is_file():
        return {"path": str(path), **json.loads(meta.read_text())}
    if on_work:
        on_work()
    words = _piper(text, voice, speed, path) if provider == "piper" else _edge(text, voice, speed, path)
    if words is None:
        words = align(path, text, cfg.get("align", "auto"))
    info = {"duration": media_duration(path), "words": words}
    meta.write_text(json.dumps(info))
    return {"path": str(path), **info}


def from_file(path, text, cfg, cache_dir):
    """Use existing narration audio; work out word timings for the captions."""
    if not Path(path).is_file():
        raise StudioError(f"Narration audio not found: {path}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    method = cfg.get("align", "auto")
    meta = cache_dir / f"al_{digest(['al3', file_sig(path), text, method, whisper_available()])}.json"
    if meta.is_file():
        return {"path": str(path), **json.loads(meta.read_text())}
    info = {"duration": media_duration(path), "words": align(path, text, method) if text else []}
    meta.write_text(json.dumps(info))
    return {"path": str(path), **info}
