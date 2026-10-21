# v1.5: apply MJ fact-check brief (21 Oct 2026) to the v1.4 timeline.
# New narration for 12 lines, one line cut (V36), picture swaps (A13 -> A05/A07, A09 Amba panels -> map + N51),
# on-screen text fixes, and extra holds on battle maps so each movement can be followed on a phone.
import json
tl = json.load(open("timeline_v14.json"))
new = {int(k): v for k, v in json.load(open("../vo15/lines15.json")).items()}
OST = {4: "A LATER RECONSTRUCTION", 13: "AMHARIC TEXT · HE MAY · PARAPHRASE", 14: "ITALIAN TEXT · HE MUST · PARAPHRASE", 41: "AMBA ALAGI · 7 DECEMBER 1895", 47: "SOME ACCOUNTS · TAYTU'S PLAN",
       58: "LATE FEBRUARY 1896", 71: "1 MARCH · AROUND DAWN", 83: "ESTIMATES DIFFER",
       84: "ITALIAN-LED ARMY · c. 6,000 DEAD · c. 3,000 TAKEN", 94: "1897 · AGREEMENTS WITH FRANCE AND BRITAIN",
       100: "ETHIOPIAN PAINTING · c. 1940", 106: "1935 INVASION · OCCUPATION TO 1941", 107: "ADWA VICTORY DAY · 2 MARCH"}
VIS = {15: (["card", "ONE VERB · PARAPHRASE", "May. Must."], None), 41: (["map", "amba"], None), 42: (["ai", "N51"], None),
       97: (["arch", "A07", [0.42, 0.0, 1.0, 0.62]], None), 98: (["arch", "A05", [0.0, 0.08, 1.0, 0.62]], None)}
HOLD = {"south": 0.6, "plan_b": 1.0, "plan_c": 1.0, "albertone_b": 0.8, "gap": 0.8, "dabormida": 1.0, "pieces": 0.8}
CUT = {104}
out, t = [], 0.0
for s in tl:
    if s["n"] in CUT:
        continue
    s = dict(s)
    lead = s["vo_at"] - s["start"]
    dur = s["dur"]
    n = s["n"]
    if n in new:
        L = new[n]
        dur += L["dur"] - s["vo_dur"]
        s.update(text=L["text"], vo_file=L["file"], vo_dur=L["dur"], words=L["words"])
        if "vis2" in s:  # re-place the second-picture cut at a word boundary near the middle
            ws = L["words"]; mid = (ws[0][1] + ws[-1][2]) / 2
            c = min((abs(w[2] - mid) * (0.5 if w[0][-1] in ",.:;?" else 1.0), w[2]) for w in ws[1:-1])[1]
            s["switch"] = round(lead + c + 0.15, 3)
    if n in OST:
        s["ost"] = OST[n]
    if n in VIS:
        s["vis"], v2 = VIS[n]
        if v2 is None:
            s.pop("vis2", None); s.pop("switch", None)
    if s["vis"][0] == "map":
        dur += HOLD.get(s["vis"][1], 0.0)
    s["v14_n"] = n
    s["start"] = round(t, 3); s["vo_at"] = round(t + lead, 3); s["dur"] = round(dur, 3)
    t += dur
    out.append(s)
for i, s in enumerate(out):
    s["n"] = i + 1
json.dump(out, open("timeline.json", "w"), indent=1)
old_total = tl[-1]["start"] + tl[-1]["dur"]
print(f"shots {len(tl)} -> {len(out)}; total {old_total:.2f} -> {t:.2f} s ({int(t//60)}:{t%60:05.2f}); frames {round(t*24)}")
