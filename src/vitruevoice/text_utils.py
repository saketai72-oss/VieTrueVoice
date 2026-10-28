"""Tiện ích chuẩn hóa văn bản tiếng Việt cho ViTrueVoice.

Hàm normalize_for_eval CHỈ DÙNG cho:
1. Tính WER/CER ở Gate 1 ASR (tránh lỗi lệch dấu thanh hoà/hòa, khoẻ/khỏe).
2. Kiểm tra trùng lặp văn bản Text-Disjoint giữa các split.

LƯU Ý: Tuyệt đối KHÔNG áp dụng normalize_for_eval lên prompt đầu vào của TTS.
Prompt TTS phải giữ nguyên văn bản gốc để bộ g2p phát âm tự nhiên.
"""

import unicodedata
import re

_OA_OE = {
    "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
    "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe"
}
_UY = {
    "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"
}

def fix_tone_token(w: str) -> str:
    """Chuẩn hóa vị trí dấu thanh theo âm tiết mở (chỉ đổi khi vần kết thúc âm tiết).
    
    Bảo toàn vần đóng: toàn, hoàng, khoảng, ngoài...
    Bảo toàn âm đầu qu: quý, quỳ, quỷ...
    Bảo toàn vần uở: thuở...
    Quy chuẩn âm tiết mở: hoà -> hòa, thuỷ -> thủy, khoẻ -> khỏe.
    """
    w = unicodedata.normalize("NFC", w).lower()
    for old, new in _OA_OE.items():
        if w.endswith(old):
            return w[:-len(old)] + new
    for old, new in _UY.items():
        if w.endswith(old) and not w[:-len(old)].endswith("q"):
            return w[:-len(old)] + new
    return w

def normalize_for_eval(text: str) -> str:
    """Chuẩn hóa văn bản NFC, chuyển thường, chuẩn hóa dấu thanh và xóa dấu câu."""
    if not text:
        return ""
    text_nfc = unicodedata.normalize("NFC", str(text)).lower()
    text_clean = re.sub(r"[^\w\s]", " ", text_nfc)
    tokens = [fix_tone_token(tok) for tok in text_clean.split()]
    return " ".join(tokens)

def has_digits(text: str) -> bool:
    """Kiểm tra văn bản có chứa chữ số (để loại bỏ khỏi Gate 1)."""
    return bool(re.search(r"\d", str(text)))
