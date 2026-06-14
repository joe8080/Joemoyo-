"""
Trading coach: a Claude layer that reviews the bot's own round-trip ledger and
writes a plain-English performance note plus a list of recurring "tendencies"
(the SMB-style idea of surfacing patterns you keep repeating).

It does NOT make trading decisions — it analyses what already happened, the same
way a desk coach reviews the day's tape. Deterministic stats come from
tools.journal; Claude only narrates and pattern-spots over those stats.
"""

import json
import os
from datetime import datetime

from config.settings import settings
from tools.journal import build_ledger, ledger_stats, exit_reasons_from_csv


def _read_trades_csv(path: str) -> list[dict]:
    import csv
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_coach_report(orders: list[dict], reports_dir: str) -> dict:
    """
    Build the ledger + stats, ask Claude for tendencies and a coach note, and
    write coach_<date>.md and tendencies.json into reports_dir. Returns a dict
    with stats, the note text, and the tendencies list. Falls back to stats-only
    (no narrative) if the Anthropic call fails — the numbers always render.
    """
    os.makedirs(reports_dir, exist_ok=True)
    csv_rows = _read_trades_csv(os.path.join(reports_dir, "trades.csv"))
    trips = build_ledger(orders, exit_reasons_from_csv(csv_rows))
    stats = ledger_stats(trips)

    note, tendencies = _ask_claude(trips, stats)

    today = datetime.now().strftime("%Y%m%d")
    with open(os.path.join(reports_dir, f"coach_{today}.md"), "w", encoding="utf-8") as f:
        f.write(f"# Coach note — {datetime.now():%Y-%m-%d %H:%M}\n\n{note}\n")
    with open(os.path.join(reports_dir, "tendencies.json"), "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now().isoformat(timespec="seconds"),
                   "tendencies": tendencies}, f, indent=2)
    with open(os.path.join(reports_dir, "ledger.json"), "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now().isoformat(timespec="seconds"),
                   "stats": stats, "trades": trips}, f, indent=2)

    return {"stats": stats, "note": note, "tendencies": tendencies, "trades": trips}


def _ask_claude(trips: list[dict], stats: dict) -> tuple[str, list[str]]:
    """Return (coach_note, tendencies). Stats-only fallback on any failure."""
    if stats.get("num_trades", 0) == 0:
        return ("No closed round trips yet — the coach note appears once the "
                "bot has completed some trades.", [])
    if not settings.anthropic_api_key or settings.anthropic_api_key.startswith("unused"):
        return (_fallback_note(stats), [])

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        payload = {
            "stats": stats,
            # cap the trade list so the prompt stays small
            "recent_trades": trips[-60:],
        }
        system = (
            "You are a trading performance coach reviewing an AUTOMATED bot's "
            "completed round-trip trades (a deterministic SMA trend-follower "
            "with a trailing stop). You are given precomputed stats and recent "
            "trades. Do NOT predict markets or suggest specific trades. Instead: "
            "(1) write a concise, plain-English performance note (5-8 sentences) "
            "on what's working and what isn't — win rate, profit factor, which "
            "symbols and which exit reasons drive P&L, hold times; (2) list 2-5 "
            "recurring 'tendencies' (patterns worth watching, e.g. 'trailing "
            "stops exit NVDA early in choppy weeks'). Respond ONLY as JSON: "
            '{"note": "...", "tendencies": ["...", "..."]}.'
        )
        resp = client.messages.create(
            model=settings.model, max_tokens=1200, system=system,
            messages=[{"role": "user", "content": json.dumps(payload, default=str)}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        data = json.loads(text[text.find("{"): text.rfind("}") + 1])
        return data.get("note", _fallback_note(stats)), data.get("tendencies", [])
    except Exception:
        return _fallback_note(stats), []


def _fallback_note(stats: dict) -> str:
    """Deterministic summary used when Claude isn't available."""
    by_sym = stats.get("by_symbol", {})
    best = max(by_sym.items(), key=lambda kv: kv[1]["pnl"], default=(None, None))
    worst = min(by_sym.items(), key=lambda kv: kv[1]["pnl"], default=(None, None))
    parts = [
        f"{stats['num_trades']} closed trades, {stats['win_rate_pct']}% win rate, "
        f"total P&L ${stats['total_pnl']:,.2f}.",
        f"Profit factor {stats.get('profit_factor')}, avg win ${stats['avg_win']}, "
        f"avg loss ${stats['avg_loss']}, avg hold {stats['avg_hold_days']} days.",
    ]
    if best[0]:
        parts.append(f"Best symbol: {best[0]} (${best[1]['pnl']:,.2f}); "
                     f"weakest: {worst[0]} (${worst[1]['pnl']:,.2f}).")
    return " ".join(parts)
