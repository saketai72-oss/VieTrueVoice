#!/usr/bin/env python3
"""Entry-point huấn luyện mô hình B_zalo Version 5 trên GPU cục bộ (NVIDIA GeForce RTX 3050 4GB VRAM).

Tối ưu hóa:
- batch_size=4, accum_steps=4 -> effective batch size = 16
- PyTorch AMP FP16 tự động bật trong Trainer
- Tiêu thụ VRAM dự kiến: 2.8 - 3.2 GB (không gây OOM)
- Đánh giá tự động 3 Gates kiểm định sau khi huấn luyện hoàn tất
"""

import subprocess
import sys
from pathlib import Path

# Đảm bảo đường dẫn gốc của project luôn nằm trong sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch


def main():
    print("=" * 60)
    print("🔥 KHỞI ĐỘNG HUẤN LUYỆN LOCAL B_ZALO V5 (GPU RTX 3050 4GB)")
    print("=" * 60)

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"🎮 GPU Device: {gpu_name}")
        print(f"📊 Total VRAM:  {vram_gb:.2f} GB")
        device = "cuda"
    else:
        print("⚠️ CẢNH BÁO: Không tìm thấy CUDA GPU, sẽ chạy trên CPU.")
        device = "cpu"

    ckpt_init = Path("out/kaggle_ssl_out/best_model_B.pt")
    sample_cv = Path("data/spoof_f5tts/CV_08110ec9e6")
    sample_proxy = Path("data/raw/CV_08110ec9e6/common_voice_vi_27640713_aac_zalo.wav")
    if not ckpt_init.exists() or not sample_cv.exists() or not sample_proxy.exists():
        print("⚠️ Checkpoint B hoặc dữ liệu âm thanh/proxy Zalo chưa sẵn sàng. Đang chạy setup_local_train.py...")
        subprocess.run([sys.executable, "-u", "scripts/setup_local_train.py"], check=True)

    out_dir = Path("out/zalo_b_zalo_v5_local")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cấu hình huấn luyện tối ưu hóa cho 4GB VRAM
    cmd = [
        sys.executable,
        "-u",
        "scripts/train.py",
        "--branch", "B_zalo",
        "--init-ckpt", str(ckpt_init),
        "--manifest-dir", "data/manifests_zalo",
        "--audio-root", ".",
        "--out-dir", str(out_dir),
        "--batch-size", "4",
        "--accum-steps", "4",
        "--loss", "am_softmax",
        "--am-s", "30.0",
        "--am-m", "0.35",
        "--phase1-epochs", "2",
        "--phase2-epochs", "15",
        "--patience", "4",
        "--num-workers", "2",
        "--device", device,
    ]

    print("\n⚙️ Lệnh thực thi:")
    print(" ".join(cmd))
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU QUÁ TRÌNH HUẤN LUYỆN...")
    print("=" * 60 + "\n")

    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        print(f"\n❌ Quá trình huấn luyện kết thúc với mã lỗi: {res.returncode}")
        sys.exit(res.returncode)

    best_model = out_dir / "best_model.pt"
    if best_model.exists():
        print(f"\n🎉 Huấn luyện thành công! Checkpoint đã lưu tại: {best_model}")
        print("\n🔍 Đang chạy đánh giá 3 Gates kiểm định qua scripts/eval_v5_gate.py...")
        subprocess.run([sys.executable, "-u", "scripts/eval_v5_gate.py", "--ckpt", str(best_model)], check=False)


if __name__ == "__main__":
    main()
