"""Chấm điểm SSL-AASIST, xuất eval_metrics cùng schema với eval_gmm.py.

Điểm = z_bonafide - z_spoof (cao = bonafide). Mặc định chỉ chấm role == 'eval'
để ba codec có đúng cùng tập phát ngôn (bộ ba ghép cặp).
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from scripts.eval_gmm import build_table
from src.models.ssl_aasist import SSLAASIST
from src.training.dataset import ViTrueVoiceDataset


def filter_role(df, role):
    if role is None or "role" not in df.columns:
        return df
    out = df[df["role"].astype(str) == role]
    if len(out) == 0:
        raise ValueError(f"Không có hàng nào với role={role}")
    return out


def check_tts_labels(scored):
    bad = scored[(scored["label"] == 0) &
                 scored["tts"].astype(str).str.lower().isin(["", "none", "nan"])]
    if len(bad):
        raise ValueError(f"{len(bad)} hàng spoof thiếu tên công cụ TTS")


def load_model(ckpt_path, device, **model_kwargs):
    ck = torch.load(ckpt_path, map_location="cpu")
    kw = {**ck.get("model_kwargs", {}), **model_kwargs}
    model = SSLAASIST(**kw)
    model.load_state_dict(ck["model"])
    return model.to(device).eval(), ck


@torch.no_grad()
def score_manifest(model, ds, device, batch_size=16, num_workers=2):
    model.eval()
    dl = DataLoader(ds, batch_size=batch_size, num_workers=num_workers)
    S, L, spk, cond, tts = [], [], [], [], []
    for b in dl:
        S.append(model.score(b["wave"].to(device)).float().cpu().numpy())
        L.append(b["label"].numpy())
        spk.extend(b["speaker_id"]); cond.extend(b["codec"]); tts.extend(b["tts"])
    return pd.DataFrame({"score": np.concatenate(S), "label": np.concatenate(L),
                         "speaker_id": spk, "condition": cond, "tts": tts})


def _kv(items):
    return dict(s.split("=", 1) for s in items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--manifest", nargs="+", required=True,
                    help="tên=csv, ví dụ in_domain=out/test_indomain.csv")
    ap.add_argument("--audio-root", default=".")
    ap.add_argument("--role", default="eval")
    ap.add_argument("--out", default="benchmarks/eval_metrics_ssl.csv")
    ap.add_argument("--scores-out", default="benchmarks/scores_ssl.csv")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, ck = load_model(a.ckpt, device)
    print(f"checkpoint: phase {ck.get('phase')}, epoch {ck.get('epoch')}, "
          f"dev_EER {ck.get('dev_eer'):.4f}")

    frames, tables = [], []
    for name, csv in _kv(a.manifest).items():
        df = filter_role(pd.read_csv(csv, keep_default_na=False), a.role)
        if a.limit:
            df = df.head(a.limit)
        ds = ViTrueVoiceDataset(df, audio_root=a.audio_root, mode="eval")
        sc = score_manifest(model, ds, device, a.batch_size)
        check_tts_labels(sc)
        sc["split"] = name
        frames.append(sc)
        tables.append(build_table(sc, split=name, n_boot=a.n_boot, seed=a.seed))

    Path(a.scores_out).parent.mkdir(parents=True, exist_ok=True)
    pd.concat(frames, ignore_index=True).to_csv(a.scores_out, index=False)
    result = pd.concat(tables, ignore_index=True)
    result.to_csv(a.out, index=False)
    print(result[["split", "condition", "tts", "eer", "eer_ci_lo",
                  "eer_ci_hi", "min_dcf"]].to_string(index=False))


if __name__ == "__main__":
    main()
