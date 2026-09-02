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

# 백필 재시도 라운드 수 (라운드 간 60s → 120s → ... 최대 900s)
_BACKFILL_ROUNDS = 5


async def backfill_coin(symbol: str, days: int = 365) -> bool:
    """Fetch historical data for a single coin. Returns True if the DB has data after."""
    db = SessionLocal()
    try:
        existing = db.query(CoinDaily).filter(CoinDaily.symbol == symbol).count()
        if existing > 100:
            logger.info(f"{symbol}: DB already has {existing} rows, skipping backfill")
            return True

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
        return count > 0
    except Exception as e:
        logger.error(f"{symbol} backfill error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


async def backfill_data(days: int = 365):
    """Backfill all supported coins, retrying coins that failed.

    CoinGecko가 클라우드 IP를 rate-limit 하면 첫 시도가 통째로 실패한다.
    재시도가 없으면 다음 크론(내일 00:05, days=2)까지 DB가 빈 채로 남아
    모든 차트가 no_data가 되므로, 실패한 코인만 backoff를 두고 다시 받는다.
    """
    pending = list(SUPPORTED_COINS)
    delay = 60

    for round_no in range(1, _BACKFILL_ROUNDS + 1):
        failed = []
        for symbol in pending:
            if not await backfill_coin(symbol, days):
                failed.append(symbol)
            await asyncio.sleep(1)  # Rate limit courtesy

        if not failed:
            logger.info(f"Backfill complete for all coins (round {round_no})")
            return

        pending = failed
        if round_no < _BACKFILL_ROUNDS:
            logger.warning(
                f"Backfill failed for {pending} (round {round_no}/{_BACKFILL_ROUNDS}), "
                f"retrying in {delay}s"
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, 900)

    logger.error(f"Backfill gave up after {_BACKFILL_ROUNDS} rounds: {pending}")


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
    """Run Alembic migrations to ensure schema is up to date."""
    import os

    # Skip Alembic in test environments — tests manage their own schema
    if os.environ.get("TESTING"):
        Base.metadata.create_all(bind=engine)
        return

    alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    if os.path.exists(alembic_ini):
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(alembic_ini)
        # fileConfig()가 root 로거를 WARNING으로 되돌리지 않도록 한다.
        alembic_cfg.attributes["configure_logger"] = False
        command.upgrade(alembic_cfg, "head")
    else:
        Base.metadata.create_all(bind=engine)
