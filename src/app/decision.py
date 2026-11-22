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
    is_borderline: bool = False
    risk_level: str = "NORMAL"


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


# Temperature Scaling parameter calibrated for AM-Softmax logit range [-50, +50]
T_CALIB: float = 16.0
PLATT_SCALE_K: float = 1.0 / T_CALIB  # k_eff = 0.0625, eliminates premature 99.9% saturation

# Margin around threshold requiring forensic audit and uncertainty warning
BORDERLINE_THRESHOLD: float = 8.0


def platt_calibrator(
    raw_score: float,
    threshold: float = 0.0,
    window_scores: list[float] | np.ndarray | None = None,
) -> float:
    """Calculate calibrated posterior probability of the predicted class using Platt Scaling & Temperature Scaling.

    Fitted for AM-Softmax logit scale [-50, +50] with temperature T_calib = 16.0 (k_eff = 0.0625).
    Guarantees:
      - At raw_score == threshold: confidence is exactly 50.0%.
      - Near threshold (|raw_score - threshold| <= 8.0): confidence remains bounded in [50%, 75%].
      - Moderate logits (+10 to +30) do not prematurely saturate to 99.9%.
      - Only very strong logits (|raw_score - threshold| >= 40.0) reach high confidence (> 92-95%).
      - Multi-window variance penalty: if window_scores has std > 6.0, discounts confidence towards 0.50.
    """
    diff = float(raw_score - threshold)
    prob_bona = 1.0 / (1.0 + float(np.exp(-PLATT_SCALE_K * diff)))
    conf = prob_bona if diff >= 0 else (1.0 - prob_bona)

    # Multi-window uncertainty penalty: discount confidence when inter-window variance is high
    if window_scores is not None and len(window_scores) > 1:
        w_arr = np.asarray(window_scores, dtype=np.float64)
        w_std = float(np.std(w_arr))
        if w_std > 6.0:
            penalty = (w_std - 6.0) * 0.02
            conf = max(0.50, conf - penalty)

    return float(max(0.50, min(0.9990, conf)))


def classify_score(
    raw_score: float,
    threshold: float = 0.0,
    calibrator: Callable[..., float] | None = platt_calibrator,
    window_scores: list[float] | np.ndarray | None = None,
) -> DecisionResult:
    """Classify a raw model score using a configured threshold and calibrator.

    STUBBORN_FACT: Raw model score >= threshold is classified as BONA_FIDE (label 1),
    otherwise SPOOF (label 0).
    Defaults to platt_calibrator (Temperature Scaling T=16.0, k_eff=0.0625).
    Sets is_borderline=True and risk_level='BORDERLINE' when |raw_score - threshold| <= 8.0.
    """
    is_bonafide = bool(raw_score >= threshold)
    prediction = "BONA_FIDE" if is_bonafide else "SPOOF"
    label = 1 if is_bonafide else 0

    diff = abs(float(raw_score - threshold))
    is_borderline = bool(diff <= BORDERLINE_THRESHOLD)
    risk_level = "BORDERLINE" if is_borderline else "NORMAL"

    if calibrator is not None:
        try:
            conf_val = float(calibrator(raw_score, threshold, window_scores=window_scores))
        except TypeError:
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
        is_borderline=is_borderline,
        risk_level=risk_level,
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
