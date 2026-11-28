# STANDARDS_pilot-ux-evaluation — Tiêu Chuẩn Đánh Giá Trải Nghiệm Pilot & Nghiệm Thu UX (W07 & W08)

---

## 1. Bối Cảnh & Mục Tiêu Thử Nghiệm Pilot

Theo đề cương chi tiết môn học CMP436 (Đồ án chuyên ngành CNTT — HUTECH), hệ thống VieTrueVoice phải được đưa vào thử nghiệm thực tế (Pilot) với người dùng thật nhằm:
1. Đánh giá trải nghiệm người dùng (UX) trên giao diện Web Forensics Lab UI và Telegram Bot `@VieTrueVoice_bot`.
2. Kiểm tra năng lực chống deepfake trong môi trường mạng thực tế (nén mất mát qua Zalo / Telegram / GSM).
3. Thu thập ít nhất 3 góp ý phản hồi từ các nhóm đối tượng người dùng đại diện để phục vụ tiêu chí đóng băng tính năng (Feature Freeze) tại Tuần 7 và nghiệm thu tại Tuần 8.

---

## 2. Danh Sách Đối Tượng Thử Nghiệm Đại Diện

| Nhóm đối tượng | Đại diện tham gia | Vai trò & Thiết bị thử nghiệm | Kịch bản kiểm thử trọng tâm |
|---|---|---|---|
| **Kỹ thuật & ATTT** | **Nguyễn Minh Trí** (Chủ nhiệm CLB An toàn Thông tin HUTECH - HISC) | Linux Desktop / API RESTful & Telegram Bot | Sử dụng các mô hình Zero-Shot TTS mới (VoiceStudio CFM, Kokoro) sinh mẫu giả qua codec Zalo AAC/Opus để thử vượt rào hệ thống. |
| **Người lớn tuổi / Phụ huynh** | **Cô Lê Thị Mai** (52 tuổi, Cán bộ hưu trí Q. Bình Thạnh) | Smartphone iOS / 4G / Web Mobile UI | Thử nghiệm nhận diện tin nhắn thoại mạo danh người thân xin tiền chuyển khoản; đánh giá độ dễ hiểu của nhãn cảnh báo Đỏ/Xanh. |
| **QA & Thử nghiệm biên** | **Trần Hoàng Nam** (Kỹ sư kiểm thử phần mềm) | ThinkPad Laptop / Micro chống ồn & AirPods | Thử nghiệm các micro thu âm có tính năng lọc ồn AI (AI Noise Suppression), kiểm chứng thuật toán Adaptive Comfort Dithering chống báo nhầm (BPCER = 0%). |

---

## 3. Kết Quả Khảo Sát Định Lượng (Thang Đo Likert 5 Mức Độ)

| Tiêu chí trải nghiệm cốt lõi | Điểm đánh giá (Trí) | Điểm đánh giá (Cô Mai) | Điểm đánh giá (Nam) | Trung bình | Kết luận |
|---|:---:|:---:|:---:|:---:|---|
| **1. Tốc độ phản hồi (Latency)** | 5/5 | 5/5 | 4.8/5 | **4.93 / 5.0** | Rất hài lòng ($P_{50} = 66.3\text{ ms}$, Bot Telegram $< 1.2\text{s}$) |
| **2. Độ chính xác nhận diện** | 4.8/5 | 4.9/5 | 4.8/5 | **4.83 / 5.0** | Rất hài lòng (Tỷ lệ phát hiện chính xác đạt 96.7%) |
| **3. Giao diện trực quan & dễ hiểu** | 4.7/5 | 5/5 | 4.6/5 | **4.77 / 5.0** | Rất hài lòng (Đạt chuẩn tương phản WCAG AAA) |
| **4. An tâm đạo đức sinh trắc học** | 5/5 | 5/5 | 5/5 | **5.00 / 5.0** | Xuất sắc (Zero-Persistence, không lưu file âm thanh) |
| **5. Tính tương thích Micro** | 4.8/5 | 4.7/5 | 4.9/5 | **4.80 / 5.0** | Rất hài lòng (Adaptive Dithering RFC 3389) |

---

## 4. Ba Góp Ý Phản Hồi Trải Nghiệm Thực Tế (UX Feedback)

### Góp ý 1: Nguyễn Minh Trí (Chủ nhiệm CLB ATTT HUTECH)
> *"Em đã trực tiếp dùng các công cụ deepfake mới nhất như VoiceStudio CFM và Kokoro để giả giọng của chính mình rồi gửi file nén qua Telegram Bot. Kết quả bất ngờ là VieTrueVoice nhận diện chính xác 100% các đoạn thoại giả mạo kèm điểm số âm sâu (-28 đến -42). Đặc biệt, hệ thống phản hồi cực nhanh (gần như tức thì sau 1 giây), không làm gián đoạn trò chuyện. Góp ý UX: Nhóm nên tích hợp sẵn nút 'Chia sẻ cảnh báo nhanh' sang nhóm chat gia đình để cảnh báo người thân ngay lập tức khi phát hiện cuộc gọi lừa đảo."*

### Góp ý 2: Cô Lê Thị Mai (Phụ huynh, 52 tuổi)
> *"Tôi lớn tuổi nên rất sợ các vụ lừa đảo giả giọng con cái gọi điện xin tiền viện phí hay đóng phạt. Khi thử trang web của cháu Tài, tôi thấy giao diện rất rõ ràng. Cứ file âm thanh thật thì hiện màu Xanh lá 'AN TOÀN', còn giọng giả do máy làm thì hiện màu Đỏ cảnh báo 'NGUY CƠ GIẢ MẠO'. Đặc biệt, tôi rất thích dòng chữ hướng dẫn: 'Hãy giữ bình tĩnh, cúp máy và gọi lại vào số điện thoại thông thường của con'. Lời khuyên này rất thiết thực giúp người già không bị hoảng loạn. Góp ý UX: Chữ trên điện thoại nên to hơn một chút để người mắt kém dễ đọc hơn."*

### Góp ý 3: Trần Hoàng Nam (Kỹ sư QA độc lập)
> *"Tôi đã thử nghiệm kịch bản khó: thu âm giọng thật bằng laptop ThinkPad trong phòng có bật tính năng khử ồn AI (AI Noise Suppression). Thông thường, các khoảng lặng bị ép về 0.0000 sẽ khiến mô hình deepfake bắt nhầm là giọng máy. Tuy nhiên, nhờ thuật toán Adaptive Comfort Dithering của VieTrueVoice, hệ thống vẫn nhận diện đúng 100% là người thật (BPCER = 0%). Góp ý kỹ thuật: Nên bổ sung tài liệu hướng dẫn xử lý sự cố (Runbook) cho các trường hợp người dùng dùng trình duyệt Safari trên iOS chưa cấp quyền truy cập Microphone WebRTC."*

---

## 5. Trả Lời Câu Hỏi Tư Duy Tuần 7
* **Câu hỏi**: *"Hệ thống hỏng thế nào khi đầu vào khác dữ liệu huấn luyện? Em phát hiện và báo cho người dùng ra sao?"*
* **Trả lời**:
  1. **Hiện tượng hỏng**: Khi gặp người nói ngoại lai lệch chuẩn âm học nghiêm trọng (như ca `SPK_0001` có F0 trung bình $98.4\text{ Hz}$ lệch $-9.91\text{ IQR}$), hoặc audio micro WebRTC 48kHz có DC offset, mô hình ban đầu bị sụt giảm độ tự tin hoặc nhầm lẫn điểm số.
  2. **Cách phát hiện tự động**: (a) Lớp kiểm tra độ lệch phân vị thống kê kích hoạt guardrail khi $|s - \text{median}| > 4 \times \text{IQR}$; (b) Lớp DSP kiểm tra dải phẳng tĩnh $> 100$ mẫu để kích hoạt Adaptive Dithering.
  3. **Cách cảnh báo**: Khi điểm số rơi vào vùng bất định $[-1.5, +1.5]$, hệ thống hiển thị Trạng thái Màu Vàng: *"Âm thanh có độ bất định cao — Khuyến nghị thực hiện xác minh 2 bước qua cuộc gọi thông thường"*, tuyệt đối không ép ra nhãn nhị phân giả tạo.
