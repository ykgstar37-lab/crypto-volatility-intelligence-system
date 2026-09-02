import math
from datetime import date

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.schemas.volatility import (
    FactorCorrelation,
    FactorCorrelationResult,
    ModelPrediction,
    VolatilityPredict,
)
from app.services.garch import predict_all, fit_garch, fit_tgarch, fit_har_garch, fit_har_tgarch, _cache_get, _cache_set
from app.services.risk_score import compute_risk_score
from scipy.stats import pearsonr

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

    # 표준화하지 않고 원값으로 넘긴다. 스케일 조정은 garch._rescale이 담당하며,
    # 여기서 미리 z-score를 씌우면 음수가 생겨 로그 변환이 막힌다.
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


@router.get("/factors", response_model=FactorCorrelationResult)
def factor_correlations(
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    days: int = Query(default=365, ge=60, le=2000),
    db: Session = Depends(get_db),
):
    """외생변수가 변동성과 실제로 연관되는지 현재 데이터로 다시 계산한다.

    2023년 논문은 FNG-수익률 상관이 0.72(p=2.2e-16)라고 서술했으나 이를
    뒷받침하는 표가 유실되어 인용만으로는 검증할 수 없다. 여기서는 DB에
    적재된 실제 데이터로 매번 다시 계산해 값 자체를 산출한다.
    """
    cache_key = f"factors:{coin}:{days}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(days)
        .all()
    )
    rows.reverse()
    if len(rows) < 60:
        return FactorCorrelationResult(
            coin=coin, period_start=date.today(), period_end=date.today(),
            n_days=len(rows), correlations=[],
        )

    df = pd.DataFrame([
        {"date": r.date, "close": r.close, "volume": r.volume,
         "fng": r.fng, "log_return": r.log_return}
        for r in rows
    ]).set_index("date")

    df["abs_return"] = df["log_return"].abs()      # 변동성 대리변수
    df["realized_vol"] = df["log_return"].rolling(7).std()

    pairs = [
        ("FNG", "log_return"),      # 논문이 0.72로 서술한 조합
        ("FNG", "abs_return"),
        ("FNG", "realized_vol"),
        ("Volume", "abs_return"),
        ("Volume", "realized_vol"),
    ]
    col = {"FNG": "fng", "Volume": "volume"}

    correlations = []
    for factor, target in pairs:
        sub = df[[col[factor], target]].dropna()
        if len(sub) < 30:
            continue
        x = sub[col[factor]].astype(float).values
        y = sub[target].astype(float).values
        if x.std() == 0 or y.std() == 0:
            continue
        r, p = pearsonr(x, y)
        correlations.append(FactorCorrelation(
            factor=factor, target=target,
            pearson_r=round(float(r), 4),
            p_value=float(p),
            significant=bool(p < 0.05),
            n=len(sub),
        ))

    result = FactorCorrelationResult(
        coin=coin,
        period_start=df.index[0],
        period_end=df.index[-1],
        n_days=len(df),
        correlations=correlations,
    )
    _cache_set(cache_key, result)
    return result
