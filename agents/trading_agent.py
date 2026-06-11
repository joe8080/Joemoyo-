"""
TradingAgent: Operates an Alpaca paper-trading account.

Connects to the Alpaca Trading + Market Data APIs and uses Claude's tool-use
loop to read the account, analyze quotes, and place/cancel orders — all in the
paper (simulated) environment by default.

Requires ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env.
"""

import json
from datetime import date

from agents.base_agent import BaseAgent
from prompts.trading_prompts import TRADING_SYSTEM_PROMPT


class TradingAgent(BaseAgent):

    def __init__(self, paper: bool | None = None):
        # Lazy import so missing credentials only error when this agent is used.
        from tools.alpaca_client import AlpacaClient
        self.alpaca = AlpacaClient(paper=paper)
        super().__init__()

    @property
    def system_prompt(self) -> str:
        env = "PAPER" if self.alpaca.paper else "LIVE"
        return TRADING_SYSTEM_PROMPT + f"\n\nActive environment: {env} trading."

    def _define_tools(self) -> list:
        return [
            {
                "name": "get_account",
                "description": "Get account status, cash, equity, buying power, and today's P&L.",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_positions",
                "description": "List all currently open positions with unrealized P&L.",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_orders",
                "description": "List recent orders. status can be 'open', 'closed', or 'all'.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["open", "closed", "all"]},
                    },
                    "required": [],
                },
            },
            {
                "name": "get_quote",
                "description": "Get the latest bid/ask quote and last trade price for a stock symbol.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Ticker, e.g. AAPL"},
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "get_bars",
                "description": "Get historical OHLCV price bars for a symbol over a recent window.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {
                            "type": "string",
                            "description": "1Min, 5Min, 15Min, 1Hour, or 1Day",
                        },
                        "days_back": {"type": "integer"},
                    },
                    "required": ["symbol"],
                },
            },
            {
                "name": "get_market_clock",
                "description": "Check whether the market is currently open and the next open/close times.",
                "input_schema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "submit_order",
                "description": (
                    "Submit a buy or sell order in the PAPER account. Provide exactly one "
                    "of qty (shares, fractional allowed) or notional (dollar amount)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "side": {"type": "string", "enum": ["buy", "sell"]},
                        "qty": {"type": "number", "description": "Number of shares"},
                        "notional": {"type": "number", "description": "Dollar amount to trade"},
                        "order_type": {
                            "type": "string",
                            "enum": ["market", "limit", "stop", "stop_limit"],
                        },
                        "time_in_force": {
                            "type": "string",
                            "enum": ["day", "gtc", "ioc", "fok", "opg", "cls"],
                        },
                        "limit_price": {"type": "number"},
                        "stop_price": {"type": "number"},
                    },
                    "required": ["symbol", "side"],
                },
            },
            {
                "name": "cancel_order",
                "description": "Cancel a single open order by its order id.",
                "input_schema": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                },
            },
            {
                "name": "close_position",
                "description": "Liquidate the entire position in one symbol (submits a market order).",
                "input_schema": {
                    "type": "object",
                    "properties": {"symbol": {"type": "string"}},
                    "required": ["symbol"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "get_account":
            return json.dumps(self.alpaca.account_summary(), indent=2)

        if tool_name == "get_positions":
            positions = self.alpaca.get_positions()
            return json.dumps(self.alpaca.simplify_positions(positions), indent=2)

        if tool_name == "get_orders":
            orders = self.alpaca.get_orders(status=tool_input.get("status", "all"))
            return json.dumps(self.alpaca.simplify_orders(orders), indent=2)

        if tool_name == "get_quote":
            quote = self.alpaca.get_latest_quote(tool_input["symbol"])
            trade = self.alpaca.get_latest_trade(tool_input["symbol"])
            return json.dumps({"quote": quote, "last_trade": trade}, indent=2)

        if tool_name == "get_bars":
            bars = self.alpaca.get_bars(
                tool_input["symbol"],
                timeframe=tool_input.get("timeframe", "1Day"),
                days_back=tool_input.get("days_back", 30),
            )
            return json.dumps(bars[-30:], indent=2)

        if tool_name == "get_market_clock":
            return json.dumps(self.alpaca.get_clock(), indent=2)

        if tool_name == "submit_order":
            try:
                order = self.alpaca.submit_order(
                    symbol=tool_input["symbol"],
                    side=tool_input["side"],
                    qty=tool_input.get("qty"),
                    notional=tool_input.get("notional"),
                    order_type=tool_input.get("order_type", "market"),
                    time_in_force=tool_input.get("time_in_force", "day"),
                    limit_price=tool_input.get("limit_price"),
                    stop_price=tool_input.get("stop_price"),
                )
            except (ValueError, RuntimeError) as e:
                return f"Order rejected: {e}"
            return json.dumps(self.alpaca.simplify_orders([order])[0], indent=2)

        if tool_name == "cancel_order":
            try:
                self.alpaca.cancel_order(tool_input["order_id"])
            except RuntimeError as e:
                return f"Cancel failed: {e}"
            return f"Cancelled order {tool_input['order_id']}"

        if tool_name == "close_position":
            try:
                order = self.alpaca.close_position(tool_input["symbol"])
            except RuntimeError as e:
                return f"Close failed: {e}"
            return json.dumps(order, indent=2) if order else f"Closing {tool_input['symbol']}"

        return f"Unknown tool: {tool_name}"

    # ------------------------------------------------------------------ #
    #  Convenience workflows                                              #
    # ------------------------------------------------------------------ #

    def account_overview(self) -> str:
        """Plain-language snapshot of account, positions, and open orders."""
        prompt = """
Give me a clear snapshot of my paper trading account right now.

Steps:
1. Get the account summary (equity, cash, buying power, today's P&L).
2. List open positions with their unrealized P&L.
3. List any open orders.
4. Check whether the market is currently open.

Then write a short, scannable summary:
- ACCOUNT HEALTH (one line)
- POSITIONS (small table: symbol, qty, avg entry, current, unrealized P&L)
- OPEN ORDERS (or "none")
- MARKET STATUS (open/closed + next change)

Remind me this is paper trading.
"""
        return self.run(prompt)

    def analyze_symbol(self, symbol: str) -> str:
        """Research a ticker using live quote + recent bars and give a paper-trade view."""
        prompt = f"""
Analyze {symbol.upper()} for a potential paper trade.

Steps:
1. Get the latest quote and last trade price.
2. Pull recent daily bars (last ~30 days).
3. Check my account buying power.
4. Check whether the market is open.

Then produce:
- PRICE SNAPSHOT (current price, bid/ask, 30-day range)
- SHORT TREND READ (what the recent bars suggest — keep it factual)
- A SUGGESTED PAPER TRADE (side, suggested size as % of buying power and in
  shares/notional, order type, and a sensible stop/limit if relevant)
- RISK NOTES

Do NOT place any order — just propose it. Educational paper trading only,
not financial advice.
"""
        result = self.run(prompt)
        self.save_output(result, "reports", f"trade_analysis_{symbol.upper()}_{date.today().isoformat()}.md")
        return result

    def execute_instruction(self, instruction: str) -> str:
        """Free-form: let the user describe a trade in natural language and act on it."""
        prompt = f"""
The user wants to do the following in their PAPER trading account:

"{instruction}"

Before acting:
1. Check account buying power and current positions.
2. Get a live quote for any symbol involved.
3. Verify market status.

Then carry out the instruction by placing/cancelling orders as needed, sizing
responsibly. After acting, confirm exactly what was submitted (symbol, side,
qty/notional, type, time-in-force) and report the order id and status.

If the instruction is unsafe, ambiguous, or would exceed reasonable risk,
do NOT place the order — explain why and propose a safer alternative.
"""
        return self.run(prompt)
