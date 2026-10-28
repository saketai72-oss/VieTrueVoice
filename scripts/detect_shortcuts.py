#!/usr/bin/env python3
"""Shallow shortcut detector based on spectral features (energy > 7kHz and silence ratio).

Checks if a simple classifier can distinguish bonafide vs spoof based purely on
surface shortcuts (MP3 cutoff, silence characteristics) under speaker-disjoint splits.
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


def extract_spectral_shortcuts(audio_path: str, target_sr: int = 16000) -> tuple[float, float]:
    """Extract (high_freq_ratio, silence_ratio) from audio file."""
    try:
        y, sr = sf.read(audio_path)
    except Exception:
        return 0.0, 0.0

    if y.ndim > 1:
        y = np.mean(y, axis=1)

    if len(y) == 0:
        return 0.0, 0.0

    # 1. High frequency energy ratio (> 7 kHz)
    # Using rfft on the signal
    fft_vals = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), d=1.0 / sr)

    total_energy = np.sum(fft_vals ** 2) + 1e-12
    high_freq_mask = freqs >= 7000.0
    high_freq_energy = np.sum(fft_vals[high_freq_mask] ** 2)
    high_freq_ratio = float(high_freq_energy / total_energy)

    # 2. Silence duration ratio (frames with amplitude < 20 dB below peak)
    frame_len = int(0.025 * sr)  # 25 ms
    hop_len = int(0.010 * sr)    # 10 ms
    if len(y) < frame_len:
        silence_ratio = 0.0
    else:
        num_frames = 1 + (len(y) - frame_len) // hop_len
        # Vectorized frame energy
        shape = (num_frames, frame_len)
        strides = (y.strides[0] * hop_len, y.strides[0])
        frames = np.lib.stride_tricks.as_strided(y, shape=shape, strides=strides)
        rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
        peak_rms = np.max(rms)
        silence_thresh = max(1e-4, peak_rms * 0.05)  # ~-26 dB relative to peak
        silence_frames = np.sum(rms < silence_thresh)
        silence_ratio = float(silence_frames / num_frames)

    return high_freq_ratio, silence_ratio


def bootstrap_auc_ci(y_true: np.ndarray, y_score: np.ndarray, n_bootstraps: int = 1000, alpha: float = 0.05) -> tuple[float, float, float]:
    """Calculate ROC AUC with non-parametric bootstrap confidence interval."""
    if len(np.unique(y_true)) < 2:
        return 0.5, 0.5, 0.5

    base_auc = float(roc_auc_score(y_true, y_score))
    rng = np.random.default_rng(42)
    boot_aucs = []

    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = rng.integers(0, n, size=n)
        b_true = y_true[idx]
        b_score = y_score[idx]
        if len(np.unique(b_true)) < 2:
            continue
        boot_aucs.append(roc_auc_score(b_true, b_score))

    if not boot_aucs:
        return base_auc, base_auc, base_auc

    low = float(np.percentile(boot_aucs, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_aucs, 100.0 * (1.0 - alpha / 2.0)))
    return base_auc, low, high


def main():
    parser = argparse.ArgumentParser(description="VieTrueVoice Spectral Shortcut Detector")
    parser.add_argument("--manifest-dir", default="out", help="Directory containing train.csv and test manifests")
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    train_path = manifest_dir / "train.csv"
    if not train_path.exists():
        print(f"File not found: {train_path}")
        return

    train_df = pd.read_csv(train_path)

    print("=" * 70)
    print("🔍 BỘ DÒ SHORTCUT QUANG PHỔ (SPECTRAL SHORTCUT DETECTOR)")
    print("   Đặc trưng: Tỷ lệ năng lượng > 7kHz + Tỷ lệ thời lượng khoảng lặng")
    print("   Phân chia: Speaker-Disjoint")
    print("=" * 70)

    # Feature extraction for train
    print(f"Đang trích xuất đặc trưng cho tập Train ({len(train_df)} mẫu)...")
    train_feats = [extract_spectral_shortcuts(p) for p in train_df["audio_path"]]
    X_train = np.array(train_feats)
    y_train = (train_df["label"] == "spoof").astype(int).values

    # Train shallow logistic regression
    clf = LogisticRegression(random_state=42, max_iter=200)
    clf.fit(X_train, y_train)

    test_files = [
        ("Test InDomain", manifest_dir / "test_indomain.csv"),
        ("Test OOD", manifest_dir / "test_ood.csv"),
        ("Dev", manifest_dir / "dev.csv"),
    ]

    for name, test_path in test_files:
        if not test_path.exists():
            continue
        test_df = pd.read_csv(test_path)
        print(f"\n--- Đánh giá trên {name} ({len(test_df)} mẫu) ---")
        test_feats = [extract_spectral_shortcuts(p) for p in test_df["audio_path"]]
        X_test = np.array(test_feats)
        y_test = (test_df["label"] == "spoof").astype(int).values

        y_prob = clf.predict_proba(X_test)[:, 1]
        auc, low, high = bootstrap_auc_ci(y_test, y_prob)
        flag = "⚠️ CẢNH BÁO SHORTCUT" if auc > 0.65 else "✅ AN TOÀN (KHÔNG BỊ SHORTCUT)"
        print(f"Tổng thể: AUC = {auc:.3f} (95% CI: [{low:.3f}, {high:.3f}]) -> {flag}")

        # Sliced by Codec
        for codec in test_df["codec"].unique():
            mask = (test_df["codec"] == codec).values
            if np.sum(mask) > 10 and len(np.unique(y_test[mask])) > 1:
                c_auc, c_low, c_high = bootstrap_auc_ci(y_test[mask], y_prob[mask])
                print(f" - Codec {codec:<12}: AUC = {c_auc:.3f} [{c_low:.3f}, {c_high:.3f}]")

        # Sliced by Source
        for src in test_df["source"].unique():
            mask = (test_df["source"] == src).values
            if np.sum(mask) > 10 and len(np.unique(y_test[mask])) > 1:
                s_auc, s_low, s_high = bootstrap_auc_ci(y_test[mask], y_prob[mask])
                print(f" - Source {src:<12}: AUC = {s_auc:.3f} [{s_low:.3f}, {s_high:.3f}]")


if __name__ == "__main__":
    main()
