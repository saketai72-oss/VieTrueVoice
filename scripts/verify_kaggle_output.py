#!/usr/bin/env python3
"""Script to verify full manifest statistics and speaker-disjoint integrity."""

import pandas as pd
from pathlib import Path

def main():
    full_csv = Path("out/full_manifest.csv")
    train_csv = Path("out/train.csv")
    dev_csv = Path("out/dev.csv")
    test_csv = Path("out/test_indomain.csv")

    assert full_csv.exists(), "full_manifest.csv not found!"
    df = pd.read_csv(full_csv)

    print("=" * 60)
    print("📊 BÁO CÁO TỔNG QUAN TẬP DỮ LIỆU VITRUEVOICE (KAGGLE GPU OUTPUT)")
    print("=" * 60)
    print(f"Tổng số mẫu âm thanh : {len(df):,}")
    print(f"Tổng số người nói     : {df['speaker_id'].nunique()}")
    print("\n1. Phân bổ nhãn (Labels):")
    print(df['label'].value_counts())
    print("\n2. Phân bổ phân chia (Splits):")
    print(df['split'].value_counts())
    print("\n3. Phân bổ tầng tấn công (Derived Tiers):")
    print(df['derived_tier'].value_counts())
    print("\n4. Phân bổ mã hóa (Codecs):")
    print(df['codec'].value_counts())
    print("\n5. Phân bổ công cụ sinh (TTS Engines):")
    print(df['tts_generator'].value_counts())

    train_df = pd.read_csv(train_csv)
    dev_df = pd.read_csv(dev_csv)
    test_df = pd.read_csv(test_csv)

    print("=" * 60)
    print("🔒 KIỂM TRA TÍNH TOÀN VẸN SPEAKER-DISJOINT (CHỐNG RÒ RỈ):")
    train_spks = set(train_df['speaker_id'])
    dev_spks = set(dev_df['speaker_id'])
    test_spks = set(test_df['speaker_id'])

    print(f" - Tập Train : {len(train_spks)} người nói, {len(train_df):,} mẫu (Bona: {(train_df['label']=='bonafide').sum():,}, Spoof: {(train_df['label']=='spoof').sum():,})")
    print(f" - Tập Dev   : {len(dev_spks)} người nói, {len(dev_df):,} mẫu (Bona: {(dev_df['label']=='bonafide').sum():,}, Spoof: {(dev_df['label']=='spoof').sum():,})")
    print(f" - Tập Test  : {len(test_spks)} người nói, {len(test_df):,} mẫu (Bona: {(test_df['label']=='bonafide').sum():,}, Spoof: {(test_df['label']=='spoof').sum():,})")

    assert train_spks.isdisjoint(dev_spks), "❌ LỖI: Rò rỉ người nói giữa Train và Dev!"
    assert train_spks.isdisjoint(test_spks), "❌ LỖI: Rò rỉ người nói giữa Train và Test!"
    assert dev_spks.isdisjoint(test_spks), "❌ LỖI: Rò rỉ người nói giữa Dev và Test!"
    assert len(train_spks) + len(dev_spks) + len(test_spks) == df['speaker_id'].nunique(), "❌ LỖI: Tổng người nói không khớp!"

    print("✅ TOÀN BỘ 3 TẬP TRAIN / DEV / TEST ĐẠT CHUẨN SPEAKER-DISJOINT 100%!")
    print("=" * 60)

if __name__ == "__main__":
    main()
