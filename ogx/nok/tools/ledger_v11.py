"""Write deliverables/ledger_v1.1.md from build/v1.1/shots.json + the OpenArt job record (v1.0 ledger untouched)."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
f = json.load(open(ROOT / "build/v1.1/shots.json")); jobs = json.load(open(ROOT / "build/openart_jobs.json"))
v10 = {s["line"]: s for s in json.load(open(ROOT / "build/shots.json"))["shots"]}
R = ["# OGX Nok v1.1 — asset and spend ledger (30 Oct 2026, UK)", "",
     "v1.1 = v1.0 plus QA's notes. Same voice, same mix, same 4:46 timing, same credit lines; no new stills.", "",
     "## Shots (one picture per narration line; timing cut from the real VO, audio/vo/vo_timing.csv)", "",
     "| Line | t0–t1 (s) | Kind | Asset | Source / licence | Camera | Layers | On-screen text |", "|---|---|---|---|---|---|---|---|"]
for s in f["shots"]:
    if s["kind"] == "ai":
        d = s.get("derived_from")
        src = (f"reuse of {d['still']} (OpenArt history {jobs.get(d['still'], '?')}), cropped and mirrored, no new generation" if d
               else f"OpenArt Wan 2.7 Image Pro (history {jobs.get(s['line'], '?')})") + ", AI still, unlabelled on screen"
        lay = "seam-safe" + (" ground-only" if s.get("layer", {}).get("ground_only") else "") + (", slide" if s.get("slide") else "") \
              + (", edge guard" if s.get("edge_guard") else "") + (f", FG ×{s['fg_boost']}" if s.get("fg_boost") else "")
    elif s["kind"] == "real":
        v = s.get("view", {}); src = f"{s['real']}, see credits_v1.1.md" + (f" (crop {v['crop']})" if v.get("crop") else "")
        lay = "photo panel over blurred extension"
    else:
        src = "Generated map (Natural Earth outlines, public domain), text-free" if s["gfx"] == "map" else "Generated chronology, text-free"
        lay = "graphic layers"
    txt = (s["credit"] or "") + ((" + name: " + s["name"]["text"]) if s.get("name") else "")
    ch = " (v1.1 change)" if (s.get("asset") != v10[s["line"]].get("asset") or s.get("view") != v10[s["line"]].get("view")
                              or s["move"] != v10[s["line"]]["move"]) else ""
    R.append(f"| {s['line']}{ch} | {s['t0']:.2f}–{s['t1']:.2f} | {s['kind']} | {s.get('asset', s.get('gfx'))} | {src} | {s['move']} | {lay} | {txt or '—'} |")
held = json.load(open(ROOT / "build/v1.1/held_prompts.json"))
R += ["", f"End card: {f['end_card']['t0']:.2f}–{f['end_card']['t1']:.2f} s, 'ORIGINEX HUMAN ARCHIVES' wordmark only. Total {f['total']:.2f} s.", "",
      "## Audio",
      "- Unchanged from v1.0: audio/MASTER_mix.wav (voice 'joe afrian british 1', ElevenLabs Music v2.5 cues, −14 LUFS master).", "",
      "## Held OpenArt prompts (NOT generated; for Ernest's decision)",
      "Wan 2.7 Image Pro, 15 credits each (30 for both), one generation per line, no rerolls. v1.1 ships the zero-cost fixes instead.", ""]
for k in ("L38", "L45"):
    R += [f"- **{k}** (15 credits): {held[k]}", ""]
R += ["## Spend (v1.1)",
      "- ElevenLabs 0 · OpenArt 0 · Canva 0 · Higgsfield/Kling 0. Running totals unchanged: ElevenLabs 10,085 · OpenArt 750 (balance 2,037).", ""]
(ROOT / "deliverables/ledger_v1.1.md").write_text("\n".join(R))
print("ledger_v1.1 written")
