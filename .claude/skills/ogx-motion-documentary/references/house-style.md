# OGX house style (as built in render.py)

## Frame
- 1920×1080 at 24 fps, H.264 CRF 19, AAC 320k 48 kHz.
- Stills are rendered on a 2304×1296 plate, so there is room for Ken Burns moves. Moves cycle push, pan right, pull, pan left, tilt down, push-left, so they never feel mechanical.
- A second picture on a long line arrives with a dissolve at `switch`.

## Colours
- Green ground `#152121` `(21,33,33)` for cards and end card.
- Gold `(201,164,92)` for kickers, rules and rims.
- Cream `(239,230,210)` for text.
- Red `(142,42,32)` for Italian forces on maps.
- Lime `(170,255,70)` for the subscribe rim flash only.

## Type
- Cinzel for the main title and "SUBSCRIBE". Cinzel has no arrow glyph, so "→" renders as an empty box; use "–".
- Lora / Lora-Italic for body text, captions and end-card lines.
- Kickers are letter-spaced gold caps.

## Overlays
- On-screen text (ost): short caps captions such as dates, places, "BY MOST ACCOUNTS", "ESTIMATES VARY".
- AI tag at top left on every AI shot: "AI RECONSTRUCTION, ANIMATED · ILLUSTRATIVE, NOT A RECORD".
- Credit strip on an archive image's first use, for about 5 s, e.g. "Le Petit Journal, 28 August 1898 | Public domain | Wikimedia Commons".
- Act header on each act's first shot: number plus title.
- Map labels: "MODERN BORDERS SHOWN" and "MOVEMENTS SCHEMATIC, POSITIONS APPROXIMATE". Data credits: AWS Terrain Tiles (SRTM/GMTED2010/ETOPO1), "Contains modified Copernicus Sentinel data <year>", Natural Earth.
- Wordmark: OrigineX.

## AI still look
- Hand-tinted 19th-century engraving / illustrated-newspaper style.
- Cross-hatching, paper grain, sepia and umber with muted colour.
- Anonymous figures seen from mid or long distance.
- No readable documents, flags or insignia.

## Subscribe badge (added v1.4, Joe's spec)
Joe asked for "a motion slide, glass black and gold, flashing lime on the rims, saying subscribe, 3–4 s, flash 3 times, not too much brightness but enough to capture attention".

- Size 600×150, corner radius 30.
- Glass: the frame behind is Gaussian-blurred (σ 16) and kept at 0.30 brightness, with a dark tint and a thin sheen line.
- 3 px gold rim.
- Gold rounded play tile.
- "SUBSCRIBE" in Cinzel 56, cream; "ORIGINEX HUMAN ARCHIVES" in Lora 19, gold.
- Lime rim: 5 px, plus a Gaussian glow (radius 9). Its alpha is the sum of 3 Gaussian pulses (width 0.16 s) at about 0.75, 1.6 and 2.45 s, capped at 1, times 0.6.
- Mid-film:
  - bottom right, centre at (W−60−300, 880), from 120.0 s for 3.8 s;
  - slides in from +260 px over 0.4 s and eases out at the end.
- End card: "ORIGINEX HUMAN ARCHIVES" kicker, a rule, then "If this record is worth keeping," in Lora-Italic 64. The badge sits centred at y 610, with no slide, flashing at 1.0, 1.9 and 2.8 s.
- Code: `badge_layers()` / `draw_badge()` in render.py.

## Structure (Nzinga v6.2 / Production OS v2.0)
1. Cold open on a striking archive object.
2. A question card with silence under it.
3. Title.
4. Numbered acts.
5. The close returns to the opening object.
6. Sign-off: "This has been OrigineX Human Archives."
7. End card with the subscribe line (no "next time" tease until Joe confirms the next film).
