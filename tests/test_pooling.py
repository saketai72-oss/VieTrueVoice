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

from src.preprocessing.pooling import (
    extract_window_batch,
    pool_scores,
    sliding_windows,
)


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


def test_dense_overlap_slicing_4p04s_clip_extracts_at_least_two_windows():
    """Verify 4.04s clip (64,640 samples @ 16kHz) extracts >= 2 windows with Dense Overlap Slicing."""
    sr = 16000
    num_samples_4p04 = int(4.04 * sr)  # 64,640 samples
    assert num_samples_4p04 == 64640

    x_4p04 = torch.sin(2 * np.pi * 220 * torch.arange(num_samples_4p04) / sr).to(torch.float32)

    # sliding_windows must extract at least 2 windows
    windows = sliding_windows(x_4p04, win=64000, hop=16000)
    assert len(windows) >= 2
    for w in windows:
        assert isinstance(w, torch.Tensor)
        assert w.shape == (64000,)

    # extract_window_batch must produce a 2D tensor of shape (N >= 2, 64000)
    batch = extract_window_batch(x_4p04, win=64000, hop=16000, max_windows=5, apply_dither=False)
    assert isinstance(batch, torch.Tensor)
    assert batch.dim() == 2
    assert batch.shape[0] >= 2
    assert batch.shape[1] == 64000


def test_dense_overlap_slicing_4p00s_and_near_boundary():
    """Verify 4.00s clip (64,000 samples) and 3.50s clip (56,000 samples) extract >= 2 windows under dense slicing."""
    sr = 16000
    # Exactly 4.00s (64,000 samples)
    x_4p00 = torch.randn(64000, dtype=torch.float32)
    windows_4p00 = sliding_windows(x_4p00, win=64000, hop=16000)
    assert len(windows_4p00) >= 2
    for w in windows_4p00:
        assert w.shape == (64000,)

    batch_4p00 = extract_window_batch(x_4p00, win=64000, hop=16000, max_windows=5, dense_slicing=True)
    assert batch_4p00.shape[0] >= 2
    assert batch_4p00.shape[1] == 64000

    # 3.50s clip (56,000 samples) with dense_slicing=True
    x_3p50 = torch.randn(56000, dtype=torch.float32)
    windows_3p50 = sliding_windows(x_3p50, win=64000, hop=16000, dense_slicing=True)
    assert len(windows_3p50) >= 2
    for w in windows_3p50:
        assert w.shape == (64000,)

    batch_3p50 = extract_window_batch(x_3p50, win=64000, hop=16000, max_windows=5, dense_slicing=True)
    assert batch_3p50.shape[0] >= 2
    assert batch_3p50.shape[1] == 64000


def test_asymmetric_veto_reverses_decision_on_single_negative_window():
    """Verify asymmetric veto reverses verdict from false Bona Fide (+3.2) to Spoof (< 0.0) when 1 window has spoof evidence."""
    # Window 0 has strong localized spoof artifact (-18.0)
    # Window 1 is unvoiced / silent and misleads max-pooling into positive (+3.2)
    scores = [-18.0, 3.2]

    # Max-pooling would select +3.2 (misclassification / APCER failure)
    score_max = pool_scores(scores, mode="max")
    assert score_max == pytest.approx(3.2)
    assert score_max > 0.0  # False Bona Fide

    # Asymmetric Veto must detect the spoof window (< -12.0) and pull the decision into negative territory
    score_veto = pool_scores(scores, mode="asymmetric_veto")
    assert score_veto < 0.0  # Successfully reversed to SPOOF
    assert score_veto == pytest.approx((-18.0 + 3.2) / 2.0)  # -7.4


def test_asymmetric_veto_three_windows_drops_highest_outlier():
    """Verify 3-window spoof clip with an unvoiced positive outlier drops the outlier window via trimmed mean."""
    # Window 0: -22.0 (spoof phoneme)
    # Window 1: -16.0 (spoof phoneme)
    # Window 2: +4.5 (unvoiced pause / ambient room floor)
    scores = [-22.0, -16.0, 4.5]

    score_max = pool_scores(scores, mode="max")
    assert score_max == pytest.approx(4.5)  # Max-pooling would fail

    score_veto = pool_scores(scores, mode="asymmetric_veto")
    # Drops +4.5 outlier, computes mean([-22.0, -16.0]) = -19.0
    assert score_veto == pytest.approx(-19.0)
    assert score_veto < 0.0


def test_asymmetric_veto_consensus_bonafide_multi_window_protection():
    """Bona fide clips with >= 3 windows where >= 2 windows strongly score bona fide (>= 6.0) must be protected via sorted_s[-2]."""
    scores_5win = [-38.7, -4.3, 10.6, 10.9, 21.6]
    s_pooled_5win = pool_scores(scores_5win, mode="asymmetric_veto")
    assert s_pooled_5win == pytest.approx(10.9)
    assert s_pooled_5win > 0.0

    scores_4win = [-31.99, -26.02, 8.09, 12.27]
    s_pooled_4win = pool_scores(scores_4win, mode="asymmetric_veto")
    assert s_pooled_4win == pytest.approx(8.09)
    assert s_pooled_4win > 0.0


def test_asymmetric_veto_single_positive_outlier_still_vetoed():
    """Spoof clip with only 1 positive outlier window (sorted_s[-2] < 6.0) must still be vetoed via trimmed mean."""
    scores = [-22.73, -13.87, 26.49]
    s_pooled = pool_scores(scores, mode="asymmetric_veto")
    assert s_pooled == pytest.approx(-18.30)
    assert s_pooled < 0.0


def test_asymmetric_veto_consensus_threshold_at_6p0():
    """Verify consensus protection threshold at precisely 6.0 for sorted_s[-2]."""
    # Exactly 6.0 -> consensus protection triggers, returns sorted_s[-2] == 6.0
    scores_at_threshold = [-15.0, 6.0, 10.0]
    assert pool_scores(scores_at_threshold, mode="asymmetric_veto") == pytest.approx(6.0)

    # Just below 6.0 -> falls back to trimmed mean of remaining windows
    scores_below_threshold = [-15.0, 5.99, 10.0]
    assert pool_scores(scores_below_threshold, mode="asymmetric_veto") == pytest.approx((-15.0 + 5.99) / 2.0)
