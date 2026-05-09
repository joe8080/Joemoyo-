from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
import config


@dataclass
class OrderSpec:
    symbol:          str
    signal:          int          # 1=buy, -1=sell, 0=hold
    position_size_pct: float      # fraction of equity
    stop_loss_price:   Optional[float] = None
    take_profit_price: Optional[float] = None
    trailing_stop_pct: Optional[float] = None


class RiskManager:
    def __init__(self,
                 risk_per_trade:     float = config.RISK_PER_TRADE,
                 stop_loss_pct:      float = config.DEFAULT_STOP_LOSS_PCT,
                 take_profit_pct:    float = config.DEFAULT_TAKE_PROFIT_PCT,
                 stop_method:        str   = "atr",      # "fixed" | "atr" | "trailing"
                 atr_stop_multiplier: float = 2.0,
                 max_positions:      int   = config.MAX_POSITIONS,
                 max_heat:           float = config.MAX_PORTFOLIO_HEAT):
        self.risk_per_trade      = risk_per_trade
        self.stop_loss_pct       = stop_loss_pct
        self.take_profit_pct     = take_profit_pct
        self.stop_method         = stop_method
        self.atr_stop_mult       = atr_stop_multiplier
        self.max_positions       = max_positions
        self.max_heat            = max_heat

    def evaluate(self, symbol: str, signal: int, price: float,
                 portfolio: Dict, atr: Optional[float] = None) -> OrderSpec:
        if signal == 0:
            return OrderSpec(symbol=symbol, signal=0, position_size_pct=0.0)

        equity          = portfolio.get("equity", config.INITIAL_CAPITAL)
        open_positions  = portfolio.get("open_positions", 0)
        current_heat    = portfolio.get("current_heat", 0.0)

        if open_positions >= self.max_positions:
            return OrderSpec(symbol=symbol, signal=0, position_size_pct=0.0)
        if current_heat >= self.max_heat:
            return OrderSpec(symbol=symbol, signal=0, position_size_pct=0.0)

        # Kelly-fraction sizing based on risk per trade
        risk_amount  = equity * self.risk_per_trade
        stop_dist    = self._stop_distance(price, atr)
        kelly_size   = risk_amount / (stop_dist * equity) if stop_dist > 0 else self.risk_per_trade
        size_pct     = min(kelly_size, self.max_heat - current_heat, self.risk_per_trade * 3)

        stop_price = tp_price = trail_pct = None
        if self.stop_method == "atr" and atr:
            stop_dist_price = self.atr_stop_mult * atr
            stop_price = price - stop_dist_price if signal == 1 else price + stop_dist_price
        elif self.stop_method == "trailing":
            trail_pct  = self.stop_loss_pct
        else:
            stop_price = price * (1 - self.stop_loss_pct) if signal == 1 else price * (1 + self.stop_loss_pct)

        if self.take_profit_pct > 0:
            tp_price = price * (1 + self.take_profit_pct) if signal == 1 else price * (1 - self.take_profit_pct)

        return OrderSpec(
            symbol=symbol, signal=signal,
            position_size_pct=round(size_pct, 4),
            stop_loss_price=round(stop_price, 4) if stop_price else None,
            take_profit_price=round(tp_price, 4) if tp_price else None,
            trailing_stop_pct=trail_pct,
        )

    def _stop_distance(self, price: float, atr: Optional[float]) -> float:
        if self.stop_method == "atr" and atr:
            return (self.atr_stop_mult * atr) / price
        return self.stop_loss_pct
