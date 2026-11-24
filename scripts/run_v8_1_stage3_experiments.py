#!/usr/bin/env python3
"""Run fast V8.1 Stage 3 calibration / partial-freeze experiments and evaluate against V7 and V8.0."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import pandas as pd
import torch
from torch.utils.data import DataLoader

from scripts.build_v8_hybrid_checkpoint import (
    build_balanced_ft_manifest,
    freeze_lower_ssl,
    train_stage3_partial_ft,
)
from scripts.eval_ssl_aasist import load_model
from scripts.eval_v8_1_benchmark import (
    _bundle_all_paths,
    collect_4979_paths,
    infer_window_scores_multi_ckpt,
    summarize_4979_from_cache,
)
from src.training.dataset import ViTrueVoiceDataset
from src.training.losses import AMSoftmaxLoss, loss_weights_from_counts


def train_headonly_balanced(
    init_ckpt_path: str,
    manifest_csv: str,
    out_ckpt_path: str,
    lr_backend: float = 2e-5,
    am_m: float = 0.20,
    batch_size: int = 8,
    accum_steps: int = 2,
    device: str = "cuda",
) -> Path:
    """1-epoch frozen-SSL backend calibration on balanced manifest."""
    model, _ = load_model(init_ckpt_path, device=device)
    model.freeze_ssl()

    df_tr = pd.read_csv(_ROOT / manifest_csv)
    n_sp = int((df_tr["label"] == "spoof").sum())
    n_bo = int((df_tr["label"] == "bonafide").sum())
    class_w = loss_weights_from_counts(n_sp, n_bo, clamp_range=(0.35, 0.65))
    weights_t = torch.tensor(class_w, dtype=torch.float32, device=device)

    criterion = AMSoftmaxLoss(
        in_features=model.out.in_features,
        num_classes=2,
        s=30.0,
        m=am_m,
        weight=weights_t,
    ).to(device)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=lr_backend, betas=(0.9, 0.98), weight_decay=1e-4)

    dataset = ViTrueVoiceDataset(df_tr, audio_root=".", mode="augmented", train=True)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    use_amp = (device == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    model.train()
    total_loss, n_samples = 0.0, 0
    optimizer.zero_grad(set_to_none=True)
    nb = len(loader)
    t0 = time.time()

    for i, batch in enumerate(loader, 1):
        x = batch["wave"].to(device)
        y = batch["label"].to(device)
        with torch.autocast(device_type=device, enabled=use_amp):
            _, emb = model(x, return_embedding=True)
            loss = criterion(emb.float(), y, weight_matrix=model.out.weight)
        scaler.scale(loss / accum_steps).backward()
        total_loss += loss.item() * len(y)
        n_samples += len(y)
        if i % accum_steps == 0 or i == nb:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
        if i % 200 == 0 or i == nb:
            print(f"   [HeadOnly Ep 1] Batch {i}/{nb} | Loss: {total_loss/n_samples:.4f} | {time.time()-t0:.1f}s", flush=True)

    out_p = _ROOT / out_ckpt_path
    out_p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model.state_dict(),
        "branch": "B_zalo_v8_1_headonly_cal",
        "phase": 3,
        "epoch": 1,
        "train_loss": total_loss / n_samples,
    }
    if hasattr(model, "model_kwargs"):
        payload["model_kwargs"] = model.model_kwargs
    torch.save(payload, out_p)
    print(f"Saved head-only calibrated checkpoint -> {out_p}", flush=True)
    return out_p


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    manifest_csv = "data/manifests_zalo/train_v8_balanced_ft.csv"
    build_balanced_ft_manifest(
        input_csv="data/manifests_zalo/train_v8_f5_omni_with_spk1.csv",
        output_csv=manifest_csv,
        random_seed=42,
    )

    out_dir = "out/zalo_b_zalo_v8_1_with_spk1"
    # 1. Partial-freeze Stage 3 from run2_phase2
    p2_ckpt = f"{out_dir}/checkpoint_phase2.pt"
    ckpt_p2_partial = train_stage3_partial_ft(
        init_ckpt_path=p2_ckpt,
        manifest_csv=manifest_csv,
        out_dir=out_dir,
        epochs=1,
        batch_size=8,
        accum_steps=2,
        lr_ssl=5e-7,
        lr_backend=5e-6,
        split_layer=8,
        device=device,
    )
    p2_partial_path = Path(out_dir) / "checkpoint_stage3_p2_partial.pt"
    p2_partial_path.write_bytes(Path(ckpt_p2_partial).read_bytes())

    # 2. Head-only frozen-SSL calibration from run2_phase2
    ckpt_p2_head = train_headonly_balanced(
        init_ckpt_path=p2_ckpt,
        manifest_csv=manifest_csv,
        out_ckpt_path=f"{out_dir}/checkpoint_stage3_p2_headonly.pt",
        lr_backend=2e-5,
        am_m=0.20,
        device=device,
    )

    # 3. Partial-freeze Stage 3 from run1_phase2
    r1_ckpt = "out/zalo_b_zalo_v8_1_no_spk1/checkpoint_phase2.pt"
    ckpt_r1_partial = train_stage3_partial_ft(
        init_ckpt_path=r1_ckpt,
        manifest_csv=manifest_csv,
        out_dir=out_dir,
        epochs=1,
        batch_size=8,
        accum_steps=2,
        lr_ssl=5e-7,
        lr_backend=5e-6,
        split_layer=8,
        device=device,
    )
    r1_partial_path = Path(out_dir) / "checkpoint_stage3_r1_partial.pt"
    r1_partial_path.write_bytes(Path(ckpt_r1_partial).read_bytes())

    # Evaluate V7 Best, V8.0 Legacy, and all 3 Stage 3 candidates in 1 decode pass!
    specs = {
        "v7_best": "out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt",
        "v8_0_legacy": "out/zalo_b_zalo_v8_inverted/checkpoint_v8_0_legacy.pt",
        "v8_1_p2_partial": str(p2_partial_path),
        "v8_1_p2_headonly": str(ckpt_p2_head),
        "v8_1_r1_partial": str(r1_partial_path),
    }

    bundle = collect_4979_paths()
    caches = infer_window_scores_multi_ckpt(specs, _bundle_all_paths(bundle), device=device, desc="Stage3VsBaselines")

    results = {}
    for name, path in specs.items():
        ck = torch.load(_ROOT / path, map_location="cpu")
        meta = {"phase": ck.get("phase"), "epoch": ck.get("epoch"), "dev_eer": ck.get("dev_eer")}
        results[name] = summarize_4979_from_cache(caches[name], bundle, path, ck_meta=meta)

    out_json = _ROOT / "benchmarks/v8_1_stage3_and_baselines.json"
    out_json.write_text(json.dumps({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "checkpoints": results}, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== STAGE 3 VS BASELINES SUMMARY ===")
    for name, res in results.items():
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


if __name__ == "__main__":
    main()
