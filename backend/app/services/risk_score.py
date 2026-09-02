import math


def compute_risk_score(predictions: list[dict]) -> tuple[float, str]:
    """Compute composite risk score (0-100) from model predictions."""
    vols = [p["annualized_vol"] for p in predictions if p["annualized_vol"] > 0]
    if not vols:
        return 0.0, "N/A"

    # annualized_vol은 비율(0.44 = 44%)이므로 퍼센트로 환산해야 한다.
    # 환산 없이 비교하면 (0.44 - 20)이 항상 음수라 점수가 늘 0.0/"Low"로 고정된다.
    avg_vol_pct = (sum(vols) / len(vols)) * 100

    # Map annualized vol to 0-100 scale
    # BTC typical range: 30% (calm) to 120%+ (extreme)
    score = min(100, max(0, avg_vol_pct - 20))
    score = round(score, 1)

    if score < 25:
        label = "Low"
    elif score < 50:
        label = "Moderate"
    elif score < 75:
        label = "High"
    else:
        label = "Extreme"

    return score, label
