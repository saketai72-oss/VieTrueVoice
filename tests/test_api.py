"""Contract tests for the in-memory FastAPI inference service."""

import hashlib
import io
import json
import wave

import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from src.app.server import create_app


class StubModel:
    def score(self, waveform):
        assert isinstance(waveform, torch.Tensor)
        assert tuple(waveform.shape) == (1, 64000)
        return torch.tensor([1.0], device=waveform.device)


def make_wav_bytes(sample_rate=16000, duration_sec=0.5):
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


@pytest.fixture
def client(tmp_path):
    app = create_app(
        checkpoint_path=tmp_path / "stub-checkpoint.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency_log.json",
        model_loader=lambda checkpoint_path, device: StubModel(),
    )
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_loaded_model_and_device(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["model"]
    assert payload["device"] == "cpu"


def test_predict_returns_contract_and_logs_only_audio_hash(client, tmp_path):
    audio_bytes = make_wav_bytes()

    response = client.post(
        "/api/v1/predict",
        files={"file": ("voice.wav", audio_bytes, "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert {
        "request_id",
        "prediction",
        "label",
        "confidence",
        "latency_sec",
        "audio_sha256",
    } <= payload.keys()
    assert payload["request_id"]
    assert payload["prediction"] == "BONA_FIDE"
    assert payload["label"] == 1
    assert payload["confidence"] is None
    assert payload["confidence_calibrated"] is False
    assert payload["threshold"] == 0.0
    assert payload["raw_score"] == 1.0
    assert payload["latency_sec"] >= 0.0
    assert payload["audio_sha256"] == hashlib.sha256(audio_bytes).hexdigest()

    log_path = tmp_path / "latency_log.json"
    entries = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(entries) == 1
    assert entries[0]["audio_sha256"] == hashlib.sha256(audio_bytes).hexdigest()
    assert "voice.wav" not in json.dumps(entries)


def test_predict_rejects_unsupported_audio_format(client):
    response = client.post(
        "/api/v1/predict",
        files={"file": ("voice.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 415
