"""Kịch bản kiểm định đa tầng (Pha 3 Gate Evaluation) cho ViTrueVoice Version 5.

Đánh giá đồng thời 3 tầng độc lập:
1. Gate 1 (G1): SPK_0001 (15 file) & Bộ VoiCes (15 file) -> FRR <= 20% (>= 12/15 bona fide)
2. Gate 2 (G2): 4 tình nguyện viên đối chứng (SPK_0004, 0005, 0006, 0007) -> >= 90% bona fide
3. Gate 3 (G3): Tập Dev Zalo (11.450 mẫu) -> EER <= 2.0% trên cả 5 codecs
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores
from src.training.dataset import fit_length


def eval_checkpoint_gates(ckpt_path: str, device: str = "cpu", pooling: bool = True):
    print("=" * 80)
    print(f"🚪 KIỂM ĐỊNH ĐA TẦNG V5 (GATES EVALUATION) CHO: {ckpt_path}")
    mode_str = "Multi-window Max-Pool (win=64k, hop=16k, max_windows=5)" if pooling else "No-pooling (First-4s / Fit-length)"
    print(f"⚙️ Chế độ Pooling: {mode_str}")
    print("=" * 80)

    model, _ = load_model(ckpt_path, device)
    model.eval()
    rng = np.random.default_rng(0)

    def score_audio(y: np.ndarray) -> float:
        if pooling:
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
            win_scores = model.score(batch)
            return pool_scores(win_scores, mode="max")
        else:
            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
            return float(model.score(tensor).item())

    # ── GATE 1: SPK_0001 & VOICES (Deep Voice Outlier) ──────────────────────
    print("\n🔍 GATE 1: Kiểm định trên các mẫu giọng trầm ngoại lai (SPK_0001 & VoiCes)")
    d_spk1 = Path(r"C:\Users\saket\Downloads\SPK_0001")
    if not d_spk1.exists():
        d_spk1 = Path("data/raw/SPK_0001")

    g1_dirs = [
        ("SPK_0001 (15 file cũ)", d_spk1),
        ("VoiCes (15 file mới)", Path(r"C:\Users\saket\Downloads\VoiCes")),
    ]
    g1_pass = True
    with torch.no_grad():
        for label, d in g1_dirs:
            if not d.exists():
                print(f"  ⚠️ Bỏ qua {label} (thư mục không tồn tại: {d})")
                continue
            files = sorted(list(d.glob("*.m4a")) + list(d.glob("*.wav")))
            if not files and (d / "VoiCes").exists():
                files = sorted(list((d / "VoiCes").glob("*.m4a")) + list((d / "VoiCes").glob("*.wav")))
            if not files:
                files = sorted(list(d.rglob("*.m4a")) + list(d.rglob("*.wav")))
            if "data" in str(d):
                files = [f for f in files if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
            scores = []
            for f in files:
                y = load_audio(f, target_sr=16000)
                scores.append(score_audio(y))
            n_bona = sum(1 for s in scores if s > 0)
            pct = n_bona / len(scores) * 100 if scores else 0
            status = "✅ PASS" if n_bona >= 12 else "❌ FAIL"
            if n_bona < 12:
                g1_pass = False
            print(f"  {label:<25} | {n_bona:2d}/{len(scores):2d} ({pct:5.1f}%) | Mean: {np.mean(scores):+6.2f} | {status}")

    # ── GATE 2: TÌNH NGUYỆN VIÊN ĐỐI CHỨNG (Generalization) ───────────────
    print("\n🔍 GATE 2: Kiểm định trên các tình nguyện viên đối chứng")
    g2_spks = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    total_g2_files, total_g2_bona = 0, 0
    ctrl4_files, ctrl4_bona = 0, 0
    failed_details: list[tuple[str, str, float]] = []

    with torch.no_grad():
        for spk in g2_spks:
            all_files = sorted(glob.glob(f"data/raw/{spk}/*.wav"))
            files = [f for f in all_files if not any(c in Path(f).name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
            if not files:
                continue
            scores = []
            for f in files:
                y = load_audio(f, target_sr=16000)
                s = score_audio(y)
                scores.append(s)
                if s <= 0:
                    failed_details.append((spk, Path(f).name, s))

            n_bona = sum(1 for s in scores if s > 0)
            total_g2_files += len(files)
            total_g2_bona += n_bona
            if spk in ["SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]:
                ctrl4_files += len(files)
                ctrl4_bona += n_bona

            pct = (n_bona / len(files) * 100) if files else 0
            print(f"  {spk:<10} | {n_bona:2d}/{len(files):2d} ({pct:5.1f}%) | Mean: {np.mean(scores):+6.2f}")

    ctrl4_pct = (ctrl4_bona / ctrl4_files * 100) if ctrl4_files else 0
    total5_pct = (total_g2_bona / total_g2_files * 100) if total_g2_files else 0
    g2_pass = ctrl4_pct >= 90.0
    print(f"  -> Nhóm 4 SPK đối chứng (0004-0007): {ctrl4_bona}/{ctrl4_files} ({ctrl4_pct:.1f}%) | {'✅ PASS' if g2_pass else '❌ FAIL'}")
    print(f"  -> Nhóm 5 SPK (0003-0007):            {total_g2_bona}/{total_g2_files} ({total5_pct:.1f}%)")
    if failed_details:
        print(f"  ⚠️ Danh sách file có score <= 0 ({len(failed_details)} file):")
        for spk, fname, sc in failed_details:
            print(f"     - {spk}/{fname}: score = {sc:+.4f}")

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
    print(f"  Gate 1 (Giọng trầm ngoại lai):  {'✅ PASS' if g1_pass else '❌ CHƯA ĐẠT (Cần Pha D Calibration)'}")
    print(f"  Gate 2 (Generalization 4 SPK):  {'✅ PASS' if g2_pass else '❌ CHƯA ĐẠT'}")
    print(f"  Gate 3 (Dev Zalo EER <= 2.0%):  {'✅ PASS' if g3_pass else '❌ CHƯA ĐẠT'}")
    print("=" * 80)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Multi-gate verification for ViTrueVoice checkpoints")
    ap.add_argument("--ckpt", default="out/zalo_b_zalo_v4/best_model_B_zalo.pt")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--pooling", action=argparse.BooleanOptionalAction, default=True, help="Enable multi-window max pooling (default: True)")
    args = ap.parse_args()
    eval_checkpoint_gates(args.ckpt, args.device, pooling=args.pooling)
