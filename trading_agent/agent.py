"""
Self-improving trading agent.

In backtest/paper mode:  uses BacktestEngine — no real orders.
In live mode:            routes signals through AlpacaBroker.

The agent tracks performance per strategy and market regime, and
rebalances strategy weights every `rebalance_every` cycles to favour
the best-performing ones.
"""
from __future__ import annotations
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

import config
from trading_agent.data.fetcher import DataFetcher
from trading_agent.data.processor import DataProcessor
from trading_agent.risk.manager import RiskManager
from trading_agent.strategies.momentum import MomentumStrategy
from trading_agent.strategies.mean_reversion import MeanReversionStrategy
from trading_agent.strategies.macd import MACDStrategy
from trading_agent.strategies.combined import CombinedStrategy
from trading_agent.backtester.metrics import calculate_metrics

logger = logging.getLogger("agent")


class TradingAgent:
    REGIMES = ("trending_up", "trending_down", "ranging", "volatile")

    def __init__(self, symbols: List[str],
                 live: bool = False,
                 rebalance_every: int = 20,
                 state_file: Optional[str] = None):
        self.symbols         = [s.upper() for s in symbols]
        self.live            = live
        self.rebalance_every = rebalance_every
        self.state_file      = Path(state_file or "agent_state.json")

        self.strategies: Dict[str, object] = {
            "momentum":      MomentumStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "macd":          MACDStrategy(),
            "combined":      CombinedStrategy(),
        }
        self.weights: Dict[str, float] = {k: 1.0 for k in self.strategies}

        # performance tracking per strategy
        self._perf: Dict[str, List[float]] = defaultdict(list)
        self._cycle = 0

        self.fetcher   = DataFetcher()
        self.processor = DataProcessor()
        self.risk_mgr  = RiskManager()

        self._broker = None
        if live:
            from trading_agent.broker.alpaca import AlpacaBroker
            self._broker = AlpacaBroker()
            mode = "PAPER" if config.ALPACA_PAPER else "LIVE"
            logger.info("Agent running in LIVE mode (%s trading)", mode)
        else:
            logger.info("Agent running in BACKTEST/PAPER mode (no real orders).")

        self._load_state()

    # ── Main loop ─────────────────────────────────────────────────────────

    def run_once(self, start: str, end: Optional[str] = None,
                 demo: bool = False) -> Dict:
        """Fetch latest data, generate signals, optionally execute."""
        results = {}
        for sym in self.symbols:
            try:
                if demo:
                    raw = self.fetcher.generate_synthetic(sym, start=start, end=end)
                else:
                    raw = self.fetcher.fetch(sym, start, end)
                if raw is None or raw.empty:
                    continue
                df = self.processor.clean(raw)
                signals = self._pick_best_signals(df)
                results[sym] = signals

                if self.live and self._broker:
                    self._execute_live(sym, signals, df)
            except Exception as exc:
                logger.error("Error processing %s: %s", sym, exc)

        self._cycle += 1
        if self._cycle % self.rebalance_every == 0:
            self._rebalance_weights()
        return results

    # ── Signal selection ──────────────────────────────────────────────────

    def _pick_best_signals(self, df: pd.DataFrame) -> Dict:
        regime = self._detect_regime(df)
        weighted_signal = 0.0
        total_w = sum(self.weights.values()) or 1.0

        for name, strat in self.strategies.items():
            result = strat.generate_signals(df)
            last   = int(result.signals.iloc[-1])
            w      = self.weights[name]
            weighted_signal += last * w

        final = 1 if weighted_signal > 0 else (-1 if weighted_signal < 0 else 0)
        confidence = abs(weighted_signal) / total_w
        return {"signal": final, "confidence": round(confidence, 3),
                "regime": regime, "weights": dict(self.weights)}

    # ── Live execution ────────────────────────────────────────────────────

    def _execute_live(self, symbol: str, signal_info: Dict, df: pd.DataFrame):
        signal = signal_info["signal"]
        if signal == 0:
            return

        acct     = self._broker.get_account()
        position = self._broker.get_position(symbol)
        price    = float(df["Close"].iloc[-1])
        atr_col  = df.get("atr_14") if hasattr(df, "get") else None
        atr      = float(atr_col.iloc[-1]) if atr_col is not None and not atr_col.empty else None

        portfolio = {
            "equity":         acct.equity,
            "open_positions": len(self._broker.get_positions()),
            "current_heat":   1.0 - acct.buying_power / acct.equity,
        }
        spec = self.risk_mgr.evaluate(symbol, signal, price, portfolio, atr)

        if spec.position_size_pct == 0:
            logger.info("Risk manager blocked trade for %s.", symbol)
            return

        # Close opposing position first
        if position and ((signal == 1 and position.side == "short") or
                         (signal == -1 and position.side == "long")):
            logger.info("Closing opposing %s position in %s.", position.side, symbol)
            self._broker.close_position(symbol)

        # Size in shares
        shares = (acct.buying_power * spec.position_size_pct) / price
        side   = "buy" if signal == 1 else "sell"

        if spec.stop_loss_price and spec.take_profit_price:
            order = self._broker.submit_bracket_order(
                symbol, shares, side,
                take_profit_price=spec.take_profit_price,
                stop_loss_price=spec.stop_loss_price,
            )
        else:
            order = self._broker.submit_market_order(symbol, shares, side)

        logger.info("Order submitted: %s %s x %.4f — ID: %s", side, symbol, shares, order.id)

    # ── Regime detection ──────────────────────────────────────────────────

    def _detect_regime(self, df: pd.DataFrame) -> str:
        if len(df) < 30:
            return "unknown"
        close = df["Close"]
        ret   = close.pct_change().dropna()
        vol   = ret.rolling(20).std().iloc[-1] * np.sqrt(252)
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        price = close.iloc[-1]

        if vol > 0.40:
            return "volatile"
        if price > ema20 > ema50:
            return "trending_up"
        if price < ema20 < ema50:
            return "trending_down"
        return "ranging"

    # ── Self-improvement ──────────────────────────────────────────────────

    def record_result(self, strategy_name: str, trade_return: float):
        self._perf[strategy_name].append(trade_return)

    def _rebalance_weights(self):
        new_weights = {}
        for name in self.strategies:
            history = self._perf.get(name, [])
            if len(history) >= 5:
                recent   = history[-20:]
                avg_ret  = np.mean(recent)
                sharpe   = avg_ret / (np.std(recent) + 1e-9) * np.sqrt(252)
                new_weights[name] = max(0.1, 1.0 + sharpe)
            else:
                new_weights[name] = 1.0

        total = sum(new_weights.values())
        self.weights = {k: v / total * len(self.strategies) for k, v in new_weights.items()}
        logger.info("Rebalanced strategy weights: %s",
                    {k: f"{v:.2f}" for k, v in self.weights.items()})
        self._save_state()

    # ── State persistence ─────────────────────────────────────────────────

    def _save_state(self):
        state = {"weights": self.weights, "cycle": self._cycle,
                 "updated": datetime.now().isoformat()}
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as exc:
            logger.warning("Could not save state: %s", exc)

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                self.weights = state.get("weights", self.weights)
                self._cycle  = state.get("cycle", 0)
                logger.info("Loaded agent state (cycle %d).", self._cycle)
            except Exception as exc:
                logger.warning("Could not load state: %s", exc)
