import gc
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import torch

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.vitruevoice.base import SynthesisRequest
from src.vitruevoice.adapters.kokoro_adapter import KokoroAdapter
from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)

KOKORO_VOICE_MAP = {
    "SPK_0003": "hung_thinh",   # Nam trung niên
    "SPK_0004": "diem_trinh",   # Nữ Bắc chuẩn
    "SPK_0005": "manh_dung",    # Nam trầm
    "SPK_0006": "mai_linh",     # Nữ trẻ
    "SPK_0007": "tuan_ngoc",    # Nam truyền cảm
}


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
    """Tạo 4 biến thể nén paired codecs cho danh sách file clean."""
    for clean_p in clean_files:
        stem = clean_p.stem
        g711_p = target_dir / f"{stem}_g711.wav"
        amr_p = target_dir / f"{stem}_amrnb.wav"
        aac_p = target_dir / f"{stem}_aac_zalo.wav"
        opus_p = target_dir / f"{stem}_opus_zalo.wav"

        # 1. G.711 A-law
        if not g711_p.exists():
            compress_g711_alaw(clean_p, g711_p)

        # 2. AMR-NB 12.2k
        if not amr_p.exists():
            compress_amr_nb(clean_p, amr_p)

        # 3. Zalo AAC-LC & Opus in-memory stream
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
    print("🚀 PIPELINE TỔNG HỢP GIỌNG GIẢ UNSEEN TTS (KOKORO-VIETNAMESE StyleTTS2)")
    print(f"Device: {device}")
    print("=" * 100)

    meta_path = Path("C:/Codes/SPK_test/data/metadata.csv")
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing {meta_path}")

    meta_df = pd.read_csv(meta_path)
    adapter = KokoroAdapter(device=device, preload=True)

    manifest_rows = []
    base_out_dir = Path("data/spoof_unseen/kokoro")
    base_out_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.perf_counter()

    for spk, voice in KOKORO_VOICE_MAP.items():
        spk_out_dir = base_out_dir / spk
        spk_out_dir.mkdir(parents=True, exist_ok=True)

        spk_meta = meta_df[(meta_df["speaker_id"] == spk) & (~meta_df["is_ref"])].reset_index(drop=True)
        print(f"\n📢 [{spk}] Voice: '{voice}' | Tổng số câu: {len(spk_meta)}")

        clean_files = []

        for idx, row in spk_meta.iterrows():
            prompt_idx = idx + 6
            file_stem = f"{spk}_kokoro_prompt_{prompt_idx:03d}"
            out_wav = spk_out_dir / f"{file_stem}.wav"
            prompt_text = str(row["transcript"]).strip()

            t0 = time.perf_counter()
            req = SynthesisRequest(
                text=prompt_text,
                speaker_id=spk,
                ref_audio=f"data/bonafide_ref/{spk}/{spk}_01.wav",
                seed=200 + prompt_idx,
                engine_preset=f"Kokoro-{voice}",
            )
            res = adapter.synthesize(req)

            # Chuẩn hóa về 16kHz mono Signed 16-bit PCM WAV (STUBBORN_FACT)
            audio_16k = res.audio
            sr = res.sample_rate
            if sr != 16000:
                import librosa
                audio_16k = librosa.resample(audio_16k, orig_sr=sr, target_sr=16000)
                sr = 16000

            sf.write(str(out_wav), audio_16k, sr, subtype="PCM_16")
            clean_files.append(out_wav)
            dur = len(audio_16k) / sr
            elapsed = time.perf_counter() - t0
            print(f"  [{idx+1:02d}/{len(spk_meta):02d}] {file_stem}.wav | {elapsed:.2f}s | {dur:.2f}s")

        # Nén paired codecs cho 15 files clean của speaker này
        print(f"  📦 Đang nén 4 codec viễn thông & Zalo cho {spk}...")
        generate_codecs_for_dir(spk_out_dir, clean_files)

        # Xây dựng manifest rows cho cả 5 biến thể (clean, g711, amrnb, aac_zalo, opus_zalo)
        for clean_p in clean_files:
            stem = clean_p.stem
            base_utt = f"{spk}_prompt_{clean_p.stem.split('_')[-1]}"
            prompt_row = spk_meta[spk_meta.index == clean_files.index(clean_p)].iloc[0]
            transcript = str(prompt_row["transcript"]).strip()

            codec_variants = [
                ("clean", "none", clean_p),
                ("g711", "clean", spk_out_dir / f"{stem}_g711.wav"),
                ("amrnb", "clean", spk_out_dir / f"{stem}_amrnb.wav"),
                ("aac_zalo_76k", "clean", spk_out_dir / f"{stem}_aac_zalo.wav"),
                ("opus_zalo_24k", "clean", spk_out_dir / f"{stem}_opus_zalo.wav"),
            ]

            for codec_name, pre_codec, pth in codec_variants:
                if pth.exists():
                    f_info = sf.info(str(pth))
                    manifest_rows.append({
                        "utt_id": pth.stem,
                        "audio_path": pth.as_posix(),
                        "speaker_id": spk,
                        "source": "volunteer_acceptance",
                        "label": "spoof",
                        "role": "eval",
                        "tts_generator": "Kokoro-Vietnamese",
                        "codec": codec_name,
                        "pre_codec": pre_codec,
                        "split": "test_unseen",
                        "duration_sec": round(f_info.duration, 3),
                        "transcript": transcript,
                        "raw_wer": 0.0,
                        "raw_cer": 0.0,
                        "ecapa_sim": 0.0,
                        "wavlm_sim": 0.0,
                        "derived_tier": "unseen_kokoro",
                        "seed": 200,
                        "base_utt": base_utt,
                        "sha256": compute_sha256(pth),
                    })

    # Lưu manifest hoàn chỉnh
    manifest_df = pd.DataFrame(manifest_rows)
    out_manifest = Path("data/manifests_zalo/unseen_kokoro_benchmark.csv")
    manifest_df.to_csv(out_manifest, index=False)

    total_time = time.perf_counter() - total_start
    print("\n" + "=" * 100)
    print(f"🎉 HOÀN THÀNH TỔNG HỢP UNSEEN KOKORO: {len(manifest_df)} tệp trong {total_time:.1f}s")
    print(f"📁 Manifest lưu tại: {out_manifest}")
    print("=" * 100)


if __name__ == "__main__":
    main()
