from __future__ import annotations
import numpy as np
import pandas as pd
from trading_agent.strategies.base import BaseStrategy, Signal, StrategyResult
import config


class MomentumStrategy(BaseStrategy):
    DEFAULT_PARAMS = dict(
        fast_ema=config.MOMENTUM_FAST_EMA,
        slow_ema=config.MOMENTUM_SLOW_EMA,
        mom_window=config.MOMENTUM_LOOKBACK,
        vol_window=20,
        min_votes=2,
    )

    def __init__(self, params=None):
        super().__init__("momentum", {**self.DEFAULT_PARAMS, **(params or {})})

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        df    = self._validate_ohlcv(data)
        p     = self.params
        close = df["Close"]
        vol   = df["Volume"]

        fast_ema   = self._ema(close, p["fast_ema"])
        slow_ema   = self._ema(close, p["slow_ema"])
        ema_signal = pd.Series(0, index=df.index, dtype=int)
        ema_signal[fast_ema > slow_ema] =  Signal.BUY
        ema_signal[fast_ema < slow_ema] =  Signal.SELL

        roc        = close.pct_change(p["mom_window"])
        mom_signal = pd.Series(0, index=df.index, dtype=int)
        mom_signal[roc > 0] =  Signal.BUY
        mom_signal[roc < 0] =  Signal.SELL

        vol_confirm = vol > self._sma(vol, p["vol_window"])
        vote_sum    = ema_signal + mom_signal
        raw         = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        raw[(vote_sum >= p["min_votes"]) & vol_confirm] = Signal.BUY
        raw[(vote_sum <= -p["min_votes"]) & vol_confirm] = Signal.SELL

        abs_roc     = roc.abs().fillna(0.0)
        roll_max    = abs_roc.rolling(p["mom_window"] * 2, min_periods=1).max()
        norm        = (abs_roc / roll_max.replace(0, np.nan)).fillna(0.5)
        pos_sizes   = raw.abs() * norm.clip(0.2, 1.0)

        return StrategyResult(
            signals=raw, position_sizes=pos_sizes,
            indicators={"fast_ema": fast_ema, "slow_ema": slow_ema, "roc": roc},
        )
