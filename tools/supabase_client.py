"""
Supabase client — the video crew's persistence layer and source of truth.

Connects to the ORIGINEX HUMAN ARCHIVES project. Every crew agent writes its
output here (episodes, per-stage outputs, assets, manifest, render jobs) and
reads sourced facts from the existing knowledge graph (people / events /
places / civilizations / citations / documents).

Discipline (mirrors vault-agents/shared/supabase_client.md):
- The service_role key bypasses RLS — operator-level care matters.
- Each helper writes to exactly one table it "owns".
- Every write is mirrored into `video_decision_log` for traceability.
- Degrades gracefully when SUPABASE_URL / SUPABASE_SERVICE_KEY are unset, so
  the crew can still run in specs-only mode (artifacts on disk, no DB).

Requires: supabase>=2.0.0
"""

from __future__ import annotations

import json
from typing import Any

from config.settings import settings

_client = None
_unavailable_reason: str | None = None


def is_configured() -> bool:
    """True when Supabase credentials are present."""
    return bool(settings.supabase_url and settings.supabase_service_key)


def get_client():
    """Lazily build and cache the Supabase client, or None if unconfigured."""
    global _client, _unavailable_reason
    if _client is not None:
        return _client
    if not is_configured():
        _unavailable_reason = (
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY "
            "in .env to persist to ORIGINEX HUMAN ARCHIVES. Running in specs-only "
            "mode (artifacts saved to disk only)."
        )
        return None
    try:
        from supabase import create_client
    except ImportError:
        _unavailable_reason = "supabase package not installed (pip install supabase>=2.0.0)."
        return None
    _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


def unavailable_reason() -> str | None:
    """Human-readable explanation when the client is unavailable."""
    return _unavailable_reason


# --------------------------------------------------------------------------- #
#  Audit                                                                        #
# --------------------------------------------------------------------------- #

def log_decision(
    agent: str,
    action: str,
    *,
    episode_id: str | None = None,
    payload: dict | None = None,
    sql_text: str | None = None,
) -> None:
    """Append an entry to video_decision_log. Never raises."""
    client = get_client()
    if client is None:
        return
    try:
        client.table("video_decision_log").insert({
            "episode_id": episode_id,
            "agent": agent,
            "action": action,
            "payload": payload or {},
            "sql_text": sql_text,
        }).execute()
    except Exception:
        # Audit logging must never break the pipeline.
        pass


# --------------------------------------------------------------------------- #
#  Episodes (owned: video_episodes)                                             #
# --------------------------------------------------------------------------- #

def create_episode(
    *,
    title: str,
    slug: str,
    channel: str = "history_channel",
    topic: str | None = None,
    target_minutes: float = 12,
    content_idea_id: str | None = None,
    related: dict[str, list[str]] | None = None,
) -> dict | None:
    """Insert a new episode row. Returns the created row (or None if no DB)."""
    client = get_client()
    if client is None:
        return None
    row: dict[str, Any] = {
        "title": title,
        "slug": slug,
        "channel": channel,
        "topic": topic,
        "target_minutes": target_minutes,
        "content_idea_id": content_idea_id,
        "status": "draft",
    }
    for key in (
        "related_documents", "related_people", "related_events",
        "related_places", "related_civilizations", "related_citations",
    ):
        if related and key in related:
            row[key] = related[key]
    result = client.table("video_episodes").insert(row).execute()
    created = result.data[0] if result.data else None
    if created:
        log_decision("director", "create_episode",
                     episode_id=created["id"], payload={"slug": slug})
    return created


def set_episode_status(episode_id: str, status: str) -> None:
    """Advance an episode's pipeline status."""
    client = get_client()
    if client is None:
        return
    client.table("video_episodes").update({"status": status}).eq("id", episode_id).execute()
    log_decision("director", "set_status", episode_id=episode_id, payload={"status": status})


def get_episode(episode_id: str) -> dict | None:
    client = get_client()
    if client is None:
        return None
    result = client.table("video_episodes").select("*").eq("id", episode_id).limit(1).execute()
    return result.data[0] if result.data else None


# --------------------------------------------------------------------------- #
#  Agent outputs (owned: video_agent_outputs)                                   #
# --------------------------------------------------------------------------- #

def save_agent_output(
    episode_id: str,
    role: str,
    *,
    payload: dict | None = None,
    content_md: str | None = None,
    model: str | None = None,
) -> dict | None:
    """Persist one crew agent's output for an episode (append-only)."""
    client = get_client()
    if client is None:
        return None
    result = client.table("video_agent_outputs").insert({
        "episode_id": episode_id,
        "role": role,
        "payload": payload or {},
        "content_md": content_md,
        "model": model or settings.model,
    }).execute()
    saved = result.data[0] if result.data else None
    log_decision(role, "save_output", episode_id=episode_id,
                 payload={"has_payload": bool(payload), "has_md": bool(content_md)})
    return saved


# --------------------------------------------------------------------------- #
#  Manifest (owned: video_manifest)                                             #
# --------------------------------------------------------------------------- #

def upsert_manifest(
    episode_id: str,
    *,
    manifest: dict | None = None,
    remotion_props: dict | None = None,
    srt: str | None = None,
    captions: dict | None = None,
) -> dict | None:
    """Insert or update the render contract for an episode."""
    client = get_client()
    if client is None:
        return None
    row = {
        "episode_id": episode_id,
        "manifest": manifest,
        "remotion_props": remotion_props,
        "srt": srt,
        "captions": captions,
    }
    result = client.table("video_manifest").upsert(row, on_conflict="episode_id").execute()
    saved = result.data[0] if result.data else None
    log_decision("manifest", "upsert_manifest", episode_id=episode_id)
    return saved


# --------------------------------------------------------------------------- #
#  Assets (owned: video_assets + Storage)                                       #
# --------------------------------------------------------------------------- #

def upload_asset(
    episode_id: str,
    local_path: str,
    *,
    kind: str,
    sequence: int | None = None,
    prompt: str | None = None,
    citation_id: str | None = None,
    content_type: str = "application/octet-stream",
    meta: dict | None = None,
) -> dict | None:
    """Upload a local file to Storage and record it in video_assets.

    Returns the asset row including its public_url, or None if no DB.
    """
    client = get_client()
    if client is None:
        return None
    import os

    bucket = settings.supabase_storage_bucket
    filename = os.path.basename(local_path)
    storage_path = f"{episode_id}/{kind}/{filename}"

    with open(local_path, "rb") as f:
        client.storage.from_(bucket).upload(
            storage_path, f.read(),
            {"content-type": content_type, "upsert": "true"},
        )
    public_url = client.storage.from_(bucket).get_public_url(storage_path)

    result = client.table("video_assets").insert({
        "episode_id": episode_id,
        "kind": kind,
        "sequence": sequence,
        "storage_path": storage_path,
        "public_url": public_url,
        "prompt": prompt,
        "citation_id": citation_id,
        "meta": meta or {},
    }).execute()
    saved = result.data[0] if result.data else None
    log_decision("visual", "upload_asset", episode_id=episode_id,
                 payload={"kind": kind, "path": storage_path})
    return saved


# --------------------------------------------------------------------------- #
#  Render jobs (owned: render_jobs)                                             #
# --------------------------------------------------------------------------- #

def create_render_job(episode_id: str, engine: str = "remotion") -> dict | None:
    client = get_client()
    if client is None:
        return None
    result = client.table("render_jobs").insert({
        "episode_id": episode_id, "engine": engine, "status": "queued",
    }).execute()
    return result.data[0] if result.data else None


def finish_render_job(
    job_id: str,
    *,
    status: str,
    out_path: str | None = None,
    out_url: str | None = None,
    logs: str | None = None,
    duration_seconds: float | None = None,
) -> None:
    client = get_client()
    if client is None:
        return
    client.table("render_jobs").update({
        "status": status,
        "out_path": out_path,
        "out_url": out_url,
        "logs": logs,
        "duration_seconds": duration_seconds,
        "finished_at": "now()",
    }).eq("id", job_id).execute()


# --------------------------------------------------------------------------- #
#  Archive reads — sourced facts for the Research agent                          #
# --------------------------------------------------------------------------- #

_ENTITY_TABLES = {
    "people": "name,slug,biography,significance,birth_date,death_date,regions",
    "events": "name,slug,description,significance,event_type,date_start,date_end",
    "places": "name,slug,modern_name,description,significance,place_type,modern_country",
    "civilizations": "name,slug,description,significance,date_start,date_end,peak_period",
}


def search_archive(query: str, *, table: str, limit: int = 8) -> list[dict]:
    """Full-text-ish search over an archive entity table by name/description.

    Uses case-insensitive ILIKE on the primary text columns. Parameterised via
    the client builder (no string interpolation into SQL).
    """
    client = get_client()
    if client is None or table not in _ENTITY_TABLES:
        return []
    cols = _ENTITY_TABLES[table]
    try:
        result = (
            client.table(table)
            .select(cols)
            .ilike("name", f"%{query}%")
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_citations_for_documents(document_ids: list[str], limit: int = 50) -> list[dict]:
    """Fetch citations tied to a set of documents (for on-screen sourcing)."""
    client = get_client()
    if client is None or not document_ids:
        return []
    result = (
        client.table("citations")
        .select("id,title,author,year,source_type,reliability,url,quote,document_id")
        .in_("document_id", document_ids)
        .limit(limit)
        .execute()
    )
    return result.data or []


def format_archive_hits(hits: list[dict]) -> str:
    """Render archive search hits as readable text for an agent's context."""
    if not hits:
        return "No archive matches."
    lines = []
    for h in hits:
        name = h.get("name") or h.get("title") or h.get("slug", "?")
        desc = h.get("significance") or h.get("description") or h.get("biography") or ""
        sim = h.get("similarity")
        tag = f" (match {sim:.2f})" if isinstance(sim, (int, float)) else ""
        lines.append(f"- {name}{tag}: {desc[:300]}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Semantic (vector) search — match_archive RPC over halfvec embeddings         #
# --------------------------------------------------------------------------- #

_SEMANTIC_TABLES = (
    "people", "events", "places", "civilizations",
    "documents", "citations", "oral_evidence",
)


def semantic_search(query: str, *, table: str, limit: int = 6) -> list[dict]:
    """Vector search one archive table via the match_archive RPC.

    Embeds `query` with OpenAI and ranks rows by cosine similarity. Returns []
    (so callers fall back to ILIKE) when OpenAI/Supabase are unconfigured or
    the table has no embeddings yet.
    """
    client = get_client()
    if client is None:
        return []
    from tools.embeddings import embed_text
    vec = embed_text(query)
    if not vec:
        return []
    try:
        result = client.rpc("match_archive", {
            "query_embedding": vec,
            "match_table": table,
            "match_count": limit,
        }).execute()
        return result.data or []
    except Exception:
        return []


def archive_context(query: str, *, tables: tuple[str, ...] | None = None,
                    per_table: int = 4) -> tuple[str, dict[str, list[str]]]:
    """Hybrid sourced-facts context for the Research agent.

    Tries semantic (vector) search per table and falls back to ILIKE name
    matching when embeddings aren't available. Returns (formatted_text,
    related_ids) where related_ids maps e.g. 'related_people' -> [uuid,...]
    for linking the episode back to the archive.
    """
    client = get_client()
    if client is None:
        return "", {}
    tables = tables or ("places", "people", "events", "civilizations")
    chunks: list[str] = []
    related: dict[str, list[str]] = {}
    for table in tables:
        hits = semantic_search(query, table=table, limit=per_table)
        mode = "semantic"
        if not hits:
            hits = search_archive(query, table=table, limit=per_table)
            mode = "name-match"
        if not hits:
            continue
        chunks.append(f"[{table} · {mode}]\n{format_archive_hits(hits)}")
        ids = [h["id"] for h in hits if h.get("id")]
        if ids:
            related[f"related_{table}"] = ids
    return "\n\n".join(chunks), related


# --------------------------------------------------------------------------- #
#  Content ideas backlog (read + status) — feeds the producer                   #
# --------------------------------------------------------------------------- #

def list_content_ideas(*, status: str | None = None, limit: int = 20) -> list[dict]:
    """List backlog ideas, newest first, optionally filtered by status."""
    client = get_client()
    if client is None:
        return []
    q = client.table("content_ideas").select(
        "id,title,description,content_type,status,hook,estimated_views,"
        "related_documents,related_people,related_events,created_at"
    )
    if status:
        q = q.eq("status", status)
    return q.order("estimated_views", desc=True).limit(limit).execute().data or []


def get_content_idea(idea_id: str) -> dict | None:
    client = get_client()
    if client is None:
        return None
    result = client.table("content_ideas").select("*").eq("id", idea_id).limit(1).execute()
    return result.data[0] if result.data else None


def set_content_idea_status(idea_id: str, status: str) -> None:
    client = get_client()
    if client is None:
        return
    client.table("content_ideas").update({"status": status}).eq("id", idea_id).execute()
    log_decision("director", "idea_status", payload={"idea": idea_id, "status": status})


# --------------------------------------------------------------------------- #
#  Embedding queue worker — makes the archive semantically searchable           #
# --------------------------------------------------------------------------- #

def _vec_literal(vec: list[float]) -> str:
    """pgvector/halfvec text form: '[0.1,0.2,...]'."""
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"


def drain_embedding_queue(*, batch_size: int = 64, max_rows: int | None = None,
                          progress=None) -> dict:
    """Embed pending `embedding_queue` rows and write vectors back to the archive.

    Processes in batches: fetch pending → embed text → UPDATE each source row's
    `embedding` → mark the queue row done. Returns a summary dict. Requires both
    Supabase and OpenAI to be configured.
    """
    client = get_client()
    if client is None:
        return {"error": _unavailable_reason or "Supabase not configured", "done": 0}
    from tools.embeddings import embed_texts, is_configured as openai_ready
    if not openai_ready():
        return {"error": "OPENAI_API_KEY not set", "done": 0}

    done = 0
    failed = 0
    while max_rows is None or done + failed < max_rows:
        remaining = batch_size if max_rows is None else min(batch_size, max_rows - done - failed)
        pending = (
            client.table("embedding_queue")
            .select("id,table_name,row_id,text_to_embed")
            .eq("status", "pending")
            .limit(remaining)
            .execute()
            .data or []
        )
        if not pending:
            break
        try:
            vectors = embed_texts([r["text_to_embed"] or "" for r in pending])
        except Exception as e:  # batch-level failure — mark and continue
            ids = [r["id"] for r in pending]
            client.table("embedding_queue").update(
                {"status": "error", "error_message": str(e)[:500]}
            ).in_("id", ids).execute()
            failed += len(pending)
            continue
        for row, vec in zip(pending, vectors):
            try:
                client.table(row["table_name"]).update(
                    {"embedding": _vec_literal(vec)}
                ).eq("id", row["row_id"]).execute()
                client.table("embedding_queue").update(
                    {"status": "done", "embedded_at": "now()"}
                ).eq("id", row["id"]).execute()
                done += 1
            except Exception as e:
                client.table("embedding_queue").update(
                    {"status": "error", "error_message": str(e)[:500]}
                ).eq("id", row["id"]).execute()
                failed += 1
        if progress:
            progress(done, failed)
    return {"done": done, "failed": failed}
