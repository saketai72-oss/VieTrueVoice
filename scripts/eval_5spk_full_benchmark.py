import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import soundfile as sf
import torch
from sklearn.metrics import roc_auc_score, roc_curve

from scripts.eval_ssl_aasist import load_model
from src.evaluation.metrics import compute_eer
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def get_clean_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    all_files = sorted(list(directory.glob("*.wav")))
    # Exclude codec variations to evaluate pure acoustic generalization
    return [
        f for f in all_files
        if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])
    ]


def evaluate_set(model, files: list[Path], device: str, rng: np.random.Generator) -> list[dict]:
    results = []
    with torch.no_grad():
        for f in files:
            y = load_audio(f, target_sr=16000)
            dur = len(y) / 16000.0
            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
            score = model.score(tensor).item()
            results.append({
                "file": f.name,
                "path": str(f),
                "duration_s": round(dur, 2),
                "score": score
            })
    return results


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 115)
    print("🔬 KIỂM ĐỊNH TOÀN DIỆN BỘ NGHIỆM THU 5 TÌNH NGUYỆN VIÊN (V5 LOCAL CHECKPOINT)")
    print(f"Device: {device}")
    print("=" * 115)

    ckpt_path = "out/zalo_b_zalo_v5_local/best_model.pt"
    if not Path(ckpt_path).exists():
        print(f"❌ Không tìm thấy checkpoint: {ckpt_path}")
        return

    print(f"Loading checkpoint: {ckpt_path}")
    model, _ = load_model(ckpt_path, device)
    model.eval()

    speakers = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    rng = np.random.default_rng(0)

    all_records = []
    speaker_summaries = []

    for spk in speakers:
        raw_dir = Path(f"data/raw/{spk}")
        f5_dir = Path(f"data/spoof_f5tts/{spk}")
        vn_dir = Path(f"data/spoof_vieneu/{spk}")

        bona_files = get_clean_files(raw_dir)
        f5_files = get_clean_files(f5_dir)
        vn_files = get_clean_files(vn_dir)

        bona_res = evaluate_set(model, bona_files, device, rng)
        f5_res = evaluate_set(model, f5_files, device, rng)
        vn_res = evaluate_set(model, vn_files, device, rng)

        for r in bona_res:
            r.update({"speaker_id": spk, "category": "bonafide", "true_label": 1})
        for r in f5_res:
            r.update({"speaker_id": spk, "category": "spoof_f5tts", "true_label": 0})
        for r in vn_res:
            r.update({"speaker_id": spk, "category": "spoof_vieneu", "true_label": 0})

        all_records.extend(bona_res + f5_res + vn_res)

        b_scores = np.array([r["score"] for r in bona_res]) if bona_res else np.array([])
        f_scores = np.array([r["score"] for r in f5_res]) if f5_res else np.array([])
        v_scores = np.array([r["score"] for r in vn_res]) if vn_res else np.array([])

        b_pass = np.sum(b_scores > 0)
        b_total = len(b_scores)
        b_rate = (b_pass / b_total * 100) if b_total else 0.0

        f_det = np.sum(f_scores < 0)
        f_total = len(f_scores)
        f_rate = (f_det / f_total * 100) if f_total else 0.0

        v_det = np.sum(v_scores < 0)
        v_total = len(v_scores)
        v_rate = (v_det / v_total * 100) if v_total else 0.0

        # AUC & EER riêng cho từng speaker (Bona vs All Spoof)
        spk_scores = np.concatenate([b_scores, f_scores, v_scores])
        spk_labels = np.concatenate([np.ones_like(b_scores), np.zeros_like(f_scores), np.zeros_like(v_scores)])

        if len(np.unique(spk_labels)) == 2:
            eer_val, thresh_val = compute_eer(spk_scores, spk_labels)
            auc_val = float(roc_auc_score(spk_labels, spk_scores))
        else:
            eer_val, thresh_val, auc_val = float("nan"), float("nan"), float("nan")

        speaker_summaries.append({
            "speaker_id": spk,
            "bona_count": b_total,
            "bona_pass": b_pass,
            "bona_rate": b_rate,
            "bona_mean": float(np.mean(b_scores)) if b_total else 0.0,
            "bona_median": float(np.median(b_scores)) if b_total else 0.0,
            "f5_count": f_total,
            "f5_det": f_det,
            "f5_rate": f_rate,
            "f5_mean": float(np.mean(f_scores)) if f_total else 0.0,
            "vn_count": v_total,
            "vn_det": v_det,
            "vn_rate": v_rate,
            "vn_mean": float(np.mean(v_scores)) if v_total else 0.0,
            "eer_pct": eer_val * 100 if not np.isnan(eer_val) else 0.0,
            "auc": auc_val,
        })

    # In Bảng Tổng Hợp Chi Tiết theo từng Người Nói
    print("\n" + "=" * 115)
    print("📊 BẢNG 1: HIỆU NĂNG PHÂN BIỆT THEO TỪNG TÌNH NGUYỆN VIÊN (QUYẾT ĐỊNH TẠI θ = 0)")
    print("=" * 115)
    header = f"{'Speaker':<10} | {'Bona Fide Pass':<16} | {'Bona Mean':>10} | {'F5-TTS Det':<14} | {'F5 Mean':>9} | {'VieNeu Det':<14} | {'VN Mean':>9} | {'EER (%)':>8} | {'AUC':>7}"
    print(header)
    print("-" * len(header))

    for s in speaker_summaries:
        b_str = f"{s['bona_pass']}/{s['bona_count']} ({s['bona_rate']:5.1f}%)"
        f_str = f"{s['f5_det']}/{s['f5_count']} ({s['f5_rate']:5.1f}%)"
        v_str = f"{s['vn_det']}/{s['vn_count']} ({s['vn_rate']:5.1f}%)"
        print(f"{s['speaker_id']:<10} | {b_str:<16} | {s['bona_mean']:+10.2f} | {f_str:<14} | {s['f5_mean']:+9.2f} | {v_str:<14} | {s['vn_mean']:+9.2f} | {s['eer_pct']:7.2f}% | {s['auc']:7.4f}")

    # Bảng Pooled Tổng Hợp Toàn Bộ 5 Speaker
    df_all = pd.DataFrame(all_records)
    out_csv = Path("out/benchmarks_5spk_detailed.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"\n📁 Đã lưu toàn bộ {len(df_all)} bản ghi chi tiết tại: {out_csv}")

    bona_all = df_all[df_all["category"] == "bonafide"]["score"].values
    f5_all = df_all[df_all["category"] == "spoof_f5tts"]["score"].values
    vn_all = df_all[df_all["category"] == "spoof_vieneu"]["score"].values
    spoof_all = df_all[df_all["true_label"] == 0]["score"].values

    total_bona_pass = np.sum(bona_all > 0)
    total_f5_det = np.sum(f5_all < 0)
    total_vn_det = np.sum(vn_all < 0)
    total_spoof_det = np.sum(spoof_all < 0)

    # EER & AUC Pooled
    y_seen = np.array([1]*len(bona_all) + [0]*len(f5_all))
    s_seen = np.concatenate([bona_all, f5_all])
    eer_seen, _ = compute_eer(s_seen, y_seen)
    auc_seen = float(roc_auc_score(y_seen, s_seen))

    y_unseen = np.array([1]*len(bona_all) + [0]*len(vn_all))
    s_unseen = np.concatenate([bona_all, vn_all])
    eer_unseen, _ = compute_eer(s_unseen, y_unseen)
    auc_unseen = float(roc_auc_score(y_unseen, s_unseen))

    y_total = np.array([1]*len(bona_all) + [0]*len(spoof_all))
    s_total = np.concatenate([bona_all, spoof_all])
    eer_total, _ = compute_eer(s_total, y_total)
    auc_total = float(roc_auc_score(y_total, s_total))

    print("\n" + "=" * 115)
    print("🏆 BẢNG 2: TỔNG HỢP POOLED TRÊN TOÀN BỘ 5 TÌNH NGUYỆN VIÊN (84 BONA FIDE + 158 SPOOF = 242 MẪU)")
    print("=" * 115)
    print(f"1. Bona Fide Accuracy (Score > 0)      : {total_bona_pass}/{len(bona_all)} ({total_bona_pass/len(bona_all)*100:.2f}%) | Mean: {np.mean(bona_all):+6.2f} | Median: {np.median(bona_all):+6.2f}")
    print(f"2. F5-TTS Seen Spoof Det (Score < 0)   : {total_f5_det}/{len(f5_all)} ({total_f5_det/len(f5_all)*100:.2f}%) | Mean: {np.mean(f5_all):+6.2f} | Median: {np.median(f5_all):+6.2f}")
    print(f"3. VieNeu Unseen Spoof Det (Score < 0) : {total_vn_det}/{len(vn_all)} ({total_vn_det/len(vn_all)*100:.2f}%) | Mean: {np.mean(vn_all):+6.2f} | Median: {np.median(vn_all):+6.2f}")
    print(f"4. Tổng Spoof Det (Seen + Unseen)      : {total_spoof_det}/{len(spoof_all)} ({total_spoof_det/len(spoof_all)*100:.2f}%) | Mean: {np.mean(spoof_all):+6.2f}")
    print("-" * 115)
    print(f"🎯 Seen TTS (F5-TTS) Discrimination    : EER = {eer_seen*100:5.2f}% | AUC = {auc_seen:.4f}")
    print(f"🎯 Unseen TTS (VieNeu) Discrimination  : EER = {eer_unseen*100:5.2f}% | AUC = {auc_unseen:.4f}")
    print(f"🔥 TOÀN BỘ BỘ NGHIỆM THU (POOLED)     : EER = {eer_total*100:5.2f}% | AUC = {auc_total:.4f}")
    print("=" * 115)

    # Liệt kê các ca lỗi cá biệt
    print("\n🔍 BẢNG 3: CHI TIẾT CÁC CA NHẬN DIỆN LỖI (CẦN XỬ LÝ / GIẢI THÍCH TRONG BÁO CÁO):")
    fa_bona = df_all[(df_all["category"] == "bonafide") & (df_all["score"] <= 0)]
    fa_spoof = df_all[(df_all["true_label"] == 0) & (df_all["score"] >= 0)]

    print(f"\n⚠️ False Alarm trên Bona Fide (Giọng thật bị gắn nhãn Spoof): {len(fa_bona)} ca")
    if len(fa_bona) > 0:
        for _, r in fa_bona.iterrows():
            print(f"   - [{r['speaker_id']}] {r['file']:<22} | Dur: {r['duration_s']:4.1f}s | Score: {r['score']:+7.2f}")

    print(f"\n⚠️ False Accept trên Spoof (Giọng giả bị lọt qua): {len(fa_spoof)} ca")
    if len(fa_spoof) > 0:
        for _, r in fa_spoof.iterrows():
            print(f"   - [{r['speaker_id']}] {r['file']:<22} | Eng: {r['category']:<12} | Dur: {r['duration_s']:4.1f}s | Score: {r['score']:+7.2f}")
    else:
        print("   ✅ TUYỆT VỜI: 0 ca False Accept trên toàn bộ 158 mẫu Spoof (100% chặn đứng F5-TTS và VieNeu-TTS)!")


if __name__ == "__main__":
    main()
