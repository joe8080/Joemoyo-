"""Mix (film book references/audio.md, adapted): separate stems -> master.
Voice bus: HPF 75 Hz, EQ -1.5 dB @250 Hz / +1.5 dB @3.5 kHz, 2.5:1 compression, loudnorm -16 LUFS.
Music: each cue -19 LUFS then -5 dB, 2.5 s crossfades at cue boundaries, ducked -11 dB under speech
(speech activity from the VO line timing, 120 ms attack / 450 ms release). Master: two-pass loudnorm to
-14 LUFS, true peak -1.5 dBTP (brief: <= -1 dBTP), LRA <= 11. Stems are kept in audio/stems/."""
import csv, json, subprocess, pathlib, numpy as np, soundfile as sf
ROOT = pathlib.Path(__file__).resolve().parents[1]; A = ROOT / "audio"; ST = A / "stems"; ST.mkdir(exist_ok=True)
SR = 48000
film = json.load(open(ROOT / "build/shots.json")); TOTAL = film["total"]
# cue plan: (cue file, start s, end s) -- lean: three cues under the voice
CUES = json.load(open(A / "music/cues.json"))

def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

n = int(TOTAL * SR)
# --- voice stem
ff("-i", str(A / "vo/VO_master_v1.1.wav"), "-af",
   "highpass=f=75,equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3500:t=q:w=1:g=1.5,"
   "acompressor=ratio=2.5:threshold=-20dB:attack=8:release=120,loudnorm=I=-16:TP=-2:LRA=11",
   "-ar", str(SR), "-ac", "2", str(ST / "voice.wav"))
voice = load(ST / "voice.wav"); voice = np.pad(voice, ((0, max(0, n - len(voice))), (0, 0)))[:n]
# --- music stem
music = np.zeros((n, 2), np.float32); XF = 2.5
for c in CUES:
    ff("-i", str(A / "music" / c["file"]), "-af", "loudnorm=I=-19:TP=-3,volume=-5dB", "-ar", str(SR), "-ac", "2", str(ST / f"_{c['file']}.wav"))
    x = load(ST / f"_{c['file']}.wav"); a, b = int(c["start"] * SR), int(min(c["end"] + XF, TOTAL) * SR)
    seg = x[: b - a]
    if len(seg) < b - a: raise SystemExit(f"cue {c['file']} too short: {len(seg) / SR:.1f}s < {(b - a) / SR:.1f}s")
    env = np.ones(len(seg), np.float32); k = int(XF * SR)
    if c["start"] > 0: env[:k] = np.linspace(0, 1, k)
    env[-k:] = np.minimum(env[-k:], np.linspace(1, 0, k))
    music[a:b] += seg * env[:, None]
# duck under speech (VO line speech spans, bridged across short gaps)
act = np.zeros(n, np.float32)
for r in csv.DictReader(open(A / "vo/vo_timing.csv")):
    act[int(float(r["speech_t0"]) * SR):int(float(r["t1"]) * SR)] = 1
win = int(0.35 * SR); act = np.convolve(act, np.ones(win) / win, "same") > 0.01
g = np.where(act, 10 ** (-11 / 20), 1.0).astype(np.float32)
att, rel = 1 - np.exp(-1 / (0.12 * SR)), 1 - np.exp(-1 / (0.45 * SR)); sm = np.empty_like(g); y = 1.0
for i in range(n):
    y += (att if g[i] < y else rel) * (g[i] - y); sm[i] = y
music *= sm[:, None]
sf.write(ST / "music.wav", music, SR, subtype="PCM_24")
sf.write(ST / "voice_aligned.wav", voice, SR, subtype="PCM_24")
sf.write(ST / "premaster.wav", voice + music, SR, subtype="FLOAT")
# --- master, two-pass loudnorm
out = subprocess.run(["ffmpeg", "-i", str(ST / "premaster.wav"), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
m = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
ff("-i", str(ST / "premaster.wav"), "-af",
   f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
   f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", "-ar", str(SR), str(A / "MASTER_mix.wav"))
print("mix done")
