import time
import random
from typing import Any, Optional, Dict
import numpy as np
import torch

from ..base import BaseTTSAdapter, SynthesisRequest, SynthesisResult


class KokoroAdapter(BaseTTSAdapter):
    """
    Adapter for Kokoro-Vietnamese (StyleTTS 2 + iSTFTNet).
    Unseen TTS benchmark engine for ViTrueVoice generalization evaluation (Hypothesis H2).
    """

    DEFAULT_VOICE = "diem_trinh"

    def __init__(
        self,
        default_voice: str = DEFAULT_VOICE,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        preload: bool = False,
    ):
        self.default_voice = default_voice
        self.device = device
        self.sample_rate = 24000
        self._engine = None
        self._loaded = False

        if preload:
            self._ensure_loaded()

    def _ensure_loaded(self):
        if not self._loaded:
            try:
                from kokoro_vietnamese import KokoroVietnamese
                self._engine = KokoroVietnamese(
                    voice=self.default_voice,
                    device=self.device,
                )
                self._loaded = True
            except ImportError as e:
                raise ImportError(
                    f"kokoro_vietnamese package not found: {e}. "
                    "Ensure external/Kokoro-Vietnamese is installed."
                ) from e

    @property
    def name(self) -> str:
        return "Kokoro-Vietnamese"

    def _resolve_voice(self, engine_preset: Optional[str], extra_params: Dict[str, Any]) -> str:
        """Resolve voice name from engine_preset or extra_params with fallback."""
        if engine_preset:
            if engine_preset.startswith("Kokoro-"):
                return engine_preset[len("Kokoro-"):]
            return engine_preset
        if "voice" in extra_params and extra_params["voice"]:
            return extra_params["voice"]
        return self.default_voice

    def synthesize(self, req: SynthesisRequest) -> SynthesisResult:
        """
        Synthesize speech from text using Kokoro-Vietnamese.
        Returns a SynthesisResult with 1D float32 audio and metadata.
        """
        self._ensure_loaded()

        voice = self._resolve_voice(req.engine_preset, req.extra_params)
        speed = float(req.extra_params.get("speed", 1.0))

        # Fix random seed for scientific reproducibility
        s = req.seed
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(s)

        t0 = time.perf_counter()
        
        # If the requested voice differs from engine's active voice, update if supported
        if hasattr(self._engine, "voice") and self._engine.voice != voice:
            try:
                self._engine.voice = voice
            except Exception:
                pass

        audio, phonemes = self._engine.synthesize(req.text, speed=speed)
        latency = time.perf_counter() - t0

        # Ensure audio is 1D float32
        if isinstance(audio, np.ndarray):
            if audio.ndim > 1:
                audio = audio.mean(axis=-1)
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
        else:
            audio = np.array(audio, dtype=np.float32)

        return SynthesisResult(
            audio=audio,
            sample_rate=self.sample_rate,
            engine_name=self.name,
            latency_s=latency,
            dtype="float32",
            metadata={
                "voice": voice,
                "phonemes": phonemes,
                "speed": speed,
                "seed": s,
            },
        )
