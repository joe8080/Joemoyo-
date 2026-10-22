# OGX — Isandlwana 1879 · v1.0 QC statement
Checked by Claude, 22 October 2026. Status: **private preview. Technical QC passed. Editorial QC owed to MJ.**

## Files
| File | Spec | md5 |
|---|---|---|
| `OGX_Isandlwana_1879_v1.0.mp4` (master, 410 MB) | H.264 1920×1080, 24 fps, 9,113 frames, 6:19.7; AAC 320k 48 kHz | 1c78351d1366d6f79d7f1b1823037230 |
| `OGX_Isandlwana_1879_v1.0_720p_review.mp4` (82 MB) | 1280×720, CRF 25, AAC 160k | 69ccdaa528359a7ff6328f61fe643265 |
| `OGX_Isandlwana_1879_v1.0_Short_9x16.mp4` (41 MB) | 1080×1920, 61.96 s, burned captions | 973fde39a8e3fc59700c0705e52e9587 |
| `OGX_Isandlwana_1879_v1.0_EN-GB.srt` | 94 cues, built from the timeline word timings | — |
| Thumbnails A and B | 1280×720 JPG | in `thumbnails/` |

The master and Short are kept outside git because of their size.

## Technical checks (all pass)
| Check | Result |
|---|---|
| Frame count | 9,113 = timeline (379.7 s × 24) |
| Black frames > 0.5 s | none |
| Master loudness | −14.0 LUFS integrated, LRA 6.0 LU, peak −1.7 dBFS (target −14 / ≤ −1.5) |
| Short loudness | −15.2 LUFS, peak −2.2 dBFS (fades in and out; YouTube normalises Shorts) |
| Contact sheet | 28 frames across the film viewed, plus the 4-frame Short sheet |
| Silence beat | the question card plays over silence, as designed |

## Picture checks
- **Every AI shot is labelled:**
  - "AI RECONSTRUCTION, ANIMATED · ILLUSTRATIVE, NOT A RECORD";
  - the eclipse (Z25), a still, reads "AI RECONSTRUCTION · ILLUSTRATIVE, NOT A RECORD".
- **Every map is labelled:**
  - "SATELLITE IMAGE, 2025 · MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE";
  - the doctrine diagrams read "SCHEMATIC · THE DOCTRINE, NOT A RECORD OF THE BATTLE".
- **Every archive picture gets its credit strip on first appearance.**
- **No AI faces of named people:**
  - Ntshingwayo and Mavumengwana appear as back views;
  - Mkhosana is an anonymous figure;
  - Cetshwayo and Frere appear only in period photographs and paintings.
- **No AI flags, insignia, documents or invented lettering**, checked on the start, middle and end frames of all 33 clips.
- **No *Zulu* (1964) or *Zulu Dawn* (1979) stills or compositions.**

## Fixed during QC (before delivery)
1. **Map labels:** the "British camp" and "ISANDLWANA" tags were crossed by route lines on the battle maps. They're now drawn last, on dark plates. Applied before those segments rendered, and verified.
2. **Credit timing:** the Holden 1879 sketch credit stayed on screen for about 1.6 s after the cut to the AI shot Z30 (4:41.7). A credit now ends before any second picture. Segment 23 was re-rendered and the master rebuilt.

## Known limitations (not fixed; for MJ and Joe)
- **Evidence is search-summary level**, with no page-level cites. The ⚠ rows in the claim ledger need Laband, Knight or the Stuart Archive pages before release.
- **Pronunciation of the Zulu names** hasn't been checked by a native speaker.
- **Length is 6:20**, below the 9–12 min target, on purpose (see the pre-production pack §1).
- **The I07 photographer's name** needs checking against Commons.
- **The Supabase `events`/`people` rows** still carry the wrong "column of 1,300 men" wording. Not edited; it's Joe's decision.
