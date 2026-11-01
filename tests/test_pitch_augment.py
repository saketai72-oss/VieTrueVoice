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

def test_pitch_perturbation_deep_voice_range():
    rng = np.random.default_rng(2026)
    x = np.random.randn(64000).astype(np.float32)
    y = pitch_perturbation(x, rng, semitones_range=(-7.0, 4.0), target_len=64000)
    assert len(y) == 64000
    assert y.dtype == np.float32
    assert not np.isnan(y).any()


def test_rawboost_transform_with_custom_semitones():
    from src.training.augment import make_rawboost
    rng = np.random.default_rng(42)
    tf = make_rawboost(p_pitch=1.0, semitones_range=(-7.0, 4.0))
    x = np.random.randn(64000).astype(np.float32)
    y = tf(x, rng)
    assert len(y) == 64000
    assert y.dtype == np.float32

def test_dataset_transforms_only_bonafide():
    import pandas as pd
    import soundfile as sf
    from src.training.dataset import ViTrueVoiceDataset

    rng = np.random.default_rng(123)
    # Mock dataframe with 1 spoof (0) and 1 bonafide (1)
    df = pd.DataFrame([
        {"utt_id": "u0", "audio_path": "u0.wav", "speaker_id": "spk0", "label": "spoof", "codec": "clean_16khz", "split": "train"},
        {"utt_id": "u1", "audio_path": "u1.wav", "speaker_id": "spk1", "label": "bonafide", "codec": "clean_16khz", "split": "train"},
    ])

    transformed_labels = []

    def mock_tf(wave, r):
        # Đánh dấu mẫu bị transform bằng cách gán giá trị đặc biệt
        wave_copy = wave.copy()
        wave_copy[0] = 999.0
        return wave_copy

    import tempfile, os
    with tempfile.TemporaryDirectory() as tmp_dir:
        sf.write(os.path.join(tmp_dir, "u0.wav"), np.ones(1000, dtype=np.float32), 16000)
        sf.write(os.path.join(tmp_dir, "u1.wav"), np.ones(1000, dtype=np.float32), 16000)

        ds = ViTrueVoiceDataset(df, audio_root=tmp_dir, target_len=1000, mode="augmented", train=True, transform=mock_tf)
        item0 = ds[0] # spoof
        item1 = ds[1] # bonafide

        # item0 (spoof) KHÔNG được áp mock_tf (wave[0] != 999.0)
        assert item0["wave"][0].item() != 999.0
        # item1 (bonafide) BẮT BUỘC được áp mock_tf (wave[0] == 999.0)
        assert item1["wave"][0].item() == 999.0


def test_loss_weights_clamping():
    from src.training.losses import loss_weights_from_counts
    # Không clamp: 100 spoof vs 1000 bonafide -> raw [0.01, 0.001] -> w ~ [0.909, 0.091]
    w_raw = loss_weights_from_counts(100, 1000)
    assert w_raw[0] > 0.90
    assert w_raw[1] < 0.10

    # Có clamp [0.35, 0.65]
    w_clamped = loss_weights_from_counts(100, 1000, clamp_range=(0.35, 0.65))
    assert w_clamped[0] == pytest.approx(0.65)
    assert w_clamped[1] == pytest.approx(0.35)
