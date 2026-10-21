# Split each act take into per-line clips at the centre of the measured pauses
# (Production OS v2.0 2.2: 10 ms RMS envelope, longest quiet runs, no speech trimming,
# 8 ms edge fades applied only inside silence).
import json, subprocess, sys
import numpy as np
from script_v05 import ACTS

SR = 48000
ACT_FILES = ["00_coldopen", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11_close"]

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def quiet_runs(x, thr_db=-45.0):
    hop = SR // 100  # 10 ms
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    q = db < thr_db
    runs, i = [], 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]:
                j += 1
            runs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    return runs

def act_lines():
    groups = [lines for _, _, lines in ACTS]
    # cold open + title share one take
    merged = [groups[0] + groups[1]] + groups[2:]
    return merged

def main(vo_dir, out_dir):
    meta = []
    for f, lines in zip(ACT_FILES, act_lines()):
        x = load(f"{vo_dir}/act_{f}.mp3")
        runs = quiet_runs(x)
        n_cuts = len(lines) - 1
        # interior runs only (not leading/trailing silence)
        interior = [r for r in runs if r[0] > 0 and r[1] < len(x)]
        best = sorted(interior, key=lambda r: r[1] - r[0], reverse=True)[:n_cuts]
        best = sorted(best)
        shortest = min((r[1] - r[0]) / SR for r in best) if best else 0
        nxt = sorted(interior, key=lambda r: r[1] - r[0], reverse=True)
        runner = (nxt[n_cuts][1] - nxt[n_cuts][0]) / SR if len(nxt) > n_cuts else 0
        cuts = [0] + [(a + b) // 2 for a, b in best] + [len(x)]
        print(f"act {f}: lines={len(lines)} cuts={n_cuts} shortest_used={shortest:.3f}s next_best={runner:.3f}s")
        for k, line in enumerate(lines):
            seg = x[cuts[k]:cuts[k + 1]].copy()
            fade = int(0.008 * SR)
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
            name = f"{out_dir}/{f}_{k:02d}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", name],
                           input=seg.tobytes(), check=True)
            meta.append({"act": f, "idx": k, "file": name, "dur": len(seg) / SR, "text": line[0]})
    json.dump(meta, open(f"{out_dir}/clips.json", "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
