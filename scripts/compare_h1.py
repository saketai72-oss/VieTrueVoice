"""Đối chứng H1 (giảm EER tương đối) và H2 (EER trên TTS chưa thấy).

Đầu vào: hai file eval_metrics_*.csv cùng schema (split, condition, tts, eer,
eer_ci_lo, eer_ci_hi, ...). EER lưu dạng phân số (0..1), ΔEER xuất dạng %.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

KEYS = ["split", "condition", "tts"]


def relative_reduction(eer_a, eer_b, min_base=1e-4):
    """ΔEER tương đối (%). NaN nếu baseline quá nhỏ để phép chia có nghĩa."""
    if not np.isfinite(eer_a) or eer_a < min_base:
        return float("nan")
    return float((eer_a - eer_b) / eer_a * 100.0)


def _verdict(delta, target):
    if not np.isfinite(delta):
        return "N/A"
    return "PASS" if delta >= target else "FAIL"


def build_h1(a, b, compressed, target=30.0, tts="all", min_base=1e-4):
    """So A (không tăng cường) với B (có tăng cường) trên các kênh nén."""
    a = a[(a["tts"].astype(str) == tts) & a["condition"].isin(compressed)]
    b = b[(b["tts"].astype(str) == tts) & b["condition"].isin(compressed)]
    cols = KEYS + ["eer", "eer_ci_lo", "eer_ci_hi"]
    m = a[cols].merge(b[cols], on=KEYS, how="outer", suffixes=("_a", "_b"))
    if len(m) == 0:
        return m
    m["delta_rel_pct"] = [
        relative_reduction(x, y, min_base) if np.isfinite(x) and np.isfinite(y)
        else float("nan")
        for x, y in zip(m["eer_a"], m["eer_b"])
    ]
    m["verdict"] = [
        "MISSING" if not (np.isfinite(x) and np.isfinite(y)) else _verdict(d, target)
        for x, y, d in zip(m["eer_a"], m["eer_b"], m["delta_rel_pct"])
    ]
    m["ci_overlap"] = (m["eer_ci_lo_a"] <= m["eer_ci_hi_b"]) & \
                      (m["eer_ci_lo_b"] <= m["eer_ci_hi_a"])

    def split_verdict(g):
        present = set(g["condition"])
        if not set(compressed) <= present or (g["verdict"] == "MISSING").any():
            return "INCOMPLETE"
        if (g["verdict"] == "FAIL").any():
            return "FAIL"
        if (g["verdict"] == "N/A").any():
            return "N/A"
        return "PASS"

    sv = m.groupby("split").apply(split_verdict, include_groups=False)
    m["split_verdict"] = m["split"].map(sv)
    return m.sort_values(["split", "condition"]).reset_index(drop=True)


def build_h2(b, unseen_pattern="vieneu", threshold=0.15):
    """EER của mô hình B trên công cụ TTS chưa thấy, theo split và codec."""
    mask = b["tts"].astype(str).str.lower().str.contains(unseen_pattern.lower(),
                                                         regex=False)
    r = b[mask & (b["condition"] != "all")].copy()
    r["verdict"] = np.where(r["eer"] <= threshold, "PASS", "FAIL")
    r["ci_hi_pass"] = r["eer_ci_hi"] <= threshold
    cols = ["split", "condition", "tts", "eer", "eer_ci_lo", "eer_ci_hi",
            "verdict", "ci_hi_pass"]
    return r[cols].sort_values(["split", "condition"]).reset_index(drop=True)


def to_markdown(df, floatfmt="{:.4f}"):
    def fmt(v):
        return floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v)
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |"
            for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="eval_metrics của mô hình A (không tăng cường)")
    ap.add_argument("--b", required=True, help="eval_metrics của mô hình B (có tăng cường)")
    ap.add_argument("--compressed", nargs="+", default=["g711_alaw", "amr_nb"])
    ap.add_argument("--target", type=float, default=30.0)
    ap.add_argument("--unseen-pattern", default="vieneu")
    ap.add_argument("--h2-threshold", type=float, default=0.15)
    ap.add_argument("--min-base", type=float, default=1e-4)
    ap.add_argument("--out-dir", default="benchmarks")
    a = ap.parse_args()

    ea, eb = pd.read_csv(a.a), pd.read_csv(a.b)
    h1 = build_h1(ea, eb, a.compressed, a.target, min_base=a.min_base)
    h2 = build_h2(eb, a.unseen_pattern, a.h2_threshold)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    h1.to_csv(out / "h1_comparison.csv", index=False)
    h2.to_csv(out / "h2_unseen_tts.csv", index=False)
    md = ("## H1: giảm EER tương đối (mục tiêu ≥ {:.0f}%)\n\n{}\n\n"
          "## H2: EER trên TTS chưa thấy (mục tiêu ≤ {:.0f}%)\n\n{}\n").format(
        a.target, to_markdown(h1) if len(h1) else "_không có dữ liệu_",
        a.h2_threshold * 100, to_markdown(h2) if len(h2) else "_không có dữ liệu_")
    (out / "h1_h2_summary.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
