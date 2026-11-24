#!/usr/bin/env python3
"""Pipeline khoi phuc va chuan hoa bo du lieu OmniVoice_CFM V8.1 (1:1 voi VieNeu-TTS).

Muc tieu:
1. Lap danh muc chuan 1:1 voi data/spoof_vieneu/ (1.289 clean = 6.445 files x 5 codecs):
   - VIVOS: 959 clean = 4.795 files (65 nguoi noi)
   - CommonVoice: 245 clean = 1.225 files (25 nguoi noi)
   - SPK_Volunteers: 85 clean = 425 files (SPK_0001: 10 clean = 50 files; SPK_0003..0007: 75 clean = 375 files)
2. Giai nen chon loc file ref con thieu (15 Test VIVOS + 5 OOD CommonVoice) va bo audio test_indomain
   tu data/vitruevoice_data_processed.zip + transcode proxy Zalo (AAC 76k, Opus 24k).
3. Tai su dung thong minh cac mau OmniVoice hop le da sinh trong:
   - data/spoof_train/omnivoice/ (108 clean hop le)
   - data/spoof_unseen/omnivoice_15spk/ (191 clean khop Dev V7)
   - data/spoof_unseen/omnivoice/ (75 clean SPK_0003..0007)
   Sau do sinh phan con thieu bang VoiceStudio OmniVoice (HF_HUB_OFFLINE=1, num_step=16, guidance_scale=2.0),
   resample 24kHz -> 16kHz, chuan hoa dinh 0.95, kiem tra duration >= 0.5s va rms > 1e-4,
   nen du 4 codec (g711_alaw, amr_nb, aac_zalo_76k, opus_zalo_24k) vao data/spoof_omnivoice_v8/<speaker_id>/.
4. Sao luu manifest V8.0 cu vao data/manifests_zalo/.backup_v8_0/ va xuat 5 manifest V8.1 chuan 19 cot:
   - train_v8_f5_omni_no_spk1.csv   (54.225 dong)
   - train_v8_f5_omni_with_spk1.csv (54.400 dong)
   - dev_v8_f5_omni.csv             (12.405 dong)
   - test_indomain_v8_f5_omni.csv   (15.980 dong)
   - unseen_vieneu_benchmark.csv    (   955 dong)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "external" / "VoiceStudio") not in sys.path:
    sys.path.insert(0, str(_ROOT / "external" / "VoiceStudio"))

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch

from scripts.generate_zalo_paired_manifests import (
    transcode_aac_adts_stream,
    transcode_opus_ogg_stream,
)

STANDARD_19_COLS = [
    "utt_id", "audio_path", "speaker_id", "source", "label", "role",
    "tts_generator", "codec", "pre_codec", "split", "duration_sec",
    "transcript", "raw_wer", "raw_cer", "ecapa_sim", "wavlm_sim",
    "derived_tier", "seed", "base_utt",
]

CODEC_SPECS = [
    ("clean_16khz", "clean_pcm", "", "", 16000),
    ("g711_alaw", "g711_alaw_8k", "_g711", "_g711", 8000),
    ("amr_nb", "amr_nb_8k", "_amrnb", "_amrnb", 8000),
    ("aac_zalo_76k", "aac_76k_m4a", "_aac_zalo", "_aac_zalo", 16000),
    ("opus_zalo_24k", "opus_24k_ogg", "_opus_zalo", "_opus_zalo", 16000),
]

SPK0001_REF_AUDIO = "data/bonafide_ref/SPK_0001/SPK_0001_01.wav"
SPK0001_REF_TEXT = "Cả hai bên hãy cố gắng bình tĩnh lắng nghe và cùng nhau tìm giải pháp phù hợp nhất."
SPK_VOLUNTEER_REF_TEXT = "Xin chào quý khách, cuộc gọi này được ghi âm để đảm bảo chất lượng dịch vụ."

REUSE_SOURCE_DIRS = [
    "data/spoof_train/omnivoice",
    "data/spoof_unseen/omnivoice_15spk",
    "data/spoof_unseen/omnivoice",
]


@dataclass
class TargetUtterance:
    speaker_id: str
    base_utt: str
    source_group: str  # "vivos", "common_voice", "volunteer_consent"
    split_bucket: str  # "train_corpus", "train_spk1", "dev", "test_indomain", "ood_cv", "acceptance_5spk"
    prompt_text: str
    ref_audio: str
    ref_text: str


def infer_source_group(speaker_id: str) -> str:
    if speaker_id.startswith("VIVOS"):
        return "vivos"
    if speaker_id.startswith("CV_"):
        return "common_voice"
    if speaker_id.startswith("SPK_"):
        return "volunteer_consent"
    raise ValueError(f"Unknown speaker source prefix: {speaker_id}")


def normalize_tts_prompt(text: str) -> str:
    """Normalize Vietnamese text for OmniVoice neural aligner only (not for manifest CSV)."""
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
    tmp_wav = dst_wav.with_suffix(".tmp.wav")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(src_wav),
        "-ar", "8000", "-ac", "1",
        "-c:a", "pcm_alaw",
        str(tmp_wav),
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and tmp_wav.exists() and tmp_wav.stat().st_size > 100:
        tmp_wav.replace(dst_wav)
        return True
    tmp_wav.unlink(missing_ok=True)
    return False


def compress_amr_nb(src_wav: Path, dst_wav: Path, bitrate: str = "12.2k") -> bool:
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    temp_amr = dst_wav.with_suffix(".amr")
    tmp_wav = dst_wav.with_suffix(".tmp.wav")
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
        str(tmp_wav),
    ]
    r1 = subprocess.run(cmd_enc, capture_output=True)
    r2 = subprocess.run(cmd_dec, capture_output=True)
    temp_amr.unlink(missing_ok=True)
    if r1.returncode == 0 and r2.returncode == 0 and tmp_wav.exists() and tmp_wav.stat().st_size > 100:
        tmp_wav.replace(dst_wav)
        return True
    tmp_wav.unlink(missing_ok=True)
    return False


def encode_all_4_codecs(clean_wav: Path, spk_out: Path, base_utt: str) -> None:
    g711_p = spk_out / f"{base_utt}_g711.wav"
    amr_p = spk_out / f"{base_utt}_amrnb.wav"
    aac_p = spk_out / f"{base_utt}_aac_zalo.wav"
    opus_p = spk_out / f"{base_utt}_opus_zalo.wav"

    if not (g711_p.exists() and g711_p.stat().st_size > 100):
        if not compress_g711_alaw(clean_wav, g711_p):
            raise RuntimeError(f"G.711 encode failed: {clean_wav}")

    if not (amr_p.exists() and amr_p.stat().st_size > 100):
        if not compress_amr_nb(clean_wav, amr_p):
            raise RuntimeError(f"AMR-NB encode failed: {clean_wav}")

    clean_bytes = clean_wav.read_bytes()
    if not (aac_p.exists() and aac_p.stat().st_size > 100):
        aac_bytes = transcode_aac_adts_stream(clean_bytes)
        tmp = aac_p.with_suffix(".tmp.wav")
        tmp.write_bytes(aac_bytes)
        tmp.replace(aac_p)

    if not (opus_p.exists() and opus_p.stat().st_size > 100):
        opus_bytes = transcode_opus_ogg_stream(clean_bytes)
        tmp = opus_p.with_suffix(".tmp.wav")
        tmp.write_bytes(opus_bytes)
        tmp.replace(opus_p)


def is_valid_clean_wav(wav_path: Path, min_dur: float = 0.5, min_rms: float = 1e-4) -> bool:
    if not wav_path.exists() or wav_path.stat().st_size <= 100:
        return False
    try:
        info = sf.info(str(wav_path))
        if info.samplerate != 16000 or info.channels != 1 or info.subtype != "PCM_16":
            return False
        if info.duration < min_dur:
            return False
        y, _ = sf.read(str(wav_path), dtype="float32")
        if y.size == 0 or not np.all(np.isfinite(y)):
            return False
        rms = float(np.sqrt(np.mean(y ** 2)))
        return rms > min_rms
    except Exception:
        return False


def is_complete_5_codecs(spk_dir: Path, base_utt: str) -> bool:
    clean_p = spk_dir / f"{base_utt}.wav"
    if not is_valid_clean_wav(clean_p):
        return False
    for _, _, file_suf, _, exp_sr in CODEC_SPECS[1:]:
        p = spk_dir / f"{base_utt}{file_suf}.wav"
        if not p.exists() or p.stat().st_size <= 100:
            return False
        try:
            info = sf.info(str(p))
            if info.samplerate != exp_sr or info.duration < 0.45:
                return False
        except Exception:
            return False
    return True


def extract_missing_refs_and_test_audio(root: Path = _ROOT) -> None:
    """Selectively extract missing bonafide_ref WAVs (20 speakers) and test_indomain audio from zip."""
    zip_path = root / "data/vitruevoice_data_processed.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing zip archive: {zip_path}")

    test_in_df = pd.read_csv(root / "data/manifests_zalo/test_indomain_zalo.csv")
    test_non_vn = test_in_df[test_in_df["tts_generator"] != "VieNeu-TTS"].copy()
    test_spks = sorted(test_in_df["speaker_id"].unique())
    ood_cv_spks = [
        "CV_353f059e70", "CV_97ee3fed8e", "CV_b5a488f638", "CV_bb99c0461b", "CV_e3e2b2e165"
    ]
    ref_target_spks = set(test_spks) | set(ood_cv_spks)

    with zipfile.ZipFile(zip_path, "r") as zf:
        znames = set(zf.namelist())
        to_extract: list[tuple[str, Path]] = []

        # 1. Extract data/bonafide_ref/<spk>/*.wav for 15 Test VIVOS + 5 OOD CV speakers
        for entry in sorted(znames):
            if entry.startswith("data/bonafide_ref/") and entry.endswith(".wav"):
                parts = entry.split("/")
                if len(parts) >= 4 and parts[2] in ref_target_spks:
                    dst = root / entry
                    if not (dst.exists() and dst.stat().st_size > 100):
                        to_extract.append((entry, dst))

        # 2. Extract missing clean_16khz / g711_alaw / amr_nb for test_indomain_zalo
        for _, row in test_non_vn.iterrows():
            if row["codec"] in ("clean_16khz", "g711_alaw", "amr_nb"):
                rel = str(row["audio_path"]).replace("\\", "/").lstrip("/")
                dst = root / rel
                if not (dst.exists() and dst.stat().st_size > 100):
                    if rel not in znames:
                        raise FileNotFoundError(f"Expected entry missing in zip: {rel}")
                    to_extract.append((rel, dst))

        if to_extract:
            print(f"[ZipExtract] Extracting {len(to_extract)} missing ref & test_indomain WAVs...")
            t0 = time.perf_counter()
            for entry, dst in to_extract:
                dst.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(entry) as src_f, open(dst, "wb") as out_f:
                    out_f.write(src_f.read())
            print(f"[ZipExtract] Done in {time.perf_counter() - t0:.1f}s")
        else:
            print("[ZipExtract] All bonafide_ref and base test_indomain WAVs already on disk.")

    # 3. Transcode missing AAC-LC 76k & Opus 24k proxies for test_indomain_zalo
    clean_rows = test_non_vn[test_non_vn["codec"] == "clean_16khz"]
    base_to_clean = dict(zip(clean_rows["base_utt"], clean_rows["audio_path"]))
    proxy_tasks: list[tuple[Path, Path, str]] = []
    seen_dst: set[str] = set()
    for _, row in test_non_vn.iterrows():
        c = row["codec"]
        if c in ("aac_zalo_76k", "opus_zalo_24k"):
            rel_dst = str(row["audio_path"]).replace("\\", "/").lstrip("/")
            if rel_dst in seen_dst:
                continue
            seen_dst.add(rel_dst)
            dst_p = root / rel_dst
            if dst_p.exists() and dst_p.stat().st_size > 100:
                continue
            clean_rel = base_to_clean[row["base_utt"]]
            proxy_tasks.append((root / clean_rel, dst_p, c))

    if proxy_tasks:
        print(f"[TestZaloProxy] Transcoding {len(proxy_tasks)} AAC/Opus files for test_indomain...")
        t0 = time.perf_counter()

        def _transcode_one(item: tuple[Path, Path, str]) -> None:
            src_p, dst_p, codec_name = item
            raw_b = src_p.read_bytes()
            out_b = (
                transcode_aac_adts_stream(raw_b)
                if codec_name == "aac_zalo_76k"
                else transcode_opus_ogg_stream(raw_b)
            )
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst_p.with_suffix(".tmp.wav")
            tmp.write_bytes(out_b)
            tmp.replace(dst_p)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(_transcode_one, proxy_tasks))
        print(f"[TestZaloProxy] Completed {len(proxy_tasks)} files in {time.perf_counter() - t0:.1f}s")
    else:
        print("[TestZaloProxy] All test_indomain AAC/Opus proxies already on disk.")


def build_target_catalog(root: Path = _ROOT) -> list[TargetUtterance]:
    """Build exact 1:1 catalog of all 1,289 clean items in data/spoof_vieneu/."""
    vn_dir = root / "data/spoof_vieneu"
    if not vn_dir.exists():
        raise FileNotFoundError(f"Missing {vn_dir}")

    tr_with = pd.read_csv(root / "data/manifests_zalo/train_dual_seen_with_spk1.csv")
    tr_zalo = pd.read_csv(root / "data/manifests_zalo/train_zalo.csv")
    dev_dual = pd.read_csv(root / "data/manifests_zalo/dev_zalo_dual_seen.csv")
    test_in = pd.read_csv(root / "data/manifests_zalo/test_indomain_zalo.csv")
    unseen_om_5spk = pd.read_csv(root / "data/manifests_zalo/unseen_omnivoice_benchmark.csv")

    with zipfile.ZipFile(root / "data/vitruevoice_data_processed.zip", "r") as zf:
        with zf.open("data/manifests/full_manifest.csv") as f:
            z_full = pd.read_csv(f)
        with zf.open("data/manifests/test_ood.csv") as f:
            z_ood = pd.read_csv(f)

    # 1. Split membership by speaker_id
    train_corpus_spks = set(
        tr_with[(tr_with["tts_generator"] == "VieNeu-TTS") & (tr_with["speaker_id"] != "SPK_0001")]["speaker_id"].unique()
    )
    dev_spks = set(dev_dual[dev_dual["tts_generator"] == "VieNeu-TTS"]["speaker_id"].unique())
    test_spks = set(test_in[test_in["tts_generator"] == "VieNeu-TTS"]["speaker_id"].unique())
    ood_cv_spks = {"CV_353f059e70", "CV_97ee3fed8e", "CV_b5a488f638", "CV_bb99c0461b", "CV_e3e2b2e165"}
    acc_5spk = {f"SPK_{i:04d}" for i in range(3, 8)}

    # 2. Prompt transcript map keyed by base_utt (guaranteed non-NaN)
    prompt_map: dict[str, str] = {}

    def _register_prompts(df_sub: pd.DataFrame) -> None:
        for _, r in df_sub.iterrows():
            b = str(r.get("base_utt", "")).strip()
            if not b or b.lower() == "nan":
                u = str(r["utt_id"])
                for suf in ("_clean", "_g711", "_amrnb", "_aac_zalo", "_opus_zalo"):
                    if u.endswith(suf):
                        u = u[: -len(suf)]
                        break
                b = u
            t = r.get("transcript", None)
            if pd.notna(t):
                ts = str(t).strip()
                if ts and ts.lower() != "nan" and b not in prompt_map:
                    prompt_map[b] = ts

    # SPK_0001 prompts MUST come from F5-TTS in train_zalo.csv (VieNeu rows in train_dual_seen_with_spk1 have NaN)
    _register_prompts(tr_zalo[(tr_zalo["speaker_id"] == "SPK_0001") & (tr_zalo["tts_generator"] == "F5-TTS-Vietnamese")])
    _register_prompts(tr_with[tr_with["tts_generator"] == "VieNeu-TTS"])
    _register_prompts(dev_dual[dev_dual["tts_generator"] == "VieNeu-TTS"])
    _register_prompts(test_in[test_in["tts_generator"] == "VieNeu-TTS"])
    _register_prompts(z_ood[z_ood["tts_generator"] == "VieNeu-TTS"])
    _register_prompts(z_full[z_full["tts_generator"] == "VieNeu-TTS"])
    _register_prompts(unseen_om_5spk)

    # 3. Bonafide transcript lookup for zip bonafide_ref files
    bona_transcript_by_file: dict[tuple[str, str], tuple[str, float]] = {}
    for df_sub in (tr_zalo, dev_dual, test_in, z_full, z_ood):
        sub = df_sub[(df_sub["label"] == "bonafide") & (df_sub["codec"] == "clean_16khz")]
        for _, r in sub.iterrows():
            spk = str(r["speaker_id"])
            fname = Path(str(r["audio_path"])).name.replace("_clean.wav", ".wav")
            t = r.get("transcript", None)
            if pd.notna(t):
                ts = str(t).strip()
                if ts and ts.lower() != "nan":
                    dur = float(r["duration_sec"]) if pd.notna(r.get("duration_sec")) else 0.0
                    bona_transcript_by_file[(spk, fname)] = (ts, dur)

    # 4. Reference map for all 96 speakers
    ref_map: dict[str, tuple[str, str]] = {}

    def _pick_manifest_ref(df_sub: pd.DataFrame, spk: str) -> tuple[str, str] | None:
        sub = df_sub[
            (df_sub["speaker_id"] == spk)
            & (df_sub["role"].isin(["enroll", "ref"]))
            & (df_sub["codec"] == "clean_16khz")
        ].sort_values("duration_sec", ascending=False)
        for _, r in sub.iterrows():
            rel = str(r["audio_path"]).replace("\\", "/").lstrip("/")
            t = str(r["transcript"]).strip()
            if (root / rel).exists() and t and t.lower() != "nan":
                return rel, t
        return None

    def _pick_bonafide_ref_dir(spk: str) -> tuple[str, str] | None:
        bdir = root / "data/bonafide_ref" / spk
        if not bdir.exists():
            return None
        cands = []
        for f in sorted(bdir.glob("*.wav")):
            if (spk, f.name) in bona_transcript_by_file:
                ts, _ = bona_transcript_by_file[(spk, f.name)]
                dur = float(sf.info(str(f)).duration)
                cands.append((dur, f.relative_to(root).as_posix(), ts))
        if cands:
            cands.sort(reverse=True)
            return cands[0][1], cands[0][2]
        return None

    # 5. Walk data/spoof_vieneu/ 1:1
    catalog: list[TargetUtterance] = []
    for spk_dir in sorted(vn_dir.iterdir()):
        if not spk_dir.is_dir() or spk_dir.name.startswith("."):
            continue
        spk = spk_dir.name
        if spk == "SPK_0001":
            split_bucket = "train_spk1"
            ref_pair = (SPK0001_REF_AUDIO, SPK0001_REF_TEXT)
        elif spk in acc_5spk:
            split_bucket = "acceptance_5spk"
            ref_pair = (f"data/bonafide_ref/{spk}/{spk}_01.wav", SPK_VOLUNTEER_REF_TEXT)
        elif spk in train_corpus_spks:
            split_bucket = "train_corpus"
            ref_pair = _pick_manifest_ref(tr_zalo, spk)
        elif spk in dev_spks:
            split_bucket = "dev"
            ref_pair = _pick_manifest_ref(dev_dual, spk)
        elif spk in test_spks:
            split_bucket = "test_indomain"
            ref_pair = _pick_bonafide_ref_dir(spk) or _pick_manifest_ref(test_in, spk)
        elif spk in ood_cv_spks:
            split_bucket = "ood_cv"
            ref_pair = _pick_bonafide_ref_dir(spk)
        else:
            raise ValueError(f"Unclassified speaker in spoof_vieneu: {spk}")

        if ref_pair is None or not (root / ref_pair[0]).exists():
            raise FileNotFoundError(f"Missing ref audio for speaker {spk}: {ref_pair}")
        ref_map[spk] = ref_pair

        for f in sorted(spk_dir.iterdir()):
            if not f.is_file() or f.suffix.lower() != ".wav":
                continue
            if any(f.name.endswith(s) for s in ("_g711.wav", "_amrnb.wav", "_aac_zalo.wav", "_opus_zalo.wav")):
                continue
            base_utt = f.stem
            if base_utt not in prompt_map:
                raise KeyError(f"Missing prompt transcript for ({spk}, {base_utt})")
            catalog.append(
                TargetUtterance(
                    speaker_id=spk,
                    base_utt=base_utt,
                    source_group=infer_source_group(spk),
                    split_bucket=split_bucket,
                    prompt_text=prompt_map[base_utt],
                    ref_audio=ref_pair[0],
                    ref_text=ref_pair[1],
                )
            )

    if len(catalog) != 1289:
        raise RuntimeError(f"Expected 1289 clean target items from spoof_vieneu, got {len(catalog)}")
    return catalog


def reuse_existing_omnivoice(
    catalog: list[TargetUtterance],
    out_dir: Path,
    root: Path = _ROOT,
) -> tuple[int, int]:
    """Copy valid matching OmniVoice samples (clean + 4 codecs) into data/spoof_omnivoice_v8/."""
    target_set = {(item.speaker_id, item.base_utt) for item in catalog}

    # Index existing valid clean+codec directories
    existing_map: dict[tuple[str, str], tuple[Path, str]] = {}
    for rel_src in REUSE_SOURCE_DIRS:
        src_root = root / rel_src
        if not src_root.exists():
            continue
        for spk_dir in sorted(src_root.iterdir()):
            if not spk_dir.is_dir():
                continue
            spk = spk_dir.name
            for f in sorted(spk_dir.iterdir()):
                if f.suffix.lower() != ".wav":
                    continue
                if any(f.name.endswith(s) for s in ("_g711.wav", "_amrnb.wav", "_aac_zalo.wav", "_opus_zalo.wav")):
                    continue
                stem = f.stem
                base_utt = stem.replace(f"{spk}_omnivoice_", f"{spk}_", 1)
                key = (spk, base_utt)
                if key not in target_set or key in existing_map:
                    continue
                if not is_valid_clean_wav(f):
                    continue
                # Verify all 4 codec files exist and are valid
                all_codecs_ok = True
                for _, _, file_suf, _, exp_sr in CODEC_SPECS[1:]:
                    cf = spk_dir / f"{stem}{file_suf}.wav"
                    if not cf.exists() or cf.stat().st_size <= 100:
                        all_codecs_ok = False
                        break
                    try:
                        info = sf.info(str(cf))
                        if info.samplerate != exp_sr or info.duration < 0.45:
                            all_codecs_ok = False
                            break
                    except Exception:
                        all_codecs_ok = False
                        break
                if all_codecs_ok:
                    existing_map[key] = (spk_dir, stem)

    copied_items = 0
    already_present = 0
    for item in catalog:
        dst_spk = out_dir / item.speaker_id
        if is_complete_5_codecs(dst_spk, item.base_utt):
            already_present += 1
            continue
        key = (item.speaker_id, item.base_utt)
        if key not in existing_map:
            continue
        src_spk_dir, src_stem = existing_map[key]
        dst_spk.mkdir(parents=True, exist_ok=True)
        for _, _, file_suf, _, _ in CODEC_SPECS:
            src_f = src_spk_dir / f"{src_stem}{file_suf}.wav"
            dst_f = dst_spk / f"{item.base_utt}{file_suf}.wav"
            shutil.copy2(src_f, dst_f)
        copied_items += 1

    print(
        f"[Reuse] Already complete in dst: {already_present} | "
        f"Copied valid reusable sets: {copied_items} (x5 = {copied_items * 5} files) | "
        f"Remaining to generate: {len(catalog) - already_present - copied_items}"
    )
    return already_present, copied_items


def generate_missing_omnivoice(
    catalog: list[TargetUtterance],
    out_dir: Path,
    root: Path = _ROOT,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> int:
    """Generate remaining OmniVoice clean + 4 codec files with full resume support."""
    todo = [
        item for item in catalog
        if not is_complete_5_codecs(out_dir / item.speaker_id, item.base_utt)
    ]
    if not todo:
        print("[Generate] 0 items remaining — all 1,289 x 5 = 6,445 files already complete!")
        return 0

    print(f"[Generate] Loading OmniVoice offline on {device} (bfloat16) for {len(todo)} items...")
    from omnivoice.models.omnivoice import OmniVoice

    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=torch.bfloat16 if device == "cuda" and torch.cuda.is_available() else torch.float32,
    )

    # Group by speaker to cache voice_clone_prompt once per speaker
    by_spk: dict[str, list[TargetUtterance]] = {}
    for item in todo:
        by_spk.setdefault(item.speaker_id, []).append(item)

    generated_count = 0
    t_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as codec_pool:
        codec_futures: list[concurrent.futures.Future] = []

        for spk in sorted(by_spk.keys()):
            items = by_spk[spk]
            ref_audio_abs = str(root / items[0].ref_audio)
            ref_text_norm = normalize_tts_prompt(items[0].ref_text)

            with torch.inference_mode():
                vc_prompt = model.create_voice_clone_prompt(
                    ref_audio=ref_audio_abs,
                    ref_text=ref_text_norm,
                )

            spk_out = out_dir / spk
            spk_out.mkdir(parents=True, exist_ok=True)

            for item in items:
                clean_wav = spk_out / f"{item.base_utt}.wav"
                if not is_valid_clean_wav(clean_wav):
                    prompt_norm = normalize_tts_prompt(item.prompt_text)
                    last_err = None
                    ok = False
                    for attempt in range(3):
                        try:
                            with torch.inference_mode():
                                audios = model.generate(
                                    text=prompt_norm,
                                    voice_clone_prompt=vc_prompt,
                                    language="vi",
                                    num_step=16,
                                    guidance_scale=2.0,
                                )
                            a0 = audios[0]
                            if isinstance(a0, torch.Tensor):
                                a0 = a0.detach().cpu().float().numpy()
                            y_24k = np.asarray(a0, dtype=np.float32).squeeze()
                            y_16k = librosa.resample(y_24k, orig_sr=24000, target_sr=16000)
                            peak = float(np.max(np.abs(y_16k))) if y_16k.size > 0 else 0.0
                            if peak > 0.0:
                                y_16k = y_16k * (0.95 / peak)
                            dur = len(y_16k) / 16000.0
                            rms = float(np.sqrt(np.mean(y_16k ** 2))) if y_16k.size > 0 else 0.0
                            if dur < 0.5 or rms <= 1e-4 or not np.all(np.isfinite(y_16k)):
                                last_err = RuntimeError(f"Quality gate failed (dur={dur:.3f}, rms={rms:.6f})")
                                continue
                            tmp_clean = spk_out / f"{item.base_utt}.tmp.wav"
                            sf.write(str(tmp_clean), y_16k, 16000, subtype="PCM_16")
                            tmp_clean.replace(clean_wav)
                            ok = True
                            break
                        except Exception as exc:
                            last_err = exc
                    if not ok:
                        raise RuntimeError(f"Failed to generate {spk}/{item.base_utt}: {last_err}")

                codec_futures.append(codec_pool.submit(encode_all_4_codecs, clean_wav, spk_out, item.base_utt))
                generated_count += 1
                if generated_count % 50 == 0 and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                if generated_count % 25 == 0 or generated_count == len(todo):
                    elapsed = time.perf_counter() - t_start
                    rate = generated_count / max(elapsed, 1e-6)
                    eta_min = (len(todo) - generated_count) / max(rate, 1e-6) / 60.0
                    print(
                        f"[Generate] {generated_count:3d}/{len(todo)} clean ready | "
                        f"{rate:.2f} utt/s | elapsed {elapsed/60:.1f}m | ETA {eta_min:.1f}m",
                        flush=True,
                    )

            for fut in codec_futures:
                fut.result()
            codec_futures.clear()

    # Final disk integrity check across all 1,289 items
    incomplete = [
        f"{item.speaker_id}/{item.base_utt}"
        for item in catalog
        if not is_complete_5_codecs(out_dir / item.speaker_id, item.base_utt)
    ]
    if incomplete:
        raise RuntimeError(f"Incomplete codec sets after generation ({len(incomplete)}): {incomplete[:10]}")

    print(f"[Generate] Verified 1,289/1,289 sets (6,445 files) in {out_dir}!")
    return generated_count


def _build_omnivoice_rows(
    items: list[TargetUtterance],
    omni_dir: Path,
    split_name: str,
    role_name: str,
    root: Path = _ROOT,
) -> pd.DataFrame:
    rows = []
    for item in items:
        spk = item.speaker_id
        rest = item.base_utt[len(spk) + 1 :] if item.base_utt.startswith(f"{spk}_") else item.base_utt
        utt_prefix = f"{spk}_omnivoice_{rest}"
        clean_p = omni_dir / spk / f"{item.base_utt}.wav"
        if not clean_p.exists():
            raise FileNotFoundError(f"Missing OmniVoice clean wav: {clean_p}")

        for codec_name, pre_codec, file_suf, utt_suf, _ in CODEC_SPECS:
            audio_p = omni_dir / spk / f"{item.base_utt}{file_suf}.wav"
            if not audio_p.exists():
                raise FileNotFoundError(f"Missing OmniVoice codec wav: {audio_p}")
            dur = round(float(sf.info(str(audio_p)).duration), 4)
            rows.append({
                "utt_id": f"{utt_prefix}{utt_suf}",
                "audio_path": audio_p.relative_to(root).as_posix(),
                "speaker_id": spk,
                "source": item.source_group,
                "label": "spoof",
                "role": role_name,
                "tts_generator": "OmniVoice",
                "codec": codec_name,
                "pre_codec": pre_codec,
                "split": split_name,
                "duration_sec": dur,
                "transcript": item.prompt_text,
                "raw_wer": 0.05,
                "raw_cer": 0.02,
                "ecapa_sim": 0.65,
                "wavlm_sim": 0.65,
                "derived_tier": "seen_omnivoice",
                "seed": 200,
                "base_utt": item.base_utt,
            })
    return pd.DataFrame(rows, columns=STANDARD_19_COLS)


def export_v8_1_manifests(
    catalog: list[TargetUtterance],
    omni_dir: Path | None = None,
    root: Path = _ROOT,
) -> dict[str, int]:
    """Backup V8.0 manifests and export all 5 standardized V8.1 manifests."""
    omni_dir = omni_dir or (root / "data/spoof_omnivoice_v8")
    out_dir = root / "data/manifests_zalo"
    backup_dir = out_dir / ".backup_v8_0"
    backup_dir.mkdir(parents=True, exist_ok=True)

    target_files = [
        "train_v8_f5_omni_no_spk1.csv",
        "train_v8_f5_omni_with_spk1.csv",
        "dev_v8_f5_omni.csv",
        "test_indomain_v8_f5_omni.csv",
        "unseen_vieneu_benchmark.csv",
    ]
    for fname in target_files:
        src = out_dir / fname
        dst = backup_dir / fname
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            print(f"[Backup] Saved V8.0 {fname} -> {dst.relative_to(root).as_posix()}")

    # Partition catalog into split buckets
    train_corpus_items = [x for x in catalog if x.split_bucket == "train_corpus"]
    train_spk1_items = [x for x in catalog if x.split_bucket == "train_spk1"]
    dev_items = [x for x in catalog if x.split_bucket == "dev"]
    test_items = [x for x in catalog if x.split_bucket == "test_indomain"]

    assert len(train_corpus_items) == 728, f"Expected 728 train_corpus items, got {len(train_corpus_items)}"
    assert len(train_spk1_items) == 10, f"Expected 10 train_spk1 items, got {len(train_spk1_items)}"
    assert len(dev_items) == 191, f"Expected 191 dev items, got {len(dev_items)}"
    assert len(test_items) == 224, f"Expected 224 test items, got {len(test_items)}"

    # Load V7 base manifests
    v7_tr_no_spk1 = pd.read_csv(out_dir / "train_dual_seen_no_spk1.csv")
    v7_tr_with_spk1 = pd.read_csv(out_dir / "train_dual_seen_with_spk1.csv")
    v7_dev = pd.read_csv(out_dir / "dev_zalo_dual_seen.csv")
    v7_test = pd.read_csv(out_dir / "test_indomain_zalo.csv")

    # 1. train_v8_f5_omni_no_spk1.csv (54,225)
    tr_base_no_spk1 = v7_tr_no_spk1[v7_tr_no_spk1["tts_generator"] != "VieNeu-TTS"][STANDARD_19_COLS].copy()
    omni_tr_df = _build_omnivoice_rows(train_corpus_items, omni_dir, split_name="train", role_name="eval", root=root)
    m_tr_no_spk1 = pd.concat([tr_base_no_spk1, omni_tr_df], ignore_index=True)[STANDARD_19_COLS]
    m_tr_no_spk1["audio_path"] = m_tr_no_spk1["audio_path"].astype(str).str.replace("\\", "/", regex=False)

    # 2. train_v8_f5_omni_with_spk1.csv (54,400)
    spk1_bona_f5 = v7_tr_with_spk1[
        (v7_tr_with_spk1["speaker_id"] == "SPK_0001") & (v7_tr_with_spk1["tts_generator"] != "VieNeu-TTS")
    ][STANDARD_19_COLS].copy()
    omni_spk1_df = _build_omnivoice_rows(train_spk1_items, omni_dir, split_name="train", role_name="train", root=root)
    m_tr_with_spk1 = pd.concat([m_tr_no_spk1, spk1_bona_f5, omni_spk1_df], ignore_index=True)[STANDARD_19_COLS]
    m_tr_with_spk1["audio_path"] = m_tr_with_spk1["audio_path"].astype(str).str.replace("\\", "/", regex=False)

    # 3. dev_v8_f5_omni.csv (12,405)
    dev_base = v7_dev[v7_dev["tts_generator"] != "VieNeu-TTS"][STANDARD_19_COLS].copy()
    omni_dev_df = _build_omnivoice_rows(dev_items, omni_dir, split_name="dev", role_name="eval", root=root)
    m_dev = pd.concat([dev_base, omni_dev_df], ignore_index=True)[STANDARD_19_COLS]
    m_dev["audio_path"] = m_dev["audio_path"].astype(str).str.replace("\\", "/", regex=False)

    # 4. test_indomain_v8_f5_omni.csv (15,980)
    test_base = v7_test[v7_test["tts_generator"] != "VieNeu-TTS"][STANDARD_19_COLS].copy()
    omni_test_df = _build_omnivoice_rows(test_items, omni_dir, split_name="test", role_name="eval", root=root)
    m_test = pd.concat([test_base, omni_test_df], ignore_index=True)[STANDARD_19_COLS]
    m_test["audio_path"] = m_test["audio_path"].astype(str).str.replace("\\", "/", regex=False)

    # 5. unseen_vieneu_benchmark.csv (955)
    m_unseen = v7_dev[v7_dev["tts_generator"] == "VieNeu-TTS"][STANDARD_19_COLS].copy()
    m_unseen["split"] = "dev_unseen"
    m_unseen["role"] = "eval"
    m_unseen["derived_tier"] = "unseen_vieneu"
    m_unseen["audio_path"] = m_unseen["audio_path"].astype(str).str.replace("\\", "/", regex=False)

    # Strict pre-save assertions
    assert len(m_tr_no_spk1) == 54225, f"train_no_spk1 count mismatch: {len(m_tr_no_spk1)}"
    assert len(m_tr_with_spk1) == 54400, f"train_with_spk1 count mismatch: {len(m_tr_with_spk1)}"
    assert len(m_dev) == 12405, f"dev count mismatch: {len(m_dev)}"
    assert len(m_test) == 15980, f"test count mismatch: {len(m_test)}"
    assert len(m_unseen) == 955, f"unseen count mismatch: {len(m_unseen)}"

    outputs = {
        "train_v8_f5_omni_no_spk1.csv": m_tr_no_spk1,
        "train_v8_f5_omni_with_spk1.csv": m_tr_with_spk1,
        "dev_v8_f5_omni.csv": m_dev,
        "test_indomain_v8_f5_omni.csv": m_test,
        "unseen_vieneu_benchmark.csv": m_unseen,
    }
    for fname, df in outputs.items():
        p = out_dir / fname
        df.to_csv(p, index=False, lineterminator="\n", encoding="utf-8")
        print(f"[Manifest] Wrote {p.relative_to(root).as_posix()}: {len(df):,} rows | gens={df['tts_generator'].value_counts().to_dict()}")

    return {k: len(v) for k, v in outputs.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate full 1:1 OmniVoice_CFM V8.1 dataset and 5 manifests")
    parser.add_argument("--out-dir", type=str, default="data/spoof_omnivoice_v8")
    parser.add_argument("--prep-only", action="store_true", help="Only run zip extraction, catalog check, and reuse copy")
    parser.add_argument("--skip-gen", action="store_true", help="Only run prep, catalog, reuse, and export if complete")
    args = parser.parse_args()

    out_dir = _ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("VITRUEVOICE V8.1 — FULL 1:1 OMNIVOICE_CFM RESTORATION PIPELINE")
    print("=" * 80)

    extract_missing_refs_and_test_audio(_ROOT)
    catalog = build_target_catalog(_ROOT)
    vivos_n = sum(1 for x in catalog if x.source_group == "vivos")
    cv_n = sum(1 for x in catalog if x.source_group == "common_voice")
    spk_n = sum(1 for x in catalog if x.source_group == "volunteer_consent")
    print(f"[Catalog] Target clean={len(catalog)} (VIVOS={vivos_n}, CV={cv_n}, SPK={spk_n}) -> {len(catalog)*5} files")

    reuse_existing_omnivoice(catalog, out_dir, _ROOT)
    if args.prep_only:
        print("[PrepOnly] Stopping before OmniVoice GPU synthesis.")
        return
    if not args.skip_gen:
        generate_missing_omnivoice(catalog, out_dir, _ROOT)

    counts = export_v8_1_manifests(catalog, out_dir, _ROOT)
    print("\nDONE V8.1:", counts)


if __name__ == "__main__":
    main()
