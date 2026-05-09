"""
Data fetcher — supports yfinance (fallback) and Alpaca Market Data API.
Falls back to synthetic GBM data when network is unavailable.
"""
from __future__ import annotations
import hashlib, logging, os, pickle, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

import config

logger = logging.getLogger("data.fetcher")


class DataFetcher:
    def __init__(self, cache_dir: Optional[str] = None,
                 cache_expiry_hours: float = config.CACHE_EXPIRY_HOURS):
        self.cache_dir = Path(cache_dir or config.DATA_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiry = cache_expiry_hours * 3600.0

    # ── Public ────────────────────────────────────────────────────────────

    def fetch(self, symbol: str, start: str, end: Optional[str] = None,
              interval: str = "1d", use_cache: bool = True) -> pd.DataFrame:
        end = end or datetime.now().strftime("%Y-%m-%d")
        key = self._cache_key(symbol, start, end, interval)
        if use_cache:
            cached = self._load_cache(key)
            if cached is not None:
                return cached

        # Try Alpaca first, then yfinance
        df = pd.DataFrame()
        if config.ALPACA_API_KEY:
            df = self._fetch_alpaca(symbol, start, end, interval)
        if df.empty:
            df = self._fetch_yfinance(symbol, start, end, interval)
        if df.empty:
            logger.warning("All fetchers failed for %s — using synthetic data.", symbol)
            df = self.generate_synthetic(symbol, start=start, end=end)

        if use_cache and not df.empty:
            self._save_cache(key, df)
        return df

    def fetch_multiple(self, symbols: List[str], start: str,
                       end: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        return {s: self.fetch(s, start, end) for s in symbols}

    # ── Alpaca market data ────────────────────────────────────────────────

    def _fetch_alpaca(self, symbol: str, start: str, end: str,
                      interval: str) -> pd.DataFrame:
        try:
            import requests
            tf_map = {"1d": "1Day", "1h": "1Hour", "15m": "15Min", "5m": "5Min", "1m": "1Min"}
            timeframe = tf_map.get(interval, "1Day")
            headers = {
                "APCA-API-KEY-ID":     config.ALPACA_API_KEY,
                "APCA-API-SECRET-KEY": config.ALPACA_SECRET_KEY,
            }
            params  = {"start": start, "end": end, "timeframe": timeframe, "limit": 10000}
            url     = f"{config.ALPACA_DATA_URL}/v2/stocks/{symbol}/bars"
            rows, token = [], None
            while True:
                if token:
                    params["page_token"] = token
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                if resp.status_code != 200:
                    logger.warning("Alpaca data API %s: %s", resp.status_code, resp.text[:200])
                    return pd.DataFrame()
                body  = resp.json()
                bars  = body.get("bars", [])
                rows.extend(bars)
                token = body.get("next_page_token")
                if not token:
                    break

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows)
            df.index = pd.to_datetime(df["t"]).dt.tz_localize(None)
            df.index.name = "Date"
            df = df.rename(columns={"o": "Open", "h": "High", "l": "Low",
                                     "c": "Close", "v": "Volume"})
            df = df[["Open", "High", "Low", "Close", "Volume"]].sort_index()
            logger.info("Alpaca: fetched %d bars for %s.", len(df), symbol)
            return df
        except Exception as exc:
            logger.warning("Alpaca fetch error for %s: %s", symbol, exc)
            return pd.DataFrame()

    # ── yfinance fallback ─────────────────────────────────────────────────

    def _fetch_yfinance(self, symbol: str, start: str, end: str,
                        interval: str) -> pd.DataFrame:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start, end=end, interval=interval,
                                auto_adjust=True, actions=False)
            if df.empty:
                return pd.DataFrame()
            if hasattr(df.index, "tz") and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df.columns = [c.strip() for c in df.columns]
            cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
            logger.info("yfinance: fetched %d bars for %s.", len(df), symbol)
            return df[cols].sort_index().dropna(how="all")
        except Exception as exc:
            logger.warning("yfinance fetch error for %s: %s", symbol, exc)
            return pd.DataFrame()

    # ── Synthetic fallback ────────────────────────────────────────────────

    @staticmethod
    def generate_synthetic(symbol: str = "DEMO", start: str = "2022-01-01",
                            end: Optional[str] = None, seed: int = 42,
                            annual_drift: float = 0.10, annual_vol: float = 0.20,
                            start_price: float = 150.0) -> pd.DataFrame:
        rng     = np.random.default_rng(seed)
        end_str = end or datetime.now().strftime("%Y-%m-%d")
        dates   = pd.bdate_range(start=start, end=end_str)
        n       = len(dates)
        dt      = 1 / 252
        mu, sig = annual_drift * dt, annual_vol * np.sqrt(dt)

        log_ret = rng.normal(mu - 0.5 * sig**2, sig, size=n)
        close   = start_price * np.exp(np.cumsum(log_ret))
        rng2    = close * annual_vol / np.sqrt(252) * rng.uniform(0.5, 2.0, n)
        high    = close + rng2 * rng.uniform(0.3, 0.7, n)
        low     = close - rng2 * rng.uniform(0.3, 0.7, n)
        open_   = low + (high - low) * rng.uniform(0.2, 0.8, n)
        volume  = rng.integers(1_000_000, 50_000_000, n).astype(float)

        df = pd.DataFrame({"Open": open_, "High": high, "Low": low,
                           "Close": close, "Volume": volume}, index=dates)
        df.index.name = "Date"
        logger.info("Generated %d synthetic bars for %s.", n, symbol)
        return df

    # ── Cache helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(symbol, start, end, interval):
        return hashlib.md5(f"{symbol}_{start}_{end}_{interval}".encode()).hexdigest()

    def _cache_path(self, key):
        return self.cache_dir / f"{key}.pkl"

    def _load_cache(self, key) -> Optional[pd.DataFrame]:
        p = self._cache_path(key)
        if not p.exists():
            return None
        if time.time() - p.stat().st_mtime > self.cache_expiry:
            return None
        try:
            with open(p, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def _save_cache(self, key, df: pd.DataFrame):
        try:
            with open(self._cache_path(key), "wb") as f:
                pickle.dump(df, f)
        except Exception as exc:
            logger.warning("Cache save failed: %s", exc)
