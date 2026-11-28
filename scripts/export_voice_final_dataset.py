#!/usr/bin/env python3
"""Kịch bản tổ chức & xuất bản toàn bộ dữ liệu âm thanh VieTrueVoice: Voice_Final.

Địa chỉ đích: C:\\Users\\saket\\Documents\\Đồ án chuyên ngành\\Voice_Final

Cấu trúc chuẩn 2 thư mục chính:
1. bonafide/
   - SPK_Volunteers/       : Đầy đủ SPK_0003..0007 (5 SPK nghiệm thu) + SPK_0001 (train Run 2), gồm raw + 4 codecs + Enrollment_Ref
   - VIVOS/                : Toàn bộ tập VIVOS thật (VIVOSSPK* + VIVOSDEV*, clean + 4 codecs)
   - CommonVoice/          : Toàn bộ tập Common Voice 8.0 thật (CV_*, clean + 4 codecs)
2. spoof/
   - v7/ (Seen: F5-TTS + VieNeu-TTS | Unseen: OmniVoice CFM)
     * Seen/F5_TTS/        : SPK_Volunteers + VIVOS + CommonVoice (loại trừ .quarantine_mock)
     * Seen/VieNeu_TTS/    : SPK_Volunteers + VIVOS + CommonVoice
     * Unseen/OmniVoice_CFM/: SPK_Volunteers_5SPK (375) + Corpus_15Spk_Eval (965)
   - v8/ (Seen: F5-TTS + OmniVoice CFM | Unseen: VieNeu-TTS)
     * Seen/F5_TTS/        : SPK_Volunteers + VIVOS + CommonVoice (loại trừ .quarantine_mock)
     * Seen/OmniVoice_CFM/ : SPK_Volunteers (425) + VIVOS (4.795) + CommonVoice (1.225) — khớp 1:1 với v7/Seen/VieNeu_TTS
     * Unseen/VieNeu_TTS/  : Benchmark_15Spk_955 + SPK_Volunteers (425) + Corpus_Remaining
3. VOICE_FINAL_MANIFEST.csv & README_NGHIEM_THU.md
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import soundfile as sf

DEST_ROOT = Path(r"C:\Users\saket\Documents\Đồ án chuyên ngành\Voice_Final")
AUDIO_EXTS = {".wav", ".m4a", ".mp3", ".flac", ".ogg", ".opus"}


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


def codec_subfolder(fname: str) -> str:
    c = detect_codec(fname)
    if c == "aac_zalo_76k":
        return "Zalo_AAC_76k"
    if c == "opus_zalo_24k":
        return "Zalo_Opus_24k"
    if c == "g711_alaw":
        return "PSTN_G711_Alaw"
    if c == "amrnb_12.2k":
        return "Cellular_AMRNB"
    return "Clean_16k"


def get_audio_info(filepath: Path) -> tuple[int, float]:
    try:
        info = sf.info(str(filepath))
        return info.samplerate, round(info.duration, 3)
    except Exception:
        return 16000, 0.0


def _collect_speaker_dirs(base_dir: Path, prefix: str | None = None) -> list[Path]:
    if not base_dir.exists():
        return []
    dirs = []
    for d in sorted(base_dir.iterdir()):
        if not d.is_dir():
            continue
        if d.name.startswith(".") or d.name == ".quarantine_mock":
            continue
        if prefix is None or d.name.startswith(prefix):
            dirs.append(d)
    return dirs


def _sub_corpus_group(spk: str) -> str:
    """Classify speaker directory into VIVOS, CommonVoice, or SPK_Volunteers."""
    if spk.startswith("SPK_"):
        return "SPK_Volunteers"
    if spk.startswith("VIVOS"):
        return "VIVOS"
    if spk.startswith("CV_"):
        return "CommonVoice"
    return "Other"


def _process_task(
    task: tuple[Path, Path, str, str, str, str, str, str],
    dest_root: Path = DEST_ROOT,
) -> tuple[dict, bool]:
    src, dst_dir, category, version, split_role, speaker_id, label, tts_generator = task
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_file = dst_dir / src.name
    copied = False
    if not dst_file.exists() or dst_file.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dst_file)
        copied = True

    rel_p = dst_file.relative_to(dest_root).as_posix()
    sha = sha256_of_file(dst_file)
    codec = detect_codec(src.name)
    sr, dur = get_audio_info(dst_file)

    row = {
        "utt_id": src.stem,
        "speaker_id": speaker_id,
        "label": label,
        "version": version,
        "split_role": split_role,
        "tts_generator": tts_generator,
        "codec": codec,
        "category": category,
        "file_name": src.name,
        "rel_path": rel_p,
        "sha256_hash": sha,
        "file_size_bytes": dst_file.stat().st_size,
        "sample_rate": sr,
        "duration_s": dur,
    }
    return row, copied


def build_export_tasks(
    root: Path = _ROOT,
    dest_root: Path = DEST_ROOT,
) -> list[tuple[Path, Path, str, str, str, str, str, str]]:
    tasks: list[tuple[Path, Path, str, str, str, str, str, str]] = []

    def add_files_in_dir(
        src_dir: Path,
        dst_dir: Path,
        category: str,
        version: str,
        split_role: str,
        speaker_id: str,
        label: str,
        tts_generator: str,
        group_by_codec: bool = False,
    ) -> None:
        if not src_dir.exists():
            return
        for f in sorted(src_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
                target_d = dst_dir / codec_subfolder(f.name) if group_by_codec else dst_dir
                tasks.append((f, target_d, category, version, split_role, speaker_id, label, tts_generator))

    # ═════════════════════════════════════════════════════════════════════════
    # 1. BONAFIDE/
    # ═════════════════════════════════════════════════════════════════════════
    bona_root = dest_root / "bonafide"

    # 1.1. Tình nguyện viên SPK (đủ 5 SPK nghiệm thu SPK_0003..0007 + SPK_0001)
    for spk_dir in _collect_speaker_dirs(root / "data/raw", prefix="SPK_"):
        spk = spk_dir.name
        role = "train_spk1" if spk == "SPK_0001" else "acceptance_5spk"
        add_files_in_dir(
            spk_dir,
            bona_root / "SPK_Volunteers" / spk,
            "bonafide/SPK_Volunteers",
            "shared",
            role,
            spk,
            "bonafide",
            "none",
            group_by_codec=True,
        )
        ref_dir = root / "data/bonafide_ref" / spk
        add_files_in_dir(
            ref_dir,
            bona_root / "SPK_Volunteers" / spk / "Enrollment_Ref",
            "bonafide/SPK_Volunteers",
            "shared",
            f"{role}_ref",
            spk,
            "bonafide",
            "none",
            group_by_codec=False,
        )

    # 1.2. VIVOS
    for spk_dir in _collect_speaker_dirs(root / "data/raw", prefix="VIVOS"):
        spk = spk_dir.name
        add_files_in_dir(
            spk_dir,
            bona_root / "VIVOS" / spk,
            "bonafide/VIVOS",
            "shared",
            "corpus_bonafide",
            spk,
            "bonafide",
            "none",
        )

    # 1.3. Common Voice 8.0
    for cv_dir in _collect_speaker_dirs(root / "data/raw", prefix="CV_"):
        spk = cv_dir.name
        add_files_in_dir(
            cv_dir,
            bona_root / "CommonVoice" / spk,
            "bonafide/CommonVoice",
            "shared",
            "corpus_bonafide",
            spk,
            "bonafide",
            "none",
        )

    # ═════════════════════════════════════════════════════════════════════════
    # 2. SPOOF/
    # ═════════════════════════════════════════════════════════════════════════
    spoof_root = dest_root / "spoof"

    def add_f5_and_vieneu_for_version(
        ver: str,
        f5_role: str,
        vieneu_role: str,
        unseen_vieneu_paths: set[Path] | None = None,
    ) -> None:
        # F5-TTS (Seen ở cả v7 và v8)
        f5_base = root / "data/spoof_f5tts"
        for d in _collect_speaker_dirs(f5_base):
            spk = d.name
            sub = _sub_corpus_group(spk)
            add_files_in_dir(
                d,
                spoof_root / ver / f5_role / "F5_TTS" / sub / spk,
                f"spoof/{ver}/{f5_role}/F5_TTS",
                ver,
                f5_role.lower(),
                spk,
                "spoof",
                "F5-TTS-Vietnamese",
            )

        # VieNeu-TTS (Seen ở v7, Unseen ở v8)
        vn_base = root / "data/spoof_vieneu"
        for d in _collect_speaker_dirs(vn_base):
            spk = d.name
            if ver == "v8" and unseen_vieneu_paths is not None:
                for f in sorted(d.iterdir()):
                    if not (f.is_file() and f.suffix.lower() in AUDIO_EXTS):
                        continue
                    if f.resolve() in unseen_vieneu_paths:
                        sub_dir = spoof_root / ver / vieneu_role / "VieNeu_TTS" / "Benchmark_15Spk_955" / spk
                    elif spk.startswith("SPK_"):
                        sub_dir = spoof_root / ver / vieneu_role / "VieNeu_TTS" / "SPK_Volunteers" / spk
                    else:
                        sub_dir = spoof_root / ver / vieneu_role / "VieNeu_TTS" / "Corpus_Remaining" / spk
                    tasks.append((
                        f,
                        sub_dir,
                        f"spoof/{ver}/{vieneu_role}/VieNeu_TTS",
                        ver,
                        vieneu_role.lower(),
                        spk,
                        "spoof",
                        "VieNeu-TTS",
                    ))
            else:
                sub = _sub_corpus_group(spk)
                add_files_in_dir(
                    d,
                    spoof_root / ver / vieneu_role / "VieNeu_TTS" / sub / spk,
                    f"spoof/{ver}/{vieneu_role}/VieNeu_TTS",
                    ver,
                    vieneu_role.lower(),
                    spk,
                    "spoof",
                    "VieNeu-TTS",
                )

    # 2.1. V7: Seen = {F5-TTS, VieNeu-TTS} | Unseen = {OmniVoice CFM}
    add_f5_and_vieneu_for_version("v7", f5_role="Seen", vieneu_role="Seen")

    for d in _collect_speaker_dirs(root / "data/spoof_unseen/omnivoice"):
        spk = d.name
        add_files_in_dir(
            d,
            spoof_root / "v7" / "Unseen" / "OmniVoice_CFM" / "SPK_Volunteers_5SPK" / spk,
            "spoof/v7/Unseen/OmniVoice_CFM",
            "v7",
            "unseen",
            spk,
            "spoof",
            "OmniVoice",
        )
    for d in _collect_speaker_dirs(root / "data/spoof_unseen/omnivoice_15spk"):
        spk = d.name
        add_files_in_dir(
            d,
            spoof_root / "v7" / "Unseen" / "OmniVoice_CFM" / "Corpus_15Spk_Eval" / spk,
            "spoof/v7/Unseen/OmniVoice_CFM",
            "v7",
            "unseen",
            spk,
            "spoof",
            "OmniVoice",
        )

    # 2.2. V8: Seen = {F5-TTS, OmniVoice CFM} | Unseen = {VieNeu-TTS}
    unseen_vn_csv = root / "data/manifests_zalo/unseen_vieneu_benchmark.csv"
    unseen_vn_set: set[Path] = set()
    if unseen_vn_csv.exists():
        uv_df = pd.read_csv(unseen_vn_csv)
        unseen_vn_set = {(root / str(p)).resolve() for p in uv_df["audio_path"]}

    add_f5_and_vieneu_for_version("v8", f5_role="Seen", vieneu_role="Unseen", unseen_vieneu_paths=unseen_vn_set)

    # OmniVoice CFM V8.1 (Seen ở v8, xuất trọn bộ khớp đối xứng 1:1 với v7/Seen/VieNeu_TTS)
    for d in _collect_speaker_dirs(root / "data/spoof_omnivoice_v8"):
        spk = d.name
        sub = _sub_corpus_group(spk)
        add_files_in_dir(
            d,
            spoof_root / "v8" / "Seen" / "OmniVoice_CFM" / sub / spk,
            "spoof/v8/Seen/OmniVoice_CFM",
            "v8",
            "seen",
            spk,
            "spoof",
            "OmniVoice",
        )

    return tasks


def _cleanup_v8_omni_legacy(
    dest_root: Path,
    tasks: list[tuple[Path, Path, str, str, str, str, str, str]],
) -> int:
    """Remove legacy V8.0 OmniVoice directories and stray files under spoof/v8/Seen/OmniVoice_CFM."""
    v8_omni_root = dest_root / "spoof" / "v8" / "Seen" / "OmniVoice_CFM"
    if not v8_omni_root.exists():
        return 0
    for legacy_sub in ("Train_55Spk", "Dev_Eval_15Spk", "SPK_Volunteers_5SPK"):
        lp = v8_omni_root / legacy_sub
        if lp.exists():
            print(f"🧹 Đang dọn thư mục V8.0 thiếu dữ liệu: {lp}", flush=True)
            shutil.rmtree(lp)
    expected_files = {
        (dst_dir / src.name).resolve()
        for src, dst_dir, category, *_ in tasks
        if category == "spoof/v8/Seen/OmniVoice_CFM"
    }
    removed = 0
    for f in list(v8_omni_root.rglob("*")):
        if f.is_file() and f.resolve() not in expected_files:
            f.unlink()
            removed += 1
    for d in sorted((p for p in v8_omni_root.rglob("*") if p.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    return removed


def main(root: Path = _ROOT, dest_root: Path = DEST_ROOT):
    print("=" * 80)
    print("📦 TỔ CHỨC LẠI TOÀN BỘ DỮ LIỆU VOICE_FINAL (bonafide/ & spoof/{v7,v8})")
    print(f"🎯 Thư mục đích: {dest_root}")
    print("=" * 80)

    t0 = time.time()
    dest_root.mkdir(parents=True, exist_ok=True)
    tasks = build_export_tasks(root=root, dest_root=dest_root)
    removed_stale = _cleanup_v8_omni_legacy(dest_root, tasks)
    if removed_stale:
        print(f"🧹 Đã xóa {removed_stale:,} tệp OmniVoice V8 cũ không khớp chuẩn V8.1.", flush=True)
    print(f"📋 Tổng số tệp âm thanh cần đồng bộ: {len(tasks):,} files", flush=True)

    manifest_rows = []
    n_copied = 0
    worker_fn = partial(_process_task, dest_root=dest_root)
    with ThreadPoolExecutor(max_workers=8) as ex:
        for idx, (row, copied) in enumerate(ex.map(worker_fn, tasks), 1):
            manifest_rows.append(row)
            if copied:
                n_copied += 1
            if idx % 10000 == 0 or idx == len(tasks):
                print(f"   Tiến độ: {idx:,}/{len(tasks):,} ({idx/len(tasks)*100:.1f}%) | Chép mới: {n_copied:,} [{time.time()-t0:.1f}s]", flush=True)

    # Dọn các thư mục cấu trúc cũ sau khi đã ghi xong cấu trúc mới
    for legacy_dir in ["01_Training_Seen", "02_Unseen_Acceptance", "01_Corpus_Evaluation"]:
        lp = dest_root / legacy_dir
        if lp.exists():
            print(f"🧹 Đang dọn cấu trúc cũ: {lp.name}...", flush=True)
            shutil.rmtree(lp)

    # Ghi manifest SHA-256 tổng thể
    manifest_csv = dest_root / "VOICE_FINAL_MANIFEST.csv"
    fieldnames = [
        "utt_id", "speaker_id", "label", "version", "split_role",
        "tts_generator", "codec", "category", "file_name", "rel_path",
        "sha256_hash", "file_size_bytes", "sample_rate", "duration_s",
    ]
    with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    # Thống kê chi tiết cho README
    n_total = len(manifest_rows)
    n_bona = sum(1 for r in manifest_rows if r["label"] == "bonafide")
    n_spoof = sum(1 for r in manifest_rows if r["label"] == "spoof")
    n_spk = sum(1 for r in manifest_rows if r["category"] == "bonafide/SPK_Volunteers")
    n_vivos = sum(1 for r in manifest_rows if r["category"] == "bonafide/VIVOS")
    n_cv = sum(1 for r in manifest_rows if r["category"] == "bonafide/CommonVoice")

    n_v7_seen_f5 = sum(1 for r in manifest_rows if r["category"] == "spoof/v7/Seen/F5_TTS")
    n_v7_seen_vn = sum(1 for r in manifest_rows if r["category"] == "spoof/v7/Seen/VieNeu_TTS")
    n_v7_unseen_om = sum(1 for r in manifest_rows if r["category"] == "spoof/v7/Unseen/OmniVoice_CFM")
    n_v7 = n_v7_seen_f5 + n_v7_seen_vn + n_v7_unseen_om

    n_v8_seen_f5 = sum(1 for r in manifest_rows if r["category"] == "spoof/v8/Seen/F5_TTS")
    n_v8_seen_om = sum(1 for r in manifest_rows if r["category"] == "spoof/v8/Seen/OmniVoice_CFM")
    n_v8_unseen_vn = sum(1 for r in manifest_rows if r["category"] == "spoof/v8/Unseen/VieNeu_TTS")
    n_v8 = n_v8_seen_f5 + n_v8_seen_om + n_v8_unseen_vn

    n_v8_om_vivos = sum(
        1 for r in manifest_rows
        if r["category"] == "spoof/v8/Seen/OmniVoice_CFM" and "/VIVOS/" in r["rel_path"]
    )
    n_v8_om_cv = sum(
        1 for r in manifest_rows
        if r["category"] == "spoof/v8/Seen/OmniVoice_CFM" and "/CommonVoice/" in r["rel_path"]
    )
    n_v8_om_spk = sum(
        1 for r in manifest_rows
        if r["category"] == "spoof/v8/Seen/OmniVoice_CFM" and "/SPK_Volunteers/" in r["rel_path"]
    )
    n_v8_om_spk1 = sum(
        1 for r in manifest_rows
        if r["category"] == "spoof/v8/Seen/OmniVoice_CFM" and "/SPK_Volunteers/SPK_0001/" in r["rel_path"]
    )
    n_v8_om_spk5 = n_v8_om_spk - n_v8_om_spk1

    readme_md = dest_root / "README_NGHIEM_THU.md"
    readme_md.write_text(
        f"""# BỘ DỮ LIỆU ĐẦY ĐỦ VieTrueVoice (`VOICE_FINAL`)

> **Sinh viên thực hiện**: Nguyễn Thành Tài (MSSV: 2380601959) — HUTECH  
> **Cập nhật lúc**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
> **Tổng số tệp âm thanh**: {n_total:,} files (`bonafide`: {n_bona:,} | `spoof`: {n_spoof:,})  
> **Toàn vẹn dữ liệu**: 100% băm SHA-256 tại `VOICE_FINAL_MANIFEST.csv` (loại bỏ hoàn toàn `.quarantine_mock`)

---

## 1. Cấu Trúc 2 Thư Mục Chính

### `bonafide/` ({n_bona:,} files)
- `SPK_Volunteers/` (**{n_spk:,} files**): Đầy đủ 5 tình nguyện viên nghiệm thu (`SPK_0003`..`SPK_0007`, 444 files) và tình nguyện viên `SPK_0001` (80 files), gồm bản clean + 4 codecs viễn thông/Zalo và `Enrollment_Ref/`.
- `VIVOS/` (**{n_vivos:,} files**): Toàn bộ ngữ liệu VIVOS (`VIVOSSPK*` + `VIVOSDEV*`) kèm 5 biến thể kênh thoại.
- `CommonVoice/` (**{n_cv:,} files**): Toàn bộ ngữ liệu Mozilla Common Voice 8.0 (`CV_*`) kèm 5 biến thể kênh thoại.

### `spoof/` ({n_spoof:,} files)
#### `spoof/v7/` — Kiến trúc V7 (Seen: F5-TTS + VieNeu-TTS | Unseen: OmniVoice CFM) — {n_v7:,} files
- `Seen/F5_TTS/` (**{n_v7_seen_f5:,} files**): Đầy đủ mẫu giả F5-TTS trên `SPK_Volunteers`, `VIVOS`, `CommonVoice`.
- `Seen/VieNeu_TTS/` (**{n_v7_seen_vn:,} files**): Đầy đủ mẫu giả VieNeu-TTS trên `SPK_Volunteers`, `VIVOS`, `CommonVoice`.
- `Unseen/OmniVoice_CFM/` (**{n_v7_unseen_om:,} files**): Đầy đủ mẫu giả Zero-Shot VoiceStudio CFM trên 5 SPK nghiệm thu (`SPK_Volunteers_5SPK`, 375 files) và 15 người nói held-out (`Corpus_15Spk_Eval`, 965 files).

#### `spoof/v8/` — Kiến trúc Hoán đổi V8.1 (Seen: F5-TTS + OmniVoice CFM | Unseen: VieNeu-TTS) — {n_v8:,} files
- `Seen/F5_TTS/` (**{n_v8_seen_f5:,} files**): Đầy đủ mẫu giả F5-TTS trên `SPK_Volunteers`, `VIVOS`, `CommonVoice`.
- `Seen/OmniVoice_CFM/` (**{n_v8_seen_om:,} files**): Đầy đủ mẫu giả OmniVoice CFM khớp đối xứng 1:1 với `v7/Seen/VieNeu_TTS/` trên `SPK_Volunteers` (**{n_v8_om_spk:,} files**: `SPK_0001` {n_v8_om_spk1:,} + `SPK_0003`..`SPK_0007` {n_v8_om_spk5:,}), `VIVOS` (**{n_v8_om_vivos:,} files**) và `CommonVoice` (**{n_v8_om_cv:,} files**).
- `Unseen/VieNeu_TTS/` (**{n_v8_unseen_vn:,} files**): Đầy đủ mẫu giả VieNeu-TTS Unseen gồm bộ kiểm định chính thức Cổng 3 H2 (`Benchmark_15Spk_955`, 955 files), `SPK_Volunteers` (425 files) và phần ngữ liệu VIVOS/CommonVoice còn lại.
""",
        encoding="utf-8",
    )

    print(f"\n✅ HOÀN TẤT XUẤT BẢN VOICE_FINAL: {n_total:,} files trong {time.time()-t0:.1f}s!")


if __name__ == "__main__":
    main()
