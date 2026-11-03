"""Unit tests for Phase 1 Deep Voice pipeline (TDD).

Verifies:
1. TSV metadata parsing and client_id speaker mapping in scan_deep_voices.
2. Leakage prevention: strictly rejects SPK_xxxx, dev/test speaker overlap, and base_utt overlap.
3. Schema integrity: valid duration_sec, real transcript, NaN similarity metrics for bonafide, valid role in train split.
"""

from __future__ import annotations
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import soundfile as sf

from scripts.scan_deep_voices import scan_deep_voices_from_tsv
from scripts.generate_zalo_paired_manifests import merge_deep_voice_pool, generate_paired_manifest


@pytest.fixture
def mock_cv_env(tmp_path):
    """Tạo môi trường giả lập Common Voice 8.0 với validated.tsv và các file audio."""
    clips_dir = tmp_path / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    sr = 16000

    # Speaker 1: Giọng trầm (sin wave 100 Hz), 3 clips
    spk1_id = "client_abc123_deep_male"
    for i in range(3):
        t = np.linspace(0, 3.0, 3 * sr)
        wav = (0.5 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)
        sf.write(clips_dir / f"clip_spk1_{i}.wav", wav, sr)

    # Speaker 2: Giọng cao (sin wave 220 Hz), 3 clips
    spk2_id = "client_xyz789_high_female"
    for i in range(3):
        t = np.linspace(0, 3.0, 3 * sr)
        wav = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        sf.write(clips_dir / f"clip_spk2_{i}.wav", wav, sr)

    tsv_data = [
        {"client_id": spk1_id, "path": "clip_spk1_0.wav", "sentence": "tôi là giọng nam trầm câu một"},
        {"client_id": spk1_id, "path": "clip_spk1_1.wav", "sentence": "tôi là giọng nam trầm câu hai"},
        {"client_id": spk1_id, "path": "clip_spk1_2.wav", "sentence": "tôi là giọng nam trầm câu ba"},
        {"client_id": spk2_id, "path": "clip_spk2_0.wav", "sentence": "tôi là giọng nữ bổng câu một"},
        {"client_id": spk2_id, "path": "clip_spk2_1.wav", "sentence": "tôi là giọng nữ bổng câu hai"},
        {"client_id": spk2_id, "path": "clip_spk2_2.wav", "sentence": "tôi là giọng nữ bổng câu ba"},
    ]
    tsv_path = tmp_path / "validated.tsv"
    pd.DataFrame(tsv_data).to_csv(tsv_path, sep="\t", index=False)

    return tmp_path, tsv_path, clips_dir


def test_scan_deep_voices_tsv_mapping(mock_cv_env):
    tmp_path, tsv_path, clips_dir = mock_cv_env
    out_csv = tmp_path / "deep_voice_pool.csv"

    df_out = scan_deep_voices_from_tsv(
        tsv_path=tsv_path,
        audio_root=clips_dir,
        out_csv=out_csv,
        f0_max=125.0,
        min_clips=2,
    )

    assert len(df_out) == 3
    # Phải bắt đúng speaker 1, loại bỏ speaker 2
    assert (df_out["speaker_id"].str.contains("abc123")).all()
    # Phải có transcript thật không rỗng
    assert (df_out["transcript"].str.startswith("tôi là giọng nam trầm")).all()
    # Duration phải đo thực tế (~3.0s)
    assert df_out["duration_sec"].iloc[0] == pytest.approx(3.0, abs=0.1)
    # F0 đo được phải xấp xỉ 100 Hz
    assert df_out["f0_median"].iloc[0] == pytest.approx(100.0, abs=10.0)


def test_merge_deep_voice_pool_leakage_prevention():
    # Tạo dev_df và test_df có speaker hiện hữu
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])
    train_df = pd.DataFrame([{"speaker_id": "spk_tr_01", "base_utt": "utt_tr_01"}])

    # Pool 1: Chứa SPK_0001 (bị cấm theo STUBBORN_FACT)
    pool_leak_spk = pd.DataFrame([{
        "utt_id": "clip_01", "audio_path": "clip_01.wav", "speaker_id": "SPK_0001",
        "transcript": "câu thử", "duration_sec": 3.0, "f0_median": 105.0
    }])
    with pytest.raises(ValueError, match="SPK_xxxx"):
        merge_deep_voice_pool(train_df, dev_df, test_df, pool_leak_spk)

    # Pool 2: Chứa speaker trùng với dev_df
    pool_leak_dev = pd.DataFrame([{
        "utt_id": "clip_02", "audio_path": "clip_02.wav", "speaker_id": "spk_dev_01",
        "transcript": "câu thử", "duration_sec": 3.0, "f0_median": 105.0
    }])
    with pytest.raises(ValueError, match="Speaker overlap"):
        merge_deep_voice_pool(train_df, dev_df, test_df, pool_leak_dev)

    # Pool 3: Chứa base_utt trùng với test_df
    pool_leak_utt = pd.DataFrame([{
        "utt_id": "utt_test_01", "audio_path": "clip_03.wav", "speaker_id": "spk_new_99",
        "transcript": "câu thử", "duration_sec": 3.0, "f0_median": 105.0
    }])
    with pytest.raises(ValueError, match="Base utterance overlap"):
        merge_deep_voice_pool(train_df, dev_df, test_df, pool_leak_utt)


def test_merge_deep_voice_pool_schema_integrity():
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])
    train_df = pd.DataFrame([{
        "utt_id": "u_tr_01", "audio_path": "tr.wav", "speaker_id": "spk_tr_01",
        "source": "vivos", "label": "bonafide", "role": "train", "codec": "clean_16khz",
        "split": "train", "duration_sec": 4.0, "transcript": "gốc",
        "raw_wer": np.nan, "raw_cer": np.nan, "ecapa_sim": np.nan, "wavlm_sim": np.nan,
        "base_utt": "u_tr_01"
    }])

    valid_pool = pd.DataFrame([{
        "utt_id": "clip_valid_01", "audio_path": "valid_01.wav", "speaker_id": "CV_deep_spk_88",
        "transcript": "câu nói thật của giọng nam trầm", "duration_sec": 3.45, "f0_median": 110.0
    }])

    merged = merge_deep_voice_pool(train_df, dev_df, test_df, valid_pool)

    # Kiểm tra số lượng
    assert len(merged) == 2
    row = merged[merged["utt_id"] == "clip_valid_01"].iloc[0]

    # Kiểm tra Lỗi 1: role không được là "eval" khi split là "train"
    assert row["role"] != "eval"
    assert row["role"] == "train"

    # Kiểm tra Lỗi 2: duration_sec phải là số đo thật, metrics similarity phải là NaN cho bona fide
    assert row["duration_sec"] == pytest.approx(3.45)
    assert row["transcript"] == "câu nói thật của giọng nam trầm"
    assert np.isnan(row["raw_wer"])
    assert np.isnan(row["ecapa_sim"])
    assert np.isnan(row["wavlm_sim"])


def test_merge_deep_voice_pool_train_without_base_utt():
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])
    # train_df lacks base_utt column completely
    train_df = pd.DataFrame([{
        "utt_id": "u_tr_01_clean", "audio_path": "tr.wav", "speaker_id": "spk_tr_01",
        "source": "vivos", "label": "bonafide", "role": "train", "codec": "clean_16khz",
        "split": "train", "duration_sec": 4.0, "transcript": "gốc",
    }])

    valid_pool = pd.DataFrame([{
        "utt_id": "clip_valid_01", "audio_path": "valid_01.wav", "speaker_id": "CV_deep_spk_88",
        "transcript": "giọng trầm", "duration_sec": 3.45, "f0_median": 110.0
    }])

    merged = merge_deep_voice_pool(train_df, dev_df, test_df, valid_pool)
    assert "base_utt" in merged.columns
    assert merged["base_utt"].isna().sum() == 0
    assert merged.loc[merged["utt_id"] == "u_tr_01_clean", "base_utt"].iloc[0] == "u_tr_01"

    paired = generate_paired_manifest(merged)
    assert paired["base_utt"].isna().sum() == 0
    assert paired["utt_id"].isna().sum() == 0


def test_scan_deep_voices_caching_and_orig_path(mock_cv_env):
    tmp_path, tsv_path, clips_dir = mock_cv_env
    cache_file = tmp_path / "deep_voice_f0_cache.json"
    out_csv = tmp_path / "deep_voice_pool.csv"

    # Lần 1: Chưa có cache
    assert not cache_file.exists()
    df1 = scan_deep_voices_from_tsv(
        tsv_path=tsv_path,
        audio_root=clips_dir,
        out_csv=out_csv,
        f0_max=125.0,
        min_clips=2,
        cache_file=cache_file,
        max_dur_sec=8.0,
    )
    assert len(df1) == 3
    assert cache_file.exists()
    assert "orig_audio_path" in df1.columns

    # Lần 2: Nạp từ cache
    df2 = scan_deep_voices_from_tsv(
        tsv_path=tsv_path,
        audio_root=clips_dir,
        out_csv=out_csv,
        f0_max=125.0,
        min_clips=2,
        cache_file=cache_file,
        max_dur_sec=8.0,
    )
    assert len(df2) == 3
    pd.testing.assert_frame_equal(df1, df2)

    # Kiểm tra merge bảo toàn orig_audio_path
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])
    train_df = pd.DataFrame([{
        "utt_id": "u_tr_01", "audio_path": "tr.wav", "speaker_id": "spk_tr_01",
        "source": "vivos", "label": "bonafide", "role": "train", "codec": "clean_16khz",
        "split": "train", "duration_sec": 4.0, "transcript": "gốc",
        "raw_wer": np.nan, "raw_cer": np.nan, "ecapa_sim": np.nan, "wavlm_sim": np.nan,
        "base_utt": "u_tr_01"
    }])
    merged = merge_deep_voice_pool(train_df, dev_df, test_df, df1)
    assert "orig_audio_path" in merged.columns
    assert merged[merged["source"] == "common_voice_deep"]["orig_audio_path"].notna().all()


def test_preaugment_deep_voices_offline(tmp_path):
    from scripts.generate_zalo_paired_manifests import preaugment_deep_voices
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    wav = (0.5 * np.sin(2 * np.pi * 150 * t)).astype(np.float32)
    sf.write(audio_dir / "clip_tr_01.wav", wav, sr)

    train_df = pd.DataFrame([
        {
            "utt_id": "clip_tr_01", "base_utt": "clip_tr_01", "audio_path": "clip_tr_01.wav",
            "speaker_id": "spk_tr_01", "label": "bonafide", "codec": "clean_16khz",
            "role": "train", "split": "train", "duration_sec": 1.0, "transcript": "test câu"
        },
        {
            # SPK_0001 (phải bị lọc bỏ)
            "utt_id": "clip_spk_01", "base_utt": "clip_spk_01", "audio_path": "clip_spk_01.wav",
            "speaker_id": "SPK_0001", "label": "bonafide", "codec": "clean_16khz",
            "role": "train", "split": "train", "duration_sec": 1.0, "transcript": "volunteer"
        }
    ])
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])

    out_audio = tmp_path / "out_audio"
    aug_df = preaugment_deep_voices(
        train_df, dev_df, test_df,
        audio_root=audio_dir,
        out_audio_dir=out_audio,
        n_samples=5,
        semitones_range=(-6.0, -4.0),
    )

    assert len(aug_df) == 1
    row = aug_df.iloc[0]
    assert row["role"] == "train"
    assert row["source"] == "deep_pitch_augmented"
    assert "SPK_" not in row["speaker_id"]
    assert (out_audio / row["audio_path"]).exists()


def test_merge_deep_voice_pool_dedup_train():
    dev_df = pd.DataFrame([{"speaker_id": "spk_dev_01", "base_utt": "utt_dev_01"}])
    test_df = pd.DataFrame([{"speaker_id": "spk_test_01", "base_utt": "utt_test_01"}])
    train_df = pd.DataFrame([
        {
            "utt_id": "u_tr_01_clean", "audio_path": "tr01.wav", "speaker_id": "spk_tr_01",
            "source": "vivos", "label": "bonafide", "role": "train", "codec": "clean_16khz",
            "split": "train", "duration_sec": 4.0, "transcript": "gốc 1", "base_utt": "u_tr_01"
        },
        {
            "utt_id": "u_tr_02_clean", "audio_path": "tr02.wav", "speaker_id": "spk_tr_02",
            "source": "vivos", "label": "bonafide", "role": "train", "codec": "clean_16khz",
            "split": "train", "duration_sec": 3.0, "transcript": "gốc 2", "base_utt": "u_tr_02"
        }
    ])

    pool_df = pd.DataFrame([
        {
            # Trùng base_utt u_tr_01 -> PHẢI BỊ LỌC BỎ
            "utt_id": "u_tr_01", "audio_path": "pool01.wav", "speaker_id": "CV_deep_spk_01",
            "transcript": "trùng với train", "duration_sec": 4.0, "f0_median": 115.0, "base_utt": "u_tr_01"
        },
        {
            # Mới hoàn toàn -> ĐƯỢC GIỮ LẠI
            "utt_id": "u_tr_03", "audio_path": "pool03.wav", "speaker_id": "CV_deep_spk_03",
            "transcript": "mới trầm", "duration_sec": 3.5, "f0_median": 105.0, "base_utt": "u_tr_03"
        }
    ])

    merged = merge_deep_voice_pool(train_df, dev_df, test_df, pool_df)
    # train có 2 + pool có 1 mới = 3
    assert len(merged) == 3
    assert "u_tr_03" in merged["base_utt"].values
    # u_tr_01 chỉ xuất hiện đúng 1 lần (từ train_df gốc)
    assert (merged["base_utt"] == "u_tr_01").sum() == 1
    assert merged.loc[merged["base_utt"] == "u_tr_01", "speaker_id"].iloc[0] == "spk_tr_01"

    paired = generate_paired_manifest(merged)
    # Mỗi base_utt có đúng 1 clean, 1 aac, 1 opus
    for b_utt in ["u_tr_01", "u_tr_02", "u_tr_03"]:
        sub = paired[paired["base_utt"] == b_utt]
        assert len(sub) == 3
        assert set(sub["codec"]) == {"clean_16khz", "aac_zalo_76k", "opus_zalo_24k"}

