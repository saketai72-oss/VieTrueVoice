from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_

from src.evaluation.metrics import compute_eer
from src.training.losses import weighted_ce


@dataclass
class TrainConfig:
    branch: str = "B"
    phase1_epochs: int = 4
    phase2_epochs: int = 20
    lr_phase1: float = 1e-4
    lr_backend: float = 1e-5
    lr_ssl: float = 1e-6
    betas: tuple = (0.9, 0.98)
    weight_decay: float = 1e-4
    accum_steps: int = 2
    grad_clip: float = 5.0
    patience: int = 5
    class_weights: tuple = (0.8602, 0.1398)   # [spoof, bonafide]
    amp: bool = True
    out_dir: str = "out/run"


class EarlyStopper:
    def __init__(self, patience, min_delta=0.0):
        self.patience, self.min_delta = patience, min_delta
        self.best, self.bad = float("inf"), 0

    def step(self, value):
        if value < self.best - self.min_delta:
            self.best, self.bad = value, 0
            return True
        self.bad += 1
        return False

    @property
    def should_stop(self):
        return self.bad >= self.patience


def make_optimizer(model, phase, cfg):
    if phase == 1:
        params = [p for p in model.parameters() if p.requires_grad]
        return torch.optim.AdamW(params, lr=cfg.lr_phase1, betas=cfg.betas,
                                 weight_decay=cfg.weight_decay)
    return torch.optim.AdamW(model.param_groups(cfg.lr_backend, cfg.lr_ssl),
                             lr=cfg.lr_backend, betas=cfg.betas,
                             weight_decay=cfg.weight_decay)


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    S, L, G = [], [], []
    for b in loader:
        S.append(model.score(b["wave"].to(device)).float().cpu().numpy())
        L.append(b["label"].numpy())
        G.extend(b["speaker_id"])
    return np.concatenate(S), np.concatenate(L), np.array(G)


class Trainer:
    def __init__(self, model, cfg, device="cpu"):
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.cfg = cfg
        self.criterion = weighted_ce(list(cfg.class_weights)).to(self.device)
        self.use_amp = cfg.amp and self.device.type == "cuda"
        self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)
        self.best_eer = float("inf")
        self.opt_steps = 0
        self.history = []

    def _train_epoch(self, loader, opt):
        cfg = self.cfg
        self.model.train()
        total, n, nb = 0.0, 0, len(loader)
        opt.zero_grad(set_to_none=True)
        for i, b in enumerate(loader, 1):
            x, y = b["wave"].to(self.device), b["label"].to(self.device)
            with torch.autocast(device_type=self.device.type, enabled=self.use_amp):
                loss = self.criterion(self.model(x).float(), y)
            self.scaler.scale(loss / cfg.accum_steps).backward()
            total += loss.item() * len(y)
            n += len(y)
            if i % cfg.accum_steps == 0 or i == nb:
                self.scaler.unscale_(opt)
                clip_grad_norm_(self.model.parameters(), cfg.grad_clip)
                self.scaler.step(opt)
                self.scaler.update()
                opt.zero_grad(set_to_none=True)
                self.opt_steps += 1
        return total / max(n, 1)

    def _save(self, phase, epoch, eer):
        out = Path(self.cfg.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        payload = {
            "model": self.model.state_dict(),
            "branch": self.cfg.branch,
            "phase": phase,
            "epoch": epoch,
            "dev_eer": eer,
            "config": asdict(self.cfg),
        }
        if hasattr(self.model, "model_kwargs"):
            payload["model_kwargs"] = self.model.model_kwargs
        torch.save(payload, out / "best_model.pt")

    def fit(self, train_loader, dev_loader):
        cfg, epoch = self.cfg, 0
        for phase, n_ep in ((1, cfg.phase1_epochs), (2, cfg.phase2_epochs)):
            if n_ep <= 0:
                continue
            self.model.freeze_ssl() if phase == 1 else self.model.unfreeze_ssl()
            opt = make_optimizer(self.model, phase, cfg)
            stopper = EarlyStopper(cfg.patience)
            for _ in range(n_ep):
                epoch += 1
                ds = getattr(train_loader, "dataset", None)
                if hasattr(ds, "set_epoch"):
                    ds.set_epoch(epoch)
                loss = self._train_epoch(train_loader, opt)
                s, l, _ = predict(self.model, dev_loader, self.device)
                eer = compute_eer(s, l)[0]
                if eer < self.best_eer:
                    self.best_eer = eer
                    self._save(phase, epoch, eer)
                stopper.step(eer)
                self.history.append({"epoch": epoch, "phase": phase,
                                     "train_loss": loss, "dev_eer": eer})
                print(f"[P{phase}] ep {epoch} loss={loss:.4f} dev_EER={eer:.4f}",
                      flush=True)
                if stopper.should_stop:
                    break
        out = Path(cfg.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "history.json").write_text(json.dumps(self.history, indent=1))
        return self.history
