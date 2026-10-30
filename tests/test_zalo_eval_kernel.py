"""Tests for Zalo Baseline Evaluation Kernel builder (Giai đoạn 2)."""

from __future__ import annotations
import json
from pathlib import Path
import pytest

from scripts.build_zalo_eval_notebook import build_zalo_eval_notebook


def test_build_zalo_eval_notebook(tmp_path: Path):
    out_dir = tmp_path / "deploy_test"
    nb_path = build_zalo_eval_notebook(out_dir=out_dir)

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

    assert meta["id"] == "nguyenthanhtai1959/vietrue-zalo-baseline-evaluation"
    assert meta["enable_gpu"] == "true"
    assert "nguyenthanhtai1959/vietrue-ssl-training" in meta["kernel_sources"]
    assert "nguyenthanhtai1959/vietrue-model-training" in meta["kernel_sources"]

    # 3. Validate embedded SHA-256 expectations
    nb_text = json.dumps(nb)
    assert "a921c3397946335c9543528993eafde80ac0d42decf431101635806b5c56bd9f" in nb_text
    assert "730937e8fe982b51c899753cd2a9aff198ff545d8d0b9fd41a9511025884f77e" in nb_text
    assert "11450" in nb_text
    assert "strict=True" in nb_text

    # 4. Validate Python syntax of all code cells
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            compile(src, f"<cell_{i}>", "exec")


def test_cell_7_metrics_and_bootstrap_execution(tmp_path: Path):
    """Xác nhận Cell 7 chạy hoàn chỉnh 5 codec, có đủ 2 lớp, xuất đủ metrics & paired deltas."""
    from scripts.build_zalo_eval_notebook import build_zalo_eval_notebook
    import numpy as np
    import pandas as pd
    from src.evaluation.metrics import compute_eer, compute_min_dcf

    nb_path = build_zalo_eval_notebook(out_dir=tmp_path / "build")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 7 là cell thứ 8 trong notebook (index 7)
    cell7_src = "".join(nb["cells"][7]["source"])

    # Tạo mock scored_df đủ 5 codec, cả 2 lớp, có base_utt ghép cặp
    records = []
    codecs = ["aac_zalo_76k", "opus_zalo_24k", "clean_16khz", "g711_alaw", "amr_nb"]
    for i in range(20):
        b_utt = f"base_{i:04d}"
        for c in codecs:
            is_spoof = (i % 4 == 0)
            score = -5.0 if is_spoof else 5.0
            records.append({
                "utt_id": f"{b_utt}_{c}",
                "base_utt": b_utt,
                "codec": c,
                "label": "spoof" if is_spoof else "bonafide",
                "label_int": 0 if is_spoof else 1,
                "score": score + (0.1 if c == "aac_zalo_76k" else 0.0),
            })
    scored_df = pd.DataFrame(records)

    scope = {
        "pd": pd,
        "np": np,
        "shutil": __import__("shutil"),
        "compute_eer": compute_eer,
        "compute_min_dcf": compute_min_dcf,
        "scored_df": scored_df,
        "working_dir": tmp_path,
    }

    # Thực thi Cell 7 trực tiếp
    exec(cell7_src, scope)

    # Xác nhận 2 tệp CSV đầu ra được sinh ra hợp lệ
    metrics_path = tmp_path / "zalo_baseline_metrics.csv"
    deltas_path = tmp_path / "zalo_paired_deltas.csv"

    assert metrics_path.exists(), "❌ Không tìm thấy zalo_baseline_metrics.csv!"
    assert deltas_path.exists(), "❌ Không tìm thấy zalo_paired_deltas.csv!"

    df_m = pd.read_csv(metrics_path)
    assert len(df_m) == 5, f"Kỳ vọng 5 codec nhưng nhận {len(df_m)}"
    assert set(df_m["codec"]) == set(codecs)
    assert df_m["is_valid"].all() == True
    assert (df_m["n_bonafide"] > 0).all()
    assert (df_m["n_spoof"] > 0).all()

    df_d = pd.read_csv(deltas_path)
    assert len(df_d) == 4, f"Kỳ vọng 4 proxy codec nhưng nhận {len(df_d)}"
    assert set(df_d["codec"]) == {"aac_zalo_76k", "opus_zalo_24k", "g711_alaw", "amr_nb"}
    assert (df_d["n_paired"] == 20).all()
