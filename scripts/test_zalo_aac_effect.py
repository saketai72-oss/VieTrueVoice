"""Thực nghiệm đo lường định lượng ảnh hưởng của chu trình nén Zalo (AAC-LC 76kbps @ 48kHz)
lên điểm số suy luận của Checkpoint B trên các người nói pilot (SPK_0001, SPK_0004, SPK_0005, SPK_0007).
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import glob
import subprocess
import tempfile
import numpy as np
import pandas as pd
import soundfile as sf
import torch

from scripts.eval_ssl_aasist import load_model
from src.training.dataset import fit_length


def transcode_zalo_aac(input_wav_path: str, temp_dir: str) -> str:
    """Mô phỏng chính xác chu trình Zalo: WAV -> AAC-LC 48kHz mono 76kbps M4A -> WAV 16kHz."""
    stem = Path(input_wav_path).stem
    m4a_path = os.path.join(temp_dir, f"{stem}_sim_zalo.m4a")
    out_wav_path = os.path.join(temp_dir, f"{stem}_sim_zalo_16k.wav")
    
    # Encode AAC-LC 48kHz mono @ 76k
    cmd_enc = [
        "ffmpeg", "-y", "-i", input_wav_path,
        "-ar", "48000", "-ac", "1",
        "-c:a", "aac", "-b:a", "76k",
        m4a_path
    ]
    subprocess.run(cmd_enc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Decode back to 16kHz PCM mono WAV
    cmd_dec = [
        "ffmpeg", "-y", "-i", m4a_path,
        "-ar", "16000", "-ac", "1",
        out_wav_path
    ]
    subprocess.run(cmd_dec, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    return out_wav_path


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    ckpt_path = "out/kaggle_ssl_out/best_model_B.pt"
    if not os.path.exists(ckpt_path):
        ckpt_path = "out/run_B/best_model.pt"
    print(f"Loading checkpoint: {ckpt_path}")
    model, _ = load_model(ckpt_path, device)
    model.eval()
    
    rng = np.random.default_rng(0)
    
    # Select audio files:
    # All 15 files of SPK_0001
    # 5 files each of SPK_0004, SPK_0005, SPK_0007
    files_to_test = []
    for f in sorted(glob.glob("data/raw/SPK_0001/*.wav")):
        files_to_test.append(("SPK_0001", f))
    for spk in ["SPK_0004", "SPK_0005", "SPK_0007"]:
        for f in sorted(glob.glob(f"data/raw/{spk}/*.wav"))[:5]:
            files_to_test.append((spk, f))
            
    temp_dir = tempfile.mkdtemp(prefix="zalo_sim_")
    out_dir = Path("out/diagnostics")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    records = []
    print(f"Processing {len(files_to_test)} files...")
    
    with torch.no_grad():
        for spk, raw_path in files_to_test:
            utt_id = Path(raw_path).stem
            
            # Score original raw audio
            y_orig, sr_orig = sf.read(raw_path)
            t_orig = fit_length(y_orig, 64000, train=False, rng=rng)
            tensor_orig = torch.from_numpy(t_orig).float().unsqueeze(0).to(device)
            score_orig = model.score(tensor_orig).item()
            
            # Simulate Zalo AAC transcoding
            sim_wav_path = transcode_zalo_aac(raw_path, temp_dir)
            y_sim, sr_sim = sf.read(sim_wav_path)
            t_sim = fit_length(y_sim, 64000, train=False, rng=rng)
            tensor_sim = torch.from_numpy(t_sim).float().unsqueeze(0).to(device)
            score_sim = model.score(tensor_sim).item()
            
            delta = score_sim - score_orig
            
            # For SPK_0001, also score the un-trimmed decoded original M4A from Downloads
            score_untrimmed_m4a = None
            if spk == "SPK_0001":
                dl_m4a = Path(r"C:\Users\saket\Downloads\SPK_0001") / f"{utt_id}.wav.m4a"
                if dl_m4a.exists():
                    untrimmed_wav = os.path.join(temp_dir, f"{utt_id}_untrimmed.wav")
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", str(dl_m4a), "-ar", "16000", "-ac", "1", untrimmed_wav],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                    y_untrimmed, _ = sf.read(untrimmed_wav)
                    t_untrimmed = fit_length(y_untrimmed, 64000, train=False, rng=rng)
                    tensor_untrimmed = torch.from_numpy(t_untrimmed).float().unsqueeze(0).to(device)
                    score_untrimmed_m4a = model.score(tensor_untrimmed).item()
            
            records.append({
                "speaker_id": spk,
                "utt_id": utt_id,
                "score_orig": score_orig,
                "score_sim_aac": score_sim,
                "delta": delta,
                "score_untrimmed_m4a": score_untrimmed_m4a,
            })
            
            print(f"[{spk}] {utt_id}: orig={score_orig:+.2f} -> aac={score_sim:+.2f} (delta={delta:+.2f})"
                  + (f" [untrimmed_m4a={score_untrimmed_m4a:+.2f}]" if score_untrimmed_m4a is not None else ""))
            
    df = pd.DataFrame(records)
    csv_out = out_dir / "zalo_aac_experiment_results.csv"
    df.to_csv(csv_out, index=False)
    print(f"\nSaved results to {csv_out}")
    
    # Summary by speaker
    summary = df.groupby("speaker_id").agg({
        "score_orig": ["mean", "min", "max"],
        "score_sim_aac": ["mean", "min", "max"],
        "delta": ["mean", "std", "min", "max"]
    })
    print("\nSummary by speaker:")
    print(summary.round(2).to_string())
    
    # Clean up temp dir
    for f in glob.glob(os.path.join(temp_dir, "*")):
        try: os.remove(f)
        except OSError: pass
    try: os.rmdir(temp_dir)
    except OSError: pass


if __name__ == "__main__":
    main()
