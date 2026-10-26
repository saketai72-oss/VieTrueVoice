from enum import Enum
from typing import Optional, Dict, Any, Tuple
import time
import logging
import numpy as np
import torch

from .base import SynthesisRequest, SynthesisResult, QualityMetrics
from .adapters.f5_adapter import F5TTSAdapter
from .adapters.vieneu_adapter import VieNeuAdapter
from .evaluator import MultiGateEvaluator

logger = logging.getLogger(__name__)

class PipelineMode(Enum):
    BEST_QUALITY = "best_quality"   # Sinh cả 2 engine, đánh giá phân cấp và tự động chọn bản tốt nhất
    ADAPTIVE = "adaptive"           # Định tuyến thông minh theo Speaker & Thể loại văn bản
    DUAL_OUTPUT = "dual_output"     # Trả về đồng thời cả 2 bản để người dùng/thẩm định viên so sánh

def select_best_engine(
    cand_f5: Tuple[str, QualityMetrics, SynthesisResult],
    cand_vn: Tuple[str, QualityMetrics, SynthesisResult]
) -> Tuple[Tuple[str, QualityMetrics, SynthesisResult], Tuple[str, QualityMetrics, SynthesisResult], str, str]:
    """
    Thang quyết định phân cấp (Hierarchical Decision Ladder):
    Bậc 1: Hard Gates (Sanity: không rỗng, không NaN/Inf, không câm, không clipping, không catastrophic).
    Bậc 2: Content Gate 1 (Clean WER <= 15%).
    Bậc 3: Speaker Gate 2 (Similarity >= 0.4905).
    Bậc 4: Composite Score (Chỉ phân hạng khi cả hai cùng đạt chuẩn).

    Trả về: (winner, runner_up, reason, selection_status)
    trong đó selection_status in ['PASS_CLEAR_WINNER', 'PASS_COMPOSITE_RANKED', 'FAIL_BOTH_GATES']
    """
    name_a, m_a, r_a = cand_f5
    name_b, m_b, r_b = cand_vn

    pass_a = m_a.overall_pass and m_a.is_valid
    pass_b = m_b.overall_pass and m_b.is_valid

    # 1. Một bên đạt chuẩn, một bên trượt -> Bên đạt chuẩn thắng tuyệt đối
    if pass_a and not pass_b:
        reason = f"{name_a} vượt qua toàn bộ hard gates trong khi {name_b} trượt chuẩn"
        return cand_f5, cand_vn, reason, "PASS_CLEAR_WINNER"
    elif pass_b and not pass_a:
        reason = f"{name_b} vượt qua toàn bộ hard gates trong khi {name_a} trượt chuẩn"
        return cand_vn, cand_f5, reason, "PASS_CLEAR_WINNER"

    # 2. Cả hai cùng vượt qua Hard Gates -> So sánh Composite Score
    elif pass_a and pass_b:
        if m_a.composite_score >= m_b.composite_score:
            reason = f"Cả hai đạt chuẩn, {name_a} có Composite Score cao hơn ({m_a.composite_score} vs {m_b.composite_score})"
            return cand_f5, cand_vn, reason, "PASS_COMPOSITE_RANKED"
        else:
            reason = f"Cả hai đạt chuẩn, {name_b} có Composite Score cao hơn ({m_b.composite_score} vs {m_a.composite_score})"
            return cand_vn, cand_f5, reason, "PASS_COMPOSITE_RANKED"

    # 3. Cả hai cùng trượt Hard Gates -> Báo động không đạt chuẩn, fallback chọn bản ít lỗi hơn nhưng gán cờ FAIL
    else:
        if m_a.clean_wer <= m_b.clean_wer:
            reason = f"CẢNH BÁO: Cả hai đều trượt hard gates! Tạm chọn {name_a} do WER thấp hơn ({m_a.clean_wer*100:.1f}% vs {m_b.clean_wer*100:.1f}%)"
            return cand_f5, cand_vn, reason, "FAIL_BOTH_GATES"
        else:
            reason = f"CẢNH BÁO: Cả hai đều trượt hard gates! Tạm chọn {name_b} do WER thấp hơn ({m_b.clean_wer*100:.1f}% vs {m_a.clean_wer*100:.1f}%)"
            return cand_vn, cand_f5, reason, "FAIL_BOTH_GATES"

class ViTrueVoiceDualPipeline:
    def __init__(self, device: Optional[str] = None, evaluator: Optional[MultiGateEvaluator] = None):
        import torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.f5_engine = F5TTSAdapter(device=self.device)
        self.vieneu_engine = VieNeuAdapter(mode="v3turbo")
        self.evaluator = evaluator or MultiGateEvaluator(device=self.device)

        # Bảng quy tắc định tuyến thực nghiệm (Adaptive Routing Table)
        # Được xác lập từ kết quả validation Version 17 - 19
        self.adaptive_rules = {
            "SPK_0006": "VieNeu-A",  # VieNeu đạt WER 12.16% tốt hơn F5 (13.71%)
            "SPK_0005": "F5",        # F5 đạt WER 2.84% và 100% Pass rate tuyệt đối
            "SPK_0001": "F5",        # F5 đạt Sim 0.6943 và WER 6.74%
            "SPK_0004": "F5",        # F5 đạt WER 6.53%
            "SPK_0007": "F5"         # F5 đạt 95% overall pass
        }

    def synthesize(
        self,
        text: str,
        speaker_id: str,
        f5_ref_audio: str,
        vieneu_ref_audio: str,
        ref_text: str = "",
        seed: int = 100,
        mode: PipelineMode = PipelineMode.DUAL_OUTPUT,
        vieneu_preset: str = "VieNeu-A",
        max_retries: int = 1,
        seeds: Optional[list] = None,
        spk_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Giao diện tổng hợp âm thanh thống nhất của ViTrueVoice với cơ chế xử lý lỗi an toàn,
        hỗ trợ multi-seed retry bù lỗi ngẫu nhiên và đo lường độ trễ chi tiết.
        """
        t_start_total = time.perf_counter()
        
        # Tự động trích xuất transcript thật của clip tham chiếu bằng ASR nếu chưa có (Label-Free)
        if not ref_text and f5_ref_audio and hasattr(self.evaluator, "transcribe_audio"):
            ref_text = self.evaluator.transcribe_audio(f5_ref_audio)

        req_f5 = SynthesisRequest(
            text=text,
            speaker_id=speaker_id,
            ref_audio=f5_ref_audio,
            seed=seed,
            extra_params={"ref_text": ref_text}
        )
        
        req_vieneu = SynthesisRequest(
            text=text,
            speaker_id=speaker_id,
            ref_audio=vieneu_ref_audio,
            seed=seed,
            engine_preset=vieneu_preset,
            extra_params={"temperature": 0.60, "top_k": 25, "top_p": 0.90}
        )

        res_f5, metrics_f5, err_f5 = None, None, None
        res_vn, metrics_vn, err_vn = None, None, None
        t_synth_f5, t_eval_f5 = 0.0, 0.0
        t_synth_vn, t_eval_vn = 0.0, 0.0

        # 1. Chạy F5 Engine an toàn (hỗ trợ multi-seed retry bù lỗi âm học / trượt cổng)
        if mode in (PipelineMode.DUAL_OUTPUT, PipelineMode.BEST_QUALITY) or (mode == PipelineMode.ADAPTIVE and self.adaptive_rules.get(speaker_id, "F5") == "F5"):
            retry_seeds_f5 = seeds or ([seed, seed + 100, seed + 1924][:max(1, max_retries)])
            for attempt_idx, cur_seed in enumerate(retry_seeds_f5):
                try:
                    req_f5.seed = cur_seed
                    t0 = time.perf_counter()
                    res_f5 = self.f5_engine.synthesize(req_f5)
                    t_synth_f5 += time.perf_counter() - t0

                    t0 = time.perf_counter()
                    metrics_f5 = self.evaluator.evaluate(
                        res_f5.audio, res_f5.sample_rate, text, f5_ref_audio,
                        engine_name="F5-TTS-Vietnamese"
                    )
                    if spk_threshold is not None:
                        metrics_f5.gate2_pass = metrics_f5.speaker_sim >= spk_threshold
                        metrics_f5.overall_pass = (
                            metrics_f5.gate1_pass and metrics_f5.gate2_pass and
                            metrics_f5.gate3_pass and metrics_f5.gate4_pass and
                            not metrics_f5.is_catastrophic
                        )
                    t_eval_f5 += time.perf_counter() - t0
                    err_f5 = None

                    passed_all_gates = metrics_f5.overall_pass and metrics_f5.is_valid and not metrics_f5.is_catastrophic
                    if passed_all_gates or attempt_idx == len(retry_seeds_f5) - 1:
                        res_f5.metadata["attempts_needed"] = attempt_idx + 1
                        res_f5.metadata["retry_recovered"] = (attempt_idx > 0 and passed_all_gates)
                        break
                    else:
                        logger.info(f"F5-TTS Seed {cur_seed} trượt cổng (WER={metrics_f5.clean_wer*100:.1f}%, Sim={metrics_f5.speaker_sim:.4f}, Prosody={metrics_f5.dialect_score:.2f}), thử tiếp seed kế...")
                except Exception as e:
                    logger.error(f"F5-TTS synthesis failed (seed {cur_seed}): {e}")
                    err_f5 = str(e)
                finally:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

        # 2. Chạy VieNeu Engine an toàn (hỗ trợ multi-seed retry bù lỗi vấp/lặp)
        if mode in (PipelineMode.DUAL_OUTPUT, PipelineMode.BEST_QUALITY) or (mode == PipelineMode.ADAPTIVE and self.adaptive_rules.get(speaker_id, "F5") != "F5"):
            preset = self.adaptive_rules.get(speaker_id, vieneu_preset) if mode == PipelineMode.ADAPTIVE else vieneu_preset
            req_vieneu.engine_preset = preset
            retry_seeds = seeds or ([seed, seed + 100, seed + 1924][:max(1, max_retries)])
            
            for attempt_idx, cur_seed in enumerate(retry_seeds):
                try:
                    req_vieneu.seed = cur_seed
                    t0 = time.perf_counter()
                    res_vn = self.vieneu_engine.synthesize(req_vieneu)
                    t_synth_vn += time.perf_counter() - t0
                    
                    t0 = time.perf_counter()
                    metrics_vn = self.evaluator.evaluate(
                        res_vn.audio, res_vn.sample_rate, text, vieneu_ref_audio,
                        engine_name="VieNeu-TTS-v3Turbo"
                    )
                    if spk_threshold is not None:
                        metrics_vn.gate2_pass = metrics_vn.speaker_sim >= spk_threshold
                        metrics_vn.overall_pass = (
                            metrics_vn.gate1_pass and metrics_vn.gate2_pass and
                            metrics_vn.gate3_pass and metrics_vn.gate4_pass and
                            not metrics_vn.is_catastrophic
                        )
                    t_eval_vn += time.perf_counter() - t0
                    err_vn = None
                    
                    # Điều kiện dừng: Vượt qua TOÀN BỘ 4 cổng hoặc hết lượt thử
                    passed_all_gates = metrics_vn.overall_pass and metrics_vn.is_valid and not metrics_vn.is_catastrophic
                    if passed_all_gates or attempt_idx == len(retry_seeds) - 1:
                        res_vn.metadata["attempts_needed"] = attempt_idx + 1
                        res_vn.metadata["retry_recovered"] = (attempt_idx > 0 and passed_all_gates)
                        break
                    else:
                        logger.info(f"Seed {cur_seed} trượt cổng (WER={metrics_vn.clean_wer*100:.1f}%, Sim={metrics_vn.speaker_sim:.4f}, Prosody={metrics_vn.dialect_score:.2f}), thử tiếp seed kế...")
                except Exception as e:
                    logger.error(f"VieNeu-TTS synthesis failed (seed {cur_seed}): {e}")
                    err_vn = str(e)
                finally:
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()



        total_latency = time.perf_counter() - t_start_total

        # 3. Phân nhánh xử lý theo chế độ vận hành
        if mode == PipelineMode.DUAL_OUTPUT:
            return {
                "mode": mode.value,
                "f5": {"result": res_f5, "metrics": metrics_f5, "error": err_f5, "latency_s": round(t_synth_f5 + t_eval_f5, 3)},
                "vieneu": {"result": res_vn, "metrics": metrics_vn, "error": err_vn, "latency_s": round(t_synth_vn + t_eval_vn, 3)},
                "total_pipeline_latency_s": round(total_latency, 3)
            }

        elif mode == PipelineMode.BEST_QUALITY:
            # Xử lý trường hợp có engine lỗi
            if res_f5 is None and res_vn is None:
                raise RuntimeError(f"Cả hai engine đều thất bại: F5 ({err_f5}) | VieNeu ({err_vn})")
            if res_f5 is None:
                return {
                    "mode": mode.value,
                    "winner_engine": "VieNeu-TTS",
                    "winner_metrics": metrics_vn,
                    "winner_result": res_vn,
                    "selection_reason": f"F5-TTS gặp lỗi ({err_f5}), tự động chuyển sang VieNeu",
                    "selection_status": "FALLBACK_SINGLE_AVAILABLE",
                    "overall_pass": metrics_vn.overall_pass if metrics_vn else False,
                    "total_pipeline_latency_s": round(total_latency, 3)
                }
            if res_vn is None:
                return {
                    "mode": mode.value,
                    "winner_engine": "F5-TTS",
                    "winner_metrics": metrics_f5,
                    "winner_result": res_f5,
                    "selection_reason": f"VieNeu-TTS gặp lỗi ({err_vn}), tự động chuyển sang F5",
                    "selection_status": "FALLBACK_SINGLE_AVAILABLE",
                    "overall_pass": metrics_f5.overall_pass if metrics_f5 else False,
                    "total_pipeline_latency_s": round(total_latency, 3)
                }

            # Quyết định phân cấp khi cả hai cùng sinh thành công
            cand_f5 = ("F5-TTS", metrics_f5, res_f5)
            cand_vn = (f"VieNeu-TTS[{vieneu_preset}]", metrics_vn, res_vn)
            winner, loser, reason, status = select_best_engine(cand_f5, cand_vn)

            # Đảm bảo cờ trạng thái được truyền thẳng vào metadata của kết quả cuối
            winner[2].metadata["selection_status"] = status
            winner[2].metadata["overall_pass"] = (status != "FAIL_BOTH_GATES")
            winner[2].metadata["selection_reason"] = reason

            return {
                "mode": mode.value,
                "winner_engine": winner[0],
                "winner_metrics": winner[1],
                "winner_result": winner[2],
                "runner_up_engine": loser[0],
                "runner_up_metrics": loser[1],
                "runner_up_result": loser[2],
                "selection_reason": reason,
                "selection_status": status,
                "overall_pass": (status != "FAIL_BOTH_GATES"),
                "total_pipeline_latency_s": round(total_latency, 3),
                "breakdown_latency_s": {
                    "f5_synth": round(t_synth_f5, 3), "f5_eval": round(t_eval_f5, 3),
                    "vn_synth": round(t_synth_vn, 3), "vn_eval": round(t_eval_vn, 3)
                }
            }

        elif mode == PipelineMode.ADAPTIVE:
            if speaker_id in self.adaptive_rules:
                target_engine = self.adaptive_rules[speaker_id]
                reason = f"Speaker '{speaker_id}' có hồ sơ validation -> Chỉ định {target_engine}"
            else:
                target_engine = "F5"
                reason = f"Speaker '{speaker_id}' chưa có hồ sơ thực nghiệm -> Mặc định dùng F5-TTS baseline"

            if target_engine == "F5":
                if res_f5 is None:
                    raise RuntimeError(f"F5-TTS được định tuyến nhưng thất bại: {err_f5}")
                return {
                    "mode": mode.value,
                    "routed_engine": "F5-TTS",
                    "result": res_f5,
                    "metrics": metrics_f5,
                    "routing_reason": reason,
                    "total_pipeline_latency_s": round(total_latency, 3)
                }
            else:
                if res_vn is None:
                    raise RuntimeError(f"VieNeu-TTS được định tuyến nhưng thất bại: {err_vn}")
                return {
                    "mode": mode.value,
                    "routed_engine": f"VieNeu-TTS[{target_engine}]",
                    "result": res_vn,
                    "metrics": metrics_vn,
                    "routing_reason": reason,
                    "total_pipeline_latency_s": round(total_latency, 3)
                }
        else:
            raise ValueError(f"Chế độ pipeline không hợp lệ: {mode}")
