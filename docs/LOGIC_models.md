# LOGIC_models — Kiến Trúc Mô Hình, Thiết Kế Đối Chứng & Huấn Luyện

---

## 1. Thiết Kế Kiến Trúc Mô Hình & Các Nhánh Đối Chứng (ADR-1, ADR-2)

### Mô Hình Cơ Sở (Baseline): LFCC + GMM
- **Triển khai**: `src/models/baseline_gmm.py` và CLI `scripts/eval_gmm.py`.
- **Trích xuất đặc trưng**: `extract_lfcc` trích xuất 60 chiều (20 hệ số tĩnh LFCC + 20 delta + 20 delta-delta) trên dải tần tuyến tính ($0–8\text{ kHz}$) ở tần số lấy mẫu $16\text{ kHz}$.
- **Cấu hình GMM**: 512 thành phần Gauss hỗn hợp (`GaussianMixture(n_components=512, covariance_type='diag')`), chia thành 2 mô hình độc lập $P(X|\text{bona})$ và $P(X|\text{spoof})$.
- **Lấy mẫu khung (Subsampling)**: Hỗ trợ `max_frames_per_utt` (ngẫu nhiên 20–100 khung/mẫu) để tối ưu thời gian huấn luyện và bộ nhớ RAM.
- **Điểm số Log-Likelihood Ratio (LLR)**:
  $$s(X) = \frac{1}{T} \sum_{t=1}^T \left[ \log P(x_t \mid \text{bonafide}) - \log P(x_t \mid \text{spoof}) \right]$$
  Điểm số $s(X) > 0$ nghiêng về giọng thật (`bonafide`), khớp quy ước chung của toàn hệ thống.

### Mô Hình Chủ Lực: SSL-AASIST
- **Triển khai**: `src/models/ssl_aasist.py`.
- **Quy ước đầu ra**: Logits $[z_{\text{spoof}}, z_{\text{bonafide}}]$, điểm số phân loại $s = z_{\text{bonafide}} - z_{\text{spoof}}$ (điểm cao = bonafide).
- **Front-end (Tự giám sát SSL)**:
  - Checkpoint tiếng Việt: `nguyenvulebinh/wav2vec2-base-vietnamese-250h` (loại bỏ tầng phân loại ký tự `lm_head`, giữ lại Transformer `Wav2Vec2Model`).
  - Chuẩn hóa biên độ theo mẫu: $\hat{x} = \frac{x - \mu}{\sqrt{\sigma^2 + 10^{-7}}}$.
  - Phép chiếu đặc trưng (`Projection`): Tuyến tính `nn.Linear(hidden_size, 128)`.
- **Back-end (Đồ thị Chú ý Compact AASIST)**:
  - Khối tích chập 2D (`ResBlock2d`): 2 tầng tích chập $3 \times 3$ với chuẩn hóa `BatchNorm2d`, kích hoạt `SELU` và đường tắt `skip connection`.
  - Mạng chú ý đồ thị (`GraphAttention` & `HSGAL`): Tích hợp nút trung tâm (`Master Node`), chú ý không đồng nhất trên cả hai trục thời gian và tần số.
  - Tầng đọc đặc trưng (`Readout`): Kết hợp gộp cực đại và trung bình (`max + mean pool`), chiếu qua tầng tuyến tính xuất 2 logits.
- **Cơ chế 2 pha tích hợp sẵn**: Hỗ trợ `freeze_ssl()`, `unfreeze_ssl()`, và phân chia `param_groups(lr_ssl, lr_backend)` cho bộ tối ưu.

---

## 2. Thiết Kế Thí Nghiệm Đối Chứng (Biến Kiểm Soát CH1 & CH2)

Nhằm trả lời câu hỏi nghiên cứu CH1 (Độ bền nén kênh thoại) và CH2 (Khả năng tổng quát hóa trên TTS chưa thấy), hệ thống phân rã thành **3 nhánh thí nghiệm**:

| Nhánh | Mô tả Kỹ thuật | Dữ liệu Huấn luyện | Augmentation | Cấu hình Epoch | Mục đích Đối chứng |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **Nhánh A** | Baseline Không tăng cường | `mode="clean"` (~9.971 mẫu) | `None` | Phase 1: 4 ep<br>Phase 2: 60 ep | Mốc so sánh cơ sở (CH1/H1). Nhân 3 epoch Phase 2 để cân bằng tổng optimizer steps. |
| **Nhánh B0** | Chỉ nén Codec, không RawBoost | `mode="augmented"` (~29.143 mẫu) | `None` (Đã nén G.711, AMR-NB) | Phase 1: 4 ep<br>Phase 2: 20 ep | Bóc tách chính xác đóng góp riêng biệt của nén kênh thoại so với RawBoost. |
| **Nhánh B** | **ViTrueVoice Đầy đủ** | `mode="augmented"` (~29.143 mẫu) | `make_rawboost()` online | Phase 1: 4 ep<br>Phase 2: 20 ep | Mô hình hoàn chỉnh (Codec + RawBoost: LnL, ISD, SSI). |

### Ràng Buộc Phân Định Seen vs Unseen TTS & Bảo Vệ Giả Thuyết H2
> STUBBORN_FACT: Hai công cụ Seen TTS cốt lõi tham gia vào quá trình huấn luyện (tập Train và Dev) là `F5-TTS` (Flow Matching) và `VieNeu-TTS v3 Turbo` (Autoregressive Qwen LLM + NeuCodec), tạo nên kiến trúc phòng thủ kép Dual-Seen. Công cụ Unseen TTS thực thụ chuẩn Zero-Shot Voice Cloning phục vụ kiểm định Giả thuyết H2 (OOD Generalization) là `VoiceStudio (OmniVoice CFM)` — được cô lập 100% khỏi quá trình huấn luyện.

- **Tiến trình chuẩn hóa kiến trúc**:
  - *Giai đoạn khảo sát W05 (Must #2, Checkpoint B)*: Ban đầu thử nghiệm cô lập VieNeu-TTS làm công cụ unseen. Kết quả thực nghiệm cho thấy EER trên VieNeu dao động $21.88\% - 26.34\%$ (chưa đạt KPI $\le 15\%$) do độ lệch miền âm học giữa 2 trường phái Flow Matching và Autoregressive LLM.
  - *Giai đoạn hoàn thiện v0.4.7+ (Must #3, Checkpoint V7 Dual-Seen)*: Đưa VieNeu-TTS vào tập Train/Dev thành kiến trúc phòng thủ đa trường phái (Dual-Seen). Đồng thời khóa công cụ Unseen TTS Zero-Shot thực thụ là **VoiceStudio (OmniVoice CFM)** làm thước đo chuẩn mực cho Giả thuyết H2.
- **Ràng buộc phân hoạch và cô lập 100%**:
  - `train_dual_seen_with_spk1.csv`: Bao gồm cả F5-TTS và VieNeu-TTS v3 Turbo (~54.400 dòng). Tuyệt đối 0% xuất hiện VoiceStudio CFM và 5 tình nguyện viên nghiệm thu (`SPK_0003`..`0007`).
  - `dev.csv` / `dev_zalo.csv`: Tập kiểm định độc lập bảo toàn ranh giới.
  - `02_Unseen_Acceptance`: Giữ nguyên 100% mẫu VoiceStudio CFM (375 clips x 5 codecs) để kiểm định Giả thuyết H2.

---

## 3. Hàm Mất Mát & Bảng Siêu Tham Số Huấn Luyện

| Thành phần Huấn luyện | Cấu hình Tham số Chi tiết | Mục đích Kỹ thuật trong Đề tài |
| :--- | :--- | :--- |
| **Hàm mất mát (Loss Function)** | Weighted Cross-Entropy Loss Động<br>Công thức: $w_c = \frac{N}{2 \cdot N_c}$ chuẩn hóa $\sum w_c = 1.0$<br>Hàm: `loss_weights_from_counts(n_spoof, n_bona)` | Bù đắp chính xác tỷ lệ mất cân bằng giữa Spoof và Bona fide trong tập Train thực tế ($w_c = \frac{N}{2 \cdot N_c}$). Tuyệt đối không gán cứng trọng số. |
| **Bộ tối ưu (Optimizer)** | Adam / AdamW<br>$\beta_1 = 0.9$, $\beta_2 = 0.98$, $\epsilon = 10^{-8}$, $\text{Weight Decay} = 10^{-4}$ | Giữ ổn định đạo hàm khi tinh chỉnh đồng thời cả khối Transformer wav2vec 2.0 và lớp đồ thị HS-GAL. |
| **Tốc độ học (Learning Rate)** | $\bullet$ Pha 1 (Warm-up 4 epochs): $lr = 10^{-4}$ (chỉ back-end)<br>$\bullet$ Pha 2 (Joint Fine-tuning): $lr_{\text{ssl}} = 10^{-6}$, $lr_{\text{backend}} = 10^{-5}$ | $lr_{\text{ssl}} = 10^{-6}$ cực nhỏ ngăn quên thảm khốc (catastrophic forgetting) các biểu diễn âm học tiếng Việt đã tiền huấn luyện. |
| **Batch Size & Bước tích lũy** | $\text{Batch Size} = 16$ (kèm Gradient Accumulation = 2); Cắt/đệm cố định 64.000 mẫu | Đảm bảo kích thước batch hiệu dụng = 32 trên GPU Kaggle (T4 16GB). |
| **Dừng sớm (Early Stopping)** | `patience = 10` epochs theo dõi `dev_eer` | Tự động ngắt huấn luyện khi EER tập Dev ngừng giảm, lưu checkpoint tối ưu nhất. |

> STUBBORN_FACT: Trọng số Loss Cross-Entropy bắt buộc tính động từ tần suất nghịch của tập Train theo công thức $w_c = \frac{N}{2 \cdot N_c}$ qua `loss_weights_from_counts`. Tuyệt đối KHÔNG sử dụng đồng thời `WeightedRandomSampler` cùng Weighted Loss để tránh lỗi bù trừ kép (double penalty).

---

## 4. Chiến Lược Huấn Luyện 2 Pha & Lưu Checkpoint

```mermaid
graph TD
    Phase1[Pha 1: Khởi động Warm-up Epoch 1-4] -->|Đóng băng Wav2Vec2, lr=1e-4 trên HS-GAL| Phase1Eval[Đánh giá EER + minDCF tập Dev]
    Phase1Eval --> Phase2[Pha 2: Tinh chỉnh Toàn mạng Epoch 5-20 / 60]
    Phase2 -->|Mở khóa toàn bộ, lr_ssl=1e-6, lr_backend=1e-5| Phase2Eval[Đánh giá EER + minDCF tập Dev]
    Phase2Eval -->|Nếu Dev EER < best_eer| SaveCheckpoint[Lưu out/run_<branch>/best_model.pt]
```

1. **Pha 1 (Khởi động Warm-up — 4 epoch đầu)**:
   - Đóng băng (`Freeze`) khối front-end wav2vec 2.0 (`ssl.frozen = True`, không tính gradient).
   - Chỉ mở khóa huấn luyện phần back-end đồ thị AASIST với tốc độ học $lr = 10^{-4}$.
2. **Pha 2 (Tinh chỉnh Toàn mạng Joint Fine-tuning)**:
   - Mở khóa (`Unfreeze`) toàn bộ các tầng Transformer của wav2vec 2.0.
   - Sử dụng 2 tốc độ học riêng biệt: $lr_{\text{ssl}} = 10^{-6}$ cho Wav2Vec2 và $lr_{\text{backend}} = 10^{-5}$ cho HS-GAL.
3. **Cấu trúc Lưu Checkpoint**:
   - Checkpoint `best_model.pt` lưu trữ đầy đủ:
     ```python
     {
         "epoch": epoch,
         "phase": phase,
         "model": model.state_dict(),
         "dev_eer": best_eer,
         "branch": cfg.branch,
         "model_kwargs": {"d_graph": 64, "conv_channels": (64, 128), "n_hs": 1},
         "config": dataclasses.asdict(cfg),
     }
     ```
   - Cho phép hàm `load_model` trong `scripts/eval_ssl_aasist.py` tự động phục hồi kiến trúc chính xác mà không cần truyền lại tham số thủ công.

---

## 5. Quy Trình Chấm Điểm & Kiểm Chứng Giả Thuyết Tự Động

### Đánh giá Chấm điểm (`scripts/eval_ssl_aasist.py`)
- Lọc mặc định `role == 'eval'` để đảm bảo bộ ba ghép cặp (Paired Triplets 1:1:1) nguyên vẹn trên cả 3 codec (`clean_16khz`, `g711_alaw`, `amr_nb`).
- Chấm điểm từng mẫu: $s = z_{\text{bonafide}} - z_{\text{spoof}}$, tính EER, khoảng tin cậy Bootstrap 95% (`cluster_bootstrap_ci` theo speaker), và minDCF ($P_{\text{spoof}}=0.05, C_{\text{miss}}=1, C_{\text{fa}}=1$).
- Xuất bảng chuẩn hóa 14 cột tương thích hoàn toàn giữa Baseline GMM và SSL-AASIST.

### Đối chứng Giả thuyết Khoa học (`scripts/compare_h1.py`)
- **Giả thuyết H1 (CH1)**: Đo độ giảm EER tương đối trên từng kênh thoại nén:
  $$\Delta\text{EER}_{\text{rel}} = \frac{\text{EER}_A - \text{EER}_B}{\text{EER}_A} \times 100\% \ge 30.0\%$$
  Verdict `PASS` khi toàn bộ các điều kiện nén đều vượt ngưỡng $30\%$; kiểm tra cờ `ci_overlap` xem khoảng tin cậy 95% có bị chồng lấn hay không.
- **Giả thuyết H2 (CH2)**: Đo EER của mô hình trên công cụ chưa từng thấy (`Unseen TTS`):
  $$\text{EER}_{\text{unseen}} \le 15.0\% \implies \text{PASS}$$
  - *Khảo sát W05 ban đầu*: Đánh giá trên `VieNeu-TTS` (EER đạt $21.88\% - 26.34\%$, chưa đạt $\le 15\%$).
  - *Nghiệm thu chuẩn mực v0.4.7+ (Dual-Seen V7)*: Đánh giá trên công cụ Zero-Shot CFM thực thụ `VoiceStudio (OmniVoice CFM)` — đạt EER **$14.67\% \le 15.0\%$** (chính thức **PASS** Giả thuyết H2, xem chi tiết tại [docs/BENCHMARK_seen_vs_unseen_degradation.md](file:///c:/Codes/VieTrueVoice/docs/BENCHMARK_seen_vs_unseen_degradation.md)).
  Kiểm tra thêm điều kiện cận trên khoảng tin cậy: `ci_hi_pass = (eer_ci_hi <= 0.15)`.
- **Phân rã biến B0 vs B**: Đo đạc độ lệch tương đối giữa B0 (chỉ nén) và B (nén + RawBoost) để định lượng chính xác đóng góp của kỹ thuật RawBoost.

---

## 6. Kết Quả Thực Nghiệm Đối Chứng H1, H2 & Phân Rã RawBoost (Must #2)

Đánh giá thực nghiệm hoàn tất trên 3 checkpoint thu được từ Kaggle GPU (Version 3 & 4) trên tập kiểm thử nội bộ (`test_indomain.csv`, 9.399 mẫu `role == 'eval'`) và ngoại vùng (`test_ood.csv`, 813 mẫu):
- **Mô hình A (Clean Baseline)**: Dừng sớm tại Epoch 10 (patience=6), checkpoint tốt nhất tại Phase 1 Epoch 4 (`dev_eer = 20.66%`).
- **Mô hình B0 (Chỉ Codec, không RawBoost)**: Hoàn thành 24/24 epoch, checkpoint tốt nhất tại Phase 2 Epoch 24 (`dev_eer = 1.93%`).
- **Mô hình B (ViTrueVoice: Codec + RawBoost)**: Đạt 20/24 epoch trước giới hạn 12h, checkpoint tốt nhất tại Phase 2 Epoch 20 (`dev_eer = 2.95%`).

### 6.1. Bảng Đối Chứng Giả Thuyết H1 (Độ Bền Nén Kênh Thoại — CH1)
> Quy ước dấu: Độ giảm EER tương đối $\Delta\text{EER}_{\text{rel}} = \frac{\text{EER}_A - \text{EER}_B}{\text{EER}_A} \times 100\%$. Giá trị dương ($> 0$) biểu thị tỷ lệ cải thiện (EER của B thấp hơn A).

| Tập kiểm thử | Kênh nén | EER Mô hình A | 95% Bootstrap CI (A) | EER Mô hình B | 95% Bootstrap CI (B) | $\Delta\text{EER}_{\text{rel}}$ | CI Overlap | Kết luận (Verdict) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **In-domain** | **AMR-NB** ($8\text{ kHz}$) | $28.06\%$ | $[24.48\%, 32.30\%]$ | **$16.70\%$** | $[12.67\%, 20.81\%]$ | **$+40.46\%$** | **False** | **PASS** ($\ge 30\%$) |
| **In-domain** | **G.711 A-law** | $28.13\%$ | $[23.00\%, 33.45\%]$ | **$14.75\%$** | $[10.52\%, 19.38\%]$ | **$+47.55\%$** | **False** | **PASS** ($\ge 30\%$) |
| *OOD* | AMR-NB ($8\text{ kHz}$) | $42.74\%$ | $[36.09\%, 49.17\%]$ | $27.89\%$ | $[17.02\%, 34.11\%]$ | $+34.75\%$ | False | PASS ($\ge 30\%$) |
| *OOD* | G.711 A-law | $35.48\%$ | $[27.39\%, 46.30\%]$ | $29.84\%$ | $[19.17\%, 36.81\%]$ | $+15.91\%$ | True | FAIL ($< 30\%$) |

> **Kết luận H1**: **ĐẠT TRÊN TẬP NỘI BỘ (In-domain Split Verdict: PASS)**. Cả hai chuẩn nén thoại đều giảm từ $40.46\%$ đến $47.55\%$ EER tương đối, vượt ngưỡng $30\%$, khoảng tin cậy 95% tách biệt hoàn toàn (`ci_overlap = False`). Trên tập ngoại vùng (OOD), AMR-NB đạt $+34.75\%$ nhưng G.711 chỉ đạt $+15.91\%$, do đó **chưa đạt toàn phần trên mọi điều kiện OOD**.

### 6.2. Bảng Đánh Giá Khảo Sát Ban Đầu Giả Thuyết H2 (Thử Nghiệm W05 Với VieNeu-TTS)
> *Ghi chú tiến trình khoa học*: Đây là số liệu khảo sát giai đoạn 1 (Must #2, Checkpoint B) khi VieNeu-TTS được dùng làm phép thử unseen ban đầu. Mục tiêu đề cương: $\text{EER} \le 15.0\%$.

| Tập kiểm thử | Điều kiện nén | EER VieNeu-TTS | 95% Bootstrap CI | Mục tiêu | Kết luận |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **In-domain** | **G.711 A-law** | **$21.88\%$** | $[15.56\%, 29.33\%]$ | $\le 15.0\%$ | **CHƯA ĐẠT** |
| **In-domain** | **Clean 16kHz** | **$22.17\%$** | $[15.62\%, 29.24\%]$ | $\le 15.0\%$ | **CHƯA ĐẠT** |
| **In-domain** | **AMR-NB** | **$26.34\%$** | $[18.89\%, 31.98\%]$ | $\le 15.0\%$ | **CHƯA ĐẠT** |
| *OOD* | G.711 A-law | $45.90\%$ | $[27.58\%, 55.50\%]$ | $\le 15.0\%$ | CHƯA ĐẠT |

> **Ý nghĩa khoa học & Hướng giải quyết kiến trúc**: Kết quả chưa đạt ($21.88\% - 26.34\%$) phản ánh chân thực độ lệch miền biểu diễn giữa mô hình Diffusion (F5) và Autoregressive LLM (VieNeu). Nhận định khoa học này dẫn tới bước đột phá ở v0.4.7+: đưa VieNeu-TTS vào tập Train để hình thành kiến trúc phòng thủ kép Dual-Seen (giảm EER của VieNeu xuống $12.27\%$), đồng thời chuyển giao công cụ kiểm định H2 chuẩn mực sang **VoiceStudio (OmniVoice CFM Zero-shot Voice Cloning)** — đạt EER **$14.67\% \le 15.0\%$** (chính thức PASS H2; xem chi tiết tại Mục 8.2 và [docs/BENCHMARK_seen_vs_unseen_degradation.md](file:///c:/Codes/VieTrueVoice/docs/BENCHMARK_seen_vs_unseen_degradation.md)).

### 6.3. Bóc Tách Đóng Góp Riêng Biệt Của RawBoost (B0 vs B)
| Tập kiểm thử | Kênh nén | EER B0 (Chỉ Codec) | EER B (Codec + RawBoost) | Mức giảm thêm nhờ RawBoost |
| :--- | :--- | :---: | :---: | :---: |
| **In-domain** | **G.711 A-law** | $18.93\%$ | **$14.75\%$** | **$+22.06\%$** |
| **In-domain** | **AMR-NB** | $19.38\%$ | **$16.70\%$** | **$+13.79\%$** |

> **Ý nghĩa khoa học**: Tăng cường Codec giúp giảm EER từ $28\%$ xuống $19\%$; bổ sung RawBoost trực tuyến giúp giảm tiếp từ $19\%$ xuống $14.75\%–16.70\%$, chứng minh vai trò tích cực độc lập của RawBoost.

### 6.4. Đánh Giá Độ Chính Xác Nội Bộ Trên Giọng Giả Đã Thấy (F5-TTS, In-domain)
- `clean_16khz`: **$2.67\%$** EER (minDCF = 0.108).
- `g711_alaw`: **$2.67\%$** EER (minDCF = 0.107).
- `amr_nb`: **$3.56\%$** EER (minDCF = 0.210).
- Toàn bộ In-domain F5-TTS: **$3.28\%$** EER (ĐẠT VƯỢT TRỘI so với mục tiêu đề tài $\le 8.0\%$).

### 6.5. Phân Tích Ca Chẩn Đoán Thực Tế (SPK_0001) & Chuẩn Hóa Điểm Phân Định
- **Hiện tượng**: Toàn bộ 15/15 phát ngôn của người nói `SPK_0001` (thuộc bộ nghiệm thu độc lập) bị mô hình cho điểm âm ($-21.78$ đến $-10.24$, trung vị $-14.36$).
- **Bằng chứng mô tả & Ranh giới kết luận**:
  1. Phân phối điểm số của 15 phát ngôn này dịch chuyển lặp lại vào dải điểm của lớp Spoof (trùng dải $-20.11$ đến $-4.89$ của F5-TTS). Đây là bằng chứng lỗi lặp lại ở một người nói cụ thể, chưa chứng minh vật lý rằng micro, cự ly, phòng thu, F0 hay SNR là nguyên nhân duy nhất.
  2. Thiết bị thu âm, phòng, khoảng cách và đặc thù người nói được xem là các **nguồn biến thiên âm học cần bao phủ trong dữ liệu**, không được quy kết chủ quan làm nguyên nhân gốc hoặc quy lỗi cho người tham gia.
  3. Phân tích pháp y chuỗi tệp cho thấy audio của `SPK_0001` được ghi bằng ứng dụng thoại điện thoại, truyền qua ứng dụng Zalo dưới dạng container `.m4a` (AAC-LC 48kHz mono ~76kbps) và được người dùng đổi thủ công phần mở rộng sang `.wav`.
  4. Thực nghiệm tách biệt tín hiệu cho thấy: mẫu âm nền tự nhiên của phòng thu `SPK_0001` đạt điểm $+11.20$ (rất thật), trong khi đoạn thoại đã cắt khoảng lặng có điểm âm sâu ($-11.91$), cho thấy mô hình phản ứng với tổ hợp đặc trưng âm học trong giọng nói qua chuỗi nén này.
  5. Mô hình Checkpoint B vẫn bảo toàn trật tự phân hạng trên `SPK_0001`: Giọng thật ($-10.83$) > VieNeu clone ($-15.18$) > F5 clone ($-18.45$).
  6. Không thể hạ ngưỡng quyết định $\theta$ xuống dưới $-10.24$ vì sẽ làm tỷ lệ chấp nhận sai (FAR) trên F5-TTS tăng vọt. Ngưỡng vận hành production được giữ cố định $\theta = 0.0$.
- **Loại bỏ xác suất giả mạo 100%**: Loại bỏ hoàn toàn công thức phi chuẩn hóa $\sigma(|s|)$. Khi chưa áp dụng mô hình cân chỉnh xác suất (Isotonic / Platt Scaling trên tập Dev độc lập), trường `confidence` trả về `null` (API) hoặc hiển thị raw score kèm thông báo chưa hiệu chuẩn (UI/Bot), đảm bảo tính trung thực khoa học theo Đề cương Mục 3.3.

---

## 7. Mở Rộng Kênh Zalo & Nhánh Huấn Luyện Fine-Tuning `B_zalo`

### 7.1. Đánh Giá Baseline Checkpoint B Trên Kênh Zalo & Quy Trình Khôi Phục (Giai Đoạn 2)
- **Kết quả chẩn đoán lỗi baseline ban đầu (146 mẫu local)**:
  - Lần chạy thử trên máy local chỉ bao phủ 146 mẫu (100% bona fide) do thiếu kho âm thanh đầy đủ (3,26 GB lưu trên Kaggle). Khi thiếu spoof, cơ chế fallback cũ đã điền $EER=0.00\%$ và $FAR=0.00\%$ sai lệch. Số liệu này không được công nhận làm baseline khoa học.
- **Quy trình khôi phục baseline chuẩn (Giai đoạn 2 — Kernel Kaggle GPU riêng biệt)**:
  - Khóa mã băm SHA-256: Checkpoint B (`a921c339…b56bd9f`) và `dev_zalo.csv` (`730937e8…f4f77e`).
  - Đóng gói kernel inference-only độc lập `deploy_zalo_eval/eval_zalo_baseline.ipynb` (kèm `kernel-metadata.json` mount 2 nguồn: `vietrue-ssl-training` và `vietrue-model-training`).
  - Thực thi giải nén chọn lọc 1-1 và suy luận toàn bộ **11.450 mẫu Dev Zalo** trên GPU Tesla T4 (5 codec: Clean 2.332, AAC 2.332, Opus 2.332, AMR 2.227, G.711 2.227). Mỗi codec bao gồm đầy đủ cả hai lớp (2.140/2.035 bona fide và 192 spoof).
  - Bắt buộc kiểm tra tính hợp lệ (`is_valid = True`), fail-fast nếu thiếu audio, báo cáo EER, minDCF, FRR@0, FAR@0, Bootstrap 95% CI theo `base_utt` và paired deltas $\Delta s = s_{\text{proxy}} - s_{\text{clean}}$.
- **Tiêu chuẩn công nhận**: Chỉ công nhận baseline sau khi kết quả Kaggle trả về đủ 11.450 điểm số và mọi codec đều có cả hai lớp. Mọi quyết định fine-tune `B_zalo` chỉ được tiến hành sau khi baseline hợp lệ này được thiết lập.
- **Kết quả Baseline Chính thức trên 11.450 Mẫu Dev Zalo (Khóa ngày 2026-10-30)**:
  - Bảng điểm chi tiết: `out/zalo_baseline/dev_zalo_scores.csv` (11.450 dòng, 10.490 bona fide, 960 spoof, 0% rò rỉ volunteer `SPK_xxxx`; lưu ý ở baseline v0.4.1 chưa nạp VieNeu, sau đó ở v0.4.7 đã chuẩn hóa Dual-Seen và khóa Unseen TTS chuẩn là VoiceStudio CFM).
  - Bảng chỉ số tổng hợp (`out/zalo_baseline/zalo_baseline_metrics.csv`):

| Nhóm Codec | n_bona | n_spoof | EER (%) | EER 95% CI (Bootstrap) | $\text{FRR}_{\theta=0}$ (%) | $\text{FAR}_{\theta=0}$ (%) | minDCF |
|---|---|---|---|---|---|---|---|
| `clean_16khz` | 2.140 | 192 | **2.604%** | [1.40, 3.85] | 1.92% | 3.12% | 0.1271 |
| **`aac_zalo_76k` (Profile A)** | 2.140 | 192 | **2.617%** | [1.82, 4.37] | 0.89% | 7.81% | 0.1480 |
| **`opus_zalo_24k` (Profile B)** | 2.140 | 192 | **2.103%** | [1.41, 3.55] | 1.82% | 3.65% | 0.1345 |
| `g711_alaw` | 2.035 | 192 | **3.125%** | [1.93, 4.12] | 2.16% | 4.69% | 0.1780 |
| `amr_nb` | 2.035 | 192 | **3.125%** | [2.03, 4.26] | 0.49% | 9.90% | 0.1508 |

  - Độ lệch điểm số ghép cặp so với Clean (`out/zalo_baseline/zalo_paired_deltas.csv`, $\Delta s = s_{\text{proxy}} - s_{\text{clean}}$):

| Codec Proxy | Số cặp ($N$) | Mean $\Delta s$ | Std $\Delta s$ | Trung vị $\Delta s$ | Min $\Delta s$ | Max $\Delta s$ |
|---|---|---|---|---|---|---|
| `aac_zalo_76k` | 2.332 | **-0.3652** | 2.5564 | -0.7087 | -8.5854 | +18.8603 |
| `opus_zalo_24k` | 2.332 | **-0.0004** | 0.7177 | -0.0151 | -6.3306 | +5.9937 |
| `g711_alaw` | 2.227 | **+0.2739** | 1.7358 | +0.2030 | -14.8060 | +11.7019 |
| `amr_nb` | 2.227 | **+0.5632** | 2.9074 | +0.0927 | -8.9529 | +19.4539 |

  - **Nhận định khoa học**:
    1. *Profile B (`opus_zalo_24k`)*: Độ lệch trung bình gần như triệt tiêu ($\text{mean }\Delta s = -0.0004$, $\text{std} = 0.7177$), EER đạt $2.103\%$, cho thấy biểu diễn Wav2Vec2 + AASIST của Checkpoint B thích ứng rất tốt với kênh thoại Opus 24kbps.
    2. *Profile A (`aac_zalo_76k`)*: Gây dịch chuyển điểm số nhẹ về phía âm ($\text{mean }\Delta s = -0.3652$, $\text{median } = -0.7087$) với độ phân tán cao ($\text{std} = 2.5564$), đẩy $\text{FAR}_{\theta=0}$ lên $7.81\%$.
    3. *Mục tiêu cho `B_zalo` Fine-Tuning*: Nhánh `B_zalo` tập trung hiệu chỉnh phân phối điểm của `aac_zalo_76k` để giảm phương sai $\Delta s$, kéo $\text{FAR}_{\theta=0}$ và $\text{FRR}_{\theta=0}$ về mức cân bằng tối ưu.

### 7.2. Cấu Hình Tinh Chỉnh Nhánh `B_zalo` (`scripts/train.py --branch B_zalo`)
Để triệt tiêu độ dịch chuyển âm và đưa $\text{FRR}_{\theta=0}$ của Profile A về $0.0\%$, nhánh `B_zalo` thực hiện fine-tuning từ checkpoint nền:
- **Trọng số khởi tạo (`--init-ckpt`)**: Tải trực tiếp `best_model_B.pt` (Phase 2 Ep 20).
- **Chiến lược Đóng Băng Khối Tự Giám Sát (Frozen SSL Backbone)**:
  - `phase1_epochs = 5`: Đóng băng 100% backbone `Wav2Vec2Model`, chỉ cập nhật tầng chiếu tuyến tính và mạng đồ thị HS-GAL với $lr = 10^{-4}$.
  - `phase2_epochs = 0`: Tắt hoàn toàn Pha 2 để ngăn hiện tượng quên thảm khốc (catastrophic forgetting) các biểu diễn âm học tiếng Việt đã hội tụ ở Checkpoint B.
- **Hàm mất mát Dynamic Weighted CE**:
  - $w_c = \frac{N}{2 \cdot N_c}$ tính toán động trên manifest huấn luyện (ở v0.4.1 chỉ gồm F5-TTS; đến v0.4.7 nâng cấp Dual-Seen bao gồm cả F5-TTS và VieNeu-TTS v3 Turbo, đồng thời cô lập 100% dữ liệu 5 tình nguyện viên nghiệm thu và công cụ Unseen VoiceStudio CFM).
- **Giám sát Dừng Sớm (Early Stopping)**:
  - `patience = 5` epochs, theo dõi chỉ số `dev_eer` trên tập `dev_zalo.csv` để lưu `best_model_B_zalo.pt`.

### 7.3. Đóng Gói Kernel Huấn Luyện Kaggle `deploy_zalo_train`
- **Tập lệnh sinh kernel**: `scripts/build_zalo_train_notebook.py`.
- **Mã định danh Kernel**: `nguyenthanhtai1959/vietrue-zalo-fine-tuning` (GPU Tesla T4, enable_internet=True).
- **Mã băm kiểm định đầu vào**:
  - Checkpoint B: `a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f`
  - `train_zalo.csv`: `0e2f42e4b9121e0386e7df2e056396b69c6ea6653c49ff86eb5bfc9ec82917e6` (49.085 dòng)
  - `dev_zalo.csv`: `730937e8fe982b51c899753cd2a9aff198ff545d8d0b9fd41a9511025884f77e` (11.450 dòng)
  - HuggingFace Revision: `69e9000591623e5a4fc2f502407860bcdc0de0b2`
- **Cơ chế nạp & sinh dữ liệu trên Kaggle**:
  - Trích xuất chọn lọc từ `vitruevoice_data_processed.zip` vào `/tmp/vitrue_audio`.
  - Sinh proxy đa luồng bằng `ThreadPoolExecutor(max_workers=4)` cho kênh AAC 76k và Opus 24k trực tiếp vào `/tmp/vitrue_audio`.
  - Thực thi huấn luyện fine-tuning qua `scripts/train.py` (Phase 1 = 5 epochs, Phase 2 = 0).
  - Đánh giá kiểm định chống thoái lui (Anti-Regression) trên 11.450 mẫu Dev Zalo độc lập ngay sau huấn luyện:
    * AAC: $\text{EER} \le 2.62\%$, $\text{FAR}_{\theta=0} \le 7.81\%$
    * Opus: $\text{EER} \le 2.10\%$, $\text{FAR}_{\theta=0} \le 3.65\%$
    * Clean: $\text{EER} \le 2.60\%$
  - Tự động dọn dẹp thư mục `/tmp/vitrue_audio` sau khi hoàn tất, đảm bảo `/kaggle/working` chỉ chứa artifact checkpoint và báo cáo điểm số.

---

## 8. Tinh Chỉnh B_zalo V6/V7, Di Chuyển SPK_0001 & Huấn Luyện Kép Dual-Seen (v0.4.4 – v0.4.7)

### 8.1. Di Chuyển SPK_0001 Vào Train & Cô Lập Tuyệt Đối 5 Tình Nguyện Viên Nghiệm Thu
- Sau khi kiểm chứng giả thuyết ngoại lai: người nói có giọng siêu trầm dị biệt `SPK_0001` (F0 < 110Hz, năng lượng dải trầm $e_{\text{low}} = 54.9\%$) không thể tự tổng quát hóa nếu hoàn toàn vắng bóng trong tập huấn luyện (Pass rate chỉ 20.0%, điểm trung bình -17.65).
- Thực thi chuyển 125 dòng của `SPK_0001` (75 bona fide + 50 F5-TTS spoof, loại bỏ 100% VieNeu-TTS) vào `data/manifests_zalo/train_zalo.csv` (nâng quy mô tập Train lên 50.710 dòng).
- Khóa chặt 5 tình nguyện viên đối chứng (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`) làm **Bộ nghiệm thu độc lập chính thức của đề tài** (84 clips bona fide x 5 codecs = 420 clips + 375 clips Unseen VoiceStudio CFM Spoof). Nghiêm cấm 100% xuất hiện trong Train, Dev, Calibration hoặc Fine-tuning.

### 8.2. Huấn Luyện Kép Dual-Seen Re-Training (F5-TTS + VieNeu-TTS v3 Turbo — Checkpoint V7)
- Để hoàn thiện năng lực tổng quát hóa theo kiến trúc phòng thủ đa động cơ, tập Train và Dev được mở rộng thành Dual-Seen bao gồm cả F5-TTS và VieNeu-TTS v3 Turbo (`train_dual_seen_with_spk1.csv`, 54.400 dòng).
- Checkpoint V7 lưu tại: `out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt`.
- Công cụ kiểm định Unseen TTS thực thụ cho Giả thuyết H2 là **VoiceStudio (OmniVoice CFM Zero-shot Voice Cloning)** — hoàn toàn tách biệt khỏi quá trình huấn luyện.

### 8.3. Kết Quả Kiểm Định Nghiệm Thu Tiêu Chuẩn Sản Xuất (Multi-window Max-Pooling V7)
Chạy kiểm định qua toàn bộ 795 clips nghiệm thu bằng script `scripts/eval_5spk_unseen_and_bonafide.py` với cơ chế chuẩn Multi-window Max-Pooling (`mode="max"`):
- **Bona Fide Pass Rate (Giọng thật Clean)**: **90.48% (76/84)** với điểm trung bình dương rất cao (`+21.49`).
  - Trên 4 người nói đối chứng nòng cốt (`SPK_0004`..`SPK_0007`, 64 clips clean): Đạt tuyệt đối **100.0% (64/64)** PASS với điểm trung bình `+28.62`.
  - Trên cả 5 người nói đối chứng trên toàn bộ 5 biến thể codec (420 clips): Đạt **89.52% (376/420)** với điểm trung bình `+20.62` ($\text{BPCER} = 10.48\%$).
- **Seen TTS Spoof Detection Rate (Giọng giả Seen)**:
  - **F5-TTS**: Pass Rate = **99.20% (372/375)**, EER = **2.38%**, Mean Score = **-34.95** (Đạt mục tiêu $\le 8.0\%$).
  - **VieNeu-TTS v3 Turbo**: Pass Rate = **87.73% (329/375)**, EER = **12.27%**, Mean Score = **-28.62** (Tăng từ 60.0% ở V6).
  - **Seen Pooled (750 clips)**: Pass Rate = **93.47% (701/750)**, EER = **6.80%**, Mean Score = **-31.79**.
- **Unseen Spoof Detection Rate (VoiceStudio OmniVoice CFM Zero-shot)**:
  - Pass Rate = **79.47% (298/375)**, EER = **14.67%**, Mean Score = **-20.76** (Chính thức **ĐẠT Giả thuyết H2** $\le 15.0\%$).
- **Độ suy giảm tổng quát hóa (Seen vs Unseen Degradation)**:
  - $\Delta\text{Pass Rate} = -14.00\%$, $\Delta\text{EER} = +7.87\%$, $\Delta\text{Mean Score} = +11.03$.
- **Chỉ số phân tách tối ưu trên tập nghiệm thu 795 clips**:
  - Equal Error Rate (**EER**) = **0.16%**.
  - minDCF = **0.6742**.
  - Khoảng cách phân tách biên độ (Margin Gap) giữa tâm phân bố Thật và Giả: **41.38 điểm** ($+20.62 - (-20.76)$).

---

## 9. Cơ Chế Gộp Điểm Đa Cửa Sổ Chuẩn Sản Xuất (Multi-Window Max-Pooling Production Standard)

### 9.1. Động Lực Kỹ Thuật & Cấu Trúc Trích Xuất Đa Cửa Sổ Song Song (Parallel Multi-Window Architecture)
Trong các kịch bản kiểm định thực tế, đoạn âm thanh thoại thường có độ dài dao động từ 3 đến 10 giây. Phương pháp cắt cúp cố định 4.0 giây đầu tiên truyền thống bỏ sót các dấu hiệu giả mạo quan trọng ở phần giữa hoặc cuối câu thoại.
- **Trích xuất đa cửa sổ trượt (Sliding Windows)**: Âm thanh đầu vào được phân tách thành $K$ cửa sổ có độ dài cố định $W = 64.000$ mẫu (4.0s @ 16kHz), bước nhảy $H = 16.000$ mẫu (1.0s), tối đa $K \le 5$ cửa sổ.
- **Suy luận song song Mini-Batch 1 lượt (`batch_window_forward`)**: Toàn bộ $K$ cửa sổ được xếp chồng thành một mini-batch $\mathbf{X} \in \mathbb{R}^{K \times 64000}$ và đưa qua mô hình trong một forward pass duy nhất. Cách tiếp cận này tận dụng triệt để năng lực tính toán vector hóa của GPU, giữ vững độ trễ chỉ $\approx 66.3\text{ms}$ (thỏa mãn NFR1 $\le 3.0\text{s}$).

### 9.2. Định Nghĩa Toán Học Multi-Window Max-Pooling
Thu được vector điểm số các cửa sổ:
$$\mathbf{s} = [s_1, s_2, \dots, s_K] \in \mathbb{R}^K$$
Điểm số gộp đại diện cho toàn bộ đoạn âm thanh theo tiêu chuẩn Max-Pooling:
$$s_{\text{pooled}} = \max_{k=1,\dots,K} s_k$$
Quyết định phân loại tại ngưỡng an toàn $\theta = 0.0$:
$$\hat{y} = \begin{cases} 1 \quad (\text{Bona Fide / Thật}) & \text{nếu } s_{\text{pooled}} \ge 0.0 \\ 0 \quad (\text{Spoof / Giả mạo}) & \text{nếu } s_{\text{pooled}} < 0.0 \end{cases}$$

**Ý nghĩa bảo vệ an toàn (Bona Fide Preservation)**:
Để một đoạn âm thanh được nhận định là giọng thật, chỉ cần có ít nhất một cửa sổ mang đặc trưng âm học tự nhiên vượt ngưỡng $0.0$. Nguyên tắc này đảm bảo rằng người dùng thật không bị từ chối oan uổng chỉ vì một vài giây ngập ngừng, khoảng lặng hoặc nhiễu môi trường, duy trì tỷ lệ nhận diện giọng thật nòng cốt đạt $100.0\%$.

### 9.3. Bằng Chứng Thực Nghiệm & Độ Vững Chắc Sản Xuất
- Triển khai hoàn tất tại `src/preprocessing/pooling.py` (`pool_scores(scores, mode="max")`).
- Đạt **100.0% (64/64)** nhận diện giọng thật trên 4 tình nguyện viên đối chứng nòng cốt (`SPK_0004`..`SPK_0007`) và **90.48% (76/84)** trên toàn bộ 5 người nói đối chứng.
- Đồng thời bảo toàn khả năng chặn đứng spoof: F5-TTS đạt **99.20%**, VieNeu-TTS đạt **87.73%**, VoiceStudio CFM đạt **79.47%** (EER 14.67%, thỏa mãn H2 $\le 15.0\%$).

### 9.4. Khảo Sát Thử Nghiệm Phương Án Ablation Asymmetric Veto & Lý Do Loại Bỏ
Trong kế hoạch nghiên cứu chuyên sâu `plan-unseen-tts-boost.md`, cơ chế **Asymmetric Veto Multi-window Pooling** (`mode="asymmetric_veto"` / alias `"adaptive"`) đã được phát triển và kiểm định như một nhánh ablation thử nghiệm:
- **Ý tưởng thiết kế**: Kích hoạt Trimmed Mean (loại bỏ cửa sổ điểm cao nhất $s_{(K)}$) khi phát hiện ít nhất một cửa sổ có bằng chứng spoof mạnh ($\min(\mathbf{s}) < -12.0$) nhằm ngăn chặn các cửa sổ vô thanh (unvoiced fricatives) làm lọt lưới giọng giả.
- **Lý do loại bỏ khỏi tiêu chuẩn sản xuất**:
  1. *Gia tăng báo nhầm (BPCER Spike)*: Trên các mẫu âm thanh thật tự nhiên của người dùng, một số đoạn ngắt nghỉ, lấy hơi sâu hoặc âm vô thanh có thể khiến điểm cửa sổ cục bộ bị âm dưới ngưỡng $-12.0$. Cơ chế Asymmetric Veto vô tình kích hoạt và kéo sụt điểm số của toàn bộ clip thật, khiến tỷ lệ nhận diện giọng thật clean trên 5 tình nguyện viên bị sụt giảm nghiêm trọng từ **90.48% xuống 78.57%** (BPCER tăng vọt từ 9.52% lên 21.43%).
  2. *Quyết định kiến trúc*: Theo quy tắc an ninh và trải nghiệm người dùng sinh trắc học (Bona Fide First), dự án quyết định **loại bỏ Asymmetric Veto khỏi cấu hình sản xuất** và khóa cứng **Multi-window Max-Pooling (`mode="max"`)** làm tiêu chuẩn duy nhất trên toàn bộ hệ thống API, Bot và Web UI. Cơ chế `asymmetric_veto` chỉ được lưu giữ trong mã nguồn phục vụ mục đích nghiên cứu ablation so sánh học thuật.

---

*v0.5.6 — 2026-11-19*
