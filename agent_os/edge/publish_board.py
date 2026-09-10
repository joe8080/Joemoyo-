#!/usr/bin/env python3
"""
Publish agent_os/board.html to the gateway.

    python main.py os publish-board        (or: python agent_os/edge/publish_board.py)

The gateway serves the board from agent_os_config (config_key "board_html"),
so updating the page never needs a function redeploy. Needs SUPABASE_URL and
SUPABASE_SERVICE_KEY in the environment (server-side key — your machine only).
"""

import os
import sys
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(os.path.dirname(HERE), "board.html")
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">')


def page() -> str:
    with open(BOARD, encoding="utf-8") as f:
        return HEAD + f.read() + "</html>"


def publish(url: str, key: str) -> None:
    html = page()
    r = requests.post(
        f"{url.rstrip('/')}/rest/v1/agent_os_config",
        params={"on_conflict": "config_key"},
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Prefer": "return=minimal,resolution=merge-duplicates"},
        json=[{"config_key": "board_html",
               "config_value": {"html": html, "bytes": len(html), "published_by": "publish_board.py"},
               "updated_at": datetime.now(timezone.utc).isoformat()}],
        timeout=30,
    )
    if r.status_code >= 300:
        sys.exit(f"publish failed {r.status_code}: {r.text[:200]}")
    print(f"published board ({len(html):,} bytes) — live within a minute at {url.rstrip('/')}/functions/v1/agent-os")


if __name__ == "__main__":
    u, k = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY", "")
    if not (u and k):
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY first.")
    publish(u, k)
