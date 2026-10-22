---
name: ogx-motion-documentary
description: >-
  The BASE skill for making OrigineX Human Archives (OGX) films: the default way to build any OGX long-form history documentary end to end as a finished MP4. It covers Joe's cloned narration, archive images with a rights ledger, real terrain and satellite maps, AI stills animated on Higgsfield (Kling), a per-act score, captions, a subscribe badge, QC, and rounds of Joe's notes and MJ fact-checks with change logs and ledgers. Reference build: Adwa 1896, v1.0 to v1.5. Use whenever Joe asks to make, build, render, re-cut, fix or version an OGX film, "make the next OGX film", "do it like Adwa", "animate the images", "add the subscribe sign", "apply MJ's fact-check", or fix a timestamp, even if he doesn't say "skill". Research, build sheet, thumbnail, MJ review and release skills plug into it. The declassified, pop-up and motion-cards styles apply only when Joe names them.
---

# OGX Motion Documentary: the base OGX film skill

This is the **default way OGX films are made**. It turns an OGX script into a finished, mastered documentary and then carries it through Joe's notes and MJ's fact-checks.

The reference build is **Adwa, 1896**:
- 10:46 long, 115 lines;
- 54 animated AI clips;
- 12 music cues;
- real maps;
- a subscribe badge.

Its latest reviewed state is **v1.5**, with the MJ fact-check applied.

- `scripts/` holds the working code from that build. Copy it into a fresh project folder and adapt it rather than rewriting; `scripts/README.md` says what each file does and which parts are Adwa-specific.
- `references/` holds the detail. Read each file when you reach its step.

Joe (the owner) is a disabled quadruple amputee who reviews on his phone. Keep updates short and numbered. Send the **720p review copy**, the production pack and the SRT; he watches and replies with timestamps.

## Creative originality (MJ correction, 22 Oct 2026; overrides creative defaults below)
Adwa 1896 v1.5 is a **quality benchmark and a reusable technical pipeline**. It is **not** a template for story, shot order, visuals, pacing or maps. Eden note: "OGX — Creative originality correction to Adwa motion skill · 22 Oct 2026".

**Treat as examples only:**
- the numbers in this skill: the 0.6 / 0.8 / 1.8 s gaps, the ~2:00 subscribe badge, one cue per act, map-per-manoeuvre;
- Adwa's devices: the "Have a look at this picture…" opener, the "artist wasn't there" beat, the THE QUESTION card, "This is the story of X", numbered parchment acts, the "It won because… Because…" recap and the callback ending.

**Keep as standards:**
- the evidence and rights ledgers;
- reconstruction labels;
- Joe's voice;
- motion QC;
- readable real maps where the geography matters;
- OGX type and colour;
- loudness;
- private preview and MJ QC.

**For every new film or re-edit:**
1. Start from the episode's own question, evidence and narrative spine. Find its strongest true moment, and decide whether it's a battle-in-a-day, a biography, an object mystery or a trade route.
2. **Write the story treatment before building any visual timeline.** It covers the question, spine, point of view and the ending. Let the history shape the film, not the production code. When re-ordering existing lines, check every join, and check what each new juxtaposition implies.
3. Before full render, write a **creative differentiation note**: what this film does differently from Adwa and from the previous OGX film in its hook, structure, visual grammar, map use, sound, emotional arc and ending.
4. Review the first 60–90 s and a middle section against Adwa. Reject disguised reskins.

Example audit: `ogx-films-and-scripts/films/isandlwana-1879/docs/OGX_Isandlwana_1879_v1.0_creative_divergence_audit.md`.

## Pipeline position (this skill is the hub)
1. `ogx-research-pdf-script` → research, a claim ledger and the first script. If no researched script exists, run it first. Never voice unverified claims.
2. `ogx-video-build-engine` → build sheet (scene plan). Optional: this skill can plan scenes itself from the script.
3. **This skill** → the actual film:
   - voice, pictures, maps, motion, score, render and QC;
   - every revision round (v1, v1.1, …).
4. `mj-editorial-review` → MJ's fact-check and editorial review. Apply its brief here (see "Applying a fact-check brief").
5. `ogx-thumbnail-engine` → thumbnail and titles.
6. `mj-release-readiness` → release checks.
   - Publishing or scheduling happens only after Joe approves, and never from this skill.
   - `ogx-weekly-film` covers the weekly cadence, Shorts and posting pack.
   - Its long-form build should follow this skill.

**Alternative visual formats.** `ogx-declassified-receipts`, `ogx-popup-overlays`, `ogx-motion-cards`, `ogx-motion-sections` and `ogx-background-plates` cover the gold-on-near-black "declassified" slide style. Use them only when Joe asks for that style. Otherwise this skill's illustrated, animated, map-led style is the default.

## Standing rules (Joe's governance)
These are not optional. Each one comes from a real correction.

- **Private preview only.** Never upload, schedule or publish anywhere. Joe alone approves release.
- **Spending needs approval.** Before generating anything that costs credits, say what it is and roughly how many credits.
  - Joe approved Higgsfield for motion.
  - ElevenLabs video was rejected: about 43k credits per clip.
  - Exception: a re-do of one flawed clip inside an approved batch is fine. Report it afterwards.
- **Never overwrite a delivered version.** Each round is v1, v1.1, v1.2 and so on. New outputs get new filenames, and old masters stay untouched.
- **Facts:**
  - No invented quotes, dialogue, numbers, routes or dates.
  - Contested items are framed in the line itself ("by most accounts", "estimates run from", "some accounts").
  - Avoid "never colonised" and "first African victory over Europe".
  - Keep separate events apart (e.g. 1896 vs 1935).
- **Pictures:**
  - No AI faces of real, named people. Use archive portraits for them.
  - AI figures stay anonymous, with no close-up faces.
  - No fake documents, flags, insignia or readable text in AI images.
  - Every AI shot is tagged on screen: "AI RECONSTRUCTION, ANIMATED · ILLUSTRATIVE, NOT A RECORD".
- **Privacy.** No private IDs or links in anything public-facing.

## New film: work in gates (MJ's next-film prompt v0.1)
Each new film runs through these gates in order. Stop at each review gate. This is how to get a strong first cut with fewer voice patches. The full prompt is in `references/next-film-prompt-v0.1.md`.

0. **Check existing work first.**
   - Read the Eden board, the episode research and the OGX standards. Reuse any relevant preparation.
   - Never touch existing releases or other films' files.
1. **Pre-production pack, before any recording. Then STOP for MJ review.** The pack contains:
   - a **source-linked claim ledger**: every claim, its source, the framing used, and its status;
   - **clean narration** in Joe's voice-bible style;
   - a **pronunciation list**: name, respelling and source;
   - a **scene plan**: one picture per line, plus maps and motion;
   - an **asset ledger draft** with candidate archive images.

   Check these before writing a single line as fact:
   - dates and chronology;
   - troop and casualty figures, kept as ranges;
   - disputed explanations, attributed to whoever holds them;
   - **winning the battle vs winning the war**.

   Include African perspectives, and say where colonial accounts are limited. Remove unsupported certainty. This is where the Adwa v1.5 fixes should have happened, so do them now.
2. **Proof sequence, 45–60 s. Then STOP for Joe and MJ.**
   - It combines narration, one readable map, authentic archive evidence, and one illustrative action shot.
   - The action shot needs **movement inside the scene**: people, equipment, smoke or terrain. Camera zooms alone don't count.
   - This proves the voice, grade, map legibility and motion before full spend.
3. **Full build.** This is the pipeline below.
4. **Delivery** (all of these, every time):
   - review MP4 and SRT;
   - the **editable project** (timeline.json plus the build folder, with separate narration, music, effects and caption tracks);
   - voiced script;
   - claim and asset ledgers;
   - change log;
   - **3 title options**;
   - **2 thumbnail concepts**;
   - **1 self-contained Short**.

   Verify that every shared link opens and the actual video is present.
5. **QC statement.** Check the complete export:
   - picture and audio duration match;
   - no clipped words;
   - pronunciation;
   - music balance;
   - caption timing;
   - the ending.

   Say exactly what was inspected. Keep **"rendered"**, **"QC passed"** and **"Joe approved"** as three separate states. Never merge them.
6. **Learning log.** After the film, record:
   - factual corrections needed after recording;
   - visual rework;
   - actual cost;
   - missing deliverables.

   Then update this skill and the prompt from those results.

**Creative rules for every new film:**
- **Opening:**
  - Establish the battlefield, the stakes and the central question immediately.
  - Show **meaningful evidence within 30 s**, and start answering within the first minute.
  - No long geography lesson up front.
- **Viewer promise:** explain how the African side achieved the outcome. Give their decisions and organisation proper weight, rather than turning the story into a list of European mistakes.
- **Length:** aim for about 9–12 min, but only as long as the evidence supports.
- **Look:** keep Adwa's warm gold landscapes, archive textures, dark backgrounds and clear terrain maps. Take the storytelling pace from Joe's longer Benin film.
- **Visual accuracy:**
  - Verify clothing, weapons, landscape and formations. Label reconstructions.
  - Never use feature-film scenes as evidence, and never copy their compositions.
  - Maps must separate documented movements from approximate interpretations.
- **Phone first:** one main point per screen, and test essential labels at phone size. Keep full source details in the ledger and description; on screen, use short readable credits.
- **Spend:** use only existing approvals. Report any additional cost **before** incurring it.

## The build, step by step
Work in a scratch project folder, one subfolder per version (`v13/`, `v14/` …). Symlink shared assets instead of copying them.

1. **Script file** (`scripts/script_v06.py` is the format).
   - `ACTS` is a list of `(act_no, act_title, [(line, vis, on_screen_text), ...])`.
   - `vis` is one of:
     - `('arch', key, crop)`
     - `('ai', key)`
     - `('map', name)`
     - `('card', kicker, text)`
     - `('title',)`
     - `('endcard', ...)`
   - `V2 = {line_no: vis}` adds a second picture partway through a long line.
   - `VOICE_SUBS` holds pronunciation respellings used in the voice prompt only (e.g. "OrigineX" → "Origin-ex").
   - Default to **one picture per line**: images, not text cards. Joe wants "more images, fewer cards". Keep at most about 3 text cards per film, for the big rhetorical beats only.
2. **Voice.** Read `references/audio.md`.
   - Voice is ElevenLabs **"joe afrian british 1"**, `eleven_multilingual_v2`, in Joe's voice-bible style: conversational British, "Have a look at this…".
   - Record one continuous take per act.
   - Split the takes into lines using Scribe word timings, cutting at the quietest point of each pause.
   - Check that the words match the script.
3. **Pictures.**
   - Archive: public-domain sources (Commons, LoC, Gallica). Log each one in the rights ledger, with original source, date, creator, licence and exact credit, and give it a credit strip on first use.
   - AI stills: house engraving style (`references/house-style.md`), one generation each, and check every one on a contact sheet.
4. **Maps.** These are real data, not drawings:
   - AWS Terrain Tiles relief;
   - Sentinel-2 true colour;
   - Natural Earth borders, labelled "MODERN BORDERS SHOWN";
   - battle arrows labelled "MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE".

   For phone readability:
   - type ≥ 40 pt on dark plates;
   - one movement at a time;
   - persistent unit names;
   - a legend.

   See `scripts/geomap.py`.
5. **Motion.** Animate every AI still on Higgsfield. Read `references/higgsfield-motion.md` first, because the network workarounds are not obvious.
   - Write one motion line per still (`scripts/motion_prompts.py`) and append the STYLE lock.
   - Clip length must cover every line the still is used for. Where a still repeats, play a different stretch of the clip each time.
   - QC start, middle and end frames for warping and invented lettering. Regenerate any that fail.
6. **Timeline** (`scripts/timeline.py`).
   - Spacing between lines: 0.6 s lead-in, 0.8 s gap, 1.8 s at act changes, `HOLDS` for deliberate beats, and an 8 s end tail.
   - Each shot stores `vo_file`, `vo_at`, `words`, `vis`, and for second pictures `vis2` + `switch`.
   - The second-picture cut lands on a word boundary near the middle of the line. Pick the cut so the picture changes when the line names the new subject (see lessons).
7. **Score.** Write one instrumental cue per act, matched to its mood, using `eleven_music_v2_5` with the instrumental setting. Mix with `scripts/mix.py`:
   - voice chain;
   - music ducked −11 dB under the voice;
   - silence under the question card;
   - master at −14 LUFS / −1.5 dBTP.
8. **Captions.** `scripts/captions.py` builds the EN-GB SRT from the timeline words.
9. **Render** (`scripts/render.py`, `render_all.sh`).
   - Output is 1920×1080 at 24 fps.
   - Ken Burns moves on stills; animated clips play through `ClipReader`.
   - Overlays: act headers, on-screen text, AI tag, credit strips, wordmark, subscribe badge.
   - Render in 32 segments with `.ok` markers, 4 in parallel. It is resumable, because cloud workers can restart and kill background jobs.
   - Before any full render, check stills first with `python3 render.py still <t1> <t2> ...` and look at them.
   - **Optional HyperFrames stings** for the title and question cards. Build them as HTML + GSAP and render them locally with the `hyperframes` CLI. See lessons → Isandlwana for the route (local gsap, `hf_clip()` hook).
   - **Map check:** look at the busiest battle frame as a still. Place labels must be drawn last, on plates.
10. **Finalize** (`scripts/finalize.sh`).
    - Concatenate the segments, mux the audio (AAC 320k), and make the 720p review copy.
    - QC checks: streams, blackdetect, ebur128 loudness, md5.
    - Update the version names inside the script first.
11. **Production pack** (markdown):
    - what changed from the last version;
    - what was built;
    - chapters;
    - claim ledger;
    - picture and rights ledger;
    - spend;
    - draft posting pack;
    - known limitations.
12. **Deliver.** Send the 720p review MP4, the SRT and the pack. The full master is about 700 MB, so mention it rather than sending it unless asked. On request, put the text docs in the Drive review folder and an Eden review note. The video goes into Drive by Joe from the chat download, because it's too large for the connector. Then wait for Joe's timestamped notes.

## Fixing a round of notes
Joe's notes come as timestamps.

1. Map each timestamp to its shot from `timeline.json` (start/dur).
2. Back up `timeline.json` first.
3. Make the edit.
4. If total duration is unchanged, segment boundaries are unchanged. Delete only the affected `parts/sN.ok` and `.mp4` files and re-run `render_all.sh`. Segment length is `Q = ceil(N/32)` frames, so a shot at time t is in segment `floor(t*24/Q)`.
5. If the voice changed, re-run `mix.py` and `captions.py`.
6. Finalize under the next version name.
7. Check frames at each fixed timestamp before sending.

## Applying a fact-check brief (MJ)
When MJ or Joe hands over a fact-check, apply it to the **latest** edit, matching passages by wording rather than old timestamps.
1. Map every flagged claim to its shot.
2. Write replacement wording in Joe's voice that follows the brief's suggested text. Never add new unsourced detail. If a claim can't be sourced, cut it.
3. Re-voice all changed lines in one take and patch them in (`scripts/split_patch.py`, `scripts/patch_timeline.py`).
4. Fix the on-screen captions and the picture/rights items.
5. Retime everything together and do a full render.
6. Deliver:
   - review video;
   - final script;
   - SRT;
   - change log (old / new / final timecode / source);
   - updated claim and asset ledgers;
   - a "still unresolved" list.

   The film isn't "ready for release" while any item on that list is open.

## House look (summary; full spec in `references/house-style.md`)
- Palette: deep green `#152121`, gold `(201,164,92)`, cream `(239,230,210)`, lime accent `(170,255,70)`, used only on the subscribe rim.
- Fonts: Cinzel for titles, Lora for body text. Cinzel has no "→" glyph, so use an en dash "–".
- **Subscribe badge:**
  - glass black with a gold rim, a gold play tile, "SUBSCRIBE" and "ORIGINEX HUMAN ARCHIVES";
  - slides in at about 2:00 for 3.8 s, bottom right;
  - the lime rim flashes 3 times at alpha 0.6: "just enough to catch the eye, not too bright".
  - The same badge sits on the end card under "If this record is worth keeping,".
- Sign-off is voiced "OR-ih-jin-EX", but on screen it stays "OrigineX".

## Lessons from Adwa and Isandlwana (read `references/lessons.md` before starting)
These are Joe's and MJ's corrections, round by round. Re-read them before each new film, so the same notes don't come back.
