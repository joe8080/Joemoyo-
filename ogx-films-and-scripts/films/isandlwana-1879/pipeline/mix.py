# Isandlwana 1879 mix (from Adwa v1.5) per OGX Production OS 2.4: VO chain (HPF 75 Hz, comp 2.5:1, -16 LUFS), story score
# ducked -11 dB under voice, silence under the cold-open question, two-pass master -14 LUFS / -1.5 dBTP.
import json, subprocess
import numpy as np

SR = 48000
shots = json.load(open("timeline.json"))
TOTAL = shots[-1]["start"] + shots[-1]["dur"]
N = int(TOTAL * SR) + SR

def dec(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    return x.reshape(-1, ch) if ch > 1 else x

def enc(x, path, ch=1):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-", path],
                   input=np.ascontiguousarray(x, np.float32).tobytes(), check=True)

def lufs_gain(path, target):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    return 10 ** ((target - I) / 20)

# 1. narration bus
vo = np.zeros(N, np.float32)
for s in shots:
    c = dec(s["vo_file"])
    a = int(s["vo_at"] * SR)
    vo[a:a + len(c)] += c
enc(vo, "mix_vo_raw.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "mix_vo_raw.wav", "-af",
                "highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3500:t=q:w=1.0:g=1.5,"
                "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2,"
                "loudnorm=I=-16:TP=-2:LRA=9", "-ar", str(SR), "mix_vo.wav"], check=True)
vo = dec("mix_vo.wav")[:N]
vo = np.pad(vo, (0, N - len(vo)))

# 2. music bed: one cue per act (v1.2), crossfaded at act boundaries
ACTS_ORDER = []
for sh in shots:
    if sh["act"] not in ACTS_ORDER:
        ACTS_ORDER.append(sh["act"])
CUE = {"COLD OPEN": "C00", "TITLE": "C00", "01": "C01", "02": "C02", "03": "C03", "04": "C04", "05": "C05", "06": "C06",
       "07": "C07", "CLOSE": "C08"}
# the title rides on the cold-open cue: merge acts that share a cue
ACTS_ORDER = [a for i, a in enumerate(ACTS_ORDER) if i == 0 or CUE[a] != CUE[ACTS_ORDER[i - 1]]]
XF = 2.5
def act_start(name):
    return next(s["start"] for s in shots if s["act"] == name)
bounds = [act_start(a) for a in ACTS_ORDER] + [TOTAL]
bed = np.zeros((N, 2), np.float32)
for i, act in enumerate(ACTS_ORDER):
    a0 = 0.0 if i == 0 else bounds[i] - XF / 2
    a1 = TOTAL if i == len(ACTS_ORDER) - 1 else bounds[i + 1] + XF / 2
    seg_len = int((a1 - a0) * SR)
    path = f"music/{CUE[act]}.mp3"
    m = dec(path, 2)
    if len(m) < seg_len:  # cue shorter than its act: slow it slightly (pitch kept)
        r = max(0.8, len(m) / seg_len * 0.995)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", f"atempo={r:.4f}", "-ac", "2", "-ar", str(SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        m = np.frombuffer(raw, np.float32).reshape(-1, 2)
        print(f"{CUE[act]}: stretched x{1/r:.3f}")
    m = m[:seg_len] * lufs_gain(path, -19.0)
    env = np.ones(len(m), np.float32)
    fi = int((2.0 if i == 0 else XF) * SR)
    fo = int((XF if i < len(ACTS_ORDER) - 1 else 6.0) * SR)
    env[:fi] *= np.linspace(0, 1, fi)
    env[-fo:] *= np.linspace(1, 0, fo)
    s0 = int(a0 * SR)
    bed[s0:s0 + len(m)] += m * env[:, None]

# 3. duck under voice + silence under the question card
act = np.zeros(N, np.float32)
for s in shots:
    for (w, ws, we) in s["words"]:
        a, b = int((s["vo_at"] + ws) * SR), int((s["vo_at"] + we) * SR)
        act[a:b] = 1.0
# dilate speech activity across short pauses (0.35 s) so the bed does not pump between words
hop = SR // 100
fr = act[: (N // hop) * hop].reshape(-1, hop).max(axis=1)
k = 35
fr = np.convolve(fr, np.ones(k), "same") > 0
duck_db = np.where(fr, -11.0, 0.0).astype(np.float32)
# smooth: 120 ms attack, 450 ms release (one-pole on 10 ms frames)
sm = np.zeros_like(duck_db)
g = 0.0
for i, d in enumerate(duck_db):
    coef = 0.08 if d < g else 0.022
    g += (d - g) * coef
    sm[i] = g
gain = 10 ** (np.repeat(sm, hop) / 20)
gain = np.pad(gain, (0, N - len(gain)), constant_values=gain[-1])
# question card: fade bed to silence over 0.6 s at the question line, hold, return for the title
q = next(s for s in shots if s["text"].startswith("But that's only half of it."))
a_ = next(s for s in shots if s["text"] == "And the answer starts with the army itself.")
t_ = next(s for s in shots if s["text"] == "This is the story of Isandlwana.")
qa, qb = int((q["vo_at"] + 1.2) * SR), int((a_["vo_at"] + 0.4) * SR)
sil = np.ones(N, np.float32)
sil[qa:qa + int(0.6 * SR)] = np.linspace(1, 0, int(0.6 * SR))
sil[qa + int(0.6 * SR):qb] = 0
sil[qb:qb + int(1.2 * SR)] = np.linspace(0, 1, int(1.2 * SR))
bed *= (gain * sil * 10 ** (-5.0 / 20))[:, None]
# title swell: +4 dB around the title card
ta, tb = int(t_["start"] * SR), int((t_["start"] + t_["dur"]) * SR)
sw = np.ones(N, np.float32)
sw[ta:tb] = 10 ** (4 / 20)
bed *= sw[:, None]

mix = bed + vo[:, None]
mix = mix[: int(TOTAL * SR)]
enc(mix, "mix_pre.wav", 2)
enc(bed[: int(TOTAL * SR)], "mix_bed.wav", 2)

# 4. two-pass loudnorm master -> -14 LUFS, -1.5 dBTP
p1 = subprocess.run(["ffmpeg", "-i", "mix_pre.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                     "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(p1[p1.rfind("{"):p1.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "mix_pre.wav", "-af", af, "-ar", str(SR), "mix_master.wav"], check=True)
print("master done; pass-1 input", js["input_i"], "LUFS")
