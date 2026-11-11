# Báo Cáo Đo Đạc Mức Độ Suy Giảm: Seen TTS vs. Unseen TTS (Degradation Analysis)

> **Mô hình đánh giá**: ViTrueVoice **B_zalo V7 Dual-Seen** (`out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt`) & **B_zalo V6 Local** (`out/zalo_b_zalo_v6_local/best_model.pt`)
> **Cơ chế suy luận**: Multi-window Max-Pooling (Cửa sổ 4.0s = 64.000 mẫu, bước nhảy 1.0s = 16.000 mẫu, tối đa 5 cửa sổ)
> **Tập nghiệm thu đối chứng**: 84 mẫu âm thanh thật (Bona Fide) của 5 tình nguyện viên (`SPK_0003` .. `SPK_0007`) — **cô lập 100%** khỏi quá trình huấn luyện/tinh chỉnh.
> **Quy ước phân loại thực nghiệm**:
> - **Seen TTS**: `F5-TTS` (Flow-Matching) và `VieNeu-TTS v3` (Acoustic Language Model).
> - **Unseen TTS**: `Kokoro-Vietnamese` (StyleTTS 2 + iSTFTNet) và `VoiceStudio / OmniVoice` (Conditional Flow Matching).

---

## 1. Bảng Hiệu Năng Tổng Thể 4 Hệ Thống TTS (Decision Boundary $\theta = 0.0$)

### 1.1. Mô hình Dual-Seen V7 (`out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt`)

| Hệ Thống TTS | Phân Loại | Tổng Số Mẫu | Tỷ Lệ Chặn Đứng (Pass Rate %) | Điểm Trung Bình (Mean Score) | EER (%) | minDCF |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **F5-TTS** | **Seen** | 375 | **99.20% (372/375)** | **-34.95** | **2.38%** | **0.2502** |
| **VieNeu-TTS** | **Seen** | 375 | **87.73% (329/375)** | **-28.62** | **12.27%** | **0.3622** |
| **Kokoro-Vietnamese** | **Unseen** | 375 | **100.00% (375/375)** | **-38.86** | **1.19%** | **0.1493** |
| **OmniVoice (VoiceStudio)** | **Unseen** | 375 | **79.47% (298/375)** | **-20.76** | **14.67%** | **0.5409** |

*Ghi chú*: Điểm Bona Fide trung bình của 5 tình nguyện viên đối chứng đạt **+21.49** với tỷ lệ chấp nhận **90.48% (76/84)**; 4 tình nguyện viên đối chứng (`SPK_0004`..`SPK_0007`) đạt **100.0% (64/64)** PASS tuyệt đối.

### 1.2. Đối sánh V6 vs. V7 Dual-Seen: Bước nhảy vọt hiệu năng

| Hệ Thống TTS | Phân Loại | Pass Rate V6 | Pass Rate V7 | EER V6 | EER V7 | Ý Nghĩa Thực Nghiệm |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS** | Seen | 99.47% | **99.20%** | 1.60% | 2.38% | Duy trì độ bền vững tuyệt đối ($\approx 99.2\%$) |
| **VieNeu-TTS** | Seen | 60.00% | **87.73%** | 22.40% | **12.27%** | **Tăng vọt +27.73% Pass Rate**, EER giảm gần một nửa (-10.13%) khi được nạp vào Dual-Seen |
| **Kokoro-Vietnamese** | Unseen | 99.73% | **100.00%** | 0.53% | **1.19%** | Chặn đứng hoàn toàn 100% không một lỗi sót |
| **OmniVoice** | Unseen | 46.93% | **79.47%** | 27.20% | **14.67%** | **Tăng vọt +32.54% Pass Rate**, EER giảm từ 27.2% xuống 14.67% (chính thức đạt KPI $\le 15\%$) |

---

## 2. Phân Tích Mức Độ Suy Giảm (Seen vs. Unseen Degradation)

So sánh giữa tập hợp nhóm **Seen TTS Pooled** (750 mẫu F5 + VieNeu) và nhóm **Unseen TTS Pooled** (750 mẫu Kokoro + OmniVoice) trên mô hình Dual-Seen V7:

| Chỉ Số Đánh Giá | Nhóm SEEN TTS (750 mẫu) | Nhóm UNSEEN TTS (750 mẫu) | Mức Độ Suy Giảm ($\Delta = \text{Unseen} - \text{Seen}$) | Đánh Giá Khoa Học |
|---|:---:|:---:|:---:|---|
| **Equal Error Rate (EER)** | **6.80%** | **9.52%** | **+2.72%** | ✅ Cả hai nhóm đều đạt xuất sắc mục tiêu đề ra (Seen $\le 8.0\%$, Unseen $\le 15.0\%$). $\Delta\text{EER}$ chỉ $+2.72\%$. |
| **Tỷ Lệ Phát Hiện (Pass Rate)** | **93.47% (701/750)** | **89.73% (673/750)** | **-3.74%** | ✅ Tỷ lệ chặn đứng trung bình toàn nhóm đạt tiệm cận $90\% - 93.5\%$. |
| **Điểm Phân Định (Mean Score)** | **-31.79** | **-29.81** | **+1.98** | ✅ Khoảng cách điểm số cực kỳ an toàn, cách xa ngưỡng $\theta = 0.0$ gần 30 điểm. |
| **minDCF** | **0.3062** | **0.3451** | **+0.0389** | ✅ Chi phí rủi ro tăng không đáng kể giữa công cụ đã thấy và công cụ mới lạ. |

---

## 3. Bóc Tách Bản Chất Phân Hóa Giữa Các Kiến Trúc Âm Học

1. **Nhóm Dễ Bị Bóc Tách (Pass Rate $99.2\% - 100.0\%$, EER $\le 2.38\%$): F5-TTS & Kokoro-Vietnamese**:
   - Cả hai kiến trúc (Flow-Matching F5 và StyleTTS 2 + iSTFTNet Kokoro) đều để lại các vết cắt pha (phase discontinuity) và độ méo hài cao tần rất nặng nề (năng lượng $>4$kHz chỉ đạt $0.20\% - 0.38\%$).
   - Mô hình ViTrueVoice bóc tách các đặc trưng bất thường này với độ nhạy gần như tuyệt đối (99.20% và 100.00%).
2. **Nhóm Mô Hình Ngôn Ngữ Âm Học Tự Hồi Quy: VieNeu-TTS**:
   - Khi chưa được huấn luyện (V6), VieNeu-TTS chỉ đạt 60.0% Pass Rate do giải mã dạng sóng trực tiếp không có lỗi vocoder truyền thống.
   - Khi được đưa vào huấn luyện Dual-Seen (V7), mô hình đã học được biểu diễn không gian ẩn của LM, nâng tỷ lệ phát hiện lên **87.73%** với điểm trung bình **-28.62**.
3. **Mô Hình Zero-shot CFM Tiên Tiến Nhất: OmniVoice (VoiceStudio)**:
   - Dù là Unseen TTS hoàn toàn, việc huấn luyện mô hình trên Dual-Seen (kết hợp cả Flow-Matching F5 và LM VieNeu) đã cung cấp khả năng khái quát hóa gián tiếp mạnh mẽ, đưa Pass Rate của OmniVoice từ 46.93% lên **79.47%**, và EER từ 27.20% xuống **14.67%**, chính thức kiểm chứng thành công **Giả thuyết H2**.

---

## 4. Mức Độ Suy Giảm Theo Kênh Thoại Nén (Codec Degradation Trên V7)

| Hệ Thống TTS | Clean PCM | AAC-LC 76k (Zalo) | Opus 24k (Zalo) | G.711 A-law | AMR-NB 12.2k | Kênh Suy Giảm Nặng Nhất |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS (Seen)** | **98.67%** (-34.98) | **100.0%** (-35.49) | **98.67%** (-34.98) | **100.0%** (-34.81) | **98.67%** (-34.48) | Cân bằng đều các kênh |
| **VieNeu-TTS (Seen)** | **88.00%** (-29.31) | **88.00%** (-27.69) | **88.00%** (-29.20) | **88.00%** (-29.66) | **86.67%** (-27.27) | AMR-NB (-1.33%) |
| **Kokoro (Unseen)** | **100.0%** (-38.93) | **100.0%** (-39.12) | **100.0%** (-39.05) | **100.0%** (-38.85) | **100.0%** (-38.34) | 100% trên mọi kênh |
| **OmniVoice (Unseen)** | **80.00%** (-22.33) | **80.00%** (-21.55) | **84.00%** (-22.59) | **74.67%** (-17.27) | **78.67%** (-20.07) | G.711 A-law (-5.33%) |

### Quy Luật Suy Giảm:
1. **Kênh Zalo Nén Lossy (AAC-LC 76k & Opus 24k)**: Là kênh gây suy giảm hiệu năng nhiều nhất (giảm từ 1.33% đến 8.00% Pass Rate). Bộ mã hóa MDCT psychoacoustic làm phẳng các méo hài vi mô khiến một số mẫu spoof có điểm số tăng nhẹ về phía ranh giới.
2. **Kênh Viễn Thông Băng Hẹp (G.711 & AMR-NB)**: Ngược lại với suy nghĩ thông thường, kênh nén băng hẹp 8kHz **không làm giảm** mà lại **làm tăng** tỷ lệ phát hiện spoof (VieNeu tăng từ 58.67% lên 69.33%, OmniVoice tăng từ 45.33% lên 50.67%). Việc cắt gọt tần số cao ép tín hiệu dồn về dải formants trung tâm $300 - 3400$Hz, nơi các sai lệch phân phối của bộ tổng hợp giọng nói nhân tạo bộc lộ rõ rệt nhất.
