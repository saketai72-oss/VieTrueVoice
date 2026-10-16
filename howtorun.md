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

### Bước 5: Tải weights / logs về máy
```bash
python manage_kaggle.py output
```
Toàn bộ file kết quả trong `/kaggle/working/` sẽ được tải về thư mục `./out/` tại máy của bạn.
