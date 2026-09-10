"""
What each built-in agent does when the OS hands it a task.

Each runner takes the task's input text (may be empty) and returns a string or
dict; the worker turns that into the task result and the card's "Last" line.
They import lazily so the worker starts without every API key — a missing key
surfaces as a clear failure on that one task instead of stopping the runner.
"""

from __future__ import annotations

import json
import os

from config.brand_profiles import BRAND_PROFILES

SWING_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD"]


def _needs(text: str, what: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError(f"This agent needs {what} — type it in the Run box.")
    return text


def _brand_and_topic(text: str, default: str = "finance_channel") -> tuple[str, str]:
    if ":" in text:
        brand, topic = text.split(":", 1)
        if brand.strip() in BRAND_PROFILES:
            return brand.strip(), topic.strip()
    return default, text.strip()


def run_trading_agent(text: str):
    from agents.trading_agent import TradingAgent
    agent = TradingAgent()
    text = (text or "").strip()
    return agent.analyze_symbol(text.upper()) if text else agent.account_overview()


def run_shopify(text: str):
    from agents.shopify_reporting import ShopifyReportingAgent
    agent = ShopifyReportingAgent()
    return agent.generate_monthly_report() if "month" in (text or "").lower() else agent.generate_weekly_report()


def run_content_research(text: str):
    from agents.content_research import ContentResearchAgent
    return ContentResearchAgent().research_topic(_needs(text, "a topic"))["research"]


def run_script_history(text: str):
    from agents.script_writer import ScriptWriterAgent
    return ScriptWriterAgent(channel="history_channel").write_script(_needs(text, "a topic"), target_minutes=12)


def run_script_finance(text: str):
    from agents.script_writer import ScriptWriterAgent
    return ScriptWriterAgent(channel="finance_channel").write_script(_needs(text, "a topic"), target_minutes=15)


def run_financial_content(text: str):
    from agents.financial_content import FinancialContentAgent
    return FinancialContentAgent().analyze_topic(_needs(text, "a topic"))


def run_marketing(text: str):
    from agents.marketing import MarketingAgent
    brand, topic = _brand_and_topic(_needs(text, "a topic"))
    return MarketingAgent().create_social_bundle(brand=brand, topic=topic)


def run_lead_generator(text: str):
    from agents.lead_generator import LeadGeneratorAgent
    parts = [p.strip() for p in _needs(text, "a prospect (name, genre, followers)").split(",")]
    prospect = {"name": parts[0]}
    if len(parts) > 1:
        prospect["genre"] = parts[1]
    if len(parts) > 2:
        prospect["followers"] = parts[2]
    return LeadGeneratorAgent().create_studio_outreach(prospect)


def run_swing_dry_run(text: str):
    """One paper-bot cycle with dry_run=True: shows what it would do, places nothing."""
    from agents.auto_trader import AutoTrader
    bot = AutoTrader(symbols=SWING_SYMBOLS, budget=50_000, cash_per_trade=5_000,
                     max_positions=10, enter_on_trend=True, trailing_stop_pct=8,
                     mode="swing", dry_run=True)
    out = bot.run_once() or {}
    if out.get("skipped"):
        return f"Skipped: {out.get('reason', 'unknown')}"
    proposals = out.get("proposals") or []
    if not proposals:
        return "Dry run: no signals this cycle — nothing would be traded."
    lines = [f"{p.get('action', '?').upper()} {p.get('symbol')} × {p.get('qty')}" for p in proposals]
    return "Dry run would: " + "; ".join(lines)


def run_coach(text: str):
    from tools.alpaca_client import AlpacaClient
    from agents.coach import generate_coach_report
    from config.settings import settings
    client = AlpacaClient()
    orders = client.simplify_orders(client.get_orders(status="all", limit=500))
    result = generate_coach_report(orders, os.path.join(settings.output_dir, "reports"))
    st = result.get("stats", {})
    return (f"Closed trades {st.get('num_trades', 0)} · win rate {st.get('win_rate_pct', 'n/a')}% · "
            f"{result.get('note', '')}")


RUNNERS = {
    "trading_analyst": run_trading_agent,
    "shopify_reporter": run_shopify,
    "history_researcher": run_content_research,
    "history_script_writer": run_script_history,
    "finance_script_writer": run_script_finance,
    "finance_analyst_writer": run_financial_content,
    "marketing_writer": run_marketing,
    "studio_lead_generator": run_lead_generator,
    "swing_trader": run_swing_dry_run,
    "trading_coach": run_coach,
}


def summarise(out) -> str:
    if isinstance(out, str):
        text = out
    else:
        try:
            text = json.dumps(out, default=str)
        except TypeError:
            text = str(out)
    text = " ".join(text.split())
    return text if len(text) <= 400 else text[:399] + "…"
