import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import price, volatility, backtest, signal, briefing, portfolio
from app.routers.ws import router as ws_router, binance_listener
from app.scheduler import backfill_data, daily_fetch, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("Database initialized")

    # Backfill in background (non-blocking startup)
    backfill_task = asyncio.create_task(backfill_data(days=365))
    logger.info("Backfill started in background")

    # Schedule daily fetch
    scheduler.add_job(
        lambda: asyncio.ensure_future(daily_fetch()),
        "cron",
        hour=0,
        minute=5,
        id="daily_fetch",
    )
    scheduler.start()
    logger.info("Scheduler started")

    # Start Binance WebSocket relay
    binance_task = asyncio.create_task(binance_listener())
    logger.info("Binance WebSocket relay started")

    yield

    # Shutdown
    backfill_task.cancel()
    binance_task.cancel()
    scheduler.shutdown()


app = FastAPI(
    title="CryptoVol Dashboard API",
    description="Real-time Bitcoin volatility prediction using 5 GARCH models",
    version="1.0.0",
    lifespan=lifespan,
)

cors_kwargs = {
    "allow_origins": [o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_origin_regex:
    cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex

app.add_middleware(CORSMiddleware, **cors_kwargs)

app.include_router(price.router)
app.include_router(volatility.router)
app.include_router(backtest.router)
app.include_router(signal.router)
app.include_router(briefing.router)
app.include_router(portfolio.router)
app.include_router(ws_router)


@app.get("/api/health")
def health():
    from app.routers.ws import clients, relay_state

    return {
        "status": "ok",
        "relay": {**relay_state, "subscribers": len(clients)},
    }
