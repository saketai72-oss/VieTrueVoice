"""Script kiểm tra và đánh giá tập mẫu giọng SPK_0003 với phiên bản mô hình mới nhất (V5)

Đối chiếu với các phiên bản trước: Baseline B, B_zalo V3 (CE), B_zalo V4 (AM-Softmax), B_zalo V5 (Latest).
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
import sys

import librosa
import numpy as np
import pandas as pd
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.eval_ssl_aasist import load_model
from src.app.decision import calibrate_score, classify_score
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def evaluate_spk0003(
    data_dir: str = r"C:\Users\saket\Downloads\SPK_0003",
    output_csv: str | None = "out/eval_spk0003_results.csv",
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 95)
    print(f"🎙️ KIỂM ĐỊNH MẪU GIỌNG TÌNH NGUYỆN VIÊN SPK_0003 (Device: {device})")
    print(f"📂 Thư mục: {data_dir}")
    print("=" * 95)

    input_path = Path(data_dir)
    if not input_path.exists():
        print(f"❌ LỖI: Thư mục không tồn tại: {input_path}")
        return

    files = sorted(list(input_path.glob("*.mp3")) + list(input_path.glob("*.wav")) + list(input_path.glob("*.m4a")))
    # Loại trừ trùng lặp nếu có
    files = sorted(list(set(files)))
    print(f"🔍 Tìm thấy {len(files)} tệp âm thanh.")
    if not files:
        print("❌ Không tìm thấy tệp âm thanh nào.")
        return

    models = {}
    ckpts = {
        "Base B": Path("out/kaggle_ssl_out/best_model_B.pt"),
        "V3 (CE)": Path("out/zalo_b_zalo_v3/best_model_B_zalo.pt"),
        "V4 (AM)": Path("out/zalo_b_zalo_v4/best_model_B_zalo.pt"),
        "V5 (Latest)": Path("out/zalo_b_zalo_v5_local/best_model.pt"),
    }

    for name, path in ckpts.items():
        if path.is_file():
            print(f"📦 Đang nạp model [{name}]: {path}")
            m, _ = load_model(str(path), device=device)
            m.eval()
            models[name] = m
        else:
            print(f"⚠️ Không tìm thấy checkpoint [{name}]: {path}")

    if "V5 (Latest)" not in models:
        # Fallback thử kiểm tra out/best_model_B_zalo.pt
        fallback = Path("out/best_model_B_zalo.pt")
        if fallback.is_file():
            print(f"📦 Nạp model fallback làm V5: {fallback}")
            m, _ = load_model(str(fallback), device=device)
            m.eval()
            models["V5 (Latest)"] = m

    rng = np.random.default_rng(0)
    records = []

    print("\n" + "-" * 95)
    hdr = f"{'Tệp':<20} | {'F0(Hz)':<7} | {'SC(Hz)':<7} | " + " | ".join(f"{k:>11}" for k in models.keys()) + f" | {'Phán quyết V5 (θ=0)':<18}"
    print(hdr)
    print("-" * 95)

    with torch.no_grad():
        for f in files:
            y = load_audio(f, target_sr=16000)
            dur = len(y) / 16000.0

            # Phân tích đặc trưng âm học F0 & Spectral Centroid
            f0, voiced_flag, _ = librosa.pyin(y, fmin=50, fmax=400, sr=16000)
            f0_clean = f0[voiced_flag & ~np.isnan(f0)]
            f0_val = float(np.median(f0_clean)) if len(f0_clean) > 0 else float("nan")
            sc_val = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=16000)))

            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)

            scores = {}
            for name, m in models.items():
                s = m.score(tensor).item()
                scores[name] = s

            s_latest = scores.get("V5 (Latest)", float("nan"))
            dec_latest = classify_score(s_latest, threshold=0.0)

            cal_s_latest = calibrate_score(s_latest, speaker_f0=f0_val if not np.isnan(f0_val) else None)
            cal_dec_latest = classify_score(cal_s_latest, threshold=0.0)

            verdict_str = f"{'✅ BONA_FIDE' if dec_latest.is_bonafide else '❌ SPOOF'}"

            score_cols = " | ".join(f"{scores[k]:+11.2f}" for k in models.keys())
            print(f"{f.name:<20} | {f0_val:7.1f} | {sc_val:7.0f} | {score_cols} | {verdict_str:<18}")

            rec = {
                "file": f.name,
                "duration_s": round(dur, 2),
                "f0_hz": round(f0_val, 1) if not np.isnan(f0_val) else None,
                "sc_hz": round(sc_val, 0),
                **{f"score_{k.lower().replace(' ', '_').replace('(', '').replace(')', '')}": round(v, 4) for k, v in scores.items()},
                "v5_verdict_raw": dec_latest.prediction,
                "v5_score_calibrated": round(cal_s_latest, 4),
                "v5_verdict_calibrated": cal_dec_latest.prediction,
            }
            records.append(rec)

    print("-" * 95)
    df = pd.DataFrame(records)

    print("\n📊 BẢNG TỔNG KẾT ĐÁNH GIÁ (N = %d files):" % len(df))
    for name in models.keys():
        col = f"score_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        scores_arr = df[col].to_numpy()
        n_bona = np.sum(scores_arr > 0)
        pct = (n_bona / len(df)) * 100.0
        print(f"  • {name:<12}: {n_bona:2d}/{len(df):2d} ({pct:5.1f}%) BONA_FIDE | Mean: {scores_arr.mean():+6.2f} (std: {scores_arr.std():.2f}) | Min: {scores_arr.min():+6.2f} | Max: {scores_arr.max():+6.2f}")

    if "V5 (Latest)" in models:
        n_cal_bona = np.sum(df["v5_verdict_calibrated"] == "BONA_FIDE")
        pct_cal = (n_cal_bona / len(df)) * 100.0
        print(f"  • V5 (Calibrated F0): {n_cal_bona:2d}/{len(df):2d} ({pct_cal:5.1f}%) BONA_FIDE")

    if output_csv:
        out_p = Path(output_csv)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        print(f"\n💾 Đã lưu kết quả chi tiết tại: {out_p}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=r"C:\Users\saket\Downloads\SPK_0003")
    parser.add_argument("--out-csv", default="out/eval_spk0003_results.csv")
    args = parser.parse_args()
    evaluate_spk0003(args.data_dir, args.out_csv)
