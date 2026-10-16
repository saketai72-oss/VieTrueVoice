# ARCH_documentation-governance — Sổ Đăng Bạ Quản Trị & Hướng Dẫn Nạp Tài Liệu

---

## Sổ Đăng Bạ Tài Liệu (Registry & Loading Guide)

> **Quy tắc**: Nếu một tệp không có tên trong bảng này, nó không tồn tại đối với Agent. Phải đăng ký trước khi sử dụng.

| Tệp tài liệu | Nội dung sở hữu | Tuyệt đối KHÔNG chứa | Thời điểm cần nạp |
|--------------|-----------------|----------------------|-------------------|
| `AGENTS.md` | Quy tắc phiên làm việc, danh mục kiểm tra nhanh, siêu dữ liệu | Chi tiết triển khai mã nguồn, nội dung tài liệu đầy đủ | **Luôn luôn nạp** |
| `docs/GUIDE_developer.md` | Tiêu chuẩn viết code, quy tắc đặt tên, mẫu thiết kế, quy trình TDD, quy trình tái cấu trúc | Logic nghiệp vụ tính năng cụ thể, cấu trúc dữ liệu | Khi thực hiện công việc kỹ thuật/code |
| `docs/ARCH_documentation-governance.md` | Nguồn chân lý quản trị tài liệu, bảng điều hướng | Chi tiết thuật toán và mã nguồn | Khi quản trị/cập nhật tài liệu |
| `docs/ARCH_technical-specs.md` | Kiến trúc hệ thống tổng thể, luồng dữ liệu âm thanh, ranh giới hệ thống, đạo đức sinh trắc học | Quy tắc định dạng chi tiết, token giao diện | Khi làm việc với cấu trúc và dữ liệu |
| `docs/LOGIC_preprocessing.md` | Chuẩn hóa tín hiệu (16kHz Mono), cắt khoảng lặng RMS phân vị 20, repeat padding 64k, RawBoost, Codec | Tiêu chuẩn lập trình chung | Khi làm việc với tiền xử lý âm thanh |
| `docs/LOGIC_models.md` | Baseline AASIST, SSL-AASIST (Wav2Vec2 + HS-GAL), hàm mất mát Weighted CE [0.1, 0.9], huấn luyện 2 pha | Công thức toán xử lý tín hiệu thuần túy | Khi làm việc với kiến trúc mô hình & training |
| `docs/STANDARDS_api-benchmarks.md` | Schema API FastAPI, giao diện Gradio, Bot Telegram, cấu trúc log ẩn danh SHA-256, eval_metrics.csv | Thuật toán đồ thị và mô hình | Khi làm việc với API & benchmark độ trễ |
| `docs/REF_developer-reference.md` | Bảng quy ước đặt tên, bảng tra cứu lệnh, hằng số tham chiếu | Mã nguồn triển khai chi tiết | Khi tra cứu quy ước và tham số |
| `docs/REF_template.md` | Bản mẫu chuẩn để tạo tệp tài liệu mới | Quy tắc nghiệp vụ cụ thể | Khi tạo thêm tệp doc mới |
| `docs/REFACTOR_TODO.md` | Kế hoạch và các mục tiêu tái cấu trúc hiện tại | Quy tắc chuẩn mực chính thức | Khi lập kế hoạch refactor |

---

## Bảng Ánh Xạ Tác Vụ → Tài Liệu Cần Nạp (Task → Load Mapping)

Agent chỉ nạp các tệp liên quan đến tác vụ hiện tại — không nạp toàn bộ thư mục `docs/`.

| Loại tác vụ | Tài liệu cần nạp |
|-------------|------------------|
| Phát triển chung | `AGENTS.md` |
| Thay đổi Tính năng / Thuật toán (Tiền xử lý âm thanh) | `AGENTS.md` + `docs/GUIDE_developer.md` + `docs/LOGIC_preprocessing.md` |
| Thay đổi Tính năng / Thuật toán (Mô hình & Huấn luyện) | `AGENTS.md` + `docs/GUIDE_developer.md` + `docs/LOGIC_models.md` |
| Thay đổi Kiến trúc / Luồng dữ liệu / Bảo mật | `AGENTS.md` + `docs/ARCH_technical-specs.md` |
| Thay đổi Giao diện / API / Định dạng Benchmark | `AGENTS.md` + `docs/STANDARDS_api-benchmarks.md` |
| Tra cứu quy ước & lệnh CLI | `docs/REF_developer-reference.md` |
| Lập kế hoạch tái cấu trúc | `docs/REFACTOR_TODO.md` |
| Quản trị hệ thống tài liệu | `docs/ARCH_documentation-governance.md` |

---

## Quyền Sở Hữu Độc Quyền (Canonical Ownership)

Mỗi nhóm quy tắc chỉ có DUY NHẤT MỘT TỆP làm nguồn chân lý. Không được lặp lại quy tắc ở nhiều tệp.

| Lĩnh vực | Tệp sở hữu duy nhất |
|----------|---------------------|
| Quy tắc phiên làm việc & Siêu dữ liệu | `AGENTS.md` |
| Tiêu chuẩn lập trình & Quy trình TDD | `docs/GUIDE_developer.md` |
| Sổ đăng bạ tài liệu & Điều hướng nạp | `docs/ARCH_documentation-governance.md` |
| Kiến trúc hệ thống, Đạo đức sinh trắc học, Kaggle Hybrid | `docs/ARCH_technical-specs.md` |
| Tiền xử lý tín hiệu, Cắt khoảng lặng, RawBoost, Codec | `docs/LOGIC_preprocessing.md` |
| Kiến trúc mô hình (AASIST, SSL-AASIST), Hàm mất mát, Huấn luyện | `docs/LOGIC_models.md` |
| Đặc tả API, Giao diện Demo/Bot, Chỉ số đánh giá & Log ẩn danh | `docs/STANDARDS_api-benchmarks.md` |

---

## Quy Ước Tiền Tố Đặt Tên Tài Liệu (Naming Convention)

| Tiền tố | Phạm vi | Nội dung |
|---------|---------|----------|
| `GUIDE_` | Tiêu chuẩn | Hướng dẫn viết mã, quy tắc kỹ thuật, giao thức refactor |
| `ARCH_` | Kiến trúc | Thiết kế hệ thống cấp cao, luồng dữ liệu, ranh giới hệ thống |
| `LOGIC_` | Hành vi | Thuật toán cốt lõi, công thức toán học, quy tắc nghiệp vụ |
| `STANDARDS_` | Giao tiếp/IO | Đặc tả endpoint API, schema dữ liệu, giao diện người dùng |
| `REF_` | Tham chiếu | Bảng tra cứu, hằng số, bảng đối chiếu lệnh |
| `INCIDENT_` | Lịch sử lỗi | Báo cáo sự cố, phân tích nguyên nhân gốc và bài học kinh nghiệm |

**Tên cố định (không dùng tiền tố, không được đổi tên):** `AGENTS.md`

---

## Quy Tắc Bảo Trì Tài Liệu

1. **Một quy tắc tối thượng**: Nội dung chỉ tồn tại ở DUY NHẤT MỘT TỆP. Không trùng lặp.
2. **Ngắn gọn nhưng không thiếu**: Xóa các mục trống không có nội dung, nhưng tuyệt đối không xóa quy tắc, trường hợp biên hoặc bảng tham chiếu để tiết kiệm diện tích.
3. **Thêm tài liệu mới**:
   - Chọn tiền tố phù hợp từ bảng quy ước.
   - Bắt buộc đăng ký ngay vào Sổ Đăng Bạ ở trên.
4. **Di chuyển nội dung giữa các tệp**:
   - Sao chép sang tệp đích → Xác nhận đầy đủ → Xóa tại tệp nguồn → Cập nhật liên kết chéo.

---

*v0.1.0 — 2026-10-16*
