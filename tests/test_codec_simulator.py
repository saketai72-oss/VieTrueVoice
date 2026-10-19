import numpy as np
import pytest
import torch

from src.preprocessing.codec_simulator import CodecSimulator


@pytest.fixture
def sample_waveform():
    """Create a 4-second 16kHz compound audio tensor."""
    sr = 16000
    t = np.linspace(0, 4.0, 64000, endpoint=False)
    # Compound signal: 300Hz, 1000Hz, 4000Hz, 6000Hz
    sig = (
        0.3 * np.sin(2 * np.pi * 300 * t)
        + 0.3 * np.sin(2 * np.pi * 1000 * t)
        + 0.2 * np.sin(2 * np.pi * 4000 * t)
        + 0.2 * np.sin(2 * np.pi * 6000 * t)
    ).astype(np.float32)
    return torch.tensor(sig, dtype=torch.float32)


def test_telephony_8khz_simulation(sample_waveform):
    """Verify 8kHz telephony bandwidth simulation (300-3400Hz filter) maintains 64k length."""
    sim = CodecSimulator(sr=16000)
    out = sim.simulate_telephony_8khz(sample_waveform)

    assert isinstance(out, torch.Tensor)
    assert out.shape == sample_waveform.shape
    assert out.dtype == torch.float32
    assert not torch.isnan(out).any()
    assert not torch.isinf(out).any()

    # The high frequencies (> 4000Hz) should be attenuated significantly
    # Let's check with FFT energy above 4000Hz vs original
    fft_orig = np.abs(np.fft.rfft(sample_waveform.numpy()))
    fft_sim = np.abs(np.fft.rfft(out.numpy()))
    freqs = np.fft.rfftfreq(len(sample_waveform), 1 / 16000)

    high_freq_mask = freqs > 3800
    high_energy_orig = np.sum(fft_orig[high_freq_mask] ** 2)
    high_energy_sim = np.sum(fft_sim[high_freq_mask] ** 2)

    assert high_energy_sim < 0.05 * high_energy_orig, "Telephony filter failed to cut high frequencies!"


def test_opus_compression_simulation(sample_waveform):
    """Verify Opus lossy compression simulation preserves shape and produces acoustic changes."""
    sim = CodecSimulator(sr=16000)
    out = sim.simulate_opus(sample_waveform, bitrate_kbps=16)

    assert out.shape == sample_waveform.shape
    assert not torch.isnan(out).any()
    diff = torch.norm(out - sample_waveform).item()
    assert diff > 0.01, "Opus compression produced no modification!"


def test_random_codec_augmentation(sample_waveform):
    """Verify augment_random operates cleanly with probability flag."""
    sim = CodecSimulator(sr=16000)
    # p=0 should return original tensor
    out_orig = sim.augment_random(sample_waveform, p=0.0)
    assert torch.equal(out_orig, sample_waveform)

    # p=1 should apply one of the codecs
    out_aug = sim.augment_random(sample_waveform, p=1.0)
    assert out_aug.shape == (64000,)
    assert not torch.isnan(out_aug).any()


def test_codec_simulator_batch():
    """Verify CodecSimulator works with batched tensors (B, 64000)."""
    batch = torch.randn(2, 64000, dtype=torch.float32)
    sim = CodecSimulator(sr=16000)
    out = sim.augment_random(batch, p=1.0)
    assert out.shape == (2, 64000)
    assert not torch.isnan(out).any()
