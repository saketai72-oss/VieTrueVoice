"""Đánh giá chi tiết 15 mẫu giọng thật Zalo M4A của SPK_0001 bằng Checkpoint B_zalo Phase 2 (Version 3)
và đối chiếu trực tiếp với Checkpoint B gốc và Checkpoint B_zalo Version 2.
"""

from __future__ import annotations
import glob
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


# Kết quả Version 2 ghi nhận trước đó từ log chẩn đoán:
V2_SCORES = {
    "SPK_0001_01.wav.m4a": -6.39,
    "SPK_0001_02.wav.m4a": -9.58,
    "SPK_0001_03.wav.m4a": -14.88,
    "SPK_0001_04.wav.m4a": -2.34,
    "SPK_0001_05.wav.m4a": -0.38,
    "SPK_0001_06.wav.m4a": -1.31,
    "SPK_0001_07.wav.m4a": -11.67,
    "SPK_0001_08.wav.m4a": -7.19,
    "SPK_0001_09.wav.m4a": -8.60,
    "SPK_0001_10.wav.m4a": -1.67,
    "SPK_0001_11.wav.m4a": -8.25,
    "SPK_0001_12.wav.m4a": +1.04,
    "SPK_0001_13.wav.m4a": +5.41,
    "SPK_0001_14.wav.m4a": +3.02,
    "SPK_0001_15.wav.m4a": -1.79,
}


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    ckpt_v3_path = "out/zalo_b_zalo_v3/best_model_B_zalo.pt"
    ckpt_base_path = "out/kaggle_ssl_out/best_model_B.pt"
    
    print(f"Loading Model V3: {ckpt_v3_path}")
    model_v3, _ = load_model(ckpt_v3_path, device)
    model_v3.eval()
    
    model_base = None
    if os.path.exists(ckpt_base_path):
        print(f"Loading Model Baseline: {ckpt_base_path}")
        model_base, _ = load_model(ckpt_base_path, device)
        model_base.eval()
        
    m4a_dir = Path(r"C:\Users\saket\Downloads\SPK_0001")
    if not m4a_dir.exists():
        print(f"ERROR: {m4a_dir} not found!")
        return
        
    files = sorted(glob.glob(str(m4a_dir / "*.wav.m4a")))
    print(f"Found {len(files)} M4A files in {m4a_dir}")
    
    rng = np.random.default_rng(0)
    records = []
    
    with torch.no_grad():
        for file_path in files:
            fname = Path(file_path).name
            
            # Load via audio_loader (in-memory ffmpeg pipe to 16kHz mono)
            y = load_audio(file_path, target_sr=16000)
            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
            
            score_v3 = model_v3.score(tensor).item()
            verdict_v3 = "BONA_FIDE" if score_v3 > 0.0 else "SPOOF"
            
            score_base = None
            verdict_base = None
            if model_base is not None:
                score_base = model_base.score(tensor).item()
                verdict_base = "BONA_FIDE" if score_base > 0.0 else "SPOOF"
                
            score_v2 = V2_SCORES.get(fname, None)
            verdict_v2 = ("BONA_FIDE" if score_v2 > 0.0 else "SPOOF") if score_v2 is not None else None
            
            records.append({
                "file": fname,
                "score_baseline": score_base,
                "verdict_baseline": verdict_base,
                "score_v2": score_v2,
                "verdict_v2": verdict_v2,
                "score_v3": score_v3,
                "verdict_v3": verdict_v3,
                "delta_v3_vs_v2": (score_v3 - score_v2) if score_v2 is not None else None,
            })
            
    df = pd.DataFrame(records)
    out_csv = Path("out/zalo_b_zalo_v3/spk0001_eval_v3.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved CSV to: {out_csv}\n")
    
    print("=" * 105)
    print(f"{'File':<22} | {'V2 Score':>9} {'V2 Verdict':>10} | {'V3 Score':>9} {'V3 Verdict':>10} | {'Delta':>8}")
    print("-" * 105)
    for r in records:
        f = r["file"]
        s2 = f"{r['score_v2']:+.2f}" if r["score_v2"] is not None else "N/A"
        v2 = r["verdict_v2"] or "N/A"
        icon2 = "✅" if v2 == "BONA_FIDE" else "❌"
        s3 = f"{r['score_v3']:+.2f}"
        v3 = r["verdict_v3"]
        icon3 = "✅" if v3 == "BONA_FIDE" else "❌"
        d = f"{r['delta_v3_vs_v2']:+.2f}" if r["delta_v3_vs_v2"] is not None else "N/A"
        print(f"{f:<22} | {s2:>9} {icon2} {v2:<9} | {s3:>9} {icon3} {v3:<9} | {d:>8}")
    print("=" * 105)
    
    n_total = len(df)
    n_v2_bona = sum(df["score_v2"] > 0)
    n_v3_bona = sum(df["score_v3"] > 0)
    mean_v2 = df["score_v2"].mean()
    mean_v3 = df["score_v3"].mean()
    
    print("\n--- TỔNG KẾT SO SÁNH SPK_0001 (15 MẪU BONAFIDE THẬT) ---")
    print(f"Số mẫu kiểm định: {n_total}")
    print(f"Version 2 (Phase 1 frozen):  {n_v2_bona}/{n_total} đúng ({n_v2_bona/n_total*100:.1f}%) | Mean Score: {mean_v2:+.2f}")
    print(f"Version 3 (Phase 2 unfreeze): {n_v3_bona}/{n_total} đúng ({n_v3_bona/n_total*100:.1f}%) | Mean Score: {mean_v3:+.2f}")
    print(f"Cải thiện điểm số trung bình: {mean_v3 - mean_v2:+.2f}")


if __name__ == "__main__":
    main()
