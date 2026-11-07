# VieTrueVoice

## 1. Tên đề tài
**Hệ thống phát hiện giọng nói giả tiếng Việt hỗ trợ phòng chống lừa đảo mạo danh cuộc gọi và tin nhắn thoại**

- **Mã đề tài:** LD-07 (Ngân hàng đề tài)
- **Sinh viên thực hiện:** Nguyễn Thành Tài – MSSV: 2380601959 – Lớp: 23DTHD5
- **Chuyên ngành:** Máy học và Ứng dụng – Đồ án chuyên ngành CNTT (HK1 2026–2027), HUTECH

---

## 2. Câu định vị
> **“Đồ án giải quyết bẫy lừa đảo bằng giọng nói giả cho người dùng mạng xã hội, đo bằng tỷ lệ nhận diện sai dưới 8% và tốc độ xử lý dưới 3 giây.”**

---

## 3. Bảng hai chỉ số trước – sau

| Chỉ số | Cách đo | Trước | Sau (mục tiêu) | Ngày đo | Bằng chứng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tỷ lệ nhận diện sai lệch EER** *(Equal Error Rate)* | Đánh giá mô hình trên tập kiểm thử giọng thật / giả tiếng Việt (gồm mẫu gốc và mẫu sinh từ F5-TTS, VieNeu-TTS; có mô phỏng nén kênh truyền) | **34.72%** *(95% Wilson CI: [24.75%, 46.24%], đo tai người trên 72 lượt)* | **EER ≤ 8%** trên tập test nội bộ; duy trì **EER ≤ 15%** khi gặp công cụ TTS chưa từng thấy (*unseen TTS*) | **W2** *(đo tai người / baseline)* & **W8** *(đo mô hình)* | File bảng tính tính toán EER, confusion matrix và script đánh giá lưu tại [`/benchmarks/eval_metrics.csv`](file:///c:/Codes/VieTrueVoice/benchmarks/eval_metrics.csv) |
| **Thời gian phản hồi phân tích đoạn thoại** *(Latency)* | Bấm giờ từ lúc tải lên file âm thanh (đoạn thoại 3–5s) đến khi trả về nhãn Thật/Giả và độ tin cậy | **5.31 giây** *(thực đo nghe tai trực tiếp; thủ công gọi người thân: 2–5 phút)* | **≤ 3 giây** trên môi trường GPU/CPU tiêu chuẩn | **W2** *(đo quy trình thủ công)* & **W8** *(đo API demo)* | File log request và benchmark độ trễ tại [`/benchmarks/latency_log.json`](file:///c:/Codes/VieTrueVoice/benchmarks/latency_log.json) |

---

## 4. Tiến độ Thực nghiệm & Kết quả Nghiệm thu (v0.4.4)

- **Must #1 (W3–W4)**: Bộ dữ liệu đa dạng hóa 49.038 mẫu (5 tình nguyện viên, 65 người VIVOS, 419 người Common Voice), 4 cổng kiểm định Label-Free Prosody, nén 3 chuẩn (Clean, G.711 A-law, AMR-NB), Paired Triplets 1:1:1 cho eval, bảo vệ quyền riêng tư theo Luật 91/2025/QH15.
- **Must #2 (W5)**: Huấn luyện SSL-AASIST trên Kaggle GPU qua 3 nhánh đối chứng (A, B0, B). Kết quả thực nghiệm:
  - **In-domain Seen TTS (F5-TTS)**: EER đạt **3.28%** (ĐẠT mục tiêu $\le 8\%$).
  - **Giả thuyết H1 (Độ bền nén kênh thoại)**: Đạt **PASS trên tập nội bộ** ($\Delta\text{EER}_{\text{rel}} = +40.46\%$ trên AMR-NB, $+47.55\%$ trên G.711 A-law, $p < 0.05$); OOD G.711 chưa qua ($+15.91\%$).
  - **Giả thuyết H2 (Công cụ lạ Unseen VieNeu-TTS)**: EER đạt **$21.88\% - 26.34\%$** (CHƯA ĐẠT mục tiêu $\le 15\%$ do bảo toàn ràng buộc 100% Unseen).
  - **Phân rã RawBoost**: Giúp giảm thêm **$13.79\% - 22.06\%$** EER trên kênh nén so với chỉ tăng cường Codec thuần túy.
- **Must #3 (W6)**: Triển khai API FastAPI (`/api/v1/predict`), giao diện Gradio tối giản $\le 3$ thao tác, Bot Telegram nhận voice message và benchmark đo độ trễ 30 lần $\le 3.0$s; chuẩn hóa phân định ngưỡng $\theta=0.0$, loại bỏ confidence phi chuẩn hóa. 193/193 unit tests TDD xanh 100%.
- **Kênh Zalo & Fine-Tuning B_zalo (v0.4.1)**: Chuẩn hóa bộ nạp âm thanh in-memory đa định dạng (`audio_loader.py` fix seekable M4A); khóa cấu hình Zalo Dual Profile (Profile A: AAC-LC 76kbps, Profile B: Opus 24kbps); sinh manifest ghép cặp `data/manifests_zalo/` (0% rò rỉ); hoàn tất đo lường baseline Checkpoint B; huấn luyện thành công Version 3 (Dev EER 1.50%) và Version 4 (AM-Softmax + Pitch Aug, Dev EER **1.56% - 1.73%**, FAR@0 giảm 3 lần còn **3.65%**).
- **Tổng Quát Hóa Giọng Trầm, Bóc Tách Âm Học & Kiểm Chứng Dữ Liệu (v0.4.2)**: Huấn luyện thành công Checkpoint V5 Local trên RTX 3050 4GB GPU đạt Dev EER kỷ lục **1.98%** trên 11.450 mẫu Zalo; Gate 2 Pass **95.3%** (+25.98 macro, +26.35 pooled). Hoàn tất chuỗi thực nghiệm bóc tách khoa học: (1) Bác bỏ giả thuyết F0 là nguyên nhân duy nhất gây điểm âm; (2) Phát hiện lỗ hổng an ninh trước spoof hạ pitch -6st (AUC giảm từ 0.9895 về 0.6717, EER 43%, FAR 62%) và độ nhạy phân hóa theo người nói (SPK_0007); (3) Hủy bỏ hoàn toàn offset tĩnh và bộ lọc suy luận thô để tránh phá vỡ phân phối dữ liệu; (4) Tự kiểm chứng dữ liệu: phát hiện và cô lập 10 file mock thử nghiệm vào `.quarantine_mock/` (xác nhận tập train/dev Zalo và sweep sạch 100%); (5) Thống nhất giải quyết bài toán độ bền vững bằng Data Augmentation 2 chiều thuần thuật toán, bác bỏ việc thu thập thêm giọng tình nguyện viên; (6) Nhập 20 file gốc `SPK_0003` bù cho `SPK_0001`, hoàn tất pipeline sinh kép F5-TTS và VieNeu-TTS (15 câu x 2 engine = 30 clip spoof clean + paired codecs, 100% SHA-256 độc bản, Pass Rate Gate 2 đạt 89.3% trên 5 tình nguyện viên); 227/227 unit tests pass 100%.
- **Khắc Phục BPCER Bằng Max-Pooling Đa Cửa Sổ Trượt (v0.4.3)**: Triển khai kỹ thuật trích xuất đa cửa sổ trượt (window 4.0s = 64k, hop 1.0s = 16k, tối đa 5 cửa sổ) gộp thành 1 mini-batch `(N_windows, 64000)` suy luận trong 1 forward pass duy nhất kết hợp max-pooling (`src/preprocessing/pooling.py`):
  - **Gate 2 trên 4 người nói đối chứng (`SPK_0004`..`0007`, 64 clips)**: Tăng từ 93.8% (V4) và 95.3% (V5) lên **98.4% (63/64)** trên cả hai checkpoint mà không cần huấn luyện lại GPU (0 GPU retrain). File duy nhất còn lại là `SPK_0004_03.wav` dài 3.84s (< 4.0s, chỉ có 1 cửa sổ).
  - **Trên cả 5 người nói đối chứng (`SPK_0003`..`0007`, 84 clips)**: V5 đạt **95.2% (80/84)**.
  - **Bảo toàn an ninh**: Tỷ lệ Dev Spoof APCER dưới max-pooling đạt **6.77% $\le 8.0\%$** tại $\theta = 0.0$.
  - **Guardrail hiệu chỉnh enrollment**: Từ chối can thiệp tự động khi $|offset| > 4 \times IQR$ (ngoại lai `SPK_0001` lệch -9.91 IQR), bảo toàn điểm thô cho quy trình định tuyến kiểm tra thủ công.
  - **Độ trễ thời gian thực (NFR1)**: Trung vị suy luận đa cửa sổ đạt **66.3ms** (P90 68.2ms), nhanh gấp ~45 lần yêu cầu $\le 3.0$s.
  - **Kiểm thử**: Toàn bộ **272/272 unit tests pass 100%**.
- **Chuyển Dịch SPK_0001 Vào Train & Khóa 5 Tình Nguyện Viên Nghiệm Thu (v0.4.4 / V6 Foundation)**:
  - Tích hợp 125 dòng `SPK_0001` (75 bona fide + 50 F5-TTS spoof) vào `data/manifests_zalo/train_zalo.csv` (nâng quy mô tập Train lên 50.710 dòng).
  - Khóa chặt 5 tình nguyện viên đối chứng held-out (`SPK_0003`..`0007`, 84 clips âm thanh thật) làm Bộ nghiệm thu độc lập chính thức của đề tài (0% rò rỉ dữ liệu).
  - Cập nhật logic validator trong `scripts/train.py` và `scripts/generate_zalo_paired_manifests.py`.
  - Hoàn tất kiểm toán an ninh `scripts/audit_v6_manifest.py` đạt chuẩn 5/5 tiêu chí (Zero-leakage, cô lập SPK_0001, Hard Text-Disjoint, cách ly 100% VieNeu-TTS, cơ cấu tệp).
  - Sẵn sàng script huấn luyện V6 Local trên RTX 3050: `scripts/train_local_zalo_v6.py`.
  - Toàn bộ **274/274 unit tests pass 100%**. Sẵn sàng đóng gói Docker và thử nghiệm Pilot (v1.0.0).
