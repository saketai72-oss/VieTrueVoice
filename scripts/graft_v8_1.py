#!/usr/bin/env python3
"""Layer-Wise Grafting grid search and 4-Gate x 3-Pooling evaluation for V8.1."""

from __future__ import annotations

import argparse
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

DEFAULT_GRID: list[tuple[int, float, float]] = [
    (4, 0.00, 1.00),
    (4, 0.10, 0.90),
    (4, 0.15, 0.90),
    (4, 0.20, 0.85),
    (4, 0.25, 0.85),
    (6, 0.00, 1.00),
    (6, 0.10, 0.90),
    (6, 0.15, 0.90),
    (6, 0.15, 0.85),
    (6, 0.25, 0.85),
]


def score_candidate(entry: dict[str, Any], pooling_mode: str = "asymmetric_veto") -> tuple:
    """Rank grafting candidates: Gate1>=80%, Gate2>=94% (prefer >=98%), Gate3<=15% (prefer <=12%), max Gate4."""
    m = entry["modes"][pooling_mode]
    g1 = m["gate1_spk0001"]["pass_rate_pct"]
    g2 = m["gate2_acceptance_5spk"]["overall_pass_rate_pct"]
    g3 = m["gate3_unseen_vieneu"]["eer_pct"]
    g4 = m["gate4_omnivoice_reversal"]["reversal_rate_pct"]
    bp = m["dev_bona_bpcer_2000"]["bpcer_pct"]

    passes_hard = (g1 >= 80.0) and (g2 >= 94.0) and (g3 <= 15.0)
    prefers_tier = (g2 >= 98.0) and (g3 <= 12.0)
    composite = g2 + (0.8 * g4) + (2.0 * g1) - (1.5 * g3) - (0.5 * bp)
    return (int(passes_hard), int(prefers_tier), round(g4, 4), round(composite, 4))


def select_best_graft_candidate(
    results: dict[str, dict[str, Any]],
    pooling_mode: str = "asymmetric_veto",
) -> tuple[str, dict[str, Any]]:
    best_name = max(results.keys(), key=lambda k: score_candidate(results[k], pooling_mode=pooling_mode))
    return best_name, results[best_name]


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid search Layer-Wise Grafting for V8.1 Phase 1 + Phase 2")
    parser.add_argument("--phase1-ckpt", default="out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase1.pt")
    parser.add_argument("--phase2-ckpt", default="out/zalo_b_zalo_v8_1_with_spk1/checkpoint_phase2.pt")
    parser.add_argument("--out-ckpt", default="out/zalo_b_zalo_v8_1_with_spk1/checkpoint_grafted.pt")
    parser.add_argument("--out-json", default="benchmarks/v8_1_graft_grid.json")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    ck_a = torch.load(_ROOT / args.phase1_ckpt, map_location="cpu")
    ck_b = torch.load(_ROOT / args.phase2_ckpt, map_location="cpu")
    sd_a = ck_a["model"]
    sd_b = ck_b["model"]
    model_kwargs = ck_a.get("model_kwargs", ck_b.get("model_kwargs", {}))

    specs: dict[str, Any] = {
        "run2_phase1": args.phase1_ckpt,
        "run2_phase2": args.phase2_ckpt,
    }
    combo_map: dict[str, tuple[int, float, float]] = {}
    grafted_sds: dict[str, dict[str, torch.Tensor]] = {}

    for split_l, low_a, high_a in DEFAULT_GRID:
        name = f"split_{split_l}_low_{low_a:.2f}_high_{high_a:.2f}"
        sd_g = graft_state_dict(sd_a, sd_b, split_layer=split_l, low_alpha=low_a, high_alpha=high_a)
        grafted_sds[name] = sd_g
        combo_map[name] = (split_l, low_a, high_a)
        specs[name] = {"state_dict": sd_g, "model_kwargs": model_kwargs}

    bundle = collect_4979_paths()
    caches = infer_window_scores_multi_ckpt(specs, _bundle_all_paths(bundle), device=args.device, desc="GraftGrid")

    eval_results: dict[str, dict[str, Any]] = {}
    for name in specs:
        meta = (
            {"phase": ck_a.get("phase"), "epoch": ck_a.get("epoch"), "dev_eer": ck_a.get("dev_eer")}
            if name == "run2_phase1"
            else {"phase": ck_b.get("phase"), "epoch": ck_b.get("epoch"), "dev_eer": ck_b.get("dev_eer")}
            if name == "run2_phase2"
            else {"phase": "grafted", "epoch": None, "dev_eer": None}
        )
        eval_results[name] = summarize_4979_from_cache(caches[name], bundle, name, ck_meta=meta)

    graft_only = {k: v for k, v in eval_results.items() if k in combo_map}
    best_name, best_res = select_best_graft_candidate(graft_only, pooling_mode="asymmetric_veto")
    best_combo = combo_map[best_name]

    out_ckpt_p = _ROOT / args.out_ckpt
    out_ckpt_p.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": grafted_sds[best_name],
            "branch": "B_zalo_v8_1_grafted",
            "combo": best_combo,
            "model_kwargs": model_kwargs,
        },
        out_ckpt_p,
    )

    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phase1_ckpt": args.phase1_ckpt,
        "phase2_ckpt": args.phase2_ckpt,
        "best_graft_name": best_name,
        "best_combo": best_combo,
        "best_out_ckpt": args.out_ckpt,
        "candidates": eval_results,
    }
    out_json_p = _ROOT / args.out_json
    out_json_p.parent.mkdir(parents=True, exist_ok=True)
    out_json_p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== GRAFTING GRID SUMMARY (asymmetric_veto) ===")
    for name, res in eval_results.items():
        m = res["modes"]["asymmetric_veto"]
        print(
            f"  {name:<26} | G1={m['gate1_spk0001']['n_pass']}/15 ({m['gate1_spk0001']['pass_rate_pct']:5.1f}%) "
            f"| G2={m['gate2_acceptance_5spk']['total_bona']}/84 ({m['gate2_acceptance_5spk']['overall_pass_rate_pct']:5.1f}%) "
            f"| G3_EER={m['gate3_unseen_vieneu']['eer_pct']:5.2f}% "
            f"| G4_Rev={m['gate4_omnivoice_reversal']['n_reversed']}/195 ({m['gate4_omnivoice_reversal']['reversal_rate_pct']:5.1f}%) "
            f"| DevBPCER={m['dev_bona_bpcer_2000']['bpcer_pct']:5.2f}%"
        )
    print(f"\nWinner: {best_name} {best_combo} -> {out_ckpt_p}")


if __name__ == "__main__":
    main()
