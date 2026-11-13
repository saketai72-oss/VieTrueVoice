"""Unit tests for the Gradio UI demo."""

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import pytest
import torch

from unittest.mock import patch

from src.app.ui import build_ui, make_live_quad_cloning_fn, make_predict_fn


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


def test_make_live_quad_cloning_fn_none():
    quad_fn = make_live_quad_cloning_fn(model=StubModel(), device="cpu")
    outputs = list(quad_fn(None, False))
    assert len(outputs) == 1
    banner, bona_h, bona_a, f5_h, f5_a, vn_h, vn_a, omni_h, omni_a, matrix_h = outputs[0]
    assert "Vui lòng ghi âm" in banner
    assert bona_a is None


def test_make_live_quad_cloning_fn_short_audio():
    quad_fn = make_live_quad_cloning_fn(model=StubModel(), device="cpu")
    short_audio = (16000, np.zeros(4000, dtype=np.float32))  # 0.25s
    outputs = list(quad_fn(short_audio, False))
    assert len(outputs) == 1
    banner, *_ = outputs[0]
    assert "quá ngắn" in banner


def test_make_live_quad_cloning_fn_streaming():
    model = StubModel(score_val=2.5)
    quad_fn = make_live_quad_cloning_fn(model=model, device="cpu")
    audio = (16000, np.zeros(32000, dtype=np.float32))  # 2.0s

    dummy_clone = np.zeros(24000, dtype=np.float32)

    with patch("src.vitruevoice.live_cloner.LiveQuadCloner.clone_f5", return_value=(dummy_clone, 24000)), \
         patch("src.vitruevoice.live_cloner.LiveQuadCloner.clone_vieneu", return_value=(dummy_clone, 48000)), \
         patch("src.vitruevoice.live_cloner.LiveQuadCloner.clone_omnivoice", return_value=(dummy_clone, 24000)):
        
        yields = list(quad_fn(audio, False))
        assert len(yields) == 4

        # Step 0: Immediate Bonafide result
        b0, bona_h0, bona_a0, f5_h0, f5_a0, vn_h0, vn_a0, omni_h0, omni_a0, matrix_h0 = yields[0]
        assert "Bước 1/4" in b0
        assert "Bona Fide" in bona_h0
        assert bona_a0 is not None
        assert f5_a0 is None

        # Step 3: Complete
        b3, bona_h3, bona_a3, f5_h3, f5_a3, vn_h3, vn_a3, omni_h3, omni_a3, matrix_h3 = yields[3]
        assert "HOÀN TẤT" in b3
        assert f5_a3 is not None
        assert vn_a3 is not None
        assert omni_a3 is not None
        assert "QUAD-FORENSICS BENCHMARK MATRIX" in matrix_h3

