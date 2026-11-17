# The Ghost Army of Dahomey: code film v2.0 (preview)
Prepared by Claude, 17 November 2026. **Private. Joe approves any release.** The v1.1 film in Drive is untouched.

## What this is
- A rebuild of the Dahomey / Cotonou 1890 film made **entirely in code** (Remotion). No AI images, no AI video, no credits spent.
- 50 scenes, one per narration line, following the v1.1 narration word for word (taken from the v1.1 film's captions).
- Kit: `../../code-film/` · episode: `code-film/remotion/src/episodes/dahomey/` · script: `code-film/data/dahomey/script.json`.

## Status
| Item | State |
|---|---|
| Pictures | Rendered, 8:30, 1080p30, captions on |
| Joe's narration | **Not in yet.** The v1.1 film in Drive is 22 MB; the Drive connector stops at 10 MB and this sandbox cannot download from Drive. |
| Timing | **Estimated** from word counts. It re-times itself to the voice once the audio is in (`data/words.py`, then `data/build_timeline.py dahomey`). |
| Sound | Placeholder bed only |

## Fixes from the 29 October release review, built in
| Review point | What v2.0 does |
|---|---|
| Opening states the women led as fact | The claim carries an "ACCORDING TO GOVERNOR BAYOL" chip and source line (S07, S13). |
| "We have gone with the two" turns sources into a headcount | That sentence is marked to be cut from the audio (S19). The screen says: "The accounts disagree. Women were among the dead. Their exact role that morning is disputed." |
| Museum line says objects were taken from a dead woman soldier | That sentence is marked to be cut (S42). S41 shows the catalogue record as text: horn, inv. 71.1891.22.186, donor Foà, "prise à la ceinture d'un Dahoméen", and "the records do not securely identify every original wearer". |
| Invented necklace under "the museum's own words" | Gone. No object is pictured. |
| Later images need dates | Forbes (1851), Fortier (early 1900s) and the March 1890 press are catalogue cards with dates and "not 1890 / not the battle" stamps. The pictures themselves are not shown. |
| Too many reconstruction pictures | There are none. Maps, diagrams, counters and source cards only. |

Not restored: sleeping defenders, a Foreign Legion force in 1890, 3,000 women, Winchester allocation, a general French-line collapse.

## Joe or MJ to check before release
1. **Battle map layout.** Place names come from Foà's 1895 plan, but I have not seen the plan image. The layout is a simplified schematic and says so on screen. Check it against `assets/p3a-foa-1895-plan-kotonou-p384.jpg` on the workstation.
2. **Name spellings in captions:** Lemoyne, Oudard, Pansier, Compérat (Foà's plan prints "Compeyrat"), Seh-Dong-Hong-Beh, Nawi, Gezo.
3. **S09** shows the meaning of the corps' name but not the name itself, because the v1.1 caption track garbles it.
4. **S39** names Le Petit Parisien (as narrated) and calls the other paper "French illustrated press"; add the title once confirmed.
5. Open items from the asset register still stand (object `.151`, the `.85` wording).
