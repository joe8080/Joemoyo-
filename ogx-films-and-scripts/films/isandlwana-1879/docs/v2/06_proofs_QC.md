# Isandlwana v2: opening proof and battle proof (QC)
Prepared by Claude, 22 October 2026. **Private proofs, not a cut of the film. 0 credits spent.**

## Files
| File | Length | Format | md5 |
|---|---|---|---|
| `OGX_Isandlwana_v2_proof_opening.mp4` | 0:56.0 | 1920×1080, 24 fps, H.264 + AAC 48 kHz 320k | `1d22ecc22783489dd503444ba2e3d187` |
| `OGX_Isandlwana_v2_proof_battle.mp4` | 1:00.0 | as above | `b373b39f3571f06bbe4534f75d6dce2c` |
| `…_opening_720p.mp4` / `…_battle_720p.mp4` | review copies for the phone | 1280×720 | `ccce4bb2…` / `b71e98d7…` |

v1.0 and v1.1 are untouched.

## Technical QC
| Check | Opening | Battle |
|---|---|---|
| Decode errors | none | none |
| Black frames over 0.5 s | none | none (the eclipse is dark by design; the testimony card stays readable) |
| Loudness | −14.1 LUFS, LRA 6.2 | −14.0 LUFS, LRA 6.0 |
| Contact sheets | `cs_opening.jpg` (every 2 s) | `cs_battle.jpg` |

## What's in each proof, and what it demonstrates
### Opening (0:00–0:56): "The valley"
| Time | Shot | Demonstrates |
|---|---|---|
| 0:00–0:07 | **3D terrain flight** from the Ngwebeni towards the hill. Blue morning grade; "22 JANUARY 1879 · MORNING" | A new map-to-ground device on the real terrain model |
| 0:07–0:11 | **Relief map:** the army in the Ngwebeni, the camp, "ABOUT 11 KM · 7 MILES" (WO Narrative), the iNyoni heights | A readable map with the distance sourced |
| 0:11–0:17 | **Archive:** Ntshingwayo, "IDENTIFIED AS…", c. 1879 | A Zulu commander on screen |
| 0:17–0:27 | Z33 regraded for morning; the moon line; **testimony card** (Mitford p. 93) | The "in their words" device |
| 0:27–0:31 | **Map:** the mounted patrol and the scouts driving cattle; "AROUND MIDDAY · TIMES APPROXIMATE" | The discovery, as the sources describe it |
| 0:31–0:36 | Z15 → Z11 regraded for midday | Fixes the "all golden hour" look |
| 0:36 | **Volley SFX, then a white flash, then the regiment rising**, with a lower-third testimony (Mitford p. 90) | Sound design and transition |
| 0:41–0:47 | Running, feet, **smoke wipe** | Rhythm |
| 0:47–0:56 | **3D flight** over the iNyoni edge to the hill; **title** | The title over the real ground |

### Battle (0:00–1:00)
| Time | Shot | Demonstrates |
|---|---|---|
| 0:00–0:06 | **3D:** the camp, the nek and the hill from the iNyoni heights; smoke grade; distant guns | The battlefield in relief |
| 0:06–0:13 | **Map:** the firing line, **TWO 7-POUNDERS**, **UMCITYU (KANDAMPEMVU)** and **MBONAMBI** advancing, "HELD AT A DISTANCE · WENT TO GROUND" | Named regiments, as in Adwa |
| 0:13–0:18 | Z18 with **synced volleys**; lower-third "They kept tumbling over one upon another" (Mitford p. 90) | Testimony over action |
| 0:18–0:22 | **Fripp's 1879 field sketch** | New archive |
| 0:22–0:26 | Z20, the induna, labelled "named in later accounts" | Contested detail kept framed |
| 0:26–0:32 | Z21 in slow motion; **testimony:** "…rushed over his body" (Mitford p. 91) | The source carries the peak |
| 0:32–0:45 | **Map in three beats:** NGOBAMAKOSI · LEFT HORN, then ROCKET BATTERY OVERRUN, then NOKENKE · RIGHT HORN through the MANZIMNYAMA VALLEY, then **THE NEK · CLOSED** and the road to Rorke's Drift cut | Terrain detail missing from v1.1 |
| 0:45–0:52 | Z24 → Z22; "EARLY AFTERNOON" | Collapse |
| 0:52–1:00 | Z23 **grading down to eclipse-dark**; "PARTIAL ECLIPSE · THAT AFTERNOON"; the drone; **testimony:** "The sun got very dark, like night…" (Mitford p. 92) | Sound and image as one beat |

## What's a placeholder (and what fixes it)
1. **The AI action shots are existing v1.0 clips,** regraded and reframed. The missing scenes need new shots: the guns firing, the rocket battery, the nek, the river crossing. → Option A or B in `05_credit_costs_for_approval.md`.
2. **The sound effects are procedural** (generated in code, free). They show the timing and layering, not final quality. **A human ear must check them,** especially the volleys and guns. → Package 4, or keep them if they pass.
3. **The narration uses existing takes only.** The new v2 lines (the march, the guns, Fugitives' Drift, the captures) aren't in the proofs. → Package 1 (Tier 2 voice).
4. **The 3D terrain is a real elevation model, heights ×1.6,** labelled on screen. The 30 m elevation data softens Isandlwana's crag, so the 3D hill reads rounder than the real cliff. The AI shots carry the true silhouette.
5. **Map positions are schematic.** Features come from the terrain model (the hill summit, the saddle of the nek, Conical Hill, the iNyoni escarpment, the Manzimnyama valley). Unit positions are approximate, and the map says so.

## Rules check
- Every AI shot is tagged "AI RECONSTRUCTION, ANIMATED · ILLUSTRATIVE, NOT A RECORD".
- Maps are tagged "MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE".
- The Ntshingwayo photo is captioned "IDENTIFIED AS".
- Every quote is verbatim and attributed. No speech is invented.
- No faces of named people are generated. No flags or insignia. No *Zulu* or *Zulu Dawn* compositions.
- Nothing has been published. No Supabase writes.

## For the listener (Joe or MJ, 2 minutes)
1. Opening, 0:36: does the volley land and feel earned?
2. Opening, 0:17–0:27: does the testimony card hold attention without narration?
3. Battle, 0:13–0:18: are the volleys too loud under the lower-third?
4. Battle, 0:52–1:00: does the eclipse beat work, or is it too dark on a phone?
