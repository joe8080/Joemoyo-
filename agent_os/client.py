"""
What an agent calls to show up on the board — a thin client for the Agent OS
gateway (the `agent-os` Supabase edge function).

    from agent_os import client as agent_os

    hb = agent_os.report("swing_trader", "running", task="Cycle over 10 symbols")
    if hb and hb["paused"]:            # Joe pressed Pause on the board
        return
    agent_os.report("swing_trader", "done", result="1 buy, 0 sells",
                    metrics={"equity": 101_240.5}, run_type="swing_cycle")

    with agent_os.task("trading_coach", "Daily close"):
        ...                            # running → done / error, automatic

Configuration (environment):
    AGENT_OS_URL    the gateway URL (…/functions/v1/agent-os, aliased as /mj)
    AGENT_OS_KEYS   JSON {agent_key: "agent_…"} — one key per agent this host runs
    AGENT_OS_KEY    a single key, when this process is one agent
    AGENT_OS_DISABLED=1 switches reporting off

Every call is best-effort: no key, no URL, or a network error prints one line
and returns None. Reporting must never break an agent.
"""

from __future__ import annotations

import json
import os
import re
import socket
import time
from contextlib import contextmanager

import requests

from agent_os.roster import CLASS_KEYS

_DISABLED = os.environ.get("AGENT_OS_DISABLED", "").lower() in ("1", "true", "yes")
_TIMEOUT = 8
_warned: set[str] = set()
# Set by the worker while it executes a task, so the finishing heartbeat does
# not log a second run row (complete_task already logs one).
in_task = False


def gateway() -> str:
    return (os.environ.get("AGENT_OS_URL") or "").rstrip("/")


def keys() -> dict[str, str]:
    raw = os.environ.get("AGENT_OS_KEYS") or ""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except ValueError:
        _warn("AGENT_OS_KEYS is not valid JSON — expected {\"agent_key\": \"agent_…\"}")
        return {}


def key_for(agent_key: str) -> str:
    return keys().get(agent_key) or os.environ.get("AGENT_OS_KEY") or ""


def source() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return "github-actions"
    if os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID"):
        return "railway"
    return socket.gethostname()[:40]


def slug_for(class_name: str) -> str:
    """BaseAgent subclass → roster agent_key."""
    if class_name in CLASS_KEYS:
        return CLASS_KEYS[class_name]
    name = re.sub(r"Agent$", "", class_name)
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _warn(msg: str) -> None:
    if msg not in _warned:
        _warned.add(msg)
        print(f"[agent-os] {msg}")


def call(action: str, agent_key: str, **fields) -> dict | None:
    """POST one action to the gateway as `agent_key`. None on any failure."""
    if _DISABLED:
        return None
    url, key = gateway(), key_for(agent_key)
    if not url:
        _warn("AGENT_OS_URL not set — not reporting to the board")
        return None
    if not key:
        _warn(f"no key for '{agent_key}' (AGENT_OS_KEYS / AGENT_OS_KEY) — not reporting")
        return None
    body = {"action": action, **{k: v for k, v in fields.items() if v is not None}}
    try:
        r = requests.post(url, json=body, headers={"content-type": "application/json", "x-agent-key": key},
                          timeout=_TIMEOUT)
    except Exception as e:  # noqa: BLE001 — reporting must never break an agent
        _warn(f"could not reach the board at {url}: {e}")
        return None
    if r.status_code >= 300:
        try:
            detail = r.json().get("error")
        except ValueError:
            detail = r.text[:120]
        _warn(f"{action} as {agent_key} → {r.status_code} {detail}")
        return None
    try:
        return r.json()
    except ValueError:
        return None


def report(agent_key: str, status: str | None = None, *, task: str | None = None,
           result: str | None = None, note: str | None = None, metrics: dict | None = None,
           run_type: str | None = None, log_run: bool | None = None) -> dict | None:
    """Say what the agent is doing. Returns the gateway reply (has `paused`)."""
    if log_run is None and in_task:
        log_run = False
    return call("heartbeat", agent_key, status=status, task=task, result=result, note=note,
                metrics=metrics, run_type=run_type, log_run=log_run, source_system=source())


def is_paused(agent_key: str) -> bool:
    """True when the board has this agent paused. Fail-open."""
    me = call("whoami", agent_key)
    return bool(me and me.get("paused"))


def log(agent_key: str, subject: str, severity: str = "info", event_type: str = "agent_event",
        payload: dict | None = None) -> dict | None:
    """Drop a line into the OS event feed (severity: info | amber | red)."""
    return call("emit_event", agent_key, subject=subject, severity=severity, event_type=event_type,
                payload=payload or {}, source_system=source())


# ---- task protocol (used by the worker) ----------------------------------- #

def pull_tasks(agent_key: str, limit: int = 10) -> list[dict]:
    data = call("pull_tasks", agent_key, limit=limit)
    return list(data.get("tasks") or []) if data else []


def claim_task(agent_key: str, task_id: str, attempt: int = 1) -> dict | None:
    data = call("claim_task", agent_key, task_id=task_id, attempt_count=attempt)
    return data.get("task") if data else None


def start_task(agent_key: str, task_id: str) -> dict | None:
    data = call("start_task", agent_key, task_id=task_id)
    return data.get("task") if data else None


def complete_task(agent_key: str, task_id: str, summary: str, result: dict | None = None) -> dict | None:
    data = call("complete_task", agent_key, task_id=task_id, summary=summary, result=result or {})
    return data.get("task") if data else None


def fail_task(agent_key: str, task_id: str, error: str) -> dict | None:
    data = call("fail_task", agent_key, task_id=task_id, error=error)
    return data.get("task") if data else None


@contextmanager
def task(agent_key: str, description: str, result: str | None = None, run_type: str | None = None):
    """running → done (or error, re-raised)."""
    report(agent_key, "running", task=description)
    t0 = time.time()
    try:
        yield
    except Exception as e:
        report(agent_key, "error", note=f"{type(e).__name__}: {e}", run_type=run_type)
        raise
    else:
        report(agent_key, "done", result=result or f"{description} — finished in {time.time() - t0:.0f}s",
               run_type=run_type)
