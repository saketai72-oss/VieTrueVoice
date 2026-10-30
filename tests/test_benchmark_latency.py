"""Unit tests for the latency benchmarking script."""

from pathlib import Path
import pytest
import pandas as pd

from scripts.benchmark_latency import run_benchmark


class StubModel:
    def score(self, waveform):
        import torch
        return torch.tensor([1.0], device=waveform.device)


def test_run_benchmark_produces_csv_and_log(tmp_path):
    # Create sample wav
    import io, wave, numpy as np
    sample_rate = 16000
    samples = (np.sin(2 * np.pi * 220 * np.arange(16000 * 5) / sample_rate) * 12000).astype("<i2").tobytes()
    wav_path = tmp_path / "sample_5s.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(samples)

    out_csv = tmp_path / "latency_benchmark.csv"
    out_log = tmp_path / "latency_log.json"

    summary = run_benchmark(
        audio_path=wav_path,
        iterations=5,
        model=StubModel(),
        device="cpu",
        out_csv=out_csv,
        log_path=out_log,
    )

    assert summary["iterations"] == 5
    assert summary["median_sec"] >= 0.0
    assert summary["median_sec"] <= 3.0
    assert summary["verdict"] == "PASS"

    assert out_csv.exists()
    df = pd.read_csv(out_csv)
    assert len(df) == 5
    assert "latency_sec" in df.columns

    assert out_log.exists()
