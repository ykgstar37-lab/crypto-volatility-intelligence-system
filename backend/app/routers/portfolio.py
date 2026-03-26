"""
Portfolio simulator — compute VaR and risk metrics for a multi-coin portfolio.
"""
import math

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.services.garch import fit_garch

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

SUPPORTED = ["BTC", "ETH", "SOL"]


class PortfolioRequest(BaseModel):
    weights: dict[str, float]  # {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    investment: float = 10000
    horizon: int = 7  # days


def _load_returns(db: Session, symbol: str, days: int = 365) -> pd.Series | None:
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == symbol)
        .order_by(desc(CoinDaily.date))
        .limit(days)
        .all()
    )
    rows.reverse()
    if len(rows) < 60:
        return None
    dates = [r.date for r in rows]
    returns = [r.log_return or 0.0 for r in rows]
    return pd.Series(returns, index=dates)


@router.post("/simulate")
def simulate_portfolio(req: PortfolioRequest, db: Session = Depends(get_db)):
    weights = {k: v for k, v in req.weights.items() if k in SUPPORTED and v > 0}
    if not weights:
        return {"error": "No valid weights"}

    # Normalize weights
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    # Load returns for each coin
    coin_returns = {}
    coin_vols = {}
    for symbol in weights:
        ret = _load_returns(db, symbol)
        if ret is None:
            return {"error": f"Insufficient data for {symbol}"}
        coin_returns[symbol] = ret

        # GARCH predicted daily vol
        try:
            sigma = fit_garch(ret.values[-120:])
        except Exception:
            sigma = ret.values[-60:].std()
        coin_vols[symbol] = sigma

    # Align all return series by common dates
    df = pd.DataFrame(coin_returns).dropna()
    if len(df) < 30:
        return {"error": "Insufficient overlapping data"}

    # Portfolio daily returns
    w_arr = np.array([weights.get(c, 0) for c in df.columns])
    port_returns = df.values @ w_arr

    # Historical stats
    port_mean = float(np.mean(port_returns))
    port_std = float(np.std(port_returns))
    ann_return = port_mean * 365 * 100
    ann_vol = port_std * math.sqrt(365) * 100
    sharpe = (ann_return / ann_vol) if ann_vol > 0 else 0

    # GARCH-based portfolio volatility (simplified — weighted sum of variances, ignoring correlation for speed)
    garch_var = sum(
        (weights[c] ** 2) * (coin_vols[c] ** 2) for c in weights
    )
    # Add cross-correlations
    symbols = list(weights.keys())
    for i in range(len(symbols)):
        for j in range(i + 1, len(symbols)):
            if symbols[i] in df.columns and symbols[j] in df.columns:
                corr = float(df[symbols[i]].corr(df[symbols[j]]))
                garch_var += 2 * weights[symbols[i]] * weights[symbols[j]] * \
                    coin_vols[symbols[i]] * coin_vols[symbols[j]] * corr
    garch_vol = math.sqrt(max(0, garch_var))

    # VaR calculations (parametric)
    z_95 = 1.645
    z_99 = 2.326
    horizon_factor = math.sqrt(req.horizon)

    var_95_pct = garch_vol * z_95 * horizon_factor * 100
    var_99_pct = garch_vol * z_99 * horizon_factor * 100
    var_95_usd = req.investment * garch_vol * z_95 * horizon_factor
    var_99_usd = req.investment * garch_vol * z_99 * horizon_factor

    # Monte Carlo simulation (1000 paths)
    n_sims = 1000
    mc_returns = np.random.normal(port_mean * req.horizon, garch_vol * horizon_factor, n_sims)
    mc_values = req.investment * np.exp(mc_returns)
    mc_pnl = mc_values - req.investment

    percentiles = {
        "p5": round(float(np.percentile(mc_pnl, 5)), 2),
        "p25": round(float(np.percentile(mc_pnl, 25)), 2),
        "p50": round(float(np.percentile(mc_pnl, 50)), 2),
        "p75": round(float(np.percentile(mc_pnl, 75)), 2),
        "p95": round(float(np.percentile(mc_pnl, 95)), 2),
    }

    # Distribution histogram
    hist_counts, hist_edges = np.histogram(mc_pnl, bins=40)
    distribution = [
        {"x": round(float((hist_edges[i] + hist_edges[i + 1]) / 2), 2), "count": int(hist_counts[i])}
        for i in range(len(hist_counts))
    ]

    # Per-coin breakdown
    coin_breakdown = []
    for symbol in weights:
        ret = coin_returns[symbol]
        coin_breakdown.append({
            "symbol": symbol,
            "weight": round(weights[symbol] * 100, 1),
            "ann_return": round(float(np.mean(ret.values)) * 365 * 100, 2),
            "ann_vol": round(coin_vols[symbol] * math.sqrt(365) * 100, 2),
            "garch_sigma": round(coin_vols[symbol], 6),
        })

    # Correlation matrix
    corr_matrix = {}
    for c1 in symbols:
        for c2 in symbols:
            if c1 in df.columns and c2 in df.columns:
                corr_matrix[f"{c1}-{c2}"] = round(float(df[c1].corr(df[c2])), 3)

    return {
        "weights": {k: round(v * 100, 1) for k, v in weights.items()},
        "investment": req.investment,
        "horizon": req.horizon,
        "portfolio": {
            "ann_return": round(ann_return, 2),
            "ann_vol": round(ann_vol, 2),
            "garch_vol": round(garch_vol * math.sqrt(365) * 100, 2),
            "sharpe": round(sharpe, 2),
        },
        "var": {
            "var_95_pct": round(var_95_pct, 2),
            "var_99_pct": round(var_99_pct, 2),
            "var_95_usd": round(var_95_usd, 2),
            "var_99_usd": round(var_99_usd, 2),
        },
        "monte_carlo": percentiles,
        "distribution": distribution,
        "coins": coin_breakdown,
        "correlations": corr_matrix,
    }
