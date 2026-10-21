# EN-GB captions from the locked script text, timed by Scribe word timings (spellings from the script).
import json
shots = json.load(open("timeline.json"))
def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}".replace(",1000", ",999")
REPL = [("eighteen-eighties and nineties", "1880s and 1890s"), ("eighteen-eighties", "1880s"),
 ("eighteen ninety-eight", "1898"), ("eighteen ninety-six", "1896"), ("eighteen eighty-nine", "1889"),
 ("eighteen ninety-three", "1893"), ("eighteen ninety-five", "1895"), ("nineteen thirty-five", "1935"),
 ("nineteen forty-one", "1941"), ("about seventy thousand men to more than a hundred thousand", "about 70,000 men to more than 100,000"),
 ("around two thousand", "around 2,000"), ("about six thousand", "about 6,000"), ("around three thousand", "around 3,000"),
 ("four thousand to seven thousand", "4,000 to 7,000"), ("fifteen and eighteen thousand", "15,000 and 18,000"),
 ("the seventh of December", "7 December"), ("the first of March", "1 March"), ("the twenty-eighth of February", "28 February"),
 ("the twenty-ninth of February", "29 February"), ("Article seventeen", "Article 17"), ("Menelik the Second", "Menelik II")]
def numerals(t):
    for a, b in REPL: t = t.replace(a, b.replace(" ", "\u00a0"))
    return t
cues = []
for s in shots:
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
open("OGX_Adwa_1896_v1.4_EN-GB.srt", "w").write("\n".join(out))
print(len(out), "cues")
