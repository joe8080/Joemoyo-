# AI Finance Toolkit Studio

A private, single-user studio that turns a controlled research brief into a complete,
review-ready YouTube production package for the **AI Finance Toolkit** channel.

It researches, cites, writes, storyboards, renders and grades. Then it stops and waits for you.

> **It cannot publish.** There is no YouTube credential, no upload OAuth scope, no call to
> `videos.insert`, and no job state that means "published". `npm run guard:no-publish` fails the
> build if any of that ever appears. The furthest a pack can travel is `archived`, which means
> "complete and stored, for you to upload by hand".
>
> **It cannot trade.** No brokerage API, no order entry, no money movement, ever.
>
> **It does not turn your portfolio into content.** Private financial data is context for the
> owner. A gate blocks any pack whose public copy mentions holdings, account details, broker
> information or personal profit and loss.

---

## What it produces

Running one topic produces a **content pack**:

| Artefact | What it is |
|---|---|
| `script.md` / `script.json` | Beat-by-beat script, each figure bound to a claim id |
| `scene_plan.json` | Every scene: composition, timing, data rows, source, as-of date |
| `narration.txt` | The spoken text, verbatim |
| `mix.wav`, `mix.opus` | The delivered mix — narration, ducked music bed, normalised to −14 LUFS — as WAV and as an Ogg/Opus review copy |
| `music_bed.wav` | The bed, with its licence and provenance recorded on the asset |
| `captions.srt` | Word-timed captions, generated from the same timeline as the burnt-in ones |
| `chapters.json` | YouTube chapter marks |
| `description.md`, `title_options.json` | Description with chapters and the full claim list; scored titles |
| `thumbnail_brief.json` | Concept, palette and an explicit forbidden list |
| `source_manifest.json` | Every source: URL, publisher, published date, accessed date, content hash |
| `composition.html` | The editable motion-graphics source for the render |
| `video.mp4` / `short.mp4` | H.264 + AAC, 1920×1080 or 1080×1920 |
| `poster.png` | A still from the composition |
| `quality_report.md` | Every gate, what it found, and how to fix what failed |
| `manifest.json` | The pack index with hashes, providers and prompt versions |

Two formats: an **8–12 minute 16:9 deep dive** and a **45–75 second 9:16 Short**.

---

## Quick start

```bash
cd aift-studio
npm install
cp .env.example .env.local        # every value may stay empty
npm run verify                    # typecheck + no-publish guard + 89 tests
npm run pack:demo -- --no-video   # a complete pack in about 5 seconds
npm run dev                       # http://localhost:3000
```

**No credentials are required for any of that.** Every external dependency has a working mock, so
the full pipeline — research, evidence, brief, script, scene plan, render, QA, review — runs end to
end on an empty `.env`. The studio will never tell you a provider is live when its credential is
absent; the dashboard shows exactly what is running.

To render real video, you need a Chromium binary and ffmpeg. Both are usually already present:

```bash
npm run pack:demo                 # renders the deep dive and the Short
npm run preview -- --format=short # one still per composition, for iterating on visuals
```

If Chromium is missing: `npx playwright install chromium`, or set `AIFT_CHROMIUM_PATH`.
`ffmpeg-static` is a dev dependency, so ffmpeg is bundled; `AIFT_FFMPEG_PATH` overrides it.

---

## The seven screens

| Screen | What it is for |
|---|---|
| **Dashboard** | What is in flight, what is blocked, what needs you, and which providers are actually live |
| **Research desk** | Create a topic; read the source register and the claim ledger, including *why* a claim was withheld |
| **Content studio** | Script beat by beat with claim ids and timings, title options, thumbnail brief, asset manifest with hashes |
| **Review room** | Quality gates, citations, chapters, and the approve / rework / archive controls |
| **Brand studio** | Voice, audience, disclosure, banned phrases, visual tokens, approved sources, private-context allow-list |
| **System log** | Every run, provider, prompt version, trace, error and review decision |
| **Security checklist** | The open RLS finding, key placement, the table access matrix, deployment readiness |

There is no publish button on any of them. There is nowhere to put one.

---

## Architecture

```
Intake ─▶ Research plan ─▶ Evidence ─▶ Analyst brief ─▶ Editorial ─▶ Script
                                                                       │
                        Review room ◀── QA gates ◀── Render ◀── Visual plan
                              │
              approve ────────┴──────── rework
                 │
              archive   (terminal — the pack is stored, not sent)
```

**Deterministic where it matters, AI where it helps.** Storage, state transitions, validation,
timing, charts and quality gates are ordinary code. Language models do bounded reasoning and
generation, always into a JSON schema that is validated before anything is stored. A response that
fails validation is retried and then refused — never coerced.

**Every external dependency is a typed port with a mock:**

`LLMProvider` · `ResearchProvider` · `ChartRenderer` · `MediaProvider` · `VoiceProvider` ·
`StorageProvider` · `JobRunner` · `PrivateContextProvider`

**The writer never grades its own draft.** `AIFT_LLM_MODEL_FAST` and `AIFT_LLM_MODEL_REVIEW` must
differ; the constructor refuses to start if they do not. The reviewer sees the script and the
approved claim list, and nothing of the writer's reasoning.

### The render engine

The whole film is one HTML document. It is loaded once in Chromium and then *seeked*, frame by
frame, with each frame piped as JPEG straight into ffmpeg. Two consequences worth having:

- **A frame is a pure function of time.** No CSS keyframes, no `requestAnimationFrame`, no
  wall-clock. Frame 4,197 is identical on every machine and every run, so what a chart shows is
  auditable rather than merely plausible.
- **The render parallelises.** Contiguous frame ranges are captured by independent browsers and
  concatenated by copy. A test proves one worker and three produce identical pixels either side of
  every segment boundary.
- **Audio is mixed, not just attached.** Narration is assembled at measured scene offsets, a music bed is ducked under it by an envelope follower, and the whole mix is normalised to −14 LUFS with a −1 dBTP ceiling — the numbers YouTube actually plays back to. Gates check loudness, true peak, duck depth and the bed's licence.
- **Charts are rendered in Node, by the same code the visual gate checks.** `ChartRenderer` exposes
  `visibleValues()` — the exact strings a viewer will read — and the gate compares them against the
  claim ledger. A number cannot reach the screen without a claim behind it.

Generated imagery is atmosphere only. `MediaAsset.factualContentAllowed` is hard-coded `false`, the
visual gate rejects any B-roll scene carrying data, and it rejects any B-roll prompt that asks for a
chart, a figure, a logo or a readable screen.

---

## Configuration

Every variable is optional. See `.env.example` for the full list and the ones deliberately absent.

| Variable | Effect when absent |
|---|---|
| `SUPABASE_URL`, `SUPABASE_ANON_KEY` | No sign-in: the studio runs as a single local owner and says so. Set both to enforce Supabase Auth on every page |
| `SUPABASE_SERVICE_ROLE_KEY` | In-memory persistence; state lives for the life of the process |
| `AIFT_LLM_API_KEY` | Deterministic composer instead of a model. The pipeline still runs and the pack is still complete |
| `AIFT_TTS_PROVIDER` | Silent narration at exactly the right length, and the music bed carried as the programme. Set `espeak` for an offline preview voice, `http` for a licensed one |
| `AIFT_MEDIA_API_KEY` | Procedural abstract B-roll |
| `AIFT_STORAGE_DRIVER` | Writes to `.artifacts/` (git-ignored) |
| `AIFT_JOB_SIGNING_SECRET` | The scheduler endpoint refuses every request rather than falling back to open access |

`SUPABASE_SERVICE_ROLE_KEY` is server-only. `src/lib/supabase/admin.ts` imports `server-only`, so a
client import is a build error, and `npm run guard:no-secrets` fails the build if a client module
references any secret, the admin client, or a restricted table.

---

## Scheduled routines

Two server-side job definitions. Neither uses a browser timer or `setInterval`; scheduling is
external, and your platform cron posts a signed request:

```bash
BODY='{"job_type":"research_radar","input":{"day":"2026-08-21"}}'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$AIFT_JOB_SIGNING_SECRET" -hex | cut -d' ' -f2)
curl -X POST "$AIFT_APP_BASE_URL/api/jobs/run" \
  -H "content-type: application/json" -H "x-aift-signature: $SIG" -d "$BODY"
```

| Routine | Cadence | Ends in |
|---|---|---|
| `research_radar` | weekdays | A topic candidate, only when the evidence is good enough |
| `editorial_production` | weekly | `needs_review` — or `blocked`, if a gate failed |

Each carries an idempotency key, so a duplicate firing is a recorded no-op rather than a second
pack. Retries are for technical failures only: a compliance or evidence failure raises
`PermanentJobError` and stops.

---

## Database

Migrations live in `supabase/migrations/`. **Nothing in this repository applies them for you**, and
no deployment step touches a production database.

- `20260821000100_aift_core.sql` — the nine `aift_*` tables. RLS enabled *and forced* on every one,
  owner-scoped policies, `anon` revoked, and the state machine enforced in a trigger so a direct SQL
  update cannot skip review.
- `20260821000200_private_context.sql` — `private.aift_content_context`, the single redacted door to
  the finance database, and its `SECURITY DEFINER` wrapper. Granted to neither `anon` nor
  `authenticated`.

`supabase/migrations-pending-review/` holds the **broker RLS proposal**. It is in a separate
directory precisely so that nothing applies it. Read `docs/SECURITY.md` before you run it, and run
`supabase/tests/broker_rls_policy_test.sql` against a branch database afterwards.

---

## Tests

```bash
npm run verify         # typecheck + guard + the full suite
npm test               # 89 tests
npm run guard:no-publish
npm run guard:no-secrets
```

What they actually prove:

- No broker, trade, benefits, income or account field can appear in the context payload — and the
  scan throws rather than silently stripping, so a leak is loud.
- No service-role key, provider key or restricted table is reachable from a client module.
- A draft with an unsupported figure, a missing disclosure, an undated figure, a trade instruction,
  or a personal portfolio value is blocked. Each of those is a separate test with a real draft.
- A generated image used where a chart belongs is rejected, and so is a B-roll prompt that asks for
  one.
- A content job cannot reach `archived` without two separate authenticated reviewer decisions, in
  order, and the workflow engine cannot perform either.
- Re-running a job duplicates no source, claim, asset or run record.
- The TypeScript state machine and the Postgres one are compared edge by edge, so they cannot drift.
- The repository contains no upload scope, no `videos.insert`, no YouTube credential and no broker
  API.

---

## What is real and what is a fixture

The demo topic — **Northwind Semiconductor (NWSC)** — is synthetic. Northwind does not exist and
every figure in `src/lib/fixtures/northwind.ts` was invented so the pipeline could be exercised and
tested without a single real investment datum entering the repository. Source labels rendered on
screen say "synthetic fixture" for exactly that reason.

Replacing `MockResearchProvider` with a live `ResearchProvider` is the only change needed to move
from demo to real research. Everything downstream — the evidence rules, the gates, the renderer —
is already the production path.

## Further reading

- [`docs/SECURITY.md`](docs/SECURITY.md) — the data boundary, the RLS finding, key placement, the migration review process
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — the nine stages, the state machine, idempotency, the render pipeline
- [`docs/CONTENT_POLICY.md`](docs/CONTENT_POLICY.md) — source hierarchy, what counts as a material claim, the uncertainty style guide, the gates
