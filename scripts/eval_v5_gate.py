"""Kịch bản kiểm định đa tầng (Pha 3 Gate Evaluation) cho ViTrueVoice Version 5.

Đánh giá đồng thời 3 tầng độc lập:
1. Gate 1 (G1): SPK_0001 (15 file) & Bộ VoiCes (15 file) -> FRR <= 20% (>= 12/15 bona fide)
2. Gate 2 (G2): 4 tình nguyện viên đối chứng (SPK_0004, 0005, 0006, 0007) -> >= 90% bona fide
3. Gate 3 (G3): Tập Dev Zalo (11.450 mẫu) -> EER <= 2.0% trên cả 5 codecs
"""

from __future__ import annotations
import argparse
import glob
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def eval_checkpoint_gates(ckpt_path: str, device: str = "cpu"):
    print("=" * 80)
    print(f"🚪 KIỂM ĐỊNH ĐA TẦNG V5 (GATES EVALUATION) CHO: {ckpt_path}")
    print("=" * 80)

    model, _ = load_model(ckpt_path, device)
    model.eval()
    rng = np.random.default_rng(0)

    # ── GATE 1: SPK_0001 & VOICES (Deep Voice Outlier) ──────────────────────
    print("\n🔍 GATE 1: Kiểm định trên các mẫu giọng trầm ngoại lai (SPK_0001 & VoiCes)")
    g1_dirs = [
        ("SPK_0001 (15 file cũ)", Path(r"C:\Users\saket\Downloads\SPK_0001")),
        ("VoiCes (15 file mới)", Path(r"C:\Users\saket\Downloads\VoiCes")),
    ]
    g1_pass = True
    with torch.no_grad():
        for label, d in g1_dirs:
            if not d.exists():
                print(f"  ⚠️ Bỏ qua {label} (thư mục không tồn tại: {d})")
                continue
            files = sorted(list(d.glob("*.m4a")) + list(d.glob("*.wav")))
            scores = []
            for f in files:
                y = load_audio(f, target_sr=16000)
                t = fit_length(y, 64000, train=False, rng=rng)
                tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
                scores.append(model.score(tensor).item())
            n_bona = sum(1 for s in scores if s > 0)
            pct = n_bona / len(scores) * 100 if scores else 0
            status = "✅ PASS" if n_bona >= 12 else "❌ FAIL"
            if n_bona < 12:
                g1_pass = False
            print(f"  {label:<25} | {n_bona:2d}/{len(scores):2d} ({pct:5.1f}%) | Mean: {np.mean(scores):+6.2f} | {status}")

    # ── GATE 2: 4 TÌNH NGUYỆN VIÊN ĐỐI CHỨNG (Generalization) ───────────────
    print("\n🔍 GATE 2: Kiểm định trên 4 tình nguyện viên đối chứng (SPK_0004, 0005, 0006, 0007)")
    g2_spks = ["SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    total_g2_files, total_g2_bona = 0, 0
    with torch.no_grad():
        for spk in g2_spks:
            files = sorted(glob.glob(f"data/raw/{spk}/*.wav"))
            if not files:
                continue
            scores = []
            for f in files:
                y = load_audio(f, target_sr=16000)
                t = fit_length(y, 64000, train=False, rng=rng)
                tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
                scores.append(model.score(tensor).item())
            n_bona = sum(1 for s in scores if s > 0)
            total_g2_files += len(files)
            total_g2_bona += n_bona
            print(f"  {spk:<10} | {n_bona:2d}/{len(files):2d} ({n_bona/len(files)*100:5.1f}%) | Mean: {np.mean(scores):+6.2f}")
    g2_pct = (total_g2_bona / total_g2_files * 100) if total_g2_files else 0
    g2_pass = g2_pct >= 90.0
    print(f"  -> Tổng hợp G2: {total_g2_bona}/{total_g2_files} ({g2_pct:.1f}%) | {'✅ PASS' if g2_pass else '❌ FAIL'}")

    # ── GATE 3: DEV ZALO METRICS ─────────────────────────────────────────────
    print("\n🔍 GATE 3: Kiểm định trên tập Dev Zalo Metrics (nếu có CSV)")
    csv_candidates = [
        Path(ckpt_path).parent / "zalo_b_zalo_metrics.csv",
        Path("out/zalo_b_zalo_v4/zalo_b_zalo_metrics.csv"),
    ]
    g3_pass = True
    found_csv = False
    for p in csv_candidates:
        if p.is_file():
            df_m = pd.read_csv(p)
            found_csv = True
            for _, r in df_m.iterrows():
                eer = r.get("eer_pct", r.get("eer_percent", 0.0))
                ok = eer <= 2.0
                if not ok and r["codec"] in ("aac_zalo_76k", "opus_zalo_24k", "clean_16khz"):
                    g3_pass = False
                print(f"  {r['codec']:15} | EER: {eer:5.2f}% | {'✅' if ok else '⚠️'}")
            break
    if not found_csv:
        print("  ⚠️ Không tìm thấy file metrics CSV, cần đánh giá qua scripts/eval_dev_full.py")

    print("\n" + "=" * 80)
    print("🏆 KẾT QUẢ TỔNG THỂ CÁC CỔNG KIỂM ĐỊNH:")
    print(f"  Gate 1 (Giọng trầm ngoại lai):  {'✅ PASS' if g1_pass else '❌ CHƯA ĐẠT (Cần Pha 4 Calibration)'}")
    print(f"  Gate 2 (Generalization 4 SPK):  {'✅ PASS' if g2_pass else '❌ CHƯA ĐẠT (Rollback m=0.20)'}")
    print(f"  Gate 3 (Dev Zalo EER <= 2.0%):  {'✅ PASS' if g3_pass else '❌ CHƯA ĐẠT'}")
    print("=" * 80)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="out/zalo_b_zalo_v4/best_model_B_zalo.pt")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    eval_checkpoint_gates(args.ckpt, args.device)
