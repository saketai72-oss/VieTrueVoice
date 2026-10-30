"""Đánh giá Baseline Kênh Zalo cho Checkpoint B (Pha 5).

Chấm điểm suy luận Checkpoint B trên tập dữ liệu ghép cặp base_utt,
đo lường độ lệch điểm theo cặp (paired score difference),
tính EER, FAR, FRR, minDCF và khoảng tin cậy 95% Bootstrap theo cụm base_utt
cho từng codec (clean_16khz, g711_alaw, amr_nb, aac_zalo_76k, opus_zalo_24k).
"""

from __future__ import annotations
import argparse
import io
import os
from pathlib import Path
import sys

# Ensure root in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import soundfile as sf
import torch

from scripts.eval_ssl_aasist import load_model
from scripts.generate_zalo_paired_manifests import (
    derive_base_utt,
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)
from src.evaluation.metrics import compute_eer, compute_min_dcf
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def find_audio_file(audio_path: str, candidates_roots: list[Path]) -> Path | None:
    """Find audio file across possible candidate root directories."""
    p = Path(audio_path)
    if p.exists():
        return p
    for root in candidates_roots:
        cand = root / audio_path
        if cand.exists():
            return cand
        # Also try replacing data/raw with out/kaggle_ssl_out/data/raw
        if "data/raw" in audio_path:
            alt = root / audio_path.replace("data/raw/", "out/kaggle_ssl_out/data/raw/")
            if alt.exists():
                return alt
            alt2 = root / audio_path.replace("data/raw", "data/raw")
            if alt2.exists():
                return alt2
    return None


def cluster_bootstrap_ci(
    df: pd.DataFrame,
    codec_name: str,
    n_boot: int = 1000,
    seed: int = 42,
) -> dict[str, tuple[float, float]]:
    """Compute 95% Confidence Interval via Cluster Bootstrap over base_utt."""
    subset = df[df["codec"] == codec_name].copy()
    lbl_col = "label" if "label" in subset.columns else "label_int"
    if len(subset) == 0 or subset[lbl_col].nunique() < 2:
        return {}

    clusters = subset["base_utt"].unique()
    n_clusters = len(clusters)
    if n_clusters < 5:
        return {}

    # Map cluster to sub-dataframe
    grouped = {k: v for k, v in subset.groupby("base_utt")}
    rng = np.random.default_rng(seed)

    boot_eers, boot_frrs, boot_fars = [], [], []

    for _ in range(n_boot):
        sampled_c = rng.choice(clusters, size=n_clusters, replace=True)
        boot_sub = pd.concat([grouped[c] for c in sampled_c], ignore_index=True)
        
        y_true = (
            boot_sub[lbl_col].to_numpy().astype(int)
            if lbl_col == "label_int"
            else np.where(boot_sub[lbl_col].astype(str).str.lower().isin(["bonafide", "1"]), 1, 0)
        )
        y_score = boot_sub["score"].to_numpy().astype(float)
        
        if len(np.unique(y_true)) < 2:
            continue

        try:
            eer_val, _ = compute_eer(y_score, y_true)
            boot_eers.append(eer_val * 100.0)
        except Exception:
            pass

        # At theta = 0.0
        n_bona = np.sum(y_true == 1)
        n_spoof = np.sum(y_true == 0)
        if n_bona > 0:
            frr_val = float(np.sum((y_true == 1) & (y_score < 0.0)) / n_bona * 100.0)
            boot_frrs.append(frr_val)
        if n_spoof > 0:
            far_val = float(np.sum((y_true == 0) & (y_score >= 0.0)) / n_spoof * 100.0)
            boot_fars.append(far_val)

    def ci(arr):
        if len(arr) == 0:
            return (0.0, 0.0)
        return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))

    return {
        "eer_ci": ci(boot_eers),
        "frr_ci": ci(boot_frrs),
        "far_ci": ci(boot_fars),
    }


def compute_codec_metrics(
    c_df: pd.DataFrame,
    scored_df: pd.DataFrame | None = None,
    n_boot: int = 1000,
) -> dict:
    """Compute verification metrics per codec with strict validity check."""
    c_name = c_df["codec"].iloc[0]
    y_true = c_df["label_int"].to_numpy().astype(int)
    y_score = c_df["score"].to_numpy().astype(float)

    n_bona = int(np.sum(y_true == 1))
    n_spoof = int(np.sum(y_true == 0))
    has_both_classes = (n_bona > 0 and n_spoof > 0)

    if has_both_classes:
        eer, eer_thr = compute_eer(y_score, y_true)
        min_dcf = compute_min_dcf(y_score, y_true)
    else:
        eer, eer_thr = float("nan"), float("nan")
        min_dcf = float("nan")

    frr_0 = float(np.sum((y_true == 1) & (y_score < 0.0)) / n_bona * 100.0) if n_bona > 0 else float("nan")
    far_0 = float(np.sum((y_true == 0) & (y_score >= 0.0)) / n_spoof * 100.0) if n_spoof > 0 else float("nan")

    ci_source = scored_df if scored_df is not None else c_df
    ci_res = cluster_bootstrap_ci(ci_source, c_name, n_boot=n_boot) if has_both_classes else {}
    eer_ci = ci_res.get("eer_ci", (float("nan"), float("nan")))
    frr_ci = ci_res.get("frr_ci", (float("nan"), float("nan")))
    far_ci = ci_res.get("far_ci", (float("nan"), float("nan")))

    return {
        "codec": c_name,
        "n_total": len(c_df),
        "n_bonafide": n_bona,
        "n_spoof": n_spoof,
        "is_valid": has_both_classes,
        "eer_pct": eer * 100.0 if not np.isnan(eer) else float("nan"),
        "eer_ci_95": f"[{eer_ci[0]:.2f}, {eer_ci[1]:.2f}]" if not np.isnan(eer_ci[0]) else "N/A",
        "eer_threshold": eer_thr,
        "min_dcf": min_dcf,
        "frr_theta_0": frr_0,
        "frr_ci_95": f"[{frr_ci[0]:.2f}, {frr_ci[1]:.2f}]" if not np.isnan(frr_ci[0]) else "N/A",
        "far_theta_0": far_0,
        "far_ci_95": f"[{far_ci[0]:.2f}, {far_ci[1]:.2f}]" if not np.isnan(far_ci[0]) else "N/A",
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Zalo Baseline on Checkpoint B.")
    parser.add_argument("--ckpt", default="out/kaggle_ssl_out/best_model_B.pt", help="Path to Checkpoint B")
    parser.add_argument("--manifest", default="data/manifests_zalo/dev_zalo.csv", help="Paired manifest to evaluate")
    parser.add_argument("--out-dir", default="out/zalo_baseline", help="Directory to save baseline outputs")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="Device (cuda/cpu)")
    parser.add_argument("--n-boot", type=int, default=1000, help="Number of bootstrap iterations")
    parser.add_argument("--max-samples", type=int, default=0, help="Optional limit for quick testing (0 = all)")
    parser.add_argument("--allow-missing", action="store_true", help="Allow missing audio files instead of raising FileNotFoundError")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading checkpoint: {args.ckpt} on {args.device}...")
    model, _ = load_model(args.ckpt, args.device)
    model.eval()

    print(f"Loading manifest: {args.manifest}...")
    df = pd.read_csv(args.manifest)
    if "base_utt" not in df.columns:
        df["base_utt"] = df["utt_id"].apply(derive_base_utt)

    candidate_roots = [
        Path("."),
        Path("out/kaggle_ssl_out"),
        Path("out/kaggle_ssl_out/data"),
        Path("data"),
    ]

    # Pre-index clean files by base_utt for on-the-fly proxy generation
    clean_audio_map = {}
    for _, row in df[df["codec"] == "clean_16khz"].iterrows():
        found = find_audio_file(row["audio_path"], candidate_roots)
        if found:
            clean_audio_map[row["base_utt"]] = found

    print(f"Indexed {len(clean_audio_map)} clean audio files available for inference.")

    rng = np.random.default_rng(0)
    scored_records = []
    
    # Process manifest rows
    rows_to_process = df.to_dict("records")
    if args.max_samples > 0:
        rows_to_process = rows_to_process[:args.max_samples]

    print(f"Starting inference on {len(rows_to_process)} manifest rows...")
    with torch.no_grad():
        for i, row in enumerate(rows_to_process):
            base_utt = row["base_utt"]
            codec = row["codec"]
            label_int = 1 if str(row["label"]).lower() in ["bonafide", "1"] else 0
            
            # Find or synthesize audio waveform
            wav_16k = None
            found_path = find_audio_file(row["audio_path"], candidate_roots)
            
            if found_path and found_path.exists():
                wav_16k = load_audio(found_path, target_sr=16000)
            elif codec in ["aac_zalo_76k", "opus_zalo_24k"] and base_utt in clean_audio_map:
                # On-the-fly proxy synthesis from clean master
                clean_p = clean_audio_map[base_utt]
                with open(clean_p, "rb") as f:
                    clean_bytes = f.read()
                if codec == "aac_zalo_76k":
                    proxy_bytes = transcode_aac_adts_stream(clean_bytes)
                else:
                    proxy_bytes = transcode_opus_ogg_stream(clean_bytes)
                wav_16k = load_audio(proxy_bytes, target_sr=16000)

            if wav_16k is None:
                if not args.allow_missing:
                    raise FileNotFoundError(
                        f"Failed to find or load audio for row {i} (utt_id={row.get('utt_id')}, "
                        f"codec={codec}, path={row.get('audio_path')}). Use --allow-missing to skip."
                    )
                continue

            # Fit length to 64,000 samples via repeat padding
            t = fit_length(wav_16k, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(args.device)
            score = model.score(tensor).item()

            rec = dict(row)
            rec["score"] = score
            rec["label_int"] = label_int
            scored_records.append(rec)

            if (i + 1) % 50 == 0 or (i + 1) == len(rows_to_process):
                print(f"Processed {i + 1}/{len(rows_to_process)} rows (valid scores: {len(scored_records)})...")

    scored_df = pd.DataFrame(scored_records)
    scores_csv = out_dir / "dev_zalo_scores.csv"
    scored_df.to_csv(scores_csv, index=False)
    print(f"\nSaved scored dataset to {scores_csv} ({len(scored_df)} rows)")

    # 1. Metric evaluation per codec with strict validation
    metric_rows = []
    for c_name, c_df in scored_df.groupby("codec"):
        m = compute_codec_metrics(c_df, scored_df=scored_df, n_boot=args.n_boot)
        metric_rows.append(m)

    metrics_df = pd.DataFrame(metric_rows)
    metrics_csv = out_dir / "zalo_baseline_metrics.csv"
    metrics_df.to_csv(metrics_csv, index=False)
    print(f"\nSaved baseline metrics to {metrics_csv}")
    print(metrics_df.to_string())

    # 2. Paired Score Difference: delta = s_proxy - s_clean
    paired_deltas = []
    clean_scores = scored_df[scored_df["codec"] == "clean_16khz"].set_index("base_utt")["score"].to_dict()

    for p_codec in ["aac_zalo_76k", "opus_zalo_24k", "g711_alaw", "amr_nb"]:
        proxy_df = scored_df[scored_df["codec"] == p_codec]
        for _, row in proxy_df.iterrows():
            b_utt = row["base_utt"]
            if b_utt in clean_scores:
                s_clean = clean_scores[b_utt]
                s_proxy = row["score"]
                delta = s_proxy - s_clean
                paired_deltas.append({
                    "base_utt": b_utt,
                    "proxy_codec": p_codec,
                    "label": row["label"],
                    "tts_generator": row.get("tts_generator", "none"),
                    "score_clean": s_clean,
                    "score_proxy": s_proxy,
                    "delta": delta,
                })

    paired_df = pd.DataFrame(paired_deltas)
    paired_csv = out_dir / "zalo_paired_deltas.csv"
    paired_df.to_csv(paired_csv, index=False)

    print("\nPaired delta summary by proxy codec:")
    if len(paired_df) > 0:
        summary_delta = paired_df.groupby("proxy_codec")["delta"].agg(["count", "mean", "std", "median", "min", "max"])
        print(summary_delta.round(3).to_string())


if __name__ == "__main__":
    main()
