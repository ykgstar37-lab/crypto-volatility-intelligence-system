"""Tests for API endpoints."""
from datetime import date, timedelta

import numpy as np
import pytest

from app.models.price import CoinDaily


def _seed_data(db, symbol="BTC", days=120):
    """Insert synthetic price data for testing. Skips existing dates."""
    from sqlalchemy import select

    rng = np.random.default_rng(42 if symbol == "BTC" else 99)
    base_price = {"BTC": 60000, "ETH": 3000, "SOL": 100}[symbol]
    prices = base_price + np.cumsum(rng.normal(0, base_price * 0.02, days))

    # Get existing dates to avoid conflicts
    existing = set(
        r[0] for r in db.execute(
            select(CoinDaily.date).where(CoinDaily.symbol == symbol)
        ).all()
    )

    for i in range(days):
        d = date.today() - timedelta(days=days - i)
        if d in existing:
            continue

        close = float(max(prices[i], 1))
        prev_close = float(max(prices[i - 1], 1)) if i > 0 else close
        log_return = float(np.log(close / prev_close)) if i > 0 else 0.0

        row = CoinDaily(
            symbol=symbol,
            date=d,
            open=close * 0.99,
            high=close * 1.02,
            low=close * 0.98,
            close=close,
            volume=float(rng.uniform(1e9, 5e9)),
            fng=int(rng.integers(10, 90)),
            log_return=log_return,
        )
        db.add(row)
    db.commit()


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestPriceEndpoints:
    def test_history_returns_list(self, client, db):
        _seed_data(db, "BTC", 120)
        resp = client.get("/api/price/history?coin=BTC&days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 30

    def test_history_different_coins(self, client, db):
        _seed_data(db, "BTC", 120)
        _seed_data(db, "ETH", 120)
        btc = client.get("/api/price/history?coin=BTC&days=10").json()
        eth = client.get("/api/price/history?coin=ETH&days=10").json()
        if btc and eth:
            assert btc[0]["close"] != eth[0]["close"]

    def test_history_invalid_coin_rejected(self, client):
        resp = client.get("/api/price/history?coin=DOGE")
        assert resp.status_code == 422


class TestVolatilityEndpoints:
    def test_predict_returns_models(self, client, db):
        _seed_data(db, "BTC", 120)
        resp = client.get("/api/volatility/predict?coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data
        assert "risk_score" in data
        assert "risk_label" in data

    def test_predict_per_coin(self, client, db):
        _seed_data(db, "ETH", 120)
        resp = client.get("/api/volatility/predict?coin=ETH")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["predictions"]) > 0


class TestSignalEndpoints:
    def test_signal_returns_structure(self, client, db):
        _seed_data(db, "BTC", 120)
        resp = client.get("/api/signal?coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert "signal" in data
        assert data["signal"] in ("buy", "sell", "neutral")
        assert "score" in data
        assert "reasons" in data

    def test_leaderboard_returns_list(self, client, db):
        _seed_data(db, "BTC", 120)
        resp = client.get("/api/signal/leaderboard?coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_signal_accuracy_structure(self, client, db):
        _seed_data(db, "BTC", 120)
        resp = client.get("/api/signal/accuracy?coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "accuracy" in data


class TestBacktestEndpoint:
    def test_backtest_returns_models(self, client, db):
        _seed_data(db, "BTC", 120)
        start = (date.today() - timedelta(days=90)).isoformat()
        end = date.today().isoformat()
        resp = client.get(f"/api/backtest?start={start}&end={end}&coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data

    def test_backtest_short_period_empty(self, client, db):
        _seed_data(db, "BTC", 120)
        start = (date.today() - timedelta(days=10)).isoformat()
        end = date.today().isoformat()
        resp = client.get(f"/api/backtest?start={start}&end={end}&coin=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert data["models"] == []
