"""
Alpaca broker integration.

Supports:
  - Account info & buying power
  - Submit market / limit / stop orders
  - Cancel orders
  - Get open positions
  - Real-time order status via REST polling
  - Paper trading by default (flip ALPACA_PAPER=false in .env for live)
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import requests

import config

logger = logging.getLogger("broker.alpaca")


@dataclass
class AccountInfo:
    equity:        float
    cash:          float
    buying_power:  float
    portfolio_value: float
    daytrade_count: int
    is_paper:      bool


@dataclass
class Position:
    symbol:         str
    qty:            float
    side:           str          # "long" | "short"
    avg_entry:      float
    current_price:  float
    unrealized_pl:  float
    unrealized_plpc: float
    market_value:   float


@dataclass
class Order:
    id:           str
    symbol:       str
    qty:          float
    side:         str            # "buy" | "sell"
    order_type:   str            # "market" | "limit" | "stop" | "stop_limit"
    status:       str            # "new" | "filled" | "partially_filled" | "canceled" | "rejected"
    filled_qty:   float = 0.0
    filled_avg:   Optional[float] = None
    limit_price:  Optional[float] = None
    stop_price:   Optional[float] = None
    created_at:   Optional[str] = None
    filled_at:    Optional[str] = None


class AlpacaBroker:
    """
    Thin wrapper around the Alpaca REST API v2.

    Usage
    -----
    broker = AlpacaBroker()          # reads keys from config / .env
    acct   = broker.get_account()
    broker.submit_market_order("AAPL", qty=10, side="buy")
    """

    def __init__(self):
        if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
            raise RuntimeError(
                "Alpaca API keys not set. Copy .env.example → .env and add your keys."
            )
        self._base   = config.ALPACA_BASE_URL
        self._headers = {
            "APCA-API-KEY-ID":     config.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": config.ALPACA_SECRET_KEY,
            "Content-Type":        "application/json",
        }
        self.paper = config.ALPACA_PAPER
        mode = "PAPER" if self.paper else "LIVE"
        logger.info("AlpacaBroker initialised [%s] — %s", mode, self._base)

    # ── Account ───────────────────────────────────────────────────────────

    def get_account(self) -> AccountInfo:
        data = self._get("/v2/account")
        return AccountInfo(
            equity          = float(data["equity"]),
            cash            = float(data["cash"]),
            buying_power    = float(data["buying_power"]),
            portfolio_value = float(data["portfolio_value"]),
            daytrade_count  = int(data.get("daytrade_count", 0)),
            is_paper        = self.paper,
        )

    def get_buying_power(self) -> float:
        return self.get_account().buying_power

    # ── Orders ────────────────────────────────────────────────────────────

    def submit_market_order(self, symbol: str, qty: float, side: str,
                            time_in_force: str = "day") -> Order:
        """Submit a market order. side = 'buy' | 'sell'."""
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(round(abs(qty), 6)),
            "side":          side.lower(),
            "type":          "market",
            "time_in_force": time_in_force,
        }
        logger.info("Market order: %s %s x %.4f", side.upper(), symbol, qty)
        return self._parse_order(self._post("/v2/orders", payload))

    def submit_limit_order(self, symbol: str, qty: float, side: str,
                           limit_price: float, time_in_force: str = "day") -> Order:
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(round(abs(qty), 6)),
            "side":          side.lower(),
            "type":          "limit",
            "limit_price":   str(round(limit_price, 4)),
            "time_in_force": time_in_force,
        }
        logger.info("Limit order: %s %s x %.4f @ %.4f", side.upper(), symbol, qty, limit_price)
        return self._parse_order(self._post("/v2/orders", payload))

    def submit_stop_order(self, symbol: str, qty: float, side: str,
                          stop_price: float, time_in_force: str = "day") -> Order:
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(round(abs(qty), 6)),
            "side":          side.lower(),
            "type":          "stop",
            "stop_price":    str(round(stop_price, 4)),
            "time_in_force": time_in_force,
        }
        logger.info("Stop order: %s %s x %.4f stop=%.4f", side.upper(), symbol, qty, stop_price)
        return self._parse_order(self._post("/v2/orders", payload))

    def submit_bracket_order(self, symbol: str, qty: float, side: str,
                              take_profit_price: float,
                              stop_loss_price: float) -> Order:
        """One-cancels-other bracket (entry + TP + SL in a single call)."""
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(round(abs(qty), 6)),
            "side":          side.lower(),
            "type":          "market",
            "time_in_force": "gtc",
            "order_class":   "bracket",
            "take_profit":   {"limit_price": str(round(take_profit_price, 4))},
            "stop_loss":     {"stop_price":  str(round(stop_loss_price, 4))},
        }
        logger.info(
            "Bracket order: %s %s x %.4f TP=%.4f SL=%.4f",
            side.upper(), symbol, qty, take_profit_price, stop_loss_price,
        )
        return self._parse_order(self._post("/v2/orders", payload))

    def cancel_order(self, order_id: str) -> bool:
        try:
            self._delete(f"/v2/orders/{order_id}")
            logger.info("Cancelled order %s", order_id)
            return True
        except Exception as exc:
            logger.warning("Cancel failed for %s: %s", order_id, exc)
            return False

    def cancel_all_orders(self) -> int:
        cancelled = self._delete("/v2/orders")
        n = len(cancelled) if isinstance(cancelled, list) else 0
        logger.info("Cancelled %d open orders.", n)
        return n

    def get_order(self, order_id: str) -> Order:
        return self._parse_order(self._get(f"/v2/orders/{order_id}"))

    def list_open_orders(self) -> List[Order]:
        orders = self._get("/v2/orders", params={"status": "open"})
        return [self._parse_order(o) for o in orders]

    def wait_for_fill(self, order_id: str, timeout: int = 30) -> Order:
        """Poll until the order is filled or timeout (seconds) reached."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            order = self.get_order(order_id)
            if order.status in ("filled", "canceled", "rejected", "expired"):
                return order
            time.sleep(1)
        return self.get_order(order_id)

    # ── Positions ─────────────────────────────────────────────────────────

    def get_positions(self) -> List[Position]:
        data = self._get("/v2/positions")
        return [self._parse_position(p) for p in data]

    def get_position(self, symbol: str) -> Optional[Position]:
        try:
            return self._parse_position(self._get(f"/v2/positions/{symbol.upper()}"))
        except Exception:
            return None

    def close_position(self, symbol: str) -> Order:
        """Liquidate an entire position at market."""
        data = self._delete(f"/v2/positions/{symbol.upper()}")
        return self._parse_order(data)

    def close_all_positions(self) -> List[Order]:
        """Liquidate all open positions."""
        data = self._delete("/v2/positions")
        if isinstance(data, list):
            return [self._parse_order(o.get("body", o)) for o in data if isinstance(o, dict)]
        return []

    # ── Market status ─────────────────────────────────────────────────────

    def is_market_open(self) -> bool:
        clock = self._get("/v2/clock")
        return bool(clock.get("is_open", False))

    def get_clock(self) -> Dict:
        return self._get("/v2/clock")

    # ── Asset info ────────────────────────────────────────────────────────

    def get_asset(self, symbol: str) -> Dict:
        return self._get(f"/v2/assets/{symbol.upper()}")

    def is_tradable(self, symbol: str) -> bool:
        try:
            asset = self.get_asset(symbol)
            return asset.get("tradable", False) and asset.get("status") == "active"
        except Exception:
            return False

    # ── Portfolio summary ─────────────────────────────────────────────────

    def portfolio_summary(self) -> str:
        acct    = self.get_account()
        pos     = self.get_positions()
        lines   = [
            f"{'='*50}",
            f"  Alpaca {'PAPER' if self.paper else 'LIVE'} Account",
            f"{'='*50}",
            f"  Equity:        ${acct.equity:>12,.2f}",
            f"  Cash:          ${acct.cash:>12,.2f}",
            f"  Buying Power:  ${acct.buying_power:>12,.2f}",
            f"  Portfolio Val: ${acct.portfolio_value:>12,.2f}",
            f"  Day Trades:    {acct.daytrade_count}",
            f"{'─'*50}",
            f"  Open Positions ({len(pos)})",
        ]
        for p in pos:
            sign = "+" if p.unrealized_pl >= 0 else ""
            lines.append(
                f"  {p.symbol:<8} {p.side:<5}  qty={p.qty:.2f}  "
                f"entry=${p.avg_entry:.2f}  now=${p.current_price:.2f}  "
                f"P&L={sign}${p.unrealized_pl:.2f} ({sign}{p.unrealized_plpc:.1%})"
            )
        lines.append("=" * 50)
        return "\n".join(lines)

    # ── Internal HTTP helpers ─────────────────────────────────────────────

    def _get(self, path: str, params: Optional[Dict] = None):
        resp = requests.get(self._base + path, headers=self._headers,
                            params=params, timeout=10)
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, payload: Dict):
        resp = requests.post(self._base + path, headers=self._headers,
                             json=payload, timeout=10)
        self._raise_for_status(resp)
        return resp.json()

    def _delete(self, path: str):
        resp = requests.delete(self._base + path, headers=self._headers, timeout=10)
        if resp.status_code == 204:
            return {}
        self._raise_for_status(resp)
        try:
            return resp.json()
        except Exception:
            return {}

    @staticmethod
    def _raise_for_status(resp: requests.Response):
        if not resp.ok:
            raise RuntimeError(f"Alpaca API error {resp.status_code}: {resp.text[:300]}")

    @staticmethod
    def _parse_order(data: Dict) -> Order:
        return Order(
            id          = data["id"],
            symbol      = data["symbol"],
            qty         = float(data.get("qty") or data.get("filled_qty") or 0),
            side        = data["side"],
            order_type  = data["type"],
            status      = data["status"],
            filled_qty  = float(data.get("filled_qty") or 0),
            filled_avg  = float(data["filled_avg_price"]) if data.get("filled_avg_price") else None,
            limit_price = float(data["limit_price"]) if data.get("limit_price") else None,
            stop_price  = float(data["stop_price"])  if data.get("stop_price")  else None,
            created_at  = data.get("created_at"),
            filled_at   = data.get("filled_at"),
        )

    @staticmethod
    def _parse_position(data: Dict) -> Position:
        return Position(
            symbol          = data["symbol"],
            qty             = float(data["qty"]),
            side            = data["side"],
            avg_entry       = float(data["avg_entry_price"]),
            current_price   = float(data["current_price"]),
            unrealized_pl   = float(data["unrealized_pl"]),
            unrealized_plpc = float(data["unrealized_plpc"]),
            market_value    = float(data["market_value"]),
        )
