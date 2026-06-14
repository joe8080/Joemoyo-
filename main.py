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
    default=1000.0,
    show_default=True,
    help="Max dollars to spend per buy",
)
@click.option(
    "--budget",
    default=5000.0,
    show_default=True,
    help="Total capital the bot may deploy across all positions (0 = no cap)",
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
@click.option(
    "--enter-on-trend",
    is_flag=True,
    help="Also enter when already in an uptrend (and exit in a downtrend), "
         "instead of trading only on the exact crossover bar",
)
@click.option(
    "--confirm-volume",
    is_flag=True,
    help="Only take crossover buys that fire on >=1.5x average volume "
         "(experimental — backtests showed it reduces returns on mega-caps)",
)
@click.option(
    "--market-filter",
    is_flag=True,
    help="Block new buys while SPY's short SMA is below its long SMA "
         "(experimental — backtests showed it reduces returns 2022-2026)",
)
@click.option("--timeframe", default="1Day", show_default=True,
              help="Bar size for signals: 1Day, 1Hour, 15Min, 5Min, 1Min")
@click.option("--stop-loss-pct", default=0.0, show_default=True,
              help="Exit a position if it falls this %% below entry (0 = off)")
@click.option("--take-profit-pct", default=0.0, show_default=True,
              help="Exit a position if it rises this %% above entry (0 = off)")
@click.option("--trailing-stop-pct", default=0.0, show_default=True,
              help="Exit if price falls this %% below its peak since entry (0 = off)")
@click.option("--flatten-eod", is_flag=True,
              help="Close all positions ~5 min before the close (intraday mode)")
@click.option("--daily-loss-limit", default=0.0, show_default=True,
              help="Stop opening new trades once the day's loss hits this $ amount (0 = off)")
@click.option("--mode", default="swing", show_default=True,
              help="Tag for the trade log: swing or intraday")
@click.option("--dry-run", is_flag=True, help="Log decisions without placing orders")
@click.option(
    "--llm-review",
    is_flag=True,
    help="Have Claude sanity-check (and veto risky) trades each cycle before placing them",
)
def autotrade(symbols, interval, cash_per_trade, budget, max_positions, short_window, long_window, once, enter_on_trend, confirm_volume, market_filter, timeframe, stop_loss_pct, take_profit_pct, trailing_stop_pct, flatten_eod, daily_loss_limit, mode, dry_run, llm_review):
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
            budget=budget,
            short_window=short_window,
            long_window=long_window,
            once=once,
            enter_on_trend=enter_on_trend,
            confirm_volume=confirm_volume,
            market_filter=market_filter,
            timeframe=timeframe,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            trailing_stop_pct=trailing_stop_pct,
            flatten_eod=flatten_eod,
            daily_loss_limit=daily_loss_limit,
            mode=mode,
            dry_run=dry_run,
            llm_review=llm_review,
        )
    except (EnvironmentError, ValueError) as e:
        console.print(f"[bold red]Auto-Trader Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--symbols", "-s",
              default="SPY,QQQ,AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,AMD",
              show_default=True, help="Watchlist to validate")
@click.option("--start", default="2022-01-01", show_default=True,
              help="History start date for the battery")
def validate(symbols, start):
    """
    Battle-test the live config: walk-forward (out-of-sample) windows, market
    regimes, and a parameter-robustness sweep. Read-only — places no orders.
    """
    from tools.alpaca_client import AlpacaClient
    from tools import validate as V
    from rich.table import Table

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    try:
        client = AlpacaClient()
    except EnvironmentError as e:
        console.print(f"[bold red]Alpaca Error:[/bold red] {e}")
        sys.exit(1)

    console.print(f"[dim]Fetching daily history since {start} for "
                  f"{len(symbol_list)} symbols...[/dim]")
    bars = {}
    for s in symbol_list:
        try:
            bars[s] = client.fetch_bars(s, "1Day", start=start)
        except RuntimeError as e:
            console.print(f"[yellow]{s}: {e} — skipped[/yellow]")
    if not bars:
        console.print("[bold red]No history fetched.[/bold red]")
        sys.exit(1)

    def _table(title, rows, cols):
        t = Table(title=title)
        for c in cols:
            t.add_column(c, justify="right")
        for r in rows:
            t.add_row(*(str(r.get(c, "")) for c in cols))
        console.print(t)

    wf = V.walk_forward(bars, test_days=90)
    _table("Walk-forward (90-day out-of-sample windows)", wf,
           ["window", "return_pct", "buyhold_pct", "max_dd_pct", "sharpe", "trades", "win_pct"])
    s = V.summarize(wf)
    if s:
        console.print(f"  [bold]Consistency:[/bold] {s['positive_windows']}/{s['windows']} "
                      f"windows positive · avg {s['avg']}% · range {s['min']}%..{s['max']}%\n")

    regimes = {
        "2022 bear": ("2022-01-01", "2022-12-31"),
        "2023-24 bull": ("2023-01-01", "2024-12-31"),
        "recent": ("2025-01-01", "2026-12-31"),
    }
    _table("Regime slices", V.regime_test(bars, regimes),
           ["window", "return_pct", "buyhold_pct", "max_dd_pct", "sharpe", "trades", "win_pct"])

    sweep = V.param_sweep(bars, short_windows=[10, 20, 30],
                          long_windows=[40, 50, 60], trails=[6, 8, 10, 12])
    _table("Parameter robustness (top 12 by Sharpe)", sweep[:12],
           ["short", "long", "trail", "return_pct", "max_dd_pct", "sharpe", "trades"])
    console.print("[dim]A broad cluster of similar Sharpes around the live config "
                  "(20/50, trail 8) = robust, not overfit.[/dim]")


@cli.command()
@click.option("--symbols", "-s",
              default="SPY,QQQ,AAPL,MSFT,NVDA,GOOGL,AMZN,META,TSLA,AMD",
              show_default=True, help="The engine's watchlist")
@click.option("--budget", default=50000.0, show_default=True, help="Engine budget")
@click.option("--start", default="2026-06-15", show_default=True,
              help="Campaign start date (for day count)")
def scorecard(symbols, budget, start):
    """
    Evaluate the strategy against its PASS/FAIL criteria (see docs/STRATEGY.md)
    and print the verdict: PASS / WATCH / FAIL / IN PROGRESS.
    """
    from tools.alpaca_client import AlpacaClient
    from tools import scorecard as SC
    from rich.table import Table
    try:
        client = AlpacaClient()
    except EnvironmentError as e:
        console.print(f"[bold red]Alpaca Error:[/bold red] {e}")
        sys.exit(1)
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    inputs = SC.build_inputs(client, budget=budget, symbols=syms, start_date=start)
    card = SC.evaluate(**inputs)
    color = {"PASS": "green", "WATCH": "yellow", "FAIL": "red",
             "IN PROGRESS": "cyan"}.get(card["verdict"], "white")
    console.print(Panel(f"[bold]{card['verdict']}[/bold] — {card['summary']}",
                        style=color, title="Strategy Scorecard"))
    if card["criteria"]:
        t = Table()
        for c in ("criterion", "target", "actual", "pass"):
            t.add_column(c)
        for c in card["criteria"]:
            t.add_row(c["criterion"], c["target"], str(c["actual"]),
                      "✅" if c["pass"] else "❌")
        console.print(t)


@cli.command()
def coach():
    """
    Generate the trading-journal coach report from the account's trade history.

    Builds the round-trip ledger from Alpaca order history, computes performance
    stats, and asks Claude for a coach note + recurring tendencies. Writes
    coach_<date>.md, tendencies.json, and ledger.json under outputs/reports/.
    Run on the close (the daily-close workflow does this automatically).
    """
    from tools.alpaca_client import AlpacaClient
    from agents.coach import generate_coach_report
    import os as _os
    try:
        client = AlpacaClient()
    except EnvironmentError as e:
        console.print(f"[bold red]Alpaca Error:[/bold red] {e}")
        sys.exit(1)
    orders = client.simplify_orders(client.get_orders(status="all", limit=500))
    from config.settings import settings as _settings
    reports_dir = _os.path.join(_settings.output_dir, "reports")
    result = generate_coach_report(orders, reports_dir)
    st = result["stats"]
    console.print(Panel(
        f"[bold]Coach report[/bold]\n"
        f"Closed trades: {st.get('num_trades', 0)} · "
        f"Win rate: {st.get('win_rate_pct', 'n/a')}% · "
        f"Total P&L: ${st.get('total_pnl', 0):,.2f}\n\n{result['note']}",
        style="cyan",
    ))
    for t in result["tendencies"]:
        console.print(f"  • {t}")


@cli.command()
@click.option(
    "--symbols", "-s",
    required=True,
    help='Comma-separated watchlist, e.g. "AAPL,MSFT,SPY,NVDA"',
)
@click.option("--days", default=365, show_default=True, help="History length in calendar days")
@click.option("--budget", default=5000.0, show_default=True, help="Starting capital")
@click.option("--cash-per-trade", default=1000.0, show_default=True, help="Max dollars per buy")
@click.option("--max-positions", default=5, show_default=True, help="Max concurrent positions")
@click.option("--short-window", default=20, show_default=True, help="Short SMA window")
@click.option("--long-window", default=50, show_default=True, help="Long SMA window")
def backtest(symbols, days, budget, cash_per_trade, max_positions, short_window, long_window):
    """
    Backtest the AutoTrader's SMA-crossover strategy on historical data.

    Replays the exact signal and sizing rules the live bot uses, so you can
    see what the bot would have done before giving it real (paper) capital.

    \b
    python main.py backtest --symbols SPY,QQQ,AAPL --days 365 --budget 5000
    """
    from tools.alpaca_client import AlpacaClient
    from tools.backtest import run_backtest

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    try:
        client = AlpacaClient()
    except EnvironmentError as e:
        console.print(f"[bold red]Alpaca Error:[/bold red] {e}")
        sys.exit(1)

    # Extra history so the long SMA is warmed up before the test window starts.
    bars_by_symbol = {}
    for sym in symbol_list:
        try:
            bars_by_symbol[sym] = client.get_bars(sym, timeframe="1Day",
                                                  days_back=days + long_window * 2)
        except RuntimeError as e:
            console.print(f"[yellow]{sym}: could not fetch bars ({e}) — skipped.[/yellow]")
    if not bars_by_symbol:
        console.print("[bold red]No bar data for any symbol — nothing to backtest.[/bold red]")
        sys.exit(1)

    result = run_backtest(
        bars_by_symbol,
        budget=budget,
        cash_per_trade=cash_per_trade,
        max_positions=max_positions,
        short_window=short_window,
        long_window=long_window,
    )
    m = result["metrics"]

    from rich.table import Table
    table = Table(title=f"Backtest — SMA {short_window}/{long_window} on "
                        f"{', '.join(bars_by_symbol)} ({m['trading_days']} trading days)")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Starting budget", f"${m['starting_budget']:,.2f}")
    table.add_row("Final equity", f"${m['final_equity']:,.2f}")
    table.add_row("Strategy return", f"{m['total_return_pct']:+.2f}%")
    table.add_row("Buy & hold return", f"{m['buy_hold_return_pct']:+.2f}%")
    table.add_row("Max drawdown", f"{m['max_drawdown_pct']:.2f}%")
    table.add_row("Sharpe (annualized)", str(m["sharpe"]) if m["sharpe"] is not None else "n/a")
    table.add_row("Closed trades", str(m["num_trades"]))
    table.add_row("Win rate", f"{m['win_rate_pct']}%" if m["win_rate_pct"] is not None else "n/a")
    table.add_row("Realized P&L", f"${m['realized_pnl']:,.2f}")
    table.add_row("Unrealized P&L (open)", f"${m['unrealized_pnl']:,.2f}")
    console.print(table)

    if result["trades"]:
        trades_table = Table(title="Closed trades")
        for col in ("symbol", "qty", "entry_date", "entry", "exit_date", "exit", "pnl", "pnl_pct"):
            trades_table.add_column(col, justify="right")
        for t in result["trades"]:
            trades_table.add_row(*(str(t[c]) for c in
                                   ("symbol", "qty", "entry_date", "entry",
                                    "exit_date", "exit", "pnl", "pnl_pct")))
        console.print(trades_table)


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
