# OGX code film kit

Films built entirely in code (Remotion). No AI images or video. See the skill at `.claude/skills/ogx-code-film/SKILL.md`.

```
code-film/
  data/build_timeline.py     script + voice word timings -> timeline.json (or an estimate with no voice)
  data/words.py              word timings from a narration track (faster-whisper)
  data/<ep>/script.json      narration lines with phrase cues
  remotion/make_geo.mjs      West Africa base map from Natural Earth -> src/geo.json
  remotion/src/kit.tsx       OGX palette, fonts, motion helpers, map, captions, evidence tags
  remotion/src/episodes/<ep> scenes, scene map, timeline
  remotion/render.mjs        full render;  stills.mjs  spot frames for contact sheets
```

Setup: `cd remotion && npm install && node make_geo.mjs && npx remotion bundle src/index.ts --out-dir bundle`.

Episodes: `dahomey` (The Ghost Army of Dahomey, Cotonou 1890).
