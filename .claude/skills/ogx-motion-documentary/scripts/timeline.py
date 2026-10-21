# Builds the edit timeline: one shot per narration line (Production OS 2.2/2.3 pacing).
import json
from script_v06 import ACTS, V2
from split_vo import ACT_FILES, act_lines

LEAD_IN = 0.6
GAP = 0.8
ACT_GAP = 1.8
END_TAIL = 8.0
HOLDS = {  # extra seconds after specific lines (deliberate beats)
    "The real question is how they did it.": 2.6,          # question card, silence under it
    "This is the story of Adwa.": 2.2,         # title holds >=1.5 s, then dissolve
    "Three brigades. Three battles. No line.": 1.0,
    "A European army had been beaten in open battle by an African state.": 1.0,
    "Tell it that way, and the winners almost vanish.": 0.8,
    "Ethiopia won at Adwa because it was ready, and Italy wasn't.": 1.2,
}

def build():
    clips = json.load(open("clips/clips.json"))
    groups = act_lines()
    # act names per merged group (cold open + title merged into group 0)
    act_meta = [("COLD OPEN", None)] + [(a[0], a[1]) for a in ACTS[2:]]
    shots, t, ci = [], LEAD_IN, 0
    for gi, (f, lines) in enumerate(zip(ACT_FILES, groups)):
        for k, (text, vis, ost) in enumerate(lines):
            c = clips[ci]; ci += 1
            assert c["text"] == text
            last_in_act = k == len(lines) - 1
            gap = ACT_GAP if last_in_act else GAP
            gap += HOLDS.get(text, 0.0)
            if gi == len(groups) - 1 and last_in_act:
                gap = END_TAIL
            start = t if shots else 0.0
            dur = (t - start) + c["dur"] + gap
            shots.append({"n": len(shots) + 1, "act": act_meta[gi][0], "act_title": act_meta[gi][1],
                          "act_first": k == 0, "text": text, "vis": vis, "ost": ost,
                          "start": round(start, 3), "dur": round(dur, 3),
                          "vo_file": c["file"], "vo_at": round(t, 3), "vo_dur": c["dur"],
                          "words": c["words"]})
            n = len(shots)
            if n in V2:  # second picture: cut at a word boundary near the middle of the line, preferring punctuation
                ws = c["words"]
                mid = (ws[0][1] + ws[-1][2]) / 2
                cands = [(abs(w[2] - mid) * (0.5 if w[0][-1] in ",.:;?" else 1.0), w[2]) for w in ws[1:-1]]
                cut = min(cands)[1] if cands else mid
                shots[-1]["vis2"] = list(V2[n])
                shots[-1]["switch"] = round(t - start + cut + 0.15, 3)
            t = start + dur
    return shots, t

if __name__ == "__main__":
    shots, total = build()
    json.dump(shots, open("timeline.json", "w"), indent=1)
    print(f"shots={len(shots)} total={total:.1f}s = {int(total//60)}:{total%60:04.1f}")
    acts = {}
    for s in shots:
        acts.setdefault(s["act"], [s["start"], 0])
        acts[s["act"]][1] = s["start"] + s["dur"]
    for a, (s, e) in acts.items():
        print(f"{a:10s} {s:7.1f} -> {e:7.1f}  ({e-s:5.1f}s)")
