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


# HAR 계열은 수익률이 아니라 실현변동성(rv_d, std~0.0016)에 적합한다.
# 관례대로 ×100만 하면 std가 0.16이라 MLE 옵티마이저가 반복 한계에 걸려
# 수렴하지 못한다(convergence_flag=9). ×1000이면 std~1.6으로 수렴한다.
_HAR_SCALE = 1000


def fit_har_tgarch(returns: pd.Series) -> float:
    """HAR-TGARCH — HAR features + asymmetric GARCH."""
    har = _compute_har_features(returns)
    if len(har) < 60:
        return 0.0

    r = (har["rv_d"] * _HAR_SCALE).values
    model = arch_model(r, vol="Garch", p=1, o=1, q=1, dist="t", rescale=False)
    res = model.fit(disp="off", show_warning=False)
    forecast = res.forecast(horizon=1)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / _HAR_SCALE


def _rescale(col: np.ndarray) -> np.ndarray:
    """외생변수를 평균 0, 표준편차 1로 맞춘다.

    호출부에 따라 원값이 올 수도(routers는 volume을 이미 z-score 표준화해서
    넘기고, 테스트나 다른 호출부는 원값을 넘긴다) 있으므로 둘 다 견뎌야 한다.
    전부 양수일 때만 로그로 왜도를 줄인다 — 이미 표준화된 값에 로그를 취하면
    음수 구간이 NaN이 되어 적합이 "SVD did not converge"로 실패한다.
    """
    col = np.asarray(col, dtype=float)
    if np.all(col > 0):
        col = np.log(col)
    sd = col.std()
    return (col - col.mean()) / (sd if sd > 0 else 1.0)


def fit_har_tgarch_x(returns: pd.Series, volume: pd.Series, fng: pd.Series) -> float:
    """HAR-TGARCH-X — HAR + asymmetric + exogenous (volume, FNG)."""
    har = _compute_har_features(returns)
    if len(har) < 60:
        return 0.0

    aligned = pd.DataFrame({
        "rv_d": har["rv_d"],
        "vol_lag": volume.reindex(har.index).ffill().shift(1),
        "fng_lag": fng.reindex(har.index).ffill().shift(1),
    }).dropna()

    if len(aligned) < 60:
        return 0.0

    r = (aligned["rv_d"] * _HAR_SCALE).values

    # 거래량 원값(~1e10)과 FNG(0~100)를 그대로 넣으면 LS 회귀가 발산한다
    # (예측 분산이 1e16까지 튄다). 스케일을 맞춰서 넘긴다.
    exog = np.column_stack([
        _rescale(aligned["vol_lag"].values.astype(float)),
        _rescale(aligned["fng_lag"].values.astype(float)),
    ])
    if not np.isfinite(exog).all():
        return 0.0

    # mean="LS"가 필수다. arch_model의 기본 평균모형은 ConstantMean이고,
    # ConstantMean은 x=를 조용히 무시해서 외생변수가 실제로 적합되지 않는다
    # (그 상태로 forecast(x=...)를 부르면 "model does not contain any
    # exogenous variables" 에러가 난다). LS로 지정해야 x0, x1이 추정된다.
    model = arch_model(
        r, x=exog, mean="LS", vol="Garch", p=1, o=1, q=1, dist="t", rescale=False
    )
    res = model.fit(disp="off", show_warning=False)

    # forecast의 x는 외생변수가 2개 이상이면 (n_exog, nobs, horizon) 3차원이어야 한다.
    # 마지막 관측 exog를 예측 시점 값으로 사용한다.
    n_exog = exog.shape[1]
    last_exog = np.tile(exog[-1].reshape(n_exog, 1, 1), (1, len(r), 1))
    forecast = res.forecast(horizon=1, x=last_exog, reindex=False)
    sigma2 = forecast.variance.values[-1, 0]
    return math.sqrt(sigma2) / _HAR_SCALE


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
            results.append({"model": name, "sigma": round(sigma, 6), "annualized_vol": round(ann, 4), "status": "ok"})
        except Exception as e:
            results.append({"model": name, "sigma": 0.0, "annualized_vol": 0.0, "status": "error", "error": str(e)})

    # HAR-TGARCH-X needs volume and FNG
    try:
        if volume is not None and fng is not None:
            sigma = fit_har_tgarch_x(returns, volume, fng)
        else:
            sigma = 0.0
        ann = sigma * math.sqrt(365)
        status = "ok" if sigma > 0 else "no_data"
        results.append({"model": "HAR-TGARCH-X", "sigma": round(sigma, 6), "annualized_vol": round(ann, 4), "status": status})
    except Exception as e:
        results.append({"model": "HAR-TGARCH-X", "sigma": 0.0, "annualized_vol": 0.0, "status": "error", "error": str(e)})

    # Cache results
    for r in results:
        _model_cache[r["model"]] = r["sigma"]

    return results


def get_cached_predictions() -> dict[str, float]:
    return _model_cache.copy()
