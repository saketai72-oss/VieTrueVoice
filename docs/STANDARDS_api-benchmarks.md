# STANDARDS_api-benchmarks — API Specifications & Benchmark Schemas

---

## 1. REST API Specification (`src/app/server.py`)

- **Base URL**: `/api/v1`
- **Endpoint**: `POST /api/v1/predict`
- **Content-Type**: `multipart/form-data`
- **Request Body**: `file: UploadFile` (audio formats: `.wav`, `.mp3`, `.m4a`, `.ogg`)

### Response Schema (`200 OK`)
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

## 2. Benchmark Log Schema (`benchmarks/latency_log.json`)

All runtime evaluation and bot requests must append an anonymous JSON entry:

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

## 3. Evaluation Metrics Table (`benchmarks/eval_metrics.csv`)

Columns required for tracking experiments:

```csv
experiment_id,model_name,augmentation,test_condition,tts_generator,eer_percent,min_dcf,date_evaluated
```

---

## 4. Latency Benchmark Protocol (`scripts/benchmark_latency.py`)

- Input audio: 5.0–10.0s clip.
- Iterations: Exactly 30 consecutive inferences.
- Metric: **Median latency**.
- Threshold: **<= 3.0 seconds**.
- Output: `benchmarks/latency_benchmark.csv`.

---

*v0.1.0 — 2026-10-16*
