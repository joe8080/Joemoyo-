# OGX Nok v1.0 REVIEW — QA report (from rendered frames)

File: `OGX_Nok_v1.0_REVIEW.mp4` · overlays-off proxy for motion checks: `proxy_overlays_off.mp4`

| Check | Result | Verdict |
|---|---|---|
| Runtime (4:30–5:30) | 285.98 s (4:46.0) | PASS |
| Loudness (≈ −14 LUFS, TP ≤ −1 dBTP) | -14.0 LUFS, -1.9 dBTP | PASS |
| OCR text inventory (22 grabs: every 30 s, every credit, every name, end card) | 0 disallowed strings | PASS |
| Real-image credits read back vs credits.md | min similarity 0.978 over 7 shots | PASS |
| Parallax FG travel (floor 3 %) | min 3.01 %, median 4.44 % | PASS |
| FG/BG ratio (floor 2) | min 2.02, median 3.84 | PASS |
| freezedetect −50 dB (overlays off) | 0 frozen spans | PASS |

Allowed on-screen strings: `Excavation at the Nok site of Ido (cropped) · Louis Champion et al. 2022 · CC BY 4.0`; `Gabriele Franke`; `Jemaa`; `Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0`; `Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain`; `Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0`; `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0`; `ORIGINEX HUMAN ARCHIVES`; `Pangwari`; `Peter Breunig`

## Motion per shot (overlays off; % of frame width over the shot)

| Line | Kind | Dur (s) | FG % | BG % | FG/BG | Pass |
|---|---|---|---|---|---|---|
| L01 | real | 3.61 | 6.29 | 0.08 | 82.21 | PASS |
| L02 | real | 3.9 | 21.66 | 0.21 | 102.79 | PASS |
| L03 | ai | 3.85 | 4.8 | 0.59 | 8.16 | PASS |
| L04 | ai | 6.15 | 4.57 | 1.69 | 2.71 | PASS |
| L05 | ai | 4.38 | 4.49 | 0.64 | 6.98 | PASS |
| L06 | ai | 4.44 | 4.39 | 0.86 | 5.1 | PASS |
| L07 | gfx | 5.57 | 5.14 | 0.04 | 132.89 | PASS |
| L08 | ai | 5.61 | 3.69 | 1.31 | 2.81 | PASS |
| L09 | ai | 4.81 | 4.41 | 0.57 | 7.74 | PASS |
| L10 | ai | 2.71 | 4.71 | 0.5 | 9.41 | PASS |
| L11 | ai | 7.6 | 4.0 | 0.36 | 11.04 | PASS |
| L12 | ai | 1.8 | 5.33 | 1.73 | 3.08 | PASS |
| L13 | ai | 3.57 | 5.88 | 0.89 | 6.61 | PASS |
| L14 | ai | 4.92 | 4.49 | 1.57 | 2.85 | PASS |
| L15 | ai | 4.15 | 4.09 | 1.06 | 3.87 | PASS |
| L16 | ai | 3.95 | 4.19 | 1.0 | 4.17 | PASS |
| L17 | ai | 3.02 | 6.07 | 0.59 | 10.23 | PASS |
| L18 | ai | 3.24 | 4.74 | 1.64 | 2.9 | PASS |
| L19 | ai | 2.18 | 6.03 | 0.6 | 9.97 | PASS |
| L20 | ai | 5.62 | 3.65 | 0.43 | 8.47 | PASS |
| L21 | ai | 5.37 | 4.32 | 1.17 | 3.7 | PASS |
| L22 | ai | 3.38 | 5.15 | 1.85 | 2.78 | PASS |
| L23 | gfx | 5.81 | 4.21 | 1.13 | 3.72 | PASS |
| L24 | ai | 5.73 | 3.45 | 1.35 | 2.55 | PASS |
| L25 | real | 7.74 | 4.44 | 0.02 | 251.57 | PASS |
| L26 | ai | 8.3 | 4.43 | 1.67 | 2.66 | PASS |
| L27 | ai | 5.54 | 4.1 | 0.66 | 6.2 | PASS |
| L28 | gfx | 3.63 | 3.64 | 1.49 | 2.44 | PASS |
| L29 | gfx | 5.46 | 3.51 | 1.54 | 2.28 | PASS |
| L30 | gfx | 2.48 | 3.3 | 1.26 | 2.62 | PASS |
| L31 | ai | 4.54 | 3.83 | 1.18 | 3.24 | PASS |
| L32 | gfx | 4.03 | 4.59 | 1.6 | 2.87 | PASS |
| L33 | ai | 1.73 | 3.99 | 0.6 | 6.68 | PASS |
| L34 | ai | 6.35 | 3.69 | 1.83 | 2.02 | PASS |
| L35 | ai | 4.01 | 3.86 | 0.82 | 4.7 | PASS |
| L36 | ai | 1.75 | 5.2 | 1.88 | 2.77 | PASS |
| L37 | ai | 2.9 | 4.82 | 1.08 | 4.45 | PASS |
| L38 | ai | 3.4 | 4.62 | 1.74 | 2.65 | PASS |
| L39 | ai | 4.75 | 3.72 | 0.63 | 5.9 | PASS |
| L40 | real | 4.61 | 6.28 | 0.12 | 50.34 | PASS |
| L41 | ai | 4.61 | 4.88 | 0.72 | 6.81 | PASS |
| L42 | ai | 4.48 | 4.86 | 1.47 | 3.31 | PASS |
| L43 | ai | 4.92 | 4.09 | 0.75 | 5.44 | PASS |
| L44 | ai | 2.53 | 5.19 | 1.91 | 2.72 | PASS |
| L45 | ai | 5.21 | 3.72 | 1.37 | 2.72 | PASS |
| L46 | ai | 3.58 | 4.42 | 1.87 | 2.36 | PASS |
| L47 | ai | 3.92 | 3.99 | 1.26 | 3.16 | PASS |
| L48 | ai | 8.96 | 3.65 | 1.16 | 3.16 | PASS |
| L49 | ai | 6.7 | 3.01 | 0.79 | 3.82 | PASS |
| L50 | ai | 2.46 | 4.4 | 1.61 | 2.74 | PASS |
| L51 | ai | 4.75 | 6.11 | 0.39 | 15.67 | PASS |
| L52 | ai | 4.79 | 4.62 | 1.37 | 3.37 | PASS |
| L53 | ai | 3.52 | 4.42 | 1.28 | 3.45 | PASS |
| L54 | ai | 6.01 | 4.2 | 1.15 | 3.65 | PASS |
| L55 | ai | 4.42 | 4.27 | 1.25 | 3.42 | PASS |
| L56 | real | 6.74 | 6.29 | 0.12 | 53.02 | PASS |
| L57 | ai | 1.57 | 6.0 | 0.74 | 8.16 | PASS |
| L58 | ai | 6.16 | 4.46 | 1.35 | 3.31 | PASS |
| L59 | ai | 5.53 | 4.37 | 0.59 | 7.46 | PASS |
| L60 | ai | 2.05 | 5.29 | 1.34 | 3.96 | PASS |
| L61 | real | 7.38 | 5.64 | 0.1 | 54.77 | PASS |
| L62 | real | 4.1 | 21.59 | 0.19 | 111.69 | PASS |

## OCR inventory

| t (s) | Why | Text found |
|---|---|---|
| 1.81 | credit L01 NOK01 | Nok terracotta head : Honolulu Museum of Art (8349.1) : Photo: Hiart, CCO |
| 5.56 | credit L02 NOK01 | Nok terracotta head : Honolulu Museum of Art (8349.1) : Photo: Hiart, CC0 |
| 15.0 | every 30 s | — (no text) |
| 45.0 | every 30 s | — (no text) |
| 56.54 | name L13 | Jemaa |
| 75.0 | every 30 s | — (no text) |
| 105.0 | every 30 s | — (no text) |
| 109.23 | credit L25 NOK04 | Nok terracotta head · Cleveland Museum of Art (1995.21) : CCO |
| 135.0 | every 30 s | — (no text) |
| 156.79 | name L35 | Peter Breunig |
| 165.0 | every 30 s | — (no text) |
| 174.28 | credit L40 NOK06 | Excavation at the Nok site of Ido (cropped) - Louis Champion et al. 2022 · CC BY 4.0 |
| 195.0 | every 30 s | — (no text) |
| 203.51 | name L47 | Gabriele Franke |
| 207.45 | name L48 | Pangwari |
| 225.0 | every 30 s | — (no text) |
| 250.81 | credit L56 NOK02 | Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CCO |
| 255.0 | every 30 s | — (no text) |
| 273.18 | credit L61 NOK03 | Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain |
| 278.93 | credit L62 NOK01 | Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CCO |
| 283.98 | end card | ORIGINEX; HUMAN; ARCHIVES |
| 285.0 | every 30 s | ORIGINEXHUMAN; ARCHIVES |

## Credits read back

| Line | Image | Expected (credits.md) | Similarity |
|---|---|---|---|
| L01 | NOK01 | `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0` | 0.981 |
| L02 | NOK01 | `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0` | 1.0 |
| L25 | NOK04 | `Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0` | 0.978 |
| L40 | NOK06 | `Excavation at the Nok site of Ido (cropped) · Louis Champion et al. 2022 · CC BY 4.0` | 1.0 |
| L56 | NOK02 | `Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0` | 0.981 |
| L61 | NOK03 | `Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain` | 1.0 |
| L62 | NOK01 | `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0` | 0.981 |

## Style rules (Claude self-check on the rendered export; independent QA review still to run)
| Rule | Evidence | Verdict |
|---|---|---|
| One OpenArt still per narration line, no Higgsfield/OpenAI/Google stills | 49 AI lines, all Wan 2.7 Image Pro (ledger.md); 7 real-image lines; 6 text-free graphics | PASS |
| No chapter cards, lower-third quote/source boxes, AI labels, subscribe badges, map tags, credit pages | OCR inventory above: only credit lines, 4 name subtitles, end-card wordmark. Banned overlays are hard-off in tools/render.py (enabling one raises an error) | PASS |
| One short credit line per real image, matching credits.md | 7/7 read back ≥ 0.978 (OCR reads "CC0" as "CCO") | PASS |
| Name subtitle only where the VO is unclear | Jemaa, Peter Breunig, Gabriele Franke, Pangwari: each mis-heard by Whisper medium.en | PASS |
| One end card | 280.98–285.98 s, wordmark only | PASS |
| Every shot moves: depth parallax + overlay + camera; not Ken Burns | FG/BG layers from Depth Anything V2; FG min 3.01 %, FG/BG min 2.02 on the overlays-OFF proxy; freezedetect −50 dB: none | PASS |
| Maps animated | L07 locator zoom Africa → central Nigeria; chronology builds L23/L28–L30/L32 (text-free) | PASS |
| Voice only 'joe afrian british 1' | single VO pass + L24 fix, same voice | PASS |
| Music under the voice | 3 cues, ducked −11 dB under speech; separate stems | PASS (phone-speaker listen still needed by a human) |
| 4:30–5:30 | 4:46.0 | PASS |

## Known issues for the reviewer
1. 2.5D seams: on some AI shots the depth cut shows soft smearing where the background is revealed (most visible on L05's tree and the ground line in L09/L11). Fix would be hand masks per shot.
2. L38: the smoke columns read a little industrial.
3. L45: the replacement still still has brick-like blocks in the back wall of the trench.
4. NOK05 (Kimbell head) not used: Wikimedia refused every download (HTTP 429). L60 is an AI still.
5. Phone-speaker check of the mix not done (no speaker on the build box); loudness proven by measurement only.
