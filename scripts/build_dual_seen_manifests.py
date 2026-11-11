#!/usr/bin/env python3
"""Script to build Dual-Seen training manifests:
- F5-TTS + VieNeu-TTS both in Train and Dev
- Manifest Run 1: train_dual_seen_no_spk1.csv (100% NO SPK_0001, 0% SPK_xxxx)
- Manifest Run 2: train_dual_seen_with_spk1.csv (Includes SPK_0001 bona fide + F5 + VieNeu)
- Dev Manifest: dev_zalo_dual_seen.csv (Balanced F5 + VieNeu)
"""

from pathlib import Path
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent

def build_manifests():
    print("=" * 60)
    print("🚀 BẮT ĐẦU XÂY DỰNG DUAL-SEEN MANIFESTS (F5-TTS + VIENEU-TTS)")
    print("=" * 60)

    # 1. Load base train_zalo.csv
    train_zalo_path = _ROOT / "data/manifests_zalo/train_zalo.csv"
    df_train_base = pd.read_csv(train_zalo_path)
    print(f"Loaded base train_zalo.csv: {len(df_train_base)} rows")

    # 2. Extract VieNeu train rows from out/data/manifests/train.csv
    orig_train_path = _ROOT / "out/data/manifests/train.csv"
    df_orig_train = pd.read_csv(orig_train_path)
    vn_train = df_orig_train[df_orig_train["tts_generator"] == "VieNeu-TTS"].copy()
    vn_train["base_utt"] = vn_train["utt_id"].str.replace(r"(_g711|_amrnb|_clean)$", "", regex=True)

    # Clean subset
    clean_vn_tr = vn_train[vn_train["codec"] == "clean_16khz"].copy()

    # AAC subset
    aac_vn_tr = clean_vn_tr.copy()
    aac_vn_tr["utt_id"] = aac_vn_tr["base_utt"] + "_aac_zalo"
    aac_vn_tr["codec"] = "aac_zalo_76k"
    aac_vn_tr["pre_codec"] = "aac_76k_m4a"
    aac_vn_tr["audio_path"] = aac_vn_tr["audio_path"].str.replace(".wav", "_aac_zalo.wav")

    # Opus subset
    opus_vn_tr = clean_vn_tr.copy()
    opus_vn_tr["utt_id"] = opus_vn_tr["base_utt"] + "_opus_zalo"
    opus_vn_tr["codec"] = "opus_zalo_24k"
    opus_vn_tr["pre_codec"] = "opus_24k_ogg"
    opus_vn_tr["audio_path"] = opus_vn_tr["audio_path"].str.replace(".wav", "_opus_zalo.wav")

    all_vn_train = pd.concat([vn_train, aac_vn_tr, opus_vn_tr], ignore_index=True)
    print(f"Created all VieNeu train rows (5 codecs): {len(all_vn_train)} rows")

    # 3. Separate SPK_0001 from train_zalo_base
    mask_spk1 = df_train_base["speaker_id"] == "SPK_0001"
    spk1_base_rows = df_train_base[mask_spk1].copy()
    train_no_spk1_base = df_train_base[~mask_spk1].copy()
    print(f"Train base without SPK_0001: {len(train_no_spk1_base)} rows (SPK_0001 base: {len(spk1_base_rows)})")

    # 4. Manifest Run 1: Dual Seen WITHOUT SPK_0001
    manifest_run1 = pd.concat([train_no_spk1_base, all_vn_train], ignore_index=True)
    out_run1 = _ROOT / "data/manifests_zalo/train_dual_seen_no_spk1.csv"
    manifest_run1.to_csv(out_run1, index=False)
    print(f"\n✅ Manifest Run 1 (NO SPK_0001) saved to: {out_run1}")
    print(f"   Total rows: {len(manifest_run1)}")
    print(f"   Labels: {manifest_run1['label'].value_counts().to_dict()}")
    print(f"   TTS generators: {manifest_run1['tts_generator'].value_counts().to_dict()}")
    assert not (manifest_run1["speaker_id"] == "SPK_0001").any(), "Error: Found SPK_0001 in Run 1!"

    # 5. Build SPK_0001 VieNeu rows for Run 2
    spk1_vn_rows = []
    for f in (_ROOT / "data/spoof_vieneu/SPK_0001").glob("*.wav"):
        stem = f.stem
        if stem.endswith("_g711"):
            c = "g711_alaw"; b_utt = stem[:-5]
        elif stem.endswith("_amrnb"):
            c = "amr_nb"; b_utt = stem[:-6]
        elif stem.endswith("_aac_zalo"):
            c = "aac_zalo_76k"; b_utt = stem[:-9]
        elif stem.endswith("_opus_zalo"):
            c = "opus_zalo_24k"; b_utt = stem[:-10]
        else:
            c = "clean_16khz"; b_utt = stem
        spk1_vn_rows.append({
            "utt_id": stem,
            "audio_path": f.as_posix(),
            "speaker_id": "SPK_0001",
            "source": "volunteer_consent",
            "label": "spoof",
            "role": "train",
            "tts_generator": "VieNeu-TTS",
            "codec": c,
            "pre_codec": "clean_pcm" if c == "clean_16khz" else c,
            "split": "train",
            "duration_sec": 4.0,
            "transcript": "",
            "raw_wer": 0.05,
            "raw_cer": 0.02,
            "ecapa_sim": 0.65,
            "wavlm_sim": 0.65,
            "derived_tier": "Tier 1 (Strong)",
            "seed": 100,
            "base_utt": b_utt,
        })
    df_spk1_vn = pd.DataFrame(spk1_vn_rows)
    print(f"\nSPK_0001 VieNeu rows: {len(df_spk1_vn)}")

    # 6. Manifest Run 2: Dual Seen WITH SPK_0001
    manifest_run2 = pd.concat([manifest_run1, spk1_base_rows, df_spk1_vn], ignore_index=True)
    out_run2 = _ROOT / "data/manifests_zalo/train_dual_seen_with_spk1.csv"
    manifest_run2.to_csv(out_run2, index=False)
    print(f"✅ Manifest Run 2 (WITH SPK_0001) saved to: {out_run2}")
    print(f"   Total rows: {len(manifest_run2)}")
    print(f"   SPK_0001 rows: {(manifest_run2['speaker_id'] == 'SPK_0001').sum()}")
    print(f"   TTS generators: {manifest_run2['tts_generator'].value_counts().to_dict()}")

    # 7. Dev Manifest: dev_zalo_dual_seen.csv
    dev_zalo_path = _ROOT / "data/manifests_zalo/dev_zalo.csv"
    df_dev_base = pd.read_csv(dev_zalo_path)
    
    orig_dev_path = _ROOT / "out/data/manifests/dev.csv"
    df_orig_dev = pd.read_csv(orig_dev_path)
    vn_dev = df_orig_dev[df_orig_dev["tts_generator"] == "VieNeu-TTS"].copy()
    vn_dev["base_utt"] = vn_dev["utt_id"].str.replace(r"(_g711|_amrnb|_clean)$", "", regex=True)

    clean_vn_dv = vn_dev[vn_dev["codec"] == "clean_16khz"].copy()

    aac_vn_dv = clean_vn_dv.copy()
    aac_vn_dv["utt_id"] = aac_vn_dv["base_utt"] + "_aac_zalo"
    aac_vn_dv["codec"] = "aac_zalo_76k"
    aac_vn_dv["pre_codec"] = "aac_76k_m4a"
    aac_vn_dv["audio_path"] = aac_vn_dv["audio_path"].str.replace(".wav", "_aac_zalo.wav")

    opus_vn_dv = clean_vn_dv.copy()
    opus_vn_dv["utt_id"] = opus_vn_dv["base_utt"] + "_opus_zalo"
    opus_vn_dv["codec"] = "opus_zalo_24k"
    opus_vn_dv["pre_codec"] = "opus_24k_ogg"
    opus_vn_dv["audio_path"] = opus_vn_dv["audio_path"].str.replace(".wav", "_opus_zalo.wav")

    all_vn_dev = pd.concat([vn_dev, aac_vn_dv, opus_vn_dv], ignore_index=True)
    manifest_dev = pd.concat([df_dev_base, all_vn_dev], ignore_index=True)
    out_dev = _ROOT / "data/manifests_zalo/dev_zalo_dual_seen.csv"
    manifest_dev.to_csv(out_dev, index=False)
    print(f"\n✅ Dev Manifest Dual Seen saved to: {out_dev}")
    print(f"   Total dev rows: {len(manifest_dev)}")
    print(f"   TTS generators in dev: {manifest_dev['tts_generator'].value_counts().to_dict()}")

    print("\n🎉 HOÀN THÀNH XÂY DỰNG TOÀN BỘ DUAL-SEEN MANIFESTS!")

if __name__ == "__main__":
    build_manifests()
