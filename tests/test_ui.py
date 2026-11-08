"""Unit tests for the Gradio UI demo."""

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import pytest
import torch

from src.app.ui import build_ui, make_predict_fn


class StubModel:
    def __init__(self, score_val=1.5):
        self.score_val = score_val

    def score(self, waveform):
        assert isinstance(waveform, torch.Tensor)
        # Supports (1, 64000) or batched (N, 64000)
        assert waveform.ndim == 2 and waveform.shape[-1] == 64000
        n_win = waveform.shape[0]
        return torch.tensor([self.score_val] * n_win, device=waveform.device)


def test_build_ui_returns_blocks():
    model = StubModel()
    demo = build_ui(model=model, device="cpu")
    assert isinstance(demo, gr.Blocks)


def test_make_predict_fn_bonafide():
    predict_fn = make_predict_fn(model=StubModel(score_val=2.0), device="cpu")
    # Synthetic 16kHz audio: 1s
    audio_tuple = (16000, np.zeros(16000, dtype=np.float32))
    verdict, conf_text, detail_text = predict_fn(audio_tuple)

    assert "THẬT" in verdict
    assert "Độ tin cậy" in conf_text or "Chưa hiệu chuẩn" in conf_text
    assert "Xác thực" in detail_text


def test_make_predict_fn_uncalibrated():
    predict_fn = make_predict_fn(model=StubModel(score_val=2.0), device="cpu", calibrator=None)
    audio_tuple = (16000, np.zeros(16000, dtype=np.float32))
    verdict, conf_text, detail_text = predict_fn(audio_tuple)

    assert "THẬT" in verdict
    assert "Chưa hiệu chuẩn" in conf_text or "Điểm thô" in conf_text
    assert "Xác thực" in detail_text


def test_make_predict_fn_spoof():
    predict_fn = make_predict_fn(model=StubModel(score_val=-2.0), device="cpu")
    audio_tuple = (16000, np.zeros(16000, dtype=np.float32))
    verdict, conf_text, detail_text = predict_fn(audio_tuple)

    assert "GIẢ" in verdict
    assert "Khuyến cáo" in detail_text


def test_make_predict_fn_none_audio():
    predict_fn = make_predict_fn(model=StubModel(), device="cpu")
    verdict, conf_text, detail_text = predict_fn(None)

    assert "Chưa cung cấp" in verdict or "Lỗi" in verdict


def test_make_predict_fn_rich_bonafide():
    predict_rich = make_predict_fn(model=StubModel(score_val=5.0), device="cpu", return_rich=True)
    audio_tuple = (16000, np.zeros(32000, dtype=np.float32))
    res = predict_rich(audio_tuple)
    assert len(res) == 9
    verdict, conf, detail, verdict_html, conf_html, metrics_html, spec_fig, wave_fig, cam_fig = res

    assert "THẬT" in verdict
    assert "verdict-box-bonafide" in verdict_html
    assert "progress-fill-bonafide" in conf_html
    assert "stat-card" in metrics_html
    assert isinstance(spec_fig, plt.Figure)
    assert isinstance(wave_fig, plt.Figure)
    assert isinstance(cam_fig, plt.Figure)
    plt.close("all")


def test_make_predict_fn_rich_spoof():
    predict_rich = make_predict_fn(model=StubModel(score_val=-5.0), device="cpu", return_rich=True)
    audio_tuple = (16000, np.zeros(32000, dtype=np.float32))
    res = predict_rich(audio_tuple)
    assert len(res) == 9
    verdict, conf, detail, verdict_html, conf_html, metrics_html, spec_fig, wave_fig, cam_fig = res

    assert "GIẢ" in verdict
    assert "verdict-box-spoof" in verdict_html
    assert "progress-fill-spoof" in conf_html
    assert "TUYỆT ĐỐI KHÔNG" in verdict_html
    assert isinstance(spec_fig, plt.Figure)
    plt.close("all")


def test_make_predict_fn_rich_none():
    predict_rich = make_predict_fn(model=StubModel(), device="cpu", return_rich=True)
    res = predict_rich(None)
    assert len(res) == 9
    verdict, conf, detail, verdict_html, conf_html, metrics_html, spec_fig, wave_fig, cam_fig = res
    assert "Chưa cung cấp" in verdict
    plt.close("all")
