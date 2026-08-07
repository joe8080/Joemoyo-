# Chilling Receipts of Declassified Global Statecraft — asset manifest

- **Slug:** `chilling-receipts-statecraft`
- **Style:** OGX declassified-receipts (locked house style)
- **DB record:** `content_ideas` → *THE VAULT FILES: What 39 Declassified Records Prove About Hidden History* (status `scripting`)
- **Runtime:** 2:54 (174s) with cards only; ~3:18 once the six motion plates are folded in
- **Status:** assets in / built — **awaiting narration VO**

## Verification

Checked against OGX Supabase `qvlllknedilztozxwscj` on 2026-08-07. Every major
card resolves to a `citations` row with `verified: true`:

| Card | Citation in DB |
| --- | --- |
| s03 / s04 Stasi | Stasi Records Archive — 111 km of GDR State Security files opened (1992–) |
| s05 Katyn | Katyn Massacre US Records Release, National Archives (2012) |
| s07 Gladio | Andreotti disclosure + European Parliament resolution (1990) |
| s08 Tonkin | NSA SIGINT releases (2005–2008) — the second attack did not happen |
| s09 Iran | CIA acknowledges TPAJAX — NSArchive EBB 435 / FRUS (2013) |
| s11 Barr Doctrine | Imperial Prerogative: Panama Invasion and the Barr Doctrine |
| s12 Family Jewels | CIA FOIA Reading Room, released 25 June 2007 |
| s13 COINTELPRO | FBI Vault — declassified COINTELPRO files |

### ⚠ Correction applied — slide 3

The card as supplied read **"1 IN 63 — CITIZENS WAS A FULL-TIME STASI OFFICER."**
That is wrong, and it contradicted the *500,000 informal informants* box beside
it. Roughly 91,000 full-time officers against a population of ~16.4M is about
**1 in 180**; the well-known 1-in-63 figure is Koehler's ratio for **informants
and collaborators**.

The composition composites a corrected label over the original — the card now
reads *"1 IN 63 / CITIZENS WAS AN INFORMANT OR COLLABORATOR"*, which keeps the
striking number and makes it true. The overlay is a stopgap: **regenerate
`s03_generated.webp` with the corrected line in the design tool** so the
underlying asset is right and the composite can be dropped.

### Deck vs dossier — known gap

The DB dossier lists key points this deck does not cover: the Lumumba
assassination evidence chain, Indonesia 1965, the Hanslope Disclosure (Britain
burning colonial records), Unit 731, and the Church Committee. Only Tonkin
overlaps. Lumumba and Hanslope are core OGX territory — **scoped to Part 2.**

## Large files held outside git

The six Highfield motion plates render to a CDN that some environments cannot
reach. Download them and drop them into `video/broll/` under these exact names,
then re-run `node build-composition.mjs` — the b-roll scenes fold themselves in.

Model `seedance_2_5`, 5s, 16:9, 7.5 credits each.

| File | Shot | Job ID |
| --- | --- | --- |
| `01_stasi_corridor.mp4` | Filing-cabinet corridor, slow dolly | `88670925-bacc-41a6-b5f2-c4398883cd8b` |
| `02_birch_forest.mp4` | Birch forest at cold dawn (Katyn) | `f689a3aa-4e4f-43a9-a308-0297573c73ab` |
| `03_weapons_cache.mp4` | Buried weapons cache at night (Gladio) | `3d5e48f0-1e02-47ed-82b3-077bab49c632` |
| `04_radar_scope.mp4` | 1960s naval radar scope (Tonkin) | `202ba8a9-1b42-43ca-8094-a51d9c104d4c` |
| `05_oil_derrick.mp4` | Oil derrick at dusk (Iran) | `dd6eaa23-547a-4c40-bf0c-d972953d753c` |
| `06_server_vault.mp4` | Server vault, red status lights (closing) | `f906525e-b1c3-4feb-b7b2-7dd834319f29` |

Base URL: `https://d8j0ntlcm91z4.cloudfront.net/user_39AwNqqHnEuHKHkz07Lufl4IL4u/hf_20260807_074324_<JOB_ID>.mp4`

## Scene index

Timings are placeholders derived from card read-time. **They are not the final
cut** — retime against the VO by editing `hold` in `build-composition.mjs`.

| # | Scene | Hold | Seam vector |
| --- | --- | --- | --- |
| s01 | Title — Chilling Receipts | 7s | fade in |
| s02 | The Unbreakable Rule — 39 citations | 6s | current (left) |
| b01 | *B-roll — Stasi corridor* | 4s | current |
| s03 | The Stasi — Europe **(corrected)** | 13s | current |
| s04 | The 1991 Reckoning | 10s | current |
| b02 | *B-roll — birch forest* | 4s | current |
| s05 | Katyn — the 50-year lie | 14s | current |
| s06 | Nazi criminals, Western payroll | 12s | current |
| b03 | *B-roll — weapons cache* | 4s | current |
| s07 | Operation Gladio | 12s | current |
| b04 | *B-roll — radar scope* | 4s | current |
| s08 | Gulf of Tonkin — Asia | 12s | current |
| b05 | *B-roll — oil derrick* | 4s | current |
| s09 | Iran 1953 — Operation TPAJAX | 12s | current |
| s10 | The Americas — regime change blueprint | 13s | current |
| s11 | The Barr Doctrine | 12s | current |
| s12 | CIA Family Jewels | 11s | current |
| s13 | MLK & COINTELPRO | 13s | current |
| s14 | The Synthesis | 16s | **Z forward** — deeper into the thought |
| b06 | *B-roll — server vault* | 4s | current |
| s15 | The Digital Vault — closing | 11s | **Z back** — arrival |

## Audio

**Not yet supplied.** Joe's masters live at
`C:\Users\Joe\claude and ogx\ogx_pipeline\audio` on Windows, which no cloud
session can read — see `assets/ogx/README.md` for transfer routes.

| Track | File | Notes |
| --- | --- | --- |
| VO master | — | drop into `audio/narration/`, then retime `hold` values |
| Music bed | — | `audio/music/`, sit −26 LUFS under VO |
| SFX | — | `audio/sfx/` — stamp hits on each card entry |

Word-level caption timing needs either an existing `.srt`/`.vtt`/`.json`
(import with `hyperframes transcribe`) or a whisper model, whose download host
is blocked by this environment's network policy.
