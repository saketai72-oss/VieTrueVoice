# STANDARDS_api-benchmarks — Đặc Tả API, Giao Diện & Định Dạng Benchmark

---

## 1. Đặc Tả REST API Suy Luận (`src/app/server.py`)

- **Đường dẫn cơ sở (Base URL)**: `/api/v1`
- **Endpoint**: `POST /api/v1/predict`
- **Kiểu nội dung (Content-Type)**: `multipart/form-data`
- **Dữ liệu đầu vào**: `file: UploadFile` (hỗ trợ các định dạng âm thanh: `.wav`, `.mp3`, `.m4a`, `.ogg`, `.opus`)
- **Xử lý**: Đọc trực tiếp vào RAM (`io.BytesIO`), chạy tiền xử lý (< 0.2s), cắt cửa sổ trượt 4s (64.000 mẫu), chạy mô hình `torch.inference_mode()`, xóa file tạm ngay.

### Cấu Trúc Phản Hồi Thành Công (`200 OK`)
```json
{
  "request_id": "req_20261016_001",
  "prediction": "BONA_FIDE",
  "label": 1,
  "raw_score": 10.9324,
  "threshold": 0.0,
  "confidence": null,
  "confidence_calibrated": false,
  "n_windows": 2,
  "latency_sec": 0.066,
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

> **Quy ước Quyết định & Độ Tin Cậy (STUBBORN_FACT)**:
> - Ngưỡng mặc định: $\theta = 0.0$ hoặc ngưỡng hiệu chuẩn theo ngân sách $\theta_{\text{cal}} = \text{percentile}(\text{scores}_{\text{bona}}, \text{budget} \times 100)$. `raw_score >= threshold` $\implies$ `BONA_FIDE` (nhãn 1), ngược lại $\implies$ `SPOOF` (nhãn 0).
> - **Hiệu chuẩn Xác suất Platt Scaling (v0.4.7)**: Khi bộ hiệu chuẩn xác suất được áp dụng (`confidence_calibrated = true`), xác suất hậu nghiệm $P(\text{bonafide}|s) = \frac{1}{1 + \exp(-k \cdot s)}$ được tính toán từ điểm gộp thô với hệ số scale $k=0.3569$. Để tuân thủ khuyến nghị NIST Forensics và tránh việc khẳng định chắc chắn 100% sai lệch, độ tin cậy được kẹp an toàn trong khoảng $[0.1\%, 99.9\%]$ (ví dụ: điểm $s=-29.56$ cho posterior $99.997\%$ kẹp thành $99.9\%$ Spoof). Khi chưa có bộ hiệu chuẩn, trường `confidence` trả về `null` và `confidence_calibrated = false`.
> - **Cơ chế Multi-window Max-pooling (v0.4.3)**: Đoạn âm thanh dài hơn 4.0s được trích xuất cửa sổ trượt (win=64.000, hop=16.000, tối đa 5 cửa sổ) và gộp thành một mini-batch `(N_windows, 64000)` để chạy trong 1 lượt forward pass duy nhất (`batch_window_forward`), sau đó gộp điểm bằng `pool_scores(mode='max')`. Trường `n_windows` minh bạch số lượng cửa sổ được gộp.
> - Tuyệt đối không dùng `sigmoid(abs(raw_score))` để tạo xác suất giả mạo 100%.

---

## 2. Giao Diện Người Dùng & Bot Tiếp Nhận

### Web Demo Gradio (Dành Cho Người Cao Tuổi – US4, NFR4)
- **Tiêu chuẩn thiết kế**: Giao diện tối giản, hoàn tất kiểm tra trong $\le 3$ thao tác (Chọn file $\rightarrow$ Bấm kiểm tra $\rightarrow$ Xem kết quả to rõ).
- **Phản hồi**: Hiển thị nhãn trực quan (`THẬT` - Xanh lá / `GIẢ MẠO` - Đỏ) kèm thang độ tin cậy và cảnh báo rủi ro lừa đảo dễ hiểu cho phụ huynh.
- **Thời gian phản hồi**: $\le 3$ giây cho đoạn thoại 5–10 giây.

### Bot Telegram Tiếp Nhận Tin Nhắn Thoại
- Nhận tin nhắn thoại (`voice message`) hoặc file âm thanh chuyển tiếp từ người dùng.
- Tải về luồng byte trên RAM, suy luận và phản hồi kết quả trực tiếp trong tin nhắn chat.

---

## 3. Cấu Trúc Log Đo Độ Trễ Ẩn Danh (`benchmarks/latency_log.json`)

Mọi yêu cầu suy luận qua Web Demo, Bot Telegram hoặc script kiểm thử đều phải tự động nối thêm bản ghi JSON ẩn danh bằng mã băm SHA-256 (tuân thủ Luật 91/2025/QH15):

```json
{
  "request_id": "req_20261016_001",
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "duration_sec": 6.5,
  "codec_detected": "opus_16kbps_8khz",
  "predicted_label": "GIA (SPOOF)",
  "confidence_score": 0.942,
  "latency_sec": 1.48,
  "timestamp": "2026-11-20T14:30:00Z"
}
```

---

## 4. Giao Thức Đánh Giá Thực Nghiệm & Đo Lường

### Giao Thức Đo Mốc 'Trước' Ở Tuần W2 (17–23/10/2026)
- **Đo tai người nghe mù (`Blind Listening Package`)**: Tổ chức cho $\ge 10$ người nghe 20 đoạn thoại thật/giả (ẩn danh kèm biểu mẫu chấm độc lập và file khóa giải mã `blind_key_private.csv`) để đo tỷ lệ phân biệt thực tế bằng tai người (thay cho con số 35% ước lượng ban đầu).
- **Đo xác minh thủ công**: Bấm giờ $\ge 3$ lần quy trình xác minh truyền thống (gọi lại người thân / hỏi câu bí mật) để làm mốc 'Trước' cho Bảng 3.3.

### Script Tái Lập EER & Đường Cong DET (`scripts/eval_eer.py` – US8)
- Quét ngưỡng quyết định $\theta$ nơi tỉ lệ chấp nhận nhầm (FAR) bằng tỉ lệ từ chối nhầm (FRR).
- Xuất EER (%), minDCF và đường DET ra tệp `benchmarks/eval_metrics.csv`:
```csv
experiment_id,model_name,augmentation,test_condition,tts_generator,eer_percent,min_dcf,date_evaluated
```

### Bộ AI Eval $\ge 30$ Tình Huống & Kiểm Thử TDD (W6 / CP6)
- Xây dựng bộ đánh giá hệ thống AI gồm $\ge 30$ ca kiểm thử (trong đó bắt buộc có $\ge 10$ tình huống hệ thống từng nhận diện sai, báo cáo tỷ lệ đạt trước và sau khi sửa).
- Duy trì bộ kiểm thử tự động TDD đạt **301/301 unit tests xanh** (`pytest tests/ -v`) trên máy cục bộ và GitHub Actions CI.

### Giao Thức Đánh Giá Nghiệm Thu 5 Tình Nguyện Viên Đối Chứng (795 Clips — v0.4.7)
- Kịch bản thực thi: `scripts/eval_5spk_unseen_and_bonafide.py`.
- Tập dữ liệu nghiệm thu gồm 795 clips:
  - 420 clip giọng thật bona fide (84 clips gốc của 5 người x 5 codecs: Clean 16kHz, AAC-LC 76k, Opus 24k, AMR-NB, G.711 A-law).
  - 375 clip giọng giả Unseen TTS thuần Zero-Shot VoiceStudio CFM (OmniVoice) qua 5 codecs.
- Chỉ số xuất bản bắt buộc ra `benchmarks/eval_5spk_unseen_and_bonafide.json`:
  - Bona Fide Pass Rate (%), Unseen Spoof Detection Rate (%).
  - Equal Error Rate (EER) và minDCF.
  - Phân tích chi tiết theo từng người nói (`SPK_0003`..`SPK_0007`) và từng loại codec viễn thông.

### Giao Thức Đo Độ Trễ Chuẩn (`scripts/benchmark_latency.py`)
- **Tệp âm thanh**: Đoạn thoại thực tế dài 5,0 đến 10,0 giây.
- **Số lần lặp**: Đo liên tiếp đúng **30 lần**.
- **Chỉ số tổng hợp**: **Trung vị (Median Latency) $\le 3,0$ giây** (thực tế đo đạt **66.3ms**, P90 **68.2ms**).
- **Đầu ra**: Tự động xuất kết quả ra `benchmarks/latency_benchmark.csv` và log mã băm SHA-256 vào `benchmarks/latency_log.json`.

---

## 5. Quy Chuẩn Thử Thách Nhân Bản Giọng Trực Tiếp 4 Chiều (Quad-Forensics Benchmark — v0.5.0)

Nhằm phục vụ đánh giá năng lực phát hiện Deepfake tương tác trực tiếp với người dùng và hội đồng bảo vệ, hệ thống chuẩn hóa luồng thử nghiệm đối chứng 4 chiều (`src/vitruevoice/live_cloner.py` & `src/app/ui.py` Tab 2):

### 5.1. Luồng Sinh Mẫu Zero-Shot Tự Động & Câu Thoại Chuẩn
1. **Âm thanh tham chiếu (Reference Audio)**: Ghi âm trực tiếp qua Microphone trình duyệt (3 - 5 giây).
2. **Câu thoại nhân bản cố định (Target Text)**:
   > `"Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."` (10 từ thuần Việt, không cần cấu hình tùy chọn để tránh phân tán).
3. **Bộ 3 Mô hình TTS Zero-Shot nhân bản**:
   - `Bản 2 (F5-TTS)`: Mô hình Flow Matching Non-Autoregressive (`hynt/F5-TTS-Vietnamese-ViVoice`).
   - `Bản 3 (VieNeu-TTS v3 Turbo)`: Mô hình Fast DiT 48kHz (`pnnbao-ump/VieNeu-TTS-v3-Turbo`).
   - `Bản 4 (VoiceStudio CFM)`: Mô hình Continuous Flow Matching thuần Zero-Shot (`k2-fsa/OmniVoice`).

### 5.2. Cơ Chế Progressive Real-Time Streaming & Quản Trị Bộ Nhớ
- **Streaming Generator (`yield`)**:
  - `Bước 0 (~66ms)`: Trả kết quả thẩm định bản Người Thật (Bona Fide) ngay lập tức kèm Audio player. 3 thẻ còn lại hiển thị trạng thái `Loading` (animated spinner).
  - `Bước 1 (~3.4s)`: Hoàn tất nhân bản F5-TTS, hiển thị kết quả thẩm định và Audio player cho Bản 2; thẻ 3 & 4 tiếp tục nạp.
  - `Bước 2 (~3.9s)`: Hoàn tất nhân bản VieNeu-TTS v3 Turbo, hiển thị kết quả thẩm định và Audio player cho Bản 3.
  - `Bước 3 (~3.5s)`: Hoàn tất nhân bản VoiceStudio CFM, hiển thị kết quả Bản 4 và xuất bản Bảng Ma Trận Đối Soát 4 Chiều (Quad-Forensics Matrix).
- **Phân luồng an toàn**: Tải file lên chỉ chạy kiểm định đơn bản (<100ms) tại Chế độ 1; chỉ ghi âm trực tiếp qua mic mới kích hoạt nhân bản 3 bản clone tại Chế độ 2.
- **Tối ưu VRAM GPU < 4GB**: Hỗ trợ checkbox *"Chế độ tiết kiệm VRAM"* (chỉ chạy VoiceStudio CFM) và lệnh giải phóng đệm CUDA `torch.cuda.empty_cache()` + `gc.collect()` sau mỗi vòng sinh giọng.
- **Bảo mật sinh trắc học (Luật 91/2025/QH15)**: Âm thanh xử lý in-memory stream trên RAM, file tham chiếu tạm xóa hủy ngay lập tức trong khối `finally`.

---

*v0.5.0 — 2026-11-13*
