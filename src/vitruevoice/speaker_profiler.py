"""
Module trích xuất hồ sơ người nói (Speaker Profiler & Reference Selector) cho ViTrueVoice.
Triển khai:
1. Tính ngưỡng nhận dạng sinh trắc học riêng cho từng Speaker (Per-Speaker Calibrated Threshold)
   có loại trừ reference clip và áp dụng empirical shrinkage cho phương sai mẫu nhỏ.
2. Tuyển chọn Reference tối ưu 2 tầng: LOO Embedding Proximity kết hợp Probe Synthesis đầu ra.
3. Ghép nối audio tự động có kiểm soát (chỉ ghép clip cùng speaker khi không có clip đơn 4-8s).
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import soundfile as sf
import torch
import logging

logger = logging.getLogger(__name__)

class SpeakerProfiler:
    def __init__(self, evaluator=None, device: Optional[str] = None):
        if evaluator is not None:
            self.evaluator = evaluator
        else:
            from .evaluator import MultiGateEvaluator
            self.evaluator = MultiGateEvaluator(device=device)
        self.device = self.evaluator.device
        self._emb_cache: Dict[str, np.ndarray] = {}

    def extract_embedding(self, audio_path: str) -> np.ndarray:
        """Trích xuất 192-d normalized embedding từ file audio với cơ chế cache."""
        path_str = str(audio_path)
        if path_str in self._emb_cache:
            return self._emb_cache[path_str]

        wav, sr = sf.read(path_str, dtype="float32")
        emb = self.evaluator.extract_embedding(wav, sr).cpu().numpy()
        norm = np.linalg.norm(emb)
        norm_emb = emb / (norm + 1e-9) if norm > 0 else emb
        self._emb_cache[path_str] = norm_emb
        return norm_emb

    def compute_speaker_threshold(
        self,
        speaker_id: str,
        bona_files: List[str],
        ref_to_exclude: Optional[str] = None,
        floor_threshold: float = 0.4905,
        pooled_std: float = 0.08,
        safety_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Tính toán phân phối Cosine Sim giữa các câu thật (bona fide) của chính người đó.
        - Loại trừ clip reference khỏi tập tính toán để tránh thiên lệch (leave-out bias).
        - Dùng empirical shrinkage: sigma = alpha * sigma_local + (1 - alpha) * pooled_std
          để ổn định phương sai khi cỡ mẫu n < 10.
        - Calibrated Threshold T_spk = max(floor_threshold, min(0.62, mean_sim - safety_multiplier * sigma))
          tránh ngưỡng bị kéo lên quá cao so với trần zero-shot (~0.58).
        """
        eval_files = [f for f in bona_files if str(f) != str(ref_to_exclude)]
        
        if len(eval_files) < 2:
            return {
                "speaker_id": speaker_id,
                "calibrated_threshold": floor_threshold,
                "mean_bona_sim": floor_threshold,
                "std_bona_sim": pooled_std,
                "num_pairs": 0,
                "note": "Không đủ file để tính phân phối bona fide, dùng floor threshold."
            }

        embs = [self.extract_embedding(f) for f in eval_files]
        pairwise_sims = []
        for i in range(len(embs)):
            for j in range(i + 1, len(embs)):
                sim = float(np.dot(embs[i], embs[j]))
                pairwise_sims.append(sim)

        mean_sim = float(np.mean(pairwise_sims))
        local_std = float(np.std(pairwise_sims))
        
        # Shrinkage variance theo cỡ mẫu n
        n = len(eval_files)
        alpha = min(1.0, n / 10.0)
        sigma = alpha * local_std + (1.0 - alpha) * pooled_std
        
        # Ngưỡng sinh trắc học riêng cho spoofing:
        # T_spk không vượt quá 0.62 để không triệt tiêu các mẫu clone đạt chuẩn zero-shot
        calibrated = max(floor_threshold, min(0.62, mean_sim - safety_multiplier * sigma))

        return {
            "speaker_id": speaker_id,
            "calibrated_threshold": round(calibrated, 4),
            "mean_bona_sim": round(mean_sim, 4),
            "std_bona_sim": round(sigma, 4),
            "local_std": round(local_std, 4),
            "num_pairs": len(pairwise_sims),
            "num_files": n,
            "note": "Calibrated với leave-out reference và shrinkage variance."
        }

    def prepare_reference_clip(
        self,
        candidate_paths: List[str],
        target_dir: str,
        speaker_id: str,
        min_dur: float = 3.5,
        max_dur: float = 7.5,
        allow_stitching: bool = False
    ) -> List[str]:
        """
        Lọc các clip sạch 3.5–7.5s. Ưu tiên tuyệt đối clip đơn tự nhiên đủ thời lượng.
        Chỉ cho phép ghép nối nếu allow_stitching=True và không có clip đơn nào đạt 3.5s.
        """
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        valid_refs = []
        short_clips = []
        
        for p in candidate_paths:
            info = sf.info(str(p))
            if min_dur <= info.duration <= max_dur:
                valid_refs.append(str(p))
            elif info.duration < min_dur:
                short_clips.append(str(p))

        # Nếu hoàn toàn không có clip đơn đủ thời lượng và cho phép ghép
        if not valid_refs and allow_stitching and len(short_clips) >= 2:
            logger.warning(f"Speaker {speaker_id} không có clip {min_dur}-{max_dur}s. Tạm thời ghép clip ngắn.")
            for idx in range(0, len(short_clips) - 1, 2):
                f1, f2 = short_clips[idx], short_clips[idx + 1]
                w1, sr1 = sf.read(f1, dtype="float32")
                w2, sr2 = sf.read(f2, dtype="float32")
                if sr1 != sr2:
                    continue
                # Khoảng dừng tự nhiên 50ms (tránh dead silence 200ms gây ngắt mạch token NeuCodec)
                silence = np.zeros(int(sr1 * 0.05), dtype=np.float32)
                stitched = np.concatenate([w1, silence, w2])
                dur = len(stitched) / sr1
                if min_dur <= dur <= max_dur:
                    out_f = target_path / f"{speaker_id}_stitched_{idx}_{Path(f1).stem}_{Path(f2).stem}.wav"
                    sf.write(str(out_f), stitched, sr1)
                    valid_refs.append(str(out_f))

        return valid_refs

    def select_best_reference_loo(
        self,
        speaker_id: str,
        candidate_refs: List[str],
        held_out_audios: List[str]
    ) -> Dict[str, Any]:
        """
        Tuyển chọn sơ bộ bằng Leave-One-Out (LOO) Embedding Proximity:
        Xếp hạng các clip tham chiếu theo khoảng cách trung bình Cosine Sim so với các câu thật còn lại.
        """
        if not candidate_refs:
            raise ValueError(f"Không có candidate reference nào cho {speaker_id}")
            
        if not held_out_audios:
            return {
                "speaker_id": speaker_id,
                "best_ref_path": candidate_refs[0],
                "avg_held_out_sim": 0.0,
                "all_ranked_candidates": [(Path(p).name, 0.0) for p in candidate_refs]
            }

        held_embs = [self.extract_embedding(f) for f in held_out_audios]
        
        scores = []
        for ref_path in candidate_refs:
            ref_emb = self.extract_embedding(ref_path)
            sims = [float(np.dot(ref_emb, h_emb)) for h_emb in held_embs]
            avg_sim = float(np.mean(sims))
            scores.append((ref_path, avg_sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        best_ref, best_score = scores[0]

        return {
            "speaker_id": speaker_id,
            "best_ref_path": best_ref,
            "avg_held_out_sim": round(best_score, 4),
            "all_ranked_candidates": [(Path(p).name, round(s, 4)) for p, s in scores]
        }

    def select_best_reference_with_probe(
        self,
        speaker_id: str,
        candidate_refs: List[str],
        held_out_audios: List[str],
        engine,
        probe_text: str = "Xin chào, đây là câu thử nghiệm để kiểm tra chất lượng giọng nói.",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Tuyển chọn Reference tối ưu 2 tầng (LOO Proximity + Probe Synthesis):
        1. Lọc top-k clip tham chiếu gần trọng tâm giọng thật nhất bằng LOO.
        2. Sinh một câu probe ngắn trên từng ứng viên (bằng v3 Turbo, ~2.7s/câu).
        3. Chấm điểm Cosine Sim của ĐẦU RA thực tế so với các câu thật (held-out bona fide).
        4. Chọn clip có điểm Sim đầu ra cao nhất.
        """
        # Bước 1: Lọc top-k qua LOO
        loo_res = self.select_best_reference_loo(speaker_id, candidate_refs, held_out_audios)
        ranked = loo_res["all_ranked_candidates"]
        
        # Lấy top-k đường dẫn file
        path_map = {Path(p).name: p for p in candidate_refs}
        top_candidates = [path_map[name] for name, _ in ranked[:top_k]]
        
        if not held_out_audios or engine is None:
            return {
                "speaker_id": speaker_id,
                "best_ref_path": top_candidates[0],
                "selection_method": "LOO_ONLY",
                "probe_scores": []
            }

        # Bước 2: Sinh probe và chấm điểm đầu ra thực tế
        probe_results = []
        held_embs = [self.extract_embedding(f) for f in held_out_audios]

        for ref_p in top_candidates:
            try:
                # v3 Turbo infer
                audio = engine.infer(
                    text=probe_text,
                    ref_audio=str(ref_p),
                    use_ref_codes=True,
                    denoise=False
                )
                if getattr(audio, "ndim", 1) > 1:
                    audio = audio.mean(axis=1)
                audio = np.asarray(audio, dtype=np.float32)
                
                # Trích xuất embedding của audio sinh ra
                synth_emb = self.evaluator.extract_embedding(audio, 48000).cpu().numpy()
                norm = np.linalg.norm(synth_emb)
                synth_emb = synth_emb / (norm + 1e-9) if norm > 0 else synth_emb
                
                # Tính Sim đầu ra so với các câu thật
                sims = [float(np.dot(synth_emb, h_emb)) for h_emb in held_embs]
                avg_output_sim = float(np.mean(sims))
                
                probe_results.append({
                    "ref_path": ref_p,
                    "ref_filename": Path(ref_p).name,
                    "output_sim_heldout": round(avg_output_sim, 4)
                })
            except Exception as e:
                logger.error(f"Lỗi khi probe ref {ref_p}: {e}")
                probe_results.append({
                    "ref_path": ref_p,
                    "ref_filename": Path(ref_p).name,
                    "output_sim_heldout": 0.0
                })

        probe_results.sort(key=lambda x: x["output_sim_heldout"], reverse=True)
        best_ref = probe_results[0]["ref_path"]
        best_score = probe_results[0]["output_sim_heldout"]

        return {
            "speaker_id": speaker_id,
            "best_ref_path": best_ref,
            "best_output_sim": best_score,
            "selection_method": "LOO_PLUS_PROBE_OUTPUT",
            "probe_scores": probe_results,
            "all_ranked_loo": ranked
        }
