# Refactor TODO — ViTrueVoice

> Kế hoạch làm việc hiện tại cho các tác vụ tái cấu trúc và phát triển. Quy tắc chuẩn mực: `docs/GUIDE_developer.md`.

---

## ✅ Đã Hoàn Thành (v0.1.0)
- [x] Khởi tạo cấu trúc khung dự án chuẩn và pipeline kiểm thử tự động GitHub Actions CI.
- [x] Cài đặt module tiền xử lý âm thanh 16kHz Mono, cắt khoảng lặng RMS phân vị 20, repeat padding 64.000 mẫu kèm 4 bài kiểm thử TDD trong `tests/test_preprocessing.py`.
- [x] Thiết lập hoàn chỉnh kiến trúc Living Docs (`AGENTS.md`, `docs/ARCH_documentation-governance.md`, `docs/GUIDE_developer.md`, `docs/ARCH_technical-specs.md`...) 100% bằng tiếng Việt.

---

## 🚀 Đang Triển Khai (v0.2.0 - Must #1 / W3–W4)
Mục tiêu: Xây dựng đường ống sinh mẫu giả và kịch bản phân chia tập dữ liệu độc lập người nói (Speaker-Disjoint).

- [ ] **1. Kịch bản phân chia tập dữ liệu độc lập người nói (`scripts/split_dataset.py`)**
  - [ ] Viết unit test trước trong `tests/test_split.py` để đảm bảo 0% trùng lặp người nói giữa tập Train, Dev và Test.
  - [ ] Cài đặt tỷ lệ chia 70% Train / 15% Dev / 15% Test và xuất ra `data/manifests/`.
- [ ] **2. Kịch bản lọc chất lượng giọng giả bằng ASR WER (`scripts/filter_asr_wer.py`)**
  - [ ] Lọc bỏ các mẫu âm thanh bị vấp từ, lặp tiếng dựa trên ngưỡng WER của PhoWhisper / Wav2Vec2.
- [ ] **3. Kịch bản tự động sinh giọng giả (`scripts/generate_spoof.py`)**
  - [ ] Tích hợp lệnh CLI sinh mẫu từ F5-TTS và VieNeu-TTS theo kịch bản mạo danh.

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
