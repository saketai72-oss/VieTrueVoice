"""Telegram bot for ViTrueVoice anti-spoofing voice verification."""

from __future__ import annotations
import hashlib
import inspect
import io
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.app.decision import classify_score
from src.app.server import TARGET_SAMPLE_COUNT, _default_model_loader, _load_audio_in_memory, _pad_or_crop


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "🛡️ *Chào mừng bạn đến với ViTrueVoice Bot!*\n\n"
            "Hãy chuyển tiếp (forward) hoặc gửi một *tin nhắn thoại* hoặc *file âm thanh* nghi ngờ vào đây. "
            "Hệ thống AI sẽ phân tích trực tiếp trên RAM và phản hồi kết quả trong vòng 1-2 giây.\n\n"
            "🔒 *Bảo mật*: Mọi âm thanh được xóa hủy ngay sau khi suy luận, tuân thủ Luật 91/2025/QH15.",
            parse_mode="Markdown",
        )


async def handle_voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    model: Any = None,
    checkpoint_path: Path | str = Path("out/run_B/best_model.pt"),
    device: str = "cpu",
    threshold: float = 0.0,
) -> None:
    if not update.message:
        return

    message = update.message
    voice_target = message.voice or message.audio
    if not voice_target:
        await message.reply_text("⚠️ Vui lòng gửi một tin nhắn thoại hoặc tệp âm thanh hợp lệ.")
        return

    # Check model
    active_model = model
    if active_model is None:
        active_model = _default_model_loader(checkpoint_path, device)
        if active_model is None:
            await message.reply_text("❌ Lỗi: Hệ thống chưa nạp được mô hình kiểm định.")
            return

    t0 = time.perf_counter()
    file_obj = await voice_target.get_file()
    buf = io.BytesIO()
    download_res = file_obj.download_to_memory(buf)
    if inspect.isawaitable(download_res):
        await download_res
    raw_bytes = buf.getvalue()

    if not raw_bytes:
        await message.reply_text("❌ Không thể tải nội dung âm thanh.")
        return

    audio_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]

    try:
        audio_data = _load_audio_in_memory(raw_bytes)
        padded = _pad_or_crop(audio_data, TARGET_SAMPLE_COUNT)
        tensor_in = torch.tensor(padded, dtype=torch.float32, device=device).unsqueeze(0)

        with torch.inference_mode():
            score_out = active_model.score(tensor_in)
            raw_score = float(score_out.item() if hasattr(score_out, "item") else score_out[0])

        latency = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold)

        if decision.is_bonafide:
            reply = (
                f"🛡️ *KẾT QUẢ: GIỌNG NÓI THẬT (BONAFIDE)*\n\n"
                f"• *Điểm phân định (Raw score)*: `{raw_score:+.4f}` (Ngưỡng: `{threshold:+.4f}`)\n"
                f"• *Độ tin cậy*: Chưa hiệu chuẩn xác suất phần trăm\n"
                f"• *Thời gian xử lý*: `{latency:.2f}s`\n"
                f"• *Mã băm kiểm định*: `{audio_hash}...`\n\n"
                f"✅ *Đánh giá*: Âm thanh tự nhiên, không phát hiện dấu vết công nghệ tổng hợp giọng nói AI."
            )
        else:
            reply = (
                f"🚨 *CẢNH BÁO LỪA ĐẢO: ĐÂY LÀ GIỌNG NÓI GIẢ MẠO (SPOOF)*\n\n"
                f"• *Điểm phân định (Raw score)*: `{raw_score:+.4f}` (Ngưỡng: `{threshold:+.4f}`)\n"
                f"• *Độ tin cậy*: Chưa hiệu chuẩn xác suất phần trăm\n"
                f"• *Thời gian xử lý*: `{latency:.2f}s`\n"
                f"• *Mã băm kiểm định*: `{audio_hash}...`\n\n"
                f"⚠️ *KHUYẾN CÁO KHẨN CẤP*:\n"
                f"1. Tuyệt đối *KHÔNG* chuyển tiền hoặc cung cấp mã OTP.\n"
                f"2. Hãy gọi điện trực tiếp lại cho người thân bằng số điện thoại di động thông thường để xác minh danh tính."
            )

        await message.reply_text(reply, parse_mode="Markdown")

    except Exception as exc:
        await message.reply_text(f"❌ Lỗi khi phân tích âm thanh: {exc}")


def build_bot_app(
    token: str,
    model: Any = None,
    device: str = "cpu",
    threshold: float = 0.0,
) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    async def _on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_voice_message(update, context, model=model, device=device, threshold=threshold)

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, _on_voice))
    return app
