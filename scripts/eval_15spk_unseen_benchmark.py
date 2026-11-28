"""Kịch bản đánh giá toàn diện mô hình VieTrueVoice B_zalo V7 trên tập Unseen TTS quy mô lớn (15 người nói).
Đo đạc ma trận suy giảm (Degradation Analysis):
- Seen TTS: F5-TTS, VieNeu-TTS (192 clean + 768 codecs = 960 clips mỗi loại).
- Unseen TTS: VoiceStudio CFM (OmniVoice, 193 clean + 772 codecs = 965 clips).
- Bona Fide: 10.490 clips đối chứng sạch và qua các kênh thoại nén từ 15 người nói.

Cơ chế suy luận: Multi-window Max-Pooling (5 cửa sổ 4.0s, hop 1.0s, mini-batch song song).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.eval_ssl_aasist import load_model
from src.evaluation.metrics import compute_eer, compute_min_dcf
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores


def evaluate_manifest_audio(
    model,
    df: pd.DataFrame,
    device: str,
    pooling_mode: str = "max",
    desc: str = "Audio",
) -> pd.DataFrame:
    records = []
    total = len(df)
    t0_all = time.perf_counter()

    for idx, (_, row) in enumerate(df.iterrows()):
        fpath = _ROOT / str(row["audio_path"])
        if not fpath.exists():
            continue

        try:
            y = load_audio(fpath, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
            with torch.no_grad():
                win_scores = model.score(batch)
            score = pool_scores(win_scores, mode=pooling_mode)

            records.append({
                "utt_id": row.get("utt_id", fpath.stem),
                "audio_path": str(row["audio_path"]),
                "speaker_id": row.get("speaker_id", "UNKNOWN"),
                "label": row.get("label", "spoof"),
                "tts_generator": row.get("tts_generator", "none"),
                "codec": row.get("codec", "clean_16khz"),
                "score": float(score),
            })
        except Exception as e:
            continue

        if (idx + 1) % 500 == 0 or (idx + 1) == total:
            elapsed = time.perf_counter() - t0_all
            print(f"  [{desc}] {idx+1}/{total} clips | Elapsed: {elapsed:.1f}s")

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description="Đánh giá mô hình B_zalo V7 trên Unseen TTS 15 người nói")
    parser.add_argument("--model-path", type=str, default="out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")
    parser.add_argument("--bona-manifest", type=str, default="data/manifests_zalo/dev_zalo_dual_seen.csv")
    parser.add_argument("--unseen-manifest", type=str, default="data/manifests_zalo/unseen_omnivoice_15spk_benchmark.csv")
    parser.add_argument("--cache-csv", type=str, default="benchmarks/cached_scores_15spk_v7.csv")
    parser.add_argument("--out-json", type=str, default="benchmarks/seen_vs_unseen_degradation_15spk_v7.json")
    parser.add_argument("--force-unseen", action="store_true", default=True, help="Tái đánh giá riêng nhóm Unseen OmniVoice")
    parser.add_argument("--pooling-mode", type=str, default="max", help="Chế độ pooling: max, mean, asymmetric_veto")
    args = parser.parse_args()

    cache_p = _ROOT / args.cache_csv
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if cache_p.exists() and not args.force_unseen:
        print(f"⚡ Tìm thấy cache điểm số tại: {cache_p}. Nạp trực tiếp để tiết kiệm thời gian...")
        full_scores_df = pd.read_csv(cache_p)
    elif cache_p.exists() and args.force_unseen:
        print(f"⚡ Tìm thấy cache điểm số tại: {cache_p}. Tái suy luận riêng 965 clips Unseen VoiceStudio CFM (Pooling: {args.pooling_mode})...")
        old_df = pd.read_csv(cache_p)
        non_unseen_df = old_df[old_df["tts_generator"] != "OmniVoice"]
        unseen_df = pd.read_csv(_ROOT / args.unseen_manifest)

        model, _ = load_model(str(_ROOT / args.model_path), device=device)
        res_unseen = evaluate_manifest_audio(model, unseen_df, device, pooling_mode=args.pooling_mode, desc="OmniVoice CFM")
        full_scores_df = pd.concat([non_unseen_df, res_unseen], ignore_index=True)
        full_scores_df.to_csv(cache_p, index=False)
        print(f"💾 Đã cập nhật cache điểm số suy luận: {cache_p}")
    else:
        model_p = _ROOT / args.model_path
        if not model_p.exists():
            print(f"❌ Không tìm thấy model checkpoint: {model_p}")
            sys.exit(1)

        print("=" * 90)
        print("🚀 ĐÁNH GIÁ ĐỘC LẬP UNSEEN TTS (VOICESTUDIO CFM) TRÊN 15 NGƯỜI NÓI HELD-OUT")
        print(f"Model: {model_p.name} | Device: {device} | Multi-window Pooling (Mode: {args.pooling_mode})")
        print("=" * 90)

        model, _ = load_model(str(model_p), device=device)

        # 1. Đọc manifest Bona Fide & Seen TTS
        df_dev = pd.read_csv(_ROOT / args.bona_manifest)
        bona_df = df_dev[(df_dev["label"] == "bonafide") & (df_dev["role"] == "eval")].copy()
        f5_df = df_dev[(df_dev["label"] == "spoof") & (df_dev["tts_generator"] == "F5-TTS-Vietnamese")].copy()
        vieneu_df = df_dev[(df_dev["label"] == "spoof") & (df_dev["tts_generator"] == "VieNeu-TTS")].copy()

        # 2. Đọc manifest Unseen CFM
        unseen_df = pd.read_csv(_ROOT / args.unseen_manifest)

        print(f"📊 Dữ liệu đánh giá:")
        print(f"  • Bona Fide Eval: {len(bona_df)} clips (15 người nói)")
        print(f"  • Seen F5-TTS: {len(f5_df)} clips")
        print(f"  • Seen VieNeu-TTS: {len(vieneu_df)} clips")
        print(f"  • Unseen VoiceStudio CFM: {len(unseen_df)} clips")

        # 3. Đánh giá suy luận
        print("\n🔍 Đang suy luận Bona Fide clips...")
        res_bona = evaluate_manifest_audio(model, bona_df, device, pooling_mode=args.pooling_mode, desc="Bona Fide")

        print("\n🔍 Đang suy luận Seen F5-TTS clips...")
        res_f5 = evaluate_manifest_audio(model, f5_df, device, pooling_mode=args.pooling_mode, desc="F5-TTS")

        print("\n🔍 Đang suy luận Seen VieNeu-TTS clips...")
        res_vieneu = evaluate_manifest_audio(model, vieneu_df, device, pooling_mode=args.pooling_mode, desc="VieNeu-TTS")

        print("\n🔍 Đang suy luận Unseen VoiceStudio CFM clips...")
        res_unseen = evaluate_manifest_audio(model, unseen_df, device, pooling_mode=args.pooling_mode, desc="OmniVoice CFM")

        full_scores_df = pd.concat([res_bona, res_f5, res_vieneu, res_unseen], ignore_index=True)
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        full_scores_df.to_csv(cache_p, index=False)
        print(f"💾 Đã lưu cache điểm số suy luận: {cache_p}")

    # Tách các nhóm điểm từ DataFrame
    res_bona = full_scores_df[full_scores_df["label"] == "bonafide"]
    res_f5 = full_scores_df[(full_scores_df["label"] == "spoof") & (full_scores_df["tts_generator"] == "F5-TTS-Vietnamese")]
    res_vieneu = full_scores_df[(full_scores_df["label"] == "spoof") & (full_scores_df["tts_generator"] == "VieNeu-TTS")]
    res_unseen = full_scores_df[(full_scores_df["label"] == "spoof") & (full_scores_df["tts_generator"] == "OmniVoice")]

    bona_scores = res_bona["score"].values

    def compute_stats(name, res_df):
        sp_scores = res_df["score"].values
        all_scores = np.concatenate([bona_scores, sp_scores])
        all_labels = np.concatenate([np.ones(len(bona_scores), dtype=int), np.zeros(len(sp_scores), dtype=int)])
        eer, th = compute_eer(all_scores, all_labels)
        dcf = compute_min_dcf(all_scores, all_labels)
        pass_rate = float(np.mean(sp_scores < 0.0) * 100.0)
        mean_s = float(np.mean(sp_scores))
        med_s = float(np.median(sp_scores))
        return {
            "name": name,
            "total": len(res_df),
            "pass_rate_pct": round(pass_rate, 2),
            "mean_score": round(mean_s, 2),
            "median_score": round(med_s, 2),
            "eer_pct": round(eer * 100.0, 2),
            "min_dcf": round(dcf, 4),
            "eer_threshold": round(th, 4),
        }

    stats_f5 = compute_stats("F5-TTS (Seen)", res_f5)
    stats_vieneu = compute_stats("VieNeu-TTS (Seen)", res_vieneu)

    # Seen Pooled
    res_seen_pooled = pd.concat([res_f5, res_vieneu], ignore_index=True)
    stats_seen_pooled = compute_stats("Seen TTS Pooled", res_seen_pooled)

    # Unseen CFM
    stats_unseen = compute_stats("VoiceStudio CFM (Unseen)", res_unseen)

    # Bona Fide stats
    bona_pass = float(np.mean(bona_scores >= 0.0) * 100.0)
    bona_mean = float(np.mean(bona_scores))
    bona_med = float(np.median(bona_scores))
    stats_bona = {
        "name": "Bona Fide (15 Speakers)",
        "total": len(res_bona),
        "pass_rate_pct": round(bona_pass, 2),
        "mean_score": round(bona_mean, 2),
        "median_score": round(bona_med, 2),
        "bpcer_pct": round(100.0 - bona_pass, 2),
    }

    # Theo từng Codec cho Unseen CFM
    codec_stats = {}
    for c in ["clean_16khz", "aac_zalo_76k", "opus_zalo_24k", "g711_alaw", "amr_nb"]:
        sub_unseen = res_unseen[res_unseen["codec"] == c]
        sub_bona = res_bona[res_bona["codec"] == c]
        if len(sub_unseen) > 0 and len(sub_bona) > 0:
            c_all_scores = np.concatenate([sub_bona["score"].values, sub_unseen["score"].values])
            c_all_labels = np.concatenate([np.ones(len(sub_bona), dtype=int), np.zeros(len(sub_unseen), dtype=int)])
            c_eer, c_th = compute_eer(c_all_scores, c_all_labels)
            c_dcf = compute_min_dcf(c_all_scores, c_all_labels)
            c_pass = float(np.mean(sub_unseen["score"].values < 0.0) * 100.0)
            codec_stats[c] = {
                "total": len(sub_unseen),
                "pass_rate_pct": round(c_pass, 2),
                "mean_score": round(float(np.mean(sub_unseen["score"].values)), 2),
                "eer_pct": round(c_eer * 100.0, 2),
                "min_dcf": round(c_dcf, 4),
            }

    # Degradation
    degradation = {
        "delta_eer": round(stats_unseen["eer_pct"] - stats_seen_pooled["eer_pct"], 2),
        "delta_pass_rate": round(stats_unseen["pass_rate_pct"] - stats_seen_pooled["pass_rate_pct"], 2),
        "delta_mean_score": round(stats_unseen["mean_score"] - stats_seen_pooled["mean_score"], 2),
    }

    report_data = {
        "model": args.model_path,
        "pooling_mode": args.pooling_mode,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bona_fide": stats_bona,
        "systems": {
            "f5_tts": stats_f5,
            "vieneu_tts": stats_vieneu,
            "seen_pooled": stats_seen_pooled,
            "voicestudio_cfm": stats_unseen,
        },
        "voicestudio_by_codec": codec_stats,
        "degradation": degradation,
    }

    out_json_path = _ROOT / args.out_json
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Đã lưu kết quả đo đạc tại: {out_json_path}")

    # In Bảng tổng hợp
    print("\n" + "=" * 90)
    print("📊 BẢNG TỔNG HỢP HIỆU NĂNG SEEN VS UNSEEN TTS TRÊN 15 NGƯỜI NÓI HELD-OUT (THETA = 0.0)")
    print("=" * 90)
    print(f"{'Hệ Thống / Tập Đánh Giá':<28} | {'Tổng Mẫu':<9} | {'Pass Rate (%)':<14} | {'Mean Score':<11} | {'Median':<9} | {'EER (%)':<9} | {'minDCF':<8}")
    print("-" * 90)
    for st in [stats_f5, stats_vieneu, stats_seen_pooled, stats_unseen]:
        print(f"{st['name']:<28} | {st['total']:<9} | {st['pass_rate_pct']:>13}% | {st['mean_score']:>11} | {st['median_score']:>9} | {st['eer_pct']:>8}% | {st['min_dcf']:>8}")
    print(f"{stats_bona['name']:<28} | {stats_bona['total']:<9} | {stats_bona['pass_rate_pct']:>13}% | {stats_bona['mean_score']:>11} | {stats_bona['median_score']:>9} | {'--':>9} | {'--':>8}")
    print("=" * 90)
    print(f"📈 MỨC ĐỘ SUY GIẢM (DEGRADATION: UNSEEN vs SEEN POOLED):")
    print(f"  • Δ EER: +{degradation['delta_eer']}%")
    print(f"  • Δ Pass Rate: {degradation['delta_pass_rate']}%")
    print(f"  • Δ Mean Score: +{degradation['delta_mean_score']}")
    print("=" * 90)


if __name__ == "__main__":
    main()
