"""
WebSocket router — relays Binance real-time ticks to dashboard clients.

Binance streams used:
  btcusdt@trade   — BTC/USDT last trade
  ethusdt@trade   — ETH/USDT last trade

Each connected client receives JSON:
  { "type": "tick", "symbol": "BTC", "price": 87445.12, "ts": 1711468800000 }
  { "type": "tick", "symbol": "ETH", "price": 2045.31, "ts": 1711468800000 }
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Set

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Connected dashboard clients ──
clients: Set[WebSocket] = set()

# ── Latest prices (for newly connected clients) ──
latest: dict[str, dict] = {}

# ── 릴레이 상태 (헬스체크로 노출해 배포 후 원인 추적을 가능하게 한다) ──
relay_state: dict = {
    "provider": None,      # 현재 연결된 공급자
    "ticks": 0,            # 수신 누적 틱 수
    "last_tick_at": None,  # 마지막 틱 시각(epoch ms)
    "blocked": [],         # 지역 차단 등으로 제외된 공급자
    "last_error": None,    # 마지막 실패 사유
}

BINANCE_WS = "wss://stream.binance.com:9443/ws"
STREAMS = ["btcusdt@trade", "ethusdt@trade", "solusdt@trade"]
SYMBOL_MAP = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}

# Binance는 미국 IP를 지역 차단한다(HTTP 451). Render 기본 리전이 오레곤(미국)이라
# 배포 환경에서는 Binance 연결이 영구히 실패한다. Coinbase는 미국에서 접근 가능하므로
# 차단이 확인되면 그쪽으로 넘어간다.
COINBASE_WS = "wss://ws-feed.exchange.coinbase.com"
COINBASE_PRODUCTS = {"BTC-USD": "BTC", "ETH-USD": "ETH", "SOL-USD": "SOL"}

# 지역 차단/거부로 재시도가 무의미한 상태 코드
_BLOCKED_STATUS = {401, 403, 451}


async def broadcast(message: dict):
    """Send to all connected clients, remove dead ones."""
    dead = set()
    data = json.dumps(message)
    for ws in clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.add(ws)
    clients.difference_update(dead)


def _status_of(exc: Exception) -> int | None:
    """websockets 버전에 따라 상태 코드 위치가 달라 방어적으로 읽는다."""
    for attr in ("status_code", "code"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    resp = getattr(exc, "response", None)
    v = getattr(resp, "status_code", None)
    if isinstance(v, int):
        return v
    for code in _BLOCKED_STATUS:
        if str(code) in str(exc):
            return code
    return None


async def _emit(symbol: str, price: float, ts: int):
    if not symbol or not price:
        return
    msg = {"type": "tick", "symbol": symbol, "price": price, "ts": ts}
    latest[symbol] = msg
    relay_state["ticks"] += 1
    relay_state["last_tick_at"] = ts
    await broadcast(msg)


async def _run_binance():
    url = f"{BINANCE_WS}/{'/'.join(STREAMS)}"
    async with websockets.connect(url) as ws:
        logger.info(f"Connected to Binance WebSocket: {STREAMS}")
        relay_state["provider"] = "Binance"
        async for raw in ws:
            try:
                data = json.loads(raw)
                if "data" in data:
                    data = data["data"]
                await _emit(
                    SYMBOL_MAP.get(data.get("s", ""), ""),
                    float(data.get("p", 0)),
                    data.get("T", 0),
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue


async def _run_coinbase():
    async with websockets.connect(COINBASE_WS) as ws:
        await ws.send(json.dumps({
            "type": "subscribe",
            "product_ids": list(COINBASE_PRODUCTS),
            "channels": ["ticker"],
        }))
        logger.info(f"Connected to Coinbase WebSocket: {list(COINBASE_PRODUCTS)}")
        relay_state["provider"] = "Coinbase"
        async for raw in ws:
            try:
                d = json.loads(raw)
                if d.get("type") != "ticker":
                    continue
                ts = int(
                    datetime.strptime(
                        d["time"][:19], "%Y-%m-%dT%H:%M:%S"
                    ).replace(tzinfo=timezone.utc).timestamp() * 1000
                ) if d.get("time") else 0
                await _emit(
                    COINBASE_PRODUCTS.get(d.get("product_id", ""), ""),
                    float(d.get("price", 0)),
                    ts,
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue


PROVIDERS = [("Binance", _run_binance), ("Coinbase", _run_coinbase)]


async def binance_listener():
    """실시간 시세 릴레이. 지역 차단된 공급자는 건너뛰고 다음 공급자로 넘어간다."""
    blocked: set[str] = set()
    idx = 0
    backoff = 1
    max_backoff = 60

    while True:
        candidates = [p for p in PROVIDERS if p[0] not in blocked]
        if not candidates:
            logger.error(
                "모든 시세 공급자가 차단되었습니다. 60초 후 전부 재시도합니다."
            )
            blocked.clear()
            await asyncio.sleep(max_backoff)
            continue

        name, run = candidates[idx % len(candidates)]
        try:
            await run()
            backoff = 1
        except Exception as e:
            status = _status_of(e)
            relay_state["provider"] = None
            relay_state["last_error"] = f"{name}: {e}"
            if status in _BLOCKED_STATUS:
                blocked.add(name)
                relay_state["blocked"] = sorted(blocked)
                logger.warning(
                    f"{name} WS가 HTTP {status}로 거부되었습니다(지역 차단 추정). "
                    f"이 공급자를 건너뜁니다."
                )
                idx += 1
                continue
            logger.warning(
                f"{name} WS disconnected: {e}. Reconnecting in {backoff}s..."
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


@router.websocket("/ws/ticks")
async def websocket_ticks(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    logger.info(f"Client connected ({len(clients)} total)")

    # Send latest cached prices immediately
    for msg in latest.values():
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            pass

    try:
        while True:
            # Keep connection alive; client can send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)
        logger.info(f"Client disconnected ({len(clients)} total)")
