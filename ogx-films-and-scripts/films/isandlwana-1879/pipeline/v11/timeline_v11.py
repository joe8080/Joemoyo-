# Isandlwana v1.1 timeline: "One day, one hill" (MJ-approved paper edit, 22 Oct 2026).
# Re-orders the recorded v1.0 lines (by v1.0 line number L) with no new narration. Two lines are trimmed
# inside their takes (L26, L44). Chapters are date/time markers, not numbered acts.
import json

V10 = {s["n"]: s for s in json.load(open("timeline_v10.json"))}
TRIM = {26: ("vowav11/L26_trim.wav", 3.99, "It was just a few miles from the British camp. Tens of thousands of men."),
        44: ("vowav11/L44_trim.wav", 2.68, "That afternoon a partial eclipse dimmed the sun.")}

LEAD_IN, GAP, SECTION_GAP, END_TAIL = 0.6, 0.8, 1.6, 6.0
BATTLE_GAP = 0.45      # the battle runs as one tightening movement
BUILD_GAP = 1.0        # the approach breathes
MAP_MIN = {"horns_doctrine2": 9.0, "horns_open": 7.0, "right_horn": 6.0, "closed": 7.0, "zoom_isa": 9.0, "columns": 7.5}

# (section, L or special, overrides)
# overrides: vis, vis2, ost, marker, hold, badge
E = []
def add(sec, L, **kw): E.append((sec, L, kw))

# OPEN: the discovery, the day, how London told it, the question
add("OPEN", 31, ost=None, marker="22 JANUARY 1879  ·  AS MOST ACCOUNTS TELL IT")
add("OPEN", 32, hold=1.0)
add("OPEN", 26, ost="A FEW MILES APART")
add("OPEN", 4)
add("OPEN", 5, vis=["arch", "I06", None], ost="1,329 KILLED  ·  858 EUROPEAN  ·  471 AFRICAN  ·  OFFICIAL RETURN")
add("OPEN", 6, vis=["arch", "I01", None], ost="THE GRAPHIC  ·  LONDON 1879  ·  DRAWN IN LONDON")
add("OPEN", 7, vis=["ai", "Z33"], hold=2.4)
add("OPEN", 8)
add("OPEN", "TITLE")
# ARMY then WHY (one musical movement)
for L in (16, 17, 18, 19, 20):
    add("ARMY", L)
add("WHY", 10, marker="DECEMBER 1878")
for L in (11, 12, 13, 14):
    add("WHY", L)
# APPROACH and the morning of the 22nd
add("APPROACH", 21, ost="COMMON ESTIMATES  ·  20,000–25,000", marker="MID-JANUARY")
for L in (22, 23, 24, 25):
    add("APPROACH", L)
add("DAY", 27, marker="BEFORE DAWN  ·  22 JANUARY")
add("DAY", 28)
add("DAY", 29)
add("DAY", 30, badge=True, hold=0.6)
# BATTLE: back to the ridge, then one movement to the eclipse
add("BATTLE", "RIDGE")
for L in (33, 34, 35, 36, 37, 38, 39, 40, 41, 42):
    add("BATTLE", L)
add("BATTLE", 43, ost=None, marker="EARLY AFTERNOON")
add("BATTLE", 44, ost="PARTIAL ECLIPSE  ·  THAT AFTERNOON", hold=1.8)
# AFTER: the answer at the climax, the cost, how we know
add("AFTER", 55, vis=["ai", "Z23"])
add("AFTER", 57)
add("AFTER", 58, hold=0.4)
for L in (45, 46, 47, 48):
    add("AFTER", L)
# WAR
add("WAR", 49, ost="RORKE'S DRIFT", marker="22–23 JANUARY")
for L in (50, 51, 52):
    add("WAR", L)
add("WAR", 53, hold=1.2)
# MEMORY: memorial line over the cleared battlefield photograph (no sculpture image), then the sign-off
add("MEMORY", 54, vis=["arch", "I08", None], ost="THE BATTLEFIELD TODAY", marker="TODAY", hold=4.0)
add("MEMORY", 60)
add("MEMORY", "SUBCARD")

def build():
    shots, t = [], LEAD_IN
    prev_sec = None
    for idx, (sec, L, kw) in enumerate(E):
        nxt_sec = E[idx + 1][0] if idx + 1 < len(E) else None
        first = sec != prev_sec
        start = t if shots else 0.0
        if L == "TITLE":
            sh = {"text": "", "vis": ["title"], "ost": None, "vo_file": None, "vo_at": start, "vo_dur": 0.0, "words": []}
            dur = 7.0
        elif L == "RIDGE":
            sh = {"text": "", "vis": ["ai", "Z15"], "vis2": ["ai", "Z11"], "ost": None, "vo_file": None, "vo_at": start,
                  "vo_dur": 0.0, "words": [], "marker": "LATE MORNING TO MIDDAY  ·  TIMES APPROXIMATE"}
            dur = 3.4
            sh["switch"] = 1.5
        elif L == "SUBCARD":
            sh = {"text": "", "vis": ["endcard"], "ost": None, "vo_file": None, "vo_at": start, "vo_dur": 0.0, "words": []}
            dur = END_TAIL
        else:
            o = V10[L]
            sh = {k: o[k] for k in ("text", "vis", "ost", "vo_file", "vo_dur", "words")}
            if L in TRIM:
                f, d, txt = TRIM[L]
                sh.update(vo_file=f, vo_dur=d, text=txt, words=[w for w in o["words"] if w[2] <= d + 0.01])
            if "vis2" in o and "vis" not in kw:
                sh["vis2"] = o["vis2"]
                sh["_cut"] = o["switch"] - (o["vo_at"] - o["start"])   # cut point relative to voice start
            for k in ("vis", "ost", "marker", "badge"):
                if k in kw:
                    sh[k] = kw[k]
            vo_at = t
            gap = BATTLE_GAP if sec == "BATTLE" else BUILD_GAP if sec in ("APPROACH", "DAY") else GAP
            if nxt_sec and nxt_sec != sec:
                gap = SECTION_GAP
            gap += kw.get("hold", 0.0)
            dur = (vo_at - start) + sh["vo_dur"] + gap
            if sh["vis"][0] == "map" and sh["vis"][1] in MAP_MIN:
                dur = max(dur, MAP_MIN[sh["vis"][1]])
            sh["vo_at"] = round(vo_at, 3)
            if "_cut" in sh:
                cut = sh.pop("_cut")
                sh["switch"] = round(min((vo_at - start) + cut, dur - 1.0), 3)
        sh.update(n=len(shots) + 1, act=sec, act_title=None, act_first=first, start=round(start, 3), dur=round(dur, 3),
                  src=L)
        if "vo_at" in sh and not sh.get("vo_file"):
            sh["vo_at"] = round(start, 3)
        shots.append(sh)
        t = start + dur
        prev_sec = sec
    return shots, t

if __name__ == "__main__":
    shots, total = build()
    json.dump(shots, open("timeline.json", "w"), indent=1)
    print(f"shots={len(shots)} total={total:.1f}s = {int(total//60)}:{total%60:04.1f}")
    secs = {}
    for s in shots:
        secs.setdefault(s["act"], [s["start"], 0]); secs[s["act"]][1] = s["start"] + s["dur"]
    for a, (s0, e) in secs.items():
        print(f"{a:9s} {s0:7.1f} -> {e:7.1f}  ({e-s0:5.1f}s)")
