"""
Central configuration — all tuneable constants live here.
Alpaca credentials are loaded from .env (never hardcoded).
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Alpaca ────────────────────────────────────────────────────────────────────
ALPACA_API_KEY    = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_PAPER      = os.getenv("ALPACA_PAPER", "true").lower() != "false"

ALPACA_BASE_URL = (
    "https://paper-api.alpaca.markets" if ALPACA_PAPER
    else "https://api.alpaca.markets"
)
ALPACA_DATA_URL  = "https://data.alpaca.markets"
ALPACA_STREAM_URL = (
    "wss://stream.data.alpaca.markets/v2/iex" if ALPACA_PAPER
    else "wss://stream.data.alpaca.markets/v2/sip"
)

# ── Capital & risk ────────────────────────────────────────────────────────────
INITIAL_CAPITAL       = 100_000.0
RISK_PER_TRADE        = 0.02        # 2 % of equity per trade
MAX_POSITIONS         = 10
MAX_PORTFOLIO_HEAT    = 0.20        # max 20 % of equity at risk at once
COMMISSION_RATE       = 0.0         # Alpaca is commission-free
SLIPPAGE_BPS          = 2           # 2 basis points simulated slippage
DEFAULT_STOP_LOSS_PCT  = 0.05
DEFAULT_TAKE_PROFIT_PCT = 0.15

# ── Strategy defaults ─────────────────────────────────────────────────────────
MOMENTUM_FAST_EMA  = 12
MOMENTUM_SLOW_EMA  = 26
MOMENTUM_LOOKBACK  = 20
RSI_PERIOD         = 14
RSI_OVERSOLD       = 30
RSI_OVERBOUGHT     = 70
BB_PERIOD          = 20
BB_STD             = 2.0
MACD_FAST          = 12
MACD_SLOW          = 26
MACD_SIGNAL        = 9

# ── Optimiser ─────────────────────────────────────────────────────────────────
WALK_FORWARD_FOLDS   = 5
WALK_FORWARD_TRAIN_RATIO = 0.7
MONTE_CARLO_RUNS     = 1000

# ── Data ──────────────────────────────────────────────────────────────────────
DEFAULT_INTERVAL     = "1d"
CACHE_EXPIRY_HOURS   = 24.0
DATA_CACHE_DIR       = str(Path(__file__).parent / "data_cache")
DEFAULT_TICKER       = "SPY"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL       = logging.INFO
LOG_FORMAT      = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOGS_DIR        = str(Path(__file__).parent / "logs")
Path(LOGS_DIR).mkdir(exist_ok=True)
Path(DATA_CACHE_DIR).mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)
