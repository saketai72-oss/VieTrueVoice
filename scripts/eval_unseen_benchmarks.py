"""Đánh giá toàn diện các mô hình Unseen TTS (Kokoro, VieNeu, CosyVoice, Bark) trên Checkpoint B_zalo V6.

Tính toán:
1. Tỷ lệ phát hiện Spoof (Pass Rate % with score < 0.0)
2. Mean score, IQR, phân bố điểm theo từng Codec
3. Kết hợp với bộ 84 bona fide clips của 5 tình nguyện viên đối chứng để tính EER, minDCF, APCER, BPCER
4. Phân tích năng lượng cao tần >4kHz (Vocoder roll-off)
"""

from __future__ import annotations

import argparse
import json
import sys
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


def evaluate_unseen_manifest(
    manifest_path: str | Path,
    ckpt_path: str = "out/zalo_b_zalo_v6_local/best_model.pt",
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    output_json: str | None = None,
) -> dict:
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    print("=" * 80)
    print(f"📊 ĐÁNH GIÁ MÔ HÌNH UNSEEN TTS TỪ: {manifest_path.name}")
    print(f"🔍 Checkpoint: {ckpt_path} | Device: {device}")
    print("=" * 80)

    model, _ = load_model(ckpt_path, device)
    model.eval()

    df_spoof = pd.read_csv(manifest_path)
    print(f"✅ Nạp {len(df_spoof)} mẫu spoof từ manifest.")

    def score_audio(file_path: str | Path) -> tuple[float, float]:
        y = load_audio(file_path, target_sr=16000)
        batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
        with torch.no_grad():
            win_scores = model.score(batch)
        score = pool_scores(win_scores, mode="max")

        # Năng lượng > 4kHz
        fft = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(len(y), 1.0 / 16000)
        total_energy = np.sum(fft**2) + 1e-10
        high_energy = np.sum(fft[freqs > 4000] ** 2)
        ratio_4k = float(high_energy / total_energy)
        return score, ratio_4k

    spoof_results = []
    print("\n⏳ Đang chấm điểm các mẫu spoof...")
    for idx, row in df_spoof.iterrows():
        fpath = _ROOT / row["audio_path"]
        if not fpath.exists():
            fpath = Path(row["audio_path"])
        if not fpath.exists():
            continue
        sc, r4k = score_audio(fpath)
        spoof_results.append({
            "utt_id": row["utt_id"],
            "speaker_id": row.get("speaker_id", "UNKNOWN"),
            "codec": row.get("codec", "clean"),
            "score": sc,
            "ratio_4k": r4k,
            "is_correct_spoof": sc < 0.0,
        })
        if (idx + 1) % 50 == 0 or (idx + 1) == len(df_spoof):
            print(f"  Processed {idx + 1}/{len(df_spoof)}...")

    df_res = pd.DataFrame(spoof_results)

    # Nạp 84 mẫu Bona Fide của 5 tình nguyện viên đối chứng
    print("\n⏳ Đang chấm điểm 84 mẫu bona fide đối chứng (SPK_0003..0007)...")
    bona_results = []
    g2_spks = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    for spk in g2_spks:
        spk_dir = _ROOT / f"data/raw/{spk}"
        if not spk_dir.exists():
            continue
        all_files = sorted(list(spk_dir.glob("*.wav")) + list(spk_dir.glob("*.m4a")))
        # Chỉ lấy file clean
        clean_files = [f for f in all_files if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
        for f in clean_files:
            sc, r4k = score_audio(f)
            bona_results.append({
                "utt_id": f.stem,
                "speaker_id": spk,
                "score": sc,
                "ratio_4k": r4k,
                "is_correct_bona": sc > 0.0,
            })

    df_bona = pd.DataFrame(bona_results)
    print(f"✅ Đã chấm điểm {len(df_bona)} mẫu bona fide đối chứng.")

    # Thống kê tổng hợp
    total_spoof = len(df_res)
    correct_spoof = int(df_res["is_correct_spoof"].sum())
    spoof_pass_rate = float(correct_spoof / total_spoof * 100) if total_spoof > 0 else 0.0
    mean_spoof_score = float(df_res["score"].mean())

    total_bona = len(df_bona)
    correct_bona = int(df_bona["is_correct_bona"].sum())
    bona_pass_rate = float(correct_bona / total_bona * 100) if total_bona > 0 else 0.0
    mean_bona_score = float(df_bona["score"].mean())

    # Tính EER & minDCF
    bona_scores = df_bona["score"].to_numpy()
    spoof_scores = df_res["score"].to_numpy()
    all_scores = np.concatenate([bona_scores, spoof_scores])
    all_labels = np.concatenate([np.ones_like(bona_scores), np.zeros_like(spoof_scores)])
    eer, threshold = compute_eer(all_scores, all_labels)
    mindcf = compute_min_dcf(all_scores, all_labels)

    # Thống kê theo Codec
    codec_stats = {}
    for c, g in df_res.groupby("codec"):
        c_tot = len(g)
        c_cor = int(g["is_correct_spoof"].sum())
        codec_stats[c] = {
            "total": c_tot,
            "correct_spoof": c_cor,
            "pass_rate_pct": round(c_cor / c_tot * 100, 2),
            "mean_score": round(float(g["score"].mean()), 3),
            "median_score": round(float(g["score"].median()), 3),
            "mean_ratio_4k_pct": round(float(g["ratio_4k"].mean() * 100), 2),
        }

    # Thống kê theo Speaker
    speaker_stats = {}
    for s, g in df_res.groupby("speaker_id"):
        s_tot = len(g)
        s_cor = int(g["is_correct_spoof"].sum())
        speaker_stats[s] = {
            "total": s_tot,
            "correct_spoof": s_cor,
            "pass_rate_pct": round(s_cor / s_tot * 100, 2),
            "mean_score": round(float(g["score"].mean()), 3),
        }

    summary = {
        "manifest": manifest_path.name,
        "checkpoint": ckpt_path,
        "total_spoof": total_spoof,
        "correct_spoof": correct_spoof,
        "spoof_detection_rate_pct": round(spoof_pass_rate, 2),
        "mean_spoof_score": round(mean_spoof_score, 3),
        "total_bona": total_bona,
        "correct_bona": correct_bona,
        "bona_pass_rate_pct": round(bona_pass_rate, 2),
        "mean_bona_score": round(mean_bona_score, 3),
        "eer_pct": round(eer * 100, 2),
        "eer_threshold": round(threshold, 4),
        "minDCF": round(mindcf, 4),
        "codec_breakdown": codec_stats,
        "speaker_breakdown": speaker_stats,
    }

    print("\n" + "=" * 80)
    print("📈 KẾT QUẢ ĐÁNH GIÁ TỔNG QUAN:")
    print("=" * 80)
    print(f"🎯 Spoof Detection Rate (Pass Rate): {spoof_pass_rate:.2f}% ({correct_spoof}/{total_spoof})")
    print(f"📉 Mean Spoof Score: {mean_spoof_score:+.2f} (Ngưỡng phân định: 0.0)")
    print(f"🛡️ Bona Fide Acceptance Rate:       {bona_pass_rate:.2f}% ({correct_bona}/{total_bona})")
    print(f"📈 Mean Bona Fide Score:          {mean_bona_score:+.2f}")
    print(f"🔥 Equal Error Rate (EER):         {eer * 100:.2f}% (tại threshold = {threshold:+.4f})")
    print(f"💎 minDCF:                         {mindcf:.4f}")
    print("\n--- CHI TIẾT THEO TỪNG KÊNH NÉN (CODEC) ---")
    for c, st in codec_stats.items():
        print(f"  {c:<15} | Spoof Pass: {st['pass_rate_pct']:6.2f}% ({st['correct_spoof']}/{st['total']}) | Mean Score: {st['mean_score']:+6.2f} | >4kHz: {st['mean_ratio_4k_pct']:5.2f}%")
    print("\n--- CHI TIẾT THEO NGƯỜI NÓI (SPEAKER) ---")
    for s, st in speaker_stats.items():
        print(f"  {s:<15} | Spoof Pass: {st['pass_rate_pct']:6.2f}% ({st['correct_spoof']}/{st['total']}) | Mean Score: {st['mean_score']:+6.2f}")
    print("=" * 80)

    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"💾 Đã lưu kết quả JSON vào: {output_json}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default="data/manifests_zalo/unseen_kokoro_benchmark.csv")
    parser.add_argument("--ckpt", type=str, default="out/zalo_b_zalo_v6_local/best_model.pt")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out", type=str, default="benchmarks/unseen_kokoro_eval.json")
    args = parser.parse_args()

    evaluate_unseen_manifest(args.manifest, args.ckpt, args.device, args.out)
