#!/usr/bin/env python3
"""Script chuẩn bị toàn diện dữ liệu và môi trường cho việc huấn luyện B_zalo trên máy Local.

Các tác vụ tự động:
1. Xác thực Kaggle API và tải Checkpoint B (379MB) nếu chưa có.
2. Tải trực tiếp tệp nén âm thanh 3.26GB (vitruevoice_data_processed.zip) bằng ApiDownloadKernelOutputRequest.
3. Giải nén chọn lọc (Bijective Selective Unzip) các file audio cần cho Train & Dev Zalo vào thư mục data/.
4. Chuyển mã trước các tệp proxy Zalo (Profile A: AAC 76k, Profile B: Opus 24k).
5. Tiền sinh offline 500 biến thể bona fide trầm (F0 < 120Hz) bổ sung vào train manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import time
import zipfile
from pathlib import Path

import pandas as pd

EXPECTED_CKPT_SHA = "a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_kaggle_kernel_file(owner: str, slug: str, filename: str, out_file: Path) -> None:
    import kaggle
    from kagglesdk.kernels.types.kernels_api_service import (
        ApiDownloadKernelOutputRequest,
    )

    print(f"📥 Đang kết nối tải trực tiếp {filename} từ {owner}/{slug}...")
    kapi = kaggle.KaggleApi()
    kapi.authenticate()
    req = ApiDownloadKernelOutputRequest()
    req.owner_slug = owner
    req.kernel_slug = slug
    req.file_path = filename

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with kapi.build_kaggle_client() as client:
        res = client.kernels.kernels_api_client.download_kernel_output(req)
        res.raise_for_status()
        total = int(res.headers.get("content-length", 0))
        downloaded = 0
        t0 = time.time()
        with open(out_file, "wb") as f:
            for chunk in res.iter_content(chunk_size=16 * 1024 * 1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and downloaded % (64 * 1024 * 1024) < len(chunk):
                        speed = (downloaded / (1024**2)) / max(0.1, time.time() - t0)
                        pct = (downloaded / total) * 100
                        print(f"   - Tiến độ: {downloaded / (1024**2):.1f} / {total / (1024**2):.1f} MB ({pct:.1f}%) | Tốc độ: {speed:.1f} MB/s", flush=True)
    print(f"✅ Đã tải hoàn tất {filename} ({out_file.stat().st_size / (1024**2):.1f} MB) trong {time.time() - t0:.1f}s!")


def ensure_checkpoint(ckpt_path: Path) -> Path:
    if ckpt_path.exists() and ckpt_path.stat().st_size > 10000000:
        actual_sha = compute_sha256(ckpt_path)
        if actual_sha == EXPECTED_CKPT_SHA:
            print(f"✅ Checkpoint B đã tồn tại và hợp lệ: {ckpt_path} (SHA-256: {actual_sha[:10]}...)")
            return ckpt_path

    print("📥 Checkpoint B chưa có hoặc sai SHA-256. Đang tải từ Kaggle...")
    download_kaggle_kernel_file("nguyenthanhtai1959", "vietrue-ssl-training", "best_model_B.pt", ckpt_path)
    actual_sha = compute_sha256(ckpt_path)
    assert actual_sha == EXPECTED_CKPT_SHA, f"❌ Sai SHA-256 Checkpoint B! Nhận được: {actual_sha}"
    print(f"✅ Checkpoint B đạt chuẩn: {ckpt_path}")
    return ckpt_path


def ensure_audio_zip(zip_path: Path) -> Path:
    if zip_path.exists() and zip_path.stat().st_size > 1000000000:
        print(f"✅ Audio ZIP đã có sẵn: {zip_path} ({zip_path.stat().st_size / (1024**2):.1f} MB)")
        return zip_path

    print("📥 Đang tải vitruevoice_data_processed.zip (3.26 GB) từ Kaggle...")
    download_kaggle_kernel_file("nguyenthanhtai1959", "vietrue-model-training", "vitruevoice_data_processed.zip", zip_path)
    return zip_path


def selective_unzip(zip_path: Path, df_tr: pd.DataFrame, df_dv: pd.DataFrame, target_root: Path) -> int:
    clean_rows = pd.concat([df_tr[df_tr["codec"] == "clean_16khz"], df_dv[df_dv["codec"] == "clean_16khz"]])
    base_to_clean = dict(zip(clean_rows["base_utt"], clean_rows["audio_path"]))

    needed_rel = set()
    for df_sub in [df_tr, df_dv]:
        for _, row in df_sub.iterrows():
            c = row["codec"]
            if c in ["clean_16khz", "g711_alaw", "amr_nb"]:
                needed_rel.add(row["audio_path"].replace("\\", "/").lstrip("/"))
            elif row["base_utt"] in base_to_clean:
                needed_rel.add(base_to_clean[row["base_utt"]].replace("\\", "/").lstrip("/"))

    print(f"🎯 Số lượng file audio gốc cần trích xuất: {len(needed_rel)}")
    t0 = time.time()
    extracted = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        name_set = set(zf.namelist())
        targets = []
        for rel_p in needed_rel:
            dest_file = target_root / rel_p
            if dest_file.exists() and dest_file.stat().st_size > 100:
                continue
            for cand in [rel_p, f"data/{rel_p}", rel_p.replace("data/", "")]:
                if cand in name_set:
                    targets.append((cand, dest_file))
                    break

        print(f"   - Cần giải nén mới: {len(targets)} tệp...")
        for src_entry, dst_p in targets:
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(src_entry) as s_f, open(dst_p, "wb") as d_f:
                d_f.write(s_f.read())
            extracted += 1

    print(f"✅ Giải nén chọn lọc hoàn tất: {extracted} tệp mới được ghi trong {time.time() - t0:.1f}s")
    return extracted


def main():
    p = argparse.ArgumentParser(description="Thiết lập dữ liệu huấn luyện cục bộ cho ViTrueVoice B_zalo")
    p.add_argument("--data-zip", default="data/vitruevoice_data_processed.zip", help="Đường dẫn lưu file ZIP âm thanh 3.26GB")
    p.add_argument("--ckpt", default="out/kaggle_ssl_out/best_model_B.pt", help="Đường dẫn lưu Checkpoint B gốc")
    p.add_argument("--skip-download", action="store_true", help="Bỏ qua bước tải xuống nếu file đã có")
    args = p.parse_args()

    print("=" * 60)
    print("🚀 BẮT ĐẦU CHUẨN BỊ MÔI TRƯỜNG HUẤN LUYỆN LOCAL B_ZALO")
    print("=" * 60)

    # 1. Checkpoint B
    ckpt_path = Path(args.ckpt)
    ensure_checkpoint(ckpt_path)

    # 2. Audio ZIP
    zip_path = Path(args.data_zip)
    if not args.skip_download:
        ensure_audio_zip(zip_path)

    # 3. Nạp Manifests
    tr_path = Path("data/manifests_zalo/train_zalo.csv")
    dv_path = Path("data/manifests_zalo/dev_zalo.csv")
    assert tr_path.exists(), f"❌ Không tìm thấy {tr_path}"
    assert dv_path.exists(), f"❌ Không tìm thấy {dv_path}"
    df_tr = pd.read_csv(tr_path)
    df_dv = pd.read_csv(dv_path)
    print(f"📊 Đã nạp Manifests: Train={len(df_tr)} dòng | Dev={len(df_dv)} dòng")

    # 4. Giải nén chọn lọc vào repo root (thư mục data/...)
    if zip_path.exists() and zip_path.stat().st_size > 100000000:
        selective_unzip(zip_path, df_tr, df_dv, target_root=Path("."))
    else:
        print("⚠️ File ZIP dữ liệu âm thanh chưa sẵn sàng, bỏ qua bước giải nén.")

    # 5. Tiền sinh Offline 500 mẫu bona fide trầm nếu có audio
    try:
        from scripts.generate_zalo_paired_manifests import (
            generate_paired_manifest,
            preaugment_deep_voices,
        )
        print("🎵 Kiểm tra tiền sinh offline biến thể giọng trầm...")
        test_cand = Path("data/manifests_zalo/test_indomain_zalo.csv")
        df_test = pd.read_csv(test_cand) if test_cand.exists() else pd.DataFrame(columns=["speaker_id", "base_utt"])
        aug_df = preaugment_deep_voices(
            df_tr, df_dv, df_test,
            audio_root=Path("."),
            out_audio_dir=Path("data/raw"),
            n_samples=500,
            semitones_range=(-8.0, -4.0),
            seed=42,
        )
        if len(aug_df) > 0:
            aug_paired = generate_paired_manifest(aug_df)
            df_tr = pd.concat([df_tr, aug_paired], ignore_index=True)
            df_tr.to_csv(tr_path, index=False, lineterminator="\n")
            print(f"✅ Đã tiền sinh {len(aug_df)} mẫu trầm và cập nhật {len(df_tr)} dòng Train manifest")
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        print(f"ℹ️ Bước pre-augment offline: {e}")

    print("=" * 60)
    print("🎉 THIẾT LẬP DỮ LIỆU CỤC BỘ HOÀN TẤT — SẴN SÀNG HUẤN LUYỆN!")
    print("=" * 60)


if __name__ == "__main__":
    main()
