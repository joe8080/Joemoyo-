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
