"""
OGX research database — client for the OrigineX Human Archives Supabase project.

This is the evidence layer for the OGX agents. Every factual claim that reaches
a script, a card, a thumbnail hook, or a posting sheet must be checked against
this database first — that is Joe's standing rule for the channel.

Design rule (deliberately the OPPOSITE of tools/supabase_store.py):
    supabase_store is best-effort logging that must never break trading, so it
    swallows errors and returns falsy. Research verification cannot work that
    way — a swallowed error is indistinguishable from "no evidence exists", and
    an agent would read that as "unverified, soften the claim" when the truth
    is "the database was unreachable". So READS RAISE. The pipeline calls
    require_enabled() up front and fails loudly rather than shipping unchecked
    history. Writes (episode logging) stay best-effort and never raise.

Configure with OGX_SUPABASE_URL and OGX_SUPABASE_SERVICE_KEY.

Schema notes verified against the live database (project qvlllknedilztozxwscj):
  - `people` and `citations` have a `verified` boolean. `people` is 100% verified.
  - `events`, `places`, `civilizations` have NO `verified` column — they carry
    `confidence_score` (smallint) instead. Filtering them on `verified = true`
    errors out, so this module uses confidence_score for those tables.
  - `content_ideas` has no `slug` column — search it by `title` only.
  - `alternate_names` is `text[]`. `ilike` against it raises
    "operator does not exist: text[] ~~*", so it is never put in an ilike
    filter. Alternate names are reached through the `search_tsv` fallback
    instead, which indexes them (searching "nzinga" finds two people by
    full-text but only one by name/slug substring).
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

_URL = (os.environ.get("OGX_SUPABASE_URL") or "").rstrip("/")
_KEY = (
    os.environ.get("OGX_SUPABASE_SERVICE_KEY")
    or os.environ.get("OGX_SUPABASE_KEY")
    or ""
)
_TIMEOUT = 20

# Default project — used only for the setup message, never for auth.
PROJECT_ID = "qvlllknedilztozxwscj"

# Tables an agent is allowed to search by name via the generic search tool.
SEARCHABLE = ("people", "events", "places", "civilizations", "documents",
              "themes", "content_ideas")


class OGXDatabaseError(RuntimeError):
    """Raised when the research database cannot be read. Never swallowed."""


def enabled() -> bool:
    return bool(_URL and _KEY)


def require_enabled() -> None:
    """Fail fast before any OGX pipeline work starts."""
    if not enabled():
        raise EnvironmentError(
            "OGX research database is not configured. Add to .env:\n"
            f"  OGX_SUPABASE_URL=https://{PROJECT_ID}.supabase.co\n"
            "  OGX_SUPABASE_SERVICE_KEY=your_service_role_key\n"
            "Every OGX claim is verified against this database — the pipeline "
            "will not run without it. Pass --allow-unverified to override "
            "(research quality drops to Claude's trained knowledge only)."
        )


def _headers() -> dict:
    return {
        "apikey": _KEY,
        "Authorization": f"Bearer {_KEY}",
        "Content-Type": "application/json",
    }


def _clean(term: str) -> str:
    """Strip characters that would break PostgREST's filter grammar."""
    return "".join(c for c in (term or "") if c not in "*,()\"'").strip()


def _select(table: str, params: dict) -> list[dict]:
    """Read rows. Raises OGXDatabaseError on any failure — never returns a lie."""
    if not enabled():
        raise OGXDatabaseError("OGX research database is not configured")
    try:
        r = requests.get(
            f"{_URL}/rest/v1/{table}",
            params=params, headers=_headers(), timeout=_TIMEOUT,
        )
    except Exception as e:  # noqa: BLE001 — re-raised as a typed error below
        raise OGXDatabaseError(f"{table} read failed: {e}") from e
    if r.status_code >= 300:
        raise OGXDatabaseError(f"{table} read failed {r.status_code}: {r.text[:200]}")
    return r.json()


def _insert(table: str, rows) -> tuple[list | None, int]:
    """Best-effort insert. Returns (inserted_rows, status_code); never raises."""
    if not enabled():
        return None, 0
    try:
        r = requests.post(
            f"{_URL}/rest/v1/{table}",
            headers={**_headers(), "Prefer": "return=representation"},
            json=rows if isinstance(rows, list) else [rows],
            timeout=_TIMEOUT,
        )
        if r.status_code >= 300:
            print(f"[ogx-db] {table} write failed {r.status_code}: {r.text[:160]}")
            return None, r.status_code
        return r.json(), r.status_code
    except Exception as e:  # noqa: BLE001 — bookkeeping must not kill a build
        print(f"[ogx-db] {table} write error: {e}")
        return None, 0


def _write(table: str, rows) -> bool:
    """Best-effort insert for pipeline bookkeeping. Never raises."""
    data, _ = _insert(table, rows)
    return data if data else False


def _truncate(rows: list[dict], field: str, limit: int = 400) -> list[dict]:
    for row in rows:
        value = row.get(field)
        if isinstance(value, str) and len(value) > limit:
            row[field] = value[:limit].rstrip() + " …[truncated]"
    return rows


def _match(term: str, *columns: str) -> str:
    """
    Build a PostgREST `or=(a.ilike.*t*,b.ilike.*t*)` filter.

    Text columns only. Never pass an array column (see the module docstring).
    """
    t = _clean(term)
    return "(" + ",".join(f"{c}.ilike.*{t}*" for c in columns) + ")"


# Tables carrying a maintained `search_tsv` tsvector, used as the fallback when
# a substring search misses. This is how alternate names, biography text, and
# description bodies get reached without an ilike over every column.
_FULL_TEXT_TABLES = ("people", "events", "places", "civilizations",
                     "documents", "oral_evidence")


def _lookup(table: str, select: str, term: str, columns: tuple[str, ...],
            limit: int, extra: dict | None = None,
            order: str = "") -> list[dict]:
    """
    Substring search first, full-text fallback second.

    Substring wins on precision ("Musa" inside "Mansa Musa"); full-text wins on
    reach (alternate names, biography prose). Running the fallback only when the
    first pass is empty keeps precise hits from being buried under loose ones.
    """
    params = {"select": select, "or": _match(term, *columns), "limit": limit}
    if order:
        params["order"] = order
    params.update(extra or {})

    rows = _select(table, params)
    if rows or table not in _FULL_TEXT_TABLES:
        return rows

    params.pop("or")
    params["search_tsv"] = f"plfts(english).{_clean(term)}"
    return _select(table, params)


# ---- research reads -------------------------------------------------------- #

def find_people(term: str, limit: int = 5) -> list[dict]:
    """Verified people only — `people.verified` is the channel's evidence gate."""
    rows = _lookup(
        "people",
        "name,slug,birth_date,death_date,biography,significance,"
        "roles,regions,civilizations,sources,confidence_score",
        term, ("name", "slug"), limit, extra={"verified": "is.true"},
    )
    return _truncate(_truncate(rows, "biography", 700), "significance")


def find_events(term: str, limit: int = 6) -> list[dict]:
    """Events carry confidence_score, not `verified` — do not filter on verified."""
    rows = _lookup(
        "events",
        "name,slug,date_start,date_end,date_precision,description,"
        "significance,causes,consequences,event_type,regions,"
        "civilizations,key_figures,confidence_score",
        term, ("name", "slug", "description"), limit, order="date_start.asc",
    )
    return _truncate(_truncate(rows, "description"), "significance")


def find_places(term: str, limit: int = 5) -> list[dict]:
    rows = _lookup(
        "places",
        "name,modern_name,slug,place_type,description,significance,"
        "region,continent,modern_country,date_founded,confidence_score",
        term, ("name", "modern_name", "slug"), limit,
    )
    return _truncate(rows, "description")


def find_civilizations(term: str, limit: int = 5) -> list[dict]:
    rows = _lookup(
        "civilizations",
        "name,slug,description,significance,date_start,date_end,"
        "peak_period,regions,key_achievements,key_figures,confidence_score",
        term, ("name", "slug"), limit,
    )
    return _truncate(_truncate(rows, "description"), "significance")


def find_documents(term: str, limit: int = 5) -> list[dict]:
    """Never selects `content` — document bodies blow up the context window."""
    rows = _lookup(
        "documents",
        "title,slug,excerpt,document_type,status,era,date_start,"
        "date_end,themes,subjects,civilizations,regions,source_urls",
        term, ("title", "slug", "excerpt"), limit,
    )
    return _truncate(rows, "excerpt", 600)


def find_themes(term: str, limit: int = 5) -> list[dict]:
    return _select("themes", {
        "select": "name,slug,description,key_questions,examples,document_count",
        "or": _match(term, "name", "slug", "description"),
        "limit": limit,
    })


def find_content_ideas(term: str, limit: int = 8) -> list[dict]:
    """`content_ideas` has no slug column — title search only."""
    return _select("content_ideas", {
        "select": "id,title,status,content_type,hook,key_points,target_audience",
        "title": f"ilike.*{_clean(term)}*",
        "limit": limit,
    })


def find_citations(term: str, limit: int = 10, verified_only: bool = True) -> list[dict]:
    params = {
        "select": "author,title,publication,publisher,year,page_reference,url,"
                  "doi,quote,reliability,verified,source_type",
        "or": _match(term, "title", "author", "quote", "publication"),
        "order": "verified.desc,year.desc",
        "limit": limit,
    }
    if verified_only:
        params["verified"] = "is.true"
    return _truncate(_select("citations", params), "quote", 500)


def find_debates(term: str, limit: int = 6) -> list[dict]:
    """Scholarly disputes — anything here must be flagged on screen, never settled."""
    return _select("scholarly_debates", {
        "select": "subject,subject_type,claim,position_a,position_b,key_scholars,"
                  "current_consensus,status,permanent_flag,notes",
        "or": _match(term, "subject", "claim", "notes"),
        "limit": limit,
    })


def find_oral_evidence(term: str, limit: int = 8, contested_only: bool = False) -> list[dict]:
    rows = _lookup(
        "oral_evidence",
        "subject_slug,source_author,source_work,source_century_start,"
        "claim_text,claim_type,contested_flag,contestation_reason,"
        "reliability_label,corroboration_count,"
        "archaeological_corroboration,modern_scholarship_cross_ref",
        term, ("subject_slug", "claim_text", "source_author", "source_work"), limit,
        extra={"contested_flag": "is.true"} if contested_only else None,
        order="corroboration_count.desc",
    )
    return _truncate(rows, "claim_text", 500)


SEARCH_FUNCTIONS = {
    "people": find_people,
    "events": find_events,
    "places": find_places,
    "civilizations": find_civilizations,
    "documents": find_documents,
    "themes": find_themes,
    "content_ideas": find_content_ideas,
}


def search(entity_type: str, term: str, limit: int = 5) -> list[dict]:
    fn = SEARCH_FUNCTIONS.get(entity_type)
    if not fn:
        raise OGXDatabaseError(
            f"Unknown entity_type '{entity_type}'. Choose from: {', '.join(SEARCHABLE)}"
        )
    return fn(term, limit)


def verify_claim(term: str) -> dict:
    """
    Check a claim's subject against every evidence table and return a verdict.

    Returns a dict with:
      status   — "supported" | "contested" | "unsupported"
      support  — the verified records that back it
      contested — debates / flagged oral claims that dispute it
    A "contested" verdict does not mean drop the claim; it means the narration
    must attribute it ("according to Livy…") rather than assert it.
    """
    support = {
        "people": find_people(term, limit=3),
        "events": find_events(term, limit=3),
        "citations": find_citations(term, limit=5),
        "oral_evidence": find_oral_evidence(term, limit=4),
    }
    contested = {
        "scholarly_debates": find_debates(term, limit=4),
        "contested_oral_claims": [
            r for r in support["oral_evidence"] if r.get("contested_flag")
        ],
    }
    hits = sum(len(v) for v in support.values())
    disputes = sum(len(v) for v in contested.values())

    if hits == 0:
        status = "unsupported"
    elif disputes:
        status = "contested"
    else:
        status = "supported"

    return {
        "term": term,
        "status": status,
        "record_count": hits,
        "support": support,
        "contested": contested,
    }


# ---- pipeline bookkeeping (best-effort writes) ----------------------------- #

# These mirror CHECK constraints on the live tables. Writing a value outside
# either set is rejected with a 400, so they are validated here instead — a
# typo should fail at the call site, not silently drop an agent's output.
EPISODE_STATUSES = ("draft", "researching", "scripting", "visualizing",
                    "voicing", "assembling", "rendering", "rendered",
                    "published", "archived")
AGENT_ROLES = ("research", "script", "packaging", "thumbnail", "visual",
               "motion", "voiceover", "manifest", "director")

# Pipeline stage -> the schema's vocabulary. The build sheet is "visual" work;
# once packaging is done the episode is ready for an editor to assemble.
STAGE_STATUS = {
    "research": "researching",
    "script": "scripting",
    "visual": "visualizing",
    "packaging": "assembling",
}


def _slugify(text: str, limit: int = 70) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")[:limit] or "episode"


def create_episode(title: str, topic: str, slug: str = "",
                   target_minutes: float = 0, channel: str = "OGX") -> str:
    """
    Open a row in video_episodes. Returns the episode id, or "" on failure.

    `slug` is UNIQUE, so a second build of the same subject collides. Rather
    than fail the run or pre-emptively uglify every slug, the clean slug is
    tried first and a timestamp suffix is added only on conflict.
    """
    base = slug or _slugify(title)
    row = {
        "title": title,
        "slug": base,
        "channel": channel,
        "topic": topic,
        "status": "draft",
        "target_minutes": target_minutes or None,
    }
    data, code = _insert("video_episodes", row)
    if data is None and code == 409:
        row["slug"] = f"{base}-{datetime.now():%Y%m%d%H%M%S}"[:80]
        data, _ = _insert("video_episodes", row)
    if data:
        return data[0].get("id", "")
    return ""


def save_agent_output(episode_id: str, role: str, content_md: str,
                      model: str = "", payload: dict | None = None) -> bool:
    """Persist one agent's deliverable so a later run can build on it."""
    if role not in AGENT_ROLES:
        raise ValueError(
            f"role '{role}' is rejected by video_agent_outputs_role_check. "
            f"Use one of: {', '.join(AGENT_ROLES)}"
        )
    if not episode_id:
        return False
    ok = bool(_write("video_agent_outputs", {
        "episode_id": episode_id,
        "role": role,
        "content_md": content_md,
        "model": model,
        "payload": payload or {},
    }))
    if ok and role in STAGE_STATUS:
        set_episode_status(episode_id, STAGE_STATUS[role])
    return ok


def log_decision(episode_id: str, agent: str, action: str,
                 payload: dict | None = None) -> bool:
    if not episode_id:
        return False
    return bool(_write("video_decision_log", {
        "episode_id": episode_id,
        "agent": agent,
        "action": action,
        "payload": payload or {},
    }))


def set_episode_status(episode_id: str, status: str = "assembling") -> bool:
    """Move an episode along the pipeline. PATCH — a status flip, not a new row."""
    if status not in EPISODE_STATUSES:
        raise ValueError(
            f"status '{status}' is rejected by video_episodes_status_check. "
            f"Use one of: {', '.join(EPISODE_STATUSES)}"
        )
    if not episode_id or not enabled():
        return False
    try:
        r = requests.patch(
            f"{_URL}/rest/v1/video_episodes",
            params={"id": f"eq.{episode_id}"},
            headers={**_headers(), "Prefer": "return=minimal"},
            json={"status": status},
            timeout=_TIMEOUT,
        )
        return r.status_code < 300
    except Exception as e:  # noqa: BLE001
        print(f"[ogx-db] episode status update failed: {e}")
        return False


# ---- formatting for Claude tool results ------------------------------------ #

def format_rows(label: str, rows: list[dict]) -> str:
    """Render rows as compact readable text. Empty is stated explicitly."""
    if not rows:
        return f"{label}: NO RECORDS FOUND in the OGX database."
    lines = [f"{label}: {len(rows)} record(s)"]
    for i, row in enumerate(rows, 1):
        fields = []
        for k, v in row.items():
            if v in (None, "", [], {}):
                continue
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v[:8])
            fields.append(f"{k}: {v}")
        lines.append(f"\n[{i}] " + "\n    ".join(fields))
    return "\n".join(lines)


def format_verdict(verdict: dict) -> str:
    """Render a verify_claim() result as an instruction the agent must obey."""
    status = verdict["status"]
    header = (
        f"CLAIM CHECK — \"{verdict['term']}\"\n"
        f"STATUS: {status.upper()} ({verdict['record_count']} supporting record(s))"
    )
    rule = {
        "supported": "You may state this directly as fact.",
        "contested": (
            "DO NOT state this as settled. Attribute it on screen "
            "(\"according to …\") and name the dispute."
        ),
        "unsupported": (
            "The database does not support this. Cut it, or soften it to what "
            "the records do show. Do not ship it as fact."
        ),
    }[status]
    body = [header, f"RULE: {rule}"]
    for name, rows in verdict["support"].items():
        if rows:
            body.append("\n" + format_rows(f"SUPPORT · {name}", rows))
    for name, rows in verdict["contested"].items():
        if rows:
            body.append("\n" + format_rows(f"CONTESTED · {name}", rows))
    return "\n".join(body)
