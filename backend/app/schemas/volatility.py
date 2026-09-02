from datetime import date
from pydantic import BaseModel


class PriceCurrent(BaseModel):
    price: float
    change_24h: float
    volume_24h: float
    fng: int | None = None
    fng_label: str | None = None
    timestamp: int


class PriceHistory(BaseModel):
    date: date
    close: float
    volume: float
    fng: int | None = None
    log_return: float | None = None


class ModelPrediction(BaseModel):
    model: str
    sigma: float
    annualized_vol: float
    status: str = "ok"
    error: str | None = None


class VolatilityPredict(BaseModel):
    predictions: list[ModelPrediction]
    risk_score: float
    risk_label: str


class VolatilityCompareRow(BaseModel):
    date: date
    realized: float | None = None
    garch: float | None = None
    tgarch: float | None = None
    har_garch: float | None = None
    har_tgarch: float | None = None
    har_tgarch_x: float | None = None


class BacktestMetric(BaseModel):
    model: str
    mse: float
    rmse: float
    mape: float
    mae: float
    r2: float


class BacktestResult(BaseModel):
    start: date
    end: date
    models: list[BacktestMetric]


class FactorCorrelation(BaseModel):
    """외생변수와 비트코인 지표 간 상관관계 (논문 §4.2 재검증용)."""
    factor: str
    target: str
    pearson_r: float
    p_value: float
    significant: bool
    n: int


class FactorCorrelationResult(BaseModel):
    coin: str
    period_start: date
    period_end: date
    n_days: int
    correlations: list[FactorCorrelation]
