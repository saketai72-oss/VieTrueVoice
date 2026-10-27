"""Human baseline and manual verification evaluation metrics.

Includes Wilson score interval computation for small-sample statistics and trial aggregation.
"""

from typing import Dict, Tuple, Any
import math
import pandas as pd


def compute_wilson_interval(errors: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute the Wilson score interval for a binomial proportion.

    Args:
        errors: Number of incorrect classifications.
        total: Total number of trials.
        confidence: Confidence level (default 0.95).

    Returns:
        Tuple of (lower_bound, upper_bound) in range [0.0, 1.0].
    """
    if total <= 0:
        return 0.0, 0.0

    # Common z values to avoid heavy scipy dependency if possible, fallback to math
    z_table = {
        0.90: 1.6448536269514722,
        0.95: 1.959963984540054,
        0.99: 2.5758293035489004,
    }
    z = z_table.get(confidence, 1.959963984540054)

    p_hat = float(errors) / float(total)
    z2 = z * z
    n = float(total)

    denominator = 1.0 + (z2 / n)
    center = (p_hat + (z2 / (2.0 * n))) / denominator
    spread = (z / denominator) * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n)))

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return float(lower), float(upper)


def evaluate_human_responses(responses_df: pd.DataFrame, key_df: pd.DataFrame) -> Dict[str, Any]:
    """Evaluate human responses against ground truth blind key.

    Args:
        responses_df: DataFrame with ['participant_id', 'sample_id', 'predicted_label'].
        key_df: DataFrame with ['sample_id', 'true_label'].

    Returns:
        Dict of metrics including total_trials, error_count, error_rate, accuracy, Wilson bounds.
    """
    merged = pd.merge(responses_df, key_df[["sample_id", "true_label"]], on="sample_id")

    pred = merged["predicted_label"].astype(str).str.strip().str.lower()
    true = merged["true_label"].astype(str).str.strip().str.lower()

    # Map possible synonyms to standard 'bonafide' / 'spoof'
    label_map = {
        "thật": "bonafide",
        "that": "bonafide",
        "bonafide": "bonafide",
        "bona_fide": "bonafide",
        "giả": "spoof",
        "gia": "spoof",
        "spoof": "spoof",
    }
    pred_std = pred.map(lambda x: label_map.get(x, x))
    true_std = true.map(lambda x: label_map.get(x, x))

    correct_mask = pred_std == true_std
    total = len(merged)
    correct_count = int(correct_mask.sum())
    error_count = total - correct_count

    error_rate = error_count / total if total > 0 else 0.0
    accuracy = correct_count / total if total > 0 else 0.0
    w_low, w_high = compute_wilson_interval(error_count, total, confidence=0.95)

    result: Dict[str, Any] = {
        "total_trials": total,
        "correct_count": correct_count,
        "error_count": error_count,
        "accuracy": float(accuracy),
        "error_rate": float(error_rate),
        "wilson_95_lower": float(w_low),
        "wilson_95_upper": float(w_high),
    }

    # Integrate latency metrics if present
    lat_col = "latency_sec" if "latency_sec" in merged.columns else ("total_sec" if "total_sec" in merged.columns else None)
    if lat_col:
        valid_lat = pd.to_numeric(merged[lat_col], errors="coerce").dropna()
        if len(valid_lat) > 0:
            result["median_latency_sec"] = float(valid_lat.median())
            result["mean_latency_sec"] = float(valid_lat.mean())
            result["min_latency_sec"] = float(valid_lat.min())
            result["max_latency_sec"] = float(valid_lat.max())

    return result


def summarize_manual_trials(trials_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Summarize manual verification trials by method.

    Args:
        trials_df: DataFrame with ['method', 'total_sec', 'is_correct'].

    Returns:
        Dict mapping method name to statistics (median_sec, mean_sec, error_rate, count).
    """
    summary = {}
    for method, group in trials_df.groupby("method"):
        method_str = str(method)
        total_trials = len(group)
        is_correct = group["is_correct"].astype(bool)
        errors = int((~is_correct).sum())

        median_sec = float(group["total_sec"].median())
        mean_sec = float(group["total_sec"].mean())
        err_rate = float(errors / total_trials) if total_trials > 0 else 0.0

        summary[method_str] = {
            "trial_count": total_trials,
            "median_sec": median_sec,
            "mean_sec": mean_sec,
            "error_rate": err_rate,
        }
    return summary
