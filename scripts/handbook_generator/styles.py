# -*- coding: utf-8 -*-
"""
Styling and formatting helper functions for ViTrueVoice Defense Handbook.
"""

from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
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

def add_callout_box(doc, text, title="GHI NHỚ QUAN TRỌNG KHI BẢO VỆ", border_color="1F497D", bg_color="F2F5F9"):
    """Create a highlight callout box for critical tips or formulas."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:top w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"★ {title}: ")
    run_t.font.name = "Times New Roman"
    run_t.font.size = Pt(10.5)
    run_t.bold = True
    run_t.font.color.rgb = RGBColor(31, 73, 125)
    
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)
        run.bold = (i % 2 == 1)
        run.font.color.rgb = RGBColor(30, 30, 30)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_prerequisite_box(doc, chapter_title, concepts_summary, border_color="B8860B", bg_color="FFFDF5"):
    """Create a dedicated prerequisite box for a chapter."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    run_t = p.add_run(f"📌 BẢNG TRA CỨU KIẾN THỨC NỀN TẢNG CẦN NẮM TRƯỚC KHI ĐỌC {chapter_title.upper()}:")
    run_t.font.name = "Times New Roman"
    run_t.font.size = Pt(10.5)
    run_t.bold = True
    run_t.font.color.rgb = RGBColor(184, 134, 11)
    
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_before = Pt(2)
    p2.paragraph_format.space_after = Pt(2)
    p2.paragraph_format.line_spacing = 1.15
    run_desc = p2.add_run(f"Trước khi đi vào các công thức, thuật toán và thông số kỹ thuật bên dưới, người đọc cần hiểu rõ các khái niệm nền tảng sau: {concepts_summary}")
    run_desc.font.name = "Times New Roman"
    run_desc.font.size = Pt(9.5)
    run_desc.font.italic = True
    run_desc.font.color.rgb = RGBColor(70, 70, 70)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_styled_paragraph(doc, text="", font_size=11, bold=False, italic=False, color_rgb=(0,0,0), align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, line_spacing=1.15):
    """Add a paragraph with Markdown bold support (**text**)."""
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

def add_bullet_item(doc, text, bold_prefix="", font_size=10.5, space_after=3):
    """Add a bullet list item with bold title prefix."""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + ": ")
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(font_size)
        r_pre.bold = True
        r_pre.font.color.rgb = RGBColor(31, 73, 125)
        
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        run = p.add_run(part)
        run.font.name = "Times New Roman"
        run.font.size = Pt(font_size)
        run.bold = (i % 2 == 1)
        run.font.color.rgb = RGBColor(30, 30, 30)
    return p

def add_heading_part(doc, title_str):
    """Add a major part heading with distinctive luxury styling."""
    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_before = Pt(22)
    p_box.paragraph_format.space_after = Pt(10)
    r_box = p_box.add_run(title_str.upper())
    r_box.font.name = "Times New Roman"
    r_box.font.size = Pt(15)
    r_box.bold = True
    r_box.font.color.rgb = RGBColor(128, 0, 0)
    
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="double" w:sz="18" w:space="6" w:color="800000"/></w:pBdr>')
    p_box._p.get_or_add_pPr().append(pBdr)
    return p_box

def add_heading_chapter(doc, number_str, title_str):
    """Add a chapter heading with professional border line."""
    p_num = doc.add_paragraph()
    p_num.paragraph_format.space_before = Pt(20)
    p_num.paragraph_format.space_after = Pt(2)
    r_num = p_num.add_run(number_str.upper())
    r_num.font.name = "Times New Roman"
    r_num.font.size = Pt(13)
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
    
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1F497D"/></w:pBdr>')
    p_title._p.get_or_add_pPr().append(pBdr)
    return p_title

def add_heading_section(doc, text):
    """Add a section heading (1.1, 1.2...)."""
    return add_styled_paragraph(doc, text, font_size=12, bold=True, color_rgb=(192, 0, 0), space_before=11, space_after=3)

def add_heading_subsection(doc, text):
    """Add a subsection heading (1.1.1, 1.1.2...)."""
    return add_styled_paragraph(doc, text, font_size=11, bold=True, italic=True, color_rgb=(40, 70, 110), space_before=7, space_after=2)
