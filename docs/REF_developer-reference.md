# REF_developer-reference — Bảng Tra Cứu Dành Cho Nhà Phát Triển

> Tài liệu chỉ dùng để tra cứu tham chiếu. Quy tắc chuẩn mực chính thức nằm tại `docs/GUIDE_developer.md`.

---

## 1. Bảng Quy Ước Đặt Tên (Naming Conventions)

| Đối tượng | Quy tắc | Nên dùng | Không nên dùng |
|-----------|---------|----------|----------------|
| Hàm (Functions) | `snake_case`, động từ + danh từ | `preprocess_audio`, `calculate_eer` | `doStuff`, `thing` |
| Biến (Variables) | Đặt tên theo ý đồ, tránh tên chung chung | `waveform`, `sample_rate`, `labels` | `data`, `tmp` |
| Biến logic (Booleans) | Bắt đầu bằng `is_` / `has_` / `can_` / `should_` | `is_spoof`, `has_silence` | `flag`, `state` |
| Hàm kiểm thử Pytest | Bắt đầu bằng `test_` + đối tượng + tình huống | `test_preprocess_crop_long_audio` | `test1`, `my_test` |
| Tệp âm thanh | `SPK_XXXX_sampleYY.wav` | `SPK_0001_utt01.wav` | `NguyenVanA.wav` |
| Checkpoint trọng số | `best_model.pt`, `checkpoint_epochN.pt` | `best_model.pt` | `model_final_v2_moi.pt` |

---

## 2. Bảng Tra Cứu Các Lệnh CLI Thường Dùng

| Lệnh CLI | Mục đích sử dụng |
|----------|------------------|
| `pytest tests/ -v` | Chạy toàn bộ 31 bài kiểm thử tự động TDD |
| `python manage_kaggle.py push` | Đẩy mã nguồn lên Kaggle GPU để chạy huấn luyện |
| `python manage_kaggle.py status` | Kiểm tra trạng thái kernel trên Kaggle (queued -> running -> complete) |
| `python manage_kaggle.py output` | Tải trọng số huấn luyện và log từ Kaggle về thư mục `./out/` |
| `python scripts/eval_eer.py` | Chạy đánh giá tự động EER trên các tập manifest kiểm thử |
| `python scripts/benchmark_latency.py` | Bấm giờ tự động 30 lần liên tiếp để đo trung vị thời gian phản hồi |
| `uvicorn src.app.server:app --reload` | Khởi động máy chủ phát triển FastAPI |

---

## 3. Quản Lý Phiên Bản (Version Governance)

| Hạng mục | Chi tiết |
|----------|----------|
| Phiên bản hiện tại | `0.2.3` (Frozen Pipeline V14) |
| Nguồn chân lý phiên bản | `docs/ARCH_documentation-governance.md` & `src/__init__.py` |

---

*v0.2.3 — 2026-10-26*
