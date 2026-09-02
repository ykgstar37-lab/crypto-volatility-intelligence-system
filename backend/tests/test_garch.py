"""Tests for GARCH model fitting services."""
import math

import numpy as np
import pandas as pd
import pytest

from app.services.garch import (
    fit_garch,
    fit_tgarch,
    fit_har_garch,
    fit_har_tgarch_x,
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


class TestHarTgarchXExog:
    """HAR-TGARCH-X는 외생변수(거래량, FNG)를 실제로 적합해야 한다."""

    @staticmethod
    def _series(n=300, seed=0):
        rng = np.random.default_rng(seed)
        idx = pd.date_range("2024-01-01", periods=n, freq="D")
        returns = pd.Series(rng.normal(0, 0.02, n), index=idx)
        volume = pd.Series(rng.lognormal(23, 0.4, n), index=idx)   # 원값 ~1e10
        fng = pd.Series(rng.integers(10, 90, n).astype(float), index=idx)
        return returns, volume, fng

    def test_fits_with_raw_volume(self):
        """원값 거래량(~1e10)이 와도 발산하지 않아야 한다."""
        returns, volume, fng = self._series()
        sigma = fit_har_tgarch_x(returns, volume, fng)
        assert math.isfinite(sigma)
        assert 0 < sigma < 1, f"sigma가 비현실적입니다: {sigma}"

    def test_fits_with_prestandardized_volume(self):
        """routers/volatility.py는 volume을 z-score로 표준화해 넘긴다.

        회귀 방지: 음수가 섞인 입력에 로그를 취해 NaN이 생기면
        적합이 "SVD did not converge"로 실패했다.
        """
        returns, volume, fng = self._series()
        volume_z = (volume - volume.mean()) / volume.std()
        assert (volume_z < 0).any(), "표준화된 입력에는 음수가 있어야 한다"

        sigma = fit_har_tgarch_x(returns, volume_z, fng)
        assert math.isfinite(sigma)
        assert 0 < sigma < 1, f"sigma가 비현실적입니다: {sigma}"

    def test_invariant_to_volume_scale(self):
        """거래량 단위(USD, 백만 USD 등)가 바뀌어도 결과가 같아야 한다.

        z(log(k*x)) = z(log k + log x) = z(log x) 이므로 상수배에 불변이다.
        """
        returns, volume, fng = self._series()
        a = fit_har_tgarch_x(returns, volume, fng)
        b = fit_har_tgarch_x(returns, volume * 1_000_000, fng)
        assert abs(a - b) < 1e-6, f"{a} vs {b}"
