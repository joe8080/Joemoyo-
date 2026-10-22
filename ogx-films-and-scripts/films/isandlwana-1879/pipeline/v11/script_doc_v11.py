# Writes the v1.1 "as played" narration script from timeline.json (export timecodes, markers, on-screen text).
import json
tl = json.load(open("timeline.json"))
tc = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"
TRIMMED = {26: "trimmed inside the take; removed: \"And nobody in the camp knew they were there.\"",
           44: "trimmed inside the take; removed: \"but by then, the battle for the camp had already been decided.\""}
out, k = [], 0
for s in tl:
    if s.get("marker"):
        out.append(f"\n**[{tc(s['start'])} · MARKER: {s['marker'].replace('  ', ' ')}]**\n")
    if s["src"] == "TITLE":
        out.append(f"*{tc(s['start'])} title sting: ISANDLWANA · 1879 (no voice)*\n"); continue
    if s["src"] == "RIDGE":
        out.append(f"*{tc(s['start'])} return to the ridge (no voice)*\n"); continue
    if s["src"] == "SUBCARD":
        out.append(f"*{tc(s['start'])} end card with visual subscribe badge (silent, 6 s)*\n"); continue
    k += 1
    extra = []
    if s.get("ost"): extra.append(f"on screen: {s['ost'].replace('  ', ' ')}")
    if s["src"] in TRIMMED: extra.append("✂ " + TRIMMED[s["src"]])
    if s.get("badge"): extra.append("subscribe badge appears (visual only)")
    tail = f" *({'; '.join(extra)})*" if extra else ""
    out.append(f"{k}. `{tc(s['vo_at'])}` {s['text']} — v1.0 L{s['src']}{tail}")
print("\n".join(out))
print(f"\n**Totals:** {k} voiced lines (2 trimmed inside their takes, 0 new recordings). Runtime {tc(tl[-1]['start'] + tl[-1]['dur'])}.")
