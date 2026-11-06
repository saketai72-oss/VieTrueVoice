# -*- coding: utf-8 -*-
"""
Script tổng hợp ma trận thực nghiệm đối chứng toàn diện cho Tuần 5 (Must #2).
Đọc toàn bộ kết quả từ out/ (eval_metrics_A.csv, B0.csv, B.csv, zalo_b_zalo_metrics.csv, benchmarks_5spk_detailed.csv)
và xuất báo cáo ma trận đối chứng Markdown / CSV.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"⚠️ Không tìm thấy: {path}")
        return None
    return pd.read_csv(path)

def generate_experiment_matrix():
    print("=" * 80)
    print("📊 BẢNG TỔNG HỢP MA TRẬN THỰC NGHIỆM ĐỐI CHỨNG VI-TRUEVOICE (MUST #2)")
    print("=" * 80)

    # 1. Đọc các file kết quả
    df_a = load_csv(ROOT / "out" / "eval_metrics_A.csv")
    df_b0 = load_csv(ROOT / "out" / "eval_metrics_B0.csv")
    df_b = load_csv(ROOT / "out" / "eval_metrics_B.csv")
    df_zalo = load_csv(ROOT / "out" / "zalo_b_zalo_metrics.csv")
    df_5spk = load_csv(ROOT / "out" / "benchmarks_5spk_detailed.csv")

    summary_rows = []

    # 2. Phân tích So sánh 3 nhánh Huấn luyện chính (A vs B0 vs B)
    if df_a is not None and df_b is not None:
        print("\n>>> BẢNG 1: SO SÁNH ĐỐI CHỨNG 3 NHÁNH TRÊN TẬP KIỂM THỬ NỘI BỘ (IN-DOMAIN)")
        # Lọc in_domain và all
        conds = ["clean_16khz", "g711_alaw", "amr_nb", "all"]
        for c in conds:
            for tts in ["all", "F5-TTS-Vietnamese", "VieNeu-TTS"]:
                row_a = df_a[(df_a["split"] == "in_domain") & (df_a["condition"] == c) & (df_a["tts"] == tts)]
                row_b = df_b[(df_b["split"] == "in_domain") & (df_b["condition"] == c) & (df_b["tts"] == tts)]
                eer_a = row_a["eer"].values[0] * 100 if len(row_a) else np.nan
                eer_b = row_b["eer"].values[0] * 100 if len(row_b) else np.nan
                rel_impr = ((eer_a - eer_b) / eer_a) * 100 if (eer_a and not np.isnan(eer_a)) else np.nan
                
                summary_rows.append({
                    "Kịch bản": f"In-domain ({c})",
                    "TTS Engine": tts,
                    "EER Nhánh A (Clean only)": f"{eer_a:.2f}%",
                    "EER Nhánh B (ViTrueVoice)": f"{eer_b:.2f}%",
                    "Mức giảm tương đối (ΔEER)": f"{rel_impr:+.2f}%",
                    "Kiểm chứng H1/H2": "H1 PASS" if ("g711" in c or "amr" in c) and rel_impr >= 30.0 else ("H2 (Unseen)" if tts == "VieNeu-TTS" else "In-domain")
                })

        df_summary = pd.DataFrame(summary_rows)
        print(df_summary.to_string(index=False))

    # 3. Phân tích Kênh thoại Zalo (B_zalo V4/V5)
    if df_zalo is not None:
        print("\n>>> BẢNG 2: KẾT QUẢ ĐÁNH GIÁ TRÊN 11.450 MẪU DEV KÊNH ZALO (DUAL PROFILE & CODEC)")
        print(df_zalo[["codec", "n_total", "n_bonafide", "n_spoof", "eer_pct", "eer_threshold", "min_dcf", "frr_theta_0", "far_theta_0"]].to_string(index=False))

    # 4. Phân tích Bộ 5 người nói đối chứng độc lập
    if df_5spk is not None:
        print("\n>>> BẢNG 3: BỘ 5 TÌNH NGUYỆN VIÊN ĐỐI CHỨNG ĐỘC LẬP (N = 234 MẪU ĐỘC BẢN)")
        grp = df_5spk.groupby(["speaker_id", "category"])["score"].agg(["count", "mean", "min", "max"])
        print(grp)

    # Xuất ra file CSV tổng hợp
    out_path = ROOT / "out" / "w05_experiment_matrix_consolidated.csv"
    if summary_rows:
        pd.DataFrame(summary_rows).to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ Đã lưu bảng tổng hợp thực nghiệm tại: {out_path}")

if __name__ == "__main__":
    generate_experiment_matrix()
