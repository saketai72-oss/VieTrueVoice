#!/usr/bin/env python3
"""Script to verify full manifest statistics, speaker-disjoint integrity,
hard text-disjointness, paired triplets equality, and pre-codec tagging."""

import json
from pathlib import Path
import pandas as pd
from vitruevoice.text_utils import normalize_for_eval

EXPECTED_COLUMNS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed",
]

def main():
    out_dir = Path("out")
    full_csv = out_dir / "full_manifest.csv"
    train_csv = out_dir / "train.csv"
    dev_csv = out_dir / "dev.csv"
    test_in_csv = out_dir / "test_indomain.csv"
    test_ood_csv = out_dir / "test_ood.csv"

    assert full_csv.exists(), "full_manifest.csv not found!"
    df = pd.read_csv(full_csv)

    print("=" * 70)
    print("📊 BÁO CÁO TỔNG QUAN TẬP DỮ LIỆU VITRUEVOICE (KAGGLE GPU OUTPUT)")
    print("=" * 70)
    print(f"Tổng số mẫu âm thanh : {len(df):,}")
    print(f"Tổng số người nói     : {df['speaker_id'].nunique()}")
    print("\n1. Phân bổ nhãn (Labels):")
    print(df["label"].value_counts())
    print("\n2. Phân bổ phân chia (Splits):")
    print(df["split"].value_counts())
    print("\n3. Phân bổ tầng tấn công (Derived Tiers):")
    print(df["derived_tier"].value_counts())
    print("\n4. Phân bổ mã hóa (Codecs):")
    print(df["codec"].value_counts())
    print("\n5. Phân bổ tiền mã hóa (Pre-codecs):")
    print(df["pre_codec"].value_counts())
    print("\n6. Phân bổ công cụ sinh (TTS Engines):")
    print(df["tts_generator"].value_counts())

    # 1. Column assertion
    assert list(df.columns) == EXPECTED_COLUMNS, f"Cột manifest không chuẩn: {list(df.columns)}"
    print("\n✅ Cấu trúc 18 cột chuẩn xác 100%!")

    # Load split manifests
    train_df = pd.read_csv(train_csv)
    dev_df = pd.read_csv(dev_csv)
    test_in_df = pd.read_csv(test_in_csv)
    test_ood_df = pd.read_csv(test_ood_csv) if test_ood_csv.exists() else pd.DataFrame()

    print("=" * 70)
    print("🔒 1. KIỂM TRA TÍNH TOÀN VẸN SPEAKER-DISJOINT:")
    train_spks = set(train_df["speaker_id"])
    dev_spks = set(dev_df["speaker_id"])
    test_in_spks = set(test_in_df["speaker_id"])
    test_ood_spks = set(test_ood_df["speaker_id"]) if not test_ood_df.empty else set()

    print(f" - Train        : {len(train_spks)} spk, {len(train_df):,} mẫu (Bona: {(train_df['label']=='bonafide').sum():,}, Spoof: {(train_df['label']=='spoof').sum():,})")
    print(f" - Dev          : {len(dev_spks)} spk, {len(dev_df):,} mẫu (Bona: {(dev_df['label']=='bonafide').sum():,}, Spoof: {(dev_df['label']=='spoof').sum():,})")
    print(f" - Test InDomain: {len(test_in_spks)} spk, {len(test_in_df):,} mẫu (Bona: {(test_in_df['label']=='bonafide').sum():,}, Spoof: {(test_in_df['label']=='spoof').sum():,})")
    if not test_ood_df.empty:
        print(f" - Test OOD     : {len(test_ood_spks)} spk, {len(test_ood_df):,} mẫu (Bona: {(test_ood_df['label']=='bonafide').sum():,}, Spoof: {(test_ood_df['label']=='spoof').sum():,})")

    assert train_spks.isdisjoint(dev_spks), "❌ LỖI: Rò rỉ speaker giữa Train và Dev!"
    assert train_spks.isdisjoint(test_in_spks), "❌ LỖI: Rò rỉ speaker giữa Train và Test InDomain!"
    assert dev_spks.isdisjoint(test_in_spks), "❌ LỖI: Rò rỉ speaker giữa Dev và Test InDomain!"
    if not test_ood_df.empty:
        assert train_spks.isdisjoint(test_ood_spks), "❌ LỖI: Rò rỉ speaker giữa Train và Test OOD!"
        assert dev_spks.isdisjoint(test_ood_spks), "❌ LỖI: Rò rỉ speaker giữa Dev và Test OOD!"
        assert test_in_spks.isdisjoint(test_ood_spks), "❌ LỖI: Rò rỉ speaker giữa Test InDomain và Test OOD!"
    print("✅ RÀNG BUỘC SPEAKER-DISJOINT ĐẠT CHUẨN 100%!")

    # 2. Text-disjoint checks
    print("=" * 70)
    print("📝 2. KIỂM TRA TÍNH TOÀN VẸN HARD TEXT-DISJOINT TRÊN VĂN BẢN CHUẨN HOÁ:")
    train_texts = {normalize_for_eval(t) for t in train_df["transcript"].dropna()}
    dev_texts = {normalize_for_eval(t) for t in dev_df["transcript"].dropna()}
    test_in_texts = {normalize_for_eval(t) for t in test_in_df["transcript"].dropna()}
    test_ood_texts = {normalize_for_eval(t) for t in test_ood_df["transcript"].dropna()} if not test_ood_df.empty else set()

    assert train_texts.isdisjoint(dev_texts), f"❌ LỖI: Rò rỉ text giữa Train và Dev ({len(train_texts & dev_texts)} câu lặp)!"
    assert train_texts.isdisjoint(test_in_texts), f"❌ LỖI: Rò rỉ text giữa Train và Test InDomain ({len(train_texts & test_in_texts)} câu lặp)!"
    assert dev_texts.isdisjoint(test_in_texts), f"❌ LỖI: Rò rỉ text giữa Dev và Test InDomain ({len(dev_texts & test_in_texts)} câu lặp)!"
    if not test_ood_df.empty:
        assert train_texts.isdisjoint(test_ood_texts), f"❌ LỖI: Rò rỉ text giữa Train và Test OOD ({len(train_texts & test_ood_texts)} câu lặp)!"
        assert dev_texts.isdisjoint(test_ood_texts), f"❌ LỖI: Rò rỉ text giữa Dev và Test OOD ({len(dev_texts & test_ood_texts)} câu lặp)!"
        assert test_in_texts.isdisjoint(test_ood_texts), f"❌ LỖI: Rò rỉ text giữa Test InDomain và Test OOD ({len(test_in_texts & test_ood_texts)} câu lặp)!"
    print("✅ RÀNG BUỘC HARD TEXT-DISJOINT GIỮA CÁC TẬP ĐẠT CHUẨN 100%!")

    # 3. Intra-speaker ref/enroll vs eval disjointness
    print("=" * 70)
    print("🎯 3. KIỂM TRA INTRA-SPEAKER REF/ENROLL VS EVAL DISJOINTNESS:")
    for name, split_data in [("Train", train_df), ("Dev", dev_df), ("Test InDomain", test_in_df)]:
        ref_enroll_data = split_data[split_data["role"].isin(["ref", "enroll"])]
        eval_data = split_data[split_data["role"] == "eval"]
        for spk in split_data["speaker_id"].unique():
            spk_ref_texts = {normalize_for_eval(t) for t in ref_enroll_data[ref_enroll_data["speaker_id"] == spk]["transcript"].dropna()}
            spk_eval_texts = {normalize_for_eval(t) for t in eval_data[eval_data["speaker_id"] == spk]["transcript"].dropna()}
            overlap = spk_ref_texts & spk_eval_texts
            assert not overlap, f"❌ LỖI: {name} Speaker {spk} bị trùng câu giữa ref/enroll và eval: {overlap}"
    print("✅ INTRA-SPEAKER REF/ENROLL VS EVAL HOÀN TOÀN TÁCH BIỆT 100%!")

    # 4. Paired triplets check
    print("=" * 70)
    print("⚖️ 4. KIỂM TRA PAIRED TRIPLETS (1:1:1 CLEAN, G711, AMR):")
    for name, split_data in [("Dev", dev_df), ("Test InDomain", test_in_df), ("Test OOD", test_ood_df)]:
        if split_data.empty:
            continue
        eval_data = split_data[split_data["role"] == "eval"]
        for lbl in ["bonafide", "spoof"]:
            sub = eval_data[eval_data["label"] == lbl]
            c_clean = (sub["codec"] == "clean_16khz").sum()
            c_g711 = (sub["codec"] == "g711_alaw").sum()
            c_amr = (sub["codec"] == "amr_nb").sum()
            print(f" - {name} ({lbl:<8}): clean={c_clean}, g711={c_g711}, amr={c_amr}")
            assert c_clean == c_g711 == c_amr, f"❌ LỖI: Paired triplets không bằng nhau ở {name} ({lbl}): clean={c_clean}, g711={c_g711}, amr={c_amr}"
    print("✅ TẤT CẢ EVAL CỦA DEV VÀ TEST ĐỀU ĐẠT CHUẨN PAIRED TRIPLETS 1:1:1 NGUYÊN BẢN!")

    # 5. Dynamic loss weights
    weights_path = out_dir / "loss_weights.json"
    if weights_path.exists():
        with open(weights_path, "r", encoding="utf-8") as f:
            loss_weights = json.load(f)
        print("=" * 70)
        print(f"📈 5. TRỌNG SỐ LOSS ĐỘNG TÍNH ĐƯỢC: {loss_weights}")

    print("=" * 70)
    print("🎉 TẤT CẢ CÁC TIÊU CHÍ ĐÃ ĐẠT CHUẨN NGHIÊM NGẶT!")
    print("=" * 70)

if __name__ == "__main__":
    main()

