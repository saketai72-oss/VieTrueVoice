"""Dataset ViTrueVoice (manifest dạng dài). Nhãn: spoof = 0, bonafide = 1."""
from __future__ import annotations
from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

CLEAN = "clean_16khz"
_LABELS = {"bonafide": 1, "bona_fide": 1, "bona fide": 1, "1": 1,
           "spoof": 0, "fake": 0, "0": 0}


from src.preprocessing.audio_loader import load_audio

def load_wave(path, sr=16000):
    return load_audio(path, target_sr=sr)


def fit_length(x, n, train, rng):
    """Repeat padding nếu ngắn; random crop (train) hoặc lấy n mẫu đầu (eval)."""
    x = np.asarray(x, dtype=np.float32)
    if len(x) == 0:
        raise ValueError("Sóng âm rỗng")
    if len(x) < n:
        x = np.tile(x, int(np.ceil(n / len(x))))
    if len(x) > n:
        start = int(rng.integers(0, len(x) - n + 1)) if train else 0
        x = x[start:start + n]
    return x


def check_unseen_excluded(df, pattern, name):
    """Báo lỗi nếu công cụ TTS 'chưa thấy' lọt vào tập train/dev (làm vô hiệu H2)."""
    hit = df["tts_generator"].astype(str).str.lower().str.contains(
        pattern.lower(), regex=False)
    if hit.any():
        raise ValueError(f"{name}: có {int(hit.sum())} hàng thuộc TTS '{pattern}'")


class ViTrueVoiceDataset(Dataset):
    """mode: 'clean' (chỉ clean_16khz), 'augmented' (áp transform khi train=True),
    'eval' (mọi codec, không transform)."""

    def __init__(self, manifest, audio_root=".", split=None, mode="clean",
                 train=False, transform=None, target_len=64000, seed=0):
        if mode not in ("clean", "augmented", "eval"):
            raise ValueError(f"mode không hợp lệ: {mode}")
        df = (pd.read_csv(manifest, keep_default_na=False)
              if isinstance(manifest, (str, Path)) else manifest.copy())
        if split is not None:
            df = df[df["split"] == split]
        if mode == "clean":
            df = df[df["codec"] == CLEAN]
        if "audio_path" in df.columns:
            df["audio_path"] = df["audio_path"].astype(str).str.replace("\\", "/", regex=False)
        if len(df) == 0:
            raise ValueError("Không còn hàng nào sau khi lọc")
        lab = df["label"].astype(str).str.lower().str.strip().map(_LABELS)
        if lab.isna().any():
            raise ValueError(f"Nhãn lạ: {df['label'][lab.isna()].unique()[:5]}")
        self.df = df.reset_index(drop=True)
        self.labels = lab.astype(int).to_numpy()
        self.root = Path(audio_root)
        self.mode, self.train = mode, train
        self.transform = transform if mode == "augmented" else None
        self.target_len, self.seed, self.epoch = target_len, seed, 0

    def set_epoch(self, epoch):
        self.epoch = int(epoch)

    def class_counts(self):
        return {"spoof": int((self.labels == 0).sum()),
                "bonafide": int((self.labels == 1).sum())}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, i):
        r = self.df.iloc[i]
        rng = np.random.default_rng([self.seed, self.epoch, i])
        x = load_wave(self.root / r["audio_path"])
        if self.train and self.transform is not None:
            x = self.transform(x, rng)
        x = fit_length(x, self.target_len, self.train, rng)
        return {"wave": torch.from_numpy(x),
                "label": torch.tensor(int(self.labels[i])),
                "speaker_id": str(r["speaker_id"]),
                "codec": str(r["codec"]),
                "tts": str(r.get("tts_generator", ""))}
