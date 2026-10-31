# QA report — OGX_Ishango_v1.0_REVIEW.mp4

Runtime: **285.24 s (4:45.2)** — target 4:30–5:30 → PASS

## 1. OCR text inventory (rendered frames)

| t (s) | why | shot | text read (conf ≥ 70) | unexpected |
|---|---|---|---|---|
| 2 | 30s-grid | L01 | — | — |
| 15.8 | credit L03 | L03 | Commons CC BY-SA | BY-SA |
| 27.6 | card L06 | L06 | The Ishango bone OrigineX Human Archives | — |
| 32 | 30s-grid | L07 | — | — |
| 40.8 | credit L08 | L08 | NASA Lands Wikimedia Commons Public domain | Lands, Public, domain |
| 46.8 | name L09 | L09 | — | — |
| 52.6 | name L10 | L10 | 54 Je de | — |
| 61.6 | credit L12 | L12 | Joeykentin Wikimedia CC BY-SA 4.0 | BY-SA |
| 62 | 30s-grid | L12 | Common BY-SA 4.0 Joeykentin | Common, BY-SA |
| 92 | 30s-grid | L18 | Reconstruction (Al) | — |
| 105.5 | credit L20 | L20 | Wikimedia Comm CC BY 2.5 | Comm (schematic line-art read as letters; check grab) |
| 111.2 | credit L21 | L21 | — | — |
| 117.4 | credit L22 | L22 | — | — |
| 122 | 30s-grid | L23 | Wikimedia Commons CC BY | — |
| 123.5 | credit L23 | L23 | Wikimedia Commons CC BY | — |
| 129.1 | credit L24 | L24 | — | — |
| 149.2 | credit L27 | L27 | Wikimedia Commons CC BY | — |
| 152 | 30s-grid | L27 | Wikimedia Commons CC BY | — |
| 155.2 | credit L28 | L28 | Wikimedia Commons CC BY | — |
| 160.6 | name L29 | L29 | Reconstruction (Al) | — |
| 170.5 | credit L30 | L30 | Wikimedia Commons CC BY 2.5 | — |
| 178.3 | name L31 | L31 | Reconstruction (Al) Ma | — |
| 181.3 | name L32 | L32 | Reconstruction (Al) “Olivier Keller | — |
| 182 | 30s-grid | L32 | Reconstruction (Al) Keller | — |
| 212 | 30s-grid | L37 | aN | — |
| 227.3 | name L40 | L40 | — | — |
| 241.0 | credit L42 | L42 | Joeykentin CC BY-SA 4.0 | BY-SA |
| 242 | 30s-grid | L42 | Joeykentin Wikimedia Commons CC BY-SA 4.0 | BY-SA |
| 250.3 | credit L43 | L43 | Wikimedia Commons CC BY 2.5 | — |
| 272 | 30s-grid | L45 | — | — |
| 282.7 | card L47_END | L47_END | Human Archives | — |

Unexpected words outside schematic shots: **9**

## 2. Credit read-back vs credits.md

| shot | expected (credits.md) | OCR of credit band | similarity | result |
|---|---|---|---|---|
| L03 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.0 | 0.953 | PASS |
| L08 | NASA Landsat . Wikimedia Commons . Public domain | NASA Landsat Wikimedia Commons: Public domain Lows | 0.898 | FAIL |
| L12 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA | 0.902 | PASS |
| L20 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L21 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L22 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L23 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L24 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L27 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L28 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L30 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L42 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.0 | 0.953 | PASS |
| L43 | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |

Credit read-back failures: **1**

## 3. freezedetect (−50 dB, ≥ 2 s)

Frozen segments: **0** (none)

## 4. Loudness

Integrated: **-14.0 LUFS** (target ≈ −14) · True peak: **-1.4 dBTP** (≤ −1) → PASS

