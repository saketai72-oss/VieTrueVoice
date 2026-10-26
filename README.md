# VieTrueVoice

## 1. Tên Đề Tài & Thông Tin Thực Hiện
**Phát triển ViTrueVoice: Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát**

- **Mã đề tài:** LD-07 (Ngân hàng đề tài)
- **Sinh viên thực hiện:** Nguyễn Thành Tài – MSSV: 2380601959 – Lớp: 23DTHD5
- **Chuyên ngành:** Máy học và Ứng dụng – Đồ án chuyên ngành CNTT (HK1 2026–2027), Đại học HUTECH
- **Đơn vị Pilot độc lập:** CLB An toàn thông tin HUTECH (GVHD / Liên hệ: Thầy Nguyễn Trọng Minh Hồng Phước)

---

## 2. Câu Định Vị & Giả Thuyết Nghiên Cứu
> **“Phân loại thật/giả đoạn thoại 5–10s qua kênh nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) cho phụ huynh và người lớn tuổi. Kiểm chứng H1 (giảm $\ge 30\%$ EER tương đối trên tập nén nhờ tăng cường nén kênh), H2 ($\text{EER} \le 15\%$ trên công cụ TTS chưa thấy: Seen F5-TTS vs. Unseen VieNeu-TTS) và thời gian phản hồi trung vị $\le 3$ giây.”**

---

## 3. Bảng Tổng Hợp Chỉ Số Trước – Sau (Target KPIs & Nghiệm Thu)

| Hạng mục Mục tiêu | Chỉ số Trước (Baseline ban đầu) | Mục tiêu Hoàn thành (Đích phải đạt) | Ngày đo | Bằng chứng Nghiệm thu (Artifacts) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Độ bền trên âm thanh đã nén (CH1 / H1)** | $\bullet$ Tai người: đo $\ge 10$ người $\times$ 20 đoạn ở W2 qua Blind Listening Package<br>$\bullet$ Baseline wav2vec 2.0 không tăng cường nén | **Giảm ít nhất $30\%$ EER tương đối** trên tập kiểm thử nén (Opus, AMR-NB, G.711 A-law, lọc $8\text{ kHz}$) nhờ tăng cường nén kênh thoại | **W2** *(đo tai người)* & **W5–W8** *(đo mô hình)* | Script tái lập [`scripts/eval_eer.py`](scripts/eval_eer.py), bảng đối sánh EER/minDCF tại [`benchmarks/eval_metrics.csv`](benchmarks/eval_metrics.csv) |
| **2. Độ bền công cụ TTS chưa thấy (CH2 / H2 / NFR2)** | Mô hình phân loại giảm mạnh độ chính xác khi gặp vocoder và kiến trúc sinh giọng lạ ngoài tập train | Duy trì **$\text{EER} \le 15\%$** trên giọng giả sinh từ Unseen TTS (`VieNeu-TTS v3 Turbo` / công cụ thứ 3) kèm báo cáo minDCF & DET curve | **W5–W6** *(đánh giá chéo TTS)* | Báo cáo đánh giá chéo TTS và kết quả thực nghiệm tại [`benchmarks/eval_metrics.csv`](benchmarks/eval_metrics.csv) |
| **3. Thời gian phản hồi (Latency - NFR1)** | Xác minh thủ công (gọi lại người thân / hỏi câu hỏi bí mật): **2–5 phút** (bấm giờ $\ge 3$ lần ở W2) | **Trung vị thời gian phản hồi $\le 3,0$ giây** cho đoạn thoại 5–10 giây (bấm giờ lặp 30 lần) | **W2** *(thủ công)* & **W6–W8** *(API/Bot demo)* | File log ẩn danh SHA-256 [`benchmarks/latency_log.json`](benchmarks/latency_log.json) và bảng 30 lần đo [`benchmarks/latency_benchmark.csv`](benchmarks/latency_benchmark.csv) |
| **4. Bộ dữ liệu & Đạo đức Sinh trắc học (Must #1 - NFR3)** | Dữ liệu giọng nói rời rạc, nhạy cảm cần bảo vệ theo Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP | $\ge 5$–$30$ người nói có Phiếu đồng ý (`SPK_XXXX`) + VIVOS & Common Voice ($\ge 1.000$ thật, $\ge 2.000$ giả đạt 4 cổng); xóa hủy dữ liệu gốc sau bảo vệ | **W3–W4** *(Frozen V14)* | Phiếu đồng ý (Phụ lục C.2), 5 file manifest 17 cột tại [`data/manifests/`](data/manifests/), cấu hình S3 Lifecycle tự xóa |
| **5. Sản phẩm MVP, Tái lập & Pilot (Must #2, #3 - NFR4, NFR5)** | Chưa có công cụ kiểm tra tự động tin nhắn thoại tiếng Việt qua kênh nén cho người lớn tuổi | FastAPI + Web Gradio ($\le 3$ thao tác) + Bot Telegram; đóng gói 1 lệnh Docker; CI chạy 31/31 unit tests xanh; AI Eval $\ge 30$ ca; Pilot CLB ATTT | **W6–W8** | Repo GitHub, `Dockerfile`, GitHub Actions CI, Bảng chi phí AWS (100/1k/10k user), Biên bản xác nhận Pilot CLB ATTT HUTECH |

---

## 4. Cấu Trúc Tài Liệu Chuẩn (Living Docs)
Hệ thống tài liệu tuân thủ quản trị tài liệu nghiêm ngặt tại [`docs/ARCH_documentation-governance.md`](docs/ARCH_documentation-governance.md):
- **Kiến trúc Kỹ thuật**: [`docs/ARCH_technical-specs.md`](docs/ARCH_technical-specs.md)
- **Quy trình Sinh Dữ Liệu**: [`docs/LOGIC_data-generation.md`](docs/LOGIC_data-generation.md)
- **Tiền Xử Lý Âm Thanh**: [`docs/LOGIC_preprocessing.md`](docs/LOGIC_preprocessing.md)
- **Kiến Trúc Mô Hình & Huấn Luyện**: [`docs/LOGIC_models.md`](docs/LOGIC_models.md)
- **Đặc Tả API & Benchmark**: [`docs/STANDARDS_api-benchmarks.md`](docs/STANDARDS_api-benchmarks.md)
- **Tiêu Chuẩn Lập Trình**: [`docs/GUIDE_developer.md`](docs/GUIDE_developer.md)

