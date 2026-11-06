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

---

# v1.2 (3 November 2026, same day)
Joe's notes on v1.1, and the fixes:
| Note | Fix |
|---|---|
| Music too loud and on top of my voice; sidechain it; use the YouTube limits | Music is now set relative to the voice: about 22 dB under narration, about 9 dB under in the gaps. A sidechain ducker keyed from the narration (attack 15 ms, release 350 ms, up to 10 dB more) drops it whenever the voice speaks. Mastered to the YouTube target: -14 LUFS integrated, true peak capped at -1.5 dBTP. |
| White hands instead of Black at about 2:09 and 3:57 | The two market clips (K6a, K6b) were remade on Higgsfield (Kling 3.0 Pro, 1080p, 10 s, about 30 Higgsfield credits) with Black Kongolese hands. Checked frame by frame. They appear at about 2:00, 3:40 and 6:30. The v1.1 clips are kept as K6a_v11_white / K6b_v11_white and are not used. |

Credits: Higgsfield about 30. No new Artlist or ElevenLabs spend.

# v1.3 (4 November 2026)
- End screen cleaned: only "KONGO, 1526" and "ORIGINEX HUMAN ARCHIVES". The private-preview line and the source list are gone from the picture.
- The sources and licences (Torre do Tombo letters, Brásio, Wikimedia/CC images, The Met, Naturalis, AI and music credits) must go in the YouTube description instead. CC BY and CC BY-SA images need credit there.

# v1.4 (5 November 2026): smoothness pass
Joe: "a bit unsmooth at the start and middle". A frame-by-frame check of v1.3 found:
1. Judder in every motion clip: the Kling clips are 24 fps, the film is 25 fps, so one frame doubled each second. Now every source frame plays once (4% faster). Where a clip is short for its slot it is slowed with blended frames, never doubled or frozen.
2. Rushed camera moves on stills (letters, maps, engravings at about 2:10, 3:50, 4:40 and the end). Every pan and zoom is now capped at a slow, even speed.
3. Flash cuts under 3 seconds removed (cold-open river clip, a 2-second dark coast shot, a ships shot, and two quick letter cuts plus a market clip in the close). The neighbouring shot now holds instead.
4. A fast "whip" in one market clip (cloth flung across frame at 6 s) is trimmed out; a candle flicker avoided.
5. Dissolves between shots lengthened from 0.6 s to 0.9 s.
Sound, words and timing are unchanged from v1.3.

# Release (5 November 2026)
Joe asked for the film to be posted on a schedule, with a comment that goes up when it goes live.
- **Scheduled** in Metricool for YouTube (OrigineX Human Archives): **Friday 6 November 2026, 16:00 UK time**, public. The file is v1.4 at 1080p.
- **Title:** Why Kongo's King Wrote to Portugal About the Slave Trade (1526)
- **Settings:** Education category; not made for kids; altered or synthetic content = yes (AI motion clips); subscriber notification OFF (Joe asked).
- **Description:** sources, the archive references for both letters, all image credits (including the CC BY and CC BY-SA ones), the AI-reconstruction note, music and voice credits.
- **First comment** (posted at go-live): "In July 1526 Afonso asked Portugal for no slave trade at all. By October he was making a law about who could be sold, after his own officials checked them. Which part surprised you most? Tell us below 👇"
- **Still open, Joe's call:** translations not yet checked against Thornton 2023 (G1); Torre do Tombo reproduction terms not yet confirmed (G3). To hold the release, delete or move the post in the Metricool planner before 16:00 on 6 November.

## v1.4 final QC (whole film, frame by frame)
- **No repeated or frozen frames anywhere** (the duplicate-frame rate is 0.00 in every shot). The 24→25 fps judder is gone.
- **The flagged "jumps" are the dissolves.** The new 0.9 s dissolves now reach into the measuring window. Each flagged peak sits 0.44 s into its shot, which is the tail of the dissolve, not a glitch. K5a (63.9 s) and the letter at 246.9 s were clean in v1.3 and are flagged only for this reason.
- **The letter pan at 277 s** now moves 41% less per frame (mean frame change 3.4, was 5.7). The figure stays higher than other shots because the page is dense handwriting, not because the pan is fast.
- **One 2.8 s shot remains:** the 1668 map at 325.6 s. Not changed.
- **Metricool check:** YouTube `notifySubscribers = false` is confirmed in the planner. That is YouTube's single "publish to subscriptions feed and notify subscribers" setting.
- **How this maps to the two boxes Joe named:**
  - Metricool's planner has one YouTube option, "Notify subscribers" (Metricool Help Center, "Schedule and Publish on YouTube"; September 2026 product update). It is set at upload. If left unset, subscribers are notified.
  - The API field that holds it is `notifySubscribers`, and for this post it reads false.
  - In YouTube Studio the same thing is a single checkbox, "Publish to subscriptions feed and notify subscribers". So both boxes are off for this upload.

# Shorts (6 November 2026)
Joe: "Can you post shorts". Three 9:16 Shorts were cut from the v1.4 film (`pipeline/v1_1/make_shorts.py`):
- Blurred fill behind the 16:9 picture, a title banner, and burned captions taken from the script.
- Caption timings come from a faster-whisper transcription of the film.
- A "FULL FILM ON THE CHANNEL" end line.
- Loudness: -14 LUFS.

| Short | Content | Length | Scheduled (UK time) |
|---|---|---|---|
| 1 "Kongo's King Warned Portugal in 1526: 'Our Kingdom Is Being Lost'" | Cold open (R0) and why he wrote (R2) | 35 s | Sat 7 Nov, 16:00 |
| 2 "In 1526, Kongo's King Made a Law About Who Could Be Sold" | The October law and the three officials (R6) | 33 s | Sun 8 Nov, 16:00 |
| 3 "What Portugal Told Kongo's King in 1529" | João III's reply (R7) | 45 s | Mon 9 Nov, 16:00 |

All three are scheduled in Metricool:
- YouTube Short, public, Education, not made for kids.
- AI content declared, subscriber notification off.
- Each has a first comment pointing to the full film.

Descriptions point to the full film's description for the sources and image credits.
