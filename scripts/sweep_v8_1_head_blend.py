#!/usr/bin/env python3
"""Sweep clean backend interpolation between run2_phase2 and calibrated p2_headonly."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch

from scripts.build_v8_hybrid_checkpoint import graft_state_dict
from scripts.eval_v8_1_benchmark import (
    _bundle_all_paths,
    collect_4979_paths,
    infer_window_scores_multi_ckpt,
    summarize_4979_from_cache,
)
from scripts.graft_v8_1 import select_best_graft_candidate


def blend_state_dicts(sd_a: dict[str, torch.Tensor], sd_b: dict[str, torch.Tensor], alpha: float) -> dict[str, torch.Tensor]:
    out = {}
    for k, va in sd_a.items():
        if k not in sd_b:
            out[k] = va.clone()
            continue
        vb = sd_b[k]
        if not va.is_floating_point():
            out[k] = vb.clone()
        else:
            out[k] = (1.0 - alpha) * va + alpha * vb
    return out


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    p1_ckpt = _ROOT / "out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase1.pt"
    p2_ckpt = _ROOT / "out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase2.pt"
    head_ckpt = _ROOT / "out/zalo_b_zalo_v8_1_with_spk1/checkpoint_stage3_p2_headonly.pt"

    ck_p1 = torch.load(p1_ckpt, map_location="cpu")
    ck_p2 = torch.load(p2_ckpt, map_location="cpu")
    ck_hd = torch.load(head_ckpt, map_location="cpu")
    model_kwargs = ck_p2.get("model_kwargs", ck_hd.get("model_kwargs", {}))

    sd_p1, sd_p2, sd_hd = ck_p1["model"], ck_p2["model"], ck_hd["model"]

    sds: dict[str, dict[str, torch.Tensor]] = {}
    specs: dict[str, Any] = {}
    for alpha in (0.65, 0.75, 0.80, 0.85, 0.90, 1.00):
        name = f"head_blend_a{alpha:.2f}"
        sd = sd_hd if alpha == 1.0 else blend_state_dicts(sd_p2, sd_hd, alpha)
        sds[name] = sd
        specs[name] = {"state_dict": sd, "model_kwargs": model_kwargs}

    graft_name = "graft_p1_hd_s4_0.15_0.90"
    sd_g = graft_state_dict(sd_p1, sd_hd, split_layer=4, low_alpha=0.15, high_alpha=0.90)
    sds[graft_name] = sd_g
    specs[graft_name] = {"state_dict": sd_g, "model_kwargs": model_kwargs}

    bundle = collect_4979_paths()
    caches = infer_window_scores_multi_ckpt(specs, _bundle_all_paths(bundle), device=device, desc="HeadBlend")

    eval_results: dict[str, dict[str, Any]] = {}
    for name in specs:
        eval_results[name] = summarize_4979_from_cache(
            caches[name],
            bundle,
            name,
            ck_meta={"phase": "v8_1_blend", "epoch": 1, "dev_eer": None},
        )

    best_name, _ = select_best_graft_candidate(eval_results, pooling_mode="asymmetric_veto")
    out_best = _ROOT / "out/zalo_b_zalo_v8_1_with_spk1/best_v8_1_candidate.pt"
    torch.save(
        {
            "model": sds[best_name],
            "branch": "B_zalo_v8_1_best",
            "candidate_name": best_name,
            "phase": 3,
            "epoch": 1,
            "model_kwargs": model_kwargs,
        },
        out_best,
    )

    out_json = _ROOT / "benchmarks/v8_1_head_blend_sweep.json"
    out_json.write_text(
        json.dumps({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "best": best_name, "candidates": eval_results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== HEAD BLEND SWEEP SUMMARY ===")
    for name, res in eval_results.items():
        print(f"\n[{name}]")
        for mode in ("max", "mean", "asymmetric_veto"):
            m = res["modes"][mode]
            g1 = m["gate1_spk0001"]
            g2 = m["gate2_acceptance_5spk"]
            g3 = m["gate3_unseen_vieneu"]
            g4 = m["gate4_omnivoice_reversal"]
            bp = m["dev_bona_bpcer_2000"]
            f5 = m["seen_f5_dev_960"]
            om = m["seen_omni_v8_1_955"]
            print(
                f"  {mode:<15} | G1={g1['n_pass']:2d}/15({g1['pass_rate_pct']:5.1f}%) "
                f"| G2={g2['total_bona']:2d}/84({g2['overall_pass_rate_pct']:5.1f}%) "
                f"| G3_VN={g3['eer_pct']:5.2f}%(blk={g3['block_rate_pct']:5.1f}%) "
                f"| G4={g4['n_reversed']:3d}/195({g4['reversal_rate_pct']:5.1f}%) "
                f"| BPCER={bp['bpcer_pct']:5.2f}% "
                f"| F5={f5['eer_pct']:4.2f}%({f5['block_rate_pct']:5.1f}%) "
                f"| Omni={om['eer_pct']:4.2f}%({om['block_rate_pct']:5.1f}%)"
            )
    print(f"\nWinner: {best_name} -> {out_best}", flush=True)


if __name__ == "__main__":
    main()
