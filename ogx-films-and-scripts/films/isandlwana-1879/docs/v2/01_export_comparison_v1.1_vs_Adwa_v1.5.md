# Isandlwana v1.1 against Adwa v1.5: what was lost, where, and the fix
Prepared by Claude, 22 October 2026, for MJ and Joe. **Private. Nothing is published.**

## How I compared them
I compared the **actual exports**, not the plans:
- `OGX_Adwa_1896_v1.5_720p_review.mp4`
- `OGX_Isandlwana_1879_v1.1_720p_review.mp4`

I used three methods:
1. Frame sampling and matched contact sheets (the openings at 0:00–1:24; Adwa's battle at 6:19–7:41 against Isandlwana's battle at 2:49–3:58).
2. A motion and sharpness measure over every second of each film.
3. A shot-by-shot count from each film's own timeline.

## Short answer
1. **v1.1 is a shorter edit of v1.0.** Nothing new went into it: no new images, maps, music or research.
2. **The battle is where the gap shows most.**
   - Adwa's battle has named units on terrain you can read, and every beat has its own shot.
   - Isandlwana's battle uses four generic "horn" maps on flat satellite imagery, about a dozen mostly static AI shots (two of them repeats), and one music cue throughout.
3. **The Zulu side of the story isn't heard.** The film says "by Zulu accounts" but never lets the accounts speak. They exist, in print, with page numbers. They are now researched (see `02_claim_ledger_v2.md`).

## 1. The numbers
| Measure | Adwa v1.5 | Isandlwana v1.1 | What it means |
|---|---|---|---|
| Runtime | 10:46 | 5:43 | Half the canvas for a bigger battle |
| Narration | 1,559 words, 115 lines | 832 words, 53 lines | Less story, less detail |
| Distinct AI motion shots | 54 | 33 | Less variety |
| Distinct maps | 17 | 11 | Fewer map beats |
| Archive images | 10 | 8 (no Zulu-side archive) | Neither commander is seen |
| Images reused | 20 | 9, including repeats 5–10 s apart | Noticeable on screen |
| Cuts (measured) | 87 | 44 | Slower, flatter rhythm |
| Seconds that are near-still | 5.9% | 10.2% | Nearly twice as static |
| Music cues | 12 (one per act) | 6 in use | Long stretches in one mood |
| Battle length | 82 s, 9 maps naming brigades and commanders | 70 s, 4 maps, no regiment named | The battle reads as diagrams, not events |

Image sharpness and colour level are about the same (sharpness 23.7 against 24.0). **So picture quality per frame isn't the problem; variety, action and design are.**

## 2. Timestamped losses and fixes (times are v1.1)

### A. Cinematic scene action
| Time | What you see | What's lost against Adwa | Fix |
|---|---|---|---|
| 0:00–0:11 | Z15 horsemen on a ridge, then Z11 (Zulu army) | The discovery is told, not shown. Nobody moves towards anyone. Adwa opens on the night march, with men moving through the frame | Open on Zulu ground: the regiments lying silent in the Ngwebeni valley (testimony: the moon was "wrong", so no attack was planned). Then the scouts drive cattle and the horsemen appear on the skyline. Then a volley, and the Umcityu rise. **3 new action clips** |
| 2:48–2:52 | **Z15 again** (also at 0:00), then Z11 again | The battle opens on recycled footage | New clip: the Umcityu springing up out of the valley floor, filmed from inside the ranks |
| 3:02–3:13 | Z18/Z19 firing line | A generic line. No guns, no rockets, no donga | New clips: the two 7-pounders firing from the camp front; the rocket battery overrun near the Conical Hill; the Ngobamakosi in the donga |
| 3:13–3:25 | Z20/Z21: the induna moment | The best moment in the battle runs 12 s on two near-still shots | Give it 20 s: the regiment pinned in the grass, the induna running down the slope, the shout of "Usutu!", the charge over his body. Use the Mitford p. 91 testimony on screen |
| 3:41–3:58 | Z22, Z24, **Z23 twice** (3:46 and 3:58) | The collapse, the nek and the last stand aren't shown. No fight for the track | New clips: the right horn closing the nek; men standing back to back on the nek (Uguku's account); the sky darkened by smoke and eclipse |
| 4:02–4:17 | **Z10 and Z21 reused** under the "why they won" answer | The answer plays over shots we've already seen | Use archive instead: Fripp's 1879 sketch and Crealock's sketch from the evening of the battle. New maps: the nek closed |

### B. Image quality and variety
| Time | Problem | Fix |
|---|---|---|
| Whole film | **Every AI shot is golden hour** (sunrise or sunset light). It reads as one mood. The battle happened around midday and early afternoon, under smoke and a partial eclipse | New shots graded by time of day: blue pre-dawn (the march), hard midday (the discovery), smoke-brown and darkening (the battle), dusk (Crealock's return) |
| 0:36, 2:11, 4:10 | Isandlwana drawn as a flat-topped table mountain, a different shape in each shot | One reference shape for the hill (the steep, crouched "sphinx" profile seen from the east), taken from the terrain model and used in every prompt |
| 3:52–3:57 | The eclipse shown as a black disc, which looks like a total eclipse | Show a dimmed, smoke-filtered sun with the light failing. On-screen text: PARTIAL ECLIPSE |
| 1:22–1:35 | The archive is all British (Frere, I02, de Neuville) | Add the Zulu side: Ntshingwayo kaMahole (a c. 1879 photograph, captioned "IDENTIFIED AS"), Dabulamanzi kaMpande (ILN, 1879), Fripp's 1879 sketch of a Zulu regiment attacking. **All public domain, now on the build machine, 0 credits** |
| 5:22–5:34 | The memorial line plays over the same 2010 photograph used at 2:05 | Close on Crealock's eyewitness sketch of the field at dusk on 22 January. It's the strongest archive image we have, and it's dated |

### C. Terrain-map detail
| Time | Problem | Fix |
|---|---|---|
| 0:11, 2:55–3:42 | **Flat satellite with no hillshade.** You can't see Isandlwana as a hill, the nek, or the iNyoni ridge. Adwa's maps shade the relief, so the mountains read | A new battlefield map from the terrain model (AWS terrain tiles), with relief shading and the hill shown in 3D |
| 2:55–3:42 | Arrows say "Zulu army", "left horn", "right horn". **No regiment is named.** Adwa names every brigade | Name the regiments from the testimony:
- the **Umcityu (Kandampemvu)** sprang up first (Colenso; WO Narrative);
- the **Ngobamakosi** were the left horn (Mitford, pp. 90–91);
- the **Uve** were held back until reinforced, and the **Mbonambi** "suffered very severely from the artillery fire" (Colenso, pp. 408–413);
- the **Nokenke** were the right horn, behind the hill (Mitford, p. 94);
- the **Undi and Udhloko** were in reserve and went on to Rorke's Drift.

Any regiment not in these sources is labelled "later reconstructions" or left out |
| 2:55–3:42 | Missing features: **the nek, the donga, the iNyoni ridge, the Conical Hill, the Manzimnyama valley, Fugitives' Drift** | Label each one at the moment it matters. Label sizes and contrast follow Adwa's readable plates |
| 3:34 | "Closed" shows the circle closing in one move | Three beats: the right horn behind the hill in the Manzimnyama, then the nek cut, then the line of retreat to Fugitives' Drift |

### D. Sound design
| Time | Problem | Fix |
|---|---|---|
| 2:49–3:58 | **One cue (C05) under the whole battle.** No change from the discovery to the charge to the collapse | Split the battle: **tension** (the discovery), then **drive** (the advance), then **impact and silence** (the collapse and the eclipse) |
| 3:58–4:46 | **C06 stretched to 1.389×**, the limit, and audibly smeared | Replace it with a cue of the right length, or loop it musically. **Don't time-stretch past 1.1×** |
| Whole film | **No sound effects layer.** No wind, no volleys, no guns, no grass. Adwa has none either, but this battle depends on the sound of the volleys ("tumbling over one upon another") | Add an effects layer: wind on the plateau, distant 7-pounder booms, volley crackle, rushing grass, the drop to near-silence at the eclipse. **The proofs use a free procedural version; the paid version is listed for approval** |
| 0:00 | The film opens on music | Open on wind and silence, then the first volley |

### E. Storytelling depth
| Time | Problem | Fix |
|---|---|---|
| 0:00–0:45 | The cold open tells the end first, then poses "how did the Zulu win?" It's Adwa's structure again | **A new spine:** the day as the Zulu army lived it, from the king's order to the regiments' return to the Ngutu hills. The witnesses are named, and their words appear on screen, attributed |
| 1:48–2:20 | The march is three lines. Testimony gives much more: they left Nodwengu on the afternoon of 17 January, marched slowly on the king's order, split into two columns on the 19th, and hid in the Ngwebeni valley on the 21st | A full sequence: the king's charge (as the prisoner reported it, with attribution), the march, the hidden valley, the cattle |
| 2:39–2:52 | "Several Zulu accounts say…" with no account shown | Show the attributed text from **Mitford (1883), p. 93**: "the moon was 'wrong'" |
| 3:13 | Mkhosana, the induna, named only "by Zulu accounts" | Mitford's veteran calls him "one of the sub-chiefs of the Kandampemvu" (p. 91). The name Mkhosana comes from later accounts; keep it framed that way |
| 4:24 | "Nobody made a full count" | Add the War Office narrative (1881), from Zulu statements: losses "not less than 1,000" at Isandlwana. The captures: two 7-pounder guns, about 800 rifles, about 400,000 cartridges. **These are concrete figures** |
| Missing | No **Fugitives' Drift**, no **Melvill's watch stopped at 2:10**, no **Dabulamanzi** leading the reserve | Add all three. Each is sourced (WO Narrative, pp. 89–90) |

### F. Transitions
| Time | Problem | Fix |
|---|---|---|
| Whole film | Every join is a plain 0.5 s dissolve or a hard cut. Adwa uses map push-ins that lead into scenes, and act stings | Match-cuts from the map to the ground (zoom into the terrain model, then a dissolve to the same place on the ground); smoke wipes in the battle; one flash-to-black at the eclipse; a slow dissolve from the dusk sketch to the 2025 landscape |
| 0:45 | The title card arrives after a reused shot | A title card over the terrain push-in to the hill |

## 3. What can't be fixed for free
1. **New narration:** the testimony beats, the march, Fugitives' Drift. This needs the approved voice. Tier 2 is on hold, so it needs Joe's approval.
2. **New action clips:** the guns, the rockets, the nek, the time-of-day grading. Each needs Kling generation.
3. **Recorded sound effects and two replacement music cues.**

The costed list is in `05_credit_costs_for_approval.md`. **The two proofs use only free material and existing voice takes**, so Joe can judge the direction before spending anything.
