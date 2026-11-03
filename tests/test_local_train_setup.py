"""Unit tests for local training setup and VRAM optimization (Giai đoạn 3 local)."""

from __future__ import annotations

import sys

import pandas as pd

from scripts.train import _parse_args, compute_weights


def test_accum_steps_cli_arg(monkeypatch):
    """Kiểm tra cờ CLI --accum-steps được chấp nhận và parse đúng giá trị."""
    test_args = [
        "train.py",
        "--branch", "B_zalo",
        "--batch-size", "4",
        "--accum-steps", "4",
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    args = _parse_args()
    assert args.accum_steps == 4
    assert args.batch_size == 4


def test_clamped_weights_for_b_zalo():
    """Kiểm tra trọng số loss nhánh B_zalo được kẹp an toàn trong [0.35, 0.65]."""
    df_imbalanced = pd.DataFrame({
        "label": ["spoof"] * 90 + ["bonafide"] * 10,
        "codec": ["clean_16khz"] * 100,
    })
    weights = compute_weights(df_imbalanced, "B_zalo")
    assert len(weights) == 2
    assert weights[0] >= 0.35 and weights[0] <= 0.65
    assert weights[1] >= 0.35 and weights[1] <= 0.65
    assert abs(sum(weights) - 1.0) < 1e-4


def test_trainer_gradient_accumulation_step():
    """Kiểm tra logic gradient accumulation trong Trainer tăng đúng số bước optimizer."""
    import torch
    from torch.utils.data import DataLoader, Dataset

    from src.training.trainer import TrainConfig, Trainer

    class DummyDataset(Dataset):
        def __len__(self):
            return 8

        def __getitem__(self, idx):
            # 64000 samples for AASIST/Wav2Vec input compatibility
            return {
                "wave": torch.randn(64000, dtype=torch.float32),
                "label": torch.tensor(idx % 2, dtype=torch.long),
            }

    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(64000, 2)
            self.out = self.linear

        def forward(self, x, return_embedding=False):
            emb = self.linear(x)
            if return_embedding:
                return emb, emb
            return emb

    cfg = TrainConfig(
        branch="B_zalo",
        accum_steps=2,
        loss_type="ce",
        amp=False,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DummyModel()
    trainer = Trainer(model, cfg, device=device)
    opt = torch.optim.SGD(model.parameters(), lr=1e-3)
    loader = DataLoader(DummyDataset(), batch_size=2)

    loss_val = trainer._train_epoch(loader, opt)
    assert isinstance(loss_val, float)
    assert loss_val > 0.0
    # 8 samples / batch_size 2 = 4 batches. With accum_steps=2, exactly 2 optimizer steps
    assert trainer.opt_steps == 2


def test_trainer_am_softmax_with_accumulation():
    """Kiểm tra loss AM-Softmax kết hợp gradient accumulation và scaler."""
    import torch
    from torch.utils.data import DataLoader, Dataset

    from src.training.trainer import TrainConfig, Trainer

    class DummyDataset(Dataset):
        def __len__(self):
            return 8

        def __getitem__(self, idx):
            return {
                "wave": torch.randn(64000, dtype=torch.float32),
                "label": torch.tensor(idx % 2, dtype=torch.long),
            }

    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = torch.nn.Linear(64000, 320)
            self.out = torch.nn.Linear(320, 2, bias=False)

        def forward(self, x, return_embedding=False):
            emb = self.linear(x)
            out = self.out(emb)
            if return_embedding:
                return out, emb
            return out

    cfg = TrainConfig(
        branch="B_zalo",
        accum_steps=2,
        loss_type="am_softmax",
        am_s=30.0,
        am_m=0.35,
        amp=False,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DummyModel()
    trainer = Trainer(model, cfg, device=device)
    opt = torch.optim.SGD(model.parameters(), lr=1e-3)
    loader = DataLoader(DummyDataset(), batch_size=2)

    loss_val = trainer._train_epoch(loader, opt)
    assert isinstance(loss_val, float)
    assert loss_val > 0.0
    assert trainer.opt_steps == 2


