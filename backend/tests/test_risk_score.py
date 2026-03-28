"""Tests for risk score computation."""
from app.services.risk_score import compute_risk_score


class TestComputeRiskScore:
    def test_low_volatility_percentage(self):
        """annualized_vol is in percentage form (e.g. 25 = 25%)."""
        preds = [{"annualized_vol": 25}]
        score, label = compute_risk_score(preds)
        assert label == "Low"
        assert 0 <= score <= 25

    def test_moderate_volatility(self):
        preds = [{"annualized_vol": 55}]
        score, label = compute_risk_score(preds)
        assert label == "Moderate"
        assert 25 <= score < 50

    def test_high_volatility(self):
        preds = [{"annualized_vol": 85}]
        score, label = compute_risk_score(preds)
        assert label == "High"
        assert 50 <= score < 75

    def test_extreme_volatility(self):
        preds = [{"annualized_vol": 120}]
        score, label = compute_risk_score(preds)
        assert label == "Extreme"
        assert score >= 75

    def test_empty_predictions(self):
        score, label = compute_risk_score([])
        assert score == 0.0
        assert label == "N/A"

    def test_zero_vol_excluded(self):
        preds = [{"annualized_vol": 0.0}, {"annualized_vol": 50}]
        score, label = compute_risk_score(preds)
        assert score > 0

    def test_all_zero_vol(self):
        preds = [{"annualized_vol": 0.0}, {"annualized_vol": 0.0}]
        score, label = compute_risk_score(preds)
        assert score == 0.0
        assert label == "N/A"

    def test_score_capped_at_100(self):
        preds = [{"annualized_vol": 500}]
        score, _ = compute_risk_score(preds)
        assert score <= 100

    def test_multiple_models_averaged(self):
        preds = [
            {"annualized_vol": 30},
            {"annualized_vol": 40},
            {"annualized_vol": 50},
        ]
        score, label = compute_risk_score(preds)
        # avg = 40 → score = (40-20)/100*100 = 20
        assert 15 <= score <= 25
