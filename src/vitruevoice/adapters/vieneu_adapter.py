import time
import random
import numpy as np
import torch
from vieneu import Vieneu
from ..base import BaseTTSAdapter, SynthesisRequest, SynthesisResult

class VieNeuAdapter(BaseTTSAdapter):
    def __init__(self, mode: str = "v3turbo"):
        self._mode = mode
        self._engine = Vieneu(mode=mode)
        self.sample_rate = 48000

    @property
    def name(self) -> str:
        return "VieNeu-TTS-v3Turbo"

    def synthesize(self, req: SynthesisRequest) -> SynthesisResult:
        preset = req.engine_preset or "VieNeu-A"
        use_ref_codes = False if preset.endswith("-F") else True
        
        # Cố định seed
        s = req.seed
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(s)

        t0 = time.perf_counter()
        infer_kwargs = {
            "text": req.text,
            "ref_audio": req.ref_audio,
            "denoise": False,  # Audio sạch không denoise
            "use_ref_codes": use_ref_codes,
            "temperature": req.extra_params.get("temperature", 0.8),
            "top_k": req.extra_params.get("top_k", 25),
            "top_p": req.extra_params.get("top_p", 0.95)
        }
        
        audio = self._engine.infer(**infer_kwargs)
        latency = time.perf_counter() - t0
        
        if getattr(audio, "ndim", 1) > 1:
            audio = audio.mean(axis=1)
        audio = np.asarray(audio, dtype=np.float32)

        # Headroom protection
        max_amp = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
        if max_amp >= 0.98:
            audio = audio / max_amp * 0.95

        return SynthesisResult(
            audio=audio,
            sample_rate=self.sample_rate,
            engine_name=f"{self.name}[{preset}]",
            latency_s=round(latency, 3),
            metadata={
                "preset": preset,
                "use_ref_codes": use_ref_codes,
                "seed": s,
                "denoise": False
            }
        )
