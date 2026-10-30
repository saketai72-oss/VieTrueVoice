"""Gradio Web UI for ViTrueVoice voice anti-spoofing detection.

Designed for elderly/parents (US4, NFR4): <= 3 actions, clear color indicators,
clear fraud prevention advice.
"""

from __future__ import annotations
import hashlib
import sys
import time
from pathlib import Path
from typing import Any, Callable

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr
import numpy as np
import torch

from src.app.decision import classify_score
from src.app.server import TARGET_SAMPLE_COUNT, TARGET_SAMPLE_RATE, _default_model_loader, _pad_or_crop
from src.preprocessing.audio_loader import load_audio


def make_predict_fn(
    model: Any = None,
    checkpoint_path: Path | str = Path("out/run_B/best_model.pt"),
    device: str = "cpu",
    threshold: float = 0.0,
    model_loader: Callable[[Path | str, str], Any] | None = None,
) -> Callable[[Any], tuple[str, str, str]]:
    active_model = model
    loader = model_loader or _default_model_loader

    def predict_audio(audio_input: Any) -> tuple[str, str, str]:
        nonlocal active_model
        if audio_input is None:
            return (
                "⚠️ Chưa cung cấp file âm thanh!",
                "Chưa hiệu chuẩn",
                "Vui lòng ghi âm hoặc tải lên một đoạn tin nhắn thoại.",
            )

        t0 = time.perf_counter()
        if active_model is None:
            active_model = loader(checkpoint_path, device)
            if active_model is None:
                return (
                    "❌ Không tìm thấy mô hình!",
                    "Lỗi hệ thống",
                    f"Không thể nạp trọng số từ {checkpoint_path}.",
                )

        # Gradio audio input can be a filepath (str) or a tuple (sample_rate, numpy_array)
        if isinstance(audio_input, str):
            data = load_audio(audio_input, target_sr=TARGET_SAMPLE_RATE)
            sr = TARGET_SAMPLE_RATE
        elif isinstance(audio_input, tuple) and len(audio_input) == 2:
            sr, data = audio_input
            if data.dtype in (np.int16, np.int32):
                data = data.astype(np.float32) / (32768.0 if data.dtype == np.int16 else 2147483648.0)
            elif data.dtype != np.float32:
                data = data.astype(np.float32)
            if data.ndim > 1:
                data = data.mean(axis=-1)
            if sr != TARGET_SAMPLE_RATE:
                import librosa
                data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)
        else:
            return ("❌ Định dạng âm thanh không hợp lệ!", "Lỗi", "Không thể phân tích dữ liệu.")

        raw_bytes = data.tobytes()
        audio_sha256 = hashlib.sha256(raw_bytes).hexdigest()[:16]

        padded = _pad_or_crop(data, TARGET_SAMPLE_COUNT)
        tensor_in = torch.tensor(padded, dtype=torch.float32, device=device).unsqueeze(0)

        with torch.inference_mode():
            score_out = active_model.score(tensor_in)
            raw_score = float(score_out.item() if hasattr(score_out, "item") else score_out[0])

        latency = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold)

        if decision.is_bonafide:
            verdict = "🛡️ GIỌNG THẬT (BONAFIDE)"
            if decision.confidence_calibrated and decision.confidence is not None:
                conf_str = f"Độ tin cậy: {decision.confidence * 100:.1f}%"
            else:
                conf_str = f"Chưa hiệu chuẩn xác suất (Điểm thô: {raw_score:+.2f} | Ngưỡng: {threshold:+.2f})"
            detail = (
                f"✅ Xác thực: Không phát hiện dấu hiệu tổng hợp âm thanh bằng AI.\n"
                f"📊 Điểm raw score: {raw_score:.4f} (Ngưỡng phân định: {threshold:.4f})\n"
                f"⏱️ Thời gian xử lý: {latency:.2f}s | Mã băm: {audio_sha256}..."
            )
        else:
            verdict = "⚠️ CẢNH BÁO: GIỌNG NÓI GIẢ MẠO (SPOOF)"
            if decision.confidence_calibrated and decision.confidence is not None:
                conf_str = f"Độ tin cậy phát hiện: {decision.confidence * 100:.1f}%"
            else:
                conf_str = f"Chưa hiệu chuẩn xác suất (Điểm thô: {raw_score:+.2f} | Ngưỡng: {threshold:+.2f})"
            detail = (
                f"🚨 Khuyến cáo: Đoạn thoại này có dấu hiệu được tạo bởi công nghệ nhái giọng (Deepfake / TTS).\n"
                f"👉 TUYỆT ĐỐI KHÔNG: Chuyển tiền, gửi thông tin tài khoản ngân hàng hoặc đọc mã OTP.\n"
                f"📊 Điểm raw score: {raw_score:.4f} (Ngưỡng phân định: {threshold:.4f})\n"
                f"⏱️ Thời gian xử lý: {latency:.2f}s | Mã băm: {audio_sha256}..."
            )

        return verdict, conf_str, detail

    return predict_audio


def build_ui(
    model: Any = None,
    checkpoint_path: Path | str = Path("out/run_B/best_model.pt"),
    device: str = "cpu",
    threshold: float = 0.0,
) -> gr.Blocks:
    predict_fn = make_predict_fn(
        model=model,
        checkpoint_path=checkpoint_path,
        device=device,
        threshold=threshold,
    )

    with gr.Blocks(title="ViTrueVoice — Hệ Thống Phát Hiện Giọng Nói Giả Mạo") as demo:
        gr.Markdown(
            """
            # 🛡️ ViTrueVoice — Phòng Chống Lừa Đảo Giọng Nói Giả Mạo
            ### *Dành cho người lớn tuổi & gia đình: Kiểm tra tin nhắn thoại chỉ với 1 lần bấm*
            ---
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(
                    label="1. Tải lên tin nhắn thoại hoặc Bấm ghi âm",
                    sources=["upload", "microphone"],
                    type="numpy",
                )
                submit_btn = gr.Button(
                    "🔍 2. KIỂM TRA NGAY",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=1):
                result_verdict = gr.Textbox(
                    label="3. Kết quả xác minh",
                    placeholder="Kết quả sẽ hiển thị tại đây...",
                    interactive=False,
                    lines=1,
                )
                result_conf = gr.Textbox(
                    label="Độ tin cậy phân tích",
                    interactive=False,
                    lines=1,
                )
                result_detail = gr.Textbox(
                    label="Hướng dẫn an toàn & Chi tiết kỹ thuật",
                    interactive=False,
                    lines=4,
                )

        submit_btn.click(
            fn=predict_fn,
            inputs=[audio_input],
            outputs=[result_verdict, result_conf, result_detail],
        )

        gr.Markdown(
            """
            ---
            🔒 *Bảo vệ quyền riêng tư theo Luật 91/2025/QH15: Âm thanh được phân tích trực tiếp trên bộ nhớ RAM và xóa hủy ngay lập tức, không lưu trữ giọng nói gốc.*
            """
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
