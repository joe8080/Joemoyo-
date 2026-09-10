"""
The OS Runner: runs the repo's Python agents as Agent OS workers.

    python main.py os worker

Every cycle it heartbeats each agent it holds a key for, pulls that agent's
tasks from the OS (`pull_tasks`), and executes them one at a time with the
matching runner (runners.py): claim → start → run → complete / fail. A task's
`context.input` (or its instructions) is the runner's input — so "Run" on the
board, or the Chief delegating work, both end up here.

Keys: AGENT_OS_KEYS='{"agent_os_runner": "agent_…", "shopify_reporter": "agent_…", …}'
Only agents with a key are served; the rest are skipped with one warning.
"""

from __future__ import annotations

import json
import time
import traceback

from agent_os import client
from agent_os.roster import ROSTER
from agent_os.runners import RUNNERS, summarise

RUNNER_KEY = "agent_os_runner"


class Worker:
    def __init__(self, poll_seconds: int = 20, heartbeat_seconds: int = 60):
        self.poll_seconds = poll_seconds
        self.heartbeat_seconds = heartbeat_seconds
        self.agents = [a["agent_key"] for a in ROSTER if a["agent_key"] in RUNNERS and client.key_for(a["agent_key"])]
        self.skipped = [a["agent_key"] for a in ROSTER if a["agent_key"] in RUNNERS and not client.key_for(a["agent_key"])]
        self._last_heartbeat = 0.0
        self.done = 0
        self.failed = 0

    # ---- one task ----------------------------------------------------------
    def run_task(self, agent_key: str, task: dict) -> bool:
        tid = task["id"]
        text = ""
        ctx = task.get("context") or {}
        if isinstance(ctx, dict) and ctx.get("input") is not None:
            text = str(ctx.get("input"))
        elif task.get("instructions"):
            text = str(task["instructions"])
        label = task.get("title") or agent_key
        if task.get("status") == "pending" and not client.claim_task(agent_key, tid, int(task.get("attempt_count") or 0) + 1):
            return False
        if task.get("status") in ("pending", "claimed") and not client.start_task(agent_key, tid):
            return False
        client.report(agent_key, "running", task=label, log_run=False)
        client.in_task = True
        try:
            out = RUNNERS[agent_key](text)
            summary = summarise(out)
            client.complete_task(agent_key, tid, summary, {"input": text, "summary": summary})
            client.report(agent_key, "done", result=summary, log_run=False)
            self.done += 1
            print(f"[runner] {agent_key} ✓ {label}: {summary[:100]}")
            return True
        except EnvironmentError as e:
            msg = f"Setup needed: {e}"
        except Exception as e:  # noqa: BLE001 — one bad task must not stop the runner
            msg = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        finally:
            client.in_task = False
        client.fail_task(agent_key, tid, msg)
        client.report(agent_key, "error", note=msg, log_run=False)
        self.failed += 1
        print(f"[runner] {agent_key} ✗ {label}: {msg}")
        return False

    # ---- one cycle ---------------------------------------------------------
    def poll_once(self) -> int:
        ran = 0
        for agent_key in self.agents:
            for task in client.pull_tasks(agent_key):
                if task.get("status") in ("pending", "claimed"):
                    self.run_task(agent_key, task)
                    ran += 1
        return ran

    def heartbeat_all(self) -> None:
        client.report(RUNNER_KEY, "online", task=f"Serving {len(self.agents)} agents",
                      metrics={"agents": len(self.agents), "tasks_done": self.done, "tasks_failed": self.failed},
                      log_run=False)
        for agent_key in self.agents:
            client.report(agent_key, "idle", log_run=False)
        self._last_heartbeat = time.time()

    def run_forever(self) -> None:
        print(f"[runner] serving: {', '.join(self.agents) or '(none — no keys found)'}")
        if self.skipped:
            print(f"[runner] no key for: {', '.join(self.skipped)} — add them to AGENT_OS_KEYS")
        if not client.gateway():
            print("[runner] AGENT_OS_URL is not set; nothing to do.")
            return
        try:
            while True:
                if time.time() - self._last_heartbeat >= self.heartbeat_seconds:
                    self.heartbeat_all()
                self.poll_once()
                time.sleep(self.poll_seconds)
        except KeyboardInterrupt:
            print("\n[runner] stopped.")


def describe_keys() -> str:
    return json.dumps({a["agent_key"]: "agent_…" for a in ROSTER}, indent=1)
