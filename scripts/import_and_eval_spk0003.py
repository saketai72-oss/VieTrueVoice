import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import librosa
import numpy as np
import soundfile as sf
import torch

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def band_energy_ratio(y: np.ndarray, sr: int, low_hz: float, high_hz: float) -> float:
    fft = np.abs(np.fft.rfft(y)) ** 2
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    total_e = float(np.sum(fft))
    if total_e <= 1e-12:
        return 0.0
    band_mask = (freqs >= low_hz) & (freqs < high_hz)
    return float(np.sum(fft[band_mask])) / total_e


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 100)
    print("🎙️ NHẬP VÀ CHUẨN HÓA DỮ LIỆU TÌNH NGUYỆN VIÊN: SPK_0003 (20 TỆP ĐỘC BẢN)")
    print("=" * 100)

    src_dir = Path("C:/Users/saket/Downloads/SPK_0003")
    raw_dst_dir = Path("data/raw/SPK_0003")
    ref_dst_dir = Path("data/bonafide_ref/SPK_0003")
    raw_dst_dir.mkdir(parents=True, exist_ok=True)
    ref_dst_dir.mkdir(parents=True, exist_ok=True)

    # Dọn dẹp các tệp cũ trong raw và ref SPK_0003
    for f in raw_dst_dir.glob("*.wav"):
        f.unlink()
    for f in ref_dst_dir.glob("*.wav"):
        f.unlink()

    src_files = sorted(list(src_dir.glob("SPK_0003_*.wav.mp3")))
    if not src_files:
        src_files = sorted(list(src_dir.glob("*.mp3")))

    print(f"Tìm thấy chính xác {len(src_files)} tệp nguồn tại {src_dir}")

    ckpt_v5_path = "out/zalo_b_zalo_v5_local/best_model.pt"
    ckpt_base_path = "out/kaggle_ssl_out/best_model_B.pt"

    model_v5, _ = load_model(ckpt_v5_path, device)
    model_v5.eval()

    model_base = None
    if Path(ckpt_base_path).exists():
        model_base, _ = load_model(ckpt_base_path, device)
        model_base.eval()

    rng = np.random.default_rng(0)
    header = f"{'File':<16} | {'Dur(s)':<6} | {'F0 (Hz)':<8} | {'SC (Hz)':<8} | {'e_low%':<7} | {'e_mid%':<7} | {'Peak':<6} | {'Base B':>8} | {'V5 Local':>8} | {'Phán quyết V5':<14}"
    print(header)
    print("-" * len(header))

    v5_scores = []
    base_scores = []
    f0_list = []
    e_low_list = []
    e_mid_list = []

    for i, src_f in enumerate(src_files, start=1):
        idx_str = f"{i:02d}"
        stem = f"SPK_0003_{idx_str}"
        dst_wav = raw_dst_dir / f"{stem}.wav"

        # Đọc in-memory qua load_audio và chuẩn hóa 16kHz mono
        y = load_audio(src_f, target_sr=16000)

        # Lưu bản chuẩn hóa 16kHz mono Signed 16-bit PCM WAV
        sf.write(str(dst_wav), y, 16000, subtype="PCM_16")

        # Lưu 5 clip đầu vào bonafide_ref
        if i <= 5:
            ref_wav = ref_dst_dir / f"{stem}.wav"
            sf.write(str(ref_wav), y, 16000, subtype="PCM_16")

        dur = len(y) / 16000.0

        # Phân tích âm học
        f0, voiced_flag, _ = librosa.pyin(y, fmin=50, fmax=400, sr=16000)
        f0_clean = f0[voiced_flag & ~np.isnan(f0)]
        f0_val = float(np.median(f0_clean)) if len(f0_clean) > 0 else float("nan")
        sc_val = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=16000)))
        e_low = band_energy_ratio(y, 16000, 0, 300) * 100.0
        e_mid = band_energy_ratio(y, 16000, 300, 3400) * 100.0
        peak = float(np.max(np.abs(y)))

        # Suy luận mô hình V5 & Base
        t = fit_length(y, 64000, train=False, rng=rng)
        tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)

        with torch.no_grad():
            s5 = model_v5.score(tensor).item()
            sb = model_base.score(tensor).item() if model_base else float("nan")

        verdict_v5 = "BONA FIDE ✅" if s5 > 0 else "SPOOF ❌"

        print(f"{dst_wav.name:<16} | {dur:6.2f} | {f0_val:6.1f} Hz | {sc_val:6.0f} Hz | {e_low:6.1f}% | {e_mid:6.1f}% | {peak:6.3f} | {sb:+8.2f} | {s5:+8.2f} | {verdict_v5:<14}")

        v5_scores.append(s5)
        base_scores.append(sb)
        if not np.isnan(f0_val):
            f0_list.append(f0_val)
        e_low_list.append(e_low)
        e_mid_list.append(e_mid)

    v5_arr = np.array(v5_scores)
    pass_cnt = np.sum(v5_arr > 0)
    total_cnt = len(v5_arr)

    print("\n" + "=" * 100)
    print("📊 TỔNG HỢP PROFILE ÂM HỌC VÀ HIỆU NĂNG NHẬN DIỆN SPK_0003 TRÊN V5 LOCAL:")
    print("=" * 100)
    print(f"Tổng số tệp nhập thành công: {total_cnt}/20")
    print(f"F0 trung bình (voiced): {np.mean(f0_list):.1f} Hz (Median: {np.median(f0_list):.1f} Hz, Min: {np.min(f0_list):.1f} Hz, Max: {np.max(f0_list):.1f} Hz)")
    print(f"Tỷ lệ năng lượng dải trầm (0-300Hz, e_low): {np.mean(e_low_list):.1f}%")
    print(f"Tỷ lệ năng lượng dải thoại (300-3400Hz, e_mid): {np.mean(e_mid_list):.1f}%")
    print(f"Điểm mô hình V5 Local: Mean = {np.mean(v5_arr):+.2f}, Median = {np.median(v5_arr):+.2f}, Min = {np.min(v5_arr):+.2f}, Max = {np.max(v5_arr):+.2f}")
    print(f"Tỷ lệ Bona Fide PASS tại θ = 0: {pass_cnt}/{total_cnt} ({pass_cnt/total_cnt*100:.1f}%)")
    print("=" * 100)


if __name__ == "__main__":
    main()
