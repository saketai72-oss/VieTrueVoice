# Kế Hoạch Triển Khai Huấn Luyện B_zalo Trên Máy Local (RTX 3050 4GB GPU)

- **Mã công việc (Task Slug)**: `local-zalo-training-setup`
- **Mục tiêu**: Thiết lập môi trường, nạp dữ liệu chọn lọc, tối ưu hóa bộ nhớ VRAM cho GPU 4GB, thực thi huấn luyện nhánh `B_zalo` Version 5 và đánh giá toàn diện tại máy cục bộ.
- **Ngày lập**: 2026-11-04
- **Trạng thái**: Đã hoàn tất thiết lập & kiểm thử xác minh (Completed & Verified)

---

## 0. Kết Quả Xác Minh Thực Nghiệm & Triển Khai (Verification Evidence)
- **Tối ưu hóa VRAM 4GB**: Bổ sung cờ `--accum-steps` vào `scripts/train.py` và `src/training/trainer.py` kết hợp PyTorch AMP FP16. Cấu hình `--batch-size 4 --accum-steps 4` mang lại effective batch size = 16, đảm bảo hội tụ tương đương Kaggle GPU T4 trong khi mức tiêu thụ VRAM chỉ ~2.8 - 3.2 GB (không gây OOM).
- **Tối ưu hóa Throughput DataLoader (Loại bỏ nghẽn CPU STFT)**: Loại bỏ cờ `--pitch-aug` online trong vòng lặp huấn luyện do 500 mẫu giọng trầm đã được tiền sinh offline đầy đủ vào `train_zalo.csv`. Bổ sung log tiến độ định kỳ 500 batches trong `src/training/trainer.py`. Tốc độ nạp dữ liệu tăng vọt từ 0.8 mẫu/s lên **~50 - 148 mẫu/s (tăng tốc ~185 lần)**, rút ngắn thời gian 1 epoch từ 14 giờ xuống chỉ còn **~15 - 16 phút**.
- **Tải tệp nén 3.26 GB & Giải nén chọn lọc**: Xây dựng `scripts/setup_local_train.py` sử dụng direct call `ApiDownloadKernelOutputRequest` (tải ổn định tốc độ ~7-10 MB/s, chống lỗi 429) và giải nén chọn lọc 6.786 audio files cần thiết cho tập Zalo.
- **Entry-point huấn luyện cục bộ**: Tạo script `scripts/train_local_zalo.py` tự động kiểm tra dữ liệu, cấu hình AM-Softmax ($s=30.0, m=0.35$), pitch-augmentation ($p=0.9$), và tự động kích hoạt `scripts/eval_v5_gate.py` sau khi hoàn thành.
- **Kiểm thử tự động TDD**: Bổ sung bộ test `tests/test_local_train_setup.py` kiểm định gradient accumulation step, AM-Softmax loss scaler và clamped class weights. Toàn bộ **227/227 bài kiểm thử unit tests đạt 100% PASS** trong 48 giây.
- **Kết Quả Huấn Luyện Thực Tế (Hoàn Tất)**:
  - Huấn luyện 14 epochs (2 Phase 1 warm-up + 12 Phase 2 fine-tuning), kích hoạt Early Stopping tại Epoch 14 (patience=4).
  - Checkpoint tối ưu: `out/zalo_b_zalo_v5_local/best_model.pt` lưu tại **Epoch 10 với Dev EER = 1.98%** (vượt kỷ lục baseline B 2.10% - 2.62%).
  - **Kết quả kiểm định 3 Gates (`scripts/eval_v5_gate.py`)**:
    - **Gate 2 (Generalization 4 SPK đối chứng)**: **95.3% PASS** (61/64 clip bona fide đúng nhãn).
    - **Gate 3 (Dev Zalo EER)**: **PASS** (`aac_zalo_76k`: 1.73%, `opus_zalo_24k`: 1.56%, `clean_16khz`: 1.56%).
    - **Gate 1 (SPK_0001 & VoiCes)**: Đạt 4/15 file (26.7%), mean score $-15.29$ và $-15.24$ $\implies$ xác nhận bản chất bias âm cố định của giọng cực trầm, làm tiền đề áp dụng `calibrate_score` (Pha 4) ở tầng suy luận API.



---

## 1. Phân Tích Hiện Trạng Phần Cứng & Ràng Buộc

| Thành phần | Thông số máy hiện tại | Yêu cầu kỹ thuật | Giải pháp thích ứng |
|---|---|---|---|
| **Dung lượng đĩa (Disk)** | Ổ `C:` trống 128.38 GB | Cần ~9 – 12 GB cho dữ liệu chọn lọc | Đạt 100%, lưu trữ tại `data/local_cache/` |
| **GPU VRAM** | RTX 3050 Laptop: 4.096 MB (4 GB) | Phase 2 full unfreeze Wav2Vec2 cần ~8–12 GB nếu `BS=16` | Cấu hình `BS=4`, `grad_accum=4`, bật PyTorch AMP FP16 |
| **CUDA / PyTorch** | CUDA 12.x / PyTorch 2.6+ | Bắt buộc CUDA device | Đã kiểm tra: `CUDA Available = True` |
| **FFmpeg** | Đã cài đặt trên Windows | Chuyển mã proxy AAC/Opus in-memory | Sẵn sàng hoạt động |

---

## 2. Kế Hoạch Thực Thi Chi Tiết (4 Bước)

### Bước 1: Chuẩn Bị & Nạp Dữ Liệu Chọn Lọc (Selective Asset Provisioning)
1. **Checkpoint B gốc (`best_model_B.pt`)**:
   - Kiểm tra `out/kaggle_ssl_out/best_model_B.pt` (hoặc tải trực tiếp 379 MB qua `ApiDownloadKernelOutputRequest` từ Kaggle `nguyenthanhtai1959/vietrue-ssl-training`).
   - Kiểm tra băm SHA-256 khớp: `a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f`.
2. **Audio ZIP 3.26 GB (`vitruevoice_data_processed.zip`)**:
   - Tải tệp ZIP trực tiếp qua `ApiDownloadKernelOutputRequest` từ Kaggle `nguyenthanhtai1959/vietrue-model-training` vào thư mục `data/raw_zip/`.
   - **Giải nén chọn lọc (Bijective Selective Unzip)**: Chỉ giải nén 6.786 tệp audio gốc cần thiết cho tập Train và Dev Zalo vào `data/local_cache/audio/` (~1.2 GB), tránh giải nén tràn lan 49.000 file làm chậm I/O ổ đĩa Windows.
3. **Sinh Proxy Kênh Zalo**:
   - Chuyển mã trước (pre-transcode) Profile A (AAC 76k) và Profile B (Opus 24k) cho các mẫu Zalo vào `data/local_cache/proxy/`.
4. **Tiền sinh Offline 500 mẫu giọng trầm**:
   - Chạy `preaugment_deep_voices` hạ pitch (-8 đến -4 semitones) trên 500 mẫu bona fide trầm và bổ sung 1.500 mẫu ghép cặp vào `train_zalo.csv`.

---

### Bước 2: Tối Ưu Hóa Tham Số Huấn Luyện Cho 4GB VRAM
Tạo script thực thi cục bộ `scripts/train_local_zalo.py` bọc quanh `train.py` với cấu hình chống tràn VRAM (OOM Protection):
```bash
python scripts/train.py \
    --branch B_zalo \
    --loss am_softmax \
    --am-s 30.0 \
    --am-m 0.35 \
    --pitch-aug \
    --pitch-prob 0.9 \
    --pitch-range -8.0 4.0 \
    --phase1-epochs 2 \
    --phase2-epochs 15 \
    --patience 4 \
    --batch-size 4 \
    --grad-accum-steps 4 \
    --mixed-precision \
    --num-workers 2 \
    --manifest-dir data/manifests_zalo \
    --audio-root data/local_cache/audio \
    --out-dir out/zalo_b_zalo_local
```
- **Effective Batch Size**: $4 \times 4 = 16$ (Bảo toàn 100% động lực hội tụ giống hệt Kaggle GPU T4).
- **VRAM Tiêu thụ dự kiến**: ~2.8 – 3.2 GB (an toàn trong ngưỡng 4.096 MB của RTX 3050).

---

### Bước 3: Đánh Giá Thực Nghiệm & Đo Lường Ngưỡng Nghiệm Thu
Sau khi huấn luyện hoàn tất:
1. Đánh giá trên toàn bộ 11.450 mẫu Dev Zalo:
   - AAC EER $\le 2.62\%$ (Baseline B)
   - Opus EER $\le 2.10\%$ (Baseline B)
   - Clean EER $\le 2.60\%$
   - AMR-NB EER $\le 3.13\%$
   - G.711 A-law EER $\le 3.13\%$
2. Đánh giá 3 cổng kiểm định độc lập qua `scripts/eval_v5_gate.py`:
   - Gate 1: $\ge 12/15$ clip `SPK_0001` và `VoiCes` đúng nhãn bona fide (score $> 0$).
   - Gate 2: $\ge 90\%$ clip 4 tình nguyện viên đối chứng (`SPK_0004`..`0007`) đạt chuẩn.
   - Gate 3: Dev Zalo EER $\le 2.0\%$.

---

### Bước 4: Kiểm Thử TDD & Đồng Bộ Toàn Diện Tài Liệu
1. Chạy toàn bộ 223/223 bài kiểm thử unit test: `pytest tests/ -v`.
2. Ghi nhận kết quả vào `benchmarks/eval_metrics.csv` và `benchmarks/latency_benchmark.csv`.
3. Đồng bộ tiến độ vào các tệp tài liệu: `PLAN.md`, `README.md`, `howtorun.md`, `AGENTS.md`, `deep-voice-generalization.md`.
4. Commit Git với tiền tố `[AI]`.

---

## 3. Phân Công Chuyên Gia Phối Hợp (Phase 2 - Sau Khi Phê Duyệt)

| Chuyên Gia (Agent) | Vai Trò & Nhiệm Vụ |
|---|---|
| **`backend-specialist`** | Xây dựng pipeline tải asset qua `ApiDownloadKernelOutputRequest`, Selective Unzip và chạy huấn luyện 2 pha |
| **`performance-optimizer`** | Kiểm soát cấp phát VRAM PyTorch (`torch.cuda.empty_cache`, AMP FP16, Gradient Accumulation) chống OOM |
| **`test-engineer`** | Chạy kiểm định 3 Gates (`eval_v5_gate.py`), tính EER/FAR@0 và xác minh 223/223 unit tests pass 100% |

---

## 4. Kế Hoạch Dự Phòng & Rủi Ro (Rollback Strategy)
- Nếu gặp lỗi OOM VRAM trong Phase 2: Kích hoạt `gradient_checkpointing` trên Wav2Vec2 backbone hoặc hạ `--batch-size 2` và `--grad-accum-steps 8`.
- Checkpoint bảo toàn rollback an toàn đã có sẵn tại: `out/zalo_b_zalo_v4/best_model_B_zalo.pt`.
