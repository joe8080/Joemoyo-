---
name: ai-video-advert
description: Produce a short cinematic VIDEO ADVERT / commercial end to end — brief, ad copy + shot list, punchy pro voiceover, native-sound AI hero clips (sizzle/steam/pours), a ducked music bed, brand/text cards, one-pass assembly, and a review-before-publish gate. Handles two brand-safety modes — an unofficial concept/spec ad, or a real-logo PITCH build where the actual brand logo is integrated on packaging, a corner bug and the end-card. Use when the user wants to make an advert, commercial, "ad for X", food/product promo, spec ad, pitch video for a brand, or asks to brand an advert / add the real logo. Cost-controlled: native-audio AI video is the pricey part, so preflight every batch and cap the clip count.
---

# AI Video Advert Builder

Turns a product or brand into one finished, cinematic **short advert** (default ~90s, 16:9)
the way a real commercial is cut — hero macro shots, a craving/desire build, people
enjoying it, and a brand end-card — over a punchy pro voiceover, native sound, and a ducked
music bed. Hands you an MP4 to review before anything is published. It is both a **guided
pipeline** (the phases below) and a **spec** (the two brand-safety modes + the locked
logo-branding technique) so every advert is repeatable.

> Built from the Favorite Chicken & Ribs job (July 2026): 90s, 12 native-sound clips, Adam
> VO, real logo on the shopfront fascia + a corner bug + the end-card, for a pitch to the
> brand's owner. See `references/advert-playbook.md` for the worked example and the exact
> model economics.

## Pick the brand-safety mode FIRST (this changes everything downstream)

Ask the user which one before building. It decides whether the real trademark appears.

- **Mode A — Concept / spec ad** (portfolio, showreel, "what an ad could look like").
  On-screen "concept spec ad — not affiliated with or endorsed by <brand>" line; evoke the
  brand's **palette + name/tagline only**; **NO pixel-exact trademark/logo**. Safe to share
  publicly as your own creative work.
- **Mode B — Real-logo pitch build** (you are pitching TO that brand or its owner/decision
  maker). Source and integrate the **real logo**; **remove the disclaimer**. Only legitimate
  when it's a genuine private pitch to the brand itself — never to pass a spec ad off as an
  official campaign to the public.

If the user hasn't said, ask. When in doubt, default to Mode A.

## Cost discipline (read first)

Native-audio AI video is the expensive part of an advert — everything else is cheap.

> 📕 **Read `references/advert-playbook.md` before any generation** — per-model prices, the
> logo-sourcing trick, asset re-hosting, and the delivery/proxy routing.

1. **Preflight every clip batch.** Higgsfield `generate_video` accepts `get_cost: true` — a
   FREE exact quote without submitting. Also check `Highfield balance` / `vidiq_balance`
   before the batch.
2. **Cap the clip count.** ~12–14 hero clips at ~6s each carries a 90s ad. Don't over-shoot.
3. **Cheapest capable video model with sound.** `kling3_0` std, **sound on** ≈ **12 cr/6s**
   is the workhorse. Reserve `seedance_2_0` +audio (~54 cr) for one marquee shot if at all.
   Seed a tricky shot with a `cinematic_studio_2_5` still (2 cr) as `start_image` for control.
4. **Stop-and-ask gate.** Stop if any single step quotes **>150 credits** or the running
   total tracks **>500**. Confirm big numbers with the user first.
5. **Free knowledge first.** `models_explore(recommend)` and `get_workflow_instructions` are
   free — load them before building; never guess a model.
6. **Budget:** a 90s native-sound ad ≈ **~350–450 credits** total (≈12–14 clips ×12 + VO ~15
   + music ~20–50 + a few stills + cards ~20 + compose ~25). Adding **real-logo branding**
   (Mode B) ≈ **+75–120 credits**.

## Pipeline (work these phases in order)

### Phase 0 — Brief
Lock: brand + product, **mode A or B**, length (default ~90s), ratio (default 16:9 for
YouTube/TV; offer a 9:16 cut for Reels/TikTok/Shorts after). Confirm the ad voice
(default **Adam** `pNInz6obpgDQGcFmaJgB` — punchy pro; or Joe OGX `JKDjSisy3uHa5eqQYalW`).

### Phase 1 — Concept + ad copy + shot list
Write the whole thing before generating anything. Structure the ~12–14 scenes as a real
commercial arc: **hero product macro → craving/desire build → people enjoying/sharing →
brand end-card + CTA**. One continuous punchy VO read (~85s). Save to
`outputs/<advert-slug>/script.md` (Mode A includes the concept-spec-ad line; Mode B does not).

### Phase 2 — Voiceover
`vidiq_voiceover_generate` with the ad voice, the ~85s of copy as one read. Keep it short,
present-tense, sensory. (Adam reads energetically; budget accordingly.)

### Phase 3 — Music bed
`vidiq_generate_music` — upbeat, appetite/energy, ~90s. It sits ducked under the VO.

### Phase 4 — Hero clips (WITH sound)
`kling3_0` (std, **sound on**, 16:9) for the batch; `get_cost:true`-preflight first. ~6s
each. Append the locked product art-direction suffix (see playbook) to every prompt. Seed
awkward shots (assembly, packaging) with a `cinematic_studio_2_5` still as `start_image`.
Poll async jobs; failures auto-refund. Log every clip URL in `outputs/<advert-slug>/manifest.md`.

### Phase 5 — Brand/text cards
`vidiq_motion_graphics`: title/wordmark, tagline, any offer/price, and the end-card CTA.
Mode A end-card includes the small "concept spec ad" line; Mode B does not.

### Phase 6 — Assemble (ONE compose)
`vidiq_compose` (16:9): scenes = hero clips (`keepNativeAudio:true` for the sizzle) + cards;
`voiceover` over the top; `music` bed with `duckTo` under the VO; fade transitions. 90s fits
one compose (≤240s / ≤50 scenes). Transcribe every signed URL EXACTLY — a 1-char typo 403s.

### Phase 7 — Real-logo branding (Mode B only) — the LOCKED technique
The exact logo is **guaranteed only on overlays / near-static composites — NEVER
retro-stamped onto moving footage** (AI can't hold a trademark stable frame-to-frame on a
sizzling close-up, and a warped logo reads worse than none to a brand boss). Put it exactly
where a logo lives on a real ad:

1. **Corner "bug"** — `vidiq_compose` `image` overlay: small, ~0.9 opacity, top corner, held
   across the whole ad.
2. **Branded end-card** — `vidiq_motion_graphics` with an `image` node = the real logo, big;
   tagline + CTA; disclaimer removed.
3. **Composited packaging / shopfront** — generate a box/cup/window/fascia still, composite
   the real logo onto it with ImageMagick inside Higgsfield `sandbox_exec`, then animate with
   gentle `kling3_0` image-to-video so the logo holds. Re-host the composite (see playbook)
   and slot it in as a hero scene.

Sourcing the logo and re-hosting built assets: see `references/advert-playbook.md`.

### Phase 8 — Deliver & QA
Poll → download the render (remotionlambda S3 is proxy-allowed) → local ffmpeg to a **720p**
preview into `outputs/<advert-slug>/` (GitHub plays MP4 <100MB inline) and a **540p** (<30MB)
for chat via `SendUserFile`. Optional Google Drive doc with the GitHub browser-play link.
Extract 2–3 QA frames to confirm the logo/branding reads correctly. **No publish without an
explicit OK.**

## Outputs layout

```
outputs/<advert-slug>/
  script.md          # concept, ad copy, shot list
  manifest.md        # every job ID + asset URL + running spend
  clips/  cards/     # notes / any local copies
  <slug>-advert-720p.mp4          # Mode A / unbranded preview (repo, browser-play)
  <slug>-advert-BRANDED-720p.mp4  # Mode B branded preview (repo, browser-play)
```

## Guardrails

- **Review before publish.** Nothing goes public until the user says so.
- **Real logos = Mode B only, and only for a genuine pitch to that brand.** Never present a
  spec ad as an official campaign; never brand a competitor's ad or mislead.
- **Honesty about the logo.** Tell the user up-front that the exact logo lives on the
  overlays/composites (bug, end-card, packaging), not stamped on the moving food shots —
  that's where a real ad puts it anyway.
- **Cost gate.** Preflight, show the number, stop at >150/step or >500 total, confirm balance.
