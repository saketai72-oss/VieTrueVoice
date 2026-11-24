#!/usr/bin/env python3
"""Two-phase wrapper around scripts/train.py that preserves both Phase 1 and Phase 2 checkpoints."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import torch


def _run_train_phase(
    *,
    init_ckpt: str,
    train_manifest: str,
    dev_manifest: str,
    out_dir: Path,
    phase1_epochs: int,
    phase2_epochs: int,
    batch_size: int,
    accum_steps: int,
    num_workers: int,
    am_s: float,
    am_m: float,
    patience: int,
    device: str,
) -> float:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-u",
        "scripts/train.py",
        "--branch", "B_zalo",
        "--init-ckpt", init_ckpt,
        "--train-manifest", train_manifest,
        "--dev-manifest", dev_manifest,
        "--audio-root", ".",
        "--out-dir", str(out_dir),
        "--batch-size", str(batch_size),
        "--accum-steps", str(accum_steps),
        "--loss", "am_softmax",
        "--am-s", str(am_s),
        "--am-m", str(am_m),
        "--phase1-epochs", str(phase1_epochs),
        "--phase2-epochs", str(phase2_epochs),
        "--patience", str(patience),
        "--num-workers", str(num_workers),
        "--device", device,
    ]
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"

    print("\n" + "=" * 80, flush=True)
    print(f"RUN: {' '.join(cmd)}", flush=True)
    print("=" * 80, flush=True)

    t0 = time.time()
    res = subprocess.run(cmd, env=env, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Training failed (exit {res.returncode}) in {out_dir}")
    elapsed_min = (time.time() - t0) / 60.0
    print(f"Finished in {elapsed_min:.2f} min -> {out_dir}", flush=True)
    return elapsed_min


def main() -> None:
    p = argparse.ArgumentParser(description="Run Phase 1 and Phase 2 training while preserving both checkpoints")
    p.add_argument("--init-ckpt", required=True)
    p.add_argument("--train-manifest", required=True)
    p.add_argument("--dev-manifest", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--phase1-epochs", type=int, default=1)
    p.add_argument("--phase2-epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--accum-steps", type=int, default=2)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--am-s", type=float, default=30.0)
    p.add_argument("--am-m", type=float, default=0.20)
    p.add_argument("--patience", type=int, default=3)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    timing: dict[str, float] = {}

    ckpt_p1 = out_dir / "checkpoint_phase1.pt"
    ckpt_p2 = out_dir / "checkpoint_phase2.pt"
    best_ckpt = out_dir / "best_model.pt"

    next_init = args.init_ckpt
    p1_eer = float("inf")
    p2_eer = float("inf")

    if args.phase1_epochs > 0:
        timing["phase1_min"] = _run_train_phase(
            init_ckpt=args.init_ckpt,
            train_manifest=args.train_manifest,
            dev_manifest=args.dev_manifest,
            out_dir=out_dir,
            phase1_epochs=args.phase1_epochs,
            phase2_epochs=0,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            num_workers=args.num_workers,
            am_s=args.am_s,
            am_m=args.am_m,
            patience=args.patience,
            device=args.device,
        )
        if not best_ckpt.exists():
            raise FileNotFoundError(f"Missing Phase 1 checkpoint at {best_ckpt}")
        shutil.copy2(best_ckpt, ckpt_p1)
        p1_meta = torch.load(ckpt_p1, map_location="cpu")
        p1_eer = float(p1_meta.get("dev_eer", float("inf")))
        print(f"Saved Phase 1 checkpoint: {ckpt_p1} (dev_eer={p1_eer:.6f})", flush=True)
        h1_path = out_dir / "history.json"
        if h1_path.exists():
            h1 = json.loads(h1_path.read_text(encoding="utf-8"))
            (out_dir / "history_phase1.json").write_text(json.dumps(h1, indent=1), encoding="utf-8")
            history.extend(h1)
        next_init = str(ckpt_p1)

    if args.phase2_epochs > 0:
        p2_dir = out_dir / "phase2_tmp"
        timing["phase2_min"] = _run_train_phase(
            init_ckpt=next_init,
            train_manifest=args.train_manifest,
            dev_manifest=args.dev_manifest,
            out_dir=p2_dir,
            phase1_epochs=0,
            phase2_epochs=args.phase2_epochs,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            num_workers=args.num_workers,
            am_s=args.am_s,
            am_m=args.am_m,
            patience=args.patience,
            device=args.device,
        )
        p2_best = p2_dir / "best_model.pt"
        if not p2_best.exists():
            raise FileNotFoundError(f"Missing Phase 2 checkpoint at {p2_best}")
        shutil.copy2(p2_best, ckpt_p2)
        p2_meta = torch.load(ckpt_p2, map_location="cpu")
        p2_eer = float(p2_meta.get("dev_eer", float("inf")))
        print(f"Saved Phase 2 checkpoint: {ckpt_p2} (dev_eer={p2_eer:.6f})", flush=True)
        h2_path = p2_dir / "history.json"
        if h2_path.exists():
            h2 = json.loads(h2_path.read_text(encoding="utf-8"))
            (out_dir / "history_phase2.json").write_text(json.dumps(h2, indent=1), encoding="utf-8")
            offset = len(history)
            for row in h2:
                row_copy = dict(row)
                row_copy["epoch"] = offset + int(row_copy["epoch"])
                history.append(row_copy)

    if ckpt_p2.exists() and (not ckpt_p1.exists() or p2_eer <= p1_eer):
        shutil.copy2(ckpt_p2, best_ckpt)
        winner_phase = "phase2"
    elif ckpt_p1.exists():
        shutil.copy2(ckpt_p1, best_ckpt)
        winner_phase = "phase1"
    else:
        raise RuntimeError("No checkpoint produced")

    (out_dir / "history.json").write_text(json.dumps(history, indent=1), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "phase1_dev_eer": None if p1_eer == float("inf") else p1_eer,
                "phase2_dev_eer": None if p2_eer == float("inf") else p2_eer,
                "best_model_source": winner_phase,
                "timing_min": timing,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"DONE {out_dir}: winner={winner_phase} | p1_eer={p1_eer:.6f} | p2_eer={p2_eer:.6f}", flush=True)


if __name__ == "__main__":
    main()
