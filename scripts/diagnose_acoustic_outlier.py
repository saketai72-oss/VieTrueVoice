import glob
import librosa
import numpy as np
import soundfile as sf
from pathlib import Path

spks = ['SPK_0001', 'SPK_0004', 'SPK_0005', 'SPK_0006', 'SPK_0007']
print("=" * 85)
print(f"{'Speaker':<10} | {'F0 Mean (Hz)':<14} | {'RMS Energy':<12} | {'Spectral Centroid':<18} | {'Sample Rate':<12}")
print("=" * 85)

for spk in spks:
    files = sorted(glob.glob(f'data/raw/{spk}/*.wav'))[:5]
    f0s, rms_list, sc_list, srs = [], [], [], []
    for f in files:
        y, sr = sf.read(f)
        srs.append(sr)
        if y.ndim > 1:
            y = y.mean(axis=1)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6'), sr=sr)
        f0_clean = f0[voiced_flag & ~np.isnan(f0)]
        if len(f0_clean) > 0:
            f0s.append(np.median(f0_clean))
        rms_list.append(np.sqrt(np.mean(y**2)))
        sc_list.append(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    sr_str = f"{srs[0]} Hz" if srs else "N/A"
    print(f"{spk:<10} | {np.mean(f0s):10.1f} Hz  | {np.mean(rms_list):10.4f}   | {np.mean(sc_list):12.1f} Hz   | {sr_str:<12}")
