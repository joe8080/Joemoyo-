"""Kongo v1 mix: narration leads; one cue looped underneath; silence where the story needs it.
Outputs build/mix.wav (stereo, 48 kHz). Loudness is normalised to -14 LUFS at mux time."""
import json, subprocess, wave
import numpy as np

SR = 48000
tl = json.load(open("build/timeline.json"))
T = tl["total"]; N = int(T * SR)


def load(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, ch) / 32768.0


vo = load("build/vo.wav", 1)[:N, 0]
vo = np.pad(vo, (0, N - len(vo)))

# music: loop the 60 s cue with 5 s equal-power crossfades
cue = load("music/C1.mp3", 2)
xf = 5 * SR
mus = cue.copy()
while len(mus) < N + SR:
    a = mus[-xf:]; b = cue[:xf]
    r = np.linspace(0, 1, xf)[:, None]
    mid = a * np.cos(r * np.pi / 2) + b * np.sin(r * np.pi / 2)
    mus = np.concatenate([mus[:-xf], mid, cue[xf:]])
mus = mus[:N]


def db(x):
    return 10 ** (x / 20)


# gain envelope (dB) on a 10 ms grid, then smoothed
step = SR // 100
g = np.full(N // step + 1, -15.0)
secs = tl["sections"]
for name, d in secs.items():
    s, e = d["start"], d["start"] + d["dur"]
    g[int(s * 100):int(e * 100)] = -25.0
# lead-in swell
g[:int(tl["lead_in"] * 100)] = -17.0
# silence under the kidnapping and branding lines (R6) until "So he made a law"
w6 = secs["R6"]["words"]
def word_time(words, phrase):
    toks = [t.lower().strip(",.“”\"'") for t in phrase.split()]
    for i in range(len(words) - len(toks) + 1):
        if [x[0].lower().strip(",.“”\"'") for x in words[i:i + len(toks)]] == toks:
            return words[i][1]
    raise SystemExit("phrase not found: " + phrase)
m0 = word_time(w6, "Free people were being taken"); m1 = word_time(w6, "So he made a law")
g[int((m0 - 0.8) * 100):int((m1 - 0.2) * 100)] = -60.0
# silence after "the people who were taken" (end of R7) through the gap
r7_end = secs["R7"]["start"] + secs["R7"]["dur"]
g[int((r7_end - 2.0) * 100):int((r7_end + secs["R7"]["gap_after"] - 0.3) * 100)] = -60.0
# end card: music up, then fade
g[int(tl["end_card"] * 100):] = -14.0
k = 60  # 0.6 s smoothing
g = np.convolve(g, np.ones(k) / k, mode="same")
env = np.interp(np.arange(N) / step, np.arange(len(g)), db(g)).astype(np.float32)
fade = np.ones(N, np.float32); fl = int(3 * SR); fade[-fl:] = np.linspace(1, 0, fl)
mus = mus * (env * fade)[:, None]

mix = mus + vo[:, None] * db(-1.0)
peak = np.abs(mix).max()
if peak > 0.98:
    mix *= 0.98 / peak
with wave.open("build/mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix ok", T)
