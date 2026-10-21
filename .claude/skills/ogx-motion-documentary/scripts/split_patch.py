# Split the v1.5 patch take into per-line clips at the quietest 10 ms point between lines,
# then match each clip's loudness to the original clip it replaces.
import json, re, subprocess
import numpy as np
SR = 48000
LINES = [
 (4, "This is a later artistic reconstruction. But the battle was real."),
 (21, "He was patient, and he planned ahead. Through the eighteen-eighties and nineties, he imported modern rifles in large numbers."),
 (27, "In the same years, Menelik's armies were conquering kingdoms to the south and west, like Wolaita. Kaffa followed in eighteen ninety-seven, after Adwa."),
 (41, "A major Ethiopian victory came on the seventh of December, at a mountain called Amba Alagi."),
 (47, "So Ethiopian troops took the springs. Some accounts credit Taytu with the plan."),
 (58, "In late February, Baratieri called in his brigade commanders and put it to them: pull back, or advance?"),
 (71, "Around dawn, his brigade ran into the Ethiopian army. On its own."),
 (81, "The Italian centre had collapsed, but fighting went on into the afternoon. Arimondi and Dabormida were killed, and Albertone was taken prisoner."),
 (83, "Estimates of the losses differ."),
 (84, "By one estimate, the Italian-led army lost about six thousand men killed, and around three thousand were taken prisoner."),
 (94, "In eighteen ninety-seven, France and Britain signed agreements with Menelik."),
 (107, "Today, Ethiopia commemorates the victory with the Adwa Victory Day holiday, on the second of March."),
]
words = [w for w in json.load(open("words_D.json"))["words"] if w.get("type", "word") == "word"]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "take_D.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).copy()
counts = [len(t.split()) for _, t in LINES]
assert sum(counts) == len(words), (sum(counts), len(words))
spans, i = [], 0
for c in counts:
    spans.append((words[i]["start"], words[i + c - 1]["end"], words[i:i + c])); i += c
hop = SR // 100
n = len(x) // hop
rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
cuts = [0.0]
for k in range(len(spans) - 1):
    a, b = int(spans[k][1] * 100) + 2, int(spans[k + 1][0] * 100) - 2
    if b <= a:
        a, b = int(spans[k][1] * 100), int(spans[k + 1][0] * 100) + 1
    j = a + int(np.argmin(rms[a:b])) if b > a else a
    cuts.append(j / 100)
cuts.append(len(x) / SR)

def lufs(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])

tl = {s["n"]: s for s in json.load(open("../v13/timeline.json"))}
meta = {}
for k, ((n, text), (s, e, ws)) in enumerate(zip(LINES, spans)):
    a, b = cuts[k], cuts[k + 1]
    # keep at most 0.25 s of air before the first word and 0.35 s after the last
    a = max(a, s - 0.25); b = min(b, e + 0.35)
    seg = x[int(a * SR):int(b * SR)].copy()
    f = int(0.012 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
    out = f"line_{n:03d}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", out],
                   input=seg.tobytes(), check=True)
    old = "../v13/" + tl[n]["vo_file"]
    g = lufs(old) - lufs(out)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-af", f"volume={g:.2f}dB", "-c:a", "pcm_s16le", out + ".tmp.wav"], check=True)
    subprocess.run(["mv", out + ".tmp.wav", out], check=True)
    meta[n] = {"text": text, "file": "../vo15/" + out, "dur": round(len(seg) / SR, 3), "gain_db": round(g, 2),
               "words": [[w["text"], round(w["start"] - a, 3), round(w["end"] - a, 3)] for w in ws]}
    print(n, f"{len(seg)/SR:5.2f}s (old {tl[n]['vo_dur']:.2f}s) gain {g:+.1f} dB |", text[:60])
json.dump(meta, open("lines15.json", "w"), indent=1)
