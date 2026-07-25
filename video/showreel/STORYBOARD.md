# STORYBOARD — JoeMoyo Portfolio Showreel

240s · 1920×1080 · 26 shots · 7 cards

Timings are the source of truth in `build.mjs` (`SHOTS` and `CARDS`). Edit those
and re-run `node build.mjs`; do not hand-edit `index.html`.

Shots overlap their neighbour by 0.9s and crossfade. Ken Burns direction
alternates across every cut so the film reads as one continuous camera move
rather than a stack of independent pushes.

## Act 0 — Cold open · 0–18s · gold only

| Shot | Plate | Window | Move |
|---|---|---|---|
| s01 | open-goldleaf | 0–9.5 | push in |
| s02 | close-converge | 8.6–18.0 | pull out |

**Card c0** (2–16s, centred) — `PORTFOLIO · 2026` / **JOEMOYO** / `Media · Markets · Machines`

## Act 1 — OrigineX Human Archives · 18–68s · amber pop

| Shot | Plate | Window | Move |
|---|---|---|---|
| s03 | hist-monolith | 17.1–26.0 | rise in |
| s04 | hist-relief-a | 25.1–34.0 | drift left |
| s05 | hist-papyrus | 33.1–42.0 | push in |
| s06 | hist-mask | 41.1–51.0 | sink out |
| s07 | hist-colonnade | 50.1–59.0 | drift right |
| s08 | hist-relief-b | 58.1–68.0 | pull out |

**Card c1** (21–34.5s) — `ORIGINEX HUMAN ARCHIVES` / **History, Restored** / `Long-form documentary · YouTube`

## Act 2 — Finance channel + AI toolkit · 68–115s · teal pop

| Shot | Plate | Window | Move |
|---|---|---|---|
| s09 | fin-chart-a | 67.1–77.0 | rise in |
| s10 | fin-skyline | 76.1–86.0 | drift left |
| s11 | fin-ribbons-a | 85.1–95.0 | push in |
| s12 | fin-chart-b | 94.1–105.0 | sink out |
| s13 | fin-ribbons-b | 104.1–115.0 | drift right |

**Card c2** (71–84.5s) — `FINANCE CHANNEL & AI TOOLKIT` / **Money, Explained** / `Education · Research · Tools`

## Act 3 — Music studio · 115–155s · amber pop

| Shot | Plate | Window | Move |
|---|---|---|---|
| s14 | mus-console-a | 114.1–123.0 | drift left |
| s15 | mus-mic-a | 122.1–131.0 | push in |
| s16 | mus-wave-a | 130.1–139.0 | pull out |
| s17 | mus-console-b | 138.1–147.0 | drift right |
| s18 | mus-mic-b | 146.1–155.0 | rise in |

**Card c3** (118–131.5s) — `MUSIC STUDIO` / **Sound, Built** / `Recording · Production`

## Act 4 — Commerce · 155–190s · crimson pop

| Shot | Plate | Window | Move |
|---|---|---|---|
| s19 | com-box-a | 154.1–166.0 | push in |
| s20 | com-warehouse | 165.1–178.0 | drift left |
| s21 | com-box-b | 177.1–190.0 | sink out |

**Card c4** (158–171.5s) — `COMMERCE` / **Product, Shipped** / `Shopify · Retail operations`

## Act 5 — Agent systems · 190–222s · teal pop

| Shot | Plate | Window | Move |
|---|---|---|---|
| s22 | sys-server | 189.1–201.0 | push in |
| s23 | sys-nodes | 200.1–212.0 | drift right |
| s24 | fin-ribbons-b | 211.1–222.0 | pull out |

**Card c5** (193–206.5s) — `AGENT SYSTEMS` / **Work, Automated** / `AI agents · Algorithmic trading`

## Act 6 — Close · 222–240s · gold only

| Shot | Plate | Window | Move |
|---|---|---|---|
| s25 | close-converge | 221.1–232.0 | push in |
| s26 | open-goldleaf | 231.1–240.0 | pull out |

**Card c6** (225–239s, centred) — `FIVE VENTURES · ONE OPERATOR` / **JOEMOYO**

## Plate prompts

All plates were generated with Higgsfield `nano_banana_pro` at 2k, 16:9
(2752×1536), on this shared style prefix:

> Cinematic prestige documentary still, 35mm anamorphic, deep near-black ground,
> volumetric haze, heavy negative space, shallow depth of field. Subject: …
> No text, no words, no letters, no logos, no watermark.

The "no text" clause is deliberate — every word on screen is rendered by the
composition, so nothing is left to AI lettering. Per-plate subjects:

| Key | Subject |
|---|---|
| open-goldleaf | macro of cracked gold leaf on black lacquer |
| close-converge | gold dust and embers converging to a luminous core |
| hist-monolith | ancient African stone monolith at night, gold rim light |
| hist-papyrus | torn edge of a weathered papyrus in museum darkness |
| hist-mask | bronze ceremonial mask on a plinth, one amber shaft |
| hist-colonnade | desert ruin colonnade at blue hour, lantern glow |
| hist-relief-a/b | carved stone relief, gold rim light raking left |
| fin-chart-a/b | glass and obsidian monoliths as a bar-chart skyline, teal underglow |
| fin-skyline | financial district from above at night, teal window grids |
| fin-ribbons-a/b | braided ribbons of teal and gold light in black space |
| mus-console-a/b | vintage mixing console raking into darkness, amber key |
| mus-mic-a/b | condenser microphone in a dark booth, amber rim |
| mus-wave-a | waveform as molten gold ridges on a black mirror |
| com-box-a/b | unbranded product box on a dark set, crimson edge light |
| com-warehouse | dark warehouse aisle receding, crimson safety lighting |
| sys-server | server corridor in darkness, teal indicator LEDs |
| sys-nodes | 3D network of glowing nodes and filaments, teal |

## Not included

- **No narration.** The film is built for a music bed. Adding VO means writing
  `SCRIPT.md` and regenerating with narration timing — the card windows would
  need to move to the voice.
- **No music bed.** None was licensed or generated. Drop an audio file in and
  add an `<audio>` element to `index.html`.
- **No metrics.** No subscriber counts, revenue, or results claims appear
  anywhere — none were supplied, and inventing them for a portfolio piece would
  be a liability. Real figures can be added as a stat card per act.
