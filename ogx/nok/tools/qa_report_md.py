"""build/qa/qa_report.json -> deliverables/QA_REPORT.md (human-readable, phone-friendly)."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
r = json.load(open(ROOT / "build/qa/qa_report.json"))
fl = r["flow"]; ok = lambda b: "PASS" if b else "FAIL"
L = ["# OGX Nok v1.0 REVIEW — QA report (from rendered frames)", "",
     f"File: `{pathlib.Path(r['final']).name}` · overlays-off proxy for motion checks: `{pathlib.Path(r['proxy_overlays_off']).name}`", "",
     "| Check | Result | Verdict |", "|---|---|---|",
     f"| Runtime (4:30–5:30) | {r['runtime_s']:.2f} s ({int(r['runtime_s'] // 60)}:{r['runtime_s'] % 60:04.1f}) | {ok(r['runtime_ok'])} |",
     f"| Loudness (≈ −14 LUFS, TP ≤ −1 dBTP) | {r['loudness_I']} LUFS, {r['true_peak_dbtp']} dBTP | {ok(r['loudness_ok'])} |",
     f"| OCR text inventory ({r['ocr']['grabs']} grabs: every 30 s, every credit, every name, end card) | {r['ocr']['disallowed_strings']} disallowed strings | {ok(r['ocr']['disallowed_strings'] == 0)} |",
     f"| Real-image credits read back vs credits.md | min similarity {min(c['similarity'] for c in r['credits_read_back']):.3f} over {len(r['credits_read_back'])} shots | {ok(min(c['similarity'] for c in r['credits_read_back']) >= 0.95)} |",
     f"| Parallax FG travel (floor 3 %) | min {fl['fg_min']} %, median {fl['fg_median']} % | {ok(fl['fg_min'] >= 3)} |",
     f"| FG/BG ratio (floor 2) | min {fl['ratio_min']}, median {fl['ratio_median']} | {ok(not fl['fails'])} |",
     f"| freezedetect −50 dB (overlays off) | {len(r['freezedetect_-50dB'])} frozen spans | {ok(not r['freezedetect_-50dB'])} |", "",
     "Allowed on-screen strings: " + "; ".join(f"`{a}`" for a in r["ocr"]["allowed"]), "",
     "## Motion per shot (overlays off; % of frame width over the shot)", "",
     "| Line | Kind | Dur (s) | FG % | BG % | FG/BG | Pass |", "|---|---|---|---|---|---|---|"]
for x in fl["shots"]:
    L.append(f"| {x['line']} | {x['kind']} | {x['dur']} | {x['fg_travel_pct']} | {x['bg_travel_pct']} | {x['ratio'] if x['ratio'] is not None else '∞ (flat BG)'} | {ok(x['pass_floor'] and x['pass_ratio'])} |")
L += ["", "## OCR inventory", "", "| t (s) | Why | Text found |", "|---|---|---|"]
for e in r["ocr"]["inventory"]:
    L.append(f"| {e['t']} | {e['why']} | {'; '.join(f['text'] + ('' if f['allowed'] else ' **NOT ALLOWED**') for f in e['found']) or '— (no text)'} |")
L += ["", "## Credits read back", "", "| Line | Image | Expected (credits.md) | Similarity |", "|---|---|---|---|"]
for c in r["credits_read_back"]:
    L.append(f"| {c['line']} | {c['image']} | `{c['expected']}` | {c['similarity']} |")
(ROOT / "deliverables/QA_REPORT.md").write_text("\n".join(L) + "\n")
print("written")
