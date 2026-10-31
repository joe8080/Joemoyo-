# QA report — OGX_Ishango_v1.2_PROOF.mp4

Runtime: **87.32 s (1:27.3)** — target 60–90 s → PASS

## 1. OCR text inventory (rendered frames)

| t (s) | why | shot | text read (conf ≥ 70) | unexpected |
|---|---|---|---|---|
| 2 | 30s-grid | L08 | DR CONGO Lake Edward NASA Landsat Wikimedia Commons Public domain | — |
| 3.1 | credit L08 | L08 | DR CONGO go. Lake Edward NASA Lands Wikimedia Commons Public domain | — |
| 22.3 | credit L12 | L12 | Joeykentin Wi dia Commons CC BY-SA 4.0 | dia |
| 32 | 30s-grid | L14 | Reconstruction (Al) Al | — |
| 40.2 | credit L16 | L16 | SE Commons CC BY-SA | — |
| 45.5 | credit L17 | L17 | Joeykentin Wikimedia Commons CC BY-SA 4.0 | — |
| 52.3 | credit L18 | L18 | ah Joeykentin Wikimedia Commons CC BY-SA 4.0 | — |
| 57.7 | credit L19 | L19 | Joeykentin Wikimedia Commons CC BY-SA 4.0 | — |
| 61.0 | credit L20 | L20 | 168 Joeykentin Wikimedia Comm CC BY-SA 4.0 Wikimedia Comm BY 2.5 | — |
| 62 | 30s-grid | L20 | 168 Joeykentin Wikimedia Comm CC BY-SA 4.0 Wikimedia Comm BY 2.5 | — |
| 66.3 | credit L21 | L21 | 13 11 Wikimedia Commons CC BY 2.5 loeykentin Wikimedia Commons cc BY-SA 4.0 | loeykentin |
| 72.1 | credit L22 | L22 | Joeykentin Wikimedia Commons cc BY-SA 4.0 Wikimedia Commons CC BY 2.5 | — |
| 77.8 | credit L23 | L23 | 21 11 ll Joeykentin Wikimedia Commons cc BY-SA 4.0 Wikimedia Comm BY 2.5 | — |
| 83.9 | credit L24 | L24 | 10 yk Wikimedia Comm CC BY-SA 4.0 Wikimedia Comm CC BY 2.5 | — |

Unexpected words outside schematic shots: **2**

## 2. Credit read-back vs credits.md

| shot | expected (credits.md) | OCR of credit band | similarity | result |
|---|---|---|---|---|
| L08 | NASA Landsat . Wikimedia Commons . Public domain | NASA le te Commons: Public domai | 0.725 | FAIL |
| L12 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA | 0.902 | PASS |
| L16 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L17 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L18 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C€ | 0.920 | PASS |
| L19 | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L20 (line 1) | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C€ | 0.920 | PASS |
| L20 (line 2) | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L21 (line 1) | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L21 (line 2) | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L22 (line 1) | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L22 (line 2) | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L23 (line 1) | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L23 (line 2) | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |
| L24 (line 1) | Joeykentin . Wikimedia Commons . CC BY-SA 4.0 | Joeykentin Wikimedia Commons CC BY-SA 4.C | 0.930 | PASS |
| L24 (line 2) | Albert1ls . Wikimedia Commons . CC BY 2.5 | Albertils Wikimedia Commons CC BY 2.5 | 0.923 | PASS |

Credit read-back failures: **1**

## 3. freezedetect (−50 dB, ≥ 2 s)

Frozen segments: **0** (none)

## 4. Loudness

Integrated: **-14.0 LUFS** (target ≈ −14) · True peak: **-1.3 dBTP** (≤ −1) → PASS

