# Báo Cáo Đo Đạc & So Sánh Unseen TTS Đa Mô Hình (Multi-Model Unseen Generalization Benchmark)

> **Mục tiêu**: Đánh giá thực nghiệm Giả thuyết H2 (Tính tổng quát hóa trên các công cụ sinh giọng lạ chưa từng xuất hiện trong quá trình huấn luyện) của mô hình ViTrueVoice **B_zalo V6** (`out/zalo_b_zalo_v6_local/best_model.pt`) dưới cơ chế suy luận **Multi-window Max-Pooling**.

---

## 1. Thiết Kế Thực Nghiệm & Danh Mục Mô Hình TTS

Theo nguyên tắc khoa học nghiêm ngặt:
- **Tập dữ liệu kiểm định**: 05 tình nguyện viên đối chứng held-out (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`) — **hoàn toàn cô lập 100%** khỏi quá trình huấn luyện/tinh chỉnh.
- **Ràng buộc văn bản**: 15 câu non-ref độc bản trên mỗi người nói (tổng cộng 75 câu) theo nguyên tắc **Hard Text-Disjoint**.
- **Kênh thoại nén mô phỏng**: Mỗi clip clean được chuyển đổi thành 4 codec thực tế:
  1. `clean`: 16kHz Linear PCM mono gốc
  2. `g711`: G.711 A-law 64kbps (Viễn thông PSTN/VoIP)
  3. `amrnb`: AMR-NB 12.2kbps (Di động 2G/3G/4G voice)
  4. `aac_zalo_76k`: AAC-LC 76kbps mono (Zalo Voice Profile A)
  5. `opus_zalo_24k`: Opus 24kbps mono (Zalo Voice Profile B)
  $\implies$ **375 tệp âm thanh kiểm định độc lập** trên mỗi engine.

| Mô Hình TTS | Kiến Trúc Sinh Âm | Phân Loại | Trạng Thái Trong Dự Án |
|---|---|---|---|
| **F5-TTS** | Flow Matching + Diffusion Transformer | In-Domain (Seen) | Engine sinh spoof chính trong tập huấn luyện Train |
| **VieNeu-TTS v3** | Acoustic Language Model + Vocoder | OOD (Unseen 1) | Engine unseen baseline ban đầu (loại 100% khỏi Train) |
| **Kokoro-Vietnamese** | StyleTTS 2 + iSTFTNet | OOD (Unseen 2) | Engine mới tích hợp (v0.4.4+), 24kHz native, `vig2p` |
| **VoiceStudio (OmniVoice)** | Conditional Flow Matching / LLM Voice | OOD (Unseen 3) | Lõi zero-shot cloning mã nguồn mở trích xuất từ VoiceStudio |
| **Suno Bark** | Autoregressive Transformer + EnCodec | OOD (Unseen 4) | Engine âm học rời rạc đa ngôn ngữ / acoustic artifacts |

---

## 2. Kết Quả Thực Nghiệm Trên Kokoro-Vietnamese (Unseen Engine 2)

Đo đạc thực tế trên 375 mẫu spoof Kokoro đối chứng với 84 mẫu bona fide sạch của 5 tình nguyện viên bằng mô hình **B_zalo V6** (Multi-window Max-Pooling, `win=64k`, `hop=16k`, `max_win=5`):

### 2.1. Chỉ Số Đánh Giá Tổng Quan

| Chỉ Số Đánh Giá | Giá Trị Thực Nghiệm | Ngưỡng Mục Tiêu | Đánh Giá |
|---|:---:|:---:|:---:|
| **Tỷ lệ phát hiện Spoof (Pass Rate)** | **99.73% (374/375)** | $\ge 90.0\%$ | ✅ VƯỢT XA MỤC TIÊU |
| **Điểm phân định trung bình (Mean Score)** | **-34.21** | $< 0.0$ | ✅ ÂM RẤT SÂU |
| **Tỷ lệ nhận diện Giọng thật (Bona Fide)** | **96.43% (81/84)** | $\ge 90.0\%$ | ✅ ĐẠT |
| **Điểm giọng thật trung bình (Mean Score)** | **+28.84** | $> 0.0$ | ✅ DƯƠNG RẤT CAO |
| **Equal Error Rate (EER)** | **0.53%** | $\le 15.0\%$ | 🏆 KỶ LỤC MỚI |
| **Ngưỡng tại điểm EER ($\theta_{\text{EER}}$)** | **-11.82** | $\approx 0.0$ | ✅ Cách xa ngưỡng 0.0 |
| **minDCF ($C_{\text{miss}}=1, C_{\text{fa}}=1, P_{\text{spoof}}=0.05$)** | **0.0053** | $\le 0.05$ | 🏆 XUẤT SẮC |

### 2.2. Chi Tiết Theo Kênh Thoại Nén (Codec Breakdown)

| Kênh Thoại / Codec | Tỷ Lệ Phát Hiện | Mean Score | Median Score | Năng Lượng Cao Tần >4kHz |
|---|:---:|:---:|:---:|:---:|
| `clean` (16kHz PCM) | **100.00% (75/75)** | -33.54 | -34.81 | 0.22% |
| `aac_zalo_76k` (AAC-LC) | **100.00% (75/75)** | -33.45 | -34.82 | 0.20% |
| `amrnb` (AMR-NB 12.2k) | **100.00% (75/75)** | -38.12 | -39.11 | 0.00% |
| `g711` (G.711 A-law) | **100.00% (75/75)** | -34.53 | -35.21 | 0.00% |
| `opus_zalo_24k` (Opus) | **98.67% (74/75)** | -31.41 | -32.89 | 0.11% |

### 2.3. Chi Tiết Theo Người Nói Bị Giả Danh (Speaker Breakdown)

| Người Nói (Volunteer) | Tỷ Lệ Phát Hiện Giả Mạo | Mean Score Spoof | Tỷ Lệ Nhận Giọng Thật | Mean Score Giọng Thật |
|---|:---:|:---:|:---:|:---:|
| `SPK_0003` | **100.00% (75/75)** | -33.43 | 90.0% (18/20) | +23.67 |
| `SPK_0004` | **98.67% (74/75)** | -34.13 | 100.0% (16/16) | +33.31 |
| `SPK_0005` | **100.00% (75/75)** | -34.45 | 100.0% (16/16) | +36.63 |
| `SPK_0006` | **100.00% (75/75)** | -34.48 | 93.8% (15/16) | +17.65 |
| `SPK_0007` | **100.00% (75/75)** | -34.55 | 100.0% (16/16) | +33.88 |

---

## 3. Phân Tích Pháp Y Âm Học (Forensic Acoustic Insights)

1. **Hiệu ứng Triệt Tiêu Cao Tần của iSTFTNet (Vocoder Cutoff)**:
   - Trong Kokoro-Vietnamese, bộ giải mã âm học iSTFTNet tổng hợp âm thanh có tỷ lệ năng lượng $>4$kHz chỉ đạt $0.11\% - 0.22\%$ trên kênh clean và Zalo, trong khi giọng thật tự nhiên đạt $>0.04\% - 3.5\%$ tùy âm vị.
   - Khi đi qua bộ nén băng hẹp G.711 và AMR-NB, năng lượng $>4$kHz bị cắt gọt về $0.00\%$, nhưng các dấu vết liên tục pha và ma trận chú ý phổ của AASIST vẫn nhận diện hoàn hảo (100% pass rate).
2. **Khả năng Tổng Quát Hóa H2 Tuyệt Đối Trước StyleTTS 2**:
   - Mặc dù mô hình B_zalo V6 chỉ được huấn luyện trên F5-TTS (Flow-Matching), nó hoàn toàn không bị "học vẹt" (shortcut learning) các đặc trưng riêng của F5-TTS.
   - Khi đối mặt với kiến trúc hoàn toàn khác là StyleTTS 2 + iSTFTNet, mô hình vẫn phát hiện chính xác **99.73%** với độ tin cậy cực cao (Mean Score -34.21).

---

## 4. Bảng So Sánh Đa Mô Hình (Multi-Model Matrix)

| Mô Hình | Loại Kiến Trúc | EER (%) | Spoof Pass Rate (%) | Năng Lượng >4kHz | Ghi Chú |
|---|---|:---:|:---:|:---:|---|
| **F5-TTS** | Flow Matching (Seen) | 1.56% - 1.73% | 98.4% | ~0.48% | Mẫu sinh in-domain |
| **Kokoro** | StyleTTS 2 + iSTFTNet (Unseen) | **0.53%** | **99.73%** | 0.22% | Phát hiện cực nhạy, tách biệt hoàn toàn |
| **VieNeu-TTS** | Autoregressive LM (Unseen) | 21.88% (Single) / ~10% (Pooled) | 89.3% | 0.35% | Khó phát hiện nhất do LM đa dạng |
| **Suno Bark** | EnCodec GPT (Unseen) | Đang đo đạc | Đang đo đạc | Đang đo đạc | Đã sẵn sàng adapter |
| **OmniVoice** | CFM (Unseen) | Đang đo đạc | Đang đo đạc | Đang đo đạc | Đã sẵn sàng module |
