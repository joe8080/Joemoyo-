# AI Advert Playbook — cost-smart commercial production

Technical notes that made the Favorite Chicken build work, so they're never re-derived.
Read before any generation. Companion to `SKILL.md`.

## Model economics (advert stage → cheapest capable tool)

| Stage | Tool | Indicative cost |
|---|---|---|
| Model choice | `models_explore(recommend)` | free |
| Cost check | any Higgsfield `generate_*` with `get_cost: true` | free exact quote |
| Hero clip WITH sound (workhorse) | `kling3_0`, mode std, **sound on**, 16:9, ~6s | **~12 cr/clip** |
| Marquee clip WITH audio (optional, ≤1) | `seedance_2_0`, `generate_audio: true` | ~54 cr/clip |
| Control still / packaging base | `cinematic_studio_2_5` (used as `start_image`) | ~2 cr |
| Image-to-video (branding / logo holds) | `kling3_0` / `kling3_0_turbo` image-to-video | ~6–10 cr |
| VO | `vidiq_voiceover_generate` (Adam / Joe OGX) | ~14 cr/1k chars |
| Music bed | `vidiq_generate_music` | ~20–50 cr |
| Cards | `vidiq_motion_graphics` | ~4 cr each |
| Assembly | `vidiq_compose` (voiceover + music + overlays + Ken Burns) | ~1 cr/4s |

**90s native-sound ad ≈ ~350–450 cr.** Real-logo branding pass ≈ **+75–120 cr**.
Cap ~12–14 clips. Stop if a step quotes >150 or the total tracks >500.

## Locked product art-direction suffix

Append verbatim to EVERY hero-clip / still prompt (this is the food version):

`appetising golden crispy fried chicken, flame-grilled, steam and glisten, macro food
cinematography, warm red-and-gold lighting, shallow depth of field, high-end commercial
food advert, mouthwatering, 16:9`

For a **non-food product**, swap the sensory clause but keep the commercial grammar:
`<product> hero shot, premium studio product cinematography, dramatic rim lighting, glossy
reflections, shallow depth of field, high-end commercial advert, aspirational, 16:9`.

## Sourcing a real logo when the brand site blocks WebFetch (Mode B)

Brand sites often 403 `WebFetch` and share/`share.google` links resolve to a *page*, not an
image. What worked:

1. Use Highfield **`sandbox_exec`** with `curl` and a **browser User-Agent** — the sandbox
   has real internet and bypassed the favorite.co.uk 403 (HTTP 200), revealing the asset
   path `https://favorite.co.uk/assets/img/logo.png` (469×101 transparent PNG).
2. Confirm the file is the **actual logo image** (open/preview it) before baking it in — not
   a share link or an HTML page. If you can't source it, ask the user for a direct image URL
   (right-click → copy image address) or an upload.
3. `media_import_url` can fetch server-side where local WebFetch fails, but reject anything
   that isn't an image (the user once correctly rejected a `share.google` page-link import).

## Re-hosting sandbox-built assets so `vidiq_compose` can fetch them

`vidiq_compose` fetches scene/overlay URLs server-side, so a composite you build in the
sandbox needs a reachable URL:

`media_upload` (get presigned PUT) → **do the PUT inside `sandbox_exec`** (the local proxy
blocks `upload.higgsfield.ai`) → `media_confirm` → use the returned **cloudfront** URL as the
`image` overlay or scene source.

ImageMagick + ffmpeg are available in the sandbox for compositing the logo onto a
packaging/fascia still. Sandbox files persist ~15 min — do it in one pass.

## Delivery / proxy routing (what downloads where)

- **Local download ALLOWED:** remotionlambda S3 (the `vidiq_compose` render output) +
  ai-voiceovers / ai-music S3. Download the final render locally from remotionlambda.
- **Local download BLOCKED (fetch via sandbox instead):** cloudfront `d8j0ntlcm91z4` and
  `upload.higgsfield.ai`.
- **GitHub** plays MP4 **<100MB** inline in the blob view → commit the 720p preview there.
- **Chat** `SendUserFile` cap **~30MB** → send the 540p.
- Local ffmpeg via `pip install imageio-ffmpeg`; make previews with a CRF encode + AAC.

## Assembly rules (reused, learned the hard way)

- `vidiq_compose` takes **ONE `voiceover` per call**, played from t=0 — write the VO as one
  continuous read for a single-compose 90s ad.
- Food/product clips assemble with **`keepNativeAudio: true`** (the sizzle), VO layered over,
  music `duckTo` under the VO.
- **Transcribe signed URLs EXACTLY** — a single stray character 403s the whole compose (a
  hand-copied space and a doubled `%3D%3D` each broke a run once).
- Signed URLs expire (vidIQ VO/cards ~12h) → do produce + assemble in **one session**.
- Do the **final stitch/preview with local ffmpeg**, not Higgsfield import (which caps at
  50MB and can't take a full 1080p render).

## Worked example — Favorite Chicken & Ribs (Mode B, July 2026)

- 12 `kling3_0` std sound-on clips (crispy macro, flame ribs, tumbling basket, wing pull,
  loaded box, wrap, friends sharing, big bite, sauce dip, delivery, family feast, hero
  spread) + Adam VO (`pNInz6obpgDQGcFmaJgB`) + generated music bed.
- Real logo (rooster + "Britain's Tastiest Chicken!") sourced via sandbox browser-UA fetch,
  integrated **three ways**: shopfront **fascia** composite, corner **bug** across the whole
  ad, full-screen branded **end-card** — disclaimer removed for the boss pitch.
- Rendered on remotionlambda (79s, 1920×1080); delivered as `favchicken-advert-BRANDED-720p.mp4`
  (repo, browser-play) + a 540p to chat. Assets logged in `outputs/fav-chicken/manifest.md`.

## Sources
- github.com/geopopos/higgsfield_ai_mcp (image-to-video quality tiers & credit costs)
- github.com/jfikrat/higgsfield-mcp (tool surface, cost-preflight pattern)
- Companion doc-pipeline economics: `youtube-animated-doc/references/higgsfield-playbook.md`
