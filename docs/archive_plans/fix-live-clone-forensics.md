# Kế Hoạch Khắc Phục Lỗi Live Voice Cloning & Thẩm Định Đối Chứng (fix-live-clone-forensics)

> **Mục tiêu**: Bóc tách nguyên nhân gốc rễ và sửa dứt điểm 2 lỗi:
> 1. Bản clone từ file SPK có sẵn sinh thành công nhưng mô hình nhận nhầm là Bona Fide (sai lệch APCER / False Negative).
> 2. Ghi âm trực tiếp qua Microphone trên Gradio Web thì bản clone sinh ra bị lỗi không nghe thấy gì.
>
> **Tài liệu tham chiếu**: [PLAN.md](PLAN.md), [AGENTS.md](AGENTS.md), [live_cloner.py](file:///c:/Codes/VieTrueVoice/src/vitruevoice/live_cloner.py), [ui.py](file:///c:/Codes/VieTrueVoice/src/app/ui.py).

---

## 1. Bóc Tách Nguyên Nhân Gốc Rễ (Root Cause Analysis - Đã Chứng Minh Thực Nghiệm)

### 🔴 Vấn đề 1: Tại sao Bản Clone VoiceStudio CFM bị nhận nhầm là Bona Fide (+25.9 điểm)?
- **Hiện tượng**: Khi nạp `SPK_0004_01.wav` và chạy clone, Bản 1 (Người Thật) được chấm `+24.7985` (Bona Fide), nhưng Bản 2 (Clone OmniVoice) lại bị chấm `+25.9086` (cũng ra Bona Fide với độ tin cậy 99.9%, gây lỗi bỏ sót APCER).
- **Thực nghiệm bóc tách nguyên nhân**:
  Đã chạy phân tích đối chứng hàm trích xuất cửa sổ trên cùng file clone `SPK_0004_omnivoice_prompt_006.wav` thuộc kho dữ liệu `Voice_Final`:
  - **Khi tắt dither (`apply_dither=False`)**: Score = **-24.3263** $\rightarrow$ **SPOOF CHÍNH XÁC 100%**!
  - **Khi bật dither (`apply_dither=True`)**: Score = **+23.4550** $\rightarrow$ **BỊ ĐẢO CHIỀU SANG BONAFIDE**!
- **Nguyên nhân kỹ thuật**:
  - Trong `src/vitruevoice/live_cloner.py` (hàm `evaluate_audio_sample`), cờ `apply_dither=True` bị gán cứng cho cả 2 mẫu âm thanh.
  - Thuật toán `apply_comfort_dither` bơm nhiễu Gaussian ($\sigma = 0.0035$) vốn chỉ được thiết kế cho audio thu trực tiếp từ WebRTC browser (để bù đắp khoảng lặng zero-floor do tính năng chống ồn của trình duyệt cắt cụt).
  - Khi bơm nhiễu này vào bản clone tổng hợp CFM (Bản 2), nhiễu đã che lấp toàn bộ các vết tích vi mô phổ - thời gian (phase & harmonic artifacts) mà mạng nơ-ron SSL-AASIST dùng để phân biệt spoof, khiến mô hình nhầm lẫn bản clone thành giọng người thật!

---

### 🔴 Vấn đề 2: Tại sao ghi âm trực tiếp qua Mic Web thì bản clone bị mất tiếng (không nghe thấy gì)?
- **Hiện tượng**: Thu âm qua Microphone trên Gradio Web rồi bấm sinh clone thì file âm thanh sinh ra bị im lặng hoặc chỉ có tiếng ù tần số thấp 50Hz.
- **Nguyên nhân kỹ thuật**:
  1. **Lệch tần số lấy mẫu (Sample Rate Mismatch)**:
     - Microphone trình duyệt WebRTC trả về âm thanh ở tần số $f_s = 48.000\text{ Hz}$ (hoặc $44.100\text{ Hz}$).
     - Trong khi đó, pipeline chuẩn của VoiceStudio CFM (`scripts/generate_omnivoice_unseen_spoofs.py`) và bộ trích xuất đặc trưng giọng nói yêu cầu reference audio bắt buộc là **16.000 Hz mono PCM**. Việc lưu thẳng tensor 48kHz vào `tmp_ref_path` khiến bộ trích xuất âm sắc của mô hình CFM bị lệch tần số khung, dẫn đến giải mã âm thanh bị hỏng.
  2. **Khoảng lặng thừa ở đầu và cuối (Leading/Trailing Silence)**:
     - Khi người dùng bấm thu âm, thường có 0.5s – 1.0s khoảng lặng trước khi nói và sau khi dứt câu. Khoảng lặng này làm sai lệch bộ ước lượng thời lượng và ma trận cross-attention giữa văn bản và âm thanh.
  3. **Sai lệch nhận dạng ASR (Phonetic Alignment Mismatch)**:
     - Khi người dùng nói tự do, mô hình ASR Wav2Vec2 có thể nhận diện sai một số âm vị (ví dụ: `ủcuộc gọi này đừ khi âm` thay vì `cuộc gọi này được ghi âm`).
     - Khi `ref_text` và `ref_audio` không khớp chính xác từng âm tiết, trường vận tốc diffusion của Flow Matching không thể hội tụ, làm năng lượng âm thanh bị sụp đổ thành sóng DC offset 50Hz (biên độ cao nhưng không có dải tần tiếng người 300Hz - 4.000Hz).

---

## 2. Giải Pháp Kỹ Thuật (Architecture & Design)

```
[User Mic (48kHz WebRTC)] 
          │
          ▼
[1. Tiền xử lý âm thanh Mic chuẩn Voice_Final]
  ├── Mono conversion
  ├── Resample 48kHz -> 16.000 Hz
  ├── Cắt tỉa khoảng lặng (librosa.effects.trim top_db=25)
  └── Peak Normalization 95%
          │
          ├────────────────────────────────────────┐
          ▼                                        ▼
[Bản 1: Người Thật (Bona Fide)]            [tmp_ref_16k.wav]
  ├── Multi-window Pooling                 ├── Chọn câu chuẩn (Default Prompt) HOẶC ASR
  └── apply_dither=is_webrtc_mic           └── VoiceStudio CFM (num_step=16, guidance=2.0)
          │                                        │
          ▼                                        ▼
   Điểm: +25.5 (THẬT)                      [Bản 2: Clone VoiceStudio CFM (16kHz)]
                                                   │
                                                   ├── Multi-window Pooling
                                                   └── apply_dither=False (BẮT BUỘC KHÔNG DITHER)
                                                           │
                                                           ▼
                                                    Điểm: -24.3 (GIẢ MẠO - CHÍNH XÁC)
```

---

## 3. Danh Sách Nhiệm Vụ Triển Khai (Task Breakdown)

### Phase 1: Viết Unit Test TDD (Kiểm Thử Trước Khi Sửa Code)
- [ ] **Task 1.1**: Bổ sung unit test trong `tests/test_live_cloner.py` kiểm tra cờ `apply_dither`:
  - Kiểm tra `evaluate_audio_sample` với `apply_dither=False` trên mẫu spoof OmniVoice phải cho điểm âm ($\le -10.0$).
  - Kiểm tra `evaluate_audio_sample` trên Bona Fide mẫu thật vẫn cho điểm dương ($\ge +15.0$).
- [ ] **Task 1.2**: Bổ sung unit test kiểm tra luồng chuẩn hóa mic audio 48kHz:
  - Giả lập đầu vào numpy 48.000 Hz có khoảng lặng, kiểm tra đầu ra ref_audio được chuyển đổi thành đúng 16.000 Hz mono sạch.

### Phase 2: Sửa Lỗi Detector & Cơ Chế Dither (`src/vitruevoice/live_cloner.py`)
- [ ] **Task 2.1**: Cập nhật hàm `evaluate_audio_sample`:
  - Thêm tham số `apply_dither: bool = False`.
  - Chỉ áp dụng dither khi tham số này là `True`.
- [ ] **Task 2.2**: Cập nhật hàm `stream_cloning_and_detection`:
  - **Bản 1 (User Audio)**: Truyền `apply_dither=is_live_mic` (chỉ kích hoạt dither khi nhận diện âm thanh thu từ WebRTC mic trình duyệt bị noise-gate).
  - **Bản 2 (VoiceStudio CFM Clone)**: Cố định **`apply_dither=False`** (tuyệt đối không bơm dither vào âm thanh sinh nhân tạo).

### Phase 3: Sửa Lỗi Bộ Nạp Âm Thanh Thu Âm Mic & Tối Ưu Hóa VoiceStudio CFM
- [ ] **Task 3.1**: Chuẩn hóa âm thanh microphone trước khi cấp cho VoiceStudio CFM:
  - Nếu $f_s \neq 16.000\text{ Hz}$, thực hiện resample về đúng 16.000 Hz.
  - Sử dụng `librosa.effects.trim(data, top_db=25)` để loại bỏ khoảng lặng thừa đầu/cuối của bản ghi âm mic.
  - Lưu file tạm chuẩn 16.000 Hz mono PCM_16 (`tmp_ref_16k.wav`) làm reference cho OmniVoice.
- [ ] **Task 3.2**: Khóa cơ chế văn bản tham chiếu thông minh:
  - Mặc định ưu tiên câu mẫu chuẩn: `"Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."` khi người dùng đọc theo hướng dẫn (tránh triệt để lỗi ASR hallucination).
  - Chỉ chạy ASR khi phát hiện nội dung đọc khác biệt hoàn toàn hoặc người dùng chọn chế độ đọc tự do.

### Phase 4: Cải Tiến Giao Diện & Trải Nghiệm Người Dùng (`src/app/ui.py`)
- [ ] **Task 4.1**: Cập nhật Tab 2 UI:
  - Thêm tùy chọn rõ ràng cho người dùng:
    - Chế độ 1 (Khuyên dùng): Đọc theo câu chuẩn (đảm bảo chất lượng clone to rõ 100%).
    - Chế độ 2: Đọc tự do (chạy ASR nhận diện văn bản).
  - Kết nối tham số `is_live_mic` chính xác từ UI xuống backend.
- [ ] **Task 4.2**: Cập nhật Bảng Đối Soát Ma Trận:
  - Khi Bản 2 ra điểm âm (Spoof), hiển thị nhãn xanh **CHÍNH XÁC** (Phát hiện thành công Deepfake).

### Phase X: Xác Minh Nghiệm Thu & Kiểm Thử Toàn Diện
- [ ] **Task 5.1**: Chạy toàn bộ test suite `pytest tests/ -v` (309/309 tests pass 100%).
- [ ] **Task 5.2**: Chạy kiểm thử tự động trên Gradio Web UI (`http://localhost:7860`):
  - **Test Case 1 (Preset SPK_0004)**: Bản 1 ra Người Thật (+25.5, CHÍNH XÁC), Bản 2 ra Giả Mạo (-24.3, CHÍNH XÁC).
  - **Test Case 2 (Thu âm trực tiếp Microphone)**: Thu âm giọng nói, sinh bản clone to rõ, nghe thấy tiếng chuẩn và kiểm định thật giả chính xác.
- [ ] **Task 5.3**: Đồng bộ cập nhật tài liệu kỹ thuật (`PLAN.md`, `README.md`, `howtorun.md`, `AGENTS.md`) và commit git với tiền tố `[AI]`.

---

## 4. Phân Công Trách Nhiệm (Agent Assignments)

| Thành phần | Agent đảm trách | Kỹ năng áp dụng |
| :--- | :--- | :--- |
| Thiết kế kế hoạch & Điều phối | `project-planner` | `plan-writing`, `clean-code` |
| Sửa thuật toán dither & tiền xử lý âm thanh | `backend-specialist` | `python-patterns`, `clean-code` |
| Tinh chỉnh giao diện Web UI & tương tác Gradio | `frontend-specialist` | `clean-code` |
| Viết unit tests TDD & chạy thực nghiệm xác minh | `test-engineer` | `tdd-workflow`, `verify-changes` |
