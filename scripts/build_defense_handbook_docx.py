# -*- coding: utf-8 -*-
r"""
Script to build the Comprehensive Technical & Defense Handbook (DOCX & PDF) for ViTrueVoice:
Topic: Phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát
Student: Nguyễn Thành Tài - MSSV: 2380601959 - Lớp: 23DTHD5 - HUTECH
Instructor: TS. Nguyễn Quang Trung

Output destinations:
- C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.docx
- C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.pdf
- C:\Users\saket\Documents\Đồ án chuyên ngành\Content\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.docx
- C:\Users\saket\Documents\Đồ án chuyên ngành\Content\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.pdf
"""

import os
import sys
import shutil
from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from handbook_generator.styles import (
    set_cell_background,
    set_cell_margins,
    set_table_borders,
    add_callout_box,
    add_styled_paragraph,
)
from handbook_generator.global_foundations import add_global_foundations
from handbook_generator.chapters_1_to_3 import add_chapters_1_to_3
from handbook_generator.chapters_4_to_6 import add_chapters_4_to_6
from handbook_generator.chapters_7_to_9 import add_chapters_7_to_9
from handbook_generator.chapters_10_to_12 import add_chapters_10_to_12

OUTPUT_DIR_1 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành")
OUTPUT_DIR_2 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content")

DOCX_NAME = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.docx"
PDF_NAME = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE.pdf"

OUTPUT_DOCX_1 = OUTPUT_DIR_1 / DOCX_NAME
OUTPUT_DOCX_2 = OUTPUT_DIR_2 / DOCX_NAME
OUTPUT_PDF_1 = OUTPUT_DIR_1 / PDF_NAME
OUTPUT_PDF_2 = OUTPUT_DIR_2 / PDF_NAME

def build_document():
    doc = Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # Header / Title Block
    add_styled_paragraph(doc, 
        "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP. HỒ CHÍ MINH (HUTECH)", 
        font_size=12, bold=True, color_rgb=(31, 73, 125), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_styled_paragraph(doc, 
        "KHOA CÔNG NGHỆ THÔNG TIN — CHUYÊN NGÀNH MÁY HỌC VÀ ỨNG DỤNG", 
        font_size=11, bold=True, color_rgb=(100, 100, 100), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=14)

    p_title = add_styled_paragraph(doc, 
        "SỔ TAY TOÀN DIỆN VỀ QUY TRÌNH KỸ THUẬT & THÔNG SỐ CHUYÊN SÂU\nHỆ THỐNG PHÁT HIỆN GIỌNG NÓI GIẢ TIẾNG VIỆT QUA KÊNH THOẠI NÉN DỰA TRÊN HỌC BIỂU DIỄN TỰ GIÁM SÁT (VITRUEVOICE)", 
        font_size=14, bold=True, color_rgb=(192, 0, 0), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)

    add_styled_paragraph(doc, 
        "Tài liệu giải thích từ gốc rễ toán học, xử lý tín hiệu âm thanh (DSP), kiến trúc mạng nơ-ron học sâu (SSL-AASIST), "
        "quy chuẩn kiểm định khoa học (EER, minDCF, ISO/IEC 30107-3) đến cẩm nang 20 câu hỏi phản biện bảo vệ trước Hội đồng chấm Đồ án chuyên ngành.",
        font_size=10.5, italic=True, color_rgb=(80, 80, 80), align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

    # Metadata Table
    meta_info = [
        ("Tên đề tài:", "Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát (ViTrueVoice)"),
        ("Sinh viên thực hiện:", "Nguyễn Thành Tài — MSSV: 2380601959 — Lớp: 23DTHD5"),
        ("Giảng viên hướng dẫn:", "TS. Nguyễn Quang Trung"),
        ("Phiên bản hệ thống:", "v0.4.7 (Dual-Seen Re-Training, SPK_0001 Isolation Verification & Voice_Final Acceptance Export)"),
        ("Công nghệ cốt lõi:", "PyTorch 2.6 CUDA, Wav2Vec 2.0 (Vietnamese 250h), Compact AASIST (HS-GAL), Multi-Window Max-Pooling, Platt Scaling, Docker")
    ]
    t_meta = doc.add_table(rows=len(meta_info), cols=2)
    t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_meta, color="CCCCCC", sz="4")

    for r_idx, (k, v) in enumerate(meta_info):
        row = t_meta.rows[r_idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.7)
        set_cell_background(c0, "F0F4F8")
        set_cell_margins(c0, top=70, bottom=70, left=100, right=100)
        set_cell_margins(c1, top=70, bottom=70, left=100, right=100)
        
        p0 = c0.paragraphs[0]; p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(k); r0.font.name = "Times New Roman"; r0.font.size = Pt(9.5); r0.bold = True; r0.font.color.rgb = RGBColor(31, 73, 125)
        
        p1 = c1.paragraphs[0]; p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v); r1.font.name = "Times New Roman"; r1.font.size = Pt(9.5); r1.font.color.rgb = RGBColor(20, 20, 20)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_callout_box(doc, 
        "Tài liệu này được biên soạn với mục tiêu kép: **(1) Cung cấp kiến thức nền tảng và chuyên sâu** để sinh viên nắm vững từng dòng mã nguồn, từng thông số kỹ thuật và bản chất toán học của hệ thống; **(2) Đóng vai trò là cẩm nang trả lời phản biện hội đồng**, giúp sinh viên tự tin giải thích rõ ràng 'TẠI SAO' lại lựa chọn giải pháp đó thay vì giải pháp khác, số liệu đó lấy từ đâu và ý nghĩa thực tiễn là gì.",
        title="LỜI MỞ ĐẦU VÀ HƯỚNG DẪN ÔN TẬP BẢO VỆ")

    # -------------------------------------------------------------------------
    # PART 1: GLOBAL FOUNDATIONS & SYSTEM BACKBONE
    # -------------------------------------------------------------------------
    add_global_foundations(doc)

    # -------------------------------------------------------------------------
    # PART 2: CHAPTERS 1 TO 3
    # -------------------------------------------------------------------------
    add_chapters_1_to_3(doc)

    # -------------------------------------------------------------------------
    # PART 3: CHAPTERS 4 TO 6
    # -------------------------------------------------------------------------
    add_chapters_4_to_6(doc)

    # -------------------------------------------------------------------------
    # PART 4: CHAPTERS 7 TO 9
    # -------------------------------------------------------------------------
    add_chapters_7_to_9(doc)

    # -------------------------------------------------------------------------
    # PART 5: CHAPTERS 10 TO 12
    # -------------------------------------------------------------------------
    add_chapters_10_to_12(doc)

    # Ensure output directories exist
    OUTPUT_DIR_1.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR_2.mkdir(parents=True, exist_ok=True)

    # Save to Location 1
    doc.save(str(OUTPUT_DOCX_1))
    print(f"[OK] Saved primary DOCX to: {OUTPUT_DOCX_1}")

    # Copy to Location 2
    shutil.copy2(OUTPUT_DOCX_1, OUTPUT_DOCX_2)
    print(f"[OK] Copied secondary DOCX to: {OUTPUT_DOCX_2}")

    # Export PDF using Word COM
    export_pdf(OUTPUT_DOCX_1, OUTPUT_PDF_1, OUTPUT_PDF_2)

def export_pdf(docx_path, pdf_path_1, pdf_path_2):
    """Export DOCX to PDF using Word Application COM interface."""
    import win32com.client
    print("[*] Launching Word COM for high-fidelity PDF export...")
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.SaveAs(str(pdf_path_1.resolve()), FileFormat=17) # 17 is wdFormatPDF
        doc.Close()
        print(f"[OK] Generated primary PDF at: {pdf_path_1} (Size: {pdf_path_1.stat().st_size:,} bytes)")

        shutil.copy2(pdf_path_1, pdf_path_2)
        print(f"[OK] Copied secondary PDF at: {pdf_path_2}")
    except Exception as e:
        print(f"[ERROR] Failed to export PDF via Word COM: {e}")
    finally:
        word.Quit()

if __name__ == "__main__":
    build_document()
