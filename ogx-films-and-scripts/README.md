# OGX films and scripts

This is the home of OrigineX Human Archives (OGX) film-making: the production skill, each film's build pipeline, scripts and review packs, and the prompts that drive them. It's private.

## Where things are
| Path | What it is |
|---|---|
| `../.claude/skills/ogx-motion-documentary/` | **The base OGX film skill.** Claude Code loads it automatically in this repo. The same skill is on claude.ai (Save skill) and on Eden's Skills page. |
| `prompts/` | Director prompts, e.g. `next-film-prompt-v0.1.md` (MJ's gated next-film test). |
| `films/adwa-1896/` | Reference film. `pipeline/` is the working code (render, maps, mix, captions, motion, voice split and patch). `docs/` holds the v1.5 change log, final script, production pack, SRT and the v05 voiced script. `voice-patch/` holds the v1.5 patch split. |
| `films/isandlwana-1879/` | Next film (test of prompt v0.1): pre-production pack for MJ review. |

## Not in git
Media lives in the build workspace and Drive, not here: masters, review MP4s, voice and music audio, generated stills and motion clips, map tiles and fonts. Rebuild the maps with `pipeline/geo/fetch_tiles.py`, `build_terrain.py` and `build_s2.py`.

## Rules (short)
1. Private preview only. Joe alone approves release, and nothing is published or scheduled from here.
2. Report spend before incurring it.
3. Never overwrite a delivered version (v1, v1.1, …).
4. Follow the skill's gates for a new film: pre-production pack, then MJ review, then a 45–60 s proof, then the full build, delivery, QC statement and learning log.
