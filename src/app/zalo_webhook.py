"""Zalo Official Account (OA) Webhook integration for ViTrueVoice anti-spoofing verification.

Implements official Zalo for Developers OpenAPI v3.0 specs:
1. HMAC-SHA256 webhook signature validation.
2. In-memory processing of Zalo voice messages (AAC-LC, Opus, M4A).
3. Multi-window inference with Platt Scaling calibrated confidence.
4. Compliant with Vietnam Personal Data Protection Law 91/2025/QH15.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any, Callable

import httpx
import numpy as np
import torch
from fastapi import APIRouter, Header, HTTPException, Request, Response

from src.app.decision import classify_score, platt_calibrator
from src.app.server import TARGET_SAMPLE_COUNT, _load_audio_in_memory
from src.preprocessing.pooling import extract_window_batch, pool_scores


def generate_zalo_signature(payload: bytes, secret: str, timestamp: str = "") -> str:
    """Generate Zalo HMAC-SHA256 signature for webhook payload validation."""
    data_to_sign = (timestamp.encode("utf-8") + payload) if timestamp else payload
    mac = hmac.new(secret.encode("utf-8"), data_to_sign, hashlib.sha256).hexdigest()
    return f"mac={mac}"


def verify_zalo_signature(payload: bytes, signature_header: str, secret: str, timestamp: str = "") -> bool:
    """Verify incoming Zalo webhook request signature using constant-time comparison."""
    if not signature_header or not secret:
        return False

    raw_sig = signature_header.split("mac=")[-1].strip() if "mac=" in signature_header else signature_header.strip()
    expected = generate_zalo_signature(payload, secret=secret, timestamp=timestamp).split("mac=")[-1]
    return hmac.compare_digest(raw_sig.lower(), expected.lower())


async def _download_audio_from_url(url: str, timeout_sec: float = 30.0) -> bytes:
    """Stream audio file from URL directly into memory without writing to disk."""
    if url.startswith("file://"):
        from pathlib import Path
        clean_path = url[7:]
        # Handle Windows leading slash e.g. /C:/path
        if len(clean_path) > 2 and clean_path[0] == "/" and clean_path[2] == ":":
            clean_path = clean_path[1:]
        file_path = Path(clean_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_bytes()

    async with httpx.AsyncClient(timeout=timeout_sec, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def build_zalo_reply_message(
    is_bonafide: bool,
    raw_score: float,
    threshold: float,
    confidence_str: str,
    n_windows: int,
    latency_sec: float,
    audio_hash: str,
) -> str:
    """Construct a clear, fraud-preventing response message for Zalo chat users."""
    if is_bonafide:
        return (
            "🛡️ [ViTrueVoice] KẾT QUẢ: GIỌNG NÓI THẬT (BONAFIDE)\n\n"
            f"• Điểm phân định: {raw_score:+.4f} (Ngưỡng: {threshold:+.4f})\n"
            f"• Phân tích đa cửa sổ: {n_windows} cửa sổ trượt (Max-Pooling)\n"
            f"• Độ tin cậy: {confidence_str}\n"
            f"• Thời gian xử lý: {latency_sec:.2f}s\n"
            f"• Mã băm kiểm định: {audio_hash[:16]}...\n\n"
            "✅ Đánh giá: Âm thanh tự nhiên, không phát hiện dấu vết công nghệ nhái giọng AI."
        )
    else:
        return (
            "🚨 [ViTrueVoice] CẢNH BÁO LỪA ĐẢO: ĐÂY LÀ GIỌNG NÓI GIẢ MẠO (SPOOF)\n\n"
            f"• Điểm phân định: {raw_score:+.4f} (Ngưỡng: {threshold:+.4f})\n"
            f"• Phân tích đa cửa sổ: {n_windows} cửa sổ trượt (Max-Pooling)\n"
            f"• Độ tin cậy phát hiện: {confidence_str}\n"
            f"• Thời gian xử lý: {latency_sec:.2f}s\n"
            f"• Mã băm kiểm định: {audio_hash[:16]}...\n\n"
            "⚠️ KHUYẾN CÁO KHẨN CẤP:\n"
            "1. Tuyệt đối KHÔNG chuyển tiền, KHÔNG cung cấp mật khẩu hoặc mã OTP.\n"
            "2. Hãy gọi điện trực tiếp lại cho người thân bằng số điện thoại di động thông thường để xác minh danh tính."
        )


async def send_zalo_oa_message(
    user_id: str,
    text: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Send customer support response message via Zalo OpenAPI v3.0 CS Message."""
    token = access_token or os.getenv("ZALO_OA_ACCESS_TOKEN", "")
    if not token:
        # Simulation / dry-run mode
        return {"error": 0, "message": "Simulation mode (token unset), reply skipped"}

    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {"access_token": token, "Content-Type": "application/json"}
    body = {
        "recipient": {"user_id": user_id},
        "message": {"text": text},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            return resp.json()
    except Exception as exc:
        return {"error": -1, "message": f"Failed to call Zalo OpenAPI: {exc}"}


def create_zalo_router(
    model: Any,
    device: str = "cpu",
    threshold: float = 0.0,
    calibrator: Callable[..., float] | None = platt_calibrator,
) -> APIRouter:
    """Create FastAPI APIRouter handling Zalo OA Webhooks."""
    router = APIRouter()

    @router.post("/api/v1/zalo/webhook")
    async def zalo_webhook_handler(
        request: Request,
        x_zevent_signature: str | None = Header(None, alias="X-ZEvent-Signature"),
        x_zevent_timestamp: str | None = Header(None, alias="X-ZEvent-Timestamp"),
    ) -> dict[str, Any]:
        body_bytes = await request.body()
        secret = os.getenv("ZALO_APP_SECRET", "")

        # Verify signature if secret is configured
        if secret:
            timestamp = x_zevent_timestamp or ""
            if not verify_zalo_signature(body_bytes, x_zevent_signature or "", secret, timestamp=timestamp):
                raise HTTPException(status_code=401, detail="Invalid Zalo signature")

        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}")

        event_name = payload.get("event_name", "")
        # Filter non-audio events
        if event_name not in ("user_send_audio", "user_send_voice", "user_send_file"):
            return {
                "error": 0,
                "message": f"Ignored non-audio event: {event_name or 'unknown'}",
            }

        sender_id = payload.get("sender", {}).get("id", "anonymous_user")
        attachments = payload.get("message", {}).get("attachments", [])
        audio_url = None

        for att in attachments:
            att_type = att.get("type", "")
            if att_type in ("audio", "voice", "file"):
                audio_url = att.get("payload", {}).get("url")
                if audio_url:
                    break

        if not audio_url:
            return {"error": 1, "message": "No audio URL found in attachments"}

        t0 = time.perf_counter()
        try:
            raw_bytes = await _download_audio_from_url(audio_url)
        except Exception as exc:
            return {"error": 2, "message": f"Failed to download audio from Zalo CDN: {exc}"}

        audio_hash = hashlib.sha256(raw_bytes).hexdigest()

        try:
            audio_data = _load_audio_in_memory(raw_bytes)
        except Exception as exc:
            return {"error": 3, "message": f"Failed to decode audio: {exc}"}

        windows_batch = extract_window_batch(
            audio_data,
            win=TARGET_SAMPLE_COUNT,
            hop=16000,
            max_windows=5,
        ).to(device)
        n_windows = int(windows_batch.shape[0])

        with torch.inference_mode():
            score_tensor = model.score(windows_batch)
            if isinstance(score_tensor, torch.Tensor):
                scores_np = score_tensor.squeeze(-1).float().cpu().numpy()
            else:
                scores_np = np.asarray(score_tensor)
            if scores_np.ndim == 0:
                scores_np = np.array([float(scores_np)])
            raw_score = float(pool_scores(scores_np, mode="max"))

        latency_sec = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold, calibrator=calibrator)

        if decision.confidence_calibrated and decision.confidence is not None:
            conf_str = f"{decision.confidence * 100:.1f}% (Platt Scaling)"
        else:
            conf_str = "Chưa hiệu chuẩn xác suất phần trăm"

        reply_text = build_zalo_reply_message(
            is_bonafide=decision.is_bonafide,
            raw_score=raw_score,
            threshold=threshold,
            confidence_str=conf_str,
            n_windows=n_windows,
            latency_sec=latency_sec,
            audio_hash=audio_hash,
        )

        # Dispatch async reply to user via Zalo CS Message API
        oa_send_status = await send_zalo_oa_message(sender_id, reply_text)

        return {
            "error": 0,
            "message": "Processed successfully",
            "data": {
                "request_id": f"zalo_{uuid.uuid4().hex[:12]}",
                "prediction": decision.prediction,
                "label": decision.label,
                "raw_score": round(raw_score, 4),
                "threshold": threshold,
                "confidence": round(decision.confidence, 4) if decision.confidence is not None else None,
                "latency_sec": round(latency_sec, 4),
                "audio_sha256": audio_hash,
                "n_windows": n_windows,
                "reply_text": reply_text,
                "oa_send_status": oa_send_status,
            },
        }

    return router
