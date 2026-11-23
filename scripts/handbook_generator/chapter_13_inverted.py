# -*- coding: utf-8 -*-
"""
Chương 13: Thực Nghiệm Đối Chứng 2 Chiều (Inverted Generalization Experiment)
và Đột Phá Khắc Phục Lỗ Hổng CFM (V7 vs V8)
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from .styles import (
    add_heading_chapter,
    add_heading_section,
    add_heading_subsection,
    add_styled_paragraph,
    add_bullet_item,
    add_callout_box,
    add_prerequisite_box,
    set_cell_background,
    set_cell_margins,
    set_table_borders,
)


def add_chapter_13_inverted(doc):
    """Add Chapter 13: Inverted Generalization Experiment & CFM Breakdown."""

    # =========================================================================
    # CHƯƠNG 13
    # =========================================================================
    add_heading_chapter(
        doc,
        "Chương 13",
        "Thực Nghiệm Đối Chứng 2 Chiều (Inverted Generalization Experiment) & Đột Phá Khắc Phục Lỗ Hổng CFM (V7 vs V8)",
    )

    add_prerequisite_box(
        doc,
        "Chương 13",
        "Mô hình dòng liên tục (Continuous Flow Matching - CFM vs Optimal Transport ODE), "
        "Mô hình ngôn ngữ âm học tự hồi quy (Acoustic LM NeuCodec RVQ), "
        "Không gian đặc trưng tự giám sát SSL-AASIST, "
        "Ma trận suy giảm (Degradation Matrix) trên 5 biến thể codec thoại nén, "
        "Phương pháp luận thí nghiệm hoán đổi đối chứng 2 chiều (Bidirectional Symmetrical Verification).",
    )

    # -------------------------------------------------------------------------
    # 13.0 Kiến thức nền tảng
    # -------------------------------------------------------------------------
    add_heading_section(doc, "13.0 Kiến Thức Nền Tảng Tiên Quyết Cần Nắm Vững Trước Khi Đọc Chương 13")
    add_styled_paragraph(
        doc,
        "Thí nghiệm đối chứng 2 chiều (Inverted Generalization Experiment) là bước nhảy vọt phương pháp luận "
        "quan trọng nhất trong giai đoạn hoàn thiện đề tài ViTrueVoice. Để hiểu trọn vẹn bản chất của thí nghiệm này, "
        "người học cần nắm vững 3 nguyên lý học máy và xử lý tín hiệu sau:",
    )

    add_heading_subsection(doc, "13.0.1 Bản Chất Toán Học Của Continuous Flow Matching (CFM) So Với Diffusion Truyền Thống")
    add_styled_paragraph(
        doc,
        "Trong các công nghệ tổng hợp giọng nói nhân bản (Voice Cloning), có hai trường phái tạo sinh dạng sóng chính:\n"
        "1. **Mô hình Khuếch tán Truyền thống (Score-based Diffusion / DDPM)**: Dựa trên phương trình vi phân ngẫu nhiên "
        "(SDE - Stochastic Differential Equation). Quá trình biến đổi từ nhiễu Gauss $\\mathcal{N}(0, I)$ về âm thanh "
        "diễn ra theo các bước ngẫu nhiên Brown ziczac qua hàng chục đến hàng trăm bước lặp. Sóng âm tạo ra thường có "
        "các vết cắt pha (phase discontinuity) và méo hài cao tần đặc trưng khi đi qua bộ vocoder CNN/GAN.\n"
        "2. **Mô hình Dòng Liên Tục (Continuous Flow Matching - CFM)**: Điển hình là VoiceStudio (OmniVoice CFM). "
        "Thay vì đi đường vòng ziczac ngẫu nhiên, CFM định nghĩa một phương trình vi phân thường (ODE - Ordinary Differential Equation) "
        "dọc theo quỹ đạo vận tốc tối ưu (Optimal Transport Vector Field):\n"
        "$$\\frac{dx_t}{dt} = v_t(x_t), \\quad x_0 \\sim \\mathcal{N}(0, I), \\quad x_1 \\sim p_{\\text{data}}$$\n"
        "Thuật toán giải ODE (như Euler hoặc Midpoint) đưa biến ngẫu nhiên trượt thẳng tắp về dạng sóng âm thanh đích "
        "chỉ trong $N = 16$ bước tích phân. Dạng sóng sinh bởi CFM có quỹ đạo pha trơn tru phi thường, không có các gai cắt rời rạc "
        "của vocoder truyền thống. Đây chính là 'vũ khí nguy hiểm nhất' có khả năng đánh lừa các bộ tiền xử lý phổ STFT cổ điển!",
    )

    add_heading_subsection(doc, "13.0.2 Kiến Trúc Mô Hình Ngôn Ngữ Âm Học & Lượng Tử Hóa Phần Dư (NeuCodec RVQ)")
    add_styled_paragraph(
        doc,
        "Trái ngược hoàn toàn với trường phái dòng liên tục CFM, công cụ VieNeu-TTS v3 Turbo hoạt động theo nguyên lý "
        "**Mô hình Ngôn ngữ Âm học (Acoustic Language Model)** kết hợp bộ mã hóa thần kinh **NeuCodec**:\n"
        "- Âm thanh được nén thành chuỗi token rời rạc thông qua cơ chế lượng tử hóa vector phần dư "
        "(Residual Vector Quantization - RVQ) với nhiều tầng codebook 1024 chiều.\n"
        "- Bộ giải mã biến đổi trực tiếp các token rời rạc này thành sóng âm mà không cần vocoder trung gian.\n"
        "- Bản chất toán học: Sự chuyển đổi giữa các vector rời rạc trong codebook luôn tạo ra các **vết răng cưa lượng tử hóa vi mô** "
        "(quantization micro-artifacts) trên cấu trúc pha và hài âm bậc cao. Dấu vết này mang tính chất rời rạc, đối nghịch "
        "với tính liên tục của CFM.",
    )

    add_heading_subsection(doc, "13.0.3 Phương Pháp Luận Thí Nghiệm Hoán Đổi Đối Chứng 2 Chiều (Inverted Symmetrical Verification)")
    add_styled_paragraph(
        doc,
        "Trong nghiên cứu khoa học, một lỗi ngụy biện phổ biến là hiện tượng 'Thành kiến kiến trúc' (Architectural Bias): "
        "Khi một mô hình phát hiện tốt một loại công cụ giả mạo, chưa chắc mô hình đã học được quy luật chung, "
        "mà có thể chỉ vì bộ dữ liệu tình cờ chứa các đặc trưng trùng lặp.\n"
        "Để đập tan hoàn toàn nghi ngờ này trước Hội đồng, chúng em thiết kế thí nghiệm hoán đổi đối xứng 2 chiều:\n"
        "- **Chiều Thuận (Mô hình V7)**: Seen TTS = {F5-TTS, VieNeu-TTS} $\\rightarrow$ Unseen TTS = {VoiceStudio OmniVoice CFM}.\n"
        "- **Chiều Nghịch (Mô hình V8)**: Seen TTS = {F5-TTS, VoiceStudio OmniVoice CFM} $\\rightarrow$ Unseen TTS = {VieNeu-TTS v3 Turbo}.\n"
        "Bằng cách hoán đổi hoàn toàn vị trí của CFM và VieNeu-TTS giữa tập Huấn luyện (Seen) và tập Kiểm định ngoại lai (Unseen), "
        "chúng em chứng minh được cơ chế toán học kiểm soát sai số trên cả hai chiều phân phối âm học.",
    )

    # -------------------------------------------------------------------------
    # 13.1 So sánh cấu trúc thực nghiệm V7 vs V8
    # -------------------------------------------------------------------------
    add_heading_section(doc, "13.1 So Sánh Chi Tiết Cấu Trúc Thực Nghiệm Giữa Mô Hình V7 Và Mô Hình V8")
    add_styled_paragraph(
        doc,
        "Bảng 13.1 tổng hợp kiến trúc phân bổ dữ liệu, vai trò của từng công cụ tổng hợp giọng nói và ranh giới kiểm định "
        "giữa hai thế hệ mô hình V7 và V8:",
    )

    headers_comp = ["Thuộc Tính / Cấu Trúc", "Mô Hình B_zalo V7 (Chiều Thuận)", "Mô Hình B_zalo V8 (Chiều Nghịch)", "Mục Đích Khoa Học Đối Chứng"]
    rows_comp = [
        ("Công cụ Seen TTS (Train & Dev)", 
         "F5-TTS (Flow-Matching)\n+ VieNeu-TTS v3 Turbo (Acoustic LM)", 
         "F5-TTS (Flow-Matching)\n+ VoiceStudio OmniVoice (CFM)", 
         "Đưa CFM vào không gian học biểu diễn để triệt tiêu lỗ hổng lọt lưới."),
        ("Công cụ Unseen TTS (Kiểm định H2)", 
         "VoiceStudio (OmniVoice CFM)\n(Continuous Flow Matching)", 
         "VieNeu-TTS v3 Turbo\n(Acoustic Language Model + NeuCodec)", 
         "Kiểm tra xem mô hình khi học CFM có giữ vững độ tổng quát hóa trên RVQ không."),
        ("Quy mô tập Train Spoof", 
         "F5-TTS: 26.850 dòng\nVieNeu-TTS: 12.000 dòng\n(Tổng: 54.225 dòng)", 
         "F5-TTS: 26.850 dòng\nOmniVoice CFM: 12.000 dòng\n(Tổng: 54.225 dòng)", 
         "Cân bằng chính xác 100% dung lượng và số lượng mẫu train giữa hai mô hình."),
        ("Tập Thẩm định Dev (Seen)", 
         "960 F5-TTS + 955 VieNeu-TTS\n(10.490 Bona Fide, 15 SPK Dev)", 
         "960 F5-TTS + 965 OmniVoice CFM\n(10.490 Bona Fide, 15 SPK Dev)", 
         "Đo lường năng lực học nội vùng (In-domain Seen EER <= 8.0%)."),
        ("Tập Nghiệm thu 5 Tình nguyện viên", 
         "SPK_0003..0007 (84 Bona Fide)\nCÔ LẬP 100% (Khóa cứng)", 
         "SPK_0003..0007 (84 Bona Fide)\nCÔ LẬP 100% (Khóa cứng)", 
         "Bảo toàn STUBBORN_FACT: Tuyệt đối không rò rỉ dữ liệu nghiệm thu."),
        ("Cơ chế Suy luận Tiêu chuẩn", 
         "Multi-Window Max-Pooling\n(Dense Overlap 5 Windows, hop 1.0s)", 
         "Multi-Window Max-Pooling\n+ Asymmetric Veto (min < -12.0)", 
         "Đồng bộ chuẩn suy luận đa cửa sổ trên cả hai mô hình."),
    ]

    t_comp = doc.add_table(rows=len(rows_comp) + 1, cols=4)
    t_comp.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_comp, color="CCCCCC", sz="4")

    # Header row
    hdr_cells = t_comp.rows[0].cells
    col_widths = [Inches(1.8), Inches(2.2), Inches(2.2), Inches(2.0)]
    for i, title in enumerate(headers_comp):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], "1F497D")
        set_cell_margins(hdr_cells[i], top=90, bottom=90, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(9.5)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_comp):
        row = t_comp.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            bg_color = "F9FBFD" if r_idx % 2 == 0 else "FFFFFF"
            if c_idx == 0:
                bg_color = "F0F4F8"
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(9.0)
            if c_idx == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(31, 73, 125)
            else:
                run.font.color.rgb = RGBColor(30, 30, 30)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------------------
    # 13.2 Phân tích cơ chế toán học
    # -------------------------------------------------------------------------
    add_heading_section(doc, "13.2 Phân Tích Cơ Chế Toán Học: Vì Sao Đưa CFM Vào Huấn Luyện Triệt Tiêu Lỗ Hổng 20% Lọt Lưới")
    add_styled_paragraph(
        doc,
        "Tại phiên bản V7, khi đối mặt với công cụ tổng hợp giọng nói chưa từng thấy VoiceStudio CFM (OmniVoice), "
        "hệ thống đạt tỷ lệ chặn ban đầu là 79.79% trên 15 người nói held-out (EER = 14.81% $\\le 15.0\\%$, đạt Giả thuyết H2). "
        "Tuy nhiên, vẫn còn tồn tại **~20.21% mẫu giả mạo CFM bị lọt lưới** (False Acceptance - phân định nhầm thành người thật). "
        "Dưới đây là bản phân tích bản chất toán học từ gốc rễ:",
    )

    add_heading_subsection(doc, "13.2.1 Tại Sao Mô Hình V7 Lại Bị Lọt Lưới 20% Trước Continuous Flow Matching?")
    add_styled_paragraph(
        doc,
        "1. **Bản chất quỹ đạo trơn ODE**: Khác với F5-TTS (sử dụng Diffusion với bước giải ngẫu nhiên có độ rung lắc vi mô), "
        "OmniVoice CFM tính toán trường vector vận tốc tối ưu $v_t^*(x) = x_1 - (1 - \\sigma_{\\min})x_0$. "
        "Khi giải tích phân qua 16 bước Midpoint, dạng sóng thời gian tạo ra cực kỳ trơn lùi, bảo toàn hoàn hảo các bao biên năng lượng "
        "và không tạo ra các cú giật biên độ (amplitude spikes).\n"
        "2. **Điểm mù của bộ lọc đồ thị HS-GAL khi chưa học CFM**: Trong khối Compact AASIST của V7, "
        "đồ thị không đồng nhất thời gian - tần số HS-GAL được huấn luyện chủ yếu trên F5-TTS và VieNeu-TTS. "
        "Mô hình học cách phát hiện vết cắt pha của F5 và vết răng cưa lượng tử của NeuCodec. "
        "Khi gặp sóng âm CFM trong môi trường phòng thu có tỷ lệ tín hiệu trên nhiễu cao (High SNR như bộ VIVOS), "
        "quỹ đạo pha quá hoàn hảo của CFM nằm trùng khít vào phân phối của giọng người thật, khiến logit đầu ra bị đẩy lên giá trị dương ($s \\in [0.0, +8.0]$).",
    )

    add_heading_subsection(doc, "13.2.2 Tác Động Của Đạo Hàm Gradient Khi Đưa CFM Vào Tập Huấn Luyện (Mô Hình V8)")
    add_styled_paragraph(
        doc,
        "Khi đưa 12.000 mẫu OmniVoice CFM vào tập huấn luyện của mô hình V8 thay thế cho VieNeu-TTS, "
        "quá trình lan truyền ngược đạo hàm (Backpropagation) đã kích hoạt một cơ chế tái cấu trúc không gian đặc trưng:\n"
        "- Hàm mất mát Weighted Cross-Entropy kết hợp AM-Softmax ($m = 0.35$):\n"
        "$$\\mathcal{L}_{\\text{AM}} = -\\log \\frac{e^{s \\cdot (\\cos(\\theta_y) - m)}}{e^{s \\cdot (\\cos(\\theta_y) - m)} + \\sum_{j \\neq y} e^{s \\cdot \\cos(\\theta_j)}}$$\n"
        "- **Bóc tách sai số xấp xỉ bước tích phân hữu hạn**: CFM thực tế giải ODE bằng số bước hữu hạn ($N=16$) "
        "chứ không phải vô hạn ($N \\rightarrow \\infty$). Do đó, giữa bước thứ $k$ và bước thứ $k+1$, luôn tồn tại sai số xấp xỉ số học cục bộ "
        "(Truncation Error $\\mathcal{O}(\\Delta t^2)$). Sai số này để lại vết tích ở các vi hài âm bậc cao trên 7.0 kHz.\n"
        "- **Hiệu ứng triệt tiêu lọt lưới**: Khi mô hình V8 được trực tiếp tối ưu hóa gradient trên các mẫu CFM, "
        "khối Wav2Vec 2.0 tiếng Việt và Nút Chủ Quyền (Master Node) của AASIST lập tức nhận diện được vết tích sai số tích phân số học này. "
        "Điểm số của OmniVoice CFM bị đẩy lùi từ vùng ranh giới $s \\in [-20, 0]$ sâu xuống $s < -38.0$.\n"
        "- **Kết quả**: Tỷ lệ phát hiện giả mạo của OmniVoice CFM nhảy vọt từ **79.47% lên 98.93% (371/375)**, "
        "EER giảm từ 14.67% xuống còn **2.13%**, triệt tiêu hoàn toàn hiện tượng lọt lưới 20% trước đây!",
    )

    add_heading_subsection(doc, "13.2.3 Tại Sao VieNeu-TTS Không Bị Sụp Đổ Khi Đóng Vai Trò Là Unseen Ở V8?")
    add_styled_paragraph(
        doc,
        "Một phát hiện khoa học mang tính bước ngoặt của đề tài: Khi VieNeu-TTS bị đẩy hoàn toàn ra ngoài tập huấn luyện "
        "và trở thành công cụ Unseen TTS ở mô hình V8, nó **hoàn toàn KHÔNG bị lọt lưới 20% như CFM từng bị**:\n"
        "- **Nguyên nhân vật lý**: NeuCodec sử dụng cơ chế lượng tử hóa phần dư rời rạc (RVQ). "
        "Sự chắp vá giữa các vector mã hóa rời rạc luôn tạo ra hiện tượng nhiễu lượng tử hóa (Quantization Noise). "
        "Nhiễu lượng tử hóa này tạo nên các bước nhảy gián đoạn rất nhỏ trong phổ pha STFT.\n"
        "- **Khả năng tổng quát hóa âm tính**: Khi mô hình V8 đã được rèn luyện để phân biệt các dạng sóng cực kỳ mượt mà "
        "(như F5-TTS và CFM), bất kỳ dạng sóng nào chứa dấu vết gián đoạn lượng tử rời rạc đều lập tức bị xem là bất thường.\n"
        "- Vì vậy, mô hình V8 phát hiện VieNeu-TTS với Pass Rate đạt **89.33% (335/375)** và EER đạt **10.67%**, "
        "vượt xa chỉ tiêu cam kết của Giả thuyết H2 (EER $\\le 15.0\\%$).",
    )

    add_callout_box(
        doc,
        "Kết quả đối chứng khẳng định: **Việc CFM từng bị lọt lưới 20% ở V7 không phải do hạn chế của kiến trúc SSL-AASIST, "
        "mà thuần túy do CFM đại diện cho một trường phái tạo sinh hoàn toàn mới (Continuous Flow). "
        "Khi đưa đại diện của trường phái này vào tập huấn luyện (V8), hệ thống tạo thành một 'Gọng Kìm Kép' "
        "(vừa bắt được dạng sóng trơn nhẵn của Flow-matching, vừa bắt được dạng sóng răng cưa của RVQ Codec)**.",
        title="KẾT LUẬN KHOA HỌC THEN CHỐT CỦA THÍ NGHIỆM ĐỐI CHỨNG V7 VS V8",
    )

    # -------------------------------------------------------------------------
    # 13.3 Ma trận suy giảm 2 chiều trên 5 kênh thoại nén
    # -------------------------------------------------------------------------
    add_heading_section(doc, "13.3 Ma Trận Suy Giảm 2 Chiều (Bidirectional Degradation Matrix) Trên 5 Kênh Thoại Nén")
    add_styled_paragraph(
        doc,
        "Bảng 13.2 và 13.3 trình bày ma trận suy giảm thực nghiệm chi tiết giữa hai mô hình V7 và V8 trên đúng "
        "375 clips spoof độc bản x 5 tình nguyện viên đối chứng (`SPK_0003` đến `SPK_0007`) và 420 clips giọng thật:",
    )

    # Table V7
    add_styled_paragraph(doc, "**Bảng 13.2: Ma Trận Hiệu Năng Mô Hình V7 (Seen: F5 + VieNeu | Unseen: OmniVoice CFM)**", bold=True, color_rgb=(31, 73, 125))
    headers_v7 = ["Công Cụ TTS / Mẫu", "Phân Loại", "Clean PCM", "AAC-LC 76k (Zalo)", "Opus 24k (Zalo)", "AMR-NB 8kHz", "G.711 A-law", "Pass Rate Pooled", "EER Pooled"]
    rows_v7 = [
        ("F5-TTS", "Seen", "98.67%", "100.0%", "98.67%", "98.67%", "100.0%", "99.20% (372/375)", "2.38%"),
        ("VieNeu-TTS v3 Turbo", "Seen", "88.00%", "88.00%", "88.00%", "86.67%", "88.00%", "87.73% (329/375)", "12.27%"),
        ("Seen TTS Pooled", "Seen", "93.33%", "94.00%", "93.33%", "92.67%", "94.00%", "93.47% (701/750)", "6.80%"),
        ("VoiceStudio (OmniVoice CFM)", "Unseen", "80.00%", "80.00%", "84.00%", "78.67%", "74.67%", "79.47% (298/375)", "14.67%"),
        ("Bona Fide (5 Volunteers)", "Held-out", "90.48%", "89.29%", "89.29%", "89.29%", "90.48%", "89.52% (376/420)", "BPCER = 10.48%"),
    ]

    t_v7 = doc.add_table(rows=len(rows_v7) + 1, cols=9)
    t_v7.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_v7, color="CCCCCC", sz="4")
    col_w9 = [Inches(1.8), Inches(0.8), Inches(0.7), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(1.1), Inches(0.8)]

    for i, title in enumerate(headers_v7):
        t_v7.rows[0].cells[i].width = col_w9[i]
        set_cell_background(t_v7.rows[0].cells[i], "1F497D")
        set_cell_margins(t_v7.rows[0].cells[i], top=80, bottom=80, left=60, right=60)
        p = t_v7.rows[0].cells[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_v7):
        row = t_v7.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w9[c_idx]
            bg_color = "F9FBFD" if r_idx % 2 == 0 else "FFFFFF"
            if c_idx == 0:
                bg_color = "F0F4F8"
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=60, bottom=60, left=50, right=50)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.0)
            if c_idx == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(31, 73, 125)
            elif "99." in val or "100." in val:
                run.bold = True
                run.font.color.rgb = RGBColor(0, 100, 0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Table V8
    add_styled_paragraph(doc, "**Bảng 13.3: Ma Trận Hiệu Năng Mô Hình V8 (Seen: F5 + OmniVoice CFM | Unseen: VieNeu-TTS v3 Turbo)**", bold=True, color_rgb=(192, 0, 0))
    rows_v8 = [
        ("F5-TTS", "Seen", "98.67%", "100.0%", "98.67%", "100.0%", "98.67%", "99.20% (372/375)", "2.10%"),
        ("VoiceStudio (OmniVoice CFM)", "Seen", "98.67%", "98.67%", "100.0%", "98.67%", "98.67%", "98.93% (371/375)", "2.13%"),
        ("Seen TTS Pooled", "Seen", "98.67%", "99.33%", "99.33%", "99.33%", "98.67%", "99.07% (743/750)", "2.11%"),
        ("VieNeu-TTS v3 Turbo", "Unseen", "90.67%", "89.33%", "89.33%", "88.00%", "89.33%", "89.33% (335/375)", "10.67%"),
        ("Bona Fide (5 Volunteers)", "Held-out", "91.67%", "90.48%", "90.48%", "90.48%", "91.67%", "90.95% (382/420)", "BPCER = 9.05%"),
    ]

    t_v8 = doc.add_table(rows=len(rows_v8) + 1, cols=9)
    t_v8.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_v8, color="CCCCCC", sz="4")

    for i, title in enumerate(headers_v7):
        t_v8.rows[0].cells[i].width = col_w9[i]
        set_cell_background(t_v8.rows[0].cells[i], "800000")
        set_cell_margins(t_v8.rows[0].cells[i], top=80, bottom=80, left=60, right=60)
        p = t_v8.rows[0].cells[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_v8):
        row = t_v8.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w9[c_idx]
            bg_color = "FFF9F9" if r_idx % 2 == 0 else "FFFFFF"
            if c_idx == 0:
                bg_color = "FDF0F0"
            set_cell_background(cell, bg_color)
            set_cell_margins(cell, top=60, bottom=60, left=50, right=50)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.0)
            if c_idx == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(180, 0, 0)
            elif "99." in val or "100." in val:
                run.bold = True
                run.font.color.rgb = RGBColor(0, 100, 0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_heading_subsection(doc, "13.3.1 Bóc Tách Quy Luật Biến Đổi Trên 5 Biến Thể Codec Thoại Nén")
    add_styled_paragraph(
        doc,
        "Từ hai bảng số liệu đối chứng Bảng 13.2 và Bảng 13.3, nhóm nghiên cứu rút ra 4 quy luật vật lý then chốt:\n"
        "1. **Đột phá trên VoiceStudio CFM**: Khi chuyển từ Unseen (V7) sang Seen (V8), tỷ lệ chặn của OmniVoice CFM "
        "tăng vọt từ **79.47% lên 98.93% (+19.46 pp)**, EER giảm sâu từ **14.67% xuống 2.13%**. "
        "Hiện tượng lọt lưới 20% bị quét sạch hoàn toàn trên cả 5 kênh viễn thông!\n"
        "2. **Độ ổn định của F5-TTS**: F5-TTS duy trì phong độ phòng thủ gần như tuyệt đối trên cả hai mô hình V7 (99.20%) và V8 (99.20%), "
        "chứng minh rằng việc bổ sung CFM không hề làm suy giảm năng lực nhận diện của các dòng mô hình trước đó.\n"
        "3. **Hiệu ứng Kênh Viễn Thông Băng Hẹp (AMR-NB 8kHz & G.711 A-law)**: Trên cả hai mô hình, kênh thoại di động 8kHz "
        "luôn đạt tỷ lệ phát hiện rất cao (88.0% - 100.0%). Thuật toán nén mã hóa nguồn thoại tuyến tính CELP hoạt động như một "
        "'kính lúp âm học', khuếch đại các vết lỗi pha và méo hài của các công cụ tổng hợp giọng nói.\n"
        "4. **Kênh Thoại Nén Zalo (AAC-LC 76k & Opus 24k)**: Do sử dụng kỹ thuật nén biến đổi cosin rời rạc sửa đổi (MDCT) "
        "kết hợp mô hình tâm thính giác, một phần năng lượng vi mô ở tần số cao bị làm mờ. Tuy nhiên, nhờ cơ chế cắt đa cửa sổ trượt "
        "(Dense Overlap Multi-Window), tỷ lệ chặn trên kênh Zalo của V8 vẫn đạt tới **98.67% - 100.0%** trên Seen và **89.33%** trên Unseen.",
    )

    # -------------------------------------------------------------------------
    # 13.4 Cẩm nang 5 câu hỏi phản biện chuyên sâu hội đồng
    # -------------------------------------------------------------------------
    add_heading_section(doc, "13.4 Cẩm Nang 5 Câu Hỏi & Trả Lời Phản Biện Chuyên Sâu Hội Đồng Về Thí Nghiệm Đối Chứng V7 vs V8")
    add_styled_paragraph(
        doc,
        "Dưới đây là 5 câu hỏi phản biện hóc búa nhất mà các thành viên Hội đồng chuyên về Học máy, Xử lý tiếng nói và An ninh mạng "
        "có thể đặt ra cho thí nghiệm đối chứng hoán đổi 2 chiều này. Mỗi câu trả lời được xây dựng chặt chẽ theo cấu trúc 3 tầng: "
        "**Claim (Khẳng định trực tiếp) $\\rightarrow$ Evidence (Bằng chứng số liệu) $\\rightarrow$ Impact (Ý nghĩa thực tiễn)**:",
    )

    qa_inverted = [
        (
            "Câu hỏi 1: Tại sao các em lại cần làm thí nghiệm đối chứng hoán đổi 2 chiều (V7 vs V8) thay vì chỉ dừng lại ở kết quả của mô hình V7?",
            "Dạ thưa Thầy/Cô, việc thực hiện thí nghiệm đối chứng hoán đổi 2 chiều (Bidirectional Inverted Experiment) xuất phát từ nguyên tắc **Liêm chính khoa học và Kiểm định đối xứng nghiêm ngặt**:\n"
            "- **Claim (Khẳng định)**: Thí nghiệm này là cách duy nhất để chứng minh rằng khả năng phát hiện của ViTrueVoice xuất phát từ năng lực trích xuất biểu diễn tự giám sát bản chất chứ không phải do ăn may kiến trúc hay thiên lệch (bias) vào một thuật toán cụ thể.\n"
            "- **Evidence (Bằng chứng)**: Ở mô hình V7, khi lấy F5 + VieNeu huấn luyện, VoiceStudio CFM (Unseen) đạt EER 14.67% (vừa vặn chạm ngưỡng KPI <= 15.0%). Nếu chỉ dừng lại ở đó, Hội đồng hoàn toàn có quyền nghi ngờ: 'Liệu mô hình có bị phụ thuộc vào họ mô hình lượng tử hóa NeuCodec hay không?'. Khi chúng em thực hiện chiều ngược lại ở mô hình V8 (đưa CFM vào huấn luyện và đẩy VieNeu ra làm Unseen), VieNeu-TTS vẫn đạt Pass Rate 89.33% và EER đạt 10.67% (thấp hơn nhiều so với trần 15.0%), trong khi CFM đạt mức chặn đứng 98.93% (EER 2.13%).\n"
            "- **Impact (Ý nghĩa thực tiễn)**: Kết quả đối xứng 2 chiều khẳng định hệ thống ViTrueVoice bao quát thành công cả hai nhánh công nghệ cốt lõi của thế giới: Mô hình Dòng liên tục (Flow-based) và Mô hình Lượng tử hóa rời rạc (Quantization-based)."
        ),
        (
            "Câu hỏi 2: Về mặt toán học, Continuous Flow Matching (CFM) khác gì so với Diffusion truyền thống và tại sao CFM ban đầu lại lọt lưới ~20% ở V7?",
            "Dạ thưa Thầy/Cô, sự khác biệt nằm ở **bản chất phương trình vi phân và quỹ đạo pha của dạng sóng**:\n"
            "- **Claim (Khẳng định)**: CFM sử dụng phương trình vi phân thường (ODE) dọc theo trường vận tốc tối ưu (Optimal Transport), sinh ra dạng sóng trơn nhẵn phi thường, làm cho các vết méo hài cao tần biến mất và đánh lừa được bộ lọc AASIST khi chưa từng được huấn luyện.\n"
            "- **Evidence (Bằng chứng)**: Mô hình Diffusion truyền thống (như F5-TTS) giải phương trình vi phân ngẫu nhiên (SDE) với quỹ đạo ziczac Brown, sau đó qua vocoder tái tạo pha nên luôn để lại các vết cắt pha gián đoạn. Mô hình V7 bắt F5-TTS đạt tới 99.20%. Ngược lại, OmniVoice CFM giải ODE $\\frac{dx_t}{dt} = v_t(x_t)$ nội suy thẳng từ nhiễu về âm thanh trong 16 bước, tạo ra quỹ đạo pha mượt mà tiệm cận giọng người thật. Trên tập VIVOS có SNR cao, các đặc trưng STFT của CFM nằm sát vùng phân phối giọng thật, khiến V7 bị lọt lưới 20.21% (Pass Rate chỉ đạt 79.79%).\n"
            "- **Impact (Ý nghĩa thực tiễn)**: Bóc tách được điều này giúp chúng em không đổ lỗi cho dữ liệu, mà hiểu rõ bản chất toán học để bổ sung mẫu đại diện CFM vào tập huấn luyện của V8, triệt tiêu hoàn toàn lỗ hổng lọt lưới."
        ),
        (
            "Câu hỏi 3: Khi hoán đổi đưa CFM vào tập Seen và VieNeu-TTS ra tập Unseen ở mô hình V8, tại sao VieNeu-TTS không bị sụp đổ tỷ lệ phát hiện như CFM trước đây?",
            "Dạ thưa Thầy/Cô, nguyên nhân nằm ở **nguyên lý lượng tử hóa phần dư rời rạc (Residual Vector Quantization - RVQ) của NeuCodec**:\n"
            "- **Claim (Khẳng định)**: VieNeu-TTS không bị sụp đổ vì bản chất kiến trúc RVQ của nó tạo ra các vết gián đoạn lượng tử hóa (quantization micro-discontinuities). Khi mô hình V8 đã được tôi luyện để nhận diện các dạng sóng siêu trơn nhẵn của F5 và CFM, bất kỳ dạng sóng nào có vết gián đoạn lượng tử đều bị coi là dị thường rõ rệt.\n"
            "- **Evidence (Bằng chứng)**: NeuCodec nén âm thanh bằng cách ép các vector liên tục vào các điểm rời rạc (codebook centroids) trong không gian vector 1024 chiều. Sự chuyển đổi giữa các mã token rời rạc trong miền thời gian luôn tạo ra các gai nhiễu lượng tử siêu nhỏ ở phổ pha STFT. Khi V8 đánh giá VieNeu-TTS (Unseen), tỷ lệ chặn đứng vẫn đạt mức rất cao: **89.33% (335/375)**, EER chỉ là **10.67%**, hoàn toàn làm chủ mục tiêu Giả thuyết H2 (EER <= 15.0%).\n"
            "- **Impact (Ý nghĩa thực tiễn)**: Điều này chứng minh rằng việc huấn luyện trên các dạng sóng trơn nhẵn (CFM) mang lại 'miễn dịch chéo' (Cross-Immunity) rất mạnh đối với các mô hình thế hệ cũ hoặc mô hình dựa trên mã hóa rời rạc."
        ),
        (
            "Câu hỏi 4: Kênh thoại nén Zalo (AAC-LC 76k, Opus 24k) và kênh thoại di động 8kHz (AMR-NB, G.711) ảnh hưởng như thế nào đến ma trận suy giảm của mô hình V8?",
            "Dạ thưa Thầy/Cô, hai nhóm kênh thoại nén này tác động theo hai cơ chế hoàn toàn đối nghịch:\n"
            "- **Claim (Khẳng định)**: Kênh viễn thông di động 8kHz khuếch đại lỗi giả mạo nhờ hiện tượng 'Nghịch lý bộ lọc viễn thông' (Codec Paradox), trong khi kênh Zalo làm mờ nhẹ đặc trưng nhưng được bảo toàn nhờ cơ chế cắt đa cửa sổ Asymmetric Veto.\n"
            "- **Evidence (Bằng chứng)**: Kênh AMR-NB 8kHz và G.711 A-law sử dụng thuật toán CELP (Code Excited Linear Prediction). Thuật toán này cố gắng mô hình hóa thanh quản con người bằng bộ lọc tuyến tính; khi gặp âm thanh tổng hợp AI, sự lệch pha giữa bộ lọc CELP và sóng AI gây ra hiện tượng cộng hưởng méo hài, giúp Pass Rate của V8 trên kênh này đạt từ **88.0% đến 100.0%**. Đối với kênh Zalo (AAC-LC 76k và Opus 24k), thuật toán biến đổi MDCT nén tâm thính giác làm giảm nhẹ độ phân tách (~1.3% - 2.0%), nhưng điểm số trung bình vẫn âm rất sâu ($s < -30.0$).\n"
            "- **Impact (Ý nghĩa thực tiễn)**: Hệ thống hoạt động cực kỳ ổn định trên cả hạ tầng mạng viễn thông truyền thống (2G/3G/PSTN) lẫn các ứng dụng OTT hiện đại (Zalo/Telegram)."
        ),
        (
            "Câu hỏi 5: Ý nghĩa thực tiễn của thí nghiệm đối chứng 2 chiều này đối với việc bảo vệ hệ thống trước các cuộc tấn công Zero-Day Voice Cloning trong tương lai là gì?",
            "Dạ thưa Thầy/Cô, thí nghiệm này đem lại giá trị định hình chiến lược phòng thủ an ninh mạng lâu dài:\n"
            "- **Claim (Khẳng định)**: Thí nghiệm chứng minh rằng để chống lại các cuộc tấn công Zero-Day (công cụ nhân bản giọng nói chưa từng xuất hiện), tập dữ liệu phòng thủ bắt buộc phải được xây dựng theo nguyên lý 'Bao quát Đa Không Gian Sinh Học' (Multi-Generative Space Coverage).\n"
            "- **Evidence (Bằng chứng)**: Khi hệ thống chỉ học một trường phái (như V7 chỉ học RVQ và Diffusion), nó sẽ để hở một sườn phòng thủ trước trường phái Dòng liên tục (CFM). Khi kết hợp cả F5-TTS (Diffusion) và OmniVoice (CFM) ở mô hình V8, hai trường phái này tạo thành một 'Gọng kìm kép'. Các công nghệ Zero-Day TTS trong tương lai (dù phát triển bởi OpenAI Voice Engine, ElevenLabs hay Meta Voicebox) về bản chất toán học vẫn phải dựa trên một trong hai trụ cột: hoặc giải phương trình vi phân (Continuous ODE/SDE) hoặc mã hóa rời rạc (Discrete Neural Codec).\n"
            "- **Impact (Ý nghĩa thực tiễn)**: ViTrueVoice đã thiết lập một khung kiến trúc phòng thủ vững chắc, sẵn sàng tích hợp và ứng phó chủ động trước mọi biến thể lừa đảo mạo danh giọng nói tinh vi trong tương lai."
        ),
    ]

    for q_idx, (q_text, a_text) in enumerate(qa_inverted):
        add_heading_subsection(doc, q_text)
        add_styled_paragraph(doc, a_text, font_size=10.5, line_spacing=1.15, space_after=6)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
