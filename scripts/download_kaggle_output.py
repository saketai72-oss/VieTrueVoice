#!/usr/bin/env python3
"""Script to download all manifests from Kaggle output."""

import re
import time
import requests
import kaggle
from pathlib import Path
from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest

TARGET_FILES = {
    "bonafide_manifest.csv",
    "spoof_manifest.csv",
    "full_manifest.csv",
    "train.csv",
    "dev.csv",
    "test_indomain.csv",
}

def main():
    api = kaggle.KaggleApi()
    api.authenticate()
    kernel_slug = "vietrue-model-training"
    owner_slug = "nguyenthanhtai1959"
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 Đang tìm kiếm các tệp manifest trên Kaggle...", flush=True)
    found_files = {}
    token = None
    page = 1

    with api.build_kaggle_client() as client:
        while page <= 10:
            time.sleep(1.5)  # Tránh lỗi 429 Rate Limit
            req = ApiListKernelSessionOutputRequest()
            req.user_name = owner_slug
            req.kernel_slug = kernel_slug
            api._set_paging(req, 100, token)
            resp = client.kernels.kernels_api_client.list_kernel_session_output(req)
            
            for item in (resp.files or []):
                basename = Path(item.file_name).name
                if basename in TARGET_FILES and basename not in found_files:
                    found_files[basename] = (item.file_name, item.url)
                    print(f"  🎯 Tìm thấy manifest: {item.file_name}", flush=True)

            # Nếu đã tìm đủ cả 6 file manifest mục tiêu thì dừng quét
            if len(found_files) >= len(TARGET_FILES):
                print("✅ Đã tìm thấy đầy đủ toàn bộ 6 tệp manifest!", flush=True)
                break

            token = resp.next_page_token
            print(f"📄 Đã duyệt trang {page} (next_page: {bool(token)})", flush=True)
            if not token:
                break
            page += 1

    print(f"\n📦 Bắt đầu tải {len(found_files)} manifest về {out_dir}...", flush=True)
    for basename, (fname, url) in found_files.items():
        dest = out_dir / basename
        print(f"⬇️ Đang tải {basename} từ {fname}...", flush=True)
        resp = requests.get(url, stream=True)
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        print(f"   ✔️ Hoàn tất: {basename} ({dest.stat().st_size / 1e3:.1f} KB)", flush=True)

    print("\n🎉 Hoàn thành cập nhật toàn bộ manifest chuẩn 17 cột từ Kaggle GPU!", flush=True)

if __name__ == "__main__":
    main()
