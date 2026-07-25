# JoeMoyo Portfolio Showreel

A 4-minute, 1920×1080 brand showreel across the five ventures — OrigineX Human
Archives, the finance channel and AI toolkit, the music studio, commerce, and the
agent systems.

Hero plates were generated in Higgsfield; motion, typography, transitions and
assembly are authored in HyperFrames. Every word on screen is rendered by the
composition, so no type is left to AI lettering.

## Render it

The plates are **not** in the repo — they live on Higgsfield's CDN and are
fetched on demand.

```bash
./fetch-images.sh     # download the 24 plates into assets/images/
npm run check         # lint + runtime + layout + motion + contrast
npm run render        # → showreel.mp4
```

`npm run dev` opens the preview with live reload if you want to scrub it first.

### If a plate 404s

Higgsfield CDN links can expire. Regenerate from the prompts in `STORYBOARD.md`,
or pull the image out of your Higgsfield generation history — job IDs for the
unused alternates are in `assets/images/manifest.json` under `pending`.

## Edit it

**`build.mjs` is the source of truth.** `index.html` is generated — hand edits to
it are lost on the next build.

```bash
node build.mjs        # regenerate index.html
```

- **Retime a shot** — edit its row in `SHOTS` (`[id, plate, start, end, move]`).
- **Change the camera move** — swap the move name; the options are in `MOVES`
  (`pushIn`, `pullOut`, `driftLeft`, `driftRight`, `riseIn`, `sinkOut`).
  Directions alternate across cuts on purpose so the film reads as one
  continuous camera move; keep that alternation if you reorder shots.
- **Change on-screen copy** — edit `CARDS`
  (`[id, kind, start, end, label, hook, sub]`). Keep hooks to ≤4 words; the type
  scale is built for that.
- **Change the palette** — `GOLD` / `DARK` at the top of `build.mjs`. The
  per-act colour pop lives in the plates themselves, one pop per act.

After any change: `node build.mjs && npm run check`.

## Verification status

The composition was checked and rendered against **placeholder plates**
(`make-placeholders.sh` writes brand-coloured gradient stand-ins). That verifies
timing, motion, typography, layout and contrast — everything except the actual
photography. `showreel-placeholder.mp4` is that reference render.

Once you run `./fetch-images.sh`, re-run `npm run check` before the real render:
contrast is measured against whatever is actually behind the type, and the real
plates are darker than the placeholders, so it should only improve.

## Known gaps

- **No music bed.** Drop an audio file into `assets/` and add an `<audio>`
  element to the generated markup in `build.mjs`. Four minutes with no audio is
  the single biggest thing between this and a finished piece.
- **No narration.** See `STORYBOARD.md` → "Not included".
- **No metrics.** Deliberate — nothing was supplied, and invented figures on a
  portfolio piece are a liability. Add a stat card per act when you have real
  numbers.
- `npm run check` reports maintainability warnings (file length, track density).
  They are advisory; the framework suggests splitting into sub-compositions.
  `build.mjs` covers the same maintainability need via the shot table.

## Files

| Path | What |
|---|---|
| `build.mjs` | shot table + card table → generates `index.html` |
| `index.html` | generated composition — do not hand-edit |
| `BRIEF.md` | confirmed intent, palette, structure, constraints |
| `STORYBOARD.md` | per-shot timings, moves, and the plate prompts |
| `fetch-images.sh` | downloads the plates from the manifest |
| `make-placeholders.sh` | brand-coloured stand-ins for offline verification |
| `assets/images/manifest.json` | plate keys → CDN filenames, plus unused alternates |
| `assets/vendor/gsap.min.js` | vendored GSAP (no CDN dependency at render time) |
| `assets/fonts/` | vendored Archivo Black + Inter |
