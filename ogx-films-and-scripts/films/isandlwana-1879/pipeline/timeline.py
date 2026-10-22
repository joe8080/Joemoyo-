# Builds the edit timeline: one shot per narration line (OGX pacing), second pictures from V2.
import json
from script_isa import ACTS, V2

LEAD_IN = 0.6
GAP = 0.8
ACT_GAP = 1.8
END_TAIL = 8.0
HOLDS = {  # extra seconds after specific lines (deliberate beats)
    "But that's only half of it. The real question is how the Zulu army did it.": 2.4,
    "This is the story of Isandlwana.": 2.2,
    "The whole Zulu army was there.": 1.0,
    "He was shot dead. But the regiment rose, and the charge went in.": 0.6,
    "So the Zulu won the battle. But the kingdom lost the war.": 1.2,
    "And it won because the British camp it found was split, spread out, and too sure of itself.": 1.0,
}
MAP_MIN = {"horns_doctrine2": 9.0, "horns_open": 8.0, "right_horn": 6.5, "closed": 7.0, "zoom_isa": 9.0, "columns": 7.5}

def build():
    clips = json.load(open("clips/clips.json"))
    shots, t, ci = [], LEAD_IN, 0
    for ai, (act, title, lines) in enumerate(ACTS):
        for k, (text, vis, ost) in enumerate(lines):
            c = clips[ci]; ci += 1
            assert c["text"] == text, (c["text"], text)
            last_in_act = k == len(lines) - 1
            gap = (ACT_GAP if last_in_act and act != "COLD OPEN" else GAP) + HOLDS.get(text, 0.0)
            if ai == len(ACTS) - 1 and last_in_act:
                gap = END_TAIL
            start = t if shots else 0.0
            dur = (t - start) + c["dur"] + gap
            if vis[0] == "map" and vis[1] in MAP_MIN and dur < MAP_MIN[vis[1]]:
                dur = MAP_MIN[vis[1]]
            shots.append({"n": len(shots) + 1, "act": act, "act_title": title, "act_first": k == 0, "text": text,
                          "vis": vis, "ost": ost, "start": round(start, 3), "dur": round(dur, 3),
                          "vo_file": c["file"], "vo_at": round(t, 3), "vo_dur": c["dur"], "words": c["words"]})
            n = len(shots)
            if n in V2:
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
        acts.setdefault(s["act"], [s["start"], 0]); acts[s["act"]][1] = s["start"] + s["dur"]
    for a, (s, e) in acts.items():
        print(f"{a:10s} {s:7.1f} -> {e:7.1f}  ({e-s:5.1f}s)")
