from pathlib import Path
import pytest
from scripts.generate_spoof import sanitize_prompt, validate_audio_duration


def test_sanitize_prompt():
    """Verify input prompt is lowercased and stripped of excessive whitespace."""
    raw = "  ALO MẸ ƠI, chuyển gấp cho con 10 triệu vào số tài khoản này nhé!   "
    clean = sanitize_prompt(raw, max_chars=250)
    assert clean == "alo mẹ ơi, chuyển gấp cho con 10 triệu vào số tài khoản này nhé!"
    assert len(clean) <= 250


def test_sanitize_prompt_max_chars():
    """Verify prompt exceeding max_chars is safely truncated."""
    long_text = "chuyển khoản " * 30  # > 250 chars
    clean = sanitize_prompt(long_text, max_chars=250)
    assert len(clean) <= 250


def test_validate_audio_duration():
    """Verify duration bounds checking (3s - 15s accepted, <1s or >30s rejected)."""
    assert validate_audio_duration(5.5, min_sec=1.0, max_sec=30.0) is True
    assert validate_audio_duration(0.5, min_sec=1.0, max_sec=30.0) is False
    assert validate_audio_duration(35.0, min_sec=1.0, max_sec=30.0) is False
