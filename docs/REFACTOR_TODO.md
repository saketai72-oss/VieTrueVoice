# Refactor TODO — ViTrueVoice

> Kế hoạch làm việc hiện tại cho các tác vụ tái cấu trúc và phát triển. Quy tắc chuẩn mực: `docs/GUIDE_developer.md`.

---

## ✅ Đã Hoàn Thành (v0.1.0 & v0.2.0 - Must #1)
- [x] Khởi tạo cấu trúc khung dự án chuẩn và pipeline kiểm thử tự động GitHub Actions CI.
- [x] Cài đặt module tiền xử lý âm thanh 16kHz Mono, cắt khoảng lặng RMS phân vị 20, repeat padding 64.000 mẫu (`src/preprocessing/audio_processor.py`).
- [x] Thiết lập hoàn chỉnh kiến trúc Living Docs 100% bằng tiếng Việt.
- [x] Kịch bản phân chia tập dữ liệu độc lập người nói (`scripts/split_dataset.py`) đảm bảo 0% trùng lặp speaker giữa Train/Dev/Test sets.
- [x] Thuật toán tăng cường dữ liệu RawBoost miền thời gian (`src/preprocessing/rawboost.py`) gồm ISD, SSI, LnL.
- [x] Bộ mô phỏng nén kênh truyền viễn thông & mạng xã hội (`src/preprocessing/codec_simulator.py`) gồm Opus 16kbps, điện thoại 8kHz lọc dải thông 300Hz–3400Hz.
- [x] Kịch bản lọc chất lượng giọng giả bằng ASR WER (`scripts/filter_asr_wer.py`).
- [x] Kịch bản tự động sinh giọng giả (`scripts/generate_spoof.py`).
- [x] Bộ kiểm thử unit tests TDD đạt 21/21 bài kiểm thử vượt qua thành công.

---

## 🚀 Đang Triển Khai (v0.3.0 - Must #2 / W5)
Mục tiêu: Xây dựng kiến trúc mô hình Baseline AASIST & SSL-AASIST và vòng lặp huấn luyện 2 pha trên Kaggle GPU.

- [ ] **1. Kiến trúc mô hình Baseline AASIST & SSL-AASIST (`src/models/`)**
  - [ ] Cài đặt SincConv, ResNet và mô-đun HS-GAL trong `src/models/aasist.py`.
  - [ ] Cài đặt backbone Wav2Vec 2.0 tiếng Việt kết hợp AASIST graph trong `src/models/ssl_aasist.py`.
- [ ] **2. Dataset, DataLoader & Hàm mất mát Weighted Cross-Entropy (`src/training/`)**
  - [ ] PyTorch Dataset tích hợp RawBoost và Codec simulation on-the-fly.
  - [ ] Weighted Cross-Entropy Loss `[0.1, 0.9]`.
- [ ] **3. Vòng lặp huấn luyện 2 pha & Entry-point Kaggle (`train.py`)**
  - [ ] Pha 1: Warm-up đóng băng Wav2Vec2.
  - [ ] Pha 2: Tinh chỉnh toàn mạng với lr=1e-6.
  - [ ] Lưu checkpoint `best_model.pt` theo EER thấp nhất trên tập Dev.

---

## 🧊 Kế Hoạch Tiếp Theo (v0.3.0 - Must #2 & v0.4.0 - Must #3)
- [ ] Xây dựng kiến trúc mô hình Baseline AASIST và SSL-AASIST trong `src/models/`.
- [ ] Xây dựng vòng lặp huấn luyện 2 pha (Warm-up -> Joint Fine-tuning) trong `src/training/` và entry-point `train.py`.
- [ ] Xây dựng dịch vụ suy luận thời gian thực qua FastAPI `/api/v1/predict`, giao diện Gradio và Bot Telegram.
- [ ] Script kiểm thử độ trễ 30 lần liên tiếp (`scripts/benchmark_latency.py`) đảm bảo trung vị <= 3 giây.

---

## An Toàn & Xác Minh
1. Giao thức Tái cấu trúc Không mất mát: Tuyệt đối không thay đổi hành vi của mã nếu không có yêu cầu.
2. Bắt buộc chạy `pytest tests/ -v` kiểm tra trước mỗi commit.
3. Mọi commit do AI thực hiện bắt buộc có tiền tố `[AI]`.

---

*v0.1.0 — 2026-10-16*
