# Kế Hoạch Thực Thi: Giai Đoạn 01 (Must #1) & Module Tăng Cường Kênh Truyền (RawBoost / Codec)

> **Bắt buộc cho Agent**: Áp dụng triệt để quy trình TDD (`tests/` trước, code sau), tuân thủ tiền tố commit `[AI]`, và không phá vỡ các `STUBBORN_FACTs` đã được định nghĩa trong [AGENTS.md](../../AGENTS.md).

**Mục tiêu:** Xây dựng hoàn chỉnh đường ống dữ liệu độc lập người nói (Speaker-Disjoint Split), kịch bản lọc chất lượng ASR WER, bộ mô phỏng tăng cường tín hiệu RawBoost & nén Codec kênh thoại (Opus/AMR/8kHz), sẵn sàng nạp vào DataLoader huấn luyện.

**Kiến trúc:**
- `scripts/split_dataset.py`: Thuật toán phân chia phân tán Speaker-Disjoint (70% Train / 15% Dev / 15% Test) đảm bảo 0% rò rỉ danh tính người nói giữa các tập.
- `src/preprocessing/rawboost.py`: Thuật toán RawBoost miền thời gian (ISD, SSI, LnL) tăng cường chống biến dạng tín hiệu.
- `src/preprocessing/codec_simulator.py`: Bộ mô phỏng nén viễn thông (Opus 16-32kbps, điện thoại 8kHz dải lọc 300Hz–3400Hz).
- `scripts/filter_asr_wer.py`: Kịch bản tính Word Error Rate (WER) và lọc mẫu giả bị biến dạng/lặp âm.
- `scripts/generate_spoof.py`: Entry-point tự động hóa lệnh sinh mẫu giả từ F5-TTS và VieNeu-TTS.

**Ngăn xếp công nghệ:** Python 3.12, PyTorch 2.6, torchaudio, librosa, soundfile, scipy, pandas, scikit-learn, pytest.

**Tài liệu đặc tả liên quan:**
- [PLAN.md](../../PLAN.md) — Giai đoạn 01 (Bước 1.1–1.3) & Giai đoạn 02 (Bước 2.3).
- [docs/LOGIC_preprocessing.md](../LOGIC_preprocessing.md) — Công thức toán học và logic chuẩn hóa tín hiệu.
- [docs/ARCH_technical-specs.md](../ARCH_technical-specs.md) — Ranh giới hệ thống và đạo đức sinh trắc học.

---

## Các Ràng Buộc Toàn Cục (Global Constraints)

1. **Ràng buộc Speaker-Disjoint**: Tập người nói giữa các tập phân chia phải tách biệt tuyệt đối:
   $$\text{Speakers}(Train) \cap \text{Speakers}(Dev) = \emptyset$$
   $$\text{Speakers}(Train) \cap \text{Speakers}(Test) = \emptyset$$
   $$\text{Speakers}(Dev) \cap \text{Speakers}(Test) = \emptyset$$
2. **Kích thước đầu vào chuẩn**: Mọi biến đổi tín hiệu phải giữ nguyên tensor độ dài 64.000 mẫu điểm (4.0 giây tại 16kHz).
3. **Đạo đức dữ liệu PII**: Tuyệt đối không ghi thông tin định danh cá nhân vào manifest. Trường ID người nói bắt buộc là mã `SPK_XXXX`.
4. **Quy ước nhãn**: `0 = Spoof` (Giả mạo), `1 = Bona fide` (Giọng thật).

---

## Chi Tiết Các Nhiệm Vụ (Task Breakdown)

### Nhiệm Vụ 1: Phân Chia Tập Dữ Liệu Độc Lập Người Nói (`scripts/split_dataset.py`)
**Tệp tin:**
- Tạo mới: `scripts/split_dataset.py`
- Kiểm thử: `tests/test_split_dataset.py`

### Nhiệm Vụ 2: Thuật Toán Tăng Cường Dữ Liệu RawBoost (`src/preprocessing/rawboost.py`)
**Tệp tin:**
- Tạo mới: `src/preprocessing/rawboost.py`
- Kiểm thử: `tests/test_rawboost.py`

### Nhiệm Vụ 3: Mô Phỏng Nén Kênh Thoại & Băng Thông (`src/preprocessing/codec_simulator.py`)
**Tệp tin:**
- Tạo mới: `src/preprocessing/codec_simulator.py`
- Kiểm thử: `tests/test_codec_simulator.py`

### Nhiệm Vụ 4: Lọc Chất Lượng Mẫu Giả Bằng ASR WER (`scripts/filter_asr_wer.py`)
**Tệp tin:**
- Tạo mới: `scripts/filter_asr_wer.py`
- Kiểm thử: `tests/test_filter_asr.py`

### Nhiệm Vụ 5: Kịch Bản Tự Động Sinh Mẫu Giả (`scripts/generate_spoof.py`)
**Tệp tin:**
- Tạo mới: `scripts/generate_spoof.py`

---

## Kế Hoạch Xác Minh (Verification Plan)
- Chạy `pytest tests/ -v`: đạt tối thiểu 10 test cases, 100% passed.
- Commit với tiền tố `[AI]` và xác nhận CI GitHub Actions xanh.
