# -*- coding: utf-8 -*-
"""Unit tests for LiveQuadCloner and Quad-Forensics streaming pipeline."""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import torch

from src.vitruevoice.live_cloner import (
    DEFAULT_TARGET_TEXT,
    LiveQuadCloner,
    evaluate_audio_sample,
)


class StubDetector:
    def __init__(self, score_val=2.5):
        self.score_val = score_val

    def score(self, waveform):
        assert isinstance(waveform, torch.Tensor)
        assert waveform.ndim == 2 and waveform.shape[-1] == 64000
        n_win = waveform.shape[0]
        return torch.tensor([self.score_val] * n_win, device=waveform.device)


def test_evaluate_audio_sample_bonafide():
    model = StubDetector(score_val=5.0)
    audio = np.zeros(32000, dtype=np.float32)
    res = evaluate_audio_sample(audio, sr=16000, detector_model=model, device="cpu")

    assert res["is_bonafide"] is True
    assert res["raw_score"] == pytest.approx(5.0)
    assert res["prob_bona_pct"] > 80.0
    assert "sha256" in res
    assert len(res["sha256"]) == 64


def test_evaluate_audio_sample_spoof():
    model = StubDetector(score_val=-5.0)
    audio = np.zeros(32000, dtype=np.float32)
    res = evaluate_audio_sample(audio, sr=16000, detector_model=model, device="cpu")

    assert res["is_bonafide"] is False
    assert res["raw_score"] == pytest.approx(-5.0)
    assert res["prob_spoof_pct"] > 80.0


def test_live_quad_cloner_streaming_generator():
    cloner = LiveQuadCloner(target_text=DEFAULT_TARGET_TEXT, device="cpu")
    model = StubDetector(score_val=3.0)
    user_audio = np.zeros(32000, dtype=np.float32)

    dummy_clone_wav = np.zeros(24000, dtype=np.float32)

    with patch.object(cloner, "clone_f5", return_value=(dummy_clone_wav, 24000)), \
         patch.object(cloner, "clone_vieneu", return_value=(dummy_clone_wav, 48000)), \
         patch.object(cloner, "clone_omnivoice", return_value=(dummy_clone_wav, 24000)):

        gen = cloner.stream_cloning_and_detection(
            user_audio=user_audio,
            user_sr=16000,
            detector_model=model,
            threshold=0.0,
        )

        # Step 0: Instant Bonafide evaluation
        s0 = next(gen)
        assert s0["step"] == 0
        assert s0["bonafide"]["is_bonafide"] is True
        assert s0["f5"]["status"] == "loading"
        assert s0["vieneu"]["status"] == "loading"
        assert s0["omnivoice"]["status"] == "loading"
        assert s0["completed"] is False

        # Step 1: F5 clone ready
        s1 = next(gen)
        assert s1["step"] == 1
        assert s1["f5"]["status"] == "done"
        assert s1["vieneu"]["status"] == "loading"
        assert s1["omnivoice"]["status"] == "loading"
        assert s1["completed"] is False

        # Step 2: VieNeu clone ready
        s2 = next(gen)
        assert s2["step"] == 2
        assert s2["vieneu"]["status"] == "done"
        assert s2["omnivoice"]["status"] == "loading"
        assert s2["completed"] is False

        # Step 3: OmniVoice clone ready -> Completed
        s3 = next(gen)
        assert s3["step"] == 3
        assert s3["omnivoice"]["status"] == "done"
        assert s3["completed"] is True


def test_live_quad_cloner_priority_only_omnivoice():
    cloner = LiveQuadCloner(device="cpu", priority_only_omnivoice=True)
    model = StubDetector(score_val=3.0)
    user_audio = np.zeros(16000, dtype=np.float32)
    dummy_clone_wav = np.zeros(24000, dtype=np.float32)

    with patch.object(cloner, "clone_omnivoice", return_value=(dummy_clone_wav, 24000)):
        gen = cloner.stream_cloning_and_detection(
            user_audio=user_audio,
            user_sr=16000,
            detector_model=model,
        )
        steps = list(gen)
        final_state = steps[-1]
        assert final_state["f5"]["status"] == "skipped"
        assert final_state["vieneu"]["status"] == "skipped"
        assert final_state["omnivoice"]["status"] == "done"
        assert final_state["completed"] is True
