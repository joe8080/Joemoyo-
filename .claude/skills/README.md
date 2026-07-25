# Claude Skills

Skills committed to this repo so they travel with it — clone on any machine and
Claude Code picks them up automatically from `.claude/skills/`. No install step.

## HyperFrames (HeyGen)

Open-source "write HTML, render video" framework built for AI agents.
Source: https://github.com/heygen-com/hyperframes (Apache-2.0)

Start with `/hyperframes` — it's the router. Describe the video you want and it
picks the right workflow and loads the domain skills it needs.

### Workflows

| Skill | Use for |
|---|---|
| `/hyperframes` | Router — read first for any video request |
| `/product-launch-video` | Product promos, feature reveals, site tours |
| `/faceless-explainer` | Topic explainers built from text (no footage) |
| `/motion-graphics` | Short kinetic type, stat count-ups, logo stings |
| `/music-to-video` | Beat-synced lyric videos and promos |
| `/talking-head-recut` | Graphic overlays on existing talking-head footage |
| `/embedded-captions` | Captions/subtitles, plain or cinematic |
| `/pr-to-video` | GitHub PR → code-change explainer |
| `/slideshow` | Decks with presenter mode (not MP4) |
| `/general-video` | Multi-scene, sizzle reels, freeform builds |
| `/changelog-video` | Weekly changelog markdown → branded video |
| `/remotion-to-hyperframes` | Port a Remotion composition to HyperFrames |
| `/figma` | Pull Figma designs, tokens, components into a video |

### Domain skills (loaded on demand by the router)

`hyperframes-core` (composition contract) · `hyperframes-animation` ·
`hyperframes-keyframes` · `hyperframes-creative` · `hyperframes-cli` ·
`hyperframes-registry` · `media-use` (assets, TTS, captions, background removal)

### Motion doctrine

`motion-doctrine` · `cut-the-curve` · `seam-craft` · `captions-overlay` ·
`oversized-cursor` — house-style rules that make multi-scene videos read as one
continuous camera move instead of a stack of slides.

### Requirements for rendering

- Node.js 22+
- FFmpeg (`apt-get install -y ffmpeg`)
- Chromium (pre-installed in Claude Code web sessions)

### Updating

```bash
npx hyperframes skills update              # core set
npx skills add heygen-com/hyperframes --all --full-depth   # all 19
```

Then copy the refreshed skills back into this directory and commit.

## trading-bot-builder

Alpaca paper-trading bot scaffold — SMA trend strategy, backtesting, Streamlit
dashboard, GitHub Actions automation, Supabase memory.

## YouTube craft skills (TheCraigHewitt/skills, MIT)

Packaging and scriptcraft that complement HyperFrames — HyperFrames renders, these
decide what to say and how to frame it. Each reads `.agents/youtube-context.md`,
so run `/yt-youtube-context` once per channel first.

| Skill | Use for |
|---|---|
| `/yt-youtube-context` | define niche, audience, pillars — bootstrap the others |
| `/yt-hook-writing` | first 30 seconds, retention hooks, reducing early drop-off |
| `/yt-script-structure` | full script structure, pacing, retention beats |
| `/yt-retention-editing` | pattern interrupts, pacing, mid-video drop-off |
| `/yt-title-craft` | titles, CTR, search vs browse, A/B variants |

Source: https://github.com/TheCraigHewitt/skills (MIT)

### Not committed — install locally

**`youtube-scripting`** (https://github.com/laurentickner/youtube-scripting-skill)
is the strongest scriptcraft artefact I found — 4,500 lines encoding the
Educate.io process, including a banned-AI-language sweep list and a failure-pattern
catalogue. **It ships no LICENCE file, so it is all-rights-reserved and cannot be
redistributed in this repo.** Personal use is fine. Install it per machine:

```bash
git clone https://github.com/laurentickner/youtube-scripting-skill.git \
  ~/.claude/skills/youtube-scripting
```
