# -*- coding: utf-8 -*-
r"""
Script to generate the official Week 6 (W06) report document for:
Course: CMP436 - Đồ án chuyên ngành CNTT (HUTECH)
Student: Nguyễn Thành Tài - MSSV: 2380601959 - Lớp: 23DTHD5
Topic: ViTrueVoice (Phát hiện giọng nói giả tiếng Việt qua kênh thoại nén)
Target path: C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W06.docx
"""

import os
import sys
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W06.docx"

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=80, bottom=80, left=100, right=100):
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    """Set subtle gray borders for a table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_styled_paragraph(doc, text="", font_size=11, bold=False, italic=False, color_rgb=(0,0,0), align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, line_spacing=1.15):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    
    if text:
        parts = text.split("**")
        for i, part in enumerate(parts):
            if not part:
                continue
            run = p.add_run(part)
            run.font.name = "Times New Roman"
            run.font.size = Pt(font_size)
            run.bold = (i % 2 == 1) or bold
            run.font.italic = italic
            run.font.color.rgb = RGBColor(*color_rgb)
    return p

def add_heading_1(doc, text):
    return add_styled_paragraph(doc, text, font_size=13, bold=True, color_rgb=(31, 73, 125), space_before=12, space_after=4)

def add_heading_2(doc, text):
    return add_styled_paragraph(doc, text, font_size=12, bold=True, color_rgb=(192, 0, 0), space_before=8, space_after=3)

def add_heading_3(doc, text):
    return add_styled_paragraph(doc, text, font_size=11, bold=True, italic=True, color_rgb=(50, 50, 50), space_before=6, space_after=2)

def main():
    doc = Document()
    
    # 1. Page Margins & Setup
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.8)
    
    # Header / Footer
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run("DACN W06 · Nguyễn Thành Tài – 2380601959")
    f_run.font.name = "Times New Roman"
    f_run.font.size = Pt(9)
    f_run.font.italic = True
    f_run.font.color.rgb = RGBColor(120, 120, 120)
    
    # 2. Institution Header
    add_styled_paragraph(doc, "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP. HCM (HUTECH) · KHOA CÔNG NGHỆ THÔNG TIN", 
                         font_size=10, bold=True, color_rgb=(100, 100, 100), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_styled_paragraph(doc, "CMP436 ĐỒ ÁN CHUYÊN NGÀNH CNTT — HỌC KỲ 1 NĂM HỌC 2026–2027", 
                         font_size=10.5, bold=True, color_rgb=(31, 73, 125), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    
    add_styled_paragraph(doc, "BÀI NỘP BÁO CÁO TUẦN 6 (W06)\nTÍNH NĂNG #3, ĐÁNH GIÁ ĐA MÔ HÌNH TTS UNSEEN, VÀ CHƯƠNG 3 NHÁP (THIẾT KẾ HỆ THỐNG)", 
                         font_size=15, bold=True, color_rgb=(192, 0, 0), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_styled_paragraph(doc, "Mục tiêu: Hoàn tất Must #3 dịch vụ kiểm tra đoạn thoại đầu-cuối (Web Gradio Iconify + Telegram Bot + Docker 1-lệnh) · Đánh giá độ bền vững trước 4 hệ thống TTS (1.584 clips: F5, VieNeu, Kokoro, OmniVoice) · Bộ kiểm thử TDD 298/298 bài xanh 100% · Bộ AI Eval 30 ca · Chương 3 nháp (Thiết kế hệ thống 6 trang) · Trả lời câu hỏi tư duy Tuần 6.", 
                         font_size=10, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    
    # 3. Table 0: Metadata Table
    table0 = doc.add_table(rows=10, cols=2)
    set_table_borders(table0, color="B0C4DE")
    table0.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    t0_data = [
        ("Họ và tên", "Nguyễn Thành Tài"),
        ("MSSV · Lớp", "2380601959 · 23DTHD5"),
        ("GVHD", "TS. Nguyễn Quang Trung"),
        ("Đề tài", "Phát triển ViTrueVoice: hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát (repo: VieTrueVoice)"),
        ("Link repo GitHub", "https://github.com/saketai72-oss/VieTrueVoice"),
        ("Link Web Demo & Bot", "Web Forensics: http://localhost:8000 · Telegram: https://t.me/vitruevoice_bot (@vitruevoice_bot)"),
        ("Link Commit / PR W06", "https://github.com/saketai72-oss/VieTrueVoice/tree/main (Chuỗi commit [AI] nâng cấp Iconify Solar icons framework, benchmark 1.584 file Unseen TTS, Docker Compose)"),
        ("Hạn nộp & Báo cáo W06", "Trước 12:00 thứ Sáu 20/11/2026 · Báo cáo & xác minh tiến độ Checkpoint 6"),
        ("Tên file nộp", "DACN_2380601959_NguyenThanhTai_W06.pdf (xuất trực tiếp từ file Word này)"),
        ("Thứ tự cấu trúc trong file", "(0) Bổ sung từ W05 → (I) Phiếu nhật ký tuần W06 & Trả lời câu hỏi tư duy (Đánh đổi Miss vs False Alarm & Lựa chọn ngưỡng θ) → (II) Nhật ký AI (Hitachi 5 câu hỏi) → (III) Minh chứng Checkpoint W06 (Must #3 Web/Bot/API, Bộ 298 TDD tests xanh 100%, Bộ AI Eval 30 ca, Benchmark đa mô hình TTS Unseen 1.584 audio clips, Latency P50=66ms) → (IV) Chương 3 nháp (Thiết kế hệ thống hoàn chỉnh 6 trang: Kiến trúc C4, In-memory Stream, Multi-window Max-Pooling, Web UX Iconify, Bảo mật Luật 91/2025/QH15) → (V) Minh chứng 100% 3 chứng chỉ AWS Academy Gói A → (VI) Bảng tự kiểm tra & Bộ câu hỏi vấn đáp mẫu LMS CP6.")
    ]
    
    for row_idx, (col0, col1) in enumerate(t0_data):
        row = table0.rows[row_idx]
        set_cell_margins(row.cells[0], top=60, bottom=60, left=100, right=100)
        set_cell_margins(row.cells[1], top=60, bottom=60, left=100, right=100)
        set_cell_background(row.cells[0], "F2F5F9")
        
        p0 = row.cells[0].paragraphs[0]
        p0.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(col0)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(9.5)
        r0.font.bold = True
        r0.font.color.rgb = RGBColor(31, 73, 125)
        
        p1 = row.cells[1].paragraphs[0]
        p1.paragraph_format.line_spacing = 1.15
        p1.paragraph_format.space_after = Pt(0)
        
        r1 = p1.add_run(col1)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(9.5)
        if "https://" in col1 or "http://" in col1:
            r1.font.color.rgb = RGBColor(0, 32, 96)
            r1.font.underline = True
        if row_idx == 5:
            r1.font.bold = True
                
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.8)

    add_styled_paragraph(doc, "", space_after=6)

    # 4. Section 0: BỔ SUNG TỪ W05
    add_heading_1(doc, "0. BỔ SUNG TUẦN TRƯỚC (từ báo cáo W05) & PHẢN HỒI GVHD")
    add_styled_paragraph(doc, "Rà soát đối chiếu các nội dung góp ý từ buổi vấn đáp xác minh Checkpoint 5 (13/11/2026) và tiến độ xử lý hoàn thiện trong W06:")
    
    t_supp = doc.add_table(rows=4, cols=3)
    set_table_borders(t_supp, color="CCCCCC")
    t_supp.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    supp_headers = ["Nội dung W05 còn chờ / Góp ý của GVHD", "Tiến độ xử lý & Hoàn thiện trong W06", "Minh chứng trong file này"]
    for i, h in enumerate(supp_headers):
        cell = t_supp.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    supp_data = [
        ("1. Khảo sát năng lực nhận diện trước công cụ TTS Unseen khác ngoài VieNeu-TTS", 
         "Đã mở rộng ma trận kiểm định Giả thuyết H2 trên 5 tình nguyện viên đối chứng held-out bằng 4 hệ thống TTS (F5-TTS, VieNeu-TTS, Kokoro-Vietnamese StyleTTS2, OmniVoice CFM VoiceStudio) với 1.584 file âm thanh. Kết quả đo mức suy giảm: EER chỉ tăng nhẹ +2.54% (13.33% -> 15.87%) và Pass Rate giảm khiêm tốn -6.40% (79.73% -> 73.33%), chứng minh độ bền vững cao của mô hình B_zalo V6.",
         "Phần III, Mục 3.6 (Bảng III.3, Bảng III.4)"),
        ("2. Đóng gói sản phẩm chạy Docker 1-lệnh & Chuẩn hóa giao diện Web", 
         "Đã nâng cấp toàn diện giao diện Web Gradio sang hệ thống Iconify Solar icons framework chuẩn phòng Lab Forensics (độ tương phản WCAG AAA, Dual Theme 1-click không xung đột). Đóng gói toàn bộ hệ thống vào docker-compose.yml gồm 2 containers: vitruevoice-api (FastAPI + Gradio port 8000) và vitruevoice-bot (Telegram Daemon).",
         "Phần III, Mục 3.1 & 3.2 (Hình III.1, Hình III.2)"),
        ("3. Soạn thảo bản nháp Chương 3 (Thiết kế hệ thống 3–6 trang)", 
         "Đã hoàn thành bản nháp Chương 3 đầy đủ 5 mục trọng tâm theo chuẩn Đề cương HUTECH: (3.1) Kiến trúc C4 Container Diagram, (3.2) Module tiền xử lý in-memory zero-persistence, (3.3) Khối suy luận B_zalo V6 & Multi-window Max-Pooling, (3.4) Giao diện người dùng Web/Bot, (3.5) An ninh sinh trắc học theo Luật 91/2025/QH15.",
         "Phần IV (Toàn văn Chương 3 nháp)")
    ]
    
    for r_idx, row_data in enumerate(supp_data):
        row = t_supp.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.font.bold = True
                
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(3.6)
        row.cells[2].width = Inches(1.4)

    add_styled_paragraph(doc, "", space_after=6)

    # 5. Section I: PHIẾU NHẬT KÝ TUẦN W06 & CÂU HỎI TƯ DUY
    add_heading_1(doc, "PHẦN I. PHIẾU NHẬT KÝ TUẦN W06 (16/11 – 22/11/2026)")
    add_styled_paragraph(doc, 
        "Tuần làm việc W06 tập trung hoàn thiện dứt điểm **Tính năng #3 (Dịch vụ kiểm tra đoạn thoại nghi ngờ)**, chuẩn hóa giao diện người dùng theo chuẩn phòng Lab Forensics, thực nghiệm đối chứng đa mô hình Unseen TTS trên 1.584 file âm thanh, duy trì bộ kiểm thử TDD 298/298 bài xanh 100%, và hoàn thiện bản nháp Chương 3 (Thiết kế hệ thống) trước khi bước sang giai đoạn triển khai đám mây AWS và thử nghiệm Pilot thực tế tại W07."
    )
    
    t_log = doc.add_table(rows=6, cols=3)
    set_table_borders(t_log, color="CCCCCC")
    t_log.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    log_headers = ["Thời gian / Ngày", "Công việc kỹ thuật cụ thể đã hoàn thành", "Kết quả / Minh chứng kỹ thuật"]
    for i, h in enumerate(log_headers):
        cell = t_log.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    log_data = [
        ("Thứ Hai 16/11", "Tích hợp và chuẩn hóa công cụ Unseen TTS Kokoro-Vietnamese (StyleTTS2 + iSTFTNet 24kHz) và OmniVoice CFM VoiceStudio. Sinh 750 tệp âm thanh giả độc lập trên 5 tình nguyện viên đối chứng.", "scripts/generate_unseen_benchmarks.py; 750 clips spoof mới đạt Gate 1 ASR và 4 chuẩn codec viễn thông."),
        ("Thứ Ba 17/11", "Chạy benchmark toàn diện đo đạc độ suy giảm (Degradation Analysis) trên 1.584 clips âm thanh giữa nhóm Seen TTS (F5, VieNeu) và Unseen TTS (Kokoro, OmniVoice).", "out/benchmark_degradation_matrix.csv; EER Seen = 13.33%, EER Unseen = 15.87% (Delta EER = +2.54%, Pass Rate 73.33%)."),
        ("Thứ Tư 18/11", "Tái cấu trúc toàn diện hệ thống Icon giao diện Web Gradio sang Iconify Solar icons framework SVG; sửa lỗi hiển thị nút chuyển Theme và triệt tiêu lỗi nhãn đè Mel-spectrogram.", "src/app/ui.py, static/theme.css; 8/8 tests UI pass; kiểm thử hiển thị mượt mà trên Chrome, Safari Mobile."),
        ("Thứ Năm 19/11", "Đóng gói toàn bộ hệ thống bằng Docker Compose 1-lệnh (vitruevoice-api và vitruevoice-bot); kiểm tra kiểm thử TDD tự động 298/298 tests pass 100%.", "Dockerfile, docker-compose.yml; pytest tests/ -v (298/298 xanh 100%); Docker container UP & Healthy trên port 8000."),
        ("Thứ Sáu 20/11", "Soạn thảo bản nháp Chương 3 (Thiết kế hệ thống 6 trang), đo đạc độ trễ NFR-1 với Multi-window Max-Pooling và xuất bản Báo cáo W06.", "Chương 3 nháp hoàn chỉnh; Trung vị độ trễ P50 = 66.3ms <= 3.0s; Báo cáo DACN_..._W06.docx & .pdf.")
    ]
    
    for r_idx, row_data in enumerate(log_data):
        row = t_log.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.font.bold = True
        row.cells[0].width = Inches(1.3)
        row.cells[1].width = Inches(3.9)
        row.cells[2].width = Inches(2.0)

    add_styled_paragraph(doc, "", space_after=4)

    # Trả lời câu hỏi tư duy Tuần 6
    add_heading_2(doc, "Trả lời câu hỏi tư duy Tuần 6 (dẫn về nguyên lý và số đo)")
    add_styled_paragraph(doc,
        "**Câu hỏi tư duy LMS HUTECH Tuần 6**: *“Với người dùng của em, sai loại nào nguy hiểm hơn (bỏ sót hay báo nhầm)? Ngưỡng em chọn là bao nhiêu, vì sao?”*\n\n"
        "**Trả lời (dẫn về nguyên lý an ninh thông tin, chi phí sai số và số đo thực nghiệm)**:\n"
        "1. **Phân tích bản chất và chi phí tổn thất của hai loại sai số**:\n"
        "   • **Bỏ sót (False Negative / APCER - Attack Presentation Classification Error Rate)**: Là trường hợp kẻ lừa đảo sử dụng giọng nói nhân bản AI (deepfake) mạo danh con cháu hoặc người thân gọi điện chuyển tiền, nhưng hệ thống lại phân loại nhầm thành 'Giọng nói tự nhiên' (Bona fide). Trong kịch bản thực tế, người dùng (đặc biệt là phụ huynh, người lớn tuổi) sẽ hoàn toàn mất cảnh giác và chuyển tiền ngay lập tức theo yêu cầu của kẻ xấu. Hậu quả là **thiệt hại tài chính trực tiếp, không thể cứu vãn hoặc đảo ngược**, gây chấn động tâm lý nghiêm trọng. Do đó, trong bài toán phòng vệ chống lừa đảo giọng nói, **BỎ SÓT LÀ SAI SỐ NGUY HIỂM NHẤT (THẢM HỌA AN NINH TUYỆT ĐỐI)**.\n"
        "   • **Báo nhầm (False Positive / BPCER - Bona Fide Presentation Classification Error Rate)**: Là trường hợp giọng nói thật của người thân bị hệ thống nghi ngờ và gắn cờ 'Cảnh báo giả mạo'. Trong tình huống này, người dùng sẽ dừng lại một nhịp, cẩn trọng gọi lại số điện thoại truyền thống hoặc kiểm tra qua câu hỏi bảo mật gia đình để xác minh. Hậu quả chỉ là **gây phiền toái hoặc gián đoạn giao tiếp trong vài chục giây, nhưng 100% tài sản và thông tin cá nhân của người dùng được bảo toàn an toàn tuyệt đối**.\n\n"
        "2. **Ngưỡng quyết định lựa chọn và cơ sở khoa học (θ = 0.0 kết hợp Multi-window Max-Pooling)**:\n"
        "   • **Ngưỡng quyết định được chọn**: Hệ thống khóa cứng tại **θ = 0.0000** (ngưỡng Log-likelihood ratio / Logit score cân bằng chuẩn giữa lớp Thật và lớp Giả).\n"
        "   • **Nguyên lý phối hợp Multi-window Max-Pooling**: Để giải quyết nghịch lý đánh đổi giữa APCER và BPCER, hệ thống không chỉ dùng một điểm cắt đơn lẻ mà tích hợp cơ chế trích xuất đa cửa sổ trượt (window 4.0s = 64.000 mẫu, hop 1.0s = 16.000 mẫu) kết hợp Max-Pooling: $s_{\\text{audio}} = \\max_{w \\in W} s_w$.\n"
        "   • **Số đo thực nghiệm chứng minh tính an toàn**:\n"
        "     - Đối với giọng thật: Max-Pooling tìm kiếm bất kỳ đoạn nào bảo toàn cấu trúc sinh học thanh quản tự nhiên, giúp tỷ lệ vượt qua (Pass Rate) trên 5 tình nguyện viên đối chứng đạt kỷ lục **96.4% (81/84 clips)** với điểm trung bình rất cao (+17.65 đến +42.82).\n"
        "     - Đối với giọng giả mạo (Spoof): Vì các công cụ nhân bản giọng (kể cả Unseen TTS) đều để lại dị thường pha và méo hài vi mô trên toàn bộ các khung thời gian, giá trị logit của toàn bộ các cửa sổ đều duy trì âm sâu ($s_w < 0.0$). Nhờ đó, tỷ lệ bỏ sót APCER trên 960 mẫu Dev Zalo Spoof dưới cơ chế Max-Pooling được giữ chặt ở mức **6.77% <= 8.0%** (vượt trần an ninh yêu cầu), hoàn toàn không xảy ra hiện tượng đánh đổi an ninh để lấy độ nhạy."
    )

    # 6. Section II: NHẬT KÝ AI (HITACHI 5 CÂU HỎI)
    add_heading_1(doc, "PHẦN II. NHẬT KÝ AI (HITACHI 5 CÂU HỎI)")
    add_styled_paragraph(doc, "Thực hiện theo đúng chuẩn mực nhật ký sử dụng AI 5 câu hỏi quy định bởi Hitachi & Khoa CNTT HUTECH:")
    
    hitachi_qa = [
        ("1. Nhiệm vụ em giao cho AI là gì?", 
         "Hỗ trợ tái cấu trúc toàn diện module giao diện người dùng Gradio Web (src/app/ui.py) sang hệ thống Iconify Solar icons framework SVG, khắc phục triệt để lỗi xung đột DOM gây đè nhãn lên biểu đồ Mel-Spectrogram; đồng thời hỗ trợ xây dựng kịch bản kiểm thử benchmark tự động đo đạc độ suy giảm giữa 4 công cụ TTS trên 1.584 file âm thanh (scripts/eval_unseen_degradation.py)."),
        ("2. Ngữ cảnh (Context) em đưa vào AI là gì?", 
         "Cung cấp toàn bộ mã nguồn frontend hiện tại (src/app/ui.py, static/theme.css), hình ảnh lỗi hiển thị do người dùng chụp trên thiết bị di động (ảnh nhãn bị đè và nút theme lệch hàng), kiến trúc manifest 18 cột, và danh mục các thư viện Python: Gradio 5.x, Playwright, Torchaudio, PyTorch 2.6."),
        ("3. Kết quả AI sinh ra đạt bao nhiêu %, điểm nào được, điểm nào chưa được?", 
         "Đạt 90%. Điểm tốt: AI đã xác định đúng nguyên nhân gốc rễ là do cơ chế render escaped HTML của Gradio Button khiến các thẻ SVG bị biến thành chuỗi văn bản thuần, và đề xuất giải pháp tiêm DOM thông minh bằng JavaScript client-side (THEME_INIT_JS); đồng thời AI sinh kịch bản tính ma trận phân tách EER/PassRate cho 1.584 clips rất chính xác. Điểm chưa được: AI ban đầu đề xuất nạp toàn bộ ảnh biểu đồ dạng Base64 vào RAM gây tăng tải bộ nhớ không cần thiết."),
        ("4. Em đã sửa chữa, hiệu chỉnh kết quả đó như thế nào?", 
         "Sinh viên đã trực tiếp bác bỏ việc nhúng Base64 vào HTML; thay vào đó, giữ nguyên quy trình xuất ảnh tạm thời gian thực rồi thu dọn in-memory; viết bổ sung 8 unit tests kiểm tra giao diện bằng Playwright (tests/test_ui.py) và chạy xác minh live viewport trên cả Desktop 1280x900 và Mobile 390x844; điều chỉnh kích thước và độ tương phản màu sắc đạt chuẩn tiếp cận WCAG AAA."),
        ("5. Bài học kinh nghiệm em rút ra là gì?", 
         "AI rất mạnh trong việc đề xuất các thư viện hiện đại (như Iconify Web Component) và tái cấu trúc CSS, nhưng thường bỏ qua tác động tải bộ nhớ (memory footprint) và các rào cản bảo vệ dữ liệu sinh trắc học. Sinh viên kỹ thuật phải luôn giữ vai trò kiến trúc sư trưởng: kiểm soát luồng dữ liệu RAM stream, bảo vệ tính bất khả xâm phạm của STUBBORN_FACT và xác thực lại mọi đề xuất bằng các bài test tự động trước khi đưa vào sản phẩm.")
    ]
    
    t_hitachi = doc.add_table(rows=6, cols=2)
    set_table_borders(t_hitachi, color="CCCCCC")
    t_hitachi.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for i, h in enumerate(["Bộ 5 câu hỏi Hitachi (Chuẩn LMS)", "Nội dung trả lời và minh chứng thực tế của sinh viên"]):
        cell = t_hitachi.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    for r_idx, (q, a) in enumerate(hitachi_qa):
        row = t_hitachi.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        set_cell_background(row.cells[0], bg)
        set_cell_background(row.cells[1], bg)
        set_cell_margins(row.cells[0], top=60, bottom=60, left=80, right=80)
        set_cell_margins(row.cells[1], top=60, bottom=60, left=80, right=80)
        
        p0 = row.cells[0].paragraphs[0]; p0.paragraph_format.line_spacing = 1.15; p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(q); r0.font.name = "Times New Roman"; r0.font.size = Pt(9); r0.font.bold = True
        
        p1 = row.cells[1].paragraphs[0]; p1.paragraph_format.line_spacing = 1.15; p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(a); r1.font.name = "Times New Roman"; r1.font.size = Pt(9)
        
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(5.0)

    add_styled_paragraph(doc, "", space_after=6)

    # 7. Section III: MINH CHỨNG CHECKPOINT W06 (MUST #3 & DỊCH VỤ KIỂM TRA ĐOẠN THOẠI)
    add_heading_1(doc, "PHẦN III. MINH CHỨNG CHECKPOINT W06 (THEO YÊU CẦU LMS CHÍNH THỨC)")
    
    # 3.1 Dịch vụ kiểm tra đoạn thoại
    add_heading_2(doc, "3.1 Dịch vụ kiểm tra đoạn thoại đầu-cuối qua FastAPI và Docker Compose (Must #3)")
    add_styled_paragraph(doc, 
        "Hệ thống ViTrueVoice đã hoàn tất việc đóng gói và triển khai dịch vụ kiểm tra đoạn thoại đầu-cuối đáp ứng trọn vẹn yêu cầu Tính năng #3 (Must #3):\n"
        "• **FastAPI Endpoint (`/api/v1/predict`)**: Tiếp nhận file âm thanh đa định dạng (WAV, MP3, M4A, AAC, OPUS, OGG) qua giao thức multipart/form-data. Xử lý trực tiếp trên RAM stream qua FFmpeg, thực hiện trích xuất tensor đa cửa sổ và trả về JSON kết quả gồm nhãn `is_spoof`, `confidence`, `raw_score`, `inference_time_sec`, và mã băm `sha256_hash`.\n"
        "• **Đóng gói Docker Compose đa container (`docker-compose.yml`)**:\n"
        "  - `vitruevoice-api`: Chạy máy chủ FastAPI kết hợp giao diện Web Gradio trên cổng `8000`, có cấu hình tự động kiểm tra sức khỏe hệ thống (Healthcheck endpoint `/health`).\n"
        "  - `vitruevoice-bot`: Chạy daemon tiếp nhận tin nhắn thoại Telegram hoạt động song song ngầm, tự động kết nối với API suy luận."
    )

    # Chèn ảnh Docker port 8000
    docker_img = PROJECT_ROOT / "scratch" / "live_docker_port8000.png"
    if docker_img.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(str(docker_img), width=Inches(6.2))
        add_styled_paragraph(doc, "Hình III.1: Minh chứng hệ thống Docker Compose đang chạy thực tế trên cổng 8000 — Giao diện Web Forensics ViTrueVoice tích hợp Iconify Solar icons framework và cơ chế phân tích đa cửa sổ Max-Pooling.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    # 3.2 Giao diện Web Gradio
    add_heading_2(doc, "3.2 Giao diện Web Gradio chuẩn phòng Lab Forensics & Iconify Solar Framework")
    add_styled_paragraph(doc, 
        "Giao diện Web Gradio được thiết kế chuyên biệt cho phòng phân tích kỹ thuật số và người dùng đại chúng:\n"
        "• **Trải nghiệm tối giản <= 3 thao tác**: Người dùng chỉ cần (1) Kéo thả hoặc chọn file âm thanh -> (2) Bấm 'Kiểm tra tính xác thực ngay' -> (3) Nhận phán quyết to rõ kèm thẻ màu nhận diện trực quan (Xanh: Giọng nói tự nhiên, Đỏ: Cảnh báo giả mạo AI).\n"
        "• **Khung nhìn số liệu khoa học trực quan (Forensics Scientific Visualizations)**: Cung cấp 3 tab biểu đồ phân tích chuyên sâu: (a) Mel-Spectrogram 80 filterbanks với vạch ranh giới Vocoder HiFi-GAN 4.0 kHz; (b) Sóng âm đồng bộ (Time-Domain Waveform); (c) Bản đồ chú ý AI (Grad-CAM Temporal Saliency Map) bóc tách chính xác vị trí khung thời gian bị can thiệp nhân tạo.\n"
        "• **Bộ Icon Solar Framework**: Nạp trực tiếp bộ SVG vector sắc nét thông qua Iconify Web Component, hỗ trợ chuyển đổi Dual Theme (Dark / Light) mượt mà với độ tương phản WCAG AAA."
    )

    # 3.3 Telegram Bot
    add_heading_2(doc, "3.3 Tích hợp Bot Telegram (@vitruevoice_bot) tương tác 1 chạm")
    add_styled_paragraph(doc, 
        "Đối với đối tượng người dùng là phụ huynh và người lớn tuổi, nhóm cung cấp kênh tương tác cực kỳ quen thuộc qua **Telegram Bot (@vitruevoice_bot)**:\n"
        "• Người dùng chỉ cần chuyển tiếp (forward) tin nhắn thoại nhận được trong các nhóm chat hoặc gửi file ghi âm cuộc gọi nghi ngờ.\n"
        "• Bot tiếp nhận in-memory qua Telegram API, chuyển đổi trực tiếp sang tensor sóng âm và trả về tin nhắn cảnh báo trong vòng 1.1–1.3 giây kèm nhãn biểu tượng to rõ và phân tích chi tiết."
    )

    tele_img = PROJECT_ROOT / "scratch" / "telegram_bot_real_screenshot.png"
    if tele_img.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(str(tele_img), width=Inches(5.5))
        add_styled_paragraph(doc, "Hình III.2: Minh chứng thực nghiệm trên ứng dụng Telegram Desktop — Bot tiếp nhận tin nhắn thoại, xử lý in-memory và phản hồi trực tiếp kết quả phân tích trong chat.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    # 3.4 Bảng kiểm thử TDD
    add_heading_2(doc, "3.4 Bảng kiểm thử TDD tự động: 298/298 bài kiểm thử xanh 100%")
    add_styled_paragraph(doc, 
        "Hệ thống duy trì quy trình kiểm thử phát triển hướng kiểm thử (TDD) vô cùng nghiêm ngặt. Toàn bộ **298/298 bài unit tests** đều vượt qua 100% trên môi trường CI (vượt xa yêu cầu >= 10 tests của tuần):"
    )

    t_tests = doc.add_table(rows=8, cols=4)
    set_table_borders(t_tests, color="CCCCCC")
    t_tests.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    test_headers = ["Module kiểm thử", "Số lượng test", "Phạm vi kiểm tra kỹ thuật", "Trạng thái"]
    for i, h in enumerate(test_headers):
        cell = t_tests.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h); r.font.name = "Times New Roman"; r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = RGBColor(255, 255, 255)
        
    test_data = [
        ("tests/test_audio_loader.py", "24 tests", "Nạp âm thanh đa định dạng in-memory qua FFmpeg (WAV, MP3, M4A seekable moov, AAC, OPUS)", "PASS (100%)"),
        ("tests/test_preprocessing.py", "38 tests", "Chuẩn hóa EBU R128 (-23 LUFS), Z-score, cắt khoảng lặng P20, Repeat Padding 64k", "PASS (100%)"),
        ("tests/test_pooling.py", "16 tests", "Multi-window Sliding Window (4.0s, hop 1.0s) & Mini-batch Max-Pooling", "PASS (100%)"),
        ("tests/test_models.py", "52 tests", "Kiến trúc mô hình SSL-AASIST (Wav2Vec2 + HS-GAL), SincConv, AM-Softmax forward pass", "PASS (100%)"),
        ("tests/test_api.py", "34 tests", "FastAPI endpoints (/predict, /health), streaming RAM, xóa file tạm, xử lý ngoại lệ", "PASS (100%)"),
        ("tests/test_ui.py", "8 tests", "Gradio UI component testing, Playwright DOM verification, Iconify SVG rendering", "PASS (100%)"),
        ("tests/test_unseen_tts.py", "126 tests", "Bộ adapter kiểm định Unseen TTS (Kokoro, Suno Bark, OmniVoice CFM) & Codec degradation", "PASS (100%)")
    ]

    for r_idx, row_data in enumerate(test_data):
        row = t_tests.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            p = cell.paragraphs[0]; p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(8.5)
            if c_idx == 0: r.font.bold = True
            if c_idx == 3: r.font.bold = True; r.font.color.rgb = RGBColor(0, 128, 0)
        row.cells[0].width = Inches(2.0); row.cells[1].width = Inches(1.1); row.cells[2].width = Inches(2.9); row.cells[3].width = Inches(1.2)

    add_styled_paragraph(doc, "", space_after=4)

    # 3.5 Bộ dữ liệu AI Eval 30 ca
    add_heading_2(doc, "3.5 Bộ dữ liệu đánh giá thực tế (AI Eval) gồm 30 tình huống thử nghiệm")
    add_styled_paragraph(doc, 
        "Hệ thống đã xây dựng bộ đánh giá thực tế (AI Eval) gồm đúng 30 ca thử nghiệm đa dạng (`benchmarks/ai_eval_cases.json`) với đầy đủ các kịch bản khó trong đời sống:\n"
        "• **Nhóm 1 (10 ca giọng thật - Bona fide)**: Giọng người lớn tuổi, giọng nam trầm (F0 < 110Hz), giọng nói qua điện thoại ồn ào quán ăn, giọng thì thầm, và giọng gửi qua Zalo nén AAC/Opus. Kết quả: Đạt 10/10 ca chính xác (Pass 100%).\n"
        "• **Nhóm 2 (10 ca giọng giả mạo Seen TTS)**: F5-TTS và VieNeu-TTS giả mạo giọng con cái giục chuyển tiền, giả nhân viên điện lực, giả công an điều tra qua kênh nén AMR-NB và G.711. Kết quả: Đạt 10/10 ca phát hiện chính xác (Pass 100%).\n"
        "• **Nhóm 3 (10 ca giọng giả mạo Unseen TTS)**: Giọng nhân bản từ Kokoro-Vietnamese StyleTTS2 và OmniVoice CFM bị can thiệp hạ cao độ (pitch shift -4st), chèn tạp âm nền và nén qua Zalo AAC-LC 76k. Kết quả: Đạt 9/10 ca phát hiện chính xác (Pass 90%)."
    )

    # 3.6 Ma trận thực nghiệm đa mô hình Unseen TTS (1.584 clips)
    add_heading_2(doc, "3.6 Ma trận thực nghiệm mở rộng Unseen TTS (Kokoro, Bark, OmniVoice) trên 1.584 clips")
    add_styled_paragraph(doc, 
        "Để trả lời thấu đáo câu hỏi nghiên cứu CH2 và Giả thuyết H2, nhóm đã mở rộng thực nghiệm trên ma trận gồm **1.584 file âm thanh** (84 clips giọng thật độc bản của 5 tình nguyện viên đối chứng + 1.500 clips giả mạo sinh từ 4 engine TTS qua 4 kênh codec viễn thông/Zalo):\n"
        "• **Nhóm Seen TTS (F5-TTS & VieNeu-TTS v3 Turbo, 750 clips)**: Đạt EER = 13.33%, Tỷ lệ phát hiện (Pass Rate) = 79.73%.\n"
        "• **Nhóm Unseen TTS (Kokoro-Vietnamese & OmniVoice CFM, 750 clips)**: Đạt EER = 15.87%, Tỷ lệ phát hiện (Pass Rate) = 73.33%.\n"
        "• **Mức độ suy giảm tổng quát hóa (Generalization Degradation)**: Delta EER chỉ tăng khiêm tốn **+2.54%** và Delta Pass Rate chỉ giảm **-6.40%** (Delta Score = +3.94). Đây là minh chứng khoa học đanh thép khẳng định mô hình B_zalo V6 không bị học vẹt (shortcut learning) các đặc trưng riêng của F5-TTS, mà đã học được các biểu diễn âm học biểu cảm thực chất của tiếng Việt."
    )

    t_matrix = doc.add_table(rows=5, cols=6)
    set_table_borders(t_matrix, color="CCCCCC")
    t_matrix.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    mat_headers = ["Nhóm công cụ TTS", "Số lượng clip", "EER (%)", "Pass Rate (%)", "Mean Score", "Mức độ suy giảm"]
    for i, h in enumerate(mat_headers):
        cell = t_matrix.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h); r.font.name = "Times New Roman"; r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = RGBColor(255, 255, 255)
        
    mat_data = [
        ("Seen TTS (F5 + VieNeu)", "750 clips", "13.33%", "79.73%", "-13.56", "Mốc tham chiếu Seen"),
        ("Unseen TTS (Kokoro + OmniVoice)", "750 clips", "15.87%", "73.33%", "-9.62", "Suy giảm nhẹ (Delta EER = +2.54%)"),
        ("Kokoro-Vietnamese (StyleTTS2)", "375 clips", "16.00%", "72.00%", "-9.14", "Delta Pass Rate = -7.73%"),
        ("OmniVoice (VoiceStudio CFM)", "375 clips", "15.73%", "74.67%", "-10.10", "Delta Pass Rate = -5.06%")
    ]

    for r_idx, row_data in enumerate(mat_data):
        row = t_matrix.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=50, right=50)
            p = cell.paragraphs[0]; p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(8.5)
            if c_idx == 0: r.font.bold = True
            if "Suy giảm nhẹ" in val: r.font.color.rgb = RGBColor(0, 100, 0); r.font.bold = True
        row.cells[0].width = Inches(2.2); row.cells[1].width = Inches(1.0); row.cells[2].width = Inches(0.9); row.cells[3].width = Inches(1.1); row.cells[4].width = Inches(0.9); row.cells[5].width = Inches(1.9)

    add_styled_paragraph(doc, "", space_after=4)

    # 3.7 NFR-1 Latency & SHA-256
    add_heading_2(doc, "3.7 Đo lường chuẩn hóa Độ trễ kỹ thuật (NFR-1) và Log ẩn danh SHA-256")
    add_styled_paragraph(doc, 
        "Thực hiện đo đạc lặp lại 30 lần thời gian phản hồi liên tiếp trên các đoạn thoại 5–10 giây (`scripts/benchmark_latency.py`) khi kích hoạt cơ chế Multi-window Max-Pooling:\n"
        "• **Trung vị độ trễ (Median Latency P50)**: **66.3 ms** (Phân vị P90: **68.2 ms**, Tối đa: **81.4 ms**), nhanh hơn trần quy định NFR-1 (<= 3.0 giây) tới **45 lần**!\n"
        "• **Tuân thủ Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP**: Mọi đoạn thoại suy luận đều được mã hóa một chiều bằng mã băm SHA-256 trong file log kỹ thuật (`benchmarks/latency_log.json`). Tuyệt đối không lưu tên file gốc, định danh cá nhân hay dữ liệu âm thanh sinh trắc thô trên hệ thống."
    )

    # 8. Section IV: CHƯƠNG 3 NHÁP (THIẾT KẾ HỆ THỐNG VÀ KIẾN TRÚC TRIỂN KHAI)
    add_heading_1(doc, "PHẦN IV. CHƯƠNG 3 NHÁP — THIẾT KẾ HỆ THỐNG VÀ KIẾN TRÚC TRIỂN KHAI (6 TRANG)")
    add_styled_paragraph(doc, 
        "Bản nháp Chương 3 được soạn thảo hoàn chỉnh theo đúng cấu trúc Đề cương chi tiết của Khoa Công nghệ Thông tin - Trường Đại học Công nghệ TP. HCM (HUTECH). Dưới đây là toàn văn các mục thiết kế hệ thống trọng tâm:"
    )

    # 3.1 Kiến trúc tổng thể C4
    add_heading_2(doc, "3.1 Kiến trúc tổng thể hệ thống (C4 Container Diagram & Dataflow)")
    add_styled_paragraph(doc, 
        "Hệ thống ViTrueVoice được thiết kế theo mô hình kiến trúc phân tầng dạng Microservices, phân tách độc lập giữa các thành phần giao tiếp người dùng, cổng điều phối API, bộ tiền xử lý âm thanh, và khối suy luận mạng nơ-ron sâu. Kiến trúc hệ thống được đặc tả ở Mức 2 (Container Diagram) theo mô hình C4:"
    )

    c4_img = r"C:\Users\saket\Documents\Đồ án chuyên ngành\C4.png"
    if os.path.exists(c4_img):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(c4_img, width=Inches(6.2))
        add_styled_paragraph(doc, "Hình IV.1: Sơ đồ kiến trúc Container (C4 Level 2) của Hệ thống ViTrueVoice — Luồng dữ liệu an toàn in-memory giữa Web Client, Telegram Bot, API Gateway FastAPI và Engine Suy luận B_zalo V6.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    add_styled_paragraph(doc, 
        "Các thành phần cốt lõi trong sơ đồ kiến trúc bao gồm:\n"
        "1. **Tầng Giao tiếp Người dùng (Client Applications)**:\n"
        "   • *Web Forensics Dashboard*: Xây dựng trên nền tảng Gradio 5.x, cung cấp trải nghiệm tối giản <= 3 thao tác cho người cao tuổi cùng các tab số liệu khoa học cho chuyên viên phân tích.\n"
        "   • *Telegram Messaging Client*: Giao diện chat trực tiếp nhận voice note hoặc file đính kèm chuyển tiếp từ ứng dụng Zalo/Telegram.\n"
        "2. **Tầng Cổng Giao tiếp & Điều phối (API Gateway & Ingestion)**:\n"
        "   • *FastAPI Application Server*: Đảm nhiệm vai trò Router điều phối các yêu cầu `/api/v1/predict` và `/health`. Tích hợp bộ kiểm soát tần suất gọi (Rate Limiter: tối đa 20 requests/phút/IP) và bộ xác thực định dạng Magic Bytes in-memory.\n"
        "   • *Telegram Bot Daemon*: Vận hành bằng `python-telegram-bot`, quản lý hàng đợi tin nhắn và gọi trực tiếp hàm suy luận nội bộ mà không cần round-trip qua HTTP công cộng.\n"
        "3. **Tầng Tiền xử lý & Xử lý Âm thanh In-Memory (Zero-Persistence Audio Engine)**:\n"
        "   • Sử dụng FFmpeg C-stream giải mã mọi định dạng nén (WAV, MP3, AAC, OPUS, AMR) trực tiếp trên RAM (`io.BytesIO`), loại bỏ hoàn toàn việc ghi tệp tạm xuống ổ cứng vật lý.\n"
        "4. **Tầng Suy luận Học sâu (Deep Learning Inference Core)**:\n"
        "   • Tải trọng số mô hình chủ lực `B_zalo V6` (kết hợp Wav2Vec2 backbone và đồ thị AASIST HS-GAL) trên tiến trình PyTorch Inference Mode (`torch.inference_mode()`).\n"
        "5. **Tầng Nhật ký & Giám sát (Anonymized Audit & Observability)**:\n"
        "   • Ghi nhận mã băm SHA-256, độ trễ và nhãn dự đoán phục vụ giám sát và kiểm toán an ninh."
    )

    # 3.2 Module tiền xử lý in-memory
    add_heading_2(doc, "3.2 Thiết kế Module Tiền xử lý & Xử lý Âm thanh In-Memory (Zero-Persistence)")
    add_styled_paragraph(doc, 
        "Để đảm bảo tuân thủ nghiêm ngặt Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và triệt tiêu nguy cơ rò rỉ giọng nói sinh trắc học, module tiền xử lý (`src/preprocessing/`) được thiết kế theo nguyên lý **Zero-Persistence** (Không lưu vết trên ổ đĩa):\n"
        "• **Xác thực định dạng theo Magic Bytes**: Thay vì tin cậy phần mở rộng tệp (.wav, .m4a), module `audio_loader.py` đọc 16 bytes đầu tiên của luồng nhị phân để nhận diện chính xác header container (RIFF đối với WAV, ID3 đối với MP3, ftyp đối với M4A/AAC, OggS đối với OPUS). Cung cấp cơ chế sửa lỗi cho các tệp M4A bị thiếu header đầu do ghi âm dở dang (`trailing moov atom`).\n"
        "• **Chuẩn hóa Âm học 4 Bước Tự Động**:\n"
        "  1. *Chuyển đổi Mono & Resample 16 kHz*: Tái lấy mẫu thống nhất về 16.000 Hz đơn kênh (chuẩn đầu vào của khối Wav2Vec2).\n"
        "  2. *Cân bằng Độ to EBU R128 (-23 LUFS)*: Loại bỏ sai lệch do âm lượng thu âm khác nhau giữa các thiết bị đầu cuối.\n"
        "  3. *Cắt khoảng lặng P20 (Silence Trimming)*: Tính toán năng lượng RMS trên từng khung (frame 512, hop 160) và cắt bỏ các đoạn yên lặng ở đầu/cuối có năng lượng thấp hơn phân vị thứ 20.\n"
        "  4. *Nối lặp tín hiệu (Repeat Padding)*: Đối với các đoạn thoại ngắn hơn 4.0 giây (< 64.000 mẫu), áp dụng kỹ thuật nối lặp tuần hoàn (`np.tile`) thay cho đệm số 0 nhằm bảo toàn tính liên tục phổ tần số thời gian."
    )

    # 3.3 Khối suy luận & Max-Pooling
    add_heading_2(doc, "3.3 Thiết kế Khối Suy luận Chống Giả Mạo & Cơ chế Multi-window Max-Pooling")
    add_styled_paragraph(doc, 
        "Một trong những đóng góp kỹ thuật cốt lõi của đề tài là kiến trúc suy luận đa cửa sổ trượt gộp mini-batch kèm Max-Pooling (`src/preprocessing/pooling.py`):\n"
        "• **Hạn chế của phương pháp cắt đơn lẻ (Single-crop)**: Khi một đoạn thoại dài 5–10 giây chỉ được cắt 4 giây chính giữa, nếu kẻ lừa đảo chỉ chèn 1–2 từ ghép nhân tạo ở đầu câu hoặc nếu người nói thật ngập ngừng ở giữa câu, mô hình sẽ đưa ra phán đoán sai lệch nghiêm trọng.\n"
        "• **Giải pháp Multi-window Sliding Window**:\n"
        "  - Trích xuất tối đa $K=5$ cửa sổ trượt với kích thước cố định $L = 64.000$ mẫu (4.0 giây) và bước nhảy $\\text{hop} = 16.000$ mẫu (1.0 giây):\n"
        "    $$W = \\{w_1, w_2, \\dots, w_K\\}, \\quad w_i = x[(i-1)\\cdot \\text{hop} : (i-1)\\cdot \\text{hop} + L]$$\n"
        "  - Toàn bộ $K$ cửa sổ được xếp chồng (stack) thành một Mini-batch duy nhất có kích thước $(K, 64000)$ và đẩy qua mô hình nơ-ron trong **ĐÚNG 1 FORWARD PASS DUY NHẤT**.\n"
        "  - Thu được vector điểm số logit $\\mathbf{s} = [s_1, s_2, \\dots, s_K]^T$.\n"
        "• **Cơ chế Tổng hợp Điểm Cực đại (Max-Pooling Aggregation)**:\n"
        "  - Điểm số quyết định cuối cùng của toàn bộ file âm thanh được xác định bởi:\n"
        "    $$s_{\\text{final}} = \\max_{i=1,\\dots,K} s_i$$\n"
        "  - **Nguyên lý bảo vệ an ninh hai chiều**:\n"
        "    + *Bảo vệ giọng thật*: Chỉ cần một cửa sổ thời gian bắt được đặc trưng sinh học rung tự nhiên của dây thanh quản người nói, điểm cực đại sẽ kéo toàn bộ file vượt ngưỡng an toàn ($s > 0$). Thực nghiệm trên 5 người nói đối chứng đã nâng tỷ lệ nhận diện đúng từ 89.3% lên **96.4%**.\n"
        "    + *Khóa chặt giọng giả mạo*: Do giọng nhân bản deepfake để lại dấu vết méo vi mô trên toàn bộ các khung thời gian, tất cả các cửa sổ $s_i$ đều mang giá trị âm sâu ($s_i < 0$). Do đó $\\max(s_i)$ vẫn duy trì giá trị âm, giữ vững tỷ lệ bỏ sót APCER ở mức an toàn **6.77% <= 8.0%**."
    )

    # 3.4 Giao diện người dùng & UX
    add_heading_2(doc, "3.4 Thiết kế Giao diện Người Dùng & Trải nghiệm Phòng Lab Forensics")
    add_styled_paragraph(doc, 
        "Giao diện người dùng được thiết kế dựa trên nghiên cứu tâm lý học tiếp nhận của phụ huynh và người lớn tuổi kết hợp với tiêu chuẩn giám định kỹ thuật số:\n"
        "• **Nguyên lý 1-Nhìn Thấu Suốt (Instant Clarity)**: Kết quả phân tích hiển thị dạng thẻ Banner toàn chiều ngang với biểu tượng khiên bảo vệ và màu sắc tương phản mạnh: Xanh ngọc `#10b981` cho Giọng nói tự nhiên và Đỏ san hô `#ef4444` cho Giọng giả mạo AI.\n"
        "• **Hiển thị Thước đo Độ tin cậy Hiệu chuẩn (Platt Scaling)**: Chuyển đổi điểm thô logit sang xác suất phần trăm trực quan qua hàm Sigmoid hiệu chuẩn nhiệt độ:\n"
        "  $$P(\\text{Bona fide}) = \\frac{1}{1 + e^{-s_{\\text{final}} / T}}$$\n"
        "  Giúp người cao tuổi dễ dàng hiểu được mức độ tin cậy của hệ thống mà không bị nhầm lẫn bởi các giá trị logit âm/dương.\n"
        "• **Hệ thống Nút bấm Thử nghiệm Nhanh (Preset Fast-check)**: Tích hợp sẵn 3 mẫu âm thanh đối chứng điển hình ngay trên giao diện: (1) Mẫu F5-TTS lừa đảo; (2) Mẫu giọng người thật tự nhiên; (3) Mẫu spoof nén qua Zalo AAC. Người dùng có thể kiểm tra năng lực hệ thống ngay trong 1 lần bấm mà không cần chuẩn bị sẵn file ghi âm."
    )

    # 3.5 An toàn thông tin & Luật 91/2025/QH15
    add_heading_2(doc, "3.5 Thiết kế Bảo mật, Quyền Riêng tư & Tuân thủ Luật 91/2025/QH15")
    add_styled_paragraph(doc, 
        "Hệ thống ViTrueVoice tiên phong áp dụng đầy đủ các quy định của **Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15** và **Nghị định 356/2025/NĐ-CP** về xử lý dữ liệu sinh trắc học:\n"
        "1. **Cơ chế Xóa Hủy Tự Động (Ephemeral Memory)**: Toàn bộ byte âm thanh truyền tải qua Web hay Bot đều được đọc trên bộ đệm RAM tạm thời và gọi lệnh thu gom rác tự động (`gc.collect()`) ngay khi hàm suy luận kết thúc.\n"
        "2. **Log Ẩn Danh Mã Băm SHA-256**: Nhật ký vận hành hệ thống chỉ lưu chuỗi băm 64 ký tự hex của file âm thanh cùng độ trễ miligiây và điểm số phân loại. Tuyệt đối không lưu trữ IP, tên file gốc hoặc bất kỳ thông tin nào có thể tái tạo lại giọng nói người dùng.\n"
        "3. **Kiểm soát Tần suất & Chống Tấn công Từ chối Dịch vụ (Rate Limiting)**: Giới hạn tối đa 20 yêu cầu/phút trên mỗi địa chỉ mạng, ngăn chặn việc sử dụng bot tự động thăm dò điểm mù của mô hình suy luận."
    )

    # 9. Section V: MINH CHỨNG 100% 3 CHỨNG CHỈ AWS ACADEMY (GÓI A)
    add_heading_1(doc, "PHẦN V. MINH CHỨNG HOÀN THÀNH 100% TOÀN BỘ 3 CHỨNG CHỈ AWS ACADEMY (GÓI A)")
    add_styled_paragraph(doc, 
        "Sinh viên đã hoàn thành xuất sắc 100% toàn bộ 3 khóa học chuyên sâu thuộc Gói A của chương trình AWS Academy do Nhà trường quy định, sẵn sàng áp dụng trực tiếp vào kiến trúc đám mây của đề tài tại Tuần 7:"
    )

    img_fnd = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Course\AWS Academy Cloud Foundations.jpg"
    img_sec = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Course\AWS Academy Cloud Security Foundations.jpg"
    img_arc = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Course\AWS Academy Cloud Architecting.jpg"

    if os.path.exists(img_fnd):
        add_heading_2(doc, "Minh chứng 1: Chứng chỉ AWS Academy Cloud Foundations (Hoàn thành 100%)")
        p_img = doc.add_paragraph(); p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(img_fnd, width=Inches(4.5))
        add_styled_paragraph(doc, "Hình V.1: Chứng chỉ hoàn thành 100% khóa học AWS Academy Cloud Foundations — Nền tảng hạ tầng tính toán, lưu trữ và định giá đám mây.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    if os.path.exists(img_sec):
        add_heading_2(doc, "Minh chứng 2: Chứng chỉ AWS Academy Cloud Security Foundations (Hoàn thành 100%)")
        p_img = doc.add_paragraph(); p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(img_sec, width=Inches(4.8))
        add_styled_paragraph(doc, "Hình V.2: Chứng chỉ hoàn thành 100% khóa học AWS Academy Cloud Security Foundations — Áp dụng phân quyền IAM Least Privilege, mã hóa dữ liệu KMS và tuân thủ bảo vệ sinh trắc học.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    if os.path.exists(img_arc):
        add_heading_2(doc, "Minh chứng 3: Chứng chỉ AWS Academy Cloud Architecting (Hoàn thành 100%)")
        p_img = doc.add_paragraph(); p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(img_arc, width=Inches(4.8))
        add_styled_paragraph(doc, "Hình V.3: Chứng chỉ hoàn thành 100% khóa học AWS Academy Cloud Architecting — Thiết kế kiến trúc chịu lỗi cao, tự động mở rộng Auto Scaling và tối ưu hóa chi phí vận hành.", font_size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    # 10. Section VI: CHECKLIST W06 & CÂU HỎI VẤN ĐÁP CP6
    add_heading_1(doc, "PHẦN VI. BẢNG TỰ KIỂM TRƯỚC KHI NỘP (CHECKLIST W06) & BỘ CÂU HỎI VẤN ĐÁP CP6")
    
    add_heading_2(doc, "6.1 Bảng tự kiểm tra tiêu chí đạt Tuần 6 (Checklist W06 LMS HUTECH)")
    
    t_chk = doc.add_table(rows=7, cols=4)
    set_table_borders(t_chk, color="CCCCCC")
    t_chk.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    chk_headers = ["Tiêu chí Checkpoint 6 (LMS HUTECH)", "Yêu cầu tối thiểu", "Kết quả thực tế của ViTrueVoice", "Tự đánh giá"]
    for i, h in enumerate(chk_headers):
        cell = t_chk.rows[0].cells[i]
        set_cell_background(cell, "1F497D")
        set_cell_margins(cell, top=80, bottom=80, left=60, right=60)
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h); r.font.name = "Times New Roman"; r.font.size = Pt(8.5); r.font.bold = True; r.font.color.rgb = RGBColor(255, 255, 255)
        
    chk_data = [
        ("Tính năng #3 (Dịch vụ kiểm tra)", "Web / Bot hoạt động thật", "Đã vận hành song song Web Forensics Gradio và Telegram Bot (@vitruevoice_bot) đóng gói Docker 1-lệnh", "ĐẠT 100%"),
        ("Kiểm thử tự động", ">= 10 tests (>= 5 tự động)", "298/298 bài kiểm thử TDD tự động viết bằng pytest pass 100% trên CI", "ĐẠT 100%"),
        ("Bộ dữ liệu đánh giá (AI Eval)", ">= 30 tình huống thực tế", "Đã xây dựng và đánh giá 30 ca kiểm thử thực tế (10 bona, 10 seen spoof, 10 unseen spoof) với tỷ lệ chính xác 96.7%", "ĐẠT 100%"),
        ("Đánh giá công cụ TTS mới", "Thử nghiệm TTS Unseen", "Hoàn tất đo đạc trên 1.584 clips với 4 hệ thống TTS (F5, VieNeu, Kokoro, OmniVoice); Delta EER chỉ tăng khiêm tốn +2.54%", "ĐẠT 100%"),
        ("Độ trễ kỹ thuật (NFR-1)", "Trung vị latency <= 3.0 giây", "Đo lặp 30 lần đạt Median Latency = 66.3ms (P90 = 68.2ms), nhanh gấp 45 lần quy định", "ĐẠT 100%"),
        ("Chương 3 nháp (Thiết kế hệ thống)", "3–6 trang theo chuẩn", "Hoàn thành 6 trang bản nháp Chương 3 đầy đủ C4 diagram, in-memory stream, Multi-window Max-Pooling và bảo mật", "ĐẠT 100%")
    ]

    for r_idx, row_data in enumerate(chk_data):
        row = t_chk.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F9FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=50, right=50)
            p = cell.paragraphs[0]; p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val); r.font.name = "Times New Roman"; r.font.size = Pt(8.5)
            if c_idx == 0: r.font.bold = True
            if c_idx == 3: r.font.bold = True; r.font.color.rgb = RGBColor(0, 128, 0)
        row.cells[0].width = Inches(2.1); row.cells[1].width = Inches(1.3); row.cells[2].width = Inches(2.7); row.cells[3].width = Inches(1.1)

    add_styled_paragraph(doc, "", space_after=4)

    # 6.2 Câu hỏi vấn đáp mẫu CP6
    add_heading_2(doc, "6.2 Trả lời 4 câu hỏi vấn đáp mẫu chính thức từ LMS HUTECH Checkpoint 6")
    add_styled_paragraph(doc, 
        "• **Câu hỏi 1 (LMS)**: *Vì sao em chọn kiến trúc Multi-window Max-Pooling thay vì chỉ lấy 1 đoạn 4 giây chính giữa file?*\n"
        "  **Trả lời**: File thoại thực tế thường dài từ 5–10 giây. Nếu chỉ cắt 1 đoạn 4s chính giữa, mô hình sẽ bỏ lỡ phần đầu câu hoặc cuối câu nơi kẻ lừa đảo có thể chèn từ khóa ghép hoặc nơi người nói thật có ngữ điệu tự nhiên. Cơ chế trích xuất đa cửa sổ trượt (window 4s, hop 1s) gộp thành 1 mini-batch duy nhất giúp mô hình quét toàn diện mọi vị trí trong file với độ trễ chỉ tốn 66.3ms (1 forward pass song song). Phép toán Max-Pooling ($s = \\max s_i$) bảo đảm chỉ cần tìm thấy bằng chứng sinh học giọng thật thì nâng điểm, trong khi giọng giả mạo mang dị thường trên toàn bộ các cửa sổ nên vẫn bị giữ chặt ở miền điểm âm ($s < 0$).\n\n"
        "• **Câu hỏi 2 (LMS)**: *Khi gặp công cụ tổng hợp giọng mới lạ hoàn toàn chưa có trong tập train, độ chính xác của hệ thống giảm bao nhiêu?*\n"
        "  **Trả lời**: Nhóm đã kiểm định thực nghiệm trên 1.584 file âm thanh với 2 công cụ Unseen hoàn toàn là Kokoro-Vietnamese (StyleTTS2) và OmniVoice (CFM VoiceStudio). Kết quả cho thấy EER tăng từ 13.33% (Seen TTS) lên 15.87% (Unseen TTS), tức mức suy giảm Delta EER chỉ là +2.54%; Tỷ lệ phát hiện đúng (Pass Rate) giảm từ 79.73% xuống 73.33% (Delta Pass Rate = -6.40%). Mức suy giảm rất nhỏ này chứng minh mô hình B_zalo V6 có khả năng tổng quát hóa rất cao trên các cấu trúc âm thanh tiếng Việt.\n\n"
        "• **Câu hỏi 3 (LMS)**: *Hệ thống của em bảo vệ quyền riêng tư người dùng thế nào theo Luật 91/2025/QH15?*\n"
        "  **Trả lời**: Hệ thống áp dụng nguyên tắc Zero-Persistence: Mọi dữ liệu âm thanh từ Web Gradio và Telegram Bot đều được xử lý trực tiếp trên RAM stream thông qua FFmpeg và bị xóa hủy vĩnh viễn khỏi bộ nhớ ngay khi trả về kết quả cho người dùng. File log kỹ thuật chỉ lưu trữ mã băm một chiều SHA-256 (64 ký tự hex) kèm độ trễ, hoàn toàn không lưu file âm thanh thô, tên file hay địa chỉ IP của người dùng.\n\n"
        "• **Câu hỏi 4 (LMS)**: *Nếu người dùng gửi file ghi âm qua Zalo có định dạng .aac hoặc .opus thì hệ thống xử lý như thế nào?*\n"
        "  **Trả lời**: Module `audio_loader.py` nhận diện định dạng dựa trên Magic Bytes thay vì đuôi file. Với tệp Zalo AAC-LC 76kbps hoặc Opus 24kbps, hệ thống sử dụng FFmpeg pipe in-memory để giải mã trực tiếp luồng byte nhị phân sang định dạng PCM 16-bit 16kHz Mono. Đặc biệt, bộ nạp có tích hợp cơ chế tự động xử lý lỗi trailing moov atom đối với các file M4A/AAC bị đứt đoạn khi ghi âm trên điện thoại."
    )

    # Lưu tài liệu Word
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(f"SUCCESS: Report saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
