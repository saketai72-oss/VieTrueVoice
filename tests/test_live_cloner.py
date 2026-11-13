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

    dummy_clone_int16 = np.zeros(16000, dtype=np.int16)

    with patch.object(cloner, "clone_omnivoice", return_value=(dummy_clone_int16, 16000, "văn bản mẫu")):
        gen = cloner.stream_cloning_and_detection(
            user_audio=user_audio,
            user_sr=16000,
            detector_model=model,
            threshold=0.0,
        )

        # Step 0: Instant Bonafide evaluation (~66ms)
        s0 = next(gen)
        assert s0["step"] == 0
        assert s0["bonafide"]["is_bonafide"] is True
        assert s0["omnivoice"]["status"] == "loading"
        assert s0["completed"] is False

        # Step 1: VoiceStudio CFM done -> Completed
        s1 = next(gen)
        assert s1["step"] == 1
        assert s1["omnivoice"]["status"] == "done"
        assert s1["omnivoice"]["audio"][0] == 16000
        assert s1["omnivoice"]["audio"][1].dtype == np.int16
        assert s1["omnivoice"]["transcript"] == "văn bản mẫu"
        assert s1["completed"] is True


def test_clone_omnivoice_pipeline_mocked(tmp_path):
    cloner = LiveQuadCloner(target_text="Câu thoại thử nghiệm", device="cpu")
    mock_model = MagicMock()
    # Mock model.generate returning dummy audio tensor
    mock_model.generate.return_value = [torch.zeros(24000)]
    cloner._omnivoice_model = mock_model

    dummy_ref = tmp_path / "ref.wav"
    import soundfile as sf
    sf.write(str(dummy_ref), np.zeros(16000, dtype=np.float32), 16000)

    with patch("omnivoice.utils.audio.save_audio") as mock_save:
        # Mock save_audio to write a valid 24k wav
        def fake_save(path, audio, sample_rate):
            sf.write(path, np.zeros(24000, dtype=np.float32), 24000)
        mock_save.side_effect = fake_save

        res = cloner.clone_omnivoice(str(dummy_ref), ref_text="câu mẫu")
        assert res is not None
        audio_int16, sr, text_used = res
        assert sr == 16000
        assert audio_int16.dtype == np.int16
        assert text_used == "câu mẫu"
        assert mock_model.generate.called
        # Verify guidance_scale=2.0 and num_step=16
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["num_step"] == 16
        assert call_kwargs["guidance_scale"] == 2.0
        assert "duration" not in call_kwargs


def test_live_quad_cloner_error_handling():
    cloner = LiveQuadCloner(device="cpu")
    model = StubDetector(score_val=3.0)
    user_audio = np.zeros(16000, dtype=np.float32)

    with patch.object(cloner, "clone_omnivoice", return_value=None):
        gen = cloner.stream_cloning_and_detection(
            user_audio=user_audio,
            user_sr=16000,
            detector_model=model,
        )
        steps = list(gen)
        assert len(steps) == 2
        final_state = steps[-1]
        assert final_state["omnivoice"]["status"] == "error"
        assert final_state["completed"] is True
