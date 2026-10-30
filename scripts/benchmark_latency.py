"""Đo độ trễ chuẩn hóa 30 lần liên tiếp cho dịch vụ suy luận ViTrueVoice.

Tiêu chuẩn: Trung vị thời gian phản hồi <= 3.0s (NFR1 / Must #3).
Xuất kết quả: benchmarks/latency_benchmark.csv và log ẩn danh benchmarks/latency_log.json.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import torch

from src.app.server import (
    TARGET_SAMPLE_COUNT,
    _append_latency_log,
    _default_model_loader,
    _load_audio_in_memory,
    _pad_or_crop,
)


def run_benchmark(
    audio_path: Path | str,
    iterations: int = 30,
    model: Any = None,
    checkpoint_path: Path | str = Path("out/run_B/best_model.pt"),
    device: str = "cpu",
    out_csv: Path | str = Path("benchmarks/latency_benchmark.csv"),
    log_path: Path | str = Path("benchmarks/latency_log.json"),
    target_median_sec: float = 3.0,
) -> dict[str, Any]:
    audio_p = Path(audio_path)
    if not audio_p.exists():
        raise FileNotFoundError(f"Không tìm thấy file âm thanh: {audio_p}")

    raw_bytes = audio_p.read_bytes()
    audio_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    active_model = model
    if active_model is None:
        active_model = _default_model_loader(checkpoint_path, device)
        if active_model is None:
            raise RuntimeError(f"Không thể nạp mô hình từ {checkpoint_path}")

    # Warm-up 1 run
    audio_data = _load_audio_in_memory(raw_bytes)
    padded = _pad_or_crop(audio_data, TARGET_SAMPLE_COUNT)
    t_in = torch.tensor(padded, dtype=torch.float32, device=device).unsqueeze(0)
    with torch.inference_mode():
        _ = active_model.score(t_in)

    records: list[dict[str, Any]] = []
    print(f"⏱️ Bắt đầu đo độ trễ ({iterations} lần lặp liên tiếp)...", flush=True)

    for i in range(1, iterations + 1):
        t0 = time.perf_counter()

        # Full pipeline: decode in-memory -> pad/crop -> tensor -> inference
        aud = _load_audio_in_memory(raw_bytes)
        pad = _pad_or_crop(aud, TARGET_SAMPLE_COUNT)
        tensor_in = torch.tensor(pad, dtype=torch.float32, device=device).unsqueeze(0)

        with torch.inference_mode():
            score_out = active_model.score(tensor_in)
            raw_score = float(score_out.item() if hasattr(score_out, "item") else score_out[0])

        latency = time.perf_counter() - t0
        is_bona = raw_score >= 0.0
        conf = float(1.0 / (1.0 + np.exp(-abs(raw_score))))

        records.append({
            "iteration": i,
            "latency_sec": round(latency, 4),
            "latency_ms": round(latency * 1000, 2),
            "prediction": "BONA_FIDE" if is_bona else "SPOOF",
            "confidence": round(conf, 4),
        })

        # Append anonymous log
        _append_latency_log(
            Path(log_path),
            {
                "request_id": f"bench_{i:03d}",
                "audio_sha256": audio_sha256,
                "predicted_label": "BONA_FIDE" if is_bona else "SPOOF",
                "confidence_score": round(conf, 4),
                "latency_sec": round(latency, 4),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

    df = pd.DataFrame(records)
    out_csv_p = Path(out_csv)
    out_csv_p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv_p, index=False)

    latencies = df["latency_sec"].values
    median_sec = float(np.median(latencies))
    mean_sec = float(np.mean(latencies))
    p90_sec = float(np.percentile(latencies, 90))
    min_sec = float(np.min(latencies))
    max_sec = float(np.max(latencies))
    verdict = "PASS" if median_sec <= target_median_sec else "FAIL"

    summary = {
        "iterations": iterations,
        "median_sec": round(median_sec, 4),
        "mean_sec": round(mean_sec, 4),
        "p90_sec": round(p90_sec, 4),
        "min_sec": round(min_sec, 4),
        "max_sec": round(max_sec, 4),
        "target_median_sec": target_median_sec,
        "verdict": verdict,
    }
    return summary


def main():
    p = argparse.ArgumentParser(description="Benchmark độ trễ hệ thống suy luận ViTrueVoice.")
    p.add_argument("--audio", required=True, help="Đường dẫn file âm thanh đo (5-10s)")
    p.add_argument("--iterations", type=int, default=30, help="Số lần lặp (mặc định 30)")
    p.add_argument("--ckpt", default="out/run_B/best_model.pt", help="Checkpoint mô hình")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--out", default="benchmarks/latency_benchmark.csv")
    p.add_argument("--log-path", default="benchmarks/latency_log.json")
    args = p.parse_args()

    res = run_benchmark(
        audio_path=args.audio,
        iterations=args.iterations,
        checkpoint_path=args.ckpt,
        device=args.device,
        out_csv=args.out,
        log_path=args.log_path,
    )

    print("\n" + "=" * 50)
    print("        KẾT QUẢ BENCHMARK ĐỘ TRỄ HỆ THỐNG")
    print("=" * 50)
    print(f"Số lần đo liên tiếp : {res['iterations']}")
    print(f"Trung vị (Median)   : {res['median_sec']:.4f}s ({res['median_sec']*1000:.1f}ms)")
    print(f"Trung bình (Mean)   : {res['mean_sec']:.4f}s")
    print(f"Phân vị 90 (P90)    : {res['p90_sec']:.4f}s")
    print(f"Nhanh nhất (Min)    : {res['min_sec']:.4f}s")
    print(f"Chậm nhất (Max)     : {res['max_sec']:.4f}s")
    print(f"Mục tiêu đề cương   : <= {res['target_median_sec']:.1f}s")
    print(f"Đánh giá kết quả    : {res['verdict']} 🎯")
    print("=" * 50)
    print(f"Bảng chi tiết: {args.out}")
    print(f"Log ẩn danh  : {args.log_path}\n")


if __name__ == "__main__":
    main()
