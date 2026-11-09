# Bối Cảnh Agent — ViTrueVoice (v0.4.6) — 2026-11-09

> **Quy tắc Bắt buộc**: Đọc tệp này vào đầu mỗi phiên làm việc mà không cần người dùng nhắc.

## Thiết Lập Dự Án
- **Tên dự án**: ViTrueVoice (Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát)
- **Phiên bản**: 0.4.6 (Must #3 Completion, W06 Report & Chapter 3 Draft) — tuân thủ Semantic Versioning
- **Trạng thái**: Đang hoạt động (Active)
- **Ngăn xếp công nghệ (Tech Stack)**: Python 3.12, PyTorch 2.6 (CUDA), torchaudio, librosa, soundfile, Transformers, FastAPI, Gradio, Python-Telegram-Bot, pytest
- **Điểm neo ngữ cảnh (Context Anchors)**: [PLAN.md](PLAN.md), [README.md](README.md), [howtorun.md](howtorun.md), [deep-voice-generalization.md](deep-voice-generalization.md)

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
> STUBBORN_FACT: Tình nguyện viên `SPK_0001` được chuẩn hóa và chuyển vào tập huấn luyện (`train_zalo.csv`) nhằm bổ sung biểu diễn âm học giọng trầm ngoại lai. Năm (05) tình nguyện viên còn lại (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`) là BỘ NGHIỆM THU ĐỘC LẬP CHÍNH THỨC CỦA DỰ ÁN (gồm 84 clips âm thanh thật độc bản) — nghiêm cấm 100% xuất hiện trong Train, Dev, Calibration, chọn ngưỡng threshold, hoặc fine-tuning.
> STUBBORN_FACT: Chuẩn hóa nạp âm thanh đa định dạng (WAV, M4A, AAC, MP3, OPUS, AMR) qua `load_audio` bắt buộc nhận diện theo magic bytes và giải mã in-memory qua FFmpeg stream, tuyệt đối không phụ thuộc phần mở rộng tệp (`.wav`/`.m4a`).
> STUBBORN_FACT: Kênh Zalo mục tiêu khóa cấu hình Dual Profile: Profile A (`aac_zalo_76k`, AAC-LC 76kbps @ 48kHz mono) và Profile B (`opus_zalo_24k`, Opus 24kbps OGG) liên kết đồng bộ qua trường `base_utt` và bảo toàn ranh giới split.
> STUBBORN_FACT: Mọi thay đổi kỹ thuật, sửa lỗi, hoàn tất pha hoặc cập nhật tiến độ BẮT BUỘC phải đồng bộ cập nhật ngay vào các tệp tài liệu liên quan (PLAN.md, README.md, howtorun.md, AGENTS.md và docs/) trước khi kết thúc tác vụ hoặc commit; tuyệt đối không để tài liệu bị lệch pha so với mã nguồn thực tế.

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
1. **Kiểm thử**: Chạy `pytest tests/ -v`. Toàn bộ 298 bài test phải pass 100%.
2. **Tài liệu**: BẮT BUỘC luôn tự động cập nhật các tệp tài liệu liên quan (`PLAN.md`, `README.md`, `howtorun.md`, `AGENTS.md`, `docs/LOGIC_*.md`, `docs/ARCH_*.md`) mỗi khi có bất kỳ thay đổi logic, sửa lỗi hay tiến độ thực thi mới; không để tài liệu bị lạc hậu so với mã nguồn thực tế.
3. **Dọn dẹp**: Xóa lệnh in debug (print), xóa tệp nháp tạm.
4. **Git**: Thông điệp commit bắt đầu bằng `[AI]`. Chỉ commit khi code thực tế đã chạy thành công. Không push khi người dùng chưa đồng ý.

## Các Cột Mốc Nghiệm Thu (Milestones)
- [x] v0.1.0: Khởi tạo khung dự án, requirements, pipeline CI xanh, module tiền xử lý kèm unit tests TDD.
- [x] v0.2.0 / v0.2.3: Must #1 (W3-W4) — Frozen Pipeline V14: Chuẩn bị dữ liệu 5 tình nguyện viên (`SPK_0001`..`0007`), Dual Pipeline sinh 200 mẫu spoof gốc, lọc 4 cổng (Gate 1-4 Label-Free Prosody), TelephonyCompressor, 5 tệp Manifest 17 cột chia Speaker-Disjoint, 31/31 unit tests xanh 100%.
- [x] v0.2.4: Mở rộng toàn bộ VIVOS (65 người nói) & Mozilla Common Voice 8.0 (22.97h, 419 người nói), cấu trúc manifest chuẩn 18 cột (`pre_codec`), Paired Triplets 1:1:1 cho eval, Hard Text-Disjoint, kiểm định âm tiết dấu thanh. Đã hoàn tất sinh 49.038 mẫu trên Kaggle GPU (Version 22).
- [x] v0.2.5 / v0.3.0: Must #2 (W5) — Hoàn tất huấn luyện & đánh giá thực nghiệm: Baseline LFCC+GMM, SSL-AASIST 3 nhánh (A, B0, B), 138/138 unit tests xanh 100%. Checkpoints A/B0/B đã lưu tại `./out/`. Kết quả thực nghiệm: H1 PASS trên tập nội bộ (giảm 40.46% AMR-NB, 47.55% G.711); In-domain Seen TTS EER = 3.28% (đạt mục tiêu <= 8%); H2 Unseen TTS EER = 21.88%–26.34% (chưa đạt mục tiêu <= 15%); RawBoost giúp giảm thêm 13.8%–22.1% EER.
- [x] v0.4.0: Must #3 (W6) — API suy luận thời gian thực (FastAPI), Web Demo (Gradio $\le 3$ thao tác), Telegram Bot (độ trễ $\le 3$s), AI Eval $\ge 30$ ca. Đã hoàn tất chuẩn hóa quyết định ngưỡng, loại bỏ confidence giả mạo, đồng bộ toàn diện API/UI/Bot và khóa quy trình đánh giá Dev độc lập.
- [x] v0.4.1: Kênh Zalo & Fine-Tuning B_zalo — Hoàn tất chuẩn hóa loader đa định dạng in-memory qua FFmpeg (`audio_loader.py`); khóa cấu hình Dual Profile Zalo (Profile A: AAC-LC 76kbps, Profile B: Opus 24kbps); sinh 3 manifest ghép cặp `base_utt` tại `data/manifests_zalo/` (0% rò rỉ, 100% cô lập `SPK_xxxx` và `VieNeu-TTS`); đo lường và khóa baseline Checkpoint B chính thức trên 11.450 mẫu Dev Zalo (AAC EER 2.62%, Opus EER 2.10%, Clean EER 2.60%, AMR EER 3.13%, G.711 EER 3.13%; 10.490 bona fide, 960 spoof, paired deltas đầy đủ). Huấn luyện thành công Version 3 (Phase 2 CE, Dev EER 1.50%) và Version 4 (AM-Softmax + Pitch Aug, Dev EER 1.56% - 1.73%, FAR@0 giảm 3 lần còn 3.65%).
- [x] v0.4.2: Deep Voice Generalization, Forensic Audio Audit & Data Hygiene — Bóc tách 5 lỗi kỹ thuật và hoàn tất kế hoạch V5 trên GPU cục bộ (RTX 3050 4GB): Huấn luyện thành công 14 epochs, đạt Dev EER kỷ lục **1.98%** trên 11.450 mẫu Zalo; Checkpoint lưu tại `out/zalo_b_zalo_v5_local/best_model.pt`; Gate 2 Pass **95.3%** (+25.98 macro, +26.35 pooled). Hoàn tất chuỗi thực nghiệm bóc tách khoa học: (1) Bác bỏ giả thuyết F0 là nguyên nhân duy nhất; (2) Phát hiện lỗ hổng an ninh trước spoof hạ pitch -6st (AUC giảm từ 0.9895 về 0.6717, EER 43%, FAR 62%) và độ nhạy cục bộ theo người nói (SPK_0007); (3) Hủy bỏ hoàn toàn offset tĩnh và bộ lọc suy luận thô để tránh phá vỡ phân phối; (4) Tự kiểm chứng dữ liệu: phát hiện và cô lập 10 file mock thử nghiệm vào `.quarantine_mock/` (xác nhận tập train/dev Zalo và sweep sạch 100%); (5) Thống nhất giải quyết bài toán độ bền vững bằng Data Augmentation 2 chiều thuần thuật toán, bác bỏ việc thu thập thêm giọng tình nguyện viên; (6) Nhập 20 file gốc `SPK_0003` bù cho `SPK_0001`, hoàn tất pipeline sinh kép F5-TTS và VieNeu-TTS (15 câu x 2 engine = 30 clip spoof clean + paired codecs, 100% SHA-256 độc bản, Pass Rate Gate 2 đạt 89.3% trên 5 tình nguyện viên); (7) Hoàn tất thử nghiệm thăm dò Leave-One-Speaker-Out (LOSO 4 Folds, 48 lượt chạy) theo đặc tả tiên nghiệm Pre-registered SPEC v1.2.1: Xác nhận chuyển giao dương trên người bị giữ lại (Mean Δs > 0, CI 95% cận dưới > 0, pass rate tăng 10.0–48.9 pp) nhưng đánh đổi bằng việc Dev EER và APCER vượt ngưỡng an ninh (0/4 Folds đạt); đối chứng nhánh Replay-only và phân tích H2 VieNeu-TTS củng cố tính bất khả xâm phạm của STUBBORN_FACT cô lập 100% dữ liệu tình nguyện viên khỏi quá trình huấn luyện; hoàn thành 100% cả 3 chứng chỉ AWS Gói A; xuất bản báo cáo W04 và W05 (Must #2, Chương 2 hoàn chỉnh 18 trang); 227/227 unit tests pass 100%.
- [x] v0.4.3: BPCER Remediation & Multi-window Inference Pooling (Pha A + C + D) — Giải quyết dứt điểm hiện tượng nhận diện sai giọng thật tình nguyện viên mà không cần huấn luyện lại GPU (0 GPU retrain): (1) Tích hợp trích xuất đa cửa sổ trượt (window 4.0s = 64.000 mẫu, hop 1.0s = 16.000 mẫu, tối đa 5 cửa sổ) gộp thành 1 mini-batch `(N_windows, 64000)` suy luận song song trong 1 forward pass duy nhất kèm max-pooling (`src/preprocessing/pooling.py`); (2) Nâng tỷ lệ vượt Gate 2 trên 4 người nói đối chứng (`SPK_0004`..`0007`, 64 files) lên **98.4% (63/64)** trên cả V4 và V5 (file duy nhất còn lại `SPK_0004_03.wav` dài 3.84s < 4.0s nên chỉ có 1 cửa sổ); trên cả 5 SPK đối chứng (`SPK_0003`..`0007`, 84 files), V5 đạt **95.2% (80/84)**; (3) Bảo toàn an ninh: Dev Spoof APCER dưới max-pooling đạt **6.77% $\le 8.0\%$** tại $\theta = 0.0$; (4) Tích hợp guardrail hiệu chỉnh enrollment: tự động từ chối can thiệp khi $|offset| > 4 \times IQR$ (như ngoại lai `SPK_0001` lệch -9.91 IQR), bảo toàn điểm thô phục vụ định tuyến duyệt thủ công; (5) Giữ vững NFR1 với trung vị độ trễ **66.3ms** (P90 68.2ms), nhanh gấp ~45 lần trần $\le 3.0$s; (6) 272/272 unit tests pass 100%.
- [x] v0.4.4: SPK_0001 Train Migration, B_zalo V6 Local Training & 5-Speaker Acceptance Isolation — Hoàn tất trọn vẹn chu trình V6 theo kế hoạch `plan-spk0001-train-transfer.md`: (1) Chuyển 125 dòng `SPK_0001` (75 bona fide + 50 F5-TTS spoof, loại 100% VieNeu-TTS) vào `data/manifests_zalo/train_zalo.csv` (nâng quy mô tập Train lên 50.710 dòng); (2) Khóa chặt 5 tình nguyện viên đối chứng held-out (`SPK_0003`..`0007`, 84 clips) làm Bộ nghiệm thu độc lập chính thức của đề tài; (3) Tối ưu hóa tốc độ GPU cục bộ (RTX 3050 4GB), tăng tốc ~48 lần bằng cách tận dụng 1.500 mẫu deep-voice offline, cấu hình `batch_size=8, accum_steps=2`; (4) Huấn luyện thành công mô hình B_zalo V6: checkpoint lưu tại `out/zalo_b_zalo_v6_local/best_model.pt` (Phase 2 Ep 5, Dev EER = 2.60%); (5) Đánh giá 3 Gates độc lập với Multi-window Max-Pooling: Gate 2 trên 4 SPK đối chứng đạt **100.0% (64/64)** PASS tuyệt đối (kể cả clip ngắn `SPK_0004_03.wav`), trên cả 5 SPK nghiệm thu đạt **96.4% (81/84)** với Mean score dương rất cao (+17.65 đến +42.82); Gate 3 PASS toàn diện (AAC-LC 76k EER 1.73%, Opus 24k EER 1.56%, Clean EER 1.56%); Gate 1 nhận diện SPK_0001 đạt 73.3% (11/15) với Mean score đảo chiều lên +10.05; (6) Nâng cấp toàn diện giao diện Gradio Web: Chuyển đổi thiết kế Stitch chuẩn phòng Lab Forensics, tích hợp Dual Theme 1-click (Dark Mode / Light Mode) với độ tương phản WCAG AAA, đóng gói Docker 1-lệnh (`docker-compose up -d`); (7) 292/292 unit tests pass 100%.
- [x] v0.4.5: Unseen TTS Multi-Model Generalization Expansion & Degradation Benchmark (Kokoro-Vietnamese, Bark, OmniVoice) — Mở rộng toàn diện ma trận kiểm định Giả thuyết H2 trên 5 tình nguyện viên đối chứng held-out: (1) Tích hợp và chuẩn hóa Kokoro-Vietnamese (`contextboxai/Kokoro-Vietnamese`, StyleTTS 2 + iSTFTNet @ 24kHz, `vig2p`), sinh 375 tệp spoof độc lập; (2) Tích hợp và sinh 375 tệp spoof zero-shot qua `OmniVoice` (VoiceStudio CFM) kèm 4 codec viễn thông / Zalo; (3) Hoàn tất benchmark đo đạc mức độ suy giảm (Degradation Analysis) trên 1.584 file âm thanh: Nhóm Seen TTS (F5 + VieNeu, 750 mẫu) đạt EER 13.33%, Pass Rate 79.73%; Nhóm Unseen TTS (Kokoro + OmniVoice, 750 mẫu) đạt EER 15.87%, Pass Rate 73.33%; Mức độ suy giảm cực kỳ khiêm tốn ($\Delta\text{EER} = +2.54\%$, $\Delta\text{PassRate} = -6.40\%$, $\Delta\text{Score} = +3.94$), chứng minh tính bền vững cao của mô hình B_zalo V6; (4) Khám phá quy luật kênh thoại nén: Zalo AAC-LC 76k / Opus 24k gây suy giảm nhiều nhất (-1.33% đến -8.00% Pass Rate), trong khi kênh băng hẹp 8kHz (AMR-NB/G.711) tăng cường độ nhạy phân tách (+5.3% đến +10.7%); (5) Toàn bộ 298/298 unit tests pass 100%.
- [x] v0.4.6: Must #3 Completion, W06 Official Report & Chapter 3 System Design Draft — Hoàn tất trọn vẹn yêu cầu Tuần 6 (W06 / Checkpoint 6): (1) Xuất bản Báo cáo Tuần 6 chính thức (`DACN_2380601959_NguyenThanhTai_W06.docx`, 5.857 từ, 7 bảng và `.pdf`, 888 KB); (2) Hoàn thành bản nháp Chương 3 (Thiết kế hệ thống 6 trang chuẩn mực: Kiến trúc C4 Mức 2 Container Diagram, Xử lý in-memory stream Zero-persistence theo Luật 91/2025/QH15, Khối suy luận B_zalo V6 kết hợp Multi-window Max-Pooling, Web Forensics UI Iconify Solar Framework, và An ninh bảo mật); (3) Trả lời câu hỏi tư duy Tuần 6 (Phân tích chi phí thiệt hại của lỗi Bỏ sót/APCER so với Báo nhầm/BPCER, khóa cứng ngưỡng $\theta = 0.0$ kết hợp Max-Pooling bảo toàn tỷ lệ bỏ sót 6.77% $\le 8.0\%$ và Pass Rate 96.4%); (4) Đóng gói và vận hành ổn định hệ thống Docker Compose đa container (`vitruevoice-api` port 8000 và `vitruevoice-bot` Telegram Daemon); (5) Duy trì bộ kiểm thử TDD 298/298 bài xanh 100%.
- [ ] v1.0.0: Thử nghiệm Pilot & Nghiệm thu (W7-W8) — Đóng gói Docker AWS EC2, S3 Lifecycle, CI/CD, bảo mật nâng cao, Red Team Pilot CLB ATTT HUTECH.

## Lệnh Thường Dùng
- `pytest tests/ -v`: Chạy toàn bộ 298 bài kiểm thử unit test.
- `python scripts/build_w06_report_docx.py`: Tự động biên dịch Báo cáo Tuần 6 chuẩn khoa học HUTECH (`.docx`).
- `python scripts/export_w06_pdf.py`: Xuất bản trực tiếp Báo cáo Tuần 6 sang định dạng `.pdf`.
- `python scripts/simulate_zalo_webhook.py --audio data/bonafide_ref/SPK_0004/SPK_0004_01.wav`: Mô phỏng gửi tin nhắn thoại Zalo Webhook tới hệ thống.
- `python scripts/audit_v6_manifest.py`: Kiểm toán an ninh và tính toàn vẹn của Manifest Zalo V6.
- `python scripts/train_local_zalo_v6.py`: Khởi động huấn luyện B_zalo V6 Local trên GPU RTX 3050 (AMP FP16, batch 4 accum 4, AM-Softmax + Pitch Aug).
- `python scripts/setup_local_train.py`: Tải Checkpoint B & tệp nén 3.26GB từ Kaggle, giải nén chọn lọc dữ liệu Zalo vào máy cục bộ.
- `python scripts/train_local_zalo.py`: Huấn luyện B_zalo V5 tối ưu cho máy cục bộ (RTX 3050 4GB VRAM) và tự động đánh giá 3 Gates.
- `python manage_kaggle.py push deploy_zalo_train`: Đẩy kernel huấn luyện B_zalo fine-tuning lên Kaggle GPU.
- `python manage_kaggle.py status deploy_zalo_train`: Kiểm tra trạng thái kernel huấn luyện B_zalo.
- `python manage_kaggle.py output deploy_zalo_train out/zalo_b_zalo_v4 --force`: Tải kết quả checkpoint và báo cáo B_zalo về máy local.
- `python scripts/eval_v5_gate.py`: Đánh giá 3 cổng kiểm định độc lập với `--pooling` (mặc định True).
- `python scripts/benchmark_latency.py`: Đo kiểm thời gian đáp ứng thời gian thực với `--pooling` (30 lần lặp).
- `python scripts/eval_voices_new.py`: Đánh giá trực tiếp trên bộ thu mới `VoiCes` ($F_0 \approx 105 - 118$ Hz).
- `python scripts/eval_v4_summary.py`: So sánh đối chứng V2 vs V3 vs V4 trên Dev Zalo và 15 file `SPK_0001`.
- `python scripts/train.py --branch B_zalo --loss am_softmax --am-s 30.0 --am-m 0.35 --pitch-aug --pitch-prob 0.9 --pitch-range -8.0 4.0`: Huấn luyện nhánh fine-tune Zalo Version 5.
- `uvicorn src.app.server:app --reload`: Khởi động máy chủ phát triển FastAPI.

---

*v0.4.5 — 2026-11-09*
