"""Calculate human error rate (with Wilson 95% interval) and manual trial latencies.

Usage:
    python scripts/calc_human_metrics.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from src.evaluation.human_metrics import (
    evaluate_human_responses,
    summarize_manual_trials,
)


def run_calculations(
    key_csv: str = "benchmarks/blind_key_private.csv",
    responses_csv: str = "benchmarks/human_blind_responses.csv",
    trials_csv: str = "benchmarks/manual_verification_trials.csv",
    output_metrics_csv: str = "benchmarks/human_baseline_metrics.csv",
):
    if not os.path.exists(key_csv):
        print(f"[ERROR] Ground truth key not found at {key_csv}. Run scripts/prepare_blind_test.py first.")
        return

    key_df = pd.read_csv(key_csv)
    print(f"Loaded ground truth key: {len(key_df)} samples.")

    # 1. Human Blind Responses Evaluation
    if os.path.exists(responses_csv) and os.path.getsize(responses_csv) > 50:
        responses_df = pd.read_csv(responses_csv)
        # Drop rows where predicted_label is empty or NaN
        valid_responses = responses_df.dropna(subset=["predicted_label"]).copy()
        if len(valid_responses) > 0:
            print(f"\n--- Phép đo 1: Đánh giá mù tai người ({len(valid_responses)} lượt nghe) ---")
            metrics = evaluate_human_responses(valid_responses, key_df)
            print(f"Tổng số lượt thử (N): {metrics['total_trials']}")
            print(f"Số câu đúng: {metrics['correct_count']} | Số câu sai: {metrics['error_count']}")
            print(f"Độ chính xác (Accuracy): {metrics['accuracy'] * 100:.2f}%")
            print(f"Tỷ lệ sai (Error Rate / Tai người): {metrics['error_rate'] * 100:.2f}%")
            print(f"Khoảng tin cậy 95% Wilson CI: [{metrics['wilson_95_lower'] * 100:.2f}%, {metrics['wilson_95_upper'] * 100:.2f}%]")

            # Save summary metrics
            out_df = pd.DataFrame([{
                "metric": "human_blind_error_rate",
                "trials": metrics["total_trials"],
                "error_count": metrics["error_count"],
                "error_rate_percent": round(metrics["error_rate"] * 100, 2),
                "wilson_95_lower_percent": round(metrics["wilson_95_lower"] * 100, 2),
                "wilson_95_upper_percent": round(metrics["wilson_95_upper"] * 100, 2),
            }])
            out_df.to_csv(output_metrics_csv, index=False, encoding="utf-8")
            print(f"Đã lưu kết quả chỉ số tai người vào {output_metrics_csv}")
        else:
            print(f"\n[INFO] {responses_csv} chưa có dữ liệu phản hồi.")
    else:
        print(f"\n[INFO] {responses_csv} chưa có dữ liệu phản hồi.")

    # 2. Manual Verification Trials (Latency)
    if os.path.exists(trials_csv):
        trials_df = pd.read_csv(trials_csv)
        # Check if total_sec has values
        trials_with_sec = trials_df.dropna(subset=["total_sec"]).copy()
        # Filter numeric total_sec
        trials_with_sec = trials_with_sec[pd.to_numeric(trials_with_sec["total_sec"], errors="coerce").notnull()].copy()
        trials_with_sec["total_sec"] = trials_with_sec["total_sec"].astype(float)

        if len(trials_with_sec) > 0:
            print(f"\n--- Phép đo 2: Thời gian và độ chính xác xác minh thủ công ({len(trials_with_sec)} lượt đo) ---")
            # Auto fill is_correct if predicted_label is provided
            if "predicted_label" in trials_with_sec.columns and trials_with_sec["predicted_label"].notnull().any():
                merged = pd.merge(trials_with_sec, key_df[["sample_id", "true_label"]], on="sample_id", how="left")
                pred = merged["predicted_label"].astype(str).str.strip().str.lower()
                true = merged["true_label"].astype(str).str.strip().str.lower()
                label_map = {"thật": "bonafide", "that": "bonafide", "giả": "spoof", "gia": "spoof"}
                pred_std = pred.map(lambda x: label_map.get(x, x))
                true_std = true.map(lambda x: label_map.get(x, x))
                trials_with_sec["is_correct"] = pred_std == true_std

            summary = summarize_manual_trials(trials_with_sec)
            for m, stats in summary.items():
                print(f"Phương pháp [{m.upper()}]:")
                print(f"  Số lượt đo: {stats['trial_count']}")
                print(f"  Trung vị thời gian (Median Latency): {stats['median_sec']:.2f} giây")
                print(f"  Thời gian trung bình (Mean Latency): {stats['mean_sec']:.2f} giây")
                print(f"  Tỷ lệ sai (Error Rate): {stats['error_rate'] * 100:.2f}%")
        else:
            print(f"\n[INFO] {trials_csv} chưa điền cột total_sec.")


if __name__ == "__main__":
    run_calculations()
