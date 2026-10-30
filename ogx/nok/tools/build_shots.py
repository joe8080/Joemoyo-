"""Locked script + real VO timing -> shots.json (one picture per narration line) and ai_prompts.json.
Picture timing comes only from audio/vo/vo_timing.csv (cut from the real narration)."""
import csv, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
END_CARD_S = 5.0
XFADE_S = 0.5

# Verbatim from credits.md (Eden bba0f4d7), unlabelled form.
CREDITS = {
    "NOK01": "Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0",
    "NOK02": "Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0",
    "NOK03": "Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain",
    "NOK04": "Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0",
    "NOK05": "Nok head · Kimbell Art Museum (AP 1996.04) · Photo: FA2010, Public domain",
    "NOK06": "Excavation at the Nok site of Ido · Louis Champion et al. 2022 · CC BY 4.0",
}
REAL_FILES = {
    "NOK01": "NOK01_Honolulu_8349.1_head.jpg", "NOK02": "NOK02_Honolulu_8348.1_kneeling.jpg",
    "NOK03": "NOK03_Louvre_70.1998.11.1_seated.jpg", "NOK04": "NOK04_Cleveland_1995.21_head.jpg",
    "NOK05": "NOK05_Kimbell_AP1996.04_head.jpg", "NOK06": "NOK06_Ido_excavation_Champion2022.webp",
}
# Text-free animated graphics (no labels, no map tags, no numerals on screen).
GFX = {"L07": ("map", {}), "L23": ("chrono", {"stage": "A"}), "L28": ("chrono", {"stage": "B_start"}),
       "L29": ("chrono", {"stage": "B_main"}), "L30": ("chrono", {"stage": "B_end"}),
       "L32": ("chrono", {"stage": "B_iron"})}

STYLE = ("Cinematic documentary still photograph, natural light, warm earth palette of laterite red, ochre and "
         "savanna green, gentle film grain, 35mm lens, shallow-to-medium depth of field with a clearly separated "
         "foreground subject and a distant background, rule-of-thirds composition, 16:9. ")
NEGATIVE = (" No text, no letters, no numbers, no signage, no labels, no watermark, no logos, no flags, no sculptures "
            "or figurines, no artefacts that look like museum objects, no recognisable faces.")

# camera move cycle: varied, never mechanical
MOVES = ["push", "pan_r", "pull", "pan_l", "push_l", "tilt_up", "pull_r", "push_r"]

def overlay_for(desc):
    d = desc.lower()
    if any(k in d for k in ("furnace", "kiln", "firelight", "fire")): return "embers"
    if any(k in d for k in ("rain", "storm")): return "rain"
    if any(k in d for k in ("mist", "dawn", "first light", "haze", "smoke", "dusk", "evening")): return "mist"
    return "dust"

rows = [l for l in (ROOT / "story/script.md").read_text().splitlines() if re.match(r"\| L\d\d ", l)]
timing = {r["line"]: r for r in csv.DictReader(open(ROOT / "audio/vo/vo_timing.csv"))}
shots, prompts = [], {}
for i, l in enumerate(rows):
    c = [x.strip() for x in l.split("|")[1:-1]]
    lid, scene, text, claims, pic = c
    t = timing[lid]
    s = {"line": lid, "scene": scene, "t0": float(t["t0"]), "t1": float(t["t1"]), "text": text,
         "move": MOVES[i % len(MOVES)], "credit": None}
    if pic.startswith("REAL"):
        key = re.search(r"NOK0\d", pic).group(0)
        s.update(kind="real", asset=f"assets/real/{REAL_FILES[key]}", real=key, credit=CREDITS[key], overlay="dust")
        if "tilt up" in pic: s["move"] = "tilt_up"
        if lid == "L01": s["move"] = "push"
    elif pic.startswith("GFX"):
        g, opts = GFX[lid]
        s.update(kind="gfx", gfx=g, gfx_opts=opts, overlay="dust", move="push" if g == "map" else "pan_r")
    else:
        desc = pic.split(":", 1)[1].strip()
        s.update(kind="ai", asset=f"assets/ai/{lid}.png", overlay=overlay_for(desc), desc=desc)
        prompts[lid] = STYLE + desc[0].upper() + desc[1:] + "." + NEGATIVE
    shots.append(s)
# first frame starts at 0; end card after the last line
total = shots[-1]["t1"] + END_CARD_S
film = {"fps": 24, "w": 1920, "h": 1080, "xfade": XFADE_S, "total": round(total, 3),
        "end_card": {"t0": shots[-1]["t1"], "t1": round(total, 3)}, "shots": shots}
json.dump(film, open(ROOT / "build/shots.json", "w"), indent=1, ensure_ascii=False)
json.dump(prompts, open(ROOT / "build/ai_prompts.json", "w"), indent=1, ensure_ascii=False)
kinds = {k: sum(s["kind"] == k for s in shots) for k in ("ai", "real", "gfx")}
print(f"shots={len(shots)} {kinds} total={total:.2f}s ({int(total // 60)}:{total % 60:04.1f})")
