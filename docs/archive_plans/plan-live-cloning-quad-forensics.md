# Kế Hoạch Kỹ Thuật: Tính Năng Live Voice Cloning & Thẩm Định Đối Chứng 4 Chiều (Quad-Forensics) Trên Gradio Web

> **Mã kế hoạch**: `plan-live-cloning-quad-forensics`  
> **Phiên bản mục tiêu**: ViTrueVoice v0.5.0  
> **Trạng thái**: Đang chờ người dùng phê duyệt (Phase 1: Planning Approval Gate)  
> **Tiêu chuẩn thực thi**: Zero-Persistence (Luật 91/2025/QH15), NFR1 Latency Stream, Progressive Yielding Gradio

---

## 1. Mục Tiêu & Trải Nghiệm Người Dùng (UX Flow)

### 1.1 Vấn đề thực tế khi demo trước Hội đồng
Hiện tại, hệ thống Web UI hỗ trợ:
1. Thu âm trực tiếp giọng nói từ Microphone trình duyệt.
2. Kiểm tra mẫu và trả về kết quả thẩm định Thật/Giả (Bona Fide / Spoof).

Tuy nhiên, khi bảo vệ trước Hội đồng, việc **chỉ phân tích 1 mẫu đơn lẻ** chưa tạo ra hiệu ứng trực quan thuyết phục tuyệt đối. Hội đồng muốn thấy:
- **Người dùng thu âm trực tiếp giọng nói qua micro**.
- Hệ thống **lấy chính giọng nói vừa thu** làm giọng mẫu tham chiếu (Voice Prompt / Reference Audio).
- Hệ thống **tự động nhân bản (clone) giọng nói đó qua 3 mô hình TTS Zero-Shot khác nhau** của dự án để nói một câu thoại ngắn (~10 từ thuần Việt).
- Sau đó, hệ thống thẩm định cả 4 bản âm thanh và xếp cạnh nhau trên màn hình:
  - **Bản 1**: Giọng người thật vừa thu $\rightarrow$ ViTrueVoice kết luận **NGƯỜI THẬT (Bona Fide, ~99.6%)**.
  - **Bản 2**: Giọng clone F5-TTS (Flow Matching) $\rightarrow$ ViTrueVoice phát hiện **GIẢ MẠO (Spoof, ~99.9%)**.
  - **Bản 3**: Giọng clone VieNeu-TTS v3 Turbo (Neural Vocoder) $\rightarrow$ ViTrueVoice phát hiện **GIẢ MẠO (Spoof, ~99.9%)**.
  - **Bản 4**: Giọng clone VoiceStudio OmniVoice (Continuous Flow Matching) $\rightarrow$ ViTrueVoice phát hiện **GIẢ MẠO (Spoof, ~99.9%)**.

### 1.2 Ràng Buộc Kỹ Thuật Theo Chỉ Đạo Của Người Dùng (User Directives)
1. **Phạm vi áp dụng (Conditional Trigger)**:
   - **Chỉ kích hoạt tự động sinh 3 bản clone khi người dùng thu âm trực tiếp từ Microphone**.
   - **Khi người dùng tải file lên (Upload)**: Giữ nguyên chế độ thẩm định đơn bản thông thường (~66ms), tuyệt đối không tự động sinh 3 bản clone để tránh lãng phí tài nguyên và độ trễ.
2. **Câu thoại mục tiêu cố định (Fixed Target Prompt)**:
   - Câu thoại ngắn gọn, đúng 10 từ, thuần Việt tự nhiên:
     `"Alo bạn ơi, tôi đang bận một chút tôi gọi lại."` (hoặc `"Alo mẹ à, chút nữa con gọi lại cho mẹ nhé."`).
   - Không cần ô nhập văn bản tùy chọn (Custom Text Input) nhằm giữ giao diện tối giản, trực quan và không gây rối cho người dùng lớn tuổi / hội đồng.
3. **Chiến lược điều phối tài nguyên VRAM (VRAM Priority & Fallback)**:
   - Ưu tiên tối đa cho mô hình **VoiceStudio CFM** (mô hình Zero-shot cốt lõi kiểm chứng H2).
   - Nếu môi trường chạy bị hạn chế VRAM không đủ nạp đồng thời, hệ thống chủ động giải phóng bộ nhớ của F5-TTS và VieNeu-TTS để dồn toàn bộ GPU cho VoiceStudio CFM, hoặc linh hoạt điều phối tuần tự (Sequential loading + `torch.cuda.empty_cache()`).

### 1.3 Yêu cầu Progressive Streaming (Không để người dùng chờ đợi)
- Quy trình sinh giọng qua 3 mô hình TTS mất vài giây cho mỗi engine.
- **Yêu cầu bắt buộc**: Áp dụng cơ chế **Gradio Generator `yield`**:
  - **Ngay lập tức (~66ms)**: Phân tích xong bản thu người thật $\rightarrow$ Hiển thị ngay thẻ kết quả Bona Fide + biểu đồ của người dùng. Ba ô clone bên dưới hiển thị hiệu ứng chuyển động **Loading / Shimmer Skeleton** ("Đang kết nối F5-TTS...", "Đang kết nối VieNeu-TTS...", "Đang kết nối VoiceStudio CFM...").
  - **Sau ~3-4 giây**: F5-TTS hoàn tất clone $\rightarrow$ Chạy detector ViTrueVoice $\rightarrow$ Cập nhật ô F5-TTS (Audio Player + Phán quyết Spoof + Độ tin cậy + Biểu đồ sóng), 2 ô còn lại vẫn tiếp tục Loading.
  - **Sau ~6-8 giây**: VieNeu-TTS hoàn tất clone $\rightarrow$ Cập nhật ô VieNeu-TTS.
  - **Sau ~10-12 giây**: VoiceStudio CFM hoàn tất clone $\rightarrow$ Cập nhật ô VoiceStudio CFM + Hiển thị Bảng tổng kết đối chứng 4 chiều (Quad Matrix).

---

## 2. Ba Mô Hình TTS Zero-Shot Của Dự Án

| # | Tên Mô Hình | Kiến Trúc Cốt Lõi | Tần Số | Vị Trí Trong Dự Án | Vai Trò Trong Kịch Bản Clone |
|---|---|---|---|---|---|
| **1** | **F5-TTS-Vietnamese** | Diffusion Transformer + Flow Matching + Vocos | 24 kHz | `src/vitruevoice/adapters/f5_adapter.py` | Đại diện cho công cụ Seen TTS #1 (tập Train/Dev) |
| **2** | **VieNeu-TTS v3 Turbo** | Qwen LLM + MOSS Acoustic Vocoder | 48 kHz | `src/vitruevoice/adapters/vieneu_adapter.py` | Đại diện cho công cụ Seen TTS #2 (tập Train/Dev) |
| **3** | **VoiceStudio OmniVoice CFM** | Continuous Flow Matching (CFM) + bfloat16 | 24 kHz | `external/VoiceStudio/` & `scripts/generate_omnivoice_unseen_spoofs.py` | Đại diện cho công cụ **Unseen Zero-Shot TTS** (Kiểm chứng Giả thuyết H2) |

*(Dự phòng: Nếu môi trường chạy không đủ GPU nạp VoiceStudio CFM, tự động fallback sang `Kokoro-Vietnamese` tại `external/Kokoro-Vietnamese/` hoặc `Suno-Bark` tại `src/vitruevoice/adapters/bark_adapter.py`).*

---

## 3. Kiến Trúc Kỹ Thuật (Architecture & Implementation)

### 3.1 Luồng Dữ Liệu In-Memory Stream (Zero-Persistence)
```
[User Mic / Upload] 
         │ (audio float32, 16kHz)
         ▼
[1. ViTrueVoice Detector] ──(~66ms)──► YIELD 1: Bản 1 Bona Fide READY (3 ô clone LOADING)
         │
         ├─────────────────────────────────────────┐
         ▼                                         │
[2. F5-TTS Cloner] (target text)                   │
         │ (wav float32, 24kHz)                    │
         ▼                                         │
[ViTrueVoice Detector] ──────────────► YIELD 2: Bản 2 Spoof READY (F5-TTS)
         │                                         │
         ▼                                         │
[3. VieNeu-TTS Cloner] (target text)               │
         │ (wav float32, 48kHz)                    │
         ▼                                         │
[ViTrueVoice Detector] ──────────────► YIELD 3: Bản 3 Spoof READY (VieNeu-TTS)
         │                                         │
         ▼                                         │
[4. VoiceStudio CFM Cloner] (target text)          │
         │ (wav float32, 24kHz)                    │
         ▼                                         │
[ViTrueVoice Detector] ──────────────► YIELD 4: Bản 4 Spoof READY (OmniVoice)
                                       + BẢNG ĐỐI CHỨNG TỔNG HỢP (Quad Matrix)
```

### 3.2 Câu Thoại Mục Tiêu (Target Text Prompt)
Giao diện cung cấp:
- **Câu mặc định (Kịch bản lừa đảo chuyển tiền khẩn cấp)**:
  `"Alo mẹ à, con đang có việc gấp cần tiền gấp, mẹ chuyển ngay mười triệu đồng vào số tài khoản này cho con nhé!"`
- **Ô nhập tùy chọn (Custom Text Input)**: Cho phép người dùng hoặc Thầy/Cô hội đồng tự gõ câu bất kỳ để thử thách khả năng đọc tiếng Việt có dấu của 3 mô hình.

### 3.3 Quản Lý Bộ Nhớ VRAM (Tránh OOM Trên GPU 4GB)
- Trên GPU RTX 3050 (4GB VRAM):
  - ViTrueVoice Detector chiếm: ~300 MB VRAM.
  - Các mô hình TTS sẽ được nạp tuần tự (Lazy loading), sinh xong mẫu âm thanh sẽ giải phóng cache (`torch.cuda.empty_cache()`) trước khi nạp mô hình tiếp theo.
  - Đảm bảo đỉnh VRAM luôn $< 3.2\text{ GB}$, không gây xung đột hay sập máy chủ.

### 3.4 Thiết Kế Giao Diện Forensics Quad-Card (Stitch Theme)
Giao diện phân bổ 4 Thẻ Phán Quyết trực quan:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎙️ BẢN 1: GIỌNG NÓI THẬT CỦA BẠN (BONA FIDE GỐC)                            │
│ 🛡️ XÁC THỰC: NGƯỜI THẬT (BONA FIDE) ── Độ tin cậy: 99.6% (Platt Scaling)    │
│ Điểm số: +18.42 | Thời gian phân tích: 66.3ms | Mã SHA-256: e8a91c...       │
│ [► Play Audio] [Waveform & Spectrogram thu gọn]                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┬────────────────────────────────────────┐
│ 🔴 BẢN 2: CLONE QUA F5-TTS        │ 🟠 BẢN 3: CLONE QUA VIENEU-TTS         │
│ 🚨 CẢNH BÁO: SPOOF DEEPFAKE       │ 🚨 CẢNH BÁO: SPOOF DEEPFAKE            │
│ Độ tin cậy: 99.9% (Score: -38.2)  │ Độ tin cậy: 99.9% (Score: -24.6)       │
│ [► Play Audio Clone 1]            │ [► Play Audio Clone 2]                 │
├───────────────────────────────────┼────────────────────────────────────────┤
│ 🟣 BẢN 4: CLONE QUA VOICESTUDIO   │ 📊 BẢNG TỔNG KẾT ĐỐI CHỨNG QUAD MATRIX │
│ 🚨 CẢNH BÁO: SPOOF DEEPFAKE       │ Bona Fide: +18.42 (PASS NGƯỜI THẬT)    │
│ Độ tin cậy: 99.8% (Score: -20.1)  │ 3/3 Mẫu Clone: BẮT TRỌN 100% DEEPFAKE  │
│ [► Play Audio Clone 3]            │ Khoảng cách an toàn (Margin): 42.8 pts │
└───────────────────────────────────┴────────────────────────────────────────┘
```

---

## 4. Các Tệp Tin Mã Nguồn Sẽ Được Cập Nhật / Tạo Mới

1. `src/vitruevoice/live_cloner.py` (Mới): Module quản lý việc sinh giọng nối tiếp từ 3 engine TTS với bộ nhớ đệm an toàn và quản lý ngoại lệ.
2. `src/app/ui.py` (Cập nhật): 
   - Tích hợp Tab / Khối giao diện `Tab 2: Phòng Lab Thử Thách Clone Giọng Trực Tiếp (Live Voice Cloning & Quad Stress-Test)`.
   - Viết hàm generator `stream_live_cloning_forensics` hỗ trợ 4 lượt `yield`.
   - Bổ sung CSS Animation cho trạng thái Loading Skeleton.
3. `tests/test_live_cloner.py` (Mới - TDD): Bộ unit test kiểm thử:
   - Kiểm thử logic generator yield 4 bước.
   - Kiểm thử fallback khi một engine TTS bị thiếu hoặc lỗi mạng.
   - Kiểm thử tính toàn vẹn của kết quả thẩm định Thật/Giả.

---

## 5. Kế Hoạch Phân Công Đa Agent (Stric 2-Phase Orchestration)

Theo quy định `/orchestrate`, tối thiểu 3 agent chuyên trách sẽ thực thi tuần tự và song song:

| # | Agent | Vai Trò & Trách Nhiệm Cụ Thể |
|---|---|---|
| 1 | `project-planner` (Hiện tại) | Lập kế hoạch kiến trúc chi tiết, xác định interface, cơ chế streaming yield và các ràng buộc bộ nhớ. |
| 2 | `backend-specialist` | Xây dựng module `src/vitruevoice/live_cloner.py` kết nối 3 engine TTS (F5, VieNeu, OmniVoice) và tích hợp pipeline suy luận in-memory. |
| 3 | `frontend-specialist` | Thiết kế giao diện Quad-Forensics trên Gradio trong `src/app/ui.py` với hiệu ứng Loading mượt mà và hiển thị tuần tự. |
| 4 | `test-engineer` | Viết bộ kiểm thử TDD `tests/test_live_cloner.py`, đảm bảo toàn bộ 301+ bài test pass 100% trước khi hoàn tất. |

---

## 6. Tiêu Chí Nghiệm Thu (Acceptance Criteria)

- [ ] Thu âm giọng nói của người dùng trực tiếp trên Gradio Web.
- [ ] Bấm nút "Kiểm định & Sinh 3 bản Clone Đối chứng" (hoặc tự động chạy).
- [ ] Bản 1 (Bona Fide) hiện ngay lập tức trong vòng $< 1.0$ giây, trong khi 3 ô clone hiển thị loading.
- [ ] Bản 2, 3, 4 lần lượt xuất hiện ngay khi từng engine sinh xong (progressive streaming yield).
- [ ] Người dùng có thể bấm nghe thử (Play Audio) cả 4 đoạn âm thanh để đối chứng bằng tai.
- [ ] Kết quả thẩm định chính xác: Bản người thật đạt Bona Fide ($s > 0$), cả 3 bản clone bị bắt trọn là Spoof ($s < 0$).
- [ ] Không làm phá vỡ các chức năng cũ của Web UI; toàn bộ test suite tiếp tục pass 100%.
