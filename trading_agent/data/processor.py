from __future__ import annotations
import numpy as np
import pandas as pd


class DataProcessor:
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df[~df.index.duplicated(keep="last")].sort_index()
        df.ffill(inplace=True)
        df.dropna(inplace=True)
        return df

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.clean(df)
        c  = df["Close"]
        h, l = df["High"], df["Low"]

        for p in [5, 10, 20, 50, 200]:
            df[f"sma_{p}"] = c.rolling(p).mean()
            df[f"ema_{p}"] = c.ewm(span=p, adjust=False).mean()

        for p in [5, 10, 20]:
            df[f"roc_{p}"] = c.pct_change(p)

        delta = c.diff()
        gain  = delta.clip(lower=0).ewm(com=13, min_periods=14).mean()
        loss  = (-delta).clip(lower=0).ewm(com=13, min_periods=14).mean()
        rs    = gain / loss.replace(0, np.nan)
        df["rsi_14"] = 100 - 100 / (1 + rs)

        macd  = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig   = macd.ewm(span=9, adjust=False).mean()
        df["macd"], df["macd_signal"], df["macd_hist"] = macd, sig, macd - sig

        mid = c.rolling(20).mean()
        std = c.rolling(20).std()
        df["bb_upper"] = mid + 2 * std
        df["bb_lower"] = mid - 2 * std
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / mid

        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        df["atr_14"] = tr.ewm(com=13, min_periods=14).mean()

        df["vol_ratio"] = df["Volume"] / df["Volume"].rolling(20).mean()
        df["daily_range"] = (h - l) / c
        df["log_return"]  = np.log(c / c.shift(1))
        df["volatility_20"] = df["log_return"].rolling(20).std() * np.sqrt(252)

        df.dropna(inplace=True)
        return df
