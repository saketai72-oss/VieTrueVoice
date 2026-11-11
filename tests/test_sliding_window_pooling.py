"""Unit tests for sliding window extraction and multi-window score pooling.

Enforces:
1. Short clips (< 4.0s) are repeat-padded to exactly 64,000 samples (STUBBORN_FACT).
2. Long clips produce sliding windows with boundary guarantee (last window terminates at signal end).
3. Window capping via max_windows selects evenly spaced windows to bound latency.
4. Every window returned strictly equals 64,000 samples in length.
5. Score pooling supports 'max' (conservative spoof detection) and 'mean' modes.
"""

import numpy as np
import pytest
import torch

from src.preprocessing.pooling import (
    apply_comfort_dither,
    extract_window_batch,
    pool_scores,
    sliding_windows,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Short Clip Repeat Padding Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_sliding_windows_short_clip_repeat_pad():
    """Verify clips < 4.0s are repeat-padded to exactly 64,000 samples in a single window."""
    # Arrange: 2.5s clip (40,000 samples) and 3.84s clip (61,440 samples like SPK_0004_03)
    sr = 16000
    x_2p5s = torch.sin(2 * np.pi * 220 * torch.arange(int(2.5 * sr)) / sr).to(torch.float32)
    x_3p84s = torch.sin(2 * np.pi * 300 * torch.arange(int(3.84 * sr)) / sr).to(torch.float32)

    # Act
    windows_2p5 = sliding_windows(x_2p5s, win=64000, hop=16000)
    windows_3p84 = sliding_windows(x_3p84s, win=64000, hop=16000)
    batch_2p5 = extract_window_batch(x_2p5s, win=64000, hop=16000, max_windows=5)

    # Assert
    assert len(windows_2p5) == 1
    assert windows_2p5[0].shape[-1] == 64000
    # STUBBORN_FACT: repeat padding instead of zero padding
    # The first 40,000 samples match original, sample 40,000 repeats sample 0
    assert torch.allclose(windows_2p5[0][:40000], x_2p5s)
    assert torch.allclose(windows_2p5[0][40000:64000], x_2p5s[:24000])

    assert len(windows_3p84) == 1
    assert windows_3p84[0].shape[-1] == 64000

    assert isinstance(batch_2p5, torch.Tensor)
    assert batch_2p5.shape == (1, 64000)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Long Clip Sliding Windows & Boundary Guarantees
# ─────────────────────────────────────────────────────────────────────────────

def test_sliding_windows_long_clip_boundary():
    """Verify long audio produces sliding windows without index overflow and ends at signal end."""
    # Arrange: 10.0s clip (160,000 samples at 16kHz)
    sr = 16000
    x_10s = torch.arange(160000, dtype=torch.float32)

    # Act: win=64000, hop=16000
    # Expected start indices: 0, 16000, 32000, 48000, 64000, 80000, 96000 (ends at 96000 + 64000 = 160000)
    windows = sliding_windows(x_10s, win=64000, hop=16000)

    # Assert
    assert len(windows) == 7
    for idx, w in enumerate(windows):
        assert w.shape[-1] == 64000
        expected_start = idx * 16000
        assert torch.allclose(w, x_10s[expected_start : expected_start + 64000])

    # Final window terminates precisely at the last sample of the clip
    assert torch.allclose(windows[-1], x_10s[-64000:])


def test_sliding_windows_non_multiple_length_boundary():
    """Verify audio whose length is not an exact hop multiple has final window anchored at the end."""
    # Arrange: 7.2s clip = 115,200 samples
    x_non_mult = torch.arange(115200, dtype=torch.float32)

    # Act
    windows = sliding_windows(x_non_mult, win=64000, hop=16000)

    # Assert
    assert len(windows) >= 2
    for w in windows:
        assert w.shape[-1] == 64000
    # The last window must finish exactly at the last sample (115200)
    assert torch.allclose(windows[-1], x_non_mult[-64000:])


# ─────────────────────────────────────────────────────────────────────────────
# 3. max_windows Cap & Even Spacing Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_window_batch_max_windows_cap():
    """Verify extract_window_batch caps number of windows to max_windows and distributes evenly."""
    # Arrange: 10.0s clip (7 windows raw) and 20.0s clip (17 windows raw)
    x_10s = torch.randn(160000, dtype=torch.float32)
    x_20s = torch.randn(320000, dtype=torch.float32)

    # Act
    batch_5 = extract_window_batch(x_10s, win=64000, hop=16000, max_windows=5)
    batch_20s_5 = extract_window_batch(x_20s, win=64000, hop=16000, max_windows=5)

    # Assert
    assert isinstance(batch_5, torch.Tensor)
    assert batch_5.shape == (5, 64000)
    assert batch_20s_5.shape == (5, 64000)

    # First window corresponds to beginning, last window corresponds to tail
    assert torch.allclose(batch_5[0], x_10s[:64000])
    assert torch.allclose(batch_5[-1], x_10s[-64000:])


def test_extract_window_batch_under_cap():
    """Verify audio producing fewer than max_windows is not truncated or upsampled."""
    # Arrange: 5.0s clip (80,000 samples) -> produces 2 windows (0..64k, 16k..80k)
    x_5s = torch.randn(80000, dtype=torch.float32)

    # Act: max_windows=5
    batch = extract_window_batch(x_5s, win=64000, hop=16000, max_windows=5)

    # Assert
    assert batch.shape == (2, 64000)


# ─────────────────────────────────────────────────────────────────────────────
# 4. STUBBORN_FACT: Strict 64k Sample Length Guarantee
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("duration_sec", [0.5, 1.0, 2.5, 3.84, 4.0, 5.5, 8.0, 10.0])
def test_all_windows_exact_64k_samples_stubborn_fact(duration_sec):
    """STUBBORN_FACT: Every extracted window must have length exactly 64,000 samples."""
    # Arrange
    sr = 16000
    num_samples = int(duration_sec * sr)
    x = torch.randn(num_samples, dtype=torch.float32)

    # Act
    windows = sliding_windows(x, win=64000, hop=16000)
    batch = extract_window_batch(x, win=64000, hop=16000, max_windows=5)

    # Assert
    assert len(windows) >= 1
    for w in windows:
        assert isinstance(w, torch.Tensor)
        assert w.shape == (64000,)
        assert w.dtype == torch.float32

    assert isinstance(batch, torch.Tensor)
    assert batch.dim() == 2
    assert batch.shape[1] == 64000
    assert batch.shape[0] <= 5


# ─────────────────────────────────────────────────────────────────────────────
# 5. Score Pooling 'max' Mode Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_pool_scores_max_mode():
    """Verify max pooling selects the maximum score (conservative anti-spoofing)."""
    # Arrange
    scores = [1.2, 5.8, -0.4]
    single_score = [3.5]

    # Act
    pooled = pool_scores(scores, mode="max")
    pooled_single = pool_scores(single_score, mode="max")

    # Assert
    assert isinstance(pooled, float)
    assert pooled == pytest.approx(5.8)
    assert pooled_single == pytest.approx(3.5)


def test_pool_scores_with_tensor_and_numpy():
    """Verify pool_scores accepts list, numpy array, and torch tensor."""
    # Arrange
    vals = [1.2, 5.8, -0.4]
    np_vals = np.array(vals, dtype=np.float32)
    torch_vals = torch.tensor(vals, dtype=torch.float32)

    # Act & Assert
    assert pool_scores(vals, mode="max") == pytest.approx(5.8)
    assert pool_scores(np_vals, mode="max") == pytest.approx(5.8)
    assert pool_scores(torch_vals, mode="max") == pytest.approx(5.8)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Score Pooling 'mean' Mode & Error Handling Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_pool_scores_mean_mode():
    """Verify mean pooling averages window scores."""
    # Arrange
    scores = [1.0, 2.0, 6.0]

    # Act
    pooled = pool_scores(scores, mode="mean")

    # Assert
    assert isinstance(pooled, float)
    assert pooled == pytest.approx(3.0)


def test_pool_scores_invalid_mode_raises():
    """Verify unsupported pooling mode raises ValueError."""
    # Arrange
    scores = [1.0, 2.0]

    # Act & Assert
    with pytest.raises(ValueError, match="Unsupported pooling mode"):
        pool_scores(scores, mode="invalid_mode")


def test_pool_scores_empty_input_raises():
    """Verify empty scores list/tensor raises ValueError."""
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot pool empty"):
        pool_scores([], mode="max")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Adaptive Comfort Dithering Tests (Dual-Platform WebRTC / Upload Support)
# ─────────────────────────────────────────────────────────────────────────────

def test_apply_comfort_dither_preserves_shape_and_dtype():
    """Verify comfort dither preserves tensor length, shape, and float32 dtype."""
    x = torch.randn(64000, dtype=torch.float32)
    dithered = apply_comfort_dither(x, noise_std=0.0035, seed=42)
    assert isinstance(dithered, torch.Tensor)
    assert dithered.shape == x.shape
    assert dithered.dtype == torch.float32
    assert not torch.allclose(dithered, x)


def test_apply_comfort_dither_silent_tensor_unchanged():
    """Verify silence / empty tensor is preserved without adding phantom noise."""
    zeros = torch.zeros(64000, dtype=torch.float32)
    dithered = apply_comfort_dither(zeros, noise_std=0.0035)
    assert torch.allclose(dithered, zeros)


def test_extract_window_batch_with_dither_flag():
    """Verify extract_window_batch applies dither when apply_dither=True."""
    x = torch.randn(80000, dtype=torch.float32)
    raw_batch = extract_window_batch(x, win=64000, hop=16000, max_windows=5, apply_dither=False)
    dither_batch = extract_window_batch(x, win=64000, hop=16000, max_windows=5, apply_dither=True)
    assert raw_batch.shape == dither_batch.shape == (2, 64000)
    assert not torch.allclose(raw_batch, dither_batch)

