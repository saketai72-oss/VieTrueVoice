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

## ✅ Đã Hoàn Thành (v0.3.0 - Must #2 / W5 & v0.4.0 - Must #3)
Mục tiêu: Xây dựng kiến trúc mô hình Baseline LFCC+GMM / AASIST & SSL-AASIST, thiết kế đối chứng CH1/CH2, vòng lặp huấn luyện 2 pha, tinh chỉnh Zalo B_zalo V6, dịch vụ thời gian thực và trọn bộ minh chứng Checkpoint W05.

- [x] **1. Kiến trúc mô hình Baseline & SSL-AASIST (`src/models/`)**
  - [x] Cài đặt LFCC + GMM baseline trên CPU làm mốc so sánh cơ sở (`src/models/baseline_gmm.py`).
  - [x] Cài đặt SincConv, ResNet và mô-đun HS-GAL trong `src/models/aasist.py`.
  - [x] Cài đặt backbone wav2vec 2.0 tiếng Việt kết hợp AASIST graph trong `src/models/ssl_aasist.py`.
- [x] **2. Dataset, DataLoader & Hàm mất mát Weighted Cross-Entropy / AM-Softmax (`src/training/`)**
  - [x] PyTorch Dataset tích hợp RawBoost và Codec simulation on-the-fly (`src/training/dataset.py`).
  - [x] Dynamic Weighted Cross-Entropy Loss $w_c = \frac{N}{2 \cdot N_c}$ và Additive Margin Softmax (AM-Softmax, margin $m=0.35$, scale $s=30.0$).
  - [x] Huấn luyện thành công Checkpoint B_zalo V6 Local (`out/zalo_b_zalo_v6_local/best_model.pt`, Dev EER 2.60%).
- [x] **3. Đánh giá đối chứng & Nghiệm thu 3 Cổng (Gates)**
  - [x] Nhánh đối chứng nén (CH1/H1): PASS (giảm 40.46% AMR-NB, 47.55% G.711).
  - [x] Nhánh tổng quát hóa (CH2/H2): Seen TTS (F5-TTS, EER 3.28%) vs Unseen TTS (VieNeu-TTS, EER 21.88%–26.34%).
  - [x] Multi-window Max-Pooling inference (`src/preprocessing/pooling.py`): Gate 2 trên 4 SPK đối chứng đạt 100.0% (64/64), trên 5 SPK nghiệm thu đạt 96.4% (81/84); Gate 3 Zalo AAC/Opus EER 1.56%–1.73%.
  - [x] Chuyển `SPK_0001` sang train (`train_zalo.csv`), khóa 5 tình nguyện viên (`SPK_0003`..`0007`, 84 clips) làm Bộ nghiệm thu độc lập chính thức.
- [x] **4. Dịch vụ người dùng & Minh chứng Checkpoint W05**
  - [x] Xây dựng dịch vụ suy luận thời gian thực qua FastAPI `/api/v1/predict` (`src/app/server.py`), Web Gradio (`src/app/ui.py`) và Bot Telegram (`src/app/bot.py`, `scripts/run_bot.py`).
  - [x] Chuẩn đo độ trễ NFR-1 với 30 lần lặp (`benchmarks/latency_benchmark.csv`), trung vị 66.3ms (model) / 352ms (API) $\le 3.0$s; log ẩn danh SHA-256 (`benchmarks/latency_log.json`).
  - [x] Xây dựng bộ dữ liệu đánh giá thực tế (AI Eval) 30 ca (`tests/eval_scenarios_30.csv`).
  - [x] Sơ đồ quy trình Trước/Sau tích hợp (Hitachi CRM/ERP): giảm từ 280s (5 bước làm tay) xuống 3.5s (2 bước tự động), tiết kiệm 98.7% thời gian.
  - [x] Chương 2 hoàn chỉnh (18 trang học thuật, tích hợp công thức, trích dẫn IEEE và bóc tách âm học).
  - [x] Hoàn thành 100% cả 3 chứng chỉ AWS Academy Gói A (Cloud Foundations, Security, Architecting).
  - [x] Xuất bản báo cáo chính thức `DACN_2380601959_NguyenThanhTai_W05.docx` và `DACN_2380601959_NguyenThanhTai_W05.pdf`.

---

## 🧊 Kế Hoạch Tiếp Theo (v1.0.0 - W7–W8)
- [ ] Đóng gói Docker trên Amazon EC2, Amazon ECR, Amazon S3 (Lifecycle auto-delete), AWS CloudWatch.
- [ ] Thử nghiệm Pilot & Red Team cùng CLB An toàn thông tin HUTECH.
- [ ] Hoàn thiện báo cáo toàn văn Đề tài (Chương 3 & 4) và chuẩn bị slide bảo vệ trước Hội đồng chuyên môn.

---

## An Toàn & Xác Minh
1. Giao thức Tái cấu trúc Không mất mát: Tuyệt đối không thay đổi hành vi của mã nếu không có yêu cầu.
2. Bắt buộc chạy `pytest tests/ -v` kiểm tra trước mỗi commit (đảm bảo giữ vững 274/274 tests xanh 100%).
3. Mọi commit do AI thực hiện bắt buộc có tiền tố `[AI]`.

---

*v0.4.4 — 2026-11-08 (W05 Complete)*
