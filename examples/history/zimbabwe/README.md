# Seed: Great Zimbabwe (history channel)

The episode that started this whole build. Reproduce it end-to-end with the
video production crew:

```bash
# Specs + package (no media keys needed)
python main.py produce --topic "Great Zimbabwe" --channel history_channel --minutes 12

# Full render (needs ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID, and an image provider)
python main.py produce -t "Great Zimbabwe" -c history_channel --render
```

What you get under `outputs/videos/history_channel_great-zimbabwe_<ts>/`:

- `research.md`, `script.md`, `narration.txt`
- `packaging.json`, `thumbnail.json`, `shotlist.json`, `motion.json`
- `manifest.json`, `captions.srt`, `remotion-props.json`
- `img/NN_*.png` + `narration.mp3` + `out.mp4` (when media keys are set)

Everything is also persisted to the **ORIGINEX HUMAN ARCHIVES** Supabase project
(`video_episodes` + related tables), linked to the archive's `people` / `events`
/ `places` / `civilizations` / `citations` so on-screen claims stay sourced.
Re-export any time with `python main.py materialize <episode_id>`.

## Notes from the original
- The "pops" were the Ken Burns zoom jumping at clip ends; the
  `ManifestEditorAgent` now clamps every clip to ≥ `2*crossfade + 0.5s`,
  and `video_agent/effects/ken_burns.py` clamps the final zoom frame.
