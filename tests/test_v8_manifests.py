"""Unit tests for V8.1 Inverted Seen/Unseen TTS Manifests (Symmetric 1:1 OmniVoice_CFM).

Audits:
- Exact V8.1 row counts:
  * train_v8_f5_omni_no_spk1.csv   : 54,225
  * train_v8_f5_omni_with_spk1.csv : 54,400
  * dev_v8_f5_omni.csv             : 12,405
  * test_indomain_v8_f5_omni.csv   : 15,980
  * unseen_vieneu_benchmark.csv    :    955
- 0% speaker and base_utt leakage across Train, Dev, and Test.
- 0% presence of acceptance volunteers SPK_0003..SPK_0007 in all 5 manifests.
- Strict SPK_0001 isolation: 0% in no_spk1, dev, test, unseen; exact 175 rows in with_spk1
  (75 bonafide + 50 F5-TTS-Vietnamese + 50 OmniVoice), 0% transcript overlap with Dev/Test.
- Inverted engine partitioning:
  * Seen TTS: F5-TTS-Vietnamese + OmniVoice in Train, Dev, and Test In-Domain.
  * Unseen TTS: VieNeu-TTS v3 Turbo locked as 955-clip benchmark.
- Strict 19-column schema, valid source attribution, POSIX relative paths, balanced 5 codecs.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import pandas as pd
import pytest

_ROOT = Path(__file__).resolve().parent.parent

TRAIN_NO_SPK1_PATH = _ROOT / "data/manifests_zalo/train_v8_f5_omni_no_spk1.csv"
TRAIN_WITH_SPK1_PATH = _ROOT / "data/manifests_zalo/train_v8_f5_omni_with_spk1.csv"
DEV_PATH = _ROOT / "data/manifests_zalo/dev_v8_f5_omni.csv"
TEST_INDOMAIN_PATH = _ROOT / "data/manifests_zalo/test_indomain_v8_f5_omni.csv"
UNSEEN_VIENEU_PATH = _ROOT / "data/manifests_zalo/unseen_vieneu_benchmark.csv"

EXPECTED_ROW_COUNTS = {
    "train_no_spk1": 54225,
    "train_with_spk1": 54400,
    "dev": 12405,
    "test_indomain": 15980,
    "unseen_vieneu": 955,
}

MANDATORY_COLUMNS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed", "base_utt",
]

REQUIRED_CODECS = {"clean_16khz", "g711_alaw", "amr_nb", "aac_zalo_76k", "opus_zalo_24k"}
VALID_SOURCES = {"vivos", "common_voice", "deep_pitch_augmented", "volunteer_deep", "volunteer_consent"}
ACCEPTANCE_VOLUNTEERS = {f"SPK_{i:04d}" for i in range(3, 8)}


def _load_normalize_for_eval():
    spec = importlib.util.spec_from_file_location("text_utils", _ROOT / "src/vitruevoice/text_utils.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.normalize_for_eval


@pytest.fixture(scope="module")
def manifests():
    paths = {
        "train_no_spk1": TRAIN_NO_SPK1_PATH,
        "train_with_spk1": TRAIN_WITH_SPK1_PATH,
        "dev": DEV_PATH,
        "test_indomain": TEST_INDOMAIN_PATH,
        "unseen_vieneu": UNSEEN_VIENEU_PATH,
    }
    for name, p in paths.items():
        assert p.exists(), f"Missing manifest {name}: {p}"
    return {name: pd.read_csv(p) for name, p in paths.items()}


def test_manifest_files_exist():
    for p in [
        TRAIN_NO_SPK1_PATH,
        TRAIN_WITH_SPK1_PATH,
        DEV_PATH,
        TEST_INDOMAIN_PATH,
        UNSEEN_VIENEU_PATH,
    ]:
        assert p.exists(), f"Required manifest not found: {p}"
        assert p.stat().st_size > 0, f"Manifest file is empty: {p}"


def test_manifest_row_counts(manifests):
    for name, expected_n in EXPECTED_ROW_COUNTS.items():
        actual_n = len(manifests[name])
        assert actual_n == expected_n, f"{name}: expected {expected_n} rows, got {actual_n}"


def test_manifest_columns_and_posix_paths(manifests):
    non_null_cols = [
        "utt_id", "audio_path", "speaker_id", "source", "label", "role",
        "tts_generator", "codec", "pre_codec", "split", "transcript", "base_utt",
    ]
    for name, df in manifests.items():
        assert list(df.columns) == MANDATORY_COLUMNS, f"{name} schema mismatch: {list(df.columns)}"
        for col in non_null_cols:
            na_cnt = int(df[col].isna().sum())
            assert na_cnt == 0, f"{name} has {na_cnt} NaN values in column '{col}'"
        paths = df["audio_path"].astype(str)
        assert not paths.str.contains("\\", regex=False).any(), f"{name} contains backslash in audio_path"
        assert not paths.str.contains(":", regex=False).any(), f"{name} contains absolute drive path in audio_path"


def test_source_column_integrity(manifests):
    for name, df in manifests.items():
        sources = set(df["source"].astype(str).unique())
        invalid = sources - VALID_SOURCES
        assert not invalid, f"{name} contains invalid source labels: {invalid}"

        omni = df[df["tts_generator"] == "OmniVoice"]
        if len(omni) > 0:
            vivos_bad = omni[omni["speaker_id"].str.startswith("VIVOS") & (omni["source"] != "vivos")]
            cv_bad = omni[omni["speaker_id"].str.startswith("CV_") & (omni["source"] != "common_voice")]
            spk_bad = omni[omni["speaker_id"].str.startswith("SPK_") & (omni["source"] != "volunteer_consent")]
            assert len(vivos_bad) == 0, f"{name}: OmniVoice VIVOS rows have wrong source"
            assert len(cv_bad) == 0, f"{name}: OmniVoice CV rows have wrong source"
            assert len(spk_bad) == 0, f"{name}: OmniVoice SPK rows have wrong source"


def test_zero_speaker_and_base_utt_leakage(manifests):
    pairs = [
        ("train_no_spk1", "dev"),
        ("train_no_spk1", "test_indomain"),
        ("train_with_spk1", "dev"),
        ("train_with_spk1", "test_indomain"),
        ("dev", "test_indomain"),
    ]
    for a, b in pairs:
        spks_a = set(manifests[a]["speaker_id"].astype(str).unique())
        spks_b = set(manifests[b]["speaker_id"].astype(str).unique())
        assert len(spks_a & spks_b) == 0, f"Speaker overlap between {a} and {b}: {spks_a & spks_b}"

        bu_a = set(manifests[a]["base_utt"].astype(str).unique())
        bu_b = set(manifests[b]["base_utt"].astype(str).unique())
        assert len(bu_a & bu_b) == 0, f"base_utt overlap between {a} and {b}: {len(bu_a & bu_b)}"


def test_zero_acceptance_volunteer_leakage(manifests):
    for name, df in manifests.items():
        spks = set(df["speaker_id"].astype(str).unique())
        breach = spks.intersection(ACCEPTANCE_VOLUNTEERS)
        assert len(breach) == 0, f"Found acceptance volunteer {breach} in {name}!"
        for v in ACCEPTANCE_VOLUNTEERS:
            assert not df["audio_path"].astype(str).str.contains(v, regex=False).any(), (
                f"Found acceptance volunteer {v} path in {name}!"
            )


def test_spk0001_isolation_and_composition(manifests):
    for name in ("train_no_spk1", "dev", "test_indomain", "unseen_vieneu"):
        cnt = int((manifests[name]["speaker_id"] == "SPK_0001").sum())
        assert cnt == 0, f"Found {cnt} SPK_0001 rows in {name}!"

    tr_with = manifests["train_with_spk1"]
    spk1 = tr_with[tr_with["speaker_id"] == "SPK_0001"]
    assert len(spk1) == 175, f"Expected 175 SPK_0001 rows in train_with_spk1, got {len(spk1)}"
    assert int((spk1["label"] == "bonafide").sum()) == 75
    assert int((spk1["tts_generator"] == "F5-TTS-Vietnamese").sum()) == 50
    assert int((spk1["tts_generator"] == "OmniVoice").sum()) == 50
    assert int((spk1["tts_generator"] == "VieNeu-TTS").sum()) == 0
    assert spk1[spk1["tts_generator"] == "OmniVoice"]["transcript"].isna().sum() == 0

    normalize_for_eval = _load_normalize_for_eval()
    spk1_texts = {normalize_for_eval(t) for t in spk1["transcript"].astype(str).unique() if normalize_for_eval(t)}
    dev_texts = {normalize_for_eval(t) for t in manifests["dev"]["transcript"].astype(str).unique() if normalize_for_eval(t)}
    test_texts = {normalize_for_eval(t) for t in manifests["test_indomain"]["transcript"].astype(str).unique() if normalize_for_eval(t)}
    assert len(spk1_texts & dev_texts) == 0, "SPK_0001 transcript leaked into Dev!"
    assert len(spk1_texts & test_texts) == 0, "SPK_0001 transcript leaked into Test!"


def test_tts_generator_distribution(manifests):
    expected_gens = {
        "train_no_spk1": {"none": 46925, "F5-TTS-Vietnamese": 3660, "OmniVoice": 3640},
        "train_with_spk1": {"none": 47000, "F5-TTS-Vietnamese": 3710, "OmniVoice": 3690},
        "dev": {"none": 10490, "F5-TTS-Vietnamese": 960, "OmniVoice": 955},
        "test_indomain": {"none": 13735, "F5-TTS-Vietnamese": 1125, "OmniVoice": 1120},
        "unseen_vieneu": {"VieNeu-TTS": 955},
    }
    for name, exp in expected_gens.items():
        df = manifests[name]
        if name != "unseen_vieneu":
            assert "VieNeu-TTS" not in set(df["tts_generator"].unique()), f"VieNeu-TTS found in {name}"
        actual = df["tts_generator"].value_counts().to_dict()
        assert actual == exp, f"{name} tts_generator counts {actual} != expected {exp}"

    unseen_df = manifests["unseen_vieneu"]
    assert (unseen_df["label"] == "spoof").all()
    assert unseen_df["codec"].value_counts().to_dict() == {c: 191 for c in REQUIRED_CODECS}


def test_codec_balance_and_presence(manifests):
    for name, df in manifests.items():
        codecs = set(df["codec"].unique())
        assert REQUIRED_CODECS.issubset(codecs), f"{name} missing codecs: {REQUIRED_CODECS - codecs}"
        omni = df[df["tts_generator"] == "OmniVoice"]
        if len(omni) > 0:
            per_base = omni.groupby("base_utt")["codec"].nunique()
            assert (per_base == 5).all(), f"{name}: some OmniVoice base_utt do not have all 5 codecs"


@pytest.mark.skipif(
    not (_ROOT / "data/spoof_omnivoice_v8").exists(),
    reason="Local OmniVoice V8 audio assets not present in CI",
)
def test_audio_files_exist_local(manifests):
    omni_root = _ROOT / "data/spoof_omnivoice_v8"
    all_omni_files = [
        p for p in omni_root.rglob("*.wav")
        if not p.name.endswith(".tmp.wav")
    ]
    assert len(all_omni_files) == 6445, f"Expected 6,445 files in data/spoof_omnivoice_v8, found {len(all_omni_files)}"

    vivos_files = [p for p in all_omni_files if p.parent.name.startswith("VIVOS")]
    cv_files = [p for p in all_omni_files if p.parent.name.startswith("CV_")]
    spk_files = [p for p in all_omni_files if p.parent.name.startswith("SPK_")]
    assert len(vivos_files) == 4795, f"Expected 4,795 VIVOS files, got {len(vivos_files)}"
    assert len(cv_files) == 1225, f"Expected 1,225 CommonVoice files, got {len(cv_files)}"
    assert len(spk_files) == 425, f"Expected 425 SPK files, got {len(spk_files)}"

    for name, df in manifests.items():
        omni = df[df["tts_generator"] == "OmniVoice"]
        for rel_p in omni["audio_path"]:
            full_p = _ROOT / rel_p
            assert full_p.exists() and full_p.stat().st_size > 100, f"Missing OmniVoice file in {name}: {full_p}"
        sample_paths = df["audio_path"].sample(n=min(50, len(df)), random_state=42)
        for rel_p in sample_paths:
            full_p = _ROOT / rel_p
            assert full_p.exists() and full_p.stat().st_size > 100, f"Missing sampled file in {name}: {full_p}"
