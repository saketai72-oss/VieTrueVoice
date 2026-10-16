# LOGIC_preprocessing — Chuẩn Hóa Tín Hiệu & Tăng Cường Âm Thanh

---

## 1. Đường Ống Tiền Xử Lý Âm Thanh (`src/preprocessing/audio_processor.py`)

### Bước 1: Chuyển Về Kênh Đơn (Mono) & Tái Lấy Mẫu (16.000 Hz)
- Các kênh âm thanh đa kênh (Stereo) được lấy trung bình cộng về 1 kênh duy nhất:
  $$x_{mono}[n] = \frac{1}{C} \sum_{c=1}^C x_c[n]$$
- Đưa toàn bộ mẫu âm thanh từ các tần số 24kHz / 44.1kHz / 48kHz về chuẩn **16.000 Hz (16-bit PCM)** — yêu cầu bắt buộc của Wav2Vec 2.0 và AASIST.

### Bước 2: Cắt Bỏ Khoảng Lặng Đầu & Cuối (Silence Trimming)
- Tính toán đường bao năng lượng hiệu dụng (RMS) với `frame_length=512, hop_length=160`.
- Ngưỡng cắt đặt tại **phân vị thứ 20 (20th percentile)** của năng lượng các khung:
  $$\text{threshold} = P_{20}(\text{RMS})$$
- Các khung có $\text{RMS} > \text{threshold}$ được giữ lại; phần khoảng lặng ở đầu và cuối file bị cắt bỏ.
- Mục đích: Triệt tiêu hiện tượng rò rỉ nhãn do khoảng lặng của người thật tạo ra.

### Bước 3: Cố Định Độ Dài 4 Giây (64.000 Mẫu Điểm)
- **Nếu file ngắn hơn 4 giây (< 64.000 mẫu)**: Thực hiện nối lặp lại chính tín hiệu đó (`Repeat Padding`) bằng `np.tile(wav, num_repeats)[:64000]`.
  > STUBBORN_FACT: Bắt buộc dùng Repeat Padding thay vì đệm số 0 (Zero-padding) nhằm giữ tính liên tục phổ - thời gian cho các bộ lọc tích chập và đồ thị chú ý.
- **Nếu file dài hơn 4 giây (>= 64.000 mẫu)**: Cắt lấy 64.000 mẫu đầu tiên (lúc huấn luyện có thể cắt ngẫu nhiên, lúc suy luận cắt chính giữa hoặc trượt cửa sổ).

### Bước 4: Chuẩn Hóa Biên Độ Z-Score
- Chuẩn hóa tín hiệu về trung bình bằng 0, phương sai bằng 1:
  $$x_{norm}[n] = \frac{x[n] - \mu}{\sigma + 10^{-8}}$$

---

## 2. Các Thuật Toán Tăng Cường Dữ Liệu (Augmentation)

### Thuật Toán RawBoost (Miền Thời Gian Waveform)
- **Nhánh 1**: Nhiễu cộng tính phụ thuộc tín hiệu (ISD).
- **Nhánh 2**: Nhiễu xung không phụ thuộc tín hiệu (SSI).
- **Nhánh 3**: Lọc tích chập tuyến tính và phi tuyến (LnL - Algo 3/5).
- Áp dụng ngẫu nhiên trong DataLoader lúc huấn luyện với xác suất 50%.

### Mô Phỏng Nén Kênh Truyền Viễn Thông & Mạng Xã Hội (Codec Simulation)
- **Chuẩn nén Opus**: Bitrate thấp 16–32 kbps (mô phỏng tin nhắn thoại Zalo, Telegram).
- **Chuẩn nén viễn thông**: AMR-NB, AMR-WB, GSM.
- **Hạ tần số 8 kHz & Bộ lọc dải thông**: Hạ tần số xuống 8 kHz và nội suy ngược lên 16 kHz kết hợp bộ lọc Bandpass 300Hz–3400Hz (mô phỏng cuộc gọi thoại PSTN/VoIP).

---

*v0.1.0 — 2026-10-16*
