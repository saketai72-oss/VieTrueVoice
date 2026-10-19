"""Speaker-disjoint dataset splitting script for ViTrueVoice.

Ensures zero speaker overlap between Train (70%), Dev (15%), and Test (15%) manifests.
Complies with STUBBORN_FACTs and biometrics privacy (SPK_XXXX).
"""

import argparse
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import pandas as pd


def split_dataset_by_speaker(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    dev_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataframe into Train, Dev, and Test ensuring strict speaker-disjoint isolation.

    Args:
        df: DataFrame containing at least 'speaker_id' and 'audio_path'.
        train_ratio: Proportion of speakers for Train set (default: 0.70).
        dev_ratio: Proportion of speakers for Dev set (default: 0.15).
        test_ratio: Proportion of speakers for Test set (default: 0.15).
        seed: Random seed for reproducible splitting.

    Returns:
        Tuple of (train_df, dev_df, test_df).
    """
    if "speaker_id" not in df.columns:
        raise ValueError("DataFrame must contain 'speaker_id' column.")

    unique_speakers = np.array(sorted(df["speaker_id"].unique()))
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_speakers)

    num_spk = len(unique_speakers)
    if num_spk < 3:
        raise ValueError(f"Need at least 3 unique speakers to split, found {num_spk}.")

    num_train = int(round(num_spk * train_ratio))
    num_dev = int(round(num_spk * dev_ratio))
    # Ensure at least 1 speaker per set
    num_train = max(1, min(num_train, num_spk - 2))
    num_dev = max(1, min(num_dev, num_spk - num_train - 1))

    train_spks = set(unique_speakers[:num_train])
    dev_spks = set(unique_speakers[num_train : num_train + num_dev])
    test_spks = set(unique_speakers[num_train + num_dev :])

    train_df = df[df["speaker_id"].isin(train_spks)].copy().reset_index(drop=True)
    dev_df = df[df["speaker_id"].isin(dev_spks)].copy().reset_index(drop=True)
    test_df = df[df["speaker_id"].isin(test_spks)].copy().reset_index(drop=True)

    return train_df, dev_df, test_df


def save_manifests(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
    unseen_df: Optional[pd.DataFrame] = None,
    output_dir: str | Path = "data/manifests",
) -> None:
    """Save split DataFrames to standard CSV manifests."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    columns = ["audio_path", "speaker_id", "label", "source_tool"]

    def _format_and_save(df: pd.DataFrame, filename: str) -> None:
        for col in columns:
            if col not in df.columns:
                df[col] = "unknown"
        df[columns].to_csv(out_path / filename, index=False, encoding="utf-8")

    _format_and_save(train_df, "train.csv")
    _format_and_save(dev_df, "dev.csv")
    _format_and_save(test_df, "test_indomain.csv")

    if unseen_df is not None and not unseen_df.empty:
        _format_and_save(unseen_df, "test_unseen.csv")


def scan_audio_directory(data_dir: str | Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Scan data directory and construct in-domain and unseen DataFrames.

    Expected structure:
      data/raw/ -> Bona fide (label: 1, tool: original)
      data/spoof_f5tts/ -> Spoof (label: 0, tool: f5tts)
      data/spoof_vieneu/ -> Spoof (label: 0, tool: vieneu)
      data/spoof_unseen/ -> Unseen Spoof (label: 0, tool: unseen)
    """
    root = Path(data_dir)
    in_domain_records = []
    unseen_records = []

    def _extract_spk(filename: str) -> str:
        # Expected format: SPK_XXXX_... or filename prefix before first underscore
        parts = filename.split("_")
        if len(parts) >= 2 and parts[0] == "SPK":
            return f"SPK_{parts[1]}"
        return parts[0]

    sources = [
        (root / "raw", 1, "original", in_domain_records),
        (root / "bonafide_ref", 1, "ref_original", in_domain_records),
        (root / "spoof_f5tts", 0, "f5tts", in_domain_records),
        (root / "spoof_vieneu", 0, "vieneu", in_domain_records),
        (root / "spoof_unseen", 0, "unseen", unseen_records),
    ]

    audio_exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}

    for dir_path, label, tool, target_list in sources:
        if dir_path.exists():
            for f in dir_path.glob("**/*"):
                if f.suffix.lower() in audio_exts and f.is_file():
                    target_list.append({
                        "audio_path": f.as_posix(),
                        "speaker_id": _extract_spk(f.stem),
                        "label": label,
                        "source_tool": tool,
                    })

    in_domain_df = pd.DataFrame(in_domain_records)
    unseen_df = pd.DataFrame(unseen_records)
    return in_domain_df, unseen_df


def main():
    parser = argparse.ArgumentParser(description="Split ViTrueVoice dataset into speaker-disjoint sets.")
    parser.add_argument("--data_dir", type=str, default="data", help="Root data directory")
    parser.add_argument("--output_dir", type=str, default="data/manifests", help="Output manifests directory")
    parser.add_argument("--train_ratio", type=float, default=0.70)
    parser.add_argument("--dev_ratio", type=float, default=0.15)
    parser.add_argument("--test_ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    in_df, unseen_df = scan_audio_directory(args.data_dir)

    if in_df.empty:
        print(f"⚠️ Không tìm thấy file âm thanh nào trong {args.data_dir}. Vui lòng nạp dữ liệu vào data/raw.")
        return

    train_df, dev_df, test_df = split_dataset_by_speaker(
        in_df,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    save_manifests(train_df, dev_df, test_df, unseen_df=unseen_df, output_dir=args.output_dir)
    print(f"✅ Đã tạo các tệp manifest thành công tại {args.output_dir}:")
    print(f" - Train: {len(train_df)} mẫu ({train_df['speaker_id'].nunique()} người nói)")
    print(f" - Dev: {len(dev_df)} mẫu ({dev_df['speaker_id'].nunique()} người nói)")
    print(f" - Test In-domain: {len(test_df)} mẫu ({test_df['speaker_id'].nunique()} người nói)")
    if not unseen_df.empty:
        print(f" - Test Unseen: {len(unseen_df)} mẫu ({unseen_df['speaker_id'].nunique()} người nói)")


if __name__ == "__main__":
    main()
