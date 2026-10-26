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

## 4. Các Lệnh Thực Thi & Kiểm Thử Thường Dùng

### Chạy Kiểm Thử Tự Động (TDD Unit Tests)
```bash
pytest tests/ -v
```
*(Yêu cầu: 31/31 unit tests pass 100% trước khi commit hoặc đẩy lên Kaggle)*

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

### Chạy Máy Chủ API Phát Triển (FastAPI)
```bash
uvicorn src.app.server:app --reload --port 8000
```

### Chạy Đo Lường Độ Trễ (30 lần lặp)
```bash
python scripts/benchmark_latency.py
```
