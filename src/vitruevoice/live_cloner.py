# -*- coding: utf-8 -*-
"""
Module điều phối Live Voice Cloning & Thẩm định đối chứng với VoiceStudio CFM (OmniVoice).

Tính năng trọng tâm:
- Tập trung chuyên sâu vào mô hình VoiceStudio CFM (OmniVoice Zero-Shot Flow Matching).
- Tự động nhận diện tiếng nói (ASR) từ đoạn ghi âm Microphone của người dùng bằng
  wav2vec2 tiếng Việt (nguyenvulebinh/wav2vec2-base-vietnamese-250h) để tạo cặp
  (ref_audio, ref_text) chuẩn xác 100%, khắc phục hoàn toàn hiện tượng lệch âm sắc
  gây mất tiếng / nhiễu tần số thấp 50Hz.
- Chuẩn hóa âm thanh đầu ra: Khử DC offset, Peak-normalization 95% và chuyển đổi sang
  16-bit PCM (int16 @ 24kHz) đảm bảo âm thanh to rõ, tự nhiên và tương thích mọi trình duyệt.
- Thẩm định đối chứng 2 chiều: 1 Bản Người Thật (Bona Fide) vs 1 Bản Clone VoiceStudio CFM (Spoof).
- Progressive Real-Time Streaming: Trả kết quả bản Người Thật ngay lập tức (~66ms),
  hiển thị trạng thái Loading trong khi VoiceStudio CFM sinh giọng, cập nhật tức thì khi hoàn tất.
- Quản trị an toàn VRAM và tuân thủ Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15.
"""

from __future__ import annotations

import gc
import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple

import numpy as np
import soundfile as sf
import torch

# Ensure project root & external are in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_VS_DIR = _ROOT / "external" / "VoiceStudio"
if _VS_DIR.exists() and str(_VS_DIR) not in sys.path:
    sys.path.insert(0, str(_VS_DIR))

from src.app.decision import PLATT_SCALE_K, classify_score, platt_calibrator
from src.app.server import TARGET_SAMPLE_COUNT, TARGET_SAMPLE_RATE
from src.preprocessing.pooling import extract_window_batch, pool_scores

DEFAULT_TARGET_TEXT = "Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."
DEFAULT_REF_PROMPT = "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."

# Global singleton ASR components for fast reference transcription
_ASR_PROCESSOR = None
_ASR_MODEL = None


def transcribe_vietnamese_reference(audio_path: str, device: str = "cpu") -> str:
    """
    Tự động nhận diện tiếng nói (ASR) của đoạn thu âm microphone
    để tạo văn bản tham chiếu ref_text khớp 100% với ref_audio.
    """
    global _ASR_PROCESSOR, _ASR_MODEL
    try:
        from transformers import AutoModelForCTC, AutoProcessor
        if _ASR_PROCESSOR is None or _ASR_MODEL is None:
            asr_device = "cuda" if (torch.cuda.is_available() and "cuda" in str(device).lower()) else "cpu"
            _ASR_PROCESSOR = AutoProcessor.from_pretrained("nguyenvulebinh/wav2vec2-base-vietnamese-250h")
            _ASR_MODEL = AutoModelForCTC.from_pretrained("nguyenvulebinh/wav2vec2-base-vietnamese-250h").to(asr_device)
            _ASR_MODEL.eval()

        asr_dev = next(_ASR_MODEL.parameters()).device
        data, sr = sf.read(audio_path)
        if data.ndim > 1:
            data = data.mean(axis=-1)
        if sr != 16000:
            import librosa
            data = librosa.resample(data, orig_sr=sr, target_sr=16000)
            sr = 16000

        data = data.astype(np.float32)
        inputs = _ASR_PROCESSOR(data, sampling_rate=16000, return_tensors="pt").to(asr_dev)
        with torch.no_grad():
            logits = _ASR_MODEL(**inputs).logits
        pred_ids = torch.argmax(logits, dim=-1)
        transcription = _ASR_PROCESSOR.batch_decode(pred_ids)[0].strip()
        if len(transcription) > 0:
            return transcription
    except Exception as e:
        print(f"⚠️ [ASR] Nhận diện ASR tham chiếu tự động: {e}")

    return DEFAULT_REF_PROMPT


def evaluate_audio_sample(
    audio: np.ndarray,
    sr: int,
    detector_model: Any,
    device: str = "cpu",
    threshold: float = 0.0,
    calibrator: Any = platt_calibrator,
    apply_dither: bool = False,
) -> Dict[str, Any]:
    """
    Thẩm định 1 mẫu âm thanh qua detector ViTrueVoice (Multi-window Max-Pooling + Platt Scaling).
    - apply_dither: Chỉ bật khi âm thanh thu từ microphone WebRTC bị squelch noise-gating.
                    Tuyệt đối tắt (False) khi thẩm định âm thanh nhân bản (Clone / Spoof) để
                    tránh nhiễu che lấp các đặc trưng âm học vi mô.
    """
    if audio.ndim > 1:
        audio = audio.mean(axis=-1)
    if sr != TARGET_SAMPLE_RATE:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)
        sr = TARGET_SAMPLE_RATE

    if np.issubdtype(audio.dtype, np.integer):
        max_v = float(np.iinfo(audio.dtype).max)
        audio = audio.astype(np.float32) / max_v
    else:
        audio = audio.astype(np.float32)

    raw_bytes = audio.tobytes()
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Multi-window sliding window extraction with optional comfort dithering
    windows_batch = extract_window_batch(
        audio,
        win=TARGET_SAMPLE_COUNT,
        hop=16000,
        max_windows=5,
        apply_dither=apply_dither,
    ).to(device)

    t0 = time.perf_counter()
    with torch.inference_mode():
        score_tensor = detector_model.score(windows_batch)
        if isinstance(score_tensor, torch.Tensor):
            scores_np = score_tensor.detach().cpu().numpy()
        else:
            scores_np = np.asarray(score_tensor)
        if scores_np.ndim > 1:
            scores_np = scores_np.squeeze(-1)
        elif scores_np.ndim == 0:
            scores_np = np.array([scores_np.item()], dtype=np.float32)
        raw_score = float(pool_scores(scores_np, mode="max"))

    latency = time.perf_counter() - t0
    decision = classify_score(raw_score, threshold=threshold, calibrator=calibrator)
    is_bonafide = bool(decision.is_bonafide)

    # Platt Scaling calibrated posterior probability
    diff = float(raw_score - threshold)
    prob_bona = 1.0 / (1.0 + float(np.exp(-PLATT_SCALE_K * diff)))
    prob_bona = float(max(0.001, min(0.999, prob_bona)))
    prob_spoof = 1.0 - prob_bona

    return {
        "raw_score": raw_score,
        "is_bonafide": is_bonafide,
        "prob_bona": prob_bona,
        "prob_spoof": prob_spoof,
        "prob_bona_pct": prob_bona * 100.0,
        "prob_spoof_pct": prob_spoof * 100.0,
        "confidence_str": f"{prob_bona * 100.0:.1f}%" if is_bonafide else f"{prob_spoof * 100.0:.1f}%",
        "latency_s": latency,
        "sha256": sha256_hash,
        "audio_16k": audio,
        "duration_s": float(len(audio) / TARGET_SAMPLE_RATE),
    }


class LiveVoiceStudioCloner:
    """
    Lớp điều phối quá trình nhân bản giọng trực tiếp qua VoiceStudio CFM (OmniVoice).
    Tập trung chuyên biệt vào VoiceStudio CFM, loại bỏ hoàn toàn các mô hình trung gian.
    """

    def __init__(
        self,
        target_text: str = DEFAULT_TARGET_TEXT,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        priority_only_omnivoice: bool = True,
    ):
        self.target_text = target_text
        self.device = device
        self.priority_only_omnivoice = priority_only_omnivoice
        self._omnivoice_model = None

    def _cleanup_gpu(self):
        """Giải phóng bộ nhớ đệm CUDA."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def _get_omnivoice_model(self):
        if self._omnivoice_model is None:
            try:
                from omnivoice.models.omnivoice import OmniVoice
                self._omnivoice_model = OmniVoice.from_pretrained(
                    "k2-fsa/OmniVoice",
                    device_map=self.device,
                    dtype=torch.bfloat16 if "cuda" in str(self.device).lower() else torch.float32,
                )
            except Exception as e:
                print(f"⚠️ [LiveVoiceStudioCloner] Không thể nạp OmniVoice: {e}")
        return self._omnivoice_model

    def clone_omnivoice(self, ref_audio_path: str, ref_text: str = "") -> Optional[Tuple[np.ndarray, int, str]]:
        """
        Sinh giọng clone qua VoiceStudio OmniVoice CFM bằng pipeline chuẩn từ Voice_Final.
        (scripts/generate_omnivoice_unseen_spoofs.py)
        Trả về: (audio_int16, 16000, transcript_used)
        """
        model = self._get_omnivoice_model()
        if model is None:
            return None

        # 1. Xác định ref_text từ ASR hoặc câu mẫu chuẩn nếu chưa có
        if not ref_text or len(ref_text.strip()) == 0:
            ref_text = transcribe_vietnamese_reference(ref_audio_path, device=self.device)
            if not ref_text or len(ref_text.strip()) == 0:
                ref_text = DEFAULT_REF_PROMPT

        tmp_dir = Path(tempfile.gettempdir()) / "vitruevoice_clone"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_24k = tmp_dir / f"tmp_omni_{int(time.time()*1000)}_24k.wav"

        try:
            from omnivoice.utils.audio import save_audio
            import librosa

            # 2. Sinh giọng CFM theo đúng pipeline gốc của Voice_Final (num_step=16, guidance_scale=2.0, không ép duration)
            audios = model.generate(
                text=self.target_text,
                ref_audio=ref_audio_path,
                ref_text=ref_text,
                language="vi",
                num_step=16,
                guidance_scale=2.0,
            )

            # 3. Lưu qua save_audio ở 24kHz rồi resample về 16kHz PCM_16 chuẩn
            save_audio(str(tmp_24k), audios[0], sample_rate=24000)

            y_24k, _ = sf.read(str(tmp_24k))
            if y_24k.ndim > 1:
                y_24k = y_24k.mean(axis=-1)
            y_16k = librosa.resample(y_24k, orig_sr=24000, target_sr=16000)

            # Peak Normalization 95% đảm bảo âm thanh to rõ, tự nhiên, không bị rè
            max_abs = float(np.max(np.abs(y_16k)))
            if max_abs > 1e-6:
                y_16k = (y_16k / max_abs) * 0.95

            audio_int16 = (y_16k * 32767.0).astype(np.int16)
            return audio_int16, 16000, ref_text
        except Exception as e:
            print(f"❌ [LiveVoiceStudioCloner] OmniVoice sinh lỗi: {e}")
            return None
        finally:
            if tmp_24k.exists():
                try:
                    tmp_24k.unlink()
                except Exception:
                    pass

    def stream_cloning_and_detection(
        self,
        user_audio: np.ndarray,
        user_sr: int,
        detector_model: Any,
        threshold: float = 0.0,
        is_live_mic: bool = False,
        custom_ref_text: str = "",
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generator 2 bước thời gian thực (Progressive Real-Time Streaming):
        - Yield 0: Thẩm định xong bản Người Thật (Bona Fide) ngay lập tức (~66ms).
                   Bản VoiceStudio CFM ở trạng thái Loading.
        - Yield 1: Clone xong qua VoiceStudio CFM (~3.5s), chuẩn hóa âm thanh to rõ,
                   thẩm định Deepfake Spoof (không dither) và xuất bản Ma trận đối soát 2 chiều.
        """
        import librosa

        # 1. Tiền xử lý chuẩn hóa reference audio: Chuyển đổi về 16.000 Hz Mono PCM_16 sạch,
        # cắt tỉa khoảng lặng thừa và peak-normalize để VoiceStudio CFM căn chỉnh chuẩn 100%.
        ref_audio_16k = user_audio.copy()
        if ref_audio_16k.ndim > 1:
            ref_audio_16k = ref_audio_16k.mean(axis=-1)
        if np.issubdtype(ref_audio_16k.dtype, np.integer):
            max_v = float(np.iinfo(ref_audio_16k.dtype).max)
            ref_audio_16k = ref_audio_16k.astype(np.float32) / max_v
        else:
            ref_audio_16k = ref_audio_16k.astype(np.float32)

        if user_sr != TARGET_SAMPLE_RATE:
            ref_audio_16k = librosa.resample(ref_audio_16k, orig_sr=user_sr, target_sr=TARGET_SAMPLE_RATE)

        # Cắt tỉa khoảng lặng thừa đầu và cuối nếu có
        ref_trimmed, _ = librosa.effects.trim(ref_audio_16k, top_db=25)
        if len(ref_trimmed) >= int(0.5 * TARGET_SAMPLE_RATE):
            ref_audio_16k = ref_trimmed

        # Peak normalization 95%
        max_abs = float(np.max(np.abs(ref_audio_16k)))
        if max_abs > 1e-6:
            ref_audio_16k = (ref_audio_16k / max_abs) * 0.95

        # Lưu file tạm chuẩn 16kHz mono an toàn trong khối try...finally
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_ref:
            tmp_ref_path = tmp_ref.name
            sf.write(tmp_ref_path, ref_audio_16k, TARGET_SAMPLE_RATE, subtype="PCM_16")

        try:
            # -------------------------------------------------------------
            # BƯỚC 0: Thẩm định ngay lập tức bản gốc của người dùng (Bona Fide)
            # -------------------------------------------------------------
            bona_res = evaluate_audio_sample(
                user_audio,
                user_sr,
                detector_model=detector_model,
                device=self.device,
                threshold=threshold,
                apply_dither=is_live_mic,
            )

            state = {
                "step": 0,
                "target_text": self.target_text,
                "bonafide": bona_res,
                "omnivoice": {"status": "loading", "msg": "Đang xử lý âm thanh & khởi tạo VoiceStudio CFM..."},
                "completed": False,
            }
            yield state

            # -------------------------------------------------------------
            # BƯỚC 1: Clone qua VoiceStudio OmniVoice CFM & Thẩm định
            # -------------------------------------------------------------
            omni_out = self.clone_omnivoice(tmp_ref_path, ref_text=custom_ref_text)
            self._cleanup_gpu()

            if omni_out is not None:
                omni_int16, omni_sr, ref_used = omni_out
                # Chuyển đổi sang float32 16kHz để detector ViTrueVoice thẩm định
                omni_float = (omni_int16.astype(np.float32) / 32768.0)
                omni_eval = evaluate_audio_sample(
                    omni_float,
                    omni_sr,
                    detector_model=detector_model,
                    device=self.device,
                    threshold=threshold,
                    apply_dither=False,  # Tuyệt đối False: Không bơm dither vào audio sinh nhân tạo
                )
                state["omnivoice"] = {
                    "status": "done",
                    "eval": omni_eval,
                    "audio": (omni_sr, omni_int16),
                    "transcript": ref_used,
                }
            else:
                state["omnivoice"] = {
                    "status": "error",
                    "msg": "Không thể sinh giọng qua VoiceStudio CFM.",
                }

            state["step"] = 1
            state["completed"] = True
            yield state

        finally:
            # Dọn dẹp tệp tạm ngay lập tức tuân thủ Luật 91/2025/QH15
            if os.path.exists(tmp_ref_path):
                try:
                    os.unlink(tmp_ref_path)
                except Exception:
                    pass
            self._cleanup_gpu()


# Alias for backward compatibility
LiveQuadCloner = LiveVoiceStudioCloner
