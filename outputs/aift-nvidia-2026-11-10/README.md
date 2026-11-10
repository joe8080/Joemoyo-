# AIFT — Nvidia: the investigation, the sell-off and two crucial dates

Research snapshot: 10 November 2026, morning UK time. Not published.

## Status

The film is built and rendered as a **preview cut without narration**. The voice track could not be recorded: ElevenLabs rejected all 27 lines with "Your subscription has a failed or incomplete payment. Complete the latest invoice to continue usage." Nothing was charged.

Scene timing in the preview follows an estimated reading pace of about 145 words a minute. The final cut must be re-timed to the real voice and rendered again.

## Files

| File | What it is |
|---|---|
| `AIFT_Nvidia_preview_captioned_720p.mp4` | Review copy: captions burned in, music bed only |
| `thumbnail.jpg` | 1280×720 thumbnail, "WHAT CHANGED?" |
| `subtitles.srt` | Subtitles, timed to the preview cut |
| `final_script.md` | Narration script, 27 lines |
| `youtube_description.md` | Description with sources and chapters |
| `chapters.txt` | Chapter timestamps from the preview cut |
| `source_asset_ledger.md` | What was checked, what is calculated, asset rights |
| `production/` | Scene code, script with cue marks, timeline and audio scripts |

## To finish once the ElevenLabs invoice is paid

1. Generate the 27 lines in `production/data/script.json` with voice "joe afrian british 1", one take each, into `audio/raw/<ID>.mp3`.
2. Run `audio/process_vo.sh`, then `data/build_timeline.py`. It picks up the real durations and rewrites the timeline, subtitles and chapters.
3. Check stills, render, then mix to −14 LUFS and mux.
