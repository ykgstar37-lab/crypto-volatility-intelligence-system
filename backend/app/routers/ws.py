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
from typing import Set

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Connected dashboard clients ──
clients: Set[WebSocket] = set()

# ── Latest prices (for newly connected clients) ──
latest: dict[str, dict] = {}

BINANCE_WS = "wss://stream.binance.com:9443/ws"
STREAMS = ["btcusdt@trade", "ethusdt@trade", "solusdt@trade"]
SYMBOL_MAP = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}


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


async def binance_listener():
    """Connect to Binance combined stream and relay ticks."""
    url = f"{BINANCE_WS}/{'/'.join(STREAMS)}"
    while True:
        try:
            async with websockets.connect(url) as ws:
                logger.info(f"Connected to Binance WebSocket: {STREAMS}")
                async for raw in ws:
                    try:
                        data = json.loads(raw)
                        # Combined stream wraps in {"stream": ..., "data": ...}
                        if "data" in data:
                            data = data["data"]

                        symbol_raw = data.get("s", "")  # e.g. "BTCUSDT"
                        symbol = SYMBOL_MAP.get(symbol_raw, symbol_raw)
                        price = float(data.get("p", 0))
                        ts = data.get("T", 0)

                        if not price:
                            continue

                        msg = {
                            "type": "tick",
                            "symbol": symbol,
                            "price": price,
                            "ts": ts,
                        }
                        latest[symbol] = msg
                        await broadcast(msg)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except Exception as e:
            logger.warning(f"Binance WS disconnected: {e}. Reconnecting in 3s...")
            await asyncio.sleep(3)


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
