---
name: ogx-code-film
description: Build an OrigineX Human Archives (OGX) history film entirely in code (Remotion): maps, battle diagrams, evidence cards, counters and word-timed captions, driven by Joe's narration. Use for any OGX film that should be made without AI image or video generation. The AIFT finance template (aift-explainer-v2) is separate and must not be changed.
---

# OGX code film

A copy of the AIFT explainer method, re-cut for history. Same engine (Remotion, word-timed cues), different look and rules.
Kit and episodes live in `ogx-films-and-scripts/code-film/`. First episode: Dahomey / Cotonou 1890 (`episodes/dahomey`).

Joe is a disabled quadruple amputee. Keep his touchpoints to a few taps, numbered, voice-friendly. Deliver results, not commentary.

## What makes it OGX (not AIFT)

1. **Every scene states how we know.** Bottom-left tag plus a source line: PRIMARY ACCOUNT, ONE WITNESS, ONE SOURCE, DISPUTED, ACCORDING TO <name>, ESTIMATE, DIAGRAM, LATER IMAGE, MUSEUM RECORD, CONTEXT.
2. **Nothing invented.** No AI faces, no fake documents, no generated objects. A picture we cannot show becomes a catalogue card that says what it is, who made it, when, and what it cannot prove.
3. **Maps are real data.** Coastlines and borders from Natural Earth (`make_geo.mjs`). Battle layouts are schematics and say so on screen ("not to scale").
4. **Disagreement is shown, not settled by headcount.** Put the accounts side by side and say what is disputed.
5. **A new visual reason to keep watching every 5–15 seconds**, landing on the spoken word.
6. **Look:** warm near-black, gold, cream; Cinzel caps, Source Serif body, Plex Mono labels; film grain. Palette is `C` in `kit.tsx`.
7. **Mobile first:** hero numbers 120 px or more, body 36 px or more, captions on.

## Workflow

1. **Script** → `data/<ep>/script.json`: one entry per narration line `{id, sec, text, cues}`.
   Cues are **phrases from the line**, not seconds. A cue fires on the first word of its phrase, so nothing needs re-timing by hand.
2. **Voice.** Either:
   - existing narration (a film's audio or a recorded take): save as `audio/<ep>/narration.wav`, or
   - new ElevenLabs takes in Joe's approved voice (ask before spending credits), joined into one file.
3. **Word timings:** `pip install --break-system-packages faster-whisper`, then `python3 data/words.py <ep> audio/<ep>/narration.wav`.
4. **Timeline:** `python3 data/build_timeline.py <ep>`. With `words.json` present it aligns every script word to the voice.
   Without it, it estimates (add a target length in seconds) so scenes can be designed before the voice exists.
5. **Scenes:** `remotion/src/episodes/<ep>/scenes*.tsx`, one component per line id, mapped in `Video.tsx` with its tag, source line and chapter chip.
   Kit pieces: `Fade`, `Pop`, `Count`, `Typed`, `Draw`, `Stamp`, `GeoMap` + `Pin`, `Figure`, `Rain`, `Palisade`, `Captions`, `SceneShell`.
6. **Check before rendering:** `npx remotion bundle src/index.ts --out-dir bundle`, then `STILLS=stillsN node stills.mjs <frames>` (one frame per scene at about 86% through), build a contact sheet and look at it. Fix overlaps and wraps. New stills folder each round.
7. **Render:** `(nohup env OUT=out/<ep>_silent.mp4 CONC=4 node render.mjs > render.log 2>&1 &)`. About 13 minutes for 8:30 on 4 cores.
8. **Sound and mux:** narration at -14 LUFS, true peak -1.5 dBTP or lower; mux onto the silent render. If the narration already carries its music (taken from an older film), use it as is.
9. **Deliver:** 720p preview and 1080p master to Joe. Private until Joe approves. Record sources, credits and open checks in the film's docs folder.

## Rules carried over from OGX

- Private preview only until Joe approves release. Never overwrite a delivered version; use new version names.
- No spending without Joe's approval of the amount.
- UK English. No sensitive IDs or private links in public text.
- Label later images with their date. Human remains are never shown.
- Check every name spelling against the source before release (captions print them).

## Gotchas

- Remote sandbox cannot reach Wikimedia or Google Drive downloads; npm is reachable. Fonts come from `public/fonts` (Cinzel via `@fontsource/cinzel`).
- The Drive connector cannot download files over 10 MB. Route that worked for a 22 MB film (Dahomey, 17 Nov 2026): Zapier Google Drive "Retrieve File or Folder by ID" gives a temporary file link; `curl` it inside the Higgsfield sandbox; run the word timings and any cuts there; print the word timings back as text; upload the small audio (MP3, under 10 MB) with `media_upload`; Zapier "Upload File" copies it into Joe's Drive; then the Drive connector can download it here. Nothing is made public. Do not curl Drive or Higgsfield hosts from this container.
- `GeoMap` takes `k` = map units per screen pixel: 2.1 shows West Africa, 0.25 the Bight of Benin, 0.08 a single town. Pass the same `k` to `Pin` so labels keep their size.
- Captions sit at the bottom centre; keep scene text out of the lowest 170 px.

## Documentary mode (pictures, not just diagrams)
Joe's standard for an OGX film is a documentary look: full-frame pictures with lower thirds. A film made only of diagrams and cards was rejected on 17 Nov 2026 ("that doesn't look like documentary"). Default to this mode.

- Use `episodes/dahomey/doc.tsx` as the pattern: a `DOC` table gives each scene its pictures (`shots`, each with a move: in, out, left, right, up, down, tiltdown, or `frame` for a framed print) and overlays (`lower`, `big`, `quote`, `head`, `title`, `stamp`, `inset`, `chip`). Times are cue indexes, so everything follows the voice.
- Effects are code, not AI video: `rain`, `smoke`, `lamp`, and dust by default.
- Pictures go in `remotion/public/<ep>/` and stay out of git; list them and their sources in `data/<ep>/images.json`.
- Where to find pictures: the painted stills of an earlier cut are usually in Joe's OpenArt or Higgsfield history (search the prompts for place names); real period images are in the film's Drive folder, with a contact sheet that says which are cleared. Wikimedia Commons can be reached from the Higgsfield sandbox, not from here.
- Every painted still must carry the "RECONSTRUCTION" note; every real image "ARCHIVE" plus its source. Never show severed heads or human remains; crop or leave out.
- Keep maps and diagrams for the few lines that need them (routes, the order of an attack).
