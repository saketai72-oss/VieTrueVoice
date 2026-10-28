import os
import re
import numpy as np
import soundfile as sf
import librosa
import torch
try:
    import jiwer
except ImportError:
    jiwer = None
from typing import Tuple, Dict, Optional, List, Union
from pathlib import Path
from transformers import pipeline
try:
    from speechbrain.inference.speaker import EncoderClassifier
except ImportError:
    EncoderClassifier = None
from .base import QualityMetrics
from .dialect_evaluator import evaluate_dialect_consistency, evaluate_prosodic_consistency
from .text_utils import normalize_for_eval


class MultiGateEvaluator:
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        if jiwer is None:
            raise ImportError("jiwer is required for MultiGateEvaluator. Install it via pip install jiwer")
        if EncoderClassifier is None:
            raise ImportError("speechbrain is required for MultiGateEvaluator. Install it via pip install speechbrain")
        self.normalizer = jiwer.Compose([
            jiwer.ToLowerCase(),
            jiwer.RemovePunctuation(),
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip()
        ])
        
        self.asr_pipe = pipeline(
            "automatic-speech-recognition",
            model="nguyenvulebinh/wav2vec2-base-vietnamese-250h",
            device=0 if "cuda" in str(device).lower() else -1
        )
        
        self.spk_classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=os.path.expanduser("~/.cache/speechbrain/spkrec-ecapa-voxceleb"),
            run_opts={"device": device}
        )
        self._ref_emb_cache: Dict[str, torch.Tensor] = {}

    def transcribe_audio(self, audio_or_path: Union[str, Path, np.ndarray], sr: int = 16000) -> str:
        """Trích xuất transcript từ file âm thanh hoặc tín hiệu numpy bằng ASR pipeline (Label-Free)."""
        try:
            if isinstance(audio_or_path, (str, Path)):
                sig, srate = sf.read(str(audio_or_path), dtype="float32")
            else:
                sig, srate = np.asarray(audio_or_path, dtype=np.float32), sr
            if sig.ndim > 1:
                sig = sig.mean(axis=1)
            max_amp = float(np.max(np.abs(sig))) if len(sig) > 0 else 0.0
            if max_amp > 1.0:
                sig = sig / max_amp
            res = self.asr_pipe({"raw": sig, "sampling_rate": srate})
            return str(res.get("text", "")).strip()
        except Exception:
            return ""

    def extract_embedding(self, audio: np.ndarray, sr: int) -> torch.Tensor:
        sig = audio.copy()
        if sig.ndim > 1:
            sig = sig.mean(axis=1)
        if sr != 16000:
            sig = librosa.resample(sig, orig_sr=sr, target_sr=16000)
        tensor = torch.tensor(sig).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.spk_classifier.encode_batch(tensor)
        return emb.squeeze()

    def get_ref_embedding(self, ref_audio_path: str) -> Optional[torch.Tensor]:
        if not ref_audio_path or not os.path.exists(ref_audio_path):
            return None
        if ref_audio_path not in self._ref_emb_cache:
            sig, sr = sf.read(ref_audio_path)
            self._ref_emb_cache[ref_audio_path] = self.extract_embedding(sig, sr)
        return self._ref_emb_cache[ref_audio_path]

    def compute_enrollment_centroid(
        self,
        audio_paths: List[str],
        exclude_path: Optional[str] = None,
        k: int = 4
    ) -> Optional[torch.Tensor]:
        """Chuẩn hóa giao thức enrollment: tính centroid L2-normalized của K câu thật (loại clip reference)."""
        norm_exclude = os.path.abspath(exclude_path) if exclude_path else None
        valid_paths = [
            p for p in audio_paths
            if os.path.exists(p) and (norm_exclude is None or os.path.abspath(p) != norm_exclude)
        ]
        if not valid_paths:
            return None
        selected = valid_paths[:k]
        embs = []
        for p in selected:
            emb = self.get_ref_embedding(p)
            if emb is not None:
                embs.append(emb / (torch.norm(emb) + 1e-9))
        if not embs:
            return None
        centroid = torch.stack(embs, dim=0).mean(dim=0)
        return centroid / (torch.norm(centroid) + 1e-9)

    @staticmethod
    def get_band_ratios(y: np.ndarray, sr: int) -> Tuple[float, float]:
        if len(y) == 0:
            return 0.0, 0.0
        if sr != 48000:
            y = librosa.resample(y, orig_sr=sr, target_sr=48000)
            sr = 48000
        y_trim, _ = librosa.effects.trim(y, top_db=25)
        if len(y_trim) == 0:
            return 0.0, 0.0
        y_norm = y_trim / (np.sqrt(np.mean(y_trim**2)) + 1e-8)
        D = np.abs(librosa.stft(y_norm, n_fft=2048, hop_length=512))**2
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        total_e = float(np.sum(D)) + 1e-12
        b2_4 = float(np.sum(D[(freqs >= 2000) & (freqs < 4000), :])) / total_e
        b4_8 = float(np.sum(D[(freqs >= 4000) & (freqs < 8000), :])) / total_e
        return b2_4 * 100.0, b4_8 * 100.0

    def evaluate(
        self,
        audio: np.ndarray,
        sr: int,
        target_text: str,
        ref_audio_path: str,
        expected_dialect: Optional[str] = None,
        engine_name: str = "",
        strict_dialect: bool = True
    ) -> QualityMetrics:
        # Kiểm tra sanity tức thì đối với dữ liệu thô (Hard sanity pre-check)
        if audio is None or len(audio) == 0:
            return QualityMetrics(
                clean_wer=1.0, clean_cer=1.0, speaker_sim=0.0, band_2_4k_pct=0.0, band_4_8k_pct=0.0,
                is_catastrophic=True, gate1_pass=False, gate2_pass=False, gate3_pass=False, overall_pass=False,
                composite_score=0.0, is_valid=False, error_message="Audio rỗng (0 mẫu)",
                dialect_score=0.0, dialect_match=False, gate4_pass=False, dialect_drift=True
            )
            
        if np.isnan(audio).any() or np.isinf(audio).any():
            return QualityMetrics(
                clean_wer=1.0, clean_cer=1.0, speaker_sim=0.0, band_2_4k_pct=0.0, band_4_8k_pct=0.0,
                is_catastrophic=True, gate1_pass=False, gate2_pass=False, gate3_pass=False, overall_pass=False,
                composite_score=0.0, is_valid=False, error_message="Audio chứa giá trị bất thường (NaN/Inf)",
                dialect_score=0.0, dialect_match=False, gate4_pass=False, dialect_drift=True
            )

        dur = len(audio) / sr
        max_amp = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio**2)))

        if rms < 1e-4:
            return QualityMetrics(
                clean_wer=1.0, clean_cer=1.0, speaker_sim=0.0, band_2_4k_pct=0.0, band_4_8k_pct=0.0,
                is_catastrophic=True, gate1_pass=False, gate2_pass=False, gate3_pass=False, overall_pass=False,
                composite_score=0.0, is_valid=False, error_message="Audio gần như câm hoàn toàn (RMS < 1e-4)",
                dialect_score=0.0, dialect_match=False, gate4_pass=False, dialect_drift=True
            )

        # 1. Gate 1: ASR Clean WER/CER
        audio_float = audio.astype(np.float32)
        if max_amp > 1.0:
            audio_float = audio_float / max_amp
            
        try:
            asr_res = self.asr_pipe({"raw": audio_float, "sampling_rate": sr})
            raw_hyp = asr_res["text"].strip()
            clean_ref = normalize_for_eval(target_text)
            clean_hyp = normalize_for_eval(raw_hyp)
            clean_wer = float(jiwer.wer(clean_ref, clean_hyp)) if clean_ref else 1.0
            clean_cer = float(jiwer.cer(clean_ref, clean_hyp)) if clean_ref else 1.0
            gate1_pass = clean_wer <= 0.15
        except Exception as e:
            return QualityMetrics(
                clean_wer=1.0, clean_cer=1.0, speaker_sim=0.0, band_2_4k_pct=0.0, band_4_8k_pct=0.0,
                is_catastrophic=True, gate1_pass=False, gate2_pass=False, gate3_pass=False, overall_pass=False,
                composite_score=0.0, is_valid=False, error_message=f"Lỗi ASR pipeline: {e}",
                dialect_score=0.0, dialect_match=False, gate4_pass=False, dialect_drift=True
            )

        # 2. Gate 2: Speaker Similarity (Ngưỡng Cosine Sim nội bộ 0.4905)
        ref_emb = self.get_ref_embedding(ref_audio_path)
        if ref_emb is None:
            sim = 0.0
            gate2_pass = False
        else:
            synth_emb = self.extract_embedding(audio, sr)
            sim = float(torch.nn.functional.cosine_similarity(ref_emb.unsqueeze(0), synth_emb.unsqueeze(0)).cpu().item())
            gate2_pass = sim >= 0.4905

        # 3. Gate 3: Audio Sanity
        gate3_pass = (dur >= 0.5) and (max_amp <= 0.999) and (rms >= 0.01)

        # 4. Gate 4: Voice & Prosody Quality Consistency (So khớp trực tiếp từ ref_audio, Label-Free)
        dialect_score = 1.0
        dialect_match = True
        dialect_drift = False
        gate4_pass = True
        if ref_audio_path and os.path.exists(ref_audio_path):
            try:
                ref_sig, ref_srate = sf.read(ref_audio_path)
            except Exception:
                ref_sig = None
                ref_srate = 16000
            if ref_sig is not None:
                dialect_score, dialect_match, dialect_drift = evaluate_prosodic_consistency(
                    audio=audio,
                    sr=sr,
                    ref_audio=ref_sig,
                    ref_sr=ref_srate,
                    engine_name=engine_name
                )
                gate4_pass = dialect_match

        # 5. Phân tích hài âm & lỗi nghiêm trọng (Catastrophic Error: WER > 45% hoặc CER > 25%)
        b2_4, b4_8 = self.get_band_ratios(audio, sr)
        is_catastrophic = clean_wer > 0.45 or clean_cer > 0.25
        if clean_wer > 0.15:
            print(f"  🔍 [ASR Detail] Ref: '{clean_ref}' | Hyp: '{clean_hyp}' (WER={clean_wer*100:.1f}%, CER={clean_cer*100:.1f}%)")

        overall_pass = gate1_pass and gate2_pass and gate3_pass and gate4_pass and not is_catastrophic


        # 6. Composite Score phân hạng
        timbre_match = max(0.0, 1.0 - abs(b2_4 - 0.27) / 2.0)
        composite = (1.0 - clean_wer) * 0.35 + sim * 0.35 + dialect_score * 0.15 + timbre_match * 0.15
        if is_catastrophic or dialect_drift:
            composite -= 0.3

        return QualityMetrics(
            clean_wer=round(clean_wer, 4),
            clean_cer=round(clean_cer, 4),
            speaker_sim=round(sim, 4),
            band_2_4k_pct=round(b2_4, 2),
            band_4_8k_pct=round(b4_8, 2),
            is_catastrophic=is_catastrophic,
            gate1_pass=gate1_pass,
            gate2_pass=gate2_pass,
            gate3_pass=gate3_pass,
            overall_pass=overall_pass,
            composite_score=round(composite, 4),
            is_valid=True,
            dialect_score=dialect_score,
            dialect_match=dialect_match,
            gate4_pass=gate4_pass,
            dialect_drift=dialect_drift
        )
