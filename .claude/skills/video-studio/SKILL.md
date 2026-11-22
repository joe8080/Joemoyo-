---
name: video-studio
description: >
  Make, edit and repair videos with the in-repo Studio engine (studio/). ALWAYS use when Joe asks to
  make a video, Short, Reel, explainer, captioned clip, "CapCut style" edit, animated captions,
  motion graphics, charts or stat cards on video, resize a video for another platform, add voice or
  music to visuals, or to fix/clean/repair bad audio or video (noise, hum, hiss, quiet, clipped,
  shaky, dark, grainy, washed out). Covers both channels: OrigineX history (brand "ogx") and UK
  finance/wealth (brand "wealth"), plus loud short-form (brand "bold").
---

# Video Studio

Script in, finished video out. You write one `project.json`; the engine does narration, captions,
camera moves, graphics, transitions, sound mix and export in every aspect ratio. Free and offline.

Full reference: `studio/README.md`. Working example: `studio/examples/demo/project.json`.
List every option: `python -m studio options` and `python -m studio voices`.

## The loop (follow in order)

1. **Set up once per machine:** `pip install -r studio/requirements.txt` (ffmpeg must be installed).
2. **Start:** `python -m studio new <folder> --brand ogx|wealth|bold`. Put media in `<folder>/assets/`.
3. **Write `project.json`.** One scene per idea: `say` (narration), `visual`, `overlays`.
4. **Check:** `python -m studio plan <folder>`. Fix every problem it lists. Read the timeline.
5. **Look before rendering:** `python -m studio frames <folder>` then open the contact sheet
   (`out/frames/*_sheet.jpg`) with the Read tool. Do it for each format (`--format 9:16`).
   Check: text fits, nothing collides with captions, pictures are framed well.
6. **Draft:** `python -m studio render <folder> --draft`. Fix what you see.
7. **Final:** `python -m studio render <folder>`. Long films: run in the background; if it is
   interrupted, run it again, finished scenes are reused.
8. **Deliver:** send the MP4s, the `.srt` and the chapters file. Say what is placeholder.

Never upload, schedule or publish anything without Joe's explicit "approve".

## Writing good projects

- Scenes are as long as their narration. Aim for 6-14 seconds each; split longer ideas.
- First scene is the hook: a question or bold claim, with a `title` overlay.
- One overlay idea per scene. A stat OR a chart OR bullets, not all three.
- Numbers: use `stat` for one big number, `chart` for change over time or comparison.
- Stills: leave `motion` out (auto cycles moves) or pick one. Use `focus: [x, y]` to keep a face
  or object in frame, especially for 9:16 crops of wide pictures.
- Video clips: `fit: "blur"` keeps the whole frame on vertical; `dim: 0.3` when text sits on top.
  `"sound": true` keeps the clip's own audio (gigs, interviews); set `"scrim": false` on a title
  that should not darken the footage.
- Captions: `pop` or `box` for Shorts, `clean` for documentaries. Turn off per scene with
  `"captions": false` (for example over a quote that is already on screen).
- Finance content is education only: keep the "not financial advice" line and label illustrations.
- OGX content: every stat verified first; contested claims carry a `label` with `tone: "alert"`.
- UK English.

## Getting assets (use what Joe already has)

| Need | How |
|---|---|
| Narration, free | default `piper` voice (offline). `python -m studio voices` |
| Narration, premium | ElevenLabs connector: generate speech, save to `assets/`, set scene `audio` or `voice.file` |
| AI stills / clips | Higgsfield or OpenArt connector: generate, download to `assets/`, reference in `visual` |
| Music | Joe's own tracks or the Artlist connector; set `music` to the file. `"ambient"` is a placeholder |
| Thumbnails | export a still with `frames --at <seconds>` and build on it |

Paid generations spend Joe's credits: ask before generating more than a couple.

With one narration file for the whole script, set `"voice": {"file": "assets/narration.mp3"}` and
give every scene its `say` text: scenes are cut to the spoken words automatically.

## Repairing bad audio or video

1. Diagnose: `python -m studio fix <file> --check`. Tell Joe what it found in plain words.
2. Repair: `python -m studio fix <file>` (add `--strength light|strong`, `--stabilize on|off`,
   `--upscale 1080`, `--no-audio` / `--no-video` to touch only one side). For live music or songs
   ALWAYS add `--music --lufs -14`: it rebalances harsh, thin phone-mic sound and skips voice
   clean-up (without it, loud music is mistaken for noise).
3. Read the before/after table it prints and report the numbers that changed.
4. The original is untouched; the result is `<name>_fixed.<ext>`.

Inside a project: `"fix": true` on a video `visual` repairs that clip before use, and
`"voice": {"clean": true, ...}` cleans narration files.

### Plugins (single jobs, chains, and Joe's own)

- List: `python -m studio plugins`. Run: `python -m studio plug <chain-or-plugins> <file>`.
- Gig or live-music sound: `python -m studio plug gig <file>` (tone match with the voice kept
  forward, gentle de-harsh, -14 LUFS). Joe chose this "voice forward" balance by ear on real
  footage after rejecting a smoother one that dulled the singer (`gig-smooth`): do not change it
  without a new ear test.
- Match a record he likes: `--set matchtone.ref=<track>`.
- Change one setting: `--set plugin.setting=value`. Stabilise without cropping: `steady` with
  `frame=full` (this is also the default inside `fix`).
- Joe's own plugins live in `studio_plugins/*.py`. To add one, copy `example_plugin.py`, write
  the maths, add a test, and run it on a real file before saying it works.
- Sound can only be judged by measurement here. For anything Joe will publish, make short
  level-matched options and let him pick by ear.

Be straight about limits: upscaling does not invent detail, clipping repair is weaker on already
compressed files, and a deliberately dark scene will be brightened unless you use `--strength light`.

## When something fails

- "Please fix these before rendering": the list names each scene and the valid options.
- A voice will not download: the machine is offline or the name is wrong; check `voices`.
- Edge voices need internet access to Microsoft's speech service; use `piper` otherwise.
- Odd look after an edit: `python -m studio clean <folder>` clears the cache, then render again.
