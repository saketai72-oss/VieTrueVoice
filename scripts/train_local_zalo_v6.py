#!/usr/bin/env python3
"""Entry-point huấn luyện mô hình B_zalo Version 6 trên GPU cục bộ (NVIDIA GeForce RTX 3050 4GB VRAM).

Cấu hình V6 Tối ưu:
- Tích hợp 125 dòng SPK_0001 vào train_zalo.csv (50.710 dòng).
- Khóa chặt 5 tình nguyện viên đối chứng held-out (SPK_0003..0007) làm Bộ nghiệm thu độc lập.
- batch_size=8, accum_steps=2 -> effective batch size = 16 (giảm 50% số bước/epoch, VRAM ~1.1GB an toàn).
- PyTorch AMP FP16 tự động bật trong Trainer.
- AM-Softmax (s=30.0, m=0.35) + 1.500 mẫu deep-voice tăng cường hạ pitch đã có sẵn offline trong dataset.
- Loại bỏ pitch augmentation CPU online để tăng tốc ~100x (loại bỏ nghẽn CPU STFT phase vocoder).
- Đánh giá tự động 3 Gates kiểm định qua scripts/eval_v5_gate.py với --pooling.
"""

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch


def main():
    print("=" * 60)
    print("🔥 KHỞI ĐỘNG HUẤN LUYỆN LOCAL B_ZALO V6 (GPU RTX 3050 4GB)")
    print("   Chuyển dịch SPK_0001 vào Train - Khóa 5 SPK Nghiệm thu")
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
        fallback_init = Path("out/zalo_b_zalo_v5_local/best_model.pt")
        if fallback_init.exists() and sample_cv.exists() and sample_proxy.exists():
            ckpt_init = fallback_init
            print(f"ℹ️ Khởi tạo từ checkpoint V5: {ckpt_init}")
        else:
            print("⚠️ Checkpoint khởi tạo hoặc dữ liệu âm thanh/proxy Zalo chưa sẵn sàng. Đang chạy setup_local_train.py...")
            subprocess.run([sys.executable, "-u", "scripts/setup_local_train.py"], check=True)

    out_dir = Path("out/zalo_b_zalo_v6_local")
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-u",
        "scripts/train.py",
        "--branch", "B_zalo",
        "--init-ckpt", str(ckpt_init),
        "--manifest-dir", "data/manifests_zalo",
        "--audio-root", ".",
        "--out-dir", str(out_dir),
        "--batch-size", "8",
        "--accum-steps", "2",
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
    print("🚀 BẮT ĐẦU QUÁ TRÌNH HUẤN LUYỆN V6...")
    print("=" * 60 + "\n")

    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        print(f"\n❌ Quá trình huấn luyện kết thúc với mã lỗi: {res.returncode}")
        sys.exit(res.returncode)

    best_model = out_dir / "best_model.pt"
    if best_model.exists():
        print(f"\n🎉 Huấn luyện thành công! Checkpoint V6 đã lưu tại: {best_model}")
        print("\n🔍 Đang chạy đánh giá 3 Gates kiểm định độc lập với --pooling...")
        subprocess.run([sys.executable, "-u", "scripts/eval_v5_gate.py", "--ckpt", str(best_model), "--pooling"], check=False)


if __name__ == "__main__":
    main()
