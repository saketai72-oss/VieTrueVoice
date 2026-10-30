"""FastAPI inference service for ViTrueVoice anti-spoofing detection."""

from __future__ import annotations
import hashlib
import io
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, File, HTTPException, UploadFile
import numpy as np
import soundfile as sf
import torch

from src.app.decision import classify_score

SUPPORTED_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac"}
SUPPORTED_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3", "audio/ogg",
    "audio/opus", "audio/x-m4a", "audio/m4a",
    "audio/flac",
}
TARGET_SAMPLE_RATE = 16000
TARGET_SAMPLE_COUNT = 64000  # 4.0s at 16kHz


def _is_supported(filename: str | None, content_type: str | None) -> bool:
    ext = Path(filename or "").suffix.lower()
    if ext in SUPPORTED_EXTS:
        return True
    if content_type and (content_type.lower() in SUPPORTED_TYPES or content_type.lower().startswith("audio/")):
        return True
    return False


from src.preprocessing.audio_loader import load_audio


def _load_audio_in_memory(raw_bytes: bytes) -> np.ndarray:
    """Read audio stream into a 1D float32 numpy array normalized to 16kHz."""
    return load_audio(raw_bytes, target_sr=TARGET_SAMPLE_RATE)


def _pad_or_crop(waveform: np.ndarray, target_len: int = TARGET_SAMPLE_COUNT) -> np.ndarray:
    """Repeat padding for short clips, crop for long clips (STUBBORN_FACT)."""
    if len(waveform) == 0:
        return np.zeros(target_len, dtype=np.float32)
    if len(waveform) < target_len:
        waveform = np.tile(waveform, int(np.ceil(target_len / len(waveform))))
    return waveform[:target_len]


def _append_latency_log(log_path: Path, entry: dict[str, Any]) -> None:
    """Log prediction metadata anonymously using SHA-256 hash without file or user IDs."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    if log_path.exists():
        try:
            content = log_path.read_text(encoding="utf-8").strip()
            if content:
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    entries = loaded
        except Exception:
            entries = []
    entries.append(entry)
    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def _default_model_loader(checkpoint_path: Path | str, device: str) -> Any:
    ckpt_p = Path(checkpoint_path)
    if not ckpt_p.exists():
        return None
    from scripts.eval_ssl_aasist import load_model
    model, _ = load_model(ckpt_p, device=device)
    return model


def create_app(
    checkpoint_path: Path | str = Path("out/run_B/best_model.pt"),
    device: str = "cpu",
    threshold: float = 0.0,
    latency_log_path: Path | str = Path("benchmarks/latency_log.json"),
    model_loader: Callable[[Path | str, str], Any] | None = None,
) -> FastAPI:
    ckpt_path = Path(checkpoint_path)
    log_path = Path(latency_log_path)
    loader = model_loader or _default_model_loader
    model = loader(ckpt_path, device)

    app = FastAPI(
        title="ViTrueVoice Anti-Spoofing Inference API",
        version="0.3.0",
        description="Phát hiện giọng nói giả mạo tiếng Việt qua kênh thoại nén.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "model": str(ckpt_path),
            "device": device,
            "threshold": threshold,
        }

    @app.post("/api/v1/predict")
    async def predict(file: UploadFile = File(...)) -> dict[str, Any]:
        if not _is_supported(file.filename, file.content_type):
            raise HTTPException(status_code=415, detail="Unsupported audio format")

        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")

        t0 = time.perf_counter()
        audio_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        try:
            audio_data = _load_audio_in_memory(raw_bytes)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to decode audio: {exc}")

        padded_audio = _pad_or_crop(audio_data, TARGET_SAMPLE_COUNT)
        tensor_input = torch.tensor(padded_audio, dtype=torch.float32, device=device).unsqueeze(0)

        if model is None:
            raise HTTPException(status_code=503, detail="Model is not loaded")

        with torch.inference_mode():
            score_tensor = model.score(tensor_input)
            raw_score = float(score_tensor.item() if hasattr(score_tensor, "item") else score_tensor[0])

        latency_sec = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold)
        req_id = f"req_{uuid.uuid4().hex[:12]}"

        result = {
            "request_id": req_id,
            "prediction": decision.prediction,
            "label": decision.label,
            "raw_score": round(decision.raw_score, 4),
            "threshold": decision.threshold,
            "confidence": round(decision.confidence, 4) if decision.confidence is not None else None,
            "confidence_calibrated": decision.confidence_calibrated,
            "latency_sec": round(latency_sec, 4),
            "audio_sha256": audio_sha256,
        }

        # Anonymized audit log
        log_entry = {
            "request_id": req_id,
            "audio_sha256": audio_sha256,
            "predicted_label": result["prediction"],
            "raw_score": result["raw_score"],
            "threshold": result["threshold"],
            "confidence_score": result["confidence"],
            "latency_sec": result["latency_sec"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_latency_log(log_path, log_entry)

        return result

    return app


# Lazy top-level app for uvicorn (PEP 562)
_app_instance: FastAPI | None = None


def __getattr__(name: str) -> Any:
    global _app_instance
    if name == "app":
        if _app_instance is None:
            _app_instance = create_app()
        return _app_instance
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
