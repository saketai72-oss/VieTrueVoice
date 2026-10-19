"""Telephony and social media Codec simulator for ViTrueVoice.

Simulates lossy Opus compression (16-32 kbps), AMR narrowband, and PSTN/VoIP 8kHz telephony.
Enables Hypothesis H1 evaluation: robustness under communication channel distortion.
"""

from typing import Union
import numpy as np
from scipy import signal
import torch


class CodecSimulator:
    """Simulates telephony, VoIP, and social media lossy audio compression."""

    def __init__(self, sr: int = 16000):
        self.sr = sr

    def _telephony_8khz_np(self, x: np.ndarray) -> np.ndarray:
        """Simulate 8kHz PSTN phone call with 300Hz-3400Hz bandpass filter."""
        orig_len = len(x)
        # 1. Downsample 16kHz -> 8kHz
        num_8k = orig_len // 2
        downsampled = signal.resample(x, num_8k)

        # 2. Bandpass filter 300Hz - 3400Hz (Nyquist = 4000Hz)
        low_norm = 300.0 / 4000.0
        high_norm = 3400.0 / 4000.0
        b, a = signal.butter(4, [low_norm, high_norm], btype="bandpass")
        filtered_8k = signal.lfilter(b, a, downsampled)

        # 3. Upsample 8kHz -> 16kHz
        upsampled = signal.resample(filtered_8k, orig_len)
        return upsampled.astype(np.float32)

    def _opus_np(self, x: np.ndarray, bitrate_kbps: int = 16) -> np.ndarray:
        """Simulate Opus low-bitrate compression via spectral quantization and band-limiting."""
        orig_len = len(x)
        # Opus at 16kbps limits audio bandwidth to ~6.5kHz
        cutoff_norm = 6500.0 / (self.sr / 2.0)
        b, a = signal.butter(3, cutoff_norm, btype="lowpass")
        bandlimited = signal.lfilter(b, a, x)

        # Frame-level quantization (MDCT / subband quantization emulation)
        frame_size = 320  # 20ms at 16kHz (standard Opus frame)
        n_frames = orig_len // frame_size
        quantized = bandlimited.copy()

        # Step size inversely proportional to bitrate
        q_step = max(0.01, 0.20 / (bitrate_kbps / 8.0))
        for i in range(n_frames):
            idx_start = i * frame_size
            idx_end = idx_start + frame_size
            frame = quantized[idx_start:idx_end]
            quantized[idx_start:idx_end] = np.round(frame / q_step) * q_step

        # Normalization
        peak = np.max(np.abs(quantized)) + 1e-8
        if peak > 1.0:
            quantized = quantized / peak
        return quantized.astype(np.float32)

    def _amr_np(self, x: np.ndarray) -> np.ndarray:
        """Simulate AMR-NB cellular telephony (200Hz - 3400Hz + A-law companding)."""
        telephony = self._telephony_8khz_np(x)
        # 8-bit non-linear quantization
        quantized = np.round(telephony * 127.0) / 127.0
        return quantized.astype(np.float32)

    def simulate_telephony_8khz(self, waveform: torch.Tensor) -> torch.Tensor:
        """Apply 8kHz telephony simulation to 1D or batched tensor."""
        return self._apply_to_tensor(waveform, self._telephony_8khz_np)

    def simulate_opus(self, waveform: torch.Tensor, bitrate_kbps: int = 16) -> torch.Tensor:
        """Apply Opus compression simulation to 1D or batched tensor."""
        fn = lambda arr: self._opus_np(arr, bitrate_kbps=bitrate_kbps)
        return self._apply_to_tensor(waveform, fn)

    def simulate_amr(self, waveform: torch.Tensor) -> torch.Tensor:
        """Apply AMR narrowband telephony simulation to 1D or batched tensor."""
        return self._apply_to_tensor(waveform, self._amr_np)

    def augment_random(self, waveform: torch.Tensor, p: float = 0.5) -> torch.Tensor:
        """Apply random codec transformation with probability p."""
        if np.random.rand() >= p:
            return waveform

        choice = np.random.choice(["telephony", "opus", "amr"])
        if choice == "telephony":
            return self.simulate_telephony_8khz(waveform)
        elif choice == "opus":
            bitrate = int(np.random.choice([16, 24, 32]))
            return self.simulate_opus(waveform, bitrate_kbps=bitrate)
        else:
            return self.simulate_amr(waveform)

    def _apply_to_tensor(self, waveform: torch.Tensor, fn) -> torch.Tensor:
        device = waveform.device
        dtype = waveform.dtype
        x_np = waveform.detach().cpu().numpy()

        if x_np.ndim == 1:
            out_np = fn(x_np)
        else:
            orig_shape = x_np.shape
            flat = x_np.reshape(-1, orig_shape[-1])
            out_list = [fn(row) for row in flat]
            out_np = np.stack(out_list, axis=0).reshape(orig_shape)

        return torch.tensor(out_np, device=device, dtype=dtype)
