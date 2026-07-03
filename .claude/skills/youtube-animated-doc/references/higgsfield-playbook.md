# Higgsfield (Highfield MCP) Playbook — cost-smart video production

Research notes (July 2026) from public Higgsfield docs, community MCP repos, and pricing
guides. Purpose: use Higgsfield well and **cheaply** inside the youtube-animated-doc
pipeline. Numbers are indicative — ALWAYS preflight with `get_cost: true` before spending.

## The golden rules

1. **Preflight everything.** `generate_video` / `generate_image` accept `get_cost: true`
   → returns the exact credit cost WITHOUT submitting a job. Free. Use it before every
   generation batch, and show the user the number for big batches.
2. **Free advice first.** `models_explore(action:'recommend')` recommends the right model
   for a goal — free. `get_workflow_instructions` loads Higgsfield's own professional
   workflow playbooks (e.g. narrated explainer videos) — free. `get_youtube_explainer_presets`
   lists explainer style presets — free. Load these before building; never guess a model.
3. **Image-to-video beats text-to-video for documentaries.** We already generate a still
   per beat. Animating a still (start_image → short clip) costs a fraction of prompting
   Sora/Veo from text, and stays on-model with our art direction:
   - DoP-style image-to-video presets: ~2 credits (lite) / ~6.5 (turbo) / ~9 (standard)
   - Kling 3.0: ~6 credits per short clip; `kling3_0_turbo` for fast single start-frame
   - Seedance 2.0: ~25 credits — mid-tier; `seedance_2_0` when identity consistency matters
   - **Sora 2 / Veo 3.1: ~40–70 credits per clip — avoid for routine beats.** Reserve for
     at most 1–2 marquee shots per episode, if at all.
4. **Quality tiers:** draft at `lite`/turbo tiers; re-render ONLY the shots that make the
   final cut at standard quality. Never draft at top quality.
5. **Assembly is free.** Higgsfield `explainer_video` stitches ordered {video, audio}
   blocks into one MP4 at exact total duration — free; burned subtitles cost ~0.05 credit
   per voiced block (Whisper). Prefer it over paid compose for long-form assembly.
   Cap: 180 blocks × ~10s ≈ 30 min. Voice shorter than a block is centered; slightly
   longer is pitch-safe sped up — so cut VO into per-beat takes for perfect sync.
6. **Check the plan's unlimited models.** Some Higgsfield plans include an unlimited
   low-tier video model (e.g. Soul V2 class). If the user's plan has one, use it for
   drafts/animatics at zero marginal cost. Check `show_plans_and_credits` / `balance`.
7. **Credits refund on failure, not on bad taste.** A completed-but-ugly generation still
   charges. So: strong prompts, consistent art-direction string, small test batch (2–3)
   before a 40-image batch.
8. **Media plumbing.** Web images → `media_import_url` → pass the returned `media_id` in
   `medias[]` (never raw URLs). Prior generations → pass their `job_id`. Poll with
   `job_display`; if a `recovery_tool` is returned, call it immediately.

## Documentary pipeline mapping (cheapest capable tool per stage)

| Stage | Tool | Indicative cost |
|---|---|---|
| Model choice | `models_explore(recommend)` | free |
| Workflow playbook | `get_workflow_instructions('video-explainer')` | free |
| Stills (one per beat) | `generate_image` (Soul or recommended) — preflight batch cost | low per image |
| Hero motion | image-to-video from our stills: DoP lite/turbo or `kling3_0_turbo` | ~2–6.5/clip |
| Marquee shot (optional, ≤2) | Sora 2 / Veo 3.1 | ~40–70/clip |
| VO | compare `generate_audio` (preflight) vs vidIQ voiceover (~14 cr/1k chars) | pick cheaper |
| Assembly + captions | `explainer_video` (+ subtitles font) | free + ~0.05/block |
| Draft animatic | unlimited-tier model if plan includes one | ~0 |

## Revised per-episode budget (13-min, 52 beats)

- ~37–40 stills: preflight; assume low tens to ~200 credits depending on model
- 10 hero clips via image-to-video lite/turbo: **~20–65 credits** (was 500–1,500 via text-to-video)
- VO ~11k chars: ~150 credits (vidIQ) or less via Higgsfield — preflight both
- Assembly 13 min: **free** (explainer_video) + ~3 credits subtitles
- Cards ×5: ~20 credits (vidiq_motion_graphics)
- **Total target: ~250–450 credits** (vs 700–900+ in the vidIQ-only routing)

## Lessons from episode 1 (Aksum, July 2026)

- **Final stitch: use local ffmpeg, not Higgsfield.** `media_import_url` caps at 50MB;
  1080p compose segments run 50–110MB. Download the segment MP4s (the remotionlambda S3
  host is proxy-allowed; cloudfront is NOT) and concat with the static ffmpeg from
  `pip install imageio-ffmpeg` using `-f concat -c copy` — lossless and free.
- **George (ElevenLabs JBFqnCBsd6RMkjVDRZzb) reads ~15 chars/sec**, much faster than
  140wpm plans. Budget ~950–1,000 chars of script per minute of narration.
- **Segments must map 1:1 to VO chunks** (compose takes ONE voiceover per call, played
  from t=0). Write VO chunks to match act boundaries, each ≤240s of scenes.
- Cinema Studio 2.5 stills: 2 credits each, ~5s render, superb quality with the OrigineX
  art-direction suffix. Kling 3 Turbo image-to-video 1080p 5s: 10 credits, ~2 min render.
- Max 8 concurrent Higgsfield jobs (ultra plan) — throttle batches; rate-limit rejections
  cost nothing.
- Signed URLs (vidIQ VO/cards ~12h, Higgsfield cloudfront long-lived): do the whole
  produce-assemble run in one session; transcribe URLs EXACTLY (a 1-char typo 403s).
- vidIQ thumbnail self-scorer is biased toward vlogger thumbs (arrows/faces/smiles);
  don't chase its score for documentary art — 2 iterations max, then human judgment.

## Sources
- github.com/geopopos/higgsfield_ai_mcp (DoP image-to-video quality tiers & credit costs)
- github.com/jfikrat/higgsfield-mcp, github.com/Hikhakk/higgsfield-mcp-unified (tool surface, cost preflight pattern)
- Higgsfield 2026 pricing guides (Kling ≈6 cr, Seedance ≈25 cr, Sora/Veo ≈40–70 cr per clip)
