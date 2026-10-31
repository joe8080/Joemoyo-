# ogx-ishango-1 — STATUS

**State (31 Oct 2026, ~06:35 UK): IDLE. v1.0 REVIEW (+720p, small 720p, noBYSA) and v1.1 natural (+noBYSA) exported and QA'd; Drive transfer blocked (connector takes inline content only). Nothing published. Media in the session only.**
Nothing is published, uploaded, scheduled or posted. No stills, no full VO, no render yet. Older films and versions are untouched.

## Follow-ups 07–08 (05:45–06:35 UK): zero credits; nothing published, uploaded or pushed (media stays in the session)
- **Voice check:** the VO take used ElevenLabs voice **"joe afrian british 1"**, voice id **FLcNu8oQgaYpRrmtMngB** (as reported by the generation).
- **Google Drive transfer: BLOCKED.** The Drive connector can write, but `create_file` only takes file content inline in the tool call (base64/text), with no local-file or resumable upload, so 44–494 MB media can't be sent from this session. No other route tried; nothing uploaded.
- **v1.1 natural cut:** same locked VO take (sha256 8dbbefd5…, unchanged), no re-voicing, no word changes, no new generations. Only the take's own pauses (incl. its 0.8 s section breaks), the 1.2 s opening picture, the end tail and one end card. **Runtime 4:20.2, under 4:30 and NOT padded, by instruction.** Picture rules identical to v1.0. QA on rendered frames: loudness −14.0 LUFS / −1.3 dBTP PASS; 0 frozen segments; 44/44 moving shots PASS (FG min 3.11 %, ratio min 2.32); only allowed text; L08 credit verified by eye (OCR misread over map texture).
- **v1.1 natural _noBYSA:** the same v1.1 cut with L03 → CC BY diagram, L12 → still 16, L42 → still 02 (exactly as v1.0 noBYSA), timed to the v1.1 timeline, v1.1 audio.
- **Small review copy:** made from the v1.0 main cut (two-pass x264, 1.1 Mbit/s video + 128 kbit/s AAC).
- **Untouched:** all v1.0 exports and the v1.1 natural file (sha256 re-checked OK).

| File | Resolution | Runtime | Size | Loudness (I / TP) | sha256 | md5 |
|---|---|---|---|---|---|---|
| OGX_Ishango_v1.0_REVIEW_720p_small.mp4 | 1280×720 | 285.24 s (4:45.2) | 44,068,281 B (44.1 MB) | −14.1 LUFS / −1.3 dBTP | `1dab5ad7841189856d9add3b5c18acfba73c075c8cd62bdf707d0315de717795` | `2ddd89c40ba4da8c3e0df55f44affa58` |
| OGX_Ishango_v1.1_REVIEW_natural.mp4 | 1920×1080 | 260.24 s (4:20.2) | 452,536,858 B (452.5 MB) | −14.0 LUFS / −1.3 dBTP | `bcf5ee71bf6286895dadd6980040fa6ef91bdbf00334ccdc181a1cf64e535914` | `e58e47a9b01e6568bc6265f36ba49bda` |
| OGX_Ishango_v1.1_REVIEW_natural_noBYSA.mp4 | 1920×1080 | 260.24 s (4:20.2) | 447,822,629 B (447.8 MB) | −14.0 LUFS / −1.3 dBTP | `177a83a70384e6a5068ae3dec1265bf7df394429b9df64b82fb7216d4fb73c63` | `4addafcc95c60cfbd071248b63d84973` |

- **Not changed tonight (logged for Research):** the L08 map credit and the bone photo author name.
- **State: IDLE** after this summary, per the Night Producer.

## DONE (review cut): v1.0 REVIEW exports + QA — 31 Oct 2026, ~05:10 UK. Nothing published, uploaded, scheduled or posted.
Exports are kept **in this session only** (`ogx-ishango-1/review/`, gitignored; never pushed). Ernest moves them to his private Drive himself.
| File | Resolution | Runtime | Size | Loudness (I / TP) | sha256 | md5 |
|---|---|---|---|---|---|---|
| OGX_Ishango_v1.0_REVIEW.mp4 | 1920×1080 | 285.24 s (4:45.2) | 494,435,762 bytes (494.4 MB) | −14.0 LUFS / −1.4 dBTP | `c175ba943f38203248c49379752eac120354d772145170d3eb4fed5491574d59` | `3705791449c04580f01ffc4214028d50` |
| OGX_Ishango_v1.0_REVIEW_720p.mp4 | 1280×720 | 285.24 s (4:45.2) | 76,202,467 bytes (76.2 MB) | −14.0 LUFS / −1.4 dBTP | `bd376042e6355faeb7bdc2b2c079169752d62ad21351c4bd621a2a5fe0d155e3` | `d311b2dac4a3ad76bc9d1783ed4f5652` |
| OGX_Ishango_v1.0_REVIEW_noBYSA.mp4 | 1920×1080 | 285.24 s (4:45.2) | 489,345,079 bytes (489.3 MB) | −14.0 LUFS / −1.4 dBTP | `8d642ad26b25143eb0af21229c5171115d1ea98dc2e77305f170c401547c902d` | `53c7f3934aa44011724d12652e067261` |

- **Main cut** uses Ishango_bone_(cropped).jpg (CC BY-SA 4.0) on L03, L12 and L42: **review only, PENDING Ernest's BY-SA exception** (Chief allowed it for review; Research would keep it out).
- **_noBYSA alternate** (same audio and timing): L03 → CC BY three-column diagram; L12 and L42 → approved AI stills (labelled). No BY-SA image. Zero credits.
- **QA:** see `qc/QA_SUMMARY.md`. Runtime, loudness, freezedetect, parallax floors, OCR text inventory, credit read-back, AI labels and VO read-back all PASS (one OCR credit miss on L08 verified by eye). The first export failed visual QA (ghosting, smudges, doubling), was fixed at zero credits, and is kept aside, not handed over.
- **Credits used (whole session):** ElevenLabs **4,917** (500 pronunciation test + 4,417 VO; Scribe 0) · OpenArt **700** (Wan 2.7 Image: 2 route tests + 45 stills incl. redos; the last redo was rejected and L15 reuses still 39) · Eden AI **~3.2** · Higgsfield/Kling **0** · Canva **0**. Music: original procedural bed, 0 credits.

### Open items for Ernest
1. **BY-SA exception** for Ishango_bone_(cropped).jpg (and confirm the author name Joeykentin vs "JhowieNitnek") — or choose the _noBYSA cut.
2. **AI label**: "Reconstruction (AI)" on every AI still (Chief's 31 Oct ruling, from your 30 Oct standard). Confirm or overrule; it's one engine flag.
3. **Ear checks**: a phone-speaker listen (L34) and a pronunciation ear-check (Heinzelin, Huylebrouck, Pletser, OrigineX). The read-back is exact, but nobody has listened in this session.
4. **Music**: the review cut uses an original placeholder bed (no approved cue was reachable). Choose a final cue; if it's ElevenLabs Music, confirm commercial terms before publishing (L35).
5. **Map marker** on L08: Ishango placed on the north-west shore near the Semliki outflow, position approximate. Research to confirm.
6. **Engine**: rebuilt tonight because the Nok engine and RUNBOOK-v2 weren't reachable from this session. Chief to decide whether this rebuild (in `engine/`) replaces or merges with the Nok engine.
7. **Review-copy size**: the house-standard draft asks for a review copy under 50 MB; the 720p copy is 76.2 MB. I can make a smaller one at no cost if wanted.
8. Before any publish: Ernest's explicit yes; description.md ready (no placeholder citations).

## v1.0 REVIEW build (follow-up 06, 03:19 UK): LOCK → VO → render → QA → re-export
- **Script v0.3 LOCKED** at 03:20 UK after OGX Research's PASS on the text (relayed by the Night Producer). Lock file sha256 11b9e6fbdce7c56d332d99028851f2d3e5dacc23b9095fb2c179f8a9c1986b40 (matches). Eden b69bd0e5 updated to "LOCKED".
- **VO:** ONE take, ElevenLabs "joe afrian british 1", eleven_multilingual_v2, 4,417 credits, 252.45 s. Scribe read-back: **756/756 tokens identical to the locked text**. The VO ran faster than the test pace, so to reach the 4:30 floor I **widened pauses only**: the stem is split at the midpoint of each silence between lines (+0.4 s per line, +1.0 s more at 7 section starts) = +25.0 s. No words cut or changed, no re-voicing.
- **Picture:** 47 shots timed from the Scribe word timings (name subtitles and schematic group highlights land on the spoken words).
- **First export failed my own visual QA** (rendered-frame contact sheet + crops): L09 figure ghosted (soft matte let the inpainted BG show through); L10 smudged halos round both men; L46 doubled walking figure (object inside the soft ground-split band); faint doubled reflections on L07/L41. Not handed over. Kept as `work/rejected_exports/*_REVIEW_prefixQA*` with hashes logged here.
- **Fixes (zero credits):** ground-split blend narrowed 18 % → 8 % (re-rendered all 15 ground-split shots); L46 split moved below the figure; L09/L10 tried a hard matte (ghost gone, smudge remained), then switched to a ground split below the figures' feet, so people stay on the BG plane with nothing revealed behind them. Re-measured from rendered frames: all re-rendered shots PASS (L09 4.57 %/6.7; L10 3.12 %/3.1; L46 5.07 %/7.6). Checked by eye at start and end of each shot: no ghosting, smudge or doubling.
- **Re-exported** (04:45–05:00 UK) and fully QA'd; see the DONE section above and qc/QA_SUMMARY.md.

## Script v0.3 DRAFT: Research FIX applied (follow-up 05, 03:11 UK). HOLD for Research's re-check; NOT LOCKED
- **Changed from v0.2 (Research's wording, verbatim):** L15, L29, L34, L36, L40, L45. **L33** now uses Research's verified Smithsonian quote ("This fossil mammal bone has three rows of tally marks along its length. They may have been used to add or multiply."). All other lines unchanged (Research PASS).
- **Correction:** my earlier STATUS line called v0.2's L33 "D05 exact". It was a paraphrase ("calls them tally marks, and says they may have been used to add or multiply"), not an exact quote. The Eden v0.2 note does hold that v0.2 text, but its title was never renamed from "v0.1". v0.2 is left as it was.
- **Files:** `work/narration_v0.3.txt` (numbered narration; stays in the session) · `script_v0.3.md` (lines + claim refs + picture plan) · `script.md` / `script_v0.2.md` = v0.2, untouched.
- **Eden v0.3 item id: b69bd0e5-9162-4084-bf7d-dbe7846cede3** (title "YouTube Script: The Ishango bone (ogx-ishango-1) v0.3 DRAFT", read back and matching). v0.2 stays in 342592c3-60ae-40f0-ba2a-bb9daf5ee103.
- **sha256 of narration_v0.3.txt:** 11b9e6fbdce7c56d332d99028851f2d3e5dacc23b9095fb2c179f8a9c1986b40
- **756 words, 46 lines;** estimated VO ≈ 293 s at the measured 155 wpm, so ≈ 5:00–5:05 with the title card, end card and line gaps (target 4:30–5:30).
- **Picture change for the FIX:** L15's still (hands cutting a notch) would have shown the attribution Research removed. The one permitted redo (15 credits, logged) was **rejected on review**: fresh whole fish, cartoon-like bones and a metal-looking hook. So L15 now **reuses approved still 39** (stratified trench wall, reversed move; no further spend). No other still changes.
- **Images (Research):** approved: IshangoColumnA/B/C, NASA Lake Edward, the 2 Virunga elephant shots (scenery only; not used in the cut). Ishango_bone_(cropped).jpg is PENDING Ernest's BY-SA exception (review cut only; lines 03, 12, 42). Ishango_Bone.jpg is never used. Every real image carries its credits.md line.

## HOLD — follow-up 04 (03:06 UK)
OGX Research is lock-checking script v0.2 against the Eden final text. **No script lock, VO, render or export** until the Night Producer relays Research's PASS or FIX. A PASS from anyone else doesn't count. Meanwhile I'm doing only zero-credit prep. No new OpenArt stills unless a Research FIX needs them.

### ElevenLabs spend so far: 500 credits, all on the pronunciation test
- **One** text-to-speech call (31 Oct, 00:48 UK), model eleven_multilingual_v2, voice "joe afrian british 1", the 10-term test line (Ishango, Lake Edward, Jean de Heinzelin, late Pleistocene, "around 20,000 years ago", Pletser, Huylebrouck, Keller, Brooks, OrigineX; 248 characters). The tool's default produced **2 takes at 250 credits each = 500**.
- Plus one Scribe transcription of the selected take for the read-back check: **0 credits** (tool reported 0).
- **No partial or full VO has been recorded.** Running ElevenLabs total: **500** (see credit_use_log.md).

### Zero-credit prep done during the hold (03:06 onwards)
- **Fixed a timing bug before it could bite:** Scribe writes spoken numbers as digits ("20,000" in the test transcript), so "one hundred and sixty-eight" would come back as "168" and my first greedy aligner would have drifted every cut after line 03. The new aligner converts numbers to words on both sides (cardinals and spoken years) and sequence-matches the token streams.
- **Dry run on a synthetic Scribe-style transcript** (digits for 168 / 20,000 / 25,000 / 1935, 1950, 1962, 1987), no render, no export, in `work/dryrun`: all 46 lines aligned (match ratio 1.0, no weak lines, no overlaps). Name subtitles and schematic group highlights land on the spoken words. Minimum readable time for a name subtitle is now 1.8 s (L09 "Hubert Damas" was 0.78 s). Mix stage on a silent stand-in VO: −13.9 LUFS integrated, −1.8 dBTP true peak.
- Runtime check: the synthetic transcript ran faster than the real voice (≈170 vs the measured 155 wpm) and gave 4:26. At the real pace the cut lands ≈ 4:50–5:00. If the real VO comes in under 4:30, I'll widen the line gaps rather than pad with silence.

### AI label ruling (clarified by the Night Producer)
"Reconstruction (AI)" on every AI still is **Chief's ruling of 31 Oct 00:25**, based on Ernest's 30 Oct editorial standard (never present AI imagery as evidence; label reconstructions). It's not a direct quote from Ernest. The label stays ON for this review cut; Ernest confirms in the morning. The engine flag `ai_label` (default ON) can turn it off in one line if he rules otherwise.

## Script draft posted for the lock-check: **v0.2** (supersedes v0.1)
- **v0.2, 31 Oct ~01:25 UK:** reconciled line by line with research/LEDGER_v1.csv (follow-up 03). Refs in `script.md` and `claim_register.md` are now ledger IDs.
- **Changed from v0.1:** lines 09–11 (Semliki line cut, as it isn't in the ledger; Damas → C04; de Heinzelin "a geologist from the Institute", Belgian Congo → C01/C03; "the museum … says it was found during that dig" → C02), 16 (C06 permitted wording), 18 (D07 attributed: de Heinzelin "engraving or tattooing", brochure "ritual scarification"), 24 (C09 permitted wording), 26 (D01: de Heinzelin's own "might be chance" hedge added), 27 (C10: the museum's pairs), 28, 30 (D03: their own "unspectacular conclusion" instead of "oldest mathematical tool"), 33 (D05 paraphrase: "tally marks … may have been used to add or multiply"; corrected 03:16, it was not an exact quote), 34 (flow), 39 (C12: layers, not the bone), 40 (C16 permitted wording + "last Ice Age"), 42.
- **Eden script item id: 342592c3-60ae-40f0-ba2a-bb9daf5ee103** (updated to v0.2, read back).
- Passes: Claude draft → YouTube Script Studio (line 02) → Write Like Joe (05, 07, 18, 44; "By hand" on 15 rejected) → ledger reconciliation.
- 46 lines · 733 words · ~284 s VO at the measured 155 wpm, so ~5:00 with the title card, end card and line gaps (target 4:30–5:30).

### Points for the lock-check
1. Lines 15 and 45 ("cut by someone in this community" / "someone at Ishango … cut these marks"): INFERENCE, the agency framing from the brief §4. OK?
2. Line 17 uses C07's evidence (brochure: species can't be told), and line 36 uses D08's evidence (de Heinzelin's "more than pure decoration"). Both ledger rows are NOT DOCUMENTED for their *claims*; the script narrates only the documented evidence. OK?
3. Line 38 range "around 20,000 to about 25,000" (C11–C14); no figure presented as settled. Lines 01, 42 and 45 say "around twenty thousand".
4. Line 40 "pushed the site's age back": the ledger's permitted wording for C16, though the earlier, younger date (C17) is UNVERIFIED. Keep, or say "placed the site in the late Pleistocene"?
5. Name subtitles: Hubert Damas, Jean de Heinzelin, Pletser & Huylebrouck, Marshack (surname only), Olivier Keller, Brooks & Smith.
6. Line 30 quotes D03's own words ("unspectacular conclusion … counts events or things … mixed bases 10 and 12"); "oldest mathematical tool" is not used anywhere.

### Script v0.2 (narration, numbered; one line = one picture)
```
01 A lake shore in central Africa, around twenty thousand years ago. Someone is holding a piece of bone about ten centimetres long.
02 At one end, a fragment of quartz. Along the sides, rows of small cut marks.
03 Today, the museum that holds it counts one hundred and sixty-eight of them.
04 And for decades, people have argued about what they mean.
05 Is it a tally? A game? A calendar? Or marks we can't read at all?
06 This is OrigineX, and this is the Ishango bone.
07 Three questions. What is it, and where is it from? What do the marks show? And how much can they really tell us?
08 Ishango sits on the Congolese shore of Lake Edward, in what is now the Democratic Republic of the Congo.
09 The site was found in 1935, by Hubert Damas.
10 In 1950, when this was still the Belgian Congo, Jean de Heinzelin, a geologist from the Institute in Brussels, led excavations here.
11 The museum that holds the bone says it was found during that dig.
12 Today, it's held by the Institute of Natural Sciences in Brussels.
13 The people who lived at Ishango were lakeside fishers. They made harpoons from bone.
14 The excavations also found the remains of at least nine people.
15 Whatever the marks mean, they were cut by someone in this community.
16 It's a small bone handle, about ten centimetres long, with a sliver of quartz at its tip. It was probably part of a tool.
17 It came from a mammal, but which animal, the museum says, can no longer be told.
18 And the quartz? De Heinzelin suggested engraving or tattooing. The museum's brochure mentions the ritual scarification of skin. These are only hypotheses.
19 Then there are the marks.
20 The museum counts one hundred and sixty-eight notches, in three columns. And they appear to be grouped.
21 On one side, groups of eleven, thirteen, seventeen and nineteen. Together, sixty.
22 In the middle: three, six, four, eight, ten, five, five and seven. Forty-eight.
23 And on the other side: eleven, twenty-one, nineteen and nine. Sixty again.
24 But some marks are worn, so a few counts are uncertain. That ten, for one, could be a nine.
25 So even the counting comes with a question mark.
26 Jean de Heinzelin admitted the patterns might be chance. But in 1962 he wrote that they seemed deliberately planned, perhaps as an arithmetical game.
27 He saw doubling in the middle column, and the museum points to the same pairs. Three and six. Four and eight. Five and ten.
28 He also noted that eleven, thirteen, seventeen and nineteen are prime numbers.
29 Not everyone agrees. Pletser and Huylebrouck rejected the prime-number idea, and the museum says there isn't enough proof.
30 Their own conclusion, which they call unspectacular: probably a tool for counting events or things, kept by someone who mixed bases ten and twelve.
31 Another reading, from the researcher Marshack, linked the marks to a lunar calendar.
32 Keller calls that idea now largely discredited.
33 The Smithsonian calls them tally marks, and says they may have been used to add or multiply.
34 Keller is the most sceptical. Some marks are worn or barely visible, he says, and that makes any numeric reading suspect.
35 A notch, he writes, may be nothing more than a mark.
36 Even de Heinzelin only said he suspected the marks were more than pure decoration.
37 So how old is it? That depends on who you ask.
38 The figures in the sources run from around twenty thousand years to about twenty-five thousand.
39 That's because the dates come from the layers at the site, not from the bone itself.
40 In 1987, a new study by Brooks and Smith pushed the site's age back, into the late Pleistocene, the last Ice Age.
41 So, our three questions.
42 What is it? A small bone handle with a quartz tip, found at Ishango on Lake Edward in 1950, and around twenty thousand years old.
43 What do the marks show? The museum counts one hundred and sixty-eight, in three columns, and they appear to be grouped. Some are worn, so not every count is certain.
44 And how much can they tell us? Less than we'd like. Counting, a game, a calendar, or simply marks: each reading has its defenders, and none is proven.
45 What we do know is this. Around twenty thousand years ago, someone at Ishango took this tool and cut these marks into it.
46 Whatever they meant, that meaning was theirs.
```

## Build progress while waiting for the lock-check (no VO recorded yet; script NOT locked)
Time: 31 Oct 2026, ~01:35 UK (GMT).
- **Stills: all 33 unique AI stills done and reviewed** (OpenArt · Wan 2.7 Image, 4K). Google/OpenAI models are excluded per brief §5; a Kling 3 Omni test was rejected (it put a boat in the scene and left the quartz off). 14 redos after per-still review: jointed long bones (C07 conflict), ruler-like ticks, "+"/"H"-shaped marks (OCR risk), metal-looking harpoons with modern rope, a modern window frame, a conifer forest. Every prompt carries "no modern buildings, bricks, metal roofs, factory smoke". Review notes per still: `work/stills/manifest.json` (stills stay in the session, not the repo). Lines 41 and 45 deliberately reuse the 07 and 01 stills as callbacks, with reversed moves.
- **Real images:** the NASA Lake Edward image now downloaded (sha256 ba390a81… matches credits.md), so line 08 is a real PD locator (animated push-in, plain ring marker on the north-west shore, position approximate, no label). Bone photo (BY-SA, review only) on lines 03, 12 and 42. CC BY schematics on lines 20–24, 27, 28, 30 and 43: **cropped to the marks so the printed sums don't appear on screen**, with each group lit as the narrator says its number.
- **Engine rebuilt** (`engine/ogx_engine.py`): FG/BG 2.5D layers (matting + inpainted BG plate), Nok motion settings, motion floors on, banned overlays (chapter cards, lower-third boxes, source cards, subscribe badge, map tags, credit pages) behind flags defaulting OFF that refuse to render if switched on, AI label ON, one credit line per real image, name subtitles. Each shot writes a rendered matte, so `engine/qa_motion.py` measures FG/BG travel from rendered frames.
- **Test renders:** AI still: FG 4.25 %, ratio 4.3, PASS. Real photo: FG 4.02 %, ratio 16.4, PASS. Schematic: FG 4.43 %, ratio 5.6, PASS. Map: flat image, logged as MAP-OVERRIDE (24 % travel, no fake parallax).
- **Music:** original procedural bed + lake ambience generated locally (0 credits); it thins under the readings section. Flagged as review-cut placeholder; no approved cue was reachable to reuse (L35).
- **Higgsfield/Kling motion clips:** not used (0 of 6 clips, 0 of 62 credits).
- **Pre-flight (L10) DONE: all 46 beats render; no missing assets.** First pass: 38 PASS, title card OK, map MAP-OVERRIDE, 6 short of the floors (16, 19, 25, 32, 34, 35). Fixed and re-measured from rendered frames: 16 FG 4.50 % (ratio 6.0); 19 6.35 % (9.6); 25 3.21 % (5.7); 32 4.05 % (4.1); 34 3.76 % (12.0); 35 3.48 % (5.5). For 19, 34 and 35 I added a luminance matte (bright bone on a dark ground), because a horizontal ground split cut across the diagonal bone and smeared a seam (the Nok L34 failure). I checked the end frames by eye: no smear. Every override is listed per shot in `scene_cards.md`. OCR on the pre-flight grabs found only allowed text (AI label, credit lines, name subtitles, title card) plus texture noise ("SSS", "wit", "Imi" on sediment and line-art frames).
- **Drafts:** `ledger.md` (claims documented/debated/inference + every picture asset by line) and `description.md` (full sources, reconstruction note, credits, ShareAlike flags). Both get finalised at script lock.
- **Waiting on:** OGX Research lock-check of script v0.2 (posted above). After PASS (and any fixes): one full VO pass in "joe afrian british 1", Scribe word timings, render, mix (−14 LUFS, TP ≤ −1), QA, exports.

## Gate log (this session)
| # | Gate | Result | Evidence |
|---|---|---|---|
| 1 | Still source (OpenArt or Canva) | **Route available** (no stills generated yet) | OpenArt account active with credits available; cdn.openart.ai reachable. Canva export host blocked, so OpenArt is the route. |
| 2 | Voice + pronunciation test | **PASS (read-back); ear-check open** | Voice "joe afrian british 1", eleven_multilingual_v2. Test line (Ishango, Heinzelin, Lake Edward, Pleistocene, Pletser, Huylebrouck, Keller, Brooks, OrigineX, "around 20,000 years"): 2 takes, 15.28 s and 16.33 s. Scribe transcript of the selected take matches the text word for word. No respellings needed so far. I can't listen in this session, so Ernest or QA needs to do an ear-check (files in work/vo/, kept in the session, not in the repo). |
| 3 | Research evidence pack before script | **CLEARED** (follow-up 02) | research/EVIDENCE_PACK_v1.md and research/credits.md saved from the Night Producer's message. My sha256 values differ from the box values (pack 444b64bd… vs be0f92b3…; credits fdba7417… vs c9db3486…). That's expected, because the chat paste rewrote the middle dots and line endings, so **the box copies are authoritative**. LEDGER_v1.csv received in follow-up 03 and saved (30 rows × 10 columns, parses cleanly). My sha256 is 322e67ca… vs box 67d69056…, the same chat-paste difference, so the box copy is authoritative. |
| 4 | Allowlist | **Partly OK** | upload.wikimedia.org reachable; commons.wikimedia.org, arxiv.org, naturalsciences.be blocked (not needed now). |
| 5 | Pre-flight every beat | Not reached | Comes after the lock. |

## Real images (fetched from upload.wikimedia.org, generic User-Agent, sha256 checked against credits.md)
| File | Result | Use |
|---|---|---|
| Ishango_bone_(cropped).jpg | **MATCH** 45fc44e8… (891×1230) | Lines 03, 12, 42. CC BY-SA 4.0: **review cut only; needs Ernest's exception before publish.** Author flag (Joeykentin vs JhowieNitnek) still open. |
| IshangoColumnA/B/C.png | **MATCH** 88fbe142… / 932733d2… / 1913c59d… (≈400×90–110) | Lines 20–24, 27, 28, 30, 43. CC BY 2.5, approved. Low resolution, so I'll redraw them for the screen with the credit "after Albert1ls · Wikimedia Commons · CC BY 2.5". |
| Wfm_lake_edward_lake_george.jpg | **NOT YET: Wikimedia 429** (twice) | Lines 08–09 locator. **Ask: Research's verified box copy** (L31), or I retry with backoff. |
| Elephants ×2 | Not fetched (429) | Not used in the script. |
| Ishango_Bone.jpg (Claire H.) | **Not fetched, by instruction** | Not used. |

## Kickoff gaps still open
- **Engine:** RUNBOOK-v2, the `ogx-motion-documentary` skill and the Nok engine code can't be reached from this session. Plan: rebuild a compact engine from Lessons L1–L37 (2.5D FG/BG parallax with Nok settings, motion floors on, every banned overlay behind a flag defaulting OFF, `ai_label` ON per Chief ruling 1, credit line per real image, name subtitles). **Chief: send the engine if it exists; otherwise I'll rebuild after the lock.**
- **House-standard conflict (flagged, not chosen silently):** the 25 Oct house standard draft (e841609d) says "no AI imagery". The brief (§5), Chief's follow-up 01 and Nok v1.0 use labelled OpenArt stills. I'm following the brief and the Chief rulings.
- **AI-label ruling:** Chief ruling 1 reverses Ernest's 29 Oct no-label rule (L23). Chief: please confirm these are Ernest's own words.

## Next (in order, after the lock-check PASS)
1. Apply any lock-check fixes; lock the script (v1.0).
2. Full VO in one pass plus line fixes; pre-flight every beat.
3. OpenArt stills, one per AI line (prompt: "no modern buildings, bricks, metal roofs, factory smoke", no faces, review each still).
4. Engine render, then QA on each cut (OCR, parallax stats, freezedetect −50 dB, loudness, credits read-back).
5. 1080p + 720p review exports kept in the session, with sha256 + md5.

## Earlier run log (same session)
- ~00:25–00:35 UK: kickoff stopped at gate 3 (no pack). Queue row updated to Blocked with the pack spec.
- 00:25 UK: Chief follow-up 01 rulings recorded (section below).
- ~00:40 UK: follow-up 02, gate 3 cleared; this build resumed.

## Follow-up 01: Chief rulings received 31 Oct 2026 (stamped 00:25 UK); apply from the next run
1. **AI labels ON:** every AI still carries a small on-screen "Reconstruction (AI)" label for its whole time on screen, plus a note in the description and ledger. Engine flag `ai_label` defaults ON for this film. ⚠️ This reverses Ernest's 29 Oct standing rule (L23: unlabelled "until Ernest rules otherwise"). Logged as a Chief ruling. **Chief: please confirm it is Ernest's own words** so QA judges against the right rule.
2. Lean AI stills from OpenArt/Canva only. Higgsfield/Kling for motion only: max 6 clips, hard cap 62 credits.
3. **Export route:** exports stay inside this session. Record sha256 + md5 for each and report file names and hashes; Ernest moves them to his private Drive himself. No media of any kind (mp4, images, audio, encoded) goes in the repo. Text and code only.
4. The two CC BY-SA Commons images are allowed in the REVIEW cut only, both flagged "needs Ernest's exception before publish". PD/CC0/CC BY substitutes preferred. Claude can't reach commons.wikimedia.org from here, so Research needs to look for them.
5. Connectors: ignored unless one blocks the build. None blocks the current stop; the blocker is the missing evidence pack, not a connector.

**Effect on tonight: none.** Gate 3 still fails, so there is still no script and no build.
