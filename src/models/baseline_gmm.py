"""Baseline LFCC + GMM cho ViTrueVoice.

Quy ước: bonafide = 1, spoof = 0; điểm cao = giống bonafide.
Điểm = trung bình theo khung của log P(x|bona) - log P(x|spoof).
"""
from __future__ import annotations
import numpy as np
import joblib
from scipy.fft import dct
from sklearn.mixture import GaussianMixture

_EPS = 1e-10


def _linear_filterbank(sr, n_fft, n_filters):
    """Bộ lọc tam giác phân bố đều trên trục tần số tuyến tính (0..sr/2)."""
    freqs = np.linspace(0, sr / 2, n_fft // 2 + 1)
    edges = np.linspace(0, sr / 2, n_filters + 2)
    fb = np.zeros((n_filters, len(freqs)))
    for i in range(n_filters):
        l, c, r = edges[i], edges[i + 1], edges[i + 2]
        up = (freqs - l) / (c - l)
        down = (r - freqs) / (r - c)
        fb[i] = np.clip(np.minimum(up, down), 0.0, None)
    return fb


def _delta(x, N=2):
    """Hệ số delta theo công thức hồi quy chuẩn. x: (T, D)."""
    T = x.shape[0]
    padded = np.pad(x, ((N, N), (0, 0)), mode="edge")
    denom = 2 * sum(n * n for n in range(1, N + 1))
    out = np.zeros_like(x)
    for n in range(1, N + 1):
        out += n * (padded[N + n:N + n + T] - padded[N - n:N - n + T])
    return out / denom


def extract_lfcc(wave, sr=16000, n_lfcc=20, n_filters=20,
                 n_fft=512, win_length=400, hop_length=160, preemph=0.97):
    """Trả về (T, 3*n_lfcc) gồm static + delta + delta-delta."""
    x = np.asarray(wave, dtype=np.float64).ravel()
    if len(x) < win_length:
        x = np.pad(x, (0, win_length - len(x)))
    x = np.append(x[0], x[1:] - preemph * x[:-1])
    frames = np.lib.stride_tricks.sliding_window_view(x, win_length)[::hop_length]
    frames = frames * np.hamming(win_length)
    power = np.abs(np.fft.rfft(frames, n=n_fft, axis=1)) ** 2
    fb = _linear_filterbank(sr, n_fft, n_filters)
    logmel = np.log(power @ fb.T + _EPS)
    static = dct(logmel, type=2, norm="ortho", axis=1)[:, :n_lfcc]
    d1 = _delta(static)
    d2 = _delta(d1)
    return np.concatenate([static, d1, d2], axis=1).astype(np.float32)


class LFCCGMMBaseline:
    def __init__(self, n_components=512, covariance_type="diag",
                 max_iter=100, max_frames_per_utt=100, seed=0):
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.max_iter = max_iter
        self.max_frames_per_utt = max_frames_per_utt
        self.seed = seed
        self.gmm_bona = None
        self.gmm_spoof = None

    def _stack(self, waves, rng):
        chunks = []
        for w in waves:
            f = extract_lfcc(w)
            if self.max_frames_per_utt and len(f) > self.max_frames_per_utt:
                f = f[rng.choice(len(f), self.max_frames_per_utt, replace=False)]
            chunks.append(f)
        return np.concatenate(chunks, axis=0)

    def _new_gmm(self):
        return GaussianMixture(
            n_components=self.n_components,
            covariance_type=self.covariance_type,
            max_iter=self.max_iter,
            reg_covar=1e-4,
            random_state=self.seed,
        )

    def fit(self, bona_waves, spoof_waves):
        if len(bona_waves) == 0 or len(spoof_waves) == 0:
            raise ValueError("Cần ít nhất một mẫu bonafide và một mẫu spoof")
        rng = np.random.default_rng(self.seed)
        xb = self._stack(bona_waves, rng)
        xs = self._stack(spoof_waves, rng)
        self.gmm_bona = self._new_gmm().fit(xb)
        self.gmm_spoof = self._new_gmm().fit(xs)
        return self

    def score_features(self, feat):
        lb = self.gmm_bona.score_samples(feat)
        ls = self.gmm_spoof.score_samples(feat)
        return float(np.mean(lb - ls))

    def score_wave(self, wave):
        if self.gmm_bona is None:
            raise RuntimeError("Mô hình chưa được fit")
        return self.score_features(extract_lfcc(wave))

    def save(self, path):
        joblib.dump(self, path)

    @staticmethod
    def load(path):
        return joblib.load(path)
