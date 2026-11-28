"""Unit tests for in-memory acoustic & pooling forensic analysis (`src/app/forensics.py`)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.app.forensics import extract_forensic_analysis


def _make_sine(freqs_hz: list[float], duration_sec: float = 2.0, sr: int = 16000, amp: float = 0.3) -> np.ndarray:
    t = np.arange(int(sr * duration_sec), dtype=np.float32) / sr
    sig = np.zeros_like(t)
    for f in freqs_hz:
        sig += np.sin(2.0 * np.pi * f * t)
    sig = sig / max(len(freqs_hz), 1) * amp
    return sig.astype(np.float32)


def test_forensics_wideband_noise_schema_and_ranges():
    """Wideband white noise produces complete forensic payload within expected bounds."""
    rng = np.random.default_rng(42)
    audio = (rng.standard_normal(16000 * 2) * 0.2).astype(np.float32)

    res = extract_forensic_analysis(
        audio,
        sr=16000,
        window_scores=[10.0, 12.0],
        raw_score=12.0,
        threshold=0.0,
        pooling_mode="asymmetric_veto",
    )

    expected_keys = {
        "duration_sec",
        "sample_rate",
        "rms_energy",
        "peak_db",
        "hf_ratio_pct",
        "estimated_f0_hz",
        "bandwidth_profile",
        "band_energy_pct",
        "pooling",
        "windows",
        "waveform",
        "mel_spectrogram",
        "platt_curve",
    }
    assert expected_keys <= res.keys()
    assert res["duration_sec"] == pytest.approx(2.0, abs=0.05)
    assert res["sample_rate"] == 16000
    assert res["rms_energy"] > 0.0
    assert math.isfinite(res["peak_db"])
    assert res["bandwidth_profile"] == "WIDEBAND_16KHZ"
    assert res["hf_ratio_pct"] > 20.0

    # Band energy sums to ~100%
    bands = res["band_energy_pct"]
    assert {"low_0_300hz", "mid_300_3400hz", "high_3400_8000hz"} <= bands.keys()
    assert sum(bands.values()) == pytest.approx(100.0, abs=0.5)
    assert bands["high_3400_8000hz"] > 20.0

    # Mel-spectrogram shape 48 x <=96 with uint8 values 0..255
    mel = res["mel_spectrogram"]
    assert mel["n_mels"] == 48
    assert mel["fmax"] == 8000
    values = mel["values"]
    assert isinstance(values, list)
    assert len(values) == 48
    assert 1 <= len(values[0]) <= 96
    assert mel["n_frames"] == len(values[0])
    flat = [v for row in values for v in row]
    assert min(flat) >= 0
    assert max(flat) <= 255
    assert all(isinstance(v, int) for v in flat)

    # Waveform downsampled to <=240 points in [-1, 1]
    wf = res["waveform"]
    assert isinstance(wf, list)
    assert 1 <= len(wf) <= 240
    assert all(-1.0 <= float(v) <= 1.0 for v in wf)

    # Platt calibration curve metadata
    platt = res["platt_curve"]
    assert platt["temperature"] == pytest.approx(16.0, abs=1e-4)
    assert platt["scale_k"] == pytest.approx(0.0625, abs=1e-4)
    assert platt["borderline_margin"] == pytest.approx(8.0, abs=1e-4)
    assert 0.1 <= platt["prob_bona_pct"] <= 99.9
    assert 0.1 <= platt["prob_spoof_pct"] <= 99.9
    assert platt["prob_bona_pct"] + platt["prob_spoof_pct"] == pytest.approx(100.0, abs=0.2)


def test_forensics_distinguishes_narrowband_vs_wideband():
    """Narrowband (<3.4kHz) sine vs wideband (with >4kHz energy) yield distinct profiles."""
    narrow = _make_sine([200.0, 1000.0, 2200.0], duration_sec=2.0)
    wide = _make_sine([220.0, 1000.0, 5200.0], duration_sec=2.0)

    res_narrow = extract_forensic_analysis(narrow, sr=16000)
    res_wide = extract_forensic_analysis(wide, sr=16000)

    assert res_narrow["bandwidth_profile"] == "NARROWBAND_8KHZ"
    assert res_narrow["hf_ratio_pct"] < 1.5
    assert res_narrow["band_energy_pct"]["high_3400_8000hz"] < 1.5
    assert sum(res_narrow["band_energy_pct"].values()) == pytest.approx(100.0, abs=0.5)

    assert res_wide["bandwidth_profile"] == "WIDEBAND_16KHZ"
    assert res_wide["hf_ratio_pct"] > 10.0
    assert res_wide["band_energy_pct"]["high_3400_8000hz"] > 10.0
    assert sum(res_wide["band_energy_pct"].values()) == pytest.approx(100.0, abs=0.5)


def test_forensics_short_and_silent_audio_safe():
    """Short clips (<0.1s) and all-zero silent clips return finite, valid structures."""
    short_sig = _make_sine([300.0], duration_sec=0.05)
    silent_sig = np.zeros(16000, dtype=np.float32)

    for sig in (short_sig, silent_sig):
        res = extract_forensic_analysis(sig, sr=16000)
        assert math.isfinite(res["duration_sec"])
        assert math.isfinite(res["rms_energy"])
        assert math.isfinite(res["peak_db"])
        assert math.isfinite(res["hf_ratio_pct"])
        assert math.isfinite(res["estimated_f0_hz"])
        assert len(res["waveform"]) <= 240
        mel_vals = res["mel_spectrogram"]["values"]
        assert len(mel_vals) == 48
        assert 1 <= len(mel_vals[0]) <= 96
        flat = [v for row in mel_vals for v in row]
        assert min(flat) >= 0 and max(flat) <= 255

    silent_res = extract_forensic_analysis(silent_sig, sr=16000)
    assert silent_res["rms_energy"] == 0.0
    assert silent_res["estimated_f0_hz"] == 0.0


def test_forensics_windows_and_risk_weights():
    """Window metadata preserves ordering, timestamps, and risk_weight in [0, 1]."""
    audio = _make_sine([250.0, 1200.0], duration_sec=6.0)
    scores = [-20.0, 0.0, 15.0]
    res = extract_forensic_analysis(
        audio,
        sr=16000,
        window_scores=scores,
        raw_score=0.0,
        threshold=0.0,
        pooling_mode="asymmetric_veto",
    )

    windows = res["windows"]
    assert len(windows) == 3
    for idx, win in enumerate(windows, start=1):
        assert win["index"] == idx
        assert win["start_sec"] >= 0.0
        assert win["end_sec"] > win["start_sec"]
        assert 0.0 <= win["risk_weight"] <= 1.0

    # Risk weight decreases monotonically as score rises above threshold
    assert windows[0]["risk_weight"] > windows[1]["risk_weight"] > windows[2]["risk_weight"]
    assert windows[1]["risk_weight"] == pytest.approx(0.5, abs=1e-3)


@pytest.mark.parametrize(
    "window_scores,expected_branch,expected_veto",
    [
        ([8.0, 12.5, 10.0], "max_default", False),
        ([-18.0, 8.5, 14.0], "consensus_rescue", False),
        ([-22.0, -4.0, 3.0], "asymmetric_veto_trimmed_mean", True),
    ],
)
def test_forensics_pooling_branches(window_scores, expected_branch, expected_veto):
    """Consensus Asymmetric Veto branch telemetry matches src/preprocessing/pooling.py."""
    audio = _make_sine([220.0, 880.0], duration_sec=6.0)
    res = extract_forensic_analysis(
        audio,
        sr=16000,
        window_scores=window_scores,
        raw_score=float(np.mean(window_scores)),
        threshold=0.0,
        pooling_mode="asymmetric_veto",
    )

    pooling = res["pooling"]
    assert pooling["mode"] == "asymmetric_veto"
    assert pooling["branch"] == expected_branch
    assert pooling["veto_triggered"] is expected_veto
    assert isinstance(pooling["explanation"], str) and len(pooling["explanation"]) > 0
