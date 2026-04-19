# video-agent

Turn a folder of images plus a narration track into a cinematic video with
Ken Burns (slow zoom/pan) motion, crossfades, captions, and a music bed.

Built as a single engine with **channel presets** so one codebase produces
great output for two very different shows:

| Channel               | Aspect | Pace          | Feel                                  |
|-----------------------|--------|---------------|---------------------------------------|
| `history`             | 16:9   | 7-10s / image | Cinematic, sepia-graded, documentary  |
| `finance.long`        | 16:9   | 3-5s  / image | Punchy, saturated, data-viz friendly  |
| `finance.short`       | 9:16   | 3-5s  / image | YouTube Shorts / TikTok / Reels       |

## Requirements

- Python 3.9+
- `ffmpeg` and `ffprobe` on `PATH`

```bash
# macOS
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get install -y ffmpeg
```

No Python dependencies are required at runtime.

## Install

```bash
pip install -e .
# or, for development
pip install -e ".[dev]"
```

## Usage

```bash
python -m video_agent \
    --channel history \
    --images ./examples/history/img \
    --audio  ./examples/history/narration.mp3 \
    --out    ./out/history.mp4
```

With music, captions, and a manifest:

```bash
python -m video_agent \
    --channel finance.short \
    --images   ./examples/finance/img \
    --audio    ./examples/finance/narration.mp3 \
    --music    ./assets/bed.mp3 \
    --captions ./examples/finance/script.srt \
    --manifest ./examples/finance/manifest.json \
    --out      ./out/finance_short.mp4
```

### Manifest format (optional)

```json
{
  "clips": [
    {"image": "01.jpg", "duration": 8.0, "pan": "left-to-right", "caption": "Rome, 49 BC"},
    {"image": "02.jpg", "duration": 6.5, "pan": "zoom-in",       "caption": "Crossing the Rubicon"}
  ]
}
```

If no manifest is given, image durations are auto-distributed across the
length of the narration audio.

## Flags

| Flag                       | Meaning                                                 |
|----------------------------|---------------------------------------------------------|
| `--channel`                | `history`, `finance.long`, `finance.short`              |
| `--images`                 | Folder of images (png/jpg/jpeg/webp)                    |
| `--audio`                  | Narration audio file (mp3/wav/m4a)                      |
| `--music`                  | Optional background music bed (ducked under narration)  |
| `--captions`               | Optional `.srt` subtitle file                           |
| `--manifest`               | Optional JSON manifest overriding per-clip settings     |
| `--out`                    | Output `.mp4` path                                      |
| `--fps`                    | Override channel default fps                            |
| `--seconds-per-image`      | Override channel default pace                           |
| `--seed`                   | Deterministic random seed for pan directions            |
| `--dry-run`                | Print the ffmpeg plan without executing                 |

## Tests

```bash
pytest
```

Unit tests cover the Ken Burns filter builder, transition math, manifest
parsing, and channel presets. They do not require `ffmpeg` to be installed.
