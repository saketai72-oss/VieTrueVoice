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
| **Tỷ lệ nhận diện sai lệch EER** *(Equal Error Rate)* | Đánh giá mô hình trên tập kiểm thử giọng thật / giả tiếng Việt (gồm mẫu gốc và mẫu sinh từ F5-TTS, OmniVoice CFM, VieNeu-TTS; có mô phỏng nén kênh truyền) | **34.72%** *(95% Wilson CI: [24.75%, 46.24%], đo tai người trên 72 lượt)* | **EER ≤ 8%** trên tập test nội bộ; duy trì **EER ≤ 15%** khi gặp công cụ TTS chưa từng thấy (*unseen TTS*) | **W2** *(27/10/2026: đo tai người)* & **W8 / v0.9.4** *(24/11/2026: đo mô hình)* | Baseline tại [`benchmarks/human_baseline_metrics.csv`](benchmarks/human_baseline_metrics.csv); kết quả mô hình (**5.63% EER** trên 15.980 mẫu test; **12.05% EER** trên *unseen* VieNeu-TTS) tại [`benchmarks/v8_1_vs_v7_benchmark.json`](benchmarks/v8_1_vs_v7_benchmark.json), [`benchmarks/v8_1_test_indomain_15980.json`](benchmarks/v8_1_test_indomain_15980.json) và [`scripts/eval_v8_1_benchmark.py`](scripts/eval_v8_1_benchmark.py) |
| **Thời gian phản hồi phân tích đoạn thoại** *(Latency)* | Bấm giờ từ lúc tải lên file âm thanh (đoạn thoại 3–5s) đến khi trả về nhãn Thật/Giả và độ tin cậy | **5.31 giây** *(thực đo nghe tai trực tiếp; thủ công gọi người thân: 2–5 phút)* | **≤ 3 giây** trên môi trường GPU/CPU tiêu chuẩn | **W2** *(27/10/2026: quy trình thủ công)* & **W8 / v0.9.4** *(08/11/2026 & 24/11/2026: đo API demo)* | Benchmark 30 lần tại [`benchmarks/latency_benchmark.csv`](benchmarks/latency_benchmark.csv) *(trung vị **1.101s**)*, log ẩn danh **140** lượt chạy cục bộ tại `benchmarks/latency_log.json` *(trung vị **0.705s**)* và [`scripts/benchmark_latency.py`](scripts/benchmark_latency.py) |
