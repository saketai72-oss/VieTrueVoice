"""Quick CLI & Web demo runner for ViTrueVoice anti-spoofing detection.

Usage:
  python scripts/demo_predict.py                  # Demo tự động trên 3 mẫu (Thật, F5-TTS, VieNeu-TTS)
  python scripts/demo_predict.py <path_to_audio>  # Phân loại 1 file âm thanh bất kỳ
  python scripts/demo_predict.py --web            # Mở giao diện Web Gradio
  python scripts/demo_predict.py --server         # Khởi động FastAPI server
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

# Ensure root in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.app.ui import make_predict_fn, DEFAULT_CHECKPOINT, build_ui


def run_cli_demo(audio_path: str, fn) -> None:
    path = Path(audio_path)
    if not path.exists():
        print(f"❌ Không tìm thấy tệp: {audio_path}")
        return

    print(f"\n🎵 Đang phân tích: {path.name} ({path})")
    t0 = time.perf_counter()
    verdict, conf, detail = fn(str(path))
    dt = time.perf_counter() - t0

    print(f"Kết quả      : {verdict}")
    print(f"Độ tin cậy   : {conf}")
    print(f"Thời gian    : {dt:.3f}s")
    print(f"Chi tiết     :\n{detail}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="ViTrueVoice Demo Runner")
    parser.add_argument("audio", nargs="?", default=None, help="Đường dẫn file âm thanh cần test")
    parser.add_argument("--web", action="store_true", help="Chạy giao diện Web Gradio")
    parser.add_argument("--server", action="store_true", help="Chạy máy chủ FastAPI")
    parser.add_argument("--port", type=int, default=7860, help="Cổng chạy Web UI / Server")
    parser.add_argument("--ckpt", type=str, default=str(DEFAULT_CHECKPOINT), help="Checkpoint model")
    parser.add_argument("--device", type=str, default="cpu", help="Thiết bị tính toán (cpu / cuda)")
    args = parser.parse_args()

    if args.web:
        print(f"🚀 Đang khởi động Gradio Web UI với checkpoint: {args.ckpt}")
        print("⏳ Đang tải trước mô hình và khởi động (warm-up) để lần bấm đầu tiên phản hồi tức thời...")
        demo = build_ui(checkpoint_path=args.ckpt, device=args.device, preload=True)
        print(f"🌐 Truy cập tại: http://localhost:{args.port}")
        demo.launch(server_name="0.0.0.0", server_port=args.port)
        return

    if args.server:
        import uvicorn
        print(f"🚀 Đang khởi động FastAPI Server trên cổng {args.port}...")
        print(f"📖 Swagger Docs: http://localhost:{args.port}/docs")
        uvicorn.run("src.app.server:app", host="0.0.0.0", port=args.port, reload=True)
        return

    # CLI mode
    print(f"📦 Khởi tạo mô hình từ checkpoint: {args.ckpt} trên {args.device.upper()}...")
    fn = make_predict_fn(checkpoint_path=args.ckpt, device=args.device)

    if args.audio:
        run_cli_demo(args.audio, fn)
    else:
        print("🔍 Không có file chỉ định. Đang chạy kiểm thử tự động trên 3 mẫu đối chứng:")
        samples = [
            ("Giọng Thật (Bona Fide - SPK_0003)", "data/raw/SPK_0003/SPK_0003_01.wav"),
            ("Giọng Giả Seen TTS (F5-TTS - SPK_0003)", "data/spoof_f5tts/SPK_0003/SPK_0003_prompt_006.wav"),
            ("Giọng Giả Unseen TTS (VieNeu-TTS - SPK_0003)", "data/spoof_vieneu/SPK_0003/SPK_0003_prompt_006.wav"),
        ]
        for name, p in samples:
            print(f"\n>>> MẪU KIỂM THỬ: {name}")
            run_cli_demo(p, fn)


if __name__ == "__main__":
    main()
