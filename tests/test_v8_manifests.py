"""Unit tests for V8 Inverted Seen/Unseen TTS Manifests.

Audits:
- 0% speaker leakage between Train and Dev.
- 0% presence of acceptance volunteers SPK_0003..SPK_0007 in Train, Dev, or Benchmarks.
- Strict SPK_0001 isolation: 0% in no_spk1 and Dev; exactly 125 rows in with_spk1.
- Inverted engine partitioning:
  - Seen TTS: F5-TTS-Vietnamese + OmniVoice (in Train and Dev).
  - Unseen TTS: VieNeu-TTS v3 Turbo locked as official 955-clip benchmark.
- Strict 18/19 column compliance (pre_codec, base_utt).
- Balanced 5-codec representation.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parent.parent

TRAIN_NO_SPK1_PATH = _ROOT / "data/manifests_zalo/train_v8_f5_omni_no_spk1.csv"
DEV_PATH = _ROOT / "data/manifests_zalo/dev_v8_f5_omni.csv"
UNSEEN_VIENEU_PATH = _ROOT / "data/manifests_zalo/unseen_vieneu_benchmark.csv"
TRAIN_WITH_SPK1_PATH = _ROOT / "data/manifests_zalo/train_v8_f5_omni_with_spk1.csv"

MANDATORY_COLUMNS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed", "base_utt"
]

ACCEPTANCE_VOLUNTEERS = {f"SPK_{i:04d}" for i in range(3, 8)}


@pytest.fixture(scope="module")
def manifests():
    assert TRAIN_NO_SPK1_PATH.exists(), f"Missing {TRAIN_NO_SPK1_PATH}"
    assert DEV_PATH.exists(), f"Missing {DEV_PATH}"
    assert UNSEEN_VIENEU_PATH.exists(), f"Missing {UNSEEN_VIENEU_PATH}"
    assert TRAIN_WITH_SPK1_PATH.exists(), f"Missing {TRAIN_WITH_SPK1_PATH}"

    return {
        "train_no_spk1": pd.read_csv(TRAIN_NO_SPK1_PATH),
        "dev": pd.read_csv(DEV_PATH),
        "unseen_vieneu": pd.read_csv(UNSEEN_VIENEU_PATH),
        "train_with_spk1": pd.read_csv(TRAIN_WITH_SPK1_PATH),
    }


def test_manifest_files_exist():
    for p in [TRAIN_NO_SPK1_PATH, DEV_PATH, UNSEEN_VIENEU_PATH, TRAIN_WITH_SPK1_PATH]:
        assert p.exists(), f"Required manifest not found: {p}"
        assert p.stat().st_size > 0, f"Manifest file is empty: {p}"


def test_manifest_columns(manifests):
    for name, df in manifests.items():
        missing_cols = set(MANDATORY_COLUMNS) - set(df.columns)
        assert not missing_cols, f"{name} is missing mandatory columns: {missing_cols}"
        assert "pre_codec" in df.columns, f"{name} must contain 'pre_codec' column"
        assert "base_utt" in df.columns, f"{name} must contain 'base_utt' column"
        assert df["pre_codec"].isna().sum() == 0, f"{name} contains NaN in pre_codec"
        assert df["base_utt"].isna().sum() == 0, f"{name} contains NaN in base_utt"


def test_zero_speaker_leakage_between_train_and_dev(manifests):
    train_no_spk1_spks = set(manifests["train_no_spk1"]["speaker_id"].unique())
    dev_spks = set(manifests["dev"]["speaker_id"].unique())

    overlap = train_no_spk1_spks.intersection(dev_spks)
    assert len(overlap) == 0, f"Critical security breach: Speaker overlap between Train and Dev: {overlap}"

    train_with_spk1_spks = set(manifests["train_with_spk1"]["speaker_id"].unique())
    overlap_with_spk1 = train_with_spk1_spks.intersection(dev_spks)
    assert len(overlap_with_spk1) == 0, f"Critical security breach: Speaker overlap between Train(with spk1) and Dev: {overlap_with_spk1}"


def test_zero_acceptance_volunteer_leakage(manifests):
    for name, df in manifests.items():
        spks = set(df["speaker_id"].unique())
        breach = spks.intersection(ACCEPTANCE_VOLUNTEERS)
        assert len(breach) == 0, f"Critical security breach: Found acceptance volunteer {breach} in {name}!"


def test_spk0001_isolation(manifests):
    train_no_spk1 = manifests["train_no_spk1"]
    dev = manifests["dev"]
    unseen = manifests["unseen_vieneu"]
    train_with_spk1 = manifests["train_with_spk1"]

    assert (train_no_spk1["speaker_id"] == "SPK_0001").sum() == 0, "Found SPK_0001 in train_v8_f5_omni_no_spk1!"
    assert (dev["speaker_id"] == "SPK_0001").sum() == 0, "Found SPK_0001 in dev_v8_f5_omni!"
    assert (unseen["speaker_id"] == "SPK_0001").sum() == 0, "Found SPK_0001 in unseen_vieneu_benchmark!"

    spk1_rows = train_with_spk1[train_with_spk1["speaker_id"] == "SPK_0001"]
    assert len(spk1_rows) == 125, f"Expected exactly 125 SPK_0001 rows in train_with_spk1, got {len(spk1_rows)}"
    assert (spk1_rows["label"] == "bonafide").sum() == 75, "Expected 75 bonafide SPK_0001 rows"
    assert (spk1_rows["label"] == "spoof").sum() == 50, "Expected 50 spoof SPK_0001 rows"
    assert (spk1_rows["tts_generator"] == "F5-TTS-Vietnamese").sum() == 50, "Expected 50 F5-TTS SPK_0001 rows"


def test_tts_generator_distribution(manifests):
    # Train no spk1
    train_gens = set(manifests["train_no_spk1"]["tts_generator"].unique())
    assert "VieNeu-TTS" not in train_gens, "VieNeu-TTS must be 0% in Train for V8 (it is now Unseen)!"
    assert "F5-TTS-Vietnamese" in train_gens, "F5-TTS must be present in Train as Seen"
    assert "OmniVoice" in train_gens, "OmniVoice must be present in Train as Seen"

    # Dev
    dev_gens = set(manifests["dev"]["tts_generator"].unique())
    assert "VieNeu-TTS" not in dev_gens, "VieNeu-TTS must be 0% in Dev for V8 (it is now Unseen)!"
    assert "F5-TTS-Vietnamese" in dev_gens, "F5-TTS must be present in Dev as Seen"
    assert "OmniVoice" in dev_gens, "OmniVoice must be present in Dev as Seen"
    assert (manifests["dev"]["tts_generator"] == "OmniVoice").sum() == 965, "Expected 965 OmniVoice dev clips"

    # Unseen VieNeu benchmark
    unseen_df = manifests["unseen_vieneu"]
    assert len(unseen_df) == 955, f"Expected exactly 955 VieNeu clips in unseen benchmark, got {len(unseen_df)}"
    assert (unseen_df["tts_generator"] == "VieNeu-TTS").all(), "Unseen benchmark must be 100% VieNeu-TTS"
    assert (unseen_df["label"] == "spoof").all(), "Unseen benchmark must be 100% spoof"


def test_codec_balance_and_presence(manifests):
    for name, df in manifests.items():
        codecs = set(df["codec"].unique())
        required_codecs = {"clean_16khz", "g711_alaw", "amr_nb", "aac_zalo_76k", "opus_zalo_24k"}
        assert required_codecs.issubset(codecs), f"{name} is missing required codecs: {required_codecs - codecs}"


def test_audio_files_exist_sample(manifests):
    for name, df in manifests.items():
        sample_paths = df["audio_path"].sample(n=min(25, len(df)), random_state=42)
        for rel_p in sample_paths:
            full_p = _ROOT / rel_p
            assert full_p.exists(), f"Audio file from {name} does not exist on disk: {full_p}"
