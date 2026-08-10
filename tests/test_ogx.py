#!/usr/bin/env python3
"""
Schema-contract and wiring tests for the OGX agents system.

    python tests/test_ogx.py

Stdlib only — no pytest, no network, no Claude API calls. Run it after any
change to the OGX research database schema or to tools/ogx_db.py.

Why this file exists: the OGX pipeline's real failure mode is not bad Python,
it is a silent mismatch with the research database. Three of these tests encode
constraints that already bit during development —

  * `alternate_names` is `text[]`, so an ilike filter against it raises
    "operator does not exist: text[] ~~*" and takes the whole query with it.
  * `video_episodes.status` and `video_agent_outputs.role` have CHECK
    constraints; a plausible-sounding value like "in_production" or
    "video_build" is rejected with a 400 and the output is silently lost.
  * `video_episodes.slug` is UNIQUE, so a second build of the same subject
    conflicts unless the insert retries.

None of those show up until a live run, by which point the API spend is done.
"""

import inspect
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-not-a-real-key")

from agents.ogx_packaging import OGXPackagingAgent          # noqa: E402
from agents.ogx_research import OGXResearchAgent            # noqa: E402
from agents.ogx_script import OGXScriptWriterAgent          # noqa: E402
from agents.ogx_video_build import OGXVideoBuildAgent       # noqa: E402
from config.brand_profiles import BRAND_PROFILES            # noqa: E402
from orchestrator.orchestrator import BusinessOrchestrator  # noqa: E402
from tools import ogx_db                                    # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []


def check(name, fn):
    try:
        fn()
        print(f"  PASS  {name}")
    except Exception as e:  # noqa: BLE001 — a failing check is the point
        failures.append((name, e))
        print(f"  FAIL  {name}: {type(e).__name__}: {e}")


def expect_error(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return True
    raise AssertionError(f"expected {exc.__name__}, none raised")


# --------------------------------------------------------------------------- #
#  Fake transport — records requests, replays canned responses                  #
# --------------------------------------------------------------------------- #

class FakeResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else []
        self.text = "" if status_code < 300 else "error body"

    def json(self):
        return self._payload


class FakeRequests:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.last_body = None

    def _next(self, verb, url, params):
        self.calls.append({"verb": verb, "url": url, "params": params or {}})
        return self.responses.pop(0) if self.responses else FakeResp(200, [])

    def get(self, url, params=None, headers=None, timeout=None):
        return self._next("GET", url, params)

    def post(self, url, params=None, headers=None, json=None, timeout=None):
        self.last_body = json
        return self._next("POST", url, params)

    def patch(self, url, params=None, headers=None, json=None, timeout=None):
        self.last_body = json
        return self._next("PATCH", url, params)


def with_fake(responses):
    """Install credentials plus a fake transport; returns the recorder."""
    ogx_db._URL = "https://test.supabase.co"
    ogx_db._KEY = "test-key"
    fake = FakeRequests(responses)
    ogx_db.requests = fake
    return fake


def without_credentials():
    ogx_db._URL = ""
    ogx_db._KEY = ""


AGENTS = {
    "research": OGXResearchAgent(),
    "script/archives": OGXScriptWriterAgent(style="archives"),
    "script/declassified": OGXScriptWriterAgent(style="declassified"),
    "video_build": OGXVideoBuildAgent(),
    "packaging": OGXPackagingAgent(),
}


# --------------------------------------------------------------------------- #

print("\n== brand profile ==")
brand = BRAND_PROFILES["origine_x"]
check("palette carries all six tokens", lambda: [
    brand["palette"][k] for k in ("gold", "dark", "crimson", "amber", "teal", "white")])
check("declassified palette present", lambda: brand["declassified_palette"]["gold"])
check("thumbnail brand anchors present",
      lambda: len(brand["thumbnail_references"]) >= 1 or 1 / 0)

print("\n== system prompts ==")
for name, agent in AGENTS.items():
    def _render(a=agent, n=name):
        prompt = a.system_prompt
        assert len(prompt) > 500, f"{n} prompt suspiciously short ({len(prompt)})"
        leftover = prompt.replace("{{", "").replace("}}", "")
        assert "{" not in leftover or "{mm:ss}" in prompt, \
            f"{n} has an unsubstituted placeholder"
        assert "EVIDENCE RULES" in prompt, f"{n} lost the evidence contract"
    check(f"{name} prompt renders", _render)

check("invalid script style rejected",
      lambda: expect_error(ValueError, OGXScriptWriterAgent, "nope"))

print("\n== tool definitions ==")
for name, agent in AGENTS.items():
    def _tools(a=agent, n=name):
        tools = a.tool_definitions
        assert tools, f"{n} has no tools"
        for tool in tools:
            assert set(tool) >= {"name", "description", "input_schema"}, f"{n}: {tool}"
            assert tool["input_schema"]["type"] == "object"
            assert tool["input_schema"].get("required")
        assert "ogx_verify_claim" in [t["name"] for t in tools], \
            f"{n} cannot verify claims"
    check(f"{name} tools well-formed", _tools)

research_tools = [t["name"] for t in AGENTS["research"].tool_definitions]
check("research agent has the full toolkit",
      lambda: all(t in research_tools for t in (
          "ogx_db_search", "ogx_db_citations", "ogx_db_evidence",
          "ogx_verify_claim", "web_search", "search_academic_sources")) or 1 / 0)
check("search tool enum matches SEARCHABLE",
      lambda: [t for t in AGENTS["research"].tool_definitions
               if t["name"] == "ogx_db_search"][0]
      ["input_schema"]["properties"]["entity_type"]["enum"]
      == list(ogx_db.SEARCHABLE) or 1 / 0)

print("\n== evidence gate ==")
without_credentials()
check("enabled() false without credentials", lambda: ogx_db.enabled() and 1 / 0)
check("require_enabled raises when unconfigured",
      lambda: expect_error(EnvironmentError, ogx_db.require_enabled))
check("reads raise rather than fake an empty result",
      lambda: expect_error(ogx_db.OGXDatabaseError, ogx_db.find_people, "test"))
check("writes stay best-effort and never raise",
      lambda: ogx_db.save_agent_output("x", "research", "md") is False or 1 / 0)


def _pipeline_gate():
    orch = object.__new__(BusinessOrchestrator)  # skip agent construction
    expect_error(EnvironmentError, BusinessOrchestrator.produce_ogx_video,
                 orch, "Test Topic")


check("pipeline refuses to run without the database", _pipeline_gate)


def _db_error_is_not_absence():
    notice = AGENTS["research"]._execute_ogx_tool("ogx_verify_claim", {"term": "x"})
    assert "DATABASE ERROR" in notice and "NOT evidence of absence" in notice, notice


check("a database failure is reported as an error, not as 'no evidence'",
      _db_error_is_not_absence)
check("unknown tool falls through to the subclass",
      lambda: AGENTS["research"]._execute_ogx_tool("nope", {}) is None or 1 / 0)

print("\n== query shapes ==")


def _substring_query():
    fake = with_fake([FakeResp(200, [{"name": "Nzinga"}])])
    assert ogx_db.find_people("Nzinga") == [{"name": "Nzinga"}]
    assert len(fake.calls) == 1, f"expected 1 request, got {len(fake.calls)}"
    params = fake.calls[0]["params"]
    assert params["or"] == "(name.ilike.*Nzinga*,slug.ilike.*Nzinga*)", params
    assert params["verified"] == "is.true", "lost the verified gate on people"
    assert "search_tsv" not in params, "ran full-text when substring matched"
    assert fake.calls[0]["url"].endswith("/rest/v1/people")


check("people substring query shape", _substring_query)


def _no_array_columns():
    """An ilike against a text[] column raises 42883 and kills the query."""
    array_cols = ("alternate_names", "roles", "regions", "civilizations",
                  "sources", "key_figures", "causes", "consequences",
                  "key_achievements", "tags", "themes", "subjects",
                  "key_points", "source_urls", "examples", "key_questions",
                  "related_people", "related_events", "citation_ids",
                  "key_scholars", "document_ids")
    finders = (ogx_db.find_people, ogx_db.find_events, ogx_db.find_places,
               ogx_db.find_civilizations, ogx_db.find_documents,
               ogx_db.find_themes, ogx_db.find_citations, ogx_db.find_debates,
               ogx_db.find_oral_evidence, ogx_db.find_content_ideas)
    for finder in finders:
        fake = with_fake([FakeResp(200, [{"hit": 1}])])
        finder("x")
        params = fake.calls[0]["params"]
        filters = params.get("or", "") + params.get("title", "")
        for col in array_cols:
            assert f"{col}.ilike" not in filters, \
                f"{finder.__name__} filters on array column {col}"


check("no ilike filter touches an array column", _no_array_columns)


def _full_text_fallback():
    fake = with_fake([FakeResp(200, []), FakeResp(200, [{"name": "Njinga"}])])
    assert ogx_db.find_people("Nzinga") == [{"name": "Njinga"}]
    assert len(fake.calls) == 2, "no fallback request was made"
    second = fake.calls[1]["params"]
    assert second["search_tsv"] == "plfts(english).Nzinga", second
    assert "or" not in second, "fallback kept the substring filter"
    assert second["verified"] == "is.true", "fallback dropped the verified gate"


check("empty substring result falls back to full-text", _full_text_fallback)


def _no_fallback_without_tsv():
    fake = with_fake([FakeResp(200, [])])
    assert ogx_db.find_themes("nothing") == []
    assert len(fake.calls) == 1, "queried search_tsv on a table that has none"


check("no full-text attempt on tables lacking search_tsv", _no_fallback_without_tsv)


def _http_error_raises():
    with_fake([FakeResp(400, None)])
    expect_error(ogx_db.OGXDatabaseError, ogx_db.find_events, "x")


check("an HTTP error raises rather than returning empty", _http_error_raises)
check("unknown entity type rejected",
      lambda: expect_error(ogx_db.OGXDatabaseError, ogx_db.search, "not_a_table", "x"))
check("filter builder strips grammar characters",
      lambda: ogx_db._match("Mansa*, Musa)", "name", "slug")
      == "(name.ilike.*Mansa Musa*,slug.ilike.*Mansa Musa*)" or 1 / 0)

print("\n== CHECK constraints ==")
check("invalid agent role rejected at the call site",
      lambda: expect_error(ValueError, ogx_db.save_agent_output, "id", "video_build", "md"))
check("invalid episode status rejected at the call site",
      lambda: expect_error(ValueError, ogx_db.set_episode_status, "id", "built"))
check("stage->status map only uses permitted values",
      lambda: (all(v in ogx_db.EPISODE_STATUSES for v in ogx_db.STAGE_STATUS.values())
               and all(k in ogx_db.AGENT_ROLES for k in ogx_db.STAGE_STATUS)) or 1 / 0)

orch_src = open(os.path.join(REPO, "orchestrator", "orchestrator.py"),
                encoding="utf-8").read()
roles_used = set(re.findall(r'record\("(\w+)"', orch_src))
check("every role the orchestrator writes passes the CHECK constraint",
      lambda: (roles_used and roles_used <= set(ogx_db.AGENT_ROLES)) or 1 / 0)

print("\n== writes ==")
check("slugify strips punctuation",
      lambda: ogx_db._slugify("Mansa Musa: The Empire's Gold!")
      == "mansa-musa-the-empire-s-gold" or 1 / 0)
check("slugify never returns empty", lambda: ogx_db._slugify("!!!") == "episode" or 1 / 0)


def _slug_conflict_retries():
    fake = with_fake([FakeResp(409, None), FakeResp(201, [{"id": "ep-123"}])])
    assert ogx_db.create_episode("Mansa Musa: The Gold", "Mansa Musa") == "ep-123"
    assert len(fake.calls) == 2, "did not retry after the unique-slug conflict"
    assert fake.last_body[0]["slug"].startswith("mansa-musa-the-gold-"), fake.last_body
    assert fake.last_body[0]["status"] == "draft", "opened with an invalid status"


check("unique-slug conflict retries with a timestamped slug", _slug_conflict_retries)


def _output_advances_status():
    fake = with_fake([FakeResp(201, [{"id": "out-1"}]), FakeResp(204, None)])
    assert ogx_db.save_agent_output("ep-1", "visual", "# build sheet") is True
    assert len(fake.calls) == 2, "episode status was not advanced"
    assert fake.calls[0]["url"].endswith("/rest/v1/video_agent_outputs")
    assert fake.calls[1]["verb"] == "PATCH"
    assert fake.calls[1]["params"] == {"id": "eq.ep-1"}
    assert fake.last_body == {"status": "visualizing"}, fake.last_body


check("saving an output advances the episode status", _output_advances_status)


def _write_failure_is_quiet():
    with_fake([FakeResp(500, None)])
    assert ogx_db.save_agent_output("ep-1", "script", "x") is False
    assert ogx_db.log_decision("ep-1", "agent", "action") is False


check("write failures return falsy and never raise", _write_failure_is_quiet)

print("\n== formatting ==")
check("an empty result is stated explicitly",
      lambda: "NO RECORDS FOUND" in ogx_db.format_rows("people", []) or 1 / 0)
check("rows render their fields",
      lambda: "Nzinga" in ogx_db.format_rows(
          "people", [{"name": "Nzinga", "roles": ["queen"]}]) or 1 / 0)
for status, marker in (("supported", "may state this directly"),
                       ("unsupported", "Do not ship it as fact"),
                       ("contested", "DO NOT state this as settled")):
    def _verdict(s=status, m=marker):
        verdict = {"term": "t", "status": s, "record_count": 1,
                   "support": {"people": []}, "contested": {"scholarly_debates": []}}
        assert m in ogx_db.format_verdict(verdict), f"{s} verdict lost its rule"
    check(f"verdict '{status}' carries its rule", _verdict)

print("\n== orchestrator and CLI ==")
signature = inspect.signature(BusinessOrchestrator.produce_ogx_video)
check("pipeline signature",
      lambda: all(p in signature.parameters for p in (
          "topic", "style", "target_minutes", "skip_research",
          "allow_unverified", "persist")) or 1 / 0)

from main import cli  # noqa: E402
check("ogx command registered", lambda: cli.commands["ogx"])
check("ogx CLI options",
      lambda: {p.name for p in cli.commands["ogx"].params} == {
          "topic", "style", "minutes", "stage", "from_file",
          "skip_research", "allow_unverified", "no_persist"} or 1 / 0)

print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} FAILURE(S)")
    for name, error in failures:
        print(f"  - {name}: {error}")
    sys.exit(1)
print("ALL OGX CHECKS PASSED")
