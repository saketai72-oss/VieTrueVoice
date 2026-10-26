"""Unit tests for human blind test evaluation and Wilson interval calculations."""

import pytest
import pandas as pd
import numpy as np

from src.evaluation.human_metrics import (
    compute_wilson_interval,
    evaluate_human_responses,
    summarize_manual_trials,
)


def test_wilson_interval_bounds():
    """Verify Wilson interval returns bounds in [0, 1] and contains empirical mean."""
    # 36 errors out of 72 trials (p_hat = 0.5)
    lower, upper = compute_wilson_interval(errors=36, total=72, confidence=0.95)
    assert 0.0 <= lower <= 0.5 <= upper <= 1.0
    # For p=0.5, n=72, Wilson interval is roughly [0.386, 0.614]
    assert pytest.approx(lower, abs=0.02) == 0.386
    assert pytest.approx(upper, abs=0.02) == 0.614


def test_wilson_interval_extremes():
    """Verify Wilson interval behavior at 0 and 100% errors."""
    low_0, high_0 = compute_wilson_interval(errors=0, total=72, confidence=0.95)
    assert low_0 >= 0.0
    assert high_0 > 0.0

    low_n, high_n = compute_wilson_interval(errors=72, total=72, confidence=0.95)
    assert low_n < 1.0
    assert high_n <= 1.0


def test_evaluate_human_responses():
    """Verify human response evaluation calculates accuracy, error rate and balanced metrics."""
    key_df = pd.DataFrame({
        "sample_id": ["s01", "s02", "s03", "s04"],
        "true_label": ["bonafide", "bonafide", "spoof", "spoof"],
    })

    responses_df = pd.DataFrame({
        "participant_id": ["P01", "P01", "P01", "P01", "P02", "P02", "P02", "P02"],
        "sample_id": ["s01", "s02", "s03", "s04", "s01", "s02", "s03", "s04"],
        "predicted_label": [
            "bonafide", "spoof", "spoof", "bonafide",  # P01: 2 wrong out of 4
            "bonafide", "bonafide", "spoof", "spoof",  # P02: 4 correct out of 4
        ],
    })

    metrics = evaluate_human_responses(responses_df, key_df)
    assert metrics["total_trials"] == 8
    assert metrics["error_count"] == 2
    assert metrics["error_rate"] == 0.25
    assert metrics["accuracy"] == 0.75
    assert metrics["wilson_95_lower"] <= 0.25 <= metrics["wilson_95_upper"]


def test_summarize_manual_trials():
    """Verify manual verification trial summary computes median latency and error rate per method."""
    trials_df = pd.DataFrame({
        "trial_id": ["T01", "T02", "T03", "T04"],
        "method": ["ear", "ear", "spectrogram", "spectrogram"],
        "sample_id": ["s01", "s02", "s01", "s02"],
        "total_sec": [4.0, 6.0, 45.0, 75.0],
        "is_correct": [False, True, True, True],
    })

    summary = summarize_manual_trials(trials_df)
    assert "ear" in summary
    assert "spectrogram" in summary
    assert summary["ear"]["median_sec"] == 5.0
    assert summary["ear"]["error_rate"] == 0.5
    assert summary["spectrogram"]["median_sec"] == 60.0
    assert summary["spectrogram"]["error_rate"] == 0.0
