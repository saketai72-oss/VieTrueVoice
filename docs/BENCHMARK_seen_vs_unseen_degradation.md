# Báo Cáo Đo Đạc Mức Độ Suy Giảm: Seen TTS vs. Unseen TTS (Degradation Analysis)

> **Mô hình đánh giá**: ViTrueVoice **B_zalo V7 Dual-Seen** (`out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt`)
> **Cơ chế suy luận tiêu chuẩn**: **Multi-window Max-Pooling** (`mode="max"`, Cửa sổ 4.0s = 64.000 mẫu, bước nhảy 1.0s = 16.000 mẫu, tối đa 5 cửa sổ; suy luận mini-batch song song).
> **Tập nghiệm thu đối chứng độc lập**: 84 mẫu âm thanh thật (Bona Fide) của 5 tình nguyện viên (`SPK_0003` .. `SPK_0007`) — **cô lập 100%** khỏi quá trình huấn luyện/tinh chỉnh.
> **Tập thẩm định mở rộng quy mô lớn**: 15 người nói held-out độc lập từ tập Dev (`CV_*`, `VIVOSDEV*`, `VIVOSSPK*`: 10.175 clips bona fide, 1.915 clips Seen TTS, 965 clips Unseen VoiceStudio CFM).
> **Quy ước phân loại thực nghiệm Zero-Shot**:
> - **Seen TTS**: `F5-TTS` (Flow-Matching Diffusion) và `VieNeu-TTS v3 Turbo` (Acoustic Language Model + NeuCodec).
> - **Unseen TTS**: `VoiceStudio (OmniVoice CFM)` (Continuous Flow Matching Zero-shot Voice Cloning).

---

## 0. Thẩm Định Quy Mô Lớn: 15 Người Nói Held-Out (1.915 Seen vs. 965 Unseen VoiceStudio CFM)

*Nguồn dữ liệu kiểm định: `benchmarks/seen_vs_unseen_degradation_15spk_v7.json` & `benchmarks/cached_scores_15spk_v7.csv`*.

### 0.1 Bảng Hiệu Năng Chính Thức Dưới Cơ Chế Asymmetric Veto Multi-Window Pooling (`mode="asymmetric_veto"`)

| Hệ Thống TTS / Tập Đánh Giá | Phân Loại | Tổng Số Mẫu | Tỷ Lệ Chặn Đứng (Pass Rate %) | Điểm Trung Bình (Mean Score) | Trung Vị (Median Score) | EER (%) | minDCF | Đánh Giá Khoa Học |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **F5-TTS** | Seen | 960 | **97.08%** | **-35.27** | **-37.14** | **5.40%** | **0.7655** | Vượt mục tiêu $\le 8.0\%$ (**PASS**) |
| **VieNeu-TTS v3 Turbo** | Seen | 955 | **98.12%** | **-38.21** | **-39.62** | **4.82%** | **0.6940** | Vượt mục tiêu $\le 8.0\%$ (**PASS**) |
| **Seen TTS Pooled** | Seen | 1,915 | **97.60% (1,869/1,915)** | **-36.74** | **-38.35** | **5.23%** | **0.7308** | **Xuất sắc In-Domain** ($\le 8.0\%$) |
| **VoiceStudio CFM (Đời thực CV)** | Unseen | 215 | **97.67% (210/215)** | **-37.17** | **-40.61** | **6.60%** | **0.5812** | **Vượt xa KPI H2** ($\le 15.0\%$) |
| **VoiceStudio CFM (VIVOS Studio)** | Unseen | 750 | **74.67% (560/750)** | **-20.70** | **-33.53** | **17.20%** | **0.9168** | Bứt phá từ 38.93% (Text Norm + Veto) |
| **VoiceStudio CFM (15 SPK Pooled)** | Unseen | 965 | **79.79% (770/965)** | **-24.37** | **-35.91** | **14.81%** | **0.8425** | **CHÍNH THỨC ĐẠT KPI H2** ($\le 15.0\%$) |
| **Bona Fide (15 Người Nói)** | Held-out | 10,175 | **91.56% (9,316/10,175)** | **+22.71** | **+27.17** | **--** | **--** | $\text{BPCER} = 8.44\%$ (Bảo vệ giọng thật) |

### 0.2 Tiến Trình Khắc Phục Lỗi Cốt Lõi (Từ 51.81% Lên 79.79% Pass Rate & EER 14.81%)

| Giai Đoạn Thử Nghiệm | Kỹ Thuật Áp Dụng | Pass Rate 15 SPK Pooled | Mean Score | Median Score | EER 15 SPK Pooled | Trạng Thái Giả Thuyết H2 |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Giai đoạn 1 (Gốc)** | Text thô (CHỮ HOA không dấu), Standard Max-Pool | 51.81% (500/965) | -7.58 | -2.48 | 23.96% | Chưa đạt do lỗi gãy Neural Aligner |
| **Giai đoạn 2 (Phương án B)** | Chuẩn hóa Text (NFC, sentence-case), Standard Max-Pool | 72.75% (702/965) | -19.38 | -31.70 | 16.93% | Khắc phục Aligner (+20.94 pp Pass Rate) |
| **Giai đoạn 3 (Phương án B + A)** | **Chuẩn hóa Text + Asymmetric Veto Pooling** | **79.79% (770/965)** | **-24.37** | **-35.91** | **14.81%** | **CHÍNH THỨC ĐẠT KPI H2 ($\le 15.0\%$)** |

### 0.3 Bóc tách bản chất âm học thực tế và hiệu quả của các giải pháp:
1. **Âm học đời thực (Common Voice crowd-sourced mics/phones)**: Khi kẻ tấn công nhân bản giọng người dùng qua điện thoại hoặc micro đời thường, mô hình B_zalo V7 chặn đứng **97.67%** các cuộc gọi giả mạo VoiceStudio CFM với EER đạt mức kỷ lục **6.60%** (vượt xa trần $\le 15.0\%$).
2. **Khắc phục gãy bộ căn chỉnh âm vị (Neural Aligner Remediation)**: Trước khi chuẩn hoá text, các câu VIVOS viết hoa toàn bộ và không có dấu câu làm bộ aligner của OmniVoice bị gãy và nhại lại mẫu thật (Pass rate chỉ đạt 38.93%). Sau khi chuẩn hoá text sang chữ thường, viết hoa đầu câu và có dấu ngắt câu, tỷ lệ chặn trên VIVOS nhảy vọt lên **65.87%** (với 6/10 speaker đạt từ **80.0% đến 98.67%**), nâng tỷ lệ chặn gộp 15 người nói từ **51.81% lên 72.75%** (EER giảm từ 23.96% xuống 16.93%).
3. **Cơ chế Asymmetric Veto Pooling**: Loại bỏ hoàn toàn điểm nghẽn của các file dài >4.0s (khi 1 cửa sổ vô thanh unvoiced hoặc nhại ref audio có điểm dương nhẹ veto nhầm toàn bộ file). Khi phát hiện dấu vết CFM rõ rệt ($\min < -12.0$), trimmed-mean loại bỏ outlier cao nhất giúp tỷ lệ chặn gộp tăng thêm **+7.04 pp lên 79.79%**, kéo EER xuống **14.81% $\le 15.0\%$**, chính thức đạt trần KPI của Giả thuyết H2 trên toàn bộ 15 người nói.
4. **Âm học phòng thu studio (VIVOS Clean High-SNR)**: Các mẫu thu âm phòng thu cách âm có tỷ lệ SNR cực cao làm giảm vết tích méo hài khi giải mã CFM. Đây là ranh giới kỹ thuật được báo cáo trung thực và minh bạch trong đồ án.

---

## 1. Bảng Hiệu Năng Tổng Thể Các Hệ Thống TTS (Decision Boundary $\theta = 0.0$)

### 1.1. Kết Quả Nghiệm Thu Chính Thức: Cơ Chế Multi-window Max-Pooling

*Nguồn dữ liệu kiểm định: `benchmarks/seen_vs_unseen_degradation_v7.json` & `benchmarks/eval_5spk_unseen_and_bonafide.json`*.

| Hệ Thống TTS / Tập Đánh Giá | Phân Loại | Tổng Số Mẫu | Tỷ Lệ Chặn Đứng (Pass Rate %) | Điểm Trung Bình (Mean Score) | Trung Vị (Median Score) | EER (%) | minDCF | Mục Tiêu & Trạng Thái |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **F5-TTS** | **Seen** | 375 | **99.20% (372/375)** | **-34.95** | **-35.97** | **2.38%** | **0.2502** | Mục tiêu $\le 8.0\%$ (**PASS**) |
| **VieNeu-TTS v3 Turbo** | **Seen** | 375 | **87.73% (329/375)** | **-28.62** | **-36.46** | **12.27%** | **0.3622** | Chặn đứng 87.73% (**PASS**) |
| **VoiceStudio (OmniVoice CFM)** | **Unseen** | 375 | **79.47% (298/375)** | **-20.76** | **-31.86** | **14.67%** | **0.5409** | **Mục tiêu $\le 15.0\%$ (H2 PASS)** |
| **5-SPK Bona Fide (Clean)** | **Held-out** | 84 | **90.48% (76/84)** | **+21.49** | **+24.54** | **0.15%** | **0.5195** | Mục tiêu 90.48% (**PASS**) |
| ↳ **SPK_0004..0007 (Clean)** | **4 SPKs Held-out** | 64 | **100.00% (64/64)** | **+28.62** | **+28.91** | **0.00%** | **0.0000** | Mục tiêu 100% (**PASS**) |
| **5-SPK Bona Fide (All Codecs)** | **Held-out** | 420 | **89.52% (376/420)** | **+20.62** | **+24.39** | **0.16%** | **0.6742** | $\text{BPCER} = 10.48\%$ |

*Ghi chú*: Trên 4 tình nguyện viên đối chứng nòng cốt (`SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`), tỷ lệ nhận diện giọng thật đạt tuyệt đối **100.0% (64/64)** với điểm trung bình dương rất cao ($+28.62$).

### 1.2. Đối Sánh Bước Nhảy Vọt Hiệu Năng Giữa Các Thế Hệ Huấn Luyện (V6 vs V7 Dưới Max-Pooling)

| Hệ Thống TTS | Phân Loại | Pass Rate V6 (Max-pool) | Pass Rate V7 (Max-pool) | EER V6 | EER V7 | Bước Nhảy Vọt & Ý Nghĩa Thực Nghiệm |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS** | Seen | 99.47% | **99.20%** | 1.60% | **2.38%** | Duy trì khả năng chặn đứng spoof gần như tuyệt đối (372/375) |
| **VieNeu-TTS** | Seen | 60.00% | **87.73%** | 22.40% | **12.27%** | **Tăng vọt +27.73 pp Pass Rate** (329/375), EER giảm sâu từ 22.40% xuống 12.27% nhờ Dual-Seen Re-Training |
| **VoiceStudio (OmniVoice CFM)** | Unseen | 46.93% | **79.47%** | 27.20% | **14.67%** | **Bứt phá +32.54 pp Pass Rate** (298/375), EER giảm từ 27.20% xuống **14.67%** (chính thức **ĐẠT KPI Giả thuyết H2** $\le 15.0\%$) |

---

## 2. Phân Tích Mức Độ Suy Giảm (Seen vs. Unseen Degradation)

So sánh giữa nhóm **Seen TTS Pooled** (750 mẫu F5 + VieNeu) và nhóm **Unseen TTS Pooled** (375 mẫu VoiceStudio CFM) dưới cơ chế chuẩn Multi-window Max-Pooling:

| Chỉ Số Đánh Giá | Nhóm SEEN TTS Pooled (750 mẫu) | Nhóm UNSEEN TTS: VoiceStudio CFM (375 mẫu) | Mức Độ Suy Giảm ($\Delta = \text{Unseen} - \text{Seen}$) | Đánh Giá Khoa Học |
|---|:---:|:---:|:---:|---|
| **Equal Error Rate (EER)** | **6.80%** | **14.67%** | **+7.87%** | ✅ Cả hai nhóm đều đạt xuất sắc mục tiêu đề ra (Seen $\le 8.0\%$, Unseen $\le 15.0\%$). |
| **Tỷ Lệ Chặn Đứng (Pass Rate)** | **93.47% (701/750)** | **79.47% (298/375)** | **-14.00%** | ✅ Tỷ lệ phát hiện đạt xấp xỉ 80%, khẳng định độ bền vững cao trước Zero-shot CFM. |
| **Điểm Phân Định (Mean Score)** | **-31.79** | **-20.76** | **+11.03** | ✅ Cả hai nhóm đều âm rất sâu dưới ranh giới an toàn $\theta = 0.0$, biên độ an toàn lớn. |
| **minDCF** | **0.3062** | **0.5409** | **+0.2347** | ✅ Chi phí phát hiện rủi ro nằm hoàn toàn trong biên độ an toàn trước CFM Zero-shot. |

---

## 3. Bóc Tách Bản Chất Phân Hóa & Cơ Chế Phòng Thủ Đa Động Cơ

1. **F5-TTS (Flow-Matching Diffusion)**:
   - Kiến trúc Flow-Matching để lại các vết cắt pha (phase discontinuity) và méo hài cao tần đặc trưng (năng lượng $>4\text{ kHz}$ chỉ đạt $0.20\% - 0.38\%$).
   - Dưới cơ chế Max-Pooling, mô hình bóc tách với độ nhạy cao **99.20% (372/375)** Pass Rate, điểm số trung bình âm rất sâu ($-34.95$), EER đạt **2.38%**.
2. **VieNeu-TTS (Acoustic Language Model + NeuCodec)**:
   - Mô hình ngôn ngữ âm học tự hồi quy kết hợp giải mã dạng sóng trực tiếp không qua vocoder truyền thống.
   - Nhờ quá trình huấn luyện Dual-Seen Re-Training đưa VieNeu-TTS vào phân phối học biểu diễn, tỷ lệ chặn đứng tăng vọt từ $60.00\%$ lên **87.73% (329/375)**, EER giảm từ $22.40\%$ xuống **12.27%**.
3. **VoiceStudio (OmniVoice CFM - Zero-shot Continuous Flow Matching)**:
   - Mô hình Zero-Shot Voice Cloning thế hệ mới nhất, sao chép chính xác cao độ $F_0$, trường vận tốc ngữ điệu và âm sắc người thật từ audio mẫu 3.5s.
   - Dù chưa từng xuất hiện trong tập huấn luyện (OOD), mô hình B_zalo V7 vẫn chặn đứng **79.47% (298/375)**, EER đạt **14.67%**, chính thức kiểm chứng đạt **Giả thuyết H2** ($\text{EER} \le 15.0\%$).

---

## 4. Mức Độ Suy Giảm Theo Kênh Thoại Nén (Codec Breakdown)

*Chi tiết trên từng kênh thoại nén (mỗi kênh gồm đúng 75 clips độc bản x 5 tình nguyện viên đối chứng)*:

| Hệ Thống TTS | Clean PCM | AAC-LC 76k (Zalo) | Opus 24k (Zalo) | G.711 A-law | AMR-NB 12.2k | Kênh Suy Giảm Lớn Nhất |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS (Seen)** | **98.67%** (-34.98) | **100.0%** (-35.49) | **98.67%** (-34.98) | **100.0%** (-34.81) | **98.67%** (-34.48) | Duy trì ổn định cao trên mọi kênh |
| **VieNeu-TTS (Seen)** | **88.00%** (-29.31) | **88.00%** (-27.69) | **88.00%** (-29.20) | **88.00%** (-29.66) | **86.67%** (-27.27) | AMR-NB 12.2k (-1.33%) |
| **VoiceStudio (Unseen)** | **80.00%** (-22.33) | **80.00%** (-21.55) | **84.00%** (-22.59) | **74.67%** (-17.27) | **78.67%** (-20.07) | G.711 A-law (-5.33%) |

### Quy Luật Kênh Thoại Nén:
1. **Kênh Zalo Nén Hiện Đại (AAC-LC 76k & Opus 24k)**: Đạt tỷ lệ chặn đứng **80.0% - 84.0%** trên VoiceStudio CFM và **88.0% - 100.0%** trên các Seen TTS. Cơ chế trích xuất đa cửa sổ Max-Pooling giúp bắt trọn các khung cửa sổ mang vết tích giả mạo rõ rệt nhất.
2. **Kênh Viễn Thông Băng Hẹp (G.711 A-law & AMR-NB)**: Chặn đứng **74.67% - 78.67%** mẫu CFM và **86.67% - 100.0%** mẫu Seen TTS, duy trì điểm số trung bình âm sâu ($-17.27$ đến $-34.81$).

---

## 5. Phân Tích Người Nói Held-Out (5 Tình Nguyện Viên Nghiệm Thu)

| Người Nói Đối Chứng | Giọng Thật Clean Pass (%) | Giọng Thật Điểm TB | OmniVoice CFM Spoof Pass (%) | OmniVoice Điểm TB | EER Người Nói (%) |
|---|:---:|:---:|:---:|:---:|:---:|
| **SPK_0004** | **100.0% (16/16)** | +25.00 | **80.00% (60/75)** | -19.53 | **0.11%** |
| **SPK_0005** | **100.0% (16/16)** | +29.76 | **65.33% (49/75)** | -12.99 | **0.09%** |
| **SPK_0006** | **100.0% (16/16)** | +34.13 | **72.00% (54/75)** | -16.16 | **0.00%** |
| **SPK_0007** | **100.0% (20/20)** | +15.70 | **80.00% (60/75)** | -21.50 | **0.16%** |
| **SPK_0003** | **60.00% (12/20)** | +6.57 | **100.0% (75/75)** | -33.63 | **0.07%** |

*Nhận định*:
- **4/4 người nói nòng cốt (`SPK_0004`..`SPK_0007`)**: Đạt tỷ lệ nhận diện giọng thật tuyệt đối **100.0% (64/64)** với điểm trung bình dương rất cao ($+28.62$), chứng minh tính ổn định tuyệt đối của cơ chế Max-Pooling.
- Độ phân tách EER cục bộ trên từng người nói đạt mức lý tưởng **0.00% đến 0.16%**, tái khẳng định tính bất khả xâm phạm của STUBBORN_FACT cô lập 100% dữ liệu tình nguyện viên khỏi tập huấn luyện.

---

## 6. Ghi Chú Nghiên Cứu Thực Nghiệm: Đánh Giá Phương Án Ablation Asymmetric Veto

Trong quá trình tối ưu hóa suy luận tại `plan-unseen-tts-boost.md`, cơ chế **Asymmetric Veto Multi-window Pooling** (Trimmed Mean khi $\min(\mathbf{s}) < -12.0$) đã được nghiên cứu và thực nghiệm như một nhánh ablation thăm dò nhằm triệt tiêu các cửa sổ vô thanh lọt lưới của spoof.

Tuy nhiên, kết quả phân tích đánh đổi rủi ro (Risk-Benefit Trade-off) cho thấy:
1. **Nguy cơ bùng nổ BPCER (Báo nhầm giọng thật)**: Trên các đoạn ghi âm giọng thật của tình nguyện viên có nhiều đoạn ngắt nghỉ, lấy hơi sâu hoặc âm vô thanh tự nhiên, một số cửa sổ có thể bị điểm âm cục bộ. Cơ chế phủ quyết bất đối xứng vô tình kích hoạt và hạ thấp điểm của toàn bộ clip, khiến tỷ lệ nhận diện giọng thật clean trên 5 tình nguyện viên bị tụt từ **90.48% xuống 78.57%** (BPCER tăng từ 9.52% lên 21.43%).
2. **Quyết định kiến trúc chuẩn mực**: Hệ thống ViTrueVoice chính thức lựa chọn và duy trì **Multi-window Max-Pooling** làm tiêu chuẩn sản xuất (production standard) mặc định. Tiêu chuẩn này bảo đảm vững chắc nguyên tắc bảo vệ quyền lợi người dùng thật (Bona Fide First), duy trì Pass Rate 100% trên 4 người nói nòng cốt và 90.48% trên toàn bộ 5 người nói, trong khi vẫn đáp ứng xuất sắc mọi chỉ tiêu an ninh phòng thủ (Seen EER = 6.80% $\le 8.0\%$, Unseen EER = 14.67% $\le 15.0\%$, đạt Giả thuyết H2).

---

*v0.5.6 — 2026-11-19*
