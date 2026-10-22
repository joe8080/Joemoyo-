# Split each act take into per-line clips at the quietest 10 ms point between lines; words carry display text.
import json, subprocess
import numpy as np
SR = 48000
acts = json.load(open("voice_acts.json"))
out = []
for ai, g in enumerate(acts):
    d = json.load(open(f"vo/words{ai}.json"))
    words = [w for w in (d["words"] if isinstance(d, dict) else d) if w.get("type", "word") == "word"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"vo/act{ai}.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    counts = [len(t.split()) for t in g["voiced"]]
    assert sum(counts) == len(words), (g["act"], sum(counts), len(words))
    spans, i = [], 0
    for c in counts:
        spans.append((words[i]["start"], words[i + c - 1]["end"], words[i:i + c])); i += c
    hop = SR // 100; n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    cuts = [0.0]
    for k in range(len(spans) - 1):
        a, b = int(spans[k][1] * 100), int(spans[k + 1][0] * 100) + 1
        j = a + int(np.argmin(rms[a:b])) if b > a else a
        cuts.append(j / 100)
    cuts.append(len(x) / SR)
    for k, (line, (s, e, ws)) in enumerate(zip(g["lines"], spans)):
        a, b = max(cuts[k], s - 0.2), min(cuts[k + 1], e + 0.3)
        seg = x[int(a * SR):int(b * SR)].copy()
        f = int(0.012 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        fn = f"vowav/a{ai}_l{k:02d}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", fn],
                       input=seg.tobytes(), check=True)
        disp = line.split()
        if len(disp) != len(ws):
            print("WORDCOUNT MISMATCH", ai, k, len(disp), len(ws))
            disp = [w["text"] for w in ws]
        out.append({"text": line, "file": fn, "dur": round(len(seg) / SR, 3),
                    "words": [[dw, round(w["start"] - a, 3), round(w["end"] - a, 3)] for dw, w in zip(disp, ws)]})
json.dump(out, open("clips/clips.json", "w"), indent=1)
print(len(out), "clips", round(sum(c["dur"] for c in out), 1), "s")
