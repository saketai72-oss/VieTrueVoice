"""Shared decision and calibration logic for ViTrueVoice inference endpoints."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, NamedTuple
import numpy as np
import torch


@dataclass(frozen=True)
class DecisionResult:
    raw_score: float
    threshold: float
    is_bonafide: bool
    prediction: str  # "BONA_FIDE" or "SPOOF"
    label: int       # 1 or 0
    confidence: float | None
    confidence_calibrated: bool


class CalibrationResult(NamedTuple):
    """Container for speaker enrollment calibration outcome and safety guardrail."""
    calibrated_score: float
    calibrated: bool
    offset: float
    raw_score: float
    reason: str


def derive_threshold(
    scores_bona: list[float] | np.ndarray | torch.Tensor,
    bpcer_budget: float = 0.005,
) -> float:
    """Derive decision threshold from bona fide score distribution under BPCER budget constraint.

    Args:
        scores_bona: Sequence or array of bona fide evaluation scores.
        bpcer_budget: False rejection rate target, strictly in (0.0, 1.0). Default 0.005 (0.5%).

    Returns:
        Score threshold corresponding to the bpcer_budget percentile.

    Raises:
        ValueError: If scores_bona is empty or bpcer_budget is outside (0.0, 1.0).
    """
    if scores_bona is None:
        raise ValueError("Cannot derive threshold from empty scores")

    if isinstance(scores_bona, torch.Tensor):
        if scores_bona.numel() == 0:
            raise ValueError("Cannot derive threshold from empty scores")
        scores_arr = scores_bona.detach().cpu().numpy().reshape(-1)
    else:
        scores_arr = np.asarray(scores_bona, dtype=np.float64).reshape(-1)
        if scores_arr.size == 0:
            raise ValueError("Cannot derive threshold from empty scores")

    if not (0.0 < bpcer_budget < 1.0):
        raise ValueError(
            f"bpcer_budget must be in range (0.0, 1.0), got {bpcer_budget}"
        )

    percentile = bpcer_budget * 100.0
    return float(np.percentile(scores_arr, percentile))


def calibrate_by_enrollment(
    score: float,
    enroll_scores: list[float] | np.ndarray | torch.Tensor,
    dev_median: float,
    dev_iqr: float,
    max_iqr_factor: float = 4.0,
) -> CalibrationResult:
    """Calibrate decision score using speaker enrollment reference distribution.

    Args:
        score: Raw prediction score for the evaluation utterance.
        enroll_scores: Bona fide enrollment scores from the enrolled speaker (>= 3 samples).
        dev_median: Median score of bona fide utterances on development set.
        dev_iqr: Interquartile range (IQR = Q75 - Q25) of bona fide utterances on dev set.
        max_iqr_factor: Safety multiplier bounding allowable shift before refusing calibration.

    Returns:
        CalibrationResult containing calibrated_score, calibrated status, offset, raw_score, and reason.
    """
    if isinstance(enroll_scores, torch.Tensor):
        enroll_arr = enroll_scores.detach().cpu().numpy().reshape(-1)
    else:
        enroll_arr = np.asarray(enroll_scores, dtype=np.float64).reshape(-1)

    if len(enroll_arr) < 3:
        return CalibrationResult(
            calibrated_score=float(score),
            calibrated=False,
            offset=0.0,
            raw_score=float(score),
            reason="Insufficient enrollment samples (< 3)",
        )

    if dev_iqr <= 0.0:
        return CalibrationResult(
            calibrated_score=float(score),
            calibrated=False,
            offset=0.0,
            raw_score=float(score),
            reason="Invalid or degenerate dev_iqr (<= 0)",
        )

    offset = float(np.median(enroll_arr) - dev_median)

    if abs(offset) > max_iqr_factor * dev_iqr:
        return CalibrationResult(
            calibrated_score=float(score),
            calibrated=False,
            offset=offset,
            raw_score=float(score),
            reason=f"Guardrail exceeded: offset {offset:+.2f} exceeds {max_iqr_factor} IQR",
        )

    calibrated_score = float(score - offset)
    return CalibrationResult(
        calibrated_score=calibrated_score,
        calibrated=True,
        offset=offset,
        raw_score=float(score),
        reason="Enrollment calibration applied successfully",
    )


# Empirically fitted Platt Scaling parameter on 11,450 Zalo development utterances (out/dev_zalo_scores_b_zalo.csv)
PLATT_SCALE_K: float = 0.3569


def platt_calibrator(raw_score: float, threshold: float = 0.0) -> float:
    """Calculate calibrated posterior probability of the predicted class using Platt Scaling.

    Trained on 11,450 development set utterances (out/dev_zalo_scores_b_zalo.csv).
    Guarantees:
      - At raw_score == threshold: confidence is 50.0%.
      - raw_score > threshold: returns P(bona_fide) in [0.50, 1.00).
      - raw_score < threshold: returns P(spoof) in [0.50, 1.00).
    """
    diff = float(raw_score - threshold)
    prob_bona = 1.0 / (1.0 + float(np.exp(-PLATT_SCALE_K * diff)))
    conf = prob_bona if diff >= 0 else (1.0 - prob_bona)
    return float(max(0.50, min(0.9990, conf)))


def classify_score(
    raw_score: float,
    threshold: float = 0.0,
    calibrator: Callable[..., float] | None = None,
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
        try:
            conf_val = float(calibrator(raw_score, threshold))
        except TypeError:
            conf_val = float(calibrator(raw_score))
        confidence = float(max(0.0001, min(0.9999, conf_val)))
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
