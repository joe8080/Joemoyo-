# Film 2 v2 (Remotion)

"Five Questions Before You Invest in the AI Data Centre Buildout". Remotion 4 + React + three.js. 1920x1080, 30 fps, 4:29.

What's in it
- `src/Plate.tsx`    procedural 3D data hall (racks, blinking LEDs, fog, floor reflections), a 20 s seamless loop, rendered once to `plate.mp4`
- `src/Globe.tsx`    3D globe plotting the real 106-site register (pillar = planned MW gold, running MW teal)
- `src/Overlays.tsx` baked-plate background, header, status tracker, word-highlight captions, voice-reactive waveform
- `src/Scenes*.tsx`  the eight scenes (cold open, five questions, money map, so-what, close)
- `src/data/`        timeline.json (word + beat times from forced alignment), sites.json (from the Supabase `dc_site_register`, 9 Oct 2026)
- `audio/sound_design.py` synthesised bed + UI sounds keyed to the same beat times (no samples, all original)

How it was built
1. Voiceover v2 = v1 with the Question 1 paragraph re-recorded (fixes "two hundred" -> "two hundred and twenty percent").
2. `audio/palign2.py` + `anchors2.py` -> word/beat times -> `src/data/timeline.json`.
3. `npx remotion render src/index.ts Plate out/plate.mp4 --codec=h264 --crf=16` then bake the colour script (hue per status, bloom) with ffmpeg into `public/plate_baked.mp4` (see the command in the session notes).
4. `npx remotion render src/index.ts Film out/film_silent.mp4 --gl=angle --concurrency=4 --codec=h264 --crf=16 --muted`
5. `python3 audio/sound_design.py` then mix with ducking and mux.

Notes
- Headless shell path in `remotion.config.ts` is machine specific. `--gl=angle` is about 4x faster than swangle for these scenes.
- The colour script: the room turns amber/red/green with each question's status, matching the tracker chips.
- Not included in git: node_modules, plate videos, rendered mp4.
