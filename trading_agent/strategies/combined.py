from __future__ import annotations
from typing import Dict, Optional
import pandas as pd
from trading_agent.strategies.base import BaseStrategy, Signal, StrategyResult
from trading_agent.strategies.momentum import MomentumStrategy
from trading_agent.strategies.mean_reversion import MeanReversionStrategy
from trading_agent.strategies.macd import MACDStrategy


class CombinedStrategy(BaseStrategy):
    DEFAULT_WEIGHTS = {"momentum": 1.0, "mean_reversion": 1.0, "macd": 1.0}

    def __init__(self, weights: Optional[Dict[str, float]] = None, params=None):
        super().__init__("combined", params or {})
        self.weights = {**self.DEFAULT_WEIGHTS, **(weights or {})}
        self._strategies = {
            "momentum":      MomentumStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "macd":          MACDStrategy(),
        }

    def update_weights(self, weights: Dict[str, float]):
        self.weights.update(weights)

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        df        = self._validate_ohlcv(data)
        vote_sum  = pd.Series(0.0, index=df.index)
        total_w   = sum(self.weights.values()) or 1.0

        for name, strat in self._strategies.items():
            w      = self.weights.get(name, 1.0)
            result = strat.generate_signals(df)
            vote_sum += result.signals.astype(float) * w

        raw = pd.Series(Signal.HOLD, index=df.index, dtype=int)
        raw[vote_sum > 0]  = Signal.BUY
        raw[vote_sum < 0]  = Signal.SELL

        pos_sizes = raw.abs() * (vote_sum.abs() / total_w).clip(0.1, 1.0)
        return StrategyResult(signals=raw, position_sizes=pos_sizes,
                              metadata={"weights": self.weights})
