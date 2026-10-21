# Split act takes into per-line clips using Scribe word timings to locate each
# line boundary, then cut at the quietest 10 ms point inside that pause.
import json, re, subprocess, difflib
import numpy as np
from script_v05 import ACTS
from split_vo11 import act_lines, load, SR
ACT_FILES = ["11_close"]

def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower().replace("’", "'"))

def main():
    words = [w for w in json.load(open("words12_close.json"))["words"] if w.get("type", "word") == "word"]
    # act offsets in the concatenated file (2 s gaps)
    offs, off = {}, 0.0
    for f in ACT_FILES:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  f"vo12/act_{f}.wav"], capture_output=True, text=True).stdout)
        offs[f] = (off, d)
        off += d + 2.0
    # script tokens with (act, line) labels
    toks, lab = [], []
    groups = act_lines()[-1:]
    for f, lines in zip(ACT_FILES, groups):
        for k, (t, _, _) in enumerate(lines):
            for w in t.split():
                n = norm(w)
                if n:
                    toks.append(n); lab.append((f, k))
    stoks = [norm(w["text"]) for w in words]
    sm = difflib.SequenceMatcher(a=toks, b=stoks, autojunk=False)
    tmap = {}
    for a, b, n in sm.get_matching_blocks():
        for i in range(n):
            tmap[a + i] = b + i
    print(f"matched {len(tmap)}/{len(toks)} script tokens")
    # per line: first/last matched transcript word
    span = {}
    for i, l in enumerate(lab):
        if i in tmap:
            j = tmap[i]
            s, e = words[j]["start"], words[j]["end"]
            if l not in span:
                span[l] = [s, e]
            span[l][0] = min(span[l][0], s); span[l][1] = max(span[l][1], e)
    meta = []
    for f, lines in zip(ACT_FILES, groups):
        o, d = offs[f]
        x = load(f"vo12/act_{f}.wav")
        hop = SR // 100
        n = len(x) // hop
        rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
        cuts = [0]
        for k in range(len(lines) - 1):
            e = span[(f, k)][1] - o
            s = span[(f, k + 1)][0] - o
            a, b = int(e * 100), int(s * 100)
            if b <= a:
                b = a + 1
            # quietest frame in the gap, ignoring 30 ms either side of word edges
            lo, hi = a + 3, max(a + 4, b - 3)
            gap = (s - e)
            if gap < 0.15:
                # Scribe word edges can swallow the pause; search wider around the boundary
                lo, hi = max(1, a - 40), b + 3
            q = lo + int(np.argmin(rms[lo:hi]))
            if gap < 0.12:
                print(f"  WARN act {f} line {k}->{k+1}: gap only {gap:.3f}s")
            cuts.append(q * hop)
        cuts.append(len(x))
        for k, line in enumerate(lines):
            seg = x[cuts[k]:cuts[k + 1]].copy()
            fade = int(0.008 * SR)
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
            name = f"clips12/{f}_{k:02d}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", name],
                           input=seg.tobytes(), check=True)
            # word-level timings relative to clip start, for captions
            ws = []
            for i, l in enumerate(lab):
                if l == (f, k) and i in tmap:
                    w = words[tmap[i]]
                    ws.append((w["text"], w["start"] - o - cuts[k] / SR, w["end"] - o - cuts[k] / SR))
            meta.append({"act": f, "idx": k, "file": name, "dur": len(seg) / SR, "text": line[0],
                         "speech_start": span[(f, k)][0] - o - cuts[k] / SR,
                         "speech_end": span[(f, k)][1] - o - cuts[k] / SR, "words": ws})
    allc = [m for m in json.load(open("clips12/clips.json")) if m["act"] != "11_close"] + meta
    json.dump(allc, open("clips12/clips.json", "w"), indent=1)
    print("clips", len(meta), "total", sum(m["dur"] for m in meta))

if __name__ == "__main__":
    main()
