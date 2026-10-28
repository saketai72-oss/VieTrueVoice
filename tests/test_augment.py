import numpy as np
import pytest
from src.training.augment import (
    lnl_convolutive, isd_additive, ssi_additive, make_rawboost,
)

SR = 16000
FNS = [lnl_convolutive, isd_additive, ssi_additive]


def sig(n=SR, seed=0):
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    return (0.3 * np.sin(2 * np.pi * 220 * t) + 0.05 * r.standard_normal(n)).astype(np.float32)


@pytest.mark.parametrize("fn", FNS)
def test_keeps_length_and_finite(fn):
    y = fn(sig(), np.random.default_rng(0))
    assert y.shape == (SR,) and np.isfinite(y).all()


@pytest.mark.parametrize("fn", FNS)
def test_deterministic_given_rng(fn):
    a = fn(sig(), np.random.default_rng(5))
    b = fn(sig(), np.random.default_rng(5))
    assert np.array_equal(a, b)


def test_lnl_preserves_peak_and_changes_signal():
    x = sig()
    y = lnl_convolutive(x, np.random.default_rng(1))
    assert np.max(np.abs(y)) == pytest.approx(np.max(np.abs(x)), rel=1e-6)
    assert not np.allclose(y, x)


def test_ssi_hits_requested_snr():
    x = sig().astype(np.float64)
    y = ssi_additive(x, np.random.default_rng(2), snr_db=(20.0, 20.0))
    snr = 10 * np.log10(np.mean(x ** 2) / np.mean((y - x) ** 2))
    assert snr == pytest.approx(20.0, abs=0.05)


def test_isd_changes_only_a_minority_of_samples():
    x = sig().astype(np.float64)
    y = isd_additive(x, np.random.default_rng(3), p_max=10.0)
    frac = np.mean(y != x)
    assert 0.0 < frac <= 0.12


def test_rawboost_identity_when_all_probs_zero():
    tf = make_rawboost(0, 0, 0, always_one=False)
    x = sig()
    y = tf(x, np.random.default_rng(0))
    assert np.array_equal(y, x) and y.dtype == np.float32


def test_rawboost_always_one_usually_changes_signal():
    tf = make_rawboost(0, 0, 0, always_one=True)
    x = sig()
    changed = [not np.array_equal(tf(x, np.random.default_rng(s)), x) for s in range(20)]
    assert np.mean(changed) > 0.9


def test_rawboost_handles_silence_and_empty():
    tf = make_rawboost(1, 1, 1)
    rng = np.random.default_rng(0)
    assert np.isfinite(tf(np.zeros(1000, np.float32), rng)).all()
    assert len(tf(np.array([], np.float32), rng)) == 0
