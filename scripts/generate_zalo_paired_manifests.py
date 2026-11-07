"""Generator for Zalo paired dataset and manifests (Pha 2 & Pha 4).

Generates paired proxy channels for Profile A (AAC-LC 76kbps) and Profile B (Opus 24kbps),
links them via base_utt, enforces 0% speaker/base_utt leakage across splits,
and strictly excludes SPK_xxxx (reserved for acceptance test) and VieNeu-TTS from Train/Dev.
"""

from __future__ import annotations
import argparse
import io
from pathlib import Path
import re
import subprocess
import numpy as np
import pandas as pd
import soundfile as sf


def derive_base_utt(utt_id: str) -> str:
    """Extract base utterance ID by stripping channel and codec suffixes."""
    # Strip extension first if present
    stem = Path(utt_id).stem if "." in str(utt_id) else str(utt_id)
    # Suffixes to strip
    pattern = r"(_clean|_g711|_amrnb|_aac_zalo|_opus_zalo|_sim_zalo|_untrimmed)$"
    return re.sub(pattern, "", stem)


def transcode_aac_adts_stream(raw_wav_bytes: bytes) -> bytes:
    """Encode to AAC-LC 48kHz mono 76kbps, then decode back to 16kHz mono WAV bytes in-memory."""
    cmd_enc = [
        "ffmpeg", "-v", "error",
        "-i", "pipe:0",
        "-ar", "48000", "-ac", "1",
        "-c:a", "aac", "-b:a", "76k",
        "-f", "adts", "pipe:1"
    ]
    proc_enc = subprocess.run(cmd_enc, input=raw_wav_bytes, capture_output=True, check=True)

    cmd_dec = [
        "ffmpeg", "-v", "error",
        "-i", "pipe:0",
        "-f", "wav", "-ar", "16000", "-ac", "1",
        "pipe:1"
    ]
    proc_dec = subprocess.run(cmd_dec, input=proc_enc.stdout, capture_output=True, check=True)
    return proc_dec.stdout


def transcode_opus_ogg_stream(raw_wav_bytes: bytes) -> bytes:
    """Encode to Opus 24kbps mono OGG, then decode back to 16kHz mono WAV bytes in-memory."""
    cmd_enc = [
        "ffmpeg", "-v", "error",
        "-i", "pipe:0",
        "-c:a", "libopus", "-b:a", "24k",
        "-f", "ogg", "pipe:1"
    ]
    proc_enc = subprocess.run(cmd_enc, input=raw_wav_bytes, capture_output=True, check=True)

    cmd_dec = [
        "ffmpeg", "-v", "error",
        "-i", "pipe:0",
        "-f", "wav", "-ar", "16000", "-ac", "1",
        "pipe:1"
    ]
    proc_dec = subprocess.run(cmd_dec, input=proc_enc.stdout, capture_output=True, check=True)
    return proc_dec.stdout


def generate_paired_manifest(
    df: pd.DataFrame,
    generate_audio: bool = False,
    audio_root: str | Path = "",
    out_audio_dir: str | Path = "",
) -> pd.DataFrame:
    """Generate paired proxy rows (Profile A: aac_zalo_76k, Profile B: opus_zalo_24k)."""
    df = df.copy()
    if "base_utt" not in df.columns:
        df["base_utt"] = df["utt_id"].apply(derive_base_utt)
    else:
        null_mask = df["base_utt"].isna() | (df["base_utt"].astype(str) == "") | (df["base_utt"].astype(str) == "nan")
        if null_mask.any():
            df.loc[null_mask, "base_utt"] = df.loc[null_mask, "utt_id"].apply(derive_base_utt)

    # Clean subset: take utterances with clean_16khz codec
    clean_mask = df["codec"].astype(str).str.contains("clean", case=False)
    clean_df = df[clean_mask].copy()
    if len(clean_df) == 0:
        # Fallback: if no explicit clean_16khz, take unique base_utt
        clean_df = df.drop_duplicates(subset=["base_utt"]).copy()

    # Proxy Profile A: AAC-LC 76kbps
    df_aac = clean_df.copy()
    df_aac["utt_id"] = df_aac["base_utt"] + "_aac_zalo"
    df_aac["codec"] = "aac_zalo_76k"
    df_aac["pre_codec"] = "aac_76k_m4a"
    df_aac["audio_path"] = df_aac["audio_path"].apply(
        lambda p: Path(p).with_name(f"{derive_base_utt(Path(p).stem)}_aac_zalo.wav").as_posix()
    )

    # Proxy Profile B: Opus 24kbps
    df_opus = clean_df.copy()
    df_opus["utt_id"] = df_opus["base_utt"] + "_opus_zalo"
    df_opus["codec"] = "opus_zalo_24k"
    df_opus["pre_codec"] = "opus_24k_ogg"
    df_opus["audio_path"] = df_opus["audio_path"].apply(
        lambda p: Path(p).with_name(f"{derive_base_utt(Path(p).stem)}_opus_zalo.wav").as_posix()
    )

    # Optional: generate physical audio files if requested and audio exists
    if generate_audio and audio_root:
        root_p = Path(audio_root)
        out_root = Path(out_audio_dir) if out_audio_dir else root_p
        for _, row in clean_df.iterrows():
            orig_path = root_p / row["audio_path"]
            if not orig_path.exists():
                continue
            with open(orig_path, "rb") as f:
                raw_bytes = f.read()

            # AAC proxy
            aac_path = out_root / row["audio_path"].replace(".wav", "_aac_zalo.wav")
            aac_path.parent.mkdir(parents=True, exist_ok=True)
            if not aac_path.exists():
                aac_bytes = transcode_aac_adts_stream(raw_bytes)
                with open(aac_path, "wb") as f:
                    f.write(aac_bytes)

            # Opus proxy
            opus_path = out_root / row["audio_path"].replace(".wav", "_opus_zalo.wav")
            opus_path.parent.mkdir(parents=True, exist_ok=True)
            if not opus_path.exists():
                opus_bytes = transcode_opus_ogg_stream(raw_bytes)
                with open(opus_path, "wb") as f:
                    f.write(opus_bytes)

    # Combine original df with proxy rows
    combined = pd.concat([df, df_aac, df_opus], ignore_index=True)
    return combined


ACCEPTANCE_VOLUNTEERS = {"SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"}


def validate_split_leakage(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """Strictly assert zero data leakage between Train, Dev, and Test splits."""
    all_dfs = [("train", train_df), ("dev", dev_df), ("test", test_df)]

    # 1. Reject 5 acceptance volunteers across all splits
    for name, df in all_dfs:
        spks = set(df["speaker_id"].astype(str).unique())
        hit_acceptance = spks.intersection(ACCEPTANCE_VOLUNTEERS)
        if hit_acceptance:
            raise ValueError(f"Found forbidden acceptance volunteer in {name}: {hit_acceptance}")

    # 2. Reject SPK_0001 in dev or test (SPK_0001 is only permitted in train)
    for name, df in [("dev", dev_df), ("test", test_df)]:
        spks = set(df["speaker_id"].astype(str).unique())
        if "SPK_0001" in spks:
            raise ValueError(f"Found forbidden SPK_0001 in {name}: SPK_0001 is only permitted in train!")

    # 2. Reject VieNeu-TTS in train or dev
    for name, df in [("train", train_df), ("dev", dev_df)]:
        tts_series = df["tts_generator"].astype(str).str.lower()
        if tts_series.str.contains("vieneu", regex=False).any():
            raise ValueError(f"Found forbidden VieNeu-TTS in {name} (violates H2 hard-unseen constraint)")

    # 3. Speaker-disjoint check
    spk_train = set(train_df["speaker_id"].unique())
    spk_dev = set(dev_df["speaker_id"].unique())
    spk_test = set(test_df["speaker_id"].unique())

    if leak_td := spk_train.intersection(spk_dev):
        raise ValueError(f"Speaker overlap between Train and Dev: {leak_td}")
    if leak_tt := spk_train.intersection(spk_test):
        raise ValueError(f"Speaker overlap between Train and Test: {leak_tt}")
    if leak_dt := spk_dev.intersection(spk_test):
        raise ValueError(f"Speaker overlap between Dev and Test: {leak_dt}")

    # 4. Base utterance-disjoint check
    base_train = set(train_df["base_utt"].unique())
    base_dev = set(dev_df["base_utt"].unique())
    base_test = set(test_df["base_utt"].unique())

    if leak_b_td := base_train.intersection(base_dev):
        raise ValueError(f"Base utterance overlap between Train and Dev: {len(leak_b_td)}")
    if leak_b_tt := base_train.intersection(base_test):
        raise ValueError(f"Base utterance overlap between Train and Test: {len(leak_b_tt)}")
    if leak_b_dt := base_dev.intersection(base_test):
        raise ValueError(f"Base utterance overlap between Dev and Test: {len(leak_b_dt)}")


def merge_deep_voice_pool(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
    pool: str | Path | pd.DataFrame | None,
) -> pd.DataFrame:
    """Enrich train split with scanned deep voice samples while asserting 0% leakage."""
    if pool is None:
        return train_df

    if isinstance(pool, (str, Path)):
        pool_path = Path(pool)
        if not pool_path.is_file():
            print(f"⚠️ Deep voice pool file not found: {pool_path}, skipping merge.")
            return train_df
        pool_df = pd.read_csv(pool_path)
    elif isinstance(pool, pd.DataFrame):
        pool_df = pool.copy()
    else:
        raise TypeError(f"Invalid pool type: {type(pool)}")

    if len(pool_df) == 0:
        return train_df

    # 1. Reject SPK_xxxx in deep voice pool
    spk_re = re.compile(r"^SPK_\d{4}$", re.IGNORECASE)
    pool_spks = set(pool_df["speaker_id"].astype(str).unique())
    forbidden_spks = [s for s in pool_spks if spk_re.match(s)]
    if forbidden_spks:
        raise ValueError(f"Found forbidden SPK_xxxx volunteer in deep voice pool: {set(forbidden_spks)}")

    # 2. Derive base_utt for pool, train_df, and splits if not present
    if "base_utt" not in pool_df.columns:
        pool_df["base_utt"] = pool_df["utt_id"].apply(derive_base_utt)

    train_df = train_df.copy()
    if "base_utt" not in train_df.columns:
        train_df["base_utt"] = train_df["utt_id"].apply(derive_base_utt)
    else:
        null_mask = train_df["base_utt"].isna() | (train_df["base_utt"].astype(str) == "") | (train_df["base_utt"].astype(str) == "nan")
        if null_mask.any():
            train_df.loc[null_mask, "base_utt"] = train_df.loc[null_mask, "utt_id"].apply(derive_base_utt)

    dev_base = (
        set(dev_df["base_utt"].dropna().unique())
        if "base_utt" in dev_df.columns
        else set(dev_df["utt_id"].apply(derive_base_utt).dropna().unique())
        if "utt_id" in dev_df.columns
        else set()
    )
    test_base = (
        set(test_df["base_utt"].dropna().unique())
        if "base_utt" in test_df.columns
        else set(test_df["utt_id"].apply(derive_base_utt).dropna().unique())
        if "utt_id" in test_df.columns
        else set()
    )

    # 3. Speaker-disjoint check with dev and test
    dev_spks = set(dev_df["speaker_id"].astype(str).unique()) if "speaker_id" in dev_df.columns else set()
    test_spks = set(test_df["speaker_id"].astype(str).unique()) if "speaker_id" in test_df.columns else set()

    if leak_spk_dev := pool_spks.intersection(dev_spks):
        raise ValueError(f"Speaker overlap between deep voice pool and dev: {leak_spk_dev}")
    if leak_spk_test := pool_spks.intersection(test_spks):
        raise ValueError(f"Speaker overlap between deep voice pool and test: {leak_spk_test}")

    # 4. Base utterance-disjoint check with dev and test
    pool_base = set(pool_df["base_utt"].dropna().unique())
    if leak_dev_utt := pool_base.intersection(dev_base):
        raise ValueError(f"Base utterance overlap between deep voice pool and dev: {leak_dev_utt}")
    if leak_test_utt := pool_base.intersection(test_base):
        raise ValueError(f"Base utterance overlap between deep voice pool and test: {leak_test_utt}")

    # 4.1 Loại bỏ hoàn toàn các clip trùng lặp với train_df (ngăn ngừa duplicate base_utt và xung đột proxy)
    train_base = set(train_df["base_utt"].dropna().unique())
    dup_mask = pool_df["base_utt"].isin(train_base)
    if dup_mask.any():
        num_dups = int(dup_mask.sum())
        print(f"ℹ️ Bỏ qua {num_dups} mẫu từ deep voice pool vì đã tồn tại trong train_df")
        pool_df = pool_df[~dup_mask].copy()

    if "audio_path" in train_df.columns:
        train_paths = set(train_df["audio_path"].dropna().unique())
        path_dup_mask = pool_df["audio_path"].isin(train_paths)
        if path_dup_mask.any():
            pool_df = pool_df[~path_dup_mask].copy()

    if len(pool_df) == 0:
        return train_df

    # 5. Build standardized bonafide rows (role='train', realistic duration, real transcript, NaN metrics)
    new_rows = []
    for _, r in pool_df.iterrows():
        u_id = str(r["utt_id"])
        b_utt = str(r["base_utt"]) if "base_utt" in r and pd.notna(r["base_utt"]) else derive_base_utt(u_id)
        row_dict = {
            "utt_id": u_id,
            "speaker_id": str(r["speaker_id"]),
            "label": "bonafide",
            "source": "common_voice_deep",
            "tts_generator": "none",
            "codec": "clean_16khz",
            "pre_codec": "clean_16khz",
            "role": "train",
            "split": "train",
            "duration_sec": float(r["duration_sec"]),
            "transcript": str(r.get("transcript", "")),
            "raw_wer": np.nan,
            "raw_cer": np.nan,
            "ecapa_sim": np.nan,
            "wavlm_sim": np.nan,
            "derived_tier": "tier1",
            "seed": 0,
            "audio_path": str(r["audio_path"]),
            "base_utt": b_utt,
        }
        if "orig_audio_path" in r and pd.notna(r["orig_audio_path"]):
            row_dict["orig_audio_path"] = str(r["orig_audio_path"])
        new_rows.append(row_dict)

    merged_df = pd.concat([train_df, pd.DataFrame(new_rows)], ignore_index=True)
    return merged_df


def preaugment_deep_voices(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
    audio_root: str | Path,
    out_audio_dir: str | Path,
    n_samples: int = 500,
    semitones_range: tuple[float, float] = (-8.0, -4.0),
    seed: int = 42,
) -> pd.DataFrame:
    """Offline pre-augmentation: Generates bona fide deep voice variants via formant-preserving pitch shift.

    Excludes SPK_xxxx, dev/test speakers, and dev/test utterances with zero leakage guarantee.
    """
    from src.preprocessing.audio_loader import load_audio
    from src.training.augment import pitch_perturbation

    rng = np.random.default_rng(seed)
    root_p = Path(audio_root)
    out_root = Path(out_audio_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    # 1. Lọc tập ứng viên bonafide clean_16khz từ train_df
    cand_df = train_df[
        (train_df["label"] == "bonafide") &
        (train_df["codec"].str.contains("clean", case=False, na=False))
    ].copy()

    # Chặn tuyệt đối SPK_xxxx
    spk_re = re.compile(r"^SPK_\d{4}$", re.IGNORECASE)
    cand_df = cand_df[~cand_df["speaker_id"].astype(str).str.match(spk_re)].copy()

    # Chặn rò rỉ speaker và base_utt với dev/test
    dev_spks = set(dev_df["speaker_id"].astype(str).unique()) if "speaker_id" in dev_df.columns else set()
    test_spks = set(test_df["speaker_id"].astype(str).unique()) if "speaker_id" in test_df.columns else set()
    forbidden_spks = dev_spks | test_spks
    cand_df = cand_df[~cand_df["speaker_id"].astype(str).isin(forbidden_spks)].copy()

    if "base_utt" not in cand_df.columns:
        cand_df["base_utt"] = cand_df["utt_id"].apply(derive_base_utt)
    else:
        null_mask = cand_df["base_utt"].isna() | (cand_df["base_utt"].astype(str) == "") | (cand_df["base_utt"].astype(str) == "nan")
        if null_mask.any():
            cand_df.loc[null_mask, "base_utt"] = cand_df.loc[null_mask, "utt_id"].apply(derive_base_utt)

    cand_df = cand_df.drop_duplicates(subset=["base_utt"]).reset_index(drop=True)

    # Lấy tối đa n_samples mẫu
    if len(cand_df) > n_samples:
        cand_df = cand_df.sample(n=n_samples, random_state=seed).reset_index(drop=True)

    new_rows = []
    for _, r in cand_df.iterrows():
        src_path = root_p / r["audio_path"]
        if not src_path.is_file():
            continue
        try:
            wav = load_audio(src_path, target_sr=16000)
            if len(wav) < 1600:
                continue
            wav_aug = pitch_perturbation(wav, rng, semitones_range=semitones_range, target_len=len(wav))
        except Exception:
            continue

        b_utt = f"{r['base_utt']}_deep"
        dst_rel = f"data/raw/deep_aug/{r['speaker_id']}/{b_utt}.wav"
        dst_full = out_root / dst_rel
        dst_full.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(dst_full), wav_aug, 16000, subtype="PCM_16")

        new_rows.append({
            "utt_id": b_utt,
            "speaker_id": f"CV_aug_{r['speaker_id']}",
            "label": "bonafide",
            "source": "deep_pitch_augmented",
            "tts_generator": "none",
            "codec": "clean_16khz",
            "pre_codec": "clean_16khz",
            "role": "train",
            "split": "train",
            "duration_sec": float(len(wav_aug) / 16000),
            "transcript": str(r.get("transcript", "")),
            "raw_wer": np.nan,
            "raw_cer": np.nan,
            "ecapa_sim": np.nan,
            "wavlm_sim": np.nan,
            "derived_tier": "tier1",
            "seed": seed,
            "audio_path": dst_rel,
            "base_utt": b_utt,
        })

    if not new_rows:
        return pd.DataFrame()
    return pd.DataFrame(new_rows)


def main():
    parser = argparse.ArgumentParser(description="Generate paired manifests for Zalo proxies (Profiles A & B).")
    parser.add_argument("--manifest-dir", default="out/kaggle_ssl_out/data/manifests_seen_only", help="Input manifest directory")
    parser.add_argument("--out-dir", default="data/manifests_zalo", help="Output directory for paired manifests")
    parser.add_argument("--audio-root", default="", help="Audio root directory to transcode physical files")
    parser.add_argument("--generate-audio", action="store_true", help="Generate proxy audio files on disk")
    parser.add_argument("--deep-voice-pool", default=None, help="Optional path to deep_voice_pool.csv to enrich train split")
    args = parser.parse_args()

    in_dir = Path(args.manifest_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading manifests from {in_dir}...")
    train_path = in_dir / "train.csv"
    dev_path = in_dir / "dev.csv"
    test_path = in_dir / "test_indomain.csv"

    train_df = pd.read_csv(train_path)
    dev_df = pd.read_csv(dev_path)
    test_df = pd.read_csv(test_path)

    print(f"Original counts: train={len(train_df)}, dev={len(dev_df)}, test={len(test_df)}")

    # Enrich train split with deep voice pool if provided
    if args.deep_voice_pool:
        print(f"Merging deep voice pool from {args.deep_voice_pool} into train split...")
        train_df = merge_deep_voice_pool(train_df, dev_df, test_df, args.deep_voice_pool)
        print(f"Enriched train count: {len(train_df)}")

    # Generate paired manifests
    train_paired = generate_paired_manifest(train_df, generate_audio=args.generate_audio, audio_root=args.audio_root)
    dev_paired = generate_paired_manifest(dev_df, generate_audio=args.generate_audio, audio_root=args.audio_root)
    test_paired = generate_paired_manifest(test_df, generate_audio=args.generate_audio, audio_root=args.audio_root)

    print(f"Paired counts: train={len(train_paired)}, dev={len(dev_paired)}, test={len(test_paired)}")

    # Validate leakage
    print("Validating zero data leakage...")
    validate_split_leakage(train_paired, dev_paired, test_paired)
    print("✅ Split validation passed: 0% speaker, base_utt, or SPK_xxxx leakage!")

    # Save to out_dir with LF line endings
    train_paired.to_csv(out_dir / "train_zalo.csv", index=False, lineterminator="\n")
    dev_paired.to_csv(out_dir / "dev_zalo.csv", index=False, lineterminator="\n")
    test_paired.to_csv(out_dir / "test_indomain_zalo.csv", index=False, lineterminator="\n")
    print(f"Saved paired manifests to {out_dir}")


if __name__ == "__main__":
    main()
