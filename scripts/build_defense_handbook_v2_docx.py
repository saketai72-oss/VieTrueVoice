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

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.handbook_generator.chapter_13_inverted import add_chapter_13_inverted  # noqa: E402
from scripts.handbook_generator.chapters_1_to_3 import add_chapters_1_to_3  # noqa: E402
from scripts.handbook_generator.chapters_4_to_6 import add_chapters_4_to_6  # noqa: E402
from scripts.handbook_generator.chapters_7_to_9 import add_chapters_7_to_9  # noqa: E402
from scripts.handbook_generator.chapters_10_to_12 import add_chapters_10_to_12  # noqa: E402
from scripts.handbook_generator.diagrams import generate_all_handbook_diagrams  # noqa: E402
from scripts.handbook_generator.global_foundations import add_global_foundations  # noqa: E402
from scripts.handbook_generator.styles import (  # noqa: E402
    add_callout_box,
    add_styled_paragraph,
    set_cell_background,
    set_cell_margins,
    set_table_borders,
)

OUTPUT_DIR_1 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành")
OUTPUT_DIR_2 = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content")

DOCX_NAME_V2 = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.docx"
PDF_NAME_V2 = "SO_TAY_TOAN_DIEN_KY_THUAT_CHUYEN_SAU_VITRUEVOICE_V2.pdf"

OUTPUT_DOCX_1 = OUTPUT_DIR_1 / DOCX_NAME_V2
OUTPUT_DOCX_2 = OUTPUT_DIR_2 / DOCX_NAME_V2
OUTPUT_PDF_1 = OUTPUT_DIR_1 / PDF_NAME_V2
OUTPUT_PDF_2 = OUTPUT_DIR_2 / PDF_NAME_V2


def build_document_v2():
    """Generate diagrams, build complete v0.9.4 handbook DOCX, export PDF, and print verification stats."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(30, 30, 30)

    tmp_fig_dir = _ROOT / "out" / "_tmp_handbook_figs"
    print("[*] Generating 8 high-resolution (300 DPI) Vietnamese visual diagrams...")
    figs = generate_all_handbook_diagrams(tmp_fig_dir)
    print(f"[OK] Generated {len(figs)} visual figures: {list(figs.keys())}")

    try:
        # Cover / Header Block
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
            "SỔ TAY KỸ THUẬT CHUYÊN SÂU TOÀN DIỆN & CẨM NANG PHẢN BIỆN HỘI ĐỒNG — PHIÊN BẢN 2.0 (CHUẨN v0.9.4)\n"
            "HỆ THỐNG PHÁT HIỆN GIỌNG NÓI GIẢ TIẾNG VIỆT QUA KÊNH THOẠI NÉN DỰA TRÊN HỌC BIỂU DIỄN TỰ GIÁM SÁT (VITRUEVOICE)",
            font_size=13.5,
            bold=True,
            color_rgb=(192, 0, 0),
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_after=10,
        )

        add_styled_paragraph(
            doc,
            "Tài liệu học tập hệ thống từ gốc rễ kiến thức nền tảng trước mỗi quy trình, sơ đồ minh họa trực quan 300 DPI, "
            "công thức toán học gốc Word OMML, hộp giải nghĩa thuật ngữ tức thời ngay dưới từng mục, thực nghiệm đối chứng "
            "hoán đổi hai chiều trên kho đối xứng 1:1 Voice_Final (103.189 tệp) và trọn bộ 27 câu hỏi phản biện bảo vệ trước Hội đồng.",
            font_size=10.5,
            italic=True,
            color_rgb=(80, 80, 80),
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_after=14,
        )

        meta_info = [
            (
                "Tên đề tài:",
                "Hệ thống phát hiện giọng nói giả tiếng Việt hỗ trợ phòng chống lừa đảo mạo danh cuộc gọi và tin nhắn thoại (ViTrueVoice)",
            ),
            (
                "Sinh viên thực hiện:",
                "Nguyễn Thành Tài — MSSV: 2380601959 — Lớp: 23DTHD5",
            ),
            ("Giảng viên hướng dẫn:", "TS. Nguyễn Quang Trung"),
            (
                "Phiên bản sổ tay:",
                "Phiên bản 2.0 (V2.0) — Đồng bộ 100% mô hình v0.9.4 xuyên suốt Toàn cục + Chương 1 đến Chương 13 (27 Câu Phản Biện)",
            ),
            (
                "Phiên bản hệ thống:",
                (
                    "ViTrueVoice v0.9.4 (`out/v0.9.4/best_model.pt`, Symmetric 6.445 OmniVoice CFM, Head-Calibration `head_blend_a0.75`, "
                    "`Consensus Asymmetric Veto`, `Platt Scaling T=16.0`, Docker cục bộ 0 VNĐ chuẩn AWS Gói A, 392/392 CI Tests 100% Green)"
                ),
            ),
            (
                "Kết quả kiểm định chốt:",
                (
                    "Test In-domain (15.980 mẫu / 5 Codecs): EER = 5,63% (Chặn 95,01%) | Unseen VieNeu-TTS (955 mẫu): EER = 12,05% (H2 PASS) | "
                    "5 SPK Độc Lập (1.545 tệp): Bonafide 94,76%, F5 100%, OmniVoice 83,47%, VieNeu 92,53% | Độ trễ: 0,705s–1,101s"
                ),
            ),
        ]
        t_meta = doc.add_table(rows=len(meta_info), cols=2)
        t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(t_meta, color="CCCCCC", sz="4")

        for r_idx, (k, v) in enumerate(meta_info):
            row = t_meta.rows[r_idx]
            c0, c1 = row.cells[0], row.cells[1]
            c0.width = Inches(2.1)
            c1.width = Inches(4.8)
            set_cell_background(c0, "F0F4F8")
            set_cell_margins(c0, top=65, bottom=65, left=100, right=100)
            set_cell_margins(c1, top=65, bottom=65, left=100, right=100)

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
            "Sổ tay Phiên bản 2.0 đã được **đồng bộ toàn diện 100% với mô hình phát hành `ViTrueVoice v0.9.4`** xuyên suốt từ Phần Mở đầu "
            "tới hết Chương 13 (không còn lẫn số liệu hay câu lệnh của các phiên bản cũ). Để giúp sinh viên học chắc từ gốc và phản biện "
            "thuyết phục trước Hội đồng, tài liệu bổ sung đồng loạt 4 trang bị sư phạm:\n"
            "• **Hộp Kiến thức Nền tảng (🧭)** đặt ngay trước mỗi quy trình kỹ thuật giải thích *vì sao cần bước đó* bằng ví dụ đời thực.\n"
            "• **Công thức Toán học gốc Word OMML (📐)** sắc nét 100% (không còn mã LaTeX thô) kèm giải nghĩa từng biến số.\n"
            "• **Sơ đồ Trực quan 300 DPI** minh họa EER/DET, luồng dữ liệu đối xứng, Repeat Padding vs Zero-Padding, SSL-AASIST, Consensus Veto, Platt Scaling, Benchmark và kiến trúc Docker/C4.\n"
            "• **Từ điển Từ viết tắt & Thuật ngữ (📖)** đặt ngay bên dưới mỗi phần tương ứng kèm **27 câu hỏi phản biện chuẩn 3 bước**.",
            title="CẤU TRÚC HỌC TẬP & NÂNG CẤP TOÀN DIỆN CHUẨN v0.9.4 CỦA SỔ TAY V2.0",
        )

        print("[*] Adding Global Foundations...")
        add_global_foundations(doc)

        print("[*] Adding Chapters 1 to 3...")
        add_chapters_1_to_3(doc, figs)

        print("[*] Adding Chapters 4 to 6...")
        add_chapters_4_to_6(doc, figs)

        print("[*] Adding Chapters 7 to 9...")
        add_chapters_7_to_9(doc, figs)

        print("[*] Adding Chapters 10 to 12...")
        add_chapters_10_to_12(doc, figs)

        print("[*] Adding Chapter 13 (Inverted Generalization Experiment v0.9.4)...")
        add_chapter_13_inverted(doc, figs)

        OUTPUT_DIR_1.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR_2.mkdir(parents=True, exist_ok=True)

        doc.save(str(OUTPUT_DOCX_1))
        print(f"[OK] Saved primary DOCX to: {OUTPUT_DOCX_1}")

        shutil.copy2(OUTPUT_DOCX_1, OUTPUT_DOCX_2)
        print(f"[OK] Copied secondary DOCX to: {OUTPUT_DOCX_2}")

        export_pdf(OUTPUT_DOCX_1, OUTPUT_PDF_1, OUTPUT_PDF_2)

        word_count, paragraph_count, table_count, shape_count = count_document_stats(OUTPUT_DOCX_1)
        print(
            f"[STATS] Words: {word_count:,} | Paragraphs: {paragraph_count:,} | "
            f"Tables: {table_count:,} | Embedded Figures: {shape_count}"
        )
        return word_count, paragraph_count, table_count, shape_count
    finally:
        shutil.rmtree(tmp_fig_dir, ignore_errors=True)


def count_document_stats(docx_path):
    """Count words, paragraphs, tables, and embedded inline shapes in a DOCX document."""
    d = Document(str(docx_path))
    p_count = len(d.paragraphs)
    t_count = len(d.tables)
    s_count = len(d.inline_shapes)
    total_words = 0
    for p in d.paragraphs:
        total_words += len(p.text.split())
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    total_words += len(p.text.split())
    return total_words, p_count, t_count, s_count


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
    except (OSError, RuntimeError) as e:
        print(f"[ERROR] Failed to export PDF via Word COM: {e}")
    finally:
        word.Quit()


if __name__ == "__main__":
    build_document_v2()
