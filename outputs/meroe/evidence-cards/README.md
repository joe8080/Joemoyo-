# OGX Evidence Cards — Kingdom of Meroë

"DECLASSIFIED"-style gold-on-black evidence receipt cards (matching the OGX channel look:
gold slab headline, aged-paper typewriter file, red stamp, duotone artefact, VERDICT column).
1920×1080 PNG. Every card cites the real artefact / primary source behind a claim in the video.

| Card | Evidence |
|---|---|
| 01 The Meroë Head | Bronze head of Augustus · British Museum BM 1911,0901.1 · Garstang 1910 |
| 02 The Kandakes | Ruling warrior queens · Naqa & Musawwarat reliefs · OGX verified |
| 03 The Roman Record | Strabo, Geographica 17.1.53–54 (the 25 BCE war) |
| 04 The Treaty of Samos | Cassius Dio 54.5 · Strabo 17.1.54 · 21 BCE, Rome waives tribute |
| 05 The Ezana Stone | Aksum, c.350 CE · trilingual · the fall of Meroë |

## Use them in the full PC render (with the evidence-card pop-ups baked in)

The upgraded `ogx-render-kit/render_ogx.py` overlays these automatically as animated pop-up
beats. Just copy this folder into your batch images folder:

```
_OGX_BATCH\02_images_inbox\23_Kingdom_of_Meroe\evidence-cards\   <- these 5 PNGs + cards.json
```
then render as normal:
```
python render_ogx.py 23_Kingdom_of_Meroe
```
`cards.json` places each card at a fraction (0–1) of the audio duration (or absolute seconds
if the value is >1). Edit `at`/`dur` to taste. Remove the folder for a clean render with no cards.

Cards were generated with `build_evidence_cards.py` (HTML → Chromium screenshot); edit the
`CARDS` list there to change copy, add cards, or swap the artefact image.
