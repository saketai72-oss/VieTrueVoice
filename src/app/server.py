"""FastAPI inference service for VieTrueVoice anti-spoofing detection."""

from __future__ import annotations
import base64
import hashlib
import io
import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import soundfile as sf
import torch

from src.app.decision import classify_score, platt_calibrator
from src.app.forensics import extract_forensic_analysis
from src.preprocessing.pooling import extract_window_batch, pool_scores

try:
    from src.vitruevoice.live_cloner import (
        DEFAULT_REF_PROMPT,
        DEFAULT_TARGET_TEXT,
        LiveVoiceStudioCloner,
    )
except Exception:
    LiveVoiceStudioCloner = None
    DEFAULT_TARGET_TEXT = "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."
    DEFAULT_REF_PROMPT = "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."

SUPPORTED_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".webm"}
SUPPORTED_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3", "audio/ogg",
    "audio/opus", "audio/x-m4a", "audio/m4a",
    "audio/flac", "audio/webm",
}
APP_VERSION = "0.9.4"
TARGET_SAMPLE_RATE = 16000
TARGET_SAMPLE_COUNT = 64000  # 4.0s at 16kHz
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"

_SAMPLE_CATALOG: tuple[dict[str, str], ...] = (
    {
        "filename": "sample_bonafide_spk0004.wav",
        "label": "01 // GIỌNG THẬT (SPK_0004)",
        "category": "BONA_FIDE",
        "codec": "Clean 16kHz PCM",
    },
    {
        "filename": "sample_spoof_f5tts.wav",
        "label": "02 // F5-TTS (GIẢ)",
        "category": "SPOOF",
        "codec": "Clean 16kHz (F5-TTS)",
    },
    {
        "filename": "sample_spoof_voicestudio_cfm.wav",
        "label": "03 // OMNIVOICE CFM (GIẢ)",
        "category": "SPOOF",
        "codec": "OmniVoice CFM 16kHz",
    },
    {
        "filename": "sample_spoof_zalo_opus.wav",
        "label": "04 // ZALO OPUS 24K (GIẢ)",
        "category": "SPOOF",
        "codec": "Zalo Opus 24kbps",
    },
    {
        "filename": "sample_telephony_amrnb.wav",
        "label": "05 // AMR-NB 8KHZ (GIẢ)",
        "category": "SPOOF",
        "codec": "PSTN AMR-NB 8kHz",
    },
)


def _list_audio_samples(samples_dir: Path | None = None) -> list[dict[str, Any]]:
    """List real audio samples in STATIC_DIR/samples with catalog metadata."""
    target_dir = samples_dir or (STATIC_DIR / "samples")
    catalog_by_name = {item["filename"]: item for item in _SAMPLE_CATALOG}

    existing_files: list[Path] = []
    if target_dir.exists() and target_dir.is_dir():
        existing_files = sorted(p for p in target_dir.iterdir() if p.is_file() and p.suffix.lower() == ".wav")

    results: list[dict[str, Any]] = []
    if existing_files:
        existing_names = {p.name for p in existing_files}
        for item in _SAMPLE_CATALOG:
            if item["filename"] in existing_names:
                results.append(
                    {
                        **item,
                        "url": f"/static/samples/{item['filename']}",
                        "exists": True,
                    }
                )
        for p in existing_files:
            if p.name not in catalog_by_name:
                is_bona = "bonafide" in p.name.lower()
                results.append(
                    {
                        "filename": p.name,
                        "url": f"/static/samples/{p.name}",
                        "label": p.stem.replace("_", " ").upper(),
                        "category": "BONA_FIDE" if is_bona else "SPOOF",
                        "codec": "WAV 16kHz",
                        "exists": True,
                    }
                )
        return results

    # Fallback catalog when *.wav files are absent (e.g. gitignored CI checkout)
    return [
        {
            **item,
            "url": f"/static/samples/{item['filename']}",
            "exists": False,
        }
        for item in _SAMPLE_CATALOG
    ]


def _score_waveform(model: Any, audio_data: np.ndarray, device: str) -> tuple[np.ndarray, float, int]:
    """Run single batched multi-window forward pass and Consensus Asymmetric Veto pooling."""
    windows_batch = extract_window_batch(
        audio_data,
        win=TARGET_SAMPLE_COUNT,
        hop=16000,
        max_windows=5,
        apply_dither=False,
        dense_slicing=True,
    ).to(device)
    n_windows = int(windows_batch.shape[0])

    with torch.inference_mode():
        score_tensor = model.score(windows_batch)
        if isinstance(score_tensor, torch.Tensor):
            scores_np = score_tensor.detach().cpu().numpy()
        else:
            scores_np = np.asarray(score_tensor)
        if scores_np.ndim > 1:
            scores_np = scores_np.squeeze(-1)
        elif scores_np.ndim == 0:
            scores_np = np.array([scores_np.item()], dtype=np.float32)
        raw_score = float(pool_scores(scores_np, mode="asymmetric_veto"))

    return scores_np, raw_score, n_windows


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


def _condition_audio_for_inference(waveform: np.ndarray) -> np.ndarray:
    """Preprocess audio stream to mitigate dead silence gating and low microphone gain.

    Applies silence trimming (top_db=25) so leading/trailing silence doesn't bias
    the neural SSL front-end into false deepfake verdicts, and peak-normalizes to 0.95
    to match the acoustic energy distribution of the training data.
    """
    if len(waveform) < int(0.5 * TARGET_SAMPLE_RATE):
        return waveform
    try:
        import librosa
        trimmed, _ = librosa.effects.trim(waveform, top_db=25)
        if len(trimmed) >= int(0.5 * TARGET_SAMPLE_RATE):
            waveform = trimmed
    except Exception:
        pass
    max_abs = float(np.max(np.abs(waveform)))
    if max_abs > 1e-5:
        waveform = (waveform / max_abs) * 0.95
    return waveform


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


_CHECKPOINT_CANDIDATES = (
    Path("out/v0.9.4/best_model.pt"),
    Path("out/zalo_b_zalo_v8_inverted/best_model.pt"),
    Path("out/zalo_b_zalo_v8_inverted_no_spk1/best_model.pt"),
    Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt"),
    Path("out/zalo_b_zalo_v6_local/best_model.pt"),
    Path("out/zalo_b_zalo_v5_local/best_model.pt"),
    Path("out/best_model_B_zalo.pt"),
    Path("out/run_B/best_model.pt"),
)


def resolve_default_checkpoint(candidates: tuple[Path, ...] = _CHECKPOINT_CANDIDATES) -> Path:
    """Return the highest-priority existing model checkpoint path."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


DEFAULT_CHECKPOINT = resolve_default_checkpoint()


DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_GLOBAL_CLONER = None


def _get_live_cloner() -> Any:
    global _GLOBAL_CLONER
    if _GLOBAL_CLONER is None and LiveVoiceStudioCloner is not None:
        c_dev = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            _GLOBAL_CLONER = LiveVoiceStudioCloner(
                target_text=DEFAULT_TARGET_TEXT,
                device=c_dev,
            )
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to initialize LiveVoiceStudioCloner: %s", exc)
    return _GLOBAL_CLONER


def create_app(
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    device: str = DEFAULT_DEVICE,
    threshold: float = 0.0,
    latency_log_path: Path | str = Path("benchmarks/latency_log.json"),
    model_loader: Callable[[Path | str, str], Any] | None = None,
) -> FastAPI:
    ckpt_path = Path(checkpoint_path)
    log_path = Path(latency_log_path)
    loader = model_loader or _default_model_loader
    model = loader(ckpt_path, device)
    if model is not None and hasattr(model, "score"):
        try:
            # Comprehensive warm-up: multi-window batch (5 windows = 9s+ clips) and single window
            dummy_5 = torch.zeros(5, TARGET_SAMPLE_COUNT, dtype=torch.float32, device=device)
            dummy_1 = torch.zeros(1, TARGET_SAMPLE_COUNT, dtype=torch.float32, device=device)
            with torch.inference_mode():
                model.score(dummy_5)
                model.score(dummy_1)
            if str(device).startswith("cuda") and torch.cuda.is_available():
                torch.cuda.synchronize()
        except Exception:
            pass

    app = FastAPI(
        title="VieTrueVoice Anti-Spoofing Inference API",
        version=APP_VERSION,
        description="Phát hiện giọng nói giả mạo tiếng Việt qua kênh thoại nén.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        if not INDEX_HTML_PATH.exists():
            raise HTTPException(status_code=404, detail="Index HTML not found")
        return FileResponse(INDEX_HTML_PATH, media_type="text/html")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        ico_path = STATIC_DIR / "favicon.ico"
        if ico_path.exists():
            return FileResponse(ico_path, media_type="image/x-icon")
        svg_path = STATIC_DIR / "assets" / "logo.svg"
        if svg_path.exists():
            return FileResponse(svg_path, media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Favicon not found")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": APP_VERSION,
            "model": str(ckpt_path),
            "device": device,
            "threshold": threshold,
        }

    @app.get("/api/v1/samples")
    def list_samples() -> list[dict[str, Any]]:
        return _list_audio_samples(STATIC_DIR / "samples")

    @app.post("/api/v1/predict")
    @app.post("/predict")
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

        audio_data = _condition_audio_for_inference(audio_data)

        if model is None:
            raise HTTPException(status_code=503, detail="Model is not loaded")

        # Multi-window extraction (STUBBORN_FACT: repeat padding <64k, single batched forward pass)
        scores_np, raw_score, n_windows = _score_waveform(model, audio_data, device)

        decision = classify_score(
            raw_score,
            threshold=threshold,
            calibrator=platt_calibrator,
            window_scores=scores_np,
        )
        forensics = extract_forensic_analysis(
            audio_data,
            sr=TARGET_SAMPLE_RATE,
            window_scores=scores_np,
            raw_score=raw_score,
            threshold=threshold,
            pooling_mode="asymmetric_veto",
        )
        latency_sec = time.perf_counter() - t0
        req_id = f"req_{uuid.uuid4().hex[:12]}"
        window_scores_list = [round(float(s), 4) for s in scores_np.tolist()]

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
            "n_windows": n_windows,
            "window_scores": window_scores_list,
            "is_borderline": decision.is_borderline,
            "risk_level": decision.risk_level,
            "prob_bona_pct": forensics["platt_curve"]["prob_bona_pct"],
            "prob_spoof_pct": forensics["platt_curve"]["prob_spoof_pct"],
            "forensics": forensics,
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
            "n_windows": n_windows,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_latency_log(log_path, log_entry)

        return result

    @app.post("/api/v1/clone-and-audit")
    @app.post("/clone-and-audit")
    async def clone_and_audit(
        file: UploadFile = File(...),
        target_text: str = Form(DEFAULT_TARGET_TEXT),
        custom_ref_text: str = Form(""),
    ) -> dict[str, Any]:
        if not _is_supported(file.filename, file.content_type):
            raise HTTPException(status_code=415, detail="Unsupported audio format")

        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")

        try:
            audio_data = _load_audio_in_memory(raw_bytes)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to decode audio: {exc}")

        audio_data = _condition_audio_for_inference(audio_data)

        if len(audio_data) < int(0.5 * TARGET_SAMPLE_RATE):
            raise HTTPException(status_code=400, detail="Đoạn âm thanh quá ngắn (< 0.5s)")

        if model is None:
            raise HTTPException(status_code=503, detail="Model is not loaded")

        # 1. Thẩm định bản gốc Bona Fide
        t0_bona = time.perf_counter()
        scores_np, raw_score_bona, n_win_bona = _score_waveform(model, audio_data, device)
        dec_bona = classify_score(
            raw_score_bona,
            threshold=threshold,
            calibrator=platt_calibrator,
            window_scores=scores_np,
        )
        forensics_bona = extract_forensic_analysis(
            audio_data,
            sr=TARGET_SAMPLE_RATE,
            window_scores=scores_np,
            raw_score=raw_score_bona,
            threshold=threshold,
            pooling_mode="asymmetric_veto",
        )
        lat_bona = time.perf_counter() - t0_bona
        prob_bona_pct = forensics_bona["platt_curve"]["prob_bona_pct"]
        prob_spoof_pct = forensics_bona["platt_curve"]["prob_spoof_pct"]
        sha_bona = hashlib.sha256(raw_bytes).hexdigest()

        bona_dict = {
            "prediction": dec_bona.prediction,
            "label": dec_bona.label,
            "raw_score": round(dec_bona.raw_score, 4),
            "threshold": dec_bona.threshold,
            "prob_bona_pct": prob_bona_pct,
            "prob_spoof_pct": prob_spoof_pct,
            "confidence": prob_bona_pct if dec_bona.is_bonafide else prob_spoof_pct,
            "latency_sec": round(lat_bona, 4),
            "audio_sha256": sha_bona,
            "duration_s": round(float(len(audio_data) / TARGET_SAMPLE_RATE), 2),
            "n_windows": n_win_bona,
            "window_scores": [round(float(s), 4) for s in scores_np.tolist()],
            "is_borderline": dec_bona.is_borderline,
            "risk_level": dec_bona.risk_level,
            "forensics": forensics_bona,
        }

        # 2. Nhân bản Zero-Shot CFM qua VoiceStudio (OmniVoice)
        t0_clone = time.perf_counter()
        cloned_audio_int16 = None
        cloned_sr = TARGET_SAMPLE_RATE
        ref_used = ""
        clone_status = "done"

        cloner = _get_live_cloner()
        if cloner is not None:
            try:
                cloner.target_text = target_text or DEFAULT_TARGET_TEXT
                ref_txt = custom_ref_text
                if not ref_txt and ("spk0004" in str(file.filename).lower() or "sample_bonafide" in str(file.filename).lower()):
                    ref_txt = DEFAULT_REF_PROMPT

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_f:
                    tmp_path = tmp_f.name
                    sf.write(tmp_path, audio_data, TARGET_SAMPLE_RATE, subtype="PCM_16")

                try:
                    res = cloner.clone_omnivoice(tmp_path, ref_text=ref_txt)
                    if res is not None:
                        cloned_audio_int16, cloned_sr, ref_used = res
                finally:
                    if os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass
            except Exception as exc:
                logging.getLogger(__name__).warning("VoiceStudio live cloning failed: %s", exc)

        # Fallback to high-quality CFM reference preset if model synthesis was unavailable
        if cloned_audio_int16 is None:
            clone_status = "fallback"
            preset_spoof = Path("data/bonafide_ref/sample_spoof_voicestudio_cfm.wav")
            if not preset_spoof.exists():
                preset_spoof = Path("src/app/samples/sample_spoof_voicestudio_cfm.wav")
            if not preset_spoof.exists():
                preset_spoof = Path("src/app/static/samples/sample_spoof_voicestudio_cfm.wav")
            if not preset_spoof.exists():
                preset_spoof = Path("data/bonafide_ref/sample_spoof_f5tts.wav")
            if not preset_spoof.exists():
                preset_spoof = Path("src/app/samples/sample_spoof_f5tts.wav")
            if preset_spoof.exists():
                try:
                    y_p, sr_p = sf.read(str(preset_spoof))
                    if y_p.ndim > 1:
                        y_p = y_p.mean(axis=-1)
                    if sr_p != TARGET_SAMPLE_RATE:
                        import librosa
                        y_p = librosa.resample(y_p, orig_sr=sr_p, target_sr=TARGET_SAMPLE_RATE)
                    cloned_audio_int16 = (y_p * 32767.0).astype(np.int16)
                    cloned_sr = TARGET_SAMPLE_RATE
                    ref_used = "VoiceStudio CFM Preset Sample"
                except Exception as e:
                    logging.getLogger(__name__).warning("Preset spoof fallback failed: %s", e)

        if cloned_audio_int16 is None:
            # Synthetic fallback for CI / headless environments without physical preset audio files
            clone_status = "synthetic_fallback"
            t_synth = np.linspace(0, 2.0, int(2.0 * TARGET_SAMPLE_RATE), endpoint=False, dtype=np.float32)
            synth_wave = (
                0.4 * np.sin(2 * np.pi * 150 * t_synth)
                + 0.3 * np.sin(2 * np.pi * 300 * t_synth)
                + 0.1 * np.sin(2 * np.pi * 450 * t_synth)
            ).astype(np.float32)
            cloned_audio_int16 = (synth_wave * 32767.0).astype(np.int16)
            cloned_sr = TARGET_SAMPLE_RATE
            ref_used = "Synthetic Fallback Wave"

        # 3. Thẩm định bản clone CFM (resample to 16kHz for model & forensics if OmniVoice returned 24kHz)
        cloned_float = cloned_audio_int16.astype(np.float32) / 32768.0
        if cloned_sr != TARGET_SAMPLE_RATE:
            import librosa
            cloned_float_16k = librosa.resample(cloned_float, orig_sr=cloned_sr, target_sr=TARGET_SAMPLE_RATE).astype(np.float32)
        else:
            cloned_float_16k = cloned_float

        sc_np, raw_score_clone, n_win_clone = _score_waveform(model, cloned_float_16k, device)
        dec_clone = classify_score(
            raw_score_clone,
            threshold=threshold,
            calibrator=platt_calibrator,
            window_scores=sc_np,
        )
        forensics_clone = extract_forensic_analysis(
            cloned_float_16k,
            sr=TARGET_SAMPLE_RATE,
            window_scores=sc_np,
            raw_score=raw_score_clone,
            threshold=threshold,
            pooling_mode="asymmetric_veto",
        )
        lat_clone = time.perf_counter() - t0_clone
        prob_clone_bona_pct = forensics_clone["platt_curve"]["prob_bona_pct"]
        prob_clone_spoof_pct = forensics_clone["platt_curve"]["prob_spoof_pct"]

        buf = io.BytesIO()
        sf.write(buf, cloned_audio_int16, cloned_sr, format="WAV", subtype="PCM_16")
        clone_wav_bytes = buf.getvalue()
        audio_b64 = "data:audio/wav;base64," + base64.b64encode(clone_wav_bytes).decode("ascii")
        sha_clone = hashlib.sha256(clone_wav_bytes).hexdigest()
        clone_filename = f"voicestudio_cfm_clone_{int(time.time()*1000)}.wav" if clone_status == "done" else "preset_sample_spoof_voicestudio_cfm.wav"

        clone_dict = {
            "status": clone_status,
            "filename": clone_filename,
            "prediction": dec_clone.prediction,
            "label": dec_clone.label,
            "raw_score": round(dec_clone.raw_score, 4),
            "threshold": dec_clone.threshold,
            "prob_bona_pct": prob_clone_bona_pct,
            "prob_spoof_pct": prob_clone_spoof_pct,
            "confidence": prob_clone_spoof_pct if not dec_clone.is_bonafide else prob_clone_bona_pct,
            "latency_sec": round(lat_clone, 4),
            "audio_sha256": sha_clone,
            "duration_s": round(float(len(cloned_float_16k) / TARGET_SAMPLE_RATE), 2),
            "n_windows": n_win_clone,
            "window_scores": [round(float(s), 4) for s in sc_np.tolist()],
            "is_borderline": dec_clone.is_borderline,
            "risk_level": dec_clone.risk_level,
            "audio_base64": audio_b64,
            "transcript_used": ref_used,
            "forensics": forensics_clone,
        }

        # Log anonymously
        log_entry_bona = {
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "audio_sha256": sha_bona,
            "predicted_label": bona_dict["prediction"],
            "raw_score": bona_dict["raw_score"],
            "threshold": bona_dict["threshold"],
            "confidence_score": bona_dict["confidence"],
            "latency_sec": bona_dict["latency_sec"],
            "n_windows": bona_dict["n_windows"],
            "type": "live_reference",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_latency_log(log_path, log_entry_bona)

        log_entry_clone = {
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "audio_sha256": sha_clone,
            "predicted_label": clone_dict["prediction"],
            "raw_score": clone_dict["raw_score"],
            "threshold": clone_dict["threshold"],
            "confidence_score": clone_dict["confidence"],
            "latency_sec": clone_dict["latency_sec"],
            "n_windows": clone_dict["n_windows"],
            "type": "live_cfm_clone",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_latency_log(log_path, log_entry_clone)

        return {
            "status": "success",
            "target_text": target_text or DEFAULT_TARGET_TEXT,
            "transcript_used": ref_used,
            "delta_margin": round(raw_score_bona - raw_score_clone, 4),
            "bonafide": bona_dict,
            "clone": clone_dict,
        }

    if model is not None:
        from src.app.zalo_webhook import create_zalo_router
        zalo_router = create_zalo_router(
            model=model,
            device=device,
            threshold=threshold,
        )
        app.include_router(zalo_router)

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
