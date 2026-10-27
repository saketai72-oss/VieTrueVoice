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
