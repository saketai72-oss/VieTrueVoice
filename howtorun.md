# Vietrue Model - Huấn Luyện Trên Kaggle GPU từ Local

Dự án này được thiết lập để bạn có thể viết code và quản lý model tại máy local, nhưng tận dụng GPU miễn phí của Kaggle để huấn luyện và tự động tải kết quả về.

---

## 1. Cấu hình xác thực Kaggle (Làm 1 lần duy nhất)

Chỉ cần chọn **1 trong 2 cách** sau:

### Cách 1 (Khuyên dùng - Nhanh nhất): Đăng nhập trực tiếp bằng OAuth
Chạy lệnh sau trên terminal để đăng nhập qua trình duyệt:
```bash
kaggle auth login
```

### Cách 2: Sử dụng file API token (`kaggle.json`)
1. Truy cập [Kaggle Settings](https://www.kaggle.com/settings).
2. Cuộn xuống phần **API** và chọn **Create New Token** (tải file `kaggle.json` về).
3. Đặt file `kaggle.json` vào thư mục:
   - Windows: `C:\Users\<Tên_User>\.kaggle\kaggle.json`
   - Linux/macOS: `~/.kaggle/kaggle.json`

---

## 2. Cài đặt Username cho dự án

Cập nhật username Kaggle của bạn vào dự án:
```bash
python manage_kaggle.py set-user <username_kaggle_cua_ban>
```

---

## 3. Quy trình sử dụng

### Bước 1: Viết code trong `train.py`
Code của bạn có thể sử dụng PyTorch / TensorFlow / Transformers với GPU bình thường:
* Dữ liệu đọc từ: `/kaggle/input/<ten-dataset>`
* Output, Model weights lưu vào: `/kaggle/working/`

### Bước 2: Thêm Dataset (nếu có)
```bash
python manage_kaggle.py add-dataset <username_so_huu>/<ten_dataset>
```

### Bước 3: Đẩy lên Kaggle để huấn luyện
```bash
python manage_kaggle.py push
```

### Bước 4: Kiểm tra trạng thái
```bash
python manage_kaggle.py status
```
*(Trạng thái sẽ hiển thị: `queued` -> `running` -> `complete`)*

---

## 3.1. Huấn Luyện Fine-Tuning B_zalo Trên Google Colab (GPU T4 Miễn Phí)

Nếu tài khoản Kaggle bị giới hạn GPU hoặc cần huấn luyện tương tác:
1. Mở [Google Colab](https://colab.research.google.com/).
2. Chọn **File -> Upload notebook** và chọn tệp [`deploy_zalo_train/train_zalo.ipynb`](file:///c:/Codes/VieTrueVoice/deploy_zalo_train/train_zalo.ipynb).
3. Đổi Runtime sang GPU: **Runtime -> Change runtime type -> T4 GPU**.
4. Bấm **Runtime -> Run all**:
   - Notebook sẽ tự nhận diện môi trường Google Colab.
   - Tự cài đặt FFmpeg, Kaggle CLI và thư viện phụ thuộc.
   - Tự động tải Checkpoint B, tập Common Voice và tệp dữ liệu âm thanh 3.26 GB từ Kaggle về `/content/input`.
   - Tự clone mã nguồn mới nhất từ GitHub `VieTrueVoice` vào container.
   - Tiến hành tiền sinh offline 500 mẫu giọng trầm và huấn luyện 2 pha với AM-Softmax ($m=0.35$).
   - Đánh giá kiểm định 5 codecs trên 11.450 mẫu Dev Zalo và xuất kết quả.

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
*(Yêu cầu: Toàn bộ 274 unit tests pass 100% trước khi commit hoặc đẩy lên Kaggle/Colab)*

### Kiểm Toán An Ninh Manifest V6
```bash
python scripts/audit_v6_manifest.py
```
*(Xác minh 5 tiêu chí: Zero-leakage 5 SPK nghiệm thu, cô lập SPK_0001 ở Train, Hard Text-Disjoint, cách ly VieNeu-TTS, và tính toàn vẹn 125 file)*

### Khởi Động Huấn Luyện B_zalo V6 Local (GPU RTX 3050 4GB)
```bash
python scripts/train_local_zalo_v6.py
```

### Huấn Luyện CLI (3 Nhánh Thí Nghiệm)
```bash
# Nhánh A (Clean only baseline)
python scripts/train.py --branch A --manifest-dir data/manifests --audio-root . --out-dir out/run_A

# Nhánh B0 (Chỉ nén Codec, không RawBoost)
python scripts/train.py --branch B0 --manifest-dir data/manifests --audio-root . --out-dir out/run_B0

# Nhánh B (ViTrueVoice: Codec + RawBoost Online)
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
from src.vitruevoice.pipeline import ViTrueVoiceDualPipeline, PipelineMode
from src.vitruevoice.batch_processor import BatchDatasetProcessor

pipeline = ViTrueVoiceDualPipeline()
processor = BatchDatasetProcessor(pipeline=pipeline, mode=PipelineMode.DUAL_OUTPUT, only_pass=True, min_dur=3.5, max_dur=7.5, allow_stitching=False)
processor.run_batch(speakers=['SPK_0001', 'SPK_0004', 'SPK_0005', 'SPK_0006', 'SPK_0007'], seeds=[100, 200, 300], codecs=['clean_16khz', 'g711_alaw', 'amr_nb'])
"
```

### Chạy Máy Chủ API Phát Triển (FastAPI với Checkpoint V6 Local)
```bash
# Biến môi trường checkpoint mặc định: out/zalo_b_zalo_v6_local/best_model.pt
uvicorn src.app.server:app --reload --port 8000
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

### Cách 1: Giao diện Web Trực Quan (Gradio Web UI — Khuyên Dùng Cho Người Dùng & Thuyết Trình)
Giao diện Dark Forensics Lab đạt chuẩn thiết kế Stitch v2.4, tối giản $\le 3$ thao tác cho người cao tuổi, tích hợp toàn diện các góc nhìn số liệu khoa học:
```bash
python scripts/demo_predict.py --web
# hoặc: python src/app/ui.py
```
- Mở trình duyệt tại: `http://localhost:7860` (hoặc `http://localhost:8000` khi chạy bằng Docker).
- **Thử nghiệm nhanh**: 3 nút Preset mẫu đối chứng 1-click (Spoof F5-TTS, Giọng thật SPK_0004, Spoof Zalo Opus nén).
- **Kết quả trực quan**: Thẻ cảnh báo nổi bật (Xanh: Giọng thật / Đỏ: Cảnh báo Deepfake kèm khuyến cáo khẩn cấp chống chuyển tiền và bảo vệ mã OTP).
- **Thanh đo độ tin cậy**: Thang đo phần trăm xác suất đã hiệu chuẩn Platt Scaling (0% - 100%).
- **Chỉ số kỹ thuật**: Điểm Raw Score, Thời gian suy luận (latency), Cửa sổ phân tích Multi-window Max-Pooling, Tỷ lệ năng lượng cao tần >4kHz phát hiện vết vocoder.
- **Biểu đồ khoa học trực quan**:
  1. *Mel-Spectrogram (80 Mels, log dBFS)*: Thể hiện dải tần 0 - 8kHz kèm đường ranh giới cắt cao tần 4.0kHz của vocoder HiFi-GAN.
  2. *Biểu đồ sóng âm đồng bộ (Raw Time-Domain Waveform)*: Hiển thị dạng sóng thời gian thực.
  3. *Bản đồ chú ý nơ-ron (Grad-CAM Temporal Saliency)*: Trọng số kích hoạt phát hiện chính xác vùng thời gian phát sinh tín hiệu giả mạo.

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

Hệ thống ViTrueVoice được đóng gói container hóa theo chuẩn bảo mật điện toán đám mây (AWS Security / CIS Docker Benchmark):

### 6.1 Khởi chạy bằng Docker
1. **Xây dựng Docker Image**:
   ```bash
   docker build -t vitruevoice:latest .
   ```
2. **Khởi chạy container độc lập (FastAPI Server + Gradio Web UI)**:
   ```bash
   docker run -d \
     --name vitruevoice-api \
     -p 8000:8000 \
     -v ${PWD}/out:/app/out:ro \
     vitruevoice:latest
   ```
3. **Truy cập các giao diện trực tiếp tại cổng 8000**:
   - **Gradio Web UI**: Mở trình duyệt tại `http://localhost:8000/` (Giao diện web trực quan kiểm tra giọng nói thật/giả kèm Platt Scaling confidence).
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

Hệ thống ViTrueVoice tích hợp đầy đủ module tiếp nhận tin nhắn thoại Zalo Webhook chuẩn OpenAPI v3.0 của Zalo for Developers:

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
2. Thiết lập Webhook URL trỏ về máy chủ ViTrueVoice:
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
Thực thi trích xuất và sao chép toàn bộ kho dữ liệu âm thanh phân tách nghiêm ngặt 2 mục lớn (`01_Training_Seen` và `02_Unseen_Acceptance`) kèm bảng chỉ mục SHA-256 và hướng dẫn hội đồng:
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

