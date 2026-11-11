#!/usr/bin/env python3
"""Quy trình huấn luyện kép (Dual-Seen Re-training) ViTrueVoice.

Bao gồm 2 pha huấn luyện theo yêu cầu người dùng:
1. RUN 1: Huấn luyện với tập Dual-Seen (VIVOS + Common Voice + F5-TTS + VieNeu-TTS) KHÔNG CÓ SPK_0001 (0% SPK_0001..0007).
   - Kiểm thử độc lập trên 15 file bona fide của SPK_0001 với Multi-window Max-Pooling.
   - Nếu tỷ lệ nhận diện đúng >= 80% (>= 12/15) và Mean Score > 0 -> Khẳng định mô hình tự tổng quát hóa tốt, hoàn thành.
2. RUN 2: Nếu Run 1 chưa nhận diện được SPK_0001 (< 80%), thực hiện đưa SPK_0001 (bona fide + F5-TTS + VieNeu-TTS) vào train.
   - Tái huấn luyện từ checkpoint tốt nhất của Run 1.
   - Đánh giá lại toàn diện SPK_0001 và 5 tình nguyện viên đối chứng held-out (SPK_0003..0007).
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import torch

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores


def eval_spk0001(ckpt_path: str | Path, device: str = "cuda") -> dict:
    """Đánh giá 15 phát ngôn gốc của SPK_0001 với Multi-window Max-Pooling."""
    print(f"\n🔍 [EVAL SPK_0001] Đánh giá trên 15 file gốc của SPK_0001 với Checkpoint: {ckpt_path}")
    raw_dir = _ROOT / "data/raw/SPK_0001"
    raw_files = sorted([
        f for f in raw_dir.glob("*.wav")
        if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])
    ])
    if not raw_files:
        raise FileNotFoundError(f"Không tìm thấy file SPK_0001 trong {raw_dir}")

    model, _ = load_model(str(ckpt_path), device)
    model.eval()

    scores = []
    with torch.no_grad():
        for f in raw_files:
            y = load_audio(f, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
            s = pool_scores(model.score(batch), mode="max")
            scores.append(s)

    n_pass = sum(1 for s in scores if s > 0)
    total = len(scores)
    pass_rate = (n_pass / total) * 100.0
    mean_score = float(np.mean(scores))
    median_score = float(np.median(scores))

    print(f"📊 Kết quả SPK_0001: {n_pass}/{total} files nhận diện đúng Bona Fide ({pass_rate:.1f}%)")
    print(f"   Mean Score: {mean_score:+.2f} | Median Score: {median_score:+.2f}")
    for f, s in zip(raw_files, scores):
        status = "✅ PASS" if s > 0 else "❌ SPOOF_PREDICTED"
        print(f"   - {f.name}: {s:+6.2f} ({status})")

    return {
        "total": total,
        "n_pass": n_pass,
        "pass_rate_pct": pass_rate,
        "mean_score": mean_score,
        "median_score": median_score,
        "scores": scores,
    }


def eval_acceptance_speakers(ckpt_path: str | Path, device: str = "cuda") -> dict:
    """Đánh giá 84 clip bona fide của 5 tình nguyện viên đối chứng held-out (SPK_0003..0007)."""
    print(f"\n🔍 [EVAL ACCEPTANCE 5 SPK] Đánh giá trên 5 SPK đối chứng held-out (SPK_0003..0007)...")
    speakers = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    model, _ = load_model(str(ckpt_path), device)
    model.eval()

    results = {}
    total_files, total_bona = 0, 0
    with torch.no_grad():
        for spk in speakers:
            raw_dir = _ROOT / f"data/raw/{spk}"
            if not raw_dir.exists():
                continue
            all_files = sorted(list(raw_dir.glob("*.wav")) + list(raw_dir.glob("*.m4a")))
            clean_files = [f for f in all_files if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
            scores = []
            for f in clean_files:
                y = load_audio(f, target_sr=16000)
                batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5).to(device)
                s = pool_scores(model.score(batch), mode="max")
                scores.append(s)

            n_bona = sum(1 for s in scores if s > 0)
            total_files += len(clean_files)
            total_bona += n_bona
            pct = (n_bona / len(clean_files) * 100) if clean_files else 0
            results[spk] = {
                "total": len(clean_files),
                "bona": n_bona,
                "pass_rate_pct": pct,
                "mean_score": float(np.mean(scores)) if scores else 0.0,
            }
            print(f"   {spk:<10}: {n_bona:2d}/{len(clean_files):2d} ({pct:5.1f}%) | Mean: {np.mean(scores):+6.2f}")

    overall_pct = (total_bona / total_files * 100) if total_files else 0
    print(f"🏆 Tổng 5 SPK đối chứng: {total_bona}/{total_files} ({overall_pct:.1f}%)")
    return {
        "by_speaker": results,
        "total_files": total_files,
        "total_bona": total_bona,
        "overall_pass_rate_pct": overall_pct,
    }


def run_training_cmd(
    train_manifest: str,
    dev_manifest: str,
    out_dir: str,
    init_ckpt: str,
    phase1_epochs: int = 2,
    phase2_epochs: int = 3,
    patience: int = 3,
    batch_size: int = 16,
    accum_steps: int = 1,
    device: str = "cuda",
) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-u",
        "scripts/train.py",
        "--branch", "B_zalo",
        "--init-ckpt", init_ckpt,
        "--train-manifest", train_manifest,
        "--dev-manifest", dev_manifest,
        "--audio-root", ".",
        "--out-dir", str(out_path),
        "--dual-seen",
        "--batch-size", str(batch_size),
        "--accum-steps", str(accum_steps),
        "--loss", "am_softmax",
        "--am-s", "30.0",
        "--am-m", "0.35",
        "--phase1-epochs", str(phase1_epochs),
        "--phase2-epochs", str(phase2_epochs),
        "--patience", str(patience),
        "--num-workers", "2",
        "--device", device,
    ]

    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU LỆNH HUẤN LUYỆN:")
    print("   " + " ".join(cmd))
    print("=" * 80 + "\n")

    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Huấn luyện thất bại với mã lỗi {res.returncode}")

    best_ckpt = out_path / "best_model.pt"
    if not best_ckpt.exists():
        raise FileNotFoundError(f"Không tìm thấy best_model.pt tại {out_path}")
    return best_ckpt


def main():
    parser = argparse.ArgumentParser(description="Dual-Seen Re-training & SPK_0001 Isolation Testing")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--accum-steps", type=int, default=2)
    parser.add_argument("--phase1-epochs", type=int, default=2)
    parser.add_argument("--phase2-epochs", type=int, default=8)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--force-run2", action="store_true", help="Bắt buộc chạy Run 2 bỏ qua kết quả Run 1")
    parser.add_argument("--skip-run1", action="store_true", help="Bỏ qua Run 1, chạy thẳng Run 2")
    args = parser.parse_args()

    init_ckpt = "out/zalo_b_zalo_v5_local/best_model.pt"
    if not Path(init_ckpt).exists():
        init_ckpt = "out/kaggle_ssl_out/best_model_B.pt"
    print(f"ℹ️ Khởi tạo trọng số từ: {init_ckpt}")

    results_summary = {}

    # ═════════════════════════════════════════════════════════════════════════
    # GIAI ĐOẠN 1: RUN 1 — KHÔNG CÓ SPK_0001
    # ═════════════════════════════════════════════════════════════════════════
    run1_ckpt = Path("out/zalo_b_zalo_v7_dual_no_spk1/best_model.pt")
    if not args.skip_run1:
        print("\n" + "#" * 80)
        print("🎯 BẮT ĐẦU HUẤN LUYỆN LẦN 1: DUAL-SEEN (F5 + VIENEU) — KHÔNG CÓ SPK_0001")
        print("   Tập huấn luyện: data/manifests_zalo/train_dual_seen_no_spk1.csv (54.225 dòng)")
        print("#" * 80)

        t0 = time.time()
        run1_ckpt = run_training_cmd(
            train_manifest="data/manifests_zalo/train_dual_seen_no_spk1.csv",
            dev_manifest="data/manifests_zalo/dev_zalo_dual_seen.csv",
            out_dir="out/zalo_b_zalo_v7_dual_no_spk1",
            init_ckpt=init_ckpt,
            phase1_epochs=2,
            phase2_epochs=4,
            patience=3,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            device=args.device,
        )
        t_run1 = time.time() - t0
        print(f"\n⏱️ Hoàn thành Run 1 sau {t_run1/60:.1f} phút! Checkpoint: {run1_ckpt}")

    # Đánh giá Run 1 trên SPK_0001
    run1_eval = eval_spk0001(run1_ckpt, device=args.device)
    run1_acc = eval_acceptance_speakers(run1_ckpt, device=args.device)
    results_summary["run1_no_spk1"] = {
        "checkpoint": str(run1_ckpt),
        "spk0001": run1_eval,
        "acceptance_5spk": run1_acc,
    }

    # Quyết định có cần Run 2 hay không
    need_run2 = args.force_run2 or (run1_eval["n_pass"] < 12)

    if not need_run2:
        print("\n" + "=" * 80)
        print("🎉 KẾT QUẢ RUN 1 THÀNH CÔNG RỰC RỠ!")
        print(f"   Mô hình không cần SPK_0001 trong train nhưng vẫn nhận diện được {run1_eval['n_pass']}/{run1_eval['total']} files ({run1_eval['pass_rate_pct']:.1f}%).")
        print("   Không cần thiết phải thực hiện Run 2.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print(f"⚠️ KẾT QUẢ RUN 1 CHƯA ĐẠT CHỈ TIÊU TRÊN SPK_0001: {run1_eval['n_pass']}/{run1_eval['total']} ({run1_eval['pass_rate_pct']:.1f}%)")
        print("   Theo chỉ thị người dùng, bắt đầu RUN 2: Bổ sung SPK_0001 vào Train.")
        print("=" * 80)

        t0 = time.time()
        run2_ckpt = run_training_cmd(
            train_manifest="data/manifests_zalo/train_dual_seen_with_spk1.csv",
            dev_manifest="data/manifests_zalo/dev_zalo_dual_seen.csv",
            out_dir="out/zalo_b_zalo_v7_dual_with_spk1",
            init_ckpt=str(run1_ckpt),
            phase1_epochs=1,
            phase2_epochs=args.phase2_epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            device=args.device,
        )
        t_run2 = time.time() - t0
        print(f"\n⏱️ Hoàn thành Run 2 sau {t_run2/60:.1f} phút! Checkpoint: {run2_ckpt}")

        run2_eval = eval_spk0001(run2_ckpt, device=args.device)
        run2_acc = eval_acceptance_speakers(run2_ckpt, device=args.device)
        results_summary["run2_with_spk1"] = {
            "checkpoint": str(run2_ckpt),
            "spk0001": run2_eval,
            "acceptance_5spk": run2_acc,
        }

    # Lưu kết quả đối chứng
    res_path = Path("benchmarks/dual_seen_training_comparison.json")
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text(json.dumps(results_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📄 Đã lưu báo cáo so sánh đối chứng tại: {res_path}")


if __name__ == "__main__":
    main()
