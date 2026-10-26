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
  "confidence": 0.942,
  "latency_sec": 1.48,
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

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
- Duy trì bộ kiểm thử tự động TDD đạt **31/31 unit tests xanh** (`pytest tests/ -v`) trên GitHub Actions CI.

### Giao Thức Đo Độ Trễ Chuẩn (`scripts/benchmark_latency.py`)
- **Tệp âm thanh**: Đoạn thoại thực tế dài 5,0 đến 10,0 giây.
- **Số lần lặp**: Đo liên tiếp đúng **30 lần**.
- **Chỉ số tổng hợp**: **Trung vị (Median Latency) $\le 3,0$ giây**.
- **Đầu ra**: Tự động xuất kết quả ra `benchmarks/latency_benchmark.csv`.

---

*v0.2.3 — 2026-10-26 (Frozen Pipeline V14)*
