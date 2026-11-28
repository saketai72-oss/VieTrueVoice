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
        assert waveform.shape[-1] == 64000
        n_windows = waveform.shape[0] if waveform.ndim == 2 else 1
        return torch.tensor([1.0] * n_windows, device=waveform.device)


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
    assert payload["version"] == "0.9.4"


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
        "prob_bona_pct",
        "prob_spoof_pct",
        "risk_level",
        "forensics",
    } <= payload.keys()
    assert payload["request_id"]
    assert payload["prediction"] == "BONA_FIDE"
    assert payload["label"] == 1
    assert payload["confidence"] is not None
    assert payload["confidence"] == pytest.approx(0.5156, abs=1e-3)
    assert payload["confidence_calibrated"] is True
    assert payload["threshold"] == 0.0
    assert payload["raw_score"] == 1.0
    assert payload["latency_sec"] >= 0.0
    assert payload["audio_sha256"] == hashlib.sha256(audio_bytes).hexdigest()
    assert payload["n_windows"] == 1
    assert "window_scores" in payload
    assert isinstance(payload["window_scores"], list)
    assert len(payload["window_scores"]) == 1
    assert "is_borderline" in payload
    assert isinstance(payload["is_borderline"], bool)
    assert payload["risk_level"] in ("NORMAL", "BORDERLINE")
    assert 0.1 <= payload["prob_bona_pct"] <= 99.9
    assert 0.1 <= payload["prob_spoof_pct"] <= 99.9
    assert payload["prob_bona_pct"] + payload["prob_spoof_pct"] == pytest.approx(100.0, abs=0.2)

    forensics = payload["forensics"]
    assert isinstance(forensics, dict)
    assert {
        "mel_spectrogram",
        "waveform",
        "windows",
        "band_energy_pct",
        "platt_curve",
        "pooling",
    } <= forensics.keys()

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


def test_root_serves_brutalist_webgl_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!DOCTYPE html>" in response.text
    assert "XÁC THỰC GIỌNG NÓI" in response.text
    assert "webgl-orb.js" in response.text
    assert "charts.js" in response.text


def test_old_playground_route_removed(client):
    assert client.get("/playground").status_code == 404
    assert client.get("/playground/").status_code == 404


def test_samples_endpoint_lists_real_wavs(client):
    response = client.get("/api/v1/samples")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) > 0
    for item in payload:
        assert isinstance(item, dict)
        assert item["url"].startswith("/static/samples/")
        assert item["url"].endswith(".wav")


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
        data={"target_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "bonafide" in payload
    assert "clone" in payload
    assert payload["bonafide"]["prediction"] == "BONA_FIDE"
    assert isinstance(payload["bonafide"]["forensics"], dict)
    assert payload["clone"]["audio_base64"].startswith("data:audio/wav;base64,")
    assert payload["clone"]["prediction"] in ("BONA_FIDE", "SPOOF")
    assert isinstance(payload["clone"]["forensics"], dict)
    assert "delta_margin" in payload
    assert payload["delta_margin"] == pytest.approx(
        payload["bonafide"]["raw_score"] - payload["clone"]["raw_score"],
        abs=1e-3,
    )

    # Verify alias route
    response_alias = client.post(
        "/clone-and-audit",
        files={"file": ("mic_alias.wav", audio_bytes, "audio/wav")},
    )
    assert response_alias.status_code == 200
    assert response_alias.json()["status"] == "success"


def test_resolve_default_checkpoint_prefers_v094(tmp_path):
    from src.app.server import resolve_default_checkpoint

    v094 = tmp_path / "out" / "v0.9.4" / "best_model.pt"
    legacy = tmp_path / "out" / "zalo_b_zalo_v8_inverted" / "best_model.pt"
    v094.parent.mkdir(parents=True)
    legacy.parent.mkdir(parents=True)
    v094.write_bytes(b"v094")
    legacy.write_bytes(b"legacy")

    assert resolve_default_checkpoint((v094, legacy)) == v094
    v094.unlink()
    assert resolve_default_checkpoint((v094, legacy)) == legacy
