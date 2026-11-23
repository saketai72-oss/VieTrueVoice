# -*- coding: utf-8 -*-
r"""
Script to build the Comprehensive Technical & Defense Handbook v2 (DOCX & PDF) for ViTrueVoice:
Title: SỔ TAY KỸ THUẬT CHUYÊN SÂU TOÀN DIỆN & CẨM NANG PHẢN BIỆN HỘI ĐỒNG — PHIÊN BẢN 2.0 (V2.0)
Topic: Phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát
Student: Nguyễn Thành Tài - MSSV: 2380601959 - Lớp: 23DTHD5 - HUTECH
Instructor: TS. Nguyễn Quang Trung

Output destinations:
- C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.docx
- C:\Users\saket\Documents\Đồ án chuyên ngành\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.pdf
- C:\Users\saket\Documents\Đồ án chuyên ngành\Content\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.docx
- C:\Users\saket\Documents\Đồ án chuyên ngành\Content\SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.pdf
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

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.handbook_generator.styles import (
    set_cell_background,
    set_cell_margins,
    set_table_borders,
    add_callout_box,
    add_styled_paragraph,
)
from scripts.handbook_generator.global_foundations import add_global_foundations
from scripts.handbook_generator.chapters_1_to_3 import add_chapters_1_to_3
from scripts.handbook_generator.chapters_4_to_6 import add_chapters_4_to_6
from scripts.handbook_generator.chapters_7_to_9 import add_chapters_7_to_9
from scripts.handbook_generator.chapters_10_to_12 import add_chapters_10_to_12
from scripts.handbook_generator.chapter_13_inverted import add_chapter_13_inverted

OUTPUT_DIR_1 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành")
OUTPUT_DIR_2 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content")

DOCX_NAME_V2 = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.docx"
PDF_NAME_V2 = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.pdf"

OUTPUT_DOCX_1 = OUTPUT_DIR_1 / DOCX_NAME_V2
OUTPUT_DOCX_2 = OUTPUT_DIR_2 / DOCX_NAME_V2
OUTPUT_PDF_1 = OUTPUT_DIR_1 / PDF_NAME_V2
OUTPUT_PDF_2 = OUTPUT_DIR_2 / PDF_NAME_V2


def build_document_v2():
    doc = Document()

    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Normal Style
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    # Header / Title Block
    add_styled_paragraph(
        doc,
        "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP. HỒ CHÍ MINH (HUTECH)",
        font_size=12,
        bold=True,
        color_rgb=(31, 73, 125),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_styled_paragraph(
        doc,
        "KHOA CÔNG NGHỆ THÔNG TIN — CHUYÊN NGÀNH MÁY HỌC VÀ ỨNG DỤNG",
        font_size=11,
        bold=True,
        color_rgb=(100, 100, 100),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=14,
    )

    add_styled_paragraph(
        doc,
        "SỔ TAY KỸ THUẬT CHUYÊN SÂU TOÀN DIỆN & CẨM NANG PHẢN BIỆN HỘI ĐỒNG — PHIÊN BẢN 2.0 (V2.0)\n"
        "HỆ THỐNG PHÁT HIỆN GIỌNG NÓI GIẢ TIẾNG VIỆT QUA KÊNH THOẠI NÉN DỰA TRÊN HỌC BIỂU DIỄN TỰ GIÁM SÁT (VITRUEVOICE)",
        font_size=14,
        bold=True,
        color_rgb=(192, 0, 0),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=12,
    )

    add_styled_paragraph(
        doc,
        "Tài liệu giải thích từ gốc rễ toán học, xử lý tín hiệu âm thanh (DSP), kiến trúc mạng nơ-ron học sâu (SSL-AASIST), "
        "quy chuẩn kiểm định khoa học (EER, minDCF, ISO/IEC 30107-3), thực nghiệm đối chứng hoán đổi 2 chiều (Inverted Generalization V7 vs V8) "
        "đến cẩm nang 27 câu hỏi phản biện bảo vệ trước Hội đồng chấm Đồ án chuyên ngành.",
        font_size=10.5,
        italic=True,
        color_rgb=(80, 80, 80),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=16,
    )

    # Metadata Table
    meta_info = [
        (
            "Tên đề tài:",
            "Hệ thống phát hiện giọng nói giả tiếng Việt qua kênh thoại nén dựa trên học biểu diễn tự giám sát (ViTrueVoice)",
        ),
        (
            "Sinh viên thực hiện:",
            "Nguyễn Thành Tài — MSSV: 2380601959 — Lớp: 23DTHD5",
        ),
        ("Giảng viên hướng dẫn:", "TS. Nguyễn Quang Trung"),
        (
            "Phiên bản sổ tay:",
            "Phiên bản 2.0 (V2.0) — Cập nhật Thực nghiệm Đối chứng 2 Chiều V7 vs V8, Triệt tiêu Lỗ hổng CFM, và 27 Câu Hỏi Phản Biện",
        ),
        (
            "Phiên bản hệ thống:",
            "v0.9.2 (Inverted Generalization V8, Dense Overlap Asymmetric Veto, Platt Scaling T=16.0 & 362 CI Tests 100% Green)",
        ),
        (
            "Công nghệ cốt lõi:",
            "PyTorch 2.6 CUDA, Wav2Vec 2.0 (Vietnamese 250h), Compact AASIST (HS-GAL), Multi-Window Asymmetric Veto, "
            "Continuous Flow Matching (OmniVoice CFM), VieNeu-TTS v3 Turbo, Platt Scaling, Docker Compose, 362 CI Tests",
        ),
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

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(k)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(9.5)
        r0.bold = True
        r0.font.color.rgb = RGBColor(31, 73, 125)

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(20, 20, 20)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    add_callout_box(
        doc,
        "Sổ tay Phiên bản 2.0 (V2.0) bổ sung trọng tâm học thuật mang tính đột phá: **Chương 13 — Thực nghiệm Đối chứng 2 Chiều "
        "(Inverted Generalization Experiment) giữa mô hình V7 và V8**. Bằng cách hoán đổi hoàn toàn vai trò của Continuous Flow Matching "
        "(OmniVoice CFM) và Discrete Neural Codec (VieNeu-TTS) giữa tập Huấn luyện (Seen) và tập Thẩm định ngoại lai (Unseen), "
        "tài liệu làm sáng tỏ cơ chế toán học triệt tiêu 20% lỗ hổng lọt lưới, phân tích ma trận suy giảm trên 5 kênh thoại nén viễn thông "
        "và bổ sung 5 câu hỏi phản biện chuyên sâu, nâng tổng số câu hỏi bảo vệ lên **27 câu hỏi chuẩn mực**.",
        title="ĐIỂM NÂNG CẤP NỔI BẬT CỦA SỔ TAY PHIÊN BẢN 2.0 (V2.0)",
    )

    # -------------------------------------------------------------------------
    # PART 1: GLOBAL FOUNDATIONS & SYSTEM BACKBONE
    # -------------------------------------------------------------------------
    print("[*] Adding Global Foundations...")
    add_global_foundations(doc)

    # -------------------------------------------------------------------------
    # PART 2: CHAPTERS 1 TO 3
    # -------------------------------------------------------------------------
    print("[*] Adding Chapters 1 to 3...")
    add_chapters_1_to_3(doc)

    # -------------------------------------------------------------------------
    # PART 3: CHAPTERS 4 TO 6
    # -------------------------------------------------------------------------
    print("[*] Adding Chapters 4 to 6...")
    add_chapters_4_to_6(doc)

    # -------------------------------------------------------------------------
    # PART 4: CHAPTERS 7 TO 9
    # -------------------------------------------------------------------------
    print("[*] Adding Chapters 7 to 9...")
    add_chapters_7_to_9(doc)

    # -------------------------------------------------------------------------
    # PART 5: CHAPTERS 10 TO 12
    # -------------------------------------------------------------------------
    print("[*] Adding Chapters 10 to 12...")
    add_chapters_10_to_12(doc)

    # -------------------------------------------------------------------------
    # PART 6: CHAPTER 13 (NEW: INVERTED GENERALIZATION EXPERIMENT V7 vs V8)
    # -------------------------------------------------------------------------
    print("[*] Adding Chapter 13 (Inverted Generalization Experiment)...")
    add_chapter_13_inverted(doc)

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

    # Count statistics
    word_count, paragraph_count, table_count = count_document_stats(OUTPUT_DOCX_1)
    print(f"[STATS] Total Words: {word_count:,} | Paragraphs: {paragraph_count:,} | Tables: {table_count:,}")
    return word_count, paragraph_count, table_count


def count_document_stats(docx_path):
    """Count words, paragraphs, and tables in a docx document."""
    d = Document(str(docx_path))
    p_count = len(d.paragraphs)
    t_count = len(d.tables)
    total_words = 0
    for p in d.paragraphs:
        total_words += len(p.text.split())
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    total_words += len(p.text.split())
    return total_words, p_count, t_count


def export_pdf(docx_path, pdf_path_1, pdf_path_2):
    """Export DOCX to PDF using Word Application COM interface."""
    import win32com.client

    print("[*] Launching Word COM for high-fidelity PDF export...")
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        doc.SaveAs(str(pdf_path_1.resolve()), FileFormat=17)  # 17 is wdFormatPDF
        doc.Close()
        print(
            f"[OK] Generated primary PDF at: {pdf_path_1} (Size: {pdf_path_1.stat().st_size:,} bytes)"
        )

        shutil.copy2(pdf_path_1, pdf_path_2)
        print(f"[OK] Copied secondary PDF at: {pdf_path_2}")
    except Exception as e:
        print(f"[ERROR] Failed to export PDF via Word COM: {e}")
    finally:
        word.Quit()


if __name__ == "__main__":
    build_document_v2()
