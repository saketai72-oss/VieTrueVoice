import pandas as pd
import pytest
from scripts.split_dataset import split_dataset_by_speaker, save_manifests


@pytest.fixture
def sample_dataset_df():
    """Create a dummy dataset with 20 speakers, 5 utterances each (100 total rows)."""
    rows = []
    # 10 bona fide speakers, 10 spoofed speakers
    for spk_idx in range(1, 21):
        spk_id = f"SPK_{spk_idx:04d}"
        label = 1 if spk_idx <= 10 else 0
        tool = "original" if label == 1 else ("f5tts" if spk_idx <= 15 else "vieneu")
        for utt_idx in range(1, 6):
            rows.append({
                "audio_path": f"data/audio/{spk_id}_sample{utt_idx:02d}.wav",
                "speaker_id": spk_id,
                "label": label,
                "source_tool": tool,
            })
    return pd.DataFrame(rows)


def test_speaker_disjoint_constraint(sample_dataset_df):
    """Verify strictly 0% speaker overlap between Train, Dev, and Test sets."""
    train_df, dev_df, test_df = split_dataset_by_speaker(
        sample_dataset_df, train_ratio=0.7, dev_ratio=0.15, test_ratio=0.15, seed=42
    )

    train_spks = set(train_df["speaker_id"])
    dev_spks = set(dev_df["speaker_id"])
    test_spks = set(test_df["speaker_id"])

    assert len(train_spks & dev_spks) == 0, "Train and Dev share speakers!"
    assert len(train_spks & test_spks) == 0, "Train and Test share speakers!"
    assert len(dev_spks & test_spks) == 0, "Dev and Test share speakers!"


def test_split_proportions_and_data_preservation(sample_dataset_df):
    """Verify sample count is preserved and proportions are approximately 70/15/15."""
    train_df, dev_df, test_df = split_dataset_by_speaker(
        sample_dataset_df, train_ratio=0.7, dev_ratio=0.15, test_ratio=0.15, seed=42
    )

    total_samples = len(sample_dataset_df)
    assert len(train_df) + len(dev_df) + len(test_df) == total_samples

    # Check speaker count proportions (14 train, 3 dev, 3 test for 20 speakers)
    assert len(set(train_df["speaker_id"])) == 14
    assert len(set(dev_df["speaker_id"])) == 3
    assert len(set(test_df["speaker_id"])) == 3


def test_save_manifests(tmp_path, sample_dataset_df):
    """Verify manifests are exported to CSV with correct headers and non-empty content."""
    train_df, dev_df, test_df = split_dataset_by_speaker(sample_dataset_df, seed=42)
    unseen_df = pd.DataFrame([{
        "audio_path": "data/spoof_unseen/unseen01.wav",
        "speaker_id": "SPK_9999",
        "label": 0,
        "source_tool": "rvc",
    }])

    save_manifests(
        train_df, dev_df, test_df, unseen_df=unseen_df, output_dir=tmp_path
    )

    train_csv = tmp_path / "train.csv"
    dev_csv = tmp_path / "dev.csv"
    test_csv = tmp_path / "test_indomain.csv"
    unseen_csv = tmp_path / "test_unseen.csv"

    assert train_csv.exists()
    assert dev_csv.exists()
    assert test_csv.exists()
    assert unseen_csv.exists()

    loaded_train = pd.read_csv(train_csv)
    assert list(loaded_train.columns) == ["audio_path", "speaker_id", "label", "source_tool"]
    assert len(loaded_train) == len(train_df)


def test_fixed_speaker_split():
    """Verify fixed speaker split assigns SPK_0001,4,5 to train, 6 to dev, 7 to test."""
    from scripts.split_dataset import split_dataset_by_speaker, SPEAKER_SPLIT
    df = pd.DataFrame([
        {"speaker_id": "SPK_0001", "audio_path": "a1.wav"},
        {"speaker_id": "SPK_0004", "audio_path": "a4.wav"},
        {"speaker_id": "SPK_0005", "audio_path": "a5.wav"},
        {"speaker_id": "SPK_0006", "audio_path": "a6.wav"},
        {"speaker_id": "SPK_0007", "audio_path": "a7.wav"},
    ])
    train_df, dev_df, test_df = split_dataset_by_speaker(df, speaker_split_map=SPEAKER_SPLIT)
    assert set(train_df["speaker_id"]) == {"SPK_0001", "SPK_0004", "SPK_0005"}
    assert set(dev_df["speaker_id"]) == {"SPK_0006"}
    assert set(test_df["speaker_id"]) == {"SPK_0007"}


def test_save_manifests_17_columns(tmp_path):
    """Verify manifests with 17 columns are preserved correctly upon save."""
    from scripts.split_dataset import save_manifests, MANIFEST_COLUMNS
    assert len(MANIFEST_COLUMNS) == 17
    df = pd.DataFrame([{col: f"val_{col}" for col in MANIFEST_COLUMNS}])
    df["speaker_id"] = "SPK_0001"
    save_manifests(df, df, df, output_dir=tmp_path)
    loaded = pd.read_csv(tmp_path / "train.csv")
    assert list(loaded.columns) == MANIFEST_COLUMNS


def test_dataset_partitioner_disjoint():
    """Verify DatasetPartitioner strictly maintains disjoint sets (Ref, Enroll, Test) with zero leakage."""
    from vitruevoice.batch_processor import DatasetPartitioner

    files = [f"speaker_sample_{i:02d}.wav" for i in range(15)]
    ref_pool, enroll_pool, test_pool = DatasetPartitioner.partition_speaker_files(
        files, n_ref_cands=3, n_enroll=4
    )

    set_ref = set(ref_pool)
    set_enr = set(enroll_pool)
    set_tst = set(test_pool)

    # 1. Tuyệt đối không giao nhau
    assert len(set_ref & set_enr) == 0, "Ref và Enroll bị rò rỉ dữ liệu!"
    assert len(set_ref & set_tst) == 0, "Ref và Test bị rò rỉ dữ liệu!"
    assert len(set_enr & set_tst) == 0, "Enroll và Test bị rò rỉ dữ liệu!"

    # 2. Bảo toàn số lượng mẫu
    assert len(ref_pool) + len(enroll_pool) + len(test_pool) == len(files)
    assert len(ref_pool) == 3
    assert len(enroll_pool) == 4
    assert len(test_pool) == 8



