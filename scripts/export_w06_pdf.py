#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export DACN_2380601959_NguyenThanhTai_W06.docx to PDF using Word COM."""

import os
import sys
from pathlib import Path
import win32com.client

DOCX_PATH = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W06.docx"
PDF_PATH = r"C:\Users\saket\Documents\Đồ án chuyên ngành\Content\DACN_2380601959_NguyenThanhTai_W06.pdf"

def export_pdf(docx_path: str, pdf_path: str) -> None:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0

    try:
        print(f"Opening: {docx_path}")
        doc = word.Documents.Open(docx_path, ReadOnly=True)
        print(f"Exporting to: {pdf_path}")
        # 17 = wdFormatPDF
        doc.SaveAs2(pdf_path, FileFormat=17)
        doc.Close(SaveChanges=False)
        print(f"SUCCESS: Exported PDF ({os.path.getsize(pdf_path):,} bytes)")
    finally:
        word.Quit()

if __name__ == "__main__":
    export_pdf(DOCX_PATH, PDF_PATH)
