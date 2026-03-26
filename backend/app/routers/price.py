from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.price import CoinDaily
from app.schemas.volatility import PriceCurrent, PriceHistory
from app.services import coingecko

router = APIRouter(prefix="/api/price", tags=["price"])


@router.get("/current", response_model=PriceCurrent)
async def current_price(coin: str = Query(default="BTC", regex="^(BTC|ETH|SOL)$")):
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


@router.get("/multi")
async def multi_prices():
    """Get current prices for all supported coins at once."""
    return await coingecko.get_multi_prices()


@router.get("/history", response_model=list[PriceHistory])
def price_history(
    days: int = Query(default=365, le=2000),
    coin: str = Query(default="BTC", regex="^(BTC|ETH|SOL)$"),
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
