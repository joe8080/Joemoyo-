"""
Joemoyo Trading Agent — CLI

Commands
--------
  backtest    Backtest a single strategy on historical data
  compare     Compare all strategies side-by-side
  paper       Run the self-improving agent in paper (no-risk) mode
  live        Connect to Alpaca and trade for real (paper or live account)
  account     Show your Alpaca account + open positions
  optimize    Grid-search strategy parameters

Examples
--------
  python main.py --demo compare --symbol AAPL --start 2022-01-01
  python main.py account
  python main.py live --symbols AAPL MSFT TSLA --start 2024-01-01
"""
from __future__ import annotations
import argparse, logging, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from trading_agent.agent import TradingAgent
from trading_agent.backtester.engine import BacktestEngine
from trading_agent.backtester.metrics import calculate_metrics
from trading_agent.data.fetcher import DataFetcher
from trading_agent.data.processor import DataProcessor
from trading_agent.strategies.momentum import MomentumStrategy
from trading_agent.strategies.mean_reversion import MeanReversionStrategy
from trading_agent.strategies.macd import MACDStrategy
from trading_agent.strategies.combined import CombinedStrategy

STRATEGY_REGISTRY = {
    "momentum":      MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "macd":          MACDStrategy,
    "combined":      CombinedStrategy,
}


# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool = False):
    log_path = Path(config.LOGS_DIR) / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    handlers = [logging.StreamHandler(sys.stdout), logging.FileHandler(log_path)]
    logging.basicConfig(
        level=logging.DEBUG if verbose else config.LOG_LEVEL,
        format=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT, handlers=handlers,
    )


# ── Data helpers ───────────────────────────────────────────────────────────────

def fetch_data(symbols: List[str], start: str, end: Optional[str] = None,
               demo: bool = False) -> Dict[str, pd.DataFrame]:
    fetcher = DataFetcher()
    proc    = DataProcessor()
    data    = {}
    for i, sym in enumerate(symbols):
        if demo:
            print(f"  [DEMO] Synthetic data for {sym}...")
            raw = fetcher.generate_synthetic(sym, start=start, end=end, seed=i * 7 + 42)
        else:
            print(f"  Fetching {sym}...")
            raw = fetcher.fetch(sym, start, end)
        if raw is None or raw.empty:
            print(f"  [WARN] No data for {sym}.")
            continue
        data[sym] = proc.clean(raw)
        print(f"  {sym}: {len(data[sym])} bars  "
              f"({data[sym].index[0].date()} → {data[sym].index[-1].date()})")
    return data


# ── Sub-commands ───────────────────────────────────────────────────────────────

def cmd_backtest(args):
    print(f"\n{'='*60}")
    print(f"  BACKTEST: {args.symbol.upper()}  |  Strategy: {args.strategy}")
    print(f"{'='*60}")
    data = fetch_data([args.symbol], args.start, args.end, demo=args.demo)
    sym  = args.symbol.upper()
    df   = data.get(sym) if data.get(sym) is not None else data.get(args.symbol)
    if df is None or df.empty:
        print("[ERROR] No data.")
        return

    strategy = STRATEGY_REGISTRY[args.strategy]()
    engine   = BacktestEngine(
        initial_capital=args.capital,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        allow_short=args.short,
    )
    result = engine.run(df, strategy, sym)
    m = result.metrics
    print(f"\n  Total Return:      {m.total_return:>8.1%}")
    print(f"  Annualised Return: {m.annualised_return:>8.1%}")
    print(f"  Sharpe Ratio:      {m.sharpe_ratio:>8.3f}")
    print(f"  Sortino Ratio:     {m.sortino_ratio:>8.3f}")
    print(f"  Max Drawdown:      {m.max_drawdown:>8.1%}")
    print(f"  Win Rate:          {m.win_rate:>8.1%}")
    print(f"  Total Trades:      {m.total_trades:>8}")
    print(f"  Profit Factor:     {m.profit_factor:>8.2f}")
    print(f"  VaR (95%%):         {m.var_95:>8.2%}")


def cmd_compare(args):
    print(f"\n{'='*60}")
    print(f"  STRATEGY COMPARISON: {args.symbol.upper()}")
    print(f"{'='*60}")
    data = fetch_data([args.symbol], args.start, args.end, demo=args.demo)
    sym  = args.symbol.upper()
    df   = data.get(sym) if data.get(sym) is not None else data.get(args.symbol)
    if df is None or df.empty:
        print("[ERROR] Could not fetch data.")
        return

    strategies = {
        "Momentum":     MomentumStrategy(),
        "MeanReversion": MeanReversionStrategy(),
        "MACD":         MACDStrategy(),
        "Combined":     CombinedStrategy(),
    }

    header = f"{'Strategy':<16} {'Total Ret':>10} {'Ann Ret':>8} {'Sharpe':>8} " \
             f"{'Sortino':>8} {'MaxDD':>7} {'WinRate':>8} {'Trades':>7}"
    print(f"\n{header}")
    print("-" * len(header))

    best_sharpe, best_name = -np.inf, ""
    engine = BacktestEngine(initial_capital=args.capital)
    for name, strat in strategies.items():
        res = engine.run(df, strat, sym)
        m   = res.metrics
        print(f"{name:<16} {m.total_return:>9.1%}  {m.annualised_return:>7.1%}  "
              f"{m.sharpe_ratio:>7.3f}  {m.sortino_ratio:>7.3f}  "
              f"{m.max_drawdown:>6.1%}  {m.win_rate:>7.1%}  {m.total_trades:>6}")
        if m.sharpe_ratio > best_sharpe:
            best_sharpe, best_name = m.sharpe_ratio, name

    print("-" * len(header))
    print(f"\n  Best strategy by Sharpe: {best_name} ({best_sharpe:.3f})")


def cmd_account(args):
    """Show Alpaca account info and open positions."""
    try:
        from trading_agent.broker.alpaca import AlpacaBroker
        broker = AlpacaBroker()
        print(broker.portfolio_summary())
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
        print("\nTo set up your Alpaca keys:")
        print("  1. Copy  .env.example  →  .env")
        print("  2. Add your API key and secret from https://app.alpaca.markets")
        print("  3. Set ALPACA_PAPER=true for paper trading (safe to test)")


def cmd_live(args):
    """
    Run the agent against your Alpaca account.
    Uses paper trading by default (ALPACA_PAPER=true in .env).
    """
    if not config.ALPACA_API_KEY:
        print("\n[ERROR] No Alpaca API key found.")
        print("  Copy .env.example → .env and add your keys.")
        return

    mode = "PAPER" if config.ALPACA_PAPER else "*** LIVE ***"
    print(f"\n{'='*60}")
    print(f"  ALPACA AGENT — {mode}")
    print(f"  Symbols: {', '.join(args.symbols)}")
    print(f"{'='*60}")

    # Show account first
    from trading_agent.broker.alpaca import AlpacaBroker
    broker = AlpacaBroker()
    print(broker.portfolio_summary())

    if not broker.is_market_open():
        print("\n[INFO] Market is currently closed. Signals will still be generated.")

    agent = TradingAgent(symbols=args.symbols, live=True)

    print(f"\nGenerating signals (start={args.start}) …\n")
    results = agent.run_once(start=args.start, demo=args.demo)

    print(f"\n{'Symbol':<10} {'Signal':>8} {'Confidence':>12} {'Regime':<16} Strategy Weights")
    print("-" * 70)
    for sym, info in results.items():
        sig_str = {1: "BUY", -1: "SELL", 0: "HOLD"}.get(info["signal"], "HOLD")
        w_str   = "  ".join(f"{k[:4]}={v:.2f}" for k, v in info["weights"].items())
        print(f"{sym:<10} {sig_str:>8} {info['confidence']:>11.1%}  {info['regime']:<16} {w_str}")

    if not config.ALPACA_PAPER and not args.demo:
        print("\n[WARNING] You are in LIVE trading mode. Orders have been submitted above.")
    elif config.ALPACA_PAPER:
        print("\n[INFO] Paper trading mode — no real money at risk.")

    print(f"\nRe-run this command periodically (e.g. every morning) to trade daily bars.")


def cmd_paper(args):
    """Self-improving agent in simulation — no Alpaca connection needed."""
    print(f"\n{'='*60}")
    print(f"  PAPER AGENT (simulation)")
    print(f"  Symbols: {', '.join(args.symbols)}")
    print(f"{'='*60}")
    agent   = TradingAgent(symbols=args.symbols, live=False)
    results = agent.run_once(start=args.start, demo=args.demo)

    print(f"\n{'Symbol':<10} {'Signal':>8} {'Confidence':>12} {'Regime'}")
    print("-" * 50)
    for sym, info in results.items():
        sig_str = {1: "BUY", -1: "SELL", 0: "HOLD"}.get(info["signal"], "HOLD")
        print(f"{sym:<10} {sig_str:>8} {info['confidence']:>11.1%}  {info['regime']}")


# ── Parser ─────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="joemoyo-trader",
        description="Joemoyo Python Trading Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--demo", action="store_true",
                        help="Use synthetic data — no internet required.")

    sub    = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--symbol", "-s", default="SPY")
    parent.add_argument("--start",  default=(datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"))
    parent.add_argument("--end",    default=None)
    parent.add_argument("--capital", type=float, default=config.INITIAL_CAPITAL)

    # backtest
    bt = sub.add_parser("backtest", parents=[parent])
    bt.add_argument("--strategy", default="momentum", choices=list(STRATEGY_REGISTRY))
    bt.add_argument("--stop-loss",   type=float, default=config.DEFAULT_STOP_LOSS_PCT, dest="stop_loss")
    bt.add_argument("--take-profit", type=float, default=config.DEFAULT_TAKE_PROFIT_PCT, dest="take_profit")
    bt.add_argument("--short", action="store_true")

    # compare
    sub.add_parser("compare", parents=[parent])

    # account
    sub.add_parser("account", help="Show Alpaca account and positions.")

    # live
    lv = sub.add_parser("live", help="Trade via Alpaca (paper or live).")
    lv.add_argument("--symbols", nargs="+", default=["SPY", "QQQ", "AAPL"])
    lv.add_argument("--start", default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))

    # paper sim
    pp = sub.add_parser("paper", help="Paper simulation (no Alpaca needed).")
    pp.add_argument("--symbols", nargs="+", default=["SPY", "QQQ", "AAPL"])
    pp.add_argument("--start", default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger("main")
    logger.info("Joemoyo Trading Agent — command: %s", args.command)

    dispatch = {
        "backtest": cmd_backtest,
        "compare":  cmd_compare,
        "account":  cmd_account,
        "live":     cmd_live,
        "paper":    cmd_paper,
    }
    try:
        dispatch[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as exc:
        logger.error("Command '%s' failed: %s", args.command, exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
