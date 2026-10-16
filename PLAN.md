# TÀI LIỆU ĐẶC TẢ & KẾ HOẠCH THỰC THI CHO ANTIGRAVITY AGENT (PLAN.md)

## 0\. TỔNG QUAN BÀI TOÁN & QUY TẮC BẮT BUỘC CHO AGENT (SYSTEM RULES)

### 0.1. Bài toán cốt lõi & Mục tiêu nghiệm thu (Target KPIs)

- **Tên dự án:** ViTrueVoice – Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát.  
- **Bài toán cốt lõi:** Phân loại nhị phân độc lập từng mẫu âm thanh tiếng Việt (độ dài thực tế 5–10 giây) thành **Giọng thật (`Bona fide` \- nhãn `1`)** hoặc **Giọng giả (`Spoof` \- nhãn `0`)** được sinh từ các công cụ TTS/Voice Cloning và truyền qua kênh nén viễn thông hoặc mạng xã hội (Opus, AMR, lọc băng tần 8 kHz).  
- **Chỉ số nghiệm thu đích (Target KPIs):**  
  1. **Độ chính xác nội bộ (In-domain EER):** `EER <= 8%` trên tập kiểm thử nội bộ (mẫu thật và mẫu giả từ F5-TTS, VieNeu-TTS).  
  2. **Độ bền nén kênh thoại (Giả thuyết H1):** Giảm ít nhất `30% tương đối` chỉ số EER trên tập kiểm thử đã nén (Opus, AMR, 8 kHz) nhờ tăng cường dữ liệu mô phỏng kênh thoại so với baseline không tăng cường.  
  3. **Độ bền trước công cụ lạ (Unseen TTS EER \- Giả thuyết H2):** Duy trì `EER <= 15%` khi kiểm thử trên công cụ TTS/Voice Conversion thứ 3 chưa từng xuất hiện trong lúc huấn luyện.  
  4. **Thời gian phản hồi (Inference Latency):** `<= 3 giây` cho một đoạn thoại dài 5–10 giây (đo lặp 30 lần liên tiếp, lấy trung vị).

### 0.2. Quy tắc Phát triển & Vận hành dành cho Antigravity Agent

1. **Quy tắc TDD (Test-Driven Development):** Bắt buộc viết kịch bản kiểm thử (`pytest`) trước khi viết mã nguồn thực thi (tối thiểu 3 unit tests viết trước ở Giai đoạn 1–2 và nâng lên `>= 10 test cases`, trong đó có `>= 5 tests tự động` chạy trên CI ở Giai đoạn 4).  
2. **Quy ước Git Commit:** Mọi bản commit có sự hỗ trợ sinh mã của AI bắt buộc gắn tiền tố `[AI]` ở đầu thông điệp commit (ví dụ: `[AI] feat(preprocessing): add 16kHz mono silence trimming and repeat padding`).  
3. **Quy trình Huấn luyện Hybrid (Local Code \<-\> Kaggle GPU):**  
   - Phát triển mã nguồn, viết unit test và quản lý toàn bộ dự án tại máy Local.  
   - Đẩy dữ liệu và kịch bản `train.py` lên GPU miễn phí của Kaggle thông qua CLI `manage_kaggle.py`:  
     - Đường dẫn đọc dữ liệu trên Kaggle: `/kaggle/input/<ten-dataset>`  
     - Đường dẫn lưu trọng số (`best_model.pt`) và log trên Kaggle: `/kaggle/working/`  
     - Đường dẫn tải kết quả về máy Local: `./out/`  
4. **Đạo đức Dữ liệu & Bảo mật Sinh trắc học (Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 & Nghị định 356/2025/NĐ-CP):**  
   - Tuyệt đối không lưu tên thật hoặc thông tin định danh cá nhân (PII) của người đóng góp giọng nói trên repo; bắt buộc dùng mã ẩn danh `SPK_XXXX`.  
   - Khi suy luận qua API/Bot, đọc luồng byte trực tiếp trên RAM và xóa hủy ngay tệp âm thanh tạm sau khi trả kết quả.  
   - Mọi bản ghi log đánh giá (`benchmarks/latency_log.json`) phải băm ẩn danh tệp âm thanh bằng mã `SHA-256` thay cho tên tệp gốc.

### 0.3. Cấu trúc Thư mục Chuẩn của Dự án

VieTrueVoice/

├── PLAN.md                        \# Kế hoạch thực thi chi tiết cho Antigravity Agent

├── README.md                      \# Tài liệu hướng dẫn và bảng chỉ số Trước \- Sau

├── manage\_kaggle.py               \# CLI điều khiển đẩy code/dataset và tải kết quả từ Kaggle GPU

├── train.py                       \# Entry-point huấn luyện mô hình trên Kaggle GPU

├── requirements.txt               \# Danh sách thư viện phụ thuộc

├── Dockerfile                     \# Đóng gói dịch vụ suy luận FastAPI / Gradio

├── .github/workflows/ci.yml       \# Pipeline GitHub Actions tự động chạy pytest

├── data/

│   ├── raw/                       \# Dữ liệu gốc (VIVOS, CommonVoice, tình nguyện viên SPK\_XXXX)

│   ├── bonafide\_ref/              \# Mẫu tham chiếu sạch 3-5s kèm transcript dùng để clone giọng

│   ├── spoof\_f5tts/               \# Mẫu giả sinh từ F5-TTS-Vietnamese (Seen TTS \#1)

│   ├── spoof\_vieneu/              \# Mẫu giả sinh từ VieNeu-TTS (Seen TTS \#2)

│   ├── spoof\_unseen/              \# Mẫu giả sinh từ công cụ thứ 3 / RVC (Unseen Test)

│   ├── real\_app\_test/             \# Mẫu gửi/nhận thực tế qua Zalo, Telegram

│   └── manifests/                 \# File chia tập train.csv, dev.csv, test\_indomain.csv, test\_unseen.csv

├── src/

│   ├── preprocessing/             \# Chuẩn hóa 16kHz Mono, cắt khoảng lặng, RawBoost, nén Codec

│   ├── models/                    \# Kiến trúc Baseline AASIST và SSL-AASIST (Wav2Vec 2.0 \+ HS-GAL)

│   ├── training/                  \# Dataset, DataLoader, Weighted CE Loss, Vòng lặp huấn luyện 2 pha

│   ├── evaluation/                \# Tính toán EER, minDCF, ROC-AUC, Confusion Matrix

│   └── app/                       \# FastAPI server, Gradio Web UI, Telegram Bot handler

├── scripts/

│   ├── generate\_spoof.py          \# Script tự động sinh mẫu giả từ F5-TTS & VieNeu-TTS

│   ├── filter\_asr\_wer.py          \# Script lọc mẫu giả lỗi bằng ASR (PhoWhisper / Wav2Vec2)

│   ├── split\_dataset.py           \# Chia tập Speaker-Disjoint (70% Train / 15% Dev / 15% Test)

│   ├── eval\_eer.py                \# Script chạy đánh giá tự động và xuất benchmarks/eval\_metrics.csv

│   └── benchmark\_latency.py       \# Script bấm giờ 30 lần xuất benchmarks/latency\_benchmark.csv

├── benchmarks/

│   ├── eval\_metrics.csv           \# Lưu kết quả EER, minDCF tự động qua các thí nghiệm

│   ├── latency\_log.json           \# Lưu log thời gian phản hồi ẩn danh (SHA-256)

│   └── latency\_benchmark.csv      \# Kết quả bấm giờ độ trễ 30 lần lấy trung vị

├── out/                           \# Thư mục nhận weights/logs tải về từ Kaggle (/kaggle/working/)

└── tests/                         \# Bộ unit tests & integration tests (\>= 10 tests)

---

## GIAI ĐOẠN 01: CHUẨN BỊ DỮ LIỆU GỐC & SINH MẪU GIỌNG GIẢ (DATA & SPOOF GENERATION \- MUST \#1 / W3–W4)

**Mục tiêu Giai đoạn 1:** Xây dựng bộ dữ liệu tiếng Việt chuẩn hóa gồm tối thiểu **1.000 mẫu giọng thật (`Bona fide`)** và **2.000 mẫu giọng giả (`Spoof`)**, kiểm soát chất lượng bằng ASR và phân chia độc lập theo người nói (`Speaker-Disjoint`).

### Bước 1.1. Thu thập và Tuyển chọn Tập dữ liệu Giọng thật (`Bona fide Audio`)

- **Nguồn thu thập trực tiếp có sự đồng ý (Consent):**  
  - Tổ chức tối thiểu 1.000 mẫu giọng thật (10–20 câu ngắn/người) từ các thành viên và tình nguyện viên theo mã ẩn danh `SPK_XXXX`.  
  - Đảm bảo liên kết metadata với Phiếu đồng ý (Consent Form) tách bạch 4 mục đích: (1) thu âm, (2) huấn luyện AI, (3) làm giọng tham chiếu (`reference audio`) nhân bản giọng giả nghiên cứu, (4) lưu trữ/đánh giá ẩn danh và xóa hủy sau khi bảo vệ đồ án.  
- **Nguồn dữ liệu mở tiếng Việt sạch (`Clean Speech Corpora`):**  
  - Tích hợp bộ dữ liệu **VIVOS** (15 giờ, 65 người nói, thu âm môi trường yên tĩnh, giấy phép CC0/CC-BY-SA) và **CommonVoice tiếng Việt** (\~6–50 giờ, đa vùng miền Bắc – Trung – Nam) làm nguồn giọng thật chuẩn và mẫu tham chiếu.  
- **Quy tắc loại trừ dữ liệu nhiễu nền cao:**  
  - Tuyệt đối không dùng các bộ dữ liệu thu thập từ mạng xã hội chứa nhiều tạp âm hoặc nhạc nền (như Vietnam-Celeb) làm đầu vào cho TTS/Voice Cloning để tránh hiện tượng mô hình học lệch (`shortcut learning`) dựa trên nhiễu nền tái tạo.

### Bước 1.2. Sinh Tập dữ liệu Giọng giả (`Spoofed Audio`) từ F5-TTS, VieNeu-TTS và Công cụ Unseen

- **Chuẩn bị Mẫu tham chiếu (`Reference Clips` \- `data/bonafide_ref/`):**  
  - Trích xuất các đoạn âm thanh sạch dài từ **3 đến 5 giây**, phát âm rõ ràng kèm bản phiên âm văn bản (`transcript`) chính xác.  
  - Nếu mẫu nguồn có nhạc nền, bắt buộc chạy mô hình **Facebook Demucs** để tách sạch phần vocal trước khi đưa vào TTS.  
- **Pipeline 1 – Sinh mẫu bằng `F5-TTS-Vietnamese` (Seen TTS \#1):**  
  - Sử dụng kho mã `nguyenthienhy/F5-TTS-Vietnamese` (checkpoint `F5-TTS-Vietnamese-ViVoice` hoặc `danhtran2mind/Vi-F5-TTS`) với bộ vocoder `Vocos`.  
  - Chuẩn hóa văn bản đầu vào về chữ thường (`lowercase`), giữ nguyên dấu câu tiếng Việt, sinh các câu thoại theo kịch bản lừa đảo tài chính/mạo danh người thân.  
  - Giới hạn độ dài đầu ra từ **3 đến 15 giây** (tự động loại bỏ mọi file `< 1 giây` hoặc `> 30 giây`).  
  - Lệnh CLI mẫu tích hợp vào `scripts/generate_spoof.py`:  
      
    f5-tts\_infer-cli \\  
      
      \--model "F5TTS\_Base" \\  
      
      \--ref\_audio data/bonafide\_ref/spk01\_ref.wav \\  
      
      \--ref\_text "cả hai bên hãy cố gắng hiểu cho nhau" \\  
      
      \--gen\_text "alo mẹ ơi chuyển gấp cho con mười lăm triệu vào số tài khoản này nhé" \\  
      
      \--speed 1.0 \--vocoder\_name vocos \\  
      
      \--vocab\_file checkpoints/F5-TTS-ViVoice/vocab.txt \\  
      
      \--ckpt\_file checkpoints/F5-TTS-ViVoice/model\_last.pt

    
- **Pipeline 2 – Sinh mẫu bằng `VieNeu-TTS` (Seen TTS \#2):**  
  - Sử dụng `pnnbao97/VieNeu-TTS` (kiến trúc Qwen 0.5B/0.3B kết hợp bộ mã hóa âm thanh NeuCodec 24kHz hoặc bản `v3turbo` dùng MOSS-Audio-Tokenizer-Nano 48kHz và bộ chuyển đổi âm vị `sea-g2p`).  
  - Thực hiện Instant Voice Cloning với mẫu tham chiếu 3–5 giây, giới hạn văn bản đầu vào `<= 250 ký tự` mỗi lượt gọi để đảm bảo độ tự nhiên cao nhất:  
      
    from vieneu import Vieneu  
      
    tts \= Vieneu(mode="v3turbo")  
      
    audio \= tts.infer(  
      
        text="Mình đang có việc gấp, chuyển khoản giúp mình ngay nhé\!",  
      
        ref\_audio="data/bonafide\_ref/spk01\_ref.wav"  
      
    )

    
- **Pipeline 3 – Sinh mẫu từ công cụ thứ 3 để kiểm thử độc lập (`Unseen TTS / VC`):**  
  - Tạo tập kiểm thử riêng biệt (`data/spoof_unseen/`) hoàn toàn không xuất hiện trong lúc huấn luyện bằng công cụ Voice Conversion (như **RVC** kết hợp **UVR5 \+ HuBERT**, chọn cặp người nói có độ tương đồng Cosine giữa các vector **ECAPA-TDNN** vượt ngưỡng) hoặc một họ TTS tiếng Việt khác để đo khả năng tổng quát hóa ngoài miền (`Out-of-distribution`).

### Bước 1.3. Kiểm soát Chất lượng Mẫu giả & Phân chia Tập dữ liệu (`Speaker-Disjoint Split`)

- **Lọc chất lượng âm thanh tổng hợp bằng ASR (`scripts/filter_asr_wer.py`):**  
  - Chạy mô hình nhận dạng giọng nói tiếng Việt (`PhoWhisper` hoặc `vietai/ASR wav2vec2-base-vietnamese-250h`) trên toàn bộ các file giả vừa sinh để tính tỷ lệ lỗi từ (**WER**).  
  - Loại bỏ các mẫu bị lặp từ, nuốt chữ hoặc nhiễu hỏng có WER vượt ngưỡng cho phép.  
- **Phân chia tập dữ liệu độc lập người nói (`scripts/split_dataset.py`):**  
  - Chia dữ liệu thành 3 tập: **Train (70%)**, **Dev/Validation (15%)**, và **Eval/Test (15%)**.  
  - **Ràng buộc bắt buộc:** Chia theo `Speaker ID` — một người nói đã xuất hiện trong tập Train (dù là mẫu thật hay mẫu giả nhân bản từ người đó) tuyệt đối không được xuất hiện trong tập Dev và Test.

---

## GIAI ĐOẠN 02: TIỀN XỬ LÝ TÍN HIỆU ÂM THANH & MÔ PHỎNG KÊNH TRUYỀN (PREPROCESSING & AUGMENTATION)

**Mục tiêu Giai đoạn 2:** Loại bỏ hoàn toàn sai lệch kỹ thuật (`Technical Bias`) về tần số lấy mẫu (24kHz/48kHz vs 16kHz) và khoảng lặng đầu/cuối câu giữa các nguồn thu và công cụ TTS, đồng thời huấn luyện độ bền của mô hình trước nén mạng xã hội / viễn thông.

### Bước 2.1. Chuẩn hóa Kênh (`Mono`), Tần số lấy mẫu (`16kHz`) và Định dạng Biên độ

- **Chuyển đổi về Kênh đơn (`Mono Channel Conversion`):** Dùng `librosa` hoặc `torchaudio` chuyển toàn bộ file âm thanh nhiều kênh (Stereo) về 1 kênh duy nhất (Mono) bằng cách lấy trung bình cộng các kênh.  
- **Đồng bộ tần số lấy mẫu về `16.000 Hz` (`Resampling`):** Đưa toàn bộ mẫu âm thanh từ 24 kHz / 44.1 kHz / 48 kHz về đúng chuẩn **16.000 Hz (16-bit PCM WAV/FLAC)** — chuẩn bắt buộc của bộ trích xuất đặc trưng Wav2Vec 2.0 và kiến trúc AASIST.  
- **Chuẩn hóa biên độ (`Z-score / Peak Normalization`):** Chuẩn hóa tín hiệu waveform về trung bình bằng 0, phương sai bằng 1 (`Zero-mean Unit-variance`) hoặc miền giá trị `[-1.0, 1.0]` trên từng đoạn thoại.

### Bước 2.2. Cắt bỏ Khoảng lặng Đầu/Cuối (`Silence Removal`) & Cố định Độ dài 4 giây (`64.000 mẫu`)

- **Loại bỏ khoảng lặng đầu và cuối (`Energy-based Silence Trimming`):** Tính đường bao năng lượng RMS (`frame_length=512, hop_length=160`) và cắt bỏ các đoạn nằm dưới **phân vị thứ 20 (`20th percentile`)** ở phần đầu và phần cuối file để triệt tiêu hiện tượng rò rỉ nhãn do khoảng lặng của người thật tạo ra.  
- **Chuẩn hóa độ dài cố định 4 giây (`64.000 sample points` tại 16 kHz):**  
  - Nếu file sau khi cắt khoảng lặng dài hơn 4 giây (`> 64.000 mẫu`): lấy mẫu ngẫu nhiên một đoạn 4 giây (`Random Crop`) trong quá trình Train, và lấy đoạn chính giữa hoặc trượt cửa sổ (`Sliding Window`) khi Inference.  
  - Nếu file ngắn hơn 4 giây (`< 64.000 mẫu`): thực hiện nối lặp lại chính tín hiệu đó (`Repeat Padding`) cho đủ 64.000 mẫu thay vì đệm số 0 (`Zero-padding`) để giữ tính liên tục phổ-thời gian.  
- **Cài đặt chuẩn trong `src/preprocessing/audio_processor.py`:**  
    
  import torch, torchaudio, librosa, numpy as np  
    
  def preprocess\_audio(file\_path, target\_sr=16000, max\_len=64000):  
    
      \# 1\. Load & chuyển về Mono, chuẩn hóa tần số lấy mẫu 16kHz  
    
      wav, sr \= librosa.load(file\_path, sr=target\_sr, mono=True)  
    
        
    
      \# 2\. Cắt khoảng lặng đầu/cuối dựa trên phân vị thứ 20 của năng lượng  
    
      energy \= librosa.feature.rms(y=wav, frame\_length=512, hop\_length=160)\[0\]  
    
      threshold \= np.percentile(energy, 20\)  
    
      valid\_frames \= np.where(energy \> threshold)\[0\]  
    
      if len(valid\_frames) \> 0:  
    
          start \= max(0, valid\_frames\[0\] \* 160\)  
    
          end \= min(len(wav), (valid\_frames\[-1\] \+ 1\) \* 160\)  
    
          wav \= wav\[start:end\]  
    
            
    
      \# 3\. Cố định độ dài 64.000 mẫu (4 giây) bằng Repeat Padding hoặc Crop  
    
      if len(wav) \< max\_len:  
    
          num\_repeats \= int(np.ceil(max\_len / len(wav)))  
    
          wav \= np.tile(wav, num\_repeats)\[:max\_len\]  
    
      else:  
    
          wav \= wav\[:max\_len\]  
    
            
    
      \# 4\. Chuẩn hóa Z-score biên độ  
    
      wav \= (wav \- np.mean(wav)) / (np.std(wav) \+ 1e-8)  
    
      return torch.tensor(wav, dtype=torch.float32)

### Bước 2.3. Tăng cường Dữ liệu (`RawBoost`) & Mô phỏng Nén Codec Zalo / Điện thoại

- **Tăng cường miền thời gian bằng `RawBoost`:** Tích hợp trực tiếp thuật toán RawBoost (gồm 3 nhánh: nhiễu cộng tính phụ thuộc tín hiệu **ISD**, nhiễu xung không phụ thuộc tín hiệu **SSI**, và lọc tích chập tuyến tính/phi tuyến **LnL** \- Algo 3/5) ngay trong `DataLoader` lúc huấn luyện.  
- **Mô phỏng nén Codec mạng xã hội & kênh thoại (`Codec & Bandwidth Simulation`):** Sử dụng `ffmpeg` / `torchaudio` biến đổi ngẫu nhiên (xác suất 50% on-the-fly lúc Train) các mẫu huấn luyện qua các bộ mã hóa nén suy hao:  
  1. Chuẩn nén **Opus** ở bitrate thấp (`16–32 kbps`, mô phỏng luồng tin nhắn thoại Zalo/Telegram).  
  2. Chuẩn nén viễn thông **AMR-NB / AMR-WB** và **GSM**.  
  3. Hạ tần số xuống **8 kHz** rồi nội suy ngược lên **16 kHz** (kết hợp Bandpass filter `300Hz–3400Hz`) để mô phỏng cuộc gọi PSTN/VoIP.  
- **Tách biệt dữ liệu mô phỏng và dữ liệu truyền thực tế:** Quản lý thư mục `data/real_app_test/` chứa tập mẫu kiểm thử được gửi và tải về thực tế qua tính năng tin nhắn thoại của Zalo và Telegram.

---

## GIAI ĐOẠN 03: KIẾN TRÚC MÔ HÌNH & QUY TRÌNH HUẤN LUYỆN CHI TIẾT (MODEL TRAINING PIPELINE \- MUST \#2 / W5)

**Mục tiêu Giai đoạn 3:** Triển khai từ mô hình cơ sở **Baseline AASIST** đến kiến trúc chủ lực **SSL-AASIST (Wav2Vec 2.0 \+ Graph Attention)**, huấn luyện trên GPU Kaggle thông qua `manage_kaggle.py` và lưu checkpoint đạt EER thấp nhất trên tập Dev.

### Bước 3.1. Thiết kế Kiến trúc Mô hình (`src/models/`)

- **Mô hình Cơ sở (`Baseline 1 - AASIST nguyên bản` \- `clovaai/aasist`):**  
  - Đầu vào: Tín hiệu waveform thô kích thước `(batch_size, 1, 64000)`.  
  - Kiến trúc: Lớp tích chập `SincConv` trích xuất đặc trưng phổ-thời gian cấp thấp \-\> mạng `ResNet` 6 khối \-\> mô-đun Mạng chú ý đồ thị không đồng nhất phổ-thời gian (`HS-GAL`) cùng nút `Master Node` \-\> lớp `Fully Connected` xuất 2 logit (`0: Spoof`, `1: Bona fide`).  
- **Mô hình Chủ lực (`Main Model - SSL-AASIST`):**  
  - Thay thế lớp `SincConv` của AASIST bằng bộ trích xuất đặc trưng tự giám sát (`Self-Supervised Learning`) **Wav2Vec 2.0 Front-end** kết hợp phần thân đồ thị **HS-GAL của AASIST Back-end**.  
  - Hỗ trợ cấu hình chạy 2 nhánh thực nghiệm đối chứng:  
    1. Sử dụng `Wav2Vec2-XLS-R` (300M tham số, đa ngôn ngữ).  
    2. Sử dụng backbone tiếng Việt `nguyenvulebinh/wav2vec2-base-vietnamese-250h` (cắt bỏ lớp phân loại ký tự `lm_head` ở cuối, chỉ giữ khối `Wav2Vec2Model`).  
  - Chiếu biểu diễn đầu ra từ tầng Transformer cuối cùng qua lớp `Linear` và đưa thẳng vào phần thân đồ thị `HS-GAL` của AASIST để bắt các dấu vết giả mạo vi mô (`micro-artefacts`).  
- **Tối ưu hóa kiến trúc cho suy luận nhanh (`Student / Compression`):**  
  - Hỗ trợ xuất mô hình sang định dạng **ONNX / TorchScript FP16** hoặc áp dụng Knowledge Distillation nén khối Transformer xuống 8 tầng để đảm bảo thời gian phản hồi `<= 3 giây`.

### Bước 3.2. Thiết lập Hàm mất mát, Bộ tối ưu hóa và Siêu tham số (`Hyperparameters`)

| Thành phần Huấn luyện | Cấu hình Tham số Chi tiết | Mục đích Kỹ thuật |
| :---- | :---- | :---- |
| **Hàm mất mát (Loss Function)** | `Weighted Cross-Entropy Loss` với trọng số `W = [0.1, 0.9]` (`Spoof: 0.1`, `Bona fide: 0.9`) | Xử lý mất cân bằng số lượng mẫu khi tập Spoof (`>= 2.000 mẫu`) gấp đôi tập Bona fide (`>= 1.000 mẫu`), giảm báo động giả. |
| **Bộ tối ưu (Optimizer)** | `Adam` / `AdamW` (`betas=(0.9, 0.98)`, `eps=1e-8`, `weight_decay=1e-4`) | Giữ ổn định đạo hàm khi tinh chỉnh đồng thời cả khối Transformer lớn và mạng đồ thị phía sau. |
| **Tốc độ học (Learning Rate)** | \- Baseline AASIST: `lr = 1e-4` (`Cosine Annealing`) \- SSL-AASIST Fine-tune: `lr = 1e-6` (Cố định / Warm-up) | Learning rate cực nhỏ (`1e-6`) ngăn hiện tượng quên thảm khốc (`catastrophic forgetting`) các biểu diễn âm học đã học của Wav2Vec 2.0. |
| **Batch Size & Epochs** | `Batch Size = 16` hoặc `32` (kèm `Gradient Accumulation`); `Epochs = 50–100` (`Early Stopping = 10 epochs`) | Đảm bảo hội tụ ổn định trên GPU Kaggle, dừng sớm ngay khi EER trên tập Dev ngừng giảm. |
| **Augmentation lúc Train** | `RawBoost (Algo 3/5)` \+ Xác suất `50%` nén Opus/AMR/8kHz on-the-fly | Buộc mô hình nhận diện đúng ngay cả khi âm thanh bị bóp méo qua Zalo/Telegram/VoIP. |

### Bước 3.3. Vòng lặp Huấn luyện 2 Pha & Điều khiển Huấn luyện trên Kaggle GPU

- **Quy trình 2 pha trong `train.py`:**  
  1. **Giai đoạn Khởi động (`Warm-up Phase` – 3 đến 5 Epoch đầu):** Đóng băng (`Freeze`) toàn bộ trọng số của khối Front-end Wav2Vec 2.0, chỉ mở khóa huấn luyện phần Back-end đồ thị AASIST và lớp phân loại cuối với `lr = 1e-4`.  
  2. **Giai đoạn Tinh chỉnh Toàn mạng (`Joint Fine-tuning Phase`):** Mở khóa (`Unfreeze`) toàn bộ các tầng Transformer của Wav2Vec 2.0, hạ Learning Rate toàn cục xuống `lr = 1e-6` và huấn luyện đồng thời cả Front-end lẫn Back-end kết hợp `RawBoost` \+ `Codec Augmentation`.  
  3. **Kiểm định & Lưu Checkpoint theo EER:** Sau mỗi epoch, chạy `model.eval()` trên tập Dev (không bật RawBoost), tính chỉ số `EER`. Chỉ lưu đè file `/kaggle/working/best_model.pt` khi EER trên tập Dev đạt mức thấp kỷ lục mới.  
- **Khung mã chuẩn trong `train.py`:**  
    
  import os, torch, torch.nn as nn  
    
  from torch.optim import Adam  
    
  device \= torch.device('cuda' if torch.cuda.is\_available() else 'cpu')  
    
  model \= SSLAASISTModel(ssl\_pretrained='nguyenvulebinh/wav2vec2-base-vietnamese-250h').to(device)  
    
  weights \= torch.FloatTensor(\[0.1, 0.9\]).to(device)  \# \[Spoof, Bona fide\]  
    
  criterion \= nn.CrossEntropyLoss(weight=weights)  
    
  optimizer \= Adam(model.parameters(), lr=1e-6, betas=(0.9, 0.98), eps=1e-8, weight\_decay=1e-4)  
    
  best\_eer \= float('inf')  
    
  for epoch in range(1, num\_epochs \+ 1):  
    
      model.train()  
    
      for batch\_x, batch\_y in train\_loader:  
    
          batch\_x, batch\_y \= batch\_x.to(device), batch\_y.to(device)  
    
          optimizer.zero\_grad()  
    
          logits \= model(batch\_x)           \# Output shape: (batch\_size, 2\)  
    
          loss \= criterion(logits, batch\_y)  
    
          loss.backward()  
    
          optimizer.step()  
    
        
    
      \# Đánh giá EER trên tập Dev cuối mỗi Epoch  
    
      dev\_eer \= evaluate\_eer(model, dev\_loader, device)  
    
      if dev\_eer \< best\_eer:  
    
          best\_eer \= dev\_eer  
    
          torch.save(model.state\_dict(), '/kaggle/working/best\_model.pt')  
    
- **Quy trình thực thi qua `manage_kaggle.py`:**  
    
  \# 1\. Cài đặt username Kaggle & thêm dataset  
    
  python manage\_kaggle.py set-user \<username\_kaggle\_cua\_ban\>  
    
  python manage\_kaggle.py add-dataset \<username\_so\_huu\>/\<ten\_dataset\>  
    
  \# 2\. Đẩy code lên Kaggle GPU để huấn luyện  
    
  python manage\_kaggle.py push  
    
  \# 3\. Kiểm tra trạng thái (queued \-\> running \-\> complete)  
    
  python manage\_kaggle.py status  
    
  \# 4\. Tải weights (best\_model.pt) và logs về thư mục ./out/ tại máy local  
    
  python manage\_kaggle.py output

---

## GIAI ĐOẠN 04: ĐÁNH GIÁ CHÉO, TRIỂN KHAI HỆ THỐNG & NGHIỆM THU ĐỀ TÀI (EVALUATION & DEPLOYMENT \- MUST \#3 / W6–W8)

**Mục tiêu Giai đoạn 4:** Kiểm định theo chuẩn ASVspoof trên 3 kịch bản, đóng gói dịch vụ suy luận thời gian thực qua **FastAPI \+ Gradio Web Demo \+ Bot Telegram**, thiết lập **Docker \+ CI**, và xuất đầy đủ bằng chứng nghiệm thu.

### Bước 4.1. Quy trình Đánh giá Chéo 3 Kịch bản (`scripts/eval_eer.py`)

- **Cách tính điểm quyết định và ngưỡng EER:**  
  - Từ vector đầu ra 2 chiều `[s_spoof, s_bonafide]`, tính điểm tin cậy (`Confidence Score / CM Score`) bằng xác suất Softmax của lớp Bona fide hoặc hiệu số LLR.  
  - Quét ngưỡng quyết định `theta` để tìm điểm giao nhau mà tại đó `FAR` (`False Acceptance Rate`) bằng với `FRR` (`False Rejection Rate`) \-\> suy ra **EER (%)**, kết hợp tính **minDCF**, **ROC-AUC** và **Confusion Matrix**.  
- **3 Kịch bản đánh giá bắt buộc:**  
  1. **Kịch bản 1 – Đánh giá Nội bộ (`In-Domain Evaluation`):** Kiểm thử trên tập Test (người nói chưa từng xuất hiện trong tập Train) với mẫu giả từ F5-TTS và VieNeu-TTS ở điều kiện chuẩn (Đích: `EER <= 8%`).  
  2. **Kịch bản 2 – Đánh giá Độ bền Kênh truyền & Nén (`Codec / Social Media Robustness`):** Kiểm thử trên các mẫu đã qua nén Opus, AMR, lọc băng thông 8kHz và tập gửi/nhận thực tế qua Zalo, Telegram; đối sánh mô hình có và không có tăng cường dữ liệu (Đích H1: giảm `>= 30% EER tương đối`).  
  3. **Kịch bản 3 – Đánh giá Công cụ Mới chưa từng thấy (`Out-of-Domain / Unseen TTS`):** Kiểm thử trên tập mẫu giả sinh từ công cụ thứ 3 / RVC (Đích H2: `EER <= 15%`).  
- **Tự động xuất kết quả ra file `benchmarks/eval_metrics.csv` theo đúng cấu trúc cột:**  
    
  experiment\_id,model\_name,augmentation,test\_condition,tts\_generator,eer\_percent,min\_dcf,date\_evaluated

### Bước 4.2. Đóng gói Suy luận Thời gian thực (`FastAPI` / `Gradio` / `Bot Telegram`)

- **Luồng xử lý Inference `<= 3 giây` cho đoạn thoại 5–10 giây (`src/app/`):**  
  1. Khi người dùng tải file ghi âm (5–10s) lên Web Demo (Gradio) hoặc chuyển tiếp tin nhắn thoại vào **Bot Telegram**, đọc luồng byte trực tiếp trên **RAM** (tránh ghi/đọc ổ cứng nhiều lần).  
  2. Chạy tiền xử lý chuẩn hóa 16kHz Mono \+ cắt khoảng lặng (`< 0.2 giây`).  
  3. Chia đoạn thoại thành 1–2 cửa sổ 4 giây (`64.000 mẫu`) đưa vào mô hình chạy song song ở chế độ `torch.inference_mode()` (hoặc `ONNX Runtime`).  
  4. Trung bình cộng điểm số các cửa sổ, so sánh với ngưỡng `theta_EER` để trả về nhãn **`THẬT (BONA FIDE)`** hoặc **`GIẢ (SPOOF)`** kèm **% Độ tin cậy** và báo cáo cảnh báo rủi ro.  
- **Ghi nhận bằng chứng tự động & Ẩn danh 100% (`benchmarks/latency_log.json`):**  
  - Mọi lượt kiểm thử qua API/Bot phải tự động băm nội dung âm thanh bằng `SHA-256` và ghi log theo đúng chuẩn JSON sau:  
      
    {  
      
      "request\_id": "req\_20261016\_001",  
      
      "audio\_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  
      
      "duration\_sec": 6.5,  
      
      "codec\_detected": "opus\_16kbps\_8khz",  
      
      "predicted\_label": "GIA (SPOOF)",  
      
      "confidence\_score": 0.942,  
      
      "latency\_sec": 1.48,  
      
      "timestamp": "2026-11-20T14:30:00Z"  
      
    }  
      
  - Viết script `scripts/benchmark_latency.py` chạy đo tự động **30 lần liên tiếp**, lấy trung vị thời gian phản hồi và xuất ra `benchmarks/latency_benchmark.csv`.

### Bước 4.3. Bảo mật, Kiểm thử Tự động (CI/CD), Docker & Bàn giao Red Team Pilot

- **Áp dụng `>= 2` biện pháp bảo mật bắt buộc (W7):**  
  1. **Mã hóa truyền tải & Tự động xóa file tạm:** Cấu hình TLS/HTTPS và cơ chế tự động xóa hủy dữ liệu âm thanh tạm ngay sau khi suy luận (kết hợp quy tắc **Amazon S3 Lifecycle** khi triển khai trên AWS).  
  2. **Kiểm soát truy cập & Chống lạm dụng API:** Áp dụng **IAM Least Privilege**, giới hạn tần suất gọi API (**Rate Limiting**), và kiểm tra nghiêm ngặt định dạng MIME/kích thước file đầu vào.  
- **Kiểm thử Tự động & Đóng gói:**  
  - Hoàn thiện bộ `pytest` gồm `>= 10 test cases` (`>= 5 tests tự động` chạy trên GitHub Actions CI) và bộ đánh giá `>= 30 tình huống` (trong đó có `>= 10 tình huống` lấy từ các trường hợp hệ thống từng nhận diện sai).  
  - Đóng gói toàn bộ ứng dụng bằng `Dockerfile` sẵn sàng triển khai trên **Amazon EC2 / Amazon ECR** và giám sát qua **AWS CloudWatch**.  
  - Bàn giao đường dẫn Web Demo và Bot Telegram cho **CLB An toàn thông tin HUTECH** đóng vai trò Red Team độc lập kiểm thử thực tế.

---

## DANH SÁCH NGHIỆM THU ĐẦU RA (DEFINITION OF DONE CHECKLIST)

- [ ] **Must \#1 (W4):** Hoàn tất bộ dữ liệu `>= 1.000` mẫu thật (có phiếu Consent \+ VIVOS/CommonVoice) & `>= 2.000` mẫu giả (F5-TTS, VieNeu-TTS) \+ bản nén Opus/AMR/8kHz; chia tập Speaker-Disjoint; viết 3 unit tests trước khi code.  
- [ ] **Must \#2 (W5):** Huấn luyện thành công Baseline AASIST và SSL-AASIST trên Kaggle GPU qua `manage_kaggle.py`; tải `best_model.pt` về `./out/`; xuất bảng đối sánh EER có/không tăng cường vào `benchmarks/eval_metrics.csv`; khởi chạy API FastAPI.  
- [ ] **Must \#3 (W6):** Hoàn thiện giao diện Gradio và Bot Telegram trả nhãn Thật/Giả \+ độ tin cậy trong `<= 3 giây`; ghi log ẩn danh SHA-256 vào `benchmarks/latency_log.json`; vượt qua `>= 10 tests` trên CI và bộ eval `>= 30 tình huống`.  
- [ ] **Pilot & Nghiệm thu (W7–W8):** Đóng gói Docker \+ CI xanh; áp dụng `>= 2` biện pháp bảo mật; đạt đích **In-domain EER \<= 8%**, **Unseen TTS EER \<= 15%**, và **Latency trung vị (30 lần) \<= 3 giây**.