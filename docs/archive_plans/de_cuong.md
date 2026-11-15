# HUTECH · KHOA CÔNG NGHỆ THÔNG TIN · CMP436 ĐỒ ÁN CHUYÊN NGÀNH CNTT · HK1 2026–2027

## DỰ THẢO ĐỀ CƯƠNG CHI TIẾT · ĐỊNH HƯỚNG CỦA GVHD
**Nguyễn Thành Tài · MSSV 2380601959 · 23DTHD5 · GVHD: TS. Nguyễn Quang Trung · 14/10/2026**

> **NHỚ 5 ĐIỀU**
> 1. Đây là đồ án nghiên cứu có sản phẩm. ViTrueVoice là công cụ để trả lời câu hỏi nghiên cứu, không phải đích đến.
> 2. Mọi quyết định thiết kế phải có nguyên lý đứng sau. Khi vấn đáp, câu “vì sao” phải dẫn được về một dòng ở mục C.
> 3. Đo có đối chứng. So sánh mô hình huấn luyện có và không có tăng cường nén kênh trên cùng tập kiểm thử đã nén; đo thêm trên công cụ TTS chưa thấy.
> 4. Thứ Sáu 12:00 nộp 1 PDF; 13:30 báo cáo; vấn đáp: W5, W7, W9 (W9 là phần hỏi đáp sau thuyết trình thử).
> 5. Dùng AI để học nhanh, nhưng nguyên lý, số đo và lập luận phải là của em.

---

## A. ĐỀ TÀI

| Mục | Nội dung |
| :--- | :--- |
| **Tên đề tài (VN)** | Phát triển ViTrueVoice: hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát |
| **Tên đề tài (EN)** | Developing ViTrueVoice: Detecting Vietnamese Deepfake Speech over Compressed Voice Channels Based on Self-supervised Speech Representations |
| **Tên sản phẩm** | ViTrueVoice (kiểm trùng tên trên Google và kho ứng dụng trước 16/10) |
| **Vấn đề nghiên cứu** | Kẻ lừa đảo dùng giọng nói nhân bản của người thân để đòi chuyển tiền; tai người khó phân biệt, nhất là khi âm thanh đã bị nén qua Zalo, Messenger hay cuộc gọi. Đồ án xem việc phát hiện là bài toán phân loại âm thanh thật/giả bằng biểu diễn học tự giám sát, và kiểm tra độ bền khi âm thanh bị nén. |
| **Câu hỏi nghiên cứu** | **CH1.** Huấn luyện có tăng cường nén kênh thoại (Opus, AMR, lọc băng tần 8 kHz) có giảm EER trên âm thanh đã nén so với huấn luyện không tăng cường không?<br>**CH2.** Mô hình giữ được EER bao nhiêu trên giọng giả từ công cụ TTS chưa thấy khi huấn luyện? |
| **Giả thuyết** | **H1:** EER trên tập nén giảm ít nhất 30% (tương đối) nhờ tăng cường nén.<br>**H2:** EER trên công cụ TTS chưa thấy ≤ 15%. |
| **Đóng góp** | (1) Bộ dữ liệu giọng thật/giả tiếng Việt có phiếu đồng ý, có phiên bản nén kênh; (2) đánh giá chéo công cụ sinh giọng; (3) dịch vụ kiểm tra đoạn thoại ≤3 giây. |

*Về tên đề tài: theo công thức của Khoa; “Phát triển” vì em giữ tên ViTrueVoice; phần học thuật là học biểu diễn tự giám sát (wav2vec 2.0) và độ bền khi nén kênh. Sản phẩm của em khác Kiên (văn bản) và Lê Minh Đình Tiến (đường link).*

---

## B. PHẦN THẦY ĐỊNH HƯỚNG VÀ PHẦN EM TỰ CHỌN

| Bắt buộc (không tự đổi) | Em tự chọn |
| :--- | :--- |
| - CH1, CH2 và hai giả thuyết ở mục A.<br>- Mọi mẫu giọng thật có phiếu đồng ý; không nhân bản giọng của người không đồng ý.<br>- Tập kiểm thử tách theo người nói và theo công cụ TTS (có công cụ chưa thấy khi huấn luyện).<br>- Báo cáo EER, minDCF; so với một baseline (ví dụ LFCC + GMM hoặc mô hình AASIST gốc).<br>- Bộ eval ≥30 tình huống, trong đó ≥10 lấy từ lần hệ thống từng sai; báo cáo tỉ lệ đạt trước và sau khi sửa.<br>- Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình.<br>- Chương 2 theo khung lý thuyết ở mục E. | - Giao diện Gradio hay web, bot Telegram.<br>- Số lượng công cụ TTS dùng để sinh giọng giả.<br>- Thử thêm codec khác nếu còn thời gian.<br>- Muốn đổi phần bắt buộc: viết 1 ADR nêu lý do và hỏi thầy ở buổi thứ Sáu. |

**Góp ý trên file ý tưởng của em**

| Mục | Góp ý |
| :--- | :--- |
| **Chỉ số “trước”** | “35% độ chính xác bằng tai người” cần đo thật: cho ≥10 người nghe 20 đoạn thật/giả và ghi kết quả ở W2. Đó là số “trước” cho câu chuyện người dùng. |
| **Đạo đức dữ liệu** | Giọng nói là dữ liệu sinh trắc. Phiếu đồng ý ghi rõ: dùng cho đồ án, được nhân bản để thử nghiệm, xoá sau khi kết thúc. |

**Trả lời câu hỏi ở mục 3.7 của em**

| Câu hỏi | Trả lời |
| :--- | :--- |
| Trường có CLB An toàn thông tin không, liên hệ thế nào? | https://web.facebook.com/groups/clbanmhutech |

---

## C. NGUYÊN LÝ ĐỨNG SAU TỪNG QUYẾT ĐỊNH THIẾT KẾ
*Mỗi dòng là một ADR hoặc một mục trong Chương 2. Cột cuối là câu thầy sẽ hỏi khi vấn đáp; trả lời bằng nguyên lý + số đo của chính em.*

| Quyết định thiết kế | Nguyên lý nền tảng | Câu hỏi em phải trả lời được |
| :--- | :--- | :--- |
| **1. Biểu diễn âm thanh** | Học tự giám sát (wav2vec 2.0) vs đặc trưng thủ công (MFCC, LFCC). | Vì sao biểu diễn tự giám sát lại bắt được dấu vết giọng tổng hợp mà MFCC bỏ sót? |
| **2. Tăng cường nén kênh** | Lệch miền (domain shift); tăng cường dữ liệu theo kênh truyền. | Codec Opus ở 16 kbps làm mất những thông tin nào của tín hiệu? |
| **3. Độ đo EER** | Đánh đổi chấp nhận nhầm – từ chối nhầm; ngưỡng. | Vì sao báo EER thay vì độ chính xác? Ngưỡng triển khai em chọn ở đâu? |
| **4. Công cụ TTS chưa thấy**| Khả năng tổng quát hoá; tách tập theo nguồn sinh. | Mô hình giảm bao nhiêu khi gặp công cụ mới? Vì sao? |
| **5. Dữ liệu sinh trắc** | Nghị định 13/2023; đồng ý có hiểu biết; tối thiểu hoá dữ liệu. | Em lưu đoạn thoại người dùng gửi lên bao lâu? Vì sao? |

---

## D. THIẾT KẾ ĐO LƯỜNG

| Thành phần | Nội dung |
| :--- | :--- |
| **Biến thay đổi** | (a) Huấn luyện có/không tăng cường nén kênh.<br>(b) Công cụ TTS đã thấy / chưa thấy. |
| **Hai chỉ số** | Chỉ số 1 – EER trên tập âm thanh đã nén.<br>Chỉ số 2 – thời gian từ lúc gửi đoạn 5–10 giây đến khi có kết quả (giây).<br>*Thêm:* tỉ lệ người nghe phân biệt đúng (số “trước”). |
| **Giữ cố định** | Cùng kiến trúc mô hình, cùng tập kiểm thử, cùng số bước huấn luyện. |
| **Người tham gia / dữ liệu** | ≥30 người nói có phiếu đồng ý; dữ liệu mở cho nghiên cứu (VIVOS, Common Voice) đúng giấy phép; ≥10 người nghe cho phép đo “trước”. |
| **Lịch** | Đo người nghe W2 · bộ dữ liệu W3–W4 · so sánh huấn luyện W6 · dùng thử với nhóm pilot W8. |
| **Phân tích** | Bảng EER/minDCF theo điều kiện; đường DET; thời gian xử lý. |
| **Mối đe doạ độ giá trị**| Ít người nói; giọng giả do chính em sinh nên dễ hơn thực tế; codec mô phỏng khác codec thật. |

**MVP: tối đa 3 Must (phục vụ câu hỏi nghiên cứu)**

| Mức | Nội dung |
| :--- | :--- |
| **Must #1 · W4** | Thu giọng có đồng ý, sinh giọng giả bằng 2 công cụ TTS, tạo bản nén Opus/AMR; chia tập theo người nói và công cụ. |
| **Must #2 · W5** | Fine-tune mô hình trên wav2vec 2.0; bảng EER có/không tăng cường; API FastAPI. |
| **Must #3 · W6** | Web/Gradio hoặc bot Telegram nhận file thoại, trả nhãn + độ tin cậy; log ẩn danh. |
| **Không làm** | Phát hiện video giả, chặn cuộc gọi thời gian thực, nhân bản giọng người không đồng ý. |

---

## E. KHUNG BÁO CÁO VÀ LÝ THUYẾT BẮT BUỘC

| Chương / mục | Trang | Nội dung thầy chỉ định |
| :--- | :--- | :--- |
| **1. Tổng quan** | 6–8 | Vấn đề nghiên cứu, CH1–CH2, H1–H2, người đại diện nhóm pilot, phạm vi. Số liệu từ 5 phỏng vấn W2. |
| **2.1 Giọng nói giả và chống giả mạo** | 15–25 (cả Ch.2) | TTS, nhân bản giọng; bài toán chống giả mạo giọng nói (ASVspoof). |
| **2.2 Biểu diễn âm thanh** | | MFCC/LFCC, học tự giám sát (wav2vec 2.0), AASIST. Kết thúc bằng kiến trúc em dùng. |
| **2.3 Đánh giá và độ bền** | | EER, minDCF, lệch miền do nén kênh, tổng quát hoá sang công cụ mới. |
| **2.4 Nền tảng kỹ thuật** | | PyTorch, torchaudio, FastAPI, Docker, CI; khoá AWS dùng ở đâu. |
| **2.5 Khảo sát giải pháp hiện có** | | Mô hình ASVspoof, công cụ thương mại, cách xác minh thủ công. |
| **3. Kết quả thực nghiệm** | 3–10 | Thiết kế (C4, 3 ADR dẫn về mục C), cài đặt, ≥10 test, 5 NFR, kết quả đo theo mục D, bảng chi phí. |
| **4. Kết luận** | 1–2 | Trả lời CH1, CH2: giả thuyết đúng hay sai, bao nhiêu; mối đe doạ độ giá trị; hướng phát triển. |

---

## F. MỖI TUẦN LÀM GÌ, VIẾT GÌ, TƯ DUY GÌ
*Cột cuối là câu hỏi tư duy của tuần. Em trả lời ngắn (3–5 câu) ở cuối Phiếu nhật ký tuần, dẫn về nguyên lý và số đo; thầy hỏi lại khi báo cáo chiều thứ Sáu.*

| Tuần | Phải xong | Viết báo cáo | Câu hỏi tư duy |
| :--- | :--- | :--- | :--- |
| **W1 16/10 CP1** | - 1 trang: vấn đề, CH1–CH2, H1–H2<br>- Xác nhận đồng ý của người đại diện nhóm pilot<br>- Repo + README<br>- Nộp Phiếu + đề cương | Ch.1 nháp (1.1–1.2) | Phát biểu CH1 thành: em đổi gì, đo gì, so với cái gì (baseline/cách làm cũ)? |
| **W2 23/10 CP2** | - 5 phỏng vấn phụ huynh và người lớn tuổi dùng mạng xã hội<br>- Đọc wav2vec 2.0, AASIST, tài liệu ASVspoof; mỗi bài tóm tắt nửa trang<br>- 8 user story, MVP ≤3 Must<br>- Số “Trước” của chỉ số 1 | Ch.1 bản 1 + dàn ý Ch.2 | Người dùng vướng ở bước nào của quy trình hiện tại? Vướng mắc đó tốn bao nhiêu (giây, %, tiền)? |
| **W3 30/10 CP3** | - C4 mức 2 + 3 ADR (dẫn về mục C)<br>- Phiếu đồng ý; kế hoạch dữ liệu; đặc tả đo<br>- Hello World + 1 test; CI chạy | Ch.2 dàn ý + ≥5 tài liệu; phác 3.1 | Dữ liệu đến từ đâu, ai gán nhãn, theo tiêu chí nào? Làm sao để tập kiểm thử không “rò” vào tập huấn luyện? |
| **W4 06/11 CP4** | - Must #1: bộ dữ liệu thật/giả + bản nén<br>- 3 test tự viết trước khi nhờ AI<br>- Video demo 1–2 phút | Ch.2 nháp (8–12 trang) | Baseline đơn giản nhất đạt bao nhiêu? Mô hình của em hơn bao nhiêu, và vì sao hơn? |
| **W5 13/11 CP5 · vấn đáp** | - Must #2: mô hình + so sánh tăng cường<br>- Bảng EER mô hình đầu tiên | Ch.2 hoàn chỉnh (15–25 trang) | Ma trận nhầm lẫn cho thấy trường hợp nào hay sai? Nguyên nhân nằm ở dữ liệu hay ở mô hình? |
| **W6 20/11 CP6** | - Must #3: dịch vụ kiểm tra đoạn thoại<br>- ≥10 test (≥5 tự động); bộ eval ≥30 tình huống<br>- Bảng EER có/không tăng cường; thử công cụ TTS mới | Ch.3 nháp (3–6 trang) | Với người dùng của em, sai loại nào nguy hiểm hơn (bỏ sót hay báo nhầm)? Ngưỡng em chọn là bao nhiêu, vì sao? |
| **W7 27/11 CP7 · vấn đáp** | - ≥2 biện pháp bảo mật; Docker + CI; 5 NFR<br>- UX: ≥3 góp ý người dùng thật<br>- Đóng băng tính năng; nhóm pilot dùng thử | Ch.3 bổ sung | Hệ thống hỏng thế nào khi đầu vào khác dữ liệu huấn luyện? Em phát hiện và báo cho người dùng ra sao? |
| **W8 04/12 CP8** | - Bảng kết quả có xác nhận của người đại diện pilot<br>- Bảng chi phí 100 / 1.000 / 10.000 người dùng<br>- Sổ tay sự cố 1 trang; tự tính % hoàn thành | Ch.3 kết quả; dàn ý Ch.4 | H1, H2 đúng hay sai? Kết quả trên tập kiểm thử có khớp với kết quả khi người dùng thật sử dụng không? |
| **W9 11/12 CP9 · vấn đáp** | - Chỉ sửa lỗi<br>- Slide 10–12 trang<br>- Thuyết trình thử 7 phút | Báo cáo đủ 4 chương | Đóng góp của em trong 2 câu: nguyên lý nào được kiểm chứng, trong điều kiện nào? |
| **W10 18/12 CP10** | - Bản v1.0, README cuối<br>- Video demo 3–5 phút<br>- Phiếu theo dõi đủ chữ ký | Báo cáo cuối ≤50 trang | Làm lại từ đầu, em thu dữ liệu và đánh giá khác thế nào để kết luận chắc hơn? |

*% hoàn thành ở W8 = 50% × (số checkpoint Đạt ÷ 8) + 50% × (số Must đã nghiệm thu ÷ tổng Must); từ 50% trở lên mới được tiếp tục.*

---

## G. QUY TẮC, KHOÁ HỌC VÀ VIỆC TRƯỚC 16/10
- **Nộp tuần:** `DACN_2380601959_NguyenThanhTai_Wxx.pdf` trước 12:00 thứ Sáu; thứ tự: Bổ sung tuần trước → Phiếu nhật ký (kèm trả lời câu hỏi tư duy) → Nhật ký AI → Minh chứng → phần chương nháp.
- **Minh chứng kiểm được:** ảnh có ngày giờ, link mở không cần quyền, commit trước 12:00. Dữ liệu người dùng: chỉ thu khi có đồng ý, ẩn danh trong báo cáo và repo.
- **AI:** viết test trước rồi mới nhờ AI viết code; commit có tiền tố `[AI]`; không bịa số đo, phỏng vấn, tài liệu.
- **Khoá học (Gói A):** Cloud Foundations nộp 23/10 · Security Foundations 06/11 (dùng cho 2 biện pháp bảo mật W7) · Architecting 50% ngày 20/11, 100% ngày 11/12 (dùng cho bảng chi phí W8).

| # | Việc phải xong trước 16/10 | Xong |
| :--- | :--- | :--- |
| **1** | Xác nhận đồng ý bằng văn bản (ảnh tin nhắn/email) của người đại diện nhóm pilot; danh sách ≥2 đơn vị dự phòng. | ☐ |
| **2** | Viết 1 trang: vấn đề nghiên cứu, CH1–CH2, H1–H2, biến thay đổi và hai chỉ số (theo mục A, D). | ☐ |
| **3** | Viết đề cương theo Mẫu đề cương chi tiết v2 trên LMS, đặc biệt 1.2.3 (câu hỏi nghiên cứu), 1.2.4 (pilot, hai chỉ số), Bảng 2.1, Phụ lục B. | ☐ |
| **4** | Gộp Phiếu đăng ký + đề cương thành 1 PDF `DACN_2380601959_NguyenThanhTai_PhieuDangKy.pdf`, nộp LMS trước 23:30 thứ Sáu 16/10. | ☐ |
| **5** | Tạo repo + README (tên đề tài, câu định vị, bảng trước–sau 6 cột); tài khoản AWS Academy (ảnh sau đăng nhập). | ☐ |
| **6** | Nộp bài W1 trước 12:00 thứ Sáu 16/10; mang máy chạy được dự án đến buổi 13:30. | ☐ |

---

### Tài liệu nền phải đọc
*(Tự mở ra đọc; kiểm lại thông tin xuất bản trước khi trích)*

1. Baevski, A. et al. (2020). *wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations.* NeurIPS.
2. Jung, J.-w. et al. (2022). *AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks.* ICASSP.
3. Géron, A. *Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow.* O’Reilly (chương đánh giá mô hình).
4. Sculley, D. et al. (2015). *Hidden Technical Debt in Machine Learning Systems.* NeurIPS.
5. Lundberg, S., Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions (SHAP).* NeurIPS.