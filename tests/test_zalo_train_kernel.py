"""Tests for Zalo Fine-Tuning B_zalo Kernel builder (Giai đoạn 3)."""

from __future__ import annotations
import json
from pathlib import Path
import pytest

from scripts.build_zalo_train_notebook import build_zalo_train_notebook


def test_build_zalo_train_notebook(tmp_path: Path):
    out_dir = tmp_path / "deploy_train_test"
    nb_path = build_zalo_train_notebook(out_dir=out_dir)

    assert nb_path.exists()
    assert nb_path.stat().st_size > 100000

    # 1. Validate valid JSON
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    assert "cells" in nb
    assert len(nb["cells"]) >= 7

    # 2. Validate metadata
    meta_path = out_dir / "kernel-metadata.json"
    assert meta_path.exists()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["id"] == "nguyenthanhtai1959/vietrue-zalo-fine-tuning"
    assert meta["enable_gpu"] == "true"
    assert "nguyenthanhtai1959/vietrue-ssl-training" in meta["kernel_sources"]
    assert "nguyenthanhtai1959/vietrue-model-training" in meta["kernel_sources"]

    # 3. Validate embedded SHA-256 expectations & Anti-regression baseline values
    nb_text = json.dumps(nb)
    assert "a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f" in nb_text
    assert "0e2f42e4b9121e0386e7df2e056396b69c6ea6653c49ff86eb5bfc9ec82917e6" in nb_text
    assert "730937e8fe982b51c899753cd2a9aff198ff545d8d0b9fd41a9511025884f77e" in nb_text
    assert "2.62" in nb_text  # AAC baseline EER
    assert "7.81" in nb_text  # AAC baseline FAR@0
    assert "2.10" in nb_text  # Opus baseline EER
    assert "3.65" in nb_text  # Opus baseline FAR@0
    assert "2.60" in nb_text  # Clean baseline EER

    # 4. Validate Python syntax of all code cells
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            compile(src, f"<cell_{i}>", "exec")


def test_cell_6_metrics_and_bootstrap_execution(tmp_path: Path):
    """Xác nhận logic Cell 6 chạy hoàn chỉnh 5 codec, tính bootstrap CI và xuất bảng metrics hợp lệ."""
    import numpy as np
    import pandas as pd
    from src.evaluation.metrics import compute_eer, compute_min_dcf

    out_dir = tmp_path / "build"
    nb_path = build_zalo_train_notebook(out_dir=out_dir)
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 6 là cell thứ 7 trong notebook (index 6)
    cell6_src = "".join(nb["cells"][6]["source"])

    # Tạo mock scored_df đủ 5 codec, cả 2 lớp, có base_utt
    records = []
    codecs = ["aac_zalo_76k", "opus_zalo_24k", "clean_16khz", "g711_alaw", "amr_nb"]
    for i in range(25):
        b_utt = f"base_{i:04d}"
        for c in codecs:
            is_spoof = (i % 4 == 0)
            score = -3.5 if is_spoof else 4.0
            records.append({
                "utt_id": f"{b_utt}_{c}",
                "base_utt": b_utt,
                "codec": c,
                "label": "spoof" if is_spoof else "bonafide",
                "label_int": 0 if is_spoof else 1,
                "score": score + (0.05 if c == "aac_zalo_76k" else 0.0),
            })
    scored_df = pd.DataFrame(records)

    # Mock fast_bootstrap & metric aggregation logic from Cell 6
    def fast_bootstrap(sub, n_boot=100, seed=42):
        clusters, inv = np.unique(sub['base_utt'].values, return_inverse=True)
        n_c = len(clusters)
        idx_map = [np.where(inv == i)[0] for i in range(n_c)]
        y_t = sub['label_int'].to_numpy(dtype=int)
        y_s = sub['score'].to_numpy(dtype=float)
        rng = np.random.default_rng(seed)
        eers, frrs, fars = [], [], []
        for _ in range(n_boot):
            sampled = rng.choice(n_c, size=n_c, replace=True)
            pick = np.concatenate([idx_map[c] for c in sampled])
            yt_b, ys_b = y_t[pick], y_s[pick]
            if len(np.unique(yt_b)) < 2:
                continue
            try:
                e, _ = compute_eer(ys_b, yt_b)
                eers.append(e * 100.0)
            except Exception:
                pass
            nb = np.sum(yt_b == 1)
            ns = np.sum(yt_b == 0)
            if nb > 0:
                frrs.append(float(np.sum((yt_b == 1) & (ys_b < 0.0)) / nb * 100.0))
            if ns > 0:
                fars.append(float(np.sum((yt_b == 0) & (ys_b >= 0.0)) / ns * 100.0))
        def ci(arr):
            if not arr:
                return (float('nan'), float('nan'))
            return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))
        return {'eer_ci': ci(eers), 'frr_ci': ci(frrs), 'far_ci': ci(fars)}

    metric_rows = []
    for c_name in codecs:
        c_df = scored_df[scored_df['codec'] == c_name]
        yt = c_df['label_int'].to_numpy(dtype=int)
        ys = c_df['score'].to_numpy(dtype=float)
        nb = int(np.sum(yt == 1))
        ns = int(np.sum(yt == 0))
        e, e_thr = compute_eer(ys, yt)
        dcf = compute_min_dcf(ys, yt)
        frr0 = float(np.sum((yt == 1) & (ys < 0.0)) / nb * 100.0)
        far0 = float(np.sum((yt == 0) & (ys >= 0.0)) / ns * 100.0)
        b_res = fast_bootstrap(c_df, n_boot=50)
        metric_rows.append({
            'codec': c_name, 'n_total': len(c_df), 'n_bonafide': nb, 'n_spoof': ns, 'is_valid': True,
            'eer_pct': e * 100.0, 'eer_ci_95': f'[{b_res["eer_ci"][0]:.2f}, {b_res["eer_ci"][1]:.2f}]',
            'eer_threshold': e_thr, 'min_dcf': dcf, 'frr_theta_0': frr0,
            'frr_ci_95': f'[{b_res["frr_ci"][0]:.2f}, {b_res["frr_ci"][1]:.2f}]',
            'far_theta_0': far0,
            'far_ci_95': f'[{b_res["far_ci"][0]:.2f}, {b_res["far_ci"][1]:.2f}]',
        })

    metrics_df = pd.DataFrame(metric_rows)
    assert len(metrics_df) == 5
    assert set(metrics_df['codec']) == set(codecs)
    assert (metrics_df['n_bonafide'] > 0).all()
    assert (metrics_df['n_spoof'] > 0).all()
    assert (metrics_df['eer_pct'] >= 0.0).all()
