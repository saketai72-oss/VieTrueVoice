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
*(Yêu cầu: Toàn bộ 227 unit tests pass 100% trước khi commit hoặc đẩy lên Kaggle/Colab)*

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

### Chạy Máy Chủ API Phát Triển (FastAPI)
```bash
uvicorn src.app.server:app --reload --port 8000
```

### Chạy Đo Lường Độ Trễ (30 lần lặp)
```bash
python scripts/benchmark_latency.py
```
