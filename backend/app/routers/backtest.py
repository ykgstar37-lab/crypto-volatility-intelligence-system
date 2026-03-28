import math
from datetime import date

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.schemas.volatility import BacktestMetric, BacktestResult
from app.services.garch import fit_garch, fit_tgarch, fit_har_garch

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


def _calc_metrics(predicted: np.ndarray, realized: np.ndarray) -> dict:
    mask = (realized > 0) & (predicted > 0)
    p, r = predicted[mask], realized[mask]
    if len(p) < 5:
        return {"mse": 0, "rmse": 0, "mape": 0, "mae": 0, "r2": 0}

    errors = p - r
    mse = float(np.mean(errors ** 2))
    rmse = math.sqrt(mse)
    mae = float(np.mean(np.abs(errors)))
    mape = float(np.mean(np.abs(errors / r))) * 100
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((r - np.mean(r)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0

    return {
        "mse": round(mse, 8),
        "rmse": round(rmse, 6),
        "mape": round(mape, 2),
        "mae": round(mae, 6),
        "r2": round(r2, 4),
    }


@router.get("", response_model=BacktestResult)
def backtest(
    start: date = Query(...),
    end: date = Query(...),
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin, CoinDaily.date >= start, CoinDaily.date <= end)
        .order_by(CoinDaily.date)
        .all()
    )

    if len(rows) < 60:
        return BacktestResult(start=start, end=end, models=[])

    returns = np.array([r.log_return or 0 for r in rows])
    realized = np.abs(returns)

    model_results = []
    fitters = [
        ("GARCH(1,1)", fit_garch),
        ("TGARCH", fit_tgarch),
        ("HAR-GARCH", fit_har_garch),
    ]

    for name, fn in fitters:
        try:
            preds = []
            window = 60
            for i in range(window, len(returns)):
                sigma = fn(returns[i - window:i])
                preds.append(sigma)
            pred_arr = np.array(preds)
            real_arr = realized[window:]
            metrics = _calc_metrics(pred_arr, real_arr)
            model_results.append(BacktestMetric(model=name, **metrics))
        except Exception:
            model_results.append(BacktestMetric(model=name, mse=0, rmse=0, mape=0, mae=0, r2=0))

    return BacktestResult(start=start, end=end, models=model_results)
