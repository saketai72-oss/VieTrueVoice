"""Evaluation metrics: EER, minDCF, ROC-AUC, Confusion Matrix, and Human Baseline Metrics."""

from src.evaluation.human_metrics import (
    compute_wilson_interval,
    evaluate_human_responses,
    summarize_manual_trials,
)
from src.evaluation.metrics import (
    compute_eer,
    compute_min_dcf,
    confusion_at_threshold,
    cluster_bootstrap_ci,
    compute_det_curve,
)

__all__ = [
    "compute_wilson_interval",
    "evaluate_human_responses",
    "summarize_manual_trials",
    "compute_eer",
    "compute_min_dcf",
    "confusion_at_threshold",
    "cluster_bootstrap_ci",
    "compute_det_curve",
]
