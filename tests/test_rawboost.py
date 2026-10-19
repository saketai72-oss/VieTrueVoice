import numpy as np
import pytest
import torch

from src.preprocessing.rawboost import RawBoost


@pytest.fixture
def clean_sine_tensor():
    """Create a 4-second 16kHz sine wave tensor (64,000 samples)."""
    sr = 16000
    t = np.linspace(0, 4.0, 64000, endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return torch.tensor(sine, dtype=torch.float32)


def test_rawboost_shape_and_dtype(clean_sine_tensor):
    """Verify RawBoost preserves 1D tensor shape (64000,) and float32 dtype."""
    rawboost = RawBoost(algo=3, sr=16000)
    augmented = rawboost(clean_sine_tensor)

    assert isinstance(augmented, torch.Tensor)
    assert augmented.shape == clean_sine_tensor.shape
    assert augmented.dtype == torch.float32
    assert not torch.isnan(augmented).any()
    assert not torch.isinf(augmented).any()


def test_rawboost_batch_support():
    """Verify RawBoost supports batched input (B, 64000)."""
    batch = torch.randn(4, 64000, dtype=torch.float32)
    rawboost = RawBoost(algo=5, sr=16000)
    augmented = rawboost(batch)

    assert augmented.shape == (4, 64000)
    assert not torch.isnan(augmented).any()


def test_rawboost_algo_variations(clean_sine_tensor):
    """Verify all RawBoost algorithms (ISD, SSI, LnL) alter the signal without destruction."""
    for algo_id in [1, 2, 3, 4, 5]:
        rawboost = RawBoost(algo=algo_id, sr=16000)
        augmented = rawboost(clean_sine_tensor)

        # Signal should change from clean sine wave
        diff = torch.norm(augmented - clean_sine_tensor).item()
        assert diff > 0.01, f"RawBoost algo {algo_id} did not modify signal!"

        # Energy should remain within reasonable limits
        orig_energy = torch.norm(clean_sine_tensor).item()
        aug_energy = torch.norm(augmented).item()
        assert 0.1 * orig_energy < aug_energy < 5.0 * orig_energy
