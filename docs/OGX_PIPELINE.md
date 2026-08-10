# OGX Agents System — OrigineX Human Archives

Four agents and one orchestrated workflow that take a topic and return a
research dossier, a narration script, a shot-by-shot build sheet, and a
publication pack — with every factual claim checked against the OrigineX
research database on the way through.

```
python main.py ogx --topic "Queen Nzinga"
```

---

## Why this pipeline is different

The other content workflows in this repo research a topic and write about it.
This one is **evidence-gated**: the research database is the source of truth,
and a claim that the database cannot support does not ship. That rule is
enforced in four places rather than trusted once:

| Layer | What enforces it |
|---|---|
| Startup | `produce_ogx_video()` calls `require_enabled()` and refuses to run without the database |
| Prompt | Every OGX system prompt opens with the same `OGX_EVIDENCE_RULES` block |
| Tools | Every OGX agent carries `ogx_verify_claim`, not just the researcher |
| Failure | A database error is reported to the model as an error, never as "no evidence" |

That last one matters more than it looks. `tools/ogx_db.py` **raises** on a
failed read instead of returning an empty list, which is the opposite of
`tools/supabase_store.py`. An empty list and a dead connection are the same
value but opposite facts — if a network blip returned `[]`, every agent would
read it as "the database has nothing on this subject", mark real history as
unsupported, and cheerfully cut it. So reads raise, and the agent-facing error
message says in as many words: *this is not evidence of absence.*

---

## The four agents

| Agent | Role | Output |
|---|---|---|
| `OGXResearchAgent` | Database first, web second. Entities, citations, contested record, existing content ideas — then the web for gaps only | Research dossier with an evidence summary table, contested claims, and a list of gaps |
| `OGXScriptWriterAgent` | Narration in one of two locked styles | Full chapter-by-chapter script plus SEO package |
| `OGXVideoBuildAgent` | Image ↔ narration sync, motion, audio | Scene-numbered build sheet for an editor or n8n/Invideo |
| `OGXPackagingAgent` | Thumbnail brief, ranked titles, posting pack | Paste-ready generation prompt, 3 titles, chaptered description, tags, pinned sources |

All four inherit `agents/ogx_base.py`, which supplies the shared database
toolkit and the brand profile, so no stage can quietly skip the gate.

### Two locked styles

- **`archives`** (default, ~18 min) — the house cinematic narrative arc: cold
  open, stakes, tension, rhetorical turn, context-before, body chapters,
  identity reclamation, resistance, modern legacy, CTA on a named next episode.
- **`declassified`** (~42 min) — the receipts format: case-file cards built
  around named declassified documents, one red shock number per card, the
  PATTERN card, the FULL TIMELINE card. A card whose receipt cannot be named
  does not get made.

---

## Commands

```bash
# Full pipeline
python main.py ogx --topic "Queen Nzinga"
python main.py ogx --topic "Operation Condor" --style declassified --minutes 45

# Single stages — iterate one part without paying for the rest
python main.py ogx --topic "Mansa Musa" --stage research
python main.py ogx --topic "Mansa Musa" --stage script  --from-file outputs/ogx/..._research_....md
python main.py ogx --topic "Mansa Musa" --stage build   --from-file outputs/ogx/..._script_....md
python main.py ogx --topic "Mansa Musa" --stage package --from-file outputs/ogx/..._script_....md

# Escape hatches
python main.py ogx --topic "X" --skip-research      # straight to script
python main.py ogx --topic "X" --allow-unverified   # no database; output marked unverified
python main.py ogx --topic "X" --no-persist         # don't log the episode
```

Outputs land in `outputs/ogx/` as `OGX_{Subject}_{stage}_{timestamp}.md`.

---

## Setup

```bash
# .env
OGX_SUPABASE_URL=https://qvlllknedilztozxwscj.supabase.co
OGX_SUPABASE_SERVICE_KEY=your_service_role_key
```

Service-role key, server-side only. Without it the pipeline stops at the gate
with a setup message rather than a stack trace.

---

## Persistence

When the database is configured, each run writes itself down:

- `video_episodes` — one row per build, opened as `draft`
- `video_agent_outputs` — one row per stage, holding the full markdown
- `video_decision_log` — the orchestrator's completion record

The episode status advances as stages land: `draft` → `researching` →
`scripting` → `visualizing` → `assembling`. An episode sitting at `scripting`
tells you the build sheet never made it.

---

## Schema contract

These are the live constraints the code is written against. Changing the
database without changing `tools/ogx_db.py` breaks the pipeline in ways that
only surface on a paid run, so `tests/test_ogx.py` encodes each one.

**Evidence gates differ per table.** `people` and `citations` have a `verified`
boolean. `events`, `places`, and `civilizations` **do not** — they carry
`confidence_score`. Filtering those on `verified = true` errors out. (The OGX
skill documentation shows `events ... AND verified = true`; that query fails
against the live schema.)

**`alternate_names` is `text[]`.** An `ilike` against it raises
`operator does not exist: text[] ~~*` and takes the whole query down. Alternate
names are reached through the `search_tsv` fallback instead.

**Search is two-pass.** Substring first (precise: "Musa" inside "Mansa Musa"),
full-text second, and only when the first pass is empty. Full-text reaches
alternate names and prose — searching *nzinga* finds two people by `search_tsv`
but only one by name/slug substring. Tables with `search_tsv`: `people`,
`events`, `places`, `civilizations`, `documents`, `oral_evidence`.

**`content_ideas` has no `slug`.** Title search only.

**CHECK constraints.**
`video_episodes.status` ∈ draft, researching, scripting, visualizing, voicing,
assembling, rendering, rendered, published, archived.
`video_agent_outputs.role` ∈ research, script, packaging, thumbnail, visual,
motion, voiceover, manifest, director.
The build sheet is written as role `visual`; there is no `video_build` role.
`ogx_db.py` validates both sets before writing, so a bad value raises at the
call site instead of returning a 400 and silently dropping the output.

**`video_episodes.slug` is UNIQUE.** A second build of the same subject
conflicts, so `create_episode()` tries the clean slug first and appends a
timestamp only on a 409.

**Never select `documents.content`.** Document bodies blow up the context
window; the excerpt is enough.

---

## What this does not do

Thumbnail generation and title scoring run through the vidIQ MCP tools, which
live in the Claude skills, not in this repo. `OGXPackagingAgent` produces the
brand-locked brief and the ranked candidates; you spend vidIQ credits only on
the concept you have already chosen. The `ogx-thumbnail-engine` skill takes it
from there.

Related skills that share this brand and database: `ogx-research-pdf-script`
(PDF dossier), `ogx-video-build-engine`, `ogx-thumbnail-engine`,
`ogx-declassified-receipts`.
