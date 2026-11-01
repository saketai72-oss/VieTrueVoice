"""Quét Common Voice 8.0 qua file validated.tsv, trích xuất các clip có F0 trung vị <= 125 Hz."""

from __future__ import annotations
import argparse
from pathlib import Path
import librosa
import numpy as np
import pandas as pd
import soundfile as sf


def median_f0_and_duration(path: Path | str, sr_target: int = 16000) -> tuple[float | None, float]:
    try:
        y, sr = sf.read(path, dtype="float32")
    except Exception:
        return None, 0.0
    if y.ndim > 1:
        y = y.mean(axis=1)
    duration_sec = float(len(y) / sr)
    if sr != sr_target:
        y = librosa.resample(y, orig_sr=sr, target_sr=sr_target)
    f0, vf, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr_target)
    c = f0[vf & ~np.isnan(f0)]
    f0_med = float(np.median(c)) if len(c) else None
    return f0_med, duration_sec


def scan_deep_voices_from_tsv(
    tsv_path: str | Path,
    audio_root: str | Path,
    out_csv: str | Path | None = None,
    f0_max: float = 125.0,
    min_clips: int = 3,
) -> pd.DataFrame:
    tsv_p = Path(tsv_path)
    root_p = Path(audio_root)

    if not tsv_p.is_file():
        raise FileNotFoundError(f"Không tìm thấy file TSV: {tsv_p}")

    df_tsv = pd.read_csv(tsv_p, sep="\t", keep_default_na=False)
    if "client_id" not in df_tsv.columns or "path" not in df_tsv.columns:
        raise ValueError(f"TSV thiếu cột 'client_id' hoặc 'path': {df_tsv.columns.tolist()}")

    # Lập chỉ mục file audio
    audio_index = {p.name: p for p in list(root_p.rglob("*.mp3")) + list(root_p.rglob("*.wav"))}
    print(f"📁 Đã lập chỉ mục {len(audio_index)} files âm thanh từ {root_p}")

    # Lọc các clip có file âm thanh tồn tại
    valid_rows = []
    for _, r in df_tsv.iterrows():
        p_name = Path(r["path"]).name
        if p_name in audio_index:
            valid_rows.append({
                "client_id": str(r["client_id"]),
                "audio_path": audio_index[p_name],
                "filename": p_name,
                "sentence": str(r.get("sentence", "")),
            })

    if not valid_rows:
        print("⚠️ Không tìm thấy file audio nào khớp với validated.tsv")
        return pd.DataFrame()

    df_valid = pd.DataFrame(valid_rows)
    print(f"🔍 Bắt đầu đo F0 cho {len(df_valid)} clips từ {df_valid['client_id'].nunique()} speakers...")

    records = []
    for i, r in df_valid.iterrows():
        f0_val, dur = median_f0_and_duration(r["audio_path"])
        if f0_val is not None:
            cid = str(r["client_id"])
            if cid.startswith("client_"):
                cid = cid[7:]
            records.append({
                "utt_id": Path(r["filename"]).stem,
                "audio_path": str(r["audio_path"]),
                "speaker_id": f"CV_deep_{cid[:10]}",
                "transcript": r["sentence"],
                "duration_sec": dur,
                "f0_median": f0_val,
            })

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
