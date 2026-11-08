"""Adapter cho Suno Bark (Autoregressive GPT + EnCodec) trong chuẩn BaseTTSAdapter."""
from __future__ import annotations

import time
from typing import Any
import numpy as np
import torch

from src.vitruevoice.base import BaseTTSAdapter, SynthesisRequest, SynthesisResult


class BarkAdapter(BaseTTSAdapter):
    """Adapter tích hợp mô hình Suno Bark vào ViTrueVoice."""

    def __init__(
        self,
        model_name: str = "suno/bark-small",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        preload: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.sample_rate = 24000
        self._processor = None
        self._model = None
        self._loaded = False
        if preload:
            self._load_engine()

    @property
    def name(self) -> str:
        return "Suno-Bark"

    def _load_engine(self) -> None:
        if self._loaded:
            return
        from transformers import AutoProcessor, BarkModel

        self._processor = AutoProcessor.from_pretrained(self.model_name)
        self._model = BarkModel.from_pretrained(self.model_name).to(self.device)
        self._loaded = True

    def _resolve_voice(self, preset: str | None, extra_params: dict[str, Any]) -> str | None:
        if extra_params and "voice_preset" in extra_params:
            return str(extra_params["voice_preset"])
        if preset and preset.startswith("Bark-"):
            return preset.replace("Bark-", "")
        return preset

    def synthesize(self, req: SynthesisRequest) -> SynthesisResult:
        if not self._loaded:
            self._load_engine()

        voice_preset = self._resolve_voice(req.engine_preset, req.extra_params)
        start_t = time.perf_counter()

        if voice_preset:
            inputs = self._processor(req.text, voice_preset=voice_preset)
        else:
            inputs = self._processor(req.text)

        # Move tensors to device
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}

        with torch.no_grad():
            audio_array = self._model.generate(**inputs)

        audio_np = audio_array.squeeze().cpu().numpy().astype(np.float32)
        max_val = float(np.max(np.abs(audio_np))) if len(audio_np) > 0 else 1.0
        if max_val > 1.0:
            audio_np = audio_np / max_val

        dur = float(len(audio_np) / self.sample_rate)
        lat = float(time.perf_counter() - start_t)

        return SynthesisResult(
            audio=audio_np,
            sample_rate=self.sample_rate,
            engine_name=self.name,
            duration_s=dur,
            latency_s=lat,
            metadata={
                "voice_preset": voice_preset,
                "model_name": self.model_name,
            },
        )
