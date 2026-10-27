"""Audio preprocessing module for ViTrueVoice.

Converts input audio to 16kHz mono, trims silence using RMS energy,
fixes length to 64,000 samples (4s) via repeat padding/crop, and normalizes.
"""

import io
from pathlib import Path
from typing import Union
import librosa
import numpy as np
import soundfile as sf
import torch


def preprocess_audio(
    audio_input: Union[str, Path, io.BytesIO, bytes, np.ndarray],
    target_sr: int = 16000,
    max_len: int = 64000,
) -> torch.Tensor:
    """Preprocess audio to fixed-length 16kHz mono tensor.

    Args:
        audio_input: File path, BytesIO stream, raw bytes, or numpy waveform.
        target_sr: Target sampling rate (default: 16000 Hz).
        max_len: Number of sample points (default: 64000 samples = 4 seconds).

    Returns:
        1D torch.Tensor of shape (max_len,) with dtype float32.
    """
    # 1. Load & convert to Mono, resample to target_sr (16kHz)
    if isinstance(audio_input, bytes):
        audio_input = io.BytesIO(audio_input)

    if isinstance(audio_input, (str, Path, io.BytesIO)):
        wav, sr = librosa.load(audio_input, sr=target_sr, mono=True)
    elif isinstance(audio_input, np.ndarray):
        wav = audio_input.astype(np.float32)
        if wav.ndim > 1:
            wav = np.mean(wav, axis=1 if wav.shape[1] < wav.shape[0] else 0)
    else:
        raise TypeError(f"Unsupported audio input type: {type(audio_input)}")

    # 2. Trim silence at start/end using top_db (relative to peak) with 150ms safety margin
    if len(wav) > 512:
        margin_samples = int(target_sr * 0.15)  # 150ms buffer
        _, index = librosa.effects.trim(wav, top_db=25, frame_length=512, hop_length=160)
        start = max(0, index[0] - margin_samples)
        end = min(len(wav), index[1] + margin_samples)
        if end > start:
            wav = wav[start:end]

    # 3. Fixed length: 64,000 samples (4 seconds) via Repeat Padding or Crop
    if len(wav) < max_len:
        if len(wav) == 0:
            wav = np.zeros(max_len, dtype=np.float32)
        else:
            num_repeats = int(np.ceil(max_len / len(wav)))
            wav = np.tile(wav, num_repeats)[:max_len]
    else:
        wav = wav[:max_len]

    # 4. Amplitude Z-score normalization (Zero-mean, Unit-variance)
    std = float(np.std(wav))
    if std > 1e-8:
        wav = (wav - float(np.mean(wav))) / std
    else:
        wav = wav - float(np.mean(wav))

    return torch.tensor(wav, dtype=torch.float32)
