"""Fast in-memory acoustic & neural forensics extraction for ViTrueVoice API.

Zero disk writes; executes on CPU in < 20ms for standard 4-10s speech clips.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.app.decision import BORDERLINE_THRESHOLD, PLATT_SCALE_K, T_CALIB

DEFAULT_WIN_SAMPLES = 64000
DEFAULT_HOP_SAMPLES = 16000
DEFAULT_MAX_WINDOWS = 5
MAX_WAVEFORM_POINTS = 240
MEL_BINS = 48
MAX_MEL_FRAMES = 96
MEL_FMAX_HZ = 8000


def _estimate_f0_hz(y: np.ndarray, sr: int) -> float:
    """Fast FFT-accelerated YIN F0 estimator (Hz); returns 0.0 on silence/unvoiced/short audio."""
    n = int(y.size)
    if n < 512 or sr <= 0:
        return 0.0

    g_rms = float(np.sqrt(np.mean(y * y)))
    if g_rms < 1e-4:
        return 0.0

    fmin, fmax = 60.0, 450.0
    tau_min = max(2, int(sr / fmax))
    frame_len = min(1024, n)
    tau_max = min(int(sr / fmin), frame_len - 32)
    if tau_max <= tau_min:
        return 0.0

    w = frame_len - tau_max
    n_fft = 1 << (frame_len * 2 - 1).bit_length()

    n_frames = min(8, max(1, (n - frame_len) // max(1, frame_len // 2) + 1))
    starts = np.linspace(0, max(0, n - frame_len), n_frames, dtype=int)

    f0_vals: list[float] = []
    for s in starts:
        frame = y[s : s + frame_len].astype(np.float64, copy=False)
        f_rms = float(np.sqrt(np.mean(frame * frame)))
        if f_rms < 0.25 * g_rms or f_rms < 1e-4:
            continue

        frame = frame - np.mean(frame)
        sq = frame * frame
        cs = np.empty(frame_len + 1, dtype=np.float64)
        cs[0] = 0.0
        np.cumsum(sq, out=cs[1:])

        energy_0 = cs[w]
        energy_tau = cs[w : w + tau_max + 1] - cs[: tau_max + 1]

        spec_a = np.fft.rfft(frame[:w], n=n_fft)
        spec_b = np.fft.rfft(frame, n=n_fft)
        xcorr = np.fft.irfft(np.conj(spec_a) * spec_b, n=n_fft)[: tau_max + 1]

        diff = np.maximum(0.0, energy_0 + energy_tau - 2.0 * xcorr)
        cmndf = np.ones(tau_max + 1, dtype=np.float64)
        running_sum = np.cumsum(diff[1:])
        lags = np.arange(1, tau_max + 1, dtype=np.float64)
        valid = running_sum > 1e-12
        cmndf[1:][valid] = diff[1:][valid] * lags[valid] / running_sum[valid]

        seg = cmndf[tau_min : tau_max + 1]
        below = np.flatnonzero(seg < 0.20)
        if below.size > 0:
            idx = int(below[0])
            while idx + 1 < seg.size and seg[idx + 1] < seg[idx]:
                idx += 1
        else:
            idx = int(np.argmin(seg))
            if seg[idx] >= 0.35:
                continue

        tau = tau_min + idx
        tau_interp = float(tau)
        if tau_min < tau < tau_max:
            y0, y1, y2 = cmndf[tau - 1], cmndf[tau], cmndf[tau + 1]
            denom = y0 - 2.0 * y1 + y2
            if abs(denom) > 1e-12:
                tau_interp = float(tau) + 0.5 * (y0 - y2) / denom

        if tau_interp > 0.0:
            f0 = sr / tau_interp
            if fmin <= f0 <= fmax:
                f0_vals.append(f0)

    if not f0_vals:
        return 0.0
    return round(float(np.median(f0_vals)), 1)


def _describe_pooling(scores_list: list[float], pooling_mode: str) -> dict[str, Any]:
    """Mirror Consensus Asymmetric Veto branching from src/preprocessing/pooling.py."""
    mode = pooling_mode or "asymmetric_veto"
    if not scores_list:
        return {
            "mode": mode,
            "veto_triggered": False,
            "branch": "max_default",
            "explanation": "Không có dữ liệu điểm cửa sổ để tổng hợp.",
        }

    arr = np.asarray(scores_list, dtype=np.float64)
    min_s = float(np.min(arr))
    k = int(arr.size)

    if mode in ("asymmetric_veto", "adaptive"):
        if k >= 3 and min_s < -12.0:
            sorted_s = np.sort(arr)
            second_best = float(sorted_s[-2])
            if second_best >= 6.0:
                return {
                    "mode": mode,
                    "veto_triggered": False,
                    "branch": "consensus_rescue",
                    "explanation": (
                        f"Phát hiện cửa sổ bất thường ({min_s:+.2f} < -12.0), nhưng ≥ 2 cửa sổ "
                        f"đồng thuận giọng thật (nhì cao nhất {second_best:+.2f} ≥ +6.0) → "
                        "kích hoạt Cứu hộ Đồng thuận (Consensus Rescue)."
                    ),
                }
            return {
                "mode": mode,
                "veto_triggered": True,
                "branch": "asymmetric_veto_trimmed_mean",
                "explanation": (
                    f"Kích hoạt Phủ quyết Bất đối xứng (min = {min_s:+.2f} < -12.0, cửa sổ "
                    f"nhì cao nhất {second_best:+.2f} < +6.0) → loại bỏ đỉnh cao nhất và lấy "
                    "trung bình cắt ngọn để chặn giọng giả."
                ),
            }
        if k == 2 and min_s < -12.0:
            return {
                "mode": mode,
                "veto_triggered": True,
                "branch": "asymmetric_veto_mean",
                "explanation": (
                    f"Kích hoạt Phủ quyết Bất đối xứng trên 2 cửa sổ (min = {min_s:+.2f} < -12.0) "
                    "→ lấy trung bình 2 cửa sổ để ngăn điểm giả mạo lọt lưới."
                ),
            }
        return {
            "mode": mode,
            "veto_triggered": False,
            "branch": "max_default",
            "explanation": (
                f"Không phát hiện bằng chứng giả mạo mạnh (min = {min_s:+.2f} ≥ -12.0) "
                "→ áp dụng Max-Pooling bảo vệ giọng người thật."
                if min_s >= -12.0
                else f"Âm thanh chỉ có 1 cửa sổ ({min_s:+.2f}) → dùng trực tiếp điểm cửa sổ duy nhất."
            ),
        }

    return {
        "mode": mode,
        "veto_triggered": False,
        "branch": f"{mode}_default",
        "explanation": f"Tổng hợp đa cửa sổ theo chế độ {mode}.",
    }


def _compute_window_spans(
    n_samples: int,
    sr: int,
    n_scores: int,
    win: int = DEFAULT_WIN_SAMPLES,
    hop: int = DEFAULT_HOP_SAMPLES,
    max_windows: int = DEFAULT_MAX_WINDOWS,
) -> list[tuple[float, float]]:
    """Compute (start_sec, end_sec) matching src.preprocessing.pooling.extract_window_batch."""
    if n_scores <= 0:
        return []
    dur = float(n_samples / sr) if sr > 0 else 0.0

    starts: list[int]
    if n_samples < win:
        if n_samples >= 50000 and n_scores == 2:
            starts = [0, 8000]
        else:
            starts = [0]
    else:
        starts = list(range(0, n_samples - win + 1, hop))
        if starts[-1] + win < n_samples:
            starts.append(n_samples - win)
        if len(starts) < 2 and n_samples >= 50000:
            starts.append(min(hop, 8000))
        if len(starts) > max_windows:
            idx = np.linspace(0, len(starts) - 1, max_windows, dtype=int)
            starts = [starts[i] for i in idx]

    if len(starts) == n_scores:
        return [
            (round(s / sr, 2), round(min(dur, (s + win) / sr), 2) if n_samples >= win else round(dur, 2))
            for s in starts
        ]

    # Fallback when caller passes an explicit window_scores count not tied to signal length
    spans: list[tuple[float, float]] = []
    for i in range(n_scores):
        s_sec = round(min(dur, (i * hop) / sr), 2)
        e_sec = round(min(dur, s_sec + win / sr), 2) if dur > 0 else 0.0
        spans.append((s_sec, e_sec))
    return spans


def _compute_waveform(y: np.ndarray) -> list[float]:
    """Peak-preserving signed downsampling to at most 240 points in [-1.0, 1.0]."""
    n = int(y.size)
    if n == 0:
        return []
    if n <= MAX_WAVEFORM_POINTS:
        return [round(float(np.clip(v, -1.0, 1.0)), 4) for v in y.tolist()]

    chunk = n // MAX_WAVEFORM_POINTS
    blocks = y[: MAX_WAVEFORM_POINTS * chunk].reshape(MAX_WAVEFORM_POINTS, chunk)
    peak_idx = np.argmax(np.abs(blocks), axis=1)
    sampled = blocks[np.arange(MAX_WAVEFORM_POINTS), peak_idx]
    return [round(float(np.clip(v, -1.0, 1.0)), 4) for v in sampled.tolist()]


def _compute_mel_spectrogram(y: np.ndarray, sr: int) -> dict[str, Any]:
    """Compute compact uint8 [48][<=96] Mel-Spectrogram (0..255) for canvas heatmap."""
    empty = {
        "n_mels": MEL_BINS,
        "n_frames": 1,
        "fmax": MEL_FMAX_HZ,
        "values": [[0] for _ in range(MEL_BINS)],
    }
    if y.size == 0 or float(np.max(np.abs(y))) < 1e-7 or sr <= 0:
        return empty

    try:
        import librosa

        y_mel = y
        if y_mel.size < 512:
            repeats = int(math.ceil(512 / y_mel.size))
            y_mel = np.tile(y_mel, repeats)[:512]

        n_fft = 1024 if y_mel.size >= 1024 else 512
        hop_length = max(128, int(y_mel.size) // MAX_MEL_FRAMES)
        fmax_eff = min(float(MEL_FMAX_HZ), sr / 2.0)

        spec = librosa.feature.melspectrogram(
            y=y_mel,
            sr=sr,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=MEL_BINS,
            fmax=fmax_eff,
        )
        if spec.size == 0 or float(np.max(spec)) <= 0.0:
            return empty

        if spec.shape[1] > MAX_MEL_FRAMES:
            col_idx = np.linspace(0, spec.shape[1] - 1, MAX_MEL_FRAMES, dtype=int)
            spec = spec[:, col_idx]

        spec_db = librosa.power_to_db(spec, ref=np.max, top_db=80.0)
        norm = np.clip((spec_db + 80.0) / 80.0, 0.0, 1.0) * 255.0
        values_u8 = np.rint(norm).astype(np.uint8)
        return {
            "n_mels": MEL_BINS,
            "n_frames": int(values_u8.shape[1]),
            "fmax": MEL_FMAX_HZ,
            "values": values_u8.tolist(),
        }
    except Exception:
        return empty


def extract_forensic_analysis(
    audio_data: np.ndarray,
    sr: int = 16000,
    window_scores: np.ndarray | list[float] | None = None,
    raw_score: float = 0.0,
    threshold: float = 0.0,
    pooling_mode: str = "asymmetric_veto",
) -> dict[str, Any]:
    """Extract real-time acoustic, spectral, pooling, and Platt forensic metrics in RAM."""
    y = np.asarray(audio_data, dtype=np.float32).reshape(-1)
    if y.size > 0:
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    sr_int = int(sr) if sr and sr > 0 else 16000
    n_samples = int(y.size)

    duration_sec = round(float(n_samples / sr_int), 2)
    rms_energy = round(float(np.sqrt(np.mean(y * y))), 5) if n_samples > 0 else 0.0
    peak_val = float(np.max(np.abs(y))) if n_samples > 0 else 0.0
    peak_db = round(float(20.0 * np.log10(max(peak_val, 1e-6))), 2)

    hf_ratio_pct = 0.0
    low_pct = 0.0
    mid_pct = 0.0
    high_pct = 0.0
    bandwidth_profile = "NARROWBAND_8KHZ"

    if n_samples >= 16 and peak_val > 1e-7:
        fft_mag = np.abs(np.fft.rfft(y))
        power = fft_mag * fft_mag
        total_power = float(np.sum(power))
        if total_power > 1e-12:
            freqs = np.fft.rfftfreq(n_samples, 1.0 / sr_int)
            hf_power = float(np.sum(power[freqs >= 4000.0]))
            hf_ratio_pct = round(hf_power / total_power * 100.0, 2)

            low_power = float(np.sum(power[freqs < 300.0]))
            high_power = float(np.sum(power[freqs >= 3400.0]))
            high_ratio_raw = high_power / total_power * 100.0
            bandwidth_profile = "NARROWBAND_8KHZ" if high_ratio_raw < 1.5 else "WIDEBAND_16KHZ"

            low_pct = round(low_power / total_power * 100.0, 2)
            high_pct = round(high_ratio_raw, 2)
            mid_pct = round(100.0 - low_pct - high_pct, 2)
            if mid_pct < 0.0:
                mid_pct = 0.0
                high_pct = round(100.0 - low_pct, 2)

    estimated_f0_hz = _estimate_f0_hz(y, sr_int)

    if window_scores is None:
        scores_list = [float(raw_score)]
    else:
        scores_list = [float(s) for s in np.asarray(window_scores, dtype=np.float64).reshape(-1).tolist()]

    spans = _compute_window_spans(n_samples, sr_int, len(scores_list))
    windows = []
    for idx, (s_val, (start_sec, end_sec)) in enumerate(zip(scores_list, spans)):
        z_risk = float(np.clip(0.3569 * (s_val - float(threshold)), -60.0, 60.0))
        risk_weight = round(1.0 / (1.0 + math.exp(z_risk)), 4)
        windows.append(
            {
                "index": idx + 1,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "score": round(s_val, 4),
                "risk_weight": risk_weight,
            }
        )

    pooling_info = _describe_pooling(scores_list, pooling_mode)

    diff = float(raw_score) - float(threshold)
    z_platt = float(np.clip(-PLATT_SCALE_K * diff, -60.0, 60.0))
    prob_bona = max(0.001, min(0.999, 1.0 / (1.0 + math.exp(z_platt))))
    prob_bona_pct = round(prob_bona * 100.0, 1)
    prob_spoof_pct = round((1.0 - prob_bona) * 100.0, 1)

    return {
        "duration_sec": duration_sec,
        "sample_rate": sr_int,
        "rms_energy": rms_energy,
        "peak_db": peak_db,
        "hf_ratio_pct": hf_ratio_pct,
        "estimated_f0_hz": estimated_f0_hz,
        "bandwidth_profile": bandwidth_profile,
        "band_energy_pct": {
            "low_0_300hz": low_pct,
            "mid_300_3400hz": mid_pct,
            "high_3400_8000hz": high_pct,
        },
        "pooling": pooling_info,
        "windows": windows,
        "waveform": _compute_waveform(y),
        "mel_spectrogram": _compute_mel_spectrogram(y, sr_int),
        "platt_curve": {
            "temperature": T_CALIB,
            "scale_k": PLATT_SCALE_K,
            "borderline_margin": BORDERLINE_THRESHOLD,
            "prob_bona_pct": prob_bona_pct,
            "prob_spoof_pct": prob_spoof_pct,
        },
    }
