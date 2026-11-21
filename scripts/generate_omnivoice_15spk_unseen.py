"""Sinh mẫu âm thanh giả mạo Unseen TTS quy mô lớn bằng VoiceStudio CFM (OmniVoice).
Áp dụng trên 15 người nói Held-out Bona Fide chính thức của mô hình (tập Dev Zalo).
Tuyệt đối cô lập 100% 5 tình nguyện viên đối chứng (SPK_0003..SPK_0007).

Quy trình:
1. Nạp mô hình k2-fsa/OmniVoice trên CUDA (bfloat16).
2. Lấy 15 người nói held-out trong dev_zalo_dual_seen.csv (VIVOS & Common Voice).
3. Sử dụng file ref/enroll của từng người nói làm mẫu giọng tham chiếu.
4. Sinh 193 câu spoof đối xứng (khớp 1:1:1 với F5-TTS và VieNeu-TTS theo base_utt).
5. Nén 4 codec: G.711 A-law, AMR-NB, AAC-LC 76k, Opus 24k -> Tổng cộng 965 clips.
6. Lưu trữ vào data/spoof_unseen/omnivoice_15spk/ và đồng bộ sang Voice_Final.
7. Xuất manifest 18 cột: data/manifests_zalo/unseen_omnivoice_15spk_benchmark.csv.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import unicodedata

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "external" / "VoiceStudio"))

from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.audio import save_audio
from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)

VOICE_FINAL_DIR = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Voice_Final\01_Corpus_Evaluation\Unseen_VoiceStudio_15Spk")


def normalize_tts_prompt(text: str) -> str:
    """Chuẩn hóa văn bản tiếng Việt cho VoiceStudio CFM / OmniVoice.

    Chuyển về chữ thường, viết hoa chữ cái đầu và bảo đảm có dấu ngắt câu cuối câu.
    Khắc phục triệt để lỗi gãy bộ căn chỉnh âm vị (neural aligner breakdown)
    khi gặp văn bản viết hoa toàn bộ không dấu chấm phẩy của VIVOS.
    """
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


def main():
    parser = argparse.ArgumentParser(description="Sinh dataset Unseen TTS VoiceStudio CFM 15 người nói")
    parser.add_argument("--source-manifest", type=str, default="data/manifests_zalo/dev_zalo_dual_seen.csv")
    parser.add_argument("--out-dir", type=str, default="data/spoof_unseen/omnivoice_15spk")
    parser.add_argument("--manifest-out", type=str, default="data/manifests_zalo/unseen_omnivoice_15spk_benchmark.csv")
    parser.add_argument("--force-vivos", action="store_true", default=True, help="Tái tổng hợp VIVOS với văn bản chuẩn hóa")
    parser.add_argument("--force-all", action="store_true", default=False, help="Tái tổng hợp toàn bộ 15 người nói")
    args = parser.parse_args()

    src_manifest = _ROOT / args.source_manifest
    if not src_manifest.exists():
        print(f"❌ Không tìm thấy manifest: {src_manifest}")
        sys.exit(1)

    df = pd.read_csv(src_manifest)
    print("=" * 90)
    print("🚀 PIPELINE TỔNG HỢP UNSEEN TTS VOICESTUDIO CFM TRÊN 15 NGƯỜI NÓI HELD-OUT")
    print("=" * 90)

    # 1. Trích xuất thông tin reference của 15 người nói
    enrolls = df[df["role"].isin(["enroll", "ref"])].drop_duplicates(subset=["speaker_id"])
    ref_map = {}
    for _, r in enrolls.iterrows():
        spk = r["speaker_id"]
        # Bảo đảm tuyệt đối 100% không dính 5 tình nguyện viên nghiệm thu
        if spk.startswith("SPK_000") and spk != "SPK_0001":
            print(f"🛑 BÁO ĐỘNG AN TOÀN: Phát hiện {spk} trong danh sách! Dừng ngay lập tức!")
            sys.exit(1)
        ref_p = _ROOT / r["audio_path"]
        if not ref_p.exists():
            print(f"❌ Thiếu file ref: {ref_p}")
            sys.exit(1)
        ref_map[spk] = {
            "ref_audio": str(ref_p),
            "ref_text": normalize_tts_prompt(r["transcript"]),
        }

    print(f"✅ Đã nạp mẫu tham chiếu chuẩn cho {len(ref_map)} người nói held-out.")

    # 2. Lấy danh sách prompt đối xứng (khớp base_utt với F5-TTS và VieNeu-TTS)
    spoofs_clean = df[(df["label"] == "spoof") & (df["codec"] == "clean_16khz")].copy()
    unique_prompts = spoofs_clean.drop_duplicates(subset=["base_utt"]).reset_index(drop=True)
    total_prompts = len(unique_prompts)
    print(f"✅ Tìm thấy {total_prompts} câu thoại đối xứng cần tổng hợp VoiceStudio CFM.")

    # 3. Nạp mô hình OmniVoice trên GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔧 Đang nạp mô hình OmniVoice (VoiceStudio CFM) trên thiết bị: {device} (bfloat16)...")
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    )
    print("✅ Nạp mô hình OmniVoice thành công!")

    out_base = _ROOT / args.out_dir
    out_base.mkdir(parents=True, exist_ok=True)
    VOICE_FINAL_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    start_total = time.perf_counter()

    for idx, row in unique_prompts.iterrows():
        spk = row["speaker_id"]
        base_utt = row["base_utt"]
        utt_id = f"{spk}_omnivoice_{base_utt.replace(f'{spk}_', '')}"
        raw_text = str(row["transcript"]).strip()
        text_norm = normalize_tts_prompt(raw_text)

        ref_info = ref_map[spk]
        spk_out = out_base / spk
        spk_out.mkdir(parents=True, exist_ok=True)

        spk_vf = VOICE_FINAL_DIR / spk
        spk_vf.mkdir(parents=True, exist_ok=True)

        clean_wav = spk_out / f"{utt_id}.wav"
        t0 = time.perf_counter()

        is_vivos = spk.startswith("VIVOS")
        should_gen = (not clean_wav.exists()) or args.force_all or (args.force_vivos and is_vivos)

        # 4. Sinh âm thanh Clean 16kHz
        if should_gen:
            try:
                audios = model.generate(
                    text=text_norm,
                    ref_audio=ref_info["ref_audio"],
                    ref_text=ref_info["ref_text"],
                    language="vi",
                    num_step=16,
                    guidance_scale=2.0,
                )
                lat = time.perf_counter() - t0
                tmp_24k = spk_out / f"{utt_id}_24k.wav"
                save_audio(str(tmp_24k), audios[0], sample_rate=24000)

                y_24k, _ = sf.read(tmp_24k)
                y_16k = librosa.resample(y_24k, orig_sr=24000, target_sr=16000)
                sf.write(clean_wav, y_16k, 16000, subtype="PCM_16")
                tmp_24k.unlink(missing_ok=True)
                dur = len(y_16k) / 16000.0
                print(f"[{idx+1:03d}/{total_prompts:03d}] {clean_wav.name} | Lat: {lat:.2f}s | Dur: {dur:.2f}s | Spk: {spk} (Regen: {should_gen})")
            except Exception as e:
                print(f"❌ Lỗi sinh {clean_wav.name}: {e}")
                continue
        else:
            y, sr = sf.read(clean_wav)
            dur = len(y) / sr

        # Đồng bộ sang Voice_Final
        vf_clean = spk_vf / clean_wav.name
        shutil.copy2(clean_wav, vf_clean)

        manifest_rows.append({
            "utt_id": utt_id,
            "audio_path": clean_wav.relative_to(_ROOT).as_posix(),
            "speaker_id": spk,
            "source": "omnivoice_corpus_eval",
            "label": "spoof",
            "role": "eval",
            "tts_generator": "OmniVoice",
            "codec": "clean_16khz",
            "pre_codec": "none",
            "split": "dev_unseen",
            "duration_sec": round(dur, 3),
            "transcript": text_norm,
            "raw_wer": 0.0,
            "raw_cer": 0.0,
            "ecapa_sim": 0.0,
            "wavlm_sim": 0.0,
            "derived_tier": "unseen_omnivoice",
            "seed": 200,
            "base_utt": base_utt,
            "sha256": compute_sha256(clean_wav),
        })

        # 5. Nén 4 kênh codec viễn thông/Zalo
        g711_p = spk_out / f"{utt_id}_g711.wav"
        amr_p = spk_out / f"{utt_id}_amrnb.wav"
        aac_p = spk_out / f"{utt_id}_aac_zalo.wav"
        opus_p = spk_out / f"{utt_id}_opus_zalo.wav"

        if should_gen or not g711_p.exists():
            compress_g711_alaw(clean_wav, g711_p)
        if should_gen or not amr_p.exists():
            compress_amr_nb(clean_wav, amr_p)

        with open(clean_wav, "rb") as f:
            raw_b = f.read()

        if should_gen or not aac_p.exists():
            aac_b = transcode_aac_adts_stream(raw_b)
            with open(aac_p, "wb") as f:
                f.write(aac_b)

        if should_gen or not opus_p.exists():
            opus_b = transcode_opus_ogg_stream(raw_b)
            with open(opus_p, "wb") as f:
                f.write(opus_b)

        # Copy các file codec sang Voice_Final
        for src_p in [g711_p, amr_p, aac_p, opus_p]:
            dst_p = spk_vf / src_p.name
            shutil.copy2(src_p, dst_p)

        codecs_meta = [
            ("g711_alaw", g711_p),
            ("amr_nb", amr_p),
            ("aac_zalo_76k", aac_p),
            ("opus_zalo_24k", opus_p),
        ]

        for c_name, c_path in codecs_meta:
            c_utt_id = f"{utt_id}_{c_name}"
            y_c, sr_c = sf.read(c_path)
            c_dur = len(y_c) / sr_c
            manifest_rows.append({
                "utt_id": c_utt_id,
                "audio_path": c_path.relative_to(_ROOT).as_posix(),
                "speaker_id": spk,
                "source": "omnivoice_corpus_eval",
                "label": "spoof",
                "role": "eval",
                "tts_generator": "OmniVoice",
                "codec": c_name,
                "pre_codec": "clean",
                "split": "dev_unseen",
                "duration_sec": round(c_dur, 3),
                "transcript": text_norm,
                "raw_wer": 0.0,
                "raw_cer": 0.0,
                "ecapa_sim": 0.0,
                "wavlm_sim": 0.0,
                "derived_tier": "unseen_omnivoice",
                "seed": 200,
                "base_utt": base_utt,
                "sha256": compute_sha256(c_path),
            })

    total_time = time.perf_counter() - start_total
    print(f"\n🎉 HOÀN TẤT SINH {len(manifest_rows)} TỆP ÂM THANH UNSEEN CFM TRONG {total_time/60:.2f} PHÚT!")

    # Xuất Manifest 18 cột
    m_out = _ROOT / args.manifest_out
    m_out.parent.mkdir(parents=True, exist_ok=True)
    out_df = pd.DataFrame(manifest_rows)
    out_df.to_csv(m_out, index=False, encoding="utf-8")
    print(f"📄 Đã lưu manifest tại: {m_out}")

    # Sao lưu sang Voice_Final
    vf_manifest = VOICE_FINAL_DIR / "UNSEEN_VOICESTUDIO_15SPK_MANIFEST.csv"
    shutil.copy2(m_out, vf_manifest)
    print(f"📄 Đã sao lưu manifest sang Voice_Final: {vf_manifest}")


if __name__ == "__main__":
    main()
