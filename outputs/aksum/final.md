# Aksum final assembly plan + log

## Architecture
7 compose segments (vidiq_compose, VO baked in per segment for sync) → media_import_url
each → Higgsfield explainer_video plain join (free) → final MP4 1920×1080.

| Seg | VO chunk (dur) | Target len | Content |
|---|---|---|---|
| S1 | C1 (76.7s) | 79s | Cold open B1,B2,B3,B4 → TITLE CARD → Act I B6–B13 → 4-powers card |
| S2 | DDA (96.4s) | 99s | Periplus + Ge'ez: B7,DDA1,B11,B12,B18,DDA2,B37,DDA2(alt pan),B3 |
| S3 | C2 (89.4s) | 92s | Coins+stones: B15,B16c,B17,B19,B20,COIN CARD,B22c,B23,B24,B25,B26c,B27,33m CARD |
| S4 | C3 (81.3s) | 84s | Theft+faith: B28,B29,B30,B31c,B33,B34,B35,B36,B37,B38,B39c,B40 |
| S5 | DDB (74.4s) | 77s | Kaleb+refugees: DDB1,B13,B42,DDB2,B12,B33,B38,B40 |
| S6 | GUDIT (43.5s) | 46s | Fall: B41,GUD1,B45,GUD2,B23 |
| S7 | C4 (75.0s) | 78s | Decline+close: B43,B44,B45,B46,B47,B48,B49c,B50,B51,OUTRO CARD |

Total ≈ 555s ≈ 9:15. Suffix c = hero clip; all stills get Ken Burns (varied zoom/pan).
Compose cost ≈ 139 credits. Music: none in v1 (add via YouTube audio library or v2).
Captions: YouTube auto-captions v1 (compose caption text not wired; explainer subs need
per-block audio).

## Hero clip jobs (kling3_0_turbo, 5s, 1080p, 10cr each)
| # | Beat | Job ID | Status |
|---|---|---|---|
| 1 | B1 map push-in | 3cbb059c-947f-425b-988b-13997233fbe3 | pending |
| 2 | B2 fourth glow | a7302d03-fa5c-4e1a-8e57-fea6533f6d29 | pending |
| 3 | B9 harbor alive | 7a1fbd36-56bc-4bd8-8a0e-c42ffaa973ea | pending |
| 4 | B16 coins tumble | d5bd6c1d-239b-444a-98ae-6fb970260925 | pending |
| 5 | B22 crane up stele | 48ad5893-1b1e-4081-8033-d687081046b0 | pending |
| 6 | B26 stele falls | 45e6fe47-fa71-419e-854b-ee94dbbb414b | pending |
| 7 | B31 obelisk rises | 4a5ad5db-7495-4e71-aa4d-12614ff36e2d | pending |
| 8 | B39 chapel dolly | de1647e7-1b32-4244-a5c5-caa687432458 | pending |
| 9 | B49 dawn stelae | _queued (slot cap)_ | |
| 10 | GUD1 city burns | _queued (slot cap)_ | |

## Spend tracker (approx)
Stills 3+88+12=103 · VO ~130 · titles 15 · thumbs 44 · cards ~10 · heroes 100 ·
compose ~139 · misc 5 → **~545 total** (balance was 2,453; resets Jul 6)
