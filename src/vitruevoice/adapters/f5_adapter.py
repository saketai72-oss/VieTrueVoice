import os
import sys
import time
import random
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

# Bảo đảm f5_tts nằm trong path
f5_src = os.path.abspath("F5-TTS-Vietnamese/src")
if f5_src not in sys.path:
    sys.path.insert(0, f5_src)

from ..base import BaseTTSAdapter, SynthesisRequest, SynthesisResult

class F5TTSAdapter(BaseTTSAdapter):
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.sample_rate = 24000
        self._model = None
        self._vocoder = None
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            import shutil
            import glob
            from omegaconf import OmegaConf
            from huggingface_hub import hf_hub_download
            from f5_tts.infer.utils_infer import load_model, load_vocoder
            from f5_tts.model import DiT

            repo_id = "hynt/F5-TTS-Vietnamese-ViVoice"
            ckpt_path = hf_hub_download(repo_id=repo_id, filename="model_last.pt")
            vocab_src = hf_hub_download(repo_id=repo_id, filename="config.json")
            
            vocab_path = os.path.abspath("vocab.txt")
            if not os.path.exists(vocab_path):
                shutil.copy2(vocab_src, vocab_path)

            yaml_cands = glob.glob("**/F5TTS_Base.yaml", recursive=True)
            if yaml_cands:
                model_cfg = OmegaConf.load(yaml_cands[0]).model.arch
            else:
                model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4, text_mask_padding=False, pe_attn_head=1)

            self._model = load_model(DiT, model_cfg, ckpt_path, mel_spec_type="vocos", vocab_file=vocab_path, device=self.device)
            self._vocoder = load_vocoder(vocoder_name="vocos", is_local=False, device=self.device)
            self._loaded = True

    @property
    def name(self) -> str:
        return "F5-TTS-Vietnamese"

    def synthesize(self, req: SynthesisRequest) -> SynthesisResult:
        self._ensure_loaded()
        from f5_tts.infer.utils_infer import infer_process

        # Cố định seed
        s = req.seed
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(s)

        t0 = time.perf_counter()
        
        # Văn bản mục tiêu (đảm bảo dấu câu kết thúc)
        tgt_text = req.text.strip()
        if not tgt_text.endswith((".", "!", "?")):
            tgt_text += "."

        ref_text = req.extra_params.get("ref_text", "").strip()
        if ref_text and not ref_text.endswith((".", "!", "?")):
            ref_text += "."

        nfe_step = req.extra_params.get("nfe_step", 32)

        final_wave, sr, _ = infer_process(
            ref_audio=req.ref_audio,
            ref_text=ref_text,
            gen_text=tgt_text,
            model_obj=self._model,
            vocoder=self._vocoder,
            mel_spec_type="vocos",
            device=self.device,
            nfe_step=nfe_step
        )
        latency = time.perf_counter() - t0

        if getattr(final_wave, "ndim", 1) > 1:
            final_wave = final_wave.mean(axis=1)
        final_wave = np.asarray(final_wave, dtype=np.float32)

        # Headroom Scaling: Chống clipping Gate 3
        max_val = float(np.max(np.abs(final_wave))) if len(final_wave) > 0 else 0.0
        if max_val >= 0.98:
            final_wave = final_wave / max_val * 0.95

        return SynthesisResult(
            audio=final_wave,
            sample_rate=sr,
            engine_name=self.name,
            latency_s=round(latency, 3),
            metadata={
                "nfe_step": nfe_step,
                "seed": s,
                "headroom_applied": (max_val >= 0.98)
            }
        )
