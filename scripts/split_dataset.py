"""Speaker-disjoint dataset splitting script for ViTrueVoice.

Ensures zero speaker overlap between Train (70%), Dev (15%), and Test (15%) manifests.
Complies with STUBBORN_FACTs and biometrics privacy (SPK_XXXX).
Supports full 17-column manifest schema per DataColunm_Plan.docx.
"""

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


SPEAKER_SPLIT = {
    "SPK_0001": "train",
    "SPK_0004": "train",
    "SPK_0005": "train",
    "SPK_0006": "dev",
    "SPK_0007": "test",
}

MANIFEST_COLUMNS = [
    "utt_id",
    "audio_path",
    "speaker_id",
    "source",
    "label",
    "role",
    "tts_generator",
    "codec",
    "split",
    "duration_sec",
    "transcript",
    "raw_wer",
    "raw_cer",
    "ecapa_sim",
    "wavlm_sim",
    "derived_tier",
    "seed",
]


def split_dataset_by_speaker(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    dev_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
    speaker_split_map: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split dataframe into Train, Dev, and Test ensuring strict speaker-disjoint isolation.

    Args:
        df: DataFrame containing at least 'speaker_id' and 'audio_path'.
        train_ratio: Proportion of speakers for Train set (default: 0.70).
        dev_ratio: Proportion of speakers for Dev set (default: 0.15).
        test_ratio: Proportion of speakers for Test set (default: 0.15).
        seed: Random seed for reproducible splitting.
        speaker_split_map: Optional dict mapping speaker_id to 'train', 'dev', or 'test'.

    Returns:
        Tuple of (train_df, dev_df, test_df).
    """
    if "speaker_id" not in df.columns:
        raise ValueError("DataFrame must contain 'speaker_id' column.")

    if speaker_split_map is not None:
        train_df = df[df["speaker_id"].map(speaker_split_map) == "train"].copy().reset_index(drop=True)
        dev_df = df[df["speaker_id"].map(speaker_split_map) == "dev"].copy().reset_index(drop=True)
        test_df = df[df["speaker_id"].map(speaker_split_map) == "test"].copy().reset_index(drop=True)
        return train_df, dev_df, test_df

    unique_speakers = np.array(sorted(df["speaker_id"].unique()))
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_speakers)

    num_spk = len(unique_speakers)
    if num_spk < 3:
        raise ValueError(f"Need at least 3 unique speakers to split, found {num_spk}.")

    num_train = int(round(num_spk * train_ratio))
    num_dev = int(round(num_spk * dev_ratio))
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
    columns: Optional[List[str]] = None,
) -> None:
    """Save split DataFrames to standard CSV manifests."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if columns is not None:
        target_cols = columns
    elif "utt_id" in train_df.columns:
        target_cols = MANIFEST_COLUMNS
    else:
        target_cols = ["audio_path", "speaker_id", "label", "source_tool"]

    def _format_and_save(df: pd.DataFrame, filename: str, split_name: str) -> None:
        if df is None or df.empty:
            return
        d = df.copy()
        if "split" in target_cols and ("split" not in d.columns or d["split"].isna().any()):
            d["split"] = split_name
        for col in target_cols:
            if col not in d.columns:
                d[col] = None
        d[target_cols].to_csv(out_path / filename, index=False, encoding="utf-8")

    _format_and_save(train_df, "train.csv", "train")
    _format_and_save(dev_df, "dev.csv", "dev")
    _format_and_save(test_df, "test_indomain.csv", "test")

    if unseen_df is not None and not unseen_df.empty:
        _format_and_save(unseen_df, "test_unseen.csv", "unseen")


def enrich_records(df: pd.DataFrame, manifests_dir: str | Path = "data/manifests") -> pd.DataFrame:
    """Enrich audio DataFrame with columns from bonafide and spoof manifests if available."""
    m_path = Path(manifests_dir)
    bonafide_csv = m_path / "bonafide_manifest.csv"
    spoof_csv = m_path / "spoof_manifest.csv"

    aux_dfs = []
    if bonafide_csv.exists():
        b_df = pd.read_csv(bonafide_csv)
        if "utt_id" not in b_df.columns:
            b_df["utt_id"] = b_df["audio_path"].apply(lambda p: Path(str(p)).stem)
        aux_dfs.append(b_df)
    if spoof_csv.exists():
        s_df = pd.read_csv(spoof_csv)
        if "utt_id" not in s_df.columns:
            s_df["utt_id"] = s_df["audio_path"].apply(lambda p: Path(str(p)).stem)
        if "is_bonafide" in s_df.columns and "label" not in s_df.columns:
            s_df["label"] = s_df["is_bonafide"].apply(lambda x: "bonafide" if x else "spoof")
        if "engine_name" in s_df.columns and "tts_generator" not in s_df.columns:
            s_df["tts_generator"] = s_df["engine_name"]
        if "raw_wer" in s_df.columns and "wer" not in s_df.columns:
            s_df["wer"] = s_df["raw_wer"]
        if "raw_cer" in s_df.columns and "cer" not in s_df.columns:
            s_df["cer"] = s_df["raw_cer"]
        aux_dfs.append(s_df)

    res = df.copy()
    if "utt_id" not in res.columns:
        res["utt_id"] = res["audio_path"].apply(lambda p: Path(str(p)).stem)

    if aux_dfs:
        merged_aux = pd.concat(aux_dfs, ignore_index=True)
        merged_aux["audio_path"] = merged_aux["audio_path"].apply(lambda p: Path(str(p)).as_posix() if pd.notna(p) else "")
        res["audio_path"] = res["audio_path"].apply(lambda p: Path(str(p)).as_posix())

        aux_by_path = merged_aux.set_index("audio_path").to_dict("index")
        aux_by_utt = merged_aux.set_index("utt_id").to_dict("index")

        for col in MANIFEST_COLUMNS:
            if col in ["utt_id", "audio_path"]:
                continue
            res[col] = res.apply(
                lambda r: (aux_by_path.get(r["audio_path"], {}).get(col)
                           if pd.notna(aux_by_path.get(r["audio_path"], {}).get(col))
                           else aux_by_utt.get(r["utt_id"], {}).get(col)
                           if pd.notna(aux_by_utt.get(r["utt_id"], {}).get(col))
                           else r.get(col)),
                axis=1
            )

    if "label" in res.columns:
        res["label"] = res["label"].apply(lambda x: "bonafide" if str(x) in ["1", "bonafide", "True"] else "spoof")
    if "split" not in res.columns or res["split"].isna().any():
        res["split"] = res["split"].fillna(res["speaker_id"].map(SPEAKER_SPLIT)).fillna("train")
    if "codec" not in res.columns or res["codec"].isna().any():
        res["codec"] = res["codec"].fillna("clean_16khz")
    if "tts_generator" not in res.columns or res["tts_generator"].isna().any():
        res["tts_generator"] = res.apply(
            lambda r: "none" if r.get("label") == "bonafide" else r.get("source_tool", "unknown"), axis=1
        )
    if "vocoder" not in res.columns or res["vocoder"].isna().any():
        res["vocoder"] = res.apply(
            lambda r: "bonafide" if r.get("label") == "bonafide" else ("Vocos" if "f5" in str(r.get("tts_generator", "")).lower() else "MOSS_48kHz"),
            axis=1
        )
    if "derived_tier" not in res.columns or res["derived_tier"].isna().any():
        res["derived_tier"] = res.apply(
            lambda r: "BonaFide" if r.get("label") == "bonafide" else "Tier 1 (Strong)", axis=1
        )

    for col in MANIFEST_COLUMNS:
        if col not in res.columns:
            res[col] = None

    return res


def scan_audio_directory(data_dir: str | Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Scan data directory and construct in-domain and unseen DataFrames."""
    root = Path(data_dir)
    in_domain_records = []
    unseen_records = []

    def _extract_spk(filename: str) -> str:
        parts = filename.split("_")
        if len(parts) >= 2 and parts[0] == "SPK":
            return f"SPK_{parts[1]}"
        return parts[0]

    sources = [
        (root / "raw", "bonafide", "original", in_domain_records),
        (root / "bonafide_ref", "bonafide", "ref_original", in_domain_records),
        (root / "spoof_f5tts", "spoof", "F5-TTS", in_domain_records),
        (root / "spoof_vieneu", "spoof", "VieNeu-TTS", in_domain_records),
        (root / "spoof_unseen", "spoof", "unseen", unseen_records),
    ]

    audio_exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}

    for dir_path, label, tool, target_list in sources:
        if dir_path.exists():
            for f in dir_path.glob("**/*"):
                if f.suffix.lower() in audio_exts and f.is_file():
                    target_list.append({
                        "utt_id": f.stem,
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
    parser.add_argument("--use_fixed_split", action="store_true", default=True, help="Use fixed speaker split for ViTrueVoice")

    args = parser.parse_args()
    in_df, unseen_df = scan_audio_directory(args.data_dir)

    if in_df.empty:
        print(f"⚠️ Không tìm thấy file âm thanh nào trong {args.data_dir}. Vui lòng nạp dữ liệu vào data/raw.")
        return

    in_df = enrich_records(in_df, manifests_dir=args.output_dir)

    spk_map = SPEAKER_SPLIT if (args.use_fixed_split and set(in_df["speaker_id"]).issubset(set(SPEAKER_SPLIT.keys()))) else None

    train_df, dev_df, test_df = split_dataset_by_speaker(
        in_df,
        train_ratio=args.train_ratio,
        dev_ratio=args.dev_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        speaker_split_map=spk_map,
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
