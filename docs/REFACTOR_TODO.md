# Refactor TODO — ViTrueVoice

> Kế hoạch làm việc hiện tại cho các tác vụ tái cấu trúc và phát triển. Quy tắc chuẩn mực: `docs/GUIDE_developer.md`.

---

## ✅ Đã Hoàn Thành (v0.1.0 & v0.2.0/v0.2.4 - Must #1 / Frozen Pipeline V14 & V20)
- [x] Khởi tạo cấu trúc khung dự án chuẩn và pipeline kiểm thử tự động GitHub Actions CI.
- [x] Module tiền xử lý âm thanh 16kHz Mono, cắt khoảng lặng RMS phân vị 20, repeat padding 64.000 mẫu (`src/preprocessing/audio_processor.py`), EBU R128 (-23 LUFS) và Z-score.
- [x] Thuật toán tăng cường dữ liệu RawBoost miền thời gian (`src/preprocessing/rawboost.py`) gồm ISD, SSI, LnL.
- [x] Bộ mô phỏng nén kênh viễn thông & mạng xã hội (`TelephonyCompressor`): Opus 16–32kbps, AMR-NB 12.2kbps, G.711 A-law 64kbps, đo lường độ suy giảm $d'$ ($22.8\%–25.5\%$) và dịch chuyển ngưỡng Narrowband Upward Shift.
- [x] Module `src/vitruevoice/`: Dual Pipeline F5-TTS (Flow Matching, Vocos, dynamic ref_text + ASR auto-fallback 0.2s) & VieNeu-TTS v3 Turbo (48kHz MOSS_48kHz/NeuCodec, sea-g2p Rust), Peak Headroom Scaling $\le 0.95$.
- [x] Tuyển chọn clip đơn Dải vàng 3.5s–7.5s (`allow_stitching=False`) qua 2 tầng LOO Proximity + Output Probe Ranking.
- [x] Bộ lọc chất lượng 4 cổng `MultiGateEvaluator`: Gate 1 ASR WER $\le 15\%$, Gate 2 ECAPA-TDNN Sim $\ge T_{\text{spk}}$, Gate 3 Sanity RMS $\ge 0.01$/Peak $\le 0.999$, Gate 4 Prosody YIN F0 dev $\le 0.30$/score $\ge 0.65$; Multi-Seed Retry.
- [x] Sinh thành công 200 mẫu spoof gốc (106 F5-TTS + 94 VieNeu-TTS) từ 5 tình nguyện viên (`SPK_0001, 0004, 0005, 0006, 0007`).
- [x] Phân hoạch chuẩn V12/V14 (`DatasetPartitioner`): Ref[:3], Enroll[3:7] (K=4 ECAPA-TDNN Centroid), Test held-out (0% data leakage).
- [x] Mở rộng toàn bộ 65 người nói VIVOS và Common Voice 8.0 (22.97h, 419 người nói) với bộ nén MP3 round-trip tương đương bitrate OOD.
- [x] Chuẩn hóa văn bản âm tiết dấu thanh (`_fix_tone_token`), loại bỏ câu chứa chữ số (`has_digits`), NFC cho Gate 1 và lọc trùng lặp; bảo tồn văn bản thô cho prompt TTS.
- [x] Ràng buộc Hard Text-Disjoint ưu tiên (Test $\rightarrow$ Dev $\rightarrow$ Train) và Intra-speaker Ref/Enroll vs Eval hoàn toàn tách biệt.
- [x] Quy tắc Paired Triplets 1:1:1 cho tập Eval (`count_clean == count_g711 == count_amr`).
- [x] Cấu trúc 18 cột manifest chuẩn tắc (`pre_codec`) và bộ dò shortcut quang phổ (`scripts/detect_shortcuts.py`).
- [x] Bộ kiểm thử unit tests TDD nâng cấp đạt **44/44 bài kiểm thử vượt qua thành công 100%**.

---

## 🚀 Đang Triển Khai (v0.3.0 - Must #2 / W5)
Mục tiêu: Xây dựng kiến trúc mô hình Baseline LFCC+GMM / AASIST & SSL-AASIST, thiết kế đối chứng CH1/CH2 và vòng lặp huấn luyện 2 pha trên Kaggle GPU.

- [ ] **1. Kiến trúc mô hình Baseline & SSL-AASIST (`src/models/`)**
  - [ ] Cài đặt LFCC + GMM baseline trên CPU làm mốc so sánh cơ sở.
  - [ ] Cài đặt SincConv, ResNet và mô-đun HS-GAL trong `src/models/aasist.py`.
  - [ ] Cài đặt backbone wav2vec 2.0 tiếng Việt kết hợp AASIST graph trong `src/models/ssl_aasist.py`.
- [ ] **2. Dataset, DataLoader & Hàm mất mát Weighted Cross-Entropy (`src/training/`)**
  - [ ] PyTorch Dataset tích hợp RawBoost và Codec simulation on-the-fly.
  - [ ] Dynamic Weighted Cross-Entropy Loss $w_c = \frac{N}{2 \cdot N_c}$ (tương ứng $\approx [0.33, 0.67]$ cho tỷ lệ Spoof:Bona 2:1; không dùng đồng thời sampler).
- [ ] **3. Vòng lặp huấn luyện 2 pha & Entry-point Kaggle (`train.py` / `train.ipynb`)**
  - [ ] Pha 1: Warm-up 3–5 epochs đóng băng wav2vec 2.0 (lr=1e-4).
  - [ ] Pha 2: Tinh chỉnh toàn mạng với lr=1e-6, kiểm chứng đối chứng:
    - Nhánh đối chứng nén (CH1/H1): Có vs Không tăng cường nén kênh thoại.
    - Nhánh tổng quát hóa (CH2/H2): Seen TTS (F5-TTS) vs Unseen TTS (VieNeu-TTS).
  - [ ] Lưu checkpoint `best_model.pt` theo EER và minDCF thấp nhất trên tập Dev (tập người nói độc lập, không chứa `SPK_xxxx`).

---

## 🧊 Kế Hoạch Tiếp Theo (v0.4.0 - Must #3 & v1.0.0 - W6–W8)
- [ ] Xây dựng dịch vụ suy luận thời gian thực qua FastAPI `/api/v1/predict`, giao diện Gradio ($\le 3$ thao tác) và Bot Telegram (phản hồi $\le 3$ giây).
- [ ] Script kiểm thử độ trễ 30 lần liên tiếp (`scripts/benchmark_latency.py`) đảm bảo trung vị $\le 3$ giây và log ẩn danh SHA-256 (`benchmarks/latency_log.json`).
- [ ] Xây dựng bộ AI Eval $\ge 30$ tình huống (trong đó $\ge 10$ ca từng nhận diện sai).
- [ ] Đóng gói Docker trên Amazon EC2, Amazon ECR, Amazon S3 (Lifecycle auto-delete), CloudWatch và Red Team Pilot cùng CLB An toàn thông tin HUTECH.

---

## An Toàn & Xác Minh
1. Giao thức Tái cấu trúc Không mất mát: Tuyệt đối không thay đổi hành vi của mã nếu không có yêu cầu.
2. Bắt buộc chạy `pytest tests/ -v` kiểm tra trước mỗi commit (đảm bảo giữ vững 31/31 tests xanh).
3. Mọi commit do AI thực hiện bắt buộc có tiền tố `[AI]`.

---

*v0.2.3 — 2026-10-26 (Frozen Pipeline V14)*
