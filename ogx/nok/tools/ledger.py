"""Write deliverables/ledger.md from shots.json + the OpenArt job record."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
f = json.load(open(ROOT / "build/shots.json")); jobs = json.load(open(ROOT / "build/openart_jobs.json"))
R = ["# OGX Nok v1.0 — asset and spend ledger (30 Oct 2026, UK)", "",
     "## Shots (one picture per narration line; timing cut from the real VO, audio/vo/vo_timing.csv)", "",
     "| Line | t0–t1 (s) | Kind | Asset | Source / licence | Camera | Overlay | On-screen text |", "|---|---|---|---|---|---|---|---|"]
for s in f["shots"]:
    if s["kind"] == "ai": src = f"OpenArt Wan 2.7 Image Pro (history {jobs.get(s['line'], '?')}), AI still, unlabelled on screen"
    elif s["kind"] == "real": src = f"{s['real']}, see credits.md"
    else: src = "Generated map (Natural Earth outlines, public domain), text-free" if s["gfx"] == "map" else "Generated chronology, text-free"
    txt = (s["credit"] or "") + ((" + name: " + s["name"]["text"]) if s.get("name") else "")
    R.append(f"| {s['line']} | {s['t0']:.2f}–{s['t1']:.2f} | {s['kind']} | {s.get('asset', s.get('gfx'))} | {src} | {s['move']} | {s['overlay']} | {txt or '—'} |")
R += ["", f"End card: {f['end_card']['t0']:.2f}–{f['end_card']['t1']:.2f} s, 'ORIGINEX HUMAN ARCHIVES' wordmark only. Total {f['total']:.2f} s.", "",
      "## Audio",
      "- Narration: ElevenLabs voice 'joe afrian british 1' (FLcNu8oQgaYpRrmtMngB), eleven_v4. One full pass (flow owD5yPSlErC0ihfaaxqZ) + single-line fix L24 ('…dates' heard as '…states').",
      "- Music: three instrumental cues, ElevenLabs Music v2.5 (flow 1JBK29uGgnij0paU1AKJ): C1 discovery 0:00–1:30, C2 investigation 1:30–3:11, C3 resolve 3:11–4:46. Generated on the account's ElevenLabs plan; use is governed by ElevenLabs' terms for that plan (confirm the plan allows commercial use before publishing).",
      "- Mix (film book audio.md): voice HPF 75 Hz, EQ, 2.5:1 comp, −16 LUFS; music −19 LUFS −5 dB, ducked −11 dB under speech; master two-pass loudnorm −14 LUFS / −1.5 dBTP. Stems kept locally in audio/stems/ (voice.wav, music.wav).",
      "- Fonts: Lora, Cinzel (SIL Open Font Licence, assets/fonts/OFL_*.txt).", "",
      "## Rejected / not used",
      "- L45 first take (OpenArt rghaQ8SezmNfLkU3yNkN): fragments looked like modern bricks; regenerated.",
      "- NOK05 Kimbell head: upload.wikimedia.org answered HTTP 429 to every request for the whole build; L60 uses an AI still instead.",
      "- Round-1 render (QA FAIL: 27 shots under the parallax floors/ratio, chronology near-frozen): kept as build/qa/r1_QAFAIL_*.mp4, not delivered.", "",
      "## Spend (this run)",
      "- ElevenLabs: pronunciation tests 882 · full VO 4,589 · L24 fix 84 · music 4,530 = **10,085**",
      "- OpenArt: 50 Wan 2.7 Image Pro stills × 15 = **750** (49 used in the cut, incl. L03 test still and L60, + 1 rejected L45 take; balance 2,787 → 2,037)",
      "- Canva: 0 · Higgsfield/Kling: 0 (no motion clips; parallax rendered locally)", ""]
(ROOT / "deliverables/ledger.md").write_text("\n".join(R))
print("ledger written")
