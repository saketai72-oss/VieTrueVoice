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

## 4. Tiến độ Thực nghiệm & Kết quả Nghiệm thu (v0.4.1)

- **Must #1 (W3–W4)**: Bộ dữ liệu đa dạng hóa 49.038 mẫu (5 tình nguyện viên, 65 người VIVOS, 419 người Common Voice), 4 cổng kiểm định Label-Free Prosody, nén 3 chuẩn (Clean, G.711 A-law, AMR-NB), Paired Triplets 1:1:1 cho eval, bảo vệ quyền riêng tư theo Luật 91/2025/QH15.
- **Must #2 (W5)**: Huấn luyện SSL-AASIST trên Kaggle GPU qua 3 nhánh đối chứng (A, B0, B). Kết quả thực nghiệm:
  - **In-domain Seen TTS (F5-TTS)**: EER đạt **3.28%** (ĐẠT mục tiêu $\le 8\%$).
  - **Giả thuyết H1 (Độ bền nén kênh thoại)**: Đạt **PASS trên tập nội bộ** ($\Delta\text{EER}_{\text{rel}} = +40.46\%$ trên AMR-NB, $+47.55\%$ trên G.711 A-law, $p < 0.05$); OOD G.711 chưa qua ($+15.91\%$).
  - **Giả thuyết H2 (Công cụ lạ Unseen VieNeu-TTS)**: EER đạt **$21.88\% - 26.34\%$** (CHƯA ĐẠT mục tiêu $\le 15\%$ do bảo toàn ràng buộc 100% Unseen).
  - **Phân rã RawBoost**: Giúp giảm thêm **$13.79\% - 22.06\%$** EER trên kênh nén so với chỉ tăng cường Codec thuần túy.
- **Must #3 (W6)**: Triển khai API FastAPI (`/api/v1/predict`), giao diện Gradio tối giản $\le 3$ thao tác, Bot Telegram nhận voice message và benchmark đo độ trễ 30 lần $\le 3.0$s; chuẩn hóa phân định ngưỡng $\theta=0.0$, loại bỏ confidence phi chuẩn hóa. 190/190 unit tests TDD xanh 100%.
- **Kênh Zalo & Fine-Tuning B_zalo (v0.4.1)**: Chuẩn hóa bộ nạp âm thanh in-memory đa định dạng (`audio_loader.py`); phân tích đối soát pháp y SPK_0001; khóa cấu hình Zalo Dual Profile (Profile A: AAC-LC 76kbps, Profile B: Opus 24kbps); sinh manifest ghép cặp `data/manifests_zalo/` (0% rò rỉ); đo lường baseline Checkpoint B; cấu hình nhánh fine-tune `train.py --branch B_zalo --init-ckpt`.
