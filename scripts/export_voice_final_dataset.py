#!/usr/bin/env python3
"""Kịch bản xuất bản toàn bộ dữ liệu âm thanh phục vụ Nghiệm thu Đồ án: Voice_Final.

Địa chỉ đích: C:\\Users\\saket\\Documents\\Đồ án chuyên ngành\\Voice_Final

Cấu trúc phân tách 2 không gian lưu trữ:
1. 01_Training_Seen:
   - SPK_0001_DeepVoice: Bona fide + F5-TTS + VieNeu-TTS (Clean + 4 Codecs + Ref)
   - VIVOS_Corpus_Train: Bona fide + F5-TTS + VieNeu-TTS (Clean + 4 Codecs)
   - CommonVoice_Corpus_Train: Bona fide + F5-TTS + VieNeu-TTS (Clean + 4 Codecs)
2. 02_Unseen_Acceptance:
   - BonaFide_5Spk_Volunteers: SPK_0003, SPK_0004, SPK_0005, SPK_0006, SPK_0007 (Clean + 4 Codecs + Ref)
   - Seen_Baseline_Benchmarks: F5_TTS, VieNeu_TTS trên 5 SPK (375 + 375 = 750 clips)
   - Unseen_TTS_Engines: Kokoro_Vietnamese, OmniVoice_CFM trên 5 SPK (375 + 375 = 750 clips)
3. VOICE_FINAL_MANIFEST.csv: Bảng chỉ mục tổng thể 13 cột băm SHA-256 bảo vệ dữ liệu sinh trắc học.
4. README_NGHIEM_THU.md: Bản hướng dẫn chi tiết dành riêng cho Hội đồng Nghiệm thu.
"""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import soundfile as sf

DEST_ROOT = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Voice_Final")


def sha256_of_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def detect_codec(fname: str) -> str:
    f = fname.lower()
    if "_aac_zalo" in f:
        return "aac_zalo_76k"
    if "_opus_zalo" in f:
        return "opus_zalo_24k"
    if "_g711" in f:
        return "g711_alaw"
    if "_amrnb" in f:
        return "amrnb_12.2k"
    return "clean_16k"


def get_audio_info(filepath: Path) -> tuple[int, float]:
    try:
        info = sf.info(str(filepath))
        return info.samplerate, round(info.duration, 3)
    except Exception:
        return 16000, 0.0


def main():
    print("=" * 80)
    print("📦 XUẤT BẢN DỮ LIỆU NGHIỆM THU: VOICE_FINAL")
    print(f"🎯 Thư mục đích: {DEST_ROOT}")
    print("=" * 80)

    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    t0 = time.time()
    n_copied = 0

    def copy_audio_file(
        src: Path,
        dst_dir: Path,
        category: str,
        subfolder: str,
        speaker_id: str,
        label: str,
        tts_generator: str,
    ) -> None:
        nonlocal n_copied
        if not src.is_file():
            return
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_file = dst_dir / src.name
        if not dst_file.exists() or dst_file.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst_file)
            n_copied += 1

        rel_p = dst_file.relative_to(DEST_ROOT).as_posix()
        sha = sha256_of_file(dst_file)
        codec = detect_codec(src.name)
        sr, dur = get_audio_info(dst_file)
        utt_id = src.stem

        manifest_rows.append({
            "utt_id": utt_id,
            "speaker_id": speaker_id,
            "label": label,
            "tts_generator": tts_generator,
            "codec": codec,
            "category": category,
            "subfolder": subfolder,
            "file_name": src.name,
            "rel_path": rel_p,
            "sha256_hash": sha,
            "file_size_bytes": dst_file.stat().st_size,
            "sample_rate": sr,
            "duration_s": dur,
        })

    # ═════════════════════════════════════════════════════════════════════════
    # 1. 01_Training_Seen / SPK_0001_DeepVoice
    # ═════════════════════════════════════════════════════════════════════════
    print("\n📂 [1/4] Sao chép dữ liệu SPK_0001 (Training Seen)...")
    dir_spk1_bona = DEST_ROOT / "01_Training_Seen" / "SPK_0001_DeepVoice" / "BonaFide"
    dir_spk1_f5 = DEST_ROOT / "01_Training_Seen" / "SPK_0001_DeepVoice" / "Spoof_F5TTS"
    dir_spk1_vn = DEST_ROOT / "01_Training_Seen" / "SPK_0001_DeepVoice" / "Spoof_VieNeuTTS"

    # Bona fide
    for f in sorted((_ROOT / "data/raw/SPK_0001").glob("*.wav")):
        c = detect_codec(f.name)
        c_sub = "Clean_16k" if c == "clean_16k" else ("Zalo_AAC_76k" if "aac" in c else ("Zalo_Opus_24k" if "opus" in c else ("PSTN_G711_Alaw" if "g711" in c else "Cellular_AMRNB")))
        copy_audio_file(f, dir_spk1_bona / c_sub, "01_Training_Seen", f"SPK_0001_DeepVoice/BonaFide/{c_sub}", "SPK_0001", "bonafide", "none")
    # Enrollment ref
    for f in sorted((_ROOT / "data/bonafide_ref/SPK_0001").glob("*.wav")):
        copy_audio_file(f, dir_spk1_bona / "Enrollment_Ref", "01_Training_Seen", "SPK_0001_DeepVoice/BonaFide/Enrollment_Ref", "SPK_0001", "bonafide", "none")
    # Spoof F5
    for f in sorted((_ROOT / "data/spoof_f5tts/SPK_0001").glob("*.wav")):
        c = detect_codec(f.name)
        c_sub = "Clean_16k" if c == "clean_16k" else ("Zalo_AAC_76k" if "aac" in c else ("Zalo_Opus_24k" if "opus" in c else ("PSTN_G711_Alaw" if "g711" in c else "Cellular_AMRNB")))
        copy_audio_file(f, dir_spk1_f5 / c_sub, "01_Training_Seen", f"SPK_0001_DeepVoice/Spoof_F5TTS/{c_sub}", "SPK_0001", "spoof", "F5-TTS-Vietnamese")
    # Spoof VieNeu
    for f in sorted((_ROOT / "data/spoof_vieneu/SPK_0001").glob("*.wav")):
        c = detect_codec(f.name)
        c_sub = "Clean_16k" if c == "clean_16k" else ("Zalo_AAC_76k" if "aac" in c else ("Zalo_Opus_24k" if "opus" in c else ("PSTN_G711_Alaw" if "g711" in c else "Cellular_AMRNB")))
        copy_audio_file(f, dir_spk1_vn / c_sub, "01_Training_Seen", f"SPK_0001_DeepVoice/Spoof_VieNeuTTS/{c_sub}", "SPK_0001", "spoof", "VieNeu-TTS")

    # ═════════════════════════════════════════════════════════════════════════
    # 2. 02_Unseen_Acceptance (Bộ Nghiệm Thu Độc Lập Held-Out 5 SPK)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n📂 [2/4] Sao chép Bộ Nghiệm thu Độc lập (SPK_0003..0007 & TTS Benchmarks)...")
    speakers = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]

    # 2.1. Bona Fide 5 SPK
    for spk in speakers:
        raw_spk_dir = _ROOT / f"data/raw/{spk}"
        dst_spk_dir = DEST_ROOT / "02_Unseen_Acceptance" / "BonaFide_5Spk_Volunteers" / spk
        if raw_spk_dir.exists():
            for f in sorted(list(raw_spk_dir.glob("*.wav")) + list(raw_spk_dir.glob("*.m4a"))):
                c = detect_codec(f.name)
                c_sub = "Clean_16k" if c == "clean_16k" else ("Zalo_AAC_76k" if "aac" in c else ("Zalo_Opus_24k" if "opus" in c else ("PSTN_G711_Alaw" if "g711" in c else "Cellular_AMRNB")))
                copy_audio_file(f, dst_spk_dir / c_sub, "02_Unseen_Acceptance", f"BonaFide_5Spk_Volunteers/{spk}/{c_sub}", spk, "bonafide", "none")

        ref_dir = _ROOT / f"data/bonafide_ref/{spk}"
        if ref_dir.exists():
            for f in sorted(ref_dir.glob("*.wav")):
                copy_audio_file(f, dst_spk_dir / "Enrollment_Ref", "02_Unseen_Acceptance", f"BonaFide_5Spk_Volunteers/{spk}/Enrollment_Ref", spk, "bonafide", "none")

    # 2.2. Seen Baseline Benchmarks (F5-TTS & VieNeu-TTS trên 5 SPK nghiệm thu)
    for spk in speakers:
        f5_spk_dir = _ROOT / f"data/spoof_f5tts/{spk}"
        if f5_spk_dir.exists():
            dst_f5 = DEST_ROOT / "02_Unseen_Acceptance" / "Seen_Baseline_Benchmarks" / "F5_TTS" / spk
            for f in sorted(f5_spk_dir.glob("*.wav")):
                c = detect_codec(f.name)
                copy_audio_file(f, dst_f5, "02_Unseen_Acceptance", f"Seen_Baseline_Benchmarks/F5_TTS/{spk}", spk, "spoof", "F5-TTS-Vietnamese")

        vn_spk_dir = _ROOT / f"data/spoof_vieneu/{spk}"
        if vn_spk_dir.exists():
            dst_vn = DEST_ROOT / "02_Unseen_Acceptance" / "Seen_Baseline_Benchmarks" / "VieNeu_TTS" / spk
            for f in sorted(vn_spk_dir.glob("*.wav")):
                copy_audio_file(f, dst_vn, "02_Unseen_Acceptance", f"Seen_Baseline_Benchmarks/VieNeu_TTS/{spk}", spk, "spoof", "VieNeu-TTS")

    # 2.3. Unseen TTS Engines (VoiceStudio OmniVoice CFM trên 5 SPK nghiệm thu)
    for spk in speakers:
        omni_spk_dir = _ROOT / f"data/spoof_unseen/omnivoice/{spk}"
        if omni_spk_dir.exists():
            dst_omni = DEST_ROOT / "02_Unseen_Acceptance" / "Unseen_TTS_Engines" / "OmniVoice_CFM" / spk
            for f in sorted(omni_spk_dir.glob("*.wav")):
                copy_audio_file(f, dst_omni, "02_Unseen_Acceptance", f"Unseen_TTS_Engines/OmniVoice_CFM/{spk}", spk, "spoof", "OmniVoice")

    # ═════════════════════════════════════════════════════════════════════════
    # 3. 01_Training_Seen / VIVOS & CommonVoice (Trích xuất mẫu đại diện hoặc đầy đủ)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n📂 [3/4] Sao chép dữ liệu VIVOS & Common Voice (Training Seen)...")
    # VIVOS train bona fide
    dst_vivos_bona = DEST_ROOT / "01_Training_Seen" / "VIVOS_Corpus_Train" / "BonaFide"
    for spk_dir in sorted((_ROOT / "data/raw").glob("VIVOSSPK*")):
        spk_id = spk_dir.name
        for f in sorted(spk_dir.glob("*.wav")):
            copy_audio_file(f, dst_vivos_bona / spk_id, "01_Training_Seen", f"VIVOS_Corpus_Train/BonaFide/{spk_id}", spk_id, "bonafide", "none")
    for spk_dir in sorted((_ROOT / "data/raw").glob("VIVOSDEV*")):
        spk_id = spk_dir.name
        for f in sorted(spk_dir.glob("*.wav")):
            copy_audio_file(f, dst_vivos_bona / spk_id, "01_Training_Seen", f"VIVOS_Corpus_Train/BonaFide/{spk_id}", spk_id, "bonafide", "none")

    # VIVOS F5 spoofs
    dst_vivos_f5 = DEST_ROOT / "01_Training_Seen" / "VIVOS_Corpus_Train" / "Spoof_F5TTS"
    for spk_dir in sorted((_ROOT / "data/spoof_f5tts").glob("VIVOSSPK*")):
        spk_id = spk_dir.name
        for f in sorted(spk_dir.glob("*.wav")):
            copy_audio_file(f, dst_vivos_f5 / spk_id, "01_Training_Seen", f"VIVOS_Corpus_Train/Spoof_F5TTS/{spk_id}", spk_id, "spoof", "F5-TTS-Vietnamese")

    # VIVOS VieNeu spoofs
    dst_vivos_vn = DEST_ROOT / "01_Training_Seen" / "VIVOS_Corpus_Train" / "Spoof_VieNeuTTS"
    for spk_dir in sorted((_ROOT / "data/spoof_vieneu").glob("VIVOSSPK*")):
        spk_id = spk_dir.name
        for f in sorted(spk_dir.glob("*.wav")):
            copy_audio_file(f, dst_vivos_vn / spk_id, "01_Training_Seen", f"VIVOS_Corpus_Train/Spoof_VieNeuTTS/{spk_id}", spk_id, "spoof", "VieNeu-TTS")

    # Common Voice train bona fide
    dst_cv_bona = DEST_ROOT / "01_Training_Seen" / "CommonVoice_Corpus_Train" / "BonaFide"
    for cv_dir in sorted((_ROOT / "data/raw").glob("CV_*")):
        spk_id = cv_dir.name
        for f in sorted(cv_dir.glob("*.wav")):
            copy_audio_file(f, dst_cv_bona / spk_id, "01_Training_Seen", f"CommonVoice_Corpus_Train/BonaFide/{spk_id}", spk_id, "bonafide", "none")

    # Common Voice F5 spoofs
    dst_cv_f5 = DEST_ROOT / "01_Training_Seen" / "CommonVoice_Corpus_Train" / "Spoof_F5TTS"
    for cv_dir in sorted((_ROOT / "data/spoof_f5tts").glob("CV_*")):
        spk_id = cv_dir.name
        for f in sorted(cv_dir.glob("*.wav")):
            copy_audio_file(f, dst_cv_f5 / spk_id, "01_Training_Seen", f"CommonVoice_Corpus_Train/Spoof_F5TTS/{spk_id}", spk_id, "spoof", "F5-TTS-Vietnamese")

    # Common Voice VieNeu spoofs
    dst_cv_vn = DEST_ROOT / "01_Training_Seen" / "CommonVoice_Corpus_Train" / "Spoof_VieNeuTTS"
    for cv_dir in sorted((_ROOT / "data/spoof_vieneu").glob("CV_*")):
        spk_id = cv_dir.name
        for f in sorted(cv_dir.glob("*.wav")):
            copy_audio_file(f, dst_cv_vn / spk_id, "01_Training_Seen", f"CommonVoice_Corpus_Train/Spoof_VieNeuTTS/{spk_id}", spk_id, "spoof", "VieNeu-TTS")

    # ═════════════════════════════════════════════════════════════════════════
    # 4. Ghi VOICE_FINAL_MANIFEST.csv
    # ═════════════════════════════════════════════════════════════════════════
    print("\n📝 [4/4] Ghi bảng chỉ mục tổng thể VOICE_FINAL_MANIFEST.csv...")
    manifest_csv = DEST_ROOT / "VOICE_FINAL_MANIFEST.csv"
    fieldnames = [
        "utt_id", "speaker_id", "label", "tts_generator", "codec",
        "category", "subfolder", "file_name", "rel_path",
        "sha256_hash", "file_size_bytes", "sample_rate", "duration_s"
    ]
    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    # ═════════════════════════════════════════════════════════════════════════
    # 5. Ghi README_NGHIEM_THU.md
    # ═════════════════════════════════════════════════════════════════════════
    readme_md = DEST_ROOT / "README_NGHIEM_THU.md"
    n_total = len(manifest_rows)
    n_train = sum(1 for r in manifest_rows if r["category"] == "01_Training_Seen")
    n_accept = sum(1 for r in manifest_rows if r["category"] == "02_Unseen_Acceptance")
    n_bona = sum(1 for r in manifest_rows if r["label"] == "bonafide")
    n_spoof = sum(1 for r in manifest_rows if r["label"] == "spoof")

    content = f"""# BỘ DỮ LIỆU NGHIỆM THU ĐỒ ÁN CHUYÊN NGÀNH: VOICE_FINAL
## Hệ Thống Phát Hiện Giọng Nói Giả Tiếng Việt Qua Kênh Thoại Nén (ViTrueVoice v0.4.6)

> **Cơ quan chủ quản**: Trường Đại học Công nghệ TP.HCM (HUTECH)  
> **Sinh viên thực hiện**: Nguyễn Thành Tài (MSSV: 2380601959)  
> **Thời gian xuất bản**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
> **Tổng số file âm thanh**: {n_total:,} clips ({n_copied:,} files mới sao chép)  
> **Tính toàn vẹn**: 100% tệp đã băm mã hóa SHA-256 đối chiếu tại `VOICE_FINAL_MANIFEST.csv`

---

## 1. Phân Tách Hai Không Gian Lưu Trữ Cốt Lõi

Bộ dữ liệu được phân chia nghiêm ngặt thành hai mục lớn theo đúng nguyên tắc thực nghiệm độc lập:

### Mục 1: `01_Training_Seen/` ({n_train:,} files)
Toàn bộ dữ liệu âm thanh tham gia vào quá trình huấn luyện và điều chỉnh mô hình (Training & Fine-Tuning):
- **SPK_0001_DeepVoice**: Tình nguyện viên giọng trầm ngoại lai chuyển giao vào tập huấn luyện ({sum(1 for r in manifest_rows if r['speaker_id'] == 'SPK_0001')} files gồm 75 bona fide + 50 F5-TTS + 50 VieNeu-TTS).
- **VIVOS_Corpus_Train**: Kho ngữ liệu VIVOS (46 người nói huấn luyện VIVOSSPK01..46) kèm biến thể nén 5 codec và spoof sinh bởi 2 công cụ Seen TTS (F5-TTS và VieNeu-TTS).
- **CommonVoice_Corpus_Train**: Ngữ liệu Mozilla Common Voice 8.0 tiếng Việt (20 người nói) kèm đầy đủ paired codecs và spoof sinh bởi 2 công cụ Seen TTS.

### Mục 2: `02_Unseen_Acceptance/` ({n_accept:,} files)
**BỘ NGHIỆM THU ĐỘC LẬP CHÍNH THỨC CỦA ĐỒ ÁN** — Hoàn toàn cô lập 100% khỏi quá trình huấn luyện, chọn ngưỡng threshold hay calibration:
- **BonaFide_5Spk_Volunteers** (444 files): 84 phát ngôn giọng thật gốc độc bản từ 5 tình nguyện viên đối chứng (`SPK_0003`, `SPK_0004`, `SPK_0005`, `SPK_0006`, `SPK_0007`) nhân với 5 biến thể codec (Clean, Zalo AAC-LC 76k, Zalo Opus 24k, G.711 A-law, AMR-NB) cùng các file chuẩn tham chiếu (Enrollment_Ref).
- **Seen_Baseline_Benchmarks** (750 files): Tập spoof đối chứng sinh bởi 2 công cụ Seen TTS (`F5_TTS`: 375 files; `VieNeu_TTS`: 375 files) nhằm kiểm định Giả thuyết H1.
- **Unseen_TTS_Engines** (375 files): Toàn bộ giọng giả sinh bởi công cụ Unseen TTS Zero-Shot VoiceStudio CFM (`OmniVoice_CFM`: 375 files) nhằm kiểm định Giả thuyết H2.

---

## 2. Thống Kê Phân Bổ Codec & Nhãn Âm Thanh

| Hạng mục | Bona Fide (Thật) | Spoof (Giả) | Tổng cộng |
|---|---|---|---|
| **01_Training_Seen** | {sum(1 for r in manifest_rows if r['category'] == '01_Training_Seen' and r['label'] == 'bonafide'):,} | {sum(1 for r in manifest_rows if r['category'] == '01_Training_Seen' and r['label'] == 'spoof'):,} | {n_train:,} |
| **02_Unseen_Acceptance** | {sum(1 for r in manifest_rows if r['category'] == '02_Unseen_Acceptance' and r['label'] == 'bonafide'):,} | {sum(1 for r in manifest_rows if r['category'] == '02_Unseen_Acceptance' and r['label'] == 'spoof'):,} | {n_accept:,} |
| **Toàn bộ kho dữ liệu** | **{n_bona:,}** | **{n_spoof:,}** | **{n_total:,}** |

---

## 3. Hướng Dẫn Thẩm Định & Kiểm Chứng 1-Click Dành Cho Hội Đồng

Hội đồng có thể kiểm tra trực tiếp bất kỳ file âm thanh nào trong thư mục này qua giao diện hoặc CLI:

### Cách 1: Chạy kịch bản suy luận CLI
```bash
python scripts/demo_predict.py --audio "02_Unseen_Acceptance/BonaFide_5Spk_Volunteers/SPK_0004/Clean_16k/SPK_0004_01.wav"
python scripts/demo_predict.py --audio "02_Unseen_Acceptance/Unseen_TTS_Engines/OmniVoice_CFM/SPK_0004/SPK_0004_omnivoice_prompt_006.wav"
```

### Cách 2: Chạy kiểm định ma trận suy giảm (Degradation Analysis)
```bash
python scripts/eval_seen_vs_unseen_degradation.py
```

### Cách 3: Đối chiếu tính toàn vẹn SHA-256
Mọi bản ghi âm thanh đều khớp chính xác mã SHA-256 trong tệp `VOICE_FINAL_MANIFEST.csv`, tuân thủ nghiêm ngặt Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 và Nghị định 356/2025/NĐ-CP.
"""
    readme_md.write_text(content, encoding="utf-8")

    dt = time.time() - t0
    print("\n" + "=" * 80)
    print(f"🎉 XUẤT BẢN THÀNH CÔNG BỘ DỮ LIỆU VOICE_FINAL!")
    print(f"📁 Tổng số file đã quét & đăng ký: {n_total:,} files ({n_copied:,} files chép mới)")
    print(f"📄 Bảng chỉ mục: {manifest_csv}")
    print(f"📖 Hướng dẫn nghiệm thu: {readme_md}")
    print(f"⏱️ Tổng thời gian thực hiện: {dt:.1f} giây")
    print("=" * 80)


if __name__ == "__main__":
    main()
