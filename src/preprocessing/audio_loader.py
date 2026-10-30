"""Universal in-memory audio loader for ViTrueVoice (Pha 3).

Supports:
- WAV, FLAC, OGG via soundfile fast path
- M4A, AAC, MP3, OPUS, AMR via in-memory ffmpeg pipe fallback
- Format auto-detection based on magic bytes/stream headers (ignores file extension)
- Guaranteed 16kHz mono float32 output
- Compliant with STUBBORN_FACTs (in-memory streaming, repeat padding to 64,000 samples)
"""

from __future__ import annotations
import io
from math import gcd
from pathlib import Path
import subprocess
from typing import Any
import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
import torch


def load_audio(
    source: str | Path | bytes | io.BytesIO,
    target_sr: int = 16000,
) -> np.ndarray:
    """Load audio from file path, raw bytes, or BytesIO into 1D float32 array at target_sr.

    Auto-detects format from header/stream contents, avoiding extension-mismatch errors.
    """
    if isinstance(source, (str, Path)):
        p = Path(source)
        if not p.exists():
            raise FileNotFoundError(f"Audio file not found: {source}")
        with open(p, "rb") as f:
            raw_bytes = f.read()
    elif isinstance(source, io.BytesIO):
        source.seek(0)
        raw_bytes = source.read()
    elif isinstance(source, bytes):
        raw_bytes = source
    else:
        raise TypeError(f"Unsupported audio source type: {type(source)}")

    if not raw_bytes:
        raise ValueError("Audio buffer is empty")

    # 1. Fast Path: soundfile in memory (WAV, FLAC, OGG)
    try:
        buf = io.BytesIO(raw_bytes)
        data, fs = sf.read(buf, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if fs != target_sr:
            g = gcd(int(fs), target_sr)
            data = resample_poly(data, target_sr // g, int(fs) // g).astype(np.float32)
        return data.astype(np.float32)
    except Exception:
        pass

    # 2. Universal In-Memory Fallback: ffmpeg pipe (M4A, AAC, MP3, OPUS, AMR)
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", "pipe:0",
        "-f", "wav",
        "-ar", str(target_sr),
        "-ac", "1",
        "pipe:1"
    ]
    proc = subprocess.run(cmd, input=raw_bytes, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode(errors="ignore").strip()
        raise ValueError(f"Failed to decode audio stream: {err}")

    data, _ = sf.read(io.BytesIO(proc.stdout), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data.astype(np.float32)


def prepare_input_tensor(
    source: str | Path | bytes | io.BytesIO,
    target_len: int = 64000,
    target_sr: int = 16000,
) -> torch.Tensor:
    """Load audio and format as fixed-length 1D float32 tensor via repeat-padding/cropping.

    Complies with STUBBORN_FACT: repeat padding for len < target_len, no zero-padding.
    """
    arr = load_audio(source, target_sr=target_sr)
    if len(arr) == 0:
        arr = np.zeros(target_len, dtype=np.float32)
    elif len(arr) < target_len:
        num_repeats = int(np.ceil(target_len / len(arr)))
        arr = np.tile(arr, num_repeats)[:target_len]
    else:
        arr = arr[:target_len]

    return torch.tensor(arr, dtype=torch.float32)
