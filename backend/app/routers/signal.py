import math

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.services.garch import fit_garch, fit_tgarch, fit_har_garch, _cache_get, _cache_set

router = APIRouter(prefix="/api/signal", tags=["signal"])


@router.get("")
def get_signal(coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"), db: Session = Depends(get_db)):
    """Generate trading signal based on FNG + volatility trend."""
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(90)
        .all()
    )
    rows.reverse()
    if len(rows) < 60:
        return {"signal": "neutral", "confidence": 0, "reasons": []}

    fng_recent = [r.fng for r in rows[-7:] if r.fng is not None]
    fng_avg = sum(fng_recent) / len(fng_recent) if fng_recent else 50

    returns = np.array([r.log_return or 0 for r in rows])
    vol_recent = np.std(returns[-7:]) * math.sqrt(365) * 100
    vol_30d = np.std(returns[-30:]) * math.sqrt(365) * 100
    vol_trend = vol_recent - vol_30d

    reasons = []
    score = 0  # -100 (strong sell) to +100 (strong buy)

    # FNG signal
    if fng_avg < 20:
        score += 40
        reasons.append({"type": "bullish", "text": f"Extreme Fear (FNG: {fng_avg:.0f}) — historically a buy opportunity"})
    elif fng_avg < 35:
        score += 20
        reasons.append({"type": "bullish", "text": f"Fear zone (FNG: {fng_avg:.0f}) — potential accumulation area"})
    elif fng_avg > 80:
        score -= 40
        reasons.append({"type": "bearish", "text": f"Extreme Greed (FNG: {fng_avg:.0f}) — correction risk elevated"})
    elif fng_avg > 65:
        score -= 20
        reasons.append({"type": "bearish", "text": f"Greed zone (FNG: {fng_avg:.0f}) — caution advised"})
    else:
        reasons.append({"type": "neutral", "text": f"Neutral sentiment (FNG: {fng_avg:.0f})"})

    # Volatility trend
    if vol_trend < -5:
        score += 20
        reasons.append({"type": "bullish", "text": f"Volatility declining ({vol_trend:+.1f}%) — market stabilizing"})
    elif vol_trend > 10:
        score -= 20
        reasons.append({"type": "bearish", "text": f"Volatility spiking ({vol_trend:+.1f}%) — increased uncertainty"})
    else:
        reasons.append({"type": "neutral", "text": f"Volatility stable ({vol_trend:+.1f}%)"})

    # Price momentum (7d)
    price_7d_change = ((rows[-1].close / rows[-8].close) - 1) * 100 if len(rows) >= 8 and rows[-8].close else 0
    if price_7d_change > 5:
        score += 10
        reasons.append({"type": "bullish", "text": f"7d price momentum: {price_7d_change:+.1f}%"})
    elif price_7d_change < -5:
        score -= 10
        reasons.append({"type": "bearish", "text": f"7d price momentum: {price_7d_change:+.1f}%"})

    # Vol vs 30d average
    if vol_recent > vol_30d * 1.5:
        reasons.append({"type": "warning", "text": f"Current vol ({vol_recent:.1f}%) is {vol_recent/vol_30d:.1f}x above 30d average"})

    # Determine signal
    if score >= 30:
        signal = "buy"
    elif score <= -30:
        signal = "sell"
    else:
        signal = "neutral"

    return {
        "signal": signal,
        "score": max(-100, min(100, score)),
        "fng_avg_7d": round(fng_avg, 1),
        "vol_7d": round(vol_recent, 2),
        "vol_30d": round(vol_30d, 2),
        "vol_trend": round(vol_trend, 2),
        "price_7d_change": round(price_7d_change, 2),
        "reasons": reasons,
    }


@router.get("/leaderboard")
def model_leaderboard(coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"), db: Session = Depends(get_db)):
    """Rank models by prediction accuracy over last 30 days."""
    cache_key = f"leaderboard:{coin}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(90)
        .all()
    )
    rows.reverse()
    if len(rows) < 70:
        return []

    returns = np.array([r.log_return or 0 for r in rows])
    window = 60

    models = [
        ("GARCH(1,1)", fit_garch),
        ("TGARCH", fit_tgarch),
        ("HAR-GARCH", fit_har_garch),
    ]

    results = []
    for name, fn in models:
        errors = []
        for i in range(window, min(window + 30, len(returns))):
            try:
                pred = fn(returns[i - window:i])
                realized = abs(returns[i])
                errors.append((pred - realized) ** 2)
            except Exception:
                continue

        if errors:
            mse = float(np.mean(errors))
            rmse = math.sqrt(mse)
            results.append({
                "model": name,
                "rmse": round(rmse, 6),
                "mse": round(mse, 10),
                "samples": len(errors),
            })

    results.sort(key=lambda x: x["rmse"])
    for i, r in enumerate(results):
        r["rank"] = i + 1

    _cache_set(cache_key, results)
    return results


@router.get("/accuracy")
def signal_accuracy(coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"), db: Session = Depends(get_db)):
    """Calculate historical signal accuracy over last 60 days."""
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(90)
        .all()
    )
    rows.reverse()
    if len(rows) < 30:
        return {"total": 0, "correct": 0, "accuracy": 0, "history": []}

    history = []
    correct = 0
    total = 0

    for i in range(14, len(rows) - 7):
        # Simple signal based on FNG at time i
        fng = rows[i].fng or 50
        price_now = rows[i].close
        price_7d_later = rows[i + 7].close if i + 7 < len(rows) else None
        if not price_7d_later or not price_now:
            continue

        actual_change = ((price_7d_later / price_now) - 1) * 100

        if fng < 25:
            signal = "buy"
            was_correct = actual_change > 0
        elif fng > 75:
            signal = "sell"
            was_correct = actual_change < 0
        else:
            continue  # neutral signals not counted

        total += 1
        if was_correct:
            correct += 1

        history.append({
            "date": rows[i].date.isoformat(),
            "fng": fng,
            "signal": signal,
            "actual_7d": round(actual_change, 2),
            "correct": was_correct,
        })

    accuracy = (correct / total * 100) if total > 0 else 0
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 1),
        "history": history[-20:],
    }
