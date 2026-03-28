"""Tests for GARCH model fitting services."""
import math

import numpy as np
import pytest

from app.services.garch import (
    fit_garch,
    fit_tgarch,
    fit_har_garch,
    predict_all,
    _cache_get,
    _cache_set,
)


@pytest.fixture
def synthetic_returns():
    """Generate synthetic log returns resembling crypto data."""
    rng = np.random.default_rng(42)
    return rng.normal(0, 0.03, size=120)


class TestGarchFitting:
    def test_fit_garch_returns_positive_sigma(self, synthetic_returns):
        sigma = fit_garch(synthetic_returns)
        assert sigma > 0
        assert sigma < 1  # daily sigma should be small

    def test_fit_tgarch_returns_positive_sigma(self, synthetic_returns):
        sigma = fit_tgarch(synthetic_returns)
        assert sigma > 0
        assert sigma < 1

    def test_fit_har_garch_returns_positive_sigma(self, synthetic_returns):
        sigma = fit_har_garch(synthetic_returns)
        assert sigma > 0
        assert sigma < 1

    def test_garch_deterministic(self, synthetic_returns):
        """Same input should give same output."""
        s1 = fit_garch(synthetic_returns)
        s2 = fit_garch(synthetic_returns)
        assert abs(s1 - s2) < 1e-6


class TestPredictAll:
    def test_predict_all_returns_5_models(self, synthetic_returns):
        import pandas as pd

        idx = pd.date_range("2025-01-01", periods=len(synthetic_returns))
        returns = pd.Series(synthetic_returns, index=idx)
        volume = pd.Series(np.random.rand(len(synthetic_returns)), index=idx)
        fng = pd.Series(np.random.randint(10, 90, len(synthetic_returns)), index=idx)

        results = predict_all(returns, volume, fng)
        assert len(results) == 5
        model_names = {r["model"] for r in results}
        assert "GARCH(1,1)" in model_names
        assert "TGARCH" in model_names
        assert "HAR-GARCH" in model_names

    def test_predict_all_has_annualized_vol(self, synthetic_returns):
        import pandas as pd

        idx = pd.date_range("2025-01-01", periods=len(synthetic_returns))
        returns = pd.Series(synthetic_returns, index=idx)

        results = predict_all(returns)
        for r in results:
            assert "sigma" in r
            assert "annualized_vol" in r
            if r["sigma"] > 0:
                expected_ann = r["sigma"] * math.sqrt(365)
                assert abs(r["annualized_vol"] - expected_ann) < 0.01


class TestResultCache:
    def test_cache_set_and_get(self):
        _cache_set("test_key", {"value": 42})
        result = _cache_get("test_key")
        assert result == {"value": 42}

    def test_cache_miss_returns_none(self):
        result = _cache_get("nonexistent_key_xyz")
        assert result is None
