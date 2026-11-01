import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import glob
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 90)
    print("🎙️ KIỂM ĐỊNH BẢN THU MỚI: C:\\Users\\saket\\Downloads\\VoiCes")
    print("=" * 90)
    
    ckpt_v4_path = "out/zalo_b_zalo_v4/best_model_B_zalo.pt"
    ckpt_v3_path = "out/zalo_b_zalo_v3/best_model_B_zalo.pt"
    ckpt_base_path = "out/kaggle_ssl_out/best_model_B.pt"
    
    print(f"Loading Model V4 (AM-Softmax): {ckpt_v4_path}")
    model_v4, _ = load_model(ckpt_v4_path, device)
    model_v4.eval()
    
    model_v3 = None
    if Path(ckpt_v3_path).exists():
        print(f"Loading Model V3 (Phase 2 CE): {ckpt_v3_path}")
        model_v3, _ = load_model(ckpt_v3_path, device)
        model_v3.eval()
        
    model_base = None
    if Path(ckpt_base_path).exists():
        print(f"Loading Model Baseline B gốc: {ckpt_base_path}")
        model_base, _ = load_model(ckpt_base_path, device)
        model_base.eval()
        
    input_dir = Path(r"C:\Users\saket\Downloads\VoiCes")
    files = sorted(list(input_dir.glob("*.m4a")) + list(input_dir.glob("*.wav")))
    print(f"\nTìm thấy {len(files)} tệp âm thanh tại {input_dir}\n")
    
    rng = np.random.default_rng(0)
    results = []
    
    header = f"{'File':<24} | {'F0 (Hz)':<8} | {'SC (Hz)':<8} | {'Base B':>8} | {'V3 (CE)':>8} | {'V4 (AM)':>8} | {'Phán quyết V4 (θ=0)':<18}"
    print(header)
    print("-" * len(header))
    
    with torch.no_grad():
        for f in files:
            y = load_audio(f, target_sr=16000)
            
            # Tính đặc trưng âm học
            f0, voiced_flag, _ = librosa.pyin(y, fmin=50, fmax=400, sr=16000)
            f0_clean = f0[voiced_flag & ~np.isnan(f0)]
            f0_val = np.median(f0_clean) if len(f0_clean) > 0 else float("nan")
            sc_val = np.mean(librosa.feature.spectral_centroid(y=y, sr=16000))
            
            t = fit_length(y, 64000, train=False, rng=rng)
            tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
            
            s4 = model_v4.score(tensor).item()
            s3 = model_v3.score(tensor).item() if model_v3 else float("nan")
            sb = model_base.score(tensor).item() if model_base else float("nan")
            
            verdict_v4 = "BONA_FIDE ✅" if s4 > 0 else "SPOOF ❌"
            
            print(f"{f.name:<24} | {f0_val:6.1f} Hz | {sc_val:6.0f} Hz | {sb:+8.2f} | {s3:+8.2f} | {s4:+8.2f} | {verdict_v4:<18}")
            results.append({
                "file": f.name,
                "f0": f0_val,
                "sc": sc_val,
                "score_base": sb,
                "score_v3": s3,
                "score_v4": s4,
                "verdict_v4": verdict_v4,
            })
            
    df_res = pd.DataFrame(results)
    n_total = len(df_res)
    n_bona_v4 = sum(1 for v in df_res["verdict_v4"] if "BONA_FIDE" in v)
    n_bona_v3 = sum(1 for s in df_res["score_v3"] if s > 0)
    n_bona_b = sum(1 for s in df_res["score_base"] if s > 0)
    
    print("-" * len(header))
    print(f"🏆 TỔNG KẾT ĐÁNH GIÁ TRÊN BỘ THU MỚI ({n_total} files):")
    print(f"  Checkpoint Baseline B gốc:        {n_bona_b:2d}/{n_total} BONA_FIDE ({n_bona_b/n_total*100:5.1f}%) | Mean Score: {df_res['score_base'].mean():+6.2f}")
    print(f"  Checkpoint B_zalo V3 (Phase 2 CE): {n_bona_v3:2d}/{n_total} BONA_FIDE ({n_bona_v3/n_total*100:5.1f}%) | Mean Score: {df_res['score_v3'].mean():+6.2f}")
    print(f"  Checkpoint B_zalo V4 (AM-Softmax): {n_bona_v4:2d}/{n_total} BONA_FIDE ({n_bona_v4/n_total*100:5.1f}%) | Mean Score: {df_res['score_v4'].mean():+6.2f}")
    print(f"  Thang điểm V4: Min = {df_res['score_v4'].min():+6.2f} | Max = {df_res['score_v4'].max():+6.2f}")


if __name__ == "__main__":
    main()
