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

## 3. Bộ Nạp Âm Thanh Đa Định Dạng In-Memory (`src/preprocessing/audio_loader.py`)

Nhằm khắc phục tình trạng nhận diện định dạng sai lệch khi người dùng/hệ thống đổi đuôi tệp thủ công (như `.m4a` đổi thành `.wav`) và tuân thủ tuyệt đối quy định bảo mật sinh trắc học (không ghi tệp âm thanh nhạy cảm ra đĩa):

### 3.1. Nhận Diện Theo Magic Bytes (File Signatures)
Bộ nạp không dựa vào phần mở rộng tệp (`.wav`, `.m4a`), mà kiểm tra trực tiếp các byte đầu tiên của luồng nhị phân:
- **WAV**: `RIFF....WAVE`.
- **OGG/Opus**: `OggS`.
- **FLAC**: `fLaC`.
- **MP3**: `ID3` hoặc Frame Sync `\xff\xfb` / `\xff\xf3` / `\xff\xf2`.
- **M4A / AAC / MP4**: Box header `ftyp` tại byte offset 4 (`M4A `, `isom`, `mp42`, `dash`).
- **AMR**: Chữ ký `#!AMR\n`.

### 3.2. Luồng Giải Mã RAM Stream Tuyệt Đối (Zero Disk Files)
- **Đường dẫn nhanh (Fast Path)**: Sử dụng `soundfile.read(io.BytesIO(raw_bytes))` cho các định dạng không nén/lossless được hỗ trợ trực tiếp (WAV, FLAC, OGG).
- **Đường dẫn FFmpeg Stream qua RAM**: Đối với M4A, AAC, MP3, AMR hoặc định dạng nén viễn thông, nạp dữ liệu bằng đường ống `pipe:0 -> pipe:1` của FFmpeg:
  ```bash
  ffmpeg -nostdin -i pipe:0 -f wav -acodec pcm_s16le -ar 16000 -ac 1 pipe:1
  ```
  Quá trình giải mã diễn ra 100% trong RAM, không sinh bất kỳ tệp tạm nào trên ổ đĩa.
- **Tính tương thích toán học bit-exact**: Trên toàn bộ các định dạng WAV 16k, G.711 8k, AMR-NB 8k, 24k mono và 44.1k stereo, đầu ra của `audio_loader.py` khớp chính xác $100\%$ ($\max |x_{\text{new}} - x_{\text{old}}| = 0.0$) với pipeline `load_wave` cũ, giữ nguyên $0.000000$ sai lệch điểm số Checkpoint B.

### 3.3. Chuẩn Hóa Đầu Vào Tensor Cố Định (`prepare_input_tensor`)
- Chuyển đổi về 1 kênh Mono và tần số lấy mẫu cố định $16.000\text{ Hz}$.
- Khóa kích thước tensor $(1, 64000)$ ($4.0\text{s}$ ở $16\text{ kHz}$):
  - Dài hơn 64.000 mẫu: Cắt ngẫu nhiên khi `train=True`, cắt chính giữa khi `train=False`.
  - Ngắn hơn 64.000 mẫu: Áp dụng **Repeat Padding** (`np.tile`) đến đủ 64.000 mẫu. Tuyệt đối không đệm số 0.

---

## 4. Kênh Truyền Zalo Mục Tiêu & Dữ Liệu Ghép Cặp (Dual Profile)

### 4.1. Đặc Tả Hai Kênh Phụ (Dual Profile)
Dựa trên khảo sát thực tế và phân tích pháp y dữ liệu tải từ nền tảng Zalo:
- **Profile A (Gửi tệp đính kèm - File Attachment)**: `aac_zalo_76k`
  - Container: `.m4a` (ISO Media / Apple QuickTime).
  - Audio Format: AAC-LC (Low Complexity), tần số $48.000\text{ Hz}$, 1 kênh Mono, bitrate danh định $\approx 76\text{ kbps}$ (giải thuật nén tương thích iOS Core Media Audio / Android MediaCodec).
- **Profile B (Tin nhắn thoại - Voice Note)**: `opus_zalo_24k`
  - Container: `.ogg` (Ogg Container).
  - Audio Format: Opus, tần số $16.000\text{ Hz}$ hoặc $48.000\text{ Hz}$, bitrate danh định $\approx 24\text{ kbps}$.

### 4.2. Sinh Manifest Ghép Cặp Khóa Mã Phát Ngôn (`scripts/generate_zalo_paired_manifests.py`)
- Trích xuất định danh phát ngôn gốc `base_utt` (loại bỏ hậu tố `_clean`, `_g711`, `_amr`).
- Mỗi phát ngôn gốc sạch tạo tương ứng 2 bản sao suy giảm kênh: Profile A và Profile B.
- Duy trì tính khép kín của từng tập phân chia (Split Containment):
  - `train_zalo.csv`: 49.085 mẫu (100% loại bỏ `SPK_xxxx` và `VieNeu-TTS`).
  - `dev_zalo.csv`: 11.450 mẫu (cân bằng 1:1:1 giữa `clean_16khz`, `aac_zalo_76k`, và `opus_zalo_24k` với 2.332 mẫu mỗi điều kiện).
  - `test_indomain_zalo.csv`: 15.980 mẫu giữ lại để đánh giá độc lập.
- Kiểm tra tính rò rỉ: Hoàn toàn không rò rỉ `base_utt`, `speaker_id` hay văn bản giữa Train, Dev và Test.

---

*v0.4.1 — 2026-10-30*
