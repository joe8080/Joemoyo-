# AIFT Video Playbook

The saved know-how for AI Finance Toolkit videos, so each film starts from what the last one learned.
The full working skill is `aift-motion-film` on Joe's computer. This file is the backup copy in GitHub.

---

## 1. The six-job system

Don't ask Claude for a whole video in one go. Split it into six jobs, one at a time:

1. **Script.** Study 3 videos in the niche that beat their channel's usual views. Save their hooks and formats to a library. Write the script in the same style.
2. **Cut.** Transcribe the raw voice with Whisper (word timestamps). Keep the last clean take of each line, cut the rest with FFmpeg, and list everything removed.
3. **Design.** Screenshot the edits you like and turn them into design rules. Build a **beat map** first (each idea, and what's on screen while it's said). One idea gets one graphic, and it stays up long enough to read.
4. **Build.** One subagent per section. Opus plans, Sonnet builds. **Max 4 renders at once.** Drafts render at half size. Full quality only after the cut is approved. Render overnight where possible.
5. **Check.** Claude checks frames for: animations that play twice, graphics that flash too briefly, text that lands too late to read, graphics over the subject, repeated words, and audio/lip drift.
6. **Learn.** After each cut, Joe gives notes. Claude fixes the video, then rewrites the skill rule that should have prevented each note.

Reuse assets (graphics, tools, templates) between films. That's what cuts the cost on every video after the first.

---

## 2. Lessons from the Yield Curve film (Oct 2026, v01 → v10)

### Grade: the values that work

v06 went muddy because four dulling changes were stacked at once. These are the corrected values:

| Setting | Bad (v06–v08) | Good (v09+) |
|---|---|---|
| Photo brightness | 0.46 | **0.60** |
| Saturation | 0.68 | **0.88** |
| Contrast | 1.06 | **1.10** |
| Sepia | 0.12 | **0.05** |
| Left scrim | .94/.72/.26/.44 | **.90/.60/.14/.30** |
| Top/bottom scrim | .86/.92 | **.74/.82** |
| Warm key light | gold at .10 | **gold-highlight at .15** |

### Rules

- **Change one grade setting at a time.** Each change can look fine alone and still go muddy when stacked.
- **Tint follows the plate.** If the photo gets brighter, raise the tint on any panel with small type.
  - Cards: **0.30** tint.
  - Charts and large panels with fine type: **0.52** tint.
  - Cards over the dark left scrim never need raising.
- **Check the brightest background at full size** before calling a grade done.
- Shine comes from the glass (gold gradient, bright inner top edge, faint bloom), not from brightening the text.

### Delivery spec

- 1080p30 upload master plus a 720p preview.
- Loudness **−14 LUFS**.
- Captions embedded. If timings change, re-export the `.srt` too, because an old `.srt` will be out of sync.
- Ship a **posting pack** (title, description, tags) and a **sources** file with every film.
- Delete superseded versions from Downloads so the wrong cut never gets uploaded.

### Pre-upload checklist

1. [ ] Photo credits pasted into the description (needed for CC-BY / CC-BY-SA images).
2. [ ] Only the current `.srt` is uploaded, or none at all if captions are embedded.
3. [ ] Joe listens to every voice join himself (Claude can't hear audio).
4. [ ] Every on-screen citation checked against its source.
5. [ ] Education-only wording, no personal advice (policy-safe).
