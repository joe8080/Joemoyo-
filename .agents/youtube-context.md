# YouTube Context

> Created by Claude for the AI Finance Toolkit channel. Last updated: 2026-07-25.
> This file is read by all `/yt-*` skills. Keep it current.
>
> **⚠ PARTIAL DRAFT.** Everything marked `[NEEDS INPUT]` is something only Joe can
> answer — subscriber counts, cadence, competitors, targets. Fill those in and
> delete this banner. The skills work on the drafted sections meanwhile, but their
> output will be generic until the gaps are closed.
>
> Drafted from what's verifiable in the repos: the `ai-finance-toolkit-website`
> copy, the `youtube-content-pipeline` skill, and the Own-Price engine build.

## Channel Overview

- **Channel Name:** AI Finance Toolkit
- **Niche:** Transparent, data-backed market analysis — building and stress-testing
  real valuation models on camera, rather than delivering opinions.
- **Subscribers:** [NEEDS INPUT]
- **Publishing Cadence:** [NEEDS INPUT]
- **Channel URL:** [NEEDS INPUT]

## Target Audience

### Primary Viewer

- **Who:** UK-centred retail investor, roughly 25–45, numerate and employed, already
  holding positions (ISA / Trading 212 / general brokerage) and dissatisfied with
  tip-led content.
- **What They Want:** To value a company themselves and know *why* the number is
  what it is — not to be told what to buy.
- **Where They Are:** Intermediate. Comfortable with a spreadsheet, shaky on DCF
  mechanics, terminal value, and where discount rates come from.
- **Why They'd Subscribe:** Every video hands over the actual working model and
  shows the assumptions that move the answer.

### Viewer Psychology

- **Pain Points:** Finance content is either too basic (index funds, budgeting) or
  a black box ("my model says $40"). Price targets appear with no visible working.
  They suspect most retail analysis is reverse-engineered from a conclusion.
- **Aspirations:** To form an independent view they can defend, and to stop
  outsourcing conviction to strangers.
- **Content Triggers:** Being shown a mistake ("this cell was lying to you"),
  seeing a confident number collapse under a changed assumption, getting a real
  tool rather than a summary.

## Positioning

### Unique Angle

The channel shows its own model breaking. Most finance channels present a finished
number; this one opens the workbook, finds the bug, changes the assumption that
moves the answer most, and reports how much of the thesis survives. The deliverable
is a working file the viewer edits, not a conclusion they accept.

Second differentiator: it's AI-operated end to end — research, scripting, voice and
render — and says so. That's a content pillar in itself, not a thing to hide.

### Competitive Landscape

| Channel | Their Angle | Your Differentiation |
|---------|-------------|---------------------|
| [NEEDS INPUT] | | |
| [NEEDS INPUT] | | |
| [NEEDS INPUT] | | |

> Name 3–5 channels you actually watch in this space. `/yt-title-craft` and
> `/yt-hook-writing` both lean on this table, and neither can do positioning work
> without it.

## Content Pillars

> Drafted from the work so far. Percentages are a proposal, not a finding.

| Pillar | % | Description | Example Topics |
|--------|---|-------------|----------------|
| Build the model | 40% | Long-form, screen-led walkthroughs of a real valuation engine on a real company. Viewer leaves with the file. | Own-Price engine on enCore; DCF from scratch; building a discount rate |
| Break the model | 25% | Stress-testing: which assumption actually carries the valuation, and what kills the thesis. | "Every year is cash-flow negative"; shared-lever traps; terminal value method swings |
| Read the filing | 20% | Extracting the handful of numbers that matter from a 10-Q/10-K and getting them into the model. | Finding real share count; convertibles and net cash; resource statements |
| Run it with AI | 15% | How the channel itself is operated — agents, skills, automation. Honest about failures. | Cloned-voice narration; agent research pipelines; what AI gets wrong in finance |

## Video Format

- **Primary Format:** Screen-led. Animated recreations of the workbook (rendered,
  not screen-recorded) with voiceover. No face.
- **Target Length:** 12–18 minutes for build/break pillars; 6–9 for filing reads.
- **Style:** Polished, measured, sceptical. Teaching a peer. Dark UI, cyan/gold.
- **Batch Recording:** N/A — narration is TTS in a cloned voice, so scripts batch
  rather than recordings.

### Production stack

- **Script:** `/yt-script-structure`, `/yt-hook-writing`, then the
  `humanise-writing` skill and the banned-AI-language sweep.
- **Voice:** vidIQ `vidiq_voiceover_generate`, voice `JKDjSisy3uHa5eqQYalW`
  ("Joe OGX"). Chunk scripts to ~1,200 chars — the tool times out above ~1,500.
- **Music:** vidIQ `vidiq_generate_music`, 180s max, looped with crossfades.
- **Render:** HyperFrames, generator-driven (`build.mjs` scene table → HTML → MP4).
- **Packaging:** `/yt-title-craft` + vidIQ thumbnail tools.

> **Do not use Higgsfield or HeyGen for audio/images in the cloud session** — both
> deliver to CDNs the egress policy blocks. vidIQ's S3 delivery works.

## Goals

### 12-Month Targets

- **Subscribers:** [NEEDS INPUT]
- **Views per Video:** [NEEDS INPUT]
- **Watch Time Retention:** [NEEDS INPUT]
- **CTR:** [NEEDS INPUT]

### Primary CTA

Download the model shown in the video. Every build video ships its workbook — that
is the channel's core promise and its list-building mechanism.

### Secondary CTA

Reply with the company to point the engine at next. Cheap engagement, and it
sources the next video.

## Hard rules

1. **No fabricated numbers.** Every figure on screen traces to a cell or a filing.
   No invented metrics, no illustrative-but-fake figures.
2. **No price targets presented as fact.** The phrase is always "on your
   assumptions".
3. **Show the bug.** When the model is wrong, that's the video, not an edit.
4. **Not financial advice** — and structure the content so that's obviously true
   rather than a disclaimer bolted on the end.
