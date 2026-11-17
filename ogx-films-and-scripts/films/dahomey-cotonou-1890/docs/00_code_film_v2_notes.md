# The Ghost Army of Dahomey: code film v2.0 (preview, with Joe's voice)
Prepared by Claude, 17 November 2026. **Private. Joe approves any release.** The v1.1 film in Drive is untouched.

## What this is
- A rebuild of the Dahomey / Cotonou 1890 film made **entirely in code** (Remotion). No AI images, no AI video, no credits spent.
- 50 scenes, one per narration line, following the v1.1 narration word for word (taken from the v1.1 film's captions).
- Kit: `../../code-film/` · episode: `code-film/remotion/src/episodes/dahomey/` · script: `code-film/data/dahomey/script.json`.

## Status
| Item | State |
|---|---|
| Pictures | Rendered, 8:21, 1080p30, captions on |
| Joe's narration | **In.** Taken from the v1.1 film's own soundtrack (voice with its music), so it is the approved voice, word for word. |
| Cuts made to the audio | Two sentences removed, as the 29 October review asked: "We have gone with the two, and told you about the one." (was at 2:16) and "The museum notes say some were taken from a dead woman soldier." (was at 6:34). 40 ms fades at each join. |
| Timing | **Real.** Word timings from the voice (`data/dahomey/words.json`, 1,246 words); 1,170 of 1,226 script words matched directly, the rest placed between their neighbours. Every scene, cue and caption follows the voice. |
| Sound | The v1.1 mix, normalised to -14 LUFS, true peak -1.5 dBTP or lower |

### How the audio got here (17 November 2026)
The v1.1 review file in Drive is 22 MB and the Drive connector stops at 10 MB. Route used, all through Joe's own connected accounts and with nothing made public:
1. Zapier (Google Drive) handed the private file to the Higgsfield edit sandbox.
2. In the sandbox: word timings (faster-whisper small.en), the two sentences cut, audio exported as a 6 MB MP3.
3. Zapier saved that MP3 into Joe's Drive as `OGX_Dahomey_v1_1_narration_cut_for_code_film.mp3` (private, top level of My Drive).
4. The Drive connector downloaded it here (under 10 MB), checksum matched.

Limits to know about: the source is the 480p review file, so the audio is 81 kbps AAC re-encoded once to MP3. It is clean for YouTube speech, but the original narration WAVs on the workstation would be better if a final master is wanted. The music under the voice jumps slightly at the two cuts.

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
