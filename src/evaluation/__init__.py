"""Evaluation metrics: EER, minDCF, ROC-AUC, Confusion Matrix, and Human Baseline Metrics."""

from src.evaluation.human_metrics import (
    compute_wilson_interval,
    evaluate_human_responses,
    summarize_manual_trials,
)

__all__ = [
    "compute_wilson_interval",
    "evaluate_human_responses",
    "summarize_manual_trials",
]

