import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import glob
import pandas as pd
import torch
import numpy as np
from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length

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

def show_dev_metrics():
    print("=" * 80)
    print("📊 KẾT QUẢ ĐÁNH GIÁ TRÊN 11.450 MẪU DEV ZALO (CHECKPOINT B_ZALO V4)")
    print("=" * 80)
    df = pd.read_csv("out/zalo_b_zalo_v4/zalo_b_zalo_metrics.csv")
    for _, r in df.iterrows():
        codec = r["codec"]
        eer = r["eer_pct"]
        th = r["eer_threshold"]
        far = r["far_theta_0"]
        frr = r["frr_theta_0"]
        print(f"  {codec:15} | EER: {eer:5.2f}% | th_EER: {th:+6.2f} | FAR@0: {far:5.2f}% | FRR@0: {frr:5.2f}%")

def eval_spk0001():
    print("\n" + "=" * 80)
    print("🎙️ ĐÁNH GIÁ TRỰC TIẾP TRÊN 15 FILE SPK_0001 (BONAFIDE NGUYÊN BẢN)")
    print("=" * 80)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    ckpt_v4_path = "out/zalo_b_zalo_v4/best_model_B_zalo.pt"
    ckpt_v3_path = "out/zalo_b_zalo_v3/best_model_B_zalo.pt"
    
    print(f"Đang nạp Model V4 (AM-Softmax + Pitch Aug): {ckpt_v4_path}")
    model_v4, _ = load_model(ckpt_v4_path, device)
    model_v4.eval()
    
    model_v3 = None
    if Path(ckpt_v3_path).exists():
        model_v3, _ = load_model(ckpt_v3_path, device)
        model_v3.eval()
        
    m4a_dir = Path(r"C:\Users\saket\Downloads\SPK_0001")
    if not m4a_dir.exists():
        print(f"❌ Không tìm thấy thư mục {m4a_dir}")
        return
        
    files = sorted(glob.glob(str(m4a_dir / "*.wav.m4a")))
    print(f"Tìm thấy {len(files)} file M4A tại {m4a_dir}\n")
    
    rng = np.random.default_rng(0)
    rows = []
    
    print(f"{'File':<22} | {'V2 Score':>8} | {'V3 Score':>8} | {'V4 Score':>8} | {'Phán quyết V4 (θ=0)':<18}")
    print("-" * 80)
    
    with torch.no_grad():
        for f in files:
            fname = Path(f).name
            y = load_audio(f, target_sr=16000)
            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
            
            s4 = model_v4.score(tensor).item()
            s3 = model_v3.score(tensor).item() if model_v3 else float("nan")
            s2 = V2_SCORES.get(fname, float("nan"))
            
            verdict_v4 = "BONA_FIDE ✅" if s4 > 0 else "SPOOF ❌"
            print(f"{fname:<22} | {s2:+8.2f} | {s3:+8.2f} | {s4:+8.2f} | {verdict_v4:<18}")
            rows.append({"file": fname, "v2": s2, "v3": s3, "v4": s4, "verdict_v4": verdict_v4})
            
    n_bona = sum(1 for r in rows if "BONA_FIDE" in r["verdict_v4"])
    v4_scores = [r["v4"] for r in rows]
    print("-" * 80)
    print(f"🏆 TỔNG KẾT SO SÁNH SPK_0001 (15 file bonafide giọng thật):")
    print(f"  V2 (Baseline Phase 1, CE):                 3/15 BONA_FIDE (20.0%) | Mean: -4.31")
    if model_v3:
        v3_scores = [r["v3"] for r in rows]
        n_v3 = sum(1 for s in v3_scores if s > 0)
        print(f"  V3 (Phase 2, CE):                          {n_v3}/15 BONA_FIDE ({n_v3/15*100:.1f}%) | Mean: {np.mean(v3_scores):+.2f}")
    print(f"  V4 (Phase 2, AM-Softmax + Pitch Aug):     {n_bona}/15 BONA_FIDE ({n_bona/15*100:.1f}%) | Mean: {np.mean(v4_scores):+.2f} | Min: {np.min(v4_scores):+.2f} | Max: {np.max(v4_scores):+.2f}")

if __name__ == "__main__":
    show_dev_metrics()
    eval_spk0001()
