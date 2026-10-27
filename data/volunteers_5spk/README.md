# Bộ Dữ Liệu 5 Tình Nguyện Viên (Biometric Consent - ViTrueVoice)

## 1. Thông Tin & Mục Đích Sử Dụng
- **Số lượng người nói**: 5 người (`SPK_0001`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`).
- **Pháp lý & Đạo đức sinh trắc học**: Thu thập theo Phiếu đồng ý hợp lệ (Consent Form - Phụ lục C.2), tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP.
- **Vai trò trong đề tài**:
  1. Dùng làm mẫu giọng kiểm thử thực nghiệm Pilot độc lập (Red-Team Evaluation) với CLB An toàn thông tin HUTECH.
  2. Dùng làm bộ mẫu nghe thẩm định tai người (Human Blind Listening Test - 72 lượt đo mốc "Trước").
  3. Đo độ giống giọng cá nhân (Cosine Similarity ECAPA-TDNN) qua 2 engine TTS (F5-TTS và VieNeu-TTS v3 Turbo).
- **Cam kết hủy dữ liệu**: Toàn bộ dữ liệu âm thanh sinh trắc học nguyên bản này được lập lịch hủy vĩnh viễn sau khi bảo vệ đề tài (tháng 12/2026).

## 2. Cấu Trúc Phân Vùng Độc Lập
- `raw/`: Các câu thoại gốc thu âm từ 5 tình nguyện viên (79 câu thoại đã chuẩn hóa 48kHz / 16kHz PCM).
- `bonafide_ref/`: Các clip tham chiếu dải vàng 3.5s - 7.5s được tuyển chọn qua 2 tầng (LOO + Probe).
- `spoof_f5tts/`: 106 mẫu nhân bản sinh từ F5-TTS-Vietnamese.
- `spoof_vieneu/`: 94 mẫu nhân bản sinh từ VieNeu-TTS v3 Turbo.
- `manifests/`: Các tệp manifest 17 cột độc lập cho nhóm tình nguyện viên:
  - `bonafide_manifest.csv`: 79 bản ghi giọng thật.
  - `spoof_manifest.csv`: 200 bản ghi giọng giả.
  - `train.csv`, `dev.csv`, `test_indomain.csv`: Phân chia Speaker-Disjoint (`SPK 1,4,5` train, `SPK 6` dev, `SPK 7` test).
