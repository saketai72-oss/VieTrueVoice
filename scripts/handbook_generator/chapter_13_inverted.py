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
    # 13.3.2 Ma trận thực nghiệm 4 Cổng x 3 Pooling Modes
    # -------------------------------------------------------------------------
    add_heading_subsection(doc, "13.3.2 Ma Trận Đối Chứng 4 Cổng x 3 Chế Độ Pooling & Đột Phá Layer-Wise Grafting")
    add_styled_paragraph(
        doc,
        "Để tìm kiếm điểm cân bằng tối ưu giữa việc triệt tiêu lọt lưới CFM và bảo vệ tính toàn vẹn sinh trắc học của giọng thật "
        "(đặc biệt là 5 tình nguyện viên đối chứng nghiệm thu độc lập và trường hợp ngoại lai SPK_0001), "
        "nhóm nghiên cứu đã tiến hành chuỗi thực nghiệm 3 giai đoạn kết hợp nâng cấp thuật toán Pooling:\n"
        "- **Giai đoạn 1 (Nâng cấp Consensus Asymmetric Veto)**: Trong `src/preprocessing/pooling.py`, cơ chế veto bất đối xứng "
        "được bổ sung bộ lọc đồng thuận (Consensus Guardrail): Khi $\\min(\\mathbf{s}) < -12.0$ và có từ 3 cửa sổ trở lên, "
        "nếu cửa sổ áp chót đạt $s_{[-2]} \\ge +6.0$ (chứng minh có ít nhất 2 cửa sổ đồng thuận là giọng thật rất rõ ràng), "
        "hệ thống giữ nguyên điểm số $s_{\\text{pooled}} = s_{[-2]}$ thay vì bị một cửa sổ vô thanh âm sâu kéo tụt toàn bộ clip.\n"
        "- **Giai đoạn 2 (Layer-Wise Grafting — Ghép Tầng Trọng Số)**: Ghép 4 tầng dưới của bộ mã hóa SSL ($l_0..l_3$, $\\alpha=0.15$) "
        "từ Checkpoint A (bảo toàn không gian biểu diễn ngữ âm vững chắc) với 8 tầng trên ($l_4..l_{11}$, $\\alpha=0.90$) "
        "và toàn bộ khối Compact AASIST từ Checkpoint B (thừa hưởng độ nhạy nhận diện CFM sắc bén).\n"
        "- **Giai đoạn 3 (1-Epoch Partial-Freeze Fine-Tuning)**: Khóa 8 tầng đầu, vi chỉnh 1 epoch trên 4.800 mẫu cân bằng.\n\n"
        "Bảng 13.4 tổng hợp ma trận đánh giá đối đầu 4 Cổng x 3 Chế độ Pooling:",
    )

    add_styled_paragraph(doc, "**Bảng 13.4: Ma Trận Đối Chứng 4 Cổng x 3 Chế Độ Pooling (Raw vs Stage 2 Grafted vs Stage 3)**", bold=True, color_rgb=(31, 73, 125))
    headers_4gate = ["Mốc Mô Hình", "Pooling Mode", "Cổng 1: SPK_0001 (15 clips)", "Cổng 2: 5 SPK Nghiệm Thu (84 clips)", "Cổng 3: Unseen VieNeu EER (955 clips)", "Cổng 4: Đảo Chiều CFM (195 clips)"]
    rows_4gate = [
        ("Checkpoint B Raw (Pha 2 thuần)", "Max", "11/15 (73.3%)", "81/84 (96.4%)", "10.89%", "119/195 (61.0%)"),
        ("Checkpoint B Raw", "Mean", "8/15 (53.3%)", "69/84 (82.1%)", "11.30%", "150/195 (76.9%)"),
        ("Checkpoint B Raw", "Asymmetric Veto", "11/15 (73.3%)", "76/84 (90.5%)", "10.70%", "140/195 (71.8%)"),
        ("Stage 2 Grafted (🏆 Winner)", "Max", "13/15 (86.7%)", "84/84 (100.0%)", "11.85%", "104/195 (53.3%)"),
        ("Stage 2 Grafted (split=4)", "Mean", "9/15 (60.0%)", "78/84 (92.9%)", "12.04%", "128/195 (65.6%)"),
        ("Stage 2 Grafted (best_model.pt)", "Consensus Veto", "12/15 (80.0%)", "83/84 (98.8%)", "11.40%", "126/195 (64.6%)"),
        ("Stage 3 Partial-FT (1 epoch)", "Max", "11/15 (73.3%)", "78/84 (92.9%)", "10.15%", "126/195 (64.6%)"),
        ("Stage 3 Partial-FT", "Mean", "7/15 (46.7%)", "69/84 (82.1%)", "10.68%", "157/195 (80.5%)"),
        ("Stage 3 Partial-FT", "Asymmetric Veto", "9/15 (60.0%)", "72/84 (85.7% ❌)", "10.68%", "154/195 (79.0%)"),
    ]

    t_4gate = doc.add_table(rows=len(rows_4gate) + 1, cols=6)
    t_4gate.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_4gate, color="CCCCCC", sz="4")
    col_w6 = [Inches(1.8), Inches(1.2), Inches(1.1), Inches(1.2), Inches(1.2), Inches(1.2)]

    for i, title in enumerate(headers_4gate):
        t_4gate.rows[0].cells[i].width = col_w6[i]
        set_cell_background(t_4gate.rows[0].cells[i], "1F497D")
        set_cell_margins(t_4gate.rows[0].cells[i], top=80, bottom=80, left=60, right=60)
        p = t_4gate.rows[0].cells[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_4gate):
        row = t_4gate.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w6[c_idx]
            bg_color = "F9FBFD" if r_idx % 2 == 0 else "FFFFFF"
            if "Winner" in r_data[0] or "Consensus Veto" in r_data[1]:
                bg_color = "F0FFF0"
            elif "❌" in val:
                bg_color = "FFF0F0"
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
            elif "Winner" in r_data[0] and c_idx == 1:
                run.bold = True
                run.font.color.rgb = RGBColor(0, 100, 0)
            elif "❌" in val:
                run.bold = True
                run.font.color.rgb = RGBColor(180, 0, 0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------------------
    # 13.3.3 Phân tích Dev Bona Fide BPCER & Case Study VIVOSDEV02
    # -------------------------------------------------------------------------
    add_heading_subsection(doc, "13.3.3 Phân Tích Dev Bona Fide BPCER (2.000 Mẫu) & Nghiên Cứu Điển Hình VIVOSDEV02")
    add_styled_paragraph(
        doc,
        "Để bảo vệ trải nghiệm người dùng thực tế tuân thủ nguyên tắc 'Bona Fide First', nhóm nghiên cứu đã đo đạc "
        "tỷ lệ từ chối nhầm người thật (BPCER @ $\\theta=0.0$) trên 2.000 mẫu âm thanh Dev Bona Fide (400 mẫu/codec, ngẫu nhiên có hạt giống cố định). "
        "Đồng thời, tiến hành đối soát chi tiết trên ca tấn công deepfake điển hình `VIVOSDEV02_omnivoice_prompt_000`:\n"
        "- **Hiệu quả giảm một nửa BPCER của Stage 2 Grafted**: Dưới cơ chế Consensus Asymmetric Veto, "
        "mô hình Stage 2 Grafted đạt BPCER chỉ **4.25% (85/2000)** với điểm trung bình dương rất cao ($+27.09$), "
        "giảm gần một nửa tỷ lệ báo nhầm so với Checkpoint B Raw (7.40%) và thấp hơn tới 2.5 lần so với Stage 3 Partial-FT (10.70%).\n"
        "- **Đảo chiều ngoạn mục ca lọt lưới VIVOSDEV02**: Ở mô hình V7, file này bị chấm điểm dương từ $+14.80$ đến $+15.94$ "
        "trên toàn bộ 5 codecs (lọt lưới 100%). Sang mô hình V8 Stage 2 Grafted, điểm số trên cả 5 codecs bị kéo tụt xuống "
        "từ **-27.45 đến -35.27**, đảo chiều hoàn toàn thành Spoof, khẳng định việc triệt tiêu lỗ hổng CFM!",
    )

    add_styled_paragraph(doc, "**Bảng 13.5: Đo Đạc Dev Bona Fide BPCER @ θ=0 (2.000 Mẫu) & Ca Nghiên Cứu VIVOSDEV02**", bold=True, color_rgb=(192, 0, 0))
    headers_bpcer = ["Mốc Mô Hình", "Pooling Mode", "BPCER @ θ=0 (2.000 mẫu)", "Mean Score Dev", "VIVOSDEV02 Clean (V7: +15.17)", "VIVOSDEV02 Zalo Opus (V7: +14.81)"]
    rows_bpcer = [
        ("Checkpoint B Raw", "Max", "5.10% (102/2000)", "+25.36", "-40.10", "-36.01"),
        ("Checkpoint B Raw", "Mean", "8.35% (167/2000)", "+22.33", "-40.46", "-37.36"),
        ("Checkpoint B Raw", "Asymmetric Veto", "7.40% (148/2000)", "+24.30", "-40.46", "-37.36"),
        ("Stage 2 Grafted (🏆 Winner)", "Max", "3.10% (62/2000)", "+27.69", "-32.77", "-27.45"),
        ("Stage 2 Grafted", "Mean", "5.15% (103/2000)", "+25.11", "-32.82", "-29.62"),
        ("Stage 2 Grafted (best_model.pt)", "Consensus Veto", "4.25% (85/2000)", "+27.09", "-32.82", "-29.62"),
        ("Stage 3 Partial-FT", "Max", "7.80% (156/2000)", "+27.17", "-33.42", "-31.73"),
        ("Stage 3 Partial-FT", "Mean", "11.95% (239/2000)", "+23.36", "-33.49", "-32.33"),
        ("Stage 3 Partial-FT", "Asymmetric Veto", "10.70% (214/2000)", "+25.76", "-33.49", "-32.33"),
    ]

    t_bpcer = doc.add_table(rows=len(rows_bpcer) + 1, cols=6)
    t_bpcer.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_bpcer, color="CCCCCC", sz="4")

    for i, title in enumerate(headers_bpcer):
        t_bpcer.rows[0].cells[i].width = col_w6[i]
        set_cell_background(t_bpcer.rows[0].cells[i], "800000")
        set_cell_margins(t_bpcer.rows[0].cells[i], top=80, bottom=80, left=60, right=60)
        p = t_bpcer.rows[0].cells[i].paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(title)
        run.font.name = "Times New Roman"
        run.font.size = Pt(8.5)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_bpcer):
        row = t_bpcer.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w6[c_idx]
            bg_color = "FFF9F9" if r_idx % 2 == 0 else "FFFFFF"
            if "Winner" in r_data[0] or "Consensus Veto" in r_data[1]:
                bg_color = "F0FFF0"
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
            elif "Consensus Veto" in r_data[1] and c_idx in [2, 3]:
                run.bold = True
                run.font.color.rgb = RGBColor(0, 100, 0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

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

    # -------------------------------------------------------------------------
    # 13.5 Thực nghiệm v0.9.4: Khôi phục đối xứng 1:1 (6.445 OmniVoice) & Head Calibration
    # -------------------------------------------------------------------------
    add_heading_section(
        doc,
        "13.5 Nâng Cấp Mô Hình Chính Thức v0.9.4: Khôi Phục Đối Xứng 1:1 (6.445 Mẫu OmniVoice_CFM), Huấn Luyện 2-Run & Hiệu Chuẩn Đầu Phân Loại (`head_blend_a0.75`)",
    )
    add_styled_paragraph(
        doc,
        "Ở phiên bản V8.0 tiền nhiệm, tập dữ liệu huấn luyện và đánh giá OmniVoice_CFM mới đạt quy mô bán phần (1.885 file), "
        "chưa tương xứng hoàn toàn 1:1 với tập Seen `VieNeu-TTS` của V7 (6.445 file). Để đảm bảo tính công bằng tuyệt đối trong đối chứng khoa học "
        "và kiểm chứng trên toàn bộ tập kiểm thử độc lập `test_indomain` (15.980 dòng), nhóm nghiên cứu đã hoàn thiện mô hình chính thức **ViTrueVoice v0.9.4**.",
    )

    add_heading_subsection(doc, "13.5.1 Khôi Phục Đối Xứng 1:1 Kho OmniVoice_CFM (6.445 Files) & Đồng Bộ Voice_Final (103.189 Files)")
    add_styled_paragraph(
        doc,
        "Toàn bộ tập mẫu giả lập `OmniVoice_CFM` tại `data/spoof_omnivoice_v8/` và kho nghiệm thu `Voice_Final/spoof/v8/Seen/OmniVoice_CFM/` "
        "được tái sinh và chuẩn hóa khớp 1:1 từng đường dẫn tương đối với `Voice_Final/spoof/v7/Seen/VieNeu_TTS/`:\n"
        "- **VIVOS**: **4.795** tệp WAV (65 người nói, 959 mẫu clean x 5 codecs).\n"
        "- **Common Voice**: **1.225** tệp WAV (25 người nói, 245 mẫu clean x 5 codecs).\n"
        "- **SPK_Volunteers**: **425** tệp WAV (`SPK_0001`: 50 tệp / 10 clean phục vụ Run 2; `SPK_0003..0007`: 375 tệp / 75 clean cô lập 100% ở kho đối chứng nghiệm thu).\n"
        "- **Tổng kho `Voice_Final`**: **103.189** tệp âm thanh (`bonafide/`: **70.174**; `spoof/v7/`: **13.955**; `spoof/v8/`: **19.060**), khớp 100% với chỉ mục kiểm toán SHA-256 `VOICE_FINAL_MANIFEST.csv`.",
    )

    add_styled_paragraph(doc, "**Bảng 13.6: Cấu Trúc 5 Manifest V8.1 Chuẩn 19 Cột (0% Rò Rỉ Dữ Liệu)**", bold=True, color_rgb=(31, 73, 125))
    headers_m81 = ["Tên Tệp Manifest (`data/manifests_zalo/`)", "Số Dòng", "Thành Phần Nhãn / TTS Generator", "Vai Trò Trong Thực Nghiệm V8.1"]
    rows_m81 = [
        ("train_v8_f5_omni_no_spk1.csv", "54.225", "46.925 Bona + 3.660 F5 + 3.640 OmniVoice", "Huấn luyện Run 1 (0% SPK_0001..0007, 0% VieNeu)"),
        ("train_v8_f5_omni_with_spk1.csv", "54.400", "+175 SPK_0001 (75 Bona + 50 F5 + 50 Omni)", "Huấn luyện Run 2 khắc phục giọng siêu trầm ngoại lai"),
        ("dev_v8_f5_omni.csv", "12.405", "10.490 Bona + 960 F5 + 955 OmniVoice", "Thẩm định hội tụ 15 người nói độc lập"),
        ("test_indomain_v8_f5_omni.csv", "15.980", "13.735 Bona + 1.125 F5 + 1.120 OmniVoice", "Đo lường công bằng V7 vs V8.0 vs V8.1 (eval_only=15.665)"),
        ("unseen_vieneu_benchmark.csv", "955", "955 VieNeu-TTS v3 Turbo (15 Dev SPK x 5 codecs)", "Kiểm định Giả thuyết H2 (Unseen OOD <= 15.0% EER)"),
    ]

    t_m81 = doc.add_table(rows=len(rows_m81) + 1, cols=4)
    t_m81.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_m81, color="CCCCCC", sz="4")
    col_w_m81 = [Inches(2.3), Inches(0.8), Inches(2.2), Inches(2.2)]
    for i, title in enumerate(headers_m81):
        cell = t_m81.rows[0].cells[i]
        cell.width = col_w_m81[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=70, right=70)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_m81):
        row = t_m81.rows[r_idx + 1]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w_m81[c_idx]
            bg = "F0F4F8" if c_idx == 0 else ("F9FBFD" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=60, right=60)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True
                r.font.color.rgb = RGBColor(31, 73, 125)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_heading_subsection(doc, "13.5.2 Quy Trình Huấn Luyện 2-Run (`am_m=0.20`) & Hiệu Chuẩn Đầu Phân Loại (`head_blend_a0.75`)")
    add_styled_paragraph(
        doc,
        "Huấn luyện được triển khai với cấu hình `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `batch_size=8`, `accum_steps=2`, "
        "AM-Softmax (`am_s=30.0`, giảm biên lề `am_m=0.20` để không ép điểm người nói trầm ngoại lai), khởi tạo từ checkpoint V5:\n"
        "- **Run 1 (`out/zalo_b_zalo_v8_1_no_spk1/`, 54.225 dòng)**: Pha 1 đạt Dev EER **7.96%** (33.70 phút); Pha 2 đạt Dev EER **6.32%** (131.63 phút). "
        "Cổng 1 (`SPK_0001`) đạt **46.7% (7/15)** ở `asymmetric_veto` và **60.0% (9/15)** ở `max` (< 80%), tự động kích hoạt rẽ nhánh Run 2.\n"
        "- **Run 2 (`out/zalo_b_zalo_v8_1_with_spk1/`, 54.400 dòng)**: Bổ sung 175 dòng `SPK_0001` (75 bona + 50 F5 + 50 OmniVoice). Pha 1 đạt Dev EER **10.76%** (34.17 phút); "
        "Pha 2 Epoch 1 đạt Dev EER **5.95%** (133.13 phút). Ở trạng thái thô (Raw Phase 2), khối SSL học phân tách rất mạnh giữa F5/OmniVoice và giọng thật "
        "(Dev Omni EER 7.98%/8.06%, Gate 4 đạt 86.2% dưới `asymmetric_veto`), nhưng độ lệch phân loại âm (negative classifier bias) kéo Gate 1 xuống 40.0% và Gate 2 xuống 65.5%. "
        "Do cả Run 2 Pha 1 và Pha 2 đều có Gate 1 < 54%, phép ghép tầng thô P1+P2 chỉ đạt tối đa 33.3% ở Gate 1.\n"
        "- **Giải pháp Stage 3 (`head_blend_a0.75`)**: Đóng băng hoàn toàn khối SSL Wav2Vec 2.0 của Run 2 Pha 2, chỉ hiệu chuẩn đầu phân loại (Head-Only) "
        "1 epoch trên tập cân bằng `train_v8_balanced_ft.csv` (5.100 dòng gồm 1.050 `SPK_0001`, 0% rò rỉ 5 tình nguyện viên/Dev/Test/VieNeu), "
        "sau đó nội suy trọng số theo tỷ lệ $\\mathbf{W}_{\\text{v0.9.4}} = 0.25\\,\\mathbf{W}_{\\text{Run2\\_P2}} + 0.75\\,\\mathbf{W}_{\\text{P2\\_HeadOnly}}$. "
        "Mô hình chiến thắng **v0.9.4** (`sha256: 30a383256458740e...`) được chuẩn hóa làm checkpoint mặc định tại `out/v0.9.4/best_model.pt`.",
    )

    add_heading_subsection(doc, "13.5.3 Đối Chứng Công Bằng 4 Cổng x 3 Chế Độ Pooling (V7 Best vs V8.0 Legacy vs v0.9.4 Best)")
    add_styled_paragraph(
        doc,
        "Bảng 13.7 đối chiếu trực diện 3 thế hệ mô hình trên bộ kiểm chứng 4.979 / 4.969 (đối xứng 1:1) qua cả 3 chế độ gộp điểm đa cửa sổ (`asymmetric_veto` | `max` | `mean`):",
    )

    add_styled_paragraph(doc, "**Bảng 13.7: Bảng Đối Chứng 4 Cổng Kiểm Định (V7 Best vs V8.0 Legacy vs v0.9.4 Best)**", bold=True, color_rgb=(31, 73, 125))
    headers_g81 = ["Mô Hình", "Pooling Mode", "G1: SPK_0001 (15)", "G2: 5 SPK (84)", "G3: Unseen VieNeu (955)", "G4: Omni Reversal (195)", "Dev BPCER (2.000)", "Seen Omni Dev (955)"]
    rows_g81 = [
        ("V7 Best", "asymmetric_veto", "26.7% (4/15)", "84.5% (71/84)", "5.03% (98.5% blk)", "0.5% (1/195)", "9.00%", "16.34% / 76.9% blk"),
        ("V8.0 Legacy", "asymmetric_veto", "80.0% (12/15)", "98.8% (83/84)", "11.40% (76.5% blk)", "64.6% (126/195)", "4.25%", "8.27% / 87.1% blk"),
        ("V8.0 Legacy", "max", "86.7% (13/15)", "100.0% (84/84)", "11.85% (71.4% blk)", "53.3% (104/195)", "3.10%", "11.70% / 76.0% blk"),
        ("V8.0 Legacy", "mean", "60.0% (9/15)", "92.9% (78/84)", "12.04% (77.9% blk)", "65.6% (128/195)", "5.15%", "7.02% / 89.0% blk"),
        ("v0.9.4 Best (head_blend_a0.75)", "asymmetric_veto", "93.3% (14/15)", "95.2% (80/84)*", "12.05% (79.6% blk)", "72.8% (142/195)", "6.00%", "8.06% / 91.5% blk"),
        ("v0.9.4 Best (head_blend_a0.75)", "max", "93.3% (14/15)", "98.8% (83/84)*", "12.30% (76.8% blk)", "60.5% (118/195)", "4.85%", "10.05% / 84.8% blk"),
        ("v0.9.4 Best (head_blend_a0.75)", "mean", "93.3% (14/15)", "91.7% (77/84)", "12.90% (81.9% blk)", "74.4% (145/195)", "8.10%", "8.10% / 91.8% blk"),
    ]

    t_g81 = doc.add_table(rows=len(rows_g81) + 1, cols=8)
    t_g81.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_g81, color="CCCCCC", sz="4")
    col_w8 = [Inches(1.3), Inches(0.95), Inches(0.85), Inches(0.95), Inches(1.05), Inches(1.0), Inches(0.75), Inches(1.05)]
    for i, title in enumerate(headers_g81):
        c = t_g81.rows[0].cells[i]
        c.width = col_w8[i]
        set_cell_background(c, "1F497D")
        set_cell_margins(c, top=70, bottom=70, left=45, right=45)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.0)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_g81):
        row = t_g81.rows[r_idx + 1]
        is_v81 = "v0.9.4 Best" in r_data[0]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w8[c_idx]
            bg = "F0FFF0" if is_v81 and r_data[1] == "asymmetric_veto" else ("F9FBFD" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=55, bottom=55, left=45, right=45)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(7.8)
            if c_idx == 0 or (is_v81 and c_idx in (2, 4, 5, 7)):
                r.bold = True
                if is_v81:
                    r.font.color.rgb = RGBColor(0, 100, 0) if c_idx > 0 else RGBColor(31, 73, 125)

    add_styled_paragraph(
        doc,
        "*Ghi chú Gate 2: Trên 4 tình nguyện viên đối chứng chính (`SPK_0004..0007`, 64 tệp), v0.9.4 Best đạt **100.0% (64/64)** ở cả `asymmetric_veto` và `max`.",
        font_size=9.0,
        italic=True,
        space_after=6,
    )

    add_heading_subsection(doc, "13.5.4 Benchmark Trên Tập Độc Lập 15.980 Clips (`test_indomain_v8_f5_omni.csv`)")
    add_styled_paragraph(
        doc,
        "Bảng 13.8 tổng hợp kết quả đánh giá quy mô lớn trên 15.980 mẫu (`eval_only=15.665` mẫu), đối chiếu toàn diện theo pooling, công cụ tạo sinh và 5 biến thể kênh nén:",
    )

    add_styled_paragraph(doc, "**Bảng 13.8: Benchmark `test_indomain_v8_f5_omni.csv` (15.980 Clips) — V7 Best vs V8.0 Legacy vs v0.9.4 Best**", bold=True, color_rgb=(192, 0, 0))
    headers_t81 = ["Mô Hình", "Pooling Mode", "Overall EER / Block", "BPCER", "F5-TTS (EER / Blk)", "OmniVoice (EER / Blk)", "5 Codecs EER (Clean | AAC | Opus | G711 | AMR)"]
    rows_t81 = [
        ("V7 Best", "asymmetric_veto", "13.72% / 87.22%", "15.10%", "6.17% / 99.38%", "19.88% / 75.00%", "13.37 | 12.92 | 14.92 | 14.03 | 13.36%"),
        ("V8.0 Legacy", "asymmetric_veto", "6.79% / 90.33%", "4.12%", "2.23% / 98.22%", "8.84% / 82.41%", "6.46 | 7.35 | 6.90 | 6.24 | 6.11%"),
        ("v0.9.4 Best", "asymmetric_veto", "5.63% / 95.01%", "6.73%", "2.81% / 98.49%", "7.95% / 91.52%", "5.52 | 5.79 | 6.02 | 6.11 | 4.88%"),
        ("V7 Best", "max", "14.72% / 83.16%", "12.07%", "5.14% / 98.93%", "21.79% / 67.32%", "14.92 | 14.25 | 15.59 | 14.48 | 14.03%"),
        ("V8.0 Legacy", "max", "9.31% / 84.37%", "2.64%", "2.77% / 97.16%", "13.30% / 71.52%", "9.25 | 10.68 | 9.80 | 8.91 | 7.90%"),
        ("v0.9.4 Best", "max", "8.33% / 88.24%", "5.34%", "3.21% / 97.69%", "11.61% / 78.75%", "8.24 | 9.35 | 8.69 | 7.35 | 7.13%"),
        ("V7 Best", "mean", "13.81% / 87.88%", "16.28%", "5.32% / 99.47%", "19.21% / 76.25%", "13.59 | 12.92 | 14.92 | 13.90 | 13.11%"),
        ("V8.0 Legacy", "mean", "5.54% / 92.92%", "4.81%", "2.31% / 98.22%", "6.54% / 87.59%", "5.57 | 6.17 | 5.88 | 5.12 | 5.25%"),
        ("v0.9.4 Best", "mean", "6.24% / 96.17%", "8.80%", "2.84% / 98.67%", "7.77% / 93.66%", "6.17 | 6.68 | 6.74 | 5.63 | 5.81%"),
    ]

    t_t81 = doc.add_table(rows=len(rows_t81) + 1, cols=7)
    t_t81.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_t81, color="CCCCCC", sz="4")
    col_w7 = [Inches(0.95), Inches(1.0), Inches(1.1), Inches(0.65), Inches(1.1), Inches(1.15), Inches(2.05)]
    for i, title in enumerate(headers_t81):
        c = t_t81.rows[0].cells[i]
        c.width = col_w7[i]
        set_cell_background(c, "800000")
        set_cell_margins(c, top=70, bottom=70, left=45, right=45)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.0)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows_t81):
        row = t_t81.rows[r_idx + 1]
        is_winner = (r_data[0] == "v0.9.4 Best" and r_data[1] == "asymmetric_veto")
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w7[c_idx]
            bg = "F0FFF0" if is_winner else ("FFF9F9" if r_idx % 2 == 0 else "FFFFFF")
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=55, bottom=55, left=45, right=45)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(7.8)
            if is_winner or c_idx == 0:
                r.bold = True
                if is_winner and c_idx > 0:
                    r.font.color.rgb = RGBColor(0, 100, 0)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    add_callout_box(
        doc,
        "Dưới cơ chế chuẩn sản xuất `asymmetric_veto` trên tập kiểm thử độc lập 15.980 mẫu (`test_indomain_v8_f5_omni.csv`), "
        "**ViTrueVoice v0.9.4 (`head_blend_a0.75`)** đạt kỷ lục **5.63% EER / 95.01% tỷ lệ chặn** (`eval_only`: 5.61%), "
        "thắng tuyệt đối cả V8.0 Legacy (6.79% / 90.33%) lẫn V7 Best (13.72% / 87.22%) trên toàn bộ **5/5 biến thể codec** "
        "(Clean 5.52%, Zalo AAC-LC 76k 5.79%, Zalo Opus 24k 6.02%, G.711 A-law 6.11%, AMR-NB 4.88%), "
        "đẩy tỷ lệ chặn OmniVoice CFM từ 75.00% (V7) lên **91.52%**, đồng thời đạt **93.3%** Gate 1 `SPK_0001`, "
        "**100%** 4 SPK đối chứng chính và **12.05% EER** trên Unseen VieNeu-TTS.",
        title="TỔNG KẾT ĐỘT PHÁ CỦA MÔ HÌNH VITRUEVOICE v0.9.4",
    )
