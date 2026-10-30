"""v1.1 shot list = the locked v1.0 build/shots.json plus QA's notes (30 Oct). v1.0 files are only read, never
written: output goes to build/v1.1/shots.json. Voice, timing, length and credit lines are unchanged; no new stills.
  1. Parallax seams: every AI shot gets the seam-safe layer split (mirrored infill instead of a blurred inpaint)
     and an edge guard (constant zoom so no layer runs off the plate), except L05, L09, L11, which per QA have no
     depth split at all (flat 2D pan + push on the whole still). The sweep of every other AI shot added L17, L41
     (sideways-only parallax, "slide") and L58 (ground-only split).
  2. L38 (modern conifers, metal roofs, factory smoke): reuses the on-brief L50 still, cropped to its homesteads
     and mirrored, so it doesn't read as the same frame at L50. Zero credits.
  3. L45 (cut bricks, roof-tile sherds): real photo instead, NOK06 panel c (terracotta fragments in a pit at Ido),
     cropped above its printed panel label; credit is the credits.md "(cropped)" line.
  4. NOK01 at most twice: L02 = NOK01 cropped to the hairstyle (credit unchanged); L62 = NOK04 with its own line."""
import json, copy, pathlib, cv2

ROOT = pathlib.Path(__file__).resolve().parents[1]
film = json.load(open(ROOT / "build/shots.json"))
# credit lines and files come from the v1.0 shot list itself (importing build_shots would re-run and rewrite it)
REAL = {s["real"]: s for s in film["shots"] if s.get("real")}
v11 = copy.deepcopy(film)
S = {s["line"]: s for s in v11["shots"]}

for s in v11["shots"]:
    if s["kind"] == "ai":
        s["layer"] = {"fill": "reflect"}
        s["edge_guard"] = True
# QA file check (30 Oct, round 2): L05, L09, L11 get NO depth parallax at all, not even slide-only: a flat 2D pan
# with a slow push on the whole still, plus the usual overlay.
for ln, mv in (("L05", "pan_l"), ("L09", "pan_r"), ("L11", "pan_l")):
    for k in ("layer", "slide", "edge_guard"): S[ln].pop(k, None)
    S[ln].update(flat=True, move=mv)
# found in the sweep of the other AI shots: mirror ghost at the end of a push (L17 spoil-heap edge, L41 furnace
# wall) -> sideways-only parallax with a pan; L58 awning cut out as a floating layer, tearing from its poles
for ln, mv in (("L17", "pan_r"), ("L41", "pan_l")):
    S[ln].update(slide=True, move=mv)
S["L58"]["layer"] = {"fill": "reflect", "ground_only": True}
S["L49"]["fg_boost"] = 1.3     # v1.1 QA proxy: FG travel 2.68 % (< 3 % floor) after the seam-safe split

# 2. L38 <- L50, cropped to the homesteads (70 % width, from x 30 %, y 10 %) and mirrored
src = cv2.imread(str(ROOT / "assets/ai/L50.png")); h, w = src.shape[:2]
x0, y0, cw = int(0.30 * w), int(0.10 * h), int(0.70 * w); ch = int(cw * 9 / 16)
der = ROOT / "assets/ai/L38_v11_from_L50.png"
cv2.imwrite(str(der), cv2.flip(src[y0:y0 + ch, x0:x0 + cw], 1))
S["L38"].update(asset=str(der.relative_to(ROOT)), desc="reuse of L50 (cropped, mirrored): homesteads spaced across fields at dusk",
                derived_from={"still": "L50", "crop_frac": [0.30, 0.10, 0.70], "mirror": True})

# 3. L45 <- NOK06 panel c (plate rows 993-1289, cols 0-416; its "Feature 16-3" / "c" label starts at row 1300)
S["L45"] = {**{k: S["L45"][k] for k in ("line", "scene", "t0", "t1", "text", "move")},
            "kind": "real", "asset": REAL["NOK06"]["asset"], "real": "NOK06",
            "credit": REAL["NOK06"]["credit"], "overlay": "dust",
            "view": {"crop": [0, 993, 416, 1289], "scale_h": 0.66, "max_up": 2.0}}

# 4. L02: NOK01 hairstyle crop (top 40 %), push in; credit line unchanged
S["L02"].update(view={"crop": [0, 0, 1650, 1300], "scale_h": 1.0}, move="push")
S["L62"].update(asset=REAL["NOK04"]["asset"], real="NOK04", credit=REAL["NOK04"]["credit"],
                view={"scale_h": 1.3}, move="push")

v11["shots"] = [S[s["line"]] for s in film["shots"]]
v11["version"] = "v1.1"
out = ROOT / "build/v1.1"; out.mkdir(parents=True, exist_ok=True)
json.dump(v11, open(out / "shots.json", "w"), indent=1, ensure_ascii=False)
uses = {}
for s in v11["shots"]:
    if s.get("real"): uses.setdefault(s["real"], []).append(s["line"])
print("total", v11["total"], "real uses", uses)
assert len(uses["NOK01"]) <= 2 and "NOK05" not in uses
