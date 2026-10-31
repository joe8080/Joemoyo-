# QA summary — ogx-ishango-1 v1.0 REVIEW (31 Oct 2026, ~05:10 UK)
All checks were run on the RENDERED exports (L4), not on config. Detail: `QA_REPORT_OGX_Ishango_v1.0_REVIEW.md`, `QA_REPORT_OGX_Ishango_v1.0_REVIEW_noBYSA.md`, `parallax_stats_v1.0_final.csv`.

## Exports (kept in the session only; never committed)
| File | Resolution | Runtime | Size | Loudness (I / TP) | sha256 | md5 |
|---|---|---|---|---|---|---|
| OGX_Ishango_v1.0_REVIEW.mp4 | 1920×1080 | 285.24 s (4:45.2) | 494,435,762 bytes (494.4 MB) | −14.0 LUFS / −1.4 dBTP | `c175ba943f38203248c49379752eac120354d772145170d3eb4fed5491574d59` | `3705791449c04580f01ffc4214028d50` |
| OGX_Ishango_v1.0_REVIEW_720p.mp4 | 1280×720 | 285.24 s (4:45.2) | 76,202,467 bytes (76.2 MB) | −14.0 LUFS / −1.4 dBTP | `bd376042e6355faeb7bdc2b2c079169752d62ad21351c4bd621a2a5fe0d155e3` | `d311b2dac4a3ad76bc9d1783ed4f5652` |
| OGX_Ishango_v1.0_REVIEW_noBYSA.mp4 | 1920×1080 | 285.24 s (4:45.2) | 489,345,079 bytes (489.3 MB) | −14.0 LUFS / −1.4 dBTP | `8d642ad26b25143eb0af21229c5171115d1ea98dc2e77305f170c401547c902d` | `53c7f3934aa44011724d12652e067261` |
SRT: review/OGX_Ishango_v1.0_REVIEW.srt (46 cues, from the Scribe timings).

## Results
| Check | Result |
|---|---|
| Runtime 4:30–5:30 | **PASS** 4:45.2 (all three files) |
| Loudness ≈ −14 LUFS, TP ≤ −1 dBTP | **PASS** −14.0 LUFS, −1.4 dBTP (1080p, 720p, noBYSA) |
| freezedetect −50 dB, ≥ 2 s | **PASS** 0 frozen segments (both cuts) |
| Parallax floors (FG ≥ 3 %, FG/BG ≥ 2), optical flow on rendered frames | **PASS** 44/44 moving shots in the main cut (FG min 3.12 %, median 4.79 %; ratio min 2.12, median 6.65); the 3 noBYSA swap shots PASS. Exceptions by design: title card, end card (CARD), and the L08 map (flat PD satellite image, MAP-OVERRIDE, 25 % travel push-in, no fake parallax). |
| OCR text inventory (every 30 s + every credit, name subtitle and card) | **PASS (manual)**. Only allowed text: "Reconstruction (AI)" labels, real-image credit lines, name subtitles, the title card ("The Ishango bone / OrigineX Human Archives") and one end card. The 3 words flagged by the classifier are OCR splits of allowed text ("truction" from the AI label; "Bro / oks" from the "Brooks & Smith" subtitle). No chapter cards, lower-third boxes, source cards, map tags, badge or credit pages (all behind flags defaulting OFF). |
| Credit read-back vs credits.md | **PASS**. 14/15 automatic PASS (≥ 0.90 similarity). L08 (NASA) scored 0.841 because OCR misread "Landsat" over the map texture and the crop clipped the final "n"; checked by eye on the final frame: renders exactly "NASA Landsat · Wikimedia Commons · Public domain". "Albertils" = OCR of "Albert1ls". Credit separator is "·" (credits.md paste shows "."; garbled middle dot per the Night Producer's note). |
| AI label on every AI still, whole time on screen | **PASS** (seen on every AI shot in the 47-frame contact sheets; engine flag `ai_label` ON). |
| Visual QA for 2.5D smears / ghosting / modern objects | **PASS after fixes**. First export failed (L09 ghost, L10 smudge, L46 doubled figure, faint doubled reflections L07/L41); fixed with zero credits and re-checked by eye on the re-rendered shots. That pre-QA export is kept aside in work/rejected_exports (sha256 e7d0c146…, 8233e1a2…, 855e1cce…), not handed over. |
| VO read-back vs locked script | **PASS** 756/756 tokens identical (Scribe). Pauses widened in silences only (+25.0 s). |
| Licences | Main cut uses Ishango_bone_(cropped).jpg (**CC BY-SA 4.0: needs Ernest's exception before any publish**; review only) on L03, L12, L42. The **_noBYSA** cut has no BY-SA image (L03 → CC BY diagram; L12, L42 → approved AI stills, labelled). Ishango_Bone.jpg never used. Elephant shots not used. Music is original/procedural (no third-party licence). |

## Not checked here (open)
- **Phone-speaker / ear listen** (L34): not possible in this session; please listen on a phone before sign-off.
- **Pronunciation by ear**: read-back is exact, but an ear check of Heinzelin, Huylebrouck, Pletser and OrigineX is still open.
