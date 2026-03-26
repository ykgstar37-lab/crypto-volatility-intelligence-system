import asyncio
import math
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models.price import CoinDaily, Base
from app.services import coingecko

logger = logging.getLogger(__name__)

SUPPORTED_COINS = ["BTC", "ETH", "SOL"]


async def backfill_coin(symbol: str, days: int = 365):
    """Fetch historical data for a single coin and populate the database."""
    db = SessionLocal()
    try:
        existing = db.query(CoinDaily).filter(CoinDaily.symbol == symbol).count()
        if existing > 100:
            logger.info(f"{symbol}: DB already has {existing} rows, skipping backfill")
            return

        logger.info(f"{symbol}: Backfilling {days} days of data...")
        chart = await coingecko.get_market_chart(days=days, symbol=symbol)

        # FNG is crypto-wide (only relevant, shared across coins)
        fng_map = await coingecko.get_fng_history(days=days) if symbol == "BTC" else {}

        # Deduplicate by date
        seen = set()
        unique_chart = []
        for item in chart:
            d = item["date"]
            if d not in seen:
                seen.add(d)
                unique_chart.append(item)

        prev_close = None
        for item in unique_chart:
            d = item["date"]
            existing_row = db.query(CoinDaily).filter(
                CoinDaily.symbol == symbol, CoinDaily.date == d
            ).first()
            if existing_row:
                prev_close = existing_row.close
                continue

            row = CoinDaily(
                symbol=symbol,
                date=d,
                close=item["close"],
                volume=item["volume"],
                fng=fng_map.get(d),
            )
            if prev_close:
                row.compute_log_return(prev_close)
            prev_close = item["close"]

            db.add(row)

        db.commit()
        count = db.query(CoinDaily).filter(CoinDaily.symbol == symbol).count()
        logger.info(f"{symbol}: Backfilled {count} total rows")
    except Exception as e:
        logger.error(f"{symbol} backfill error: {e}")
        db.rollback()
    finally:
        db.close()


async def backfill_data(days: int = 365):
    """Backfill all supported coins."""
    for symbol in SUPPORTED_COINS:
        await backfill_coin(symbol, days)
        await asyncio.sleep(1)  # Rate limit courtesy


async def daily_fetch():
    """Fetch yesterday's data for all coins."""
    for symbol in SUPPORTED_COINS:
        db = SessionLocal()
        try:
            chart = await coingecko.get_market_chart(days=2, symbol=symbol)
            fng_map = {}
            if symbol == "BTC":
                fng_list = await coingecko.get_fng(limit=2)
                fng_map = {f["date"]: f["value"] for f in fng_list}

            last_row = (
                db.query(CoinDaily)
                .filter(CoinDaily.symbol == symbol)
                .order_by(CoinDaily.date.desc())
                .first()
            )
            prev_close = last_row.close if last_row else None

            for item in chart:
                d = item["date"]
                if db.query(CoinDaily).filter(
                    CoinDaily.symbol == symbol, CoinDaily.date == d
                ).first():
                    continue

                row = CoinDaily(
                    symbol=symbol,
                    date=d,
                    close=item["close"],
                    volume=item["volume"],
                    fng=fng_map.get(d),
                )
                if prev_close:
                    row.compute_log_return(prev_close)
                prev_close = item["close"]
                db.add(row)

            db.commit()
            logger.info(f"{symbol}: Daily fetch complete")
        except Exception as e:
            logger.error(f"{symbol} daily fetch error: {e}")
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(1)


def init_db():
    """Create tables if not exist."""
    Base.metadata.create_all(bind=engine)
