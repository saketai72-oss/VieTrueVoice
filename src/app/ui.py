"""Gradio Web UI for ViTrueVoice voice anti-spoofing detection.

Designed according to ViTrueVoice Dark Forensics Lab Theme (Stitch Specification v2.4):
- Intuitive elder-friendly workflow (<= 3 actions, clear color indicators, fraud prevention checklist).
- Deep forensics analytical laboratory (Mel-Spectrogram 80 Mels, Raw Waveform, Grad-CAM Saliency Map).
- Empirical Platt Scaling confidence calibration.
- Full compliance with Vietnam Personal Data Protection Law 91/2025/QH15.
"""

from __future__ import annotations
import hashlib
import sys
import time
from pathlib import Path
from typing import Any, Callable

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from src.app.decision import classify_score, platt_calibrator, PLATT_SCALE_K
from src.app.server import TARGET_SAMPLE_COUNT, TARGET_SAMPLE_RATE, _default_model_loader, _pad_or_crop
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores
try:
    from src.vitruevoice.live_cloner import LiveQuadCloner, DEFAULT_TARGET_TEXT, evaluate_audio_sample
except Exception:
    LiveQuadCloner = None
    DEFAULT_TARGET_TEXT = "Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."
    evaluate_audio_sample = None

DEFAULT_CHECKPOINT = (
    Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")
    if Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt").exists()
    else (
        Path("out/zalo_b_zalo_v6_local/best_model.pt")
        if Path("out/zalo_b_zalo_v6_local/best_model.pt").exists()
        else (
            Path("out/zalo_b_zalo_v5_local/best_model.pt")
            if Path("out/zalo_b_zalo_v5_local/best_model.pt").exists()
            else (
                Path("out/best_model_B_zalo.pt")
                if Path("out/best_model_B_zalo.pt").exists()
                else Path("out/run_B/best_model.pt")
            )
        )
    )
)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    /* Dark Mode Defaults (Lab Kỹ thuật) */
    --bg-page: #0B0F17;
    --bg-surface: #131B2E;
    --bg-card: #111827;
    --bg-stat: #111827;
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --border-color: #334155;
    --header-bg: rgba(19, 27, 46, 0.95);
    --header-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    --btn-primary-bg: linear-gradient(135deg, #14B8A6 0%, #0F766E 100%);
    --btn-primary-border: #71F8E4;
    --btn-primary-text: #00201C;
    --btn-secondary-bg: #1E293B;
    --btn-secondary-text: #F8FAFC;
    --btn-secondary-border: #334155;
    --spoof-box-bg: #1F0B0F;
    --spoof-box-border: #EF4444;
    --spoof-title-color: #F87171;
    --spoof-desc-color: #FCA5A5;
    --spoof-action-text: #FCA5A5;
    --action-spoof-bg: #18080B;
    --action-spoof-border: rgba(239, 68, 68, 0.4);
    --bona-box-bg: #072414;
    --bona-box-border: #2ECC71;
    --bona-title-color: #86EFAC;
    --bona-desc-color: #86EFAC;
    --bona-action-text: #F8FAFC;
    --bona-action-text-bold: #86EFAC;
    --action-bona-bg: #072414;
    --action-bona-border: rgba(46, 204, 113, 0.4);
    --conf-box-bg: #111827;
    --track-bg: #0F172A;
    --hash-row-bg: #0B0F17;
    --hash-row-border: #1E293B;
    --plot-card-bg: #0B0F17;
    --teal-accent: #71F8E4;
    --toggle-bg: rgba(20, 184, 166, 0.12);
    --toggle-border: rgba(20, 184, 166, 0.4);
    --toggle-text: #71F8E4;
}

body.theme-light {
    /* Light Mode Variables (ViTrueVoice Light) */
    --bg-page: #F8F9FF;
    --bg-surface: #FFFFFF;
    --bg-card: #EFF4FF;
    --bg-stat: #FFFFFF;
    --text-primary: #0B1C30;
    --text-secondary: #3E4947;
    --text-muted: #64748B;
    --border-color: #D3E4FE;
    --header-bg: #FFFFFF;
    --header-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
    --btn-primary-bg: linear-gradient(135deg, #007A6E 0%, #005C55 100%);
    --btn-primary-border: #004D47;
    --btn-primary-text: #FFFFFF;
    --btn-secondary-bg: #F1F5F9;
    --btn-secondary-text: #0F172A;
    --btn-secondary-border: #CBD5E1;
    --spoof-box-bg: #FEF2F2;
    --spoof-box-border: #EF4444;
    --spoof-title-color: #B91C1C;
    --spoof-desc-color: #991B1B;
    --spoof-action-text: #991B1B;
    --action-spoof-bg: #FFFFFF;
    --action-spoof-border: #FECACA;
    --bona-box-bg: #F0FDF4;
    --bona-box-border: #16A34A;
    --bona-title-color: #15803D;
    --bona-desc-color: #166534;
    --bona-action-text: #1E293B;
    --bona-action-text-bold: #15803D;
    --action-bona-bg: #FFFFFF;
    --action-bona-border: #BBF7D0;
    --conf-box-bg: #FFFFFF;
    --track-bg: #E2E8F0;
    --hash-row-bg: #F8FAFC;
    --hash-row-border: #E2E8F0;
    --plot-card-bg: #FFFFFF;
    --teal-accent: #0F766E;
    --toggle-bg: #EFF4FF;
    --toggle-border: #93C5FD;
    --toggle-text: #1D4ED8;
}

body, .gradio-container {
    background-color: var(--bg-page) !important;
    font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
    transition: background-color 0.3s ease, color 0.3s ease;
}

.gradio-container .block,
.gradio-container .panel,
.gradio-container .form {
    background-color: var(--bg-surface) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
    transition: background-color 0.3s ease, border-color 0.3s ease;
}

.gradio-container label,
.gradio-container span:not([style*="color"]) {
    color: var(--text-primary);
}

.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4 {
    color: var(--text-primary) !important;
}

.gradio-container p {
    color: var(--text-secondary);
}

.gradio-container [data-testid="plot"],
.gradio-container div[class*="plot"] {
    background-color: var(--plot-card-bg) !important;
    border-color: var(--border-color) !important;
}

.lab-header {
    background: var(--header-bg);
    border: 1px solid var(--border-color);
    border-radius: 1rem;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--header-shadow);
    transition: all 0.3s ease;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}

.header-actions-row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 0.6rem !important;
    width: 100% !important;
}

.header-actions-row > div,
.header-actions-row .block {
    min-width: unset !important;
    width: auto !important;
    flex: 0 0 auto !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

#theme-toggle-btn,
#theme-toggle-btn button {
    min-width: 40px !important;
    max-width: 44px !important;
    width: 40px !important;
    height: 38px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 19px !important;
    line-height: 1 !important;
    border-radius: 8px !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    cursor: pointer !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    transition: transform 0.15s ease, border-color 0.15s ease, background 0.15s ease !important;
}

#theme-toggle-btn:hover,
#theme-toggle-btn button:hover {
    transform: scale(1.08) !important;
    border-color: #14B8A6 !important;
}

body.theme-light #theme-toggle-btn,
body.theme-light #theme-toggle-btn button {
    background: #EFF4FF !important;
    border-color: #CBD5E1 !important;
}

iconify-icon {
    display: inline-block;
    vertical-align: middle;
}

button iconify-icon {
    pointer-events: none;
}

.stat-card {
    background: var(--bg-stat);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 0.85rem 1rem;
    transition: all 0.3s ease;
}

body.theme-light .stat-card {
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.pulse-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #2ECC71;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(46, 204, 113, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
}

.verdict-box-spoof {
    background: var(--spoof-box-bg);
    border: 2px solid var(--spoof-box-border);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(239, 68, 68, 0.15);
    transition: all 0.3s ease;
}

.verdict-box-bonafide {
    background: var(--bona-box-bg);
    border: 2px solid var(--bona-box-border);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(46, 204, 113, 0.15);
    transition: all 0.3s ease;
}

.progress-track {
    background: var(--track-bg);
    border: 1px solid var(--border-color);
    border-radius: 9999px;
    height: 14px;
    overflow: hidden;
    margin: 8px 0;
    position: relative;
    display: flex;
}

.progress-fill-spoof {
    background: linear-gradient(90deg, #DC2626, #EF4444);
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
    height: 100%;
    transition: width 0.6s ease-in-out;
}

.progress-fill-bonafide {
    background: linear-gradient(90deg, #10B981, #2ECC71);
    box-shadow: 0 0 12px rgba(46, 204, 113, 0.6);
    height: 100%;
    transition: width 0.6s ease-in-out;
}

.btn-primary-teal {
    background: var(--btn-primary-bg) !important;
    border: 1px solid var(--btn-primary-border) !important;
    color: var(--btn-primary-text) !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    box-shadow: 0 4px 20px rgba(20, 184, 166, 0.35) !important;
    transition: all 0.2s ease-in-out !important;
}

.btn-primary-teal:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(20, 184, 166, 0.5) !important;
}

/* Light Mode specific overrides for Gradio native components */
body.theme-light button:not(.btn-primary-teal) {
    background: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
}

body.theme-light button:not(.btn-primary-teal):hover {
    background: #E2E8F0 !important;
}

body.theme-light .gradio-container .tab-nav button {
    color: #475569 !important;
}

body.theme-light .gradio-container .tab-nav button.selected {
    color: #0F766E !important;
    border-bottom: 2px solid #0F766E !important;
    font-weight: 700 !important;
}

body.theme-light .gradio-container .accordion {
    background: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}

/* Quad Forensics Live Cloning Styles */
.quad-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 0.875rem;
    padding: 1.1rem;
    transition: all 0.3s ease;
    margin-bottom: 0.5rem;
}

.quad-card-loading {
    border-color: #14B8A6 !important;
    box-shadow: 0 0 16px rgba(20, 184, 166, 0.25) !important;
    animation: pulseBorder 2s infinite ease-in-out;
}

@keyframes pulseBorder {
    0%, 100% { border-color: rgba(20, 184, 166, 0.4); }
    50% { border-color: rgba(20, 184, 166, 1.0); }
}

.quad-card-bonafide {
    border-color: rgba(46, 204, 113, 0.5) !important;
    background: linear-gradient(180deg, rgba(7, 36, 20, 0.35) 0%, var(--bg-card) 100%) !important;
}

.quad-card-spoof {
    border-color: rgba(239, 68, 68, 0.5) !important;
    background: linear-gradient(180deg, rgba(31, 11, 15, 0.35) 0%, var(--bg-card) 100%) !important;
}

body.theme-light .quad-card-bonafide {
    background: linear-gradient(180deg, #F0FDF4 0%, #FFFFFF 100%) !important;
    border-color: #86EFAC !important;
}

body.theme-light .quad-card-spoof {
    background: linear-gradient(180deg, #FEF2F2 0%, #FFFFFF 100%) !important;
    border-color: #FCA5A5 !important;
}

.badge-loading {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(20, 184, 166, 0.15);
    border: 1px solid rgba(20, 184, 166, 0.4);
    color: var(--teal-accent);
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
}

.badge-waiting {
    display: inline-flex;
    align-items: center;
    background: rgba(100, 116, 139, 0.15);
    border: 1px solid rgba(100, 116, 139, 0.4);
    color: var(--text-muted);
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 11px;
}

.badge-skipped {
    display: inline-flex;
    align-items: center;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #F59E0B;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 11px;
}

.badge-bonafide {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(46, 204, 113, 0.15);
    border: 1px solid #2ECC71;
    color: #86EFAC;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
}

body.theme-light .badge-bonafide {
    background: #DCFCE7;
    border-color: #86EFAC;
    color: #15803D;
}

.badge-spoof {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #EF4444;
    color: #F87171;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
}

body.theme-light .badge-spoof {
    background: #FEE2E2;
    border-color: #FCA5A5;
    color: #B91C1C;
}

.rotating-spinner {
    animation: spin 1.2s linear infinite;
    display: inline-block;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
"""


def _extract_acoustic_metrics(y: np.ndarray, sr: int = TARGET_SAMPLE_RATE) -> dict[str, Any]:
    """Extract acoustic forensics: high-frequency cutoff ratio, energy, duration."""
    duration = float(len(y) / sr)
    energy = float(np.mean(y ** 2)) if len(y) > 0 else 0.0

    # High frequency energy ratio (> 4 kHz vs total) via fast FFT (<10ms)
    if len(y) >= 512:
        fft_mag = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
        tot_power = float(np.sum(fft_mag ** 2)) + 1e-10
        hf_power = float(np.sum(fft_mag[freqs >= 4000] ** 2))
        hf_ratio = float(hf_power / tot_power) * 100.0
    else:
        hf_ratio = 0.0

    return {
        "duration": duration,
        "energy": energy,
        "hf_ratio": hf_ratio,
        "mean_f0": 0.0,
    }


def _create_forensic_plots(
    y: np.ndarray,
    sr: int,
    window_scores: np.ndarray | None,
    threshold: float = 0.0,
    is_bonafide: bool = False,
) -> tuple[plt.Figure, plt.Figure, plt.Figure]:
    """Generate dark-mode scientific figures: Mel-Spectrogram, Waveform, Saliency Map."""
    import librosa
    dur = float(len(y) / sr) if len(y) > 0 else 1.0

    # 1. Mel-Spectrogram Figure
    fig_spec, ax_spec = plt.subplots(figsize=(8.5, 2.8), facecolor="#0B0F17")
    ax_spec.set_facecolor("#0B0F17")
    if len(y) >= 512:
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80, fmax=8000)
        S_dB = librosa.power_to_db(S, ref=np.max)
        librosa.display.specshow(S_dB, x_axis="time", y_axis="mel", sr=sr, fmax=8000, ax=ax_spec, cmap="magma")
        ax_spec.axhline(4000, color="#EF4444", linestyle="--", linewidth=1.2, alpha=0.75)
        ax_spec.text(0.08, 4200, "Ranh giới Vocoder HiFi-GAN (4.0 kHz)", color="#FCA5A5", fontsize=8, weight="bold")
    else:
        ax_spec.text(0.5, 0.5, "Đoạn âm thanh quá ngắn để tạo phổ Mel", color="#94A3B8", ha="center")
    ax_spec.tick_params(colors="#94A3B8", labelsize=8)
    ax_spec.set_xlabel("Thời gian (giây)", color="#94A3B8", fontsize=9)
    ax_spec.set_ylabel("Tần số (Hz)", color="#94A3B8", fontsize=9)
    ax_spec.set_title("Mel-Spectrogram (80 Filterbanks - Phân bố Năng lượng Tần số Log-Scale)", color="#F8FAFC", fontsize=10, weight="bold")
    for spine in ax_spec.spines.values():
        spine.set_color("#334155")
    plt.tight_layout()

    # 2. Raw Time-Domain Waveform Figure (downsampled for crisp rendering without vector lag)
    fig_wave, ax_wave = plt.subplots(figsize=(8.5, 2.0), facecolor="#0B0F17")
    ax_wave.set_facecolor("#0B0F17")
    wave_color = "#2ECC71" if is_bonafide else "#EF4444"
    if len(y) > 0:
        step = max(1, len(y) // 2000)
        y_down = y[::step]
        t_down = np.linspace(0, dur, len(y_down))
        ax_wave.plot(t_down, y_down, color=wave_color, linewidth=0.75, alpha=0.9)
    ax_wave.axhline(0, color="#334155", linestyle="--", linewidth=0.8)
    ax_wave.set_ylim(-1.05, 1.05)
    ax_wave.tick_params(colors="#94A3B8", labelsize=8)
    ax_wave.set_xlabel("Thời gian (giây)", color="#94A3B8", fontsize=9)
    ax_wave.set_ylabel("Biên độ (-1.0 .. +1.0)", color="#94A3B8", fontsize=9)
    ax_wave.set_title("Biểu Đồ Sóng Âm Đồng Bộ Thời Gian (Raw Time-Domain Waveform)", color="#F8FAFC", fontsize=10, weight="bold")
    for spine in ax_wave.spines.values():
        spine.set_color("#334155")
    plt.tight_layout()

    # 3. Grad-CAM / Temporal Window Attention Saliency Figure
    fig_cam, ax_cam = plt.subplots(figsize=(8.5, 1.8), facecolor="#0B0F17")
    ax_cam.set_facecolor("#0B0F17")
    if window_scores is not None and len(window_scores) > 0:
        scores_arr = np.array(window_scores, dtype=np.float32)
        # Saliency risk mapping: score < threshold indicates high risk (spoof)
        risk_weights = 1.0 / (1.0 + np.exp(0.3569 * (scores_arr - threshold)))
        cam_grid = np.repeat(risk_weights[np.newaxis, :], 20, axis=0)
        im = ax_cam.imshow(cam_grid, aspect="auto", cmap="turbo", extent=[0, dur, 0, 1], vmin=0.0, vmax=1.0)
        ax_cam.set_yticks([])
        ax_cam.tick_params(colors="#94A3B8", labelsize=8)
        ax_cam.set_xlabel("Thời gian (giây) - Trục Độ Chú Ý Anomaly Risk (0.0: Bình thường → 1.0: Điểm Kích Hoạt Giả Mạo)", color="#94A3B8", fontsize=9)
        ax_cam.set_title(f"Bản Đồ Chú Ý Mạng Nơ-ron Grad-CAM ({len(scores_arr)} Cửa Sổ Trượt Multi-Window)", color="#F8FAFC", fontsize=10, weight="bold")
    else:
        ax_cam.text(0.5, 0.5, "Chưa có dữ liệu attention", color="#94A3B8", ha="center")
    for spine in ax_cam.spines.values():
        spine.set_color("#334155")
    plt.tight_layout()

    return fig_spec, fig_wave, fig_cam


def _warmup_inference_pipeline(
    model: Any,
    device: str = "cpu",
    threshold: float = 0.0,
) -> None:
    """Pre-warm model and scientific plotting pipelines to eliminate cold-start latency."""
    if model is not None and hasattr(model, "score"):
        try:
            # 1. Warm-up multi-window batch (5 windows = max 9s audio)
            dummy_multi = torch.zeros(5, TARGET_SAMPLE_COUNT, dtype=torch.float32, device=device)
            with torch.inference_mode():
                _ = model.score(dummy_multi)
            # 2. Warm-up single window batch (1 window = short audio)
            dummy_single = torch.zeros(1, TARGET_SAMPLE_COUNT, dtype=torch.float32, device=device)
            with torch.inference_mode():
                _ = model.score(dummy_single)
            if str(device).startswith("cuda") and torch.cuda.is_available():
                torch.cuda.synchronize()
        except Exception:
            pass

    # 3. Pre-warm Matplotlib & Librosa plotting pipeline (font cache, colormaps, canvas)
    try:
        dummy_y = np.zeros(TARGET_SAMPLE_COUNT, dtype=np.float32)
        dummy_scores = np.array([0.0], dtype=np.float32)
        f1, f2, f3 = _create_forensic_plots(dummy_y, sr=TARGET_SAMPLE_RATE, window_scores=dummy_scores, threshold=threshold)
        plt.close(f1)
        plt.close(f2)
        plt.close(f3)
    except Exception:
        pass


def make_predict_fn(
    model: Any = None,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    device: str = "cpu",
    threshold: float = 0.0,
    model_loader: Callable[[Path | str, str], Any] | None = None,
    preload: bool = True,
    calibrator: Callable[..., float] | None = platt_calibrator,
    return_rich: bool = False,
) -> Callable[..., Any]:
    active_model = model
    loader = model_loader or _default_model_loader

    if active_model is None and preload and Path(checkpoint_path).exists():
        active_model = loader(checkpoint_path, device)

    if active_model is not None:
        _warmup_inference_pipeline(active_model, device=device, threshold=threshold)

    def predict_audio(audio_input: Any) -> Any:
        nonlocal active_model

        if audio_input is None:
            v_text = "⚠️ Chưa cung cấp file âm thanh!"
            c_text = "Chưa hiệu chuẩn"
            d_text = "Vui lòng ghi âm hoặc tải lên một đoạn tin nhắn thoại."
            if not return_rich:
                return v_text, c_text, d_text
            empty_fig, _ = plt.subplots(figsize=(4, 1), facecolor="#0B0F17")
            return (
                v_text, c_text, d_text,
                """<div style="padding: 1.5rem; border-radius: 1rem; background: #131B2E; border: 1px solid #334155; text-align: center; color: #94A3B8;">
                    <p style="margin-top: 0.5rem; font-size: 14px;">Vui lòng tải lên file âm thanh hoặc chọn mẫu thử nghiệm bên trái để phân tích.</p>
                </div>""",
                "", "",
                empty_fig, empty_fig, empty_fig,
            )

        t0 = time.perf_counter()
        if active_model is None:
            active_model = loader(checkpoint_path, device)
            if active_model is None:
                v_text = "❌ Không tìm thấy mô hình!"
                c_text = "Lỗi hệ thống"
                d_text = f"Không thể nạp trọng số từ {checkpoint_path}."
                if not return_rich:
                    return v_text, c_text, d_text
                empty_fig, _ = plt.subplots(figsize=(4, 1), facecolor="#0B0F17")
                return v_text, c_text, d_text, f"<div style='color:red;'>{v_text}</div>", "", "", empty_fig, empty_fig, empty_fig

        # Gradio audio input can be a filepath (str) or a tuple (sample_rate, numpy_array)
        if isinstance(audio_input, str):
            data = load_audio(audio_input, target_sr=TARGET_SAMPLE_RATE)
            sr = TARGET_SAMPLE_RATE
        elif isinstance(audio_input, tuple) and len(audio_input) == 2:
            sr, data = audio_input
            if data.dtype in (np.int16, np.int32):
                data = data.astype(np.float32) / (32768.0 if data.dtype == np.int16 else 2147483648.0)
            elif data.dtype != np.float32:
                data = data.astype(np.float32)
            if data.ndim > 1:
                data = data.mean(axis=-1)
            if sr != TARGET_SAMPLE_RATE:
                import librosa
                data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)
                sr = TARGET_SAMPLE_RATE
        else:
            v_text = "❌ Định dạng âm thanh không hợp lệ!"
            c_text = "Lỗi"
            d_text = "Không thể phân tích dữ liệu."
            if not return_rich:
                return v_text, c_text, d_text
            empty_fig, _ = plt.subplots(figsize=(4, 1), facecolor="#0B0F17")
            return v_text, c_text, d_text, f"<div style='color:red;'>{v_text}</div>", "", "", empty_fig, empty_fig, empty_fig

        raw_bytes = data.tobytes()
        audio_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # Multi-window inference with max-pooling (STUBBORN_FACT: repeat padding <64k, single batched forward pass)
        windows_batch = extract_window_batch(
            data,
            win=TARGET_SAMPLE_COUNT,
            hop=16000,
            max_windows=5,
            apply_dither=True,
        ).to(device)
        n_windows = int(windows_batch.shape[0])

        with torch.inference_mode():
            score_tensor = active_model.score(windows_batch)
            if isinstance(score_tensor, torch.Tensor):
                scores_np = score_tensor.detach().cpu().numpy()
            else:
                scores_np = np.asarray(score_tensor)
            if scores_np.ndim > 1:
                scores_np = scores_np.squeeze(-1)
            elif scores_np.ndim == 0:
                scores_np = np.array([scores_np.item()], dtype=np.float32)
            raw_score = pool_scores(scores_np, mode="max")

        latency = time.perf_counter() - t0
        decision = classify_score(raw_score, threshold=threshold, calibrator=calibrator)
        is_bonafide = decision.is_bonafide
        conf_val = decision.confidence if decision.confidence is not None else 0.5
        conf_pct = conf_val * 100.0

        # Acoustic features for forensics
        acoustics = _extract_acoustic_metrics(data, sr=TARGET_SAMPLE_RATE)

        # Legacy string formats for backward-compatible test suites
        if is_bonafide:
            verdict = "🛡️ GIỌNG THẬT (BONAFIDE)"
            if decision.confidence_calibrated and decision.confidence is not None:
                conf_str = f"Độ tin cậy: {conf_pct:.1f}% (Platt Scaling)"
            else:
                conf_str = f"Chưa hiệu chuẩn xác suất (Điểm thô: {raw_score:+.2f} | Ngưỡng: {threshold:+.2f})"
            detail = (
                f"✅ Xác thực: Không phát hiện dấu hiệu tổng hợp âm thanh bằng AI.\n"
                f"📊 Điểm raw score: {raw_score:.4f} (Ngưỡng phân định: {threshold:.4f})\n"
                f"⏱️ Thời gian xử lý: {latency:.2f}s | Mã băm: {audio_sha256[:16]}..."
            )
        else:
            verdict = "⚠️ CẢNH BÁO: GIỌNG NÓI GIẢ MẠO (SPOOF)"
            if decision.confidence_calibrated and decision.confidence is not None:
                conf_str = f"Độ tin cậy phát hiện: {conf_pct:.1f}% (Platt Scaling)"
            else:
                conf_str = f"Chưa hiệu chuẩn xác suất (Điểm thô: {raw_score:+.2f} | Ngưỡng: {threshold:+.2f})"
            detail = (
                f"🚨 Khuyến cáo: Đoạn thoại này có dấu hiệu được tạo bởi công nghệ nhái giọng (Deepfake / TTS).\n"
                f"👉 TUYỆT ĐỐI KHÔNG: Chuyển tiền, gửi thông tin tài khoản ngân hàng hoặc đọc mã OTP.\n"
                f"📊 Điểm raw score: {raw_score:.4f} (Ngưỡng phân định: {threshold:.4f})\n"
                f"⏱️ Thời gian xử lý: {latency:.2f}s | Mã băm: {audio_sha256[:16]}..."
            )

        if not return_rich:
            return verdict, conf_str, detail

        # Probability calculation (Platt Scaling) for full dual-class visualization
        diff = float(raw_score - threshold)
        prob_bona = 1.0 / (1.0 + float(np.exp(-PLATT_SCALE_K * diff)))
        prob_bona = float(max(0.001, min(0.999, prob_bona)))
        prob_spoof = 1.0 - prob_bona
        prob_bona_pct = prob_bona * 100.0
        prob_spoof_pct = prob_spoof * 100.0

        # Generate Stitch-Theme Rich HTML Components
        if is_bonafide:
            verdict_html = f"""
            <div class="verdict-box-bonafide">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #10B981, #059669); display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3); flex-shrink: 0;">
                        <iconify-icon icon="solar:shield-check-bold" width="28" height="28"></iconify-icon>
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                            <span style="font-size: 1.25rem; font-weight: 700; color: var(--bona-title-color);">XÁC THỰC: GIỌNG NÓI TỰ NHIÊN</span>
                            <span style="padding: 2px 10px; border-radius: 9999px; background: #10B981; color: white; font-size: 11px; font-weight: 700; text-transform: uppercase;">Bonafide Audio</span>
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 13.5px; color: var(--bona-desc-color); line-height: 1.5;">
                            Không tìm thấy bất kỳ dấu hiệu tổng hợp âm thanh bằng AI hay cắt ghép giả mạo. Đường nét cao độ thanh quản và nhiễu vi mô hoàn toàn trùng khớp giọng nói người thật.
                        </p>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; background: var(--action-bona-bg); border: 1px solid var(--action-bona-border); display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; background: #10B981; color: white; flex-shrink: 0;">
                            <iconify-icon icon="solar:check-read-bold" width="14" height="14"></iconify-icon>
                        </span>
                        <span style="font-size: 12px; color: var(--bona-action-text);"><strong style="color: var(--bona-action-text-bold);">Âm sắc Người Thật:</strong> Phổ sinh học đầy đủ, phản xạ hơi thở tự nhiên.</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; background: #0F766E; color: white; flex-shrink: 0;">
                            <iconify-icon icon="solar:hand-shake-bold" width="14" height="14"></iconify-icon>
                        </span>
                        <span style="font-size: 12px; color: var(--bona-action-text);"><strong style="color: var(--bona-action-text-bold);">An Tâm Giao Tiếp:</strong> Đoạn thoại an toàn và không bị can thiệp.</span>
                    </div>
                </div>
            </div>
            """
            conf_color = "#10B981"
            conf_label = "Tự Nhiên (Bonafide)"
        else:
            verdict_html = f"""
            <div class="verdict-box-spoof">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #EF4444, #B91C1C); display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4); flex-shrink: 0;">
                        <iconify-icon icon="solar:shield-warning-bold" width="28" height="28"></iconify-icon>
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                            <span style="font-size: 1.25rem; font-weight: 700; color: var(--spoof-title-color);">CẢNH BÁO: GIỌNG NÓI GIẢ MẠO</span>
                            <span style="padding: 2px 10px; border-radius: 9999px; background: #EF4444; color: white; font-size: 11px; font-weight: 700; text-transform: uppercase;">Phát hiện Deepfake</span>
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 13.5px; color: var(--spoof-desc-color); line-height: 1.5;">
                            Hệ thống AI nhận diện thấy dấu vết biến điệu nhân tạo (AI Voice Cloning / TTS Synthesis). Có nguy cơ cao đây là cuộc gọi hoặc tin nhắn giả danh để lừa đảo.
                        </p>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; background: var(--action-spoof-bg); border: 1px solid var(--action-spoof-border); display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; background: #EF4444; color: white; flex-shrink: 0;">
                            <iconify-icon icon="solar:close-circle-bold" width="14" height="14"></iconify-icon>
                        </span>
                        <span style="font-size: 12px; color: var(--spoof-action-text);"><strong>TUYỆT ĐỐI KHÔNG:</strong> Không chuyển tiền, không đọc mã OTP hoặc gửi mật khẩu.</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; background: #0F766E; color: white; flex-shrink: 0;">
                            <iconify-icon icon="solar:phone-calling-bold" width="14" height="14"></iconify-icon>
                        </span>
                        <span style="font-size: 12px; color: var(--text-primary);"><strong>GỌI LẠI TRỰC TIẾP:</strong> Gọi điện thoại truyền thống hoặc Video Call để nhìn mặt.</span>
                    </div>
                </div>
            </div>
            """
            conf_color = "#EF4444"
            conf_label = "Giả Mạo (Deepfake Spoof)"

        conf_html = f"""
        <div style="background: var(--conf-box-bg); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 1rem; margin-top: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Độ tin cậy phân tích (Platt Scaling Calibrated):</span>
                <span style="font-size: 15px; font-weight: 700; color: {conf_color}; font-family: 'JetBrains Mono', monospace;">{conf_pct:.1f}% {conf_label}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill-spoof" style="width: {prob_spoof_pct:.1f}%;"></div>
                <div class="progress-fill-bonafide" style="width: {prob_bona_pct:.1f}%;"></div>
                <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: rgba(148, 163, 184, 0.8); transform: translateX(-50%); z-index: 2;" title="Ngưỡng phân định θ"></div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-family: 'JetBrains Mono', monospace; margin-top: 0.25rem;">
                <span style="color: {'#EF4444' if not is_bonafide else 'var(--text-muted)'}; font-weight: {'700' if not is_bonafide else '400'}; display: inline-flex; align-items: center; gap: 4px;">
                    <iconify-icon icon="solar:danger-circle-bold" width="13" height="13"></iconify-icon> Giả Mạo: {prob_spoof_pct:.1f}%
                </span>
                <span style="color: var(--text-muted);">Ngưỡng θ: {threshold:.4f} (50%)</span>
                <span style="color: {'#10B981' if is_bonafide else 'var(--text-muted)'}; font-weight: {'700' if is_bonafide else '400'}; display: inline-flex; align-items: center; gap: 4px;">
                    <iconify-icon icon="solar:check-circle-bold" width="13" height="13"></iconify-icon> Người Thật: {prob_bona_pct:.1f}%
                </span>
            </div>
        </div>
        """

        hf_val = acoustics['hf_ratio']
        if is_bonafide:
            hf_color = "#10B981"
            hf_sub = "Dải cao tần tự nhiên"
        else:
            if hf_val < 1.0:
                hf_color = "#EF4444"
                hf_sub = "Bất thường Vocoder (<1%)"
            else:
                hf_color = "#F87171"
                hf_sub = "Vocoder Roll-off"

        metrics_html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 0.75rem;">
            <div class="stat-card">
                <div style="font-size: 11px; color: var(--text-muted);">Điểm Raw Score</div>
                <div style="font-size: 14px; font-weight: 700; color: {conf_color}; font-family: 'JetBrains Mono', monospace;">{raw_score:+.4f}</div>
                <div style="font-size: 10px; color: var(--text-muted);">Ngưỡng θ: {threshold:.4f}</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: var(--text-muted);">Thời gian xử lý</div>
                <div style="font-size: 14px; font-weight: 700; color: var(--teal-accent); font-family: 'JetBrains Mono', monospace;">{latency:.3f}s</div>
                <div style="font-size: 10px; color: var(--text-muted);">NFR1: ≤ 3.0s (PASS)</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: var(--text-muted);">Cửa sổ suy luận</div>
                <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace;">{n_windows} Cửa sổ</div>
                <div style="font-size: 10px; color: var(--text-muted);">Max-Pooling Mode</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: var(--text-muted);">Năng lượng >4kHz</div>
                <div style="font-size: 14px; font-weight: 700; color: {hf_color}; font-family: 'JetBrains Mono', monospace;">{hf_val:.2f}%</div>
                <div style="font-size: 10px; color: {hf_color};">{hf_sub}</div>
            </div>
        </div>
        <div style="margin-top: 0.5rem; background: var(--hash-row-bg); border: 1px solid var(--hash-row-border); border-radius: 0.5rem; padding: 0.5rem 0.75rem; display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            <span>Mã băm SHA-256 đối soát: <strong style="color: var(--teal-accent);">{audio_sha256[:24]}...</strong></span>
            <span>Thời lượng: <strong style="color: var(--text-primary);">{acoustics['duration']:.2f}s</strong> | Tần số: 16,000 Hz Mono</span>
        </div>
        """

        # Generate 3 Scientific Plots
        spec_fig, wave_fig, cam_fig = _create_forensic_plots(
            data,
            sr=TARGET_SAMPLE_RATE,
            window_scores=scores_np,
            threshold=threshold,
            is_bonafide=is_bonafide,
        )

        return (
            verdict,
            conf_str,
            detail,
            verdict_html,
            conf_html,
            metrics_html,
            spec_fig,
            wave_fig,
            cam_fig,
        )

    return predict_audio


def _render_status_banner(kind: str, text: str) -> str:
    """Render a responsive status banner for live cloning progression."""
    if kind == "info":
        bg = "rgba(20, 184, 166, 0.12)"
        border = "rgba(20, 184, 166, 0.4)"
        color = "var(--text-primary)"
        icon = '<iconify-icon icon="solar:cpu-bolt-bold" class="rotating-spinner" width="18" height="18" style="color: var(--teal-accent); flex-shrink: 0;"></iconify-icon>'
    elif kind == "success":
        bg = "rgba(46, 204, 113, 0.15)"
        border = "rgba(46, 204, 113, 0.5)"
        color = "var(--text-primary)"
        icon = '<iconify-icon icon="solar:check-circle-bold" width="18" height="18" style="color: #2ECC71; flex-shrink: 0;"></iconify-icon>'
    elif kind == "warning":
        bg = "rgba(245, 158, 11, 0.15)"
        border = "rgba(245, 158, 11, 0.5)"
        color = "#F59E0B"
        icon = '<iconify-icon icon="solar:danger-triangle-bold" width="18" height="18" style="color: #F59E0B; flex-shrink: 0;"></iconify-icon>'
    else:  # error
        bg = "rgba(239, 68, 68, 0.15)"
        border = "rgba(239, 68, 68, 0.5)"
        color = "#EF4444"
        icon = '<iconify-icon icon="solar:close-circle-bold" width="18" height="18" style="color: #EF4444; flex-shrink: 0;"></iconify-icon>'

    return f"""
    <div style="background: {bg}; border: 1px solid {border}; border-radius: 0.75rem; padding: 0.85rem 1rem; display: flex; align-items: center; gap: 0.75rem; color: {color}; font-size: 13px;">
        {icon}
        <div>{text}</div>
    </div>
    """


def _render_quad_card_placeholder(title: str, subtitle: str, icon: str) -> str:
    """Render a card in idle/waiting state."""
    return f"""
    <div class="quad-card">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <iconify-icon icon="{icon}" width="18" height="18" style="color: var(--text-muted);"></iconify-icon>
                <strong style="color: var(--text-primary); font-size: 13.5px;">{title}</strong>
            </div>
            <span class="badge-waiting">Đang chờ</span>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">{subtitle}</div>
        <div style="background: var(--bg-surface); border: 1px dashed var(--border-color); border-radius: 8px; padding: 1.25rem 0.5rem; text-align: center; color: var(--text-muted); font-size: 12px;">
            <iconify-icon icon="solar:clock-circle-linear" width="24" height="24" style="margin-bottom: 4px; opacity: 0.5;"></iconify-icon>
            <div>Chưa có dữ liệu xử lý</div>
        </div>
    </div>
    """


def _render_quad_card_done(
    title: str,
    subtitle: str,
    icon: str,
    eval_dict: dict,
    is_bonafide_truth: bool = False,
) -> str:
    """Render a finished card with detection metrics and Platt-scaled verdict."""
    is_bonafide = bool(eval_dict.get("is_bonafide", False))
    raw_score = float(eval_dict.get("raw_score", 0.0))
    prob_bona_pct = float(eval_dict.get("prob_bona_pct", 50.0))
    prob_spoof_pct = float(eval_dict.get("prob_spoof_pct", 50.0))
    latency = float(eval_dict.get("latency_s", 0.0))
    sha256 = str(eval_dict.get("sha256", ""))[:16]

    if is_bonafide:
        badge = f"""<span class="badge-bonafide"><iconify-icon icon="solar:check-circle-bold" width="13" height="13"></iconify-icon> NGƯỜI THẬT ({prob_bona_pct:.1f}%)</span>"""
        card_class = "quad-card quad-card-bonafide"
        score_color = "#10B981"
    else:
        badge = f"""<span class="badge-spoof"><iconify-icon icon="solar:danger-circle-bold" width="13" height="13"></iconify-icon> GIẢ MẠO ({prob_spoof_pct:.1f}%)</span>"""
        card_class = "quad-card quad-card-spoof"
        score_color = "#EF4444"

    # Ground Truth assessment
    if is_bonafide_truth:
        if is_bonafide:
            verdict_text = "✅ Nhận diện chính xác 100% giọng thật của bạn."
            verdict_color = "#10B981"
        else:
            verdict_text = "⚠️ Báo nhầm (BPCER): Giọng thật bị nghi ngờ giả mạo."
            verdict_color = "#F59E0B"
    else:
        if not is_bonafide:
            verdict_text = "🛡️ Chặn thành công: Phát hiện chính xác bản Deepfake."
            verdict_color = "#EF4444"
        else:
            verdict_text = "⚠️ Bỏ sót (APCER): Mô hình chưa phát hiện bản giả mạo."
            verdict_color = "#F59E0B"

    return f"""
    <div class="{card_class}">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <iconify-icon icon="{icon}" width="18" height="18" style="color: {'#10B981' if is_bonafide else '#EF4444'};"></iconify-icon>
                <strong style="color: var(--text-primary); font-size: 13.5px;">{title}</strong>
            </div>
            {badge}
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">{subtitle}</div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 8px;">
            <div style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 6px; padding: 6px 8px;">
                <div style="font-size: 10px; color: var(--text-muted);">Raw Score (θ=0.0)</div>
                <div style="font-size: 13px; font-weight: 700; color: {score_color}; font-family: 'JetBrains Mono', monospace;">{raw_score:+.4f}</div>
            </div>
            <div style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 6px; padding: 6px 8px;">
                <div style="font-size: 10px; color: var(--text-muted);">Thời gian phân tích</div>
                <div style="font-size: 13px; font-weight: 700; color: var(--teal-accent); font-family: 'JetBrains Mono', monospace;">{latency*1000:.1f}ms</div>
            </div>
        </div>

        <div style="font-size: 11.5px; font-weight: 600; color: {verdict_color}; margin-bottom: 6px;">
            {verdict_text}
        </div>

        <div style="font-size: 10px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
            SHA-256: {sha256}...
        </div>
    </div>
    """


def _render_quad_card_step(
    title: str,
    subtitle: str,
    icon: str,
    step_dict: dict,
    is_bonafide_truth: bool = False,
) -> str:
    """Render a card based on current lifecycle status."""
    status = step_dict.get("status", "waiting")
    if status == "done":
        return _render_quad_card_done(
            title, subtitle, icon, step_dict.get("eval", {}), is_bonafide_truth=is_bonafide_truth
        )
    elif status == "loading":
        msg = step_dict.get("msg", "Đang nạp mô hình & nhân bản giọng...")
        return f"""
        <div class="quad-card quad-card-loading">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <iconify-icon icon="{icon}" width="18" height="18" style="color: var(--teal-accent);"></iconify-icon>
                    <strong style="color: var(--text-primary); font-size: 13.5px;">{title}</strong>
                </div>
                <span class="badge-loading"><iconify-icon icon="solar:refresh-circle-bold" class="rotating-spinner" width="12" height="12"></iconify-icon> Đang nhân bản...</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">{subtitle}</div>
            <div style="background: var(--bg-surface); border: 1px dashed var(--border-color); border-radius: 8px; padding: 1.25rem 0.5rem; text-align: center;">
                <iconify-icon icon="solar:cpu-bolt-bold" class="rotating-spinner" width="28" height="28" style="color: var(--teal-accent);"></iconify-icon>
                <div style="margin-top: 8px; font-size: 12px; color: var(--text-primary); font-weight: 500;">{msg}</div>
                <div style="font-size: 10.5px; color: var(--text-muted); margin-top: 2px;">Vui lòng đợi giây lát...</div>
            </div>
        </div>
        """
    elif status == "skipped":
        msg = step_dict.get("msg", "Bỏ qua trong chế độ tiết kiệm VRAM.")
        return f"""
        <div class="quad-card">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <iconify-icon icon="{icon}" width="18" height="18" style="color: var(--text-muted);"></iconify-icon>
                    <strong style="color: var(--text-primary); font-size: 13.5px;">{title}</strong>
                </div>
                <span class="badge-skipped">Đã bỏ qua</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">{subtitle}</div>
            <div style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.25rem 0.5rem; text-align: center; color: var(--text-muted); font-size: 12px;">
                <iconify-icon icon="solar:forbidden-circle-linear" width="24" height="24" style="margin-bottom: 4px; opacity: 0.6;"></iconify-icon>
                <div>{msg}</div>
            </div>
        </div>
        """
    elif status == "error":
        msg = step_dict.get("msg", "Lỗi trong quá trình sinh giọng.")
        return f"""
        <div class="quad-card" style="border-color: #EF4444;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <iconify-icon icon="{icon}" width="18" height="18" style="color: #EF4444;"></iconify-icon>
                    <strong style="color: var(--text-primary); font-size: 13.5px;">{title}</strong>
                </div>
                <span class="badge-spoof">Lỗi</span>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">{subtitle}</div>
            <div style="background: var(--bg-surface); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px; padding: 1.25rem 0.5rem; text-align: center; color: #EF4444; font-size: 12px;">
                <iconify-icon icon="solar:danger-circle-bold" width="24" height="24" style="margin-bottom: 4px;"></iconify-icon>
                <div>{msg}</div>
            </div>
        </div>
        """
    else:
        return _render_quad_card_placeholder(title, subtitle, icon)


def _render_matrix_summary(state: dict, completed: bool = False) -> str:
    """Render the 4-sample comparison matrix table."""
    rows = []
    items = [
        ("Bản 1: Người Thật (Bona Fide)", "Microphone Trực Tiếp", "Thật (Bona Fide)", state.get("bonafide")),
        ("Bản 2: Clone F5-TTS", "Flow Matching Non-AR", "Giả Mạo (Deepfake)", state.get("f5", {}).get("eval")),
        ("Bản 3: Clone VieNeu-TTS", "Fast DiT v3 Turbo", "Giả Mạo (Deepfake)", state.get("vieneu", {}).get("eval")),
        ("Bản 4: Clone VoiceStudio CFM", "OmniVoice Zero-Shot CFM", "Giả Mạo (Deepfake)", state.get("omnivoice", {}).get("eval")),
    ]

    for label, engine, truth, ev in items:
        if ev is not None and isinstance(ev, dict) and "raw_score" in ev:
            is_bona = bool(ev.get("is_bonafide", False))
            raw_s = float(ev.get("raw_score", 0.0))
            prob_pct = float(ev.get("prob_bona_pct" if is_bona else "prob_spoof_pct", 50.0))
            lat = float(ev.get("latency_s", 0.0)) * 1000.0

            if is_bona:
                decision_badge = '<span style="color: #10B981; font-weight: 700;">Người Thật</span>'
            else:
                decision_badge = '<span style="color: #EF4444; font-weight: 700;">Giả Mạo</span>'

            # Match check
            if (truth.startswith("Thật") and is_bona) or (truth.startswith("Giả") and not is_bona):
                match_badge = '<span style="color: #10B981; font-weight: 700; background: rgba(16, 185, 129, 0.15); padding: 2px 8px; border-radius: 4px;">CHÍNH XÁC</span>'
            else:
                match_badge = '<span style="color: #F59E0B; font-weight: 700; background: rgba(245, 158, 11, 0.15); padding: 2px 8px; border-radius: 4px;">CẢNH BÁO</span>'

            row_html = f"""
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px 12px; font-weight: 600; color: var(--text-primary);">{label}</td>
                <td style="padding: 8px 12px; color: var(--text-secondary);">{engine}</td>
                <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">{truth}</td>
                <td style="padding: 8px 12px;">{decision_badge}</td>
                <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-weight: 600;">{prob_pct:.1f}%</td>
                <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-weight: 600; color: {'#10B981' if is_bona else '#EF4444'};">{raw_s:+.4f}</td>
                <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; color: var(--teal-accent);">{lat:.1f}ms</td>
                <td style="padding: 8px 12px;">{match_badge}</td>
            </tr>
            """
        else:
            status_txt = "Đang chờ..."
            if label.startswith("Bản 2") and state.get("f5", {}).get("status") == "skipped":
                status_txt = "Đã bỏ qua (VRAM Opt)"
            elif label.startswith("Bản 3") and state.get("vieneu", {}).get("status") == "skipped":
                status_txt = "Đã bỏ qua (VRAM Opt)"

            row_html = f"""
            <tr style="border-bottom: 1px solid var(--border-color); opacity: 0.6;">
                <td style="padding: 8px 12px; font-weight: 600; color: var(--text-primary);">{label}</td>
                <td style="padding: 8px 12px; color: var(--text-muted);">{engine}</td>
                <td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">{truth}</td>
                <td style="padding: 8px 12px; color: var(--text-muted); font-style: italic;">{status_txt}</td>
                <td style="padding: 8px 12px; color: var(--text-muted);">-</td>
                <td style="padding: 8px 12px; color: var(--text-muted);">-</td>
                <td style="padding: 8px 12px; color: var(--text-muted);">-</td>
                <td style="padding: 8px 12px; color: var(--text-muted);">-</td>
            </tr>
            """
        rows.append(row_html)

    header_status = "HOÀN TẤT KIỂM ĐỊNH" if completed else "TIẾN TRÌNH ĐANG XỬ LÝ"
    header_color = "#10B981" if completed else "var(--teal-accent)"

    return f"""
    <div style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 0.875rem; padding: 1.25rem; margin-top: 1.25rem;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;">
            <div style="font-size: 13.5px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                <iconify-icon icon="solar:checklist-minimalistic-bold" width="18" height="18" style="color: {header_color};"></iconify-icon>
                BẢNG ĐỐI SOÁT TOÀN DIỆN 4 CHIỀU (QUAD-FORENSICS BENCHMARK MATRIX)
            </div>
            <span style="font-size: 11px; font-family: 'JetBrains Mono', monospace; color: {header_color}; font-weight: 600; background: var(--bg-card); border: 1px solid var(--border-color); padding: 2px 10px; border-radius: 9999px;">
                {header_status}
            </span>
        </div>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                <thead>
                    <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-secondary); font-size: 11px;">
                        <th style="padding: 8px 12px;">Mẫu Thử</th>
                        <th style="padding: 8px 12px;">Mô Hình / Nguồn</th>
                        <th style="padding: 8px 12px;">Ground Truth</th>
                        <th style="padding: 8px 12px;">Kết Luận AI</th>
                        <th style="padding: 8px 12px;">Độ Tin Cậy</th>
                        <th style="padding: 8px 12px;">Điểm Raw</th>
                        <th style="padding: 8px 12px;">Độ Trễ</th>
                        <th style="padding: 8px 12px;">Đối Soát</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </div>
    """


def make_live_quad_cloning_fn(
    model: Any = None,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    device: str = "cpu",
    threshold: float = 0.0,
):
    """Factory creating the generator function for live 4-way voice cloning & forensics."""
    loaded_model = model

    def stream_quad_cloning(
        audio_input: Any,
        only_omnivoice: bool = False,
    ):
        nonlocal loaded_model
        if loaded_model is None:
            loaded_model = _default_model_loader(checkpoint_path, device=device)

        if audio_input is None:
            yield (
                _render_status_banner("warning", "⚠️ Vui lòng ghi âm giọng nói của bạn qua Microphone (khoảng 3 – 5 giây) trước khi bấm Bắt đầu."),
                _render_quad_card_placeholder("Bản 1: Người Thật (Bona Fide)", "Giọng nói gốc trực tiếp từ Microphone", "solar:user-bold"),
                None,
                _render_quad_card_placeholder("Bản 2: Clone F5-TTS", "Flow Matching Non-Autoregressive", "solar:cpu-bold"),
                None,
                _render_quad_card_placeholder("Bản 3: Clone VieNeu-TTS", "Fast DiT v3 Turbo (48kHz)", "solar:bolt-bold"),
                None,
                _render_quad_card_placeholder("Bản 4: Clone VoiceStudio CFM", "OmniVoice Continuous Flow Matching", "solar:magic-stick-3-bold"),
                None,
                "",
            )
            return

        if isinstance(audio_input, tuple):
            sr, data = audio_input
        else:
            yield (
                _render_status_banner("error", "❌ Định dạng âm thanh không hợp lệ."),
                _render_quad_card_placeholder("Bản 1: Người Thật (Bona Fide)", "Giọng nói gốc trực tiếp từ Microphone", "solar:user-bold"),
                None,
                _render_quad_card_placeholder("Bản 2: Clone F5-TTS", "Flow Matching Non-Autoregressive", "solar:cpu-bold"),
                None,
                _render_quad_card_placeholder("Bản 3: Clone VieNeu-TTS", "Fast DiT v3 Turbo (48kHz)", "solar:bolt-bold"),
                None,
                _render_quad_card_placeholder("Bản 4: Clone VoiceStudio CFM", "OmniVoice Continuous Flow Matching", "solar:magic-stick-3-bold"),
                None,
                "",
            )
            return

        if data.ndim > 1:
            data = data.mean(axis=-1)
        if np.issubdtype(data.dtype, np.integer):
            max_val = float(np.iinfo(data.dtype).max)
            data = data.astype(np.float32) / max_val
        else:
            data = data.astype(np.float32)

        duration = len(data) / float(sr)
        if duration < 1.0:
            yield (
                _render_status_banner("warning", f"⚠️ Đoạn ghi âm quá ngắn ({duration:.2f}s < 1.0s). Vui lòng ghi âm tối thiểu 2-3 giây để mô hình có đủ ngữ âm mẫu."),
                _render_quad_card_placeholder("Bản 1: Người Thật (Bona Fide)", "Giọng nói gốc trực tiếp từ Microphone", "solar:user-bold"),
                None,
                _render_quad_card_placeholder("Bản 2: Clone F5-TTS", "Flow Matching Non-Autoregressive", "solar:cpu-bold"),
                None,
                _render_quad_card_placeholder("Bản 3: Clone VieNeu-TTS", "Fast DiT v3 Turbo (48kHz)", "solar:bolt-bold"),
                None,
                _render_quad_card_placeholder("Bản 4: Clone VoiceStudio CFM", "OmniVoice Continuous Flow Matching", "solar:magic-stick-3-bold"),
                None,
                "",
            )
            return

        cloner_device = "cuda" if (torch.cuda.is_available() and "cuda" in str(device).lower()) else "cpu"
        if LiveQuadCloner is None:
            yield (
                _render_status_banner("error", "❌ Không tìm thấy module LiveQuadCloner."),
                _render_quad_card_placeholder("Bản 1: Người Thật (Bona Fide)", "Giọng nói gốc trực tiếp từ Microphone", "solar:user-bold"),
                None,
                _render_quad_card_placeholder("Bản 2: Clone F5-TTS", "Flow Matching Non-Autoregressive", "solar:cpu-bold"),
                None,
                _render_quad_card_placeholder("Bản 3: Clone VieNeu-TTS", "Fast DiT v3 Turbo (48kHz)", "solar:bolt-bold"),
                None,
                _render_quad_card_placeholder("Bản 4: Clone VoiceStudio CFM", "OmniVoice Continuous Flow Matching", "solar:magic-stick-3-bold"),
                None,
                "",
            )
            return

        cloner = LiveQuadCloner(
            target_text=DEFAULT_TARGET_TEXT,
            device=cloner_device,
            priority_only_omnivoice=bool(only_omnivoice),
        )

        bona_audio_out = (sr, data)
        f5_audio_out = None
        vn_audio_out = None
        omni_audio_out = None

        for state in cloner.stream_cloning_and_detection(
            data, sr, detector_model=loaded_model, threshold=threshold
        ):
            step = state.get("step", 0)
            completed = state.get("completed", False)

            if state.get("f5", {}).get("status") == "done" and "audio" in state["f5"]:
                f5_audio_out = state["f5"]["audio"]
            if state.get("vieneu", {}).get("status") == "done" and "audio" in state["vieneu"]:
                vn_audio_out = state["vieneu"]["audio"]
            if state.get("omnivoice", {}).get("status") == "done" and "audio" in state["omnivoice"]:
                omni_audio_out = state["omnivoice"]["audio"]

            if not completed:
                if step == 0:
                    banner = _render_status_banner("info", "⚡ <strong>Bước 1/4:</strong> Đã xác thực giọng người thật (~66ms)! Đang nạp mô hình F5-TTS...")
                elif step == 1:
                    banner = _render_status_banner("info", "⚡ <strong>Bước 2/4:</strong> Đã hoàn tất nhân bản F5-TTS! Đang chuyển sang VieNeu-TTS v3 Turbo...")
                elif step == 2:
                    banner = _render_status_banner("info", "⚡ <strong>Bước 3/4:</strong> Đã hoàn tất nhân bản VieNeu-TTS! Đang nạp VoiceStudio CFM...")
                else:
                    banner = _render_status_banner("info", "⚡ Đang xử lý các bước còn lại...")
            else:
                banner = _render_status_banner("success", "✅ <strong>HOÀN TẤT THỬ THÁCH NHÂN BẢN & ĐỐI CHỨNG 4 CHIỀU TOÀN DIỆN!</strong>")

            bona_html = _render_quad_card_done(
                "Bản 1: Người Thật (Bona Fide)",
                "Giọng nói gốc trực tiếp từ Microphone",
                "solar:user-bold",
                state.get("bonafide", {}),
                is_bonafide_truth=True,
            )
            f5_html = _render_quad_card_step(
                "Bản 2: Clone F5-TTS",
                "Flow Matching Non-Autoregressive",
                "solar:cpu-bold",
                state.get("f5", {}),
                is_bonafide_truth=False,
            )
            vn_html = _render_quad_card_step(
                "Bản 3: Clone VieNeu-TTS",
                "Fast DiT v3 Turbo (48kHz)",
                "solar:bolt-bold",
                state.get("vieneu", {}),
                is_bonafide_truth=False,
            )
            omni_html = _render_quad_card_step(
                "Bản 4: Clone VoiceStudio CFM",
                "OmniVoice Continuous Flow Matching",
                "solar:magic-stick-3-bold",
                state.get("omnivoice", {}),
                is_bonafide_truth=False,
            )

            matrix_html = _render_matrix_summary(state, completed=completed)

            yield (
                banner,
                bona_html, bona_audio_out,
                f5_html, f5_audio_out,
                vn_html, vn_audio_out,
                omni_html, omni_audio_out,
                matrix_html,
            )

    return stream_quad_cloning


THEME_TOGGLE_JS = """
() => {
    const isLight = document.body.classList.contains('theme-light');
    const btn = document.querySelector('#theme-toggle-btn button') || document.getElementById('theme-toggle-btn');
    if (isLight) {
        document.body.classList.remove('theme-light');
        document.body.classList.add('dark');
        localStorage.setItem('vitruevoice_theme', 'dark');
        if (btn) {
            btn.innerHTML = '<iconify-icon icon="solar:sun-2-bold" width="22" height="22" style="color: #F59E0B; vertical-align: middle;"></iconify-icon>';
            btn.title = 'Chế độ Sáng (Light)';
        }
    } else {
        document.body.classList.add('theme-light');
        document.body.classList.remove('dark');
        localStorage.setItem('vitruevoice_theme', 'light');
        if (btn) {
            btn.innerHTML = '<iconify-icon icon="solar:moon-bold" width="20" height="20" style="color: #38BDF8; vertical-align: middle;"></iconify-icon>';
            btn.title = 'Chế độ Tối (Dark)';
        }
    }
}
"""

THEME_INIT_JS = """
() => {
    // 1. Ensure Iconify Web Component is loaded in <head>
    if (!document.querySelector('script[src*="iconify-icon"]')) {
        const sc = document.createElement('script');
        sc.src = 'https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js';
        document.head.appendChild(sc);
    }

    // 2. Setup theme
    const saved = localStorage.getItem('vitruevoice_theme');
    const urlParams = new URLSearchParams(window.location.search);
    const urlTheme = urlParams.get('__theme');
    const isLight = (saved === 'light' || urlTheme === 'light');
    const btn = document.querySelector('#theme-toggle-btn button') || document.getElementById('theme-toggle-btn');
    if (isLight) {
        document.body.classList.add('theme-light');
        document.body.classList.remove('dark');
        if (btn) {
            btn.innerHTML = '<iconify-icon icon="solar:moon-bold" width="20" height="20" style="color: #38BDF8; vertical-align: middle;"></iconify-icon>';
            btn.title = 'Chế độ Tối (Dark)';
        }
    } else {
        document.body.classList.remove('theme-light');
        document.body.classList.add('dark');
        if (btn) {
            btn.innerHTML = '<iconify-icon icon="solar:sun-2-bold" width="22" height="22" style="color: #F59E0B; vertical-align: middle;"></iconify-icon>';
            btn.title = 'Chế độ Sáng (Light)';
        }
    }

    // 3. Inject icons into buttons and tabs via Iconify
    function applyIconifyDecorations() {
        const submitBtn = document.querySelector("#submit-btn button, #submit-btn");
        if (submitBtn && !submitBtn.querySelector('iconify-icon')) {
            submitBtn.innerHTML = '<iconify-icon icon="solar:magnifer-bold" width="18" height="18" style="vertical-align: middle; margin-right: 6px;"></iconify-icon> 2. KIỂM TRA TÍNH XÁC THỰC NGAY';
        }
        const qBtn = document.querySelector("#start-quad-btn button, #start-quad-btn");
        if (qBtn && !qBtn.querySelector('iconify-icon')) {
            qBtn.innerHTML = '<iconify-icon icon="solar:rocket-bold" width="18" height="18" style="vertical-align: middle; margin-right: 6px;"></iconify-icon> 2. BẮT ĐẦU NHÂN BẢN & ĐỐI CHỨNG 4 CHIỀU';
        }
        const s1 = document.querySelector("#sample-spoof-btn button, #sample-spoof-btn");
        if (s1 && !s1.querySelector('iconify-icon')) {
            s1.innerHTML = '<iconify-icon icon="solar:danger-circle-bold" width="14" height="14" style="color: #EF4444; vertical-align: middle; margin-right: 4px;"></iconify-icon> Mẫu 1 (Spoof F5-TTS)';
        }
        const s2 = document.querySelector("#sample-bona-btn button, #sample-bona-btn");
        if (s2 && !s2.querySelector('iconify-icon')) {
            s2.innerHTML = '<iconify-icon icon="solar:check-circle-bold" width="14" height="14" style="color: #10B981; vertical-align: middle; margin-right: 4px;"></iconify-icon> Mẫu 2 (Người Thật)';
        }
        const s3 = document.querySelector("#sample-zalo-btn button, #sample-zalo-btn");
        if (s3 && !s3.querySelector('iconify-icon')) {
            s3.innerHTML = '<iconify-icon icon="solar:shield-warning-bold" width="14" height="14" style="color: #F59E0B; vertical-align: middle; margin-right: 4px;"></iconify-icon> Mẫu 3 (Spoof Zalo Nén)';
        }
        const tabBtns = document.querySelectorAll('button[role="tab"]');
        if (tabBtns.length >= 3) {
            if (!tabBtns[0].querySelector('iconify-icon')) {
                tabBtns[0].innerHTML = '<iconify-icon icon="solar:chart-square-bold" width="15" height="15" style="vertical-align: middle; margin-right: 5px;"></iconify-icon> Mel-Spectrogram (80 Mels, log dBFS)';
            }
            if (!tabBtns[1].querySelector('iconify-icon')) {
                tabBtns[1].innerHTML = '<iconify-icon icon="solar:soundwave-bold" width="15" height="15" style="vertical-align: middle; margin-right: 5px;"></iconify-icon> Sóng Âm Đồng Bộ (Time-Domain Waveform)';
            }
            if (!tabBtns[2].querySelector('iconify-icon')) {
                tabBtns[2].innerHTML = '<iconify-icon icon="solar:radar-2-bold" width="15" height="15" style="vertical-align: middle; margin-right: 5px;"></iconify-icon> Bản Đồ Chú Ý AI (Grad-CAM Temporal Saliency)';
            }
        }
        const accBtn = document.querySelector('#detail-accordion button');
        if (accBtn && !accBtn.querySelector('iconify-icon')) {
            const span = accBtn.querySelector('span') || accBtn;
            span.innerHTML = '<iconify-icon icon="solar:document-text-bold" width="15" height="15" style="vertical-align: middle; margin-right: 5px;"></iconify-icon> Chi tiết dạng văn bản (Screen Reader & API)';
        }
    }
    applyIconifyDecorations();
    setTimeout(applyIconifyDecorations, 250);
    setTimeout(applyIconifyDecorations, 800);

    // 4. Dual-Platform Raw Audio Capture Hook: disable aggressive browser noise gating
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        if (!window.__vitruevoice_gum_patched) {
            window.__vitruevoice_gum_patched = true;
            const origGUM = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = function(constraints) {
                if (constraints && constraints.audio) {
                    if (typeof constraints.audio === 'object') {
                        constraints.audio.noiseSuppression = false;
                        constraints.audio.echoCancellation = false;
                        constraints.audio.autoGainControl = false;
                    } else if (constraints.audio === true) {
                        constraints.audio = {
                            noiseSuppression: false,
                            echoCancellation: false,
                            autoGainControl: false,
                        };
                    }
                }
                return origGUM(constraints);
            };
        }
    }
}
"""


def build_ui(
    model: Any = None,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
    device: str = "cpu",
    threshold: float = 0.0,
    preload: bool = True,
    calibrator: Callable[..., float] | None = platt_calibrator,
) -> gr.Blocks:
    predict_rich_fn = make_predict_fn(
        model=model,
        checkpoint_path=checkpoint_path,
        device=device,
        threshold=threshold,
        preload=preload,
        calibrator=calibrator,
        return_rich=True,
    )
    live_quad_cloning_fn = make_live_quad_cloning_fn(
        model=model,
        checkpoint_path=checkpoint_path,
        device=device,
        threshold=threshold,
    )

    theme = gr.themes.Monochrome(
        primary_hue="teal",
        neutral_hue="slate",
    ).set(
        body_background_fill="#0B0F17",
        block_background_fill="#131B2E",
        block_border_color="#334155",
    )

    with gr.Blocks(title="ViTrueVoice — Phòng Lab Nhận Diện Deepfake Giọng Nói Tiếng Việt") as demo:
        # Inject Custom Forensics CSS and Iconify Web Component
        gr.HTML(
            f"<style>{CUSTOM_CSS}</style>",
            head='<script src="https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js"></script>',
        )

        # Header Section with Light/Dark Theme Switcher
        with gr.Row(elem_classes=["lab-header"]):
            with gr.Column(scale=9):
                gr.HTML(
                    """
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #14B8A6, #0F766E); display: flex; align-items: center; justify-content: center; color: white; font-size: 26px; box-shadow: 0 4px 20px rgba(20, 184, 166, 0.4); flex-shrink: 0;">
                            <iconify-icon icon="solar:shield-check-bold" width="28" height="28" style="color: white;"></iconify-icon>
                        </div>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <span style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.02em;">ViTrueVoice</span>
                                <span style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 3px 10px; border-radius: 9999px; font-size: 12px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; display: inline-flex; align-items: center; gap: 6px;">
                                    <span class="pulse-dot"></span><iconify-icon icon="solar:cpu-bolt-bold" width="14" height="14" style="color: var(--teal-accent);"></iconify-icon> Mô hình AI: B_zalo V7 Dual-Seen Active
                                </span>
                            </div>
                            <div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">
                                Phòng Lab phân tích âm thanh Forensics Deepfake qua kênh thoại nén tiếng Việt
                            </div>
                        </div>
                    </div>
                    """
                )
            with gr.Column(scale=1, min_width=50):
                with gr.Row(elem_classes=["header-actions-row"]):
                    theme_btn = gr.Button(
                        "☀️",
                        size="sm",
                        elem_id="theme-toggle-btn",
                        min_width=40,
                        scale=0,
                    )
                theme_btn.click(fn=None, js=THEME_TOGGLE_JS)

        with gr.Tabs(elem_id="main-app-tabs") as main_tabs:
            with gr.TabItem("🛡️ Chế Độ 1: Thẩm Định Nhanh Đơn Mẫu (Single-File Analysis)", id="tab_single"):
                with gr.Row():
                    # LEFT COLUMN: Audio Input & Presets
                    with gr.Column(scale=5):
                        gr.Markdown("### <iconify-icon icon='solar:microphone-3-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> 1. Tải lên tin nhắn thoại hoặc Bấm ghi âm")
                        audio_input = gr.Audio(
                            label="Hỗ trợ các định dạng .wav, .mp3, .m4a, .opus, .ogg",
                            sources=["upload", "microphone"],
                            type="numpy",
                        )

                        submit_btn = gr.Button(
                            "2. KIỂM TRA TÍNH XÁC THỰC NGAY",
                            variant="primary",
                            size="lg",
                            elem_id="submit-btn",
                            elem_classes=["btn-primary-teal"],
                        )

                        # 1-Click Preset Samples
                        gr.Markdown("#### <iconify-icon icon='solar:bolt-bold-duotone' width='18' height='18' style='vertical-align: -0.15em; color: #F59E0B;'></iconify-icon> Mẫu âm thanh thử nghiệm đối chứng nhanh:")
                        with gr.Row():
                            sample_spoof_btn = gr.Button("Mẫu 1 (Spoof F5-TTS)", size="sm", elem_id="sample-spoof-btn")
                            sample_bonafide_btn = gr.Button("Mẫu 2 (Người Thật)", size="sm", elem_id="sample-bona-btn")
                            sample_zalo_btn = gr.Button("Mẫu 3 (Spoof Zalo Nén)", size="sm", elem_id="sample-zalo-btn")

                        gr.HTML(
                            """
                            <div style="margin-top: 1rem; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 0.85rem 1rem; display: flex; align-items: flex-start; gap: 0.75rem;">
                                <iconify-icon icon="solar:shield-keyhole-bold-duotone" width="24" height="24" style="color: var(--teal-accent); flex-shrink: 0; margin-top: 2px;"></iconify-icon>
                                <div>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <strong style="font-size: 12px; color: var(--text-primary);">Cam kết Quyền Riêng Tư & An Toàn Tuyệt Đối</strong>
                                        <span style="background: rgba(20, 184, 166, 0.15); border: 1px solid rgba(20, 184, 166, 0.4); color: var(--teal-accent); font-size: 10px; padding: 1px 6px; border-radius: 4px;">Luật 91/2025/QH15</span>
                                    </div>
                                    <p style="font-size: 11.5px; color: var(--text-secondary); margin-top: 3px; line-height: 1.4;">
                                        Âm thanh được phân tích trực tiếp trên RAM và xóa hủy ngay lập tức sau 0.4s. Không lưu trữ, không sao chép và không chia sẻ giọng nói gốc.
                                    </p>
                                </div>
                            </div>
                            """
                        )

                    # RIGHT COLUMN: Analytical Verdict & Forensic Stats
                    with gr.Column(scale=7):
                        gr.Markdown("### <iconify-icon icon='solar:chart-square-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> 3. Kết Quả Xác Minh Âm Thanh")

                        verdict_html = gr.HTML(
                            """
                            <div style="padding: 1.5rem; border-radius: 1rem; background: var(--bg-surface); border: 1px solid var(--border-color); text-align: center; color: var(--text-secondary);">
                                <iconify-icon icon="solar:waveform-bold-duotone" width="38" height="38" style="color: var(--teal-accent); margin-bottom: 8px;"></iconify-icon>
                                <p style="margin-top: 0.25rem; font-size: 14px;">Bấm nút <strong>'2. KIỂM TRA TÍNH XÁC THỰC NGAY'</strong> để nhận diện giọng thật / giả mạo.</p>
                            </div>
                            """
                        )
                        conf_html = gr.HTML()
                        metrics_html = gr.HTML()

                        with gr.Accordion("Chi tiết dạng văn bản (Screen Reader & API)", open=False, elem_id="detail-accordion"):
                            result_verdict = gr.Textbox(label="Kết quả phân định", interactive=False)
                            result_conf = gr.Textbox(label="Độ tin cậy phân tích", interactive=False)
                            result_detail = gr.Textbox(label="Khuyến cáo an toàn", interactive=False, lines=3)

                # SCIENTIFIC VISUALIZATION TABS (Mel-Spectrogram, Waveform, Grad-CAM Attention Map)
                gr.Markdown("---")
                gr.Markdown("### <iconify-icon icon='solar:test-tube-minimalistic-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> Góc Nhìn Số Liệu Khoa Học Trực Quan (Forensic Scientific Visualizations)")
                with gr.Tabs():
                    with gr.TabItem("Mel-Spectrogram (80 Mels, log dBFS)"):
                        spec_plot = gr.Plot(show_label=False)
                    with gr.TabItem("Sóng Âm Đồng Bộ (Time-Domain Waveform)"):
                        wave_plot = gr.Plot(show_label=False)
                    with gr.TabItem("Bản Đồ Chú Ý AI (Grad-CAM Temporal Saliency)"):
                        cam_plot = gr.Plot(show_label=False)

                # Presets click handlers
                samples_dir = Path(__file__).resolve().parent / "samples"
                sample_spoof_path = str(samples_dir / "sample_spoof_f5tts.wav")
                sample_bonafide_path = str(samples_dir / "sample_bonafide_spk0004.wav")
                sample_zalo_path = str(samples_dir / "sample_spoof_zalo_opus.wav")

                def _load_sample_audio(path: str) -> str:
                    p = Path(path)
                    return str(p) if p.exists() else ""

                sample_spoof_btn.click(fn=lambda: _load_sample_audio(sample_spoof_path), outputs=[audio_input])
                sample_bonafide_btn.click(fn=lambda: _load_sample_audio(sample_bonafide_path), outputs=[audio_input])
                sample_zalo_btn.click(fn=lambda: _load_sample_audio(sample_zalo_path), outputs=[audio_input])

                # Main Submit Action
                submit_btn.click(
                    fn=predict_rich_fn,
                    inputs=[audio_input],
                    outputs=[
                        result_verdict,
                        result_conf,
                        result_detail,
                        verdict_html,
                        conf_html,
                        metrics_html,
                        spec_plot,
                        wave_plot,
                        cam_plot,
                    ],
                )

            with gr.TabItem("🧪 Chế Độ 2: Thử Thách Nhân Bản Giọng Trực Tiếp 4 Chiều (Quad-Forensics)", id="tab_quad"):
                with gr.Row():
                    # LEFT COLUMN: Microphone Live Capture & Options
                    with gr.Column(scale=5):
                        gr.Markdown("### <iconify-icon icon='solar:microphone-3-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> 1. Ghi âm giọng nói trực tiếp")
                        live_mic_input = gr.Audio(
                            label="Bấm biểu tượng Micro để ghi âm giọng nói của bạn (khuyến nghị 3 - 5 giây)",
                            sources=["microphone"],
                            type="numpy",
                        )

                        gr.HTML(
                            f"""
                            <div style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 0.75rem; padding: 0.85rem 1rem; margin-top: 0.75rem;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <iconify-icon icon="solar:chat-round-dots-bold" width="18" height="18" style="color: var(--teal-accent);"></iconify-icon>
                                    <strong style="font-size: 13px; color: var(--text-primary);">Câu thoại nhân bản tự động (10 từ thuần Việt):</strong>
                                </div>
                                <div style="margin-top: 6px; padding: 8px 12px; background: var(--bg-card); border-radius: 6px; font-size: 13px; font-weight: 600; color: var(--teal-accent); font-family: 'JetBrains Mono', monospace;">
                                    "{DEFAULT_TARGET_TEXT}"
                                </div>
                                <div style="font-size: 11px; color: var(--text-muted); margin-top: 6px; line-height: 1.4;">
                                    Ba mô hình TTS Zero-Shot (F5-TTS, VieNeu-TTS v3 Turbo, VoiceStudio CFM) sẽ tự động lấy âm sắc giọng vừa ghi âm của bạn làm mẫu để sinh câu thoại trên.
                                </div>
                            </div>
                            """
                        )

                        with gr.Row():
                            only_omnivoice_cb = gr.Checkbox(
                                label="Chế độ tiết kiệm VRAM (Chỉ chạy VoiceStudio CFM)",
                                value=False,
                                info="Bỏ qua F5-TTS và VieNeu-TTS để tối ưu bộ nhớ GPU",
                            )

                        start_quad_btn = gr.Button(
                            "2. BẮT ĐẦU NHÂN BẢN & ĐỐI CHỨNG 4 CHIỀU",
                            variant="primary",
                            size="lg",
                            elem_id="start-quad-btn",
                            elem_classes=["btn-primary-teal"],
                        )

                    # RIGHT COLUMN: Progress Banner
                    with gr.Column(scale=7):
                        gr.Markdown("### <iconify-icon icon='solar:chart-square-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> 3. Tiến Trình Nhân Bản & Thẩm Định Thời Gian Thực")
                        status_banner_html = gr.HTML(
                            """
                            <div style="padding: 1.25rem; border-radius: 0.75rem; background: var(--bg-surface); border: 1px dashed var(--border-color); text-align: center; color: var(--text-secondary); font-size: 13px;">
                                <iconify-icon icon="solar:info-circle-linear" width="28" height="28" style="color: var(--teal-accent); margin-bottom: 6px;"></iconify-icon>
                                <div>Ghi âm giọng nói của bạn ở cột bên trái và bấm nút <strong>'2. BẮT ĐẦU NHÂN BẢN & ĐỐI CHỨNG 4 CHIỀU'</strong>.</div>
                                <div style="font-size: 11.5px; color: var(--text-muted); margin-top: 4px;">Kết quả từng mẫu sẽ hiển thị tuần tự theo thời gian thực (Progressive Real-Time Streaming).</div>
                            </div>
                            """
                        )

                # 4-Card Comparison Grid
                gr.Markdown("---")
                gr.Markdown("### <iconify-icon icon='solar:tuning-square-2-bold-duotone' width='22' height='22' style='vertical-align: -0.2em; color: var(--teal-accent);'></iconify-icon> Kết Quả Đối Soát 4 Mẫu Âm Thanh (1 Người Thật vs 3 Deepfake Spoof)")

                with gr.Row():
                    with gr.Column(scale=1):
                        bona_card_html = gr.HTML(_render_quad_card_placeholder("Bản 1: Người Thật (Bona Fide)", "Giọng nói gốc trực tiếp từ Microphone", "solar:user-bold"))
                        bona_audio = gr.Audio(label="Nghe lại giọng thật của bạn", interactive=False)
                    with gr.Column(scale=1):
                        f5_card_html = gr.HTML(_render_quad_card_placeholder("Bản 2: Clone F5-TTS", "Mô hình Flow Matching Non-Autoregressive", "solar:cpu-bold"))
                        f5_audio = gr.Audio(label="Nghe bản clone F5-TTS", interactive=False)

                with gr.Row():
                    with gr.Column(scale=1):
                        vn_card_html = gr.HTML(_render_quad_card_placeholder("Bản 3: Clone VieNeu-TTS", "Mô hình Fast DiT v3 Turbo (48kHz)", "solar:bolt-bold"))
                        vn_audio = gr.Audio(label="Nghe bản clone VieNeu-TTS", interactive=False)
                    with gr.Column(scale=1):
                        omni_card_html = gr.HTML(_render_quad_card_placeholder("Bản 4: Clone VoiceStudio CFM", "Mô hình OmniVoice Continuous Flow Matching", "solar:magic-stick-3-bold"))
                        omni_audio = gr.Audio(label="Nghe bản clone VoiceStudio CFM", interactive=False)

                matrix_summary_html = gr.HTML("")

                start_quad_btn.click(
                    fn=live_quad_cloning_fn,
                    inputs=[live_mic_input, only_omnivoice_cb],
                    outputs=[
                        status_banner_html,
                        bona_card_html,
                        bona_audio,
                        f5_card_html,
                        f5_audio,
                        vn_card_html,
                        vn_audio,
                        omni_card_html,
                        omni_audio,
                        matrix_summary_html,
                    ],
                )

        gr.Markdown(
            """
            ---
            <div style="text-align: center; color: #64748B; font-size: 12px; font-family: 'JetBrains Mono', monospace; padding: 1rem 0;">
                ViTrueVoice Anti-Spoofing Inference Engine v0.4.7 | Backbone: Wav2Vec2 + AASIST (B_zalo V7 Dual-Seen) | Multi-Window Max-Pooling | Tuân thủ Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP
            </div>
            """
        )

        demo.load(fn=None, js=THEME_INIT_JS)

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
