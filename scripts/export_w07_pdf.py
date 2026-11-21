#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export DACN_2380601959_NguyenThanhTai_W07.docx to PDF using Word COM."""

import os
import sys
import shutil
from pathlib import Path
import win32com.client

DOCX_CONTENT = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W07.docx"
PDF_CONTENT = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W07.pdf"
DOCX_ROOT = r"C:\Users\saket\Documents\Đồ án chuyên ngành\DACN_2380601959_NguyenThanhTai_W07.docx"
PDF_ROOT = r"C:\Users\saket\Documents\Đồ án chuyên ngành\DACN_2380601959_NguyenThanhTai_W07.pdf"

def export_pdf() -> None:
    if not os.path.exists(DOCX_CONTENT):
        raise FileNotFoundError(f"DOCX file not found: {DOCX_CONTENT}")

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        print(f"Opening: {DOCX_CONTENT}")
        doc = word.Documents.Open(DOCX_CONTENT, ReadOnly=True)
        print(f"Exporting to: {PDF_CONTENT}")
        # 17 = wdFormatPDF
        doc.SaveAs2(PDF_CONTENT, FileFormat=17)
        doc.Close(SaveChanges=False)
        print(f"SUCCESS: Exported PDF ({os.path.getsize(PDF_CONTENT):,} bytes)")
        shutil.copy2(PDF_CONTENT, PDF_ROOT)
        print(f"SUCCESS: Copied PDF to ({PDF_ROOT})")
    finally:
        word.Quit()

if __name__ == "__main__":
    export_pdf()
