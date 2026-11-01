"""Shared decision and calibration logic for ViTrueVoice inference endpoints."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class DecisionResult:
    raw_score: float
    threshold: float
    is_bonafide: bool
    prediction: str  # "BONA_FIDE" or "SPOOF"
    label: int       # 1 or 0
    confidence: float | None
    confidence_calibrated: bool


def classify_score(
    raw_score: float,
    threshold: float = 0.0,
    calibrator: Callable[[float], float] | None = None,
) -> DecisionResult:
    """Classify a raw model score using a configured threshold and optional calibrator.

    STUBBORN_FACT: Raw model score >= threshold is classified as BONA_FIDE (label 1),
    otherwise SPOOF (label 0).
    When no calibrator is provided, confidence is None and confidence_calibrated is False.
    """
    is_bonafide = bool(raw_score >= threshold)
    prediction = "BONA_FIDE" if is_bonafide else "SPOOF"
    label = 1 if is_bonafide else 0

    if calibrator is not None:
        confidence = float(calibrator(raw_score))
        confidence_calibrated = True
    else:
        confidence = None
        confidence_calibrated = False

    return DecisionResult(
        raw_score=raw_score,
        threshold=threshold,
        is_bonafide=is_bonafide,
        prediction=prediction,
        label=label,
        confidence=confidence,
        confidence_calibrated=confidence_calibrated,
    )


def calibrate_score(score: float, speaker_f0: float | None = None) -> float:
    """Dịch ngưỡng theo F0: giọng trầm (F0 < 130 Hz) được nới ngưỡng để chống False Positive.
    
    Chỉ dùng cho UI/bot cảnh báo ứng dụng thực tế, không ảnh hưởng đến metric học thuật gốc.
    """
    if speaker_f0 is None or speaker_f0 <= 0:
        return score
    # F0 càng thấp, ngưỡng càng hạ (dễ nhận bona fide hơn), tối đa bù 2.0
    offset = max(0.0, (130.0 - speaker_f0) / 130.0) * 2.0
    return score + offset
