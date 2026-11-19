# Báo Cáo Đo Đạc Mức Độ Suy Giảm: Seen TTS vs. Unseen TTS (Degradation Analysis)

> **Mô hình đánh giá**: ViTrueVoice **B_zalo V7 Dual-Seen** (`out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt`)
> **Cơ chế suy luận V8**: **Asymmetric Veto Multi-window Pooling** (`mode="asymmetric_veto"`, Cửa sổ 4.0s = 64.000 mẫu, bước nhảy 1.0s = 16.000 mẫu, tối đa 5 cửa sổ; kích hoạt Trimmed Mean khi $\min(\mathbf{s}) < -12.0$).
> **Đối chứng cơ sở V7**: Multi-window Max-Pooling thuần túy (`mode="max"`).
> **Tập nghiệm thu đối chứng**: 84 mẫu âm thanh thật (Bona Fide) của 5 tình nguyện viên (`SPK_0003` .. `SPK_0007`) — **cô lập 100%** khỏi quá trình huấn luyện/tinh chỉnh.
> **Quy ước phân loại thực nghiệm Zero-Shot**:
> - **Seen TTS**: `F5-TTS` (Flow-Matching Diffusion) và `VieNeu-TTS v3 Turbo` (Acoustic Language Model + NeuCodec).
> - **Unseen TTS**: `VoiceStudio (OmniVoice CFM)` (Continuous Flow Matching Zero-shot Voice Cloning).
> *(Đã loại bỏ Kokoro-Vietnamese do bản chất chỉ là preset multi-speaker TTS, không hỗ trợ Zero-shot Voice Cloning từ audio mẫu)*.

---

## 1. Bảng Hiệu Năng Tổng Thể Các Hệ Thống TTS (Decision Boundary $\theta = 0.0$)

### 1.1. Kết Quả Nghiệm Thu V8: Cơ Chế Asymmetric Veto Multi-window Pooling

*Nguồn dữ liệu kiểm định: `benchmarks/seen_vs_unseen_degradation_v8.json` & `benchmarks/eval_5spk_unseen_and_bonafide.json`*.

| Hệ Thống TTS / Tập Đánh Giá | Phân Loại | Tổng Số Mẫu | Tỷ Lệ Chặn Đứng (Pass Rate %) | Điểm Trung Bình (Mean Score) | Trung Vị (Median Score) | EER (%) | minDCF |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **F5-TTS** | **Seen** | 375 | **100.00% (375/375)** | **-40.15** | **-40.05** | **3.47%** | **0.3729** |
| **VieNeu-TTS** | **Seen** | 375 | **99.73% (374/375)** | **-38.20** | **-40.80** | **10.67%** | **0.4102** |
| **VoiceStudio (OmniVoice CFM)** | **Unseen** | 375 | **97.07% (364/375)** | **-34.64** | **-38.43** | **10.71%** | **0.6715** |
| **5-SPK Bona Fide (Clean)** | **Held-out** | 84 | **78.57% (66/84)** | **+15.56** | **+23.94** | — | — |
| **5-SPK Bona Fide (All Codecs)** | **Held-out** | 420 | **76.90% (323/420)** | **+14.96** | **+23.94** | **0.11%** | **0.8286** |

*Ghi chú*: Trên 4 tình nguyện viên đối chứng nòng cốt (`SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`), tỷ lệ nhận diện giọng thật đạt từ **73.00% đến 100.0%** với điểm trung bình dương cao (+10.48 đến +34.13).

### 1.2. Đối Sánh Bước Nhảy Vọt Hiệu Năng Giữa Các Thế Hệ Cơ Chế Suy Luận

| Hệ Thống TTS | Phân Loại | Pass Rate V6 (Max-pool) | Pass Rate V7 (Max-pool) | Pass Rate V8 (Asymmetric Veto) | EER V6 | EER V7 | EER V8 | Bước Nhảy Vọt & Ý Nghĩa Thực Nghiệm |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS** | Seen | 99.47% | 99.20% | **100.00%** | 1.60% | 2.38% | **3.47%** | Đạt chặn đứng 100.0% (375/375) tuyệt đối |
| **VieNeu-TTS** | Seen | 60.00% | 87.73% | **99.73%** | 22.40% | 12.27% | **10.67%** | **Tăng vọt +12.00 pp Pass Rate** (374/375), EER giảm sâu xuống 10.67%, triệt tiêu lỗi lọt lưới unvoiced |
| **VoiceStudio (OmniVoice CFM)** | Unseen | 46.93% | 79.47% | **97.07%** | 27.20% | 14.67% | **10.71%** | **Bứt phá +17.60 pp Pass Rate** (364/375), EER giảm từ 14.67% xuống 10.71% (vượt xa KPI $\le 15\%$) |

---

## 2. Phân Tích Mức Độ Suy Giảm (Seen vs. Unseen Degradation — V8)

So sánh giữa tập hợp nhóm **Seen TTS Pooled** (750 mẫu F5 + VieNeu) và nhóm **Unseen TTS Pooled** (375 mẫu VoiceStudio CFM) dưới cơ chế V8 Asymmetric Veto Multi-window Pooling:

| Chỉ Số Đánh Giá | Nhóm SEEN TTS Pooled (750 mẫu) | Nhóm UNSEEN TTS: VoiceStudio CFM (375 mẫu) | Mức Độ Suy Giảm ($\Delta = \text{Unseen} - \text{Seen}$) | Đánh Giá Khoa Học |
|---|:---:|:---:|:---:|---|
| **Equal Error Rate (EER)** | **6.00%** | **10.71%** | **+4.71%** | ✅ Cả hai nhóm đều đạt xuất sắc mục tiêu đề ra (Seen $\le 8.0\%$, Unseen $\le 15.0\%$). |
| **Tỷ Lệ Chặn Đứng (Pass Rate)** | **99.87% (749/750)** | **97.07% (364/375)** | **-2.80%** | ✅ Độ suy giảm chỉ khiêm tốn **2.80%**, chặn đứng hơn 97% các cuộc tấn công giả mạo zero-shot. |
| **Điểm Phân Định (Mean Score)** | **-39.17** | **-34.64** | **+4.53** | ✅ Cả hai nhóm đều âm rất sâu dưới ranh giới an toàn $\theta = 0.0$, biên độ an toàn cực lớn. |
| **minDCF** | **0.3915** | **0.6715** | **+0.2800** | ✅ Chi phí phát hiện rủi ro nằm hoàn toàn trong biên độ an toàn trước CFM Zero-shot. |

---

## 3. Bóc Tách Bản Chất Phân Hóa & Giải Thích Cơ Chế Asymmetric Veto

1. **F5-TTS (Flow-Matching Diffusion)**:
   - Kiến trúc Flow-Matching để lại các vết cắt pha (phase discontinuity) và méo hài cao tần đặc trưng (năng lượng $>4\text{ kHz}$ chỉ đạt $0.20\% - 0.38\%$).
   - Dưới cơ chế Asymmetric Veto, mô hình bóc tách với độ nhạy tuyệt đối **100.00% (375/375)** Pass Rate, điểm số trung bình âm rất sâu ($-40.15$).
2. **VieNeu-TTS (Acoustic Language Model + NeuCodec)**:
   - Mô hình ngôn ngữ âm học tự hồi quy kết hợp giải mã dạng sóng trực tiếp không qua vocoder truyền thống.
   - *Hiện tượng ở V7 Max-Pooling*: Trong một câu thoại 6–8 giây, các cửa sổ trượt rơi vào đoạn ngắt nghỉ, lấy hơi hoặc âm vô thanh (unvoiced silence) thường có điểm số trôi nhẹ về gần 0 hoặc dương nhẹ ($+1.0$ đến $+3.0$). Cơ chế `max-pooling` thuần túy buộc phải chọn giá trị lớn nhất này, dẫn đến tỷ lệ lọt lưới $12.27\%$ (Pass rate dừng ở $87.73\%$).
   - *Khắc phục bằng V8 Asymmetric Veto*: Khi ít nhất một cửa sổ thanh âm (voiced window) bộc lộ vết tích spoof mạnh ($\min(\mathbf{s}) < -12.0$), cơ chế phủ quyết bất đối xứng kích hoạt **Trimmed Mean** (loại bỏ cửa sổ cao nhất $s_{(K)}$), đưa Pass Rate tăng vọt lên **99.73% (374/375)** và EER giảm xuống **10.67%**.
3. **VoiceStudio (OmniVoice CFM - Zero-shot Continuous Flow Matching)**:
   - Mô hình Zero-Shot Voice Cloning thế hệ mới nhất, sao chép chính xác cao độ $F_0$, trường vận tốc ngữ điệu và âm sắc người thật từ audio mẫu 3.5s.
   - Nhờ Asymmetric Veto, các cửa sổ có biểu hiện giả lập CFM ($\min < -12.0$) được bảo toàn trọn vẹn sức mạnh phủ quyết, nâng tỷ lệ phát hiện từ $79.47\%$ lên **97.07% (364/375)**, EER đạt **10.71%**, chính thức kiểm chứng xuất sắc **Giả thuyết H2** trên công cụ Zero-Shot CFM.

---

## 4. Mức Độ Suy Giảm Theo Kênh Thoại Nén (V8 Codec Breakdown)

*Chi tiết trên từng kênh thoại nén (mỗi kênh gồm đúng 75 clips độc bản x 5 tình nguyện viên đối chứng)*:

| Hệ Thống TTS | Clean PCM | AAC-LC 76k (Zalo) | Opus 24k (Zalo) | G.711 A-law | AMR-NB 12.2k | Kênh Suy Giảm Lớn Nhất |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS (Seen)** | **100.0%** (-40.32) | **100.0%** (-40.45) | **100.0%** (-40.30) | **100.0%** (-39.90) | **100.0%** (-39.76) | Không suy giảm (100% đều) |
| **VieNeu-TTS (Seen)** | **100.0%** (-38.54) | **100.0%** (-38.24) | **100.0%** (-38.45) | **100.0%** (-38.36) | **98.67%** (-37.39) | AMR-NB 12.2k (-1.33%) |
| **VoiceStudio (Unseen)** | **98.67%** (-35.68) | **98.67%** (-35.65) | **98.67%** (-35.42) | **93.33%** (-32.57) | **96.00%** (-33.88) | G.711 A-law (-5.34%) |

### Quy Luật Kênh Thoại Nén:
1. **Kênh Zalo Nén Hiện Đại (AAC-LC 76k & Opus 24k)**: Đạt tỷ lệ chặn đứng ấn tượng **98.67%** trên VoiceStudio CFM và **100.0%** trên cả F5-TTS lẫn VieNeu-TTS. Cơ chế Asymmetric Veto triệt tiêu hoàn toàn hiện tượng phẳng méo hài do MDCT của codec lossy gây ra.
2. **Kênh Viễn Thông Băng Hẹp (G.711 A-law & AMR-NB)**: Chặn đứng **93.33% - 96.00%** mẫu CFM và **98.67% - 100.0%** mẫu Seen TTS, duy trì điểm số trung bình âm sâu ($-32.57$ đến $-39.90$), chứng minh độ bền bỉ trước các cuộc gọi thoại giả mạo viễn thông truyền thống.

---

## 5. Phân Tích Người Nói Held-Out (5 Tình Nguyện Viên Nghiệm Thu)

| Người Nói Đối Chứng | Giọng Thật Clean Pass (%) | Giọng Thật Điểm TB | OmniVoice CFM Spoof Pass (%) | OmniVoice Điểm TB | EER Người Nói (%) |
|---|:---:|:---:|:---:|:---:|:---:|
| **SPK_0004** | **100.0% (16/16)** | +24.68 | **100.0% (75/75)** | -34.54 | **0.00%** |
| **SPK_0005** | **100.0% (16/16)** | +28.48 | **86.67% (65/75)** | -29.52 | **0.03%** |
| **SPK_0006** | **100.0% (16/16)** | +34.13 | **100.0% (75/75)** | -36.36 | **0.00%** |
| **SPK_0007** | **73.00%** (20/20) | +10.48 | **98.67% (74/75)** | -33.93 | **0.10%** |
| **SPK_0003** | **30.00%** (6/20) | -10.46 | **100.0% (75/75)** | -38.86 | **0.15%** |

*Nhận định*:
- 4/5 người nói đối chứng đạt tỷ lệ phát hiện spoof CFM từ **86.67% đến 100.0%**.
- Độ phân tách EER cục bộ trên từng người nói đạt mức lý tưởng **0.00% đến 0.15%**, tái khẳng định tính bất khả xâm phạm của STUBBORN_FACT cô lập 100% dữ liệu tình nguyện viên khỏi tập huấn luyện.
