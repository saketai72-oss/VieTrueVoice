import numpy as np
import pytest
from src.evaluation.metrics import (
    compute_eer, compute_min_dcf, confusion_at_threshold,
    cluster_bootstrap_ci, compute_det_curve,
)


def test_eer_perfect_separation():
    labels = np.array([1, 1, 1, 0, 0, 0])
    scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
    eer, _ = compute_eer(scores, labels)
    assert eer == pytest.approx(0.0, abs=1e-9)


def test_eer_inverted_scores_is_100_percent():
    labels = np.array([1, 1, 1, 0, 0, 0])
    scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    eer, _ = compute_eer(scores, labels)
    assert eer == pytest.approx(1.0, abs=1e-9)


def test_eer_random_near_50_percent():
    rng = np.random.default_rng(0)
    labels = rng.integers(0, 2, 20000)
    scores = rng.normal(size=20000)
    eer, _ = compute_eer(scores, labels)
    assert eer == pytest.approx(0.5, abs=0.03)


def test_eer_tied_scores():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([0.5, 0.5, 0.5, 0.5])
    eer, _ = compute_eer(scores, labels)
    assert eer == pytest.approx(0.5, abs=1e-9)


def test_eer_requires_both_classes():
    with pytest.raises(ValueError):
        compute_eer(np.array([0.1, 0.2]), np.array([1, 1]))


def test_min_dcf_perfect_is_zero():
    labels = np.array([1, 1, 0, 0])
    scores = np.array([0.9, 0.8, 0.2, 0.1])
    assert compute_min_dcf(scores, labels) == pytest.approx(0.0, abs=1e-9)


def test_min_dcf_normalized_upper_bound():
    rng = np.random.default_rng(1)
    labels = rng.integers(0, 2, 5000)
    scores = rng.normal(size=5000)
    assert 0.0 <= compute_min_dcf(scores, labels) <= 1.0 + 1e-9


def test_confusion_matrix_counts():
    labels = np.array([1, 1, 0, 0, 0])
    scores = np.array([0.9, 0.4, 0.6, 0.2, 0.1])
    cm = confusion_at_threshold(scores, labels, threshold=0.5)
    # hàng = nhãn thật (spoof, bonafide), cột = dự đoán (spoof, bonafide)
    assert cm.tolist() == [[2, 1], [1, 1]]


def test_cluster_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(2)
    n = 2000
    labels = rng.integers(0, 2, n)
    scores = labels + rng.normal(scale=0.8, size=n)
    speakers = rng.integers(0, 40, n)
    eer, _ = compute_eer(scores, labels)
    lo, hi = cluster_bootstrap_ci(scores, labels, speakers, n_boot=200, seed=0)
    assert lo <= eer <= hi


def test_cluster_bootstrap_is_reproducible():
    rng = np.random.default_rng(3)
    labels = rng.integers(0, 2, 500)
    scores = rng.normal(size=500) + labels
    speakers = rng.integers(0, 10, 500)
    a = cluster_bootstrap_ci(scores, labels, speakers, n_boot=50, seed=7)
    b = cluster_bootstrap_ci(scores, labels, speakers, n_boot=50, seed=7)
    assert a == b


def test_det_curve_shapes_and_monotonic():
    labels = np.array([1, 1, 1, 0, 0, 0])
    scores = np.array([0.9, 0.6, 0.4, 0.5, 0.3, 0.1])
    far, frr, thr = compute_det_curve(scores, labels)
    assert len(far) == len(frr) == len(thr)
    assert np.all(np.diff(far) <= 1e-12)   # FAR giảm khi ngưỡng tăng
    assert np.all(np.diff(frr) >= -1e-12)  # FRR tăng khi ngưỡng tăng
