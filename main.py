#!/usr/bin/env python3
"""
JoeMoyo Business Agent System
==============================
AI agents for your YouTube channels, music studio, and Shopify store.

Usage:
  python main.py history  --topic "The Fall of Constantinople"
  python main.py finance  --topic "Bitcoin ETF Analysis"
  python main.py shopify  --report weekly
  python main.py leads    --type studio --name "Artist Name" --genre "R&B"
  python main.py leads    --type sponsor --name "Brand Name" --channel history
  python main.py market   --brand history_channel --topic "New video out now"
  python main.py ideas    --weeks 4
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def get_orchestrator():
    """Lazy-load orchestrator to show errors clearly."""
    try:
        from orchestrator.orchestrator import BusinessOrchestrator
        return BusinessOrchestrator()
    except EnvironmentError as e:
        console.print(f"[bold red]Setup Error:[/bold red] {e}")
        console.print("\n[dim]Steps to fix:")
        console.print("  1. Copy .env.example to .env")
        console.print("  2. Add your ANTHROPIC_API_KEY")
        console.print("  3. Run the command again[/dim]")
        sys.exit(1)


@click.group()
def cli():
    """
    \b
    JoeMoyo Business Agent System
    Powered by Claude AI
    """
    console.print(Panel(
        "[bold cyan]JoeMoyo Business Agent System[/bold cyan]\n"
        "[dim]Powered by Claude claude-sonnet-4-6[/dim]",
        style="cyan",
        padding=(0, 2),
    ))


# ------------------------------------------------------------------ #
#  HISTORY CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Historical topic (e.g. "The Fall of Rome")',
)
@click.option(
    "--script-only",
    is_flag=True,
    help="Skip research, write script from Claude knowledge only",
)
def history(topic: str, script_only: bool):
    """
    Produce a complete historical YouTube video package.

    Runs: Research → Script → Social Media Bundle
    Outputs saved to outputs/scripts/ and outputs/marketing/
    """
    orch = get_orchestrator()
    if script_only:
        console.print(f"[bold]Writing script for:[/bold] {topic}")
        result = orch.script_history.write_script(topic_or_research=topic)
        console.print(result)
    else:
        result = orch.produce_history_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  FINANCE CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Financial topic (e.g. "Bitcoin ETF Analysis")',
)
@click.option(
    "--ideas-only",
    is_flag=True,
    help="Generate video ideas instead of a full analysis",
)
@click.option(
    "--count",
    default=10,
    show_default=True,
    help="Number of ideas to generate (used with --ideas-only)",
)
def finance(topic: str, ideas_only: bool, count: int):
    """
    Produce financial YouTube content.

    Runs: Financial Research → Script → Social Media Bundle
    Or: Generate video ideas list (with --ideas-only)
    """
    orch = get_orchestrator()
    if ideas_only:
        console.print(f"[bold]Generating {count} video ideas for:[/bold] {topic}")
        result = orch.financial_agent.generate_video_ideas(niche=topic, count=count)
        console.print(result)
    else:
        result = orch.produce_finance_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  SHOPIFY REPORTING                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--report", "-r",
    default="weekly",
    type=click.Choice(["weekly", "monthly"]),
    show_default=True,
    help="Report type",
)
def shopify(report: str):
    """
    Generate Shopify store performance reports.

    Requires: SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env
    Outputs saved to outputs/reports/
    """
    orch = get_orchestrator()
    try:
        if report == "weekly":
            result = orch.weekly_shopify_report()
        else:
            result = orch.monthly_shopify_report()
        console.print(result)
    except EnvironmentError as e:
        console.print(f"[bold red]Shopify Error:[/bold red] {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
#  LEAD GENERATION                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--type", "lead_type",
    required=True,
    type=click.Choice(["studio", "sponsor"]),
    help="studio = music studio client | sponsor = YouTube sponsorship",
)
@click.option("--name", "-n", required=True, help="Prospect/brand name")
@click.option("--genre", default="", help="Music genre (for studio leads)")
@click.option("--followers", default="", help="Social media following size")
@click.option("--industry", default="", help="Industry (for sponsorship leads)")
@click.option(
    "--channel",
    default="history_channel",
    type=click.Choice(["history_channel", "finance_channel"]),
    help="Which channel to pitch for (sponsor only)",
)
def leads(lead_type: str, name: str, genre: str, followers: str, industry: str, channel: str):
    """
    Generate sales outreach sequences.

    For music studio: cold email sequence to book recording clients.
    For sponsors: YouTube sponsorship pitch package.

    Outputs saved to outputs/leads/
    """
    orch = get_orchestrator()
    if lead_type == "studio":
        prospect = {"name": name, "genre": genre, "followers": followers}
        result = orch.studio_outreach(prospect)
    else:
        brand_info = {"name": name, "industry": industry}
        result = orch.sponsorship_pitch(brand_info, channel=channel)
    console.print(result)


# ------------------------------------------------------------------ #
#  MARKETING CONTENT                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--brand", "-b",
    required=True,
    type=click.Choice(["history_channel", "finance_channel", "music_studio", "shopify_store"]),
    help="Which brand to create content for",
)
@click.option("--topic", "-t", required=True, help="Content topic or angle")
@click.option(
    "--type", "content_type",
    default="social",
    type=click.Choice(["social", "email", "ads"]),
    show_default=True,
    help="Type of content to generate",
)
def market(brand: str, topic: str, content_type: str):
    """
    Generate marketing content for any brand.

    social = Social media bundle (all platforms)
    email  = Full email newsletter
    ads    = Ad copy variations

    Outputs saved to outputs/marketing/
    """
    orch = get_orchestrator()
    if content_type == "social":
        result = orch.marketing_agent.create_social_bundle(brand, topic)
    elif content_type == "email":
        result = orch.marketing_agent.write_email_newsletter(brand, topic)
    else:
        result = orch.marketing_agent.write_ad_copy(brand, topic)
    console.print(result)


# ------------------------------------------------------------------ #
#  ALPACA PAPER TRADING                                                #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--action", "-a",
    default="overview",
    type=click.Choice(["overview", "analyze", "execute"]),
    show_default=True,
    help="overview = account snapshot | analyze = research a ticker | execute = place a trade",
)
@click.option("--symbol", "-s", default="", help="Ticker symbol (for analyze)")
@click.option(
    "--instruction", "-i",
    default="",
    help='Natural-language trade (for execute), e.g. "Buy $500 of AAPL at market"',
)
def trade(action: str, symbol: str, instruction: str):
    """
    Operate your Alpaca PAPER trading account (simulated money, real data).

    Requires ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env.

    \b
    python main.py trade --action overview
    python main.py trade --action analyze --symbol AAPL
    python main.py trade --action execute --instruction "Buy $500 of AAPL at market"
    """
    orch = get_orchestrator()
    try:
        if action == "overview":
            result = orch.trading_overview()
        elif action == "analyze":
            if not symbol:
                console.print("[bold red]--symbol is required for analyze[/bold red]")
                sys.exit(1)
            result = orch.trading_analyze(symbol)
        else:  # execute
            if not instruction:
                console.print("[bold red]--instruction is required for execute[/bold red]")
                sys.exit(1)
            result = orch.trading_execute(instruction)
        console.print(result)
    except EnvironmentError as e:
        console.print(f"[bold red]Alpaca Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--symbols", "-s",
    required=True,
    help='Comma-separated watchlist, e.g. "AAPL,MSFT,SPY,NVDA"',
)
@click.option(
    "--interval", "-i",
    default=15,
    show_default=True,
    help="Minutes between cycles (ignored with --once)",
)
@click.option(
    "--cash-per-trade",
    default=5000.0,
    show_default=True,
    help="Max dollars to spend per buy",
)
@click.option(
    "--max-positions",
    default=5,
    show_default=True,
    help="Max concurrent open positions",
)
@click.option("--short-window", default=20, show_default=True, help="Short SMA window")
@click.option("--long-window", default=50, show_default=True, help="Long SMA window")
@click.option("--once", is_flag=True, help="Run a single cycle instead of looping")
@click.option("--dry-run", is_flag=True, help="Log decisions without placing orders")
@click.option(
    "--llm-review",
    is_flag=True,
    help="Have Claude sanity-check (and veto risky) trades each cycle before placing them",
)
def autotrade(symbols, interval, cash_per_trade, max_positions, short_window, long_window, once, dry_run, llm_review):
    """
    Run the automated paper-trading loop (SMA-crossover momentum strategy).

    Deterministic and rule-based — safe to leave running on your paper account.
    Requires ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY in .env (paper only).

    \b
    python main.py autotrade --symbols AAPL,MSFT,SPY --interval 15
    python main.py autotrade --symbols AAPL,MSFT --once --dry-run
    """
    orch = get_orchestrator()
    symbol_list = [s for s in symbols.split(",") if s.strip()]
    try:
        orch.run_auto_trader(
            symbols=symbol_list,
            interval_minutes=interval,
            cash_per_trade=cash_per_trade,
            max_positions=max_positions,
            short_window=short_window,
            long_window=long_window,
            once=once,
            dry_run=dry_run,
            llm_review=llm_review,
        )
    except (EnvironmentError, ValueError) as e:
        console.print(f"[bold red]Auto-Trader Error:[/bold red] {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
#  CONTENT CALENDAR                                                    #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--weeks", "-w",
    default=4,
    show_default=True,
    help="Number of weeks to plan",
)
def ideas(weeks: int):
    """
    Generate a content ideas calendar for all YouTube channels.

    Outputs video ideas for both history and finance channels.
    Outputs saved to outputs/scripts/
    """
    orch = get_orchestrator()
    result = orch.generate_content_calendar(weeks=weeks)
    console.print("\n[bold]HISTORY CHANNEL IDEAS[/bold]")
    console.print(result["history_channel_ideas"])
    console.print("\n[bold]FINANCE CHANNEL IDEAS[/bold]")
    console.print(result["finance_channel_ideas"])


if __name__ == "__main__":
    cli()
