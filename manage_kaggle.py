#!/usr/bin/env python3
"""
Công cụ quản lý Kaggle Job cho project vietrue_model.
Hỗ trợ push code, xem status, tải output và cập nhật metadata nhanh chóng.
"""

import sys
import json
import subprocess
from pathlib import Path

METADATA_FILE = Path("kernel-metadata.json")
OUTPUT_DIR = Path("out")

def load_metadata():
    if not METADATA_FILE.exists():
        print(f"❌ Không tìm thấy file {METADATA_FILE}!")
        sys.exit(1)
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(data):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_cmd(cmd):
    print(f"👉 Thực thi: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def check_username(meta):
    kernel_id = meta.get("id", "")
    if "YOUR_KAGGLE_USERNAME" in kernel_id or not kernel_id:
        print("⚠️ CẢNH BÁO: Bạn chưa cập nhật Kaggle Username trong kernel-metadata.json!")
        print("💡 Chạy lệnh sau để cập nhật username:")
        print("   python manage_kaggle.py set-user <ten-username-cua-ban>\n")
        return False
    return True

def cmd_push():
    meta = load_metadata()
    if not check_username(meta):
        return
    print(f"🚀 Đang đẩy code lên Kaggle ({meta['id']})...")
    run_cmd(["kaggle", "kernels", "push", "-p", "."])

def cmd_status():
    meta = load_metadata()
    if not check_username(meta):
        return
    print(f"📊 Kiểm tra trạng thái kernel: {meta['id']}")
    run_cmd(["kaggle", "kernels", "status", meta["id"]])

def cmd_output(force: bool = False):
    meta = load_metadata()
    if not check_username(meta):
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📥 Đang tải kết quả từ Kaggle ({meta['id']}) về thư mục ./{OUTPUT_DIR}...")
    cmd = ["kaggle", "kernels", "output", meta["id"], "-p", str(OUTPUT_DIR)]
    if force:
        cmd.append("--force")
    run_cmd(cmd)

def cmd_set_user(username):
    meta = load_metadata()
    slug = meta.get("id", "vietrue-model-training").split("/")[-1]
    meta["id"] = f"{username.strip()}/{slug}"
    save_metadata(meta)
    print(f"✅ Đã cập nhật Kernel ID thành: {meta['id']}")

def cmd_add_dataset(dataset_slug):
    meta = load_metadata()
    sources = meta.get("dataset_sources", [])
    dataset_slug = dataset_slug.strip()
    if dataset_slug not in sources:
        sources.append(dataset_slug)
        meta["dataset_sources"] = sources
        save_metadata(meta)
        print(f"✅ Đã thêm dataset '{dataset_slug}' vào kernel-metadata.json")
    else:
        print(f"ℹ️ Dataset '{dataset_slug}' đã tồn tại trong danh sách.")

def print_help():
    print("""
==================================================
        KAGGLE JOB MANAGER - VIETRUE MODEL
==================================================
Các lệnh hỗ trợ:
  python manage_kaggle.py set-user <username>     : Cài đặt username Kaggle của bạn
  python manage_kaggle.py add-dataset <slug>      : Thêm dataset (ví dụ: user/ten-data)
  python manage_kaggle.py push                    : Đẩy code và chạy trên Kaggle GPU
  python manage_kaggle.py status                  : Xem trạng thái job (running, complete...)
  python manage_kaggle.py output                  : Tải toàn bộ kết quả về thư mục ./out
==================================================
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    action = sys.argv[1].lower()
    if action == "push":
        cmd_push()
    elif action == "status":
        cmd_status()
    elif action == "output":
        force = ("--force" in sys.argv) or ("-f" in sys.argv)
        cmd_output(force=force)
    elif action == "set-user" and len(sys.argv) >= 3:
        cmd_set_user(sys.argv[2])
    elif action == "add-dataset" and len(sys.argv) >= 3:
        cmd_add_dataset(sys.argv[2])
    else:
        print_help()

if __name__ == "__main__":
    main()
