# OGX Nok v1.1 REVIEW — QA report (from rendered frames)

File: `OGX_Nok_v1.1_REVIEW.mp4` · overlays-off proxy for motion checks: `proxy_overlays_off.mp4`

| Check | Result | Verdict |
|---|---|---|
| Runtime (4:30–5:30) | 285.98 s (4:46.0) | PASS |
| Loudness (≈ −14 LUFS, TP ≤ −1 dBTP) | -14.0 LUFS, -1.9 dBTP | PASS |
| OCR text inventory (23 grabs: every 30 s, every credit, every name, end card) | 0 disallowed strings | PASS |
| Real-image credits read back vs credits.md | min similarity 0.978 over 8 shots | PASS |
| Parallax FG travel (floor 3 %) | min 3.14 %, median 4.58 % | PASS |
| FG/BG ratio (floor 2) | min 2.17, median 3.65 | PASS |
| freezedetect −50 dB (overlays off) | 0 frozen spans | PASS |

Allowed on-screen strings: `Excavation at the Nok site of Ido (cropped) · Louis Champion et al. 2022 · CC BY 4.0`; `Gabriele Franke`; `Jemaa`; `Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0`; `Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain`; `Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0`; `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0`; `ORIGINEX HUMAN ARCHIVES`; `Pangwari`; `Peter Breunig`

## Motion per shot (overlays off; % of frame width over the shot)

| Line | Kind | Dur (s) | FG % | BG % | FG/BG | Pass |
|---|---|---|---|---|---|---|
| L01 | real | 3.61 | 6.31 | 0.07 | 84.24 | PASS |
| L02 | real | 3.9 | 5.94 | 0.01 | 520.62 | PASS |
| L03 | ai | 3.85 | 4.99 | 0.65 | 7.73 | PASS |
| L04 | ai | 6.15 | 4.69 | 1.76 | 2.66 | PASS |
| L05 | ai | 4.38 | 5.82 | 0.0 | ∞ (flat BG) | PASS |
| L06 | ai | 4.44 | 4.48 | 1.15 | 3.88 | PASS |
| L07 | gfx | 5.57 | 5.09 | 0.05 | 112.28 | PASS |
| L08 | ai | 5.61 | 4.02 | 1.56 | 2.57 | PASS |
| L09 | ai | 4.81 | 5.83 | 0.0 | ∞ (flat BG) | PASS |
| L10 | ai | 2.71 | 4.85 | 0.71 | 6.87 | PASS |
| L11 | ai | 7.6 | 5.05 | 0.0 | ∞ (flat BG) | PASS |
| L12 | ai | 1.8 | 5.32 | 1.76 | 3.02 | PASS |
| L13 | ai | 3.57 | 6.35 | 1.01 | 6.3 | PASS |
| L14 | ai | 4.92 | 4.57 | 1.82 | 2.51 | PASS |
| L15 | ai | 4.15 | 4.23 | 1.13 | 3.74 | PASS |
| L16 | ai | 3.95 | 4.4 | 1.14 | 3.87 | PASS |
| L17 | ai | 3.02 | 4.88 | 1.97 | 2.47 | PASS |
| L18 | ai | 3.24 | 4.92 | 1.62 | 3.03 | PASS |
| L19 | ai | 2.18 | 7.63 | 0.7 | 10.97 | PASS |
| L20 | ai | 5.62 | 4.2 | 0.51 | 8.27 | PASS |
| L21 | ai | 5.37 | 4.51 | 1.54 | 2.94 | PASS |
| L22 | ai | 3.38 | 5.27 | 1.85 | 2.85 | PASS |
| L23 | gfx | 5.81 | 4.55 | 1.21 | 3.76 | PASS |
| L24 | ai | 5.73 | 3.85 | 1.35 | 2.85 | PASS |
| L25 | real | 7.74 | 4.48 | 0.02 | 185.86 | PASS |
| L26 | ai | 8.3 | 4.54 | 1.65 | 2.75 | PASS |
| L27 | ai | 5.54 | 4.31 | 0.66 | 6.55 | PASS |
| L28 | gfx | 3.63 | 3.14 | 1.45 | 2.17 | PASS |
| L29 | gfx | 5.46 | 3.51 | 1.54 | 2.28 | PASS |
| L30 | gfx | 2.48 | 3.71 | 1.27 | 2.93 | PASS |
| L31 | ai | 4.54 | 3.97 | 1.21 | 3.28 | PASS |
| L32 | gfx | 4.03 | 4.37 | 1.6 | 2.72 | PASS |
| L33 | ai | 1.73 | 4.04 | 0.59 | 6.88 | PASS |
| L34 | ai | 6.35 | 3.67 | 1.7 | 2.17 | PASS |
| L35 | ai | 4.01 | 3.85 | 0.7 | 5.52 | PASS |
| L36 | ai | 1.75 | 5.31 | 1.96 | 2.71 | PASS |
| L37 | ai | 2.9 | 5.12 | 1.29 | 3.97 | PASS |
| L38 | ai | 3.4 | 4.56 | 1.83 | 2.5 | PASS |
| L39 | ai | 4.75 | 3.82 | 0.68 | 5.64 | PASS |
| L40 | real | 4.61 | 6.3 | 0.13 | 47.92 | PASS |
| L41 | ai | 4.61 | 4.82 | 1.96 | 2.46 | PASS |
| L42 | ai | 4.48 | 4.91 | 1.62 | 3.02 | PASS |
| L43 | ai | 4.92 | 4.18 | 0.72 | 5.83 | PASS |
| L44 | ai | 2.53 | 5.21 | 1.79 | 2.91 | PASS |
| L45 | real | 5.21 | 6.68 | 0.17 | 39.66 | PASS |
| L46 | ai | 3.58 | 4.46 | 1.78 | 2.51 | PASS |
| L47 | ai | 3.92 | 4.11 | 1.27 | 3.25 | PASS |
| L48 | ai | 8.96 | 3.82 | 0.96 | 3.97 | PASS |
| L49 | ai | 6.7 | 3.23 | 0.85 | 3.79 | PASS |
| L50 | ai | 2.46 | 4.51 | 1.62 | 2.79 | PASS |
| L51 | ai | 4.75 | 6.58 | 0.48 | 13.68 | PASS |
| L52 | ai | 4.79 | 4.79 | 1.34 | 3.57 | PASS |
| L53 | ai | 3.52 | 4.65 | 1.28 | 3.64 | PASS |
| L54 | ai | 6.01 | 4.36 | 1.21 | 3.61 | PASS |
| L55 | ai | 4.42 | 4.31 | 1.32 | 3.27 | PASS |
| L56 | real | 6.74 | 6.39 | 0.11 | 57.86 | PASS |
| L57 | ai | 1.57 | 6.55 | 0.73 | 9.04 | PASS |
| L58 | ai | 6.16 | 4.38 | 1.7 | 2.58 | PASS |
| L59 | ai | 5.53 | 4.6 | 0.63 | 7.34 | PASS |
| L60 | ai | 2.05 | 5.47 | 1.5 | 3.65 | PASS |
| L61 | real | 7.38 | 5.63 | 0.09 | 59.34 | PASS |
| L62 | real | 4.1 | 5.13 | 0.02 | 237.05 | PASS |

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
| 109.23 | credit L25 NOK04 | Nok terracotta head : Cleveland Museum of Art (1995.21) : CCO |
| 135.0 | every 30 s | — (no text) |
| 156.79 | name L35 | Peter Breunig |
| 165.0 | every 30 s | — (no text) |
| 174.28 | credit L40 NOK06 | Excavation at the Nok site of Ido (cropped) - Louis Champion et al. 2022 · CC BY 4.0 |
| 195.0 | every 30 s | Excavation at the Nok site of Ido (cropped) Louis Champion et al. 2022 · CC BY 4.0 |
| 195.73 | credit L45 NOK06 | Excavation at the Nok site of Ido (cropped) Louis Champion et al. 2022 · CC BY 4.0 |
| 203.51 | name L47 | Gabriele Franke |
| 207.45 | name L48 | Pangwari |
| 225.0 | every 30 s | — (no text) |
| 250.81 | credit L56 NOK02 | Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0 |
| 255.0 | every 30 s | — (no text) |
| 273.18 | credit L61 NOK03 | Nok seated figure Louvre (70.1998.11.1) - Photo: Marie-Lan Nguyen, Public domain |
| 278.93 | credit L62 NOK04 | Nok terracotta head : Cleveland Museum of Art (1995.21) · CC0 |
| 283.98 | end card | ORIGINEX; HUMAN; ARCHIVES |
| 285.0 | every 30 s | ORIGINEXHUMAN; ARCHIVES |

## Credits read back

| Line | Image | Expected (credits.md) | Similarity |
|---|---|---|---|
| L01 | NOK01 | `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0` | 0.981 |
| L02 | NOK01 | `Nok terracotta head · Honolulu Museum of Art (8349.1) · Photo: Hiart, CC0` | 1.0 |
| L25 | NOK04 | `Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0` | 0.978 |
| L40 | NOK06 | `Excavation at the Nok site of Ido (cropped) · Louis Champion et al. 2022 · CC BY 4.0` | 1.0 |
| L45 | NOK06 | `Excavation at the Nok site of Ido (cropped) · Louis Champion et al. 2022 · CC BY 4.0` | 1.0 |
| L56 | NOK02 | `Nok kneeling figure · Honolulu Museum of Art (8348.1) · Photo: Hiart, CC0` | 1.0 |
| L61 | NOK03 | `Nok seated figure · Louvre (70.1998.11.1) · Photo: Marie-Lan Nguyen, Public domain` | 1.0 |
| L62 | NOK04 | `Nok terracotta head · Cleveland Museum of Art (1995.21) · CC0` | 1.0 |
