"""Tăng cường online cho nhánh B (RawBoost cài lại theo mô tả bài báo).

Mọi hàm: f(x, rng) -> mảng cùng độ dài. Ngẫu nhiên chỉ lấy từ rng
(Dataset truyền rng theo (seed, epoch, idx) nên tái lập được).
"""
from __future__ import annotations
import numpy as np

import scipy.signal as sps

SR = 16000
_EPS = 1e-12


def _peak_match(y, ref):
    py, pr = np.max(np.abs(y)), np.max(np.abs(ref))
    return y if py < _EPS or pr < _EPS else y * (pr / py)


def pitch_perturbation(
    x: np.ndarray,
    rng: np.random.Generator,
    semitones_range: tuple[float, float] = (-7.0, 4.0),
    target_len: int = 64000,
    sr: int = SR,
) -> np.ndarray:
    """Tăng cường biến đổi cao độ giữ nguyên formant (pitch-preserving via phase vocoder).
    
    Sử dụng torchaudio.functional.pitch_shift để chỉ dịch chuyển F0,
    bảo toàn formant và tốc độ nói của người nói thật.
    """
    import torch
    import torchaudio

    x = np.asarray(x, dtype=np.float32)
    if len(x) == 0 or np.max(np.abs(x)) < _EPS:
        return np.zeros(target_len, dtype=np.float32)

    n_steps = float(rng.uniform(*semitones_range))
    if abs(n_steps) < 0.1:
        y = x.copy()
    else:
        t = torch.from_numpy(x)
        y = torchaudio.functional.pitch_shift(
            t, sample_rate=sr, n_steps=n_steps
        ).numpy()
        if len(y) > target_len:
            y = y[:target_len]
        elif len(y) < target_len:
            y = np.tile(y, int(np.ceil(target_len / len(y))))[:target_len]

    return _peak_match(y, x).astype(np.float32)


class RawBoostTransform:
    """Callable class thay cho local closure để tương thích pickle khi DataLoader num_workers > 0 trên Windows."""

    def __init__(self, p_lnl: float = 0.5, p_isd: float = 0.3, p_ssi: float = 0.5,
                 p_pitch: float = 0.0, semitones_range: tuple[float, float] = (-7.0, 4.0),
                 always_one: bool = True):
        self.p_lnl = p_lnl
        self.p_isd = p_isd
        self.p_ssi = p_ssi
        self.p_pitch = p_pitch
        self.semitones_range = semitones_range
        self.always_one = always_one

    def __call__(self, x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        flags = [rng.random() < p for p in (self.p_lnl, self.p_isd, self.p_ssi)]
        if self.always_one and not any(flags):
            flags[int(rng.integers(0, 3))] = True
        y = x.astype(np.float64)
        if flags[0]:
            y = lnl_convolutive(y, rng)
        if flags[1]:
            y = isd_additive(y, rng)
        if flags[2]:
            y = ssi_additive(y, rng)
        y = y.astype(np.float32)
        if self.p_pitch > 0.0 and rng.random() < self.p_pitch:
            y = pitch_perturbation(y, rng, semitones_range=self.semitones_range, target_len=len(x))
        return y


def make_rawboost(p_lnl=0.5, p_isd=0.3, p_ssi=0.5, p_pitch=0.0, semitones_range=(-7.0, 4.0), always_one=True):
    """Trả về transform(x, rng) cho ViTrueVoiceDataset(mode='augmented')."""
    return RawBoostTransform(p_lnl=p_lnl, p_isd=p_isd, p_ssi=p_ssi,
                             p_pitch=p_pitch, semitones_range=semitones_range, always_one=always_one)


def lnl_convolutive(x, rng, n_bands=(1, 4), gain_db=8.0, width=(0.1, 0.6),
                    nl=0.05, sr=SR):
    """Nhiễu tích chập tuyến tính (đáp ứng tần số ngẫu nhiên) + méo phi tuyến nhẹ."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0 or np.max(np.abs(x)) < _EPS:
        return x
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    lf = np.log(np.maximum(f, 1.0))
    h_db = np.zeros_like(lf)
    for _ in range(int(rng.integers(n_bands[0], n_bands[1] + 1))):
        fc = np.log(rng.uniform(100.0, sr / 2 - 500.0))
        w = rng.uniform(*width)
        h_db += rng.uniform(-gain_db, gain_db) * np.exp(-0.5 * ((lf - fc) / w) ** 2)
    y = np.fft.irfft(np.fft.rfft(x) * 10 ** (h_db / 20), n=len(x))
    p = np.max(np.abs(y))
    if p < _EPS:
        return x
    yn = y / p
    yn = yn + rng.uniform(-nl, nl) * yn ** 2 + rng.uniform(-nl, nl) * yn ** 3
    return _peak_match(yn, x)


def isd_additive(x, rng, p_max=10.0, g_max=2.0):
    """Nhiễu xung phụ thuộc tín hiệu trên p% mẫu (p ~ U(0, p_max))."""
    x = np.asarray(x, dtype=np.float64)
    y = x.copy()
    if len(x) == 0:
        return y
    p = rng.uniform(0.0, p_max) / 100.0
    idx = np.flatnonzero(rng.random(len(x)) < p)
    y[idx] += rng.uniform(0.0, g_max) * x[idx] * rng.uniform(-1, 1, size=len(idx))
    return y


def ssi_additive(x, rng, snr_db=(10.0, 40.0), sr=SR):
    """Nhiễu cộng màu, dừng, độc lập tín hiệu, SNR ~ U(snr_db)."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0:
        return x
    px = np.mean(x ** 2)
    if px < _EPS:
        return x
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    lo = rng.uniform(20.0, 2000.0)
    hi = rng.uniform(lo + 500.0, sr / 2)
    spec = np.fft.rfft(rng.standard_normal(len(x))) * ((f >= lo) & (f <= hi))
    n = np.fft.irfft(spec, n=len(x))
    pn = np.mean(n ** 2)
    if pn < _EPS:
        return x
    n *= np.sqrt(px / (pn * 10 ** (rng.uniform(*snr_db) / 10)))
    return x + n
