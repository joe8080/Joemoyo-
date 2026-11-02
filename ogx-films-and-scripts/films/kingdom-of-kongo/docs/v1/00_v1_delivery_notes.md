# Kongo v1: private preview, delivery notes
Prepared by Claude, 2 November 2026. **Private. Joe approves any release.**

## 1. What v1 is
- A first full cut, 6:57.5, 1080p25, built from the dev-v0.1 script (`../dev-v0.1/03_script_v0.1.md`).
- Narration in ElevenLabs (approved channel voice "joe afrian british 1"). This replaces Joe recording it himself, at Joe's request ("use eleven labs for that and create the film").
- **Not locked.** The translations are working translations from Brásio's Portuguese. They have **not** been checked against Thornton's 2023 English edition (gap G1). Fix that before any public release.

## 2. Status board
| Status | State |
|---|---|
| Research ready | Partly (G1, G2 still open) |
| Script locked | No |
| Narration | AI voice, v1 (8 sections) |
| Rendered | **Yes, v1 private** |
| Technical QC | See section 5 |
| Approved | No (Joe only) |
| Published | No |

## 3. What changed from the plan
1. **Motion clips: none in v1.** The 5 Higgsfield Kling 3.0 clips failed twice on Higgsfield's side (first batch queued about 90 minutes, then failed; the retry failed too). All 90 credits were refunded. I stopped there and sent nothing more. Every AI still uses slow camera moves instead.
2. **K4 (school scene)** was flagged by Higgsfield's upload filter (a false positive), so it was always going to be a still.
3. **Music:** one 60-second ElevenLabs cue, looped with crossfades. It drops to silence under the kidnapping lines in R6 and after "the people who were taken" (end of R7).
4. **Real 1526 pages:** colour scans of the 6 July 1526 letter (PT/TT/CC/1/34/94) and the microfilm of the 18 October 1526 letter (PT/TT/CC/1/35/21), from Torre do Tombo's DigitArq. The colour chart is cropped off.
5. **Loudness:** the raw mix measured about −35 LUFS. It was levelled to −14 LUFS (YouTube target) with ffmpeg's dynamic loudnorm.

## 4. Credits used (this build)
| Service | Used | Notes |
|---|---|---|
| ElevenLabs | 6,404 (voice) + 900 (music) = **7,304** | Inside the approved ~9,500 |
| OpenArt | **270** | 6 stills, gpt-image-2.5, 2K, medium (45 each) |
| Higgsfield | **0 net** | 2 × 5 Kling jobs, all refunded. Balance 3,261.3 before and after |
| Firecrawl | a few searches | research only |

## 5. Technical QC
Filled in from the final file. See `01_v1_qc.md`.

## 6. Asset register (as used)
| ID | Asset | Date | Source | Licence | Label on screen |
|---|---|---|---|---|---|
| P1–P4 | Afonso I to João III, letter, 4 image files | 6 Jul 1526 | ANTT, DigitArq, PT/TT/CC/1/34/94 | Original public domain; reproduction terms of ANTT still to confirm before public release | Yes |
| O1–O2 | Afonso I to João III, microfilm | 18 Oct 1526 | ANTT, DigitArq, PT/TT/CC/1/35/21 | as above | Yes ("MICROFILM") |
| MAP1668 | *Regna Congo et Angola*, Olfert Dapper | 1668 | Wikimedia Commons | CC BY-SA 4.0 | Yes, "drawn 140 years later" |
| BANSA1670 | *Bansa or Salvador*, engraving | 1670 | Wikimedia Commons (BEIC) | Public domain | Yes, "as imagined by a European engraver" |
| SHIPS | *Livro das Armadas* | 16th century | Wikimedia Commons | Public domain | Yes |
| CAVAZZI | Cavazzi da Montecuccolo, Kongo–Angola scene | 1650s | Wikimedia Commons | CC BY 4.0 | Yes |
| CUSHION | Kongo raffia cushion cover | c. 1600 | Wikimedia Commons (Etnografiska, Stockholm) | CC BY-SA 2.5 | Yes |
| NZIMBU | *Olivancillaria nana* shell | modern specimen | Naturalis via Commons | CC0 | Yes |
| CRUCIFIX | Kongo crucifix | 16th–17th century | The Met via Commons | CC0 | Yes |
| JOAO3 | João III, Antonis Mor | 1552 | Wikimedia Commons | Public domain | Yes |
| BAPTISM | Baptism of Nzinga a Nkuwu, Robert Benard | 1780 | Wikimedia Commons | Public domain | Yes, "as imagined, 1780" |
| TT | Torre do Tombo building | modern | Wikimedia Commons | CC0 | Yes |
| MAP | OGX locator map | 2026 | OGX, Natural Earth base (PD), extent after Thornton 2020 | OGX | "Approximate" |
| K1–K6 | AI reconstructions (coast, hilltop town, scribe's table, school, river at night, trade goods) | 2026 | OpenArt | OGX, generated | "AI RECONSTRUCTION · ILLUSTRATIVE, NOT A RECORD" |

**Rule checks:** no AI faces of named people; no generated manuscript (the scribe's table shows a blank page); no invented flags or insignia; Kinshasa marked "not Kongo's capital" on the map.

## 7. Before any public release
1. Check the quoted translations against Thornton 2023 (G1).
2. Confirm ANTT's reproduction terms for the DigitArq images (G3).
3. Credit the CC BY / CC BY-SA images in the description (Dapper map, Cavazzi, cushion cover).
4. Joe's approval.
