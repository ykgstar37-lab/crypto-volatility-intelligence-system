"""Tests for risk score computation."""
from app.services.risk_score import compute_risk_score


class TestComputeRiskScore:
    def test_low_volatility(self):
        """annualized_vol is a fraction (0.25 = 25%), matching garch.py output
        and the frontend, which renders it as annualized_vol * 100."""
        preds = [{"annualized_vol": 0.25}]
        score, label = compute_risk_score(preds)
        assert label == "Low"
        assert 0 <= score <= 25

    def test_moderate_volatility(self):
        preds = [{"annualized_vol": 0.55}]
        score, label = compute_risk_score(preds)
        assert label == "Moderate"
        assert 25 <= score < 50

    def test_high_volatility(self):
        preds = [{"annualized_vol": 0.85}]
        score, label = compute_risk_score(preds)
        assert label == "High"
        assert 50 <= score < 75

    def test_extreme_volatility(self):
        preds = [{"annualized_vol": 1.20}]
        score, label = compute_risk_score(preds)
        assert label == "Extreme"
        assert score >= 75

    def test_empty_predictions(self):
        score, label = compute_risk_score([])
        assert score == 0.0
        assert label == "N/A"

    def test_zero_vol_excluded(self):
        preds = [{"annualized_vol": 0.0}, {"annualized_vol": 0.50}]
        score, label = compute_risk_score(preds)
        assert score > 0

    def test_all_zero_vol(self):
        preds = [{"annualized_vol": 0.0}, {"annualized_vol": 0.0}]
        score, label = compute_risk_score(preds)
        assert score == 0.0
        assert label == "N/A"

    def test_score_capped_at_100(self):
        preds = [{"annualized_vol": 5.0}]
        score, _ = compute_risk_score(preds)
        assert score <= 100

    def test_multiple_models_averaged(self):
        preds = [
            {"annualized_vol": 0.30},
            {"annualized_vol": 0.40},
            {"annualized_vol": 0.50},
        ]
        score, label = compute_risk_score(preds)
        # avg = 0.40 → 40% → score = 40 - 20 = 20
        assert 15 <= score <= 25

    def test_realistic_btc_vol_is_not_low(self):
        """Regression: garch.py returns fractions. Treating them as percentages
        made (0.43 - 20) negative, pinning every real reading to 0.0 / "Low"."""
        preds = [{"annualized_vol": 0.4312}, {"annualized_vol": 0.3858}]
        score, label = compute_risk_score(preds)
        # avg 40.85% → 20.85. "Low"(<25)인 것은 의도된 보정이다
        # (20% → 0, 120% → 100). 버그는 점수가 늘 0.0이던 것.
        assert score > 0, "realistic BTC volatility must not score 0"
        assert 15 < score < 30
