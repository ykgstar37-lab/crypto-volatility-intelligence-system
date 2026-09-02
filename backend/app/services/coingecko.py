import asyncio
import logging
from datetime import datetime, date

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(5)

# CoinGecko 무료 API는 데이터센터 IP(클라우드 PaaS)를 공격적으로 rate-limit 한다.
# 로컬에서는 통과하던 요청이 배포 환경에서 429/403으로 막히므로 재시도가 필요하다.
_MAX_RETRIES = 4
_RETRY_STATUS = {403, 408, 429, 500, 502, 503, 504}

# CoinGecko ID mapping
COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


def _headers(url: str) -> dict:
    """Demo API key를 붙이면 IP 기반이 아닌 키 기반 쿼터를 사용한다."""
    if settings.coingecko_api_key and url.startswith(settings.coingecko_base_url):
        return {"x-cg-demo-api-key": settings.coingecko_api_key}
    return {}


async def _get(url: str, params: dict | None = None) -> dict:
    """GET with exponential backoff on rate limiting / transient errors."""
    backoff = 2
    last_exc: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        async with _semaphore:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.get(url, params=params, headers=_headers(url))
                    if resp.status_code in _RETRY_STATUS and attempt < _MAX_RETRIES:
                        logger.warning(
                            f"{url} -> HTTP {resp.status_code} "
                            f"(attempt {attempt}/{_MAX_RETRIES}), retrying in {backoff}s"
                        )
                        last_exc = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code}", request=resp.request, response=resp
                        )
                    else:
                        resp.raise_for_status()
                        return resp.json()
            except (httpx.TransportError, httpx.TimeoutException) as e:
                if attempt >= _MAX_RETRIES:
                    raise
                logger.warning(
                    f"{url} -> {type(e).__name__} "
                    f"(attempt {attempt}/{_MAX_RETRIES}), retrying in {backoff}s"
                )
                last_exc = e

        await asyncio.sleep(backoff)
        backoff *= 2

    raise last_exc if last_exc else RuntimeError(f"{url}: exhausted retries")


async def get_current_price(symbol: str = "BTC") -> dict:
    coin_id = COIN_IDS.get(symbol, "bitcoin")
    data = await _get(
        f"{settings.coingecko_base_url}/simple/price",
        {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        },
    )
    coin = data[coin_id]
    return {
        "price": coin["usd"],
        "change_24h": coin.get("usd_24h_change", 0),
        "volume_24h": coin.get("usd_24h_vol", 0),
        "timestamp": coin.get("last_updated_at", 0),
    }


async def get_multi_prices() -> dict:
    """Fetch prices for all supported coins at once."""
    ids = ",".join(COIN_IDS.values())
    data = await _get(
        f"{settings.coingecko_base_url}/simple/price",
        {
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        },
    )
    result = {}
    for symbol, coin_id in COIN_IDS.items():
        if coin_id in data:
            coin = data[coin_id]
            result[symbol] = {
                "price": coin["usd"],
                "change_24h": coin.get("usd_24h_change", 0),
                "volume_24h": coin.get("usd_24h_vol", 0),
            }
    return result


async def get_market_chart(days: int = 365, symbol: str = "BTC") -> list[dict]:
    coin_id = COIN_IDS.get(symbol, "bitcoin")
    data = await _get(
        f"{settings.coingecko_base_url}/coins/{coin_id}/market_chart",
        {"vs_currency": "usd", "days": str(days), "interval": "daily"},
    )
    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])

    vol_map = {}
    for ts, vol in volumes:
        d = datetime.utcfromtimestamp(ts / 1000).date()
        vol_map[d] = vol

    results = []
    for ts, price in prices:
        d = datetime.utcfromtimestamp(ts / 1000).date()
        results.append({
            "date": d,
            "close": price,
            "volume": vol_map.get(d, 0),
        })
    return results


async def get_fng(limit: int = 1) -> list[dict]:
    data = await _get(settings.fng_base_url, {"limit": str(limit)})
    results = []
    for item in data.get("data", []):
        results.append({
            "date": date.fromtimestamp(int(item["timestamp"])),
            "value": int(item["value"]),
            "label": item.get("value_classification", ""),
        })
    return results


async def get_fng_history(days: int = 365) -> dict[date, int]:
    data = await _get(settings.fng_base_url, {"limit": str(days)})
    result = {}
    for item in data.get("data", []):
        d = date.fromtimestamp(int(item["timestamp"]))
        result[d] = int(item["value"])
    return result
