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
from telegram.request import HTTPXRequest

from src.app.decision import classify_score, platt_calibrator
from src.app.server import DEFAULT_CHECKPOINT, TARGET_SAMPLE_COUNT, _default_model_loader, _load_audio_in_memory
from src.preprocessing.pooling import extract_window_batch, pool_scores


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
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    device: str = "cpu",
    threshold: float = 0.0,
    calibrator: Any = platt_calibrator,
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

    try:
        try:
            if message.chat:
                await message.chat.send_action("typing")
        except Exception:
            pass

        try:
            file_obj = await voice_target.get_file(read_timeout=30.0)
        except TypeError:
            file_obj = await voice_target.get_file()

        buf = io.BytesIO()
        try:
            download_res = file_obj.download_to_memory(buf, read_timeout=30.0)
        except TypeError:
            download_res = file_obj.download_to_memory(buf)

        if inspect.isawaitable(download_res):
            await download_res
        raw_bytes = buf.getvalue()

        if not raw_bytes:
            await message.reply_text("❌ Không thể tải nội dung âm thanh.")
            return

        audio_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
        audio_data = _load_audio_in_memory(raw_bytes)
        # Multi-window extraction (STUBBORN_FACT: repeat padding <64k, single batched forward pass)
        windows_batch = extract_window_batch(
            audio_data,
            win=TARGET_SAMPLE_COUNT,
            hop=16000,
            max_windows=5,
        ).to(device)
        n_windows = int(windows_batch.shape[0])

        with torch.inference_mode():
            score_tensor = active_model.score(windows_batch)
            if isinstance(score_tensor, torch.Tensor):
                scores_np = score_tensor.squeeze(-1).float().cpu().numpy()
            else:
                scores_np = np.asarray(score_tensor)
            if scores_np.ndim == 0:
                scores_np = np.array([float(scores_np)])
            raw_score = float(pool_scores(scores_np, mode="max"))

        latency = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold, calibrator=calibrator)

        if decision.confidence_calibrated and decision.confidence is not None:
            conf_str = f"`{decision.confidence * 100:.1f}%` (Đã hiệu chuẩn Platt Scaling)"
        else:
            conf_str = "Chưa hiệu chuẩn xác suất phần trăm"

        if decision.is_bonafide:
            reply = (
                f"🛡️ *KẾT QUẢ: GIỌNG NÓI THẬT (BONAFIDE)*\n\n"
                f"• *Điểm phân định (Raw score)*: `{raw_score:+.4f}` (Ngưỡng: `{threshold:+.4f}`)\n"
                f"• *Phân tích đa cửa sổ*: `{n_windows}` cửa sổ trượt (Max-Pooling)\n"
                f"• *Độ tin cậy*: {conf_str}\n"
                f"• *Thời gian xử lý*: `{latency:.2f}s`\n"
                f"• *Mã băm kiểm định*: `{audio_hash}...`\n\n"
                f"✅ *Đánh giá*: Âm thanh tự nhiên, không phát hiện dấu vết công nghệ tổng hợp giọng nói AI."
            )
        else:
            reply = (
                f"🚨 *CẢNH BÁO LỪA ĐẢO: ĐÂY LÀ GIỌNG NÓI GIẢ MẠO (SPOOF)*\n\n"
                f"• *Điểm phân định (Raw score)*: `{raw_score:+.4f}` (Ngưỡng: `{threshold:+.4f}`)\n"
                f"• *Phân tích đa cửa sổ*: `{n_windows}` cửa sổ trượt (Max-Pooling)\n"
                f"• *Độ tin cậy phát hiện*: {conf_str}\n"
                f"• *Thời gian xử lý*: `{latency:.2f}s`\n"
                f"• *Mã băm kiểm định*: `{audio_hash}...`\n\n"
                f"⚠️ *KHUYẾN CÁO KHẨN CẤP*:\n"
                f"1. Tuyệt đối *KHÔNG* chuyển tiền hoặc cung cấp mã OTP.\n"
                f"2. Hãy gọi điện trực tiếp lại cho người thân bằng số điện thoại di động thông thường để xác minh danh tính."
            )

        await message.reply_text(reply, parse_mode="Markdown")

    except Exception as exc:
        await message.reply_text(f"❌ Lỗi khi phân tích âm thanh: {exc}\n\n👉 Vui lòng thử gửi lại một lần nữa.")


def build_bot_app(
    token: str,
    model: Any = None,
    device: str = "cpu",
    threshold: float = 0.0,
    calibrator: Any = platt_calibrator,
) -> Application:
    request_cfg = HTTPXRequest(
        connection_pool_size=16,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=20.0,
        pool_timeout=10.0,
    )
    app = Application.builder().token(token).request(request_cfg).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    async def _on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_voice_message(
            update,
            context,
            model=model,
            device=device,
            threshold=threshold,
            calibrator=calibrator,
        )

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, _on_voice))
    return app


def main() -> None:
    import argparse
    import os

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    parser = argparse.ArgumentParser(description="Khởi chạy ViTrueVoice Telegram Bot")
    parser.add_argument("--token", default=os.getenv("TELEGRAM_BOT_TOKEN"),
                        help="Telegram Bot Token từ @BotFather (hoặc đặt biến môi trường TELEGRAM_BOT_TOKEN)")
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT),
                        help="Đường dẫn file trọng số checkpoint mô hình")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu",
                        help="Thiết bị suy luận (cuda hoặc cpu)")
    parser.add_argument("--threshold", type=float, default=0.0,
                        help="Ngưỡng phân định (mặc định: 0.0)")
    args = parser.parse_args()

    token = args.token
    if not token:
        print("⏸️ [ViTrueVoice Bot Daemon] Chưa có Telegram Bot Token. Đang tạm dừng chờ cấu hình...")
        print("👉 Hướng dẫn lấy token:")
        print("   1. Mở Telegram, tìm kiếm bot @BotFather (https://t.me/BotFather) và gửi lệnh /newbot")
        print("   2. Sao chép API Token nhận được (dạng: 123456789:ABCdefGhI...)")
        print("   3. Đặt vào file .env: TELEGRAM_BOT_TOKEN=<TOKEN_CỦA_BẠN>")
        print("   4. Khởi động lại bot bằng lệnh: docker compose restart bot")
        try:
            while True:
                time.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            return

    print("=" * 60)
    print("🛡️ KHỞI ĐỘNG VITRUEVOICE TELEGRAM BOT")
    print("=" * 60)
    print(f"📦 Checkpoint: {args.checkpoint}")
    print(f"⚙️ Thiết bị:   {args.device}")
    print(f"🎯 Ngưỡng:     {args.threshold:+.4f}")
    print(f"🌊 Pooling:    Multi-window Max-Pool (win=64k, hop=16k, max=5)")
    print("🤖 Đang tải mô hình...")

    loaded_model = _default_model_loader(args.checkpoint, args.device)
    if loaded_model is None:
        print("❌ LỖI: Không thể nạp mô hình từ checkpoint!")
        return

    print("✅ Nạp mô hình thành công!")
    print("🚀 Đang kết nối tới Telegram và bắt đầu lắng nghe tin nhắn thoại...")
    print("   (Nhấn Ctrl+C để dừng bot)")
    print("=" * 60)

    app = build_bot_app(
        token=token,
        model=loaded_model,
        device=args.device,
        threshold=args.threshold,
    )
    app.run_polling()


if __name__ == "__main__":
    main()
