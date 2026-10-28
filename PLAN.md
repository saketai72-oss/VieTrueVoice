# TÀI LIỆU ĐẶC TẢ & KẾ HOẠCH THỰC THI CHO ANTIGRAVITY AGENT (PLAN.md)

## 0. TỔNG QUAN BÀI TOÁN & QUY TẮC BẮT BUỘC CHO AGENT (SYSTEM RULES)

### 0.1. Bài toán Cốt Lõi & Mục Tiêu Nghiệm Thu (Target KPIs & Giả Thuyết)

- **Tên đề tài**: Phát triển ViTrueVoice: Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát (SV: Nguyễn Thành Tài – MSSV: 2380601959).
- **Định vị & Giả thuyết**: Phân loại thật/giả đoạn thoại 5–10s qua kênh nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) cho phụ huynh và người lớn tuổi. Kiểm chứng:
  1. **Giả thuyết H1 (Độ bền nén kênh thoại - CH1)**: Giảm ít nhất $\ge 30\%$ EER tương đối trên tập kiểm thử nén (Opus, AMR-NB, G.711, $8\text{ kHz}$) nhờ tăng cường nén kênh thoại so với baseline không tăng cường.
  2. **Giả thuyết H2 (Độ bền công cụ lạ - CH2 / NFR2)**: Duy trì $\text{EER} \le 15\%$ trên công cụ tổng hợp giọng chưa từng thấy khi huấn luyện (Seen: `F5-TTS` vs. Unseen: `VieNeu-TTS v3 Turbo`).
  3. **Độ chính xác nội bộ (In-domain EER)**: `EER <= 8%` trên tập kiểm thử nội bộ người nói chưa từng thấy (`SPK_0007`).
  4. **Thời gian phản hồi (Latency - NFR1)**: Trung vị thời gian phản hồi $\le 3,0$ giây cho đoạn thoại 5–10 giây (bấm giờ lặp 30 lần).

### 0.2. Quy Tắc Phát Triển & Vận Hành Bắt Buộc Cho Agent

1. **Quy tắc TDD (Test-Driven Development)**: Bắt buộc viết kịch bản kiểm thử (`pytest`) trước khi viết mã nguồn thực thi. Toàn bộ **44/44 unit tests** hiện tại phải vượt qua $100\%$ trước mỗi commit.
2. **Quy ước Git Commit**: Mọi bản commit có sự hỗ trợ của AI bắt buộc gắn tiền tố `[AI]` ở đầu thông điệp commit.
3. **Quy trình Huấn luyện Hybrid (Local Code <-> Kaggle GPU)**:
   - Phát triển mã nguồn, viết unit tests và quản lý toàn bộ dự án tại máy Local.
   - Điều khiển đẩy dữ liệu và kịch bản `train.py` / `train.ipynb` lên GPU miễn phí của Kaggle (Tesla T4 16GB) qua CLI `manage_kaggle.py`:
     - Dữ liệu đọc từ: `/kaggle/input/<ten-dataset>`
     - Checkpoint và log lưu tại: `/kaggle/working/best_model.pt`
     - Tải kết quả về máy Local: `./out/`
4. **Đạo đức Dữ liệu & Bảo mật Sinh trắc học (Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP)**:
   - Triệt tiêu PII: Tuyệt đối không lưu tên thật hoặc thông tin định danh cá nhân; bắt buộc mã hóa ẩn danh `SPK_XXXX`.
   - Xử lý in-memory trên RAM: Đọc luồng byte trực tiếp (`io.BytesIO`) và xóa hủy ngay tệp âm thanh tạm sau khi suy luận.
   - Băm ẩn danh SHA-256: Mọi bản ghi trong `benchmarks/latency_log.json` bắt buộc băm SHA-256 nội dung âm thanh.
   - Cam kết xóa hủy: Toàn bộ dữ liệu sinh trắc học gốc sẽ được xóa hủy vĩnh viễn sau khi bảo vệ đồ án (12/2026).

### 0.3. Cấu Trúc Thư Mục Chuẩn Của Dự Án

```
VieTrueVoice/
├── PLAN.md                        # Kế hoạch thực thi chi tiết cho Antigravity Agent
├── README.md                      # Bảng chỉ số Trước - Sau & thông tin đề tài
├── howtorun.md                    # Hướng dẫn chạy Kaggle Hybrid, test & server
├── AGENTS.md                      # Bối cảnh agent, quy tắc phiên, stubborn facts
├── manage_kaggle.py               # CLI điều khiển Kaggle GPU (push/status/output)
├── train.py / train.ipynb         # Entry-point huấn luyện mô hình 2 pha trên Kaggle GPU
├── requirements.txt               # Thư viện phụ thuộc
├── Dockerfile                     # Đóng gói container Docker (EC2 / ECR)
├── .github/workflows/ci.yml       # Pipeline CI tự động chạy 31/31 unit tests
├── data/
│   ├── raw/                       # Giọng thật gốc 5 tình nguyện viên SPK_XXXX + VIVOS + Common Voice
│   ├── bonafide_ref/              # Mẫu tham chiếu 3.5s-7.5s (allow_stitching=False)
│   ├── spoof_f5tts/               # Mẫu giả F5-TTS-Vietnamese (Seen TTS #1)
│   ├── spoof_vieneu/              # Mẫu giả VieNeu-TTS v3 Turbo 48kHz (Seen #2 / Unseen TTS)
│   ├── spoof_unseen/              # Mẫu giả công cụ thứ 3 / RVC (OOD Eval)
│   ├── real_app_test/             # Mẫu gửi/nhận thực tế qua Zalo, Telegram
│   └── manifests/                 # 5 file manifest 18 cột: train, dev, test_indomain, test_ood, full
├── src/
│   ├── vitruevoice/               # Pipeline sinh mẫu giả kép, 4 cổng lọc, profiler, text_utils, batch processor
│   ├── preprocessing/             # Chuẩn hóa 16kHz mono, EBU R128, P20 silence trim, RawBoost, Codec
│   ├── models/                    # Baseline LFCC+GMM, AASIST SincConv, SSL-AASIST (wav2vec 2.0 + HS-GAL)
│   ├── training/                  # Dataset, DataLoader, Dynamic Weighted CE Loss, Vòng lặp 2 pha
│   ├── evaluation/                # Tính toán EER, minDCF, ROC-AUC, DET Curve, Confusion Matrix
│   └── app/                       # FastAPI server (/api/v1/predict), Gradio UI (<=3 thao tác), Telegram Bot
├── scripts/
│   ├── generate_spoof.py          # Script sinh mẫu giả
│   ├── filter_asr_wer.py          # Script lọc ASR WER
│   ├── split_dataset.py           # Chia tập Speaker-Disjoint & Text-Disjoint xuất manifest 18 cột
│   ├── verify_kaggle_output.py    # Kiểm tra toàn diện 18 cột, speaker-disjoint, text-disjoint, paired triplets
│   ├── detect_shortcuts.py        # Bộ dò shortcut quang phổ (>7kHz, tỷ lệ khoảng lặng)
│   ├── eval_eer.py                # Đánh giá EER/minDCF xuất benchmarks/eval_metrics.csv
│   └── benchmark_latency.py       # Bấm giờ 30 lần xuất benchmarks/latency_benchmark.csv
├── benchmarks/
│   ├── eval_metrics.csv           # Bảng theo dõi EER, minDCF có/không tăng cường nén
│   ├── latency_log.json           # Log độ trễ ẩn danh băm SHA-256
│   └── latency_benchmark.csv      # Bảng 30 lần bấm giờ lấy trung vị
├── out/                           # Trọng số best_model.pt và manifests tải từ Kaggle về
└── tests/                         # Bộ kiểm thử TDD (44/44 tests xanh 100%)
```

---

## BẢNG TỔNG QUAN KIẾN TRÚC PIPELINE KỸ THUẬT (4 CHẶNG)

| Chặng Kỹ Thuật | Đầu Vào (Input) | Xử Lý Cốt Lõi (Core Process) | Đầu Ra (Output) |
| :--- | :--- | :--- | :--- |
| **1. Tạo & Chuẩn bị Dữ liệu (Must #1 - W3, W4)** | Giọng thật (5 tình nguyện viên `SPK_0001`..`0007` + VIVOS 65 spk & Common Voice 8.0 419 spk) + Văn bản kịch bản | Phân hoạch V12/V14/V20; clip đơn 3.5–7.5s (`allow_stitching=False`); sinh kép `DUAL_OUTPUT` (F5-TTS & VieNeu-TTS v3 Turbo $48\text{ kHz}$); lọc 4 cổng (Gate 1–4 Label-Free Prosody); Hard Text-Disjoint; TelephonyCompressor | $\ge 1.000$ mẫu Bona fide + $\ge 2.000$ mẫu Spoof (độc lập $\approx 2:1$) + Manifests 18 cột (`pre_codec`), Paired Triplets 1:1:1 cho Eval |
| **2. Tiền xử lý & Augmentation (W4, W5)** | File âm thanh thô đa định dạng ($24\text{ kHz}$ / $48\text{ kHz}$ / $16\text{ kHz}$, Stereo/Mono) | Chuyển Mono, Resample $16\text{ kHz}$, chuẩn hóa EBU R128 (-23 LUFS) / Z-score, cắt khoảng lặng (20th percentile), Cắt/Đệm 4s (64.000 mẫu), RawBoost + Nén Opus/AMR-NB/G.711/lọc $8\text{ kHz}$ | Tensor Waveform chuẩn hóa $(1, 64000)$ mô phỏng lệch miền (domain shift) qua Zalo/PSTN/GSM |
| **3. Huấn luyện & Đối chứng (Must #2 - W5)** | Batch Tensor Waveform $(1, 64000)$ + Nhãn (`0`: Spoof, `1`: Bona fide) | Fine-tune wav2vec 2.0 (có vs. không tăng cường nén kênh; Seen F5-TTS vs. Unseen VieNeu-TTS) & Baseline LFCC+GMM / AASIST với Dynamic Weighted CE $w_c = \frac{N}{2 \cdot N_c}$ | Trọng số `best_model.pt` + Bảng so sánh EER & minDCF có/không tăng cường nén kênh |
| **4. Đánh giá, Triển khai & Pilot (Must #2, #3 - W5–W8)** | Đoạn thoại nghi ngờ (5–10s) từ Web Gradio hoặc chuyển tiếp qua Bot Telegram | Suy luận qua FastAPI trên AWS EC2 + Log ẩn danh SHA-256; $\ge 10$ test case (44/44 unit tests xanh), bộ eval $\ge 30$ tình huống; Pilot với CLB ATTT HUTECH | Giảm $\ge 30\%$ EER tập nén (H1), EER Unseen TTS $\le 15\%$ (H2), Trung vị độ trễ $\le 3$ giây (30 lần đo) |

---

## GIAI ĐOẠN 01: CHUẨN BỊ DỮ LIỆU GỐC & QUY TRÌNH SINH MẪU GIỌNG GIẢ (DATA & SPOOF GENERATION – FROZEN PIPELINE v0.2.3 / KAGGLE V14)

*Thực hiện Must #1 (W3–W4): Xây dựng bộ dữ liệu tiếng Việt chuẩn hóa $\ge 1.000$ mẫu thật, $\ge 2.000$ mẫu giả qua kiến trúc Hai Engine Song Song (`src/vitruevoice/`), kiểm định 4 cổng (Multi-Gate Label-Free Prosody) và tuân thủ Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP.*

### [BƯỚC 1.1] Thu thập Giọng thật (Bona fide), Phân hoạch Chuẩn V12/V14 & Đạo đức Dữ liệu Sinh trắc học

- **Thu thập trực tiếp có Phiếu đồng ý (Consent Form – Phụ lục C.2)**: Chuẩn hóa **5 tình nguyện viên chính thức**: `SPK_0001`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007` (79 câu thoại gốc, loại bỏ hoàn toàn `SPK_0003` và chuyển đổi `SPK_0005` gồm 20 câu từ `.m4a` sang PCM 16-bit $48\text{ kHz}$ Mono WAV; mở rộng $\ge 30$ người nói). Mã hóa ẩn danh `SPK_XXXX`. Tách bạch 3 mục đích trong Phiếu đồng ý: (1) mẫu thật, (2) mẫu tham chiếu nhân bản giọng nghiên cứu, (3) trích xuất chỉ số EER/minDCF ẩn danh. Cam kết xóa hủy vĩnh viễn sau bảo vệ (12/2026).
- **Nguồn dữ liệu mở tiếng Việt đúng giấy phép**: VIVOS (15 giờ, 65 người, CC BY-NC 4.0) và Mozilla Common Voice tiếng Việt (~6–50 giờ, CC0 1.0) tích hợp qua `BatchDatasetProcessor`.
- **Phân hoạch 3 tập con độc lập chống rò rỉ dữ liệu (`DatasetPartitioner` – Chuẩn V12/V14)**:
  1. **Tập ứng viên tham chiếu** $\mathcal{D}_{\text{ref\_cands}}$ (`ref_pool = files[:3]`): Dùng để chọn clip reference cho TTS.
  2. **Tập đăng ký sinh trắc** $\mathcal{D}_{\text{enroll}}$ (`enroll_pool = files[3:7]`): Gồm đúng $K=4$ câu sạch tính vector **Enrollment Centroid chuẩn hóa $L_2$** bằng SpeechBrain `spkrec-ecapa-voxceleb` (192 chiều):
     $$\mathbf{e}_{\text{enroll}} = \frac{\sum_{i=1}^4 \mathbf{e}_i}{\left\|\sum_{i=1}^4 \mathbf{e}_i\right\|_2}$$
  3. **Tập kiểm thử** $\mathcal{D}_{\text{eval}}$: Gồm các câu held-out còn lại, bảo toàn câu hội thoại tự nhiên `SPK_0004_02.wav` ($4.76\text{s}$) thay vì trượt vào câu kịch bản tổng đài.
- **Chống học lệch (Anti-Shortcut Learning)**: Không dùng dữ liệu mạng xã hội nhiều tạp âm (như Vietnam-Celeb) làm đầu vào TTS; chuẩn hóa độ to **EBU R128** (target $-23\text{ LUFS}$) và tắt watermark ngầm (`apply_watermark=False`).

### [BƯỚC 1.2] Tuyển chọn Clip đơn Dải vàng ($3.5\text{s}$–$7.5\text{s}$) & Sinh Giọng giả Kép (`ViTrueVoiceDualPipeline`)

- **Tuyển chọn mẫu tham chiếu 2 tầng không ghép nối (`allow_stitching=False`)**: Cố định dải vàng `min_dur=3.5s`, `max_dur=7.5s`. Tắt ghép nối nhân tạo để tránh chèn 0.2s khoảng lặng làm gãy token âm học của NeuCodec + Qwen LLM.
  1. *LOO Centroid Proximity*: Lọc top-3 clip điển hình trong `ref_pool`.
  2. *Output Probe Ranking*: Sinh thử đầu ra thực tế chọn `best_ref`.
- **Chế độ Sinh Kép Toàn Diện (`PipelineMode.DUAL_OUTPUT`)**: Hỗ trợ `BEST_QUALITY`, `ADAPTIVE` (GPU 4GB VRAM $< 2.5\text{ GB}$), và `DUAL_OUTPUT` (Kaggle T4 16GB kích hoạt cả F5-TTS và VieNeu-TTS, đã sinh **200 mẫu spoof gốc** V8–V14: 106 F5-TTS + 94 VieNeu-TTS).
- **Đặc tả Engine #1 – `F5-TTS-Vietnamese` (Flow Matching + Vocos)**: Chuẩn hóa chữ thường, giữ dấu câu, kịch bản chuyển tiền gấp 5–10s (loại $< 1\text{s}$ hoặc $> 30\text{s}$). Nhận cặp `(ref_audio, ref_text)` động; tự động nhận diện từ sóng âm bằng ASR trong 0.2s (**Label-Free ASR Auto-Fallback**). Peak Headroom Scaling $\le 0.95$. Đạt 5/5 speaker $100\%$, Mean WER $6.26\%$, Mean Sim $0.8008$, Gate 3 Pass $100\%$.
- **Đặc tả Engine #2 – `VieNeu-TTS v3 Turbo` (Qwen LLM + `MOSS_48kHz`)**: Chốt cố định v3 Turbo ($48\text{ kHz}$ PCM), nhanh hơn v2 GPU 6.7 lần ($2.7\text{s}$ vs $18.1\text{s}$) và Sim Ref cao hơn ($0.7231$ vs $0.6556$). Preset A (`use_ref_codes=True`), `denoise=False`, `apply_watermark=False`, `temperature=0.60`, `top_p=0.90`, Headroom $\le 0.95$, văn bản $\le 250$ ký tự. Đạt 4/5 speaker $100\%$, Mean WER $8.47\%$, Mean Sim $0.7108$.
- **Đánh giá Khả năng Tổng quát hóa (Seen vs. Unseen TTS – CH2 / H2 & ADR-3)**:
  1. *Seen TTS (In-Domain)*: Mẫu giả sinh từ `F5-TTS-Vietnamese`.
  2. *Unseen TTS (Out-of-Distribution)*: Mẫu giả sinh từ `VieNeu-TTS v3 Turbo` (kèm công cụ thứ 3 ở mức Could – W6).

```python
# Thực thi Pipeline Sinh Kép (DUAL_OUTPUT) Chuẩn Version 14 (v0.2.3) trên Kaggle GPU
from src.vitruevoice.pipeline import ViTrueVoiceDualPipeline, PipelineMode
from src.vitruevoice.batch_processor import BatchDatasetProcessor

pipeline = ViTrueVoiceDualPipeline(
    f5_config={"vocoder": "vocos", "sample_rate": 24000, "headroom_limit": 0.95},
    vieneu_config={
        "model_id": "pnnbao-ump/VieNeu-TTS-v3-Turbo", "sample_rate": 48000,
        "use_ref_codes": True, "denoise": False, "apply_watermark": False,
        "temperature": 0.60, "top_p": 0.90, "headroom_limit": 0.95
    }
)
processor = BatchDatasetProcessor(
    pipeline=pipeline, mode=PipelineMode.DUAL_OUTPUT, only_pass=True,
    min_dur=3.5, max_dur=7.5, allow_stitching=False
)
processor.run_batch(
    speakers=["SPK_0001", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"],
    seeds=[100, 200, 300],
    codecs=["clean_16khz", "g711_alaw", "amr_nb"],
    manifest_dir="data/manifests/"
)
```

### [BƯỚC 1.3] Kiểm soát Chất lượng 4 Cổng, Nén Viễn thông & Manifest 17 Cột (ADR-3)

- **Bộ lọc chất lượng 4 cổng nghiêm ngặt (`MultiGateEvaluator`) & `Multi-Seed Retry`**:
  1. *Gate 1 – Nội dung ASR (`wav2vec2-base-vietnamese-250h`)*: Clean WER $\le 15\%$, CER $\le 8\%$, `is_catastrophic = False`.
  2. *Gate 2 – Sinh trắc học người nói (`spkrec-ecapa-voxceleb`)*: Cosine Sim so với Centroid ($K=4$) đạt $\text{Sim} \ge T_{\text{spk}}$ (sàn $\ge 0.4905$, shrinkage $\sigma_{\text{pooled}} = 0.08$, trần $0.62$).
  3. *Gate 3 – Sanity tín hiệu*: Không NaN/Inf, $\text{RMS} \ge 0.01$, thời lượng $\ge 1.0\text{s}$, $\text{Peak} \le 0.999$.
  4. *Gate 4 – Ngữ điệu & Phương ngữ Thuần Âm học (`dialect_evaluator.py`)*: YIN $F_0$ trên $[65\text{ Hz} - 400\text{ Hz}]$:
     $$\frac{|F_{0,\text{synth}} - F_{0,\text{ref}}|}{F_{0,\text{ref}}} \le 0.30, \quad |\Delta CV_{F0}| \le 0.12, \quad |dF_0/dt| > 25\text{ Hz} \le 0.18, \quad \text{dialect\_score} \ge 0.65$$
  Nếu trượt, `Multi-Seed Retry` tự động thử seed kế tiếp (`200`, `300`) — trung bình 1.4 lần thử/mẫu.
- **Chuỗi mô phỏng suy giảm kênh thoại (`TelephonyCompressor`) & Dịch chuyển Ngưỡng**:
  - `clean_16khz`: 16kHz Mono phòng thu.
  - `g711_alaw`: 8kHz Mono, 64kbps (PSTN/ISDN, 300–3400Hz).
  - `amr_nb`: 8kHz Mono, 12.2kbps (2G/3G GSM) + `opus` (16–32kbps).
  - Băng hẹp 8kHz triệt tiêu hài âm $> 3.4\text{ kHz}$ làm phương sai Impostor tăng ($0.0875 \rightarrow 0.1011$), độ nhạy $d'$ giảm mạnh: G.711 giảm $22.8\%$ ($d'=4.02$) và AMR-NB giảm $25.5\%$ ($d'=3.89$) so với Studio ($d'=5.21$); gây **Narrowband Upward Shift** đẩy $T_{\text{FAR 1\%}}$ từ $0.4800 \rightarrow 0.5958$ (G.711) và $0.6195$ (AMR-NB).
- **Cấu trúc 5 Tệp Manifest 17 Cột & Phân Vùng Speaker-Disjoint**:
  - Lưu tại `data/manifests/` (`train_manifest.csv`, `dev_manifest.csv`, `test_manifest.csv`, `spoof_manifest.csv`, `full_manifest.csv`).
  - 17 cột: `utt_id, audio_path, speaker_id, label, tts_generator, vocoder, codec, split, duration_sec, transcript, wer, cer, ecapa_sim, derived_tier, engine_name, ref_audio_path, seed`.
  - Phân vùng: Train (`SPK_0001, 0004, 0005`), Dev (`SPK_0006`), Test In-domain (`SPK_0007`). Tỷ lệ 70% / 15% / 15% khi mở rộng.
  - Toàn bộ **31/31 unit tests** (`pytest tests/ -v`) vượt qua $100\%$.

---

## GIAI ĐOẠN 02: TIỀN XỬ LÝ TÍN HIỆU ÂM THANH & MÔ PHỎNG KÊNH TRUYỀN (PREPROCESSING & AUGMENTATION)

*Loại bỏ sai lệch kỹ thuật (Technical Bias) và giải quyết bài toán lệch miền (Domain Shift – ADR-2) qua kênh thoại nén Opus, AMR-NB, G.711 A-law, băng tần $8\text{ kHz}$.*

### [BƯỚC 2.1] Chuẩn hóa Kênh (Mono), Tần số Lấy Mẫu (16 kHz) và Biên Độ

- **Chuyển về Mono**: Lấy trung bình cộng các kênh Stereo về 1 kênh duy nhất.
- **Tái lấy mẫu 16.000 Hz**: Đưa mọi mẫu từ 24kHz / 44.1kHz / 48kHz về 16.000 Hz PCM.
- **Chuẩn hóa EBU R128 & Z-score**: Đưa về target $-23\text{ LUFS}$ và chuẩn hóa Z-score trung bình 0, phương sai 1 trên từng đoạn thoại. Tắt watermark âm học.

### [BƯỚC 2.2] Cắt Bỏ Khoảng Lặng Đầu/Cuối & Cố Định Độ Dài 4 Giây (64.000 Mẫu)

- **Cắt khoảng lặng phân vị 20**: Tính RMS (`frame_length=512, hop_length=160`), cắt bỏ phần nằm dưới phân vị thứ 20 ở đầu và cuối file.
- **Cố định 64.000 mẫu**:
  - Dài hơn 4s: Lấy ngẫu nhiên 4s (`Random Crop`) khi Train; cắt chính giữa hoặc trượt cửa sổ (`Sliding Window`) khi Inference.
  - Ngắn hơn 4s: Nối lặp lại chính tín hiệu đó (`Repeat Padding`) bằng `np.tile(wav, num_repeats)[:64000]` thay vì đệm số 0.

### [BƯỚC 2.3] Tăng Cường Nén Kênh Thoại & RawBoost (ADR-2)

- **Mô phỏng Codec**: Nén Opus 16–32kbps, AMR-NB 12.2kbps, G.711 A-law 64kbps (bandpass 300–3400Hz) rồi nội suy ngược lên 16kHz.
- **Tăng cường RawBoost**: Áp dụng ngẫu nhiên xác suất 50% trong DataLoader (ISD, SSI, LnL - Algo 3/5).
- **Mở rộng Codec thực tế (Should – W7–W8)**: Thu thập tin nhắn thoại thực tế qua Bot Telegram/Zalo (`data/real_app_test/`).

---

## GIAI ĐOẠN 03: KIẾN TRÚC MÔ HÌNH, THIẾT KẾ ĐỐI CHỨNG & QUY TRÌNH HUẤN LUYỆN (MODEL TRAINING PIPELINE)

*Thực hiện Must #2 (W5): Fine-tune wav2vec 2.0 đối chứng Có vs. Không tăng cường nén kênh và so sánh với Baseline LFCC + GMM / AASIST (ADR-1, Bảng 2.2).*

### [BƯỚC 3.1] Thiết Kế Kiến Trúc Mô Hình & Các Nhánh Đối Chứng (ADR-1, ADR-2)

- **Baseline Cơ sở**: LFCC + GMM (trên CPU) và AASIST nguyên bản (`SincConv` + ResNet 6 khối + `HS-GAL` + `Master Node`).
- **Mô hình Đối chứng cho CH1 / H1**: SSL-AASIST huấn luyện chỉ trên âm thanh sạch (`clean_16khz`).
- **Mô hình Chủ lực ViTrueVoice**: SSL-AASIST (backbone `nguyenvulebinh/wav2vec2-base-vietnamese-250h` hoặc `Wav2Vec2-XLS-R` kết hợp đồ thị `HS-GAL`) huấn luyện với tăng cường nén kênh thoại (Opus, AMR-NB, G.711, 8kHz + RawBoost) để kiểm chứng giả thuyết **H1** (giảm $\ge 30\%$ EER tương đối).
- **Nhánh Đánh giá Khả năng Tổng quát hóa (CH2 / H2)**: Kiểm chứng chuyển giao từ **Seen TTS (F5-TTS)** sang **Unseen TTS (VieNeu-TTS v3 Turbo)** để đạt $\text{EER} \le 15\%$.

### [BƯỚC 3.2] Bảng Thiết Lập Hàm Mất Mát, Bộ Tối Ưu Hóa & Siêu Tham Số

| Thành phần Huấn luyện | Cấu hình Tham số Chi tiết | Mục đích Kỹ thuật trong Đề tài |
| :--- | :--- | :--- |
| **Biến kiểm soát thí nghiệm (Mục 3.5)** | $\bullet$ Biến thay đổi: (a) Có/Không nén kênh thoại; (b) Seen F5-TTS vs. Unseen VieNeu-TTS<br>$\bullet$ Giữ cố định: Kiến trúc mô hình, tập Test, số bước huấn luyện | Đảm bảo tính đối chứng khoa học nghiêm ngặt khi trả lời câu hỏi CH1 và CH2. |
| **Hàm mất mát (Loss Function)** | Weighted Cross-Entropy Loss Động<br>Công thức: $w_c = \frac{N}{2 \cdot N_c}$ chuẩn hóa<br>(Spoof:Bona $\approx 2:1 \implies W \approx [0.33, 0.67]$) | Bù đắp chính xác mất cân bằng số lượng mẫu giữa Spoof và Bona fide. Không dùng đồng thời `WeightedRandomSampler`. |
| **Bộ tối ưu (Optimizer)** | Adam / AdamW<br>$\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-8}$, $\text{Weight Decay} = 10^{-4}$ | Giữ ổn định đạo hàm khi tinh chỉnh đồng thời cả khối Transformer lớn và đồ thị HS-GAL. |
| **Tốc độ học (Learning Rate)** | $\bullet$ Warm-up 3–5 epochs: $lr = 10^{-4}$<br>$\bullet$ Fine-tune wav2vec 2.0: $lr = 10^{-6}$ | Learning rate cực nhỏ ($10^{-6}$) ngăn hiện tượng quên thảm khốc (catastrophic forgetting) các biểu diễn âm học tiền huấn luyện. |
| **Batch Size & Bước huấn luyện** | $\text{Batch Size} = 16$ hoặc $32$ (kèm Gradient Accumulation); cố định 50–100 epochs | Hội tụ ổn định trên GPU Kaggle; lưu `best_model.pt` tại điểm EER + minDCF tối ưu trên tập Dev (`SPK_0006`). |

### [BƯỚC 3.3] Quy Trình Vòng Lặp Huấn Luyện 2 Pha

1. **Pha 1 (Warm-up — 3 đến 5 Epoch đầu)**: Đóng băng (`Freeze`) khối front-end wav2vec 2.0, chỉ mở khóa huấn luyện phần back-end đồ thị AASIST với $lr = 10^{-4}$.
2. **Pha 2 (Joint Fine-tuning — Epoch 6 đến 50–100)**: Mở khóa (`Unfreeze`) toàn bộ các tầng Transformer của wav2vec 2.0, hạ $lr = 10^{-6}$, bật tăng cường nén kênh thoại và RawBoost.
3. **Kiểm định & Checkpoint**: Đánh giá `model.eval()` trên tập Dev (`dev.csv`) cuối mỗi epoch; chỉ lưu đè `/kaggle/working/best_model.pt` khi EER đạt kỷ lục thấp mới.

---

## GIAI ĐOẠN 04: ĐÁNH GIÁ THỰC NGHIỆM, TRIỂN KHAI AWS/DOCKER, KIỂM THỬ & PILOT (GOALS & DELIVERABLES)

*Thực hiện Must #2, #3 & CP6–CP10 (W5–W10): Kiểm định EER/minDCF, triển khai FastAPI + Gradio + Bot Telegram, bảo mật AWS và Pilot với CLB ATTT HUTECH.*

### [BƯỚC 4.1] Giao Thức Đo Lường Trước–Sau, Script Tái Lập & Bộ AI Eval $\ge 30$ Ca

- **Đo mốc 'Trước' ở Tuần W2 (17–23/10/2026)**:
  - *Blind Listening Package*: $\ge 10$ người nghe 20 đoạn thoại thật/giả kèm file khóa giải mã `blind_key_private.csv` để đo tỷ lệ phân biệt thực tế bằng tai người.
  - *Xác minh thủ công*: Bấm giờ $\ge 3$ lần cách xác minh truyền thống (gọi lại / hỏi câu bí mật: 2–5 phút).
- **Script Tái Lập EER & Đường Cong DET (`scripts/eval_eer.py` – US8)**: Quét ngưỡng quyết định $\theta$, xuất EER (%), minDCF và đường DET ra `benchmarks/eval_metrics.csv` cho cả 2 kịch bản:
  1. Đánh giá có vs. không tăng cường nén trên tập nén Opus/AMR-NB/G.711/8kHz (CH1/H1).
  2. Đánh giá chuyển giao từ Seen TTS (F5-TTS) sang Unseen TTS (VieNeu-TTS) (CH2/H2).
- **Bộ AI Eval $\ge 30$ Tình Huống & Kiểm Thử TDD (44/44 Tests)**: Thiết lập bộ đánh giá $\ge 30$ tình huống (trong đó $\ge 10$ tình huống từng nhận diện sai, báo cáo tỷ lệ đạt trước và sau khi sửa); duy trì bộ unit tests 44/44 bài xanh $100\%$ trên CI.

### [BƯỚC 4.2] Triển Khai Dịch Vụ, Hạ Tầng AWS & Bảo Mật

- **Dịch vụ Suy luận Thời Gian Thực $\le 3$ Giây (Must #2, #3 – W5, W6)**:
  - **FastAPI (`/api/v1/predict`)**: Đọc file qua RAM stream, cắt cửa sổ 4s, suy luận song song `torch.inference_mode()`, xóa file tạm ngay.
  - **Web Gradio (US4, NFR4)**: Giao diện tối giản $\le 3$ thao tác cho người lớn tuổi, hiển thị nhãn `THẬT` / `GIẢ MẠO` to rõ kèm thang độ tin cậy.
  - **Bot Telegram**: Tiếp nhận tin nhắn thoại chuyển tiếp, xử lý in-memory và phản hồi trực tiếp trong chat.
  - **Đo Độ Trễ 30 Lần**: Script `scripts/benchmark_latency.py` đo 30 lần liên tiếp lấy trung vị $\le 3,0$ giây lưu `benchmarks/latency_benchmark.csv`. Log ẩn danh SHA-256 ghi nhận vào `benchmarks/latency_log.json`.
- **Hạ Tầng Đám Mây AWS & 2 Biện Pháp Bảo Mật (Gói khóa học A – Bảng 2.3 / CP7 – W7)**:
  1. *Biện pháp 1*: Mã hóa HTTPS/TLS và Server-Side Encryption kèm **Amazon S3 Lifecycle** tự động xóa file tạm ngay sau khi xử lý.
  2. *Biện pháp 2*: Quản lý quyền tối thiểu (**IAM Least Privilege**), giới hạn tần suất gọi (**Rate Limiting**) và kiểm tra định dạng MIME/kích thước file.
  - Ước tính chi phí vận hành cho 100 / 1.000 / 10.000 người dùng qua AWS Pricing Calculator (Bảng 3.4).
- **Kiểm Thử Độc Lập Với Đơn Vị Pilot (CLB An Toàn Thông Tin HUTECH – W7, W8)**:
  - Đơn vị Pilot chính: CLB An toàn thông tin HUTECH (Người liên hệ: Thầy Nguyễn Trọng Minh Hồng Phước; dự phòng: CLB AI HUTECH & ChongLuaDao.vn).
  - Từ W7–W8 (04/12/2026), CLB đóng vai trò Red Team kiểm thử độc lập, tự tạo mẫu giọng giả (có đồng ý) để thử thách hệ thống và ký xác nhận Bảng trước–sau (Bảng 3.3).

### [BƯỚC 4.3] Bảng Tổng Hợp Mục Tiêu Hoàn Thành Đề Tài (Target KPIs, NFRs & Deliverables)

| Hạng mục Mục tiêu | Chỉ số Trước (Baseline ban đầu) | Mục tiêu Hoàn thành (Đích phải đạt) | Bằng chứng Nghiệm thu (Artifacts) |
| :--- | :--- | :--- | :--- |
| **1. Độ bền trên âm thanh đã nén (CH1 / H1)** | $\bullet$ Tai người: đo $\ge 10$ người $\times$ 20 đoạn ở W2<br>$\bullet$ Baseline không tăng cường nén (W4–W6) | **Giảm ít nhất $30\%$ EER tương đối** trên tập nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) nhờ tăng cường nén kênh thoại | Script `scripts/eval_eer.py`, bảng đối sánh EER/minDCF trong `benchmarks/eval_metrics.csv` |
| **2. Độ bền trước công cụ TTS chưa thấy (CH2 / H2 / NFR2)** | Mô hình giảm chất lượng khi gặp công cụ tổng hợp giọng mới ngoài tập huấn luyện | Duy trì **$\text{EER} \le 15\%$** trên giọng giả sinh từ Unseen TTS (`VieNeu-TTS v3 Turbo` / công cụ thứ 3) kèm minDCF & DET curve | Báo cáo đánh giá chéo TTS (W6) và tệp kết quả `benchmarks/eval_metrics.csv` |
| **3. Thời gian phản hồi (Latency - NFR1)** | Xác minh thủ công (gọi lại / hỏi câu bí mật): 2–5 phút (bấm giờ $\ge 3$ lần ở W2) | **Trung vị thời gian phản hồi $\le 3,0$ giây** cho đoạn thoại 5–10 giây (đo lặp 30 lần) | File log ẩn danh SHA-256 `benchmarks/latency_log.json` và bảng 30 lần đo `benchmarks/latency_benchmark.csv` |
| **4. Bộ dữ liệu & Đạo đức Sinh trắc học (Must #1 - NFR3)** | Dữ liệu rời rạc, giọng nói sinh trắc học nhạy cảm cần bảo vệ theo Luật 91/2025/QH15 | $\ge 5$–$30$ người nói có Phiếu đồng ý (`SPK_XXXX`) + VIVOS 65 spk & Common Voice 8.0 419 spk ($\ge 1.000$ thật, $\ge 2.000$ giả đạt 4 cổng, tỷ lệ $\approx 2:1$); $100\%$ log ẩn danh; xóa dữ liệu sau bảo vệ | Mẫu Phiếu đồng ý (Phụ lục C.2), 5 file manifest 18 cột (W4), cấu hình S3 Lifecycle tự xóa file tạm |
| **5. Sản phẩm MVP, Tái lập & Pilot (Must #2, #3 - NFR4, NFR5)** | Chưa có công cụ kiểm tra tự động tin nhắn thoại tiếng Việt qua kênh nén cho người cao tuổi | FastAPI + Web Gradio ($\le 3$ thao tác) + Bot Telegram; chạy 1 lệnh Docker; CI chạy 44/44 TDD tests xanh; AI Eval $\ge 30$ ca; Pilot CLB ATTT | Repo GitHub hoàn chỉnh, `Dockerfile`, GitHub Actions CI, Bảng chi phí AWS (100/1k/10k user) & Biên bản xác nhận Pilot (W8) |

---

## DANH SÁCH NGHIỆM THU ĐẦU RA (DEFINITION OF DONE CHECKLIST)

- [x] **Must #1 (W3–W4 / Frozen Pipeline V14 & V20)**: Hoàn tất bộ dữ liệu 5 tình nguyện viên (`SPK_0001`..`0007`) có Phiếu đồng ý + VIVOS (65 người nói) & Common Voice 8.0 (22.97h, 419 người nói); sinh kép F5-TTS và VieNeu-TTS v3 Turbo; lọc 4 cổng (Gate 1–4 Label-Free Prosody); TelephonyCompressor; xuất 5 tệp manifest 18 cột (`pre_codec`) chia Speaker-Disjoint & Hard Text-Disjoint; Paired Triplets 1:1:1 cho eval; 44/44 unit tests TDD xanh 100%.
- [ ] **Must #2 (W5)**: Huấn luyện thành công Baseline LFCC+GMM / AASIST và SSL-AASIST trên Kaggle GPU qua `manage_kaggle.py`; tải `best_model.pt` về `./out/`; kiểm chứng 2 nhánh đối chứng (H1: có vs. không nén kênh; H2: Seen F5-TTS vs. Unseen VieNeu-TTS); xuất kết quả vào `benchmarks/eval_metrics.csv`; khởi chạy API FastAPI.
- [ ] **Must #3 (W6)**: Hoàn thiện giao diện Gradio ($\le 3$ thao tác) và Bot Telegram trả nhãn Thật/Giả + độ tin cậy trong $\le 3$ giây; ghi log ẩn danh SHA-256 vào `benchmarks/latency_log.json`; vượt qua 44/44 tests trên CI và bộ eval $\ge 30$ tình huống.
- [ ] **Pilot & Nghiệm thu (W7–W8)**: Đóng gói Docker trên AWS EC2, S3 Lifecycle tự xóa, IAM least privilege, CloudWatch; đạt đích **In-domain EER <= 8%**, **H1: Giảm >= 30% EER trên tập nén**, **H2: Unseen TTS EER <= 15%**, và **Latency trung vị (30 lần) <= 3,0 giây**; ký biên bản xác nhận nghiệm thu Pilot cùng CLB An toàn thông tin HUTECH.