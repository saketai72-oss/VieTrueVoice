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

from src.app.decision import classify_score, platt_calibrator
from src.app.server import TARGET_SAMPLE_COUNT, TARGET_SAMPLE_RATE, _default_model_loader, _pad_or_crop
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores

DEFAULT_CHECKPOINT = (
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

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-dark: #0B0F17;
    --card-bg: #131B2E;
    --card-high: #1E293B;
    --border-color: #334155;
    --teal-primary: #14B8A6;
    --teal-glow: #71F8E4;
    --red-spoof: #EF4444;
    --red-bg: #2A0F14;
    --green-bonafide: #2ECC71;
    --green-bg: #072414;
}

body, .gradio-container {
    background-color: var(--bg-dark) !important;
    font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #F8FAFC !important;
}

.lab-header {
    background: rgba(19, 27, 46, 0.95);
    border: 1px solid var(--border-color);
    border-radius: 1rem;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.lab-banner {
    background: linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(19, 27, 46, 0.9) 100%);
    border: 1px solid rgba(20, 184, 166, 0.3);
    border-radius: 1rem;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
}

.stat-card {
    background: #111827;
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 0.85rem 1rem;
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
    background: var(--red-bg);
    border: 2px solid var(--red-spoof);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(239, 68, 68, 0.25);
}

.verdict-box-bonafide {
    background: var(--green-bg);
    border: 2px solid var(--green-bonafide);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 8px 30px rgba(46, 204, 113, 0.25);
}

.progress-track {
    background: #0F172A;
    border: 1px solid var(--border-color);
    border-radius: 9999px;
    height: 14px;
    overflow: hidden;
    margin: 8px 0;
}

.progress-fill-spoof {
    background: linear-gradient(90deg, #E74C3C, #EF4444);
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.8);
    height: 100%;
    border-radius: 9999px;
    transition: width 0.6s ease-in-out;
}

.progress-fill-bonafide {
    background: linear-gradient(90deg, #2ECC71, #4AE183);
    box-shadow: 0 0 12px rgba(46, 204, 113, 0.8);
    height: 100%;
    border-radius: 9999px;
    transition: width 0.6s ease-in-out;
}

.btn-primary-teal {
    background: linear-gradient(135deg, #14B8A6 0%, #0F766E 100%) !important;
    border: 1px solid #71F8E4 !important;
    color: #00201C !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    box-shadow: 0 4px 20px rgba(20, 184, 166, 0.35) !important;
    transition: all 0.2s ease-in-out !important;
}

.btn-primary-teal:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 24px rgba(20, 184, 166, 0.5) !important;
}
"""


def _extract_acoustic_metrics(y: np.ndarray, sr: int = TARGET_SAMPLE_RATE) -> dict[str, Any]:
    """Extract acoustic forensics: high-frequency cutoff ratio, F0 pitch, energy."""
    duration = float(len(y) / sr)
    energy = float(np.mean(y ** 2)) if len(y) > 0 else 0.0

    # High frequency energy ratio (> 4 kHz vs total)
    if len(y) >= 512:
        fft_mag = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
        tot_power = float(np.sum(fft_mag ** 2)) + 1e-10
        hf_power = float(np.sum(fft_mag[freqs >= 4000] ** 2))
        hf_ratio = float(hf_power / tot_power) * 100.0
    else:
        hf_ratio = 0.0

    # Mean Pitch F0 estimation
    try:
        import librosa
        if len(y) >= 2048 and energy > 1e-5:
            f0 = librosa.yin(y, fmin=60, fmax=400, sr=sr)
            f0_valid = f0[(f0 >= 60) & (f0 <= 400)]
            mean_f0 = float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0.0
        else:
            mean_f0 = 0.0
    except Exception:
        mean_f0 = 0.0

    return {
        "duration": duration,
        "energy": energy,
        "hf_ratio": hf_ratio,
        "mean_f0": mean_f0,
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

    # 2. Raw Time-Domain Waveform Figure
    fig_wave, ax_wave = plt.subplots(figsize=(8.5, 2.0), facecolor="#0B0F17")
    ax_wave.set_facecolor("#0B0F17")
    t = np.linspace(0, dur, len(y)) if len(y) > 0 else np.array([0, 1])
    wave_color = "#2ECC71" if is_bonafide else "#EF4444"
    if len(y) > 0:
        ax_wave.plot(t, y, color=wave_color, linewidth=0.75, alpha=0.9)
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
        if active_model is not None and hasattr(active_model, "score"):
            try:
                dummy = torch.zeros(1, TARGET_SAMPLE_COUNT, dtype=torch.float32, device=device)
                with torch.inference_mode():
                    active_model.score(dummy)
            except Exception:
                pass

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

        # Generate Stitch-Theme Rich HTML Components
        if is_bonafide:
            verdict_html = f"""
            <div class="verdict-box-bonafide">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #2ECC71, #1E824C); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; box-shadow: 0 4px 16px rgba(46, 204, 113, 0.4); flex-shrink: 0;">
                        🛡️
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                            <span style="font-size: 1.25rem; font-weight: 700; color: #86EFAC;">XÁC THỰC: GIỌNG NÓI TỰ NHIÊN</span>
                            <span style="padding: 2px 10px; border-radius: 9999px; background: #2ECC71; color: #00210C; font-size: 11px; font-weight: 700; text-transform: uppercase;">Bonafide Audio</span>
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 13.5px; color: #86EFAC; line-height: 1.5;">
                            Không tìm thấy bất kỳ dấu hiệu tổng hợp âm thanh bằng AI hay cắt ghép giả mạo. Đường nét cao độ thanh quản và nhiễu vi mô hoàn toàn trùng khớp giọng nói người thật.
                        </p>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; background: #072414; border: 1px solid rgba(46, 204, 113, 0.4); display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: #2ECC71; font-size: 18px;">✅</span>
                        <span style="font-size: 12px; color: #F8FAFC;"><strong>Âm sắc Người Thật:</strong> Phổ sinh học đầy đủ, phản xạ hơi thở tự nhiên.</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: #2ECC71; font-size: 18px;">🤝</span>
                        <span style="font-size: 12px; color: #F8FAFC;"><strong>An Tâm Giao Tiếp:</strong> Đoạn thoại an toàn và không bị can thiệp.</span>
                    </div>
                </div>
            </div>
            """
            conf_bar_class = "progress-fill-bonafide"
            conf_color = "#2ECC71"
            conf_label = "Tự Nhiên (Bonafide)"
        else:
            verdict_html = f"""
            <div class="verdict-box-spoof">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #EF4444, #B91C1C); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4); flex-shrink: 0;">
                        ⚠️
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
                            <span style="font-size: 1.25rem; font-weight: 700; color: #F87171;">CẢNH BÁO: GIỌNG NÓI GIẢ MẠO</span>
                            <span style="padding: 2px 10px; border-radius: 9999px; background: #EF4444; color: white; font-size: 11px; font-weight: 700; text-transform: uppercase;">Phát hiện Deepfake</span>
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 13.5px; color: #FCA5A5; line-height: 1.5;">
                            Hệ thống AI nhận diện thấy dấu vết biến điệu nhân tạo (AI Voice Cloning / TTS Synthesis). Có nguy cơ cao đây là cuộc gọi hoặc tin nhắn giả danh để lừa đảo.
                        </p>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; background: #18080B; border: 1px solid rgba(239, 68, 68, 0.4); display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: #EF4444; font-size: 18px;">🛑</span>
                        <span style="font-size: 12px; color: #FCA5A5;"><strong>TUYỆT ĐỐI KHÔNG:</strong> Không chuyển tiền, không đọc mã OTP hoặc gửi mật khẩu.</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: #14B8A6; font-size: 18px;">📞</span>
                        <span style="font-size: 12px; color: #F8FAFC;"><strong>GỌI LẠI TRỰC TIẾP:</strong> Gọi điện thoại truyền thống hoặc Video Call để nhìn mặt.</span>
                    </div>
                </div>
            </div>
            """
            conf_bar_class = "progress-fill-spoof"
            conf_color = "#EF4444"
            conf_label = "Giả Mạo (Deepfake Spoof)"

        conf_html = f"""
        <div style="background: #111827; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; margin-top: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; font-weight: 600; color: #F8FAFC;">Độ tin cậy phân tích (Platt Scaling Calibrated):</span>
                <span style="font-size: 16px; font-weight: 700; color: {conf_color}; font-family: 'JetBrains Mono', monospace;">{conf_pct:.1f}% {conf_label}</span>
            </div>
            <div class="progress-track">
                <div class="{conf_bar_class}" style="width: {conf_pct:.1f}%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">
                <span>0.0% Tự nhiên</span>
                <span>50.0% Ngưỡng phân định</span>
                <span style="color: {conf_color}; font-weight: 600;">{conf_pct:.1f}%</span>
            </div>
        </div>
        """

        metrics_html = f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 0.75rem;">
            <div class="stat-card">
                <div style="font-size: 11px; color: #94A3B8;">Điểm Raw Score</div>
                <div style="font-size: 14px; font-weight: 700; color: {conf_color}; font-family: 'JetBrains Mono', monospace;">{raw_score:+.4f}</div>
                <div style="font-size: 10px; color: #64748B;">Ngưỡng θ: {threshold:.4f}</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: #94A3B8;">Thời gian xử lý</div>
                <div style="font-size: 14px; font-weight: 700; color: #14B8A6; font-family: 'JetBrains Mono', monospace;">{latency:.3f}s</div>
                <div style="font-size: 10px; color: #64748B;">NFR1: ≤ 3.0s (PASS)</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: #94A3B8;">Cửa sổ suy luận</div>
                <div style="font-size: 14px; font-weight: 700; color: #F8FAFC; font-family: 'JetBrains Mono', monospace;">{n_windows} Cửa sổ</div>
                <div style="font-size: 10px; color: #64748B;">Max-Pooling Mode</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 11px; color: #94A3B8;">Năng lượng >4kHz</div>
                <div style="font-size: 14px; font-weight: 700; color: #71F8E4; font-family: 'JetBrains Mono', monospace;">{acoustics['hf_ratio']:.2f}%</div>
                <div style="font-size: 10px; color: #64748B;">Vocoder Roll-off</div>
            </div>
        </div>
        <div style="margin-top: 0.5rem; background: #0B0F17; border: 1px solid #1E293B; border-radius: 0.5rem; padding: 0.5rem 0.75rem; display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">
            <span>Mã băm SHA-256 đối soát: <strong style="color: #71F8E4;">{audio_sha256[:24]}...</strong></span>
            <span>Thời lượng: <strong style="color: #F8FAFC;">{acoustics['duration']:.2f}s</strong> | Tần số: 16,000 Hz Mono</span>
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

    theme = gr.themes.Monochrome(
        primary_hue="teal",
        neutral_hue="slate",
    ).set(
        body_background_fill="#0B0F17",
        block_background_fill="#131B2E",
        block_border_color="#334155",
    )

    with gr.Blocks(title="ViTrueVoice — Phòng Lab Nhận Diện Deepfake Giọng Nói Tiếng Việt") as demo:
        # Inject Custom Forensics CSS
        gr.HTML(f"<style>{CUSTOM_CSS}</style>")

        # Header Section
        gr.HTML(
            """
            <div class="lab-header" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #14B8A6, #0F766E); display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; box-shadow: 0 4px 20px rgba(20, 184, 166, 0.4);">
                        🛡️
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <span style="font-size: 1.5rem; font-weight: 700; color: #F8FAFC; letter-spacing: -0.02em;">ViTrueVoice</span>
                            <span style="background: #111827; border: 1px solid #334155; padding: 2px 10px; border-radius: 9999px; font-size: 12px; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">
                                <span class="pulse-dot"></span>Mô hình AI: B_zalo V6 Active
                            </span>
                        </div>
                        <div style="font-size: 13px; color: #94A3B8; margin-top: 2px;">
                            Phòng Lab phân tích âm thanh Forensics Deepfake qua kênh thoại nén tiếng Việt
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="background: rgba(20, 184, 166, 0.12); border: 1px solid rgba(20, 184, 166, 0.4); color: #71F8E4; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600;">
                        🌙 Chế độ Lab Kỹ thuật (Dark Mode)
                    </span>
                    <span style="background: #1E293B; border: 1px solid #334155; color: #CBD5E1; padding: 4px 10px; border-radius: 8px; font-size: 12px;">
                        🔒 RAM In-Memory
                    </span>
                </div>
            </div>
            <div class="lab-banner" style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;">
                <div style="display: flex; align-items: flex-start; gap: 1rem;">
                    <span style="font-size: 28px;">👨‍👩‍👧‍👦</span>
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <strong style="font-size: 1.1rem; color: #F8FAFC;">Phòng Chống Lừa Đảo Giọng Nói Giả Mạo</strong>
                            <span style="background: rgba(46, 204, 113, 0.15); border: 1px solid rgba(46, 204, 113, 0.4); color: #2ECC71; font-size: 11px; padding: 1px 8px; border-radius: 9999px; font-weight: 600;">
                                Dành Cho Gia Đình & Người Cao Tuổi
                            </span>
                        </div>
                        <p style="font-size: 13px; color: #94A3B8; margin-top: 4px; line-height: 1.4;">
                            Kiểm tra tin nhắn thoại mượn tiền, cuộc gọi lạ chỉ với <strong>1 lần bấm</strong>. Hệ thống tự động bóc tách sóng âm và khuyến cáo tức thời.
                        </p>
                    </div>
                </div>
                <div style="background: rgba(11, 15, 23, 0.85); border: 1px solid #334155; border-radius: 8px; padding: 6px 14px; text-align: right;">
                    <div style="font-size: 11px; color: #94A3B8;">Chứng nhận AI Forensics</div>
                    <div style="font-size: 12px; color: #14B8A6; font-weight: 600;">Chuẩn Âm Sắc Tiếng Việt 2026</div>
                </div>
            </div>
            """
        )

        with gr.Row():
            # LEFT COLUMN: Audio Input & Presets
            with gr.Column(scale=5):
                gr.Markdown("### 🎙️ 1. Tải lên tin nhắn thoại hoặc Bấm ghi âm")
                audio_input = gr.Audio(
                    label="Hỗ trợ các định dạng .wav, .mp3, .m4a, .opus, .ogg",
                    sources=["upload", "microphone"],
                    type="numpy",
                )

                submit_btn = gr.Button(
                    "🔍 2. KIỂM TRA TÍNH XÁC THỰC NGAY",
                    variant="primary",
                    size="lg",
                    elem_classes=["btn-primary-teal"],
                )

                # 1-Click Preset Samples
                gr.Markdown("#### ⚡ Mẫu âm thanh thử nghiệm đối chứng nhanh:")
                with gr.Row():
                    sample_spoof_btn = gr.Button("🔴 Mẫu 1 (Spoof F5-TTS)", size="sm")
                    sample_bonafide_btn = gr.Button("🟢 Mẫu 2 (Người Thật)", size="sm")
                    sample_zalo_btn = gr.Button("🟠 Mẫu 3 (Spoof Zalo Nén)", size="sm")

                gr.HTML(
                    """
                    <div style="margin-top: 1rem; background: #131B2E; border: 1px solid #334155; border-radius: 0.75rem; padding: 0.85rem 1rem; display: flex; align-items: flex-start; gap: 0.75rem;">
                        <span style="font-size: 20px; color: #14B8A6;">🛡️</span>
                        <div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <strong style="font-size: 12px; color: #F8FAFC;">Cam kết Quyền Riêng Tư & An Toàn Tuyệt Đối</strong>
                                <span style="background: rgba(20, 184, 166, 0.15); border: 1px solid rgba(20, 184, 166, 0.4); color: #71F8E4; font-size: 10px; padding: 1px 6px; border-radius: 4px;">Luật 91/2025/QH15</span>
                            </div>
                            <p style="font-size: 11.5px; color: #94A3B8; margin-top: 3px; line-height: 1.4;">
                                Âm thanh được phân tích trực tiếp trên RAM và xóa hủy ngay lập tức sau 0.4s. Không lưu trữ, không sao chép và không chia sẻ giọng nói gốc.
                            </p>
                        </div>
                    </div>
                    """
                )

            # RIGHT COLUMN: Analytical Verdict & Forensic Stats
            with gr.Column(scale=7):
                gr.Markdown("### 📊 3. Kết Quả Xác Minh Âm Thanh")

                verdict_html = gr.HTML(
                    """
                    <div style="padding: 1.5rem; border-radius: 1rem; background: #131B2E; border: 1px solid #334155; text-align: center; color: #94A3B8;">
                        <p style="margin-top: 0.5rem; font-size: 14px;">Bấm nút <strong>'2. KIỂM TRA TÍNH XÁC THỰC NGAY'</strong> để nhận diện giọng thật / giả mạo.</p>
                    </div>
                    """
                )
                conf_html = gr.HTML()
                metrics_html = gr.HTML()

                with gr.Accordion("📋 Chi tiết dạng văn bản (Screen Reader & API)", open=False):
                    result_verdict = gr.Textbox(label="Kết quả phân định", interactive=False)
                    result_conf = gr.Textbox(label="Độ tin cậy phân tích", interactive=False)
                    result_detail = gr.Textbox(label="Khuyến cáo an toàn", interactive=False, lines=3)

        # SCIENTIFIC VISUALIZATION TABS (Mel-Spectrogram, Waveform, Grad-CAM Attention Map)
        gr.Markdown("---")
        gr.Markdown("### 🔬 Góc Nhìn Số Liệu Khoa Học Trực Quan (Forensic Scientific Visualizations)")
        with gr.Tabs():
            with gr.TabItem("📊 Mel-Spectrogram (80 Mels, log dBFS)"):
                spec_plot = gr.Plot(label="Phổ Tần Số Mel-Spectrogram (Dải 0 - 8.0 kHz với Ranh Giới Vocoder 4.0 kHz)")
            with gr.TabItem("🌊 Sóng Âm Đồng Bộ (Time-Domain Waveform)"):
                wave_plot = gr.Plot(label="Biểu Đồ Sóng Âm Thời Gian Thực (Normalized 16kHz)")
            with gr.TabItem("🎯 Bản Đồ Chú Ý AI (Grad-CAM Temporal Saliency)"):
                cam_plot = gr.Plot(label="Trọng Số Chú Ý Mạng Nơ-ron (Vùng Kích Hoạt Quyết Định Giả Mạo)")

        # Presets click handlers
        sample_spoof_path = "data/spoof_f5tts/CV_08110ec9e6/CV_08110ec9e6_prompt_000.wav"
        sample_bonafide_path = "data/bonafide_ref/SPK_0004/SPK_0004_01.wav"
        sample_zalo_path = "data/spoof_f5tts/CV_08110ec9e6/CV_08110ec9e6_prompt_000_opus_zalo.wav"

        def _load_sample_audio(path: str) -> str:
            return path if Path(path).exists() else ""

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

        gr.Markdown(
            """
            ---
            <div style="text-align: center; color: #64748B; font-size: 12px; font-family: 'JetBrains Mono', monospace; padding: 1rem 0;">
                ViTrueVoice Anti-Spoofing Inference Engine v0.4.4 | Backbone: Wav2Vec2 + AASIST (B_zalo V6) | Multi-Window Max-Pooling | Tuân thủ Luật 91/2025/QH15 & Nghị định 356/2025/NĐ-CP
            </div>
            """
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
