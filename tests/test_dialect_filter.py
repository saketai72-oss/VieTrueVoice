import numpy as np
import pytest
from src.vitruevoice.dialect_evaluator import (
    compute_pitch_dynamics,
    evaluate_prosodic_consistency,
    evaluate_dialect_consistency,
)
from src.vitruevoice.base import QualityMetrics


def test_compute_pitch_dynamics():
    """Verify pitch extraction returns non-negative mean and variance for voiced signals."""
    sr = 16000
    t = np.linspace(0, 1.0, int(1.0 * sr), endpoint=False)
    # Synthetic pitch signal ~150Hz
    sig = (0.5 * np.sin(2 * np.pi * 150 * t)).astype(np.float32)
    stats = compute_pitch_dynamics(sig, sr=sr)
    
    assert "mean_f0" in stats
    assert "std_f0" in stats
    assert "cv_f0" in stats
    assert "pitch_jump_rate" in stats
    assert 130 <= stats["mean_f0"] <= 170
    assert stats["cv_f0"] >= 0.0


def test_evaluate_prosodic_consistency_match():
    """Consistent voice dynamics with matching reference should pass Gate 4."""
    sr = 16000
    t = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    # Smooth prosody ~140Hz
    freq = np.linspace(135, 145, len(t))
    sig = (0.4 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    
    score, match, drift = evaluate_prosodic_consistency(
        audio=sig,
        sr=sr,
        ref_audio=sig,
        ref_sr=sr,
        engine_name="VieNeu-TTS-v3Turbo"
    )
    
    assert match is True
    assert drift is False
    assert score >= 0.70


def test_evaluate_prosodic_consistency_drift_detected():
    """Wild pitch excursion or pitch jump anomalies should trigger drift (Label-Free)."""
    sr = 16000
    t = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    # Severe pitch shift (250Hz synthetic vs 140Hz reference)
    sig_drift = (0.4 * np.sin(2 * np.pi * 250 * t)).astype(np.float32)
    
    # Smooth natural reference ~140Hz
    freq_ref = np.linspace(135, 145, len(t))
    sig_ref = (0.4 * np.sin(2 * np.pi * freq_ref * t)).astype(np.float32)

    
    score, match, drift = evaluate_prosodic_consistency(
        audio=sig_drift,
        sr=sr,
        ref_audio=sig_ref,
        ref_sr=sr,
        engine_name="AnyEngine"
    )
    
    assert match is False
    assert drift is True
    assert score < 0.65


def test_label_free_agnostic_to_engine():
    """Gate 4 evaluates acoustic signal directly without engine-name prejudice."""
    sr = 16000
    t = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    sig = (0.35 * np.sin(2 * np.pi * 150 * t)).astype(np.float32)
    
    # Test F5-TTS
    s_f5, m_f5, d_f5 = evaluate_prosodic_consistency(
        audio=sig, sr=sr, ref_audio=sig, ref_sr=sr, engine_name="F5-TTS-Vietnamese"
    )
    # Test VieNeu-TTS
    s_vn, m_vn, d_vn = evaluate_prosodic_consistency(
        audio=sig, sr=sr, ref_audio=sig, ref_sr=sr, engine_name="VieNeu-TTS-v3Turbo"
    )
    
    assert m_f5 is True and m_vn is True
    assert d_f5 is False and d_vn is False
    assert abs(s_f5 - s_vn) < 1e-4


def test_quality_metrics_gate4_integration():
    """QualityMetrics dataclass must support Gate 4 prosody fields and dict subscripting."""
    qm = QualityMetrics(
        clean_wer=0.05,
        clean_cer=0.02,
        speaker_sim=0.75,
        band_2_4k_pct=0.29,
        band_4_8k_pct=0.02,
        is_catastrophic=False,
        gate1_pass=True,
        gate2_pass=True,
        gate3_pass=True,
        overall_pass=True,
        composite_score=0.85,
        dialect_score=0.55,
        dialect_match=False,
        gate4_pass=False,
        dialect_drift=True
    )
    
    assert qm["gate4_pass"] is False
    assert qm["dialect_drift"] is True
    assert qm.get("dialect_score") == 0.55
