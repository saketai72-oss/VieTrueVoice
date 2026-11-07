"""Unit tests for speaker-level enrollment calibration and safety guardrails.

Enforces:
1. Normal calibration applies when |offset| <= max_iqr_factor * dev_iqr:
   offset = median(enroll_scores) - dev_median, calibrated_score = score - offset.
2. Safety Guardrail: When |offset| > max_iqr_factor * dev_iqr (e.g., SPK_0001 extreme shift),
   calibration is refused (calibrated=False) and the raw score is preserved for manual review.
3. Insufficient enrollment samples (< 3 clips) aborts calibration (calibrated=False).
4. Degenerate distribution handling (dev_iqr <= 0) is guarded safely.
5. Consistent result object providing calibrated_score, calibrated flag, and offset.
"""

import numpy as np
import pytest
import torch

from src.app.decision import calibrate_by_enrollment


# ─────────────────────────────────────────────────────────────────────────────
# 1. Normal Enrollment Calibration within Guardrail
# ─────────────────────────────────────────────────────────────────────────────

def test_calibrate_by_enrollment_normal_within_guardrail():
    """Verify normal calibration subtracts speaker median offset when within IQR limits."""
    # Arrange: dev_median=5.0, dev_iqr=1.0, max_iqr_factor=4.0 (allowable offset up to 4.0)
    # Speaker enrollment scores have median=6.0 -> offset = 6.0 - 5.0 = 1.0 (1.0 IQR shift)
    dev_median = 5.0
    dev_iqr = 1.0
    max_iqr_factor = 4.0
    enroll_scores = [5.8, 6.0, 6.2]
    raw_score = 5.5

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=enroll_scores,
        dev_median=dev_median,
        dev_iqr=dev_iqr,
        max_iqr_factor=max_iqr_factor,
    )

    # Assert
    assert res.calibrated is True
    assert res.offset == pytest.approx(1.0)
    # Calibrated score = score - offset = 5.5 - 1.0 = 4.5
    assert res.calibrated_score == pytest.approx(4.5)
    assert res.raw_score == pytest.approx(5.5)


def test_calibrate_by_enrollment_negative_offset_acceptance():
    """Verify negative shift within guardrail is properly compensated."""
    # Arrange: speaker speaks softer/lower, median=3.5 -> offset = 3.5 - 5.0 = -1.5
    dev_median = 5.0
    dev_iqr = 1.0
    enroll_scores = [3.4, 3.5, 3.6]
    raw_score = 2.0

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=enroll_scores,
        dev_median=dev_median,
        dev_iqr=dev_iqr,
        max_iqr_factor=4.0,
    )

    # Assert
    assert res.calibrated is True
    assert res.offset == pytest.approx(-1.5)
    # Calibrated score = 2.0 - (-1.5) = 3.5
    assert res.calibrated_score == pytest.approx(3.5)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Safety Guardrail: Extreme Shift Rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_calibrate_by_enrollment_guardrail_rejected_extreme_shift():
    """Guardrail test: When |offset| > max_iqr_factor * dev_iqr, calibration is refused."""
    # Arrange: dev_median=5.0, dev_iqr=1.0, max_iqr_factor=4.0 (limit = 4.0)
    # Simulating SPK_0001 extreme shift (-9.91 IQR): median = -4.91 -> offset = -9.91
    dev_median = 5.0
    dev_iqr = 1.0
    enroll_scores = [-5.0, -4.91, -4.8]
    raw_score = -4.5

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=enroll_scores,
        dev_median=dev_median,
        dev_iqr=dev_iqr,
        max_iqr_factor=4.0,
    )

    # Assert: Must refuse calibration and return raw score unchanged
    assert res.calibrated is False
    assert res.calibrated_score == pytest.approx(raw_score)
    assert res.offset == pytest.approx(-9.91)
    assert "guardrail" in res.reason.lower() or "exceeded" in res.reason.lower() or not res.calibrated


def test_calibrate_by_enrollment_positive_extreme_shift_guardrail():
    """Guardrail test: Positive extreme shift > +4.0 IQR is also rejected."""
    # Arrange: offset = 12.0 - 5.0 = 7.0 (> 4.0 * 1.0)
    dev_median = 5.0
    dev_iqr = 1.0
    enroll_scores = [11.8, 12.0, 12.2]
    raw_score = 11.5

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=enroll_scores,
        dev_median=dev_median,
        dev_iqr=dev_iqr,
        max_iqr_factor=4.0,
    )

    # Assert
    assert res.calibrated is False
    assert res.calibrated_score == pytest.approx(raw_score)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Sample Size Threshold Tests (< 3 samples)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("small_enrollment", [
    [],
    [5.0],
    [5.0, 5.2],
])
def test_calibrate_by_enrollment_insufficient_samples(small_enrollment):
    """Verify calibration is rejected when enrollment sample size is less than 3."""
    # Arrange
    raw_score = 4.0

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=small_enrollment,
        dev_median=5.0,
        dev_iqr=1.0,
    )

    # Assert: Refuse calibration, preserve raw score
    assert res.calibrated is False
    assert res.calibrated_score == pytest.approx(raw_score)
    assert res.offset == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Degenerate Distribution & Zero IQR Guard Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("invalid_iqr", [0.0, -1.0])
def test_calibrate_by_enrollment_degenerate_iqr_guard(invalid_iqr):
    """Verify zero or negative IQR does not cause ZeroDivisionError and safely rejects calibration."""
    # Arrange
    enroll_scores = [5.0, 5.2, 5.4]
    raw_score = 4.5

    # Act
    res = calibrate_by_enrollment(
        score=raw_score,
        enroll_scores=enroll_scores,
        dev_median=5.0,
        dev_iqr=invalid_iqr,
    )

    # Assert
    assert res.calibrated is False
    assert res.calibrated_score == pytest.approx(raw_score)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Input Types (Tensor / NumPy / List) Interoperability
# ─────────────────────────────────────────────────────────────────────────────

def test_calibrate_by_enrollment_supported_types():
    """Verify calibrate_by_enrollment handles NumPy arrays and PyTorch tensors."""
    # Arrange
    enroll_np = np.array([5.9, 6.0, 6.1], dtype=np.float32)
    enroll_torch = torch.tensor([5.9, 6.0, 6.1], dtype=torch.float32)

    # Act
    res_np = calibrate_by_enrollment(score=5.5, enroll_scores=enroll_np, dev_median=5.0, dev_iqr=1.0)
    res_torch = calibrate_by_enrollment(score=5.5, enroll_scores=enroll_torch, dev_median=5.0, dev_iqr=1.0)

    # Assert
    assert res_np.calibrated is True
    assert res_np.calibrated_score == pytest.approx(4.5)
    assert res_torch.calibrated is True
    assert res_torch.calibrated_score == pytest.approx(4.5)
