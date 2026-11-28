# VieTrueVoice — Hướng Dẫn Chạy, Huấn Luyện & Triển Khai

Dự án hỗ trợ huấn luyện trực tiếp trên GPU cục bộ (`scripts/run_v8_1_phase_train.py`, `scripts/train.py`), kiểm thử CI (`pytest`) và triển khai qua FastAPI / Brutalist WebGL Forensics Web UI (`/`) / Docker. Các trình sinh notebook Colab/Kaggle nằm trong `scripts/build_*_notebook.py` (tạo tự động khi cần).

---

## 1. Sinh notebook Colab / Kaggle (tùy chọn)
```bash
python scripts/build_zalo_train_notebook.py
python scripts/build_zalo_eval_notebook.py
python scripts/build_dev_eval_notebook.py
```

---

## 3.2. Huấn Luyện Cục Bộ Trên Máy Local (GPU RTX 3050 4GB)

Dành cho việc huấn luyện trực tiếp trên GPU máy tính cá nhân mà không phụ thuộc cloud/timeout:

### Bước 1: Chuẩn bị & Tải dữ liệu chọn lọc (1 lần duy nhất)
Tự động tải Checkpoint B và tệp nén 3.26 GB từ Kaggle, sau đó giải nén chọn lọc 6.786 audio files phục vụ tập Zalo:
```bash
python scripts/setup_local_train.py
```

### Bước 2: Khởi động huấn luyện chống tràn VRAM
Script tự động kích hoạt Gradient Accumulation (`--batch-size 4 --accum-steps 4`, effective batch size 16) kết hợp PyTorch AMP FP16, kiểm soát VRAM trong khoảng 2.8 - 3.2 GB:
```bash
python scripts/train_local_zalo.py
```
*Sau khi huấn luyện xong, script tự động gọi `scripts/eval_v5_gate.py` để kiểm định độc lập 3 Gates.*

---

## 4. Các Lệnh Thực Thi & Kiểm Thử Thường Dùng

### Chạy Kiểm Thử Tự Động (TDD Unit Tests)
```bash
pytest tests/ -v
```
*(Yêu cầu: Toàn bộ bộ kiểm thử TDD pass 100% trước khi commit hoặc đẩy lên Kaggle/Colab/CI)*

### Kiểm Toán An Ninh Manifest V6
```bash
python scripts/audit_v6_manifest.py
```
*(Xác minh 5 tiêu chí: Zero-leakage 5 SPK nghiệm thu, cô lập SPK_0001 ở Train, Hard Text-Disjoint, cách ly VieNeu-TTS, và tính toàn vẹn 125 file)*

### Khởi Động Huấn Luyện B_zalo V6 Local (GPU RTX 3050 4GB)
```bash
python scripts/train_local_zalo_v6.py
```

### Huấn Luyện Mô Hình B_zalo V8 Đối Chứng 2 Chiều (Seen: F5 + OmniVoice | Unseen: VieNeu-TTS)
Huấn luyện mô hình V8 hoán đổi cấu trúc Seen/Unseen để triệt tiêu hiện tượng lọt lưới 20% của Continuous Flow Matching (CFM) và kiểm định Giả thuyết H2 trên VieNeu-TTS:
```bash
# Bước 1: Tổng hợp mẫu OmniVoice train & xuất 4 tệp manifest V8 chuẩn 18/19 cột
python scripts/generate_omnivoice_train_manifests.py --max-spks 55 --prompts-per-spk 2

# Bước 2: Huấn luyện V8 Pha 1 & Pha 2 và tự động đánh giá 4 Cổng kiểm định
python scripts/train_v8_inverted_dual.py --device cuda --batch-size 8 --accum-steps 2

# (Tùy chọn) Tiếp tục chạy Pha 2 của Run 2 từ checkpoint bảo lưu
python scripts/train_v8_inverted_dual.py --resume-run2 --phase2-epochs 3

# (Tùy chọn) Chạy đánh giá độc lập 4 Cổng trên checkpoint bất kỳ
python -c "from scripts.train_v8_inverted_dual import evaluate_all_gates; evaluate_all_gates('out/zalo_b_zalo_v8_inverted/best_model.pt', 'data/manifests_zalo/dev_v8_f5_omni.csv')"
```

### Tối Ưu Lai Ghép Tầng (Layer-Wise Grafting), Huấn Luyện Đối Xứng 6.445 Mẫu & Hiệu Chuẩn `v0.9.4`
Thực thi quy trình khôi phục dữ liệu OmniVoice_CFM đối xứng 1:1 (6.445 files), huấn luyện 2-Run (`am_m=0.20`), hiệu chuẩn đầu phân loại (`head_blend_a0.75`) và sinh báo cáo benchmark 4.979 / 15.980 / 955:
```bash
# Bước 1: Khôi phục 6.445 mẫu OmniVoice_CFM đối xứng 1:1 & xuất 5 manifests chuẩn
python scripts/generate_omnivoice_v8_full.py

# Bước 2: Huấn luyện 2-Run tách riêng checkpoint Pha 1 & Pha 2
python scripts/run_v8_1_phase_train.py --init-ckpt out/zalo_b_zalo_v5_local/best_model.pt --train-manifest data/manifests_zalo/train_v8_f5_omni_no_spk1.csv --dev-manifest data/manifests_zalo/dev_v8_f5_omni.csv --out-dir out/zalo_b_zalo_v8_1_no_spk1 --phase1-epochs 1 --phase2-epochs 2 --am-m 0.20
python scripts/run_v8_1_phase_train.py --init-ckpt out/zalo_b_zalo_v5_local/best_model.pt --train-manifest data/manifests_zalo/train_v8_f5_omni_with_spk1.csv --dev-manifest data/manifests_zalo/dev_v8_f5_omni.csv --out-dir out/zalo_b_zalo_v8_1_with_spk1 --phase1-epochs 1 --phase2-epochs 2 --am-m 0.20

# Bước 3: Tạo tập cân bằng 5.100 dòng & chạy đánh giá đối chứng V7 vs V8.0 vs v0.9.4 (4.979/15.980/955)
python scripts/build_v8_hybrid_checkpoint.py
python scripts/eval_v8_1_benchmark.py
python scripts/build_v8_1_reports.py
```
*(Checkpoint chiến thắng `v0.9.4` (`head_blend_a0.75`) được lưu tại `out/v0.9.4/best_model.pt`)*

### Huấn Luyện CLI (3 Nhánh Thí Nghiệm)
```bash
# Nhánh A (Clean only baseline)
python scripts/train.py --branch A --manifest-dir data/manifests --audio-root . --out-dir out/run_A

# Nhánh B0 (Chỉ nén Codec, không RawBoost)
python scripts/train.py --branch B0 --manifest-dir data/manifests --audio-root . --out-dir out/run_B0

# Nhánh B (VieTrueVoice: Codec + RawBoost Online)
python scripts/train.py --branch B --manifest-dir data/manifests --audio-root . --out-dir out/run_B
```

### Chấm Điểm & Đánh Giá Mô Hình (EER + minDCF + Bootstrap CI)
```bash
# Đánh giá Baseline GMM
python scripts/eval_gmm.py --manifest data/manifests/test_indomain.csv --audio-root . --role eval --out out/eval_metrics_gmm.csv

# Đánh giá SSL-AASIST
python scripts/eval_ssl_aasist.py --ckpt out/run_B/best_model.pt --manifest in_domain=data/manifests/test_indomain.csv ood=data/manifests/test_ood.csv --audio-root . --role eval --out out/eval_metrics_B.csv
```

### Kiểm Chứng Giả Thuyết H1 & H2 Tự Động
```bash
# Đối chứng H1 (giảm >= 30% EER kênh nén) và H2 (EER Unseen TTS <= 15%)
python scripts/compare_h1.py --a out/eval_metrics_A.csv --b out/eval_metrics_B.csv --out-dir out/comparison_A_B

# Phân rã đóng góp RawBoost (B0 vs B)
python scripts/compare_h1.py --a out/eval_metrics_B0.csv --b out/eval_metrics_B.csv --out-dir out/comparison_B0_B
```

### Chạy Batch Dataset Processor (Dual Pipeline F5-TTS + VieNeu-TTS v3 Turbo)
```bash
python -c "
from src.VieTrueVoice.pipeline import VieTrueVoiceDualPipeline, PipelineMode
from src.VieTrueVoice.batch_processor import BatchDatasetProcessor

pipeline = VieTrueVoiceDualPipeline()
processor = BatchDatasetProcessor(pipeline=pipeline, mode=PipelineMode.DUAL_OUTPUT, only_pass=True, min_dur=3.5, max_dur=7.5, allow_stitching=False)
processor.run_batch(speakers=['SPK_0001', 'SPK_0004', 'SPK_0005', 'SPK_0006', 'SPK_0007'], seeds=[100, 200, 300], codecs=['clean_16khz', 'g711_alaw', 'amr_nb'])
"
```

### Chạy Máy Chủ API & Brutalist WebGL Forensics Web UI (FastAPI cổng 8000)
```bash
# Checkpoint mặc định tự động nạp: out/v0.9.4/best_model.pt
uvicorn src.app.server:app --reload --port 8000
# Giao diện Web UI: http://localhost:8000/ | Swagger API: http://localhost:8000/docs
```

### Chạy Telegram Bot Phát Hiện Giọng Giả (Multi-window Max-Pooling V6)
```bash
# 1. Chạy với token trực tiếp từ @BotFather:
python scripts/run_bot.py --token <TELEGRAM_BOT_TOKEN>

# 2. Hoặc cấu hình file .env (TELEGRAM_BOT_TOKEN=...) và chạy:
python scripts/run_bot.py

# 3. Chạy với GPU và checkpoint tùy chọn:
python scripts/run_bot.py --device cuda --checkpoint out/zalo_b_zalo_v6_local/best_model.pt
```

### Chạy Đánh Giá 3 Cổng Kiểm Định (Gates 1, 2, 3) Cho Checkpoint V6
```bash
# Đánh giá mặc định bật multi-window max-pooling (--pooling)
python scripts/eval_v5_gate.py --ckpt out/zalo_b_zalo_v6_local/best_model.pt

# Hoặc tắt pooling để so sánh với cách cắt 4s đầu truyền thống:
python scripts/eval_v5_gate.py --ckpt out/zalo_b_zalo_v6_local/best_model.pt --no-pooling
```

### Chạy Đo Lường Độ Trễ (30 lần lặp)
```bash
# Đo lường độ trễ chuẩn hóa theo NFR1 (mặc định bật --pooling)
python scripts/benchmark_latency.py

# Đo lường không dùng pooling:
python scripts/benchmark_latency.py --no-pooling
```

---

## 5. Hướng Dẫn Demo Dự Án (Trực Quan & Đầy Đủ Các Kênh)

Hệ thống cung cấp 4 phương thức demo linh hoạt:

### Cách 1: Giao diện Web Trực Quan (Brutalist Editorial & WebGL Forensics Web UI tại `/`)
Giao diện Dark Obsidian Forensics phục vụ trực tiếp trên FastAPI tại cổng `8000` (thay thế hoàn toàn Gradio `src/app/ui.py` và `/playground` cũ — `/playground` hiện trả về `404`), tích hợp WebGL 3D Liquid Obsidian Orb (có nút bật/tắt 3D), 3 thẻ bối cảnh với ảnh phổ thực tế và 2 chế độ thẩm định thời gian thực:
```bash
python scripts/demo_predict.py --web
# hoặc: uvicorn src.app.server:app --port 8000
```
- Mở trình duyệt tại: `http://localhost:8000/` (cả chạy trực tiếp lẫn Docker đều dùng chung cổng `8000`).

#### 🛡️ Tab 01 (`01 // THẨM ĐỊNH GIỌNG NÓI` — `POST /api/v1/predict`)
- **Tải lên hoặc Ghi âm trực tiếp**: Hỗ trợ kéo-thả/chọn tệp (`.wav, .mp3, .m4a, .ogg, .opus, .flac, .webm`), thu âm trực tiếp qua Microphone trình duyệt (tắt `echoCancellation`/`noiseSuppression`/`autoGainControl`, mã hóa 16kHz PCM WAV ngay trên trình duyệt) và 5 mẫu đối chứng thực tế nạp qua `GET /api/v1/samples`.
- **Kết quả trực quan**: Nhãn kết luận `BONA_FIDE` (Xanh lục) / `SPOOF` (Đỏ thẫm) / cảnh báo `BORDERLINE` (Hổ phách khi $|s - \theta| \le 8.0$), xác suất hiệu chuẩn Platt Scaling (`prob_bona_pct%` / `prob_spoof_pct%`), Raw Logit `s`, độ trễ suy luận, mã băm `SHA-256` (Zero-Persistence), `Bandwidth Profile`, `F0`, `HF Ratio > 4kHz`.
- **4 Biểu đồ Canvas HD trích xuất thực từ `response.forensics` (`src/app/forensics.py`)**:
  1. *Mel-Spectrogram Heatmap (48 Mels, 0–8 kHz)* kèm đường ranh giới `3.4 kHz AMR-NB` và `4.0 kHz Vocoder`.
  2. *Waveform Oscilloscope* đồng bộ theo nhãn kết luận.
  3. *Multi-Window Consensus Asymmetric Veto Chart* (`W1..W5` kèm đường ngưỡng $\theta=0.0$, `+6.0` rescue, `-12.0` veto và diễn giải nhánh pooling).
  4. *Platt Calibration Curve (`T=16.0`)* & biểu đồ năng lượng 3 dải tần (`<300Hz`, `300–3400Hz`, `3400–8000Hz`).

#### 🧪 Tab 02 (`02 // CLONE & KIỂM CHỨNG OMNIVOICE CFM` — `POST /api/v1/clone-and-audit`)
- **Đầu vào linh hoạt**: Tải tệp, thu âm trực tiếp qua Microphone trình duyệt, hoặc 1-click mẫu chuẩn `SPK_0004`, kèm hộp nhập văn bản mục tiêu tiếng Việt (`target_text`) và tùy chọn `custom_ref_text` (tự động nhận diện ASR Wav2Vec2 nếu để trống).
- **Ma trận đối soát 2 chiều**: Hiển thị banner chênh lệch **`Δ MARGIN GAP` (`delta_margin`)**, văn bản ASR đã dùng, trạng thái `LIVE OMNIVOICE CFM` / `CFM PRESET FALLBACK`, 2 thẻ so sánh trực tiếp **Bản Gốc (Bona Fide)** vs **Bản Nhân Bản (OmniVoice CFM Clone)** kèm trình phát âm thanh, nút tải `.wav` clone và biểu đồ phổ/sóng âm/cửa sổ thời gian thực từ `bonafide.forensics` và `clone.forensics`.
- **Tuân thủ Quyền riêng tư (Luật 91/2025/QH15)**: Âm thanh xử lý in-memory trên RAM, dọn dẹp file tạm ngay lập tức sau khi suy luận và chỉ lưu log mã băm SHA-256.

### Cách 2: Thử Nghiệm Nhanh Trên Dòng Lệnh (CLI Demo)
Thực hiện phân loại tức thời trên terminal:
```bash
# Tự động chạy demo trên 3 mẫu đối chứng (Thật, F5-TTS, VieNeu-TTS):
python scripts/demo_predict.py

# Hoặc phân loại 1 file âm thanh bất kỳ:
python scripts/demo_predict.py data/raw/SPK_0003/SPK_0003_01.wav
```

### Cách 3: Dịch Vụ API Chuẩn Doanh Nghiệp (FastAPI Swagger)
```bash
python scripts/demo_predict.py --server --port 8000
# hoặc: uvicorn src.app.server:app --reload --port 8000
```
- Truy cập tài liệu tương tác: `http://localhost:8000/docs`
- Thử nghiệm endpoint `POST /api/v1/predict` với file audio tải lên, kiểm tra phản hồi JSON và log mã băm SHA-256 ẩn danh.

### Cách 4: Chạy Đánh Giá Hàng Loạt 234 Mẫu Thật/Giả (Quay Video Demo W04)
```bash
python scripts/eval_5spk_full_benchmark.py
```
In bảng tổng kết toàn diện trên 5 người nói đối chứng (SPK_0003..0007), hiển thị rõ EER 11.33% và AUC 0.9343.

---

## 6. Hướng Dẫn Đóng Gói Docker & Triển Khai Trên AWS

Hệ thống VieTrueVoice được đóng gói container hóa theo chuẩn bảo mật điện toán đám mây (AWS Security / CIS Docker Benchmark):

### 6.1 Khởi chạy bằng Docker
1. **Xây dựng Docker Image**:
   ```bash
   docker build -t VieTrueVoice:latest .
   ```
2. **Khởi chạy container độc lập (FastAPI Server + Brutalist WebGL Forensics Web UI)**:
   ```bash
   docker run -d \
     --name VieTrueVoice-api \
     -p 8000:8000 \
     -v ${PWD}/out:/app/out:ro \
     -v ${PWD}/data/bonafide_ref:/app/data/bonafide_ref:ro \
     -v ${PWD}/external:/app/external:ro \
     VieTrueVoice:latest
   ```
3. **Truy cập các giao diện trực tiếp tại cổng 8000**:
   - **Brutalist WebGL Forensics Web UI**: Mở trình duyệt tại `http://localhost:8000/` (Tích hợp Tab 01 Thẩm định giọng nói `/api/v1/predict` & Tab 02 Nhân bản và Kiểm chứng OmniVoice CFM `/api/v1/clone-and-audit`).
   - **Swagger API Docs**: `http://localhost:8000/docs`
   - **Kiểm tra trạng thái sức khỏe container**:
     ```bash
     curl http://localhost:8000/health
     ```

### 6.2 Khởi chạy toàn bộ hệ thống bằng Docker Compose (Web UI + REST API + Telegram Bot)
Điều phối tự động toàn bộ dịch vụ trong 1 lệnh duy nhất:
```bash
# Thiết lập token bot (nếu có):
export TELEGRAM_BOT_TOKEN="token_cua_ban"

# Khởi chạy ngầm toàn bộ dịch vụ:
docker compose up -d

# Xem log hoạt động:
docker compose logs -f
```
Sau khi khởi chạy:
- Truy cập Web UI tại: `http://localhost:8000/`
- Truy cập REST API Swagger tại: `http://localhost:8000/docs`
- Telegram Bot hoạt động song song tại nền tảng Telegram nhận diện tin nhắn thoại.

### 6.3 Triển khai tự động trên máy chủ AWS EC2 (G4dn.xlarge GPU hoặc T3.large CPU)
1. Cấu hình quyền tối thiểu IAM Role theo mẫu: `deploy/aws/iam_policy.json`.
2. Áp dụng quy tắc tự động hủy dữ liệu sinh trắc học S3 Lifecycle: `deploy/aws/s3_lifecycle_policy.json`.
3. Chạy script triển khai tự động 1 lệnh duy nhất trên EC2:
   ```bash
   bash scripts/aws_deploy_ec2.sh
   ```
4. Tham khảo bảng ước tính chi phí vận hành cho 100 / 1.000 / 10.000 users tại: `deploy/aws/pricing_calculator_w08.md`.

---

## 7. Hướng Dẫn Tích Hợp & Mô Phỏng Nền Tảng Zalo Official Account (OA)

Hệ thống VieTrueVoice tích hợp đầy đủ module tiếp nhận tin nhắn thoại Zalo Webhook chuẩn OpenAPI v3.0 của Zalo for Developers:

### 7.1 Kiểm thử nhanh bằng Bộ mô phỏng (Zalo Webhook Simulator)
Khởi chạy kiểm thử mô phỏng gửi voice note Zalo kèm chữ ký số HMAC-SHA256:
```bash
# 1. Kiểm thử với giọng nói thật (Bona fide):
python scripts/simulate_zalo_webhook.py --audio data/bonafide_ref/SPK_0004/SPK_0004_01.wav

# 2. Kiểm thử với giọng giả mạo (F5-TTS Spoof):
python scripts/simulate_zalo_webhook.py --audio data/spoof_f5tts/CV_08110ec9e6/CV_08110ec9e6_prompt_000.wav
```

### 7.2 Cấu hình triển khai Zalo Official Account thật trong sản xuất
1. Mở trang quản trị [Zalo for Developers](https://developers.zalo.me/) và tạo Zalo App liên kết Zalo OA.
2. Thiết lập Webhook URL trỏ về máy chủ VieTrueVoice:
   ```text
   https://<ten-mien-cua-ban>/api/v1/zalo/webhook
   ```
3. Đăng ký sự kiện: `user_send_audio` (người dùng gửi tin nhắn thoại).
4. Điền các khóa bảo mật vào file `.env`:
   ```bash
   ZALO_APP_ID=<APP_ID_CUA_BAN>
   ZALO_APP_SECRET=<APP_SECRET_CUA_BAN>
   ZALO_OA_ACCESS_TOKEN=<OA_ACCESS_TOKEN_CUA_BAN>
   ```
5. Hệ thống sẽ tự động xác thực chữ ký số HMAC-SHA256 từ Zalo và tự động phản hồi kết quả kiểm định tới hộp chat của người dùng qua Zalo OpenAPI v3.0 CS Message.

---

## 8. Hướng Dẫn Xuất Bản Dữ Liệu Nghiệm Thu (Voice_Final) & Huấn Luyện Dual-Seen

### 8.1 Xuất bản toàn bộ dữ liệu ra thư mục nghiệm thu Voice_Final
Thực thi trích xuất và tổ chức toàn bộ kho dữ liệu âm thanh (**103.189 files**, đồng bộ đối xứng 1:1 giữa `spoof/v7/Seen/VieNeu_TTS` và `spoof/v8/Seen/OmniVoice_CFM` đạt đúng 6.445 files) thành 2 thư mục chính (`bonafide/`: 70.174 files gồm `SPK_Volunteers` 524, `VIVOS` 55.225, `CommonVoice` 14.425; và `spoof/` tách `v7/` 13.955 files và `v8/` 19.060 files) kèm bảng chỉ mục SHA-256 (`VOICE_FINAL_MANIFEST.csv`):
```bash
python scripts/export_voice_final_dataset.py
```
Toàn bộ dữ liệu sẽ được lưu tại: `C:\Users\saket\Documents\Đồ án chuyên ngành\Voice_Final\`

### 8.2 Khởi động quy trình Huấn luyện kép Dual-Seen (F5-TTS + VieNeu-TTS)
Thực hiện huấn luyện mô hình Dual-Seen và kiểm định cách ly giọng trầm ngoại lai SPK_0001:
```bash
python scripts/train_dual_seen.py --batch-size 16 --accum-steps 1 --device cuda
```
Quy trình sẽ tự động thực hiện:
- **Lần 1**: Huấn luyện trên tập không có SPK_0001 (54.225 dòng) và đánh giá trên 15 file bona fide của SPK_0001 với Multi-window Max-Pooling.
- **Lần 2**: Nếu Lần 1 chưa nhận diện được SPK_0001 (Pass Rate < 80%), tự động kích hoạt đưa SPK_0001 vào tập train (54.400 dòng) và tái huấn luyện.

### 8.3 Đánh giá nghiệm thu toàn diện 5 tình nguyện viên đối chứng (795 Clips)
Chạy kịch bản đánh giá mô hình B_zalo V7 qua toàn bộ 420 clip bona fide (84 clips x 5 codecs) và 375 clip Unseen Spoof (VoiceStudio OmniVoice CFM Zero-shot) trên 5 tình nguyện viên held-out (`SPK_0003`..`0007`) dưới cơ chế gộp đa cửa sổ chuẩn sản xuất **Multi-window Max-Pooling** (mặc định `--pooling max`):
```bash
python scripts/eval_5spk_unseen_and_bonafide.py --ckpt out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt --pooling max
```
Kết quả chi tiết và báo cáo phân tích lưu tự động tại: `benchmarks/eval_5spk_unseen_and_bonafide.json` và `benchmarks/seen_vs_unseen_degradation_v7.json`.

### 8.4 Kiểm định 2 Nền tảng Thử nghiệm (Dual-Platform Verification)
Hệ thống tự động kích hoạt **Adaptive Comfort Dithering** ($\sigma = 0.0035$) theo chuẩn RFC 3389 / AES-17 để xử lý đồng thời hai nguồn dữ liệu âm thanh:
1. **Nền tảng 1 (File âm thanh viễn thông tải lên)**: Hỗ trợ kéo thả trực tiếp tệp `.wav`, `.m4a`, `.opus`, `.ogg`, `.mp3` qua Web UI hoặc Zalo/Telegram Bot.
2. **Nền tảng 2 (Ghi âm trực tiếp qua Micro trình duyệt)**: Bấm trực tiếp nút ghi âm Micro trên giao diện Web UI (`http://localhost:8000/`). Trình duyệt tắt noise suppression/AEC/AGC và mã hóa 16kHz PCM WAV ngay tại client, kết hợp DSP phía máy chủ bảo toàn tính liên tục âm học và ngăn ngừa triệt để hiện tượng báo nhầm giọng thật thành giả mạo.

### 8.5 Xuất bản Sổ tay Kỹ thuật Chuyên sâu Toàn diện & Cẩm nang Phản biện Hội đồng (Phiên bản 2.0 — Chuẩn `v0.9.4`)
Tự động biên dịch cuốn Sổ tay Kỹ thuật Chuyên sâu Toàn diện V2 (đồng bộ 100% mô hình chính thức `v0.9.4` xuyên suốt 13 chương, tích hợp hộp kiến thức nền tảng trước mỗi quy trình, công thức toán học gốc Word OMML, sơ đồ trực quan 300 DPI, từ điển giải nghĩa thuật ngữ ngay bên dưới mỗi mục và 27 câu hỏi phản biện hội đồng) sang cả hai định dạng `.docx` và `.pdf`:
```bash
python scripts/build_defense_handbook_v2_docx.py
```
Tài liệu được xuất bản và đồng bộ tự động tại:
- `C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VieTrueVoice_V2.docx`
- `C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VieTrueVoice_V2.pdf`
- Và bản sao tại thư mục `C:\Users\saket\Documents\Đồ án chuyên ngành\Content\`.

### 8.6 Khởi chạy Phòng Thí Nghiệm Nhân Bản Trực Tiếp OmniVoice CFM (Web UI Tab 02 tại `/`)
Tính năng nhân bản trực tiếp VoiceStudio (OmniVoice CFM) đã được hợp nhất trực tiếp vào **Brutalist WebGL Forensics Web UI** tại `http://localhost:8000/` (thay thế hoàn toàn Gradio `src/app/ui.py` cổng `7860` và `/playground` cũ):
```bash
python scripts/demo_predict.py --web
# hoặc: uvicorn src.app.server:app --port 8000
```
Truy cập trình duyệt tại `http://localhost:8000/`:
1. Chọn `[ ⚡ CLONE OMNIVOICE ]` hoặc chuyển sang **Tab 02 (`02 // CLONE & KIỂM CHỨNG OMNIVOICE CFM`)**.
2. **Chọn nguồn giọng thật**: Tải file âm thanh, thu âm trực tiếp qua Microphone trình duyệt (3–5 giây), hoặc bấm 1-click nạp mẫu chuẩn `SPK_0004`.
3. Nhập hoặc chọn nhanh câu thoại tiếng Việt mục tiêu (`target_text`) và bấm **`[ ⚡ NHÂN BẢN OMNIVOICE & THẨM ĐỊNH ]`** (`POST /api/v1/clone-and-audit`):
   - Thẩm định đồng thời bản gốc (Bona Fide) và bản clone OmniVoice CFM, xuất **`Δ MARGIN GAP` (`delta_margin`)**, trình phát 2 chiều, nút tải `.wav` clone và bộ biểu đồ Mel-Spectrogram / Waveform / Multi-Window Scores thực từ `bonafide.forensics` & `clone.forensics`.

### 8.7 Xuất bản Bộ Tài liệu Thử nghiệm Pilot & Dự toán Chi phí AWS Runbook (W07 & W08)
Tự động biên dịch Phiếu khảo sát UX Pilot, Biên bản nghiệm thu có chữ ký, Bảng dự toán chi phí đám mây AWS (100 / 1.000 / 10.000 users) và Sổ tay xử lý sự cố (Troubleshooting Runbook) 1 trang sang cả hai định dạng `.docx` và `.pdf`:
```bash
python scripts/build_pilot_and_w08_docs.py
```
Tài liệu được xuất bản và đồng bộ tự động tại:
- `C:\Users\saket\Documents\Đồ án chuyên ngành\Bien_Ban_Nghiem_Thu_Va_Khao_Sat_Pilot_VieTrueVoice.docx` & `.pdf`
- `C:\Users\saket\Documents\Đồ án chuyên ngành\Bang_Chi_Phi_AWS_Va_So_Tay_Su_Co_Runbook.docx` & `.pdf`
- Và bản sao tại thư mục `C:\Users\saket\Documents\Đồ án chuyên ngành\Content\`.

### 8.8 Trải nghiệm Brutalist Editorial & WebGL Forensics Web UI tại `/` (Thay thế Gradio & `/playground`)
Giao diện Web Forensics hợp nhất được phục vụ trực tiếp tại đường dẫn gốc `/` trên cổng `8000` (Gradio và `/playground` đã bị gỡ bỏ hoàn toàn; `/playground` trả về HTTP `404`):
```bash
# Khởi động máy chủ phát triển cục bộ (cổng 8000)
python -m uvicorn src.app.server:app --port 8000

# Hoặc khởi động cụm Docker Compose (cổng 8000)
docker compose up -d --build
```
Truy cập trình duyệt:
- **URL chính thức**: `http://localhost:8000/` (API docs: `http://localhost:8000/docs`, danh sách mẫu thật: `GET /api/v1/samples`).
- **Tab 01 (`01 // THẨM ĐỊNH GIỌNG NÓI`)**: Tải file, thu âm Mic 16kHz PCM trực tiếp hoặc chọn 1 trong 5 mẫu đối chứng thực (`/static/samples/*.wav`); kết nối thật `POST /api/v1/predict` kèm 4 biểu đồ Canvas HD từ `response.forensics` (Mel-Spectrogram 48 Mels kèm vạch 3.4kHz/4.0kHz, Waveform Oscilloscope, Multi-Window Consensus Asymmetric Veto, Platt Calibration Curve `T=16.0` & 3-Band Energy).
- **Tab 02 (`02 // CLONE & KIỂM CHỨNG OMNIVOICE CFM`)**: Ghi âm Micro / tải file / 1-click `SPK_0004`, nhập văn bản mục tiêu và chạy `POST /api/v1/clone-and-audit`, xuất Ma trận đối soát 2 chiều kèm `delta_margin`, bản tải `.wav` và biểu đồ thực từ `bonafide.forensics` & `clone.forensics`.

### 8.9 Đánh Giá Mở Rộng Unseen TTS VoiceStudio CFM Trên 15 Người Nói Held-out (W07)
Quy trình sinh và đánh giá suy giảm (Degradation Analysis) trên 15 người nói held-out độc lập (10.175 bona fide, 1.915 seen TTS, 965 unseen VoiceStudio CFM clips):
```bash
# 1. Tái sinh 965 clips Unseen VoiceStudio CFM với văn bản chuẩn hóa NFC & sentence-case
python scripts/generate_omnivoice_15spk_unseen.py --force-vivos

# 2. Đánh giá suy luận độc lập mô hình B_zalo V7 và tính toán EER, minDCF, Pass Rate (mặc định Asymmetric Veto)
python scripts/eval_15spk_unseen_benchmark.py --force-unseen --pooling-mode asymmetric_veto

# 3. Xuất bản báo cáo tổng hợp W07 (.docx & .pdf)
python scripts/build_w07_report_docx.py
```
Toàn bộ tập audio mẫu nghiệm thu được đồng bộ sang thư mục lưu trữ chính thức:
`C:\Users\saket\Documents\Đồ án chuyên ngành\Voice_Final\01_Corpus_Evaluation\Unseen_VoiceStudio_15Spk\`



