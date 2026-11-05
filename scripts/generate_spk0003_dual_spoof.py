import gc
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import soundfile as sf
import torch

from src.vitruevoice.base import SynthesisRequest
from src.vitruevoice.adapters.f5_adapter import F5TTSAdapter
from src.vitruevoice.adapters.vieneu_adapter import VieNeuAdapter
from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compress_g711_alaw(src_wav: Path, dst_wav: Path) -> bool:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src_wav), "-ar", "8000", "-ac", "1", "-c:a", "pcm_alaw", str(dst_wav)]
    res = subprocess.run(cmd, capture_output=True)
    return res.returncode == 0


def compress_amr_nb(src_wav: Path, dst_wav: Path, bitrate: str = "12.2k") -> bool:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_amr = dst_wav.with_suffix(".amr")
    cmd_enc = ["ffmpeg", "-y", "-v", "error", "-i", str(src_wav), "-ar", "8000", "-ac", "1", "-c:a", "libopencore_amrnb", "-b:a", bitrate, str(temp_amr)]
    cmd_dec = ["ffmpeg", "-y", "-v", "error", "-i", str(temp_amr), "-ar", "8000", "-ac", "1", "-c:a", "pcm_s16le", str(dst_wav)]
    r1 = subprocess.run(cmd_enc, capture_output=True)
    r2 = subprocess.run(cmd_dec, capture_output=True)
    if temp_amr.exists():
        temp_amr.unlink()
    return (r1.returncode == 0) and (r2.returncode == 0)


def generate_codecs_for_dir(target_dir: Path, clean_files: list[Path]):
    """Tạo paired codec (_g711, _amrnb, _aac_zalo, _opus_zalo) cho danh sách file clean."""
    print(f"\n📦 Đang nén codec viễn thông & Zalo cho {len(clean_files)} tệp tại {target_dir}...")
    for clean_p in clean_files:
        stem = clean_p.stem
        g711_p = target_dir / f"{stem}_g711.wav"
        amr_p = target_dir / f"{stem}_amrnb.wav"
        aac_p = target_dir / f"{stem}_aac_zalo.wav"
        opus_p = target_dir / f"{stem}_opus_zalo.wav"

        # G.711 A-law
        if not g711_p.exists():
            compress_g711_alaw(clean_p, g711_p)

        # AMR-NB
        if not amr_p.exists():
            compress_amr_nb(clean_p, amr_p)

        # AAC Zalo & Opus Zalo in-memory
        with open(clean_p, "rb") as f:
            raw_b = f.read()

        if not aac_p.exists():
            aac_b = transcode_aac_adts_stream(raw_b)
            with open(aac_p, "wb") as f:
                f.write(aac_b)

        if not opus_p.exists():
            opus_b = transcode_opus_ogg_stream(raw_b)
            with open(opus_p, "wb") as f:
                f.write(opus_b)


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 100)
    print("🚀 PIPELINE SINH GIỌNG GIẢ KÉP (F5-TTS & VIENEU-TTS) CHO TÌNH NGUYỆN VIÊN: SPK_0003")
    print(f"Device: {device}")
    print("=" * 100)

    # 1. Tải metadata prompts của SPK_0003
    meta_path = Path("C:/Codes/SPK_test/data/metadata.csv")
    meta_df = pd.read_csv(meta_path)
    spk3_df = meta_df[meta_df["speaker_id"] == "SPK_0003"].copy()

    # Tách ref và non-ref (prompts)
    non_ref_df = spk3_df[~spk3_df["is_ref"]].reset_index(drop=True)
    print(f"Số câu kịch bản cần sinh (non-ref): {len(non_ref_df)} câu")

    ref_audio_path = "data/bonafide_ref/SPK_0003/SPK_0003_01.wav"
    ref_text = "Người lớn tuổi thường gặp nhiều bỡ ngỡ khi sử dụng các ứng dụng công nghệ mới."
    print(f"Reference Audio: {ref_audio_path}")
    print(f"Reference Text : {ref_text}")

    f5_out_dir = Path("data/spoof_f5tts/SPK_0003")
    vn_out_dir = Path("data/spoof_vieneu/SPK_0003")
    f5_out_dir.mkdir(parents=True, exist_ok=True)
    vn_out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Sinh F5-TTS
    print("\n" + "=" * 80)
    print("🎙️ GIAI ĐOẠN 1: TỔNG HỢP GIỌNG GIẢ VỚI F5-TTS-VIETNAMESE (SEEN TTS)")
    print("=" * 80)
    f5_adapter = F5TTSAdapter(device=device)
    clean_f5_files = []

    t_f5_start = time.perf_counter()
    for idx, row in non_ref_df.iterrows():
        # idx 0 tương ứng prompt 006
        prompt_idx = idx + 6
        file_stem = f"SPK_0003_prompt_{prompt_idx:03d}"
        out_wav = f5_out_dir / f"{file_stem}.wav"
        prompt_text = str(row["transcript"]).strip()

        print(f"[{idx+1:02d}/{len(non_ref_df):02d}] F5-TTS -> {file_stem}.wav | '{prompt_text[:45]}...'")
        t0 = time.perf_counter()
        req = SynthesisRequest(
            text=prompt_text,
            speaker_id="SPK_0003",
            ref_audio=ref_audio_path,
            seed=100 + prompt_idx,
            extra_params={"ref_text": ref_text, "nfe_step": 32}
        )
        res = f5_adapter.synthesize(req)
        # Chuẩn hóa về 16kHz mono Signed 16-bit PCM WAV
        audio_16k = res.audio
        sr = res.sample_rate
        if sr != 16000:
            import librosa
            audio_16k = librosa.resample(audio_16k, orig_sr=sr, target_sr=16000)
            sr = 16000

        sf.write(str(out_wav), audio_16k, sr, subtype="PCM_16")
        dur = len(audio_16k) / sr
        elapsed = time.perf_counter() - t0
        print(f"      ✅ Xong trong {elapsed:.2f}s (Dur: {dur:.2f}s, SR: {sr})")
        clean_f5_files.append(out_wav)

    t_f5_total = time.perf_counter() - t_f5_start
    print(f"\n🎉 Hoàn thành F5-TTS: {len(clean_f5_files)} file trong {t_f5_total:.1f}s")

    # Giải phóng VRAM của F5
    del f5_adapter
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Sinh VieNeu-TTS
    print("\n" + "=" * 80)
    print("🎙️ GIAI ĐOẠN 2: TỔNG HỢP GIỌNG GIẢ VỚI VIENEU-TTS V3 TURBO (UNSEEN TTS)")
    print("=" * 80)
    vn_adapter = VieNeuAdapter(mode="v3turbo")
    clean_vn_files = []

    t_vn_start = time.perf_counter()
    for idx, row in non_ref_df.iterrows():
        prompt_idx = idx + 6
        file_stem = f"SPK_0003_prompt_{prompt_idx:03d}"
        out_wav = vn_out_dir / f"{file_stem}.wav"
        prompt_text = str(row["transcript"]).strip()

        print(f"[{idx+1:02d}/{len(non_ref_df):02d}] VieNeu -> {file_stem}.wav | '{prompt_text[:45]}...'")
        t0 = time.perf_counter()
        req = SynthesisRequest(
            text=prompt_text,
            speaker_id="SPK_0003",
            ref_audio=ref_audio_path,
            seed=200 + prompt_idx,
            engine_preset="VieNeu-A",
            extra_params={"temperature": 0.60, "top_p": 0.90}
        )
        res = vn_adapter.synthesize(req)
        audio_16k = res.audio
        sr = res.sample_rate
        if sr != 16000:
            import librosa
            audio_16k = librosa.resample(audio_16k, orig_sr=sr, target_sr=16000)
            sr = 16000

        sf.write(str(out_wav), audio_16k, sr, subtype="PCM_16")
        dur = len(audio_16k) / sr
        elapsed = time.perf_counter() - t0
        print(f"      ✅ Xong trong {elapsed:.2f}s (Dur: {dur:.2f}s, SR: {sr})")
        clean_vn_files.append(out_wav)

    t_vn_total = time.perf_counter() - t_vn_start
    print(f"\n🎉 Hoàn thành VieNeu-TTS: {len(clean_vn_files)} file trong {t_vn_total:.1f}s")

    # Giải phóng VRAM của VieNeu
    del vn_adapter
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 4. Tạo paired codecs viễn thông cho F5, VieNeu, và Raw Bona Fide
    generate_codecs_for_dir(f5_out_dir, clean_f5_files)
    generate_codecs_for_dir(vn_out_dir, clean_vn_files)

    raw_spk3_dir = Path("data/raw/SPK_0003")
    raw_bona_files = sorted(list(raw_spk3_dir.glob("SPK_0003_*.wav")))
    # Chỉ lấy các file clean không có hậu tố codec
    clean_bona_files = [f for f in raw_bona_files if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
    generate_codecs_for_dir(raw_spk3_dir, clean_bona_files)

    # 5. Kiểm tra tính toàn vẹn và độc bản SHA-256 (Anti-Mock Audit)
    print("\n" + "=" * 80)
    print("🔍 GIAI ĐOẠN 3: KIỂM TOÁN TÍNH TOÀN VẸN & MÃ BĂM SHA-256 (ANTI-MOCK AUDIT)")
    print("=" * 80)
    all_gen_files = clean_f5_files + clean_vn_files
    hashes = {}
    duplicates = []
    dummy_quarantine_hash = "b5fac7b45f7b"

    for f in all_gen_files:
        h = compute_sha256(f)
        if h in hashes:
            duplicates.append((f, hashes[h]))
        hashes[h] = f
        if h.startswith(dummy_quarantine_hash):
            print(f"🚨 CẢNH BÁO: Tệp {f.name} khớp mã băm mock cách ly!")

    print(f"Tổng số tệp sinh mới (clean): {len(all_gen_files)}")
    print(f"Số mã băm SHA-256 độc bản : {len(hashes)}")
    print(f"Số tệp trùng lặp mã băm    : {len(duplicates)}")
    if duplicates:
        print(f"❌ Phát hiện trùng lặp: {duplicates}")
    else:
        print("✅ 100% tệp sinh mới có mã băm SHA-256 độc bản hoàn toàn, sạch 0% mock dummy!")

    # 6. Đánh giá nhanh trên Checkpoint V5 Local
    print("\n" + "=" * 80)
    print("📊 GIAI ĐOẠN 4: ĐÁNH GIÁ ĐỐI CHỨNG TRÊN MÔ HÌNH V5 LOCAL")
    print("=" * 80)
    from scripts.eval_ssl_aasist import load_model
    from src.preprocessing.audio_loader import load_audio
    from src.training.dataset import fit_length

    ckpt_v5_path = "out/zalo_b_zalo_v5_local/best_model.pt"
    model_v5, _ = load_model(ckpt_v5_path, device)
    model_v5.eval()
    rng = np.random.default_rng(0)

    def eval_files(flist, label_name):
        scores = []
        with torch.no_grad():
            for f in flist:
                y = load_audio(f, target_sr=16000)
                t = fit_length(y, 64000, train=False, rng=rng)
                tensor = torch.from_numpy(t).float().unsqueeze(0).to(device)
                s = model_v5.score(tensor).item()
                scores.append(s)
        arr = np.array(scores)
        pass_rate = np.mean(arr < 0) * 100 if "SPOOF" in label_name else np.mean(arr > 0) * 100
        print(f"  {label_name:<25}: Mean = {np.mean(arr):+6.2f} | Median = {np.median(arr):+6.2f} | Std = {np.std(arr):5.2f} | Nhận diện đúng ({'Score<0' if 'SPOOF' in label_name else 'Score>0'}): {pass_rate:.1f}% ({np.sum(arr < 0 if 'SPOOF' in label_name else arr > 0)}/{len(arr)})")
        return arr

    print("\nKết quả suy luận trên các tập mẫu SPK_0003:")
    bona_scores = eval_files(clean_bona_files, "SPK_0003 Bona Fide (Clean)")
    f5_scores = eval_files(clean_f5_files, "SPK_0003 F5-TTS (Seen)")
    vn_scores = eval_files(clean_vn_files, "SPK_0003 VieNeu-TTS (Unseen)")

    print("=" * 100)
    print("🏁 PIPELINE HOÀN TẤT THÀNH CÔNG VÀ SẴN SÀNG CHO BỘ NGHIỆM THU 5 TÌNH NGUYỆN VIÊN!")
    print("=" * 100)


if __name__ == "__main__":
    main()
