# Kongo v1.1: change log
Prepared by Claude, 3 November 2026. **Private. Joe approves any release.** v1 files are untouched.

## Joe's notes, and what changed
| Note | Fix in v1.1 |
|---|---|
| Bring the king's warning forward so the stakes are clear sooner | New cold open (R0). The film now starts on "Our kingdom is being lost…" and the "sons of our nobles… our relatives" line, over the 6 July 1526 letter, then the title. The polite opening of the letter follows. "Then the tone changes" is gone. The R2 question now reads "send that warning". |
| Map: stop the zoom cropping its labels | Locator map labels moved inside the safe area. The zoom is now gentle (full frame to 93%). The "modern borders / extent approximate" note moved to the on-screen label strip, so it can't be cropped. Checked on the first and last frame of the shot. |
| Keep July's demand alongside October's rules | R6 now ends: "So in July, he had asked for no slave trade at all. By October, he was setting rules that let some people be shipped, but only after his own officials had checked them." The "Regulation, not abolition" card is replaced by "JULY: 'NO TRADE IN SLAVES' / OCTOBER: SOME SALES, AFTER ROYAL CHECKS". R8 repeats both. |
| Don't claim we know his complete motives | R2: "His letters give us part of the answer… What his letters complain about is…". R8 rewritten: "We can't know everything he thought. We only have what he chose to write to another king. But his letters point to real dangers…" |
| AI illustrations as real motion clips | All 18 AI shots are now motion clips (Kling v3 Pro, 1080p, 10 s, via Artlist): ship sailing, canoe paddled, river flowing, town with smoke and people walking, candle flicker, the lesson under the tree, torches and canoes at night, hands lifting cloth and shells. Two variants per image, plus offsets, so no clip repeats the same way. Labels unchanged: "AI RECONSTRUCTION · ILLUSTRATIVE, NOT A RECORD". |
| Music via Artlist | Three original cues (Artlist, Lyria 3 Pro, instrumental): dark open (R0–R2), the kingdom (R3–R4), sombre close (R5–end). Crossfaded. Silences kept under the kidnapping lines and after "the people who were taken". Stock-catalogue tracks were tried first, but their download links returned 403 in the build sandbox. |
| 4:57–5:13 card stretch (v1 QC note) | The names cards now sit over the October microfilm, and a page of the October letter appears between them. |

## Credits used for v1.1
| Service | Used | Notes |
|---|---|---|
| Artlist | 11,000 (11 clips) + 900 (3 music cues) = **11,900** | Approved by Joe ("yes"). Night-river clip K5a was the free trial clip. |
| ElevenLabs | 455 + 168 + 622 = **1,245** | Re-voiced R2, the R6 ending and R8 in the approved voice. Total for the film is now 8,549, inside the approved ~9,500. |
| Higgsfield | 0 | Sandbox only |

## Files
- Pipeline: `../../pipeline/v1_1/` (film.py, audio_build.py, mix.py, tts.json)
- New sections: R0 (cut from the v1 R1 take), R1 (shortened), R2 (new take), R6 (v1 take plus a new ending), R8 (new take)
- Clips: K1a K1b K2a K2b K3a K4a K4b K5a K5b K5c K6a K6b
- Music: M1_open, M2_kingdom, M3_close

## Still open before any public release
1. Check the quoted translations against Thornton 2023 (G1).
2. Confirm ANTT reproduction terms for the DigitArq images (G3).
3. Credit the CC BY / CC BY-SA images in the description.
4. Joe's approval.
