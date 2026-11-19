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
    assert payload["n_windows"] == 1

    log_path = tmp_path / "latency_log.json"
    entries = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(entries) == 1
    assert entries[0]["audio_sha256"] == hashlib.sha256(audio_bytes).hexdigest()
    assert entries[0]["n_windows"] == 1
    assert "voice.wav" not in json.dumps(entries)


def test_predict_multi_window_long_clip(tmp_path):
    class MultiWindowStubModel:
        def score(self, waveform):
            assert isinstance(waveform, torch.Tensor)
            assert waveform.dim() == 2
            assert waveform.shape[1] == 64000
            assert waveform.shape[0] == 2
            return torch.tensor([0.5, 1.2], device=waveform.device)

    app = create_app(
        checkpoint_path=tmp_path / "stub-checkpoint.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency_log.json",
        model_loader=lambda checkpoint_path, device: MultiWindowStubModel(),
    )
    with TestClient(app) as test_client:
        # 5.0s audio at 16kHz = 80,000 samples -> produces 2 windows
        audio_bytes = make_wav_bytes(duration_sec=5.0)
        response = test_client.post(
            "/api/v1/predict",
            files={"file": ("voice_5s.wav", audio_bytes, "audio/wav")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["n_windows"] == 2
        # Max pooling across [0.5, 1.2] selects 1.2
        assert payload["raw_score"] == 1.2


def test_predict_rejects_unsupported_audio_format(client):
    response = client.post(
        "/api/v1/predict",
        files={"file": ("voice.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 415


def test_playground_endpoint_returns_html(client):
    response = client.get("/playground")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in response.text
    assert "ViTrueVoice Labs" in response.text

    # Verify trailing slash routing
    response_slash = client.get("/playground/")
    assert response_slash.status_code == 200
    assert "text/html" in response_slash.headers.get("content-type", "")


def test_predict_alias_route(client):
    audio_bytes = make_wav_bytes()
    response = client.post(
        "/predict",
        files={"file": ("voice_alias.wav", audio_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["prediction"] == "BONA_FIDE"
    assert payload["raw_score"] == 1.0


def test_clone_and_audit_endpoint(client, tmp_path):
    audio_bytes = make_wav_bytes(duration_sec=1.0)
    response = client.post(
        "/api/v1/clone-and-audit",
        files={"file": ("mic_record.wav", audio_bytes, "audio/wav")},
        data={"target_text": "Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "bonafide" in payload
    assert "clone" in payload
    assert payload["bonafide"]["prediction"] == "BONA_FIDE"
    assert payload["clone"]["audio_base64"].startswith("data:audio/wav;base64,")
    assert payload["clone"]["prediction"] in ("BONA_FIDE", "SPOOF")

    # Verify alias route
    response_alias = client.post(
        "/clone-and-audit",
        files={"file": ("mic_alias.wav", audio_bytes, "audio/wav")},
    )
    assert response_alias.status_code == 200
    assert response_alias.json()["status"] == "success"


