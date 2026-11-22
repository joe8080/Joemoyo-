# Studio

A video engine Claude can drive from start to finish: script in, finished captioned video out.
It also repairs bad audio and video. Everything runs free and offline (ffmpeg + Python);
paid tools (ElevenLabs, Higgsfield, Artlist) plug in as assets when you want them.

## What it does

1. **Makes videos from a script.** One project file becomes 16:9, 9:16, 1:1 and 4:5 videos with:
   narration, word-by-word captions, camera moves on stills, video clips, titles, count-up stats,
   animated charts, quotes, bullet lists, name plates, transitions, music that dips under the voice,
   sound effects, subtitles (.srt) and YouTube chapter times.
2. **Repairs footage and recordings.** Hiss, hum, clipping, a dead channel, uneven or quiet audio;
   shaky, dark, flat, grainy, colour-cast, interlaced or variable-frame-rate video.
   It measures first, fixes only what is wrong, then measures again and reports before/after.
3. **Three brand kits built in:** `ogx` (OrigineX gold on black), `wealth` (finance), `bold` (Shorts).

## Setup (once)

```bash
pip install -r studio/requirements.txt     # needs ffmpeg installed too
python -m studio demo                      # renders the 36-second example
```

## Commands

| Command | What it does |
|---|---|
| `python -m studio new my-video --brand ogx` | start a project folder |
| `python -m studio plan my-video` | check the project, print the timeline (fast) |
| `python -m studio frames my-video` | save one still per scene + a contact sheet |
| `python -m studio render my-video --draft` | quick half-size preview |
| `python -m studio render my-video` | final render, every format in the project |
| `python -m studio fix clip.mp4` | repair audio and picture, with a before/after report |
| `python -m studio fix clip.mp4 --check` | diagnose only |
| `python -m studio voices` / `options` | list voices / every style and setting |

Re-rendering after an edit only redraws the scenes that changed.

## Project file

```json
{
  "title": "The Boring Habit",
  "brand": "wealth",
  "formats": ["16:9", "9:16"],
  "voice": {"provider": "piper", "voice": "en_GB-alan-medium"},
  "captions": true,
  "music": "ambient",
  "scenes": [
    {
      "id": "hook",
      "chapter": "The question",
      "say": "What if getting rich had nothing to do with picking winners?",
      "visual": {"src": "assets/city.jpg", "motion": "push_in"},
      "overlays": [{"type": "title", "kicker": "Money, simply", "text": "The boring habit"}]
    }
  ]
}
```

A full working example is in `studio/examples/demo/project.json`.

### Top-level settings

| Setting | Values |
|---|---|
| `brand` | `ogx`, `wealth`, `bold`, or `{"base": "wealth", "accent": "#FF8800"}` |
| `formats` | any of `16:9`, `9:16`, `1:1`, `4:5` |
| `voice` | `{"provider": "piper" \| "edge" \| "none", "voice": "...", "speed": 1.0}`; or `{"file": "narration.mp3"}` for one recording of the whole script; add `"clean": true` to repair your audio first |
| `captions` | `true`, `false`, a style (`pop`, `box`, `clean`), or `{"style", "position", "scale", "color"}` |
| `music` | a file path, `"ambient"` (built-in placeholder bed), or `{"file", "level_lufs": -22, "duck_db": -11}` |
| `grade` | `none`, `cinematic`, `warm`, `cool`, `noir`, `archive`, `vivid` |
| `finish` | `{"grain": 0.08, "vignette": 0.2, "crf": 18}` (0 turns grain or vignette off; more grain means much bigger files; lower crf means higher quality and size) |
| `progress`, `watermark` | progress bar along the bottom; small corner text |

### Scene settings

| Setting | Meaning |
|---|---|
| `say` | narration text; also drives the captions |
| `audio` | your own narration file for this scene (instead of the built-in voice) |
| `visual` | image or video path, a card name (`gradient`, `grid`, `spotlight`, `solid`), or an object: `{"src", "motion", "focus": [x, y], "grade", "dim", "fit": "cover" \| "blur", "start", "speed", "loop", "fix": true, "sound": true}` (`sound` keeps a video clip's own audio, e.g. live music) |
| `overlays` | list of graphics (below) |
| `transition` | `cut`, `fade`, `dip`, `flash`, `zoom`, `slide_left/right/up/down`, `wipe_left/right` |
| `duration` | minimum length in seconds (scenes are otherwise as long as their narration) |
| `sfx` | `whoosh`, `impact`, `pop`, `riser`, `tick`, or `{"file": ..., "at": 1.2}` |
| `chapter` | name for the YouTube chapter list |

Camera moves for stills: `auto`, `push_in`, `pull_out`, `pan_left/right/up/down`, `drift`, `punch`, `static`.

### Overlays

Every overlay takes `at` (seconds into the scene) and optionally `for` (how long it stays).

| Type | Settings |
|---|---|
| `title` | `text`, `kicker`, `sub`, `pos`: `center` / `upper` / `lower` |
| `stat` | `value` (counts up), `prefix`, `suffix`, `decimals`, `label`, `sub` |
| `chart` | `kind`: `line` / `bar`, `title`, `data`: `[["label", value], ...]`, `prefix`, `suffix`, `draw` (seconds) |
| `bullets` | `title`, `items`, `numbered`, `every` (seconds between items) |
| `quote` | `text`, `by` |
| `lower_third` | `text`, `sub` |
| `label` | `text`, `corner`: `tl` / `tr` / `bl` / `br`, `tone`: `accent` / `alert` / `muted` |
| `text` | `text`, `x`, `y`, `size`, `role`, `color` |
| `image` | `src`, `x`, `y`, `width`, `frame`, `rotate`, `opacity` |

## Narration options

| Option | Cost | Notes |
|---|---|---|
| `piper` | free, offline | British and American voices; downloads each voice once (about 60 MB) |
| `edge` | free, online | Microsoft neural voices with exact word timing; needs internet |
| your audio | whatever you paid | ElevenLabs exports, recordings; per scene (`audio`) or one file (`voice.file`) |
| `none` | free | silent draft timed by reading speed |

Captions for your own audio use Whisper for word timing when `faster-whisper` is installed,
and a phoneme-weighted estimate otherwise.

## Repair tool

```bash
python -m studio fix interview.mp4                 # normal strength
python -m studio fix interview.mp4 --strength strong
python -m studio fix voiceover.wav --lufs -16
python -m studio fix clip.mp4 --stabilize on --upscale 1080
python -m studio fix gig.mp4 --music --lufs -14    # live music: rebalance harsh/thin phone sound, no voice clean-up
```

The original file is never changed; a `_fixed` copy is written next to it.

## Plugins

Small single-purpose processors you can chain, tune and extend.

```bash
python -m studio plugins                              # list every plugin, chain and setting
python -m studio plug gig clip.mp4                    # live music from a phone: tone, harshness, level
python -m studio plug gig-video clip.mp4              # the same plus full-frame stabilisation
python -m studio plug voice interview.wav             # hum, noise, level
python -m studio plug matchtone,level take.wav --set matchtone.ref=record_i_love.wav
python -m studio plug gig clip.mp4 --set deharsh.max_cut=8 --set level.lufs=-16
```

| Plugin | Kind | What it does |
|---|---|---|
| `matchtone` | audio | Matches tonal balance to a finished-mix target, or to a reference track (`ref=`) |
| `deharsh` | audio | Dynamic treble tamer: cuts harsh highs only in the moments they swamp the mids |
| `declip` | audio | Rebuilds clipped peaks (best on original, uncompressed recordings) |
| `dehum` | audio | Finds and notches 50/60 Hz mains hum |
| `denoise` | audio | Reduces steady noise and hiss under speech |
| `level` | audio | Sets loudness (LUFS) and keeps peaks under a ceiling |
| `steady` | video | Stabilises; `frame=full` keeps the whole picture, `frame=crop` zooms in slightly |
| `sharpen` | video | Crisps soft footage (cannot undo motion blur) |
| `fps` | video | Locks a wobbly frame rate, or smooths choppy footage (`mode=blend` / `flow`) |

Running a chain on a video leaves the picture untouched unless the chain has a video plugin,
and the sound stays exactly in sync.

### Your own plugins

Drop a `.py` file in `studio_plugins/` (next to the `studio` folder) or in `~/.studio/plugins/`.
It is loaded automatically and shows up in `python -m studio plugins`.
`studio_plugins/example_plugin.py` is a working template: one audio plugin (`warmth`) and one
personal chain (`joe-gig`).

## Limits worth knowing

- The upscale is a sharp resize, not AI detail invention.
- Clipping repair works best on original recordings (not ones already compressed to MP3/AAC).
- Brightness repair cannot tell a moody night scene from an under-exposed one: use `--check` first, or `--strength light`.
- The built-in `ambient` music is a simple placeholder bed. Use your own tracks for finals.
- No trained AI models are built in, so there is no motion deblur, no stem separation (pulling
  vocals or drums apart) and no AI upscaling. Those need tools like Topaz Video or iZotope RX.
- AI image and video generation is not built in; generate shots with your connected tools and drop the files into `assets/`.

## Tests

```bash
python -m unittest discover -s studio/tests -t .
```

Fonts in `studio/fonts` are open-licence (SIL OFL); licence texts are alongside them.
