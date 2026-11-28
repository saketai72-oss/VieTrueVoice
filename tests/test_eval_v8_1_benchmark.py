from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import torch

from scripts.build_v8_1_reports import build_all_reports
from scripts.eval_v8_1_benchmark import (
    _binary_metrics,
    collect_4979_paths,
    evaluate_4979_and_4gates,
    summarize_test_indomain_from_cache,
)
from scripts.graft_v8_1 import select_best_graft_candidate
from scripts.run_v8_1_phase_train import main as phase_train_main

_HAS_LOCAL_SPK = Path("data/raw/SPK_0001").exists()


def test_binary_metrics_basic():
    bona = np.array([10.0, 12.0, 8.0, 5.0])
    spoof = np.array([-10.0, -5.0, -8.0, -2.0])
    res = _binary_metrics(bona, spoof)
    assert res["eer_pct"] == pytest.approx(0.0)
    assert res["block_rate_pct"] == pytest.approx(100.0)
    assert res["total_bona"] == 4
    assert res["total_spoof"] == 4


@pytest.mark.skipif(not _HAS_LOCAL_SPK, reason="Local SPK audio assets not present in CI")
def test_collect_4979_paths_counts():
    bundle = collect_4979_paths()
    assert len(bundle["spk1_paths"]) == 15
    assert len(bundle["acc_items"]) == 84
    assert len(bundle["bona_2000_df"]) == 2000
    assert len(bundle["f5_dev_df"]) == 960
    assert len(bundle["omni_v8_0_df"]) == 965
    assert len(bundle["omni_v8_1_df"]) == 955
    assert len(bundle["vieneu_df"]) == 955
    assert len(bundle["omni_missed_df"]) == 195
    assert (
        len(bundle["spk1_paths"])
        + len(bundle["acc_items"])
        + len(bundle["bona_2000_df"])
        + len(bundle["f5_dev_df"])
        + len(bundle["omni_v8_0_df"])
        + len(bundle["vieneu_df"])
    ) == 4979
    assert (
        len(bundle["spk1_paths"])
        + len(bundle["acc_items"])
        + len(bundle["bona_2000_df"])
        + len(bundle["f5_dev_df"])
        + len(bundle["omni_v8_1_df"])
        + len(bundle["vieneu_df"])
    ) == 4969


def test_evaluate_4979_and_4gates_mocked_ci_safe(tmp_path):
    """CI-safe mocked test using synthetic bundle paths without local audio files."""
    bundle = {
        "spk1_paths": [f"data/raw/SPK_0001/spk1_{i:02d}.wav" for i in range(15)],
        "acc_items": [
            (spk, f"data/raw/{spk}/{spk}_01.wav")
            for spk in ("SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007")
            for _ in range(2)
        ],
        "bona_2000_df": pd.DataFrame({"audio_path": [f"bona_{i}.wav" for i in range(10)]}),
        "f5_dev_df": pd.DataFrame({"audio_path": [f"f5_{i}.wav" for i in range(5)]}),
        "omni_v8_0_df": pd.DataFrame({"audio_path": [f"omni0_{i}.wav" for i in range(5)]}),
        "omni_v8_1_df": pd.DataFrame({"audio_path": [f"omni1_{i}.wav" for i in range(5)]}),
        "vieneu_df": pd.DataFrame({"audio_path": [f"vn_{i}.wav" for i in range(5)]}),
        "omni_missed_df": pd.DataFrame({
            "utt_id": ["VIVOSDEV02_omnivoice_prompt_000"] + [f"m_{i}" for i in range(4)],
            "audio_path": [f"missed_{i}.wav" for i in range(5)],
            "score": [15.0] * 5,
        }),
    }
    fake_cache = {}
    for p in bundle["spk1_paths"]:
        fake_cache[p] = [12.0, 15.0]
    for _, p in bundle["acc_items"]:
        fake_cache[p] = [20.0, 22.0]
    for p in bundle["bona_2000_df"]["audio_path"]:
        fake_cache[p] = [18.0, 19.0]
    for df_sp in (bundle["f5_dev_df"], bundle["omni_v8_0_df"], bundle["omni_v8_1_df"], bundle["vieneu_df"], bundle["omni_missed_df"]):
        for p in df_sp["audio_path"]:
            fake_cache[p] = [-25.0, -30.0]

    ckpt_dummy = tmp_path / "best_model.pt"
    ckpt_dummy.write_bytes(b"stub")

    with (
        patch("scripts.eval_v8_1_benchmark.load_model", return_value=(object(), {"phase": 2, "epoch": 1, "dev_eer": 0.02})),
        patch("scripts.eval_v8_1_benchmark.infer_window_scores_batched", return_value=fake_cache),
    ):
        res = evaluate_4979_and_4gates(ckpt_dummy, bundle, device="cpu")

    assert res["clip_counts"]["set_4979"] == 4979
    assert res["clip_counts"]["set_4969_v8_1_sym"] == 4969
    for mode in ("max", "mean", "asymmetric_veto"):
        m = res["modes"][mode]
        assert m["gate1_spk0001"]["n_pass"] == 15
        assert m["gate2_acceptance_5spk"]["total_bona"] == 10
        assert m["gate3_unseen_vieneu"]["eer_pct"] == pytest.approx(0.0)
        assert m["gate4_omnivoice_reversal"]["n_reversed"] == 5
        assert "VIVOSDEV02_omnivoice_prompt_000" in m["gate4_omnivoice_reversal"]["vivosdev02_prompt0_details"]
        assert m["dev_bona_bpcer_2000"]["bpcer_pct"] == pytest.approx(0.0)


def test_run_v8_1_phase_train_preserves_phase1_and_phase2(tmp_path, monkeypatch):
    out_dir = tmp_path / "run_out"
    calls = []

    def fake_run_phase(**kwargs):
        calls.append((kwargs["phase1_epochs"], kwargs["phase2_epochs"], str(kwargs["out_dir"])))
        d = Path(kwargs["out_dir"])
        d.mkdir(parents=True, exist_ok=True)
        if kwargs["phase1_epochs"] > 0:
            torch.save({"model": {"w": torch.tensor([1.0])}, "phase": 1, "epoch": 1, "dev_eer": 0.04}, d / "best_model.pt")
            (d / "history.json").write_text('[{"epoch": 1, "phase": 1, "dev_eer": 0.04}]', encoding="utf-8")
        else:
            torch.save({"model": {"w": torch.tensor([2.0])}, "phase": 2, "epoch": 1, "dev_eer": 0.06}, d / "best_model.pt")
            (d / "history.json").write_text('[{"epoch": 1, "phase": 2, "dev_eer": 0.06}]', encoding="utf-8")
        return 0.1

    monkeypatch.setattr("scripts.run_v8_1_phase_train._run_train_phase", fake_run_phase)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_v8_1_phase_train.py",
            "--init-ckpt", "init.pt",
            "--train-manifest", "tr.csv",
            "--dev-manifest", "dv.csv",
            "--out-dir", str(out_dir),
            "--phase1-epochs", "1",
            "--phase2-epochs", "2",
        ],
    )
    phase_train_main()

    assert len(calls) == 2
    assert (out_dir / "checkpoint_phase1.pt").exists()
    assert (out_dir / "checkpoint_phase2.pt").exists()
    assert (out_dir / "best_model.pt").exists()
    # Best model should pick phase1 since 0.04 < 0.06, while checkpoint_phase2.pt is preserved!
    best = torch.load(out_dir / "best_model.pt", map_location="cpu")
    p2 = torch.load(out_dir / "checkpoint_phase2.pt", map_location="cpu")
    assert best["phase"] == 1
    assert p2["phase"] == 2


def test_summarize_test_indomain_from_cache_mocked():
    rows = []
    cache = {}
    for c in ("clean_16khz", "aac_zalo_76k", "opus_zalo_24k", "g711_alaw", "amr_nb"):
        p_b = f"bona_{c}.wav"
        p_f5 = f"f5_{c}.wav"
        p_om = f"om_{c}.wav"
        rows.append({"audio_path": p_b, "label": "bonafide", "role": "eval", "tts_generator": "none", "codec": c})
        rows.append({"audio_path": p_f5, "label": "spoof", "role": "eval", "tts_generator": "F5-TTS-Vietnamese", "codec": c})
        rows.append({"audio_path": p_om, "label": "spoof", "role": "eval", "tts_generator": "OmniVoice", "codec": c})
        cache[p_b] = [15.0, 12.0]
        cache[p_f5] = [-20.0, -25.0]
        cache[p_om] = [-18.0, -22.0]

    df = pd.DataFrame(rows)
    res = summarize_test_indomain_from_cache(cache, df, ckpt_label="dummy.pt")
    assert res["total_rows"] == 15
    for mode in ("max", "mean", "asymmetric_veto"):
        ov = res["modes"][mode]["full_15980"]["overall"]
        assert ov["eer_pct"] == pytest.approx(0.0)
        assert ov["bona_bpcer_pct"] == pytest.approx(0.0)
        assert len(res["modes"][mode]["full_15980"]["by_codec"]) == 5


def test_select_best_graft_candidate():
    def _mk(g1, g2, g3, g4, bp=4.0):
        return {
            "modes": {
                "asymmetric_veto": {
                    "gate1_spk0001": {"pass_rate_pct": g1},
                    "gate2_acceptance_5spk": {"overall_pass_rate_pct": g2},
                    "gate3_unseen_vieneu": {"eer_pct": g3},
                    "gate4_omnivoice_reversal": {"reversal_rate_pct": g4},
                    "dev_bona_bpcer_2000": {"bpcer_pct": bp},
                }
            }
        }

    candidates = {
        "fails_g2": _mk(90.0, 92.0, 10.0, 90.0),
        "ok_tier1": _mk(80.0, 95.0, 13.0, 80.0),
        "best_tier2": _mk(86.7, 98.8, 11.4, 72.0),
    }
    best_name, _ = select_best_graft_candidate(candidates, pooling_mode="asymmetric_veto")
    assert best_name == "best_tier2"


def test_build_all_reports_idempotent_with_legacy_snapshot(tmp_path):
    import json

    bench = tmp_path / "benchmarks"
    bench.mkdir(parents=True)
    r1_dir = tmp_path / "out" / "zalo_b_zalo_v8_1_no_spk1"
    r2_dir = tmp_path / "out" / "zalo_b_zalo_v8_1_with_spk1"
    r1_dir.mkdir(parents=True)
    r2_dir.mkdir(parents=True)

    dummy_mode = {
        "gate1_spk0001": {"pass_rate_pct": 93.3},
        "gate2_acceptance_5spk": {"overall_pass_rate_pct": 95.2},
        "gate3_unseen_vieneu": {"eer_pct": 12.05},
        "gate4_omnivoice_reversal": {"reversal_rate_pct": 72.8},
        "dev_bona_bpcer_2000": {"bpcer_pct": 6.0},
        "seen_f5_dev_960": {"eer_pct": 5.63},
        "seen_omni_v8_0_965": {"eer_pct": 7.98},
        "seen_omni_v8_1_955": {"eer_pct": 8.06},
        "seen_v8_1_pooled_1915": {"eer_pct": 6.53},
    }
    modes = {m: dummy_mode for m in ("max", "mean", "asymmetric_veto")}
    entry = {"modes": modes}

    (bench / "v8_inverted_evaluation_report.json").write_text(
        json.dumps({"model_version": "VieTrueVoice B_zalo V8 Inverted Dual-Seen", "winning_checkpoint": "legacy.pt"}),
        encoding="utf-8",
    )
    (bench / "v8_1_run1_eval.json").write_text(json.dumps({"checkpoints": {"run1_phase1": entry, "run1_phase2": entry}}), encoding="utf-8")
    (bench / "v8_1_graft_grid.json").write_text(
        json.dumps({"best_graft_name": "g1", "best_combo": [4, 0.25, 0.85], "candidates": {"run2_phase1": entry, "run2_phase2": entry, "g1": entry}}),
        encoding="utf-8",
    )
    (bench / "v8_1_stage3_and_baselines.json").write_text(
        json.dumps({"checkpoints": {"v7_best": entry, "v8_0_legacy": entry, "v8_1_p2_partial": entry, "v8_1_r1_partial": entry, "v8_1_p2_headonly": entry}}),
        encoding="utf-8",
    )
    (bench / "v8_1_head_blend_sweep.json").write_text(
        json.dumps({"best": "head_blend_a0.75", "candidates": {"head_blend_a0.75": entry}}),
        encoding="utf-8",
    )
    (bench / "v8_1_test_indomain_15980.json").write_text(json.dumps({"checkpoints": {"v7_best": entry, "v8_0_legacy": entry, "v8_1_best": entry}}), encoding="utf-8")
    sum_payload = {"phase1_dev_eer": 0.08, "phase2_dev_eer": 0.06, "timing_min": {"phase1_min": 30.0, "phase2_min": 130.0}}
    (r1_dir / "run_summary.json").write_text(json.dumps(sum_payload), encoding="utf-8")
    (r2_dir / "run_summary.json").write_text(json.dumps(sum_payload), encoding="utf-8")

    inv_p, pool_p, vs_p = build_all_reports(tmp_path)
    inv_p, pool_p, vs_p = build_all_reports(tmp_path)  # idempotency pass
    inv = json.loads(inv_p.read_text(encoding="utf-8"))
    pool = json.loads(pool_p.read_text(encoding="utf-8"))
    vs = json.loads(vs_p.read_text(encoding="utf-8"))
    assert inv["v8_0_legacy_report"]["winning_checkpoint"] == "legacy.pt"
    assert pool["winning_model"] == "head_blend_a0.75"
    assert vs["unseen_vieneu_955"]["v8_1_best"]["asymmetric_veto"]["eer_pct"] == pytest.approx(12.05)
