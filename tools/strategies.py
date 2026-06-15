"""
Pure trading-strategy functions — no I/O, no API calls, no global state.

Keeping signal logic here (separate from the Alpaca client and the agents)
makes it trivially unit-testable and easy to swap or extend later
(RSI, breakout, multi-factor, etc.). Everything is deterministic.
"""

from math import floor


def sma(values: list[float], n: int) -> float | None:
    """Simple moving average of the last n values. None if not enough data."""
    if n <= 0 or len(values) < n:
        return None
    window = values[-n:]
    return sum(window) / n


def sma_crossover_signal(
    bars: list[dict],
    short_window: int = 20,
    long_window: int = 50,
    price_key: str = "close",
) -> str:
    """
    Momentum signal from a short/long SMA crossover.

    Returns:
      "buy"  — short SMA crossed ABOVE long SMA on the latest bar (bullish)
      "sell" — short SMA crossed BELOW long SMA on the latest bar (bearish)
      "hold" — no fresh crossover, or insufficient data

    A "crossover" means the relationship flipped between the previous bar and
    the latest bar, so we only act on the bar where the trend actually changes
    rather than every bar the trend persists.
    """
    if short_window >= long_window:
        raise ValueError("short_window must be smaller than long_window")

    closes = [float(b[price_key]) for b in bars if b.get(price_key) is not None]
    # Need long_window + 1 points to compute the SMA on both the latest and the
    # previous bar.
    if len(closes) < long_window + 1:
        return "hold"

    prev_short = sma(closes[:-1], short_window)
    prev_long = sma(closes[:-1], long_window)
    curr_short = sma(closes, short_window)
    curr_long = sma(closes, long_window)

    if None in (prev_short, prev_long, curr_short, curr_long):
        return "hold"

    crossed_up = prev_short <= prev_long and curr_short > curr_long
    crossed_down = prev_short >= prev_long and curr_short < curr_long

    if crossed_up:
        return "buy"
    if crossed_down:
        return "sell"
    return "hold"


def position_size(
    buying_power: float,
    cash_per_trade: float,
    price: float,
    cash_buffer: float = 0.0,
) -> int:
    """
    Whole-share quantity to buy for one trade, bounded by risk caps.

    - Never spends more than `cash_per_trade` on the trade.
    - Never dips into `cash_buffer` (cash to keep uninvested).
    - Never exceeds available `buying_power`.
    Returns 0 if a trade can't be sized responsibly.
    """
    if price <= 0 or cash_per_trade <= 0:
        return 0
    spendable = min(cash_per_trade, max(0.0, buying_power - cash_buffer))
    if spendable < price:
        return 0
    return floor(spendable / price)


def atr(bars: list[dict], n: int = 14) -> float | None:
    """Average true range of the last n bars. None if not enough data."""
    if len(bars) < n + 1:
        return None
    trs = []
    for prev, curr in zip(bars[-(n + 1):-1], bars[-n:]):
        high, low = float(curr["high"]), float(curr["low"])
        prev_close = float(prev["close"])
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return sum(trs) / n


def volume_confirmed(bars: list[dict], n: int = 20, mult: float = 1.5) -> bool:
    """
    True when the latest bar's volume is at least `mult` times the average of
    the previous n bars. Filters out signals that fire on dead volume — a
    pattern without participation is usually noise.
    """
    vols = [float(b["volume"]) for b in bars if b.get("volume") is not None]
    if len(vols) < n + 1:
        return False
    avg = sum(vols[-(n + 1):-1]) / n
    return avg > 0 and vols[-1] >= mult * avg


def participation_ok(
    bars: list[dict],
    min_avg_volume: float = 2_000_000,
    min_atr: float = 1.0,
    n: int = 20,
) -> bool:
    """
    True when the symbol trades enough shares and has enough daily range to
    be worth trading at all ("is the stock in play?"). Thin, rangeless names
    produce random-looking signals with no follow-through.
    """
    vols = [float(b["volume"]) for b in bars if b.get("volume") is not None]
    if len(vols) < n:
        return False
    if sum(vols[-n:]) / n < min_avg_volume:
        return False
    a = atr(bars)
    return a is not None and a >= min_atr


def risk_exit(
    entry_price: float,
    last_price: float,
    peak_price: float | None = None,
    stop_pct: float = 0.0,
    take_profit_pct: float = 0.0,
    trail_pct: float = 0.0,
) -> str | None:
    """
    Decide whether a long position should be exited on a risk rule, independent
    of the strategy signal. Pure and deterministic.

    Percentages are whole numbers (5 == 5%). A value of 0 disables that rule.

      stop_pct        — exit if price falls this far below the entry price
      take_profit_pct — exit if price rises this far above the entry price
      trail_pct       — exit if price falls this far below the highest price
                        seen since entry (peak_price). Falls back to entry
                        price if no peak is supplied.

    Returns "stop" | "take_profit" | "trailing" | None. Stop-loss is checked
    first (capital protection beats profit-taking).
    """
    if entry_price <= 0 or last_price <= 0:
        return None

    change_pct = (last_price - entry_price) / entry_price * 100

    if stop_pct > 0 and change_pct <= -stop_pct:
        return "stop"
    if take_profit_pct > 0 and change_pct >= take_profit_pct:
        return "take_profit"
    if trail_pct > 0:
        peak = max(peak_price or 0.0, entry_price, last_price)
        if peak > 0 and (last_price - peak) / peak * 100 <= -trail_pct:
            return "trailing"
    return None


# --------------------------------------------------------------------- #
#  Opening-Range Breakout (intraday day-trading) — pure functions       #
# --------------------------------------------------------------------- #

def session_bars(bars: list[dict], date: str, rth_start: str = "13:30", rth_end: str = "20:00") -> list[dict]:
    """
    The regular-trading-hours bars for one session date (UTC `t` timestamps),
    in order. `date` is "YYYY-MM-DD". RTH window defaults to ~9:30-16:00 ET.
    """
    return [b for b in bars
            if b.get("t", "")[:10] == date and rth_start <= b.get("t", "")[11:16] <= rth_end]


def opening_range(day_bars: list[dict], or_bars: int = 6) -> dict | None:
    """
    High, low, and average volume of the first `or_bars` bars of the session
    (e.g. 6 five-minute bars = the first 30 minutes). None if too few bars.
    """
    if len(day_bars) < or_bars:
        return None
    first = day_bars[:or_bars]
    return {
        "high": max(float(b["high"]) for b in first),
        "low": min(float(b["low"]) for b in first),
        "avg_vol": sum(float(b.get("volume", 0) or 0) for b in first) / or_bars,
    }


def orb_signal(day_bars: list[dict], or_bars: int = 6, vol_mult: float = 1.5) -> str:
    """
    "buy" when the latest bar is AFTER the opening range and breaks above the
    opening-range high on volume >= vol_mult x the opening-range average volume;
    otherwise "hold". `day_bars` are this session's bars in order (last = now).

    This is the entry edge that backtested with a real, market-filtered edge —
    the live bot and the backtester both call this so they stay identical.
    """
    if len(day_bars) <= or_bars:
        return "hold"
    rng = opening_range(day_bars, or_bars)
    if not rng or rng["avg_vol"] <= 0:
        return "hold"
    last = day_bars[-1]
    if float(last["high"]) > rng["high"] and float(last.get("volume", 0) or 0) >= vol_mult * rng["avg_vol"]:
        return "buy"
    return "hold"
