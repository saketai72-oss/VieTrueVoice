"""Kịch bản kiểm toán an ninh độc lập cho Manifest V6 (ViTrueVoice v0.4.4).

Thực hiện 4 kiểm định an ninh nghiêm ngặt:
1. Zero-leakage check: 5 tình nguyện viên nghiệm thu (SPK_0003..0007) tuyệt đối 0% trong Train & Dev.
2. Hard Text-Disjoint check: SPK_0001 trong Train có 0 câu trùng lặp với Dev Zalo & Test In-domain Zalo.
3. H2 Unseen Engine check: Tuyệt đối không có dòng nào của VieNeu-TTS trong Train Zalo.
4. SPK_0001 Integrity check: Đúng 125 dòng (75 bona fide + 50 spoof F5-TTS), file tồn tại trên đĩa.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.vitruevoice.text_utils import normalize_for_eval

ACCEPTANCE_VOLUNTEERS = {"SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"}
EXPECTED_CODECS = {"clean_16khz", "aac_zalo_76k", "opus_zalo_24k", "amr_nb", "g711_alaw"}


def audit_v6_manifests(
    train_path: Path | str = "data/manifests_zalo/train_zalo.csv",
    dev_path: Path | str = "data/manifests_zalo/dev_zalo.csv",
    test_path: Path | str = "data/manifests_zalo/test_indomain_zalo.csv",
) -> dict[str, Any]:
    print("=" * 80)
    print("🛡️ KIỂM TOÁN AN NINH ĐỘC LẬP & TÍNH TOÀN VẸN MANIFEST V6")
    print("=" * 80)

    train_p = Path(train_path)
    dev_p = Path(dev_path)
    test_p = Path(test_path)

    if not train_p.exists():
        raise FileNotFoundError(f"Không tìm thấy tập train: {train_p}")
    if not dev_p.exists():
        raise FileNotFoundError(f"Không tìm thấy tập dev: {dev_p}")

    train_df = pd.read_csv(train_p)
    dev_df = pd.read_csv(dev_p)
    test_df = pd.read_csv(test_p) if test_p.exists() else None

    print(f"📁 Tệp nạp:")
    print(f"  - Train Zalo : {train_p} ({len(train_df):,} dòng)")
    print(f"  - Dev Zalo   : {dev_p} ({len(dev_df):,} dòng)")
    if test_df is not None:
        print(f"  - Test Zalo  : {test_p} ({len(test_df):,} dòng)")
    print("-" * 80)

    results: dict[str, Any] = {}

    # ── 1. ZERO-LEAKAGE AUDIT: 5 HELD-OUT ACCEPTANCE VOLUNTEERS ───────────────
    print("\n🔍 1. KIỂM TOÁN ZERO-LEAKAGE (5 TÌNH NGUYỆN VIÊN ĐỐI CHỨNG HELD-OUT)")
    print(f"  Danh sách bị cấm: {sorted(ACCEPTANCE_VOLUNTEERS)}")

    train_spks = set(train_df["speaker_id"].dropna().astype(str).unique())
    dev_spks = set(dev_df["speaker_id"].dropna().astype(str).unique())

    leak_train = train_spks.intersection(ACCEPTANCE_VOLUNTEERS)
    leak_dev = dev_spks.intersection(ACCEPTANCE_VOLUNTEERS)

    # Quét thêm theo chuỗi audio_path và utt_id
    leak_audio_train = [s for s in ACCEPTANCE_VOLUNTEERS if train_df["audio_path"].astype(str).str.contains(s, regex=False).any()]
    leak_audio_dev = [s for s in ACCEPTANCE_VOLUNTEERS if dev_df["audio_path"].astype(str).str.contains(s, regex=False).any()]

    status_1 = len(leak_train) == 0 and len(leak_dev) == 0 and len(leak_audio_train) == 0 and len(leak_audio_dev) == 0
    results["zero_leakage_5spk"] = {
        "pass": status_1,
        "leak_train": sorted(list(leak_train)),
        "leak_dev": sorted(list(leak_dev)),
        "leak_audio_train": sorted(leak_audio_train),
        "leak_audio_dev": sorted(leak_audio_dev),
    }

    if status_1:
        print("  ✅ PASS: 0% rò rỉ 5 tình nguyện viên đối chứng (SPK_0003..0007 hoàn toàn held-out)")
    else:
        print(f"  ❌ FAIL: Phát hiện rò rỉ tình nguyện viên đối chứng!")
        if leak_train:
            print(f"     -> Trong Train: {leak_train}")
        if leak_dev:
            print(f"     -> Trong Dev: {leak_dev}")

    # ── 2. SPK_0001 ISOLATION AUDIT ──────────────────────────────────────────
    print("\n🔍 2. KIỂM TOÁN CÔ LẬP SPK_0001 (CHỈ XUẤT HIỆN TRONG TRAIN)")
    spk1_in_train = (train_df["speaker_id"] == "SPK_0001").sum()
    spk1_in_dev = (dev_df["speaker_id"] == "SPK_0001").sum()
    spk1_in_test = (test_df["speaker_id"] == "SPK_0001").sum() if test_df is not None else 0

    status_2 = spk1_in_train > 0 and spk1_in_dev == 0 and spk1_in_test == 0
    results["spk0001_isolation"] = {
        "pass": status_2,
        "count_train": int(spk1_in_train),
        "count_dev": int(spk1_in_dev),
        "count_test": int(spk1_in_test),
    }
    print(f"  SPK_0001 trong Train: {spk1_in_train:3d} dòng")
    print(f"  SPK_0001 trong Dev  : {spk1_in_dev:3d} dòng (yêu cầu 0)")
    print(f"  SPK_0001 trong Test : {spk1_in_test:3d} dòng (yêu cầu 0)")
    print(f"  -> Trạng thái: {'✅ PASS' if status_2 else '❌ FAIL'}")

    # ── 3. HARD TEXT-DISJOINT AUDIT ──────────────────────────────────────────
    print("\n🔍 3. KIỂM TOÁN RÀNG BUỘC HARD TEXT-DISJOINT CỦA SPK_0001")
    spk1_df = train_df[train_df["speaker_id"] == "SPK_0001"]
    spk1_transcripts = set(
        normalize_for_eval(t)
        for t in spk1_df["transcript"].dropna().astype(str).unique()
        if normalize_for_eval(t)
    )

    dev_transcripts = set(
        normalize_for_eval(t)
        for t in dev_df["transcript"].dropna().astype(str).unique()
        if normalize_for_eval(t)
    )

    overlap_dev = spk1_transcripts.intersection(dev_transcripts)
    overlap_test = set()
    if test_df is not None:
        test_transcripts = set(
            normalize_for_eval(t)
            for t in test_df["transcript"].dropna().astype(str).unique()
            if normalize_for_eval(t)
        )
        overlap_test = spk1_transcripts.intersection(test_transcripts)

    status_3 = len(overlap_dev) == 0 and len(overlap_test) == 0
    results["text_disjoint"] = {
        "pass": status_3,
        "n_spk1_texts": len(spk1_transcripts),
        "overlap_dev": sorted(list(overlap_dev)),
        "overlap_test": sorted(list(overlap_test)),
    }
    print(f"  Số câu độc bản của SPK_0001 trong Train: {len(spk1_transcripts)}")
    print(f"  Trùng lặp với Dev Zalo : {len(overlap_dev)} câu")
    print(f"  Trùng lặp với Test Zalo: {len(overlap_test)} câu")
    if status_3:
        print("  ✅ PASS: 100% Hard Text-Disjoint được bảo toàn")
    else:
        print(f"  ❌ FAIL: Phát hiện rò rỉ văn bản!")
        if overlap_dev:
            print(f"     -> Trùng với Dev: {overlap_dev}")
        if overlap_test:
            print(f"     -> Trùng với Test: {overlap_test}")

    # ── 4. H2 UNSEEN TTS ENGINE AUDIT ────────────────────────────────────────
    print("\n🔍 4. KIỂM TOÁN BẢO TỒN GIẢ THUYẾT H2 (CÔNG CỤ UNSEEN VIENEU-TTS)")
    vieneu_in_train_tts = train_df["tts_generator"].astype(str).str.lower().str.contains("vieneu", regex=False).sum()
    vieneu_in_train_path = train_df["audio_path"].astype(str).str.lower().str.contains("vieneu", regex=False).sum()
    vieneu_in_train_utt = train_df["utt_id"].astype(str).str.lower().str.contains("vieneu", regex=False).sum()

    total_vieneu_train = vieneu_in_train_tts + vieneu_in_train_path + vieneu_in_train_utt
    status_4 = total_vieneu_train == 0
    results["h2_unseen_engine"] = {
        "pass": status_4,
        "vieneu_rows": int(total_vieneu_train),
    }
    print(f"  Số dòng VieNeu-TTS trong Train Zalo: {total_vieneu_train}")
    if status_4:
        print("  ✅ PASS: 100% VieNeu-TTS được cách ly khỏi tập huấn luyện (Bảo vệ H2)")
    else:
        print(f"  ❌ FAIL: Phát hiện VieNeu-TTS trong Train Zalo ({total_vieneu_train} dòng)!")

    # ── 5. SPK_0001 ROW COUNT & COMPOSITION AUDIT ───────────────────────────
    print("\n🔍 5. KIỂM TOÁN CƠ CẤU VÀ TÍNH TOÀN VẸN CỦA SPK_0001 TRONG TRAIN")
    spk1_bona = spk1_df[spk1_df["label"] == "bonafide"]
    spk1_spoof = spk1_df[spk1_df["label"] == "spoof"]

    n_spk1_total = len(spk1_df)
    n_spk1_bona = len(spk1_bona)
    n_spk1_spoof = len(spk1_spoof)

    # Kiểm tra sự tồn tại của file âm thanh trên đĩa
    missing_files = []
    for p in spk1_df["audio_path"]:
        if not Path(p).exists():
            missing_files.append(p)

    status_5 = (
        n_spk1_total == 125
        and n_spk1_bona == 75
        and n_spk1_spoof == 50
        and len(missing_files) == 0
    )
    results["spk0001_composition"] = {
        "pass": status_5,
        "total": n_spk1_total,
        "bona": n_spk1_bona,
        "spoof": n_spk1_spoof,
        "missing_files": missing_files,
    }
    print(f"  Tổng số dòng SPK_0001: {n_spk1_total}/125")
    print(f"  - Bona fide           : {n_spk1_bona}/75 (15 clips x 5 codecs)")
    print(f"  - Spoof F5-TTS        : {n_spk1_spoof}/50 (10 prompts x 5 codecs)")
    print(f"  - Tệp thiếu trên đĩa  : {len(missing_files)}")
    if status_5:
        print("  ✅ PASS: Cơ cấu 125 dòng SPK_0001 đạt chuẩn 100%")
    else:
        print(f"  ❌ FAIL: Sai lệch cơ cấu hoặc thiếu tệp âm thanh trên đĩa!")

    # ── TỔNG HỢP KIỂM TOÁN ───────────────────────────────────────────────────
    all_passed = status_1 and status_2 and status_3 and status_4 and status_5
    results["overall_pass"] = all_passed

    print("\n" + "=" * 80)
    print("🏆 KẾT LUẬN KIỂM TOÁN AN NINH MANIFEST V6:")
    print(f"  1. Zero-leakage 5 SPK nghiệm thu : {'✅ PASS' if status_1 else '❌ FAIL'}")
    print(f"  2. Cô lập SPK_0001 đúng tập      : {'✅ PASS' if status_2 else '❌ FAIL'}")
    print(f"  3. Hard Text-Disjoint            : {'✅ PASS' if status_3 else '❌ FAIL'}")
    print(f"  4. Bảo vệ Giả thuyết H2 (VieNeu) : {'✅ PASS' if status_4 else '❌ FAIL'}")
    print(f"  5. Cơ cấu 125 dòng SPK_0001      : {'✅ PASS' if status_5 else '❌ FAIL'}")
    print(f"  -> KẾT QUẢ CUỐI CÙNG              : {'✅ ĐẠT TIÊU CHUẨN AN NINH' if all_passed else '❌ CẦN KHẮC PHỤC'}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Audit manifest V6 security and data integrity")
    ap.add_argument("--train", default="data/manifests_zalo/train_zalo.csv")
    ap.add_argument("--dev", default="data/manifests_zalo/dev_zalo.csv")
    ap.add_argument("--test", default="data/manifests_zalo/test_indomain_zalo.csv")
    args = ap.parse_args()
    res = audit_v6_manifests(train_path=args.train, dev_path=args.dev, test_path=args.test)
    if not res["overall_pass"]:
        sys.exit(1)
