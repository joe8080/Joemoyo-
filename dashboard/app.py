"""
JoeMoyo Trading Dashboard — live view of the Alpaca paper account and the
AutoTrader strategy.

Run with:
    streamlit run dashboard/app.py

Shows account equity/cash/buying power, the equity curve, open positions,
recent orders, per-symbol SMA crossover charts (the exact signal the
AutoTrader trades on), and the tail of today's auto-trader log.
Auto-refreshes on an interval you pick in the sidebar.
"""

import glob
import os
import sys
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Allow `streamlit run dashboard/app.py` from the repo root or anywhere else.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# On Streamlit Community Cloud credentials arrive via st.secrets, not .env.
# Mirror them into the environment before config.settings reads it.
try:
    for _key in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY", "ALPACA_PAPER"):
        if _key not in os.environ and _key in st.secrets:
            os.environ[_key] = str(st.secrets[_key])
except FileNotFoundError:
    pass  # no secrets.toml — running locally off .env
# The dashboard never calls Anthropic; don't let settings' key check kill it.
os.environ.setdefault("ANTHROPIC_API_KEY", "unused-by-dashboard")

from config.settings import settings  # noqa: E402
from tools.alpaca_client import AlpacaClient  # noqa: E402
from tools.backtest import run_backtest  # noqa: E402
from tools.strategies import sma_crossover_signal  # noqa: E402

st.set_page_config(
    page_title="JoeMoyo Trading Dashboard",
    page_icon="📈",
    layout="wide",
)

DEFAULT_WATCHLIST = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
SHORT_WINDOW = 20
LONG_WINDOW = 50


# --------------------------------------------------------------------- #
#  Data access (cached)                                                  #
# --------------------------------------------------------------------- #

@st.cache_resource
def get_client() -> AlpacaClient:
    return AlpacaClient()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_snapshot():
    """One bundle of everything the dashboard needs, cached for 30s."""
    c = get_client()
    account = c.account_summary()
    positions = c.simplify_positions(c.get_positions())
    open_orders = c.simplify_orders(c.get_orders(status="open"))
    closed_orders = c.simplify_orders(c.get_orders(status="closed", limit=25))
    clock = c.get_clock()
    try:
        history = c.get_portfolio_history(period="1M", timeframe="1D")
    except RuntimeError:
        history = {}
    return account, positions, open_orders, closed_orders, clock, history


@st.cache_data(ttl=120, show_spinner=False)
def fetch_bars(symbol: str) -> list[dict]:
    return get_client().get_bars(symbol, timeframe="1Day", days_back=LONG_WINDOW * 3 + 10)


def latest_log_path() -> str | None:
    logs = sorted(glob.glob(os.path.join(settings.output_dir, "reports", "autotrade_log_*.md")))
    return logs[-1] if logs else None


# --------------------------------------------------------------------- #
#  Charts                                                                #
# --------------------------------------------------------------------- #

def equity_curve_chart(history: dict) -> go.Figure | None:
    stamps = history.get("timestamp") or []
    equity = history.get("equity") or []
    points = [(datetime.fromtimestamp(t), e) for t, e in zip(stamps, equity) if e is not None]
    if len(points) < 2:
        return None
    df = pd.DataFrame(points, columns=["time", "equity"])
    fig = go.Figure(go.Scatter(x=df["time"], y=df["equity"], mode="lines", fill="tozeroy",
                               line=dict(color="#00b894")))
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                      yaxis_title="Equity ($)", xaxis_title=None)
    fig.update_yaxes(rangemode="normal")
    return fig


def symbol_chart(symbol: str, bars: list[dict]) -> go.Figure:
    df = pd.DataFrame(bars)
    df["sma_short"] = df["close"].rolling(SHORT_WINDOW).mean()
    df["sma_long"] = df["close"].rolling(LONG_WINDOW).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["t"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name=symbol, showlegend=False,
    ))
    fig.add_trace(go.Scatter(x=df["t"], y=df["sma_short"], name=f"SMA {SHORT_WINDOW}",
                             line=dict(color="#0984e3", width=1.5)))
    fig.add_trace(go.Scatter(x=df["t"], y=df["sma_long"], name=f"SMA {LONG_WINDOW}",
                             line=dict(color="#e17055", width=1.5)))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.05))
    return fig


# --------------------------------------------------------------------- #
#  Sidebar                                                               #
# --------------------------------------------------------------------- #

st.sidebar.title("📈 JoeMoyo Trading")

watchlist_input = st.sidebar.text_input(
    "Watchlist (comma-separated)", ", ".join(DEFAULT_WATCHLIST)
)
watchlist = [s.strip().upper() for s in watchlist_input.split(",") if s.strip()]

refresh_secs = st.sidebar.slider(
    "Auto-refresh every (seconds)", 0, 300,
    int(os.getenv("DASHBOARD_REFRESH_SECS", "60")),
    help="0 disables auto-refresh.",
)
if st.sidebar.button("🔄 Refresh now", width="stretch"):
    fetch_snapshot.clear()
    fetch_bars.clear()
    st.rerun()

# --------------------------------------------------------------------- #
#  Main page                                                             #
# --------------------------------------------------------------------- #

try:
    account, positions, open_orders, closed_orders, clock, history = fetch_snapshot()
except Exception as e:
    st.error(f"Could not reach Alpaca: {e}")
    st.stop()

mode = "🧪 PAPER" if get_client().paper else "🔴 LIVE"
market = "🟢 Market OPEN" if clock.get("is_open") else "🔴 Market CLOSED"
next_event = clock.get("next_close") if clock.get("is_open") else clock.get("next_open")

st.title("Trading System Dashboard")
st.caption(
    f"{mode} account · {market} · next {'close' if clock.get('is_open') else 'open'}: "
    f"{(next_event or '?')[:16].replace('T', ' ')} · "
    f"last refreshed {datetime.now().strftime('%H:%M:%S')}"
)

if account.get("trading_blocked") or account.get("account_blocked"):
    st.error("⚠️ This account is BLOCKED from trading — check your Alpaca dashboard.")

# --- Headline metrics -------------------------------------------------- #
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Equity", f"${account['equity']:,.2f}",
          delta=f"${account['todays_pl']:,.2f} today")
c2.metric("Cash", f"${account['cash']:,.2f}")
c3.metric("Buying Power", f"${account['buying_power']:,.2f}")
total_unrealized = sum(p["unrealized_pl"] for p in positions)
c4.metric("Open P&L", f"${total_unrealized:,.2f}")
c5.metric("Positions", len(positions))

# --- Equity curve ------------------------------------------------------ #
st.subheader("Equity curve (1 month)")
curve = equity_curve_chart(history)
if curve:
    st.plotly_chart(curve, width="stretch")
else:
    st.info("Not enough account history yet — the curve appears after your first trading days.")

# --- Positions & orders ------------------------------------------------ #
left, right = st.columns(2)

with left:
    st.subheader("Open positions")
    if positions:
        dfp = pd.DataFrame(positions)
        dfp = dfp.rename(columns={
            "avg_entry_price": "entry", "current_price": "price",
            "market_value": "value", "unrealized_pl": "P&L $", "unrealized_plpc": "P&L %",
        })
        st.dataframe(dfp, width="stretch", hide_index=True)
    else:
        st.info("No open positions.")

with right:
    st.subheader("Open orders")
    if open_orders:
        st.dataframe(pd.DataFrame(open_orders).drop(columns=["id"]),
                     width="stretch", hide_index=True)
    else:
        st.info("No open orders.")

st.subheader("Recent filled / closed orders")
if closed_orders:
    st.dataframe(pd.DataFrame(closed_orders).drop(columns=["id"]),
                 width="stretch", hide_index=True)
else:
    st.info("No order history yet — the table fills in once the system starts trading.")

# --- Watchlist strategy view ------------------------------------------- #
st.subheader(f"Watchlist — SMA {SHORT_WINDOW}/{LONG_WINDOW} crossover (AutoTrader signal)")
held = {p["symbol"] for p in positions}
tabs = st.tabs(watchlist)
for tab, symbol in zip(tabs, watchlist):
    with tab:
        try:
            bars = fetch_bars(symbol)
        except Exception as e:
            st.warning(f"Could not load bars for {symbol}: {e}")
            continue
        if not bars:
            st.warning(f"No bar data for {symbol}.")
            continue
        signal = sma_crossover_signal(bars, short_window=SHORT_WINDOW, long_window=LONG_WINDOW)
        state = "HOLDING" if symbol in held else "flat"
        badge = {"buy": "🟢 BUY signal", "sell": "🔴 SELL signal"}.get(signal, "⚪ HOLD / no signal")
        st.markdown(f"**{badge}** · position: **{state}** · last close: "
                    f"**${bars[-1]['close']:,.2f}**")
        st.plotly_chart(symbol_chart(symbol, bars), width="stretch")

# --- Backtest ----------------------------------------------------------- #
st.subheader("Strategy backtest")
st.caption(
    "Replays the exact SMA-crossover signal and sizing rules the AutoTrader "
    "uses over historical data — fills at the signal bar's close, no slippage."
)
with st.form("backtest_form"):
    b1, b2, b3 = st.columns(3)
    bt_days = b1.slider("History (days)", 90, 1000, 365, step=5)
    bt_budget = b2.number_input("Budget ($)", 500.0, 1_000_000.0, 5000.0, step=500.0)
    bt_per_trade = b3.number_input("Cash per trade ($)", 100.0, 1_000_000.0, 1000.0, step=100.0)
    bt_regime = st.checkbox(
        "Regime mode (enter existing uptrends, don't wait for a fresh cross)", value=True,
    )
    run_bt = st.form_submit_button("▶ Run backtest on watchlist", width="stretch")

if run_bt:
    bt_bars = {}
    with st.spinner("Fetching history and replaying the strategy..."):
        for sym in watchlist:
            try:
                bt_bars[sym] = get_client().get_bars(
                    sym, timeframe="1Day", days_back=bt_days + LONG_WINDOW * 2
                )
            except Exception as e:
                st.warning(f"{sym}: could not fetch bars ({e}) — skipped.")
        if bt_bars:
            result = run_backtest(
                bt_bars, budget=bt_budget, cash_per_trade=bt_per_trade,
                short_window=SHORT_WINDOW, long_window=LONG_WINDOW,
                enter_on_trend=bt_regime,
            )
    if not bt_bars:
        st.error("No data to backtest.")
    else:
        m = result["metrics"]
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("Strategy return", f"{m['total_return_pct']:+.2f}%",
                  delta=f"{m['total_return_pct'] - m['buy_hold_return_pct']:+.2f}% vs buy&hold")
        r2.metric("Final equity", f"${m['final_equity']:,.2f}")
        r3.metric("Max drawdown", f"{m['max_drawdown_pct']:.2f}%")
        r4.metric("Trades / win rate",
                  f"{m['num_trades']} / {m['win_rate_pct'] or 0}%")
        r5.metric("Sharpe", m["sharpe"] if m["sharpe"] is not None else "n/a")

        dfe = pd.DataFrame(result["equity_curve"])
        fig = go.Figure(go.Scatter(x=dfe["date"], y=dfe["equity"], mode="lines",
                                   name="Strategy", line=dict(color="#6c5ce7")))
        fig.add_hline(y=bt_budget, line_dash="dot", line_color="gray",
                      annotation_text="starting budget")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title="Equity ($)")
        st.plotly_chart(fig, width="stretch")

        if result["trades"]:
            st.dataframe(pd.DataFrame(result["trades"]), width="stretch", hide_index=True)
        if result["open_positions"]:
            st.caption("Still open at the end of the test:")
            st.dataframe(pd.DataFrame(result["open_positions"]), width="stretch", hide_index=True)
        if not result["trades"] and not result["open_positions"]:
            st.info("The strategy produced no trades in this window — try a longer history.")

# --- AutoTrader activity log -------------------------------------------- #
st.subheader("AutoTrader activity log")
log_path = latest_log_path()
if log_path:
    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()
    st.caption(f"`{log_path}` — last {min(len(lines), 40)} entries")
    st.markdown("".join(lines[-40:]))
else:
    st.info("No auto-trader log yet. Start the bot with "
            "`python main.py autotrade` and its decisions will appear here.")

# --- Auto-refresh -------------------------------------------------------- #
if refresh_secs > 0:
    time.sleep(refresh_secs)
    fetch_snapshot.clear()
    st.rerun()
