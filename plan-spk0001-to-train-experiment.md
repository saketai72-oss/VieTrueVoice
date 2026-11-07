# Kế Hoạch Thực Nghiệm: Đưa SPK_0001 vào Tập Huấn Luyện (Nhánh Đối Chứng Thử Nghiệm)

> **File Kế Hoạch**: `plan-spk0001-to-train-experiment.md`  
> **Chế độ**: Orchestration Mode (Phase 1: Planning)  
> **Trạng thái**: Đang chờ người dùng phê duyệt (Waiting for User Approval)  
> **Mục tiêu**: Đánh giá thực nghiệm việc bổ sung dữ liệu người nói `SPK_0001` vào tập Train nhằm kiểm chứng năng lực tổng quát hóa của mô hình trước các giọng trầm đặc dị, đồng thời bảo toàn tính độc lập của bộ 5 tình nguyện viên nghiệm thu (`SPK_0003`..`SPK_0007`).

---

## 1. Bối Cảnh & Phân Tích Rủi Ro Học Thuật (Critical Risk Assessment)

### 1.1 Hiện trạng Bộ Dữ liệu Tình Nguyện Viên
- Tại phiên bản v0.4.2, hệ thống **đã chuẩn hóa bộ 5 tình nguyện viên đối chứng độc lập** gồm: `SPK_0003` (nam, 20 file gốc, 84 clips bona fide, 150 clips spoof), `SPK_0004` (nam), `SPK_0005` (nữ), `SPK_0006` (nữ), và `SPK_0007` (nam).
- Bộ 5 người nói này đã đáp ứng **100% chỉ tiêu nghiệm thu** của Đề cương chi tiết v4 (Đạt Gate 2 Pass Rate **89.3%**, AUC = 0.9343, EER = 11.33%).
- `SPK_0001` (15 clip gốc) hiện được giữ độc lập như một **Ca nghiên cứu âm học chuyên sâu (Forensic Audio Case Study)** trong Chương 2 và Báo cáo chẩn đoán.

### 1.2 Ba Rủi Ro Kỹ Thuật & Học Thuật Khi Chuyển SPK_0001 Sang Tập Train
1. **Rủi ro Hội đồng Bảo vệ Đồ án (Academic Integrity & Data Contamination)**:
   - Trong phương pháp luận nghiên cứu: Việc thấy một người nói trong tập test bị trượt rồi bốc người đó chuyển sang tập train rất dễ bị Hội đồng phản biện đánh giá là hành vi *"cherry-picking"* hoặc *"overfitting có chủ đích"*.
   - **Giải pháp bảo vệ**: Bắt buộc phải trình bày việc này dưới dạng **Một thí nghiệm đối chứng có kiểm soát (Ablation / Controlled Experiment)**: So sánh Checkpoint V5 (Baseline sạch, không có SPK_0001) với Checkpoint V5-Exp (Có thêm SPK_0001 trong train) để chứng minh tính khoa học.
2. **Rủi ro Giả thuyết H2 (Unseen TTS)**:
   - `SPK_0001` có cả clip spoof sinh bằng F5-TTS (Seen) và VieNeu-TTS (Unseen).
   - Nếu đưa vào tập Train, **BẮT BUỘC chỉ được đưa clip F5-TTS**, tuyệt đối nghiêm cấm đưa clip VieNeu-TTS của `SPK_0001` vào train để không làm hỏng tính toàn vẹn của Giả thuyết H2.
3. **Rủi ro Tỷ lệ Gradient (Gradient Washout)**:
   - Tập Train Zalo có 33.000+ mẫu. 15 mẫu bona fide của `SPK_0001` chỉ chiếm **0.045%**. Nếu chỉ thêm đơn thuần 15 mẫu, gradient sẽ bị phân tán hoàn toàn. Nếu nhân bản (oversample) quá nhiều, mô hình sẽ học vẹt định danh cá nhân của `SPK_0001`.

---

## 2. Thiết Kế Kiến Trúc Thử Nghiệm Cô Lập (Isolated Architecture)

Để đảm bảo an toàn tuyệt đối cho codebase chính và không phá vỡ 227 unit tests đang pass 100%:

```
[Kho lưu trữ dữ liệu hiện tại]
    ├── data/manifests_zalo/
    │   ├── train_zalo.csv          <-- GIỮ NGUYÊN 100% (Chuẩn chính thức của Đề cương)
    │   ├── dev_zalo.csv            <-- GIỮ NGUYÊN 100%
    │   └── train_zalo_spk1_exp.csv <-- TẠO MỚI (Nhánh thử nghiệm chứa SPK_0001)
    └── data/raw/SPK_0001/          <-- Nạp 15 file bona fide + paired codecs + F5-TTS
```

- **Mã định danh trong Train**: Đổi `speaker_id` trong manifest thử nghiệm thành `EXP_SPK_0001` để vừa phân biệt rõ ràng với tập nghiệm thu, vừa tương thích với bộ lọc chống rò rỉ của `train.py`.
- **Tập kiểm định độc lập**: Tiếp tục khóa cứng 5 tình nguyện viên `SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007` làm tập nghiệm thu mù (Blind Evaluation Set).

---

## 3. Phân Công Tác Vụ Đa Tác Nhân (Multi-Agent Task Breakdown)

| Tác nhân (Agent) | Trách nhiệm chính | Sản phẩm đầu ra |
|---|---|---|
| **1. project-planner** | Khởi tạo kế hoạch, lập ma trận rủi ro và tiêu chí nghiệm thu | `plan-spk0001-to-train-experiment.md` |
| **2. backend-specialist** | Xây dựng script tạo manifest `train_zalo_spk1_exp.csv`, ghép cặp paired codec (Clean, AAC, Opus, AMR, G.711) và tích hợp cờ huấn luyện | `scripts/make_spk0001_train_manifest.py`, `data/manifests_zalo/train_zalo_spk1_exp.csv` |
| **3. test-engineer** | Viết unit tests kiểm tra tính cô lập (0% rò rỉ SPK_0003..0007, 0% rò rỉ VieNeu), chạy script so sánh đối chứng V5 vs V5-SPK1 | `tests/test_spk0001_train_leakage.py`, `scripts/eval_spk1_exp_comparison.py` |

---

## 4. Các Bước Thực Hiện Cụ Thể (Implementation Steps)

### Bước 1: Tạo Manifest Huấn Luyện Thử Nghiệm (Backend Specialist)
- Trích xuất 15 file bona fide của `SPK_0001` kèm 4 phiên bản codec viễn thông / OTT (Clean 16kHz, AAC Zalo 76k, Opus Zalo 24k, AMR-NB 12.2k, G.711 A-law) $\implies 75$ mẫu bona fide.
- Trích xuất 15 clip spoof F5-TTS (Seen TTS) tương ứng của `SPK_0001` kèm 4 phiên bản codec $\implies 75$ mẫu spoof.
- Ghép $150$ mẫu này vào bản sao `data/manifests_zalo/train_zalo_spk1_exp.csv` với nhãn `speaker_id = EXP_SPK_0001`.
- Kiểm tra loại trừ: Không có bất kỳ dòng nào của `VieNeu-TTS` hoặc `SPK_0003`..`SPK_0007`.

### Bước 2: Thiết Lập Script Huấn Luyện Cục Bộ (Backend Specialist)
- Cấu hình huấn luyện thử nghiệm nhánh `B_zalo_spk1_exp` trên GPU cục bộ (RTX 3050 4GB VRAM) hoặc tạo kernel Kaggle.
- Lưu trọng số tại `out/zalo_b_zalo_v5_spk1_exp/best_model.pt`.

### Bước 3: Đánh Giá Đối Chứng & Phân Tích Hiệu Ứng (Test Engineer)
Đo lường ma trận 4 chiều giữa Checkpoint V5 gốc và Checkpoint V5-SPK1-Exp:
1. **Điểm số trên chính SPK_0001**: Xem 15 file của SPK_0001 có được kéo lên vùng bona fide (Score > 0) hay không.
2. **Điểm số trên 5 tình nguyện viên đối chứng (`SPK_0003`..`0007`)**: Pass rate Gate 2 có duy trì được $\ge 89.3\%$ hay bị suy giảm?
3. **Điểm số trên 11.450 mẫu Dev Zalo**: Dev EER có duy trì $\approx 1.98\%$ hay bị méo phân phối?
4. **Mức độ an toàn trước tấn công Pitch-Drop Spoof**: Đo lường FAR@0 trên các mẫu deepfake bị hạ pitch (-4st, -6st) để đảm bảo mô hình không bị hở sườn bảo mật.

---

## 5. Tiêu Chí Chấp Nhận (Acceptance Criteria)

- [ ] AC-1: File manifest gốc `data/manifests_zalo/train_zalo.csv` không bị biến đổi (MD5/SHA-256 giữ nguyên).
- [ ] AC-2: Toàn bộ 227/227 unit tests hiện tại tiếp tục pass 100%.
- [ ] AC-3: Tuyệt đối không rò rỉ bất kỳ mẫu nào của `VieNeu-TTS` hoặc `SPK_0003`..`0007` vào manifest mới.
- [ ] AC-4: Xuất bảng so sánh đối chứng toàn diện 4 chiều (SPK_0001, 5 SPK đối chứng, Dev Zalo, Pitch-drop spoof) để có cơ sở học thuật vững chắc bảo vệ trước Hội đồng.
