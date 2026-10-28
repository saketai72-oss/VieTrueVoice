import numpy as np
import pytest
from src.models.baseline_gmm import extract_lfcc, LFCCGMMBaseline
from src.evaluation.metrics import compute_eer

SR = 16000


def _noise(seed, n=SR * 2):
    return np.random.default_rng(seed).normal(size=n).astype(np.float32)


def _lowpassed(seed, n=SR * 2):
    x = _noise(seed, n)
    k = np.ones(8) / 8.0  # lọc thông thấp đơn giản
    return np.convolve(x, k, mode="same").astype(np.float32)


def test_lfcc_shape_is_60_dim():
    feat = extract_lfcc(_noise(0, 64000))
    assert feat.ndim == 2 and feat.shape[1] == 60
    assert feat.shape[0] == 1 + (64000 - 400) // 160


def test_lfcc_is_finite_on_normal_and_silent_input():
    assert np.all(np.isfinite(extract_lfcc(_noise(1))))
    assert np.all(np.isfinite(extract_lfcc(np.zeros(SR, dtype=np.float32))))


def test_lfcc_handles_short_waveform():
    feat = extract_lfcc(_noise(2, 200))  # ngắn hơn 1 cửa sổ
    assert feat.shape[0] >= 1 and feat.shape[1] == 60


def test_fit_rejects_empty_class():
    m = LFCCGMMBaseline(n_components=2)
    with pytest.raises(ValueError):
        m.fit([_noise(0)], [])


def test_scores_separate_two_synthetic_classes():
    bona = [_noise(s) for s in range(12)]
    spoof = [_lowpassed(100 + s) for s in range(12)]
    m = LFCCGMMBaseline(n_components=4, max_frames_per_utt=50, seed=0)
    m.fit(bona[:8], spoof[:8])
    test_w = bona[8:] + spoof[8:]
    labels = np.array([1] * 4 + [0] * 4)
    scores = np.array([m.score_wave(w) for w in test_w])
    eer, _ = compute_eer(scores, labels)
    assert eer < 0.1
    assert scores[labels == 1].mean() > scores[labels == 0].mean()


def test_save_load_roundtrip(tmp_path):
    bona = [_noise(s) for s in range(4)]
    spoof = [_lowpassed(50 + s) for s in range(4)]
    m = LFCCGMMBaseline(n_components=2, max_frames_per_utt=30, seed=0)
    m.fit(bona, spoof)
    p = tmp_path / "gmm.joblib"
    m.save(p)
    m2 = LFCCGMMBaseline.load(p)
    w = _noise(999)
    assert m.score_wave(w) == pytest.approx(m2.score_wave(w), rel=1e-9)
