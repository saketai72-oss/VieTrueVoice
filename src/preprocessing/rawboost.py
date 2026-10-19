"""RawBoost time-domain audio data augmentation module.

Implements Linear and non-linear filtering (LnL), Impulsive signal-independent noise (SSI),
and Signal-dependent additive noise (ISD) according to ASVspoof RawBoost specifications.
"""

from typing import Union
import numpy as np
from scipy import signal
import torch


class RawBoost:
    """RawBoost data augmentation operating directly on raw speech waveforms."""

    def __init__(self, algo: int = 5, sr: int = 16000):
        """
        Args:
            algo: RawBoost algorithm mode:
                  1 = LnL (Linear and non-linear filtering)
                  2 = SSI (Impulsive signal-independent noise)
                  3 = LnL + SSI
                  4 = SSI + ISD
                  5 = Full LnL + SSI + ISD (Default)
            sr: Sampling rate (default: 16000 Hz).
        """
        self.algo = algo
        self.sr = sr

    def _apply_lnl(self, x: np.ndarray) -> np.ndarray:
        """Linear and non-linear filtering (randomized frequency distortion)."""
        # Random filter order and cutoff
        cutoff = np.random.uniform(500, self.sr // 2 - 500)
        norm_cutoff = cutoff / (self.sr / 2.0)
        b, a = signal.butter(2, norm_cutoff, btype=np.random.choice(["low", "high"]))
        filtered = signal.lfilter(b, a, x)
        # Mix with original signal
        mix = np.random.uniform(0.3, 0.7)
        out = mix * x + (1.0 - mix) * filtered
        return out.astype(np.float32)

    def _apply_ssi(self, x: np.ndarray, impulse_prob: float = 0.001) -> np.ndarray:
        """Impulsive signal-independent noise (random impulse spikes)."""
        mask = np.random.rand(*x.shape) < impulse_prob
        impulse_amp = np.random.uniform(0.1, 0.5)
        sign = np.random.choice([-1.0, 1.0], size=x.shape)
        impulses = mask * impulse_amp * sign
        return (x + impulses).astype(np.float32)

    def _apply_isd(self, x: np.ndarray, snr_db: float = 20.0) -> np.ndarray:
        """Signal-dependent colored additive noise."""
        signal_power = np.mean(x ** 2) + 1e-8
        noise_power = signal_power / (10 ** (snr_db / 10.0))
        # Signal-dependent envelope
        envelope = np.abs(x) + 0.1
        noise = np.random.normal(0, np.sqrt(noise_power), size=x.shape) * envelope
        return (x + noise).astype(np.float32)

    def process_numpy(self, x: np.ndarray) -> np.ndarray:
        """Apply RawBoost transformations based on selected algo."""
        y = x.copy()
        if self.algo in [1, 3, 5]:
            y = self._apply_lnl(y)
        if self.algo in [2, 3, 4, 5]:
            y = self._apply_ssi(y)
        if self.algo in [4, 5]:
            snr = np.random.uniform(15.0, 30.0)
            y = self._apply_isd(y, snr_db=snr)

        # Normalize back to avoid extreme clipping
        peak = np.max(np.abs(y)) + 1e-8
        if peak > 1.0:
            y = y / peak
        return y.astype(np.float32)

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        """
        Apply RawBoost to a PyTorch tensor.

        Args:
            waveform: Tensor of shape (..., 64000) or (64000,).

        Returns:
            Augmented tensor with identical shape and dtype float32.
        """
        device = waveform.device
        dtype = waveform.dtype
        x_np = waveform.detach().cpu().numpy()

        if x_np.ndim == 1:
            out_np = self.process_numpy(x_np)
        else:
            # Batch mode: process row by row
            orig_shape = x_np.shape
            flat = x_np.reshape(-1, orig_shape[-1])
            out_list = [self.process_numpy(row) for row in flat]
            out_np = np.stack(out_list, axis=0).reshape(orig_shape)

        return torch.tensor(out_np, device=device, dtype=dtype)
