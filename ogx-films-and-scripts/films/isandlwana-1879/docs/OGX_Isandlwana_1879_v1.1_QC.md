# OGX — Isandlwana 1879 · v1.1 private preview: QC report
Prepared by Claude, 22 October 2026. This answers MJ's second review in Eden ("zero-credit private v1.1 preview").

**Status:**
- **Private preview only.** It's not final script lock, not QC-passed, and not approved for release.
- Nothing has been published, scheduled or uploaded publicly.
- No paid generation was run, and **no credits were spent** on this version. No ElevenLabs or Higgsfield calls were made; the free tools used were ffmpeg, PIL and pocketsphinx.
- The two Supabase corrections are **still on hold**, and no database write was made.

## 1. Version record
| Item | Value |
|---|---|
| Version | v1.1, "One day, one hill" re-edit, built from existing assets only |
| Master | `OGX_Isandlwana_1879_v1.1.mp4`, 1920×1080, 24 fps, H.264 + AAC 48 kHz 320k, 342.96 s (5:42.96), 385,020,293 bytes, md5 `2f8810cc0523ecd696b387d6998e8d77` |
| Review copy | `OGX_Isandlwana_1879_v1.1_720p_review.mp4`, 1280×720, 75,735,203 bytes, md5 `5854232c61dfc39e117779319b4c61a6` |
| Captions | `OGX_Isandlwana_1879_v1.1_EN-GB.srt`, 81 cues, md5 `746b936849a69792900a743267e493e3` (copy in this folder) |
| Mix | `mix_master.wav`, md5 `9821c4b31af536b7511f337e1856b5c9` |
| Voice | the v1.0 ElevenLabs takes in Joe's channel voice. **No new recordings.** Two takes are trimmed inside the recording: `L26_trim.wav` (3.99 s, md5 `c497aa58…`) and `L44_trim.wav` (2.68 s, md5 `16dbaac1…`) |
| Script | `OGX_Isandlwana_1879_v1.1_script.md` (53 voiced lines, export timecodes) |
| Ledgers | `OGX_Isandlwana_1879_v1.1_ledgers.md` (claims, assets and rights, pronunciation) |
| Build | `pipeline/v11/` (timeline_v11.py → timeline.json; render, mix, captions, finalize; QC alignment scripts) |
| v1.0 | **Unchanged.** `OGX_Isandlwana_1879_v1.0.mp4` md5 `1c78351d…` and `_720p_review.mp4` md5 `69ccdaa5…` were re-checked after the v1.1 build |
| Credits | **0** |

## 2. Technical QC (on the actual export)
| Check | Result |
|---|---|
| Render segments | 32 of 32 complete |
| Streams | h264 1920×1080 24/1 · aac 48 kHz |
| Frames | 8,230 decoded, with **no decode errors**. The timeline is 343.0 s (8,232 frames); the 2-frame shortfall falls in the silent end card |
| Black frames (>0.5 s) | none |
| Loudness | **−14.0 LUFS integrated**, LRA 7.1 LU, true peak −1.8 dBFS |
| Contact sheet | `OGX_Isandlwana_1879_v1.1_contact_sheet.jpg` (one frame every 6 s) and `OGX_Isandlwana_1879_v1.1_check_frames.jpg` |
| SRT | 81 cues; the last cue ends 5:36.3. It contains neither removed clause ("nobody in the camp…", "already been decided") nor a voiced subscribe line |

**Pictures checked frame by frame:**
- **0:01:** marker "22 JANUARY 1879 · AS MOST ACCOUNTS TELL IT", top right, clear of the AI tag.
- **0:26:** "1,329 KILLED · 858 EUROPEAN · 471 AFRICAN · OFFICIAL RETURN" over I06, with the credit "oleograph after Alphonse de Neuville, 1881".
- **2:05:** I08 with "ISANDLWANA TODAY" and the credit "…2010 | Photo: Michael Gundelfinger, CC BY-SA 4.0".
- **2:42:** the subscribe badge appears, visual only.
- **2:50:** "LATE MORNING TO MIDDAY · TIMES APPROXIMATE".
- **3:54:** "PARTIAL ECLIPSE · THAT AFTERNOON" on the still eclipse image, which is AI-tagged.
- **5:22:** **memorial line now plays over I08**, the 2010 landscape with no sculpture, labelled "THE BATTLEFIELD TODAY" with the "TODAY" marker. **I07 (sculpture photo) appears nowhere in v1.1.**
- **5:41:** the end card, silent, with the visual subscribe badge.
- **AI tag:** on every AI shot sampled.

## 3. Audio joins (MJ's items at 0:10, 1:48, 3:47)
**What I could and couldn't do:**
- No hosted transcription was used: ElevenLabs Scribe needs a file upload that isn't available in this session, and it isn't zero-credit.
- I installed **pocketsphinx**, a free offline recogniser with its bundled US-English model. It ran on the **export's own audio**, decoded from the MP4, in two ways:
  - **forced alignment:** are all the expected words present, in order, inside each line's slot?
  - **free decode:** what does a recogniser hear with no script?
- Its free decoding is weak on accents, music and Zulu names, so a low score alone means little.
- **This is machine evidence, not a listening QC.** MJ's rule stands: **a human must listen.** The three excerpts below make that a 50-second job.

**All 53 lines:**
- Every line aligned inside its slot.
- No words spill outside a slot by more than 0.4 s.
- No line overlaps the next. The tightest real gap is 0.45 s, by design, in the battle run (L39 → L40).

| Time in v1.1 | Join | Machine evidence | Verdict / for the listener |
|---|---|---|---|
| **0:11.0–0:15.0** (MJ "0:10") | L26 trimmed, "…Tens of thousands of men." | In the source take, "men" ends at 3.82 s and the cut is at 3.99 s, inside the pause before the removed "And…". Pitch appears to fall on "men" (crude estimate), as at a sentence end. On the export, the free decode hears "**tens of thousands of men**". The next line starts 0.8 s after the trimmed take ends | **Clean by measurement.** Listen for any clipped "m-" or a hint of "And" |
| **1:41.4–1:55.4** (MJ "1:48") | L14 (British columns cross at Rorke's Drift) → **L21** "In the middle of January, **the army** set out from **the king's homestead**…" | A 1.9 s gap, with the MID-JANUARY marker and a picture change to Zulu columns (Z06). The free decode hears "**the army sets out from the king's home state**", so "king's" is clearly heard | **The referent depends on "the king's homestead".** The king is named at 1:30. Listen: does "the army" read as the Zulu army on first hearing? If not, the fix needs either a new line (Tier 2) or the on-screen marker "MID-JANUARY · THE ZULU ARMY" (free, a one-segment re-render) |
| **3:52.7–3:58.8** (MJ "3:47") | L44 trimmed, "That afternoon a partial eclipse dimmed the sun." → 1.8 s hold → L55 "So, how did the Zulu army win…" | "Sun" ends 2.58 s into the take; the cut is at 2.68 s, in the 0.18 s pause before the removed "but". No onset of "but" is present. **Pitch on "sun" rises (about 103 → 133 Hz)**, unlike sentence-final words (flat or falling): the take was read with a comma | **Risk flagged.** "Sun" may sound unfinished. The near-silence that follows may carry it as a suspended beat, or it may sound cut off. **This needs an ear.** If it fails: re-voice L44 as a full stop (Tier 2), or I can try a free pitch-shaping pass on the last syllable |

**Listening excerpts** (cut from the export's own audio):
- `v1.1_listen_0m05-0m17_L26.mp3`
- `v1.1_listen_1m39-1m57_L14-L21.mp3`
- `v1.1_listen_3m44-4m05_L43-L44-L55.mp3`

## 4. MJ's second-review conditions
| # | Condition | Status |
|---|---|---|
| 1 | Verify book pages, or replace over-precise assertions and update the ledger | **Pages not verified:** the books aren't reachable here. **Over-precise wording replaced:** the L26 and L44 clauses are cut; discovery is attributed and its time approximated; the eclipse sequence is dropped; casualty numbers are given as the official return. The ⚠ rows in the ledger still want page cites |
| 2 | Pronunciation checked with a competent speaker or reference | **No speaker reached.** References: Isandlwana [ísanˈdɮwáːna] and Cetshwayo [ᵏǀétʃwajo]. **Every Zulu name is flagged as an English approximation** in the ledger, §3 |
| 3 | Memorial sculpture rights; use a cleared alternative; don't imply 1879 | **Done.** I07 is removed; I08 (2010 landscape, CC BY-SA 4.0) is used. Present-day pictures carry "TODAY" labels and their year in the credit |
| 4 | QC the full private export at 0:10, 1:48 and 3:47 | Technical QC and the machine join check are **done on the export**. **The human listening check is still open** (§3) |
| 5 | Record filenames, voice and caption files, ledgers, zero credit, version | **Done** (§1) |

## 5. Open before any release decision
1. **Human listening** of the three excerpts, especially L44 "sun", and of the full 720p review.
2. **Page-level cites** for the ⚠ claim rows (Laband, Knight, the Stuart Archive).
3. **Native-speaker pronunciation check.** Any fix needs a re-voice (Tier 2, priced first, on hold).
4. **Script lock** by MJ, then **release approval** by Joe.
5. **Supabase:** two corrections, approved in principle, not run, awaiting Joe's explicit authorisation.
6. At release: CC BY-SA credits and licence links for I08 and I09 in the description.
