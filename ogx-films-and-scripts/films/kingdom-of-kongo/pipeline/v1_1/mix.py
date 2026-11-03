"""Kongo v1.1 mix: narration leads; three original Artlist (Lyria 3 Pro) cues underneath.
M1 (dark, tense) cold open to the end of R2; M2 (the kingdom) R3-R4; M3 (sombre close) R5 to the end.
Cues are level-matched, crossfaded over 4 s, and looped with a crossfade only if a cue runs short.
Silence stays where the story needs it (R6 kidnapping lines; after "the people who were taken").
Outputs build/mix.wav (stereo, 48 kHz). Loudness is normalised to -14 LUFS at mux time."""
import json, subprocess, wave
import numpy as np

SR = 48000
tl = json.load(open("build/timeline.json"))
T = tl["total"]; N = int(T * SR)
secs = tl["sections"]


def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, ch) / 32768.0


def level(x, target=0.09):
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    return x * (target / rms)


def fit(cue, n, xf):
    """Return exactly n samples of cue, looping with an equal-power crossfade if needed."""
    out = cue.copy()
    while len(out) < n:
        a = out[-xf:]; b = cue[:xf]
        r = np.linspace(0, 1, xf)[:, None]
        out = np.concatenate([out[:-xf], a * np.cos(r * np.pi / 2) + b * np.sin(r * np.pi / 2), cue[xf:]])
    return out[:n]


vo = load("build/vo.wav", 1)[:N, 0]
vo = np.pad(vo, (0, N - len(vo)))

XF = 4 * SR
cues = [level(load(f"music11/{f}.wav", 2)) for f in ("M1_open", "M2_kingdom", "M3_close")]
b1 = int((secs["R3"]["start"] - 1.5) * SR)        # change of cue in the gap before R3
b2 = int((secs["R5"]["start"] - 1.0) * SR)        # and before R5
bounds = [(0, b1), (b1, b2), (b2, N)]
mus = np.zeros((N, 2), np.float32)
for k, ((s, e), cue) in enumerate(zip(bounds, cues)):
    s0 = max(0, s - XF // 2); e0 = min(N, e + XF // 2)
    seg = fit(cue, e0 - s0, XF)
    w = np.ones(e0 - s0, np.float32)
    if k > 0:
        w[:XF] = np.sin(np.linspace(0, 1, XF) * np.pi / 2)
    if k < 2:
        w[-XF:] = np.cos(np.linspace(0, 1, XF) * np.pi / 2)
    mus[s0:e0] += seg * w[:, None]


def db(x):
    return 10 ** (x / 20)


step = SR // 100
g = np.full(N // step + 1, -13.0)
for name, d in secs.items():
    s, e = d["start"], d["start"] + d["dur"]
    g[int(s * 100):int(e * 100)] = -23.0
g[:int(tl["lead_in"] * 100)] = -14.0


def word_time(words, phrase):
    toks = [t.lower().strip(",.“”\"'") for t in phrase.split()]
    for i in range(len(words) - len(toks) + 1):
        if [x[0].lower().strip(",.“”\"'") for x in words[i:i + len(toks)]] == toks:
            return words[i][1]
    raise SystemExit("phrase not found: " + phrase)


w6 = secs["R6"]["words"]
m0 = word_time(w6, "Free people were being taken"); m1 = word_time(w6, "So he made a law")
g[int((m0 - 0.8) * 100):int((m1 - 0.2) * 100)] = -60.0
r7_end = secs["R7"]["start"] + secs["R7"]["dur"]
g[int((r7_end - 2.0) * 100):int((r7_end + secs["R7"]["gap_after"] - 0.3) * 100)] = -60.0
g[int(tl["end_card"] * 100):] = -12.0
k = 60
g = np.convolve(g, np.ones(k) / k, mode="same")
env = np.interp(np.arange(N) / step, np.arange(len(g)), db(g)).astype(np.float32)
fade = np.ones(N, np.float32); fl = int(3 * SR); fade[-fl:] = np.linspace(1, 0, fl)
mus = mus * (env * fade)[:, None] * 4.0      # cues levelled to 0.09 RMS; restore headroom

mix = mus + vo[:, None] * db(-1.0)
peak = np.abs(mix).max()
if peak > 0.98:
    mix *= 0.98 / peak
with wave.open("build/mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix ok", T, "cue changes", b1 / SR, b2 / SR)
