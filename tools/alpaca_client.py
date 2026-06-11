"""
Alpaca Trading API client (paper + live).

Wraps the Alpaca Trading REST API for account info, positions, orders,
and the Market Data API for live quotes.

Defaults to PAPER trading (https://paper-api.alpaca.markets) so strategies
can be tested with zero real-money risk before going live.

Requires ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env.
Get paper keys free at https://app.alpaca.markets (Paper Trading > API Keys).
"""

import json
from datetime import datetime, timedelta

import requests

from config.settings import settings

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"


class AlpacaClient:
    """Wrapper for the Alpaca Trading and Market Data REST APIs."""

    API_VERSION = "v2"

    def __init__(self, paper: bool | None = None):
        if not settings.alpaca_api_key_id or not settings.alpaca_api_secret_key:
            raise EnvironmentError(
                "Alpaca credentials not configured. "
                "Add ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY to your .env file. "
                "Get free paper-trading keys at https://app.alpaca.markets "
                "(Home > Paper Trading > API Keys). Note: the Secret Key is only "
                "shown once at creation — save it immediately."
            )
        # Default to whatever .env says; explicit arg wins.
        self.paper = settings.alpaca_paper if paper is None else paper
        self.base_url = PAPER_BASE_URL if self.paper else LIVE_BASE_URL
        self.headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key_id,
            "APCA-API-SECRET-KEY": settings.alpaca_api_secret_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------ #
    #  Low-level request helpers                                          #
    # ------------------------------------------------------------------ #

    def _trading_url(self, path: str) -> str:
        return f"{self.base_url}/{self.API_VERSION}/{path.lstrip('/')}"

    def _data_url(self, path: str) -> str:
        return f"{DATA_BASE_URL}/{path.lstrip('/')}"

    def _request(self, method: str, url: str, **kwargs) -> dict | list:
        resp = requests.request(method, url, headers=self.headers, timeout=15, **kwargs)
        # Surface Alpaca's JSON error messages instead of a bare HTTP code.
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise RuntimeError(f"Alpaca API error {resp.status_code}: {detail}")
        if resp.text:
            return resp.json()
        return {}

    # ------------------------------------------------------------------ #
    #  Account                                                            #
    # ------------------------------------------------------------------ #

    def get_account(self) -> dict:
        """Fetch account status, equity, buying power, and P&L."""
        return self._request("GET", self._trading_url("account"))

    def account_summary(self) -> dict:
        """Account info trimmed to the fields a trader actually reads."""
        a = self.get_account()
        equity = float(a.get("equity", 0))
        last_equity = float(a.get("last_equity", 0))
        return {
            "status": a.get("status"),
            "currency": a.get("currency", "USD"),
            "cash": round(float(a.get("cash", 0)), 2),
            "equity": round(equity, 2),
            "buying_power": round(float(a.get("buying_power", 0)), 2),
            "portfolio_value": round(float(a.get("portfolio_value", 0)), 2),
            "todays_pl": round(equity - last_equity, 2),
            "trading_blocked": a.get("trading_blocked", False),
            "account_blocked": a.get("account_blocked", False),
            "pattern_day_trader": a.get("pattern_day_trader", False),
            "daytrade_count": a.get("daytrade_count", 0),
        }

    def get_portfolio_history(self, period: str = "1M", timeframe: str = "1D") -> dict:
        """
        Account equity/P&L history for charting.
        period examples: 1D, 1W, 1M, 3M, 1A, all. timeframe: 1Min, 15Min, 1H, 1D.
        Returns {"timestamp": [...], "equity": [...], "profit_loss": [...], ...}.
        """
        return self._request(
            "GET",
            self._trading_url("account/portfolio/history"),
            params={"period": period, "timeframe": timeframe},
        )

    # ------------------------------------------------------------------ #
    #  Positions                                                          #
    # ------------------------------------------------------------------ #

    def get_positions(self) -> list[dict]:
        """Fetch all open positions."""
        return self._request("GET", self._trading_url("positions"))

    def simplify_positions(self, positions: list[dict]) -> list[dict]:
        """Strip positions to key fields."""
        return [
            {
                "symbol": p.get("symbol"),
                "qty": p.get("qty"),
                "side": p.get("side"),
                "avg_entry_price": round(float(p.get("avg_entry_price", 0)), 2),
                "current_price": round(float(p.get("current_price", 0)), 2),
                "market_value": round(float(p.get("market_value", 0)), 2),
                "unrealized_pl": round(float(p.get("unrealized_pl", 0)), 2),
                "unrealized_plpc": round(float(p.get("unrealized_plpc", 0)) * 100, 2),
            }
            for p in positions
        ]

    def close_position(self, symbol: str) -> dict:
        """Liquidate an entire position in one symbol (submits a market order)."""
        return self._request("DELETE", self._trading_url(f"positions/{symbol}"))

    # ------------------------------------------------------------------ #
    #  Orders                                                             #
    # ------------------------------------------------------------------ #

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        """Fetch orders. status: open | closed | all."""
        return self._request(
            "GET",
            self._trading_url("orders"),
            params={"status": status, "limit": limit, "direction": "desc"},
        )

    def simplify_orders(self, orders: list[dict]) -> list[dict]:
        """Strip orders to key fields."""
        return [
            {
                "id": o.get("id"),
                "symbol": o.get("symbol"),
                "side": o.get("side"),
                "qty": o.get("qty"),
                "type": o.get("order_type") or o.get("type"),
                "status": o.get("status"),
                "filled_qty": o.get("filled_qty"),
                "filled_avg_price": o.get("filled_avg_price"),
                "submitted_at": (o.get("submitted_at") or "")[:19],
            }
            for o in orders
        ]

    def submit_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: float | None = None,
        stop_price: float | None = None,
    ) -> dict:
        """
        Submit an order.

        Provide exactly one of qty (number of shares, fractional allowed) or
        notional (dollar amount). side: buy | sell. order_type: market | limit |
        stop | stop_limit. time_in_force: day | gtc | ioc | fok | opg | cls.
        """
        if (qty is None) == (notional is None):
            raise ValueError("Provide exactly one of qty or notional.")

        payload: dict = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }
        if qty is not None:
            payload["qty"] = str(qty)
        if notional is not None:
            payload["notional"] = str(notional)
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)

        return self._request("POST", self._trading_url("orders"), data=json.dumps(payload))

    def cancel_order(self, order_id: str) -> dict:
        """Cancel a single open order by id."""
        return self._request("DELETE", self._trading_url(f"orders/{order_id}"))

    def cancel_all_orders(self) -> list[dict]:
        """Cancel all open orders."""
        return self._request("DELETE", self._trading_url("orders"))

    # ------------------------------------------------------------------ #
    #  Market data                                                        #
    # ------------------------------------------------------------------ #

    def get_latest_quote(self, symbol: str) -> dict:
        """Latest bid/ask quote for a stock symbol."""
        data = self._request(
            "GET", self._data_url(f"v2/stocks/{symbol.upper()}/quotes/latest")
        )
        q = data.get("quote", {})
        return {
            "symbol": symbol.upper(),
            "bid_price": q.get("bp"),
            "ask_price": q.get("ap"),
            "bid_size": q.get("bs"),
            "ask_size": q.get("as"),
            "timestamp": q.get("t"),
        }

    def get_latest_trade(self, symbol: str) -> dict:
        """Latest traded price for a stock symbol."""
        data = self._request(
            "GET", self._data_url(f"v2/stocks/{symbol.upper()}/trades/latest")
        )
        t = data.get("trade", {})
        return {"symbol": symbol.upper(), "price": t.get("p"), "size": t.get("s"), "timestamp": t.get("t")}

    def get_bars(self, symbol: str, timeframe: str = "1Day", days_back: int = 30) -> list[dict]:
        """
        Historical OHLCV bars for a symbol.
        timeframe examples: 1Min, 5Min, 15Min, 1Hour, 1Day.
        """
        start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        data = self._request(
            "GET",
            self._data_url(f"v2/stocks/{symbol.upper()}/bars"),
            params={"timeframe": timeframe, "start": start, "limit": 1000, "adjustment": "raw"},
        )
        bars = data.get("bars", [])
        return [
            {
                "t": b.get("t", "")[:10],
                "open": b.get("o"),
                "high": b.get("h"),
                "low": b.get("l"),
                "close": b.get("c"),
                "volume": b.get("v"),
            }
            for b in bars
        ]

    # ------------------------------------------------------------------ #
    #  Clock / market status                                              #
    # ------------------------------------------------------------------ #

    def get_clock(self) -> dict:
        """Market clock: whether the market is open and next open/close times."""
        return self._request("GET", self._trading_url("clock"))
