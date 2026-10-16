# STANDARDS_api-benchmarks — Đặc Tả API & Định Dạng Benchmark

---

## 1. Đặc Tả REST API Suy Luận (`src/app/server.py`)

- **Đường dẫn cơ sở (Base URL)**: `/api/v1`
- **Endpoint**: `POST /api/v1/predict`
- **Kiểu nội dung (Content-Type)**: `multipart/form-data`
- **Dữ liệu đầu vào**: `file: UploadFile` (hỗ trợ các định dạng âm thanh: `.wav`, `.mp3`, `.m4a`, `.ogg`, `.opus`)

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

## 2. Cấu Trúc Log Đo Độ Trễ Ẩn Danh (`benchmarks/latency_log.json`)

Mọi yêu cầu suy luận qua Web Demo, Bot Telegram hoặc script kiểm thử đều phải tự động nối thêm bản ghi JSON ẩn danh:

```json
{
  "request_id": "req_20261016_001",
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "duration_sec": 6.5,
  "codec_detected": "opus_16kbps_8khz",
  "predicted_label": "GIA (SPOOF)",
  "confidence_score": 0.942,
  "latency_sec": 1.48,
  "timestamp": "2026-10-16T14:30:00Z"
}
```

---

## 3. Cấu Trúc Bảng Kết Quả Đánh Giá (`benchmarks/eval_metrics.csv`)

Các cột bắt buộc để theo dõi tiến độ thực nghiệm và đối sánh trước/sau:

```csv
experiment_id,model_name,augmentation,test_condition,tts_generator,eer_percent,min_dcf,date_evaluated
```

---

## 4. Giao Thức Đo Độ Trễ Chuẩn (`scripts/benchmark_latency.py`)

- **Tệp âm thanh đầu vào**: Đoạn thoại thực tế dài từ 5,0 đến 10,0 giây.
- **Số lần lặp**: Đo liên tiếp đúng **30 lần**.
- **Chỉ số tổng hợp**: Lấy giá trị **Trung vị (Median Latency)**.
- **Ngưỡng đạt yêu cầu**: **<= 3,0 giây**.
- **Đầu ra**: Tự động lưu bảng kết quả vào `benchmarks/latency_benchmark.csv`.

---

*v0.1.0 — 2026-10-16*
