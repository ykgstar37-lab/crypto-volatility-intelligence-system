import math

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.schemas.volatility import ModelPrediction, VolatilityPredict
from app.services.garch import predict_all, fit_garch, fit_tgarch, fit_har_garch, fit_har_tgarch, _cache_get, _cache_set
from app.services.risk_score import compute_risk_score

router = APIRouter(prefix="/api/volatility", tags=["volatility"])

WINDOW = 60  # rolling window for fitting


def _load_series(db: Session, days: int = 400, symbol: str = "BTC"):
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == symbol)
        .order_by(desc(CoinDaily.date))
        .limit(days)
        .all()
    )
    rows.reverse()
    if not rows:
        return None, None, None

    dates = [r.date for r in rows]
    returns = pd.Series([r.log_return or 0 for r in rows], index=dates)
    volume = pd.Series([r.volume or 0 for r in rows], index=dates)
    fng = pd.Series([r.fng or 50 for r in rows], index=dates)

    if volume.std() > 0:
        volume = (volume - volume.mean()) / volume.std()

    return returns, volume, fng


@router.get("/predict", response_model=VolatilityPredict)
def volatility_predict(
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    cache_key = f"predict:{coin}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    returns, volume, fng = _load_series(db, symbol=coin)
    if returns is None or len(returns) < 60:
        return VolatilityPredict(predictions=[], risk_score=0, risk_label="N/A")

    preds = predict_all(returns, volume, fng)
    score, label = compute_risk_score(preds)

    result = VolatilityPredict(
        predictions=[ModelPrediction(**p) for p in preds],
        risk_score=score,
        risk_label=label,
    )
    _cache_set(cache_key, result)
    return result


@router.get("/compare")
def volatility_compare(
    days: int = Query(default=90, le=180),
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    """Return daily rolling volatility predictions for all 5 models."""
    cache_key = f"compare:{coin}:{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    total_needed = days + WINDOW + 30
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(total_needed)
        .all()
    )
    rows.reverse()
    if len(rows) < WINDOW + 30:
        return []

    returns = np.array([r.log_return or 0 for r in rows])
    dates = [r.date for r in rows]
    returns_series = pd.Series(returns, index=dates)

    results = []
    step = max(1, days // 60)

    for i in range(WINDOW + 30, len(rows), step):
        window_returns = returns[i - WINDOW:i]
        window_series = returns_series.iloc[i - WINDOW:i]
        realized = abs(returns[i]) * math.sqrt(365) * 100

        row_data = {
            "date": dates[i].isoformat(),
            "realized": round(realized, 2),
        }

        try:
            row_data["garch"] = round(fit_garch(window_returns) * math.sqrt(365) * 100, 2)
        except Exception:
            row_data["garch"] = None

        try:
            row_data["tgarch"] = round(fit_tgarch(window_returns) * math.sqrt(365) * 100, 2)
        except Exception:
            row_data["tgarch"] = None

        try:
            row_data["har_garch"] = round(fit_har_garch(window_returns) * math.sqrt(365) * 100, 2)
        except Exception:
            row_data["har_garch"] = None

        try:
            row_data["har_tgarch"] = round(fit_har_tgarch(window_series) * math.sqrt(365) * 100, 2)
        except Exception:
            row_data["har_tgarch"] = None

        results.append(row_data)

    _cache_set(cache_key, results)
    return results


@router.get("/accuracy")
def volatility_accuracy(
    days: int = Query(default=60, le=120),
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    """Track cumulative prediction accuracy: predicted vs realized volatility per model."""
    cache_key = f"accuracy:{coin}:{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    total_needed = days + WINDOW + 30
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(total_needed)
        .all()
    )
    rows.reverse()
    if len(rows) < WINDOW + 31:
        return {"models": [], "daily": []}

    returns = np.array([r.log_return or 0 for r in rows])
    dates = [r.date for r in rows]
    returns_series = pd.Series(returns, index=dates)

    model_fns = [
        ("GARCH(1,1)", lambda w: fit_garch(w)),
        ("TGARCH", lambda w: fit_tgarch(w)),
        ("HAR-GARCH", lambda w: fit_har_garch(w)),
    ]

    # Collect daily predictions vs realized
    daily = []
    cumulative_errors = {name: [] for name, _ in model_fns}

    for i in range(WINDOW + 30, len(rows)):
        window_returns = returns[i - WINDOW:i]
        realized = abs(returns[i]) * math.sqrt(365) * 100

        day_data = {"date": dates[i].isoformat(), "realized": round(realized, 2)}

        for name, fn in model_fns:
            try:
                pred = fn(window_returns) * math.sqrt(365) * 100
                error = abs(pred - realized)
                cumulative_errors[name].append(error)
                day_data[name] = round(pred, 2)
                day_data[f"{name}_error"] = round(error, 2)
                # Cumulative RMSE up to this point
                day_data[f"{name}_cum_rmse"] = round(
                    math.sqrt(np.mean([e**2 for e in cumulative_errors[name]])), 4
                )
            except Exception:
                day_data[name] = None

        daily.append(day_data)

    # Summary per model
    models_summary = []
    for name, _ in model_fns:
        errors = cumulative_errors[name]
        if errors:
            mae = float(np.mean(errors))
            rmse = math.sqrt(float(np.mean([e**2 for e in errors])))
            # Direction accuracy: was the prediction's relative magnitude correct?
            models_summary.append({
                "model": name,
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "samples": len(errors),
            })

    models_summary.sort(key=lambda x: x["rmse"])
    for i, m in enumerate(models_summary):
        m["rank"] = i + 1

    result = {"models": models_summary, "daily": daily}
    _cache_set(cache_key, result)
    return result
