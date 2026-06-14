"""
Durable memory for the paper bot — thin Supabase REST client (PostgREST).

Persists trades, round trips, equity snapshots, coach notes, tendencies, pattern
performance, and manual journal entries to the `public.bot_*` tables so the
history survives container/Streamlit restarts and the coach can build on the
past. Uses the service-role key (server-side only).

Design rule: this is best-effort logging that must NEVER break trading. Every
call is wrapped — if credentials are missing or the network fails, it logs a
warning and returns a falsy value instead of raising. Configure with env vars
SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_KEY).
"""

import os

import requests

_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or ""
_TIMEOUT = 10


def enabled() -> bool:
    return bool(_URL and _KEY)


def _headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": _KEY,
        "Authorization": f"Bearer {_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _post(table: str, rows, on_conflict: str | None = None) -> bool:
    """Insert/upsert rows. Returns True on success, False otherwise (never raises)."""
    if not enabled():
        return False
    try:
        params = {}
        prefer = "return=minimal"
        if on_conflict:
            params["on_conflict"] = on_conflict
            prefer = "return=minimal,resolution=merge-duplicates"
        r = requests.post(
            f"{_URL}/rest/v1/{table}",
            params=params, headers=_headers({"Prefer": prefer}),
            json=rows if isinstance(rows, list) else [rows],
            timeout=_TIMEOUT,
        )
        if r.status_code >= 300:
            print(f"[supabase] {table} write failed {r.status_code}: {r.text[:160]}")
            return False
        return True
    except Exception as e:  # noqa: BLE001 — logging must never break trading
        print(f"[supabase] {table} write error: {e}")
        return False


def _get(table: str, query: str = "select=*") -> list:
    if not enabled():
        return []
    try:
        r = requests.get(f"{_URL}/rest/v1/{table}?{query}",
                         headers=_headers(), timeout=_TIMEOUT)
        return r.json() if r.status_code < 300 else []
    except Exception as e:  # noqa: BLE001
        print(f"[supabase] {table} read error: {e}")
        return []


# ---- write paths ---------------------------------------------------------- #

def log_trade(row: dict) -> bool:
    return _post("bot_trades", {k: row.get(k) for k in
                 ("symbol", "action", "qty", "price", "est_cost", "entry_price",
                  "pnl_pct", "exit_reason", "mode", "reason", "status")})


def snapshot_equity(row: dict) -> bool:
    return _post("bot_equity_snapshots", row, on_conflict="snapshot_date")


def save_round_trips(trips: list[dict]) -> bool:
    if not trips:
        return False
    cols = ("symbol", "qty", "entry_date", "entry_price", "exit_date",
            "exit_price", "pnl", "pnl_pct", "hold_days", "exit_reason")
    rows = [{k: t.get(k) for k in cols} for t in trips]
    return _post("bot_round_trips", rows,
                 on_conflict="symbol,entry_date,exit_date,entry_price,exit_price")


def save_coach_note(note: str, stats: dict) -> bool:
    return _post("bot_coach_notes", {"note": note, "stats": stats})


def save_tendencies(tendencies: list[str]) -> bool:
    if not tendencies:
        return False
    return _post("bot_tendencies", [{"tendency": t} for t in tendencies])


def save_pattern_performance(stats: dict) -> bool:
    rows = []
    for bucket_type in ("by_symbol", "by_exit_reason"):
        for key, v in (stats.get(bucket_type) or {}).items():
            rows.append({"bucket_type": bucket_type.replace("by_", ""),
                         "bucket_key": key or "unknown", "trades": v["trades"],
                         "wins": v["wins"], "pnl": v["pnl"]})
    return _post("bot_pattern_performance", rows,
                 on_conflict="bucket_type,bucket_key") if rows else False


def save_manual_entry(entry: dict) -> bool:
    return _post("bot_manual_journal", entry)


# ---- read paths ----------------------------------------------------------- #

def get_round_trips() -> list:
    return _get("bot_round_trips", "select=*&order=exit_date.asc")


def get_coach_notes(limit: int = 30) -> list:
    return _get("bot_coach_notes", f"select=*&order=created_at.desc&limit={limit}")


def get_tendencies(limit: int = 20) -> list:
    return _get("bot_tendencies", f"select=*&order=observed_at.desc&limit={limit}")


def get_equity_snapshots() -> list:
    return _get("bot_equity_snapshots", "select=*&order=snapshot_date.asc")


def get_manual_entries() -> list:
    return _get("bot_manual_journal", "select=*&order=created_at.desc")
