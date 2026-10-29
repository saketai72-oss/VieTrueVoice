"""Entry-point huấn luyện CLI cho ViTrueVoice — 3 nhánh A / B0 / B.

Dùng: python scripts/train.py --branch B --manifest-dir data/manifests
             --audio-root . --out-dir out/run_B --batch-size 16

Kaggle: bọc script này trong train_kaggle.ipynb (notebook riêng biệt).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from src.models.ssl_aasist import SSLAASIST
from src.training.augment import make_rawboost
from src.training.dataset import ViTrueVoiceDataset, check_unseen_excluded
from src.training.losses import loss_weights_from_counts
from src.training.trainer import TrainConfig, Trainer

# ─────────────────────────────────────────────
# Hằng số
# ─────────────────────────────────────────────
_VIENEU_PATTERN = "vieneu"
_TARGET_LEN = 64_000          # 4.0 s @ 16 kHz (STUBBORN_FACT)

# ─────────────────────────────────────────────
# Public API (được test trực tiếp)
# ─────────────────────────────────────────────

def build_branch_config(
    branch: str,
    out_dir: str,
) -> tuple[TrainConfig, str, Optional[Callable]]:
    """Trả về (TrainConfig, mode, transform) theo nhánh A / B0 / B.

    - A  : clean only, phase2 = 60 (×3 để cân bằng optimizer steps)
    - B0 : augmented, không RawBoost   (bóc tách đóng góp codec)
    - B  : augmented + RawBoost online (ViTrueVoice đầy đủ)
    """
    if branch == "A":
        cfg = TrainConfig(branch="A", phase1_epochs=4, phase2_epochs=60, out_dir=out_dir)
        return cfg, "clean", None
    if branch == "B0":
        cfg = TrainConfig(branch="B0", phase1_epochs=4, phase2_epochs=20, out_dir=out_dir)
        return cfg, "augmented", None
    if branch == "B":
        cfg = TrainConfig(branch="B", phase1_epochs=4, phase2_epochs=20, out_dir=out_dir)
        return cfg, "augmented", make_rawboost()
    raise ValueError(f"branch phải là A, B0 hoặc B — nhận được: {branch!r}")


def compute_weights(train_df: pd.DataFrame, branch: str) -> list[float]:
    """Tính w_c = N/(2·N_c) từ tập train thực tế theo nhánh.

    Nhánh A chỉ xét hàng clean_16khz (phản ánh đúng dữ liệu mà dataset thấy).
    """
    if branch == "A":
        df = train_df[train_df["codec"] == "clean_16khz"]
    else:
        df = train_df
    n_spoof  = int((df["label"] == "spoof").sum())
    n_bona   = int((df["label"] == "bonafide").sum())
    return loss_weights_from_counts(n_spoof, n_bona)


def validate_manifest(train_df: pd.DataFrame, split_name: str) -> None:
    """Báo lỗi nếu VieNeu lọt vào tập train/dev (vô hiệu hóa H2)."""
    check_unseen_excluded(train_df, _VIENEU_PATTERN, split_name)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(description="Huấn luyện ViTrueVoice SSL-AASIST")
    p.add_argument("--branch", required=True, choices=["A", "B0", "B"],
                   help="Nhánh thí nghiệm: A (clean), B0 (codec), B (codec+RawBoost)")
    p.add_argument("--manifest-dir", default="data/manifests",
                   help="Thư mục chứa train.csv và dev.csv")
    p.add_argument("--audio-root", default=".",
                   help="Thư mục gốc chứa file âm thanh")
    p.add_argument("--out-dir", default=None,
                   help="Thư mục lưu best_model.pt (mặc định: out/run_<branch>)")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    # Tùy chọn kiểm thử nhanh và điều chỉnh epoch
    p.add_argument("--limit", type=int, default=0,
                   help="Giới hạn số mẫu train/dev để kiểm thử nhanh (0 = toàn bộ)")
    p.add_argument("--phase1-epochs", type=int, default=None,
                   help="Ghi đè số epoch Pha 1 (mặc định theo nhánh: 4)")
    p.add_argument("--phase2-epochs", type=int, default=None,
                   help="Ghi đè số epoch Pha 2 (mặc định theo nhánh: 60 cho A, 20 cho B0/B)")
    # Siêu tham số kiến trúc (giữ mặc định để tái lập từ model_kwargs)
    p.add_argument("--d-graph", type=int, default=64)
    p.add_argument("--conv-channels", nargs=2, type=int, default=[64, 128])
    p.add_argument("--n-hs", type=int, default=1)
    return p.parse_args()


def main():
    args = _parse_args()
    out_dir = args.out_dir or f"out/run_{args.branch}"
    manifest_dir = Path(args.manifest_dir)

    # ── Tải manifest ────────────────────────────────────────────────────────
    train_df = pd.read_csv(manifest_dir / "train.csv", keep_default_na=False)
    dev_df   = pd.read_csv(manifest_dir / "dev.csv",   keep_default_na=False)

    # ── Kiểm tra VieNeu không lọt vào train/dev ─────────────────────────────
    validate_manifest(train_df, "train")
    validate_manifest(dev_df,   "dev")

    if args.limit > 0:
        print(f"⚡ Giới hạn số mẫu (--limit {args.limit}) cho kiểm thử nhanh.")
        train_df = train_df.head(args.limit)
        dev_df = dev_df.head(args.limit)

    # ── Cấu hình nhánh ──────────────────────────────────────────────────────
    cfg, mode, transform = build_branch_config(args.branch, out_dir=out_dir)
    if args.phase1_epochs is not None:
        cfg.phase1_epochs = args.phase1_epochs
    if args.phase2_epochs is not None:
        cfg.phase2_epochs = args.phase2_epochs

    # ── Trọng số loss động ──────────────────────────────────────────────────
    cfg.class_weights = tuple(compute_weights(train_df, args.branch))
    print(f"⚖️  class_weights [spoof, bona] = {cfg.class_weights}")

    # ── Dataset & DataLoader ─────────────────────────────────────────────────
    train_ds = ViTrueVoiceDataset(
        train_df, audio_root=args.audio_root,
        mode=mode, train=True, transform=transform, target_len=_TARGET_LEN,
    )
    dev_ds = ViTrueVoiceDataset(
        dev_df, audio_root=args.audio_root,
        mode="eval", train=False, target_len=_TARGET_LEN,
    )
    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, pin_memory=(args.device == "cuda"),
    )
    dev_loader = DataLoader(
        dev_ds, batch_size=args.batch_size * 2,
        num_workers=args.num_workers, pin_memory=(args.device == "cuda"),
    )

    # ── Model ────────────────────────────────────────────────────────────────
    model = SSLAASIST(
        d_graph=args.d_graph,
        conv_channels=tuple(args.conv_channels),
        n_hs=args.n_hs,
    )
    total_params = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"🧠 Model: {total_params:.1f}M params | branch={args.branch} | device={args.device}")
    print(f"📦 Train: {len(train_ds)} mẫu | Dev: {len(dev_ds)} mẫu")
    print(f"🔁 Phase1={cfg.phase1_epochs}ep | Phase2={cfg.phase2_epochs}ep | patience={cfg.patience}")

    # ── Huấn luyện ──────────────────────────────────────────────────────────
    trainer = Trainer(model, cfg, device=args.device)
    history = trainer.fit(train_loader, dev_loader)

    best_eer = min(h["dev_eer"] for h in history)
    print(f"\n✅ Xong! best_dev_EER={best_eer:.4f} | checkpoint: {out_dir}/best_model.pt")


if __name__ == "__main__":
    main()
