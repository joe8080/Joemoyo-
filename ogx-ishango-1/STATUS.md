# ogx-ishango-1 — STATUS

**State: STOPPED AT KICKOFF (gate 3 failed).** No script, no stills, no voice, no render. Nothing published, uploaded, scheduled or posted. No other film, file or version was touched.
Run: Claude Code night build, Sat 31 Oct 2026, ~00:25–00:35 UK. This is the only run logged here.

## Gate log
| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | Still source works (OpenArt or Canva) | **Route available** (no still generated) | OpenArt account active with credits available. cdn.openart.ai reachable through the proxy. Canva connector is present, but its export host (export-download.canva.com) is blocked, so OpenArt is the route. |
| 2 | Voice route + pronunciation test | **Route available; test NOT run** | ElevenLabs voice "joe afrian british 1" found (generated voice, en, middle-aged). Test held back on purpose: gate 3 stops the run, so I spent no credits on a cut that can't be scripted tonight. |
| 3 | OGX Research evidence pack in hand before the script | **FAIL — STOP** | No Ishango pack in Eden. Only the 25 Oct ideas note exists. The handoff-queue row "OGX film idea: The Ishango bone" was still "Awaiting assignment" with next action "Ernest/MJ to pick; then Research builds evidence pack". |
| 4 | Allowlist | **Partly OK** | Reachable: cdn.openart.ai, upload.wikimedia.org, storage.googleapis.com. Blocked: commons.wikimedia.org, export-download.canva.com, api.elevenlabs.io (the MCP route works), arxiv.org, www.naturalsciences.be. Research has to fetch the sources and the real images. |
| 5 | Pre-flight every beat | Not reached | — |

## Other kickoff gaps
- **Film book:** neither branch of joe8080/Joemoyo- has RUNBOOK-v2. The `ogx-motion-documentary` skill isn't installed in this session, and the Nok engine code (render.py / film.py, Nok motion settings) isn't reachable. **Chief:** supply the engine, or confirm that Claude should rebuild it from Lessons L1–L37.
- **Production box:** this session has no /workspace/ogx-productions and no connected computer folder. **Chief:** agree the private route for Research's image copies coming in and for the exports going out.

## Action taken
- Eden handoff-queue row "OGX film idea: The Ishango bone" updated: Episode ID ogx-ishango-1, owner OGX Research (Grok), Status Blocked, and the next action lists exactly what the pack must contain.

## Eden script id
None. No script was written (no pack, no script).

## QA results
None. No cut exists.

## Restart checklist (next run)
1. Research pack in Eden: claim register, verified copies of the 2 Commons images, credits.md, and the date variants including Smithsonian "about 25,000".
2. Engine/runbook and private transfer route confirmed by Chief.
3. Then: pronunciation test, differentiation note, script (YouTube Script Studio + Write Like Joe), Research lock-check, stills, VO, render, QA.

## Follow-up 01: Chief rulings received 31 Oct 2026 (stamped 00:25 UK); apply from the next run
1. **AI labels ON:** every AI still carries a small on-screen "Reconstruction (AI)" label for its whole time on screen, plus a note in the description and ledger. Engine flag `ai_label` defaults ON for this film. ⚠️ This reverses Ernest's 29 Oct standing rule (L23: unlabelled "until Ernest rules otherwise"). Logged as a Chief ruling. **Chief: please confirm it is Ernest's own words** so QA judges against the right rule.
2. Lean AI stills from OpenArt/Canva only. Higgsfield/Kling for motion only: max 6 clips, hard cap 62 credits.
3. **Export route:** exports stay inside this session. Record sha256 + md5 for each and report file names and hashes; Ernest moves them to his private Drive himself. No media of any kind (mp4, images, audio, encoded) goes in the repo. Text and code only.
4. The two CC BY-SA Commons images are allowed in the REVIEW cut only, both flagged "needs Ernest's exception before publish". PD/CC0/CC BY substitutes preferred. Claude can't reach commons.wikimedia.org from here, so Research needs to look for them.
5. Connectors: ignored unless one blocks the build. None blocks the current stop; the blocker is the missing evidence pack, not a connector.

**Effect on tonight: none.** Gate 3 still fails, so there is still no script and no build.
