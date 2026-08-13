# Voice Generator

Clone your own voice and turn scripts into finished narration — including
two-host podcast dialogue — using [VibeVoice](https://github.com/vibevoice-community/VibeVoice),
an open-source (MIT) long-form speech model.

Feeds directly off `ScriptWriterAgent` output: write the script with the agent,
run it through here, get a WAV you can drop straight into the edit.

## What it does

- **Voice cloning** from a 15-25 second sample of you talking
- **Two-host dialogue** — you and a second voice, with natural turn-taking
- **Long-form** — up to ~90 minutes in one pass, no per-line stitching
- **Script cleanup** — strips markdown, headers, and `[B-ROLL]` style stage
  directions so production notes never get read aloud

## Where it runs

VibeVoice is a diffusion model and needs a GPU in practice.

| Option | Setup | Notes |
|---|---|---|
| **Google Colab** | `notebooks/VibeVoice_Colab.ipynb` | Free T4 is enough for the 1.5B model. Start here. |
| **Local NVIDIA GPU** | `bash voice/setup.sh` | Needs ~7 GB VRAM (1.5B). An RTX 3060 or better. |
| **Apple Silicon** | `bash voice/setup.sh` | Runs on Metal (`mps`). Slower than CUDA but usable. |
| **Rented GPU** | `Dockerfile` | RunPod / Vast.ai, roughly $0.30-1/hr while running. |
| **CPU** | `bash voice/setup.sh --cpu` | Works, but far slower than real time. Testing only. |

## Quick start

```bash
# 1. Install (clones VibeVoice into voice/vendor/, installs deps)
bash voice/setup.sh

# 2. Make a voice sample for each speaker
python voice/prepare_voice.py --input me_talking.mp4 --name Joe  --gender man
python voice/prepare_voice.py --input cohost.wav    --name Maya --gender woman

# 3. Generate
python voice/generate.py --script voice/scripts/example_2p.txt --voices Joe Maya
```

Output lands in `voice/outputs/`.

## Script format

Speaker 1 gets the first name in `--voices`, Speaker 2 the second:

```
Speaker 1: In 1961, a plane went down over Northern Rhodesia.
Speaker 2: And the official verdict at the time was pilot error.
Speaker 1: Pilot error. That was the finding.
```

Named labels work too — `JOE:` and `MAYA:` are mapped to Speaker 1 and 2 in
order of first appearance. Plain prose with no labels is treated as a single
narrator. Check how any script will be interpreted before spending GPU time:

```bash
python voice/generate.py --script draft.txt --voices Joe Maya --dry-run
```

## Options

| Flag | Default | What it does |
|---|---|---|
| `--voices` | required | Voice names in speaker order, max 4 |
| `--model` | `1.5b` | `1.5b`, `7b`, or any HF/local path |
| `--cfg-scale` | `1.3` | Higher = more expressive, less faithful to the sample |
| `--chunk-chars` | `6000` | Splits long scripts, then joins the audio. `0` disables |
| `--device` | `auto` | `cuda`, `mps`, or `cpu` |
| `--seed` | none | Fix for a reproducible take |
| `--raw` | off | Keep markdown and bracketed notes instead of stripping them |
| `--dry-run` | off | Show the parsed script and exit |

## Getting a good result

The voice sample matters more than any flag. 15-25 seconds, one speaker, no
music, no echo, delivered in your actual narration voice — a flat sample gives
you a flat episode.

After that, `--cfg-scale` is the main dial: raise it toward 2.0 if delivery is
monotone, drop it toward 1.1 if the voice warbles or drifts. Punctuation drives
pacing, so write full stops where you want breaths.

## Models

| Model | Speakers | Max length | VRAM |
|---|---|---|---|
| `1.5b` | 4 | ~90 min | ~7 GB |
| `7b` | 4 | ~45 min | more than a free T4 has |

Weights download from Hugging Face on first run and cache locally.

## Limitations

- **English only** in practice. Chinese exists but is unstable; other languages
  are not supported.
- **No singing**, no sound effects, no background music — speech only.
- **Not transcription.** This generates audio from text. For the reverse
  (audio to transcript/subtitles) you want Whisper — separate tool.

## Licence and consent

The code and model weights are MIT-licensed. Microsoft published VibeVoice in
August 2025 and withdrew the repository that September after finding misuse;
because the release was MIT, the community fork this project uses is a legal
preservation of that code.

That history is the reason for the obvious rule: only clone a voice you own or
have written permission to use. If you add a second host, get their consent
before you publish anything generated here. Voice samples in `voice/voices/`
are gitignored — they are biometric data, so keep them out of the repo.
