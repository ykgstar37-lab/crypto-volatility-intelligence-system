import math

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.schemas.volatility import ModelPrediction, VolatilityPredict
from app.services.garch import predict_all, fit_garch, fit_tgarch, fit_har_garch, fit_har_tgarch
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
    coin: str = Query(default="BTC", regex="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    returns, volume, fng = _load_series(db, symbol=coin)
    if returns is None or len(returns) < 60:
        return VolatilityPredict(predictions=[], risk_score=0, risk_label="N/A")

    preds = predict_all(returns, volume, fng)
    score, label = compute_risk_score(preds)

    return VolatilityPredict(
        predictions=[ModelPrediction(**p) for p in preds],
        risk_score=score,
        risk_label=label,
    )


@router.get("/compare")
def volatility_compare(
    days: int = Query(default=90, le=180),
    coin: str = Query(default="BTC", regex="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    """Return daily rolling volatility predictions for all 5 models."""
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

    return results
