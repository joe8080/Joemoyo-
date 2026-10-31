# QA report — OGX_Ishango_v1.1_REVIEW_natural.mp4

Runtime: **260.24 s (4:20.2)** — target 4:30–5:30 → FAIL

## 1. OCR text inventory (rendered frames)

| t (s) | why | shot | text read (conf ≥ 70) | unexpected |
|---|---|---|---|---|
| 2 | 30s-grid | L01 | — | — |
| 14.8 | credit L03 | L03 | Commons CC BY-SA Joeyken | Joeyken |
| 25.4 | card L06 | L06 | The Ishango bone OrigineX Human Archives | — |
| 32 | 30s-grid | L07 | Mh | — |
| 36.8 | credit L08 | L08 | NASA Lands Wikimedia Commons Public domain | — |
| 42.2 | name L09 | L09 | th TW | — |
| 48.0 | name L10 | L10 | Reconstruction (Al) de | — |
| 56.0 | credit L12 | L12 | Joeykentin Commons CC BY-SA 40 | — |
| 62 | 30s-grid | L13 | fe | — |
| 92 | 30s-grid | L19 | — | — |
| 94.7 | credit L20 | L20 | Wikimedia Commons CC BY 2.5 | — |
| 100.0 | credit L21 | L21 | — | — |
| 105.8 | credit L22 | L22 | Wikimedia Commons CC BY | — |
| 111.5 | credit L23 | L23 | Wikimedia Commons CC BY | — |
| 116.7 | credit L24 | L24 | Wikimedia Commons CC BY | — |
| 122 | 30s-grid | L25 | Reconstruction (Al) | — |
| 134.6 | credit L27 | L27 | Wikimedia Commons CC BY | — |
| 140.2 | credit L28 | L28 | — | — |
| 145.4 | name L29 | L29 | Reconstruction (Al) CK | — |
| 152 | 30s-grid | L30 | Wikimedia Commons CC BY 2.5 | — |
| 154.7 | credit L30 | L30 | Wikimedia Commons CC BY 2.5 | — |
| 162.1 | name L31 | L31 | Reconstruction (Al) Ma | — |
| 164.7 | name L32 | L32 | (Al) Keller | — |
| 182 | 30s-grid | L34 | — | — |
| 206.7 | name L40 | L40 | — | — |
| 212 | 30s-grid | L40 | te | — |
| 218.4 | credit L42 | L42 | Joeykentin Commons BY-SA | — |
| 227.3 | credit L43 | L43 | Wikimedia Commons CC BY 2.5 | — |
| 242 | 30s-grid | L44 | truction (Al) | truction |
| 257.7 | card L47_END | L47_END | Human Archives | — |

Unexpected words outside schematic shots: **2**

## 2. Credit read-back vs credits.md

| shot | expected (credits.md) | OCR of credit band | similarity | result |
|---|---|---|---|---|
| L03 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L08 | NASA Landsat . Wikimedia Commons . Public domain | NASA aaa te al Commons: Public domai | 0.643 | FAIL |
| L12 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA | 0.902 | PASS |
| L20 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L21 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L22 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L23 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L24 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L27 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L28 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L30 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L42 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L43 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |

Credit read-back failures: **1**

## 3. freezedetect (−50 dB, ≥ 2 s)

Frozen segments: **0** (none)

## 4. Loudness

Integrated: **-14.0 LUFS** (target ≈ −14) · True peak: **-1.3 dBTP** (≤ −1) → PASS

