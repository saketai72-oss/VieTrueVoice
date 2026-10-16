# GUIDE_developer — Tiêu Chuẩn Thực Thi & Lập Trình Cho ViTrueVoice

---

## 1. Các Quy Tắc Cốt Lõi

> Ràng buộc cứng. AI bắt buộc phải tuân thủ vô điều kiện.

| Quy tắc | Chi tiết thực tế |
|---------|------------------|
| Không tự ý refactor | Tuyệt đối không tái cấu trúc mã đang hoạt động nếu người dùng không yêu cầu rõ ràng |
| Quy ước Git Commit | Mọi bản commit do AI sinh ra bắt buộc gắn tiền tố `[AI]`. Không tự ý push khi chưa có sự đồng ý |
| Bắt buộc TDD | Viết kịch bản kiểm thử (`pytest`) trước khi viết mã nguồn cho mọi logic liên quan đến tiền xử lý, mô hình, mất mát, đánh giá và API |
| Đạo đức Dữ liệu & PII | Tuyệt đối không lưu tên thật, số điện thoại hoặc giọng nói định danh cá nhân. Bắt buộc dùng mã `SPK_XXXX` và băm `SHA-256` |
| Xử lý trực tiếp trên RAM | Đọc file âm thanh qua stream `io.BytesIO` trên RAM trong API/Bot; xóa hủy file tạm ngay lập tức sau khi trả kết quả |

---

## 2. Tiêu Chuẩn Tái Cấu Trúc (Refactoring Standards)

### Khi Nào Cần Tách Hàm (Extract Function)

| Điều kiện kích hoạt | Hành động bắt buộc |
|---------------------|-------------------|
| Đoạn mã hoặc mẫu xử lý xuất hiện từ **2 lần trở lên** | Trích xuất thành hàm dùng chung ngay lập tức — không ngoại lệ |
| Thân hàm vượt quá **20 dòng** | Tách các đoạn logic bên trong thành các hàm trợ giúp (helpers) có tên tường minh |
| Biểu thức cần chú thích (comment) mới hiểu | Thay thế biểu thức bằng một hàm có tên mô tả rõ ý đồ |
| Thao tác biến đổi tín hiệu lặp lại | Trích xuất thành hàm tiền xử lý riêng biệt |

### Khi Nào Cần Tách Tệp (Split File)

| Điều kiện kích hoạt | Hành động bắt buộc |
|---------------------|-------------------|
| Tệp vượt quá **200 dòng** | Xem xét phân tách nếu tệp đảm nhận từ 2 trách nhiệm trở lên |
| Tệp vượt quá **400 dòng** | Bắt buộc chia tách — mỗi tệp chỉ giữ một trách nhiệm duy nhất |
| Tệp chứa từ 2 nhóm khái niệm không liên quan | Chia tách bất kể số lượng dòng mã |
| Một hàm được tái sử dụng ở 2 tệp khác nhau | Chuyển hàm đó vào tệp helper dùng chung |

### Quy Tắc Cấu Trúc Module

| Quy tắc | Chi tiết thực tế |
|---------|------------------|
| Một trách nhiệm cho mỗi tệp | Mỗi tệp làm đúng một việc: xử lý tín hiệu, định nghĩa kiến trúc mạng, điều khiển vòng lặp huấn luyện, hoặc tính toán chỉ số |
| File điều phối (Orchestrator) phải gọn | Các tệp entry-point (`train.py`, `manage_kaggle.py`, `src/app/server.py`) chỉ giữ vai trò kết nối, không chứa thuật toán lõi |
| Hàm trợ giúp (Helper) phi trạng thái | Các hàm helper phải là hàm thuần túy (pure function) — không gây side-effect, không đọc/ghi biến toàn cục |
| Chiều import một chiều | Preprocessing không import Models. Models không import App. Helpers không import Orchestrators |

### Giao Thức Tái Cấu Trúc Không Mất Mát (Zero-Loss Refactor Protocol)

Áp dụng cho mọi lần chia tách tệp hoặc tái cấu trúc lớn:

1. **Khảo sát (Audit)**: Đọc toàn bộ module và các nơi đang gọi trước khi chỉnh sửa.
2. **Tạo đích đến (Create targets)**: Tạo các tệp/hàm mới trước khi xóa mã cũ.
3. **Cầu nối (Bridge)**: Dùng re-export hoặc adapter để các module gọi cũ không bị gãy import đột ngột.
4. **Xác minh (Verify)**: Chạy `pytest tests/ -v` để đảm bảo mọi bài kiểm thử đều vượt qua.
5. **Cắt bỏ (Cut)**: Xóa bỏ mã nguồn cũ chỉ sau khi hành vi mới đã hoàn toàn ổn định.
6. **Kiểm tra lại (Verify again)**: Chạy lại toàn bộ test suite lần cuối.

---

## 3. Các Phản Mẫu Bị Nghiêm Cấm (Anti-Patterns)

| Phản mẫu | Hậu quả kỹ thuật | Cách xử lý đúng |
|----------|------------------|-----------------|
| Đệm số 0 (Zero-padding) cho âm thanh ngắn | Gây đứt gãy phổ tín hiệu, làm hỏng đặc trưng SincConv / AASIST | Dùng nối lặp `Repeat Padding` (`np.tile`) cho đủ 64.000 mẫu |
| Trọng số bằng nhau trong hàm mất mát CE | Tỷ lệ báo động giả (False Alarm) cao trên người dùng thật | Dùng trọng số cố định `weights = [0.1, 0.9]` cho `[Spoof, Bona fide]` |
| Lưu file ghi âm người dùng lâu dài trên ổ cứng | Vi phạm Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 & Nghị định 356/2025/NĐ-CP | Đọc qua RAM stream (`io.BytesIO`) và xóa hủy tệp tạm ngay lập tức |
| Ghi tên tệp gốc vào log đánh giá | Rò rỉ danh tính người đóng góp giọng nói | Băm ẩn danh toàn bộ bằng mã `SHA-256` |
| Lặp lại logic biến đổi tín hiệu ở nhiều file | Không đồng bộ khi cập nhật giải thuật | Tập trung tại `src/preprocessing/audio_processor.py` |

---

## 4. Các Mặc Định Về Kiến Trúc

### Phân Tách 3 Lớp (3-Layer Separation)
- **Lớp Tín Hiệu & Dữ Liệu**: `src/preprocessing/` (nhận âm thanh thô → tensor 16kHz mono 64.000 mẫu đã chuẩn hóa).
- **Lớp Biểu Diễn & Mô Hình**: `src/models/` và `src/training/` (trích xuất đặc trưng tự giám sát Wav2Vec2 + đồ thị chú ý HS-GAL).
- **Lớp Dịch Vụ & Trình Diễn**: `src/app/` (API FastAPI, giao diện Gradio, Bot Telegram).

### Không Gian Tên & Định Danh (Namespace Governance)
- **File Manifests**: Lưu tại `data/manifests/{train,dev,test_indomain,test_unseen}.csv` gồm các cột `audio_path,label,speaker_id`.
- **Quy ước Nhãn**: `0` = Giả mạo (`Spoof`), `1` = Giọng thật (`Bona fide`).

---

## 5. Xử Lý Các Trường Hợp Biên (Edge Cases)

- **File âm thanh hoàn toàn im lặng**: Tự động trả về mảng zero kích thước 64.000 mẫu kèm xử lý tránh chia cho 0 trong chuẩn hóa độ lệch chuẩn (`std < 1e-8`).
- **File âm thanh cực ngắn (< 0,2 giây)**: Nối lặp tuần hoàn cho đến khi đạt `>= 64.000 mẫu`.
- **File âm thanh dài (> 10 giây)**: Khi suy luận cắt cửa sổ trượt 4,0 giây (64.000 mẫu) và lấy trung bình cộng điểm tin cậy.

---

*v0.1.0 — 2026-10-16*
