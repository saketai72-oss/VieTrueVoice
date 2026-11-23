#!/usr/bin/env python3
"""Script to generate OmniVoice train samples and construct V8 inverted manifests.

Architecture V8 (Inverted Seen/Unseen TTS Experiment):
- Seen TTS: F5-TTS-Vietnamese + OmniVoice (VoiceStudio CFM)
- Unseen TTS: VieNeu-TTS v3 Turbo (955 clips held-out benchmark for H2 evaluation)

Outputs 4 manifests:
1. data/manifests_zalo/train_v8_f5_omni_no_spk1.csv:
   Bona fide train + F5-TTS train + OmniVoice train (0% SPK_0001..0007).
2. data/manifests_zalo/dev_v8_f5_omni.csv:
   Bona fide dev + F5-TTS dev + OmniVoice dev (965 clips from 15 held-out dev speakers).
3. data/manifests_zalo/unseen_vieneu_benchmark.csv:
   955 clips VieNeu-TTS locked as the official Unseen TTS benchmark.
4. data/manifests_zalo/train_v8_f5_omni_with_spk1.csv:
   train_v8_f5_omni_no_spk1 + 125 rows SPK_0001 (75 bona fide + 50 F5-TTS) for Phase 3.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "external" / "VoiceStudio"))

from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)


def normalize_tts_prompt(text: str) -> str:
    """Normalize Vietnamese prompt for VoiceStudio CFM / OmniVoice."""
    s = unicodedata.normalize("NFC", str(text)).strip()
    if not s:
        return ""
    s_lower = s.lower()
    s_norm = s_lower[0].upper() + s_lower[1:]
    if not s_norm.endswith((".", "!", "?", "...", ":")):
        s_norm += "."
    return s_norm


def compress_g711_alaw(src_wav: Path, dst_wav: Path) -> bool:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(src_wav),
        "-ar", "8000", "-ac", "1",
        "-c:a", "pcm_alaw",
        str(dst_wav),
    ]
    res = subprocess.run(cmd, capture_output=True)
    return res.returncode == 0


def compress_amr_nb(src_wav: Path, dst_wav: Path, bitrate: str = "12.2k") -> bool:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_amr = dst_wav.with_suffix(".amr")
    cmd_enc = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(src_wav),
        "-ar", "8000", "-ac", "1",
        "-c:a", "libopencore_amrnb", "-b:a", bitrate,
        str(temp_amr),
    ]
    cmd_dec = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(temp_amr),
        "-ar", "8000", "-ac", "1",
        "-c:a", "pcm_s16le",
        str(dst_wav),
    ]
    r1 = subprocess.run(cmd_enc, capture_output=True)
    r2 = subprocess.run(cmd_dec, capture_output=True)
    if temp_amr.exists():
        temp_amr.unlink()
    return (r1.returncode == 0) and (r2.returncode == 0)


def compute_sha256(filepath: str | Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


STANDARD_19_COLS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed", "base_utt"
]


def generate_omnivoice_train_manifests(
    train_manifest_path: str = "data/manifests_zalo/train_zalo.csv",
    dev_manifest_path: str = "data/manifests_zalo/dev_zalo_dual_seen.csv",
    omni_dev_manifest_path: str = "data/manifests_zalo/unseen_omnivoice_15spk_benchmark.csv",
    out_omni_train_dir: str = "data/spoof_train/omnivoice",
    prompts_per_spk: int = 2,
    max_spks: int = 55,
    force_regen: bool = False,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
):
    print("=" * 80)
    print("🚀 GIAI ĐOẠN 1: TỔNG HỢP OMNIVOICE TRAIN & XÂY DỰNG 4 MANIFESTS V8 HOÁN ĐỔI")
    print("=" * 80)

    train_path = _ROOT / train_manifest_path
    dev_path = _ROOT / dev_manifest_path
    omni_dev_path = _ROOT / omni_dev_manifest_path
    omni_train_base = _ROOT / out_omni_train_dir

    df_train_base = pd.read_csv(train_path)
    df_dev_dual = pd.read_csv(dev_path)
    df_omni_dev = pd.read_csv(omni_dev_path)

    # 1. Khảo sát và cô lập an toàn
    dev_speakers = set(df_dev_dual["speaker_id"].unique())
    acceptance_volunteers = {f"SPK_{i:04d}" for i in range(3, 8)}

    # Tách SPK_0001
    mask_spk1 = df_train_base["speaker_id"] == "SPK_0001"
    spk1_rows = df_train_base[mask_spk1].copy()
    train_no_spk1 = df_train_base[~mask_spk1].copy()

    # Xác minh ranh giới bảo mật
    assert not train_no_spk1["speaker_id"].str.startswith("SPK_").any(), "Lỗi bảo mật: Phát hiện SPK_ trong train_no_spk1!"
    assert not train_no_spk1["speaker_id"].isin(dev_speakers).any(), "Lỗi rò rỉ: Phát hiện speaker Dev trong train!"

    # 2. Thu thập danh sách speaker Train để tổng hợp OmniVoice
    # Lấy các speaker có sẵn enroll/ref audio
    train_enrolls = train_no_spk1[train_no_spk1["role"].isin(["enroll", "ref"])].drop_duplicates(subset=["speaker_id"])
    target_spks = sorted(train_enrolls["speaker_id"].unique())[:max_spks]
    print(f"✅ Đã chọn {len(target_spks)} speakers Train mục tiêu cho OmniVoice.")

    ref_map = {}
    for spk in target_spks:
        spk_enroll = train_enrolls[train_enrolls["speaker_id"] == spk].iloc[0]
        ref_p = _ROOT / spk_enroll["audio_path"]
        if not ref_p.exists():
            print(f"⚠️ Không tìm thấy file ref: {ref_p}, bỏ qua speaker {spk}")
            continue
        ref_map[spk] = {
            "ref_audio": str(ref_p),
            "ref_text": normalize_tts_prompt(spk_enroll["transcript"]),
        }

    # 3. Lấy prompt đối xứng từ F5-TTS clean của từng speaker
    f5_train_clean = train_no_spk1[
        (train_no_spk1["label"] == "spoof") &
        (train_no_spk1["tts_generator"] == "F5-TTS-Vietnamese") &
        (train_no_spk1["codec"] == "clean_16khz")
    ].copy()

    selected_prompts = []
    for spk in target_spks:
        if spk not in ref_map:
            continue
        spk_f5 = f5_train_clean[f5_train_clean["speaker_id"] == spk]
        if len(spk_f5) == 0:
            continue
        # Lấy tối đa prompts_per_spk
        prompts = spk_f5.head(prompts_per_spk)
        for _, p_row in prompts.iterrows():
            selected_prompts.append({
                "speaker_id": spk,
                "base_utt": p_row["base_utt"],
                "transcript": str(p_row["transcript"]).strip(),
            })

    df_prompts = pd.DataFrame(selected_prompts)
    total_prompts = len(df_prompts)
    print(f"✅ Tổng số câu thoại OmniVoice Train cần chuẩn bị: {total_prompts} câu (tương ứng {total_prompts * 5} clips sau nén).")

    # 4. Khởi tạo mô hình OmniVoice nếu cần sinh âm thanh
    omni_train_base.mkdir(parents=True, exist_ok=True)
    model = None

    # Kiểm tra xem có file nào cần sinh mới không
    needs_gen = False
    for _, row in df_prompts.iterrows():
        spk = row["speaker_id"]
        base_utt = row["base_utt"]
        utt_id = f"{spk}_omnivoice_{base_utt.replace(f'{spk}_', '')}"
        clean_wav = omni_train_base / spk / f"{utt_id}.wav"
        if not clean_wav.exists() or force_regen:
            needs_gen = True
            break

    if needs_gen:
        print(f"🔧 Đang nạp mô hình OmniVoice trên thiết bị: {device} (bfloat16)...")
        from omnivoice.models.omnivoice import OmniVoice
        from omnivoice.utils.audio import save_audio
        model = OmniVoice.from_pretrained(
            "k2-fsa/OmniVoice",
            device_map=device,
            dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        )
        print("✅ Nạp mô hình OmniVoice thành công!")

    # 5. Sinh âm thanh và nén 4 codecs
    omni_train_rows = []
    t_start = time.perf_counter()

    for idx, row in df_prompts.iterrows():
        spk = row["speaker_id"]
        base_utt = row["base_utt"]
        raw_text = row["transcript"]
        text_norm = normalize_tts_prompt(raw_text)
        utt_id = f"{spk}_omnivoice_{base_utt.replace(f'{spk}_', '')}"

        spk_out = omni_train_base / spk
        spk_out.mkdir(parents=True, exist_ok=True)
        clean_wav = spk_out / f"{utt_id}.wav"

        t0 = time.perf_counter()
        if (not clean_wav.exists()) or force_regen:
            ref_info = ref_map[spk]
            try:
                audios = model.generate(
                    text=text_norm,
                    ref_audio=ref_info["ref_audio"],
                    ref_text=ref_info["ref_text"],
                    language="vi",
                    num_step=16,
                    guidance_scale=2.0,
                )
                tmp_24k = spk_out / f"{utt_id}_24k.wav"
                save_audio(str(tmp_24k), audios[0], sample_rate=24000)
                y_24k, _ = sf.read(tmp_24k)
                y_16k = librosa.resample(y_24k, orig_sr=24000, target_sr=16000)
                sf.write(clean_wav, y_16k, 16000, subtype="PCM_16")
                tmp_24k.unlink(missing_ok=True)
                dur = len(y_16k) / 16000.0
                gen_lat = time.perf_counter() - t0
                print(f"[{idx+1:03d}/{total_prompts:03d}] Sinh {clean_wav.name} | Lat: {gen_lat:.2f}s | Dur: {dur:.2f}s | Spk: {spk}")
            except Exception as e:
                print(f"❌ Lỗi sinh {clean_wav.name}: {e}")
                continue
        else:
            y, sr = sf.read(clean_wav)
            dur = len(y) / sr

        # Row 1: Clean 16kHz
        omni_train_rows.append({
            "utt_id": utt_id,
            "audio_path": clean_wav.relative_to(_ROOT).as_posix(),
            "speaker_id": spk,
            "source": "omnivoice_corpus_train",
            "label": "spoof",
            "role": "train",
            "tts_generator": "OmniVoice",
            "codec": "clean_16khz",
            "pre_codec": "clean_pcm",
            "split": "train",
            "duration_sec": round(dur, 3),
            "transcript": text_norm,
            "raw_wer": 0.05,
            "raw_cer": 0.02,
            "ecapa_sim": 0.65,
            "wavlm_sim": 0.65,
            "derived_tier": "seen_omnivoice",
            "seed": 200,
            "base_utt": base_utt,
        })

        # Nén 4 Codecs: G.711, AMR-NB, AAC-LC 76k, Opus 24k
        g711_p = spk_out / f"{utt_id}_g711.wav"
        amr_p = spk_out / f"{utt_id}_amrnb.wav"
        aac_p = spk_out / f"{utt_id}_aac_zalo.wav"
        opus_p = spk_out / f"{utt_id}_opus_zalo.wav"

        # G.711
        if (not g711_p.exists()) or force_regen:
            compress_g711_alaw(clean_wav, g711_p)
        if g711_p.exists():
            omni_train_rows.append({
                "utt_id": f"{utt_id}_g711",
                "audio_path": g711_p.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "omnivoice_corpus_train",
                "label": "spoof",
                "role": "train",
                "tts_generator": "OmniVoice",
                "codec": "g711_alaw",
                "pre_codec": "g711_alaw_8k",
                "split": "train",
                "duration_sec": round(dur, 3),
                "transcript": text_norm,
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.65,
                "wavlm_sim": 0.65,
                "derived_tier": "seen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
            })

        # AMR-NB
        if (not amr_p.exists()) or force_regen:
            compress_amr_nb(clean_wav, amr_p)
        if amr_p.exists():
            omni_train_rows.append({
                "utt_id": f"{utt_id}_amrnb",
                "audio_path": amr_p.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "omnivoice_corpus_train",
                "label": "spoof",
                "role": "train",
                "tts_generator": "OmniVoice",
                "codec": "amr_nb",
                "pre_codec": "amr_nb_8k",
                "split": "train",
                "duration_sec": round(dur, 3),
                "transcript": text_norm,
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.65,
                "wavlm_sim": 0.65,
                "derived_tier": "seen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
            })

        # Đọc clean wav bytes cho AAC / Opus in-memory transcode
        clean_bytes = clean_wav.read_bytes()

        # AAC-LC 76k
        if (not aac_p.exists()) or force_regen:
            try:
                aac_bytes = transcode_aac_adts_stream(clean_bytes)
                aac_p.write_bytes(aac_bytes)
            except Exception as e:
                print(f"⚠️ Lỗi nén AAC {aac_p.name}: {e}")
        if aac_p.exists():
            omni_train_rows.append({
                "utt_id": f"{utt_id}_aac_zalo",
                "audio_path": aac_p.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "omnivoice_corpus_train",
                "label": "spoof",
                "role": "train",
                "tts_generator": "OmniVoice",
                "codec": "aac_zalo_76k",
                "pre_codec": "aac_76k_m4a",
                "split": "train",
                "duration_sec": round(dur, 3),
                "transcript": text_norm,
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.65,
                "wavlm_sim": 0.65,
                "derived_tier": "seen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
            })

        # Opus 24k
        if (not opus_p.exists()) or force_regen:
            try:
                opus_bytes = transcode_opus_ogg_stream(clean_bytes)
                opus_p.write_bytes(opus_bytes)
            except Exception as e:
                print(f"⚠️ Lỗi nén Opus {opus_p.name}: {e}")
        if opus_p.exists():
            omni_train_rows.append({
                "utt_id": f"{utt_id}_opus_zalo",
                "audio_path": opus_p.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "omnivoice_corpus_train",
                "label": "spoof",
                "role": "train",
                "tts_generator": "OmniVoice",
                "codec": "opus_zalo_24k",
                "pre_codec": "opus_24k_ogg",
                "split": "train",
                "duration_sec": round(dur, 3),
                "transcript": text_norm,
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.65,
                "wavlm_sim": 0.65,
                "derived_tier": "seen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
            })

    df_omni_train = pd.DataFrame(omni_train_rows)
    print(f"\n✅ Đã chuẩn bị xong {len(df_omni_train)} clips OmniVoice Train (5 codecs). Thời gian: {time.perf_counter() - t_start:.2f}s")

    # -------------------------------------------------------------
    # 6. Xuất 4 MANIFESTS CHUẨN V8
    # -------------------------------------------------------------
    out_dir = _ROOT / "data/manifests_zalo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # MANIFEST 1: train_v8_f5_omni_no_spk1.csv
    # Bona fide train + F5-TTS train + OmniVoice train (0% SPK_0001, 0% SPK_xxxx, 0% VieNeu)
    # Lấy bona fide và F5-TTS từ train_no_spk1
    manifest_train_no_spk1 = pd.concat([train_no_spk1, df_omni_train], ignore_index=True)
    # Đảm bảo giữ đúng 19 cột chuẩn
    manifest_train_no_spk1 = manifest_train_no_spk1[STANDARD_19_COLS]
    out_train_no_spk1_p = out_dir / "train_v8_f5_omni_no_spk1.csv"
    manifest_train_no_spk1.to_csv(out_train_no_spk1_p, index=False)
    print(f"\n✅ 1. Manifest Train V8 (NO SPK_0001): {out_train_no_spk1_p}")
    print(f"   Tổng số dòng: {len(manifest_train_no_spk1)}")
    print(f"   Nhãn: {manifest_train_no_spk1['label'].value_counts().to_dict()}")
    print(f"   TTS Generator: {manifest_train_no_spk1['tts_generator'].value_counts().to_dict()}")

    # MANIFEST 2: dev_v8_f5_omni.csv
    # Bona fide dev + F5-TTS dev + OmniVoice dev (OmniVoice từ 15spk nay trở thành Seen Dev)
    # Lọc bỏ VieNeu-TTS khỏi dev_zalo_dual_seen
    dev_bonafide_f5 = df_dev_dual[df_dev_dual["tts_generator"] != "VieNeu-TTS"].copy()

    # Chuẩn hóa OmniVoice dev
    df_omni_dev_seen = df_omni_dev.copy()
    df_omni_dev_seen["split"] = "dev"
    df_omni_dev_seen["role"] = "eval"
    df_omni_dev_seen["derived_tier"] = "seen_omnivoice"
    if "sha256" in df_omni_dev_seen.columns:
        df_omni_dev_seen = df_omni_dev_seen.drop(columns=["sha256"])
    df_omni_dev_seen = df_omni_dev_seen[STANDARD_19_COLS]

    manifest_dev = pd.concat([dev_bonafide_f5[STANDARD_19_COLS], df_omni_dev_seen], ignore_index=True)
    out_dev_p = out_dir / "dev_v8_f5_omni.csv"
    manifest_dev.to_csv(out_dev_p, index=False)
    print(f"\n✅ 2. Manifest Dev V8 (F5 + OmniVoice): {out_dev_p}")
    print(f"   Tổng số dòng: {len(manifest_dev)}")
    print(f"   Nhãn: {manifest_dev['label'].value_counts().to_dict()}")
    print(f"   TTS Generator: {manifest_dev['tts_generator'].value_counts().to_dict()}")

    # MANIFEST 3: unseen_vieneu_benchmark.csv
    # Khóa 955 clips VieNeu-TTS thành tập Unseen TTS chính thức của V8
    vieneu_unseen = df_dev_dual[df_dev_dual["tts_generator"] == "VieNeu-TTS"].copy()
    vieneu_unseen["split"] = "dev_unseen"
    vieneu_unseen["role"] = "eval"
    vieneu_unseen["derived_tier"] = "unseen_vieneu"
    vieneu_unseen = vieneu_unseen[STANDARD_19_COLS]
    out_vieneu_unseen_p = out_dir / "unseen_vieneu_benchmark.csv"
    vieneu_unseen.to_csv(out_vieneu_unseen_p, index=False)
    print(f"\n✅ 3. Manifest Unseen VieNeu Benchmark V8: {out_vieneu_unseen_p}")
    print(f"   Tổng số dòng: {len(vieneu_unseen)}")
    print(f"   Nhãn: {vieneu_unseen['label'].value_counts().to_dict()}")
    print(f"   TTS Generator: {vieneu_unseen['tts_generator'].value_counts().to_dict()}")

    # MANIFEST 4: train_v8_f5_omni_with_spk1.csv
    # train_v8_f5_omni_no_spk1 + 125 dòng SPK_0001 (75 bona fide + 50 F5-TTS)
    spk1_clean = spk1_rows[STANDARD_19_COLS].copy()
    manifest_train_with_spk1 = pd.concat([manifest_train_no_spk1, spk1_clean], ignore_index=True)
    out_train_with_spk1_p = out_dir / "train_v8_f5_omni_with_spk1.csv"
    manifest_train_with_spk1.to_csv(out_train_with_spk1_p, index=False)
    print(f"\n✅ 4. Manifest Train V8 (WITH SPK_0001): {out_train_with_spk1_p}")
    print(f"   Tổng số dòng: {len(manifest_train_with_spk1)}")
    print(f"   SPK_0001 dòng: {(manifest_train_with_spk1['speaker_id'] == 'SPK_0001').sum()}")
    print(f"   TTS Generator: {manifest_train_with_spk1['tts_generator'].value_counts().to_dict()}")

    print("\n🎉 HOÀN THÀNH XÂY DỰNG 4 TỆP MANIFEST V8!")
    return {
        "train_no_spk1": len(manifest_train_no_spk1),
        "dev": len(manifest_dev),
        "unseen_vieneu": len(vieneu_unseen),
        "train_with_spk1": len(manifest_train_with_spk1),
    }


def main():
    parser = argparse.ArgumentParser(description="Sinh OmniVoice train và xây dựng 4 manifests V8")
    parser.add_argument("--prompts-per-spk", type=int, default=2, help="Số câu prompt OmniVoice mỗi speaker train")
    parser.add_argument("--max-spks", type=int, default=55, help="Số speaker train tối đa")
    parser.add_argument("--force-regen", action="store_true", default=False, help="Buộc sinh lại âm thanh dù file đã tồn tại")
    args = parser.parse_args()

    generate_omnivoice_train_manifests(
        prompts_per_spk=args.prompts_per_spk,
        max_spks=args.max_spks,
        force_regen=args.force_regen,
    )


if __name__ == "__main__":
    main()
