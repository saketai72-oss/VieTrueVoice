"""Tests for eval_zalo_baseline module (Pha 5)."""

from __future__ import annotations
import numpy as np
import pandas as pd
import pytest

from scripts.eval_zalo_baseline import cluster_bootstrap_ci, compute_codec_metrics


def test_cluster_bootstrap_ci():
    # Synthetic cluster dataframe with 20 base_utts
    records = []
    rng = np.random.default_rng(42)
    for i in range(20):
        base_utt = f"utt_{i:02d}"
        label = 1 if i < 10 else 0
        base_score = 5.0 if label == 1 else -5.0
        # 3 codecs per base_utt
        for codec in ["clean_16khz", "aac_zalo_76k"]:
            score = base_score + rng.normal(0, 0.5)
            records.append({
                "base_utt": base_utt,
                "label": label,
                "codec": codec,
                "score": score,
            })
    df = pd.DataFrame(records)

    ci = cluster_bootstrap_ci(df, "clean_16khz", n_boot=50, seed=42)
    assert "eer_ci" in ci
    assert "frr_ci" in ci
    assert "far_ci" in ci
    assert len(ci["eer_ci"]) == 2
    assert ci["eer_ci"][0] <= ci["eer_ci"][1]


def test_compute_codec_metrics_both_classes():
    df = pd.DataFrame([
        {"codec": "aac_zalo_76k", "label_int": 1, "score": 2.5, "base_utt": f"u{i}"} for i in range(10)
    ] + [
        {"codec": "aac_zalo_76k", "label_int": 0, "score": -3.0, "base_utt": f"s{i}"} for i in range(10)
    ])
    res = compute_codec_metrics(df, n_boot=20)
    assert res["is_valid"] is True
    assert res["n_bonafide"] == 10
    assert res["n_spoof"] == 10
    assert not np.isnan(res["eer_pct"])
    assert res["frr_theta_0"] == 0.0
    assert res["far_theta_0"] == 0.0


def test_compute_codec_metrics_missing_spoof_fails_validity():
    df = pd.DataFrame([
        {"codec": "aac_zalo_76k", "label_int": 1, "score": 2.5, "base_utt": f"u{i}"} for i in range(10)
    ])
    res = compute_codec_metrics(df, n_boot=20)
    assert res["is_valid"] is False
    assert res["n_bonafide"] == 10
    assert res["n_spoof"] == 0
    assert np.isnan(res["eer_pct"])
    assert np.isnan(res["far_theta_0"])
    assert res["eer_ci_95"] == "N/A"

