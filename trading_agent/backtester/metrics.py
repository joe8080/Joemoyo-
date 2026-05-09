from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    total_return:      float
    annualised_return: float
    sharpe_ratio:      float
    sortino_ratio:     float
    max_drawdown:      float
    max_dd_duration:   int         # bars
    calmar_ratio:      float
    win_rate:          float
    profit_factor:     float
    total_trades:      int
    var_95:            float
    cvar_95:           float
    avg_trade_return:  float
    best_trade:        float
    worst_trade:       float

    def __str__(self):
        return (
            f"Return: {self.total_return:.1%}  Ann: {self.annualised_return:.1%}  "
            f"Sharpe: {self.sharpe_ratio:.2f}  Sortino: {self.sortino_ratio:.2f}  "
            f"MaxDD: {self.max_drawdown:.1%}  WinRate: {self.win_rate:.1%}  "
            f"Trades: {self.total_trades}"
        )


def calculate_metrics(equity_curve: pd.Series,
                       trade_returns: pd.Series,
                       periods_per_year: int = 252) -> PerformanceMetrics:
    if equity_curve.empty or len(equity_curve) < 2:
        return _empty_metrics()

    ret = equity_curve.pct_change().dropna()
    total_return      = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    n_years           = len(ret) / periods_per_year
    annualised_return = (1 + total_return) ** (1 / max(n_years, 1e-6)) - 1

    mean_ret  = ret.mean()
    std_ret   = ret.std()
    sharpe    = (mean_ret / std_ret * np.sqrt(periods_per_year)) if std_ret > 0 else 0.0

    downside  = ret[ret < 0].std()
    sortino   = (mean_ret / downside * np.sqrt(periods_per_year)) if downside > 0 else 0.0

    rolling_max = equity_curve.cummax()
    drawdown    = (equity_curve - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    # drawdown duration
    in_dd   = drawdown < 0
    dd_dur  = 0
    cur_dur = 0
    for v in in_dd:
        cur_dur = cur_dur + 1 if v else 0
        dd_dur  = max(dd_dur, cur_dur)

    calmar = (annualised_return / abs(max_dd)) if max_dd != 0 else 0.0

    tr = trade_returns.dropna()
    wins  = tr[tr > 0]
    losses= tr[tr < 0]
    win_rate     = len(wins) / len(tr) if len(tr) > 0 else 0.0
    gross_profit = wins.sum()
    gross_loss   = losses.abs().sum()
    pf           = (gross_profit / gross_loss) if gross_loss > 0 else (np.inf if gross_profit > 0 else 0.0)

    var95  = float(ret.quantile(0.05)) if len(ret) >= 20 else 0.0
    cvar95 = float(ret[ret <= var95].mean()) if len(ret[ret <= var95]) > 0 else var95

    return PerformanceMetrics(
        total_return      = total_return,
        annualised_return = annualised_return,
        sharpe_ratio      = sharpe,
        sortino_ratio     = sortino,
        max_drawdown      = max_dd,
        max_dd_duration   = dd_dur,
        calmar_ratio      = calmar,
        win_rate          = win_rate,
        profit_factor     = pf,
        total_trades      = len(tr),
        var_95            = var95,
        cvar_95           = cvar95,
        avg_trade_return  = float(tr.mean()) if len(tr) > 0 else 0.0,
        best_trade        = float(tr.max()) if len(tr) > 0 else 0.0,
        worst_trade       = float(tr.min()) if len(tr) > 0 else 0.0,
    )


def _empty_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        total_return=0, annualised_return=0, sharpe_ratio=0, sortino_ratio=0,
        max_drawdown=0, max_dd_duration=0, calmar_ratio=0, win_rate=0,
        profit_factor=0, total_trades=0, var_95=0, cvar_95=0,
        avg_trade_return=0, best_trade=0, worst_trade=0,
    )
