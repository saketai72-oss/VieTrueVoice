"""TDD Unit & Contract tests for Zalo Official Account (OA) Webhook integration."""

import hashlib
import hmac
import io
import json
import wave
from unittest.mock import AsyncMock, patch
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from src.app.server import create_app
from src.app.zalo_webhook import generate_zalo_signature, verify_zalo_signature


class StubModel:
    def __init__(self, score_val: float = 12.0):
        self.score_val = score_val

    def score(self, waveform: torch.Tensor) -> torch.Tensor:
        return torch.tensor([self.score_val], dtype=torch.float32, device=waveform.device)


def make_wav_bytes(sample_rate: int = 16000, duration_sec: float = 0.5) -> bytes:
    sample_count = int(sample_rate * duration_sec)
    samples = (np.sin(2 * np.pi * 220 * np.arange(sample_count) / sample_rate) * 12000).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples)
    return buf.getvalue()


@pytest.fixture
def test_app(tmp_path):
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: StubModel(score_val=12.0),
    )
    return app


def test_zalo_signature_generation_and_verification():
    secret = "zalo_test_secret_12345"
    payload = b'{"event_name": "user_send_audio", "app_id": "12345"}'
    timestamp = "1731052000"

    sig = generate_zalo_signature(payload, secret=secret, timestamp=timestamp)
    assert sig
    assert verify_zalo_signature(payload, sig, secret=secret, timestamp=timestamp) is True
    assert verify_zalo_signature(payload, "invalid_sig", secret=secret, timestamp=timestamp) is False
    assert verify_zalo_signature(payload, sig, secret="wrong_secret", timestamp=timestamp) is False


def test_zalo_webhook_rejects_invalid_signature(test_app, monkeypatch):
    monkeypatch.setenv("ZALO_APP_SECRET", "super_secret_key")
    client = TestClient(test_app)

    body = json.dumps({"event_name": "user_send_audio"}).encode("utf-8")
    headers = {"X-ZEvent-Signature": "mac=invalid_mac", "X-ZEvent-Timestamp": "12345"}

    response = client.post("/api/v1/zalo/webhook", content=body, headers=headers)
    assert response.status_code in (401, 403)


def test_zalo_webhook_ignores_non_audio_event(test_app):
    client = TestClient(test_app)
    payload = {
        "event_name": "user_send_text",
        "sender": {"id": "user_001"},
        "message": {"text": "Xin chao"},
    }
    response = client.post("/api/v1/zalo/webhook", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["error"] == 0
    assert "Ignored non-audio event" in res_data["message"]


def test_zalo_webhook_bonafide_voice_flow(test_app):
    client = TestClient(test_app)
    audio_bytes = make_wav_bytes()

    payload = {
        "event_name": "user_send_audio",
        "app_id": "app_test_123",
        "sender": {"id": "zalo_user_789"},
        "recipient": {"id": "oa_official_456"},
        "message": {
            "msg_id": "msg_001",
            "attachments": [
                {
                    "type": "audio",
                    "payload": {
                        "url": "https://zalo-cdn.example.com/audio/voice_sample.m4a"
                    }
                }
            ]
        },
        "timestamp": 1731052000000,
    }

    with patch("src.app.zalo_webhook._download_audio_from_url", new=AsyncMock(return_value=audio_bytes)):
        response = client.post("/api/v1/zalo/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["error"] == 0
    assert "data" in data
    assert data["data"]["prediction"] == "BONA_FIDE"
    assert data["data"]["label"] == 1
    assert data["data"]["raw_score"] == 12.0
    assert data["data"]["confidence"] is not None
    assert "GIỌNG NÓI THẬT" in data["data"]["reply_text"]
    assert "Platt Scaling" in data["data"]["reply_text"]


def test_zalo_webhook_spoof_voice_flow(tmp_path):
    app = create_app(
        checkpoint_path=tmp_path / "stub.pt",
        device="cpu",
        latency_log_path=tmp_path / "latency.json",
        model_loader=lambda p, d: StubModel(score_val=-15.0),
    )
    client = TestClient(app)
    audio_bytes = make_wav_bytes()

    payload = {
        "event_name": "user_send_audio",
        "sender": {"id": "zalo_user_victim"},
        "message": {
            "attachments": [{"type": "audio", "payload": {"url": "https://zalo.cdn/spoof.opus"}}]
        }
    }

    with patch("src.app.zalo_webhook._download_audio_from_url", new=AsyncMock(return_value=audio_bytes)):
        response = client.post("/api/v1/zalo/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["error"] == 0
    assert data["data"]["prediction"] == "SPOOF"
    assert data["data"]["label"] == 0
    assert "CẢNH BÁO" in data["data"]["reply_text"]
    assert "KHUYẾN CÁO KHẨN CẤP" in data["data"]["reply_text"]
