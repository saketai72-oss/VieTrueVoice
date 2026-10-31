"""Unit tests for Pitch & Speed Perturbation augmentation.
Verifies fixed length output (64,000 samples), reproducibility, and numeric stability.
"""

from __future__ import annotations
import numpy as np
import pytest

from src.training.augment import pitch_perturbation


def test_pitch_perturbation_preserves_length():
    rng = np.random.default_rng(42)
    x = np.random.randn(64000).astype(np.float32)
    y = pitch_perturbation(x, rng, semitones_range=(-4.0, 4.0), target_len=64000)
    
    assert isinstance(y, np.ndarray)
    assert y.dtype == np.float32
    assert len(y) == 64000
    assert not np.isnan(y).any()
    assert not np.isinf(y).any()


def test_pitch_perturbation_different_than_original():
    rng = np.random.default_rng(123)
    x = np.sin(2 * np.pi * 440 * np.linspace(0, 4.0, 64000)).astype(np.float32)
    y = pitch_perturbation(x, rng, semitones_range=(-3.0, -1.0), target_len=64000)
    
    # Sóng sau biến đổi phải khác sóng gốc nhưng năng lượng tương đương
    assert not np.allclose(x, y, atol=1e-3)
    assert np.max(np.abs(y)) > 0.0


def test_pitch_perturbation_reproducibility():
    x = np.random.randn(64000).astype(np.float32)
    
    rng1 = np.random.default_rng(999)
    y1 = pitch_perturbation(x, rng1, semitones_range=(-4.0, 4.0), target_len=64000)
    
    rng2 = np.random.default_rng(999)
    y2 = pitch_perturbation(x, rng2, semitones_range=(-4.0, 4.0), target_len=64000)
    
    np.testing.assert_array_equal(y1, y2)


def test_pitch_perturbation_silence_input():
    rng = np.random.default_rng(0)
    silence = np.zeros(64000, dtype=np.float32)
    y = pitch_perturbation(silence, rng, semitones_range=(-4.0, 4.0), target_len=64000)
    
    assert len(y) == 64000
    assert np.max(np.abs(y)) == 0.0
