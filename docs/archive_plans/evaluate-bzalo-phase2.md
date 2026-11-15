# Kế hoạch Đánh giá Checkpoint B_zalo Phase 2 (Version 3)
`evaluate-bzalo-phase2.md`

## 1. Overview
Kernel Kaggle `nguyenthanhtai1959/vietrue-zalo-fine-tuning` (Version 3: Joint Fine-Tuning B_zalo Phase 2 — `phase1_epochs=0`, `phase2_epochs=10`, `lr_ssl=1e-6`, `lr_backend=1e-5`, `patience=3`) đã hoàn thành thành công (`KernelWorkerStatus.COMPLETE`).

Mục tiêu của kế hoạch này là:
1. Tải toàn bộ artifacts, checkpoint và training log từ Kaggle về thư mục riêng biệt `out/zalo_b_zalo_v3/`.
2. Đánh giá trực tiếp trên 15 tệp giọng thật của tình nguyện viên `SPK_0001` (`data/eval_zalo/SPK_0001_*.wav.m4a`) để kiểm chứng xem việc mở khóa backbone trong Phase 2 có triệt tiêu hiện tượng False Positive (bị nhận diện nhầm là SPOOF 80% ở Version 2) hay không.
3. Đánh giá toàn diện trên tập `dev_zalo.csv` (11.450 mẫu) nhằm đo lường EER, minDCF, FAR@θ=0, FRR@θ=0 trên cả 5 codec (AAC, Opus, Clean, G.711, AMR) và xác nhận tính chống thoái lui (anti-regression) so với Baseline Checkpoint B.
4. Đưa ra quyết định nghiệm thu và cập nhật checkpoint suy luận cho API & Telegram Bot.

---

## 2. Project Type
**BACKEND / ML EVALUATION & VERIFICATION**

---

## 3. Success Criteria
1. **Tải và kiểm định Checkpoint**: Tải đầy đủ `best_model_B_zalo.pt` và log vào `out/zalo_b_zalo_v3/`, xác nhận nạp trọng số PyTorch thành công và kiểm tra số epoch thực tế chạy trong Phase 2.
2. **Khắc phục False Positive SPK_0001**:
   - Tỷ lệ nhận diện đúng BONA_FIDE tại ngưỡng cố định $\theta = 0$ đạt $\ge 80\%$ (ít nhất 12/15 tệp có score $> 0$).
   - Điểm số trung bình (mean score) chuyển từ âm (-4.31) sang dương rõ rệt.
3. **Tiêu chí Chống thoái lui trên Dev Zalo (`dev_zalo.csv`)**:
   - AAC EER $\le 3.50\%$ (Baseline Checkpoint B: 2.62%).
   - Opus EER $\le 3.00\%$ (Baseline Checkpoint B: 2.10%).
   - Clean EER $\le 3.00\%$ (Baseline Checkpoint B: 2.60%).
   - FAR tại $\theta = 0$ trên AAC không vượt quá $10.0\%$ (Version 2 trước đó bị $10.42\%$).
4. **Bảo toàn Hệ thống**: 202/202 unit tests tiếp tục pass 100%.

---

## 4. Tech Stack & Tools
- Python 3.12, PyTorch 2.6 (CUDA/CPU), torchaudio, librosa, soundfile
- Kaggle CLI (`manage_kaggle.py output deploy_zalo_train`)
- Scripts: `scripts/eval_zalo_baseline.py`, `scripts/evaluate_audio.py`
- Test suite: `pytest`

---

## 5. File Structure
```
out/zalo_b_zalo_v3/
├── best_model_B_zalo.pt          # Checkpoint đã huấn luyện Phase 2
├── training_log.txt              # Log quá trình huấn luyện Kaggle
├── spk0001_eval_v3.csv           # Kết quả đo chi tiết 15 file SPK_0001
└── zalo_b_zalo_v3_metrics.csv    # Bảng chỉ số trên 11.450 file Dev Zalo
```

---

## 6. Task Breakdown

### Task 1: Tải Artifacts & Kiểm định Cấu trúc Checkpoint
- **Agent**: `backend-specialist`
- **Skill**: `@verify-changes`
- **Priority**: P0 (Blocker)
- **Dependencies**: Không
- **INPUT**: Kernel Kaggle `nguyenthanhtai1959/vietrue-zalo-fine-tuning`
- **OUTPUT**: Thư mục `out/zalo_b_zalo_v3/` chứa `best_model_B_zalo.pt` và log.
- **VERIFY**: Nạp thử state_dict bằng PyTorch, in ra số tham số, xác nhận phase 2 và epoch huấn luyện.

### Task 2: Đánh giá Nghiệm thu SPK_0001 (15 mẫu thực tế Zalo AAC)
- **Agent**: `test-engineer`
- **Skill**: `@tdd-workflow`
- **Priority**: P1
- **Dependencies**: Task 1
- **INPUT**: 15 tệp `data/eval_zalo/SPK_0001_*.wav.m4a` và checkpoint `out/zalo_b_zalo_v3/best_model_B_zalo.pt`.
- **OUTPUT**: Tệp `out/zalo_b_zalo_v3/spk0001_eval_v3.csv` ghi nhận score từng tệp, min, max, mean score và phán quyết tại $\theta = 0$.
- **VERIFY**: So sánh trực tiếp với bảng điểm Version 2 (trước đó 12/15 bị SPOOF). Đạt nghiệm thu nếu $\ge 12/15$ là BONA_FIDE.

### Task 3: Đánh giá Toàn diện Tập Dev Zalo (11.450 mẫu Paired Profiles)
- **Agent**: `test-engineer`
- **Skill**: `@verify-changes`
- **Priority**: P1
- **Dependencies**: Task 1
- **INPUT**: `data/manifests_zalo/dev_zalo.csv` và checkpoint `out/zalo_b_zalo_v3/best_model_B_zalo.pt`.
- **OUTPUT**: `out/zalo_b_zalo_v3/zalo_b_zalo_v3_metrics.csv` với đầy đủ EER, minDCF, FAR@0, FRR@0 cho AAC, Opus, Clean, G.711, AMR.
- **VERIFY**: Kiểm tra tiêu chí chống thoái lui so với Baseline Checkpoint B.

### Task 4: Tổng hợp, Đồng bộ Bộ nhớ & Đề xuất Thăng cấp Checkpoint
- **Agent**: `backend-specialist`
- **Skill**: `@clean-code`
- **Priority**: P2
- **Dependencies**: Task 2, Task 3
- **INPUT**: Báo cáo từ Task 2 và Task 3.
- **OUTPUT**: Báo cáo tổng hợp, cập nhật `.agents/memory/` và đề xuất cập nhật default checkpoint trong API/Telegram Bot nếu đạt chuẩn.
- **VERIFY**: Chạy `pytest tests/ -v` xác nhận 202/202 tests pass 100%.

---

## 7. Phase X: Verification Checklist
- [x] Checkpoint Version 3 tải về đầy đủ, nạp PyTorch hợp lệ (Epoch 7, Phase 2, `out/zalo_b_zalo_v3/best_model_B_zalo.pt`).
- [x] 15 file SPK_0001 được chấm điểm và xuất CSV (`out/zalo_b_zalo_v3/spk0001_eval_v3.csv`).
- [x] Dev Zalo (11.450 file) được đo đầy đủ chỉ số EER/FAR/FRR trên 5 codec (`out/zalo_b_zalo_v3/zalo_b_zalo_v3_metrics.csv`).
- [x] Bảng so sánh Version 2 vs Version 3 vs Baseline được lập rõ ràng (AAC EER đạt 1.56%, FAR@0 giảm xuống 1.56%).
- [x] Toàn bộ 202 unit tests giữ vững trạng thái xanh (100% pass).
