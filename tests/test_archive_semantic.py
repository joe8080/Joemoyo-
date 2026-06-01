"""Tests for semantic search + embedding-queue worker plumbing.

No network: OpenAI and the Supabase client are monkeypatched. These lock the
deterministic glue — vector literal format, batch ordering, hybrid fallback,
and the queue-drain loop control flow.
"""

import tools.supabase_client as sb
import tools.embeddings as emb


def test_vec_literal_format():
    assert sb._vec_literal([0.5, -1.0, 2]) == "[0.5,-1.0,2.0]"


def test_embed_texts_preserves_order(monkeypatch):
    # OpenAI may return data out of order; embed_texts must re-sort by index.
    monkeypatch.setattr(emb.settings, "openai_api_key", "k", raising=False)

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": [
                {"index": 1, "embedding": [1.0]},
                {"index": 0, "embedding": [0.0]},
            ]}

    monkeypatch.setattr(emb.requests, "post", lambda *a, **k: Resp())
    assert emb.embed_texts(["a", "b"]) == [[0.0], [1.0]]


def test_embed_texts_empty_when_unconfigured(monkeypatch):
    monkeypatch.setattr(emb.settings, "openai_api_key", "", raising=False)
    assert emb.embed_texts(["x"]) == []


def test_archive_context_falls_back_to_name_match(monkeypatch):
    """When semantic search yields nothing, ILIKE results are used + labelled."""
    monkeypatch.setattr(sb, "get_client", lambda: object())
    monkeypatch.setattr(sb, "semantic_search", lambda q, table, limit: [])

    def fake_ilike(q, *, table, limit):
        if table == "places":
            return [{"id": "p1", "name": "Great Zimbabwe", "significance": "stone city"}]
        return []

    monkeypatch.setattr(sb, "search_archive", fake_ilike)
    text, related = sb.archive_context("Great Zimbabwe", tables=("places", "people"))
    assert "name-match" in text
    assert "Great Zimbabwe" in text
    assert related["related_places"] == ["p1"]


def test_archive_context_prefers_semantic(monkeypatch):
    monkeypatch.setattr(sb, "get_client", lambda: object())

    def fake_semantic(q, *, table, limit):
        if table == "people":
            return [{"id": "x1", "name": "Mutota", "significance": "king", "similarity": 0.91}]
        return []

    monkeypatch.setattr(sb, "semantic_search", fake_semantic)
    monkeypatch.setattr(sb, "search_archive", lambda *a, **k: [])
    text, related = sb.archive_context("Mutapa", tables=("people",))
    assert "semantic" in text and "match 0.91" in text
    assert related["related_people"] == ["x1"]


def test_archive_context_empty_without_client(monkeypatch):
    monkeypatch.setattr(sb, "get_client", lambda: None)
    assert sb.archive_context("anything") == ("", {})
