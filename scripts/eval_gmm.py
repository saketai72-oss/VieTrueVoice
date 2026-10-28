"""Đánh giá baseline LFCC+GMM theo codec và theo công cụ TTS.

Quy ước: bonafide = 1, spoof = 0; điểm cao = giống bonafide.
Hỗ trợ cả manifest dạng "rộng" (mỗi codec một cột) và dạng "dài" (18 cột chuẩn của ViTrueVoice).
"""
from __future__ import annotations
import argparse
from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.metrics import (
    compute_eer, compute_min_dcf, confusion_at_threshold, cluster_bootstrap_ci,
)

SR = 16000
TARGET_LEN = 64000  # 4,0 s @ 16 kHz

_LABEL_MAP = {
    "bonafide": 1, "bona_fide": 1, "bona fide": 1, "real": 1, "1": 1,
    "spoof": 0, "fake": 0, "0": 0
}


def normalize_labels(series: pd.Series) -> np.ndarray:
    mapped = series.astype(str).str.lower().str.strip().map(_LABEL_MAP)
    if mapped.isna().any():
        bad = series[mapped.isna()].unique()[:5]
        raise ValueError(f"Nhãn không nhận diện được: {bad}")
    return mapped.astype(int).to_numpy()


def load_wave(path, sr=SR):
    import soundfile as sf
    from scipy.signal import resample_poly
    x, fs = sf.read(str(path), dtype="float32", always_2d=False)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if fs != sr:
        g = gcd(int(fs), sr)
        x = resample_poly(x, sr // g, int(fs) // g).astype(np.float32)
    return x


def fix_length(x, n=TARGET_LEN):
    """Lặp (tile) nếu ngắn, cắt phần đầu nếu dài - xác định, không ngẫu nhiên."""
    x = np.asarray(x, dtype=np.float32)
    if len(x) == 0:
        raise ValueError("Sóng âm rỗng")
    if len(x) < n:
        x = np.tile(x, int(np.ceil(n / len(x))))
    return x[:n]


def to_long(df, path_cols: dict, id_cols: list):
    """Chuyển manifest rộng (mỗi codec một cột đường dẫn) sang dạng dài."""
    parts = []
    for cond, col in path_cols.items():
        part = df[id_cols].copy()
        part["condition"] = cond
        part["path"] = df[col]
        parts.append(part[part["path"].notna()])
    return pd.concat(parts, ignore_index=True)


def evaluate_subset(scores, labels, speakers, n_boot=1000, seed=0):
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels).astype(int)
    eer, thr = compute_eer(scores, labels)
    mdcf = compute_min_dcf(scores, labels)
    cm = confusion_at_threshold(scores, labels, thr)
    lo = hi = float("nan")
    if n_boot > 0:
        lo, hi = cluster_bootstrap_ci(scores, labels, np.asarray(speakers),
                                      n_boot=n_boot, seed=seed)
    return {
        "n_bona": int((labels == 1).sum()), "n_spoof": int((labels == 0).sum()),
        "eer": eer, "eer_ci_lo": lo, "eer_ci_hi": hi,
        "eer_threshold": thr, "min_dcf": mdcf,
        # hàng = nhãn thật, cột = dự đoán tại ngưỡng EER
        "spoof_correct": int(cm[0, 0]), "spoof_accepted": int(cm[0, 1]),
        "bona_rejected": int(cm[1, 0]), "bona_correct": int(cm[1, 1]),
    }


def build_table(df, split, n_boot=1000, seed=0):
    """df cần cột: label (0/1), speaker_id, tts, condition, score.

    Với mỗi codec (và 'all'): một dòng tổng ('all' TTS) và một dòng cho từng
    công cụ TTS = toàn bộ bonafide + spoof của công cụ đó.
    """
    rows = []
    if len(df) == 0:
        return pd.DataFrame(rows)
    conds = sorted(df["condition"].unique()) + ["all"]
    for cond in conds:
        sub = df if cond == "all" else df[df["condition"] == cond]
        bona = sub[sub["label"] == 1]
        spoof = sub[sub["label"] == 0]
        if len(bona) == 0 or len(spoof) == 0:
            continue
        groups = [("all", sub)]
        for tool in sorted(spoof["tts"].astype(str).unique()):
            groups.append((tool, pd.concat([bona, spoof[spoof["tts"].astype(str) == tool]])))
        for tool, g in groups:
            r = evaluate_subset(g["score"], g["label"], g["speaker_id"],
                                n_boot=n_boot, seed=seed)
            rows.append({"split": split, "condition": cond, "tts": tool, **r})
    return pd.DataFrame(rows)


def score_files(model, paths, log_every=500):
    out = []
    for i, p in enumerate(paths, 1):
        out.append(model.score_wave(fix_length(load_wave(p))))
        if i % log_every == 0:
            print(f"  đã chấm {i}/{len(paths)}", flush=True)
    return np.array(out)


def _parse_kv(items):
    return dict(s.split("=", 1) for s in items)


def filter_role(df, role):
    if role is None or "role" not in df.columns:
        return df
    out = df[df["role"].astype(str) == role]
    if len(out) == 0:
        raise ValueError(f"Không có hàng nào với role={role}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--manifest", nargs="+", required=True,
                    help="tên=đường_dẫn_csv, ví dụ in_domain=data/test_indomain.csv")
    ap.add_argument("--path-cols", nargs="*", default=None,
                    help="codec=tên_cột cho manifest dạng rộng (ví dụ clean=clean_16khz g711=... amr_nb=...)")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--speaker-col", default="speaker_id")
    ap.add_argument("--tts-col", default="tts_generator")
    ap.add_argument("--audio-path-col", default="audio_path")
    ap.add_argument("--codec-col", default="codec")
    ap.add_argument("--role", default="eval")
    ap.add_argument("--audio-root", default=".")
    ap.add_argument("--out", default="benchmarks/eval_metrics_baseline_gmm.csv")
    ap.add_argument("--scores-out", default="benchmarks/scores_baseline_gmm.csv")
    ap.add_argument("--reuse-scores", action="store_true")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--limit", type=int, default=0, help="chỉ lấy N hàng đầu để chạy thử")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    scores_path = Path(a.scores_out)

    if a.reuse_scores and scores_path.exists():
        scored = pd.read_csv(scores_path)
    else:
        from src.models.baseline_gmm import LFCCGMMBaseline
        model = LFCCGMMBaseline.load(a.model)
        frames = []
        for name, csv in _parse_kv(a.manifest).items():
            df = filter_role(pd.read_csv(csv, keep_default_na=False), a.role)
            if a.limit:
                df = df.head(a.limit)

            # Fallback tên cột cho phù hợp với 18 cột manifest
            actual_tts_col = a.tts_col if a.tts_col in df.columns else ("tts_engine" if "tts_engine" in df.columns else "tts")
            actual_speaker_col = a.speaker_col if a.speaker_col in df.columns else "speaker"
            actual_label_col = a.label_col if a.label_col in df.columns else "label"

            if a.path_cols:
                # Manifest dạng rộng (wide format)
                path_cols = _parse_kv(a.path_cols)
                id_cols = [actual_label_col, actual_speaker_col, actual_tts_col]
                long = to_long(df, path_cols, id_cols)
            else:
                # Manifest dạng dài (long format - chuẩn 18 cột của ViTrueVoice)
                long = pd.DataFrame()
                long["path"] = df[a.audio_path_col]
                long["condition"] = df[a.codec_col]
                long[actual_label_col] = df[actual_label_col]
                long[actual_speaker_col] = df[actual_speaker_col]
                long[actual_tts_col] = df[actual_tts_col]

            long["split"] = name
            full = [str(Path(a.audio_root) / p) for p in long["path"]]
            print(f"[{name}] chấm {len(full)} file", flush=True)
            long["score"] = score_files(model, full)
            frames.append(long)
        scored = pd.concat(frames, ignore_index=True)
        scores_path.parent.mkdir(parents=True, exist_ok=True)
        scored.to_csv(scores_path, index=False)

    # Đổi tên cột đồng nhất
    col_remap = {}
    for col in [a.label_col, "label"]:
        if col in scored.columns:
            col_remap[col] = "label"
    for col in [a.speaker_col, "speaker_id", "speaker"]:
        if col in scored.columns:
            col_remap[col] = "speaker_id"
    for col in [a.tts_col, "tts_generator", "tts_engine", "tts"]:
        if col in scored.columns:
            col_remap[col] = "tts"
    scored = scored.rename(columns=col_remap)

    scored["label"] = normalize_labels(scored["label"])

    # Bảo đảm mẫu spoof có tts_generator hợp lệ
    spoof_missing_tts = (scored["label"] == 0) & (
        scored["tts"].isna() | scored["tts"].astype(str).str.strip().str.lower().isin(["", "nan", "none"])
    )
    if spoof_missing_tts.any():
        bad_samples = scored.loc[spoof_missing_tts, "path"].tolist()[:5]
        raise ValueError(f"Phát hiện mẫu spoof thiếu tts_generator: {bad_samples}")

    tables = [build_table(g, split=name, n_boot=a.n_boot, seed=a.seed)
              for name, g in scored.groupby("split")]
    result = pd.concat(tables, ignore_index=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(a.out, index=False)
    print(result[["split", "condition", "tts", "eer", "eer_ci_lo",
                  "eer_ci_hi", "min_dcf"]].to_string(index=False))


if __name__ == "__main__":
    main()
