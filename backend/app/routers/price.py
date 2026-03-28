import logging
import time
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.price import CoinDaily
from app.schemas.volatility import PriceCurrent, PriceHistory
from app.services import coingecko

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/price", tags=["price"])


def _fallback_from_db(coin: str) -> dict | None:
    """Return latest price data from DB when CoinGecko is unavailable."""
    db = SessionLocal()
    try:
        row = (
            db.query(CoinDaily)
            .filter(CoinDaily.symbol == coin)
            .order_by(desc(CoinDaily.date))
            .first()
        )
        if not row:
            return None
        return {
            "price": row.close,
            "change_24h": 0,
            "volume_24h": row.volume or 0,
            "fng": row.fng,
            "fng_label": _fng_label(row.fng),
            "timestamp": int(time.time()),
        }
    finally:
        db.close()


def _fng_label(val: int | None) -> str:
    if val is None:
        return ""
    if val <= 25:
        return "Extreme Fear"
    if val <= 45:
        return "Fear"
    if val <= 55:
        return "Neutral"
    if val <= 75:
        return "Greed"
    return "Extreme Greed"


@router.get("/current", response_model=PriceCurrent)
async def current_price(coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$")):
    try:
        price_data = await coingecko.get_current_price(symbol=coin)
        fng_data = await coingecko.get_fng(limit=1)
        fng_val = fng_data[0]["value"] if fng_data else None
        fng_label = fng_data[0]["label"] if fng_data else None
        return PriceCurrent(
            price=price_data["price"],
            change_24h=price_data["change_24h"],
            volume_24h=price_data["volume_24h"],
            fng=fng_val,
            fng_label=fng_label,
            timestamp=price_data["timestamp"],
        )
    except Exception as e:
        logger.warning(f"CoinGecko API failed for {coin}, falling back to DB: {e}")
        fallback = _fallback_from_db(coin)
        if fallback:
            return PriceCurrent(
                price=fallback["price"],
                change_24h=fallback["change_24h"],
                volume_24h=fallback["volume_24h"],
                fng=fallback["fng"],
                fng_label=fallback["fng_label"],
                timestamp=fallback["timestamp"],
            )
        raise


@router.get("/multi")
async def multi_prices():
    """Get current prices for all supported coins at once."""
    try:
        return await coingecko.get_multi_prices()
    except Exception as e:
        logger.warning(f"CoinGecko multi API failed, falling back to DB: {e}")
        result = {}
        for coin in ("BTC", "ETH", "SOL"):
            fb = _fallback_from_db(coin)
            if fb:
                result[coin] = {
                    "price": fb["price"],
                    "change_24h": fb["change_24h"],
                    "volume_24h": fb["volume_24h"],
                }
        return result


@router.get("/history", response_model=list[PriceHistory])
def price_history(
    days: int = Query(default=365, le=2000),
    coin: str = Query(default="BTC", pattern="^(BTC|ETH|SOL)$"),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CoinDaily)
        .filter(CoinDaily.symbol == coin)
        .order_by(desc(CoinDaily.date))
        .limit(days)
        .all()
    )
    rows.reverse()
    return [
        PriceHistory(
            date=r.date,
            close=r.close,
            volume=r.volume or 0,
            fng=r.fng,
            log_return=r.log_return,
        )
        for r in rows
    ]
