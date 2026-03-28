import math
import time
import warnings

import numpy as np
import pandas as pd
from arch import arch_model
from scipy.stats import norm

warnings.filterwarnings("ignore")

MODEL_NAMES = ["GARCH(1,1)", "TGARCH", "HAR-GARCH", "HAR-TGARCH", "HAR-TGARCH-X"]

_model_cache: dict[str, float] = {}

# Time-based result cache: key -> (timestamp, result)
_result_cache: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str):
    if key in _result_cache:
        ts, result = _result_cache[key]
        if time.time() - ts < _CACHE_TTL:
            return result
    return None


def _cache_set(key: str, result):
    _result_cache[key] = (time.time(), result)


def _compute_har_features(returns: pd.Series) -> pd.DataFrame:
    """Compute HAR realized volatility features: daily, weekly, monthly."""
    rv = returns ** 2
    df = pd.DataFrame({"rv": rv})
    df["rv_d"] = rv
    df["rv_w"] = rv.rolling(7).mean()
    df["rv_m"] = rv.rolling(30).mean()
    df["neg"] = (returns < 0).astype(float) * rv
    df["sigma_lag"] = rv.rolling(5).mean().shift(1)
    return df.dropna()


def fit_garch(returns: np.ndarray) -> float:
    """GARCH(1,1) — basic conditional variance model."""
    r = returns * 100
    model = arch_model(r, vol="Garch", p=1, q=1, dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / 100


def fit_tgarch(returns: np.ndarray) -> float:
    """TGARCH (GJR-GARCH) — asymmetric leverage effect."""
    r = returns * 100
    model = arch_model(r, vol="Garch", p=1, o=1, q=1, dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / 100


def fit_har_garch(returns: np.ndarray) -> float:
    """HAR-GARCH — multi-scale (1,7,30) volatility structure."""
    r = returns * 100
    model = arch_model(r, vol="HARCH", lags=[1, 7, 30], dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / 100


def fit_har_tgarch(returns: pd.Series) -> float:
    """HAR-TGARCH — HAR features + asymmetric GARCH."""
    har = _compute_har_features(returns)
    if len(har) < 60:
        return 0.0

    r = (har["rv_d"] * 100).values
    model = arch_model(r, vol="Garch", p=1, o=1, q=1, dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / 100


def fit_har_tgarch_x(returns: pd.Series, volume: pd.Series, fng: pd.Series) -> float:
    """HAR-TGARCH-X — HAR + asymmetric + exogenous (volume, FNG)."""
    har = _compute_har_features(returns)
    if len(har) < 60:
        return 0.0

    aligned = pd.DataFrame({
        "rv_d": har["rv_d"],
        "vol_lag": volume.reindex(har.index).fillna(method="ffill").shift(1),
        "fng_lag": fng.reindex(har.index).fillna(method="ffill").shift(1),
    }).dropna()

    if len(aligned) < 60:
        return 0.0

    r = (aligned["rv_d"] * 100).values
    exog = aligned[["vol_lag", "fng_lag"]].values

    model = arch_model(r, vol="Garch", p=1, o=1, q=1, dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / 100


def predict_all(returns: pd.Series, volume: pd.Series | None = None, fng: pd.Series | None = None) -> list[dict]:
    """Run all 5 models and return predictions."""
    r_np = returns.values

    results = []
    fitters = [
        ("GARCH(1,1)", lambda: fit_garch(r_np)),
        ("TGARCH", lambda: fit_tgarch(r_np)),
        ("HAR-GARCH", lambda: fit_har_garch(r_np)),
        ("HAR-TGARCH", lambda: fit_har_tgarch(returns)),
    ]

    for name, fn in fitters:
        try:
            sigma = fn()
            ann = sigma * math.sqrt(365)
            results.append({"model": name, "sigma": round(sigma, 6), "annualized_vol": round(ann, 4)})
        except Exception:
            results.append({"model": name, "sigma": 0.0, "annualized_vol": 0.0})

    # HAR-TGARCH-X needs volume and FNG
    try:
        if volume is not None and fng is not None:
            sigma = fit_har_tgarch_x(returns, volume, fng)
        else:
            sigma = 0.0
        ann = sigma * math.sqrt(365)
        results.append({"model": "HAR-TGARCH-X", "sigma": round(sigma, 6), "annualized_vol": round(ann, 4)})
    except Exception:
        results.append({"model": "HAR-TGARCH-X", "sigma": 0.0, "annualized_vol": 0.0})

    # Cache results
    for r in results:
        _model_cache[r["model"]] = r["sigma"]

    return results


def get_cached_predictions() -> dict[str, float]:
    return _model_cache.copy()
