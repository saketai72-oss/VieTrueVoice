#!/usr/bin/env python3
"""Trích xuất và lưu bộ đệm đặc trưng FP16 từ ngõ ra encoder của mô hình SSL-AASIST.
Theo đặc tả SPEC_loso_exploratory_ablation.md (v1.1.0):
- Tapped tại: model.frontend.encoder.last_hidden_state (768 chiều, shape [199, 768])
- Trạng thái encoder: model.frontend.encoder.eval()
- Dữ liệu trích xuất:
  1. dev_zalo: Toàn bộ 11.450 mẫu từ data/manifests_zalo/dev_zalo.csv
  2. replay: 4.800 mẫu (2.400 bona + 2.400 spoof) từ train_zalo_49k.csv (seed 42)
  3. volunteers:
     - bona fide: 495 tệp (6 người x 5 codecs)
     - spoof F5-TTS: 425 tệp (6 người x 5 codecs)
     - spoof VieNeu-TTS: 425 tệp (6 người x 5 codecs, dùng cho H2 secondary metric)
  4. dev_spoof_offsets: 960 mẫu spoof Dev x 11 offsets (0.00 đến 0.50s)
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.eval_ssl_aasist import load_model
from src.preprocessing.audio_loader import load_audio
from src.training.dataset import fit_length


def extract_features_batch(wavs_np, model, device):
    """Trích xuất batch âm thanh đã padding 64k mẫu qua encoder ở chế độ eval."""
    # wavs_np: numpy array (B, 64000)
    wav = torch.from_numpy(wavs_np).float().to(device)
    # Chuẩn hóa chuẩn STUBBORN_FACT
    wav_norm = (wav - wav.mean(1, keepdim=True)) / torch.sqrt(
        wav.var(1, keepdim=True, unbiased=False) + 1e-7
    )
    with torch.no_grad():
        h = model.frontend.encoder(wav_norm).last_hidden_state  # (B, 199, 768)
        # Chuyển sang FP16 và đưa về CPU để lưu đệm
        return h.half().cpu()


def cache_file_list(file_records, model, device, out_path, batch_size=32, desc=""):
    """Trích xuất và lưu danh sách file thành file tensor duy nhất kèm metadata."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        print(f"⏩ Đã tồn tại cache: {out_path} ({out_path.stat().st_size / (1024**2):.1f} MB), bỏ qua.")
        return

    print(f"\n📦 Bắt đầu trích xuất [{desc}] ({len(file_records)} mẫu)...")
    t0 = time.time()
    rng = np.random.default_rng(0)

    all_features = []
    metadata = []

    batch_wavs = []
    batch_meta = []

    for idx, rec in enumerate(file_records):
        path = rec["audio_path"]
        offset_sec = rec.get("offset_sec", 0.0)
        try:
            y = load_audio(path, target_sr=16000)
            if offset_sec > 0:
                start_idx = int(offset_sec * 16000)
                y = y[start_idx:] if start_idx < len(y) else y
            t = fit_length(y, 64000, train=False, rng=rng)
        except Exception as e:
            print(f"⚠️ Lỗi đọc file {path}: {e}")
            t = np.zeros(64000, dtype=np.float32)

        batch_wavs.append(t)
        batch_meta.append(rec)

        if len(batch_wavs) == batch_size or (idx + 1) == len(file_records):
            wavs_np = np.stack(batch_wavs, axis=0)
            feats = extract_features_batch(wavs_np, model, device)
            all_features.append(feats)
            metadata.extend(batch_meta)
            batch_wavs = []
            batch_meta = []

            if (idx + 1) % 500 == 0 or (idx + 1) == len(file_records):
                dt = time.time() - t0
                rate = (idx + 1) / max(dt, 0.001)
                print(f"   Trích xuất: {idx + 1}/{len(file_records)} ({((idx + 1)/len(file_records))*100:.1f}%) | {rate:.1f} mẫu/s")

    all_features = torch.cat(all_features, dim=0)  # (N, 199, 768) FP16
    torch.save({"features": all_features, "metadata": metadata}, out_path)
    dt = time.time() - t0
    size_mb = out_path.stat().st_size / (1024**2)
    print(f"✅ Hoàn tất [{desc}]: {len(metadata)} mẫu -> {out_path} ({size_mb:.1f} MB, {dt:.1f}s)")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 80)
    print("🚀 BẮT ĐẦU TRÍCH XUẤT BỘ ĐỆM ĐẶC TRƯNG FP16 (LOSO 4 FOLDS SPEC v1.1.0)")
    print(f"   Thiết bị: {device}")
    print("=" * 80)

    ckpt_path = "out/best_model_B_zalo.pt"
    model, _ = load_model(ckpt_path, device=device)
    model.eval()
    model.frontend.encoder.eval()

    cache_dir = Path("data/cache_loso_fp16")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 1. Dev Zalo (11.450 mẫu)
    dev_csv = Path("data/manifests_zalo/dev_zalo.csv")
    df_dev = pd.read_csv(dev_csv)
    dev_records = []
    for _, r in df_dev.iterrows():
        lbl = 1 if r["label"] == "bonafide" else 0
        dev_records.append({
            "audio_path": r["audio_path"],
            "label": lbl,
            "speaker": r.get("speaker_id", "unknown"),
            "codec": r.get("codec", "clean"),
            "base_utt": r.get("base_utt", Path(r["audio_path"]).stem),
            "offset_sec": 0.0,
        })
    # Chia dev thành 4 parts để tránh file quá lớn và nạp nhẹ nhàng
    n_total = len(dev_records)
    chunk_size = (n_total + 3) // 4
    for p_idx in range(4):
        p_records = dev_records[p_idx * chunk_size : (p_idx + 1) * chunk_size]
        cache_file_list(
            p_records, model, device,
            cache_dir / f"dev_zalo_part{p_idx}.pt",
            batch_size=32,
            desc=f"Dev Zalo Part {p_idx+1}/4"
        )

    # 2. Replay Buffer (2.400 bona + 2.400 spoof từ train_zalo_49k.csv)
    train_csv = Path("data/manifests_zalo/train_zalo_49k.csv")
    df_train = pd.read_csv(train_csv)
    df_train_bona = df_train[df_train["label"] == "bonafide"].sample(n=2400, random_state=42)
    df_train_spoof = df_train[df_train["label"] == "spoof"].sample(n=2400, random_state=42)
    df_replay = pd.concat([df_train_bona, df_train_spoof]).sample(frac=1.0, random_state=42).reset_index(drop=True)
    replay_records = []
    for _, r in df_replay.iterrows():
        lbl = 1 if r["label"] == "bonafide" else 0
        replay_records.append({
            "audio_path": r["audio_path"],
            "label": lbl,
            "speaker": r.get("speaker_id", "train_spk"),
            "codec": r.get("codec", "unknown"),
            "base_utt": r.get("base_utt", Path(r["audio_path"]).stem),
            "offset_sec": 0.0,
        })
    cache_file_list(
        replay_records, model, device,
        cache_dir / "replay_buffer.pt",
        batch_size=32,
        desc="Replay Buffer (4.800 mẫu)"
    )

    # 3. Volunteers
    # Tình nguyện viên: bona fide, spoof F5-TTS, spoof VieNeu-TTS
    vol_speakers = ["SPK_0001", "SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    vol_records = []
    for spk in vol_speakers:
        # Bona fide
        raw_files = sorted(Path(f"data/raw/{spk}").glob("*.wav"))
        for p in raw_files:
            stem = p.stem
            # Nhận diện codec từ stem
            codec = "clean"
            for c in ["g711", "amr", "aac_zalo", "opus_zalo"]:
                if f"_{c}" in stem:
                    codec = c
                    break
            base_utt = stem.split(f"_{codec}")[0] if codec != "clean" else stem
            vol_records.append({
                "audio_path": str(p),
                "label": 1,
                "speaker": spk,
                "codec": codec,
                "base_utt": base_utt,
                "kind": "bonafide",
                "offset_sec": 0.0,
            })

        # Spoof F5-TTS
        f5_files = sorted(Path(f"data/spoof_f5tts/{spk}").glob("*.wav")) if Path(f"data/spoof_f5tts/{spk}").exists() else []
        for p in f5_files:
            stem = p.stem
            codec = "clean"
            for c in ["g711", "amr", "aac_zalo", "opus_zalo"]:
                if f"_{c}" in stem:
                    codec = c
                    break
            base_utt = stem.split(f"_{codec}")[0] if codec != "clean" else stem
            vol_records.append({
                "audio_path": str(p),
                "label": 0,
                "speaker": spk,
                "codec": codec,
                "base_utt": base_utt,
                "kind": "spoof_f5tts",
                "offset_sec": 0.0,
            })

        # Spoof VieNeu-TTS
        vn_files = sorted(Path(f"data/spoof_vieneu/{spk}").glob("*.wav")) if Path(f"data/spoof_vieneu/{spk}").exists() else []
        for p in vn_files:
            stem = p.stem
            codec = "clean"
            for c in ["g711", "amr", "aac_zalo", "opus_zalo"]:
                if f"_{c}" in stem:
                    codec = c
                    break
            base_utt = stem.split(f"_{codec}")[0] if codec != "clean" else stem
            vol_records.append({
                "audio_path": str(p),
                "label": 0,
                "speaker": spk,
                "codec": codec,
                "base_utt": base_utt,
                "kind": "spoof_vieneu",
                "offset_sec": 0.0,
            })

    cache_file_list(
        vol_records, model, device,
        cache_dir / "volunteers.pt",
        batch_size=32,
        desc="Volunteers (Bona, F5, VieNeu)"
    )

    # 4. Dev Spoof with 11 Offsets (cho điều kiện APCER worst-case)
    df_dev_spoof = df_dev[df_dev["label"] == "spoof"].reset_index(drop=True)
    offsets = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    dev_spoof_offset_records = []
    for _, r in df_dev_spoof.iterrows():
        for off_s in offsets:
            dev_spoof_offset_records.append({
                "audio_path": r["audio_path"],
                "label": 0,
                "speaker": r.get("speaker_id", "unknown"),
                "codec": r.get("codec", "clean"),
                "base_utt": r.get("base_utt", Path(r["audio_path"]).stem),
                "offset_sec": off_s,
            })
    # Chia thành 3 parts
    n_off = len(dev_spoof_offset_records)
    chunk_off = (n_off + 2) // 3
    for p_idx in range(3):
        p_records = dev_spoof_offset_records[p_idx * chunk_off : (p_idx + 1) * chunk_off]
        cache_file_list(
            p_records, model, device,
            cache_dir / f"dev_spoof_offsets_part{p_idx}.pt",
            batch_size=32,
            desc=f"Dev Spoof Offsets Part {p_idx+1}/3"
        )

    print("\n🎉 TOÀN BỘ BỘ ĐỆM ĐẶC TRƯNG FP16 ĐÃ ĐƯỢC TRÍCH XUẤT VÀ LƯU THÀNH CÔNG!")


if __name__ == "__main__":
    main()
