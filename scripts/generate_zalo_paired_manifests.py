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


def validate_split_leakage(
    train_df: pd.DataFrame,
    dev_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """Strictly assert zero data leakage between Train, Dev, and Test splits."""
    all_dfs = [("train", train_df), ("dev", dev_df), ("test", test_df)]

    # 1. Reject SPK_xxxx in train or dev
    for name, df in all_dfs:
        spks = df["speaker_id"].astype(str).tolist()
        hit_spk = [s for s in spks if re.match(r"^SPK_\d{4}$", s, re.IGNORECASE)]
        if hit_spk:
            raise ValueError(f"Found forbidden SPK_xxxx volunteer in {name}: {set(hit_spk)}")

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


def main():
    parser = argparse.ArgumentParser(description="Generate paired manifests for Zalo proxies (Profiles A & B).")
    parser.add_argument("--manifest-dir", default="out/kaggle_ssl_out/data/manifests_seen_only", help="Input manifest directory")
    parser.add_argument("--out-dir", default="data/manifests_zalo", help="Output directory for paired manifests")
    parser.add_argument("--audio-root", default="", help="Audio root directory to transcode physical files")
    parser.add_argument("--generate-audio", action="store_true", help="Generate proxy audio files on disk")
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
