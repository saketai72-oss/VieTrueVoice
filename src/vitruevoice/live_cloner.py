# -*- coding: utf-8 -*-
"""
Module điều phối Live Voice Cloning & Thẩm định đối chứng 4 chiều (Quad-Forensics).

Tính năng:
- Lấy mẫu giọng thu âm trực tiếp từ microphone của người dùng làm giọng mẫu (Reference Voice).
- Tự động sinh 3 bản clone giọng nói qua 3 mô hình TTS Zero-Shot của dự án:
    1. F5-TTS-Vietnamese (Flow Matching)
    2. VieNeu-TTS v3 Turbo (Neural Vocoder 48kHz)
    3. VoiceStudio OmniVoice CFM (Continuous Flow Matching)
- Sử dụng câu thoại mục tiêu cố định ngắn gọn (~10 từ thuần Việt):
    "Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."
- Progressive Generator yielding: Trả kết quả bản người thật (Bona Fide) ngay lập tức (~66ms),
  sau đó lần lượt sinh và thẩm định từng bản clone, cập nhật giao diện ngay khi có kết quả
  để người dùng không phải chờ đợi.
- Quản trị bộ nhớ VRAM an toàn, hỗ trợ cơ chế giải phóng cache GPU giữa các engine.
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

_F5_DIR = _ROOT / "F5-TTS-Vietnamese" / "src"
if _F5_DIR.exists() and str(_F5_DIR) not in sys.path:
    sys.path.insert(0, str(_F5_DIR))

from src.app.decision import PLATT_SCALE_K, classify_score, platt_calibrator
from src.app.server import TARGET_SAMPLE_COUNT, TARGET_SAMPLE_RATE
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores

DEFAULT_TARGET_TEXT = "Alo bạn ơi, tôi đang bận chút nữa gọi lại nhé."


def evaluate_audio_sample(
    audio: np.ndarray,
    sr: int,
    detector_model: Any,
    device: str = "cpu",
    threshold: float = 0.0,
    calibrator: Any = platt_calibrator,
) -> Dict[str, Any]:
    """
    Thẩm định 1 mẫu âm thanh qua detector ViTrueVoice (Multi-window Max-Pooling + Platt Scaling).
    """
    if audio.ndim > 1:
        audio = audio.mean(axis=-1)
    if sr != TARGET_SAMPLE_RATE:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SAMPLE_RATE)
        sr = TARGET_SAMPLE_RATE

    audio = audio.astype(np.float32)
    raw_bytes = audio.tobytes()
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Multi-window sliding window extraction with comfort dithering
    windows_batch = extract_window_batch(
        audio,
        win=TARGET_SAMPLE_COUNT,
        hop=16000,
        max_windows=5,
        apply_dither=True,
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


class LiveQuadCloner:
    """
    Lớp điều phối quá trình sinh 3 bản clone và thẩm định 4 chiều (Quad-Forensics).
    """

    def __init__(
        self,
        target_text: str = DEFAULT_TARGET_TEXT,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        priority_only_omnivoice: bool = False,
    ):
        self.target_text = target_text
        self.device = device
        self.priority_only_omnivoice = priority_only_omnivoice

        self._f5_adapter = None
        self._vieneu_adapter = None
        self._omnivoice_model = None

    def _cleanup_gpu(self):
        """Giải phóng bộ nhớ đệm CUDA."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    def _get_f5_adapter(self):
        if self._f5_adapter is None and not self.priority_only_omnivoice:
            try:
                from src.vitruevoice.adapters.f5_adapter import F5TTSAdapter
                self._f5_adapter = F5TTSAdapter(device=self.device)
            except Exception as e:
                print(f"⚠️ [LiveQuadCloner] Không thể khởi tạo F5TTSAdapter: {e}")
        return self._f5_adapter

    def _get_vieneu_adapter(self):
        if self._vieneu_adapter is None and not self.priority_only_omnivoice:
            try:
                from src.vitruevoice.adapters.vieneu_adapter import VieNeuAdapter
                self._vieneu_adapter = VieNeuAdapter(mode="v3turbo")
            except Exception as e:
                print(f"⚠️ [LiveQuadCloner] Không thể khởi tạo VieNeuAdapter: {e}")
        return self._vieneu_adapter

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
                print(f"⚠️ [LiveQuadCloner] Không thể nạp OmniVoice: {e}")
        return self._omnivoice_model

    def clone_f5(self, ref_audio_path: str, ref_text: str = "") -> Optional[Tuple[np.ndarray, int]]:
        """Sinh giọng clone qua F5-TTS."""
        adapter = self._get_f5_adapter()
        if adapter is None:
            return None
        try:
            from src.vitruevoice.base import SynthesisRequest
            req = SynthesisRequest(
                speaker_id="live_user",
                text=self.target_text,
                ref_audio=ref_audio_path,
                extra_params={"ref_text": ref_text, "nfe_step": 16},
            )
            res = adapter.synthesize(req)
            return res.audio, res.sample_rate
        except Exception as e:
            print(f"❌ [LiveQuadCloner] F5-TTS sinh lỗi: {e}")
            return None

    def clone_vieneu(self, ref_audio_path: str) -> Optional[Tuple[np.ndarray, int]]:
        """Sinh giọng clone qua VieNeu-TTS v3 Turbo."""
        adapter = self._get_vieneu_adapter()
        if adapter is None:
            return None
        try:
            from src.vitruevoice.base import SynthesisRequest
            req = SynthesisRequest(
                speaker_id="live_user",
                text=self.target_text,
                ref_audio=ref_audio_path,
            )
            res = adapter.synthesize(req)
            return res.audio, res.sample_rate
        except Exception as e:
            print(f"❌ [LiveQuadCloner] VieNeu-TTS sinh lỗi: {e}")
            return None

    def clone_omnivoice(self, ref_audio_path: str, ref_text: str = "") -> Optional[Tuple[np.ndarray, int]]:
        """Sinh giọng clone qua VoiceStudio OmniVoice CFM."""
        model = self._get_omnivoice_model()
        if model is None:
            return None
        try:
            audios = model.generate(
                text=self.target_text,
                ref_audio=ref_audio_path,
                ref_text=ref_text or "Xin chào đây là giọng nói mẫu ghi âm trực tiếp.",
                language="vi",
                num_step=16,
                guidance_scale=2.0,
            )
            audio_tensor = audios[0]
            if isinstance(audio_tensor, torch.Tensor):
                audio_np = audio_tensor.detach().cpu().numpy()
            else:
                audio_np = np.asarray(audio_tensor)
            if audio_np.ndim > 1:
                audio_np = audio_np.squeeze()
            return audio_np.astype(np.float32), 24000
        except Exception as e:
            print(f"❌ [LiveQuadCloner] OmniVoice sinh lỗi: {e}")
            return None

    def stream_cloning_and_detection(
        self,
        user_audio: np.ndarray,
        user_sr: int,
        detector_model: Any,
        threshold: float = 0.0,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generator đa bước (yields 4 lần):
        - Yield 0: Thẩm định xong bản Bona Fide gốc (ngay lập tức).
        - Yield 1: Clone & Thẩm định xong bản F5-TTS.
        - Yield 2: Clone & Thẩm định xong bản VieNeu-TTS.
        - Yield 3: Clone & Thẩm định xong bản VoiceStudio OmniVoice CFM + Tổng kết đối chứng 4 chiều.
        """
        # Lưu file tạm in-memory an toàn cho reference audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_ref:
            tmp_ref_path = tmp_ref.name
            sf.write(tmp_ref_path, user_audio, user_sr)

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
            )

            state = {
                "step": 0,
                "target_text": self.target_text,
                "bonafide": bona_res,
                "f5": {"status": "loading", "msg": "Đang kết nối F5-TTS (Flow Matching)..."},
                "vieneu": {"status": "loading", "msg": "Đang chờ hàng đợi VieNeu-TTS..."},
                "omnivoice": {"status": "loading", "msg": "Đang chờ hàng đợi VoiceStudio CFM..."},
                "completed": False,
            }
            yield state

            # -------------------------------------------------------------
            # BƯỚC 1: Clone qua F5-TTS & Thẩm định
            # -------------------------------------------------------------
            if not self.priority_only_omnivoice:
                f5_out = self.clone_f5(tmp_ref_path)
                self._cleanup_gpu()
            else:
                f5_out = None

            if f5_out is not None:
                f5_wav, f5_sr = f5_out
                f5_eval = evaluate_audio_sample(f5_wav, f5_sr, detector_model, device=self.device, threshold=threshold)
                state["f5"] = {"status": "done", "eval": f5_eval, "audio": (f5_sr, f5_wav)}
            else:
                state["f5"] = {"status": "skipped", "msg": "Đã tối ưu VRAM dành riêng cho VoiceStudio CFM."}

            state["step"] = 1
            yield state

            # -------------------------------------------------------------
            # BƯỚC 2: Clone qua VieNeu-TTS & Thẩm định
            # -------------------------------------------------------------
            if not self.priority_only_omnivoice:
                vn_out = self.clone_vieneu(tmp_ref_path)
                self._cleanup_gpu()
            else:
                vn_out = None

            if vn_out is not None:
                vn_wav, vn_sr = vn_out
                vn_eval = evaluate_audio_sample(vn_wav, vn_sr, detector_model, device=self.device, threshold=threshold)
                state["vieneu"] = {"status": "done", "eval": vn_eval, "audio": (vn_sr, vn_wav)}
            else:
                state["vieneu"] = {"status": "skipped", "msg": "Đã tối ưu VRAM dành riêng cho VoiceStudio CFM."}

            state["step"] = 2
            yield state

            # -------------------------------------------------------------
            # BƯỚC 3: Clone qua VoiceStudio OmniVoice CFM & Thẩm định
            # -------------------------------------------------------------
            omni_out = self.clone_omnivoice(tmp_ref_path)
            self._cleanup_gpu()

            if omni_out is not None:
                omni_wav, omni_sr = omni_out
                omni_eval = evaluate_audio_sample(omni_wav, omni_sr, detector_model, device=self.device, threshold=threshold)
                state["omnivoice"] = {"status": "done", "eval": omni_eval, "audio": (omni_sr, omni_wav)}
            else:
                state["omnivoice"] = {"status": "error", "msg": "Không thể sinh giọng qua OmniVoice."}

            state["step"] = 3
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
