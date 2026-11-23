"""Sliding window extraction and multi-window score pooling for ViTrueVoice.

STUBBORN_FACTs:
- Every extracted window tensor has a fixed shape of exactly 64,000 samples (4.0s @ 16kHz).
- Audio shorter than 64,000 samples uses repeat padding (torch.tile), NEVER zero-padding.
- Multi-window inference collates all windows into a single mini-batch (N_windows, 64000)
  for one single batched model forward pass, NEVER sequential single-window forward loops.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import torch


def sliding_windows(
    x: torch.Tensor | np.ndarray,
    win: int = 64000,
    hop: int = 16000,
    dense_slicing: bool = False,
) -> list[torch.Tensor]:
    """Extract fixed-length sliding windows from 1D audio waveform.

    Args:
        x: Input audio waveform (1D torch.Tensor or numpy.ndarray).
        win: Window length in samples (default 64,000 = 4.0s @ 16kHz).
        hop: Hop size between consecutive windows in samples (default 16,000 = 1.0s @ 16kHz).
        dense_slicing: Whether to enforce dense overlap slicing for signals >= 50,000 samples
            (~3.125s) to guarantee at least 2 windows for Asymmetric Veto anomaly detection.

    Returns:
        List of 1D torch.Tensor, each of length `win` and dtype float32.
    """
    if isinstance(x, np.ndarray):
        t = torch.from_numpy(x).to(torch.float32)
    elif isinstance(x, torch.Tensor):
        t = x.to(torch.float32)
    else:
        t = torch.tensor(x, dtype=torch.float32)

    t = t.view(-1)
    sig_len = t.shape[0]

    # Empty audio guard
    if sig_len == 0:
        return [torch.zeros(win, dtype=torch.float32)]

    # Short clip repeat padding (STUBBORN_FACT: repeat padding instead of zero padding)
    if sig_len < win:
        if dense_slicing and sig_len >= 50000:
            repeats = int(np.ceil((win * 2) / sig_len)) + 1
            t_rep = torch.tile(t, (repeats,))
            w1 = t_rep[:win]
            w2 = t_rep[8000 : 8000 + win]
            return [w1, w2]
        repeats = int(np.ceil(win / sig_len))
        padded = torch.tile(t, (repeats,))[:win]
        return [padded]

    # Signal >= win: slide with step `hop`
    starts = list(range(0, sig_len - win + 1, hop))
    windows = [t[s : s + win] for s in starts]

    # Boundary guarantee: if last window does not end at signal tail, append tail window
    if starts[-1] + win < sig_len:
        windows.append(t[-win:])

    # Dense Overlap Slicing guarantee:
    # If sig_len >= 50,000 samples and only 1 window extracted (e.g. when sig_len == win == 64000
    # or starts produced only 1 window and tail window didn't expand count),
    # ensure at least 2 windows exist so Asymmetric Veto can detect local anomalies.
    if len(windows) < 2 and sig_len >= 50000:
        t_rep = torch.tile(t, (2,))
        windows.append(t_rep[min(hop, 8000) : min(hop, 8000) + win])

    return windows


def apply_comfort_dither(
    x: torch.Tensor | np.ndarray,
    noise_std: float = 0.0035,
    seed: int | None = 42,
) -> torch.Tensor:
    """Apply micro comfort noise dither to restore physical acoustic continuity.

    In VoIP and browser WebRTC capture, aggressive noise suppression (ANS/AEC)
    zeroes out ambient room floors, which neural SSL models misinterpret as vocoder artifacts.
    This injects imperceptible Gaussian dither (~-35dB relative to speech RMS) to bridge
    the representation gap without degrading spoof detection accuracy.
    """
    if isinstance(x, np.ndarray):
        t = torch.from_numpy(x).to(torch.float32)
    elif isinstance(x, torch.Tensor):
        t = x.to(torch.float32)
    else:
        t = torch.tensor(x, dtype=torch.float32)

    if t.numel() == 0 or torch.max(torch.abs(t)).item() < 1e-5:
        return t

    if seed is not None:
        g = torch.Generator(device=t.device if t.is_cuda else "cpu")
        g.manual_seed(seed)
        noise = torch.randn(t.shape, generator=g, dtype=torch.float32, device=t.device) * noise_std
    else:
        noise = torch.randn_like(t) * noise_std

    return t + noise


def extract_window_batch(
    x: torch.Tensor | np.ndarray,
    win: int = 64000,
    hop: int = 16000,
    max_windows: int = 5,
    apply_dither: bool = False,
    dither_std: float = 0.0035,
    dense_slicing: bool = True,
) -> torch.Tensor:
    """Extract evenly-spaced sliding windows collated into a 2D batch tensor.

    When the signal produces more windows than `max_windows`, windows are sampled
    evenly across the signal duration to bound inference latency.

    Args:
        x: Input audio waveform.
        win: Window length in samples (default 64,000).
        hop: Hop size in samples (default 16,000).
        max_windows: Maximum number of windows to retain (default 5).
        apply_dither: Whether to apply micro comfort dither.
            NOTE: Only apply dither on live audio captured from WebRTC microphone to
            compensate for noise gating. Hardcode `apply_dither=False` for compressed
            telephony audio and uploaded files to prevent blurring CFM vocoder artifacts.
        dither_std: Standard deviation of comfort dither (default 0.0035).
        dense_slicing: Whether to enforce dense overlap slicing for signals >= 50,000 samples.

    Returns:
        torch.Tensor of shape (N_windows, win) with dtype float32, where 1 <= N_windows <= max_windows.
    """
    windows = sliding_windows(x, win=win, hop=hop, dense_slicing=dense_slicing)

    if len(windows) > max_windows:
        indices = np.linspace(0, len(windows) - 1, max_windows, dtype=int)
        windows = [windows[i] for i in indices]

    if apply_dither:
        windows = [apply_comfort_dither(w, noise_std=dither_std, seed=42) for w in windows]

    return torch.stack(windows, dim=0)


def pool_scores(
    scores: list[float] | np.ndarray | torch.Tensor,
    mode: str = "max",
) -> float:
    """Aggregate window-level scores into a single utterance-level decision score.

    Args:
        scores: Window scores (list, numpy array, or torch tensor).
        mode: Pooling method:
            - 'max': Conservative anti-spoofing (highest score window governs).
            - 'mean': Average score across all temporal windows.
            - 'min': Minimum score across all temporal windows.
            - 'asymmetric_veto' (or 'adaptive'): Consensus Asymmetric Veto pooling. If any
              window shows strong spoof evidence (min < -12.0) and >= 3 windows exist,
              checks whether >= 2 independent windows strongly vote bona fide
              (sorted_s[-2] >= 6.0) to protect with sorted_s[-2]; otherwise drops the
              highest outlier window (trimmed mean) or uses mean (< 3 windows) to
              prevent unvoiced near-zero windows from vetoing spoof detection. If
              min >= -12.0, protects bona fide voice using max-pooling.

    Returns:
        Aggregated utterance score as float.

    Raises:
        ValueError: If scores is empty or if mode is unsupported.
    """
    if scores is None:
        raise ValueError("Cannot pool empty scores")

    if isinstance(scores, torch.Tensor):
        if scores.numel() == 0:
            raise ValueError("Cannot pool empty scores")
        scores_np = scores.detach().cpu().numpy().reshape(-1)
    else:
        scores_np = np.asarray(scores, dtype=np.float64).reshape(-1)
        if scores_np.size == 0:
            raise ValueError("Cannot pool empty scores")

    if mode == "max":
        return float(np.max(scores_np))
    if mode == "mean":
        return float(np.mean(scores_np))
    if mode == "min":
        return float(np.min(scores_np))
    if mode in ("asymmetric_veto", "adaptive"):
        if np.min(scores_np) < -12.0:
            # Strong spoof evidence in at least one voiced segment; verify multi-window bona fide consensus before vetoing.
            if len(scores_np) >= 3:
                sorted_s = np.sort(scores_np)
                if sorted_s[-2] >= 6.0:
                    s_pooled = float(sorted_s[-2])
                else:
                    s_pooled = float(np.mean(sorted_s[:-1]))
            else:
                s_pooled = float(np.mean(scores_np))
        else:
            # No strong spoof evidence; protect bona fide voice using max-pooling
            s_pooled = float(np.max(scores_np))
        return s_pooled

    raise ValueError(
        f"Unsupported pooling mode: '{mode}'. Must be 'max', 'mean', 'min', or 'asymmetric_veto'"
    )


def batch_window_forward(
    model: Any,
    windows_batch: torch.Tensor,
    device: torch.device | str = "cpu",
) -> np.ndarray:
    """Run a single batched model forward pass across all extracted windows.

    STUBBORN_FACT: Never run sequential single-window forward loops.
    Collates all extracted windows into a single mini-batch (N_windows, 64000)
    for one single batched model forward pass to minimize latency.

    Args:
        model: Anti-spoofing model with `.score(batch)` method.
        windows_batch: Tensor of shape (N_windows, 64000).
        device: PyTorch device (CPU or CUDA).

    Returns:
        1D numpy array of scores for each window.
    """
    batch_dev = windows_batch.to(device)
    with torch.inference_mode():
        scores = model.score(batch_dev)

    if isinstance(scores, torch.Tensor):
        scores_np = scores.detach().cpu().numpy()
    else:
        scores_np = np.asarray(scores, dtype=np.float32)

    if scores_np.ndim > 1:
        scores_np = scores_np.squeeze(-1)
    elif scores_np.ndim == 0:
        scores_np = np.array([scores_np.item()], dtype=np.float32)

    return scores_np
