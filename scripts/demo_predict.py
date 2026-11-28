"""Quick CLI & FastAPI Web UI demo runner for VieTrueVoice anti-spoofing detection.

Usage:
  python scripts/demo_predict.py                  # Demo tự động trên 3 mẫu đối chứng
  python scripts/demo_predict.py <path_to_audio>  # Phân loại 1 file âm thanh bất kỳ
  python scripts/demo_predict.py --web            # Khởi động FastAPI + WebGL Forensics UI (port 8000)
  python scripts/demo_predict.py --server         # Khởi động FastAPI Server (port 8000)
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.app.decision import classify_score, platt_calibrator
from src.app.forensics import extract_forensic_analysis
from src.app.server import (
    DEFAULT_CHECKPOINT,
    DEFAULT_DEVICE,
    TARGET_SAMPLE_RATE,
    _condition_audio_for_inference,
    _default_model_loader,
    _load_audio_in_memory,
    _score_waveform,
    create_app,
)


def run_cli_demo(audio_path: str, model: Any, device: str, threshold: float = 0.0) -> None:
    path = Path(audio_path)
    if not path.exists():
        print(f"Không tìm thấy tệp: {audio_path}")
        return

    print(f"\nĐang phân tích: {path.name} ({path})")
    t0 = time.perf_counter()
    raw_bytes = path.read_bytes()
    audio_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    audio_data = _condition_audio_for_inference(_load_audio_in_memory(raw_bytes))
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
    dt = time.perf_counter() - t0

    verdict = "BONA_FIDE (GIỌNG THẬT)" if decision.is_bonafide else "SPOOF (GIỌNG GIẢ MẠO)"
    conf_pct = (
        forensics["platt_curve"]["prob_bona_pct"]
        if decision.is_bonafide
        else forensics["platt_curve"]["prob_spoof_pct"]
    )
    print(f"Kết quả      : {verdict} [{decision.risk_level}]")
    print(f"Platt Prob   : {conf_pct:.1f}% (Bona={forensics['platt_curve']['prob_bona_pct']:.1f}% | Spoof={forensics['platt_curve']['prob_spoof_pct']:.1f}%)")
    print(f"Raw Logit    : {decision.raw_score:+.4f} (threshold={threshold:+.2f}, windows={n_windows})")
    print(f"Pooling      : {forensics['pooling']['branch']} — {forensics['pooling']['explanation']}")
    print(f"Acoustic     : dur={forensics['duration_sec']}s | F0={forensics['estimated_f0_hz']}Hz | HF={forensics['hf_ratio_pct']}% | {forensics['bandwidth_profile']}")
    print(f"Thời gian    : {dt:.3f}s | SHA-256: {audio_sha256[:16]}...")
    print("-" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="VieTrueVoice CLI & FastAPI Web UI Runner")
    parser.add_argument("audio", nargs="?", default=None, help="Đường dẫn file âm thanh cần test")
    parser.add_argument("--web", action="store_true", help="Khởi động FastAPI + WebGL Forensics UI (uvicorn)")
    parser.add_argument("--server", action="store_true", help="Khởi động máy chủ FastAPI (uvicorn)")
    parser.add_argument("--port", type=int, default=8000, help="Cổng chạy Web UI / Server (mặc định 8000)")
    parser.add_argument("--ckpt", type=str, default=str(DEFAULT_CHECKPOINT), help="Checkpoint model")
    parser.add_argument("--device", type=str, default=DEFAULT_DEVICE, help="Thiết bị tính toán (cpu / cuda)")
    parser.add_argument("--threshold", type=float, default=0.0, help="Ngưỡng quyết định")
    args = parser.parse_args()

    if args.web or args.server:
        import uvicorn

        print(f"Đang khởi động VieTrueVoice FastAPI + WebGL Forensics UI trên cổng {args.port}...")
        print(f"Web UI       : http://localhost:{args.port}/")
        print(f"Swagger Docs : http://localhost:{args.port}/docs")
        app = create_app(
            checkpoint_path=args.ckpt,
            device=args.device,
            threshold=args.threshold,
        )
        uvicorn.run(app, host="0.0.0.0", port=args.port)
        return

    # CLI direct model inference mode
    print(f"Khởi tạo mô hình từ checkpoint: {args.ckpt} trên {args.device.upper()}...")
    model = _default_model_loader(args.ckpt, args.device)
    if model is None:
        print(f"Không thể nạp checkpoint tại: {args.ckpt}")
        sys.exit(1)

    if args.audio:
        run_cli_demo(args.audio, model, args.device, threshold=args.threshold)
    else:
        print("Không có file chỉ định. Đang chạy kiểm thử tự động trên 3 mẫu đối chứng:")
        samples = [
            ("Giọng Thật (Bona Fide - SPK_0004)", "src/app/static/samples/sample_bonafide_spk0004.wav"),
            ("Giọng Giả Seen TTS (F5-TTS)", "src/app/static/samples/sample_spoof_f5tts.wav"),
            ("Giọng Giả OmniVoice CFM", "src/app/static/samples/sample_spoof_voicestudio_cfm.wav"),
        ]
        for name, sample_path in samples:
            print(f"\n>>> MẪU KIỂM THỬ: {name}")
            run_cli_demo(sample_path, model, args.device, threshold=args.threshold)


if __name__ == "__main__":
    main()
