# -*- coding: utf-8 -*-
"""
Phần Đặc Biệt: Khung Xương Sống Học Thuật Toàn Cục & Bản Chất Cốt Lõi ViTrueVoice
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from .styles import (
    add_heading_part,
    add_heading_section,
    add_heading_subsection,
    add_styled_paragraph,
    add_bullet_item,
    add_callout_box,
    set_cell_background,
    set_cell_margins,
    set_table_borders,
)

def add_global_foundations(doc):
    """Render the comprehensive Global Foundations & Backbone section."""
    add_heading_part(doc, "PHẦN ĐẶC BIỆT: BẢN ĐỒ KIẾN THỨC NỀN TẢNG TOÀN CỤC & KHUNG XƯƠNG SỐNG HỆ THỐNG VITRUEVOICE")

    add_styled_paragraph(doc, 
        "Dành cho người mới bắt đầu tiếp cận đề tài: Trước khi đi sâu vào chi tiết kỹ thuật của từng chương, "
        "phần này đóng vai trò là **kim chỉ nam định hướng học thuật toàn cục**. Nó khẳng định dứt khoát ranh giới bài toán, "
        "bản chất công nghệ và 4 trụ cột kiến trúc xuyên suốt toàn bộ hệ thống ViTrueVoice. "
        "Khi nắm chắc phần này, sinh viên sẽ không bao giờ bị nhầm lẫn khái niệm khi hội đồng đặt các câu hỏi tổng quát.",
        font_size=10.5, italic=True, color_rgb=(60, 60, 60), space_after=8)

    # -------------------------------------------------------------------------
    # G.1 Phân định 3 bài toán giọng nói
    # -------------------------------------------------------------------------
    add_heading_section(doc, "G.1 Bản Chất Trọng Tâm Đề Tài: Phân Định Dứt Khoát 3 Bài Toán Giọng Nói")
    add_styled_paragraph(doc, 
        "Trong lĩnh vực trí tuệ nhân tạo và xử lý tiếng nói (Speech Processing), có ba bài toán hoàn toàn độc lập "
        "về mặt mục tiêu và bản chất toán học nhưng người mới học rất dễ đánh đồng:")

    add_bullet_item(doc, 
        "Mục tiêu là trả lời câu hỏi **'Người nói đang nói câu gì?' (What was said)**. "
        "Đầu vào là sóng âm thanh, đầu ra là văn bản chữ viết (Text). "
        "Thuật toán chỉ quan tâm đến nội dung ngữ nghĩa và âm vị (Phonemes), hoàn toàn bỏ qua việc ai đang nói "
        "hay giọng đó là thật hay giả. Ví dụ: OpenAI Whisper, Google Speech-to-Text.", 
        "1. Bài toán ASR (Automatic Speech Recognition - Nhận dạng nội dung nói)")

    add_bullet_item(doc, 
        "Mục tiêu là trả lời câu hỏi **'Ai đang nói?' (Who said it)**. "
        "Đầu vào là mẫu âm thanh cần kiểm tra và mẫu âm thanh đăng ký (Enrollment) của một người cụ thể. "
        "Hệ thống so khớp khoảng cách vân giọng (Speaker Embedding) để xác nhận danh tính: 'Đây có phải là Anh A hay không?'. "
        "Điểm yếu chết người của ASV truyền thống: **ASV bị lừa 100% nếu kẻ gian dùng AI nhân bản đúng vân giọng của Anh A**, "
        "bởi vì vector đặc trưng của giọng nhân bản sẽ trùng khớp hoàn hảo với vector đăng ký của Anh A! Ví dụ: ECAPA-TDNN, X-vector.",
        "2. Bài toán ASV (Automatic Speaker Verification - Xác thực danh tính người nói)")

    add_bullet_item(doc, 
        "Mục tiêu là trả lời câu hỏi **'Giọng nói này là của con người sinh học tự nhiên hay do máy tính/thuật toán tạo ra?' (Human biological vs Machine synthetic artifact)**. "
        "Hệ thống hoàn toàn **KHÔNG QUAN TÂM** người nói là ai (không cần biết danh tính nạn nhân), "
        "cũng **KHÔNG CẦN QUAN TÂM** họ đang nói câu gì. Nhiệm vụ duy nhất của mô hình là rà soát toàn bộ cấu trúc phổ, "
        "pha dao động và tính liên tục vi mô để phát hiện xem có sự can thiệp của thuật toán trí tuệ nhân tạo "
        "(TTS - Text-to-Speech hoặc VC - Voice Conversion) hay không.",
        "3. Bài toán Anti-Spoofing / Deepfake Detection (Phát hiện tiếng nói giả mạo)")

    add_callout_box(doc,
        "Đề tài **ViTrueVoice tập trung 100% vào Bài toán Anti-Spoofing độc lập (Stand-alone Deepfake Detection)** "
        "trên môi trường kênh thoại viễn thông nén. Hệ thống KHÔNG cần lưu trữ cơ sở dữ liệu vân giọng của từng người dân, "
        "không cần biết người gọi là ai. Bất kỳ ai gửi một đoạn âm thanh đến, hệ thống đều có thể thẩm định ngay lập tức: "
        "đây là giọng con người sinh học hay giọng AI nhân bản lừa đảo.",
        title="KHẲNG ĐỊNH TRỌNG TÂM CỐT LÕI CỦA ĐỀ TÀI TRƯỚC HỘI ĐỒNG")

    # -------------------------------------------------------------------------
    # G.2 Bốn trụ cột công nghệ xuyên suốt
    # -------------------------------------------------------------------------
    add_heading_section(doc, "G.2 Bốn Trụ Cột Công Nghệ Xuyên Suốt (The 4 Foundational Pillars)")
    add_styled_paragraph(doc, 
        "Hệ thống ViTrueVoice được xây dựng dựa trên sự liên kết chặt chẽ của 4 trụ cột công nghệ học thuật, "
        "tạo thành một chu trình khép kín từ xử lý tín hiệu vật lý đến suy luận thống kê:")

    add_bullet_item(doc, 
        "Đảm bảo âm thanh đầu vào đồng nhất tuyệt đối về mặt vật lý (16.000 Hz Mono, RMS P20 silence trimming, "
        "Repeat Padding 64.000 mẫu, EBU R128 -23 LUFS, Z-score). Đặc biệt, tích hợp kỹ thuật **Adaptive Comfort Dithering** "
        "(RFC 3389 / AES-17) để phá vỡ các shortcut toán học giả mạo và bộ mô phỏng suy giảm nén viễn thông (Lossy Codecs).",
        "Trụ cột 1: Xử lý Tín hiệu Âm thanh (Acoustic DSP) & Khử Shortcut")

    add_bullet_item(doc, 
        "Tận dụng mô hình Wav2Vec 2.0 huấn luyện trước trên 250 giờ tiếng Việt (`nguyenvulebinh/wav2vec2-base-vietnamese-250h`). "
        "Backbone này đóng vai trò là 'bộ tai nhân tạo' đã thấu hiểu sâu sắc quy luật thanh điệu (6 thanh tiếng Việt), "
        "ngữ điệu và cấu trúc âm vị bản địa, giúp bóc tách các bất thường vi mô mà mắt thường và mô hình tiếng Anh không thể nhận diện.",
        "Trụ cột 2: Học Biểu diễn Tự Giám sát Tiếng Việt (Vietnamese SSL Backbone)")

    add_bullet_item(doc, 
        "Mô hình Compact AASIST sử dụng đồ thị không đồng nhất HS-GAL (Heterogeneous Spatio-Temporal Graph Attention Layer). "
        "Nó biến các đặc trưng phổ thành các nút thời gian và nút tần số, đồng thời sử dụng một **Nút Chủ Quyền (Master Node)** "
        "làm cầu nối liên miền để phát hiện sự phi lý trong mối liên kết thời gian - tần số do thuật toán AI gây ra.",
        "Trụ cột 3: Mạng Nơ-ron Đồ Thị Không Đồng Nhất (Graph Attention Network Back-end)")

    add_bullet_item(doc, 
        "Giải quyết triệt để tính bất đối xứng âm học bằng giải thuật **Multi-window Sliding Window kết hợp Max-Pooling** "
        "chạy song song mini-batch trên GPU; chuyển đổi điểm số thô thành xác suất có ý nghĩa thực tế bằng mô hình hồi quy "
        "**Platt Scaling** ($k = 0.3569$), kèm guardrail an toàn kẹp xác suất trong khoảng $[0.1\\%, 99.9\\%]$ theo chuẩn NIST Forensics.",
        "Trụ cột 4: Suy Luận Sinh Trắc Học & Hiệu Chuẩn Xác Suất (Inference & Calibration)")

    # -------------------------------------------------------------------------
    # G.3 Tam giác thách thức thực tế
    # -------------------------------------------------------------------------
    add_heading_section(doc, "G.3 Tam Giác Thách Thức Thực Tế Của ViTrueVoice (The Core Trilemma)")
    add_styled_paragraph(doc, 
        "Trong điều kiện lý tưởng (phòng thu âm, định dạng WAV không nén, cùng một công cụ AI quen thuộc), "
        "các mô hình học máy rất dễ đạt độ chính xác > 99%. Tuy nhiên, trong thực tế an ninh phòng chống lừa đảo, "
        "ViTrueVoice phải đối mặt và giải quyết đồng thời **Tam giác Thách thức Cốt lõi (The Core Trilemma)**:")

    add_bullet_item(doc, 
        "Kẻ gian không bao giờ gửi file WAV gốc. Chúng gửi qua tin nhắn Zalo (AAC-LC 76kbps, Opus 24kbps) hoặc gọi qua mạng "
        "di động GSM (AMR-NB 12.2kbps, tần số lấy mẫu bị bóp nghẽn về 8kHz). Các thuật toán nén này đã xóa bỏ hầu hết các méo hài bậc cao.",
        "Cạnh 1: Kênh thoại viễn thông nén mất mát (Lossy Codec Channel)")

    add_bullet_item(doc, 
        "Kẻ gian liên tục cập nhật công nghệ mới (từ Concatenative, FastSpeech2 sang Diffusion và Continuous Flow Matching - CFM). "
        "Mô hình rất dễ bị 'học vẹt' dấu vết của F5-TTS hoặc VieNeu-TTS nhưng lại mù tịt trước công cụ mới như VoiceStudio CFM.",
        "Cạnh 2: Động cơ sinh giọng nói chưa từng thấy (Unseen Zero-Shot CFM Engines)")

    add_bullet_item(doc, 
        "Giọng con người cực kỳ phong phú: có người giọng the thé (Pitch > 300Hz), có người giọng siêu trầm đục (Pitch < 90Hz "
        "như tình nguyện viên SPK_0001), có người bị nghẹt mũi, khàn giọng hoặc nói trong quán cà phê có nhạc nền. "
        "Hệ thống phải phân biệt được đâu là biến thiên sinh học tự nhiên, đâu là giọng máy nhân bản.",
        "Cạnh 3: Đa dạng sinh học và biến thiên âm học người nói (Acoustic Variance)")

    # -------------------------------------------------------------------------
    # G.4 Bảng tra cứu thuật ngữ cốt lõi toàn cục
    # -------------------------------------------------------------------------
    add_heading_section(doc, "G.4 Bảng Tra Cứu Thuật Ngữ Cốt Lõi Toàn Cục (Global Terminology Lexicon)")
    add_styled_paragraph(doc, 
        "Bảng tra cứu nhanh 20 khái niệm và từ viết tắt xuất hiện xuyên suốt toàn bộ tài liệu và mã nguồn dự án:")

    terms_data = [
        ("Bona fide", "Âm thanh giọng nói con người sinh học tự nhiên 100% (không qua can thiệp tổng hợp của máy tính)."),
        ("Spoof", "Âm thanh giả mạo được tạo ra hoặc chỉnh sửa bởi trí tuệ nhân tạo (TTS, Voice Cloning, Voice Conversion)."),
        ("EER (Equal Error Rate)", "Tỷ lệ sai số cân bằng — điểm mà tại đó tỷ lệ bỏ sót spoof bằng đúng tỷ lệ báo nhầm bona fide."),
        ("minDCF (Minimum Detection Cost)", "Chi phí quyết định tối thiểu của chuẩn NIST/ASVspoof, tính đến trọng số thiệt hại thực tế ($C_{\\text{miss}}=1, C_{\\text{fa}}=10$)."),
        ("APCER / FAR", "Tỷ lệ chấp nhận nhầm mẫu giả mạo thành người thật (Bỏ sót deepfake - nguy hiểm tính mạng/tài chính)."),
        ("BPCER / FRR", "Tỷ lệ từ chối nhầm người thật thành giả mạo (Báo động giả gây phiền hà người dùng)."),
        ("WER / CER", "Tỷ lệ lỗi từ (Word Error Rate) và lỗi ký tự (Character Error Rate) dùng để đánh giá chất lượng ASR."),
        ("LUFS", "Đơn vị đo độ to cảm nhận âm thanh chuẩn phát thanh quốc tế (EBU R128). Chuẩn của đề tài là -23 LUFS."),
        ("dBFS", "Decibels Relative to Full Scale — thang đo biên độ năng lượng cực đại trong âm thanh số ($0\\text{ dBFS}$ là cực đại)."),
        ("PCM (Pulse Code Modulation)", "Định dạng âm thanh số hóa dạng sóng thô không nén (Linear PCM 16-bit)."),
        ("STFT / Spectrogram", "Biến đổi Fourier thời gian ngắn và biểu đồ phổ thể hiện năng lượng theo thời gian và tần số."),
        ("F0 (Pitch / Cao độ cơ bản)", "Tần số dao động cơ bản của dây thanh đới người trong quá trình phát âm (Hz)."),
        ("Formants (F1, F2, F3)", "Các tần số cộng hưởng của khoang họng và khoang miệng định hình nên các nguyên âm."),
        ("CFM (Continuous Flow Matching)", "Kiến trúc sinh giọng nói tổng hợp hiện đại nhất hiện nay dựa trên phương trình vi phân và dòng vector (VoiceStudio)."),
        ("Vocoder", "Bộ giải mã chuyển đổi biểu diễn phổ (Mel-spectrogram) thành sóng âm thanh nghe được (ví dụ HiFi-GAN)."),
        ("Lossy Codec", "Thuật toán nén âm thanh có suy hao dữ liệu dựa trên tâm lý âm học (AAC, Opus, AMR-NB, G.711)."),
        ("Platt Scaling", "Mô hình hồi quy Logistic dùng để hiệu chuẩn điểm thô logit thành xác suất thực nghiệm tin cậy."),
        ("RMS P20 Silence Trimming", "Cắt tỉa khoảng lặng thông minh dựa trên ngưỡng năng lượng phân vị thứ 20 thay vì ngưỡng cứng cố định."),
        ("Repeat Padding", "Đệm lặp tuần hoàn mẫu âm thanh ngắn cho đủ 64.000 mẫu để bảo toàn tính liên tục phổ."),
        ("Zero-Persistence", "Nguyên tắc kiến trúc không bao giờ lưu trữ file giọng nói thô lên ổ cứng nhằm bảo vệ quyền riêng tư.")
    ]

    table_terms = doc.add_table(rows=len(terms_data) + 1, cols=2)
    table_terms.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table_terms)

    hdr = table_terms.rows[0]
    c0, c1 = hdr.cells[0], hdr.cells[1]
    c0.width, c1.width = Inches(2.2), Inches(4.7)
    set_cell_background(c0, "1F497D")
    set_cell_background(c1, "1F497D")
    set_cell_margins(c0, 90, 90, 110, 110)
    set_cell_margins(c1, 90, 90, 110, 110)

    p0 = c0.paragraphs[0]; r0 = p0.add_run("Thuật Ngữ / Từ Viết Tắt"); r0.bold = True; r0.font.color.rgb = RGBColor(255, 255, 255); r0.font.name = "Times New Roman"; r0.font.size = Pt(10)
    p1 = c1.paragraphs[0]; r1 = p1.add_run("Định Nghĩa & Ý Nghĩa Học Thuật Trong ViTrueVoice"); r1.bold = True; r1.font.color.rgb = RGBColor(255, 255, 255); r1.font.name = "Times New Roman"; r1.font.size = Pt(10)

    for idx, (term, definition) in enumerate(terms_data):
        row = table_terms.rows[idx + 1]
        rc0, rc1 = row.cells[0], row.cells[1]
        rc0.width, rc1.width = Inches(2.2), Inches(4.7)
        if idx % 2 == 0:
            set_cell_background(rc0, "F9FAFC")
            set_cell_background(rc1, "F9FAFC")
        set_cell_margins(rc0, 60, 60, 100, 100)
        set_cell_margins(rc1, 60, 60, 100, 100)

        rp0 = rc0.paragraphs[0]; rp0.paragraph_format.space_after = Pt(0)
        rr0 = rp0.add_run(term); rr0.bold = True; rr0.font.name = "Times New Roman"; rr0.font.size = Pt(9.5); rr0.font.color.rgb = RGBColor(31, 73, 125)

        rp1 = rc1.paragraphs[0]; rp1.paragraph_format.space_after = Pt(0); rp1.paragraph_format.line_spacing = 1.15
        rr1 = rp1.add_run(definition); rr1.font.name = "Times New Roman"; rr1.font.size = Pt(9.5); rr1.font.color.rgb = RGBColor(30, 30, 30)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)
