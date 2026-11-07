"""Unit tests for SPK_0001 migration to train split and 5-acceptance-volunteer isolation."""

from pathlib import Path
import pandas as pd
import pytest

from scripts.migrate_spk0001_to_train import build_spk0001_rows, migrate_spk0001
from scripts.generate_zalo_paired_manifests import ACCEPTANCE_VOLUNTEERS, validate_split_leakage
from scripts.train import validate_manifest


EXPECTED_COLUMNS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed", "base_utt"
]


def test_build_spk0001_rows_structure_and_constraints():
    """Verify build_spk0001_rows produces exactly 125 valid rows conforming to all constraints."""
    rows = build_spk0001_rows()
    df = pd.DataFrame(rows)

    # 1. Total row count and label balance
    assert len(df) == 125
    bona_df = df[df["label"] == "bonafide"]
    spoof_df = df[df["label"] == "spoof"]
    assert len(bona_df) == 75
    assert len(spoof_df) == 50

    # 2. Strict H2 Unseen TTS preservation: 0% VieNeu
    assert not df["audio_path"].str.contains("vieneu", case=False).any()
    assert not df["tts_generator"].str.contains("vieneu", case=False).any()
    assert set(spoof_df["tts_generator"].unique()) == {"F5-TTS-Vietnamese"}
    assert set(bona_df["tts_generator"].unique()) == {"none"}

    # 3. Codec distribution (all 5 codecs present equally)
    expected_codecs = {"clean_16khz", "aac_zalo_76k", "opus_zalo_24k", "amr_nb", "g711_alaw"}
    assert set(df["codec"].unique()) == expected_codecs
    for c in expected_codecs:
        assert (bona_df["codec"] == c).sum() == 15
        assert (spoof_df["codec"] == c).sum() == 10

    # 4. Audio files existence on disk
    for path_str in df["audio_path"]:
        p = Path(path_str)
        assert p.is_file(), f"Audio file does not exist: {p}"

    # 5. Schema integrity (19 columns)
    assert list(df.columns) == EXPECTED_COLUMNS

    # 6. Speaker ID isolation
    assert set(df["speaker_id"].unique()) == {"SPK_0001"}
    assert not set(df["speaker_id"].unique()).intersection(ACCEPTANCE_VOLUNTEERS)


def test_migration_manifest_clean_and_leak_free():
    """Verify live train_zalo.csv contains SPK_0001 and passes all leakage checks."""
    train_path = Path("data/manifests_zalo/train_zalo.csv")
    dev_path = Path("data/manifests_zalo/dev_zalo.csv")
    test_path = Path("data/manifests_zalo/test_indomain_zalo.csv")

    assert train_path.exists()
    assert dev_path.exists()
    assert test_path.exists()

    train_df = pd.read_csv(train_path)
    dev_df = pd.read_csv(dev_path)
    test_df = pd.read_csv(test_path)

    # 1. Total row count includes 125 SPK_0001 rows
    spk1_in_train = train_df[train_df["speaker_id"] == "SPK_0001"]
    assert len(spk1_in_train) == 125
    assert len(train_df) == 50710

    # 2. Acceptance volunteers must NOT be in train, dev, or test
    for split_name, d in [("train", train_df), ("dev", dev_df), ("test", test_df)]:
        spks = set(d["speaker_id"].astype(str).unique())
        assert not spks.intersection(ACCEPTANCE_VOLUNTEERS), f"Found acceptance volunteer in {split_name}"

    # 3. SPK_0001 must NOT be in dev or test
    assert "SPK_0001" not in set(dev_df["speaker_id"].astype(str).unique())
    assert "SPK_0001" not in set(test_df["speaker_id"].astype(str).unique())

    # 4. Zero text leakage
    spk1_texts = set(spk1_in_train["transcript"].dropna().str.strip().str.lower().unique())
    dev_texts = set(dev_df["transcript"].dropna().str.strip().str.lower().unique())
    test_texts = set(test_df["transcript"].dropna().str.strip().str.lower().unique())

    assert len(spk1_texts.intersection(dev_texts)) == 0
    assert len(spk1_texts.intersection(test_texts)) == 0

    # 5. Core validation functions pass
    validate_split_leakage(train_df, dev_df, test_df)
    validate_manifest(train_df, "train")
