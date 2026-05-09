from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Optional
import numpy as np
import pandas as pd


class Signal(IntEnum):
    SELL = -1
    HOLD = 0
    BUY  = 1


@dataclass
class StrategyResult:
    signals:        pd.Series
    position_sizes: pd.Series
    indicators:     Dict[str, pd.Series] = field(default_factory=dict)
    metadata:       Dict = field(default_factory=dict)

    def __post_init__(self):
        self.signals        = self.signals.fillna(Signal.HOLD)
        self.position_sizes = self.position_sizes.clip(0.0, 1.0).fillna(0.0)


class BaseStrategy(ABC):
    def __init__(self, name: str, params: Optional[Dict] = None):
        self.name   = name
        self.params = params or {}
        self.logger = logging.getLogger(f"strategy.{name}")
        self._fitted = False

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> StrategyResult: ...

    def fit(self, data: pd.DataFrame) -> "BaseStrategy":
        self._fitted = True
        return self

    def get_params(self) -> Dict:
        return dict(self.params)

    def set_params(self, **params) -> "BaseStrategy":
        self.params.update(params)
        return self

    @staticmethod
    def _validate_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing  = required - set(data.columns)
        if missing:
            raise ValueError(f"Data missing columns: {missing}")
        return data.copy()

    @staticmethod
    def _ema(s: pd.Series, span: int) -> pd.Series:
        return s.ewm(span=span, adjust=False).mean()

    @staticmethod
    def _sma(s: pd.Series, window: int) -> pd.Series:
        return s.rolling(window=window).mean()

    @staticmethod
    def _rsi(s: pd.Series, period: int = 14) -> pd.Series:
        delta    = s.diff()
        gain     = delta.clip(lower=0.0)
        loss     = (-delta).clip(lower=0.0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs       = avg_gain / avg_loss.replace(0.0, np.nan)
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low  - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        return tr.ewm(com=period - 1, min_periods=period).mean()

    @staticmethod
    def _bollinger_bands(s: pd.Series, window: int = 20, num_std: float = 2.0):
        mid   = s.rolling(window).mean()
        std   = s.rolling(window).std()
        return mid + num_std * std, mid, mid - num_std * std

    @staticmethod
    def _zscore(s: pd.Series, window: int = 20) -> pd.Series:
        m = s.rolling(window).mean()
        d = s.rolling(window).std()
        return (s - m) / d.replace(0.0, np.nan)

    @staticmethod
    def _constant_position(signals: pd.Series, size: float = 1.0) -> pd.Series:
        return signals.abs().clip(0, 1) * size

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, params={self.params})"
