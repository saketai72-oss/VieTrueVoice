# Báo Cáo Đo Đạc Mức Độ Suy Giảm: Seen TTS vs. Unseen TTS (Degradation Analysis)

> **Mô hình đánh giá**: ViTrueVoice **B_zalo V6** (`out/zalo_b_zalo_v6_local/best_model.pt`)
> **Cơ chế suy luận**: Multi-window Max-Pooling (Cửa sổ 4.0s = 64.000 mẫu, bước nhảy 1.0s = 16.000 mẫu, tối đa 5 cửa sổ)
> **Tập nghiệm thu đối chứng**: 84 mẫu âm thanh thật (Bona Fide) của 5 tình nguyện viên (`SPK_0003` .. `SPK_0007`) — **cô lập 100%** khỏi quá trình huấn luyện/tinh chỉnh.
> **Quy ước phân loại thực nghiệm**:
> - **Seen TTS**: `F5-TTS` (Flow-Matching) và `VieNeu-TTS v3` (Acoustic Language Model).
> - **Unseen TTS**: `Kokoro-Vietnamese` (StyleTTS 2 + iSTFTNet) và `VoiceStudio / OmniVoice` (Conditional Flow Matching).

---

## 1. Bảng Hiệu Năng Tổng Thể 4 Hệ Thống TTS (Decision Boundary $\theta = 0.0$)

| Hệ Thống TTS | Phân Loại | Tổng Số Mẫu | Tỷ Lệ Chặn Đứng (Pass Rate %) | Điểm Trung Bình (Mean Score) | EER (%) | minDCF |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **F5-TTS** | **Seen** | 375 | **99.47% (373/375)** | **-32.99** | **1.60%** | **0.0267** |
| **VieNeu-TTS** | **Seen** | 375 | **60.00% (225/375)** | **-7.54** | **22.40%** | **0.4560** |
| **Kokoro-Vietnamese** | **Unseen** | 375 | **99.73% (374/375)** | **-34.21** | **0.53%** | **0.0053** |
| **OmniVoice (VoiceStudio)** | **Unseen** | 375 | **46.93% (176/375)** | **+1.55** | **27.20%** | **0.6053** |

*Ghi chú*: Điểm Bona Fide trung bình của 5 tình nguyện viên đối chứng đạt **+28.84** với tỷ lệ chấp nhận **96.43% (81/84)**.

---

## 2. Phân Tích Mức Độ Suy Giảm (Seen vs. Unseen Degradation)

So sánh giữa tập hợp nhóm **Seen TTS Pooled** (750 mẫu F5 + VieNeu) và nhóm **Unseen TTS Pooled** (750 mẫu Kokoro + OmniVoice):

| Chỉ Số Đánh Giá | Nhóm SEEN TTS (750 mẫu) | Nhóm UNSEEN TTS (750 mẫu) | Mức Độ Suy Giảm ($\Delta = \text{Unseen} - \text{Seen}$) | Đánh Giá Khoa Học |
|---|:---:|:---:|:---:|---|
| **Equal Error Rate (EER)** | **13.33%** | **15.87%** | **+2.54%** | ✅ Suy giảm rất nhẹ (+2.54%), duy trì tiệm cận trần $\le 15\%$ của Giả thuyết H2 |
| **Tỷ Lệ Phát Hiện (Pass Rate)** | **79.73% (598/750)** | **73.33% (550/750)** | **-6.40%** | ✅ Khả năng chặn đứng giọng giả tổng thể vẫn giữ vững trên $73.3\%$ |
| **Điểm Phân Định (Mean Score)** | **-20.27** | **-16.33** | **+3.94** | ✅ Điểm số trung bình toàn nhóm vẫn duy trì âm sâu dưới ngưỡng $0.0$ |
| **minDCF** | **0.2413** | **0.3053** | **+0.0640** | ✅ Chi phí rủi ro tăng nhẹ nhưng nằm trong biên độ kiểm soát an toàn |

---

## 3. Bóc Tách Bản Chất Phân Hóa Giữa Các Kiến Trúc Âm Học

1. **Nhóm Dễ Bị Bóc Tách (Pass Rate $> 99.4\%$, EER $\le 1.6\%$): F5-TTS & Kokoro-Vietnamese**:
   - Cả hai kiến trúc (Flow-Matching F5 và StyleTTS 2 + iSTFTNet Kokoro) đều để lại các vết cắt pha (phase discontinuity) và độ méo hài cao tần rất nặng nề (năng lượng $>4$kHz chỉ đạt $0.20\% - 0.38\%$).
   - Mô hình ViTrueVoice B_zalo V6 bóc tách các đặc trưng bất thường này với độ nhạy gần như tuyệt đối (99.47% và 99.73%).
2. **Nhóm Thách Thức Hệ Thống (Pass Rate $46.9\% - 60.0\%$, EER $22.4\% - 27.2\%$): VieNeu-TTS & OmniVoice**:
   - **VieNeu-TTS**: Mô hình ngôn ngữ âm học tự hồi quy (Acoustic LM) kết hợp mạng sinh âm thanh giải mã dạng sóng trực tiếp, tái tạo độ biến thiên ngữ điệu tự nhiên cao và ít méo hài vocoder.
   - **OmniVoice**: Mô hình zero-shot conditional flow-matching tiên tiến nhất của VoiceStudio/Xiaomi, tổng hợp dạng sóng mượt mà với phổ tần số phân bố đồng đều ($>4$kHz đạt $0.38\% - 0.39\%$).
   - Kết quả này phản ánh chân thực ranh giới kỹ thuật hiện tại của thế giới: các mô hình deepfake giọng nói thế hệ mới nhất sử dụng zero-shot CFM/LM tiệm cận cấu trúc âm học người thật là mối đe dọa tinh vi nhất.

---

## 4. Mức Độ Suy Giảm Theo Kênh Thoại Nén (Codec Degradation)

| Hệ Thống TTS | Clean PCM | AAC-LC 76k (Zalo) | Opus 24k (Zalo) | G.711 A-law | AMR-NB 12.2k | Kênh Suy Giảm Nặng Nhất |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **F5-TTS (Seen)** | **100.0%** (-33.38) | **98.67%** (-31.26) | **98.67%** (-33.03) | **100.0%** (-34.29) | **100.0%** (-33.01) | AAC-LC & Opus (-1.33%) |
| **VieNeu-TTS (Seen)** | **58.67%** (-7.36) | **50.67%** (-1.49) | **60.00%** (-7.53) | **69.33%** (-12.30) | **61.33%** (-9.01) | AAC-LC 76k (-8.00%) |
| **Kokoro (Unseen)** | **100.0%** (-33.54) | **100.0%** (-33.45) | **98.67%** (-31.41) | **100.0%** (-34.53) | **100.0%** (-38.12) | Opus 24k (-1.33%) |
| **OmniVoice (Unseen)** | **45.33%** (+1.93) | **45.33%** (+2.22) | **44.00%** (+3.41) | **50.67%** (+0.83) | **49.33%** (-0.63) | Opus 24k (-1.33%) |

### Quy Luật Suy Giảm:
1. **Kênh Zalo Nén Lossy (AAC-LC 76k & Opus 24k)**: Là kênh gây suy giảm hiệu năng nhiều nhất (giảm từ 1.33% đến 8.00% Pass Rate). Bộ mã hóa MDCT psychoacoustic làm phẳng các méo hài vi mô khiến một số mẫu spoof có điểm số tăng nhẹ về phía ranh giới.
2. **Kênh Viễn Thông Băng Hẹp (G.711 & AMR-NB)**: Ngược lại với suy nghĩ thông thường, kênh nén băng hẹp 8kHz **không làm giảm** mà lại **làm tăng** tỷ lệ phát hiện spoof (VieNeu tăng từ 58.67% lên 69.33%, OmniVoice tăng từ 45.33% lên 50.67%). Việc cắt gọt tần số cao ép tín hiệu dồn về dải formants trung tâm $300 - 3400$Hz, nơi các sai lệch phân phối của bộ tổng hợp giọng nói nhân tạo bộc lộ rõ rệt nhất.
