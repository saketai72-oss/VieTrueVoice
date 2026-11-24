"""Build canonical V8.1 evaluation, pooling ablation, and V7/V8.0/V8.1 comparison JSON reports."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"
OUT = ROOT / "out"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _extract_legacy_v8_0_report(inv_report_path: Path) -> dict[str, Any] | None:
    if not inv_report_path.exists():
        return None
    existing = _load_json(inv_report_path)
    if "v8_0_legacy_report" in existing and isinstance(existing["v8_0_legacy_report"], dict):
        return existing["v8_0_legacy_report"]
    if str(existing.get("model_version", "")).startswith("ViTrueVoice B_zalo V8 Inverted"):
        return existing
    return None


def _run_summary_for_inverted_entry(
    checkpoint: str,
    modes: dict[str, Any],
    summary_data: dict[str, Any] | None = None,
    phase_key: str = "phase2_dev_eer",
) -> dict[str, Any]:
    default_mode = modes["asymmetric_veto"]
    entry: dict[str, Any] = {
        "checkpoint": checkpoint,
        "default_inference_mode": "asymmetric_veto",
        "gate1_spk0001": default_mode["gate1_spk0001"],
        "gate2_acceptance_5spk": default_mode["gate2_acceptance_5spk"],
        "gate3_unseen_vieneu": default_mode["gate3_unseen_vieneu"],
        "gate4_omnivoice_reversal": default_mode["gate4_omnivoice_reversal"],
        "dev_bona_bpcer_2000": default_mode["dev_bona_bpcer_2000"],
        "seen_f5_dev_960": default_mode["seen_f5_dev_960"],
        "seen_omni_v8_0_965": default_mode["seen_omni_v8_0_965"],
        "seen_omni_v8_1_955": default_mode["seen_omni_v8_1_955"],
        "seen_v8_1_pooled_1915": default_mode["seen_v8_1_pooled_1915"],
        "modes": modes,
    }
    if summary_data:
        timing = summary_data.get("timing_min", {})
        entry["training_time_min"] = round(sum(float(v) for v in timing.values()), 2)
        entry["timing_breakdown_min"] = timing
        if phase_key in summary_data:
            entry["dev_eer_pct"] = round(float(summary_data[phase_key]) * 100.0, 4)
        entry["phase1_dev_eer_pct"] = round(float(summary_data.get("phase1_dev_eer", 0.0)) * 100.0, 4)
        entry["phase2_dev_eer_pct"] = round(float(summary_data.get("phase2_dev_eer", 0.0)) * 100.0, 4)
    return entry


def build_all_reports(root: Path = ROOT) -> tuple[Path, Path, Path]:
    bench = root / "benchmarks"
    out_dir = root / "out"

    run1 = _load_json(bench / "v8_1_run1_eval.json")
    graft = _load_json(bench / "v8_1_graft_grid.json")
    stage3 = _load_json(bench / "v8_1_stage3_and_baselines.json")
    sweep = _load_json(bench / "v8_1_head_blend_sweep.json")
    test15980 = _load_json(bench / "v8_1_test_indomain_15980.json")

    run1_sum = _load_json(out_dir / "zalo_b_zalo_v8_1_no_spk1" / "run_summary.json")
    run2_sum = _load_json(out_dir / "zalo_b_zalo_v8_1_with_spk1" / "run_summary.json")

    winning_ckpt_v8_1 = "out/zalo_b_zalo_v8_1_with_spk1/best_model.pt"
    promoted_prod_ckpt = "out/zalo_b_zalo_v8_inverted/best_model.pt"
    legacy_ckpt = "out/zalo_b_zalo_v8_inverted/checkpoint_v8_0_legacy.pt"
    winning_name = sweep.get("best", "head_blend_a0.75")

    inv_path = bench / "v8_inverted_evaluation_report.json"
    legacy_v8_0 = _extract_legacy_v8_0_report(inv_path)

    best_graft_name = graft["best_graft_name"]
    run1_p1_modes = run1["checkpoints"]["run1_phase1"]["modes"]
    run1_p2_modes = run1["checkpoints"]["run1_phase2"]["modes"]
    run2_p1_modes = graft["candidates"]["run2_phase1"]["modes"]
    run2_p2_modes = graft["candidates"]["run2_phase2"]["modes"]
    best_graft_modes = graft["candidates"][best_graft_name]["modes"]
    p2_partial_modes = stage3["checkpoints"]["v8_1_p2_partial"]["modes"]
    r1_partial_modes = stage3["checkpoints"]["v8_1_r1_partial"]["modes"]
    p2_headonly_modes = stage3["checkpoints"]["v8_1_p2_headonly"]["modes"]
    winner_modes = sweep["candidates"][winning_name]["modes"]

    ablation_summary = {
        "run1_phase1": run1_p1_modes,
        "run1_phase2": run1_p2_modes,
        "run2_phase1": run2_p1_modes,
        "run2_phase2": run2_p2_modes,
        "stage2_grafted": best_graft_modes,
        "stage3_p2_partial": p2_partial_modes,
        "stage3_r1_partial": r1_partial_modes,
        "stage3_p2_headonly": p2_headonly_modes,
        winning_name: winner_modes,
        "winning_model": winning_name,
        "winning_checkpoint": winning_ckpt_v8_1,
        "promoted_production_checkpoint": promoted_prod_ckpt,
    }

    inv_report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_version": "ViTrueVoice B_zalo V8.1 Inverted Dual-Seen (Full 6,445 OmniVoice)",
        "seen_tts": ["F5-TTS", "OmniVoice CFM (VoiceStudio)"],
        "unseen_tts": ["VieNeu-TTS v3 Turbo"],
        "winning_model": winning_name,
        "winning_checkpoint": winning_ckpt_v8_1,
        "promoted_production_checkpoint": promoted_prod_ckpt,
        "legacy_v8_0_checkpoint": legacy_ckpt,
        "training_config": {
            "init_checkpoint": "out/zalo_b_zalo_v5_local/best_model.pt",
            "train_no_spk1_rows": 54225,
            "train_with_spk1_rows": 54400,
            "dev_rows": 12405,
            "batch_size": 8,
            "accum_steps": 2,
            "effective_batch_size": 16,
            "num_workers": 0,
            "am_s": 30.0,
            "am_m": 0.20,
            "phase1_epochs": 1,
            "phase2_epochs": 2,
            "stage3_ft_rows": 5100,
            "head_blend_alpha": 0.75,
        },
        "run1_no_spk1": {
            **_run_summary_for_inverted_entry(
                "out/zalo_b_zalo_v8_1_no_spk1/best_model.pt",
                run1_p2_modes,
                summary_data=run1_sum,
                phase_key="phase2_dev_eer",
            ),
            "phase1": _run_summary_for_inverted_entry(
                "out/zalo_b_zalo_v8_1_no_spk1/checkpoint_phase1.pt",
                run1_p1_modes,
                summary_data=run1_sum,
                phase_key="phase1_dev_eer",
            ),
        },
        "run2_with_spk1": {
            **_run_summary_for_inverted_entry(
                "out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase2.pt",
                run2_p2_modes,
                summary_data=run2_sum,
                phase_key="phase2_dev_eer",
            ),
            "phase1": _run_summary_for_inverted_entry(
                "out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase1.pt",
                run2_p1_modes,
                summary_data=run2_sum,
                phase_key="phase1_dev_eer",
            ),
        },
        "hybrid_remediation": {
            "root_cause_note": (
                "V8.1 Run 2 initialized from V5 with 100 SPK_0001 spoof vs 75 bona and am_m=0.20 "
                "yielded <54% Gate 1 in both Run 2 Phase 1 and Phase 2, so Phase1+Phase2 grafting could "
                "not recover Gate 1 (<=33.3%). Run 2 Phase 2 still learned strong SSL OmniVoice/F5 "
                "separation (7.96% Dev Omni EER, 86.2% Gate 4 veto) with a negative classifier bias; "
                "1-epoch frozen-SSL backend calibration on 5,100 balanced rows plus 0.25*P2 + 0.75*HeadOnly "
                "weight interpolation resolved Gate 1 (93.3%) and Gate 2 (95.2% veto / 98.8% max / 100% ctrl4) "
                "while improving Seen Omni EER (8.06% dev, 7.95% on 15,980 test)."
            ),
            "stage2_best_graft_name": best_graft_name,
            "stage2_best_combo": graft["best_combo"],
            "winner": winning_name,
            "winning_checkpoint": winning_ckpt_v8_1,
            "promoted_production_checkpoint": promoted_prod_ckpt,
            "ablation_results": ablation_summary,
        },
        "v7_vs_v8_0_vs_v8_1_test_indomain_15980": test15980["checkpoints"],
    }
    if legacy_v8_0 is not None:
        inv_report["v8_0_legacy_report"] = legacy_v8_0

    pool_path = bench / "v8_pooling_ablation_report.json"
    pool_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_version": "ViTrueVoice B_zalo V8.1",
        "winning_model": winning_name,
        "winning_checkpoint": winning_ckpt_v8_1,
        "promoted_production_checkpoint": promoted_prod_ckpt,
        "legacy_v8_0_checkpoint": legacy_ckpt,
        "checkpoint_b_raw": run2_p2_modes,
        "stage2_grafted": best_graft_modes,
        "stage3_partial_ft": p2_headonly_modes,
        "v8_1_best_head_blend_a0_75": winner_modes,
        "run1_no_spk1_phase1": run1_p1_modes,
        "run1_no_spk1_phase2": run1_p2_modes,
        "run2_phase1": run2_p1_modes,
        "stage3_p2_partial": p2_partial_modes,
        "stage3_r1_partial": r1_partial_modes,
        "head_blend_sweep": {k: v["modes"] for k, v in sweep["candidates"].items()},
        "baselines": {
            "v7_best": stage3["checkpoints"]["v7_best"]["modes"],
            "v8_0_legacy": stage3["checkpoints"]["v8_0_legacy"]["modes"],
        },
    }

    vs_path = bench / "v8_1_vs_v7_benchmark.json"
    control_models = {
        "v7_best": {
            "checkpoint": "out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt",
            "modes": stage3["checkpoints"]["v7_best"]["modes"],
        },
        "v8_0_legacy": {
            "checkpoint": legacy_ckpt,
            "modes": stage3["checkpoints"]["v8_0_legacy"]["modes"],
        },
        "v8_1_best": {
            "checkpoint": winning_ckpt_v8_1,
            "promoted_checkpoint": promoted_prod_ckpt,
            "candidate_name": winning_name,
            "modes": winner_modes,
        },
    }
    unseen_vieneu = {
        model_key: {
            mode: control_models[model_key]["modes"][mode]["gate3_unseen_vieneu"]
            for mode in ("max", "mean", "asymmetric_veto")
        }
        for model_key in ("v7_best", "v8_0_legacy", "v8_1_best")
    }
    vs_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": (
            "Fair head-to-head comparison of V7 Best, V8.0 Legacy, and V8.1 Best across max, mean, "
            "and asymmetric_veto pooling on the 4,979/4,969 control benchmark, 15,980-clip "
            "test_indomain_v8_f5_omni.csv, and 955-clip unseen_vieneu_benchmark.csv."
        ),
        "datasets": {
            "control_4979_slices": {
                "gate1_spk0001_bona": 15,
                "gate2_5spk_bona": 84,
                "dev_bona_sample": 2000,
                "seen_f5_dev": 960,
                "seen_omni_v8_0_15spk": 965,
                "unseen_vieneu_benchmark": 955,
                "total_v8_0_frame": 4979,
                "seen_omni_v8_1_symmetric": 955,
                "total_v8_1_symmetric_frame": 4969,
                "gate4_omnivoice_reversal_subset": 195,
            },
            "test_indomain_v8_f5_omni": {
                "full_rows": 15980,
                "eval_only_rows": 15665,
            },
            "unseen_vieneu_benchmark": {
                "spoof_rows": 955,
                "bona_eval_rows": 2000,
            },
        },
        "control_4979": control_models,
        "test_indomain_15980": test15980["checkpoints"],
        "unseen_vieneu_955": unseen_vieneu,
    }

    _save_json(inv_path, inv_report)
    _save_json(pool_path, pool_report)
    _save_json(vs_path, vs_report)
    return inv_path, pool_path, vs_path


if __name__ == "__main__":
    inv, pool, vs = build_all_reports()
    print(f"Wrote {inv}, {pool}, {vs}")
