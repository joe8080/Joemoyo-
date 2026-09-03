"""
Unit tests for the Jarvis package. No network: every HTTP call is mocked.
Run with: python -m pytest tests/test_jarvis.py -q
"""
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from jarvis.brain import Jarvis, TOOLS, build_live_context, echoable_content  # noqa: E402
from jarvis.config import JarvisConfig  # noqa: E402
from jarvis.content import OGX  # noqa: E402
from jarvis.runner import JarvisRunner  # noqa: E402
from jarvis.supabase_client import SupabaseREST  # noqa: E402
from jarvis.telegram import chunk_text  # noqa: E402
from jarvis.vault import Vault  # noqa: E402
from jarvis import voice  # noqa: E402


def make_cfg(**overrides) -> JarvisConfig:
    base = dict(
        anthropic_api_key="test-key", model="claude-opus-5", effort="high", max_tokens=4000, fallbacks=False,
        vault_url="https://vault.example", vault_key="vault-key",
        ogx_url="https://ogx.example", ogx_key="ogx-key",
        telegram_token="tok", telegram_chat_id="123", poll_timeout=1,
        owner_key="owner@example.test", assistant_name="Jarvis",
        openai_api_key="", elevenlabs_api_key="", elevenlabs_voice_id="",
        voice_replies=True, history_turns=3, context_ttl_seconds=600,
    )
    base.update(overrides)
    return JarvisConfig(**base)


# ---- telegram --------------------------------------------------------------- #

def test_chunk_text_splits_on_line_boundaries():
    text = "\n".join(f"line {i} " + "x" * 50 for i in range(200))
    chunks = chunk_text(text, limit=1000)
    assert all(len(c) <= 1000 for c in chunks)
    assert "".join(c.replace("\n", "") for c in chunks).replace(" ", "") == text.replace("\n", "").replace(" ", "")
    assert chunk_text("") == ["(empty reply)"]


# ---- supabase client -------------------------------------------------------- #

def test_select_builds_postgrest_query():
    db = SupabaseREST("https://x.supabase.co", "k", label="t")
    with patch("jarvis.supabase_client.requests.get") as get:
        get.return_value = MagicMock(status_code=200, json=lambda: [{"a": 1}])
        rows = db.select("holdings", {"status": "eq.active", "order": "value.desc"}, limit=5)
    assert rows == [{"a": 1}]
    args, kwargs = get.call_args
    assert args[0] == "https://x.supabase.co/rest/v1/holdings"
    assert kwargs["params"] == {"select": "*", "status": "eq.active", "order": "value.desc", "limit": "5"}
    assert kwargs["headers"]["Authorization"] == "Bearer k"


def test_disabled_client_is_safe():
    db = SupabaseREST("", "")
    assert db.select("anything") == []
    assert db.insert("anything", {"a": 1}) is False
    assert db.insert("anything", {"a": 1}, returning=True) is None
    assert db.update("anything", {"id": "eq.1"}, {"a": 2}) is False


def test_any_of_sanitises_search_terms():
    expr = SupabaseREST.any_of("Mansa Musa, (gold)", ["title", "quote"])
    assert expr == "(title.ilike.*Mansa Musa gold*,quote.ilike.*Mansa Musa gold*)"


def test_vault_writes_never_raise_and_strip_nones():
    vault = Vault("https://x.supabase.co", "k")
    with patch("jarvis.supabase_client.requests.post") as post:
        post.return_value = MagicMock(status_code=201, json=lambda: [])
        assert vault.log_decision("portfolio", "Trim RGTI", "Trim to 2%") is True
        body = post.call_args.kwargs["json"][0]
    assert body["domain"] == "portfolio" and body["is_trade"] is False
    assert "reasoning" not in body and "ticker" not in body
    assert body["decision_date"]


# ---- brain ------------------------------------------------------------------ #

def fake_vault():
    v = MagicMock(spec=Vault)
    v.enabled = True
    v.profile.return_value = {"display_name": "Joe", "risk_posture": "aggressive_growth_with_rules",
                              "north_star_target_gbp": 1000000, "north_star_years_min": 7,
                              "north_star_years_max": 10, "passive_income_target_monthly_gbp": 1000,
                              "max_single_stock_pct": 10, "max_theme_pct": 20, "account_rules": {}}
    v.owner_key.return_value = "owner@example.test"
    v.rules.return_value = [{"domain": "portfolio", "rule_name": "isa_first", "rule_text": "ISA before GIA."}]
    v.goals.return_value = [{"goal_name": "Passive income", "status": "active", "progress_pct": 12.5,
                             "target_value_gbp": 1200, "current_value_gbp": 150, "notes": ""}]
    v.portfolio_summary.return_value = {"snapshot_date": "2026-09-01", "total_value_gbp": 106000,
                                        "isa_value_gbp": 60000, "gia_value_gbp": 46000,
                                        "total_pnl_gbp": 7000, "total_pnl_pct": 7.1, "holding_count": 20,
                                        "progress_pct": 10.6}
    v.net_worth.return_value = {}
    v.holdings.return_value = [{"ticker": "MSFT", "account": "ISA", "current_value_gbp": 9000,
                                "pnl_pct": 12.0, "bucket": "core", "snapshot_date": "2026-09-01"}]
    v.watchlist.return_value = [{"ticker": "VRT", "priority": "high"}]
    v.recent_decisions.return_value = [{"decision_date": "2026-08-28", "domain": "investing", "title": "No deployment"}]
    v.recent_sessions.return_value = []
    v.ventures.return_value = [{"name": "OGX", "status": "active"}]
    v.content_pipeline.return_value = []
    v.content_log.return_value = []
    v.recall.return_value = []
    v.remember.return_value = True
    v.log_decision.return_value = True
    v.log_memory_event.return_value = True
    v.log_message.return_value = True
    v.start_conversation.return_value = "conv-1"
    v.latest_conversation.return_value = {}
    v.telegram_chat_id.return_value = ""
    return v


def fake_ogx():
    o = MagicMock(spec=OGX)
    o.enabled = True
    o.ideas.return_value = [{"title": "Mansa Musa", "status": "idea", "content_type": "long_form"}]
    o.episodes.return_value = []
    o.competitive_brief.return_value = {"run_date": "2026-08-30", "headline": "Peers pivot to shorts"}
    o.scholarly_flags.return_value = [{"subject": "Abu Bakr II", "claim": "Reached the Americas"}]
    o.open_research_flags.return_value = []
    o.declass_new.return_value = []
    o.search_citations.return_value = [{"title": "Tarikh al-Sudan"}]
    o.add_idea.return_value = True
    return o


def test_live_context_contains_rules_goals_holdings_and_flags():
    text = build_live_context(fake_vault(), fake_ogx(), "Jarvis")
    assert "isa_first" in text and "ISA before GIA" in text
    assert "Passive income" in text and "12.5%" in text
    assert "MSFT" in text and "£9,000" in text
    assert "Abu Bakr II" in text
    assert "Peers pivot to shorts" in text


def test_execute_tool_dispatches_and_logs_memory_event():
    v, o = fake_vault(), fake_ogx()
    brain = Jarvis(make_cfg(), v, o, client=MagicMock())
    assert '"MSFT"' in brain.execute_tool("get_holdings", {"limit": 5})
    assert brain.execute_tool("search_ogx", {"query": "Sudan", "kind": "citations"}).startswith("[")
    assert brain.execute_tool("log_decision", {"domain": "portfolio", "title": "T", "decision_made": "D"}) == "logged"
    v.log_memory_event.assert_called_once()
    assert brain.execute_tool("remember", {"title": "Amy", "content": "Partner"}) == "saved"
    with pytest.raises(ValueError):
        brain.execute_tool("nope", {})


def test_tool_names_are_unique_and_have_schemas():
    names = [t["name"] for t in TOOLS]
    assert len(names) == len(set(names))
    assert all(t["input_schema"]["type"] == "object" for t in TOOLS)


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.message


def test_reply_runs_tool_loop_and_returns_text():
    v, o = fake_vault(), fake_ogx()
    tool_turn = SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", id="tu1", name="get_goals", input={})],
    )
    final_turn = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text="1. Passive income is 12.5% along.")],
    )
    client = MagicMock()
    client.messages.stream.side_effect = [FakeStream(tool_turn), FakeStream(final_turn)]
    brain = Jarvis(make_cfg(), v, o, client=client)
    text, tools = brain.reply("How are my goals?", [])
    assert text.startswith("1. Passive income")
    assert tools == ["get_goals"]
    second_call = client.messages.stream.call_args_list[1].kwargs
    assert second_call["messages"][-1]["content"][0]["type"] == "tool_result"
    assert second_call["messages"][-1]["content"][0]["tool_use_id"] == "tu1"
    assert second_call["thinking"] == {"type": "adaptive"}
    assert second_call["output_config"] == {"effort": "high"}
    assert second_call["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_reply_handles_refusal():
    client = MagicMock()
    client.messages.stream.return_value = FakeStream(SimpleNamespace(stop_reason="refusal", content=[]))
    brain = Jarvis(make_cfg(), fake_vault(), fake_ogx(), client=client)
    text, _ = brain.reply("x", [])
    assert "can't help" in text


# ---- voice ------------------------------------------------------------------ #

def test_voice_without_keys_is_a_noop():
    cfg = make_cfg()
    assert voice.transcribe(cfg, b"audio") is None
    assert voice.synthesize(cfg, "hello") is None
    assert cfg.can_transcribe is False and cfg.can_speak is False


def test_synthesize_truncates_long_text():
    cfg = make_cfg(elevenlabs_api_key="k", elevenlabs_voice_id="v")
    with patch("jarvis.voice.requests.post") as post:
        post.return_value = MagicMock(ok=True, content=b"mp3")
        assert voice.synthesize(cfg, "word " * 1000) == b"mp3"
        sent = post.call_args.kwargs["json"]["text"]
    assert len(sent) < 1600 and sent.endswith("The rest is in the text above.")


# ---- runner ----------------------------------------------------------------- #

def make_runner(**cfg_overrides):
    cfg = make_cfg(**cfg_overrides)
    v, o = fake_vault(), fake_ogx()
    brain = MagicMock()
    brain.owner_key = "owner@example.test"
    brain.fallbacks_enabled = False
    brain.reply.return_value = ("Portfolio is at 106 thousand pounds.", ["get_portfolio_summary"])
    bot = MagicMock()
    runner = JarvisRunner(cfg, vault=v, ogx=o, brain=brain, bot=bot)
    runner.start_conversation("Telegram test")
    return runner, brain, bot, v


def test_unauthorised_chat_is_refused():
    runner, brain, bot, _ = make_runner()
    runner.handle_update({"update_id": 1, "message": {"chat": {"id": 999}, "text": "hello"}})
    brain.reply.assert_not_called()
    assert "Not authorised" in bot.send_message.call_args.args[1]
    assert "999" in bot.send_message.call_args.args[1]


def test_authorised_text_reaches_brain_and_is_persisted():
    runner, brain, bot, v = make_runner()
    runner.handle_update({"update_id": 2, "message": {"chat": {"id": 123}, "text": "How is the portfolio?"}})
    brain.reply.assert_called_once()
    assert brain.reply.call_args.args[0] == "How is the portfolio?"
    bot.send_message.assert_called_with(123, "Portfolio is at 106 thousand pounds.")
    assert runner.history[-1] == {"role": "assistant", "content": "Portfolio is at 106 thousand pounds."}
    assert v.log_message.call_count == 2


def test_history_is_trimmed_to_configured_turns():
    runner, brain, bot, _ = make_runner(history_turns=2)
    for i in range(5):
        runner.handle_update({"update_id": i, "message": {"chat": {"id": 123}, "text": f"q{i}"}})
    assert len(runner.history) == 4
    assert runner.history[0]["role"] == "user" and runner.history[0]["content"] == "q3"


def test_commands_do_not_call_claude():
    runner, brain, bot, _ = make_runner()
    runner.handle_update({"update_id": 3, "message": {"chat": {"id": 123}, "text": "/help"}})
    runner.handle_update({"update_id": 4, "message": {"chat": {"id": 123}, "text": "/voice off"}})
    runner.handle_update({"update_id": 5, "message": {"chat": {"id": 123}, "text": "/portfolio"}})
    brain.reply.assert_not_called()
    assert runner.voice_replies is False
    texts = [c.args[1] for c in bot.send_message.call_args_list]
    assert any("Commands:" in t for t in texts)
    assert any("106,000" in t for t in texts)


def test_voice_note_without_transcription_gets_guidance():
    runner, brain, bot, _ = make_runner()
    runner.handle_update({"update_id": 6, "message": {"chat": {"id": 123}, "voice": {"file_id": "f1"}}})
    brain.reply.assert_not_called()
    assert "voice notes" in bot.send_message.call_args.args[1]


def test_voice_note_is_transcribed_and_answered():
    runner, brain, bot, _ = make_runner(openai_api_key="k")
    bot.download.return_value = b"ogg"
    with patch("jarvis.runner.voice.transcribe", return_value="what are my goals"):
        runner.handle_update({"update_id": 7, "message": {"chat": {"id": 123}, "voice": {"file_id": "f1"}}})
    assert brain.reply.call_args.args[0] == "what are my goals"
    texts = [c.args[1] for c in bot.send_message.call_args_list]
    assert texts[0] == "Heard: what are my goals"


def test_echoable_content_drops_pre_fallback_thinking_and_tool_use():
    blocks = [
        SimpleNamespace(type="thinking", thinking=""),
        SimpleNamespace(type="tool_use", id="old", name="get_goals", input={}),
        SimpleNamespace(type="text", text="partial"),
        SimpleNamespace(type="fallback"),
        SimpleNamespace(type="tool_use", id="new", name="get_rules", input={}),
    ]
    kept = echoable_content(blocks)
    assert [b.type for b in kept] == ["text", "fallback", "tool_use"]
    assert kept[-1].id == "new"
    plain = [SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text="x")]
    assert echoable_content(plain) == plain
