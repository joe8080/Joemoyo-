from __future__ import annotations
import pandas as pd
from trading_agent.strategies.base import BaseStrategy, Signal, StrategyResult
import config


class MeanReversionStrategy(BaseStrategy):
    DEFAULT_PARAMS = dict(
        rsi_period=config.RSI_PERIOD,
        rsi_oversold=config.RSI_OVERSOLD,
        rsi_overbought=config.RSI_OVERBOUGHT,
        bb_period=config.BB_PERIOD,
        bb_std=config.BB_STD,
        min_votes=1,
    )

    def __init__(self, params=None):
        super().__init__("mean_reversion", {**self.DEFAULT_PARAMS, **(params or {})})

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        df    = self._validate_ohlcv(data)
        p     = self.params
        close = df["Close"]

        rsi        = self._rsi(close, p["rsi_period"])
        rsi_signal = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        rsi_signal[rsi < p["rsi_oversold"]]  = Signal.BUY
        rsi_signal[rsi > p["rsi_overbought"]] = Signal.SELL

        upper, mid, lower = self._bollinger_bands(close, p["bb_period"], p["bb_std"])
        bb_signal = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        bb_signal[close < lower] = Signal.BUY
        bb_signal[close > upper] = Signal.SELL

        vote_sum = rsi_signal + bb_signal
        raw      = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        raw[vote_sum >= p["min_votes"]]  = Signal.BUY
        raw[vote_sum <= -p["min_votes"]] = Signal.SELL

        zscore    = self._zscore(close, p["bb_period"])
        pos_sizes = raw.abs() * (zscore.abs().clip(0.5, 3.0) / 3.0).fillna(0.5)

        return StrategyResult(
            signals=raw, position_sizes=pos_sizes,
            indicators={"rsi": rsi, "bb_upper": upper, "bb_mid": mid, "bb_lower": lower},
        )
