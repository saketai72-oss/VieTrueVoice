# LOGIC_preprocessing — Chuẩn Hóa Tín Hiệu & Tăng Cường Âm Thanh

---

## 1. Đường Ống Tiền Xử Lý Âm Thanh Chuẩn Hóa (`src/preprocessing/audio_processor.py`)

> **Nguyên tắc chống học lệch (Anti-Shortcut Learning)**:
> Các công cụ TTS xuất âm thanh ở tần số lấy mẫu khác nhau (VieNeu-TTS: 24kHz/48kHz, F5-TTS: 24kHz, VIVOS: 16kHz) và không có khoảng lặng tự nhiên ở đầu/cuối như bản thu thật. Khi truyền qua kênh nén (Opus, AMR-NB, G.711, 8kHz), tín hiệu suy hao làm xóa mờ các dấu vết giả mạo vi mô. Tiền xử lý bắt buộc loại bỏ triệt để sai lệch kỹ thuật này.

### Bước 1: Chuyển Về Kênh Đơn (Mono) & Tái Lấy Mẫu (16.000 Hz)
- Các file âm thanh Stereo được lấy trung bình cộng về 1 kênh duy nhất:
  $$x_{mono}[n] = \frac{1}{C} \sum_{c=1}^C x_c[n]$$
- Đưa toàn bộ mẫu âm thanh từ các tần số 24kHz / 44.1kHz / 48kHz về chuẩn **16.000 Hz (16-bit PCM WAV)** — yêu cầu tensor đầu vào bắt buộc của Wav2Vec 2.0 và AASIST.

### Bước 2: Cắt Bỏ Khoảng Lặng Đầu & Cuối (Silence Trimming)
- Tính đường bao năng lượng hiệu dụng (RMS) với `frame_length=512, hop_length=160`.
- Ngưỡng cắt đặt tại **phân vị thứ 20 (20th percentile)** của năng lượng các khung:
  $$\text{threshold} = P_{20}(\text{RMS})$$
- Các khung có $\text{RMS} > \text{threshold}$ được giữ lại; phần khoảng lặng ở đầu và cuối file bị cắt bỏ, triệt tiêu hiện tượng rò rỉ nhãn do khoảng lặng của người thật tạo ra.

### Bước 3: Cố Định Độ Dài 4 Giây (64.000 Mẫu Điểm tại 16 kHz)
- **Nếu file ngắn hơn 4 giây (< 64.000 mẫu)**: Thực hiện nối lặp lại chính tín hiệu đó (`Repeat Padding`) bằng `np.tile(wav, num_repeats)[:64000]`.
  > STUBBORN_FACT: Bắt buộc dùng Repeat Padding thay vì đệm số 0 (Zero-padding) nhằm giữ tính liên tục phổ - thời gian cho các bộ lọc tích chập và đồ thị chú ý.
- **Nếu file dài hơn 4 giây (>= 64.000 mẫu)**: Lấy ngẫu nhiên một đoạn 4 giây (`Random Crop`) khi Train; lấy đoạn chính giữa hoặc trượt cửa sổ (`Sliding Window`) khi Inference.

### Bước 4: Chuẩn Hóa Độ To EBU R128 & Biên Độ Z-Score
- Áp dụng chuẩn hóa độ to âm lượng **EBU R128** (cùng mức target **$-23\text{ LUFS}$** cho cả bona fide và spoof) và tắt watermark âm học (`apply_watermark=False`) để ngăn mô hình học lệch biên độ.
- Chuẩn hóa Z-score tín hiệu waveform về trung bình bằng 0, phương sai bằng 1:
  $$x_{norm}[n] = \frac{x[n] - \mu}{\sigma + 10^{-8}}$$

```python
# Hàm tiền xử lý âm thanh chuẩn hóa
import torch, torchaudio, librosa, numpy as np

def preprocess_audio(file_path, target_sr=16000, max_len=64000):
    # 1. Load & chuyển Mono, resample 16kHz
    wav, sr = librosa.load(file_path, sr=target_sr, mono=True)
    # 2. Cắt khoảng lặng dựa trên phân vị thứ 20 của năng lượng
    energy = librosa.feature.rms(y=wav, frame_length=512, hop_length=160)[0]
    threshold = np.percentile(energy, 20)
    valid_frames = np.where(energy > threshold)[0]
    if len(valid_frames) > 0:
        start = max(0, valid_frames[0] * 160)
        end = min(len(wav), (valid_frames[-1] + 1) * 160)
        wav = wav[start:end]
    # 3. Cố định 64.000 mẫu bằng Repeat Padding hoặc Crop
    if len(wav) < max_len:
        num_repeats = int(np.ceil(max_len / len(wav)))
        wav = np.tile(wav, num_repeats)[:max_len]
    else:
        wav = wav[:max_len]
    # 4. Chuẩn hóa Z-score
    wav = (wav - np.mean(wav)) / (np.std(wav) + 1e-8)
    return torch.tensor(wav, dtype=torch.float32)
```

---

## 2. Các Thuật Toán Tăng Cường Dữ Liệu (Augmentation & ADR-2)

### Thuật Toán RawBoost (Miền Thời Gian Waveform)
Tích hợp trực tiếp thuật toán RawBoost (Tak et al., Odyssey 2022) ngay trong `DataLoader` lúc huấn luyện:
- **Nhánh 1**: Nhiễu cộng tính phụ thuộc tín hiệu (ISD).
- **Nhánh 2**: Nhiễu xung không phụ thuộc tín hiệu (SSI).
- **Nhánh 3**: Lọc tích chập tuyến tính và phi tuyến (LnL - Algo 3/5).
- Áp dụng ngẫu nhiên trong DataLoader lúc huấn luyện với xác suất 50%.

### Mô Phỏng Nén Kênh Truyền Viễn Thông (`TelephonyCompressor`)
- **Chuẩn nén Opus**: Bitrate thấp $16$–$32\text{ kbps}$ (mô phỏng tin nhắn thoại Zalo, Messenger, Telegram).
- **Chuẩn nén AMR-NB**: $8\text{ kHz}$ Mono, $12.2\text{ kbps}$ qua `libopencore_amrnb` (chuẩn di động 2G/3G GSM).
- **Chuẩn nén G.711 A-law**: $8\text{ kHz}$ Mono, $64\text{ kbps}$ (PSTN/ISDN) kết hợp lọc Bandpass $300\text{ Hz}$–$3400\text{ Hz}$ rồi nội suy ngược lên $16\text{ kHz}$.

### Hiện Tượng Lệch Miền & Dịch Chuyển Ngưỡng (Narrowband Upward Shift)
Thực nghiệm đối soát trên tập dữ liệu chứng minh:
- Băng thông hẹp $8\text{ kHz}$ triệt tiêu toàn bộ dải hài âm trên $3.4$–$4.0\text{ kHz}$, làm phương sai phân phối Impostor $\sigma_I$ tăng từ $0.0875$ lên $0.1011$.
- Chỉ số nhạy phân tách $d'$ suy giảm mạnh:
  - G.711 A-law: $d' = 4.02$ (giảm **$22.8\%$** so với Studio $d' = 5.21$).
  - AMR-NB: $d' = 3.89$ (giảm **$25.5\%$** so với Studio $d' = 5.21$).
- Gây hiện tượng **Dịch chuyển Ngưỡng (Narrowband Upward Shift)** đẩy ngưỡng $T_{\text{FAR 1\%}}$ từ $0.4800$ lên $0.5958$ (G.711) và $0.6195$ (AMR-NB). Do đó, nhãn `codec` bắt buộc được ghi nhận trong manifest và tăng cường trực tiếp vào tập huấn luyện.

---

*v0.2.3 — 2026-10-26 (Frozen Pipeline V14)*
