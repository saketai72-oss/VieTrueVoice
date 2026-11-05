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


SPEAKER_REFS = {
    "SPK_0004": {
        "audio": "data/bonafide_ref/SPK_0004/SPK_0004_01.wav",
        "text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."
    },
    "SPK_0005": {
        "audio": "data/bonafide_ref/SPK_0005/SPK_0005_01.wav",
        "text": "Công dân có quyền yêu cầu bảo vệ thông tin dữ liệu cá nhân theo luật định."
    },
    "SPK_0006": {
        "audio": "data/bonafide_ref/SPK_0006/SPK_0006_01.wav",
        "text": "Dịp Tết Nguyên đán năm nay cả đại gia đình mình sẽ về quê sum họp."
    },
    "SPK_0007": {
        "audio": "data/bonafide_ref/SPK_0007/SPK_0007_01.wav",
        "text": "Tập thể lớp chúng ta đã hoàn thành xuất sắc kế hoạch học tập học kỳ một."
    },
}


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
    for clean_p in clean_files:
        stem = clean_p.stem
        g711_p = target_dir / f"{stem}_g711.wav"
        amr_p = target_dir / f"{stem}_amrnb.wav"
        aac_p = target_dir / f"{stem}_aac_zalo.wav"
        opus_p = target_dir / f"{stem}_opus_zalo.wav"

        if not g711_p.exists():
            compress_g711_alaw(clean_p, g711_p)
        if not amr_p.exists():
            compress_amr_nb(clean_p, amr_p)

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
    print("🚀 PIPELINE ĐỒNG BỘ GIỌNG GIẢ KÉP CHUẨN (F5-TTS & VIENEU-TTS) CHO CẢ 4 TÌNH NGUYỆN VIÊN")
    print(f"Device: {device}")
    print("=" * 100)

    meta_path = Path("C:/Codes/SPK_test/data/metadata.csv")
    meta_df = pd.read_csv(meta_path)

    # 1. Dọn dẹp thư mục spoof cũ của 4 speakers
    for spk in SPEAKER_REFS.keys():
        for d in [Path(f"data/spoof_f5tts/{spk}"), Path(f"data/spoof_vieneu/{spk}")]:
            if d.exists():
                for f in d.glob("*.wav"):
                    f.unlink()

    # 2. Sinh F5-TTS tuần tự
    print("\n" + "=" * 80)
    print("🎙️ GIAI ĐOẠN 1: SINH F5-TTS-VIETNAMESE VỚI REF_TEXT CHUẨN")
    print("=" * 80)
    f5_adapter = F5TTSAdapter(device=device)

    all_clean_f5 = {}
    for spk, ref_info in SPEAKER_REFS.items():
        ref_audio = ref_info["audio"]
        ref_text = ref_info["text"]
        out_dir = Path(f"data/spoof_f5tts/{spk}")
        out_dir.mkdir(parents=True, exist_ok=True)

        spk_meta = meta_df[(meta_df["speaker_id"] == spk) & (~meta_df["is_ref"])].reset_index(drop=True)
        print(f"\n--- Sinh F5-TTS cho {spk} ({len(spk_meta)} câu) ---")
        clean_files = []

        for idx, row in spk_meta.iterrows():
            prompt_idx = idx + 6
            file_stem = f"{spk}_prompt_{prompt_idx:03d}"
            out_wav = out_dir / f"{file_stem}.wav"
            prompt_text = str(row["transcript"]).strip()

            t0 = time.perf_counter()
            req = SynthesisRequest(
                text=prompt_text,
                speaker_id=spk,
                ref_audio=ref_audio,
                seed=100 + prompt_idx,
                extra_params={"ref_text": ref_text, "nfe_step": 32}
            )
            res = f5_adapter.synthesize(req)
            audio_16k = res.audio
            sr = res.sample_rate
            if sr != 16000:
                import librosa
                audio_16k = librosa.resample(audio_16k, orig_sr=sr, target_sr=16000)
                sr = 16000

            sf.write(str(out_wav), audio_16k, sr, subtype="PCM_16")
            clean_files.append(out_wav)
            print(f"  [{idx+1:02d}/{len(spk_meta):02d}] {file_stem}.wav | {time.perf_counter()-t0:.2f}s | {len(audio_16k)/sr:.2f}s")

        all_clean_f5[spk] = clean_files
        generate_codecs_for_dir(out_dir, clean_files)

    del f5_adapter
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 3. Sinh VieNeu-TTS tuần tự
    print("\n" + "=" * 80)
    print("🎙️ GIAI ĐOẠN 2: SINH VIENEU-TTS V3 TURBO (UNSEEN TTS)")
    print("=" * 80)
    vn_adapter = VieNeuAdapter(mode="v3turbo")

    all_clean_vn = {}
    for spk, ref_info in SPEAKER_REFS.items():
        ref_audio = ref_info["audio"]
        out_dir = Path(f"data/spoof_vieneu/{spk}")
        out_dir.mkdir(parents=True, exist_ok=True)

        spk_meta = meta_df[(meta_df["speaker_id"] == spk) & (~meta_df["is_ref"])].reset_index(drop=True)
        print(f"\n--- Sinh VieNeu-TTS cho {spk} ({len(spk_meta)} câu) ---")
        clean_files = []

        for idx, row in spk_meta.iterrows():
            prompt_idx = idx + 6
            file_stem = f"{spk}_prompt_{prompt_idx:03d}"
            out_wav = out_dir / f"{file_stem}.wav"
            prompt_text = str(row["transcript"]).strip()

            t0 = time.perf_counter()
            req = SynthesisRequest(
                text=prompt_text,
                speaker_id=spk,
                ref_audio=ref_audio,
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
            clean_files.append(out_wav)
            print(f"  [{idx+1:02d}/{len(spk_meta):02d}] {file_stem}.wav | {time.perf_counter()-t0:.2f}s | {len(audio_16k)/sr:.2f}s")

        all_clean_vn[spk] = clean_files
        generate_codecs_for_dir(out_dir, clean_files)

    del vn_adapter
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # 4. Tạo codecs cho các file raw bona fide còn thiếu của SPK_0004..0007
    print("\n" + "=" * 80)
    print("📦 GIAI ĐOẠN 3: NÉN CODEC CHO BONA FIDE CỦA CẢ 4 TÌNH NGUYỆN VIÊN")
    print("=" * 80)
    for spk in SPEAKER_REFS.keys():
        r_dir = Path(f"data/raw/{spk}")
        c_files = [f for f in sorted(r_dir.glob("*.wav")) if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
        generate_codecs_for_dir(r_dir, c_files)

    print("\n" + "=" * 100)
    print("🎉 HOÀN TẤT SINH GIỌNG GIẢ KÉP CHUẨN CHO TOÀN BỘ 5 TÌNH NGUYỆN VIÊN!")
    print("=" * 100)


if __name__ == "__main__":
    main()
