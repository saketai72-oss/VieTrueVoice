"""Sinh mẫu âm thanh giả mạo Unseen TTS bằng OmniVoice (VoiceStudio Core Engine).

Quy trình:
1. Nạp mô hình k2-fsa/OmniVoice trên CUDA (bfloat16).
2. Lấy 5 tình nguyện viên đối chứng: SPK_0003..SPK_0007.
3. Dùng clip ref (SPK_XXXX_01.wav) và transcript gốc làm mẫu giọng tham chiếu.
4. Sinh 15 câu non-ref độc bản (Hard Text-Disjoint).
5. Nén 4 codec: G.711, AMR-NB, AAC-LC 76k, Opus 24k.
6. Xuất manifest 18 cột: data/manifests_zalo/unseen_omnivoice_benchmark.csv.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "external" / "VoiceStudio"))

from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.audio import save_audio
import subprocess
from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)


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

REF_METADATA = {
    "SPK_0003": {
        "ref_audio": "data/bonafide_ref/SPK_0003/SPK_0003_01.wav",
        "ref_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.",
    },
    "SPK_0004": {
        "ref_audio": "data/bonafide_ref/SPK_0004/SPK_0004_01.wav",
        "ref_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.",
    },
    "SPK_0005": {
        "ref_audio": "data/bonafide_ref/SPK_0005/SPK_0005_01.wav",
        "ref_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.",
    },
    "SPK_0006": {
        "ref_audio": "data/bonafide_ref/SPK_0006/SPK_0006_01.wav",
        "ref_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.",
    },
    "SPK_0007": {
        "ref_audio": "data/bonafide_ref/SPK_0007/SPK_0007_01.wav",
        "ref_text": "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ.",
    },
}


def compute_sha256(filepath: str | Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_omnivoice_dataset(
    speakers: list[str] | None = None,
    num_prompts_per_spk: int = 15,
    out_dir: str = "data/spoof_unseen/omnivoice",
    manifest_out: str = "data/manifests_zalo/unseen_omnivoice_benchmark.csv",
):
    speakers = speakers or ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 90)
    print("🚀 PIPELINE TỔNG HỢP GIỌNG GIẢ UNSEEN TTS (OMNIVOICE / VOICESTUDIO)")
    print(f"Device: {device} | Speakers: {speakers} | Prompts/spk: {num_prompts_per_spk}")
    print("=" * 90)

    # Nạp mô hình OmniVoice
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    )

    # Nạp danh sách câu từ metadata
    meta_df = pd.read_csv("C:/Codes/SPK_test/data/metadata.csv")

    out_base = _ROOT / out_dir
    manifest_rows = []

    start_all = time.perf_counter()

    for spk in speakers:
        spk_prompts = meta_df[(meta_df["speaker_id"] == spk) & (~meta_df["is_ref"])].copy()
        spk_prompts = spk_prompts.head(num_prompts_per_spk)

        spk_out = out_base / spk
        spk_out.mkdir(parents=True, exist_ok=True)

        ref_info = REF_METADATA.get(spk)
        if not ref_info:
            print(f"⚠️ Thiếu thông tin ref cho {spk}, bỏ qua.")
            continue

        ref_audio_path = str(_ROOT / ref_info["ref_audio"])
        ref_text = ref_info["ref_text"]

        print(f"\n📢 [{spk}] Zero-Shot Voice Cloning từ: {ref_info['ref_audio']} | {len(spk_prompts)} câu")

        for idx, (_, row) in enumerate(spk_prompts.iterrows(), start=1):
            fname = row["filename"]  # e.g. SPK_0004_06.wav
            prompt_idx = fname.replace(f"{spk}_", "").replace(".wav", "")
            base_utt = f"{spk}_prompt_{int(prompt_idx):03d}"
            utt_id = f"{spk}_omnivoice_prompt_{int(prompt_idx):03d}"
            text = row["transcript"]

            clean_wav_path = spk_out / f"{utt_id}.wav"

            # Check if clean already generated
            if not clean_wav_path.exists():
                t0 = time.perf_counter()
                try:
                    audios = model.generate(
                        text=text,
                        ref_audio=ref_audio_path,
                        ref_text=ref_text,
                        language="vi",
                        num_step=16,
                        guidance_scale=2.0,
                    )
                    lat = time.perf_counter() - t0
                    # Save at 24kHz
                    tmp_24k = spk_out / f"{utt_id}_24k.wav"
                    save_audio(str(tmp_24k), audios[0], sample_rate=24000)

                    # Resample to 16kHz mono PCM for standard pipeline
                    import librosa
                    y_24k, _ = sf.read(tmp_24k)
                    y_16k = librosa.resample(y_24k, orig_sr=24000, target_sr=16000)
                    sf.write(clean_wav_path, y_16k, 16000, subtype="PCM_16")
                    tmp_24k.unlink(missing_ok=True)
                    dur = len(y_16k) / 16000.0
                    print(f"  [{idx:02d}/{len(spk_prompts):02d}] {clean_wav_path.name} | Latency: {lat:.2f}s | Dur: {dur:.2f}s")
                except Exception as e:
                    print(f"  ❌ Lỗi sinh {clean_wav_path.name}: {e}")
                    continue
            else:
                data, sr = sf.read(clean_wav_path)
                dur = len(data) / sr

            # Manifest row cho Clean
            manifest_rows.append({
                "utt_id": utt_id,
                "audio_path": clean_wav_path.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "volunteer_acceptance",
                "label": "spoof",
                "role": "eval",
                "tts_generator": "OmniVoice",
                "codec": "clean",
                "pre_codec": "none",
                "split": "test_unseen",
                "duration_sec": round(dur, 3),
                "transcript": text,
                "raw_wer": 0.0,
                "raw_cer": 0.0,
                "ecapa_sim": 0.0,
                "wavlm_sim": 0.0,
                "derived_tier": "unseen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
                "sha256": compute_sha256(clean_wav_path),
            })

            # Nén 4 codecs
            g711_p = spk_out / f"{utt_id}_g711.wav"
            amr_p = spk_out / f"{utt_id}_amrnb.wav"
            aac_p = spk_out / f"{utt_id}_aac_zalo.wav"
            opus_p = spk_out / f"{utt_id}_opus_zalo.wav"

            if not g711_p.exists():
                compress_g711_alaw(clean_wav_path, g711_p)
            if not amr_p.exists():
                compress_amr_nb(clean_wav_path, amr_p)

            with open(clean_wav_path, "rb") as f:
                raw_b = f.read()

            if not aac_p.exists():
                aac_b = transcode_aac_adts_stream(raw_b)
                with open(aac_p, "wb") as f:
                    f.write(aac_b)

            if not opus_p.exists():
                opus_b = transcode_opus_ogg_stream(raw_b)
                with open(opus_p, "wb") as f:
                    f.write(opus_b)

            codecs = [
                ("g711", g711_p),
                ("amrnb", amr_p),
                ("aac_zalo_76k", aac_p),
                ("opus_zalo_24k", opus_p),
            ]

            for c_name, c_path in codecs:
                manifest_rows.append({
                    "utt_id": f"{utt_id}_{c_name}",
                    "audio_path": c_path.relative_to(_ROOT).as_posix(),
                    "speaker_id": spk,
                    "source": "volunteer_acceptance",
                    "label": "spoof",
                    "role": "eval",
                    "tts_generator": "OmniVoice",
                    "codec": c_name,
                    "pre_codec": "clean",
                    "split": "test_unseen",
                    "duration_sec": round(dur, 3),
                    "transcript": text,
                    "raw_wer": 0.0,
                    "raw_cer": 0.0,
                    "ecapa_sim": 0.0,
                    "wavlm_sim": 0.0,
                    "derived_tier": "unseen_omnivoice",
                    "seed": 200,
                    "base_utt": base_utt,
                    "sha256": compute_sha256(c_path),
                })

    df_out = pd.DataFrame(manifest_rows)
    m_path = _ROOT / manifest_out
    m_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(m_path, index=False, encoding="utf-8")

    tot_time = time.perf_counter() - start_all
    print("\n" + "=" * 90)
    print(f"🎉 HOÀN THÀNH TỔNG HỢP UNSEEN OMNIVOICE: {len(df_out)} tệp trong {tot_time:.1f}s")
    print(f"📁 Manifest lưu tại: {manifest_out}")
    print("=" * 90)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", type=int, default=15)
    parser.add_argument("--spk", nargs="*", default=None)
    args = parser.parse_args()

    generate_omnivoice_dataset(speakers=args.spk, num_prompts_per_spk=args.prompts)
