# OGX — ADWA 1896 · v1.5 production pack
Episode ID: ogx-adwa-1896 · Version: v1.5 (private) · Built by Claude, 21 October 2026 · supersedes v1.4 for review (v1 to v1.4 kept unchanged)
Status: PRIVATE PREVIEW for MJ review → Joe approve / request changes. Not uploaded, scheduled or published.

## What changed from v1.4 (MJ fact-check brief, 21 Oct, applied at Joe's instruction)
Full old/new wording, timecodes and sources are in `OGX_Adwa_1896_v1.5_change_log.md`. In short:
1. **Five required corrections:**
   - V01: "a later artistic reconstruction";
   - V10: Kaffa moved to 1897, after Adwa;
   - V17: "a major Ethiopian victory" at Amba Alagi;
   - V29: fighting continued into the afternoon;
   - V38: the holiday is on 2 March; the battle stays 1 March 1896.
2. **Qualifications:**
   - no Russian-supply detail;
   - "late February" for the council;
   - "around dawn" for first contact;
   - "Estimates of the losses differ";
   - "Italian-led army… by one estimate";
   - "In 1897, France and Britain signed agreements";
   - Taytu's plan credited to "some accounts";
   - the unnamed-historian line is cut;
   - May/must is labelled PARAPHRASE;
   - the 1935 caption separates the invasion from the occupation.
3. **Pictures:**
   - A10 re-dated to c. 1940, with the photo credited CC BY-SA 4.0 (Szilas);
   - A13 removed and replaced by A07 and A05;
   - the A09 Amba Alagi panels replaced by a real-terrain map and N51.
4. **Battle maps:** darker base, larger type, columns drawn one at a time, persistent brigade names, a legend, and longer holds.
5. Re-voiced lines come from one new take of the same voice. Everything was retimed together. **10:46**, 166 caption cues.
6. **Spend:** ElevenLabs ≈ 4,680 credits; Higgsfield 0.

## Earlier changes (v1.4, from v1.3) (Joe's notes, 21 Oct)
1. **10:01: the emperor now appears.** The line "…an emperor… and an empress" showed only Taytu. It now opens on the Menelik II engraving (A02) and dissolves to Taytu (A04) just before "and an empress".
2. **Tonga removed.** The next-film tease is gone from the voice and the end card. The close now says "If you think this record is worth keeping, please subscribe." and the end card reads "If this record is worth keeping," with the subscribe badge below.
3. **Subscribe badge at 2:00.** A glass black-and-gold badge with a play icon, "SUBSCRIBE" and "ORIGINEX HUMAN ARCHIVES". It slides in at the bottom right from 2:00.0 to 2:03.8, and its rim flashes lime 3 times at moderate brightness. The same badge also flashes 3 times on the end card.
4. **Same length (10:51) and same everything else.** Only the affected segments were re-rendered. The mix and captions were rebuilt for the shortened close line (`OGX_Adwa_1896_v1.4_EN-GB.srt`, 168 cues).
5. **Spend:** 0 credits (local edit and render only).
6. **Saved as a skill:** `ogx-motion-documentary` captures the whole pipeline and all of Joe's corrections so far. It is ready to refine after the next round.

## Earlier changes (v1.3, from v1.2) (Joe's note, 21 Oct: "turn the images into motion clips… people actually move")
1. **Every AI picture now moves.** All 54 AI reconstruction stills were animated image-to-video on Higgsfield (Kling 3.0 Pro, 1080p, 24 fps, no audio). Each clip starts on the exact approved still, so composition and style are unchanged, and each has its own motion direction: columns marching, horsemen charging, rifle smoke, campfires, lamp and candle flicker, mist and cloud moving, crowds walking.
2. **Clip lengths match the narration.** Each clip was generated 4 to 15 s long, enough for every line it covers. Where a picture appears more than once, each appearance plays a different stretch of its clip, so no movement repeats. Only one appearance is slowed at all, by under 1% (N04 at the close).
3. **Same guardrails.** Figures stay anonymous with no close-up faces, no flags or readable text were added, and the on-screen tag now reads "AI RECONSTRUCTION, ANIMATED · ILLUSTRATIVE, NOT A RECORD". Archive pictures, real maps, cards, voice, music and captions are unchanged from v1.2, so the timing is identical (10:51).
4. **Checked.** Contact sheets for all 54 clips (start, middle and end frames) were reviewed for warping, drift and invented markings. In the first version of N45 (the 1935 convoy), the biplanes flew close to camera with made-up lettering on them, so that clip was regenerated with the planes kept distant and unmarked, and the new version passed the check. One clip (N29, the messenger) blurs in its final second, but that second is never used in the cut.
5. **Caption fix.** The 1935 caption's arrow ("1935 → 1941") showed as an empty box because the font has no arrow character. It now reads "1935 – 1941 · ITALY RETURNS". The same fault was in v1.2.
6. **Spend.** Higgsfield: 646.5 credits (54 clips at 633, plus 13.5 to redo N45; 1,993.75 → 1,347.25). ElevenLabs: 0 credits; it was used only as a free file bridge, because this cloud session cannot download from Higgsfield directly.

## Earlier changes (v1.2, from v1.1) (Joe's notes, 21 Oct)
1. **More pictures, fewer cards.** Text cards are down from 27 to 3: the opening question, "May. Must." and the final "Ready". The other 24 are now pictures, with the key fact kept as an on-screen caption (dates, estimates, "contested", "by most accounts").
2. **34 new illustrated stills** in the house engraving style. All figures are anonymous, with no flags and no readable documents, and each is labelled "AI reconstruction". The 8 longest lines now cut to a second picture partway through.
3. **Music by scene.** The 4 long cues are replaced by 12 new cues, one per act, each matched to what's happening:
   - washint flute mystery for the cold open
   - pizzicato intrigue for the treaty
   - krar and masenqo court music for the emperor and empress
   - kebero war drums for the call to arms
   - action, then siege tension, for first blood
   - suspense for the standoff, a stealthy night march
   - a full battle cue
   - a lament for the cost
   - hope for the peace
   - legacy and pride
   - a resolving finale
4. **Sign-off pronunciation.** The close is re-voiced so "OrigineX" is said "OR-ih-jin-EX". It's spelt "Origin-ex" in the voice prompt only; the screen and captions keep "OrigineX". Scribe still writes it as "Origin X", with a ~60 ms join between the two parts. Joe to confirm by ear.

## 1. What was built
- Master: `OGX_Adwa_1896_v1.5.mp4`, 1920×1080, 24 fps, H.264 CRF 19, AAC 320k 48 kHz, **10:46**. QC: −14.0 LUFS, LRA 5.1, peak −1.5 dBFS, no black frames, 15,514 frames.
- Structure unchanged (Nzinga v6.2 / Production OS v2.0): cold open on the 1898 Petit Journal image → question card with silence → title → 10 numbered acts → close returns to the object → sign-off → next-film end card (8 s tail).
- Narration: ElevenLabs **joe afrian british 1**, `eleven_multilingual_v2`, one continuous take per act (12 takes), split per line using Scribe word timings, with each cut placed at the quietest point of the pause. v1.5: 12 lines re-voiced in one patch take (same voice and model), 1 line cut, so 115 lines. Original pass: 1,611/1,633 script words matched in the Scribe transcript, and the misses are spelling variants only (Wolayta, Albertoni, centre/center, numerals).
- Picture: 115 shots, one per line, some with a second picture. AI reconstruction shots are all animated motion clips (54 unique clips). There are archive shots, real-map shots (v1.5 adds an Amba Alagi terrain map and drops A13 and the A09 Amba panels), 3 cards, a title card and end cards.
- Score: 12 ElevenLabs `eleven_music_v2_5` instrumental cues, one per act, 2.5 s crossfades at act changes. Ducked −11 dB under voice, silence under the question card, swell on the title. No time-stretching was needed. No separate vocal-detection pass this time; every cue was generated with the instrumental setting.
- Mix: master **−14.0 LUFS**, −1.5 dBTP, LRA 5.0.
- Captions: `OGX_Adwa_1896_v1.5_EN-GB.srt`, 166 cues, from the v1.5 voiced text (see `OGX_Adwa_1896_v1.5_final_script.md`).
- Script: `OGX_Adwa_1896_v1.5_final_script.md` (as voiced, with timecodes and on-screen text).

## 2. Chapters (from the actual cut)
0:00 Adwa, 1896 · 0:45 One word · 1:50 The emperor and the empress · 2:56 The call to arms · 4:00 First blood · 4:53 The standoff · 5:34 The night march · 6:20 The battle · 7:41 The cost · 8:24 The peace · 9:01 Whose victory · 9:55 The answer

## 3. Claim ledger (v04 ledger, re-checked against the v05 wording)
Evidence level throughout: modern secondary/reference sources via search summaries (publisher and Wikipedia pages could not be opened from the build machine). No contemporary document was read. Contested items are framed in the line itself.

| ID | Line (short) | Basis | Framing used | MJ check |
|---|---|---|---|---|
| V01 | Le Petit Journal printed the image in Paris, 1898; **"a later artistic reconstruction"** (v1.5) | Image itself dated 28 Aug 1898, after Paul Buffet; Fontaine (S3) documents Buffet photographing Menelik in 1897, which does not make him a battle eyewitness | "This is a later artistic reconstruction" | Resolved v1.5 |
| V02 | 1 Mar 1896, Ethiopia destroyed an invading Italian army **in a single day** (v1 said "single morning"; corrected, fighting ran to early afternoon, see V29) | v03 C02; Jonas preview; Britannica/EBSCO summaries | Broad outcome | — |
| V03 | Wuchale 1889; Article 17 Amharic "may" vs Italian "must" reading | v03 C03–C04; LOC (S2); S7 | **Labelled PARAPHRASE on screen (v1.5)**; no facsimile | Original texts still unread |
| V04 | Historians debate mistake vs deliberate | v03 C06 | "Historians still argue" (used once) | — |
| V05 | Menelik formally rejected (renounced) the treaty in 1893 | v03 C07 (single summary); **S1 McLachlan pp.6–11, 37 (per MJ check)** | Plain | Corroborated (MJ, S1) |
| V06 | Menelik ruled Shewa 20+ years before becoming emperor (1889) | Standard reference (king of Shewa from 1860s) | Plain | Low risk |
| V07 | "Planned ahead"; **imported modern rifles in large numbers** (v1.5: France/Russia specificity removed) | v03 C11; MJ brief | Plain | Resolved v1.5 |
| V08 | Taytu a political force; co-founded Addis Ababa in the 1880s; "new flower" | LOC (S2); Wikipedia summary (1886) | Plain | Low risk |
| V09 | Taytu pushed hardest against the Italian reading | LOC (S2) says it infuriated her and she pressed Menelik | "By one account" | — |
| V10 | Menelik's armies conquered Wolaita; **Kaffa followed in 1897, after Adwa** (v1.5); brutal; remembered as a conqueror in the south | S2 Seid Ahmed (Kaffa 1897); search summaries for the rest | "Many of those campaigns", "for many peoples" | Kaffa resolved; **broader framing still needs a scholarly source (e.g. Bahru Zewde)** |
| V11 | Crispi used the quarrel; Italy held Eritrea; Baratieri pushed into Tigray 1895 | v03 C08; standard reference | Plain | — |
| V12 | Call to arms in September (on-screen 17 Sept 1895) after famine and cattle disease | Search summaries (awaj, 17 Sept); Biography.com; **S1 McLachlan pp.6–11, 37 (per MJ check)** | Plain | Corroborated (MJ, S1) |
| V13 | Forces from Shewa, Gojjam, Tigray, Wollo under own commanders | Search summary on deployment (Tekle Haymanot, Mengesha, Mikael) | Plain | Low risk |
| V14 | Army 70,000 to 100,000+ | v03 C10 | "Estimates run from" | — |
| V15 | Pack animals, grain, camp followers; logistics feat | General; not page-sourced; **S1 McLachlan pp.6–11, 37 (per MJ check)** | Interpretive | Corroborated (MJ, S1) |
| V16 | Taytu marched at the head of her own troops | Search summaries (contingent sizes vary 3,000–6,000) | "According to the accounts" | Size deliberately omitted |
| V17 | **A major Ethiopian victory** at Amba Alagi, 7 Dec 1895 (v1.5; was "first big clash"); Ras Makonnen; ~2,000-man outpost, mostly Eritrean | S1 McLachlan | Plain | Resolved v1.5 |
| V18 | Mekelle: surrounded in January, springs seized, white flag within ~2 weeks, garrison allowed to leave | v03 C09/C13; search (siege 7–21 Jan) | "Within about two weeks" | — |
| V19 | **Some accounts credit Taytu with the plan** (v1.5; "thinner than legend" removed) | Encyclopedia.com, thesis; MJ brief | Attributed to accounts; placed at Mekelle | Resolved v1.5 (attribution kept) |
| V20 | Both armies short of food in February; Baratieri expected Ethiopian army to disperse | Britannica + Wikipedia (Baratieri) summaries | Plain | — |
| V21 | Rome pressed; Crispi's telegrams | v03 C14; search | Plain | — |
| V22 | A replacement general already sent | Search summaries (Baldissera); one 1896 paper reported a denial | "By most accounts" | — |
| V23 | Council of war **in late February** (v1.5) | Accounts differ, 28 vs 29 Feb (MJ brief) | "In late February" | Resolved v1.5 |
| V24 | Three brigades on separate tracks, fourth in reserve; 15,000–18,000 men | v03 C10/C16 | "Somewhere between" | — |
| V25 | Set out ~21:30, 29 Feb; dark, rough tracks, poor maps | v03 C01/C14 | "About" | — |
| V26 | Albertone's guides / wrong hill; pushed on kilometres ahead; gap | v03 C16 | "By most accounts" | — |
| V27 | First contact **around dawn** (v1.5); Dabormida drawn into separate fight | S1 | "Around dawn" | Resolved v1.5 |
| V28 | Arimondi held for a time; Menelik committed reserve; Ras Mikael's Oromo cavalry on flanks | v03 C19; search (Mikael led Oromo cavalry) | "According to the accounts" | — |
| V29 | **Italian centre collapsed; fighting continued into the afternoon**; Arimondi and Dabormida killed; Albertone captured (no single time, v1.5) | S1 pp.20–22 | Plain | Resolved v1.5 |
| V30 | **Estimates of the losses differ**; by one estimate the **Italian-led army** lost ~6,000 killed, ~3,000 prisoners; many Eritrean soldiers; Ethiopian dead 4,000–7,000 | S1, S7 (reference summaries disagree) | "By one estimate", "about", "around", "Estimates run" | Resolved v1.5 |
| V31 | The Graphic printed this scene from survivors' details | Commons file description ("drawn from details supplied by survivors", 11 Apr 1896) | Plain | Low risk |
| V32 | Protests in Italy; Crispi's government fell within days | v03 C23; search (resigned ~5 Mar) | Plain | — |
| V33 | Treaty of Addis Ababa Oct 1896; Wuchale cancelled; independence recognised; Italy kept Eritrea | v03 C25–C26 | Plain | — |
| V34 | **In 1897**, France and Britain signed agreements with Menelik (v1.5) | S5 FRUS 1907 d460 (20 Mar and 14 May 1897) | Plain | Resolved v1.5 |
| V35 | Ethiopian paintings show St George above the army | The A10 painting itself | "Paintings like this one, made long after" | Rights check A10 |
| V36 | Adwa seen as proof colonial rule could be beaten. **The unnamed-historian "meaning made later" line is cut in v1.5** | S6 (Jonas description: immediate recognition across the diaspora) | — | Resolved v1.5 (cut, no replacement) |
| V37 | 1935 invasion; occupation of much of the country until 1941. Caption "1935 INVASION · OCCUPATION TO 1941" | v03 C29; S3 | Plain; no claim of uninterrupted independence or total control | Resolved v1.5 |
| V38 | Battle 1 March 1896; **today the Adwa Victory Day holiday is on 2 March** (v1.5) | S4 Ethiopian Investment Commission holidays table | Plain | Resolved v1.5 |

Deliberately omitted: exact Ethiopian deployments, Taytu's troop numbers, askari mutilation, "never colonised", "first African victory over Europe", any quotation or dialogue.


## 4. Picture sources and rights ledger
Archive (shown framed with an on-screen credit strip for ~5 s on first use):
- A01 Le Petit Journal, 28 Aug 1898, after Paul Buffet — Commons "Menelik - Adoua-2.jpg", PD-old.
- A02 Menelik II engraving — Commons "Menelik II.jpg", PD.
- A03 Taytu Betul engraving c.1886 — Commons "Taitu Betul v d.jpg", PD.
- A04 Taytu Betul, 1900 — Commons "Taytu Betul of Ethiopia.png" (BnF Gallica).
- A05 La Tribuna Illustrata 1895, Baratieri — Commons "Oreste Baratieri (1895) il vincitore di Coatit.jpg", PD in Italy.
- A07 The Graphic, 11 Apr 1896 — Commons "Adoua 1.jpg", PD.
- A09 Le Petit Journal composite (Commons "Ethiopia Italia war-2.JPG", PD-old). **v1.5: Amba Alagi panels removed** (source issue unidentified). Only the released-prisoners panel is still used (8:26). MJ cites LoC (S10) for that illustration, dated 29 Nov 1896. **Visual match to our crop still to confirm.**
- A10 Ethiopian painting of Adwa, **c. 1940** (1896 is the event, not the painting). Commons "Ethiopian painting, Battle of Adwa, 1896.jpg". **Photo by Szilas, CC BY-SA 4.0**, credited on screen and **not** public domain. **Underlying artwork status, artist and museum still unconfirmed.**
- A12 Carta dimostrativa della Colonia Eritrea, 1895 — Commons WDL649 (Library of Congress/WDL), PD.
- A13 "two Italian survivors" (Commons): **removed in v1.5** because its provenance leads to Quora and other secondary sites (S9). Replaced at 9:01 by A07 (The Graphic, 11 Apr 1896) and at 9:06 by A05 (La Tribuna Illustrata, 27 Jan 1895).
- A15 Francesco Crispi — Commons "Francesco Crispi.jpg", PD.
- Reference only (not shown): Commons "Adua battlefield.jpg" terrain map, used as a reference for placing the schematic battle movements.
AI reconstructions N01–N22: ElevenLabs gpt-image-2.5-sunburst, 2K, one generation each; anonymous figures, no faces of named people, no documents, no flags. Disclose AI use in the description.



**Maps (new in v1.1):**
- Relief: AWS Terrain Tiles (Mapzen terrarium encoding), sources SRTM, GMTED2010, ETOPO1. Open data; attribution is shown on screen (credit strip on first use) and goes in the description.
- Satellite: Copernicus Sentinel-2 L2A true colour, January 2025 (one 21 Feb and one 6 Mar tile on the outer Tigray edge), public sentinel-cogs archive. Required credit: "Contains modified Copernicus Sentinel data 2025". It is on screen and goes in the description.
- Borders, lakes: Natural Earth (public domain). Modern borders, labelled "MODERN BORDERS SHOWN".
- **Battle movements are schematic**, placed after standard published battle maps and keyed to Adwa town and the eastern ridges. Every battle frame carries "MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE". The Sauria camp, objective line and overshoot positions are approximations, not surveyed points. Amba Alagi's pin is approximate too.

## 5. Spend (ElevenLabs credits)
v1 ≈ 31,200 · v1.1 ≈ 12,600 · v1.2: 12 music cues 11,910 + 34 stills 9,354 + close re-voice 606 + Scribe 199 = **≈ 22,070**. **Running total ≈ 65,900 ElevenLabs credits.** v1.3: ElevenLabs 0; Higgsfield 646.5 credits (separate account). v1.4: 0. v1.5: ElevenLabs ≈ 4,680 (patch voice take). **Running total ≈ 70,580 ElevenLabs credits.**

## 6. Draft posting pack (for Joe's decision; nothing scheduled)
- Title A (recommended): **Italy Invaded Ethiopia. Then Came Adwa.**
- Title B (searchable): Adwa 1896: How Ethiopia Defeated Italy
- Description: as in v1, plus: "Maps: relief from AWS Terrain Tiles (SRTM, GMTED2010, ETOPO1); contains modified Copernicus Sentinel data 2025; borders from Natural Earth (modern borders shown). Battle movements are schematic and approximate. Contains AI-generated historical reconstructions, labelled on screen."
- Chapters: section 2.
- Thumbnails and Shorts: briefs as v1 (not yet made). The Africa→Adwa satellite zoom (0:09–0:16) is a strong Shorts opener.

## 7. Known limitations / for MJ
0. **v1.5 open items** are listed in the change log, section 5: A10 artwork status, A09 prisoners panel match, V10 scholarly source, V03 original texts, pronunciation, and a listen-through of the patched voice.
1. Research is still largely search-summary level. MJ corroborated V05, V12 and V15 against S1 and fixed V34 via S5. V10's broader framing still needs a scholarly source.
2. A10: the photo licence is now credited (CC BY-SA 4.0), but the underlying artwork status is open. A13 is removed. A09: only the prisoners panel remains, and its match to LoC is still to confirm.
3. Archive images are ≤1,024 px (relay limit), so some framed portraits are soft.
4. No next-film tease (Tonga removed in v1.4). Add one back only once the next release is confirmed.
5. Pronunciations (Adwa, Menelik, Taytu, Wuchale, Baratieri, Mekelle) still need a native-speaker listen.
6. The voice pass is a calibration of your correspondence voice for public narration (the voice bible's own caveat). Your corrections on specific lines are the best evidence for the next film.
7. The v1.5 master (≈ 680 MB) and the 720p review copy (≈ 135 MB) were sent to Joe in chat. They are too large for the Drive connector from this build machine, so Joe should drop the 720p copy into this folder from the chat download.
