# After Closing — 1962 period drama (series bible)

**Format:** 16:9 widescreen, ~5 min episodes. Style lock for every visual:
> Cinematic 1962 period drama, 16:9 aspect ratio, 35mm film grain, moody amber practical lighting, deep shadows, premium television aesthetic.

**Pipeline (Joe's call):** OpenArt makes every still (cast, sets, one keyframe per shot) → Higgsfield animates the stills (Kling 2.6 / 3.0 std ≈ 1–1.25 credits per second; Seedance 2.5 480p with an audio reference only for shots that need visible lip-sync) → ElevenLabs voices, piano and room tone → ffmpeg edit.

## Cast (original fictional characters; distinctive, ordinary faces)
| ID | Character | Look | Wardrobe codes |
|---|---|---|---|
| IR | Isaiah, 31, Black man, pianist at the Marigold | (set when the portrait is locked) | IR-W01 charcoal suit |
| MJ | Mary Jane, 27, white woman, waitress and gifted seamstress | (set when the portrait is locked) | MJ-W01 sage work dress with apron; MJ-W02 neutral blouse, hair pinned |
| VB | Vincent Bell, 38, club owner | (set when the portrait is locked) | immaculate tailoring |
| ED | Eddie, Bell's silent associate | (set when the portrait is locked) | — |

## Sets and props
- SET-01 Marigold Ballroom (after hours) · SET-03 Mary Jane's room
- PROP-01 Isaiah's grand piano · PROP-03 Mary Jane's departure letter (New York)

## Locked references
(Filled in as each portrait and set is approved. Reuse; never regenerate.)

### Draft references (OpenArt, Nano Banana 2, awaiting Joe's approval)
| Item | OpenArt historyId | Resource id |
|---|---|---|
| Isaiah portrait | 6JQeDehMr96UUN359r7u | zTO1KllGj48oAaUb7obr |
| Mary Jane portrait (MJ-W01) | Ee8QgjwYN7OhEu7IbJRC | hamwSpl4RLkRBTaatzno |
| Vincent Bell portrait | x95QFhFy0YkzqisAbt1T | n1AuPgUO2yDT6Go6GvZO |
| Eddie portrait | 75XIPI6dsBWoFcEPPjD3 | QethMDPuVQDEuWj5jK2a |
| SET-01 Marigold Ballroom | eXXyjlIj38DWV7paeoty | BM3EzZCWUKTPETW5OJYt |
| SET-03 Mary Jane's room | 9Yolu3Z0VmJGhVHGHI2v | 6RYAiS7DluK1Ss3vLPqD |

Budget check (26 Oct): Higgsfield 407 credits, OpenArt 7,442. Kling 2.6 animation = 10 Higgsfield credits per 10s; Kling 3.0 std (no sound) = 12.5 per 10s; Seedance 2.5 480p = 30 per 10s.

**Joe's note (26 Oct):** in the first drafts Mary Jane looked older than Isaiah. Recast so Isaiah reads clearly older (mid-to-late 30s look, grey at the temples) and Mary Jane clearly younger (early-20s look). Script ages stay 31 / 27 unless Joe changes them.
| Isaiah v2 (2 options) | tgZLsHT92Kl3KYoF1KOF |
| Mary Jane v2 (2 options) | qQLPevAMdGENBiCs5gFD |

## LOCKED cast (Joe approved 26 Oct)
| Character | Source | OpenArt ref (upload id) | Higgsfield media id |
|---|---|---|---|
| Isaiah | Joe's chosen image, `assets/ref_isaiah.png` | moabcp0m2ks3poYuhE0M | 16119c6e-e38f-47c9-a812-73082085b871 |
| Mary Jane (MJ-W01) | Joe's chosen image, `assets/ref_maryjane.png` | lI9jMJ5TYm06MdZF1v6t | b43e2285-cdda-418a-bd5d-ac6bf1cfdf72 |
| Vincent Bell | draft above (resource n1AuPgUO2yDT6Go6GvZO), approved by default | — | — |
| Eddie | draft above (resource QethMDPuVQDEuWj5jK2a), approved by default | — | — |
| SET-01 ballroom | resource BM3EzZCWUKTPETW5OJYt | — | — |
| SET-03 MJ's room | resource 6RYAiS7DluK1Ss3vLPqD | — | — |

## Voices (ElevenLabs, eleven_v4; flow nkBdd9MZSFBLq5mfO3Iw)
- Isaiah: "Jasper's Pro Voice" nzU5ko5DAR6BBpafyNfM (warm, calm, mid-30s African American)
- Mary Jane: "Boo – Warm & Expressive" Y0G5nEDw2qHnUHGmtoM9 (early 20s, warm, wry)
- Bell: to pick when Scene 5 is made

## Ep 1 Scene 1 (first test) — Higgsfield jobs
| Shot | Model | Start still (Higgsfield) | Job |
|---|---|---|---|
| 01A wide, piano stops, MJ listens (10s) | Kling 2.6 | fc64777b | bd11f6f4 |
| 01B hands freeze on keys (5s) | Kling 2.6 | f8ff2925 | 8e3151bf |
| 01C MJ listening (5s) | Kling 2.6 | 576a2045 | 4a38e301 |
| 01D dialogue two-shot, lip-synced (12s) | Seedance 2.5 480p | ace75ecd + refs + audio a69f7e7c | f63d3112 |
| 01E Isaiah rueful smile (5s) | Kling 2.6 | 97e3af65 | 25739a7f |

## Ep 1 Scene 01 v2 — "The City and the Room" (opening, 2:00)

- Final: `ep01/AfterClosing_E01_S01_TheCityAndTheRoom_16x9.mp4` (1920x1080, 24 fps, -16 LUFS). Replaces the 35s test cut.
- Build: `ep01/v2/build_opening_v2.py` (shot in/out points, sound cues, two-pass linear loudnorm). Clips (Kling 2.6) in `ep01/v2/clips/` are git-ignored; job IDs in `ep01/v2/jobs.tsv`.
- Stills: OpenArt Nano Banana 2 (17 stills incl. a V12b retake: first take had her in black with patrons in the background).
- Sound: all ElevenLabs, 4 takes each in `ep01/v2/audio_raw/`. Used: sax_1, piano_4 (swells at 50–65s), chord_3, street_1, steps_4, tray_2, room_4.
- Rules honoured: piano muffled through the doors, full inside, cut dead on the wrong chord (80.95s); 2.0s of near-silence (room tone only) before "You always stop there."
- Known nit: V08 (over-the-shoulder) has Isaiah still wearing his jacket; every other shot has it draped over the chair.

## Ep 1 Block 1 — "The Empty Room" (0:00–1:00, cut to Joe's director's map)

- Final: `ep01/AfterClosing_E01_Block1_TheEmptyRoom_16x9.mp4` (1:02, 1920x1080, -16 LUFS). Map: `ep01/block1/director_map_block1.md`.
- Build: `ep01/block1/build_block1.py`. Reuses v2 street, doors, ballroom and macro clips; B05–B10 are new (OpenArt stills → Kling 2.6, job IDs in `ep01/block1/jobs.tsv`).
- Isaiah now wears the charcoal suit jacket throughout Block 1, per the map.
- B07 is mirrored so Mary Jane looks screen-left, toward the piano (the render had her looking right).
- Cloth foley is synthesised by `ep01/block1/cloth_foley.py` from the hand's on-screen motion: ElevenLabs credits ran out (quota hit), so no new ElevenLabs audio.
- Sound timing: piano J-cut muffled from 0:06, clear inside from 0:08, swell on Mary Jane's hold; room tone only until "You always stop there." at 0:51.8 (slight echo).
- Joe's revision: no bad chord and no hands-faltering shot (B08 dropped). The piano ends gently on a soft phrase while we hold on Mary Jane (fades 0:41.6–0:43.55), then we cut back to Isaiah rubbing his eyes. Block is now exactly 1:00.
