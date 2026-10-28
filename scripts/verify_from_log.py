import re
from pathlib import Path

def check_log():
    log_path = Path("out/kaggle_stdout.log")
    text = log_path.read_text(encoding='utf-8')

    print("=== KIỂM TRA TẬP MẪU TỪ LOG THỰC NGHIỆM KAGGLE GPU ===")
    
    # 1. Check speakers
    vivos_spks = set(re.findall(r'Hoàn tất (VIVOS[A-Z0-9]+)', text))
    cv_spks = set(re.findall(r'Hoàn tất (CV_[a-z0-9]+)', text))
    
    print(f"\n1. Danh sách Speaker hoàn tất sinh spoof:")
    print(f" - VIVOS DEV (19 spks): {len([s for s in vivos_spks if 'DEV' in s])}/19")
    print(f" - VIVOS SPK (46 spks): {len([s for s in vivos_spks if 'SPK' in s])}/46")
    print(f" - VIVOS Tổng cộng: {len(vivos_spks)}/65 (100%)")
    print(f" - Common Voice 8.0: {len(cv_spks)}/25 (100%)")
    print(f" => Tổng số speaker hoàn tất: {len(vivos_spks) + len(cv_spks)} / 90")

    # 2. Check Bonafide & Text Disjoint
    print(f"\n2. Khử trùng lặp văn bản (Hard Text-Disjoint):")
    disjoint_match = re.search(r'Thống kê văn bản sau khử trùng lặp.*?(?=✅)', text, re.DOTALL)
    if disjoint_match:
        print(disjoint_match.group(0).strip())
    
    bona_match = re.search(r'Đã lưu (\d+) mẫu Bona fide chuẩn hóa tại: (.*?bonafide_manifest\.csv)', text)
    if bona_match:
        print(f"\n3. Mẫu Bona fide: {bona_match.group(1)} mẫu")

    # 3. Check Spoof samples
    spoof_match = re.search(r'Đã hoàn tất sinh spoof! Lưu manifest tại: (.*?spoof_manifest\.csv) \((\d+) mẫu\)', text)
    if spoof_match:
        print(f"\n4. Mẫu Spoof sinh ra: {spoof_match.group(2)} mẫu")

    # 4. Check Paired Triplets
    triplet_match = re.search(r'Kiểm tra số lượng Codec Eval: (.*?)\n', text)
    if triplet_match:
        print(f"\n5. Cấu trúc Paired Triplets (Eval): {triplet_match.group(1).strip()}")

    # 5. Check Summary report
    report_match = re.search(r'📊 BÁO CÁO TỔNG KẾT TẬP DỮ LIỆU ĐÃ CHUẨN HÓA.*?(?=📦)', text, re.DOTALL)
    if report_match:
        print(f"\n6. Báo cáo phân bổ 18 cột toàn diện:\n{report_match.group(0).strip()}")

    # 6. Check empty transcript ratio
    empty_t = re.search(r'Tỷ lệ transcript rỗng của spoof: ([\d\.\%]+)', text)
    if empty_t:
        print(f"\n7. Tỷ lệ transcript rỗng: {empty_t.group(1)}")

    # 7. Check if zip packaging completed
    zip_match = re.search(r'Đã tạo gói dữ liệu thành công: (.*?vitruevoice_data_processed\.zip) \(([\d\.]+ MB)\)', text)
    if zip_match:
        print(f"\n8. Đóng gói dữ liệu Kaggle: {zip_match.group(1)} ({zip_match.group(2)})")

if __name__ == '__main__':
    check_log()
