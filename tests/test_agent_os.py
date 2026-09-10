"""
Agent OS checks: the client speaks the gateway protocol, the worker runs the
task lifecycle, the roster is well-formed, the board page builds.

Run:  pytest tests/test_agent_os.py -q      (no network — the gateway is faked)
"""

import importlib
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class FakeGateway:
    """Records every POST and answers like the agent-os edge function."""

    def __init__(self):
        self.calls = []
        self.paused = set()
        self.tasks = {}

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "body": json, "headers": headers})
        key = headers.get("x-agent-key", "")
        if not key.startswith("agent_"):
            return _Resp(401, {"error": "agent_unauthorised"})
        agent = key.split("_")[1] + "_" + key.split("_")[2] if key.count("_") >= 3 else key
        action = json["action"]
        if action == "heartbeat":
            return _Resp(200, {"ok": True, "agent_key": agent, "status": "paused" if agent in self.paused else "active",
                               "paused": agent in self.paused})
        if action == "whoami":
            return _Resp(200, {"agent_key": agent, "paused": agent in self.paused})
        if action == "emit_event":
            return _Resp(201, {"event": {"subject": json["subject"]}})
        if action == "pull_tasks":
            return _Resp(200, {"tasks": [t for t in self.tasks.values() if t["assigned_to_agent"] == agent and t["status"] in ("pending", "claimed", "running")]})
        if action in ("claim_task", "start_task", "complete_task", "fail_task"):
            t = self.tasks[json["task_id"]]
            t["status"] = {"claim_task": "claimed", "start_task": "running", "complete_task": "completed", "fail_task": "failed"}[action]
            if action == "complete_task":
                t["summary"] = json["summary"]
            if action == "fail_task":
                t["error"] = json["error"]
            return _Resp(200, {"task": t})
        return _Resp(400, {"error": "unknown_action"})


class _Resp:
    def __init__(self, status, body):
        self.status_code, self._body, self.text = status, body, json.dumps(body)

    def json(self):
        return self._body


@pytest.fixture()
def gw(monkeypatch):
    monkeypatch.setenv("AGENT_OS_URL", "https://example.test/functions/v1/agent-os")
    monkeypatch.setenv("AGENT_OS_KEYS", json.dumps({"shopify_reporter": "agent_shopify_reporter_KEYAAAAAAAAAAAAAAAAAAAAAAAA",
                                                    "agent_os_runner": "agent_agent_os_runner_KEYBBBBBBBBBBBBBBBBBBBBBBBB",
                                                    "swing_trader": "agent_swing_trader_KEYCCCCCCCCCCCCCCCCCCCCCCCCCC"}))
    monkeypatch.delenv("AGENT_OS_KEY", raising=False)
    monkeypatch.delenv("AGENT_OS_DISABLED", raising=False)
    import agent_os.client as client
    importlib.reload(client)
    fake = FakeGateway()
    monkeypatch.setattr(client.requests, "post", fake)
    return fake


def test_client_reports_with_the_right_key(gw):
    from agent_os import client
    reply = client.report("shopify_reporter", "done", result="Weekly report sent", metrics={"orders": 12}, run_type="weekly")
    assert reply and reply["ok"] and reply["paused"] is False
    call = gw.calls[-1]
    assert call["headers"]["x-agent-key"].startswith("agent_shopify_reporter_")
    assert call["body"] == {"action": "heartbeat", "status": "done", "result": "Weekly report sent",
                            "metrics": {"orders": 12}, "run_type": "weekly", "source_system": client.source()}
    assert client.key_for("unknown_agent") == ""
    assert client.report("unknown_agent", "done") is None      # no key → not reported, no exception


def test_pause_is_visible_to_bots(gw):
    from agent_os import client
    gw.paused.add("swing_trader")
    hb = client.report("swing_trader", "running", task="cycle")
    assert hb["paused"] is True
    assert client.is_paused("swing_trader") is True
    assert client.is_paused("shopify_reporter") is False


def test_task_context_manager(gw):
    from agent_os import client
    with pytest.raises(RuntimeError):
        with client.task("shopify_reporter", "Weekly report"):
            raise RuntimeError("Shopify down")
    statuses = [c["body"]["status"] for c in gw.calls]
    assert statuses == ["running", "error"] and "Shopify down" in gw.calls[-1]["body"]["note"]
    with client.task("shopify_reporter", "Weekly report", result="Sent"):
        pass
    assert gw.calls[-1]["body"]["status"] == "done" and gw.calls[-1]["body"]["result"] == "Sent"


def test_worker_runs_the_task_lifecycle(gw, monkeypatch):
    from agent_os import client
    import agent_os.worker as worker
    importlib.reload(worker)
    seen = []
    monkeypatch.setitem(worker.RUNNERS, "shopify_reporter", lambda text: seen.append(text) or f"Report ({text or 'weekly'})")
    w = worker.Worker()
    assert "shopify_reporter" in w.agents and "swing_trader" in w.agents
    assert "trading_coach" in w.skipped                 # no key for it → skipped, not crashed
    gw.tasks["t1"] = {"id": "t1", "assigned_to_agent": "shopify_reporter", "status": "pending", "title": "Weekly report: monthly",
                      "instructions": "monthly", "context": {"input": "monthly", "run": True}, "attempt_count": 0}
    assert w.poll_once() == 1
    assert seen == ["monthly"] and gw.tasks["t1"]["status"] == "completed" and gw.tasks["t1"]["summary"] == "Report (monthly)"
    actions = [c["body"]["action"] for c in gw.calls]
    assert actions[-5:] == ["claim_task", "start_task", "heartbeat", "complete_task", "heartbeat"]
    assert gw.calls[-1]["body"]["log_run"] is False    # complete_task already logged the run
    assert client.in_task is False

    monkeypatch.setitem(worker.RUNNERS, "shopify_reporter", lambda text: (_ for _ in ()).throw(EnvironmentError("SHOPIFY_ACCESS_TOKEN missing")))
    gw.tasks["t2"] = {"id": "t2", "assigned_to_agent": "shopify_reporter", "status": "pending", "title": "Weekly report", "instructions": "Weekly report", "context": {}}
    w.poll_once()
    assert gw.tasks["t2"]["status"] == "failed" and "Setup needed" in gw.tasks["t2"]["error"]
    assert w.done == 1 and w.failed == 1


def test_roster_is_well_formed():
    from agent_os.roster import ROSTER, SUPERVISORS, CLASS_KEYS
    from agent_os.runners import RUNNERS
    keys = [a["agent_key"] for a in ROSTER]
    assert len(keys) == len(set(keys))
    for a in ROSTER:
        assert re.fullmatch(r"[a-z0-9_]{2,60}", a["agent_key"]), a["agent_key"]
        assert a["role"] in ("worker", "venture", "supervisor", "chief")
        assert a["reports_to"] in SUPERVISORS, a["agent_key"]
        assert a["notes"] and a["display_name"] and a["capabilities"]
        if a.get("board", {}).get("runner"):
            assert a["agent_key"] in RUNNERS, f"{a['agent_key']} says runner but has no runner"
    assert set(RUNNERS) <= set(keys)
    assert set(CLASS_KEYS.values()) <= set(keys)


def test_slug_for_maps_agent_classes():
    from agent_os import client
    assert client.slug_for("ContentResearchAgent") == "history_researcher"
    assert client.slug_for("ShopifyReportingAgent") == "shopify_reporter"
    assert client.slug_for("BrandNewThingAgent") == "brand_new_thing"


def test_board_page_builds_and_parses():
    from agent_os.edge import publish_board
    html = publish_board.page()
    assert html.startswith("<!doctype html>") and html.endswith("</html>") and "<title>JoeMoyo Agent OS</title>" in html
    src = open(os.path.join(ROOT, "agent_os", "board.html"), encoding="utf-8").read()
    js = src[src.index("<script>") + 8: src.rindex("</script>")]
    try:
        subprocess.run(["node", "--check", "-"], input=js.encode(), check=True, capture_output=True)
    except FileNotFoundError:
        pytest.skip("node not installed")
    gateway = open(os.path.join(ROOT, "agent_os", "edge", "agent-os", "index.ts"), encoding="utf-8").read()
    for action in ("dashboard", "register_agent", "issue_agent_key", "heartbeat", "whoami", "pull_tasks", "complete_task", "set_agent_status", "decide_approval"):
        assert f'action==="{action}"' in gateway
