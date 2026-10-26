# The Founder's Test — Arthur & Julian (vertical micro-drama)

Format: 9:16 vertical, **~30s per episode** (Joe's decision: one Seedance 2.5 generation, 210 Higgsfield credits), 3 episodes per day (12:00 / 16:00 / 20:00 UK).

| Day | Episodes | File |
|-----|----------|------|
| 1 | Ep 1–3 (Setup, Escalation, The Drop) | `episodes_01-03.md` |
| 2 | Ep 4–6 (The Rival's Move, The Loyalty Test, The Checkmate) | `episodes_04-06.md` |

## Character lock (paste before every image/video prompt)

> Style: Cinematic vertical 9:16 mobile drama, hyper-realistic, dramatic moody lighting.

- **Arthur (The Founder):** 68, weathered face, silver hair. Ep 1: faded blue warehouse janitor jumpsuit. Ep 2: tweed jacket. Ep 3 onward: navy Savile Row suit, burgundy tie. Hook: his eyes flash electric blue on his power lines.
- **Julian (The Arrogant Heir, Arthur's grandson):** 28, slicked-back dark hair, bespoke charcoal slim-fit suit, arrogant smirk. Off screen in Ep 4–6; returns in Ep 7 seeking redemption.
- **Marcus (The Loyal Worker):** early 40s, Black British, short beard, broad build. Hi-vis vest over a grey work shirt (Ep 2–6).
- **Victor (The Rival CEO, Ravencore Logistics):** 45, sharp angular features, hawkish nose, widow's peak, dark hair silver at the temples, salt-and-pepper stubble, steel-grey eyes, aggressive navy pinstripe three-piece suit, black shirt, silver tie bar.

## Environments
- Warehouse: high-tech corporate logistics warehouse at night, towering steel racks, blue overhead industrial lighting.
- Boardroom: 9th floor, glass walls, massive conference table, city skyline behind.
- Victor's office: hyper-modern minimalist, black marble, stark white light, floor-to-ceiling windows over the city.

## Story so far (canon)
1. Julian fires the "old janitor" (Arthur, undercover) on the warehouse floor.
2. Julian deactivates Marcus's badge and shreds both men's complaint files.
3. Arthur walks into the boardroom as the founder and fires Julian.
4. Rival CEO Victor launches a Ravencore buyout and claims the warehouse; Arthur holds the land deed.
5. Victor offers Marcus triple pay to walk; Marcus refuses. Victor orders his contractors to clear them out.
6. Arthur freezes Victor's funds through the global server grid he owns. Victor is bankrupt.
7. (Next) Julian tries to crawl back for redemption.

## Production log

### Ep 1, The Setup (finished: `ep1/Ep1_The_Setup_9x16.mp4`, 29s, 720×1280)
- **Voices (ElevenLabs, eleven_v4):** Julian = "Posh Josh". Arthur = "Alistair – Cultured and Articulate". Reuse these for every episode.
- **Character lock:** `assets/character_ref_arthur_julian.png`. Wire it into every scene clip as the reference image.
- **Video:** Seedance 2.5, 9:16, 720p. Each clip gets the reference image plus its voice line as reference audio, so the lips sync.
- **Fix:** scene 1 came back with improvised dialogue. It was re-synced with Sync 3 lip-sync (silence mode). Always check each clip's audio against its line.
- **Music:** ElevenLabs Music v2.5, 32s instrumental tension bed, ducked under dialogue.
- **Edit:** `python3 assemble.py ep1`. This burns bold yellow captions, adds the "PART 1" tag, ducks the music and normalises to -14 LUFS.
- **Cost:** about £15 (images £2.70, voices £0.70, 4 clips £10.80, lip-sync fix £0.65, music £0.50).

## Locked references (reuse these; never regenerate)
Saved in Higgsfield. Pass the media ID straight into `medias` with role `image_references`.

| Character | Higgsfield media ID | Local file | Notes |
|---|---|---|---|
| Julian (v2, original face) | `4f83d792-578d-4a8f-a528-6aa16c6bed2a` | (OpenArt Seedream 4.5, option 1) | Replaces the Ep 1 v1 face, which the video models block as a real-actor look-alike |
| Arthur (janitor jumpsuit) | `6c15c0c4-3bc3-4abe-ba1b-8e365d64bbe5` | `assets/ref_arthur_face.jpg` | From Ep 1 scene 3. Wardrobe changes (tweed, suit) go in the prompt, not a new image |
| Marcus | `af05a25a-c522-480b-9c7f-b9195944349d` | (OpenArt Seedream 4.5, made once for Ep 2) | Hi-vis vest + grey shirt |
| Victor | `8fdf44e0-94e7-45ec-80bf-5296c5eca167` | (OpenArt Seedream 4.5, made once for Ep 4) | Navy pinstripe three-piece suit |

Rules:
1. New images only for **new characters** (Marcus, Victor, the security guard). Make one portrait each, once, then add it to this table.
2. Wardrobe or location changes go in the prompt text; the face image stays the same.
3. Voices: ElevenLabs "Posh Josh" for Julian, "Alistair" for Arthur, "Hymzy" for Marcus, "Victor – Deep British Male / Dark Psychology" for Victor and "PETER Mature Northern British" for the security guard. New lines are cheap (~50–150 EL credits each).

## Ep 2–7 render log (Higgsfield Seedance 2.5, 720p, 9:16, 30s, ~210 credits each)
| Ep | Job | References | Dialogue audio | Status |
|---|---|---|---|---|
| 2 | `03b26f8a` | Julian, Arthur, Marcus | `614643a0` | Done |
| 3 | `455cfc39` | Julian, Arthur, Marcus | `2a40c235` | Done |
| 4 | `cf5a7e69` | Victor, Arthur | `c335dd67` | Done |
| 5 | `2ea45f03` | Victor, Arthur, Marcus | `0a11d187` | Done |
| 6 | `b244323a` | Victor, Arthur, Marcus | `b71fdcb8` | Done |
| 7 | `cb5327eb` | Julian (jumpsuit), Arthur, Marcus; Victor voice only | `477df7e4` | Rendering |

Dialogue offsets: Ep 4 Victor 0.5s, Victor 10.0s, Arthur 22.0s. Ep 5 Victor 1.5s, Marcus 12.5s, Victor 23.0s. Ep 6 Victor 1.0s, Arthur 12.0s, Arthur 23.0s. Ep 7 Marcus 1.0s, Julian 3.2s, Julian 9.6s, Arthur 16.6s, Victor (voiceover) 22.5s.

## Lessons from Higgsfield's "5-Step Workflow" tutorial (60M-view AI drama)
1. Character sheets: plain grey background; full-body front (face erased), back, and a face close-up, so the model has one face to follow.
2. Locations: one three-quarter-view set image per recurring location (warehouse, boardroom, Victor's office) to keep layouts consistent.
3. Hook: open on the loudest moment; an emotional swing every 20–30s; end right before the reveal.
4. Voices: describe each accent in detail and carry the description into every scene.
5. Fix takes: keep what works, describe exactly what to change, regenerate, compare.
6. Money: client dramas, brand integrations, paid early access to the next episode.

## Joe's review of Ep 1–6 (rules for Ep 7 onward)
- Working: locked faces (Victor, Arthur across wardrobe changes), haze and contrast, legible phone text ("FUNDS FROZEN").
- AI tell: floaty, frictionless walking (Arthur's aisle walk, the contractors, Victor approaching the workers).
- Prompt rule: keep walking under 2s on screen. Enter characters already in place or from a cut; favour CU/ECU reactions, hands and props over full-body walks.
- Edit rule (CapCut): hide existing walks with a punch-in on the face (keyframed zoom to ~140–160%) so the baked-in dialogue stays in sync.
