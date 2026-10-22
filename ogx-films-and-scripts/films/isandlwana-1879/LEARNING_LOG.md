# Isandlwana 1879: learning log (test of next-film prompt v0.1)
Filled in at each gate. After the film, use it to improve the prompt and the base skill.

| Gate | Date | What happened | Corrections needed | Cost | Missing deliverables |
|---|---|---|---|---|---|
| 0 Existing work | 21 Oct 2026 | Eden searched: no Isandlwana prep exists. Adwa untouched | — | 0 | — |
| 1 Pre-production pack | 21 Oct 2026 | v0.1 delivered for MJ: 30-row claim ledger, ~950-word narration, pronunciation list, scene plan, asset leads | Pending MJ review. Known gap: sources are search-summary level, with no page-level cites | 0 | Page-level sources; verified archive rights; native pronunciation check |
| 2 Proof sequence | 21 Oct 2026 | **Skipped at Joe's instruction** ("you make the whole film now"). Test stills Z03 and Z08 checked instead | The cold-open photo had to change: no PD copy of the May 1879 wagon photo was found, so *The Graphic* 1879 was used | ElevenLabs 550 (2 test stills) | The proof sequence itself |
| 3 Full build | 21–22 Oct 2026 | 9 voice takes split into 61 lines. 35 AI stills; 33 Kling clips; 10 archive images (9 used); 12 maps (Sentinel-2 + terrain); 2 HyperFrames stings; 9 music cues | Sentinel "0% cloud" scene was cloudy (fixed with a pixel check). 293 MB bridge pack timed out (re-packed to 6). Z34 moon cropped. Z25 eclipse kept still. Map labels crossed by routes (drawn last on plates) | ElevenLabs ≈ 22,000; Higgsfield 381 | — |
| 4 Delivery | 22 Oct 2026 | 1080p master, 720p review, SRT (94 cues), Short 9:16, 2 thumbnails, 3 titles, production pack, voiced script, change log. Committed to the repo; Eden note; sent to Joe | — | 0 | MJ fact-check of the cut; page-level cites; pronunciation check; I07 author spelling |
| 5 QC statement | 22 Oct 2026 | See `docs/OGX_Isandlwana_1879_v1.0_QC.md` | — | 0 | — |

## What to change in the next-film prompt (v0.2)
1. **Check the cold-open evidence first.** Before writing the cold open around an archive item, check that a PD or CC copy is actually reachable. Isandlwana's planned photograph wasn't.
2. **If Joe skips a gate, the gate's review moves to the finished cut.** The pack must say so on page one, with the priority lines to check.
3. **Ask for page-level sources at Gate 1.** That's the only route to the 9–12 min target. Without them, the film is ~6 min.
4. **Budget line in the Gate 1 pack:** about 22k ElevenLabs credits and about 400 Higgsfield credits for a ~6 min film. Ask Joe before going above it.
