# Isandlwana EN-GB captions from the locked script text, timed by Scribe word timings (spellings from the script).
import json
shots = json.load(open("timeline.json"))
def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}".replace(",1000", ",999")
REPL = [("one thousand to more than three thousand", "1,000 to more than 3,000"),
 ("twenty to twenty-five thousand", "20,000 to 25,000"), ("More than thirteen hundred", "More than 1,300"),
 ("About eighteen hundred", "About 1,800"), ("a hundred and fifty", "150"), ("thirteen chiefdoms", "13 chiefdoms"),
 ("the twenty-second of January, eighteen seventy-nine", "22 January 1879"), ("the fourth of July, eighteen seventy-nine", "4 July 1879"),
 ("December eighteen seventy-eight", "December 1878"), ("March, eighteen seventy-nine", "March 1879"),
 ("January nineteen ninety-nine", "January 1999"), ("on the twenty-second", "on the 22nd"), ("eighteen seventy-nine", "1879")]
def numerals(t):
    for a, b in REPL: t = t.replace(a, b.replace(" ", "\u00a0"))
    return t
cues = []
for s in shots:
    if not s.get("vo_file"):
        continue
    words = numerals(s["text"]).split(" ")
    tw = s["words"]
    if len(tw) == len(words):
        times = [(s["vo_at"] + a, s["vo_at"] + b) for _, a, b in tw]
    else:  # distribute across the measured speech span by character length
        a0, a1 = s["vo_at"] + tw[0][1], s["vo_at"] + tw[-1][2]
        tot = sum(len(w) + 1 for w in words); acc = 0; times = []
        for w in words:
            st = a0 + (a1 - a0) * acc / tot; acc += len(w) + 1
            times.append((st, a0 + (a1 - a0) * acc / tot))
    # chunk into captions of <= 42 chars per line, max 2 lines (~84 chars)
    import math
    k = max(1, math.ceil(len(" ".join(words)) / 80))
    target = len(" ".join(words)) / k
    chunk, start, acc = [], None, 0
    for i, (w, (a, b)) in enumerate(zip(words, times)):
        if start is None: start = a
        chunk.append(w); prev_end = b; acc = len(" ".join(chunk))
        brk = acc >= target * 0.9 and (w.endswith((",", ".", ":", "?")) or acc >= target)
        if brk and i < len(words) - 1 and len(cues_line := " ".join(words[i + 1:])) > 12:
            cues.append([start, prev_end, " ".join(chunk)]); chunk, start = [], None
    if chunk: cues.append([start, prev_end, " ".join(chunk)])
def wrap(t):
    if len(t) <= 42: return t
    ws = t.split(" "); best = None
    for i in range(1, len(ws)):
        l1, l2 = " ".join(ws[:i]), " ".join(ws[i:])
        sc = max(len(l1), len(l2))
        if best is None or sc < best[0]: best = (sc, l1 + "\n" + l2)
    return best[1]
out = []
for i, (a, b, t) in enumerate(cues):
    b = max(b + 0.25, a + 1.0)
    if i + 1 < len(cues): b = min(b, cues[i + 1][0] - 0.04)
    out.append(f"{i+1}\n{ts(a)} --> {ts(b)}\n{wrap(t).replace(chr(160), ' ')}\n")
open("OGX_Isandlwana_1879_v1.1_EN-GB.srt", "w").write("\n".join(out))
print(len(out), "cues")
