"""Tests for robust universal audio loader (Pha 3).
Verifies in-memory loading, format auto-detection, M4A/AAC decoding,
resampling to 16kHz mono, and length fitting to 64,000 samples.
"""

from __future__ import annotations
import io
import subprocess
import numpy as np
import pytest
import soundfile as sf
import torch

from src.preprocessing.audio_loader import load_audio, prepare_input_tensor


@pytest.fixture
def wav_16k_mono(tmp_path) -> str:
    sr = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    path = tmp_path / "test_16k_mono.wav"
    sf.write(str(path), sine, sr)
    return str(path)


@pytest.fixture
def wav_24k_stereo(tmp_path) -> str:
    sr = 24000
    duration = 1.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    stereo = np.column_stack([sine, sine * 0.8])
    path = tmp_path / "test_24k_stereo.wav"
    sf.write(str(path), stereo, sr)
    return str(path)


@pytest.fixture
def m4a_sample(tmp_path, wav_16k_mono) -> str:
    """Generate a real AAC-LC M4A file via ffmpeg."""
    out_path = tmp_path / "test_aac.m4a"
    cmd = [
        "ffmpeg", "-y", "-i", wav_16k_mono,
        "-ar", "48000", "-ac", "1",
        "-c:a", "aac", "-b:a", "76k",
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out_path)


@pytest.fixture
def renamed_m4a_sample(tmp_path, m4a_sample) -> str:
    """An M4A file deceptively renamed with .wav extension (common user behavior)."""
    with open(m4a_sample, "rb") as f:
        data = f.read()
    renamed_path = tmp_path / "deceptive_audio.wav"
    with open(renamed_path, "wb") as f:
        f.write(data)
    return str(renamed_path)


def test_load_audio_from_wav_path(wav_16k_mono):
    arr = load_audio(wav_16k_mono, target_sr=16000)
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.float32
    assert arr.ndim == 1
    assert len(arr) == 32000


def test_load_audio_from_wav_bytes(wav_16k_mono):
    with open(wav_16k_mono, "rb") as f:
        raw_bytes = f.read()
    arr = load_audio(raw_bytes, target_sr=16000)
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.float32
    assert arr.ndim == 1
    assert len(arr) == 32000


def test_load_audio_from_bytesio(wav_16k_mono):
    with open(wav_16k_mono, "rb") as f:
        raw_bytes = f.read()
    buf = io.BytesIO(raw_bytes)
    arr = load_audio(buf, target_sr=16000)
    assert isinstance(arr, np.ndarray)
    assert len(arr) == 32000


def test_load_audio_stereo_resamples_to_16k_mono(wav_24k_stereo):
    arr = load_audio(wav_24k_stereo, target_sr=16000)
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.float32
    assert arr.ndim == 1
    # 1.5s at 16kHz = 24000 samples
    assert len(arr) == 24000


def test_load_audio_from_m4a_path_and_bytes(m4a_sample):
    # From path
    arr_path = load_audio(m4a_sample, target_sr=16000)
    assert isinstance(arr_path, np.ndarray)
    assert arr_path.dtype == np.float32
    assert arr_path.ndim == 1
    assert len(arr_path) > 0

    # From bytes
    with open(m4a_sample, "rb") as f:
        raw_bytes = f.read()
    arr_bytes = load_audio(raw_bytes, target_sr=16000)
    assert isinstance(arr_bytes, np.ndarray)
    assert len(arr_bytes) == len(arr_path)


def test_load_audio_from_renamed_m4a_ignores_wav_extension(renamed_m4a_sample):
    """File extension is .wav, but internal container is M4A."""
    arr = load_audio(renamed_m4a_sample, target_sr=16000)
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.float32
    assert len(arr) > 0


def test_load_audio_invalid_input():
    with pytest.raises(TypeError):
        load_audio(12345)

    with pytest.raises(ValueError):
        load_audio(b"not a valid audio stream content")


def test_prepare_input_tensor_short_repeat_padding(wav_16k_mono):
    # 2.0s = 32000 samples -> should be repeat padded to 64000
    tensor = prepare_input_tensor(wav_16k_mono, target_len=64000, target_sr=16000)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.dtype == torch.float32
    assert tensor.shape == (64000,)


def test_prepare_input_tensor_long_cropping(wav_16k_mono, tmp_path):
    # Create 6.0s = 96000 samples -> should be cropped to 64000
    sr = 16000
    t = np.linspace(0, 6.0, int(sr * 6.0), endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    path = tmp_path / "long.wav"
    sf.write(str(path), sine, sr)

    tensor = prepare_input_tensor(str(path), target_len=64000, target_sr=16000)
    assert tensor.shape == (64000,)
