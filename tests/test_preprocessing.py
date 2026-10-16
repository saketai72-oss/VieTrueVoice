import numpy as np
import pytest
import soundfile as sf
import torch

from src.preprocessing.audio_processor import preprocess_audio


@pytest.fixture
def temp_audio_short(tmp_path):
    """Create a 1.5s dummy sine wave audio file (24kHz stereo)."""
    sr = 24000
    duration = 1.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Stereo signal: 440Hz sine wave
    sine = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    stereo = np.column_stack([sine, sine])
    file_path = tmp_path / "short_sample.wav"
    sf.write(str(file_path), stereo, sr)
    return str(file_path)


@pytest.fixture
def temp_audio_long(tmp_path):
    """Create a 6.0s dummy audio file (16kHz mono)."""
    sr = 16000
    duration = 6.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    file_path = tmp_path / "long_sample.wav"
    sf.write(str(file_path), sine, sr)
    return str(file_path)


@pytest.fixture
def temp_audio_with_silence(tmp_path):
    """Create an audio file with 1s silence at start and end."""
    sr = 16000
    silence = np.zeros(int(sr * 1.0), dtype=np.float32)
    t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
    tone = (0.6 * np.sin(2 * np.pi * 500 * t)).astype(np.float32)
    full_signal = np.concatenate([silence, tone, silence])
    file_path = tmp_path / "silence_sample.wav"
    sf.write(str(file_path), full_signal, sr)
    return str(file_path)


def test_preprocess_output_shape_and_type(temp_audio_short):
    """Verify output is a 1D PyTorch float tensor with exactly 64,000 samples (4s at 16kHz)."""
    tensor = preprocess_audio(temp_audio_short, target_sr=16000, max_len=64000)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.dtype == torch.float32
    assert tensor.shape == (64000,)


def test_preprocess_crop_long_audio(temp_audio_long):
    """Verify long audio (> 4s) is cropped to exactly 64,000 samples."""
    tensor = preprocess_audio(temp_audio_long, target_sr=16000, max_len=64000)
    assert tensor.shape == (64000,)


def test_preprocess_zscore_normalization(temp_audio_short):
    """Verify signal is normalized to zero-mean and unit-variance."""
    tensor = preprocess_audio(temp_audio_short, target_sr=16000, max_len=64000)
    mean = tensor.mean().item()
    std = tensor.std().item()
    assert pytest.approx(mean, abs=1e-3) == 0.0
    assert pytest.approx(std, abs=1e-2) == 1.0


def test_silence_trimming(temp_audio_with_silence):
    """Verify that audio with leading/trailing silence is trimmed and padded to 64,000."""
    tensor = preprocess_audio(temp_audio_with_silence, target_sr=16000, max_len=64000)
    assert tensor.shape == (64000,)
    assert not torch.isnan(tensor).any()
