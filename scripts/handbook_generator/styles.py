"""
Styling, native Word OMML equation builders, pedagogical boxes, and figure helpers
for the VieTrueVoice v0.9.4 Defense & Study Handbook.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

MATH_NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
)


def set_cell_background(cell, fill_hex: str) -> None:
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top: int = 100, bottom: int = 100, left: int = 140, right: int = 140) -> None:
    """Set inner cell padding in dxa (1 pt = 20 dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tc_pr.append(tc_mar)


def set_table_borders(table, color: str = "D3D3D3", sz: str = "4", val: str = "single") -> None:
    """Set subtle borders for a table."""
    tbl_pr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f"</w:tblBorders>"
    )
    tbl_pr.append(borders)


def _create_card_cell(
    doc,
    bg_color: str,
    left_color: str,
    left_sz: str = "24",
    box_color: str | None = None,
    box_sz: str = "4",
    top_pad: int = 110,
    bottom_pad: int = 110,
    left_pad: int = 150,
    right_pad: int = 150,
):
    """Create a styled single-cell card with left accent border and optional outer hairline borders."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.7)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=top_pad, bottom=bottom_pad, left=left_pad, right=right_pad)

    side_bdr = (
        f'<w:top w:val="single" w:sz="{box_sz}" w:space="0" w:color="{box_color}"/>'
        f'<w:bottom w:val="single" w:sz="{box_sz}" w:space="0" w:color="{box_color}"/>'
        f'<w:right w:val="single" w:sz="{box_sz}" w:space="0" w:color="{box_color}"/>'
        if box_color
        else '<w:top w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>'
    )
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="{left_sz}" w:space="0" w:color="{left_color}"/>'
        f"{side_bdr}"
        f"</w:tcBorders>"
    )
    tc_pr.append(borders)
    return cell


def add_rich_runs(
    paragraph,
    text: str,
    font_size: float = 10.5,
    default_bold: bool = False,
    default_italic: bool = False,
    color_rgb: tuple[int, int, int] = (25, 25, 25),
) -> None:
    """Render inline **bold** and `code` spans cleanly without raw markdown markers."""
    bold_parts = text.split("**")
    for b_idx, b_seg in enumerate(bold_parts):
        if not b_seg:
            continue
        is_bold = (b_idx % 2 == 1) or default_bold
        code_parts = b_seg.split("`")
        for c_idx, c_seg in enumerate(code_parts):
            if not c_seg:
                continue
            is_code = c_idx % 2 == 1
            run = paragraph.add_run(c_seg)
            if is_code:
                run.font.name = "Consolas"
                run.font.size = Pt(max(font_size - 1.0, 8.5))
                run.bold = is_bold
                run.italic = False
                run.font.color.rgb = RGBColor(15, 76, 129)
            else:
                run.font.name = "Times New Roman"
                run.font.size = Pt(font_size)
                run.bold = is_bold
                run.italic = default_italic
                run.font.color.rgb = RGBColor(*color_rgb)


def add_styled_paragraph(
    doc,
    text: str = "",
    font_size: float = 10.5,
    bold: bool = False,
    italic: bool = False,
    color_rgb: tuple[int, int, int] = (25, 25, 25),
    align=WD_ALIGN_PARAGRAPH.LEFT,
    space_before: float = 0,
    space_after: float = 5,
    line_spacing: float = 1.2,
):
    """Add a paragraph supporting **bold** and `code` spans."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        add_rich_runs(p, text, font_size=font_size, default_bold=bold, default_italic=italic, color_rgb=color_rgb)
    return p


def add_bullet_item(
    doc,
    text: str,
    bold_prefix: str = "",
    font_size: float = 10.5,
    space_after: float = 3,
):
    """Add a bullet list item with optional bold navy prefix."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.18
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + ": ")
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(font_size)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(31, 73, 125)
    add_rich_runs(p, text, font_size=font_size, color_rgb=(30, 30, 30))
    return p


def add_callout_box(
    doc,
    text: str,
    title: str = "GHI NHỚ QUAN TRỌNG KHI BẢO VỆ",
    border_color: str = "1F497D",
    bg_color: str = "F2F5F9",
) -> None:
    """Create a highlight callout box for key takeaways or defense tips."""
    cell = _create_card_cell(
        doc,
        bg_color=bg_color,
        left_color=border_color,
        left_sz="24",
        top_pad=120,
        bottom_pad=120,
        left_pad=160,
        right_pad=160,
    )

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.18
    run_t = p.add_run(f"★ {title}:\n")
    run_t.font.name = "Times New Roman"
    run_t.font.size = Pt(10.5)
    run_t.bold = True
    run_t.font.color.rgb = RGBColor(31, 73, 125)
    add_rich_runs(p, text, font_size=10.0, color_rgb=(30, 30, 30))

    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_foundation_primer(
    doc,
    process_name: str,
    why_needed: str,
    real_analogy: str,
    core_points: list[str],
) -> None:
    """
    Pedagogical primer box placed BEFORE entering any technical pipeline/process.
    Explains in plain Vietnamese what foundational knowledge to know first.
    """
    cell = _create_card_cell(
        doc,
        bg_color="FFFBEB",
        left_color="D97706",
        left_sz="24",
        box_color="FDE68A",
        box_sz="4",
    )

    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(4)
    rt = p0.add_run(f"🧭 CẦN NẮM KIẾN THỨC NỀN TẢNG GÌ TRƯỚC QUY TRÌNH: {process_name.upper()}?")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(10.0)
    rt.bold = True
    rt.font.color.rgb = RGBColor(180, 83, 9)

    for prefix_text in (
        f"• **Vì sao cần bước này?** {why_needed}",
        f"• **Ví dụ đời thực dễ hình dung:** {real_analogy}",
        "• **Kiến thức nền tảng cần bổ sung trước khi đọc tiếp:**",
    ):
        p_sec = cell.add_paragraph()
        p_sec.paragraph_format.space_after = Pt(2.5)
        p_sec.paragraph_format.line_spacing = 1.15
        add_rich_runs(p_sec, prefix_text, font_size=9.5, color_rgb=(35, 35, 35))

    for idx, pt_text in enumerate(core_points, 1):
        p_item = cell.add_paragraph()
        p_item.paragraph_format.left_indent = Inches(0.2)
        p_item.paragraph_format.space_after = Pt(2)
        p_item.paragraph_format.line_spacing = 1.15
        add_rich_runs(p_item, f"{idx}. {pt_text}", font_size=9.5, color_rgb=(45, 45, 45))

    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_term_glossary(doc, terms: list[tuple[str, str, str]]) -> None:
    """
    Inline glossary box placed IMMEDIATELY BELOW a section containing acronyms or jargon.
    Each tuple: (acronym_or_term, full_english_or_origin, plain_vietnamese_explanation).
    """
    if not terms:
        return
    cell = _create_card_cell(
        doc,
        bg_color="F0FDFA",
        left_color="0D9488",
        left_sz="20",
        box_color="CCFBF1",
        box_sz="4",
        top_pad=95,
        bottom_pad=95,
        left_pad=140,
        right_pad=140,
    )

    p0 = cell.paragraphs[0]
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(3)
    rt = p0.add_run("📖 GIẢI NGHĨA TỪ VIẾT TẮT & THUẬT NGỮ CHUYÊN NGÀNH VỪA GẶP:")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(9.5)
    rt.bold = True
    rt.font.color.rgb = RGBColor(15, 118, 110)

    for abbr, full_en, desc_vi in terms:
        p_t = cell.add_paragraph()
        p_t.paragraph_format.space_before = Pt(0)
        p_t.paragraph_format.space_after = Pt(2)
        p_t.paragraph_format.line_spacing = 1.15
        header = f"• **{abbr}** (*{full_en}*): " if full_en else f"• **{abbr}**: "
        add_rich_runs(p_t, header + desc_vi, font_size=9.2, color_rgb=(35, 35, 35))

    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_figure(doc, image_path: str | Path, caption_text: str, width_inches: float = 6.1) -> None:
    """Embed an image centered with an italic academic caption underneath."""
    p_path = Path(image_path)
    if not p_path.exists():
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(6)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.add_run().add_picture(str(p_path), width=Inches(width_inches))

    add_styled_paragraph(
        doc,
        caption_text,
        font_size=9.2,
        italic=True,
        color_rgb=(60, 70, 85),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=0,
        space_after=7,
    )


# =========================================================================
# MICROSOFT WORD NATIVE EQUATION (OMML) BUILDERS — ZERO RAW LATEX
# =========================================================================

def omml_r(text: str, normal: bool = False, bold: bool = False) -> str:
    """Create an OMML math run <m:r>. Set normal=True for operators, numbers, function names."""
    esc = xml_escape(text)
    m_rpr = ""
    if normal:
        m_rpr = "<m:rPr><m:nor/></m:rPr>"
    w_bold = "<w:b/>" if bold else ""
    return (
        f"<m:r>{m_rpr}"
        f'<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{w_bold}<w:sz w:val="22"/></w:rPr>'
        f'<m:t xml:space="preserve">{esc}</m:t></m:r>'
    )


def omml_frac(num_xml: str, den_xml: str) -> str:
    """Create an OMML stacked fraction <m:f>."""
    return f"<m:f><m:num>{num_xml}</m:num><m:den>{den_xml}</m:den></m:f>"


def omml_sub(base_xml: str, sub_xml: str) -> str:
    """Create an OMML subscript <m:sSub>."""
    return f"<m:sSub><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub></m:sSub>"


def omml_sup(base_xml: str, sup_xml: str) -> str:
    """Create an OMML superscript <m:sSup>."""
    return f"<m:sSup><m:e>{base_xml}</m:e><m:sup>{sup_xml}</m:sup></m:sSup>"


def omml_subsup(base_xml: str, sub_xml: str, sup_xml: str) -> str:
    """Create an OMML combined subscript + superscript <m:sSubSup>."""
    return f"<m:sSubSup><m:e>{base_xml}</m:e><m:sub>{sub_xml}</m:sub><m:sup>{sup_xml}</m:sup></m:sSubSup>"


def omml_sqrt(body_xml: str) -> str:
    """Create an OMML square root <m:rad>."""
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{body_xml}</m:e></m:rad>'


def omml_delim(body_xml: str, beg: str = "(", end: str = ")") -> str:
    """Create an OMML auto-sized delimiter <m:d>."""
    b_esc = xml_escape(beg)
    e_esc = xml_escape(end)
    return (
        f'<m:d><m:dPr><m:begChr m:val="{b_esc}"/><m:endChr m:val="{e_esc}"/></m:dPr>'
        f"<m:e>{body_xml}</m:e></m:d>"
    )


def add_omml_equation(
    doc,
    formula_title: str,
    omml_body_xml: str,
    variables: list[tuple[str, str]] | None = None,
) -> None:
    """
    Render a genuine Microsoft Word OMML equation inside a clean formula card,
    with optional symbol-by-symbol explanation immediately underneath.
    """
    cell = _create_card_cell(
        doc,
        bg_color="F8FAFC",
        left_color="2563EB",
        left_sz="18",
        box_color="DBEAFE",
        box_sz="4",
        top_pad=90,
        bottom_pad=90,
        left_pad=140,
        right_pad=140,
    )

    p_title = cell.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    rt = p_title.add_run(f"📐 Công thức: {formula_title}")
    rt.font.name = "Times New Roman"
    rt.font.size = Pt(9.8)
    rt.bold = True
    rt.font.color.rgb = RGBColor(30, 64, 175)

    p_eq = cell.add_paragraph()
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(3)
    p_eq.paragraph_format.space_after = Pt(4)
    omml_elem = parse_xml(f"<m:oMathPara {MATH_NS}><m:oMath>{omml_body_xml}</m:oMath></m:oMathPara>")
    p_eq._p.append(omml_elem)

    if variables:
        p_vh = cell.add_paragraph()
        p_vh.paragraph_format.space_before = Pt(2)
        p_vh.paragraph_format.space_after = Pt(2)
        r_vh = p_vh.add_run("Giải thích ký hiệu trong công thức:")
        r_vh.font.name = "Times New Roman"
        r_vh.font.size = Pt(9.2)
        r_vh.italic = True
        r_vh.bold = True
        r_vh.font.color.rgb = RGBColor(55, 65, 81)

        for sym, desc in variables:
            p_v = cell.add_paragraph()
            p_v.paragraph_format.left_indent = Inches(0.18)
            p_v.paragraph_format.space_before = Pt(0)
            p_v.paragraph_format.space_after = Pt(1.5)
            p_v.paragraph_format.line_spacing = 1.12
            r_sym = p_v.add_run(f"• {sym}: ")
            r_sym.font.name = "Cambria Math"
            r_sym.font.size = Pt(9.3)
            r_sym.bold = True
            r_sym.font.color.rgb = RGBColor(30, 64, 175)
            add_rich_runs(p_v, desc, font_size=9.2, color_rgb=(40, 40, 40))

    doc.add_paragraph().paragraph_format.space_after = Pt(3)


def add_heading_part(doc, title_str: str):
    """Add a major part heading."""
    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_before = Pt(20)
    p_box.paragraph_format.space_after = Pt(8)
    r_box = p_box.add_run(title_str.upper())
    r_box.font.name = "Times New Roman"
    r_box.font.size = Pt(14.5)
    r_box.bold = True
    r_box.font.color.rgb = RGBColor(128, 0, 0)

    p_bdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="double" w:sz="18" w:space="6" w:color="800000"/></w:pBdr>')
    p_box._p.get_or_add_pPr().append(p_bdr)
    return p_box


def add_heading_chapter(doc, number_str: str, title_str: str):
    """Add a chapter heading with bottom rule."""
    p_num = doc.add_paragraph()
    p_num.paragraph_format.space_before = Pt(18)
    p_num.paragraph_format.space_after = Pt(2)
    r_num = p_num.add_run(number_str.upper())
    r_num.font.name = "Times New Roman"
    r_num.font.size = Pt(12.5)
    r_num.bold = True
    r_num.font.color.rgb = RGBColor(192, 0, 0)

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run(title_str.upper())
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(13.5)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(31, 73, 125)

    p_bdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1F497D"/></w:pBdr>')
    p_title._p.get_or_add_pPr().append(p_bdr)
    return p_title


def add_heading_section(doc, text: str):
    """Add a section heading (1.1, 1.2...)."""
    return add_styled_paragraph(doc, text, font_size=12, bold=True, color_rgb=(192, 0, 0), space_before=10, space_after=3)


def add_heading_subsection(doc, text: str):
    """Add a subsection heading (1.1.1, 1.1.2...)."""
    return add_styled_paragraph(doc, text, font_size=11, bold=True, italic=True, color_rgb=(40, 70, 110), space_before=6, space_after=2)


def add_defense_qa(doc, q_num: int, question: str, intent: str, step1: str, step2: str, step3: str) -> None:
    """Render a structured 3-step thesis defense Q&A block consistently across chapters."""
    add_heading_subsection(doc, f"Câu {q_num}: {question}")
    add_styled_paragraph(
        doc,
        f"🎯 **Ý đồ kiểm tra của Giảng viên**: *{intent}*",
        font_size=10.0,
        color_rgb=(120, 53, 15),
        space_before=2,
        space_after=3,
    )
    add_bullet_item(doc, step1, bold_prefix="Bước 1 — Chốt kết luận trực diện", font_size=10.2, space_after=2)
    add_bullet_item(doc, step2, bold_prefix="Bước 2 — Bản chất vật lý / toán học", font_size=10.2, space_after=2)
    add_bullet_item(doc, step3, bold_prefix="Bước 3 — Bằng chứng thực nghiệm v0.9.4", font_size=10.2, space_after=6)


def add_styled_table(
    doc,
    headers: list[str],
    rows: list[tuple[str, ...]],
    col_widths: list[float] | None = None,
    header_hex: str = "1F497D",
    highlight_row_pred=None,
) -> None:
    """Create a clean, consistent academic table with alternating row shading."""
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color="CCCCCC", sz="4")

    for i, h_text in enumerate(headers):
        c = tbl.rows[0].cells[i]
        if col_widths and i < len(col_widths):
            c.width = Inches(col_widths[i])
        set_cell_background(c, header_hex)
        set_cell_margins(c, top=75, bottom=75, left=70, right=70)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.0)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, r_data in enumerate(rows):
        row = tbl.rows[r_idx + 1]
        is_hi = bool(highlight_row_pred and highlight_row_pred(r_idx, r_data))
        bg = "ECFDF5" if is_hi else ("F9FBFD" if r_idx % 2 == 0 else "FFFFFF")
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            if col_widths and c_idx < len(col_widths):
                cell.width = Inches(col_widths[c_idx])
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=65, bottom=65, left=70, right=70)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.12
            add_rich_runs(
                p,
                str(val),
                font_size=8.8,
                default_bold=(c_idx == 0 or is_hi),
                color_rgb=(6, 95, 70) if (is_hi and c_idx > 0) else ((31, 73, 125) if c_idx == 0 else (30, 30, 30)),
            )

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
