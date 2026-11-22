"""Unit tests for confidence calibration, Temperature Scaling, Borderline flag,
anti-saturation guarantees, and multi-window variance penalty in decision logic.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.app.decision import (
    BORDERLINE_THRESHOLD,
    PLATT_SCALE_K,
    T_CALIB,
    DecisionResult,
    classify_score,
    platt_calibrator,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Temperature Scaling & Effective Parameter
# ─────────────────────────────────────────────────────────────────────────────

def test_temperature_scaling_effective_parameters():
    """T_calib is 16.0 and effective k is 1 / 16.0 = 0.0625."""
    assert T_CALIB == 16.0
    assert PLATT_SCALE_K == pytest.approx(0.0625, abs=1e-5)
    assert BORDERLINE_THRESHOLD == 8.0


def test_confidence_at_threshold_is_exactly_50_percent():
    """At raw_score == threshold, posterior confidence must be exactly 50.0%."""
    assert platt_calibrator(0.0, threshold=0.0) == pytest.approx(0.50, abs=1e-4)
    assert platt_calibrator(5.0, threshold=5.0) == pytest.approx(0.50, abs=1e-4)
    assert platt_calibrator(-10.0, threshold=-10.0) == pytest.approx(0.50, abs=1e-4)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Borderline Margin & Anti-Saturation Guarantees
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score_diff", [-8.0, -6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0])
def test_near_threshold_confidence_bounded_in_50_to_75_percent(score_diff):
    """Near threshold (|s - thr| <= 8.0), confidence must stay within [50%, 75%]."""
    conf = platt_calibrator(raw_score=score_diff, threshold=0.0)
    assert 0.50 <= conf <= 0.75, f"Confidence {conf:.4f} outside [0.50, 0.75] at diff={score_diff}"


def test_anti_saturation_moderate_logits():
    """Moderate logits (+10 to +30) must NOT prematurely saturate to 99.9%.

    Under old steep k=0.3569:
      s=+10 gave 97.3%
      s=+20 gave 99.9% (premature saturation)
      s=+30 gave 99.9%
    Under Temperature Scaling T=16.0 (k=0.0625):
      s=+10 gives ~65.1%
      s=+20 gives ~77.7%
      s=+30 gives ~86.7%
    All are strictly < 90.0%.
    """
    conf_10 = platt_calibrator(10.0, threshold=0.0)
    conf_20 = platt_calibrator(20.0, threshold=0.0)
    conf_30 = platt_calibrator(30.0, threshold=0.0)

    assert conf_10 == pytest.approx(0.6514, abs=1e-3)
    assert conf_20 == pytest.approx(0.7773, abs=1e-3)
    assert conf_30 == pytest.approx(0.8670, abs=1e-3)

    assert conf_10 < 0.70
    assert conf_20 < 0.80
    assert conf_30 < 0.90


def test_strong_logits_reach_high_confidence():
    """Only very strong logits (|s| >= 40..48) reach high confidence (> 92% - 95%)."""
    conf_40 = platt_calibrator(40.0, threshold=0.0)
    conf_48 = platt_calibrator(48.0, threshold=0.0)
    conf_extreme = platt_calibrator(100.0, threshold=0.0)

    assert conf_40 >= 0.92
    assert conf_48 >= 0.95
    assert conf_extreme <= 0.9990  # Guardrail prevents 100.0% certainty explosion


# ─────────────────────────────────────────────────────────────────────────────
# 3. Borderline Flag & Risk Level in classify_score
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,threshold,expected_borderline,expected_risk", [
    (0.0, 0.0, True, "BORDERLINE"),
    (4.0, 0.0, True, "BORDERLINE"),
    (-4.0, 0.0, True, "BORDERLINE"),
    (8.0, 0.0, True, "BORDERLINE"),
    (-8.0, 0.0, True, "BORDERLINE"),
    (8.0001, 0.0, False, "NORMAL"),
    (-8.0001, 0.0, False, "NORMAL"),
    (25.0, 0.0, False, "NORMAL"),
    (-30.0, 0.0, False, "NORMAL"),
    (10.0, 5.0, True, "BORDERLINE"),    # diff = 5.0 <= 8.0
    (15.0, 5.0, False, "NORMAL"),       # diff = 10.0 > 8.0
])
def test_classify_score_borderline_flag_and_risk_level(score, threshold, expected_borderline, expected_risk):
    res = classify_score(score, threshold=threshold)
    assert res.is_borderline is expected_borderline
    assert res.risk_level == expected_risk


def test_classify_score_defaults_to_platt_calibrator():
    """classify_score without calibrator argument defaults to platt_calibrator."""
    res = classify_score(10.0, threshold=0.0)
    assert res.confidence_calibrated is True
    assert res.confidence is not None
    assert res.confidence == pytest.approx(0.6514, abs=1e-3)
    assert res.is_bonafide is True
    assert res.prediction == "BONA_FIDE"
    assert res.label == 1


def test_classify_score_allows_explicit_calibrator_none():
    """Explicitly passing calibrator=None leaves confidence None and uncalibrated."""
    res = classify_score(10.0, threshold=0.0, calibrator=None)
    assert res.confidence is None
    assert res.confidence_calibrated is False
    assert res.is_borderline is False
    assert res.risk_level == "NORMAL"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Multi-Window Variance Penalty
# ─────────────────────────────────────────────────────────────────────────────

def test_multi_window_variance_penalty_low_variance_no_discount():
    """When window scores have std <= 6.0, no confidence penalty is applied."""
    consistent_windows = [20.0, 21.0, 19.5, 20.5]  # std = 0.56 <= 6.0
    base_conf = platt_calibrator(20.0, threshold=0.0)
    penalized_conf = platt_calibrator(20.0, threshold=0.0, window_scores=consistent_windows)
    assert penalized_conf == pytest.approx(base_conf, abs=1e-5)


def test_multi_window_variance_penalty_high_variance_discounts_confidence():
    """When window scores have std > 6.0, confidence is discounted towards 0.50."""
    inconsistent_windows = [40.0, 5.0, 30.0, 15.0]  # std = 13.578 > 6.0
    w_std = float(np.std(inconsistent_windows))
    expected_penalty = (w_std - 6.0) * 0.02

    base_conf = platt_calibrator(30.0, threshold=0.0)
    penalized_conf = platt_calibrator(30.0, threshold=0.0, window_scores=inconsistent_windows)

    assert penalized_conf < base_conf
    assert penalized_conf == pytest.approx(base_conf - expected_penalty, abs=1e-4)


def test_multi_window_variance_penalty_floor_at_50_percent():
    """Even under extreme window discrepancy, confidence never drops below 0.50."""
    extreme_discrepancy = [-100.0, 100.0]  # std = 100.0, penalty = (100 - 6) * 0.02 = 1.88
    conf = platt_calibrator(5.0, threshold=0.0, window_scores=extreme_discrepancy)
    assert conf == 0.50


def test_classify_score_forwards_window_scores_to_calibrator():
    """classify_score passes window_scores to platt_calibrator and applies discount."""
    inconsistent_windows = [35.0, 5.0, 30.0, 10.0]
    res_no_win = classify_score(25.0, threshold=0.0)
    res_with_win = classify_score(25.0, threshold=0.0, window_scores=inconsistent_windows)

    assert res_with_win.confidence is not None
    assert res_no_win.confidence is not None
    assert res_with_win.confidence < res_no_win.confidence
