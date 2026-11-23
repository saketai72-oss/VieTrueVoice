#!/usr/bin/env python3
"""Quy trình huấn luyện và đánh giá mô hình ViTrueVoice V8 Hoán Đổi (Inverted Generalization).

Seen TTS:   F5-TTS + OmniVoice CFM (VoiceStudio)
Unseen TTS: VieNeu-TTS v3 Turbo

Quy trình 2 pha:
1. RUN 1: Huấn luyện với tập V8 không có SPK_0001 (51.130 dòng, 0% SPK_0001..0007).
   - Đánh giá 4 Cổng kiểm định độc lập:
     * Cổng 1: 15 file gốc SPK_0001 (Dense Slicing + Asymmetric Veto).
     * Cổng 2: 84 file của 5 tình nguyện viên đối chứng held-out (SPK_0003..0007).
     * Cổng 3: 955 file Unseen VieNeu-TTS (EER & minDCF).
     * Cổng 4: 195 file OmniVoice từng bị lọt lưới ở V7 (kiểm tra đảo chiều thành Spoof).
2. QUYẾT ĐỊNH RẼ NHÁNH RUN 2:
   - Nếu Run 1 đạt >= 12/15 (>= 80%) files SPK_0001 -> Hoàn thành xuất sắc, không cần Run 2.
   - Nếu Run 1 < 12/15 -> Kích hoạt Run 2 với `train_v8_f5_omni_with_spk1.csv` (51.255 dòng),
     fine-tune 3 epochs từ checkpoint Run 1, lưu tại `out/zalo_b_zalo_v8_inverted/best_model.pt`.
     Đánh giá lại toàn diện 4 Cổng.
3. Cập nhật DEFAULT_CHECKPOINT trong src/app/server.py.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Đảm bảo đường dẫn gốc của project luôn nằm trong sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Đặt biến môi trường offline cho HuggingFace để ngăn chặn timeout/treo process trên Windows
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import pandas as pd
import torch

from scripts.eval_ssl_aasist import load_model
from src.evaluation.metrics import compute_eer, compute_min_dcf
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores


def run_training_cmd(
    train_manifest: str,
    dev_manifest: str,
    out_dir: str,
    init_ckpt: str,
    phase1_epochs: int = 2,
    phase2_epochs: int = 4,
    patience: int = 3,
    batch_size: int = 8,
    accum_steps: int = 2,
    num_workers: int = 0,
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
        "--batch-size", str(batch_size),
        "--accum-steps", str(accum_steps),
        "--loss", "am_softmax",
        "--am-s", "30.0",
        "--am-m", "0.35",
        "--phase1-epochs", str(phase1_epochs),
        "--phase2-epochs", str(phase2_epochs),
        "--patience", str(patience),
        "--num-workers", str(num_workers),
        "--device", device,
    ]

    print("\n" + "=" * 80)
    print("🚀 BẮT ĐẦU LỆNH HUẤN LUYỆN:")
    print("   " + " ".join(cmd))
    print("=" * 80 + "\n", flush=True)

    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"

    res = subprocess.run(cmd, env=env, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Huấn luyện thất bại với mã lỗi {res.returncode}")

    best_ckpt = out_path / "best_model.pt"
    if not best_ckpt.exists():
        raise FileNotFoundError(f"Không tìm thấy best_model.pt tại {out_path}")
    return best_ckpt


def eval_gate1_spk0001(model, device: str = "cuda") -> dict:
    """CỔNG 1: Đánh giá 15 file bona fide gốc của SPK_0001 (Dense Slicing + Asymmetric Veto)."""
    print("\n🔍 [CỔNG 1] Đánh giá trên 15 file gốc của SPK_0001...")
    raw_dir = _ROOT / "data/raw/SPK_0001"
    raw_files = sorted([
        f for f in raw_dir.glob("*.wav")
        if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])
    ])
    if not raw_files:
        raise FileNotFoundError(f"Không tìm thấy file SPK_0001 trong {raw_dir}")

    scores = []
    file_details = []
    with torch.no_grad():
        for f in raw_files:
            y = load_audio(f, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
            s = pool_scores(model.score(batch), mode="asymmetric_veto")
            scores.append(float(s))
            file_details.append({"file": f.name, "score": float(s), "is_bonafide": bool(s > 0)})

    n_pass = sum(1 for s in scores if s > 0)
    total = len(scores)
    pass_rate = (n_pass / total) * 100.0
    mean_sc = float(np.mean(scores))
    median_sc = float(np.median(scores))
    passed = n_pass >= 12

    print(f"📊 Kết quả Cổng 1 (SPK_0001): {n_pass}/{total} files ({pass_rate:.1f}%) | Mean: {mean_sc:+.2f} | Median: {median_sc:+.2f} | {'✅ PASS' if passed else '⚠️ CHƯA ĐẠT'}")
    return {
        "gate": "Gate 1 - SPK_0001 Isolation",
        "total": total,
        "n_pass": n_pass,
        "pass_rate_pct": pass_rate,
        "mean_score": mean_sc,
        "median_score": median_sc,
        "passed": passed,
        "details": file_details,
    }


def eval_gate2_acceptance_5spk(model, device: str = "cuda") -> dict:
    """CỔNG 2: Đánh giá 84 clip bona fide của 5 tình nguyện viên nghiệm thu độc lập (SPK_0003..0007)."""
    print("\n🔍 [CỔNG 2] Đánh giá trên 5 SPK nghiệm thu held-out (SPK_0003..0007)...")
    speakers = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]

    results_by_spk = {}
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
                batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
                s = pool_scores(model.score(batch), mode="asymmetric_veto")
                scores.append(float(s))

            n_bona = sum(1 for s in scores if s > 0)
            total_files += len(clean_files)
            total_bona += n_bona
            pct = (n_bona / len(clean_files) * 100) if clean_files else 0
            results_by_spk[spk] = {
                "total": len(clean_files),
                "bona": n_bona,
                "pass_rate_pct": pct,
                "mean_score": float(np.mean(scores)) if scores else 0.0,
            }
            print(f"   {spk:<10}: {n_bona:2d}/{len(clean_files):2d} ({pct:5.1f}%) | Mean: {np.mean(scores):+6.2f}")

    overall_pct = (total_bona / total_files * 100) if total_files else 0
    passed = overall_pct >= 90.0
    print(f"🏆 Tổng 5 SPK nghiệm thu: {total_bona}/{total_files} ({overall_pct:.1f}%) | {'✅ PASS' if passed else '❌ FAIL'}")
    return {
        "gate": "Gate 2 - 5 Acceptance Volunteers",
        "by_speaker": results_by_spk,
        "total_files": total_files,
        "total_bona": total_bona,
        "overall_pass_rate_pct": overall_pct,
        "passed": passed,
    }


def eval_gate3_unseen_vieneu(model, dev_bona_df: pd.DataFrame, device: str = "cuda") -> dict:
    """CỔNG 3: Đánh giá 955 file Unseen VieNeu-TTS Benchmark đối soát với Dev Bona Fide, tính EER và minDCF."""
    print("\n🔍 [CỔNG 3] Đánh giá trên 955 file Unseen VieNeu-TTS Benchmark...")
    unseen_path = _ROOT / "data/manifests_zalo/unseen_vieneu_benchmark.csv"
    if not unseen_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {unseen_path}")

    unseen_df = pd.read_csv(unseen_path)
    spoof_scores = []
    t0 = time.time()
    with torch.no_grad():
        for i, (_, row) in enumerate(unseen_df.iterrows()):
            fpath = _ROOT / str(row["audio_path"])
            if not fpath.exists():
                continue
            y = load_audio(fpath, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
            s = pool_scores(model.score(batch), mode="asymmetric_veto")
            spoof_scores.append(float(s))
            if (i + 1) % 300 == 0 or (i + 1) == len(unseen_df):
                print(f"   [VieNeu Unseen] {i+1}/{len(unseen_df)} clips ({time.time() - t0:.1f}s)")

    # Lấy điểm bona fide từ tập Dev Zalo
    print("   Đang tính điểm Dev Bona Fide cho ma trận EER...")
    bona_scores = []
    # Chọn subset representative hoặc toàn bộ bona fide để tính EER
    bona_sample = dev_bona_df[dev_bona_df["label"] == "bonafide"]
    if len(bona_sample) > 2000:
        # Lấy mẫu cân bằng các codecs
        bona_sample = bona_sample.groupby("codec", group_keys=False).apply(lambda x: x.sample(min(len(x), 400), random_state=42))

    with torch.no_grad():
        for i, (_, row) in enumerate(bona_sample.iterrows()):
            fpath = _ROOT / str(row["audio_path"])
            if not fpath.exists():
                continue
            y = load_audio(fpath, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
            s = pool_scores(model.score(batch), mode="asymmetric_veto")
            bona_scores.append(float(s))

    scores = np.array(bona_scores + spoof_scores)
    labels = np.array([1] * len(bona_scores) + [0] * len(spoof_scores))

    eer, eer_thresh = compute_eer(scores, labels)
    min_dcf = compute_min_dcf(scores, labels)

    n_blocked = sum(1 for s in spoof_scores if s <= 0)
    spoof_pass_rate = (n_blocked / len(spoof_scores)) * 100.0 if spoof_scores else 0.0

    print(f"📊 Kết quả Cổng 3 (Unseen VieNeu-TTS):")
    print(f"   EER: {eer * 100:.2f}% (Threshold: {eer_thresh:+.4f}) | minDCF: {min_dcf:.4f}")
    print(f"   Chặn thành công: {n_blocked}/{len(spoof_scores)} clips ({spoof_pass_rate:.1f}%)")

    return {
        "gate": "Gate 3 - Unseen VieNeu-TTS Benchmark",
        "total_unseen_spoof": len(spoof_scores),
        "total_bona_eval": len(bona_scores),
        "eer_pct": float(eer * 100.0),
        "eer_threshold": float(eer_thresh),
        "min_dcf": float(min_dcf),
        "spoof_blocked_count": n_blocked,
        "spoof_block_rate_pct": spoof_pass_rate,
        "mean_spoof_score": float(np.mean(spoof_scores)),
        "mean_bona_score": float(np.mean(bona_scores)),
    }


def eval_gate4_omnivoice_reversal(model, device: str = "cuda") -> dict:
    """CỔNG 4: Kiểm tra 195 file OmniVoice CFM từng bị lọt lưới ở V7 (score > 0), đo tỷ lệ đảo chiều thành Spoof."""
    print("\n🔍 [CỔNG 4] Kiểm tra 195 file OmniVoice từng lọt lưới ở V7...")
    v7_cache = _ROOT / "benchmarks/cached_scores_15spk_v7.csv"
    if not v7_cache.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {v7_cache}")

    df_v7 = pd.read_csv(v7_cache)
    missed_v7 = df_v7[(df_v7["tts_generator"] == "OmniVoice") & (df_v7["score"] > 0)]
    print(f"   Số file OmniVoice từng lọt lưới ở V7: {len(missed_v7)} files")

    reversal_details = []
    vivos_prompt0_scores = {}
    with torch.no_grad():
        for _, row in missed_v7.iterrows():
            fpath = _ROOT / str(row["audio_path"])
            if not fpath.exists():
                continue
            y = load_audio(fpath, target_sr=16000)
            batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
            new_s = float(pool_scores(model.score(batch), mode="asymmetric_veto"))
            old_s = float(row["score"])
            is_reversed = bool(new_s <= 0)

            reversal_details.append({
                "utt_id": row["utt_id"],
                "audio_path": row["audio_path"],
                "old_score_v7": old_s,
                "new_score_v8": new_s,
                "is_reversed_to_spoof": is_reversed,
            })

            if "VIVOSDEV02_omnivoice_prompt_000" in row["utt_id"]:
                vivos_prompt0_scores[row["utt_id"]] = {"old": old_s, "new": new_s}

    n_reversed = sum(1 for r in reversal_details if r["is_reversed_to_spoof"])
    total = len(reversal_details)
    reversal_pct = (n_reversed / total * 100.0) if total else 0.0

    print(f"📊 Kết quả Cổng 4 (OmniVoice Reversal):")
    print(f"   Đã đảo chiều thành Spoof: {n_reversed}/{total} files ({reversal_pct:.1f}%)")
    print(f"   Case Study VIVOSDEV02 prompt 000:")
    for k, v in vivos_prompt0_scores.items():
        print(f"     * {k}: V7 = {v['old']:+.2f} -> V8 = {v['new']:+.2f} ({'✅ FLIPPED TO SPOOF' if v['new'] <= 0 else '❌ STILL BONA'})")

    return {
        "gate": "Gate 4 - OmniVoice CFM Reversal",
        "total_missed_v7": total,
        "n_reversed_to_spoof": n_reversed,
        "reversal_rate_pct": reversal_pct,
        "vivosdev02_prompt0_details": vivos_prompt0_scores,
        "sample_details": reversal_details[:10],
    }


def evaluate_all_gates(ckpt_path: str | Path, dev_manifest_path: str | Path, device: str = "cuda") -> dict:
    """Chạy toàn bộ 4 Cổng kiểm định trên một checkpoint."""
    print("\n" + "=" * 80)
    print(f"🧪 BẮT ĐẦU ĐÁNH GIÁ TOÀN DIỆN 4 CỔNG VỚI CHECKPOINT: {ckpt_path}")
    print("=" * 80)

    model, _ = load_model(str(ckpt_path), device)
    model.eval()

    dev_df = pd.read_csv(dev_manifest_path)

    g1 = eval_gate1_spk0001(model, device=device)
    g2 = eval_gate2_acceptance_5spk(model, device=device)
    g3 = eval_gate3_unseen_vieneu(model, dev_bona_df=dev_df, device=device)
    g4 = eval_gate4_omnivoice_reversal(model, device=device)

    return {
        "checkpoint": str(ckpt_path),
        "gate1_spk0001": g1,
        "gate2_acceptance_5spk": g2,
        "gate3_unseen_vieneu": g3,
        "gate4_omnivoice_reversal": g4,
    }


def update_server_default_checkpoint(new_ckpt_path: str) -> None:
    """Cập nhật DEFAULT_CHECKPOINT trong src/app/server.py."""
    server_file = _ROOT / "src/app/server.py"
    if not server_file.exists():
        print(f"⚠️ Không tìm thấy server.py tại {server_file}")
        return

    content = server_file.read_text(encoding="utf-8")
    rel_path = Path(new_ckpt_path).relative_to(_ROOT) if Path(new_ckpt_path).is_absolute() else Path(new_ckpt_path)
    posix_path = rel_path.as_posix()

    target_block = f'DEFAULT_CHECKPOINT = (\n    Path("{posix_path}")\n    if Path("{posix_path}").exists()\n    else ('

    if f'Path("{posix_path}")' in content:
        print(f"ℹ️ {posix_path} đã có trong DEFAULT_CHECKPOINT của server.py")
        return

    old_anchor = 'DEFAULT_CHECKPOINT = (\n    Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")'
    if old_anchor in content:
        new_content = content.replace(
            'DEFAULT_CHECKPOINT = (\n    Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")',
            f'DEFAULT_CHECKPOINT = (\n    Path("{posix_path}")\n    if Path("{posix_path}").exists()\n    else (\n        Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")',
            1,
        )
        server_file.write_text(new_content, encoding="utf-8")
        print(f"✅ Đã cập nhật DEFAULT_CHECKPOINT trong {server_file} -> {posix_path}")
    else:
        print(f"⚠️ Không tìm thấy vị trí neo chuẩn trong server.py để cập nhật tự động.")


def main():
    parser = argparse.ArgumentParser(description="ViTrueVoice V8 Inverted Generalization Dual Training & 4-Gate Evaluation")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--accum-steps", type=int, default=2)
    parser.add_argument("--phase1-epochs", type=int, default=2)
    parser.add_argument("--phase2-epochs", type=int, default=4)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--force-run2", action="store_true", help="Bắt buộc chạy Run 2 bỏ qua kết quả Run 1")
    parser.add_argument("--skip-run1", action="store_true", help="Bỏ qua Run 1, chạy thẳng Run 2")
    parser.add_argument("--resume-run2", action="store_true", help="Tiếp tục chạy Pha 2 của Run 2 từ checkpoint đã bảo lưu")
    args = parser.parse_args()

    init_ckpt = "out/zalo_b_zalo_v5_local/best_model.pt"
    if not Path(init_ckpt).exists():
        init_ckpt = "out/kaggle_ssl_out/best_model_B.pt"
    print(f"ℹ️ Khởi tạo trọng số ban đầu từ: {init_ckpt}")

    train_no_spk1 = "data/manifests_zalo/train_v8_f5_omni_no_spk1.csv"
    train_with_spk1 = "data/manifests_zalo/train_v8_f5_omni_with_spk1.csv"
    dev_manifest = "data/manifests_zalo/dev_v8_f5_omni.csv"

    full_report = {}

    if args.resume_run2:
        print("\n" + "=" * 80)
        print("🚀 TIẾP TỤC HUẤN LUYỆN RUN 2 TỪ CHECKPOINT ĐÃ BẢO LƯU:")
        print("   Tập train có SPK_0001 (51.255 mẫu)")
        print("   Chạy Pha 2: Mở khóa Wav2Vec 2.0 (Unfrozen SSL) cho 3 epochs")
        print("=" * 80)

        saved_ckpt = Path("out/zalo_b_zalo_v8_inverted/checkpoint_saved_v8_with_spk1.pt")
        if not saved_ckpt.exists():
            saved_ckpt = Path("out/zalo_b_zalo_v8_inverted/best_model.pt")
        print(f"📥 Nạp checkpoint bảo lưu: {saved_ckpt}")

        report_path = _ROOT / "benchmarks/v8_inverted_evaluation_report.json"
        if report_path.exists():
            try:
                full_report = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        run2_dir = "out/zalo_b_zalo_v8_inverted"
        t0 = time.time()
        run2_ckpt = run_training_cmd(
            train_manifest=train_with_spk1,
            dev_manifest=dev_manifest,
            out_dir=run2_dir,
            init_ckpt=str(saved_ckpt),
            phase1_epochs=0,
            phase2_epochs=args.phase2_epochs if args.phase2_epochs is not None else 3,
            patience=args.patience,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            num_workers=args.num_workers,
            device=args.device,
        )
        t_run2 = time.time() - t0
        print(f"\n⏱️ Hoàn thành Run 2 Pha 2 sau {t_run2/60:.1f} phút! Checkpoint: {run2_ckpt}")

        run2_results = evaluate_all_gates(run2_ckpt, dev_manifest, device=args.device)
        full_report["run2_with_spk1"] = run2_results
        winning_ckpt = run2_ckpt
        full_report["winning_checkpoint"] = str(winning_ckpt)
        report_path.write_text(json.dumps(full_report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n📄 Đã cập nhật báo cáo nghiệm thu V8 đầy đủ tại: {report_path}")

        update_server_default_checkpoint(str(winning_ckpt))
        print("\n🏁 TIẾP TỤC HUẤN LUYỆN VÀ ĐÁNH GIÁ RUN 2 HOÀN TẤT THÀNH CÔNG 100%!")
        return

    # ═════════════════════════════════════════════════════════════════════════
    # GIAI ĐOẠN 2: HUẤN LUYỆN LẦN 1 (Run 1 — Không có SPK_0001)
    # ═════════════════════════════════════════════════════════════════════════
    run1_dir = "out/zalo_b_zalo_v8_inverted_no_spk1"
    run1_ckpt = Path(run1_dir) / "best_model.pt"

    if not args.skip_run1:
        print("\n" + "#" * 80)
        print("🎯 BẮT ĐẦU HUẤN LUYỆN LẦN 1: V8 HOÁN ĐỔI (SEEN: F5 + OMNIVOICE CFM) — KHÔNG CÓ SPK_0001")
        print(f"   Train Manifest: {train_no_spk1}")
        print(f"   Dev Manifest:   {dev_manifest}")
        print("#" * 80)

        t0 = time.time()
        run1_ckpt = run_training_cmd(
            train_manifest=train_no_spk1,
            dev_manifest=dev_manifest,
            out_dir=run1_dir,
            init_ckpt=init_ckpt,
            phase1_epochs=args.phase1_epochs,
            phase2_epochs=args.phase2_epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            num_workers=args.num_workers,
            device=args.device,
        )
        t_run1 = time.time() - t0
        print(f"\n⏱️ Hoàn thành Run 1 sau {t_run1/60:.1f} phút! Checkpoint: {run1_ckpt}")

    # Đánh giá toàn diện 4 Cổng cho Run 1
    run1_results = evaluate_all_gates(run1_ckpt, dev_manifest, device=args.device)
    full_report["run1_no_spk1"] = run1_results

    # ═════════════════════════════════════════════════════════════════════════
    # GIAI ĐOẠN 3: QUYẾT ĐỊNH PHÂN NHÁNH LẦN 2 (Run 2 — Tích hợp SPK_0001)
    # ═════════════════════════════════════════════════════════════════════════
    g1_pass_count = run1_results["gate1_spk0001"]["n_pass"]
    need_run2 = args.force_run2 or (g1_pass_count < 12)

    winning_ckpt = run1_ckpt

    if not need_run2:
        print("\n" + "=" * 80)
        print("🎉 KẾT QUẢ RUN 1 THÀNH CÔNG XUẤT SẮC!")
        print(f"   Mô hình không cần SPK_0001 trong train nhưng vẫn nhận diện đúng {g1_pass_count}/15 files SPK_0001 ({run1_results['gate1_spk0001']['pass_rate_pct']:.1f}% >= 80%).")
        print("   Không cần thiết phải thực hiện Run 2.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print(f"⚠️ KẾT QUẢ RUN 1 TRÊN SPK_0001: {g1_pass_count}/15 files (< 12/15, tức < 80.0%)")
        print("   KÍCH HOẠT RUN 2: Tích hợp SPK_0001 vào Train (fine-tune 3 epochs từ Checkpoint Run 1).")
        print("=" * 80)

        run2_dir = "out/zalo_b_zalo_v8_inverted"
        t0 = time.time()
        run2_ckpt = run_training_cmd(
            train_manifest=train_with_spk1,
            dev_manifest=dev_manifest,
            out_dir=run2_dir,
            init_ckpt=str(run1_ckpt),
            phase1_epochs=1,
            phase2_epochs=3,
            patience=args.patience,
            batch_size=args.batch_size,
            accum_steps=args.accum_steps,
            num_workers=args.num_workers,
            device=args.device,
        )
        t_run2 = time.time() - t0
        print(f"\n⏱️ Hoàn thành Run 2 sau {t_run2/60:.1f} phút! Checkpoint: {run2_ckpt}")

        run2_results = evaluate_all_gates(run2_ckpt, dev_manifest, device=args.device)
        full_report["run2_with_spk1"] = run2_results
        winning_ckpt = run2_ckpt

    # ═════════════════════════════════════════════════════════════════════════
    # CẬP NHẬT HỆ THỐNG VÀ XUẤT BÁO CÁO
    # ═════════════════════════════════════════════════════════════════════════
    full_report["winning_checkpoint"] = str(winning_ckpt)
    report_path = _ROOT / "benchmarks/v8_inverted_evaluation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(full_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📄 Đã lưu báo cáo nghiệm thu V8 đầy đủ tại: {report_path}")

    # Cập nhật DEFAULT_CHECKPOINT trong server.py
    update_server_default_checkpoint(str(winning_ckpt))

    print("\n🏁 QUY TRÌNH HUẤN LUYỆN VÀ ĐÁNH GIÁ V8 HOÀN TẤT THÀNH CÔNG 100%!")


if __name__ == "__main__":
    main()
