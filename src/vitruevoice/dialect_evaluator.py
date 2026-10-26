import numpy as np
import librosa
from typing import Dict, Tuple, Optional

# Giữ lại SPEAKER_DIALECT_MAP rỗng để tương thích ngược với các module cũ nếu có import
SPEAKER_DIALECT_MAP: Dict[str, str] = {}

def compute_pitch_dynamics(audio: np.ndarray, sr: int = 16000) -> Dict[str, float]:
    """
    Trích xuất các đặc trưng cao độ (F0 dynamics) và độ biến thiên prosody.
    Sử dụng thuật toán YIN để phát hiện F0 trong dải tiếng nói [65Hz - 400Hz].
    """
    if audio is None or len(audio) == 0:
        return {"mean_f0": 0.0, "std_f0": 0.0, "cv_f0": 0.0, "pitch_jump_rate": 0.0}

    sig = audio.astype(np.float32)
    if sig.ndim > 1:
        sig = sig.mean(axis=1)

    min_len = 2048
    if len(sig) < min_len:
        sig = np.pad(sig, (0, min_len - len(sig)))

    try:
        f0 = librosa.yin(sig, fmin=65, fmax=400, sr=sr, frame_length=2048, hop_length=512)
        voiced = f0[(f0 >= 65) & (f0 <= 400) & (~np.isnan(f0))]
        if len(voiced) < 5:
            return {"mean_f0": 0.0, "std_f0": 0.0, "cv_f0": 0.0, "pitch_jump_rate": 0.0}

        mean_f0 = float(np.mean(voiced))
        std_f0 = float(np.std(voiced))
        cv_f0 = float(std_f0 / (mean_f0 + 1e-6))

        df0 = np.abs(np.diff(voiced))
        pitch_jump_rate = float(np.mean(df0 > 25.0)) if len(df0) > 0 else 0.0

        return {
            "mean_f0": round(mean_f0, 2),
            "std_f0": round(std_f0, 2),
            "cv_f0": round(cv_f0, 4),
            "pitch_jump_rate": round(pitch_jump_rate, 4)
        }
    except Exception:
        return {"mean_f0": 0.0, "std_f0": 0.0, "cv_f0": 0.0, "pitch_jump_rate": 0.0}


def evaluate_prosodic_consistency(
    audio: np.ndarray,
    sr: int,
    ref_audio: Optional[np.ndarray] = None,
    ref_sr: int = 16000,
    expected_dialect: Optional[str] = None,
    engine_name: str = ""
) -> Tuple[float, bool, bool]:
    """
    Đánh giá độ nhất quán chất giọng & ngữ điệu tự động (Cổng 4: Voice & Prosody Quality Gate).
    
    CƠ CHẾ LABEL-FREE (HOÀN TOÀN KHÔNG CẦN NHÃN PHƯƠNG NGỮ):
    - Hoạt động trực tiếp dựa trên đặc trưng tín hiệu âm học giữa file tổng hợp và clip tham chiếu gốc.
    - So khớp dải cao độ cơ bản F0, độ phân tán nhịp điệu (CV_F0) và các bất thường nhảy pitch.
    - Áp dụng cho mọi tập dữ liệu lớn không có nhãn vùng miền.
    
    Trả về: (prosody_score: float, prosody_match: bool, prosody_drift: bool)
    """
    synth_stats = compute_pitch_dynamics(audio, sr=sr)

    if ref_audio is not None and len(ref_audio) > 0:
        ref_stats = compute_pitch_dynamics(ref_audio, sr=ref_sr)
    else:
        ref_stats = {"cv_f0": 0.18, "pitch_jump_rate": 0.05, "mean_f0": 140.0}

    ref_f0 = ref_stats.get("mean_f0", 140.0)
    synth_f0 = synth_stats.get("mean_f0", 140.0)

    # 1. Độ lệch cao độ cơ bản tương đối so với người nói thật
    if ref_f0 > 0:
        f0_rel_diff = abs(synth_f0 - ref_f0) / ref_f0
    else:
        f0_rel_diff = 0.0

    # 2. Độ lệch phân tán cao độ (Prosodic contour variance)
    synth_cv = synth_stats["cv_f0"]
    ref_cv = ref_stats.get("cv_f0", 0.18)
    cv_diff = abs(synth_cv - ref_cv)

    # 3. Bước nhảy âm vực dị thường (Vỡ giọng, biến dạng cao độ)
    synth_jumps = synth_stats["pitch_jump_rate"]
    ref_jumps = ref_stats.get("pitch_jump_rate", 0.05)
    jump_excess = max(0.0, synth_jumps - ref_jumps)

    # Tính điểm chất giọng (Trừng phạt lệch tone và bất thường prosody)
    penalty = (f0_rel_diff * 0.5) + (cv_diff * 0.8) + (jump_excess * 0.5)
    score = max(0.0, min(1.0, 1.0 - penalty))

    # Chuẩn đạt: điểm số >= 0.65 và độ lệch cao độ cơ bản <= 30%
    match = (score >= 0.65) and (f0_rel_diff <= 0.30)
    drift = not match

    return round(score, 4), match, drift



# Alias tương thích ngược với code cũ
evaluate_dialect_consistency = evaluate_prosodic_consistency


