# TÀI LIỆU KỸ THUẬT THỰC THI ĐỀ TÀI: VITRUEVOICE (SV: NGUYỄN THÀNH TÀI - 2380601959)
## PHÁT TRIỂN VITRUEVOICE: HỆ THỐNG PHÁT HIỆN GIỌNG NÓI GIẢ TIẾNG VIỆT QUA KÊNH THOẠI NÉN DỰA TRÊN HỌC BIỂU DIỄN TỰ GIÁM SÁT

> **Định vị & Giả thuyết:** Phân loại thật/giả đoạn thoại 5–10s qua kênh nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) cho phụ huynh và người lớn tuổi. Kiểm chứng **H1** (giảm $\ge 30\%$ EER tương đối trên tập nén nhờ tăng cường nén kênh), **H2** ($\text{EER} \le 15\%$ trên công cụ TTS chưa thấy: Seen F5-TTS vs. Unseen VieNeu-TTS) và thời gian phản hồi trung vị $\le 3$ giây.

---

## BẢNG TỔNG QUAN KIẾN TRÚC PIPELINE KỸ THUẬT

| Chặng Kỹ Thuật | Đầu Vào (Input) | Xử Lý Cốt Lõi (Core Process) | Đầu Ra (Output) |
| :--- | :--- | :--- | :--- |
| **1. Tạo & Chuẩn bị Dữ liệu (Must #1 - W3, W4)** | Giọng thật (5 tình nguyện viên chính thức `SPK_0001`..`0007` có Phiếu đồng ý + mở rộng VIVOS & Common Voice) + Văn bản kịch bản | Phân hoạch chuẩn V12/V14 (`ref_pool[:3]`, `enroll_pool[3:7]`); chọn clip đơn 3.5–7.5s (`allow_stitching=False`) qua LOO + Probe; sinh kép `DUAL_OUTPUT` bằng F5-TTS (`ref_text` động + ASR fallback 0.2s) & VieNeu-TTS v3 Turbo ($48\text{ kHz}$, `denoise=False`); lọc 4 cổng (Gate 1–4 Label-Free Prosody) + Multi-Seed Retry; nén G.711/AMR-NB/Opus | $\ge 1.000$ mẫu Bona fide + $\ge 2.000$ mẫu Spoof (đạt chuẩn 4 Gates, đã sinh 200 mẫu gốc V8–V14) + 5 file Manifest 17 cột chia Speaker-Disjoint |
| **2. Tiền xử lý & Augmentation (W4, W5)** | File âm thanh thô đa định dạng ($24\text{ kHz}$ / $48\text{ kHz}$ / $16\text{ kHz}$, Stereo/Mono) | Chuyển Mono, Resample $16\text{ kHz}$, chuẩn hóa EBU R128 / Z-score, cắt khoảng lặng (20th percentile), Cắt/Đệm 4s (64.000 mẫu), RawBoost + Nén Opus/AMR-NB/G.711/lọc $8\text{ kHz}$ | Tensor Waveform chuẩn hóa $(1, 64000)$ mô phỏng lệch miền (domain shift) qua Zalo/PSTN/GSM |
| **3. Huấn luyện & Đối chứng (Must #2 - W5)** | Batch Tensor Waveform $(1, 64000)$ + Nhãn (`0`: Spoof, `1`: Bona fide) | Fine-tune wav2vec 2.0 (có vs. không tăng cường nén kênh; Seen F5-TTS vs. Unseen VieNeu-TTS) & Baseline LFCC+GMM / AASIST với Weighted CE Loss | Trọng số `best_model.pt` + Bảng so sánh EER & minDCF có/không tăng cường nén kênh |
| **4. Đánh giá, Triển khai & Pilot (Must #2, #3 - W5–W8)** | Đoạn thoại nghi ngờ (5–10s) từ Web Gradio hoặc chuyển tiếp qua Bot Telegram | Suy luận qua FastAPI trên AWS EC2 + Log ẩn danh SHA-256; $\ge 10$ test case (31/31 unit tests xanh), bộ eval $\ge 30$ tình huống; Pilot với CLB ATTT HUTECH | Giảm $\ge 30\%$ EER tập nén (H1), EER Unseen TTS $\le 15\%$ (H2), Trung vị độ trễ $\le 3$ giây (30 lần đo) |

---

## GIAI ĐOẠN 01: CHUẨN BỊ DỮ LIỆU GỐC & QUY TRÌNH SINH MẪU GIỌNG GIẢ (DATA & SPOOF GENERATION – FROZEN PIPELINE v0.2.3 / KAGGLE V14)

*Thực hiện Must #1 (W3–W4): Xây dựng bộ dữ liệu tiếng Việt chuẩn hóa $\ge 1.000$ mẫu thật, $\ge 2.000$ mẫu giả qua kiến trúc Hai Engine Song Song (`src/vitruevoice/`), kiểm định 4 cổng (Multi-Gate Label-Free Prosody) và tuân thủ Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP.*

### [BƯỚC 1.1] Thu thập Giọng thật (Bona fide), Phân hoạch Chuẩn V12/V14 & Đạo đức Dữ liệu Sinh trắc học

* **Thu thập trực tiếp có Phiếu đồng ý (Consent Form – Phụ lục C.2):** Thực hiện thu âm từ các tình nguyện viên có ký Phiếu đồng ý hợp lệ (theo hướng dẫn của GVHD ngày 23/10/2026 cho phép thu từ $\ge 5$ người trở lên kết hợp dữ liệu mở; hiện đã hoàn tất chuẩn hóa **5 tình nguyện viên chính thức**: `SPK_0001`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007` với 79 câu thoại gốc/mô hình, đã loại bỏ hoàn toàn `SPK_0003` và chuyển đổi `SPK_0005` gồm 20 câu từ định dạng `.m4a` sang chuẩn PCM 16-bit $48\text{ kHz}$ Mono WAV; hướng tới mở rộng $\ge 30$ người nói). Mã hóa ẩn danh toàn bộ người nói thành `SPK_XXXX` (tuyệt đối không lưu tên thật lên repo công khai). Phiếu đồng ý tuân thủ Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 và Nghị định 356/2025/NĐ-CP, tách biệt rõ 3 mục đích:
  1. Thu âm làm mẫu giọng thật (bona fide).
  2. Dùng làm mẫu tham chiếu để sinh giọng nhân bản (spoof) bằng F5-TTS và VieNeu-TTS cho đồ án ViTrueVoice.
  3. Trích xuất chỉ số EER, minDCF, ECAPA Similarity ẩn danh trong báo cáo.
  *Cam kết xóa hủy vĩnh viễn toàn bộ dữ liệu sinh trắc nguyên bản sau khi bảo vệ đồ án (tháng 12/2026).*
* **Nguồn dữ liệu mở tiếng Việt đúng giấy phép (Clean Speech Corpora):** Sử dụng bộ dữ liệu **VIVOS** (15 giờ, 65 người nói, môi trường thu âm yên tĩnh, giấy phép CC BY-NC 4.0) và **Mozilla Common Voice** tiếng Việt (~6–50 giờ, đa vùng miền Bắc – Trung – Nam, giấy phép CC0 1.0 Public Domain) tích hợp qua `BatchDatasetProcessor` kết hợp cùng tập mẫu tình nguyện viên có phiếu đồng ý để đạt quy mô $\ge 1.000$ mẫu giọng thật và $\ge 2.000$ mẫu giọng giả.
* **Phân hoạch 3 tập con độc lập chống rò rỉ dữ liệu (`DatasetPartitioner` – Chuẩn Version 12 / Version 14):** Trên mỗi người nói, `DatasetPartitioner.partition_speaker_files` phân hoạch nghiêm ngặt danh sách tệp thành 3 tập rời rạc hoàn toàn không giao nhau ($0\%$ data leakage, kiểm chứng qua `test_dataset_partitioner_disjoint`):
  1. **Tập ứng viên tham chiếu $\mathcal{D}_{\text{ref\_cands}}$ (`ref_pool = files[:3]`):** Chỉ dùng để chọn clip reference cho TTS.
  2. **Tập đăng ký sinh trắc $\mathcal{D}_{\text{enroll}}$ (`enroll_pool = files[3:7]`):** Gồm đúng $K=4$ câu thật dài/sạch dùng riêng để tính vector **Enrollment Centroid chuẩn hóa $L_2$** bằng mô hình SpeechBrain `spkrec-ecapa-voxceleb` (192 chiều):
     $$\mathbf{e}_{\text{enroll}} = \frac{\sum_{i=1}^4 \mathbf{e}_i}{\left\|\sum_{i=1}^4 \mathbf{e}_i\right\|_2}$$
  3. **Tập kiểm thử $\mathcal{D}_{\text{eval}}$:** Gồm các câu held-out còn lại. Việc giữ cố định cơ chế phân tập chuẩn của Version 12/14 ngăn chặn hiện tượng dịch chuyển trọng tâm LOO sang các câu chào kịch bản tổng đài viên formal (như `SPK_0004_01.wav` ở Version 13), bảo toàn $100\%$ câu mẫu hội thoại tự nhiên `SPK_0004_02.wav` ($4.76\text{s}$).
* **Quy tắc loại trừ dữ liệu nhiễu nền cao & Chống học lệch (Anti-Shortcut):** Không dùng các bộ dữ liệu thu thập từ mạng xã hội chứa nhiều tạp âm hoặc nhạc nền (như Vietnam-Celeb) làm đầu vào cho công cụ TTS/Voice Cloning; đồng thời chuẩn hóa độ to âm lượng theo chuẩn **EBU R128** (cùng mức target LUFS như $-23\text{ LUFS}$ cho cả tập bona fide và tập spoof) và tắt đóng dấu âm học ngầm (`apply_watermark=False`) để ngăn mô hình phân loại học lệch (shortcut learning) dựa vào biên độ hoặc watermark.

### [BƯỚC 1.2] Tuyển chọn Clip đơn Dải vàng ($3.5\text{s}$–$7.5\text{s}$) & Sinh Giọng giả Kép (`ViTrueVoiceDualPipeline`)

* **Tuyển chọn mẫu tham chiếu 2 tầng trên Dải vàng $3.5\text{s}$–$7.5\text{s}$ (`allow_stitching=False`):** Trong `SpeakerProfiler` và `BatchDatasetProcessor`, hệ thống chốt cố định dải thời lượng vàng `min_dur=3.5s`, `max_dur=7.5s` và tắt hoàn toàn chế độ ghép nối nhân tạo (`allow_stitching=False`). Thực nghiệm ở Version 11–12 chứng minh việc ghép nối câu ngắn (stitching) chèn $0.2\text{s}$ khoảng lặng chết làm gãy chuỗi token âm học của NeuCodec + Qwen LLM và làm mất khóa tra cứu `ref_text`. Toàn bộ 5 tình nguyện viên đều sở hữu các clip câu đơn tự nhiên dài $3.6\text{s}$–$6.8\text{s}$, được tuyển chọn qua 2 tầng:
  1. **LOO Centroid Proximity:** Lọc top-3 clip điển hình nhất trong `ref_pool`.
  2. **Output Probe Ranking:** Sinh thử đầu ra thực tế để chọn `best_ref` (loại bỏ các clip rớt ngưỡng như `SPK_0001_04.wav` có $\text{Sim} = 0.4815 < 0.4905$). Nếu mẫu nguồn có nhiễu nền, lọc nhiễu ồn ít bằng Adobe Podcast Enhance / Facebook Demucs, ồn nhiều bằng UVR5.
* **Chế độ Sinh Kép Toàn Diện (`PipelineMode.DUAL_OUTPUT`) & Đồng bộ SSOT:** Khung mã nguồn chuẩn hóa tại `src/vitruevoice/` (đồng bộ Nguồn Chân Lý Duy Nhất SSOT sang `out/vitruevoice` và `train.ipynb`) hỗ trợ 3 chế độ: `BEST_QUALITY` (thang quyết định 4 bậc), `ADAPTIVE` (định tuyến thông minh cho GPU 4GB VRAM như RTX 3050 để giữ VRAM $< 2.5\text{ GB}$), và `DUAL_OUTPUT`. Trên Kaggle Tesla T4 GPU (16GB VRAM), chế độ `DUAL_OUTPUT` kích hoạt đồng thời cả F5-TTS và VieNeu-TTS cho toàn bộ các speaker, lưu tách biệt vào `data/spoof_f5tts/SPK_xxxx/` và `data/spoof_vieneu/SPK_xxxx/` (tại Kaggle Version 8–14 đã sinh thành công **200 mẫu spoof gốc** chất lượng cao từ 5 tình nguyện viên: 106 mẫu F5-TTS và 94 mẫu VieNeu-TTS).
* **Đặc tả Công cụ TTS #1 – `F5-TTS-Vietnamese` (Non-Autoregressive Flow Matching + ASR Auto-Fallback):** Sử dụng kho mã `nguyenthienhy/F5-TTS-Vietnamese` (checkpoint `F5-TTS-Vietnamese-ViVoice` hoặc `danhtran2mind/Vi-F5-TTS`) kết hợp vocoder **Vocos** và đầu vào tách sạch qua **Demucs $24\text{ kHz}$ Mono**. Văn bản đầu vào chuẩn hóa chữ thường (`lowercase`), bảo tồn trọn vẹn dấu câu tiếng Việt (`.`, `,`, `!`, `?`), mô phỏng kịch bản lừa đảo mạo danh người thân giục chuyển tiền gấp (tai nạn giao thông, cấp cứu viện phí, phong tỏa tài sản) với thời lượng mục tiêu 5–10 giây (lọc cứng loại bỏ file $< 1$ giây hoặc $> 30$ giây). Để chống hiện tượng vỡ căn chỉnh (*alignment collapse*) của Flow Matching, `f5_adapter.py` xóa bỏ hoàn toàn câu fallback cứng và nhận cặp `(ref_audio, ref_text)` động từ transcript thật của `best_ref`; nếu chạy trên tập dữ liệu mở lớn không có nhãn transcript, hàm `transcribe_audio` trong `evaluator.py` tự động nhận diện văn bản từ sóng âm bằng ASR trong $0.2\text{s}$ (**Label-Free ASR Auto-Fallback**). Kết hợp **Peak Headroom Scaling ($\le 0.95$)**, F5-TTS đạt **5/5 speaker hoàn hảo $100\%$** chất giọng và phương ngữ gốc ($\text{Mean WER} = 6.26\%$, `SPK_0005` đạt WER $2.84\%$ và $0.0\%$ ở các câu khẩn cấp, $\text{Mean Sim} = 0.8008$, $\text{Gate 3 Pass} = 100\%$).
* **Đặc tả Công cụ TTS #2 – `VieNeu-TTS v3 Turbo` (Autoregressive Qwen LLM + `MOSS_48kHz` / `NeuCodec`):** Chốt cố định `pnnbao-ump/VieNeu-TTS-v3-Turbo` (kiến trúc Qwen kết hợp `MOSS_48kHz` xuất chuẩn $48\text{ kHz}$ High-Fidelity PCM và bộ phiên âm `sea-g2p` bằng Rust engine); **KHÔNG** chuyển sang bản v2 GPU ($24\text{ kHz}$) do thực nghiệm đối đầu trên 5 speaker chứng minh v3 Turbo có độ giống giọng cao hơn ($0.7231$ vs. $0.6556$ trên Ref; $0.5795$ vs. $0.5505$ trên Held-out) và nhanh hơn $6.7$ lần ($2.7\text{s}$/câu vs. $18.1\text{s}$/câu). Thực hiện Instant Voice Cloning với mẫu tham chiếu $3.5$–$7.5$ giây, giới hạn văn bản $\le 250$ ký tự mỗi lượt gọi để loại trừ ảo giác ngữ âm (*hallucination*). Cấu hình tối ưu tại `vieneu_adapter.py`: truyền trực tiếp Raw $48\text{ kHz}$ PCM, Preset A (`use_ref_codes=True`), `denoise=False` (bảo toàn dải hài âm thanh quản, tránh mất $\sim 0.07$ Cosine Similarity), `apply_watermark=False`, `temperature=0.60`, `top_p=0.90` và Peak Headroom Scaling $\le 0.95$, đạt **4/5 speaker hoàn hảo $100\%$** chất giọng gốc.
* **Thiết lập nguồn sinh cho đánh giá khả năng tổng quát hóa (Seen vs. Unseen TTS – CH2 / H2 & ADR-3):** Để kiểm chứng giả thuyết H2 ($\text{EER} \le 15\%$ trên công cụ TTS chưa thấy) và câu hỏi nghiên cứu CH2 theo ADR-3, bộ dữ liệu phân tách rõ:
  1. **Seen TTS (In-Domain):** Mẫu giả sinh từ công cụ có mặt trong tập huấn luyện (`F5-TTS-Vietnamese`).
  2. **Unseen TTS (Out-of-Distribution - OOD):** Mẫu giả sinh từ công cụ hoàn toàn mới chưa từng xuất hiện khi huấn luyện (`VieNeu-TTS`, kèm mở rộng công cụ thứ 3 ở mức Could – W6 nếu còn thời gian) nhằm chứng minh biểu diễn tự giám sát wav2vec 2.0 không học vẹt dấu vết cục bộ của một bộ vocoder duy nhất.

```python
# Thực thi Pipeline Sinh Kép (DUAL_OUTPUT) Chuẩn Version 14 (v0.2.3) trên Kaggle GPU
from src.vitruevoice.pipeline import ViTrueVoiceDualPipeline, PipelineMode
from src.vitruevoice.batch_processor import BatchDatasetProcessor

# 1. Khởi tạo Dual Pipeline (F5-TTS 24kHz Vocos + VieNeu-TTS v3 Turbo 48kHz Label-Free)
pipeline = ViTrueVoiceDualPipeline(
    f5_config={"vocoder": "vocos", "sample_rate": 24000, "headroom_limit": 0.95},
    vieneu_config={
        "model_id": "pnnbao-ump/VieNeu-TTS-v3-Turbo", "sample_rate": 48000,
        "use_ref_codes": True, "denoise": False, "apply_watermark": False,
        "temperature": 0.60, "top_p": 0.90, "headroom_limit": 0.95
    }
)

# 2. Chạy BatchDatasetProcessor (Dải vàng 3.5s-7.5s, allow_stitching=False, ASR Auto-Fallback,
# lọc 4 cổng Gate 1-4 kèm Multi-Seed Retry và xuất 5 tệp Manifest 17 cột)
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

### [BƯỚC 1.3] Kiểm soát Chất lượng 4 Cổng (Multi-Gate Label-Free Prosody), Nén Viễn thông & Manifest 17 Cột (ADR-3)

* **Bộ lọc chất lượng 4 cổng nghiêm ngặt (`only_pass=True`) & Vòng lặp `Multi-Seed Retry`:** Nhằm khắc phục việc Gate 1 (ASR) và Gate 2 (ECAPA-TDNN vốn chỉ đo hình học thanh quản và mù phương ngữ / *accent-agnostic*) có thể bỏ lọt các mẫu bị lệch ngữ điệu hoặc vỡ giọng khi sinh hàng loạt, `MultiGateEvaluator` tích hợp 4 cổng kiểm định tự động hoàn toàn không phụ thuộc nhãn vùng miền (**Label-Free Architecture**):
  1. **Gate 1 – Nội dung ASR (`wav2vec2-base-vietnamese-250h`):** Chuẩn hóa dấu câu, yêu cầu $\text{Clean WER} \le 15\%$, $\text{CER} \le 8\%$ và không mắc lỗi nghiêm trọng (`is_catastrophic = False`: không vấp lặp hay đứt từ đầu câu).
  2. **Gate 2 – Sinh trắc học người nói (SpeechBrain `spkrec-ecapa-voxceleb`):** Cosine Similarity so với Enrollment Centroid ($K=4$) đạt $\text{Sim} \ge T_{\text{spk}}$ (ngưỡng sàn $\ge 0.4905$; hiệu chuẩn riêng bằng empirical shrinkage $\sigma = \alpha \sigma_{\text{local}} + (1-\alpha)\sigma_{\text{pooled}}$ với $\sigma_{\text{pooled}} = 0.08$ và trần $0.62$).
  3. **Gate 3 – Sanity tín hiệu:** Không chứa NaN/Inf, $\text{RMS} \ge 0.01$, thời lượng $\ge 1.0\text{s}$ và không clipping ($\text{Peak} \le 0.999$ nhờ Peak Headroom Scaling $\le 0.95$).
  4. **Gate 4 – Thẩm định Chất giọng & Ngữ điệu Thuần Âm học (`evaluate_prosodic_consistency` trong `dialect_evaluator.py`):** Trích xuất đường cao độ $F_0$ qua thuật toán **YIN** trên dải $[65\text{ Hz} - 400\text{ Hz}]$, đối chiếu trực tiếp mẫu sinh ra với clip tham chiếu gốc qua độ lệch cao độ tương đối:
     $$\frac{|F_{0,\text{synth}} - F_{0,\text{ref}}|}{F_{0,\text{ref}}} \le 0.30$$
     độ lệch hệ số biến thiên cao độ $|\Delta CV_{F0}| \le 0.12$ (với $CV_{F0} = \frac{\sigma_{F0}}{\mu_{F0}}$) và tỷ lệ bước nhảy cao độ tức thời (**Pitch Jump Rate**: $|dF_0/dt| > 25\text{ Hz} \le 0.18$), yêu cầu điểm tổng hợp `dialect_score >= 0.65`. Nếu seed đầu tiên bị trượt bất kỳ cổng nào, `Multi-Seed Retry` tự động đổi sang seed kế tiếp (`200`, `300`) để phục hồi mẫu (trung bình $1.4$ lần thử/mẫu).
* **Chuỗi mô phỏng suy giảm kênh thoại viễn thông (`TelephonyCompressor`) & Hiện tượng Dịch chuyển Ngưỡng:** Toàn bộ mẫu âm thanh sạch (cả bona fide và spoof) được xử lý qua chuỗi mã hóa/giải mã viễn thông bằng `ffmpeg`:
  1. `clean_16khz`: PCM 16-bit $16\text{ kHz}$ Mono chuẩn phòng thu.
  2. `g711_alaw`: $8\text{ kHz}$ Mono, $64\text{ kbps}$ – chuẩn mạng thoại cố định PSTN/ISDN, dải thông hẹp $300$–$3400\text{ Hz}$.
  3. `amr_nb`: Adaptive Multi-Rate NarrowBand $8\text{ kHz}$ Mono, $12.2\text{ kbps}$ qua `libopencore_amrnb` – chuẩn di động 2G/3G, kết hợp nén **Opus** ($16$–$32\text{ kbps}$).
  Thực nghiệm chứng minh dải thông hẹp $8\text{ kHz}$ triệt tiêu hài âm trên $3.4$–$4.0\text{ kHz}$ làm phân tán phân phối Impostor ($\sigma_I$ tăng từ $0.0875$ lên $0.1011$), khiến chỉ số nhạy phân tách $d'$ suy giảm mạnh **$22.8\%$ (G.711: $d' = 4.02$)** và **$25.5\%$ (AMR-NB: $d' = 3.89$)** so với Studio ($d' = 5.21$), đồng thời gây hiện tượng **Dịch chuyển Ngưỡng (Narrowband Upward Shift)** đẩy $T_{\text{FAR 1\%}}$ từ $0.4800$ lên $0.5958$ (G.711) và $0.6195$ (AMR-NB). Do đó, nhãn `codec` và chỉ số `ecapa_sim`, `raw_wer` được ghi nhận riêng theo từng điều kiện kênh.
* **Cấu trúc 5 Tệp Manifest 17 cột chuẩn tắc & Phân vùng Độc lập Người nói (`Speaker-Disjoint Split` – ADR-3):** Hệ thống tự động xuất 5 tệp manifest tại `data/manifests/` (`train_manifest.csv`, `dev_manifest.csv`, `test_manifest.csv`, `spoof_manifest.csv` và `full_manifest.csv`) theo đúng quy chuẩn 17 cột: `utt_id`, `audio_path`, `speaker_id`, `label` (`bonafide`/`spoof`), `tts_generator` (`none`/`F5-TTS-Vietnamese`/`VieNeu-TTS`), `vocoder` (`bonafide`/`Vocos`/`MOSS_48kHz`), `codec` (`clean_16khz`/`g711_alaw`/`amr_nb`), `split` (`train`/`dev`/`test`), `duration_sec`, `transcript`, `wer`, `cer`, `ecapa_sim`, `derived_tier` (`BonaFide`/`Tier 1 (Strong)`), `engine_name`, `ref_audio_path`, và `seed`. Phân vùng tập dữ liệu độc lập tuyệt đối theo người nói (**Speaker-Disjoint**):
  * **Tập Train:** `SPK_0001`, `SPK_0004`, `SPK_0005`.
  * **Tập Dev:** `SPK_0006` (kiểm soát overfitting và căn chỉnh ngưỡng EER).
  * **Tập Test In-Domain:** `SPK_0007` (người nói chưa từng xuất hiện khi huấn luyện).
  Kết hợp duy trì tỷ lệ $70\%$ Train / $15\%$ Dev / $15\%$ Test khi mở rộng cùng VIVOS và Common Voice. Toàn bộ **31/31 unit tests** (`pytest tests/ -v`) đều vượt qua $100\%$.

| Hạng mục Kiểm định (Đến Kaggle V14 / v0.2.3) | Thông số / Kết quả Thực nghiệm Đạt được | Ý nghĩa Kỹ thuật trong Pipeline ViTrueVoice |
| :--- | :--- | :--- |
| **1. Hiệu năng F5-TTS (`F5TTSAdapter` + ASR Fallback)** | Đạt **5/5 speaker hoàn hảo $100\%$** chất giọng gốc $\cdot$ Mean WER: **$6.26\%$** $\cdot$ Mean CER: **$2.26\%$** $\cdot$ Mean Sim: **$0.8008$** $\cdot$ Gate 3 Pass: **$100\%$ (79/79)** $\cdot$ Overall Pass: **$89.9\%$** (`SPK_0005` đạt WER $2.84\%$, câu khẩn cấp WER $0.0\%$) | Truyền `ref_text` động + Label-Free ASR Auto-Fallback ($0.2\text{s}$) + Peak Headroom Scaling ($\le 0.95$) triệt tiêu hoàn toàn lỗi lệch pha cross-attention. |
| **2. Hiệu năng VieNeu-TTS v3 Turbo (`VieNeuAdapter`)** | Đạt **4/5 speaker hoàn hảo $100\%$** chất giọng gốc $\cdot$ Mean WER: **$8.47\%$** $\cdot$ Mean Sim: **$0.7108$** $\cdot$ Độ trễ: **$2.7\text{s}$/câu** (nhanh hơn v2 GPU **$6.7$ lần**, Sim Ref đạt **$0.7231$** vs. $0.6556$ của v2) | Giữ cố định v3 Turbo ($48\text{ kHz}$ PCM, `denoise=False`, `temperature=0.60`, `top_p=0.90`) làm động cơ sinh song hành và nguồn Unseen TTS đối chứng. |
| **3. Dải vàng $3.5\text{s}$–$7.5\text{s}$, Cổng 4 Prosody & Retry** | Clip đơn tự nhiên $3.5\text{s}$–$7.5\text{s}$ (`allow_stitching=False`) $\cdot$ Cổng 4 YIN $F_0$ ($\text{score} \ge 0.65$, $\Delta F_0 \le 0.30$) $\cdot$ Giảm WER từ **$18.6\%$ xuống $11.0\%$** $\cdot$ Trung bình **$1.4$ lần thử/mẫu** | Khôi phục câu mẫu vàng `SPK_0004_02.wav` ($4.76\text{s}$), thẩm định chất giọng & nhịp điệu hoàn toàn không cần nhãn vùng miền (Label-Free). |
| **4. Suy giảm Kênh thoại Viễn thông ($8\text{ kHz}$)** | Chỉ số nhạy phân tách $d'$ giảm từ **$5.21$ (Studio)** xuống **$4.02$ (G.711, $-22.8\%$)** và **$3.89$ (AMR-NB, $-25.5\%$)** $\cdot$ Ngưỡng $T_{\text{FAR 1\%}}$ dịch chuyển $0.4800 \rightarrow 0.5958 \rightarrow 0.6195$ | Chứng minh thực nghiệm hiện tượng lệch miền kênh nén (CH1) và tính bắt buộc của việc lưu nhãn `codec` trong manifest. |
| **5. Xuất 5 Manifest 17 cột & Kiểm thử TDD (V8–V14)** | Đã sinh **200 mẫu spoof gốc** (106 F5 + 94 VieNeu) $\cdot$ 5 file manifest 17 cột $\cdot$ Train: `SPK 1,4,5` / Dev: `SPK 6` / Test: `SPK 7` $\cdot$ **31/31 TDD unit tests PASS $100\%$** | Đảm bảo $0\%$ data leakage giữa 3 tập (Ref, Enroll, Test) và tự động hóa $100\%$ trên Kaggle T4 GPU qua `manage_kaggle.py`. |

---

## GIAI ĐOẠN 02: TIỀN XỬ LÝ TÍN HIỆU ÂM THANH & MÔ PHỎNG KÊNH TRUYỀN (PREPROCESSING & AUGMENTATION)

*Loại bỏ sai lệch kỹ thuật (Technical Bias) và giải quyết bài toán lệch miền (Domain Shift – ADR-2) qua kênh thoại nén Opus, AMR-NB, G.711 A-law, băng tần $8\text{ kHz}$.*

> **NGUYÊN TẮC CỐT LÕI TRONG TIỀN XỬ LÝ CHỐNG GIẢ MẠO & LỆCH MIỀN (DOMAIN SHIFT):**
> Các công cụ TTS xuất âm thanh ở tần số lấy mẫu khác nhau (VieNeu-TTS xuất $24\text{ kHz}$/$48\text{ kHz}$, F5-TTS xuất $24\text{ kHz}$, trong khi VIVOS là $16\text{ kHz}$) và thường không có khoảng lặng ở đầu/cuối câu như bản thu thật. Đồng thời, khi âm thanh truyền qua Zalo, Messenger hoặc mạng viễn thông PSTN/GSM (G.711 A-law, AMR-NB, Opus), tín hiệu bị nén suy hao và giới hạn băng tần $8\text{ kHz}$ ($300$–$3400\text{ Hz}$) làm xóa mờ các dấu vết giả mạo vi mô và làm suy giảm $22.8\%$–$25.5\%$ chỉ số nhạy phân tách $d'$. Mọi mẫu âm thanh bắt buộc phải đồng bộ hóa và tăng cường nén kênh theo ADR-2.

### [BƯỚC 2.1] Chuẩn hóa Kênh (Mono), Tần số lấy mẫu ($16\text{ kHz}$) và Định dạng biên độ

* **Chuyển đổi về Kênh đơn (Mono Channel Conversion):** Sử dụng thư viện `librosa` hoặc `torchaudio` chuyển toàn bộ file âm thanh nhiều kênh (Stereo) về 1 kênh duy nhất (Mono) bằng cách lấy trung bình cộng các kênh, loại bỏ sự khác biệt về cấu hình thiết bị thu.
* **Đồng bộ tần số lấy mẫu về $16\text{ kHz}$ (Resampling):** Đưa toàn bộ mẫu âm thanh từ $24\text{ kHz}$ / $44.1\text{ kHz}$ / $48\text{ kHz}$ về đúng chuẩn $16.000\text{ Hz}$ (16-bit PCM WAV/FLAC). Tần số $16\text{ kHz}$ là chuẩn bắt buộc của bộ biểu diễn tự giám sát wav2vec 2.0 và kiến trúc AASIST.
* **Chuẩn hóa biên độ & Độ to (EBU R128 / Z-score Normalization):** Áp dụng chuẩn hóa độ to âm lượng **EBU R128** (cùng mức target $-23\text{ LUFS}$ cho cả bona fide và spoof) kết hợp chuẩn hóa tín hiệu waveform về trung bình bằng $0$, phương sai bằng $1$ (Zero-mean Unit-variance) trên từng đoạn thoại để triệt tiêu sự chênh lệch âm lượng giữa các nguồn thu.

### [BƯỚC 2.2] Cắt bỏ khoảng lặng đầu/cuối (Silence Removal) & Cố định độ dài (Padding/Cropping)

* **Loại bỏ khoảng lặng đầu và cuối (Energy-based Silence Trimming):** Tính đường bao năng lượng làm mượt (smoothed energy envelope) của từng file âm thanh và cắt bỏ các đoạn nằm dưới phân vị thứ 20 (20th percentile) ở đầu và cuối file, triệt tiêu hiện tượng rò rỉ nhãn do khoảng lặng của người thật tạo ra.
* **Chuẩn hóa độ dài cố định 4 giây (64.000 mẫu tại $16\text{ kHz}$):** Để đưa vào huấn luyện theo Batch:
  1. Nếu đoạn thoại (5–10 giây) sau khi cắt khoảng lặng dài hơn 4 giây (64.000 mẫu), lấy ngẫu nhiên một đoạn 4 giây (Random Crop) khi Train và trượt cửa sổ (Sliding Window) khi Inference.
  2. Nếu ngắn hơn 4 giây, nối lặp lại chính tín hiệu đó (Repeat Padding) cho đủ 64.000 mẫu thay vì đệm số 0 (Zero-padding).

### [BƯỚC 2.3] Tăng cường nén kênh thoại (Opus, AMR-NB, G.711 A-law, $8\text{ kHz}$) & RawBoost (ADR-2 – Biến thay đổi của CH1)

* **Mô phỏng nén Codec ứng dụng nhắn tin & viễn thông (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$):** Sử dụng `ffmpeg` / `torchaudio` (`TelephonyCompressor`) tạo các bản nén kênh thoại cho cả tập huấn luyện (nhánh tăng cường) và tập kiểm thử:
  1. Nén codec **Opus** ở bitrate thấp ($16$–$32\text{ kbps}$, mô phỏng tin nhắn thoại Zalo, Messenger, Telegram).
  2. Nén codec **AMR-NB** ($8\text{ kHz}$ mono, $12.2\text{ kbps}$ qua `libopencore_amrnb` dùng trong mạng di động 2G/3G GSM).
  3. Nén codec **G.711 A-law** ($8\text{ kHz}$ mono, $64\text{ kbps}$ dùng trong mạng điện thoại cố định PSTN/ISDN) và lọc giới hạn băng tần $8\text{ kHz}$ (Bandpass $300\text{ Hz}$–$3400\text{ Hz}$) rồi nội suy ngược lên $16\text{ kHz}$.
* **Tăng cường miền thời gian bằng RawBoost:** Kết hợp thuật toán **RawBoost** (nhiễu cộng tính phụ thuộc tín hiệu ISD, nhiễu xung SSI và lọc tích chập LnL theo Tak et al., Odyssey 2022 [3]) ngay trong `DataLoader` lúc huấn luyện để tăng độ bền biểu diễn âm học.
* **Mở rộng Codec & Kiểm thử truyền thực tế (Mức Should – W7–W8):** Ngoài các bản nén mô phỏng, thu thập thêm các đoạn thoại truyền thực tế qua tính năng chuyển tiếp tin nhắn thoại của Bot Telegram/Zalo và thử thêm codec khác ngoài Opus/AMR/G.711 nếu còn thời gian.

```python
# Pipeline Tiền xử lý chuẩn hóa tín hiệu âm thanh (Python / Torchaudio / Librosa)
import torch, torchaudio, librosa, numpy as np

def preprocess_audio(file_path, target_sr=16000, max_len=64000):
    # 1. Load & chuyển về Mono, chuẩn hóa tần số lấy mẫu 16kHz
    wav, sr = librosa.load(file_path, sr=target_sr, mono=True)
    
    # 2. Cắt khoảng lặng đầu/cuối dựa trên phân vị thứ 20 của năng lượng
    energy = librosa.feature.rms(y=wav, frame_length=512, hop_length=160)[0]
    threshold = np.percentile(energy, 20)
    valid_frames = np.where(energy > threshold)[0]
    if len(valid_frames) > 0:
        start = max(0, valid_frames[0] * 160)
        end = min(len(wav), (valid_frames[-1] + 1) * 160)
        wav = wav[start:end]
        
    # 3. Cố định độ dài 64.000 mẫu (4 giây) bằng Repeat Padding hoặc Crop
    if len(wav) < max_len:
        num_repeats = int(np.ceil(max_len / len(wav)))
        wav = np.tile(wav, num_repeats)[:max_len]
    else:
        wav = wav[:max_len]
        
    # 4. Chuẩn hóa Z-score biên độ
    wav = (wav - np.mean(wav)) / (np.std(wav) + 1e-8)
    return torch.tensor(wav, dtype=torch.float32)
```

---

## GIAI ĐOẠN 03: KIẾN TRÚC MÔ HÌNH, THIẾT KẾ ĐỐI CHỨNG & QUY TRÌNH HUẤN LUYỆN (MODEL TRAINING PIPELINE)

*Thực hiện Must #2 (W5): Fine-tune wav2vec 2.0 đối chứng Có vs. Không tăng cường nén kênh và so sánh với Baseline LFCC + GMM / AASIST (ADR-1, Bảng 2.2).*

### [BƯỚC 3.1] Thiết kế Kiến trúc Mô hình & Các Nhánh Đối chứng (ADR-1, ADR-2, Bảng 2.2)

* **Mô hình Baseline đơn giản (Bảng 2.2) – LFCC + GMM & AASIST gốc:** Triển khai baseline truyền thống sử dụng đặc trưng cepstral tần số tuyến tính thủ công (LFCC) kết hợp mô hình hỗn hợp Gauss (GMM) chạy trên CPU (kèm tham chiếu AASIST gốc dùng SincConv) để làm mốc cơ sở chứng minh ưu thế bắt dấu vết giọng tổng hợp của học tự giám sát (ADR-1).
* **Mô hình Đối chứng chính cho CH1 – wav2vec 2.0 (Không tăng cường nén kênh):** Sử dụng kiến trúc wav2vec 2.0 fine-tune kết hợp lớp phân loại / mạng chú ý đồ thị phổ-thời gian (SSL-AASIST theo Tak et al. [3]), huấn luyện chỉ trên âm thanh sạch (`clean_16khz`, không tăng cường nén Opus/AMR-NB/G.711/$8\text{ kHz}$) với cùng tập kiểm thử và cùng số bước huấn luyện.
* **Mô hình Chủ lực của ViTrueVoice – wav2vec 2.0 (Có tăng cường nén kênh – ADR-2):** Giữ cố định cùng kiến trúc wav2vec 2.0 (HuggingFace `transformers`: `nguyenvulebinh/wav2vec2-base-vietnamese-250h` hoặc `Wav2Vec2-XLS-R` kết hợp đồ thị HS-GAL của AASIST) và cùng số bước huấn luyện như mô hình đối chứng, nhưng bật tăng cường nén kênh thoại (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$ + RawBoost) để kiểm chứng giả thuyết **H1** (giảm $\ge 30\%$ EER tương đối) và đánh giá tổng quát hóa từ **Seen TTS (F5-TTS)** sang **Unseen TTS (VieNeu-TTS)** theo **H2**.

### [BƯỚC 3.2] Thiết lập Hàm mất mát, Bộ tối ưu hóa, Biến kiểm soát và Siêu tham số

| Thành phần Huấn luyện | Cấu hình Tham số Chi tiết | Mục đích Kỹ thuật trong Đề tài |
| :--- | :--- | :--- |
| **Biến kiểm soát thí nghiệm (Mục 3.5)** | $\bullet$ Biến thay đổi: (a) Có/Không tăng cường nén kênh; (b) Seen TTS (F5-TTS) vs. Unseen TTS (VieNeu-TTS)<br>$\bullet$ Giữ cố định: Kiến trúc, tập Test, số bước huấn luyện | Đảm bảo tính đối chứng khoa học nghiêm ngặt khi trả lời hai câu hỏi nghiên cứu CH1 và CH2. |
| **Hàm mất mát (Loss Function)** | Weighted Cross-Entropy Loss<br>Trọng số lớp: $W = [0.1, 0.9]$ (Spoof: $0.1$, Bona fide: $0.9$) | Xử lý mất cân bằng số lượng mẫu giữa tập Spoof và Bona fide, tối ưu đánh đổi chấp nhận nhầm – từ chối nhầm. |
| **Bộ tối ưu (Optimizer)** | Adam / AdamW<br>$\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-8}$, $\text{Weight Decay} = 10^{-4}$ | Giữ ổn định đạo hàm khi tinh chỉnh đồng thời (joint fine-tuning) cả khối Transformer wav2vec 2.0 và lớp phân loại/đồ thị. |
| **Tốc độ học (Learning Rate)** | $\bullet$ Khởi động (Warm-up 3–5 epochs): $lr = 10^{-4}$<br>$\bullet$ Tinh chỉnh wav2vec 2.0 (Fine-tune): $lr = 10^{-6}$ | Learning rate cực nhỏ ($10^{-6}$) ngăn hiện tượng quên thảm khốc (catastrophic forgetting) các biểu diễn tiền huấn luyện. |
| **Batch Size & Bước huấn luyện** | $\text{Batch Size} = 16$ hoặc $32$; cố định cùng số bước huấn luyện (50–100 epochs) giữa 2 nhánh đối chứng | Đảm bảo hội tụ ổn định trên GPU và lưu `best_model.pt` tại điểm đạt EER + minDCF tối ưu trên tập Dev (`SPK_0006` + mở rộng). |

### [BƯỚC 3.3] Quy trình thực thi vòng lặp Huấn luyện từng bước (Step-by-Step Training Loop)

* **Giai đoạn Khởi động (Warm-up Phase – 3 đến 5 Epoch đầu):** Đóng băng (Freeze) toàn bộ trọng số của khối Front-end wav2vec 2.0, chỉ mở khóa huấn luyện phần Back-end đồ thị AASIST và lớp phân loại cuối với $lr = 10^{-4}$ để thích nghi với không gian biểu diễn tự giám sát.
* **Giai đoạn Tinh chỉnh Toàn mạng (Joint Fine-tuning Phase):** Mở khóa (Unfreeze) toàn bộ các tầng Transformer của wav2vec 2.0, hạ Learning Rate xuống $10^{-6}$. Nhánh đề xuất kích hoạt biến đổi nén kênh Opus/AMR-NB/G.711/$8\text{ kHz}$ + RawBoost; nhánh đối chứng giữ nguyên âm thanh sạch.
* **Kiểm định & Lưu Checkpoint theo EER và minDCF:** Sau mỗi epoch, chạy mô hình ở chế độ `eval()` trên tập Dev (`dev_manifest.csv`), tính chỉ số EER ($\%$) và minDCF. Chỉ lưu đè file `checkpoints/best_model.pt` khi EER trên tập Dev đạt mức thấp nhất mới.

```python
# Khung mã Huấn luyện & Tính hàm mất mát Weighted Cross-Entropy (PyTorch)
import torch, torch.nn as nn
from torch.optim import Adam

# Khởi tạo mô hình wav2vec 2.0 (SSL-AASIST) và hàm mất mát có trọng số cân bằng lớp
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = SSLAASISTModel(ssl_pretrained='nguyenvulebinh/wav2vec2-base-vietnamese-250h').to(device)
weights = torch.FloatTensor([0.1, 0.9]).to(device)  # [Spoof, Bona fide]
criterion = nn.CrossEntropyLoss(weight=weights)
optimizer = Adam(model.parameters(), lr=1e-6, betas=(0.9, 0.98), eps=1e-8, weight_decay=1e-4)

for epoch in range(1, num_epochs + 1):
    model.train()
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        logits = model(batch_x)           # Output shape: (batch_size, 2)
        loss = criterion(logits, batch_y)
        loss.backward()
        optimizer.step()
    
    # Đánh giá EER & minDCF trên tập Dev cuối mỗi Epoch
    dev_eer, dev_mindcf = evaluate_eer_mindcf(model, dev_loader, device)
    if dev_eer < best_eer:
        best_eer = dev_eer
        torch.save(model.state_dict(), 'checkpoints/best_model.pt')
```

---

## GIAI ĐOẠN 04: ĐÁNH GIÁ THỰC NGHIỆM, TRIỂN KHAI AWS/DOCKER, KIỂM THỬ & PILOT (GOALS & DELIVERABLES)

*Thực hiện Must #2, #3 & CP6–CP10 (W5–W10): Kiểm định EER/minDCF, triển khai FastAPI + Gradio + Bot Telegram, bảo mật AWS và Pilot với CLB ATTT HUTECH.*

### [BƯỚC 4.1] Giao thức Đo lường Trước–Sau, Đánh giá Chéo & Bộ AI Eval $\ge 30$ Tình huống

* **Đo số 'Trước' của người nghe & cách thủ công ở Tuần W2 (17–23/10/2026) & Blind Listening Package:** Cho $\ge 10$ người nghe 20 đoạn thoại thật/giả (tận dụng các gói nghe mù ẩn danh `blind_listening` kèm biểu mẫu chấm độc lập và khóa giải mã `blind_key_private.csv`) để đo tỷ lệ phân biệt đúng bằng tai người (thay thế con số $35\%$ ước lượng ban đầu trong dự thảo ý tưởng); đồng thời bấm giờ $\ge 3$ lần cách xác minh thủ công (gọi lại / hỏi câu bí mật) để làm mốc 'Trước' cho Bảng 3.3.
* **Chạy Script tái lập EER, minDCF và đường DET (`scripts/eval_eer.py` – US8):** Quét ngưỡng quyết định $\theta$ nơi tỉ lệ chấp nhận nhầm (FAR) bằng tỉ lệ từ chối nhầm (FRR) để xuất EER ($\%$), minDCF và đường cong DET ra tệp `benchmarks/eval_metrics.csv` cho cả 2 kịch bản:
  1. Đánh giá có vs. không tăng cường nén trên tập âm thanh nén Opus/AMR-NB/G.711/$8\text{ kHz}$ (CH1/H1).
  2. Đánh giá từ Seen TTS (F5-TTS) sang Unseen TTS (VieNeu-TTS) chưa thấy khi huấn luyện (CH2/H2).
* **Xây dựng bộ AI Eval $\ge 30$ tình huống & Hệ thống Kiểm thử TDD (31/31 Unit Tests – W6 / CP6):** Thiết lập bộ đánh giá hệ thống AI gồm $\ge 30$ tình huống kiểm thử (trong đó bắt buộc có $\ge 10$ tình huống lấy từ các lần hệ thống từng nhận diện sai, báo cáo tỉ lệ đạt trước và sau khi sửa), kết hợp duy trì bộ kiểm thử tự động TDD (hiện đã đạt **31/31 unit tests xanh $100\%$** trong `tests/test_vitruevoice_pipeline.py`, `test_speaker_profiler.py`, `test_dialect_filter.py`, `test_split_dataset.py` chạy qua `pytest` và GitHub Actions CI ở mỗi lần push).

### [BƯỚC 4.2] Triển khai Dịch vụ (FastAPI / Gradio / Bot Telegram), Hạ tầng AWS & Bảo mật

* **Dịch vụ kiểm tra đoạn thoại $\le 3$ giây (Must #2 & Must #3 – W5, W6):** Xây dựng API FastAPI kết nối với Web Gradio (giao diện tối giản $\le 3$ thao tác cho người lớn tuổi – US4, NFR4) và Bot Telegram thử nghiệm (nhận tin nhắn thoại chuyển tiếp từ người dùng). Khi nhận đoạn thoại 5–10 giây, hệ thống xử lý trên RAM và trả về Nhãn (`THẬT` / `GIẢ`) + Độ tin cậy trong $\le 3$ giây (bấm giờ lặp 30 lần, lấy trung vị lưu vào `benchmarks/latency_benchmark.csv`).
* **Hạ tầng Đám mây AWS & 2 Biện pháp Bảo mật (Gói khóa học A – Bảng 2.3):** Triển khai container Docker trên Amazon EC2 (G4dn/T3), lưu image trên Amazon ECR, lưu log ẩn danh trên Amazon S3 và giám sát qua AWS CloudWatch. Áp dụng 2 biện pháp bảo mật từ AWS Cloud Security Foundations (CP7 – W7):
  1. Mã hóa HTTPS/TLS và Server-Side Encryption kèm S3 Lifecycle tự động xóa file thoại tạm ngay sau khi xử lý.
  2. Quản lý quyền tối thiểu (IAM Least Privilege) kết hợp giới hạn tần suất gọi API (Rate Limiting) và kiểm tra định dạng/kích thước tệp đầu vào.
  *Ước tính chi phí vận hành cho 100 / 1.000 / 10.000 người dùng bằng AWS Pricing Calculator (Bảng 3.4 – W8).*
* **Kiểm thử độc lập với Đơn vị Pilot (CLB An toàn thông tin HUTECH – W7, W8):** Người chủ pilot chính: CLB An toàn thông tin HUTECH (người liên hệ: Thầy Nguyễn Trọng Minh Hồng Phước; dự phòng: CLB Trí tuệ Nhân tạo HUTECH và Dự án ChongLuaDao.vn). Từ W7–W8 (04/12/2026), CLB đóng vai trò kiểm thử độc lập, tự tạo mẫu giọng giả (có đồng ý) để thử thách hệ thống và ký xác nhận Bảng trước–sau (Bảng 3.3); CLB nhận lại bộ dữ liệu, mô hình và Web Demo/API làm tư liệu nghiên cứu.

```json
{
  "request_id": "req_20261016_001",
  "audio_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "duration_sec": 6.5,
  "codec_detected": "opus_16kbps_8khz",
  "predicted_label": "GIA (SPOOF)",
  "confidence_score": 0.942,
  "latency_sec": 1.48,
  "timestamp": "2026-11-20T14:30:00Z"
}
```

### [BƯỚC 4.3] Bảng Tổng hợp Mục tiêu Hoàn thành Đề tài (Target KPIs, NFRs & Deliverables)

| Hạng mục Mục tiêu | Chỉ số Trước (Baseline ban đầu) | Mục tiêu Hoàn thành (Đích phải đạt) | Bằng chứng Nghiệm thu (Artifacts) |
| :--- | :--- | :--- | :--- |
| **1. Độ bền trên âm thanh đã nén (Chỉ số 1A – CH1 / H1)** | $\bullet$ Tai người: đo $\ge 10$ người $\times$ 20 đoạn ở W2 (số $35\%$ ban đầu là ước lượng)<br>$\bullet$ Baseline mô hình không tăng cường nén (W4–W6) | EER trên tập âm thanh đã nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) giảm ít nhất $30\%$ (tương đối) nhờ huấn luyện tăng cường nén kênh | Script tái lập `scripts/eval_eer.py`, bảng EER/minDCF có & không tăng cường trong `benchmarks/eval_metrics.csv` |
| **2. Độ bền trước công cụ TTS chưa thấy (Chỉ số 1B – CH2 / H2 / NFR2)** | Mô hình giảm chất lượng khi gặp công cụ tổng hợp giọng mới ngoài tập huấn luyện | Duy trì $\text{EER} \le 15\%$ trên giọng giả sinh từ công cụ Unseen TTS (VieNeu-TTS / công cụ thứ 3) chưa thấy khi huấn luyện (báo cáo kèm minDCF & DET) | Báo cáo đánh giá chéo công cụ TTS (W6) và tệp kết quả `benchmarks/eval_metrics.csv` |
| **3. Thời gian phản hồi (Chỉ số 2 – NFR1)** | Cách xác minh thủ công (gọi lại / hỏi câu bí mật): bấm giờ $\ge 3$ lần ở W2 | Thời gian phản hồi trung vị $\le 3$ giây cho đoạn thoại 5–10 giây (đo lặp 30 lần) | File log ẩn danh `benchmarks/latency_log.json` và bảng đo 30 lần `benchmarks/latency_benchmark.csv` |
| **4. Bộ dữ liệu & Riêng tư (Must #1 – NFR3)** | Dữ liệu rời rạc, giọng nói sinh trắc học nhạy cảm cần bảo vệ theo Luật 91/2025/QH15 | $\ge 5$–$30$ người nói có Phiếu đồng ý (`SPK_XXXX`) + VIVOS/Common Voice ($\ge 1.000$ thật, $\ge 2.000$ giả đạt 4 cổng); $100\%$ log ẩn danh; xóa dữ liệu gốc sau bảo vệ | Mẫu Phiếu đồng ý (Phụ lục C.2), 5 file manifest 17 cột (W4), cấu hình S3 Lifecycle tự xóa file tạm |
| **5. Sản phẩm MVP, Tái lập & Pilot (Must #2, #3 – NFR4, NFR5)** | Chưa có công cụ kiểm tra tự động tin nhắn thoại tiếng Việt đã nén | FastAPI + Web Gradio ($\le 3$ thao tác) + Bot Telegram; chạy bằng 1 lệnh Docker; CI chạy $\ge 10$ test (31/31 TDD tests xanh); AI Eval $\ge 30$ ca; Pilot CLB ATTT | Repo GitHub hoàn chỉnh, `Dockerfile`, GitHub Actions CI, Bảng chi phí AWS (100/1k/10k user) & Biên bản xác nhận Pilot (W8) |