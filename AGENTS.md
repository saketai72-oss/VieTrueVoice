# Bối Cảnh Agent — ViTrueVoice (v0.4.1) — 2026-10-30

> **Quy tắc Bắt buộc**: Đọc tệp này vào đầu mỗi phiên làm việc mà không cần người dùng nhắc.

## Thiết Lập Dự Án
- **Tên dự án**: ViTrueVoice (Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát)
- **Phiên bản**: 0.4.1 (Zalo Dual-Profile Paired Pipeline & B_zalo Fine-Tuning) — tuân thủ Semantic Versioning
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
- **Đặc tả Kỹ thuật & Hệ thống**: `docs/ARCH_technical-specs.md` — luồng xử lý hệ thống, cấu trúc Kaggle Hybrid, hạ tầng AWS, đạo đức sinh trắc học.
- **Sinh Mẫu Giả & Dữ Liệu**: `docs/LOGIC_data-generation.md` — sinh kép F5-TTS / VieNeu-TTS v3 Turbo, lọc 4 cổng, 5 manifests 18 cột, Common Voice 8.0, Paired Triplets, Hard Text-Disjoint, dò shortcut.
- **Thuật toán Tiền xử lý**: `docs/LOGIC_preprocessing.md` — chuẩn hóa 16kHz mono, EBU R128 (-23 LUFS), Z-score, cắt khoảng lặng P20, repeat padding 64k, RawBoost, suy giảm Codec.
- **Kiến trúc Mô hình & Huấn luyện**: `docs/LOGIC_models.md` — Baseline LFCC+GMM / AASIST, SSL-AASIST, Dynamic Weighted CE $w_c = \frac{N}{2 \cdot N_c}$, thiết kế đối chứng CH1/CH2, huấn luyện 2 pha.
- **Tiêu chuẩn API & Đánh giá**: `docs/STANDARDS_api-benchmarks.md` — endpoint FastAPI, Gradio/Bot UI, log ẩn danh SHA-256, chuẩn đo độ trễ, AI Eval $\ge 30$ ca.
- **Quy tắc**: Tuyệt đối không hợp nhất các tệp này nếu không có chỉ định rõ ràng. Phân tách ranh giới để ngăn ngừa lỗi hồi quy.

## Các Quyết Định Có Chủ Đích (STUBBORN_FACTs)
> STUBBORN_FACT: Sử dụng kỹ thuật nối lặp (Repeat Padding) thay cho đệm số 0 (Zero-padding) khi độ dài < 64.000 mẫu — nhằm duy trì tính liên tục phổ - thời gian cho bộ lọc AASIST / Wav2Vec 2.0.
> STUBBORN_FACT: Hàm mất mát Weighted Cross-Entropy bắt buộc tính động theo tỷ lệ nghịch tần suất thực tế của tập Train: $w_c = \frac{N}{2 \cdot N_c}$ qua `loss_weights_from_counts` (sau khi lọc VieNeu khỏi train, spoof chiếm $\approx 7.5\% \implies W \approx [0.925, 0.075]$). Tuyệt đối KHÔNG dùng đồng thời `WeightedRandomSampler` cùng Weighted Loss để tránh bù trừ kép (double penalty).
> STUBBORN_FACT: Ràng buộc Hard Text-Disjoint áp dụng bắt buộc giữa mọi cặp split (Test giữ nguyên $\rightarrow$ Dev lọc trùng $\rightarrow$ Train lọc trùng) và giữa các vai trò cùng người nói (ref/enroll hoàn toàn tách biệt khỏi eval).
> STUBBORN_FACT: Công cụ Unseen TTS (`VieNeu-TTS`) bắt buộc loại bỏ 100% khỏi tập Train và Dev (`manifests_seen_only`), chỉ giữ lại trong tập Test để đảm bảo giá trị khoa học của Giả thuyết H2.
> STUBBORN_FACT: Chuẩn hóa văn bản `normalize_for_eval` (NFC, chuẩn hóa dấu thanh cuối từ `_fix_tone_token`, loại câu có chữ số `has_digits`) CHỈ dùng cho Gate 1 WER/CER và lọc trùng lặp — prompt TTS bắt buộc giữ nguyên văn bản thô để bảo toàn ngữ âm.
> STUBBORN_FACT: Mọi bản ghi âm thanh trong benchmarks/latency_log.json phải dùng mã băm SHA-256 thay cho tên file hoặc ID người dùng — tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP.
> STUBBORN_FACT: Luồng âm thanh trong API/Bot phải được xử lý trực tiếp trên RAM (stream in-memory) và xóa hủy file tạm ngay lập tức sau khi suy luận — ngăn chặn tuyệt đối nguy cơ rò rỉ giọng nói sinh trắc học.
> STUBBORN_FACT: Độ dài đầu vào mô hình cố định chính xác 64.000 mẫu (4,0 giây ở tần số 16kHz) — đây là kích thước tensor đầu vào bắt buộc của khối front-end AASIST / Wav2Vec2.
> STUBBORN_FACT: Mọi bản commit Git do AI tạo ra BẮT BUỘC có tiền tố `[AI]` ở đầu thông điệp commit và chỉ commit khi code đã thực nghiệm thành công.
> STUBBORN_FACT: Toàn bộ tập dữ liệu tình nguyện viên `SPK_xxxx` là BỘ NGHIỆM THU TÁCH BIỆT HOÀN TOÀN — nghiêm cấm 100% đưa vào Train, Dev, Calibration, chọn threshold, chọn checkpoint hoặc fine-tuning.
> STUBBORN_FACT: Chuẩn hóa nạp âm thanh đa định dạng (WAV, M4A, AAC, MP3, OPUS, AMR) qua `load_audio` bắt buộc nhận diện theo magic bytes và giải mã in-memory qua FFmpeg stream, tuyệt đối không phụ thuộc phần mở rộng tệp (`.wav`/`.m4a`).
> STUBBORN_FACT: Kênh Zalo mục tiêu khóa cấu hình Dual Profile: Profile A (`aac_zalo_76k`, AAC-LC 76kbps @ 48kHz mono) và Profile B (`opus_zalo_24k`, Opus 24kbps OGG) liên kết đồng bộ qua trường `base_utt` và bảo toàn ranh giới split.

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
| Gán cứng trọng số loss hoặc dùng đồng thời sampler | Tính động $w_c = \frac{N}{2 \cdot N_c}$ và không dùng `WeightedRandomSampler` |
| Rò rỉ văn bản hoặc rò rỉ người nói giữa các split | Áp dụng Speaker-disjoint + Hard Text-disjoint (Test $\rightarrow$ Dev $\rightarrow$ Train) |
| Chuẩn hoá làm biến dạng từ tiếng Việt ("toàn" $\rightarrow$ "tòan") | Chỉ chuẩn hoá dấu thanh cuối từ (`_fix_tone_token`) |
| Quên đăng ký tài liệu mới vào sổ quản trị | Đăng ký vào `docs/ARCH_documentation-governance.md` trước khi sử dụng |

## Giao Thức Trước Khi Commit (Pre-Commit Protocol)
1. **Kiểm thử**: Chạy `pytest tests/ -v`. Toàn bộ 202 bài test phải pass 100%.
2. **Tài liệu**: Cập nhật tệp `docs/LOGIC_*.md` hoặc `docs/ARCH_*.md` liên quan nếu logic thay đổi (thông qua yêu cầu doc sweep rõ ràng).
3. **Dọn dẹp**: Xóa lệnh in debug (print), xóa tệp nháp tạm.
4. **Git**: Thông điệp commit bắt đầu bằng `[AI]`. Chỉ commit khi code thực tế đã chạy thành công. Không push khi người dùng chưa đồng ý.

## Các Cột Mốc Nghiệm Thu (Milestones)
- [x] v0.1.0: Khởi tạo khung dự án, requirements, pipeline CI xanh, module tiền xử lý kèm unit tests TDD.
- [x] v0.2.0 / v0.2.3: Must #1 (W3-W4) — Frozen Pipeline V14: Chuẩn bị dữ liệu 5 tình nguyện viên (`SPK_0001`..`0007`), Dual Pipeline sinh 200 mẫu spoof gốc, lọc 4 cổng (Gate 1-4 Label-Free Prosody), TelephonyCompressor, 5 tệp Manifest 17 cột chia Speaker-Disjoint, 31/31 unit tests xanh 100%.
- [x] v0.2.4: Mở rộng toàn bộ VIVOS (65 người nói) & Mozilla Common Voice 8.0 (22.97h, 419 người nói), cấu trúc manifest chuẩn 18 cột (`pre_codec`), Paired Triplets 1:1:1 cho eval, Hard Text-Disjoint, kiểm định âm tiết dấu thanh. Đã hoàn tất sinh 49.038 mẫu trên Kaggle GPU (Version 22).
- [x] v0.2.5 / v0.3.0: Must #2 (W5) — Hoàn tất huấn luyện & đánh giá thực nghiệm: Baseline LFCC+GMM, SSL-AASIST 3 nhánh (A, B0, B), 138/138 unit tests xanh 100%. Checkpoints A/B0/B đã lưu tại `./out/`. Kết quả thực nghiệm: H1 PASS trên tập nội bộ (giảm 40.46% AMR-NB, 47.55% G.711); In-domain Seen TTS EER = 3.28% (đạt mục tiêu <= 8%); H2 Unseen TTS EER = 21.88%–26.34% (chưa đạt mục tiêu <= 15%); RawBoost giúp giảm thêm 13.8%–22.1% EER.
- [/] v0.4.0: Must #3 (W6) — API suy luận thời gian thực (FastAPI), Web Demo (Gradio $\le 3$ thao tác), Telegram Bot (độ trễ $\le 3$s), AI Eval $\ge 30$ ca. Đã hoàn tất chuẩn hóa quyết định ngưỡng, loại bỏ confidence giả mạo, đồng bộ toàn diện API/UI/Bot và khóa quy trình đánh giá Dev độc lập.
- [/] v0.4.1: Kênh Zalo & Fine-Tuning B_zalo — Hoàn tất chuẩn hóa loader đa định dạng in-memory qua FFmpeg (`audio_loader.py`); khóa cấu hình Dual Profile Zalo (Profile A: AAC-LC 76kbps, Profile B: Opus 24kbps); sinh 3 manifest ghép cặp `base_utt` tại `data/manifests_zalo/` (0% rò rỉ, 100% cô lập `SPK_xxxx` và `VieNeu-TTS`); đo lường và khóa baseline Checkpoint B chính thức trên 11.450 mẫu Dev Zalo (AAC EER 2.62%, Opus EER 2.10%, Clean EER 2.60%, AMR EER 3.13%, G.711 EER 3.13%; 10.490 bona fide, 960 spoof, paired deltas đầy đủ); giải quyết đường dẫn manifest qua TDD trong `scripts/train.py`, hoàn tất smoke test CPU nội bộ xác nhận đóng băng 211 tensors Wav2Vec2 và cập nhật 84 tensors HS-GAL/proj; đóng gói hoàn chỉnh kernel `deploy_zalo_train/` sẵn sàng đẩy Kaggle khi quota reset. 202/202 unit tests xanh 100%.
- [ ] v1.0.0: Thử nghiệm Pilot & Nghiệm thu (W7-W8) — Đóng gói Docker AWS EC2, S3 Lifecycle, CI/CD, bảo mật nâng cao, Red Team Pilot CLB ATTT HUTECH.

## Lệnh Thường Dùng
- `pytest tests/ -v`: Chạy toàn bộ 202 bài kiểm thử unit test.
- `python manage_kaggle.py push deploy_zalo_train`: Đẩy kernel huấn luyện B_zalo fine-tuning lên Kaggle GPU.
- `python manage_kaggle.py status deploy_zalo_train`: Kiểm tra trạng thái kernel huấn luyện B_zalo.
- `python manage_kaggle.py output deploy_zalo_train out/zalo_b_zalo --force`: Tải kết quả checkpoint và báo cáo B_zalo về máy local.
- `python manage_kaggle.py push deploy_zalo_eval`: Đẩy kernel đo baseline Zalo lên Kaggle GPU.
- `python manage_kaggle.py status deploy_zalo_eval`: Kiểm tra trạng thái kernel đo baseline Zalo.
- `python manage_kaggle.py output deploy_zalo_eval`: Tải 11.450 scores và baseline report về `out/zalo_baseline/`.
- `python scripts/train.py --branch B_zalo --init-ckpt out/kaggle_ssl_out/best_model_B.pt --manifest-dir data/manifests_zalo`: Huấn luyện nhánh fine-tune Zalo.
- `python scripts/eval_zalo_baseline.py --ckpt out/kaggle_ssl_out/best_model_B.pt --manifest data/manifests_zalo/dev_zalo.csv`: Đo lường baseline kênh Zalo.
- `python scripts/generate_zalo_paired_manifests.py`: Sinh manifest ghép cặp Zalo Profiles A & B.
- `uvicorn src.app.server:app --reload`: Khởi động máy chủ phát triển FastAPI.

---

*v0.4.1 — 2026-10-30*
