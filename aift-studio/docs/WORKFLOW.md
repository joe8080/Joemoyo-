# Workflow

Nine stages, one state machine, and a hard stop before anything reaches an audience.

---

## The state machine

```
queued ─▶ researching ─▶ evidence_ready ─▶ drafting ─▶ visual_planning ─▶ rendering ─▶ qa_running ─▶ needs_review
   │           │              │               │              │               │            │              │
   └───────────┴──────────────┴───────────────┴──────────────┴───────────────┴────────────┘              │
                                        ▼                                                                │
                                     blocked ──(reviewer)──▶ drafting                                    │
                                                                                                         │
                        rework_required ◀──(reviewer)────────────────────────────────────────────────────┤
                               │                                                                         │
                               └──▶ drafting                                    (reviewer) ──────────────┘
                                                                                     │
                                                                        approved_for_archive
                                                                                     │
                                                                        (reviewer) ──┴──▶ archived  ■ terminal
```

Three properties are worth stating plainly:

- **No shortcuts.** `queued → needs_review` is illegal. So is `drafting → qa_running`. The engine
  walks the path one edge at a time, and a job resuming mid-way after a rework still passes through
  every state.
- **Two human decisions, in order.** `needs_review → approved_for_archive` and
  `approved_for_archive → archived` both require actor `reviewer`. `needs_review → archived` is not
  an edge at all. The workflow engine has no method that can perform either.
- **`archived` is terminal, and it means stored.** Not published, not scheduled, not queued for
  upload. There is no state after it because there is nothing after it.

The rule is written twice — as a table in `src/lib/workflow/states.ts` and as
`public.aift_transition_allowed` plus a `BEFORE UPDATE` trigger in the migration — so that a direct
SQL update from psql cannot skip review either. A test reads the migration and compares it edge by
edge against the TypeScript table, so the two cannot drift apart unnoticed.

---

## The nine stages

| # | Stage | Deterministic controls | What a model does | Output |
|---|---|---|---|---|
| 1 | **Intake** | Validate the topic, set the reference date, record the policy version, derive an idempotency key from topic + date + format | nothing | `aift_research_job` in `queued` |
| 2 | **Research plan** | Select source classes; reject an empty or restricted scope | Produce a query plan. It fetches nothing and may cite nothing | Search plan JSON |
| 3 | **Evidence** | Fetch each page, deduplicate by URL, store title, publisher, published date, accessed date, excerpt and content hash | Judge relevance only | `aift_source_documents` |
| 4 | **Analyst brief** | Run every claim through the public-safety evaluator | Synthesis with claim ids, confidences and uncertainty notes | Dated brief + `aift_claims` |
| 5 | **Editorial** | Enforce channel voice, banned phrases, and a chapter that carries the counter-case | Angle, titles with honest overpromise ratings, hook, outline, CTA | Editorial JSON |
| 6 | **Script** | **Only public-safe claims are passed in.** Any other figure is unavailable to the writer | Narration, on-screen text, chapters, description, tags | Script JSON + Markdown |
| 7 | **Visual plan** | Scenes, timings, chart data and source stamps are assembled in code from the claim ledger | B-roll prompt text for scenes with no figures | Scene plan + asset manifest |
| 8 | **Render** | Narration synthesised and measured; scenes timed from the measurement; charts pre-rendered in Node | optional atmospheric imagery | MP4, WAV, SRT, poster, HTML |
| 9 | **QA** | Nine gate families, each returning a message, the offenders and a remediation | An independent reviewer critique on a **different model** | Pass, rework or block |

### Why stage 6 is the one that matters

The writer is handed the approved claims and nothing else. A claim that failed the evidence check is
not softened, footnoted or flagged — it is absent. You cannot write an unsupported figure into a
script if the figure was never in the room.

The check that catches the subtle case: **does the stored excerpt actually contain the figure the
claim asserts?** A citation that exists, is real, and simply does not say what the sentence says is
the failure mode nobody notices. `excerptSupportsClaim` normalises `billion`/`bn`, `%`/`per cent`
and thousands separators, then requires every figure in the claim to appear in the stored excerpt.

---

## Idempotency

Every identifier is derived, not generated:

| Record | Key |
|---|---|
| Research job | `user + topic + reference date + job type` |
| Content job | `research job + format` |
| Source document | `research job + canonical URL` |
| Claim | `research job + claim id` |
| Asset | `content job + asset type + storage key` |
| Quality check | `content job + gate + check name` |
| Job run | `job type + idempotency key` |

Re-running a job therefore updates in place. The database expresses the same guarantee as `UNIQUE`
constraints, so the property holds whichever implementation is in use — and a test re-runs a
complete production twice and asserts the counts are unchanged.

`JobRunner.trigger` returns `{ runId, deduplicated }`. A second firing with the same key does no
work, records why, and returns the original run id.

---

## Retries

Bounded, and only for technical failures. `PermanentJobError` — which is what a compliance or
evidence failure raises — is recorded and never retried. Retrying a blocked compliance gate produces
the same block, more slowly, while making the log harder to read.

Backoff is exponential and capped at 8 seconds. Each job definition carries its own timeout, and the
`AbortSignal` is passed through to the work.

---

## Scheduling

Server-side only. No browser timer, no `setInterval`, no in-process scheduler. Your platform cron
posts a signed request to `/api/jobs/run`:

```bash
BODY='{"job_type":"research_radar","input":{"day":"2026-08-21"}}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$AIFT_JOB_SIGNING_SECRET" -hex | cut -d' ' -f2)
curl -X POST "$AIFT_APP_BASE_URL/api/jobs/run" \
  -H 'content-type: application/json' -H "x-aift-signature: $SIG" -d "$BODY"
```

Without `AIFT_JOB_SIGNING_SECRET` the route returns 503 and refuses everything. It does not fall
back to open access — an unauthenticated job trigger on a private tool is a worse failure than a
broken schedule.

**Research radar** (weekdays) refreshes the private evidence digest and promotes a topic to a
candidate *only when it yields at least three public-safe claims*. A topic that does not clear that
bar stays as research with the reason recorded.

**Editorial production** (weekly) takes one candidate, produces a complete pack, runs QA, and stops
in `needs_review` or `blocked`. It cannot approve, archive or publish.

---

## The render pipeline

```
scene plan ─▶ narration clips (measured) ─▶ scene timings ─▶ caption timeline
                                                   │
     charts pre-rendered in Node ──────────────────┤
     B-roll generated (atmosphere only) ───────────┤
                                                   ▼
                                       one HTML document
                                                   │
                        Chromium: seek(t) → screenshot → JPEG
                                                   │
                                        ffmpeg (libx264 + AAC)
                                                   ▼
                                    video.mp4 · captions.srt · poster.png
```

**Timing runs forward from the voice, not backwards from a guess.** Narration is synthesised first
and measured; scene durations are the measured length plus a 260 ms lead-in and a 420 ms tail. The
same measurement drives the caption timeline, so picture, voice and captions are in sync by
construction rather than by adjustment afterwards.

**A frame is a pure function of time.** `window.__seek(tMs)` writes inline styles; there are no CSS
keyframes, no `requestAnimationFrame` and no wall-clock reads. The consequence is that a re-render is
identical, which is what makes what a chart shows auditable rather than merely plausible.

**Charts are pre-rendered in Node** by `SvgChartRenderer`, at one SVG per animation step, embedded
in the document. That is the same class whose `visibleValues()` the visual-accuracy gate compares
against the claim ledger — so the code that draws the pixels is the code the gate checks.

**Every asset carries provenance**: SHA-256, generator, prompt version, source claim ids, byte
count, duration and aspect ratio. `manifest.json` indexes the lot.

---

## Providers

| Port | Mock (default) | Live |
|---|---|---|
| `LLMProvider` | Deterministic composer | OpenAI-compatible chat completions with strict JSON-schema output |
| `ResearchProvider` | Fixture corpus with the real two-step shape | HTTP fetch + extraction |
| `ChartRenderer` | *(always deterministic — there is no mock)* | — |
| `MediaProvider` | Procedural abstract field | Image/video generation adapter |
| `VoiceProvider` | Silent track at exactly the right length | `espeak-ng` preview, or licensed cloud TTS |
| `StorageProvider` | Local filesystem, path-traversal checked | Private Supabase bucket, signed URLs only |
| `JobRunner` | In-process, idempotent, bounded retry | Same interface behind a queue |
| `PrivateContextProvider` | Redacted fixture context | Single RPC to `aift_content_context` |

The mocks are not stubs. `MockResearchProvider` reproduces the two-step discover/fetch shape, so
code that shortcuts from a snippet to a citation fails there exactly as it would in production. The
mock LLM composes from the actual stage input, so the same brief always produces the same script and
a different brief produces a different one — which is what makes the whole pipeline testable with no
credentials and no spend.
