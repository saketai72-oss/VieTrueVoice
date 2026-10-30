"""Unit tests for the Gradio UI demo."""

import gradio as gr
import numpy as np
import pytest
import torch

from src.app.ui import build_ui, make_predict_fn


class StubModel:
    def __init__(self, score_val=1.5):
        self.score_val = score_val

    def score(self, waveform):
        assert isinstance(waveform, torch.Tensor)
        assert tuple(waveform.shape) == (1, 64000)
        return torch.tensor([self.score_val], device=waveform.device)


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
