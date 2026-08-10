# OGX IMAGE PILOT — Mansa Musa I

Five scenes generated from the build sheet's `IMAGE:` briefs to test whether they
produce OGX-looking frames before committing to the full set.

**Model:** Recraft V4.1 (`recraft_v4_1`), 16:9, 1k (1344×768), 1.25 credits each.
Chosen because it accepts an explicit `colors` palette, so the gold-on-near-black
lock is enforced by the model rather than hoped for in prose.

**Shot-type spread** — deliberately varied, to find where the briefs break rather
than where they flatter:

| Scene | Type | Palette passed | Tests |
|---|---|---|---|
| 1 | Wide landscape, held 69s | `#C9A84C` `#1A1A2E` `#6B5B4A` | The single most important frame in the film |
| 18 | Macro object | `#C9A84C` `#1A1A2E` | Whether "one gold rim-light" reads at all |
| 43 | Abstract UI (`utility` variant) | `#C9A84C` `#1A1A2E` `#5A5A5A` | Hardest brief — a database as an image |
| 46 | Architecture, no people | `#1A1A2E` `#8C7B6B` `#C9A84C` | Restraint: a foundation, not a finished mosque |
| 63 | Engraved document | `#0F4C75` `#FFF3CD` `#1A1A2E` | Chapter palette break — no gold at all |

## Results

| Scene | PNG |
|---|---|
| 1 | https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260810_085404_495d8f83-b524-49b0-a983-4d0016ff187d.png |
| 18 | https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260810_085404_d42eb9be-b830-4258-ba5e-37a3b7af33c7.png |
| 43 | https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260810_085404_265ddaaa-3a21-4ec6-86d3-0f9e3ec9b136.png |
| 46 | https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260810_085404_08ec5719-bdc4-4b55-8b12-6f4d2961d0fa.png |
| 63 | https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260810_085404_433d3246-3ef3-41a4-9fd6-8f795e456ca4.png |

## Shot budget for the full episode

70 `IMAGE:` briefs, and they are not all generatable:

- **45 AI-permitted** → ~56 credits to generate.
- **25 archival-locked** → cannot be generated at any price. They need a human to
  source and licence real material (Catalan Atlas sheet 6 from BnF Gallica, the
  Haidara photographs, Ahmad Baba material). The build sheet marks each one.

## Build-sheet header defects — fix before assembly

The header block contradicts its own body on three counts. The body is right.

1. **Scene count:** header says `Scenes: 71`; the body runs to `SCENE 88`.
2. **Runtime:** header says `Runtime target: 14:00`; the last scene ends at
   `17:58`. That is within 20s of the measured narration (18:17), so the body
   silently corrected to the true pace while the header kept the stale target.
3. **Identity moment:** header says `Scene 61 (Ch.7)`; the ⭐ marker is on
   `SCENE 80`.
