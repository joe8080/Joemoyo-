# Golden Stool 1900 — box build kit

Code and checklists only. **No media, scripts, scans or private links go in this
repository; it is public.** Run everything on the box that holds
`/workspace/ogx-productions/golden-stool-1900/`.

## Status at 30 Oct 2026, about 10:30 UK

| Status | State |
|---|---|
| Inputs verified | **No.** This session could not reach the box. Nothing in `manifest_inputs.json` has been read; its hashes are copied from the project hub. |
| VO recorded | No |
| Rendered | No |
| QC passed | No |
| Joe approved | No |
| Published | No (do not publish, schedule or run thumbnail tests) |

## Run order

1. **Verify inputs.** `python3 verify_inputs.py manifest_inputs.json`
   It must print `PASS`. If the narration hash is not
   `ea0177a0cbf874c2b5debdf844f7a7bfdd6ac24d6836889f4141ac1add53f421`, stop: do not record.
   Never build from `CLAUDE_PACK_v1.md` or any script earlier than v1.5.
2. **Historical gate (AMD-01).** Before recording the annexation line, Research (owner B)
   reads the Ashanti Order in Council in Cd. 938, printed pp.56–57, and records two dates:
   when it was made and when it commenced. If the locked line gives only "1901" as the
   date of annexation, Research issues a versioned amendment (v1.5a), the Supervisor
   (owner C) re-checks it, and only the amended line is recorded. The locked v1.5 file is
   never edited in place.
3. **VO.** Voice `joe afrian british 1` only. Record one take per script line with
   character timestamps. Write `segments.json` (see `build_srt.py`) with each line's
   start time in the edit. Check every Twi name against `research/NAME_GUIDE_v1.1.md`.
   Log any word you cannot confirm in the QC report as UNRESOLVED and carry on with the edit.
4. **Edit (Zero-AI).** Follow `visuals_drafts/scene_plan.csv` (46 scenes including the end
   card). AI-01 has no APPROVE on record, so S14 and S18 use the plan's documented Zero-AI
   fallback (Card 1 and a D02 hold). Then remove the AI disclosure paragraph and the AI
   credit line from the description and the end card. Final timing follows the recorded VO
   and reading holds; 5:54 is provisional.
   Hard rules:
   - no AI image of the Golden Stool;
   - no likeness of Yaa Asantewaa or Prempeh I;
   - date-label the 1935 and 1953 stool photographs;
   - use the R02 inset at 153×210 px, never upscaled;
   - caption the gold lion as illustrative goldwork;
   - caption Kakum as illustrative;
   - Lady Hodgson appears as typeset quotes only, no page scan;
   - keep the GeoNames and OGL lines;
   - no modern borders or invented routes on the maps.
5. **Export.**
   - Master: the scene plan's frame size, H.264 high, yuv420p, AAC 48 kHz.
   - 720p review copy: `ffmpeg -i master.mp4 -vf scale=-2:720 -c:v libx264 -crf 20 -preset slow -c:a aac -b:a 192k review_720p.mp4`
6. **Captions and transcript.**
   `python3 build_srt.py segments.json --narration script/SCRIPT_v1.5_clean_narration.md --srt golden-stool-1900.en.srt --transcript transcript.md`
   It refuses to run if the recorded text differs from the locked narration.
7. **QC.**
   - `./qc_render.sh master.mp4 review_720p.mp4 golden-stool-1900.en.srt > qc_auto.md` checks integrity, loudness, clipping, black and frozen frames, and silence.
   - Then watch and listen to the whole film. Log each issue against its timecode: pronunciation, caption accuracy, visual claims, map labels, credits, phone readability and audio balance.
   - Sampled frames are not full-playback approval.
8. **Chapters.** Re-time the seven chapters in the release pack to the actual cut.
9. **Delivery.** Use a private route only. `joe8080/ogx-productions` must exist and be
   private first, or use another verified private store. Record the master's sha256 and
   md5, the 720p copy and the SRT in the hub. "Rendered", "QC passed", "Joe approved" and
   "Published" stay separate statuses.
