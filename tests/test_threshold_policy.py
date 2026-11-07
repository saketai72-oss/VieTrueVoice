"""Unit tests for BPCER-budgeted decision threshold derivation.

Enforces:
1. derive_threshold calculates the target percentile corresponding to bpcer_budget.
2. Permutation invariance: order of bona fide scores does not affect threshold value.
3. Strict edge case validation: empty input raises ValueError.
4. Budget validation: bpcer_budget must strictly be in range (0.0, 1.0).
5. Interoperability across Python lists, NumPy arrays, and PyTorch tensors.
"""

import numpy as np
import pytest
import torch

from src.app.decision import derive_threshold


# ─────────────────────────────────────────────────────────────────────────────
# 1. Percentile Calculation by BPCER Budget Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_derive_threshold_percentile_budget():
    """Verify derive_threshold computes the exact percentile matching bpcer_budget."""
    # Arrange: 1,000 bona fide scores from a normal distribution
    np.random.seed(42)
    scores_bona = np.random.normal(loc=6.0, scale=2.0, size=1000).tolist()
    budget = 0.005  # 0.5% False Rejection / BPCER budget

    # Act
    thr = derive_threshold(scores_bona, bpcer_budget=budget)

    # Assert: Threshold should match the 0.5th percentile (100 * 0.005)
    expected_thr = float(np.percentile(scores_bona, budget * 100.0))
    assert isinstance(thr, float)
    assert thr == pytest.approx(expected_thr, abs=1e-5)

    # Actual false rejections (bona scores < thr) must be within budget tolerance
    emp_bpcer = np.mean(np.array(scores_bona) < thr)
    assert emp_bpcer <= budget + 1e-3


@pytest.mark.parametrize("budget", [0.001, 0.005, 0.01, 0.02, 0.05, 0.10])
def test_derive_threshold_various_budgets(budget):
    """Verify derive_threshold scales properly across multiple BPCER budgets."""
    # Arrange
    scores = np.linspace(-2.0, 12.0, num=2000)

    # Act
    thr = derive_threshold(scores, bpcer_budget=budget)

    # Assert
    expected = float(np.percentile(scores, budget * 100.0))
    assert thr == pytest.approx(expected, abs=1e-5)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Determinism & Permutation Invariance Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_derive_threshold_permutation_invariance_and_determinism():
    """Verify threshold derivation is deterministic and permutation invariant."""
    # Arrange
    rng = np.random.RandomState(1337)
    original_scores = rng.normal(loc=5.0, scale=3.0, size=500)
    shuffled_scores = original_scores.copy()
    rng.shuffle(shuffled_scores)

    # Act
    thr_orig_1 = derive_threshold(original_scores, bpcer_budget=0.01)
    thr_orig_2 = derive_threshold(original_scores, bpcer_budget=0.01)
    thr_shuffled = derive_threshold(shuffled_scores, bpcer_budget=0.01)

    # Assert
    # Deterministic
    assert thr_orig_1 == thr_orig_2
    # Permutation invariant (independent of order of samples)
    assert thr_orig_1 == pytest.approx(thr_shuffled, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Empty & Degenerate Input Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_derive_threshold_empty_input_raises():
    """Verify empty input sequences raise ValueError."""
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot derive threshold from empty"):
        derive_threshold([], bpcer_budget=0.005)

    with pytest.raises(ValueError, match="Cannot derive threshold from empty"):
        derive_threshold(np.array([]), bpcer_budget=0.005)

    with pytest.raises(ValueError, match="Cannot derive threshold from empty"):
        derive_threshold(torch.tensor([]), bpcer_budget=0.005)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Budget Range Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("invalid_budget", [0.0, -0.01, -1.0, 1.0, 1.5, 2.0])
def test_derive_threshold_invalid_budget_raises(invalid_budget):
    """Verify bpcer_budget outside (0.0, 1.0) raises ValueError."""
    # Arrange
    scores = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Act & Assert
    with pytest.raises(ValueError, match="bpcer_budget must be in range"):
        derive_threshold(scores, bpcer_budget=invalid_budget)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Input Type Interoperability Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_derive_threshold_supported_input_types():
    """Verify function seamlessly accepts list, NumPy array, and PyTorch tensor."""
    # Arrange
    raw_list = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
    np_arr = np.array(raw_list, dtype=np.float32)
    torch_t = torch.tensor(raw_list, dtype=torch.float32)

    # Act
    thr_list = derive_threshold(raw_list, bpcer_budget=0.05)
    thr_np = derive_threshold(np_arr, bpcer_budget=0.05)
    thr_torch = derive_threshold(torch_t, bpcer_budget=0.05)

    # Assert
    assert isinstance(thr_list, float)
    assert isinstance(thr_np, float)
    assert isinstance(thr_torch, float)
    assert thr_list == pytest.approx(thr_np, abs=1e-5)
    assert thr_list == pytest.approx(thr_torch, abs=1e-5)
