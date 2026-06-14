"""
Trading bot CLI. Paper trading only.

    python main.py overview                      # account snapshot
    python main.py autotrade --symbols SPY,QQQ --once --dry-run
    python main.py backtest  --symbols SPY,QQQ --days 365
    python main.py validate                      # walk-forward / regime / sweep
    python main.py coach                         # journal + AI coach report
    python main.py scorecard                     # PASS / WATCH / FAIL verdict
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def cli():
    """Automated paper-trading bot."""


@cli.command()
def overview():
    """Print account equity, buying power, and open positions."""
    from tools.alpaca_client import AlpacaClient
    c = AlpacaClient()
    a = c.account_summary()
    console.print(Panel(
        f"Equity ${a.get('equity'):,.2f} · Cash ${a.get('cash'):,.2f} · "
        f"Buying power ${a.get('buying_power'):,.2f}", title="Account"))
    pos = c.simplify_positions(c.get_positions())
    if pos:
        t = Table()
        for col in ("symbol", "qty", "avg_entry_price", "current_price", "unrealized_pl"):
            t.add_column(col, justify="right")
        for p in pos:
            t.add_row(*(str(p.get(col)) for col in
                        ("symbol", "qty", "avg_entry_price", "current_price", "unrealized_pl")))
        console.print(t)


@cli.command()
@click.option("--symbols", "-s", required=True, help="Comma-separated watchlist")
@click.option("--interval", default=30, show_default=True, help="Minutes between cycles")
@click.option("--budget", default=50000.0, show_default=True, help="Total capital the bot may deploy")
@click.option("--cash-per-trade", default=5000.0, show_default=True)
@click.option("--max-positions", default=10, show_default=True)
@click.option("--short-window", default=20, show_default=True)
@click.option("--long-window", default=50, show_default=True)
@click.option("--timeframe", default="1Day", show_default=True, help="1Day, 1Hour, 15Min, 5Min, 1Min")
@click.option("--enter-on-trend", is_flag=True, help="Enter existing uptrends, not just fresh crosses")
@click.option("--trailing-stop-pct", default=0.0, show_default=True)
@click.option("--stop-loss-pct", default=0.0, show_default=True)
@click.option("--take-profit-pct", default=0.0, show_default=True)
@click.option("--flatten-eod", is_flag=True, help="Close all positions near the bell (intraday)")
@click.option("--daily-loss-limit", default=0.0, show_default=True)
@click.option("--mode", default="swing", show_default=True, help="swing | intraday (log tag)")
@click.option("--once", is_flag=True, help="One cycle instead of looping")
@click.option("--dry-run", is_flag=True, help="Log decisions without placing orders")
def autotrade(symbols, interval, budget, cash_per_trade, max_positions, short_window,
              long_window, timeframe, enter_on_trend, trailing_stop_pct, stop_loss_pct,
              take_profit_pct, flatten_eod, daily_loss_limit, mode, once, dry_run):
    """Run the automated SMA-crossover paper-trading loop."""
    from agents.auto_trader import AutoTrader
    syms = [s.strip() for s in symbols.split(",") if s.strip()]
    try:
        trader = AutoTrader(
            symbols=syms, interval_minutes=interval, budget=budget,
            cash_per_trade=cash_per_trade, max_positions=max_positions,
            short_window=short_window, long_window=long_window, timeframe=timeframe,
            enter_on_trend=enter_on_trend, trailing_stop_pct=trailing_stop_pct,
            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
            flatten_eod=flatten_eod, daily_loss_limit=daily_loss_limit, mode=mode,
            dry_run=dry_run,
        )
        trader.run_once() if once else trader.run_forever()
    except (EnvironmentError, ValueError) as e:
        console.print(f"[bold red]Auto-Trader Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--symbols", "-s", required=True)
@click.option("--days", default=365, show_default=True)
@click.option("--budget", default=50000.0, show_default=True)
@click.option("--cash-per-trade", default=5000.0, show_default=True)
@click.option("--max-positions", default=10, show_default=True)
@click.option("--short-window", default=20, show_default=True)
@click.option("--long-window", default=50, show_default=True)
@click.option("--trailing-stop-pct", default=8.0, show_default=True)
def backtest(symbols, days, budget, cash_per_trade, max_positions, short_window,
             long_window, trailing_stop_pct):
    """Replay the strategy over historical bars."""
    from tools.alpaca_client import AlpacaClient
    from tools.backtest import run_backtest
    c = AlpacaClient()
    bars = {}
    for s in [x.strip() for x in symbols.split(",") if x.strip()]:
        bars[s] = c.get_bars(s, "1Day", days_back=days + long_window * 2)
    r = run_backtest(bars, budget=budget, cash_per_trade=cash_per_trade,
                     max_positions=max_positions, short_window=short_window,
                     long_window=long_window, enter_on_trend=True,
                     trailing_stop_pct=trailing_stop_pct)
    m = r["metrics"]
    t = Table(title="Backtest")
    t.add_column("metric"); t.add_column("value", justify="right")
    for k in ("total_return_pct", "buy_hold_return_pct", "max_drawdown_pct",
              "sharpe", "num_trades", "win_rate_pct"):
        t.add_row(k, str(m[k]))
    console.print(t)


@cli.command()
@click.option("--symbols", "-s", default="SPY,QQQ,AAPL,MSFT,NVDA", show_default=True)
@click.option("--start", default="2022-01-01", show_default=True)
def validate(symbols, start):
    """Walk-forward, regime, and parameter-robustness battery (read-only)."""
    from tools.alpaca_client import AlpacaClient
    from tools import validate as V
    c = AlpacaClient()
    bars = {s.strip(): c.fetch_bars(s.strip(), "1Day", start=start)
            for s in symbols.split(",") if s.strip()}
    rows = V.walk_forward(bars, test_days=90)
    t = Table(title="Walk-forward (90-day OOS windows)")
    for col in ("window", "return_pct", "buyhold_pct", "max_dd_pct", "sharpe", "trades", "win_pct"):
        t.add_column(col, justify="right")
    for r in rows:
        t.add_row(*(str(r.get(c2, "")) for c2 in
                    ("window", "return_pct", "buyhold_pct", "max_dd_pct", "sharpe", "trades", "win_pct")))
    console.print(t)
    s = V.summarize(rows)
    if s:
        console.print(f"Consistency: {s['positive_windows']}/{s['windows']} windows "
                      f"positive · avg {s['avg']}%")


@cli.command()
def coach():
    """Generate the journal coach report (ledger, note, tendencies)."""
    import os
    from tools.alpaca_client import AlpacaClient
    from agents.coach import generate_coach_report
    from config.settings import settings
    c = AlpacaClient()
    orders = c.simplify_orders(c.get_orders(status="all", limit=500))
    res = generate_coach_report(orders, os.path.join(settings.output_dir, "reports"))
    console.print(Panel(res["note"], title="Coach"))


@cli.command()
@click.option("--symbols", "-s", default="SPY,QQQ,AAPL,MSFT,NVDA", show_default=True)
@click.option("--budget", default=50000.0, show_default=True)
@click.option("--start", default="2026-01-01", show_default=True, help="Campaign start date")
def scorecard(symbols, budget, start):
    """Evaluate the strategy against its PASS/FAIL criteria."""
    from tools.alpaca_client import AlpacaClient
    from tools import scorecard as SC
    c = AlpacaClient()
    syms = [s.strip() for s in symbols.split(",") if s.strip()]
    card = SC.evaluate(**SC.build_inputs(c, budget=budget, symbols=syms, start_date=start))
    color = {"PASS": "green", "WATCH": "yellow", "FAIL": "red", "IN PROGRESS": "cyan"}
    console.print(Panel(f"[bold]{card['verdict']}[/bold] — {card['summary']}",
                        style=color.get(card["verdict"], "white"), title="Scorecard"))
    for cr in card["criteria"]:
        console.print(f"  {'✅' if cr['pass'] else '❌'} {cr['criterion']}: "
                      f"{cr['actual']} (target {cr['target']})")


if __name__ == "__main__":
    cli()
