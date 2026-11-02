"""Quét Common Voice 8.0 qua file validated.tsv, trích xuất các clip có F0 trung vị <= 125 Hz."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torchaudio


def median_f0_and_duration(
    path: Path | str,
    sr_target: int = 16000,
    max_dur_sec: float = 8.0,
) -> tuple[float | None, float]:
    try:
        y, sr = sf.read(path, dtype="float32")
    except Exception:
        return None, 0.0
    if y.ndim > 1:
        y = y.mean(axis=1)
    duration_sec = float(len(y) / sr)
    if duration_sec <= 0.1:
        return None, duration_sec
    # Cắt tối đa max_dur_sec đầu để tối ưu thời gian tính mà vẫn chuẩn xác
    y_f0 = y[: int(max_dur_sec * sr)] if duration_sec > max_dur_sec else y
    if sr != sr_target:
        y_f0 = librosa.resample(y_f0, orig_sr=sr, target_sr=sr_target)
    t_wav = torch.from_numpy(y_f0)
    # torchaudio detect_pitch_frequency: nhanh gấp 250 lần librosa.pyin
    pitches = torchaudio.functional.detect_pitch_frequency(t_wav, sample_rate=sr_target)
    valid_p = pitches[(pitches >= 65.0) & (pitches <= 400.0)]
    f0_med = float(valid_p.median().item()) if len(valid_p) > 0 else None
    return f0_med, duration_sec


def scan_deep_voices_from_tsv(
    tsv_path: str | Path,
    audio_root: str | Path,
    out_csv: str | Path | None = None,
    f0_max: float = 125.0,
    min_clips: int = 3,
    max_clips_per_speaker: int = 10,
    cache_file: str | Path | None = None,
    max_dur_sec: float = 8.0,
) -> pd.DataFrame:
    tsv_p = Path(tsv_path)
    root_p = Path(audio_root)

    if not tsv_p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file TSV: {tsv_p}")

    df_tsv = pd.read_csv(tsv_p, sep="\t", keep_default_na=False)
    if "client_id" not in df_tsv.columns or "path" not in df_tsv.columns:
        raise ValueError(f"TSV thiếu cột 'client_id' hoặc 'path': {df_tsv.columns.tolist()}")

    # 1. Nạp cache F0 nếu có
    f0_cache: dict[str, dict[str, float | None]] = {}
    if cache_file:
        c_path = Path(cache_file)
        if c_path.is_file():
            try:
                f0_cache = json.loads(c_path.read_text(encoding="utf-8"))
                print(f"📦 Đã nạp {len(f0_cache)} mục từ cache F0: {c_path}")
            except Exception as e:
                print(f"⚠️ Lỗi đọc cache F0 ({e}), khởi tạo cache mới.")
                f0_cache = {}

    # 2. Lọc nhanh các speaker có tối thiểu min_clips
    spk_counts_raw = df_tsv.groupby("client_id").size()
    eligible_clients = set(spk_counts_raw[spk_counts_raw >= min_clips].index)
    print(f"👥 Tổng speaker trong TSV: {df_tsv['client_id'].nunique()} | Đạt >= {min_clips} clips: {len(eligible_clients)}")
    df_tsv_filtered = df_tsv[df_tsv["client_id"].isin(eligible_clients)].copy()

    # 3. Lập chỉ mục file audio
    audio_index = {p.name: p for p in list(root_p.rglob("*.mp3")) + list(root_p.rglob("*.wav"))}
    print(f"📁 Đã lập chỉ mục {len(audio_index)} files âm thanh từ {root_p}")

    # 4. Lọc clip tồn tại và giới hạn tối đa max_clips_per_speaker
    valid_rows = []
    spk_used_counts: dict[str, int] = {}
    for _, r in df_tsv_filtered.iterrows():
        cid = str(r["client_id"])
        if spk_used_counts.get(cid, 0) >= max_clips_per_speaker:
            continue
        p_name = Path(r["path"]).name
        if p_name in audio_index:
            valid_rows.append({
                "client_id": cid,
                "audio_path": audio_index[p_name],
                "filename": p_name,
                "sentence": str(r.get("sentence", "")),
            })
            spk_used_counts[cid] = spk_used_counts.get(cid, 0) + 1

    if not valid_rows:
        print("⚠️ Không tìm thấy file audio nào khớp với validated.tsv")
        return pd.DataFrame()

    df_valid = pd.DataFrame(valid_rows)
    print(f"🔍 Bắt đầu đo F0 cho {len(df_valid)} clips từ {df_valid['client_id'].nunique()} speakers...")

    records = []
    cache_dirty = False
    for i, r in df_valid.iterrows():
        fname = r["filename"]
        if fname in f0_cache:
            f0_val = f0_cache[fname].get("f0")
            dur = float(f0_cache[fname].get("dur", 0.0))
        else:
            f0_val, dur = median_f0_and_duration(r["audio_path"], max_dur_sec=max_dur_sec)
            f0_cache[fname] = {"f0": f0_val, "dur": dur}
            cache_dirty = True

        if f0_val is not None:
            cid = str(r["client_id"])
            if cid.startswith("client_"):
                cid = cid[7:]
            spk_id = f"CV_deep_{cid[:10]}"
            records.append({
                "utt_id": Path(r["filename"]).stem,
                "audio_path": f"data/raw/{spk_id}/{r['filename']}",
                "orig_audio_path": str(r["audio_path"]),
                "speaker_id": spk_id,
                "transcript": r["sentence"],
                "duration_sec": dur,
                "f0_median": f0_val,
            })

    # Cập nhật cache lên đĩa
    if cache_file and cache_dirty:
        c_path = Path(cache_file)
        c_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            c_path.write_text(json.dumps(f0_cache, indent=2), encoding="utf-8")
            print(f"💾 Đã lưu {len(f0_cache)} mục vào cache F0: {c_path}")
        except Exception as e:
            print(f"⚠️ Không thể ghi cache F0: {e}")

    df_res = pd.DataFrame(records)
    if len(df_res) == 0:
        return pd.DataFrame()

    # Tính F0 trung vị theo speaker
    spk_f0 = df_res.groupby("speaker_id")["f0_median"].median()
    spk_counts = df_res.groupby("speaker_id").size()

    deep_spks = spk_f0[(spk_f0 <= f0_max) & (spk_counts >= min_clips)].index
    df_deep = df_res[df_res["speaker_id"].isin(deep_spks)].copy().reset_index(drop=True)

    print(f"✅ Đã trích xuất {len(df_deep)} clip từ {df_deep['speaker_id'].nunique()} speakers có F0 <= {f0_max} Hz")

    if out_csv:
        out_p = Path(out_csv)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_deep.to_csv(out_p, index=False)
        print(f"💾 Đã lưu kết quả tại: {out_p}")

    return df_deep


def main():
    ap = argparse.ArgumentParser(description="Scan deep voices from Common Voice TSV")
    ap.add_argument("--tsv", required=True, help="Đường dẫn validated.tsv")
    ap.add_argument("--audio-root", required=True, help="Thư mục chứa clips Common Voice")
    ap.add_argument("--out", default="data/deep_voice_pool.csv", help="Đường dẫn lưu danh sách")
    ap.add_argument("--f0-max", type=float, default=125.0, help="Ngưỡng F0 tối đa (Hz)")
    ap.add_argument("--min-clips", type=int, default=3, help="Số clip tối thiểu mỗi speaker")
    a = ap.parse_args()

    scan_deep_voices_from_tsv(
        tsv_path=a.tsv,
        audio_root=a.audio_root,
        out_csv=a.out,
        f0_max=a.f0_max,
        min_clips=a.min_clips,
    )


if __name__ == "__main__":
    main()
