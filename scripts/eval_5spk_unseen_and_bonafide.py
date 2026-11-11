#!/usr/bin/env python3
"""Đánh giá toàn diện mô hình ViTrueVoice trên toàn bộ tập Unseen TTS và Bona Fide của 5 tình nguyện viên đối chứng held-out (SPK_0003..0007).

Tập kiểm định:
- Bona Fide: 420 clips (84 clips gốc x 5 kênh codec: Clean, AAC-LC 76k, Opus 24k, AMR-NB, G.711)
- Unseen Spoof: 375 clips OmniVoice CFM / VoiceStudio Zero-shot (15 câu x 5 SPK x 5 kênh codec)
- Tổng cộng: 795 clips âm thanh

Quy chuẩn:
- Multi-window Max-Pooling (win=64k, hop=16k, max_windows=5)
- Ngưỡng quyết định cố định: theta = 0.0 (Bona Fide > 0, Spoof < 0)
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

SPEAKERS = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]


def get_codec(fname: str) -> str:
    f = fname.lower()
    if "_aac_zalo" in f:
        return "aac_zalo_76k"
    if "_opus_zalo" in f:
        return "opus_zalo_24k"
    if "_amrnb" in f:
        return "amrnb"
    if "_g711" in f:
        return "g711"
    return "clean"


def evaluate_dataset(
    model,
    device: str,
    apply_dither: bool = True,
) -> pd.DataFrame:
    records = []

    # 1. Thu thập 420 tệp Bona Fide của 5 tình nguyện viên
    bona_files = []
    for spk in SPEAKERS:
        spk_dir = _ROOT / "data/raw" / spk
        if spk_dir.exists():
            for f in sorted(list(spk_dir.glob("*.wav")) + list(spk_dir.glob("*.m4a"))):
                bona_files.append((spk, f, "Bona Fide", 1))

    # 2. Thu thập 375 tệp Unseen Spoof (OmniVoice CFM Zero-shot)
    spoof_files = []
    for spk in SPEAKERS:
        spk_dir = _ROOT / "data/spoof_unseen/omnivoice" / spk
        if spk_dir.exists():
            for f in sorted(list(spk_dir.glob("*.wav"))):
                spoof_files.append((spk, f, "Unseen Spoof (OmniVoice)", 0))

    all_items = bona_files + spoof_files
    print(f"Tổng số tệp kiểm định: {len(all_items)} (Bona Fide: {len(bona_files)}, Unseen Spoof: {len(spoof_files)})")
    print(f"Cấu hình suy luận: Multi-window Max-Pooling | apply_dither={apply_dither}")

    t0 = time.perf_counter()
    with torch.no_grad():
        for i, (spk, fpath, label_str, true_label) in enumerate(all_items):
            try:
                y = load_audio(fpath, target_sr=16000)
                dur = float(len(y) / 16000.0)
                wb = extract_window_batch(
                    y,
                    win=64000,
                    hop=16000,
                    max_windows=5,
                    apply_dither=apply_dither,
                ).to(device)
                win_scores = model.score(wb)
                score = pool_scores(win_scores, mode="max")
                pred_label = 1 if score > 0.0 else 0
                is_correct = (pred_label == true_label)

                records.append({
                    "file": fpath.name,
                    "speaker": spk,
                    "type": label_str,
                    "true_label": true_label,
                    "codec": get_codec(fpath.name),
                    "duration_s": round(dur, 2),
                    "score": round(score, 4),
                    "pred_label": pred_label,
                    "is_correct": is_correct,
                })
            except Exception as e:
                print(f"Lỗi đọc {fpath}: {e}")

            if (i + 1) % 100 == 0 or (i + 1) == len(all_items):
                elapsed = time.perf_counter() - t0
                fps = (i + 1) / elapsed
                print(f"  -> Đã xử lý {i + 1}/{len(all_items)} clips ({fps:.1f} clips/s)...")

    return pd.DataFrame(records)


def compute_metrics_table(df: pd.DataFrame) -> dict:
    df_bona = df[df["true_label"] == 1]
    df_spoof = df[df["true_label"] == 0]

    bona_pass = float(df_bona["is_correct"].mean() * 100) if len(df_bona) else 0.0
    spoof_pass = float(df_spoof["is_correct"].mean() * 100) if len(df_spoof) else 0.0

    bpcer = 100.0 - bona_pass  # False Reject Rate (giọng thật bị báo nhầm là spoof)
    apcer = 100.0 - spoof_pass  # False Accept Rate (spoof bị lọt lưới nhận nhầm là thật)

    y_true = df["true_label"].to_numpy()
    y_scores = df["score"].to_numpy()

    eer_val, eer_thr = compute_eer(y_scores, y_true)
    min_dcf = compute_min_dcf(y_scores, y_true)

    return {
        "total_clips": len(df),
        "total_bona": len(df_bona),
        "total_spoof": len(df_spoof),
        "bona_pass_rate_pct": round(bona_pass, 2),
        "spoof_pass_rate_pct": round(spoof_pass, 2),
        "bpcer_pct": round(bpcer, 2),
        "apcer_pct": round(apcer, 2),
        "eer_pct": round(eer_val, 2),
        "eer_threshold": round(eer_thr, 4),
        "min_dcf": round(min_dcf, 4),
        "mean_bona_score": round(float(df_bona["score"].mean()), 2) if len(df_bona) else 0.0,
        "median_bona_score": round(float(df_bona["score"].median()), 2) if len(df_bona) else 0.0,
        "mean_spoof_score": round(float(df_spoof["score"].mean()), 2) if len(df_spoof) else 0.0,
        "median_spoof_score": round(float(df_spoof["score"].median()), 2) if len(df_spoof) else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", type=str, default="out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--dither", action="store_true", help="Apply comfort dithering (default: False)")
    parser.add_argument("--out", type=str, default="benchmarks/eval_5spk_unseen_and_bonafide.json")
    args = parser.parse_args()

    print("=" * 95)
    print("🔬 KIỂM ĐỊNH TOÀN BỘ TẬP UNSEEN TTS & BONA FIDE CỦA 5 TÌNH NGUYỆN VIÊN ĐỐI CHỨNG HELD-OUT")
    print(f"Mô hình: {args.ckpt}")
    print(f"Thiết bị: {args.device} | Ngưỡng quyết định: theta = 0.0 | Comfort Dither: {args.dither}")
    print("=" * 95)

    model, _ = load_model(args.ckpt, args.device)
    model.eval()

    # 1. Chạy đánh giá tập dữ liệu
    mode_name = "MULTI-WINDOW MAX-POOLING (RAW ACOUSTIC)" if not args.dither else "MULTI-WINDOW MAX-POOLING + COMFORT DITHERING"
    print("\n" + "=" * 95)
    print(f"🚀 CHẠY ĐÁNH GIÁ CHẾ ĐỘ: {mode_name}")
    print("=" * 95)
    df_res = evaluate_dataset(model, args.device, apply_dither=args.dither)

    summary_overall = compute_metrics_table(df_res)

    # 2. Phân tách theo người nói (SPK_0003 .. SPK_0007)
    spk_breakdowns = {}
    for spk in SPEAKERS:
        df_spk = df_res[df_res["speaker"] == spk]
        spk_breakdowns[spk] = compute_metrics_table(df_spk)

    # 3. Phân tách theo kênh codec (Clean, AAC, Opus, AMR, G711)
    codec_breakdowns = {}
    codecs_order = ["clean", "aac_zalo_76k", "opus_zalo_24k", "amrnb", "g711"]
    for c in codecs_order:
        df_c = df_res[df_res["codec"] == c]
        if len(df_c):
            codec_breakdowns[c] = compute_metrics_table(df_c)

    # In kết quả dạng bảng khoa học
    print("\n" + "=" * 95)
    print("📊 BẢNG 1: HIỆU NĂNG TỔNG THỂ TRÊN BỘ 5 TÌNH NGUYỆN VIÊN (795 CLIPS)")
    print("=" * 95)
    print(f"• Tổng số mẫu kiểm thử:           {summary_overall['total_clips']} clips")
    print(f"• Số mẫu Bona Fide (Người Thật):   {summary_overall['total_bona']} clips (84 clips x 5 codec)")
    print(f"• Số mẫu Unseen Spoof (OmniVoice): {summary_overall['total_spoof']} clips (15 prompts x 5 SPK x 5 codec)")
    print(f"• Tỷ lệ nhận diện Giọng Thật:      {summary_overall['bona_pass_rate_pct']}% (BPCER = {summary_overall['bpcer_pct']}%)")
    print(f"• Tỷ lệ phát hiện Deepfake:        {summary_overall['spoof_pass_rate_pct']}% (APCER = {summary_overall['apcer_pct']}%)")
    print(f"• Điểm EER (Equal Error Rate):     {summary_overall['eer_pct']}% (Ngưỡng EER: {summary_overall['eer_threshold']:+.4f})")
    print(f"• Chỉ số minDCF (C_miss=10, C_fa=1): {summary_overall['min_dcf']}")
    print(f"• Điểm Mean Bona Fide:             {summary_overall['mean_bona_score']:+.2f} (Median: {summary_overall['median_bona_score']:+.2f})")
    print(f"• Điểm Mean Unseen Spoof:          {summary_overall['mean_spoof_score']:+.2f} (Median: {summary_overall['median_spoof_score']:+.2f})")

    print("\n" + "=" * 95)
    print("👤 BẢNG 2: CHI TIẾT TỪNG TÌNH NGUYỆN VIÊN (SPEAKER-LEVEL GENERALIZATION)")
    print("=" * 95)
    print(f"{'Người Nói':<10} | {'Bona Fide Pass':<16} | {'Unseen Spoof Pass':<18} | {'EER (%)':>8} | {'minDCF':>8} | {'Bona Mean':>11} | {'Spoof Mean':>11}")
    print("-" * 95)
    for spk, m in spk_breakdowns.items():
        bona_str = f"{m['bona_pass_rate_pct']}% ({m['total_bona']})"
        spoof_str = f"{m['spoof_pass_rate_pct']}% ({m['total_spoof']})"
        print(f"{spk:<10} | {bona_str:<16} | {spoof_str:<18} | {m['eer_pct']:7.2f}% | {m['min_dcf']:8.4f} | {m['mean_bona_score']:+10.2f} | {m['mean_spoof_score']:+10.2f}")

    print("\n" + "=" * 95)
    print("📻 BẢNG 3: CHI TIẾT THEO KÊNH NÉN THOẠI & VIỄN THÔNG (CODEC BREAKDOWN)")
    print("=" * 95)
    print(f"{'Kênh Thoại / Codec':<18} | {'Bona Pass':<16} | {'Spoof Pass':<18} | {'EER (%)':>8} | {'minDCF':>8} | {'Bona Mean':>11} | {'Spoof Mean':>11}")
    print("-" * 95)
    codec_labels = {
        "clean": "Clean 16kHz",
        "aac_zalo_76k": "AAC-LC 76kbps",
        "opus_zalo_24k": "Opus 24kbps",
        "amrnb": "AMR-NB 12.2k",
        "g711": "G.711 A-law",
    }
    for c, m in codec_breakdowns.items():
        lbl = codec_labels.get(c, c)
        bona_str = f"{m['bona_pass_rate_pct']}% ({m['total_bona']})"
        spoof_str = f"{m['spoof_pass_rate_pct']}% ({m['total_spoof']})"
        print(f"{lbl:<18} | {bona_str:<16} | {spoof_str:<18} | {m['eer_pct']:7.2f}% | {m['min_dcf']:8.4f} | {m['mean_bona_score']:+10.2f} | {m['mean_spoof_score']:+10.2f}")

    # Lưu kết quả json
    report = {
        "checkpoint": args.ckpt,
        "device": args.device,
        "threshold": 0.0,
        "pooling": "multi_window_max_pooling_5win",
        "apply_dither": args.dither,
        "overall": summary_overall,
        "by_speaker": spk_breakdowns,
        "by_codec": codec_breakdowns,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Đã lưu toàn bộ báo cáo chi tiết vào: {args.out}")


if __name__ == "__main__":
    main()
