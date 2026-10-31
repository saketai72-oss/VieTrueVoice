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
    source_path: Path | None = None
    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source}")
        with open(source_path, "rb") as f:
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

    # 2. Universal In-Memory Fallback: ffmpeg
    # When source_path exists, prefer it as FFmpeg input because MP4/M4A containers
    # require seeking to parse trailing metadata (moov atom), which fails over stdin pipes.
    input_arg = str(source_path) if source_path is not None else "pipe:0"
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", input_arg,
        "-f", "wav",
        "-ar", str(target_sr),
        "-ac", "1",
        "pipe:1"
    ]
    proc = subprocess.run(
        cmd,
        input=raw_bytes if source_path is None else None,
        capture_output=True
    )

    # If piping bytes failed or returned empty (e.g. non-seekable M4A with trailing moov),
    # use an ephemeral temp file scrubbed immediately after decoding.
    if (proc.returncode != 0 or len(proc.stdout) <= 78) and source_path is None:
        import tempfile, os
        tmp_fd, tmp_file = tempfile.mkstemp(prefix="vitrue_tmp_decode_")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(raw_bytes)
            cmd_tmp = [
                "ffmpeg", "-v", "error",
                "-i", tmp_file,
                "-f", "wav",
                "-ar", str(target_sr),
                "-ac", "1",
                "pipe:1"
            ]
            proc = subprocess.run(cmd_tmp, capture_output=True)
        finally:
            if os.path.exists(tmp_file):
                try: os.unlink(tmp_file)
                except OSError: pass

    if proc.returncode != 0:
        err = proc.stderr.decode(errors="ignore").strip()
        raise ValueError(f"Failed to decode audio stream: {err}")

    if len(proc.stdout) == 0:
        raise ValueError("Decoded audio stream is empty")

    try:
        data, _ = sf.read(io.BytesIO(proc.stdout), dtype="float32", always_2d=False)
    except Exception as exc:
        raise ValueError(f"Failed to parse decoded WAV stream: {exc}")

    if data.ndim > 1:
        data = data.mean(axis=1)

    if len(data) == 0:
        raise ValueError("Decoded audio stream produced 0 samples")

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
