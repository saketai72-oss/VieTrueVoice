"""Unit tests for multi-window score pooling in src/preprocessing/pooling.py.

Tests:
1. mode="asymmetric_veto" (and alias "adaptive"):
   - Spoof clips with strong negative window(s) and unvoiced near-zero/positive window.
   - Bona fide clips with positive or mildly negative windows (> -12.0) protected by max-pooling.
   - Boundary condition at threshold -12.0.
   - 1, 2, and >=3 window cases.
2. Backwards compatibility for modes "max", "mean", "min".
3. Support for list, numpy.ndarray, and torch.Tensor.
4. Error handling for empty scores or unsupported mode.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from src.preprocessing.pooling import pool_scores


def test_asymmetric_veto_spoof_with_unvoiced_window_trimmed_mean():
    """Spoof clips with >= 3 windows and an unvoiced positive window must drop the positive window and remain negative."""
    # 3 windows: 2 strong spoof voiced (-25.0, -20.0) and 1 unvoiced positive (+3.0)
    scores = [-25.0, -20.0, 3.0]
    # np.min < -12.0 and len >= 3: trimmed mean drops +3.0 -> mean([-25.0, -20.0]) = -22.5
    s_pooled = pool_scores(scores, mode="asymmetric_veto")
    assert s_pooled == pytest.approx(-22.5)
    assert s_pooled < 0.0

    # 4 windows: drop single highest outlier window (+4.0)
    scores_4 = [-30.0, -25.0, -20.0, 4.0]
    s_pooled_4 = pool_scores(scores_4, mode="asymmetric_veto")
    assert s_pooled_4 == pytest.approx((-30.0 - 25.0 - 20.0) / 3.0)
    assert s_pooled_4 < 0.0


def test_asymmetric_veto_spoof_with_fewer_than_three_windows():
    """Spoof clips with < 3 windows must average the scores when min < -12.0."""
    # 2 windows: one voiced spoof (-25.0), one unvoiced (+3.0)
    scores_2 = [-25.0, 3.0]
    s_pooled_2 = pool_scores(scores_2, mode="asymmetric_veto")
    assert s_pooled_2 == pytest.approx((-25.0 + 3.0) / 2.0)
    assert s_pooled_2 < 0.0

    # 1 window: single strong spoof (-18.0)
    scores_1 = [-18.0]
    s_pooled_1 = pool_scores(scores_1, mode="asymmetric_veto")
    assert s_pooled_1 == pytest.approx(-18.0)


def test_asymmetric_veto_bonafide_protection():
    """Bona fide clips with all positive or mildly negative windows (>= -12.0) must use max-pooling."""
    # All positive
    scores_pos = [1.5, 5.2, 3.0]
    assert pool_scores(scores_pos, mode="asymmetric_veto") == pytest.approx(5.2)

    # Mildly negative windows (e.g. background noise or unvoiced consonants, min >= -12.0)
    scores_mild = [-5.0, 2.0, 4.5]
    assert pool_scores(scores_mild, mode="asymmetric_veto") == pytest.approx(4.5)

    scores_boundary = [-11.99, -2.0, 1.0]
    assert pool_scores(scores_boundary, mode="asymmetric_veto") == pytest.approx(1.0)


def test_asymmetric_veto_threshold_boundary():
    """Verify threshold at precisely -12.0."""
    # Exactly -12.0 -> not strictly < -12.0 -> falls into else (max-pooling)
    scores_at_threshold = [-12.0, 2.0, 5.0]
    assert pool_scores(scores_at_threshold, mode="asymmetric_veto") == pytest.approx(5.0)

    # Slightly below -12.0 -> triggers veto logic
    scores_below_threshold = [-12.01, 2.0, 5.0]
    # Trimmed mean drops 5.0: mean([-12.01, 2.0]) = -5.005
    assert pool_scores(scores_below_threshold, mode="asymmetric_veto") == pytest.approx((-12.01 + 2.0) / 2.0)


def test_asymmetric_veto_adaptive_alias():
    """Verify 'adaptive' is a full alias of 'asymmetric_veto'."""
    scores_spoof = [-25.0, -20.0, 3.0]
    scores_bona = [-3.0, 2.0, 6.0]

    assert pool_scores(scores_spoof, mode="adaptive") == pool_scores(scores_spoof, mode="asymmetric_veto")
    assert pool_scores(scores_bona, mode="adaptive") == pool_scores(scores_bona, mode="asymmetric_veto")


def test_pool_scores_min_mode():
    """Verify min pooling mode selects the lowest score."""
    scores = [1.5, -3.2, 5.0]
    assert pool_scores(scores, mode="min") == pytest.approx(-3.2)


def test_pool_scores_max_and_mean_modes():
    """Verify backwards compatibility of max and mean modes."""
    scores = [1.0, 5.0, 9.0]
    assert pool_scores(scores, mode="max") == pytest.approx(9.0)
    assert pool_scores(scores, mode="mean") == pytest.approx(5.0)


def test_pool_scores_default_is_max():
    """Verify default pooling mode is max-pooling for production anti-spoofing."""
    scores = [1.0, 5.0, 9.0]
    assert pool_scores(scores) == pytest.approx(9.0)
    # Even if scores contain negative values with min < -12.0, default max mode takes maximum
    scores_with_low = [-25.0, 2.0, 4.0]
    assert pool_scores(scores_with_low) == pytest.approx(4.0)


@pytest.mark.parametrize("mode", ["max", "mean", "min", "asymmetric_veto", "adaptive"])
def test_pool_scores_input_types(mode):
    """Verify pool_scores accepts list, numpy array, and torch tensor."""
    vals = [-15.0, -10.0, 2.0]
    list_res = pool_scores(vals, mode=mode)
    np_res = pool_scores(np.array(vals, dtype=np.float32), mode=mode)
    tensor_res = pool_scores(torch.tensor(vals, dtype=torch.float32), mode=mode)

    assert isinstance(list_res, float)
    assert isinstance(np_res, float)
    assert isinstance(tensor_res, float)
    assert list_res == pytest.approx(np_res)
    assert list_res == pytest.approx(tensor_res)


def test_pool_scores_empty_input_raises():
    """Verify empty input raises ValueError."""
    with pytest.raises(ValueError, match="Cannot pool empty"):
        pool_scores([], mode="asymmetric_veto")
    with pytest.raises(ValueError, match="Cannot pool empty"):
        pool_scores(np.array([]), mode="asymmetric_veto")
    with pytest.raises(ValueError, match="Cannot pool empty"):
        pool_scores(torch.empty(0), mode="asymmetric_veto")


def test_pool_scores_unsupported_mode_raises():
    """Verify unsupported mode raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported pooling mode"):
        pool_scores([1.0, 2.0], mode="unknown_mode")
