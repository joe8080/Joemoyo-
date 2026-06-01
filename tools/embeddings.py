"""OpenAI text embeddings — 1536-dim vectors that match the ORIGINEX archive.

Used for two things:
  1. Embedding the search query so the Research agent can do semantic
     (vector) lookups against the archive's `embedding` columns.
  2. Draining `embedding_queue` (the worker) so the archive becomes searchable.

Key-gated on OPENAI_API_KEY; returns None / [] gracefully when unset.
Model: text-embedding-3-small (1536 dims) — must match the DB columns.
"""

from __future__ import annotations

import requests

from config.settings import settings

_URL = "https://api.openai.com/v1/embeddings"


def is_configured() -> bool:
    return bool(settings.openai_api_key)


def embed_texts(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed a batch of texts. Returns one vector per input (order preserved).

    Returns [] when OpenAI isn't configured so callers can fall back.
    """
    if not is_configured() or not texts:
        return []
    resp = requests.post(
        _URL,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        json={"model": model or settings.embedding_model, "input": texts},
        timeout=60,
    )
    resp.raise_for_status()
    data = sorted(resp.json()["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in data]


def embed_text(text: str, *, model: str | None = None) -> list[float] | None:
    """Embed a single string, or None if unconfigured/empty."""
    if not text:
        return None
    vecs = embed_texts([text], model=model)
    return vecs[0] if vecs else None
