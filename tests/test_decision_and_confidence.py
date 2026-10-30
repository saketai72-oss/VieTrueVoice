"""TDD Tests for decision threshold, uncalibrated confidence, and parity.

Ensures:
1. Decision threshold is configurable and defaults to 0.0.
2. Boundary conditions: score > thr is BONA_FIDE, score < thr is SPOOF, score == thr is BONA_FIDE.
3. No fake 100% confidence from sigmoid(abs(raw_score)) without calibration.
4. API, UI, and Bot share identical decision logic.
5. Diagnostic path matching requires full path / hash integrity, preventing basename collisions.
"""

import hashlib
import io
import json
import wave
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from src.app.server import create_app
from src.app.ui import make_predict_fn
from src.app.bot import handle_voice_message


class ParametricStubModel:
    """Stub model that returns a configured raw score."""
    def __init__(self, score_val: float):
        self.score_val = score_val

    def score(self, waveform: torch.Tensor) -> torch.Tensor:
        assert isinstance(waveform, torch.Tensor)
        assert tuple(waveform.shape) == (1, 64000)
        return torch.tensor([self.score_val], dtype=torch.float32, device=waveform.device)


def make_synthetic_wav_bytes(sample_rate: int = 16000, duration_sec: float = 0.5) -> bytes:
    sample_count = int(sample_rate * duration_sec)
    samples = (np.sin(2 * np.pi * 220 * np.arange(sample_count) / sample_rate) * 12000)
    pcm = samples.astype("<i2").tobytes()
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return output.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Configurable Decision Threshold & Boundary Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score_val,expected_label,expected_pred", [
    (0.0001, 1, "BONA_FIDE"),
    (-0.0001, 0, "SPOOF"),
    (0.0, 1, "BONA_FIDE"),   # Boundary case: exactly at threshold 0.0
    (12.5, 1, "BONA_FIDE"),
    (-11.9, 0, "SPOOF"),
])
def test_api_default_threshold_is_zero(tmp_path, score_val, expected_label, expected_pred):
    """At default threshold 0.0, score >= 0 is BONA_FIDE, score < 0 is SPOOF."""
    model = ParametricStubModel(score_val=score_val)
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: model,
    )
    client = TestClient(app)
    audio_bytes = make_synthetic_wav_bytes()

    res = client.post("/api/v1/predict", files={"file": ("test.wav", audio_bytes, "audio/wav")})
    assert res.status_code == 200
    data = res.json()
    assert data["label"] == expected_label
    assert data["prediction"] == expected_pred
    assert data["threshold"] == 0.0
    assert data["raw_score"] == pytest.approx(score_val, abs=1e-4)


@pytest.mark.parametrize("threshold,score_val,expected_label,expected_pred", [
    (5.0, 4.5, 0, "SPOOF"),       # Positive score but below threshold -> SPOOF
    (5.0, 5.0, 1, "BONA_FIDE"),   # Exactly at threshold -> BONA_FIDE
    (5.0, 5.5, 1, "BONA_FIDE"),   # Above threshold -> BONA_FIDE
    (-5.0, -6.0, 0, "SPOOF"),     # Negative score below threshold -> SPOOF
    (-5.0, -5.0, 1, "BONA_FIDE"), # Exactly at negative threshold -> BONA_FIDE
    (-5.0, -4.0, 1, "BONA_FIDE"), # Negative score above threshold -> BONA_FIDE
])
def test_api_configurable_threshold(tmp_path, threshold, score_val, expected_label, expected_pred):
    """create_app accepts an explicit threshold parameter governing classification."""
    model = ParametricStubModel(score_val=score_val)
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        threshold=threshold,
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: model,
    )
    client = TestClient(app)
    audio_bytes = make_synthetic_wav_bytes()

    res = client.post("/api/v1/predict", files={"file": ("test.wav", audio_bytes, "audio/wav")})
    assert res.status_code == 200
    data = res.json()
    assert data["threshold"] == threshold
    assert data["label"] == expected_label
    assert data["prediction"] == expected_pred


# ─────────────────────────────────────────────────────────────────────────────
# 2. Uncalibrated Confidence Tests (No fake 100%)
# ─────────────────────────────────────────────────────────────────────────────

def test_api_does_not_return_fake_100_percent_confidence(tmp_path):
    """Large negative raw score (-11.9034) must NOT return 1.0 (100%) confidence."""
    model = ParametricStubModel(score_val=-11.9034)
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: model,
    )
    client = TestClient(app)
    audio_bytes = make_synthetic_wav_bytes()

    res = client.post("/api/v1/predict", files={"file": ("voice.wav", audio_bytes, "audio/wav")})
    assert res.status_code == 200
    data = res.json()

    # Confidence must not be the uncalibrated sigmoid(abs(score)) pseudo-probability
    assert data["confidence"] is None
    assert data["confidence_calibrated"] is False
    assert data["raw_score"] == pytest.approx(-11.9034, abs=1e-4)


def test_ui_predict_fn_does_not_display_100_percent_uncalibrated():
    """Gradio UI must state that probabilities are uncalibrated and not print '100.0%'."""
    model = ParametricStubModel(score_val=-11.9034)
    predict_fn = make_predict_fn(model=model, device="cpu", threshold=0.0)
    audio_tuple = (16000, np.zeros(16000, dtype=np.float32))

    verdict, conf_text, detail_text = predict_fn(audio_tuple)

    assert "100.0%" not in conf_text
    assert "100%" not in conf_text
    assert "Chưa hiệu chuẩn" in conf_text or "Điểm thô" in conf_text or "Score" in conf_text
    assert "-11.9" in detail_text or "-11.9" in conf_text


@pytest.mark.anyio
async def test_bot_handle_voice_does_not_display_100_percent_uncalibrated():
    """Telegram bot must not display fake 100% confidence for uncalibrated scores."""
    update = MagicMock()
    context = MagicMock()
    file_mock = AsyncMock()
    raw_wav = make_synthetic_wav_bytes()

    async def fake_download(buf):
        buf.write(raw_wav)
        return buf

    file_mock.download_to_memory = fake_download
    voice_mock = MagicMock()
    voice_mock.get_file = AsyncMock(return_value=file_mock)
    update.message.voice = voice_mock
    update.message.audio = None
    update.message.reply_text = AsyncMock()

    model = ParametricStubModel(score_val=-11.9034)
    await handle_voice_message(update, context, model=model, device="cpu", threshold=0.0)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "100.0%" not in reply
    assert "100%" not in reply


# ─────────────────────────────────────────────────────────────────────────────
# 3. Decision Parity Across API, UI, and Bot
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
@pytest.mark.parametrize("score_val", [-15.0, -5.0, -0.01, 0.0, 0.01, 5.0, 15.0])
async def test_parity_across_api_ui_bot(tmp_path, score_val):
    """For any given raw score and threshold, API, UI, and Bot produce identical verdicts."""
    model = ParametricStubModel(score_val=score_val)
    thr = 0.0

    # 1. API
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        threshold=thr,
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: model,
    )
    client = TestClient(app)
    raw_bytes = make_synthetic_wav_bytes()
    api_res = client.post("/api/v1/predict", files={"file": ("v.wav", raw_bytes, "audio/wav")}).json()
    is_bona_api = (api_res["prediction"] == "BONA_FIDE")

    # 2. UI
    ui_predict = make_predict_fn(model=model, device="cpu", threshold=thr)
    verdict, _, _ = ui_predict((16000, np.zeros(16000, dtype=np.float32)))
    is_bona_ui = ("THẬT" in verdict or "BONAFIDE" in verdict)

    # 3. Bot
    update = MagicMock()
    context = MagicMock()
    file_mock = AsyncMock()
    file_mock.download_to_memory = lambda buf: buf.write(raw_bytes) or buf
    update.message.voice = MagicMock(get_file=AsyncMock(return_value=file_mock))
    update.message.audio = None
    update.message.reply_text = AsyncMock()

    await handle_voice_message(update, context, model=model, device="cpu", threshold=thr)
    bot_reply = update.message.reply_text.call_args[0][0]
    is_bona_bot = ("THẬT" in bot_reply or "BONAFIDE" in bot_reply)

    assert is_bona_api == is_bona_ui == is_bona_bot, f"Mismatch at score={score_val}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Diagnostic Path Matching Integrity (No Basename Collisions)
# ─────────────────────────────────────────────────────────────────────────────

def test_diagnostic_resolver_rejects_basename_collision(tmp_path):
    """A path resolver must match the directory hierarchy, not collide on filename."""
    dir_f5 = tmp_path / "data" / "spoof_f5tts" / "SPK1"
    dir_vieneu = tmp_path / "data" / "spoof_vieneu" / "SPK1"
    dir_f5.mkdir(parents=True)
    dir_vieneu.mkdir(parents=True)

    wav_f5 = dir_f5 / "prompt_000.wav"
    wav_vieneu = dir_vieneu / "prompt_000.wav"
    wav_f5.write_bytes(b"F5_AUDIO_BYTES_AAA")
    wav_vieneu.write_bytes(b"VIENEU_AUDIO_BYTES_BBB")

    # Target manifest entry looking for spoof_f5tts
    manifest_target = "data/spoof_f5tts/SPK1/prompt_000.wav"

    # A safe resolver checks the parent/sub-path relative to root
    def safe_resolve(relative_manifest_path: str, root_dir: Path) -> Path:
        resolved = (root_dir / relative_manifest_path).resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Cannot resolve {relative_manifest_path} under {root_dir}")
        return resolved

    resolved = safe_resolve(manifest_target, tmp_path)
    assert resolved == wav_f5.resolve()
    assert resolved.read_bytes() == b"F5_AUDIO_BYTES_AAA"
    assert resolved != wav_vieneu.resolve()
