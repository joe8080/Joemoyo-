"""
Round-trip trade ledger and performance stats — pure functions, no I/O.

Pairs filled BUY and SELL orders per symbol (FIFO) into completed round trips
with entry/exit price, P&L, hold time, and the exit reason, then rolls them up
into the kind of stats a trading journal shows: win rate, P&L by symbol, by
exit reason, and a calendar of daily P&L. Built so the dashboard and the Claude
coach read the same numbers.

Feed it Alpaca filled orders (`AlpacaClient.simplify_orders(get_orders("all"))`)
and, optionally, the bot's `trades.csv` rows so each exit can be tagged with the
reason the bot recorded (stop / take_profit / trailing / signal / eod_flatten).
"""

from collections import deque
from datetime import datetime


def _to_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_ledger(orders: list[dict], exit_reasons: dict | None = None) -> list[dict]:
    """
    Pair filled buys/sells per symbol (FIFO) into closed round trips.

    `orders` are simplified Alpaca orders (need symbol, side, filled_qty,
    filled_avg_price, submitted_at). `exit_reasons` optionally maps
    "SYMBOL|YYYY-MM-DD" -> reason string (from trades.csv) to tag each exit.

    Returns a list of round trips sorted by exit time, each with: symbol, qty,
    entry_date, entry_price, exit_date, exit_price, pnl, pnl_pct, hold_days,
    exit_reason.
    """
    exit_reasons = exit_reasons or {}
    fills = sorted(
        (o for o in orders
         if o.get("filled_qty") and float(o["filled_qty"]) > 0
         and o.get("filled_avg_price") and o.get("submitted_at")),
        key=lambda o: o["submitted_at"],
    )
    lots: dict[str, deque] = {}
    trips: list[dict] = []

    for o in fills:
        sym = o["symbol"]
        qty = float(o["filled_qty"])
        price = float(o["filled_avg_price"])
        ts = o["submitted_at"]
        book = lots.setdefault(sym, deque())

        if o.get("side") == "buy":
            book.append({"qty": qty, "price": price, "ts": ts})
            continue

        # SELL: match against open buy lots FIFO.
        remaining = qty
        while remaining > 1e-9 and book:
            lot = book[0]
            matched = min(remaining, lot["qty"])
            entry_dt, exit_dt = _to_dt(lot["ts"]), _to_dt(ts)
            hold_days = (exit_dt - entry_dt).days if entry_dt and exit_dt else None
            pnl = matched * (price - lot["price"])
            trips.append({
                "symbol": sym,
                "qty": round(matched, 4),
                "entry_date": lot["ts"][:10],
                "entry_price": round(lot["price"], 2),
                "exit_date": ts[:10],
                "exit_price": round(price, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round((price - lot["price"]) / lot["price"] * 100, 2),
                "hold_days": hold_days,
                "exit_reason": exit_reasons.get(f"{sym}|{ts[:10]}", ""),
            })
            lot["qty"] -= matched
            remaining -= matched
            if lot["qty"] <= 1e-9:
                book.popleft()

    trips.sort(key=lambda t: t["exit_date"])
    return trips


def ledger_stats(trips: list[dict]) -> dict:
    """Roll a ledger up into journal-style performance stats."""
    if not trips:
        return {"num_trades": 0}

    wins = [t for t in trips if t["pnl"] > 0]
    losses = [t for t in trips if t["pnl"] < 0]
    total_pnl = sum(t["pnl"] for t in trips)
    gross_win = sum(t["pnl"] for t in wins)
    gross_loss = -sum(t["pnl"] for t in losses)

    def _bucket(key: str) -> dict:
        out: dict[str, dict] = {}
        for t in trips:
            k = t.get(key) or "unknown"
            b = out.setdefault(k, {"trades": 0, "wins": 0, "pnl": 0.0})
            b["trades"] += 1
            b["wins"] += 1 if t["pnl"] > 0 else 0
            b["pnl"] = round(b["pnl"] + t["pnl"], 2)
        return out

    daily: dict[str, float] = {}
    for t in trips:
        daily[t["exit_date"]] = round(daily.get(t["exit_date"], 0.0) + t["pnl"], 2)

    return {
        "num_trades": len(trips),
        "win_rate_pct": round(len(wins) / len(trips) * 100, 1),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(gross_win / len(wins), 2) if wins else 0.0,
        "avg_loss": round(-gross_loss / len(losses), 2) if losses else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else None,
        "best_trade": round(max(t["pnl"] for t in trips), 2),
        "worst_trade": round(min(t["pnl"] for t in trips), 2),
        "avg_hold_days": round(
            sum(t["hold_days"] for t in trips if t["hold_days"] is not None)
            / max(1, sum(1 for t in trips if t["hold_days"] is not None)), 1),
        "by_symbol": _bucket("symbol"),
        "by_exit_reason": _bucket("exit_reason"),
        "daily_pnl": daily,
    }


def exit_reasons_from_csv(rows: list[dict]) -> dict:
    """Map 'SYMBOL|YYYY-MM-DD' -> exit reason from trades.csv close rows."""
    out: dict[str, str] = {}
    for r in rows:
        if r.get("action") == "close" and r.get("exit_reason"):
            out[f"{r['symbol']}|{(r.get('timestamp') or '')[:10]}"] = r["exit_reason"]
    return out
