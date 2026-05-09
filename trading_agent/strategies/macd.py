from __future__ import annotations
import pandas as pd
from trading_agent.strategies.base import BaseStrategy, Signal, StrategyResult
import config


class MACDStrategy(BaseStrategy):
    DEFAULT_PARAMS = dict(
        fast_period=config.MACD_FAST,
        slow_period=config.MACD_SLOW,
        signal_period=config.MACD_SIGNAL,
        min_votes=1,
    )

    def __init__(self, params=None):
        super().__init__("macd", {**self.DEFAULT_PARAMS, **(params or {})})

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        df    = self._validate_ohlcv(data)
        p     = self.params
        close = df["Close"]

        fast_ema   = self._ema(close, p["fast_period"])
        slow_ema   = self._ema(close, p["slow_period"])
        macd_line  = fast_ema - slow_ema
        signal_line = self._ema(macd_line, p["signal_period"])
        histogram  = macd_line - signal_line

        cross_signal = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        cross_signal[macd_line > signal_line] = Signal.BUY
        cross_signal[macd_line < signal_line] = Signal.SELL

        hist_signal = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        hist_signal[histogram > 0] = Signal.BUY
        hist_signal[histogram < 0] = Signal.SELL

        vote_sum = cross_signal + hist_signal
        raw      = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        raw[vote_sum >= p["min_votes"]]  = Signal.BUY
        raw[vote_sum <= -p["min_votes"]] = Signal.SELL

        strength  = histogram.abs() / histogram.abs().rolling(20, min_periods=1).max().replace(0, 1)
        pos_sizes = raw.abs() * strength.clip(0.2, 1.0).fillna(0.5)

        return StrategyResult(
            signals=raw, position_sizes=pos_sizes,
            indicators={"macd": macd_line, "signal": signal_line, "histogram": histogram},
        )
