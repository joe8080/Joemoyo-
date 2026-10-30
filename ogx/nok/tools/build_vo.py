"""Assemble the master VO from the single full pass plus single-line fixes; write per-line stems and
the final line timing (vo_timing.csv). Picture timing is cut from this file, never from guesses."""
import csv, subprocess, pathlib, numpy as np, soundfile as sf
ROOT = pathlib.Path(__file__).resolve().parents[1]; V = ROOT / "audio/vo"
FIXES = {"L24": V / "L24_fix.mp3"}          # line -> replacement take (eleven_v4, same voice)
SR = 48000
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)
full = load(V / "VO_full_v1.0.mp3")
def trim(x, thr=10 ** (-40 / 20)):
    idx = np.where(np.abs(x) > thr)[0]; return x[idx[0]:idx[-1] + 1]
rows = list(csv.DictReader(open(V / "line_timing.csv")))
(V / "lines").mkdir(exist_ok=True)
out, t, timing = [], 0.0, []
for r in rows:
    ci, co, st, en = (float(r[k]) for k in ("cut_in", "cut_out", "start", "end"))
    if r["line"] in FIXES:
        speech = trim(load(FIXES[r["line"]]))
        seg = np.concatenate([np.zeros(int((st - ci) * SR)), speech, np.zeros(int((co - en) * SR))]).astype(np.float32)
        lead = st - ci
    else:
        seg = full[int(ci * SR):int(co * SR)]; lead = st - ci
    sf.write(V / "lines" / f"{r['line']}.wav", seg, SR, subtype="PCM_24")
    d = len(seg) / SR
    timing.append({"line": r["line"], "t0": round(t, 3), "t1": round(t + d, 3), "dur": round(d, 3),
                   "speech_t0": round(t + lead, 3), "fixed": r["line"] in FIXES})
    out.append(seg); t += d
sf.write(V / "VO_master_v1.1.wav", np.concatenate(out), SR, subtype="PCM_24")
with open(V / "vo_timing.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(timing[0])); w.writeheader(); w.writerows(timing)
print(f"VO master {t:.2f}s, lines={len(timing)}, min line {min(x['dur'] for x in timing):.2f}s, max {max(x['dur'] for x in timing):.2f}s")
