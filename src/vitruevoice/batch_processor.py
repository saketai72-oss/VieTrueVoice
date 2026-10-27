"""
ViTrueVoice Batch Dataset Processor & Manifest Generator.
CMP436 - Synthetic Voice Detection in Compressed Telephony.

Cung cấp tiện ích xử lý hàng loạt trên các tập dữ liệu lớn (VIVOS, Common Voice):
- Phân hoạch 3 tập rời rạc chống rò rỉ dữ liệu (Ref, Enrollment, Test).
- Tuyển chọn reference clip tự động (LOO + Probe).
- Tổng hợp âm thanh qua Pipeline chuẩn hóa (Multi-Seed Retry + 3 Gates).
- Mô phỏng suy giảm kênh viễn thông (G.711 A-law & AMR-NB).
- Xuất Manifest chuẩn hóa tách riêng trục danh tính (ecapa_sim) và độ rõ (raw_wer).
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd
import soundfile as sf
import torch

from .base import ManifestRecord, QualityMetrics
from .evaluator import MultiGateEvaluator
from .speaker_profiler import SpeakerProfiler
from .pipeline import ViTrueVoiceDualPipeline, PipelineMode


class DatasetPartitioner:
    """Phân hoạch tập dữ liệu của mỗi speaker thành 3 tập rời rạc chống rò rỉ."""

    @staticmethod
    def partition_speaker_files(
        files: List[str],
        n_ref_cands: int = 3,
        n_enroll: int = 4
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Chia danh sách file của 1 speaker thành 3 tập không giao nhau:
        - ref_pool: các file ứng viên để chọn clip tham chiếu (thường 2-3 file 4-8s)
        - enroll_pool: các file để tính enrollment centroid sinh trắc (3-5 file)
        - test_pool: các câu thật độc lập dùng để test hoặc câu held-out
        """
        if len(files) < (n_ref_cands + n_enroll + 1):
            # Nếu số file ít, phân bổ theo tỷ lệ tối thiểu
            n_ref = max(1, len(files) // 3)
            n_enr = max(1, (len(files) - n_ref) // 2)
            ref_pool = files[:n_ref]
            enroll_pool = files[n_ref : n_ref + n_enr]
            test_pool = files[n_ref + n_enr :]
        else:
            ref_pool = files[:n_ref_cands]
            enroll_pool = files[n_ref_cands : n_ref_cands + n_enroll]
            test_pool = files[n_ref_cands + n_enroll :]

        # Ràng buộc nghiêm ngặt chống rò rỉ dữ liệu giữa 3 tập
        set_ref = set(ref_pool)
        set_enr = set(enroll_pool)
        set_tst = set(test_pool)
        assert len(set_ref & set_enr) == 0, f"Rò rỉ dữ liệu: ref_pool và enroll_pool giao nhau! {set_ref & set_enr}"
        assert len(set_ref & set_tst) == 0, f"Rò rỉ dữ liệu: ref_pool và test_pool giao nhau! {set_ref & set_tst}"
        assert len(set_enr & set_tst) == 0, f"Rò rỉ dữ liệu: enroll_pool và test_pool giao nhau! {set_enr & set_tst}"

        return ref_pool, enroll_pool, test_pool

    @staticmethod
    def assign_utterance_role(file_path: str, ref_pool: List[str], enroll_pool: List[str]) -> str:
        """Xác định vai trò rõ ràng của utterance: 'ref', 'enroll' hoặc 'eval'."""
        p_str = str(file_path)
        ref_strs = {str(f) for f in ref_pool}
        enr_strs = {str(f) for f in enroll_pool}
        if p_str in ref_strs:
            return "ref"
        elif p_str in enr_strs:
            return "enroll"
        return "eval"




class TelephonyCompressor:
    """Nén thoại viễn thông chuẩn G.711 A-law và AMR-NB."""

    @staticmethod
    def compress_g711_alaw(src_path: str, dst_path: str) -> bool:
        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = f'ffmpeg -y -v error -i "{src_path}" -ar 8000 -ac 1 -c:a pcm_alaw "{dst_path}"'
        res = subprocess.run(cmd, shell=True)
        return res.returncode == 0

    @staticmethod
    def compress_amr_nb(src_path: str, dst_path: str, bitrate: str = "12.2k") -> bool:
        dst_p = Path(dst_path)
        dst_p.parent.mkdir(parents=True, exist_ok=True)
        temp_amr = dst_p.with_suffix(".amr")
        cmd_enc = f'ffmpeg -y -v error -i "{src_path}" -ar 8000 -ac 1 -c:a libopencore_amrnb -b:a {bitrate} "{temp_amr}"'
        cmd_dec = f'ffmpeg -y -v error -i "{temp_amr}" -ar 8000 -ac 1 -c:a pcm_s16le "{dst_path}"'
        r1 = subprocess.run(cmd_enc, shell=True)
        r2 = subprocess.run(cmd_dec, shell=True)
        if temp_amr.exists():
            temp_amr.unlink()
        return (r1.returncode == 0) and (r2.returncode == 0)


class BatchDatasetProcessor:
    """Quy trình tự động hóa xử lý sinh dữ liệu & thẩm định hàng loạt."""

    def __init__(
        self,
        pipeline: Optional[ViTrueVoiceDualPipeline] = None,
        evaluator: Optional[MultiGateEvaluator] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.evaluator = evaluator or MultiGateEvaluator(device=device)
        self.profiler = SpeakerProfiler(evaluator=self.evaluator)
        self.pipeline = pipeline or ViTrueVoiceDualPipeline(evaluator=self.evaluator)

    def process_speaker(
        self,
        speaker_id: str,
        speaker_wav_files: List[str],
        prompts: List[str],
        out_synth_dir: Path,
        mode: PipelineMode = PipelineMode.BEST_QUALITY,
        apply_telephony: bool = True,
        only_pass: bool = True,
        transcript_map: Optional[Dict[str, str]] = None,
        max_retries: int = 2,
        out_f5_dir: Optional[Path] = None,
        out_vn_dir: Optional[Path] = None,
    ) -> List[ManifestRecord]:
        """
        Xử lý hoàn chỉnh cho 1 speaker:
        1. Phân hoạch 3 tập rời rạc (Ref, Enrollment, Test).
        2. Tính Enrollment Centroid từ tập enrollment.
        3. Chọn Reference clip tốt nhất từ tập ref_cands.
        4. Sinh âm thanh cho danh sách câu kiểm thử prompts (kèm Multi-Seed Retry).
        5. Thẩm định 3 cổng, trích xuất ecapa_sim so với Enrollment Centroid.
        6. Tạo bản nén viễn thông (G.711 / AMR-NB) nếu được bật.
        """
        records = []
        out_synth_dir.mkdir(parents=True, exist_ok=True)

        ref_pool, enroll_pool, test_pool = DatasetPartitioner.partition_speaker_files(speaker_wav_files)

        # 1. Enrollment Centroid K câu thật
        enroll_centroid = self.evaluator.compute_enrollment_centroid(enroll_pool, k=len(enroll_pool))

        # 2. Chọn reference clip từ ref_pool (Ưu tiên clip đơn tự nhiên 3.5s - 7.5s)
        ref_cands = self.profiler.prepare_reference_clip(
            ref_pool, str(out_synth_dir / "refs"), speaker_id, min_dur=3.5, max_dur=7.5, allow_stitching=False
        )
        if not ref_cands:
            ref_cands = self.profiler.prepare_reference_clip(
                ref_pool, str(out_synth_dir / "refs"), speaker_id, min_dur=3.0, max_dur=8.5, allow_stitching=True
            )
            if not ref_cands:
                ref_cands = ref_pool[:1]

        loo_res = self.profiler.select_best_reference_loo(speaker_id, ref_cands, enroll_pool)
        best_ref = loo_res["best_ref_path"]

        # 3. Tính ngưỡng hiệu chuẩn riêng cho speaker
        thresh_info = self.profiler.compute_speaker_threshold(speaker_id, enroll_pool, ref_to_exclude=best_ref)
        spk_thresh = thresh_info["calibrated_threshold"]

        # Trích xuất transcript thật của clip tham chiếu được chọn (kèm ASR Label-Free fallback cho dataset lớn không nhãn)
        ref_stem = Path(best_ref).stem
        ref_text = transcript_map.get(ref_stem, "") if transcript_map else ""
        if not ref_text and hasattr(self.evaluator, "transcribe_audio"):
            ref_text = self.evaluator.transcribe_audio(best_ref)

        def _process_one_candidate(synth_res, metrics, eng_name, dest_dir, file_prefix):

            if synth_res is None or synth_res.audio is None:
                return []

            clean_wer = getattr(metrics, "clean_wer", 1.0) if metrics else 1.0
            clean_cer = getattr(metrics, "clean_cer", 1.0) if metrics else 1.0
            comp_score = getattr(metrics, "composite_score", 0.0) if metrics else 0.0

            synth_emb = self.evaluator.extract_embedding(synth_res.audio, synth_res.sample_rate)
            if enroll_centroid is not None:
                sim_to_enroll = float(torch.nn.functional.cosine_similarity(
                    enroll_centroid.unsqueeze(0), synth_emb.unsqueeze(0)
                ).cpu().item())
            else:
                sim_to_enroll = getattr(synth_res, "speaker_sim", None)
                if sim_to_enroll is None and metrics is not None:
                    sim_to_enroll = getattr(metrics, "speaker_sim", 0.0)

            gate1_pass = getattr(metrics, "gate1_pass", True) if metrics else True
            gate3_pass = getattr(metrics, "gate3_pass", True) if metrics else True
            is_catastrophic = getattr(metrics, "is_catastrophic", False) if metrics else False

            # Lọc cứng CHỈ trên Gate 1 (WER/độ rõ) và Gate 3 (Sanity/clipping/duration)
            # Gate 2 (độ giống giọng) và Gate 4 (prosody) chỉ dùng để ghi điểm và gán tầng tấn công
            hard_gate_pass = gate1_pass and gate3_pass and (not is_catastrophic)

            d_score = getattr(metrics, "dialect_score", 1.0) if metrics else 1.0
            d_match = getattr(metrics, "dialect_match", True) if metrics else True
            d_drift = getattr(metrics, "dialect_drift", False) if metrics else False

            if only_pass and not hard_gate_pass:
                print(f"  ⏭️ Bỏ qua {file_prefix} ({eng_name}): không đạt chuẩn Hard Gate 1/3 (WER={clean_wer*100:.1f}%, Catastrophic={is_catastrophic})")
                return []

            dest_dir.mkdir(parents=True, exist_ok=True)
            out_wav = dest_dir / f"{file_prefix}.wav"
            sf.write(str(out_wav), synth_res.audio, synth_res.sample_rate)

            cand_records = []
            rec_studio = ManifestRecord(
                audio_path=str(out_wav),
                speaker_id=speaker_id,
                is_bonafide=False,
                ecapa_sim=round(sim_to_enroll, 4) if sim_to_enroll is not None else 0.0,
                raw_wer=round(clean_wer, 4),
                raw_cer=round(clean_cer, 4),
                source="vivos",
                role="eval",
                codec="clean_16khz",
                tts_generator=eng_name,
                engine_name=eng_name,
                ref_audio_path=best_ref,
                seed=synth_res.metadata.get("seed", 100) if hasattr(synth_res, "metadata") else 100,
                metadata={
                    "attempts_needed": synth_res.metadata.get("attempts_needed", 1) if hasattr(synth_res, "metadata") else 1,
                    "selection_status": synth_res.metadata.get("selection_status", "") if hasattr(synth_res, "metadata") else "",
                    "composite_score": comp_score,
                    "dialect_score": d_score,
                    "dialect_match": d_match,
                    "dialect_drift": d_drift
                }
            )
            cand_records.append(rec_studio)

            if apply_telephony:
                g711_wav = dest_dir / f"{file_prefix}_g711.wav"
                if TelephonyCompressor.compress_g711_alaw(str(out_wav), str(g711_wav)):
                    w_g, sr_g = sf.read(str(g711_wav), dtype="float32")
                    emb_g = self.evaluator.extract_embedding(w_g, sr_g)
                    sim_g = float(torch.nn.functional.cosine_similarity(
                        enroll_centroid.unsqueeze(0), emb_g.unsqueeze(0)
                    ).cpu().item()) if enroll_centroid is not None else 0.0
                    rec_g711 = ManifestRecord(
                        audio_path=str(g711_wav),
                        speaker_id=speaker_id,
                        is_bonafide=False,
                        ecapa_sim=round(sim_g, 4),
                        raw_wer=round(clean_wer, 4),
                        raw_cer=round(clean_cer, 4),
                        source="vivos",
                        role="eval",
                        codec="g711_alaw",
                        tts_generator=eng_name,
                        engine_name=eng_name,
                        ref_audio_path=best_ref,
                        seed=synth_res.metadata.get("seed", 100) if hasattr(synth_res, "metadata") else 100,
                        metadata={"parent_studio_wav": str(out_wav)}
                    )
                    cand_records.append(rec_g711)

                amr_wav = dest_dir / f"{file_prefix}_amrnb.wav"
                if TelephonyCompressor.compress_amr_nb(str(out_wav), str(amr_wav)):
                    w_a, sr_a = sf.read(str(amr_wav), dtype="float32")
                    emb_a = self.evaluator.extract_embedding(w_a, sr_a)
                    sim_a = float(torch.nn.functional.cosine_similarity(
                        enroll_centroid.unsqueeze(0), emb_a.unsqueeze(0)
                    ).cpu().item()) if enroll_centroid is not None else 0.0
                    rec_amr = ManifestRecord(
                        audio_path=str(amr_wav),
                        speaker_id=speaker_id,
                        is_bonafide=False,
                        ecapa_sim=round(sim_a, 4),
                        raw_wer=round(clean_wer, 4),
                        raw_cer=round(clean_cer, 4),
                        source="vivos",
                        role="eval",
                        codec="amr_nb",
                        tts_generator=eng_name,
                        engine_name=eng_name,
                        ref_audio_path=best_ref,
                        seed=synth_res.metadata.get("seed", 100) if hasattr(synth_res, "metadata") else 100,
                        metadata={"parent_studio_wav": str(out_wav)}
                    )
                    cand_records.append(rec_amr)

            return cand_records

        # 4. Sinh và đánh giá từng prompt
        for idx, text in enumerate(prompts):
            file_prefix = f"{speaker_id}_prompt_{idx:03d}"

            # Run synthesis pipeline
            res = self.pipeline.synthesize(
                text=text,
                speaker_id=speaker_id,
                f5_ref_audio=best_ref,
                vieneu_ref_audio=best_ref,
                ref_text=ref_text,
                mode=mode,
                spk_threshold=spk_thresh,
                max_retries=max_retries
            )

            if mode == PipelineMode.DUAL_OUTPUT:
                f5_dir = (out_f5_dir or (out_synth_dir / "spoof_f5tts" / speaker_id))
                vn_dir = (out_vn_dir or (out_synth_dir / "spoof_vieneu" / speaker_id))
                records.extend(_process_one_candidate(
                    res["f5"]["result"], res["f5"]["metrics"], "F5-TTS-Vietnamese", f5_dir, file_prefix
                ))
                records.extend(_process_one_candidate(
                    res["vieneu"]["result"], res["vieneu"]["metrics"], "VieNeu-TTS", vn_dir, file_prefix
                ))
            else:
                if isinstance(res, dict) and "winner_result" in res:
                    synth_res = res["winner_result"]
                    metrics = res.get("winner_metrics")
                    engine_name = res.get("winner_engine")
                else:
                    synth_res = res.get("result") or res
                    metrics = res.get("metrics")
                    engine_name = res.get("engine_name") or getattr(synth_res, "engine_name", None)

                records.extend(_process_one_candidate(
                    synth_res, metrics, engine_name, out_synth_dir, file_prefix
                ))

        return records

    @staticmethod
    def export_manifest_csv(records: List[ManifestRecord], csv_path: str):
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for r in records:
            row = {
                "utt_id": Path(r.audio_path).stem,
                "audio_path": r.audio_path,
                "speaker_id": r.speaker_id,
                "source": getattr(r, "source", "vivos"),
                "label": "bonafide" if r.is_bonafide else "spoof",
                "role": getattr(r, "role", "eval"),
                "tts_generator": r.tts_generator or (r.engine_name if not r.is_bonafide else "none"),
                "codec": r.codec,
                "split": r.metadata.get("split", "train"),
                "duration_sec": r.metadata.get("duration_sec", 4.0),
                "transcript": r.metadata.get("transcript", ""),
                "raw_wer": r.raw_wer,
                "raw_cer": r.raw_cer,
                "ecapa_sim": r.ecapa_sim,
                "wavlm_sim": getattr(r, "wavlm_sim", None),
                "derived_tier": r.derive_attack_tier(),
                "seed": r.seed if r.seed is not None else 100,
            }
            if r.metadata:
                for k, v in r.metadata.items():
                    if k not in row:
                        row[f"meta_{k}"] = v
            rows.append(row)
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return df
