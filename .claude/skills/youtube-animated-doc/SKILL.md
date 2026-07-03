---
name: youtube-animated-doc
description: Produce a 10–15 minute animated cinematic history documentary for the OrigineX Human Archives YouTube channel, end to end — topic validation, high-CTR title + thumbnail, a hook-first script, pro AI voiceover, AI period-accurate visuals with Ken Burns/parallax motion, a few AI hero video clips, motion-graphic title cards, music, burned captions, assembly, and a review-before-upload gate. Use when the user wants to make an animated/motion history video, a faceless documentary, or a new OrigineX episode. Cost-controlled: cheap-first visuals, expensive AI video reserved for a handful of hero beats, and a credit-estimate gate before any big spend.
---

# YouTube Animated Documentary Builder (OrigineX)

Turns a single history topic into one finished, cinematic, "animated" 10–15 minute
documentary the way the top history channels do it — then hands you an MP4 to review
before anything is published. It is both a **guided pipeline** (the ordered phases below)
and a **house-style spec** (Part H) so every episode looks and sounds like the same channel.

> Channel: **OrigineX Human Archives** (`UC_VwS819y4GZgNmYajBvm3Q`). Niche: hidden / erased
> history — African empires, ancient civilizations, colonial economics. UK English.

> 💡 **Why this exists.** OrigineX had 533 videos but ~150 views each: high volume, low
> retention, weak titles/thumbnails. This skill inverts that — **fewer, far better,
> single-topic animated flagships**. Quality and consistency over quantity.

## What "animated" means here

Not cartoon animation. **Cinematic motion-documentary**: AI period-accurate images that
pan / zoom / parallax (Ken Burns), motion-graphic title & stat cards, and a *small* number
of true AI video clips (Sora/Veo/Seedance/Highfield) for dramatic beats — over a pro
voiceover, music bed, and burned captions. Optional short illustrated/animated sequences
for abstract concepts. This is the affordable, scalable look modern history channels use.

## Cost discipline (read first)

Credits are finite. Follow these or you'll blow a month's budget on one video:

1. **Cheap-first visuals.** Default = AI **stills** + Ken Burns/parallax (`vidiq_compose`
   ≈ 1 credit / 4s) + motion graphics. These carry ~85% of screen time.
2. **Ration AI video.** True AI video clips (`vidiq_generate_video`, Highfield
   `generate_video`) are the expensive line item (duration × per-sec rate × 20). Cap at
   **6–10 hero clips, 4–6s each** per episode. Never fill 15 min with generated video.
3. **Estimate gate.** Before any generate step, call `vidiq_balance`, compute an exact
   per-video estimate, and confirm the number with the user. Nothing big runs unapproved.
4. **Cheapest capable tool per stage.** Highfield `explainer_video` assembly is free;
   `vidiq_compose` is cheap. Prefer them over pricier paths when quality is equal.
5. **Batchable.** Write the script and all image prompts first, then generate in batches so
   nothing is regenerated. Poll async jobs with `vidiq_job_poll` (refunds on failure).

## Pipeline (work these phases in order)

### Phase 0 — Topic validation (cheap)
- Confirm the topic has demand. Optional: `vidiq_outliers`, `vidiq_keyword_research`,
  `vidiq_similar_channels` to check what's working in-niche. Lean on OrigineX's proven
  winners (Mansa Musa/Mali, Aksum, Kush, African-Roman emperors).
- Output: one locked topic + the angle (the "hidden truth" hook).

### Phase 1 — Title + thumbnail concept (lock BEFORE building)
- `vidiq_generate_titles` → `vidiq_score_title`; keep the highest-CTR title. 3–5 words of
  punch, curiosity gap, no clickbait lie. Pattern that works for OrigineX:
  *"Aksum: The African Empire That Outlasted Rome."*
- `vidiq_generate_thumbnail` → `vidiq_score_thumbnail` → `vidiq_refine_thumbnail` until the
  score is strong. One bold subject (face/artifact), high contrast, ≤3 words of overlay.
- Title + thumbnail are a **matched pair** — decide them together, first.

### Phase 2 — Script (hook-first)
- 10–15 min ≈ **1,800–2,300 words**. Structure:
  - **0:00–0:15 hook** — a shocking claim or question, before the title card.
  - **Title card** (motion graphic).
  - **3–5 acts**, each one scene beat = one image/clip. End each act on a mini-cliffhanger.
  - **Payoff + "why this was erased"** close, then a subscribe CTA.
- Write the script as a **beat sheet**: for every ~15–25s beat, capture (a) the VO line,
  (b) a visual prompt, (c) whether it's a still (default) or a hero AI clip.
- Save to `outputs/<topic>/script.md`. This beat sheet drives every later phase.

### Phase 3 — Voiceover
- Default: `vidiq_voiceover_generate` with a chosen `voiceId` from
  `vidiq_voiceover_list_voices` (deep, documentary tone). ~14 credits / 1,000 chars.
- Script > 5,000 chars → split into chunks, generate each, keep the ordered MP3 URLs.
- Optional upgrade: clone the user's own voice via `vidiq_voiceover_clone_start` /
  `vidiq_voiceover_clone` once they provide a sample.

### Phase 4 — Visuals
- **Stills (bulk):** one cinematic, period-accurate image per beat (~40–70). Generate via
  Highfield `generate_image`, Adobe Firefly, or `vidiq_generate_broll`. Keep a consistent
  art direction string (Part H) in every prompt for a unified look.
- **Hero clips (rationed):** 6–10 short AI video clips for the biggest dramatic beats only
  (`vidiq_generate_video` sora-2/veo-3.1, or Highfield `generate_video`). 4–6s each.
- **Motion-graphic cards:** title card, act cards, stat counters (e.g. "1,700 years"),
  map/quote cards via `vidiq_motion_graphics`.

### Phase 5 — Motion + assembly
- Give **every still** motion: `vidiq_compose` with `kenBurns` (slow zoom/pan, scale
  1.0→1.15, vary focal point) so nothing is static. Add `fade` transitions between beats.
- `vidiq_compose` limits: ≤240s and ≤50 scenes per call → build the 15-min video as a few
  segments, then stitch. Highfield `explainer_video` can also stitch clip+VO blocks (free).
- Lay the VO track over the scenes; drop a low-volume music bed; enable captions.
- Poll each render with `vidiq_job_poll`; collect the signed MP4 URL(s).

### Phase 6 — Final stitch + QA
- Stitch segments in order into the final MP4 (compose or explainer_video).
- QA: audio synced to visuals, no static shots, captions readable, title card correct,
  length 10–15 min, hook lands in first 15s.

### Phase 7 — Deliver & (optional) publish
- Deliver the final MP4 URL + the scored title + thumbnail to the user for review.
- **Never auto-publish.** On explicit approval only, upload via Zapier
  `youtube_upload_video` and set the thumbnail (`youtube_update_video_thumbnail`).
- Write a strong description + tags + pinned comment.

## Part H — OrigineX house style (keep every episode consistent)

- **Art direction (put in every image prompt):** "cinematic, dramatic volumetric lighting,
  historically accurate [era/region], rich earth-and-gold palette, film grain, shallow
  depth of field, epic scale, museum-documentary realism." Match ethnicity and material
  culture to the real history — this is the channel's whole point.
- **Tone:** authoritative, revelatory, respectful; "the history you were never taught."
- **Voice:** deep, measured, documentary narrator (until the user's own voice is cloned).
- **Title card & lower-thirds:** heavy condensed serif/impact font, gold-on-dark.
- **Pacing:** a visual change every 5–8 seconds; never hold a static frame.
- **Cadence:** 1–2 flagship videos/week — not the old 5-a-day firehose.

## Outputs layout

```
outputs/<topic-slug>/
  script.md            # beat sheet: VO + visual prompt + still|clip per beat
  title-thumbnail.md   # chosen title, scores, thumbnail concept + URL
  voiceover/           # VO mp3 chunk URLs
  stills/              # image URLs/prompts per beat
  clips/               # hero AI clip URLs
  cards/               # motion-graphic card URLs
  final.md             # final MP4 URL(s) + QA checklist + publish copy
```

## Guardrails

- Balance-check + estimate before every expensive generate step; get the user's OK.
- Async jobs: always `vidiq_job_poll` to completion; failures auto-refund.
- Nothing publishes without explicit user approval.
- Keep historical claims defensible — this channel's credibility is the brand.
