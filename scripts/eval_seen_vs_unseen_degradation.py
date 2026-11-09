"""Kịch bản đo đạc và phân tích mức độ suy giảm (Degradation Analysis) giữa Seen TTS và Unseen TTS trên mô hình B_zalo V6 (Multi-window Max-Pooling).

Quy ước:
- Seen TTS: F5-TTS, VieNeu-TTS
- Unseen TTS: Kokoro-Vietnamese, OmniVoice, Bark
- Bộ nghiệm thu: 84 clips bona fide sạch từ 5 tình nguyện viên đối chứng SPK_0003..SPK_0007 (hoàn toàn cô lập).
"""

from __future__ import annotations

import argparse
import glob
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


def get_codec_from_filename(fname: str) -> str:
    if "_aac_zalo" in fname:
        return "aac_zalo_76k"
    if "_opus_zalo" in fname:
        return "opus_zalo_24k"
    if "_g711" in fname:
        return "g711"
    if "_amrnb" in fname:
        return "amrnb"
    return "clean"


def evaluate_system_files(
    model,
    files: list[Path],
    device: str,
    system_name: str,
    system_type: str,
) -> pd.DataFrame:
    records = []
    for idx, f in enumerate(files):
        try:
            y = load_audio(f, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
            with torch.no_grad():
                win_scores = model.score(batch)
            score = pool_scores(win_scores, mode="max")

            # High-frequency ratio (>4kHz)
            fft = np.abs(np.fft.rfft(y))
            freqs = np.fft.rfftfreq(len(y), 1.0 / 16000)
            tot_e = np.sum(fft**2) + 1e-10
            hi_e = np.sum(fft[freqs > 4000] ** 2)
            r4k = float(hi_e / tot_e)

            # Speaker
            spk = "UNKNOWN"
            for s in ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]:
                if s in f.parts or s in f.name:
                    spk = s
                    break

            codec = get_codec_from_filename(f.name)

            records.append({
                "system": system_name,
                "type": system_type,
                "file": f.name,
                "speaker_id": spk,
                "codec": codec,
                "score": score,
                "ratio_4k": r4k,
                "is_correct_spoof": score < 0.0,
            })
        except Exception as e:
            print(f"Error processing {f}: {e}")

        if (idx + 1) % 50 == 0 or (idx + 1) == len(files):
            print(f"  [{system_name}] Processed {idx + 1}/{len(files)}...")

    return pd.DataFrame(records)


def run_benchmark(
    ckpt_path: str = "out/zalo_b_zalo_v6_local/best_model.pt",
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    output_json: str = "benchmarks/seen_vs_unseen_degradation.json",
):
    print("=" * 90)
    print("🔬 ĐO ĐẠC SO SÁNH SEEN TTS VS UNSEEN TTS & ĐÁNH GIÁ MỨC ĐỘ SUY GIẢM")
    print(f"Checkpoint: {ckpt_path} | Device: {device} | Pooling: Multi-window Max-Pooling")
    print("=" * 90)

    model, _ = load_model(ckpt_path, device)
    model.eval()

    speakers = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]

    # 1. Nạp và chấm điểm 84 mẫu bona fide sạch của 5 tình nguyện viên đối chứng
    print("\n⏳ Chấm điểm 84 mẫu Bona Fide đối chứng (SPK_0003..0007)...")
    bona_records = []
    for spk in speakers:
        raw_dir = _ROOT / f"data/raw/{spk}"
        if not raw_dir.exists():
            continue
        all_raw = sorted(list(raw_dir.glob("*.wav")) + list(raw_dir.glob("*.m4a")))
        clean_raw = [f for f in all_raw if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
        for f in clean_raw:
            y = load_audio(f, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
            with torch.no_grad():
                win_scores = model.score(batch)
            score = pool_scores(win_scores, mode="max")
            bona_records.append({
                "system": "BonaFide",
                "type": "bonafide",
                "file": f.name,
                "speaker_id": spk,
                "codec": "clean",
                "score": score,
                "is_correct_bona": score > 0.0,
            })

    df_bona = pd.DataFrame(bona_records)
    bona_scores = df_bona["score"].to_numpy()
    bona_pass_rate = float(df_bona["is_correct_bona"].sum() / len(df_bona) * 100)
    bona_mean_score = float(df_bona["score"].mean())
    print(f"✅ Đã chấm điểm {len(df_bona)} mẫu Bona Fide: Pass Rate = {bona_pass_rate:.2f}%, Mean Score = {bona_mean_score:+.2f}")

    # 2. Thu thập file cho từng hệ thống TTS
    tts_systems = {}

    # SEEN TTS #1: F5-TTS
    f5_files = []
    for spk in speakers:
        f5_files.extend(list((_ROOT / f"data/spoof_f5tts/{spk}").glob("*.wav")))
    if f5_files:
        tts_systems["F5-TTS"] = {"type": "Seen", "files": sorted(f5_files)}

    # SEEN TTS #2: VieNeu-TTS
    vn_files = []
    for spk in speakers:
        vn_files.extend(list((_ROOT / f"data/spoof_vieneu/{spk}").glob("*.wav")))
    if vn_files:
        tts_systems["VieNeu-TTS"] = {"type": "Seen", "files": sorted(vn_files)}

    # UNSEEN TTS #1: Kokoro-Vietnamese
    kk_files = []
    for spk in speakers:
        kk_files.extend(list((_ROOT / f"data/spoof_unseen/kokoro/{spk}").glob("*.wav")))
    if kk_files:
        tts_systems["Kokoro-Vietnamese"] = {"type": "Unseen", "files": sorted(kk_files)}

    # UNSEEN TTS #2: OmniVoice (nếu có)
    omni_files = []
    for spk in speakers:
        omni_dir = _ROOT / f"data/spoof_unseen/omnivoice/{spk}"
        if omni_dir.exists():
            omni_files.extend(list(omni_dir.glob("*.wav")))
    if omni_files:
        tts_systems["OmniVoice"] = {"type": "Unseen", "files": sorted(omni_files)}

    # UNSEEN TTS #3: Bark (nếu có)
    bark_files = []
    for spk in speakers:
        bark_dir = _ROOT / f"data/spoof_unseen/bark/{spk}"
        if bark_dir.exists():
            bark_files.extend(list(bark_dir.glob("*.wav")))
    if bark_files:
        tts_systems["Bark"] = {"type": "Unseen", "files": sorted(bark_files)}

    # 3. Đánh giá từng hệ thống
    system_summaries = {}
    all_spoof_dfs = []

    for name, meta in tts_systems.items():
        print(f"\n⏳ Đang chấm điểm hệ thống [{meta['type']}]: {name} ({len(meta['files'])} files)...")
        df_sys = evaluate_system_files(model, meta["files"], device, name, meta["type"])
        all_spoof_dfs.append(df_sys)

        spoof_sc = df_sys["score"].to_numpy()
        tot = len(df_sys)
        cor = int(df_sys["is_correct_spoof"].sum())
        prate = cor / tot * 100 if tot else 0.0
        m_score = float(df_sys["score"].mean())
        med_score = float(df_sys["score"].median())

        # EER & minDCF
        y_eval = np.concatenate([np.ones_like(bona_scores), np.zeros_like(spoof_sc)])
        s_eval = np.concatenate([bona_scores, spoof_sc])
        eer_val, thr_val = compute_eer(s_eval, y_eval)
        mindcf_val = compute_min_dcf(s_eval, y_eval)

        # Codec breakdown
        codec_breakdown = {}
        for c, g in df_sys.groupby("codec"):
            c_tot = len(g)
            c_cor = int(g["is_correct_spoof"].sum())
            codec_breakdown[c] = {
                "total": c_tot,
                "correct_spoof": c_cor,
                "pass_rate_pct": round(c_cor / c_tot * 100, 2),
                "mean_score": round(float(g["score"].mean()), 2),
                "median_score": round(float(g["score"].median()), 2),
                "ratio_4k_pct": round(float(g["ratio_4k"].mean() * 100), 2),
            }

        system_summaries[name] = {
            "type": meta["type"],
            "total_files": tot,
            "correct_spoof": cor,
            "pass_rate_pct": round(prate, 2),
            "mean_score": round(m_score, 2),
            "median_score": round(med_score, 2),
            "eer_pct": round(eer_val * 100, 2),
            "eer_threshold": round(thr_val, 4),
            "minDCF": round(mindcf_val, 4),
            "codec_breakdown": codec_breakdown,
        }

    # 4. Phân tích mức độ suy giảm (Degradation Analysis)
    # Nhóm Seen pooled vs Unseen pooled
    df_all_spoof = pd.concat(all_spoof_dfs, ignore_index=True)

    seen_df = df_all_spoof[df_all_spoof["type"] == "Seen"]
    unseen_df = df_all_spoof[df_all_spoof["type"] == "Unseen"]

    def calc_group_metrics(df_sub):
        if len(df_sub) == 0:
            return {}
        s_sc = df_sub["score"].to_numpy()
        tot = len(df_sub)
        cor = int(df_sub["is_correct_spoof"].sum())
        pr = cor / tot * 100
        ms = float(df_sub["score"].mean())
        y = np.concatenate([np.ones_like(bona_scores), np.zeros_like(s_sc)])
        s = np.concatenate([bona_scores, s_sc])
        e, _ = compute_eer(s, y)
        d = compute_min_dcf(s, y)
        return {
            "total": tot,
            "correct": cor,
            "pass_rate_pct": round(pr, 2),
            "mean_score": round(ms, 2),
            "eer_pct": round(e * 100, 2),
            "minDCF": round(d, 4),
        }

    seen_metrics = calc_group_metrics(seen_df)
    unseen_metrics = calc_group_metrics(unseen_df)

    degradation = {
        "delta_eer_pct": round(unseen_metrics.get("eer_pct", 0.0) - seen_metrics.get("eer_pct", 0.0), 2),
        "delta_pass_rate_pct": round(unseen_metrics.get("pass_rate_pct", 0.0) - seen_metrics.get("pass_rate_pct", 0.0), 2),
        "delta_mean_score": round(unseen_metrics.get("mean_score", 0.0) - seen_metrics.get("mean_score", 0.0), 2),
        "relative_degradation_descr": (
            "Hiệu năng không suy giảm mà cải thiện" if unseen_metrics.get("eer_pct", 0) <= seen_metrics.get("eer_pct", 0)
            else f"EER tăng thêm +{unseen_metrics.get('eer_pct', 0) - seen_metrics.get('eer_pct', 0):.2f}%"
        ),
    }

    report = {
        "checkpoint": ckpt_path,
        "bona_fide_evaluation": {
            "total": len(df_bona),
            "pass_rate_pct": round(bona_pass_rate, 2),
            "mean_score": round(bona_mean_score, 2),
        },
        "systems": system_summaries,
        "seen_pooled": seen_metrics,
        "unseen_pooled": unseen_metrics,
        "degradation_analysis": degradation,
    }

    # In kết quả trực quan ra màn hình
    print("\n" + "=" * 90)
    print("📊 BẢNG 1: HIỆU NĂNG TỔNG THỂ TỪNG HỆ THỐNG (Quyết định tại θ = 0.0)")
    print("=" * 90)
    print(f"{'Hệ Thống TTS':<20} | {'Phân Loại':<8} | {'Tổng Mẫu':<8} | {'Pass Rate (%)':<14} | {'Mean Score':>10} | {'EER (%)':>8} | {'minDCF':>8}")
    print("-" * 90)
    for name, st in system_summaries.items():
        pr_str = f"{st['correct_spoof']}/{st['total_files']} ({st['pass_rate_pct']:5.2f}%)"
        print(f"{name:<20} | {st['type']:<8} | {st['total_files']:<8} | {pr_str:<14} | {st['mean_score']:+10.2f} | {st['eer_pct']:7.2f}% | {st['minDCF']:8.4f}")

    print("\n" + "=" * 90)
    print("🔍 BẢNG 2: PHÂN TÍCH MỨC ĐỘ SUY GIẢM (SEEN VS UNSEEN TTS DEGRADATION)")
    print("=" * 90)
    print(f"1. Nhóm SEEN TTS (F5-TTS + VieNeu-TTS) : EER = {seen_metrics.get('eer_pct', 0.0):.2f}% | Pass Rate = {seen_metrics.get('pass_rate_pct', 0.0):.2f}% | Mean Score = {seen_metrics.get('mean_score', 0.0):+.2f}")
    print(f"2. Nhóm UNSEEN TTS (Kokoro + ...)     : EER = {unseen_metrics.get('eer_pct', 0.0):.2f}% | Pass Rate = {unseen_metrics.get('pass_rate_pct', 0.0):.2f}% | Mean Score = {unseen_metrics.get('mean_score', 0.0):+.2f}")
    print("-" * 90)
    print(f"👉 Độ lệch EER (ΔEER)                : {degradation['delta_eer_pct']:+.2f}%")
    print(f"👉 Độ lệch Pass Rate (ΔPass Rate)     : {degradation['delta_pass_rate_pct']:+.2f}%")
    print(f"👉 Độ lệch Mean Score (ΔScore)        : {degradation['delta_mean_score']:+.2f}")
    print(f"👉 Đánh giá tổng quát                 : {degradation['relative_degradation_descr']}")
    print("=" * 90)

    # In chi tiết từng codec
    print("\n" + "=" * 90)
    print("📻 BẢNG 3: MỨC ĐỘ SUY GIẢM DO NÉN KÊNH THOẠI (CODEC DEGRADATION)")
    print("=" * 90)
    for name, st in system_summaries.items():
        print(f"\n--- {name} ({st['type']}) ---")
        for c, c_info in st["codec_breakdown"].items():
            print(f"  {c:<15} | Pass: {c_info['pass_rate_pct']:6.2f}% ({c_info['correct_spoof']}/{c_info['total']}) | Mean Score: {c_info['mean_score']:+6.2f} | >4kHz: {c_info['ratio_4k_pct']:5.2f}%")

    out_p = Path(output_json)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Đã lưu báo cáo đo đạc chi tiết vào: {output_json}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", type=str, default="out/zalo_b_zalo_v6_local/best_model.pt")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out", type=str, default="benchmarks/seen_vs_unseen_degradation.json")
    args = parser.parse_args()

    run_benchmark(args.ckpt, args.device, args.out)
