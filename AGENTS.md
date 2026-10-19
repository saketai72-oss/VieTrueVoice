# Bối Cảnh Agent — ViTrueVoice (v0.1.0) — 2026-10-16

> **Quy tắc Bắt buộc**: Đọc tệp này vào đầu mỗi phiên làm việc mà không cần người dùng nhắc.

## Thiết Lập Dự Án
- **Tên dự án**: ViTrueVoice (Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát)
- **Phiên bản**: 0.1.0 — tuân thủ Semantic Versioning
- **Trạng thái**: Đang hoạt động (Active)
- **Ngăn xếp công nghệ (Tech Stack)**: Python 3.12, PyTorch 2.6 (CUDA), torchaudio, librosa, soundfile, Transformers, FastAPI, Gradio, Python-Telegram-Bot, pytest
- **Điểm neo ngữ cảnh (Context Anchors)**: [PLAN.md](PLAN.md), [README.md](README.md), [howtorun.md](howtorun.md)

## Thứ Tự Ưu Tiên Tài Liệu
- Thư mục `docs/` là Nguồn Chân Lý Duy Nhất (Single Source of Truth - SSOT) về hành vi, kiến trúc và tiêu chuẩn thực thi.
- Tệp `AGENTS.md` chỉ lưu trữ: quy tắc bắt buộc của phiên, danh mục kiểm tra nhanh và siêu dữ liệu (metadata).
- Không sao chép các giải thích chi tiết vào đây — hãy dẫn liên kết tới `docs/`.
- **Chưa rõ phạm vi tác vụ?** Mở `docs/ARCH_documentation-governance.md` trước tiên — bảng ánh xạ Tác vụ → Tài liệu cần nạp nằm tại đó.

## Quản Trị Tài Liệu (Documentation Governance)
- **Tiêu chuẩn Thực thi**: `docs/GUIDE_developer.md` — cách viết mã nguồn, tái cấu trúc và kiểm thử.
- **Đặc tả Kỹ thuật & Hệ thống**: `docs/ARCH_technical-specs.md` — luồng xử lý hệ thống, cấu trúc Kaggle Hybrid, đạo đức sinh trắc học.
- **Thuật toán Tiền xử lý**: `docs/LOGIC_preprocessing.md` — chuẩn hóa 16kHz mono, cắt khoảng lặng, repeat padding, RawBoost, Codec.
- **Kiến trúc Mô hình & Huấn luyện**: `docs/LOGIC_models.md` — AASIST, SSL-AASIST, Weighted CE [0.1, 0.9], huấn luyện 2 pha.
- **Tiêu chuẩn API & Đánh giá**: `docs/STANDARDS_api-benchmarks.md` — endpoint FastAPI, Gradio/Bot UI, log ẩn danh SHA-256.
- **Quy tắc**: Tuyệt đối không hợp nhất các tệp này nếu không có chỉ định rõ ràng. Phân tách ranh giới để ngăn ngừa lỗi hồi quy.

## Các Quyết Định Có Chủ Đích (STUBBORN_FACTs)
> STUBBORN_FACT: Sử dụng kỹ thuật nối lặp (Repeat Padding) thay cho đệm số 0 (Zero-padding) khi độ dài < 64.000 mẫu — nhằm duy trì tính liên tục phổ - thời gian cho bộ lọc AASIST / Wav2Vec 2.0.
> STUBBORN_FACT: Hàm mất mát Weighted Cross-Entropy bắt buộc dùng trọng số [0.1, 0.9] (Spoof: 0.1, Bona fide: 0.9) — nhằm bù đắp mất cân bằng tập dữ liệu (Spoof >= 2.000 so với Bona fide >= 1.000) và giảm thiểu báo động giả trên người dùng thật.
> STUBBORN_FACT: Mọi bản ghi âm thanh trong benchmarks/latency_log.json phải dùng mã băm SHA-256 thay cho tên file hoặc ID người dùng — tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP.
> STUBBORN_FACT: Luồng âm thanh trong API/Bot phải được xử lý trực tiếp trên RAM (stream in-memory) và xóa hủy file tạm ngay lập tức sau khi suy luận — ngăn chặn tuyệt đối nguy cơ rò rỉ giọng nói sinh trắc học.
> STUBBORN_FACT: Độ dài đầu vào mô hình cố định chính xác 64.000 mẫu (4,0 giây ở tần số 16kHz) — đây là kích thước tensor đầu vào bắt buộc của khối front-end AASIST / Wav2Vec2.
> STUBBORN_FACT: Mọi bản commit Git do AI tạo ra BẮT BUỘC có tiền tố `[AI]` ở đầu thông điệp commit — quy tắc truy vết bắt buộc.

## Nguyên Tắc Kỹ Thuật Cho AI (TỐI QUAN TRỌNG)
- **Ưu tiên Thảo luận (Discussion Precedence)**: Nghiêm cấm tự ý tạo mới, chỉnh sửa hoặc xóa mã nguồn/tệp tin khi kế hoạch chưa được thảo luận và thống nhất hoàn toàn với người dùng.

## Quy Tắc Quyết Định Áp Dụng TDD
- **Bắt buộc dùng TDD** cho: xử lý tín hiệu âm thanh, phân chia tập dữ liệu, tính toán hàm mất mát, chỉ số đánh giá (EER/minDCF), forward pass mô hình, endpoint API. Viết kịch bản `pytest` trước mã thực thi.
- **Bỏ qua TDD** cho: tài liệu, ghi chú markdown, định dạng mã, chỉnh sửa giao diện thẩm mỹ.

## Thực Thi Theo Mục Tiêu (Goal-Driven Execution)
Xác minh → Truy vết → Xây dựng → Khẳng định lại. Không đoán mò → làm đại → sửa vá → lặp lại.
Trước khi thực hiện tác vụ nhiều bước, luôn nêu kế hoạch ngắn: `[Bước] → xác minh: [kiểm tra]`.

## Phong Cách Phản Hồi (TỐI QUAN TRỌNG)
- Chỉ trả lời những gì được hỏi. Không mở đầu, tóm tắt lại, kết bài sáo rỗng hoặc độn chữ.
- Chỉ dùng Markdown khi thực sự tăng tính trực quan (bảng, khối mã).
- Khi chưa chắc chắn → hỏi **duy nhất một câu**. Không tự ý giả định.

### Quy Tắc Viết
Loại bỏ: từ đệm, từ khen ngợi/xã giao, văn phong ngập ngừng. Dùng câu ngắn gọn, trực diện. Giữ nguyên thuật ngữ kỹ thuật và mã lỗi nguyên bản.

Mẫu chuẩn: `[đối tượng] [hành động] [nguyên nhân]. [bước tiếp theo].`

### Tự Động Rõ Ràng (Auto-Clarity)
Chuyển về câu đầy đủ trong các trường hợp: cảnh báo an mật, xác nhận hành động không thể hoàn tác, chuỗi thao tác nhiều bước nếu viết ngắn có nguy cơ hiểu sai. Sau đó quay về phong cách súc tích.

## Lỗi Thường Gặp Cần Tránh
| Lỗi | Cách phòng tránh |
|-----|------------------|
| Tự ý tái cấu trúc mã nguồn đang hoạt động | Chỉ tái cấu trúc khi có yêu cầu rõ ràng |
| Commit mã do AI sinh mà thiếu tiền tố `[AI]` | Luôn gắn tiền tố `[AI]` cho thông điệp commit |
| Lưu trữ file giọng nói thô hoặc PII trong repo | Tuân thủ `.gitignore` và chỉ ghi log mã băm SHA-256 |
| Đệm số 0 (Zero-padding) cho đoạn âm thanh ngắn | Luôn dùng Repeat Padding (`np.tile`) cho đủ 64.000 mẫu |
| Trọng số bằng nhau trong hàm mất mát Cross-Entropy | Luôn đặt `weights = [0.1, 0.9]` cho `[Spoof, Bona fide]` |
| Trùng lặp quy tắc ở nhiều file khác nhau | Mỗi quy tắc chỉ thuộc về một tệp duy nhất — liên kết, không sao chép |
| Quên đăng ký tài liệu mới vào sổ quản trị | Đăng ký vào `docs/ARCH_documentation-governance.md` trước khi sử dụng |

## Giao Thức Trước Khi Commit (Pre-Commit Protocol)
1. **Kiểm thử**: Chạy `pytest tests/ -v`. Toàn bộ test phải pass.
2. **Tài liệu**: Cập nhật tệp `docs/LOGIC_*.md` hoặc `docs/ARCH_*.md` liên quan nếu logic thay đổi (thông qua yêu cầu doc sweep rõ ràng).
3. **Dọn dẹp**: Xóa lệnh in debug (print), xóa tệp nháp tạm.
4. **Git**: Thông điệp commit bắt đầu bằng `[AI]`. Không push khi người dùng chưa đồng ý.

## Các Cột Mốc Nghiệm Thu (Milestones)
- [x] v0.1.0: Khởi tạo khung dự án, requirements, pipeline CI xanh, module tiền xử lý kèm unit tests TDD.
- [x] v0.2.0: Must #1 (W4) — Chuẩn bị dữ liệu, lọc chất lượng ASR WER, script chia tập độc lập người nói (Speaker-Disjoint), thuật toán RawBoost & mô phỏng Codec.
- [ ] v0.3.0: Must #2 (W5) — Đường ống huấn luyện Baseline AASIST và SSL-AASIST trên Kaggle GPU.
- [ ] v0.4.0: Must #3 (W6) — API suy luận thời gian thực (FastAPI), Web Demo (Gradio), Telegram Bot (độ trễ <= 3s).
- [ ] v1.0.0: Thử nghiệm Pilot & Nghiệm thu (W7-W8) — Đóng gói Docker, CI/CD, bảo mật nâng cao, báo cáo đối sánh chính thức.

## Lệnh Thường Dùng
- `pytest tests/ -v`: Chạy toàn bộ bộ kiểm thử unit test.
- `python manage_kaggle.py push`: Đẩy mã huấn luyện lên Kaggle GPU.
- `python manage_kaggle.py status`: Kiểm tra trạng thái thực thi của kernel Kaggle.
- `python manage_kaggle.py output`: Tải trọng số (`best_model.pt`) về thư mục `./out/`.
- `uvicorn src.app.server:app --reload`: Khởi động máy chủ phát triển FastAPI.

---

*v0.1.0 — 2026-10-16*
