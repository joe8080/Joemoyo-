# JoeMoyo Remotion compositor

The motion-graphics render engine for the video crew. Renders the `Episode`
composition: a title card → Ken Burns stills → outro, with narration audio,
burnt-in captions, and dynamic overlays (lower-thirds, stat cards, quote cards).

The Python `VideoProducer` drives this automatically via `tools/remotion.py`,
writing the crew's props to `_props.json` and calling `npx remotion render`.

## Setup

```bash
cd remotion
npm install
```

## Use it manually

```bash
# Interactive studio (preview + tweak)
npm start

# Render with the crew's props
npx remotion render Episode out/video.mp4 --props=_props.json
```

## Props shape

See `src/types.ts` (`EpisodeProps`). The producer's
`_build_remotion_props()` emits exactly this shape:

- `clips[]` — `{ src, duration, pan, caption }` (src = image URL or `staticFile()` path)
- `intro` / `outro` — title cards
- `lowerThirds` / `statCards` / `quoteCards` — overlays timed by `at` (seconds from narration start)
- `narrationUrl` — ElevenLabs mp3
- `srt` — caption track

## Notes / refinement track

- **Images:** `clip.src` is currently a local path from the producer. For
  rendering, serve stills via a public URL (Supabase signed URL) or copy them
  into `remotion/public/` and reference with `staticFile()`. The ffmpeg engine
  (`--engine ffmpeg`) reads the local `img/` folder directly and is the
  reliable default until this is wired.
- **Crossfades:** clips use a soft fade-in; swap to `@remotion/transitions`
  `TransitionSeries` for true crossfades (kept simple here on purpose).
