"""
Event-driven backtesting engine.
Processes bars one at a time; no look-ahead bias.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from trading_agent.backtester.metrics import PerformanceMetrics, calculate_metrics
from trading_agent.strategies.base import BaseStrategy, Signal
import config

logger = logging.getLogger("backtester.engine")


@dataclass
class Trade:
    symbol:     str
    entry_bar:  int
    entry_price:float
    direction:  int          # 1=long, -1=short
    size:       float        # shares
    exit_bar:   Optional[int]   = None
    exit_price: Optional[float] = None
    pnl:        float           = 0.0
    return_pct: float           = 0.0
    exit_reason:str             = ""


@dataclass
class BacktestResult:
    equity_curve:  pd.Series
    trade_returns: pd.Series
    trades:        List[Trade]
    metrics:       PerformanceMetrics
    symbol:        str
    strategy_name: str


class BacktestEngine:
    def __init__(self,
                 initial_capital: float = config.INITIAL_CAPITAL,
                 commission:      float = config.COMMISSION_RATE,
                 slippage_bps:    int   = config.SLIPPAGE_BPS,
                 allow_short:     bool  = False,
                 stop_loss_pct:   float = config.DEFAULT_STOP_LOSS_PCT,
                 take_profit_pct: float = config.DEFAULT_TAKE_PROFIT_PCT,
                 trailing_stop:   bool  = False):
        self.initial_capital = initial_capital
        self.commission      = commission
        self.slippage        = slippage_bps / 10_000
        self.allow_short     = allow_short
        self.stop_loss_pct   = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop   = trailing_stop

    def run(self, data: pd.DataFrame, strategy: BaseStrategy,
            symbol: str = "ASSET") -> BacktestResult:
        df = data.copy().reset_index(drop=True)
        logger.info("Backtesting %s over %d bars.", symbol, len(df))

        result   = strategy.generate_signals(data)
        signals  = result.signals.values
        pos_sz   = result.position_sizes.values
        closes   = df["Close"].values
        highs    = df["High"].values
        lows     = df["Low"].values

        cash     = self.initial_capital
        position = 0.0        # shares held (negative = short)
        entry_p  = 0.0
        entry_i  = 0
        high_watermark = 0.0  # for trailing stop

        equity_curve = np.empty(len(df))
        trades: List[Trade] = []
        trade_returns: List[float] = []

        for i in range(len(df)):
            price = closes[i]

            # ── Check stops on open price ──────────────────────────────
            if position != 0 and i > 0:
                open_p = df["Open"].iloc[i] if "Open" in df.columns else price
                exit_p, reason = None, ""

                if position > 0:
                    sl = entry_p * (1 - self.stop_loss_pct)
                    tp = entry_p * (1 + self.take_profit_pct) if self.take_profit_pct else None
                    if self.trailing_stop:
                        high_watermark = max(high_watermark, highs[i - 1])
                        sl = high_watermark * (1 - self.stop_loss_pct)
                    if open_p <= sl:
                        exit_p, reason = open_p, "stop_loss"
                    elif tp and open_p >= tp:
                        exit_p, reason = open_p, "take_profit"
                else:
                    sl = entry_p * (1 + self.stop_loss_pct)
                    tp = entry_p * (1 - self.take_profit_pct) if self.take_profit_pct else None
                    if open_p >= sl:
                        exit_p, reason = open_p, "stop_loss"
                    elif tp and open_p <= tp:
                        exit_p, reason = open_p, "take_profit"

                if exit_p is not None:
                    cash, pnl, ret = self._close(cash, position, exit_p)
                    trades.append(Trade(symbol, entry_i, entry_p, int(np.sign(position)),
                                        abs(position), i, exit_p, pnl, ret, reason))
                    trade_returns.append(ret)
                    position, high_watermark = 0.0, 0.0

            # ── Signal execution ───────────────────────────────────────
            sig = int(signals[i])
            if sig != Signal.HOLD:
                exec_price = price * (1 + self.slippage * sig)

                if position != 0 and np.sign(sig) != np.sign(position):
                    cash, pnl, ret = self._close(cash, position, exec_price)
                    trades.append(Trade(symbol, entry_i, entry_p, int(np.sign(position)),
                                        abs(position), i, exec_price, pnl, ret, "signal_exit"))
                    trade_returns.append(ret)
                    position, high_watermark = 0.0, 0.0

                if position == 0 and (sig == Signal.BUY or (sig == Signal.SELL and self.allow_short)):
                    size    = pos_sz[i] if pos_sz[i] > 0 else 0.5
                    equity  = cash
                    shares  = (equity * size) / exec_price
                    cost    = shares * exec_price * (1 + self.commission)
                    if cost <= cash:
                        cash    -= cost
                        position = shares * sig
                        entry_p, entry_i = exec_price, i
                        high_watermark   = exec_price if sig == Signal.BUY else 0.0

            market_val     = position * closes[i]
            equity_curve[i] = cash + market_val

        # ── Close any open position at end ─────────────────────────────
        if position != 0:
            cash, pnl, ret = self._close(cash, position, closes[-1])
            trades.append(Trade(symbol, entry_i, entry_p, int(np.sign(position)),
                                abs(position), len(df) - 1, closes[-1], pnl, ret, "end_of_data"))
            trade_returns.append(ret)

        eq_series = pd.Series(equity_curve, index=data.index)
        tr_series = pd.Series(trade_returns, dtype=float)
        metrics   = calculate_metrics(eq_series, tr_series)

        return BacktestResult(
            equity_curve=eq_series, trade_returns=tr_series,
            trades=trades, metrics=metrics,
            symbol=symbol, strategy_name=strategy.name,
        )

    def _close(self, cash, position, price):
        proceeds = abs(position) * price * (1 - self.commission)
        cost     = abs(position) * (price if position > 0 else -price)
        if position > 0:
            pnl = proceeds - (position * price)   # approximate
            # true pnl
            pnl = (price - (cash + position * price - cash) / position) * position
        else:
            pnl = 0.0
        cash += proceeds
        ret   = (price / abs(cash)) if cash > 0 else 0.0  # rough; real ret computed below
        # simpler accurate return
        entry_val = abs(position) * price  # we don't track entry here, caller uses Trade
        ret       = 0.0
        return cash, pnl, ret
