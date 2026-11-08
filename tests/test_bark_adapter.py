import pytest
import numpy as np
from unittest.mock import MagicMock

from src.vitruevoice.base import SynthesisRequest, SynthesisResult, BaseTTSAdapter
from src.vitruevoice.adapters.bark_adapter import BarkAdapter


def test_bark_adapter_interface():
    """Verify BarkAdapter conforms to BaseTTSAdapter contract."""
    adapter = BarkAdapter(preload=False)
    assert isinstance(adapter, BaseTTSAdapter)
    assert adapter.name == "Suno-Bark"
    assert adapter.sample_rate == 24000


def test_bark_adapter_voice_resolution():
    """Verify voice preset resolution."""
    adapter = BarkAdapter(preload=False)
    assert adapter._resolve_voice("Bark-v2/en_speaker_6", {}) == "v2/en_speaker_6"
    assert adapter._resolve_voice(None, {"voice_preset": "v2/en_speaker_9"}) == "v2/en_speaker_9"
    assert adapter._resolve_voice("v2/en_speaker_3", {}) == "v2/en_speaker_3"


def test_bark_adapter_synthesis_mock():
    """Verify synthesis produces a valid SynthesisResult."""
    adapter = BarkAdapter(preload=False)
    
    # Mock processor and model
    mock_processor = MagicMock()
    mock_processor.return_value.to.return_value = {"input_ids": [1, 2, 3]}
    mock_model = MagicMock()
    
    import torch
    dummy_tensor = torch.zeros((1, 24000), dtype=torch.float32)
    mock_model.generate.return_value = dummy_tensor
    
    adapter._processor = mock_processor
    adapter._model = mock_model
    adapter._loaded = True

    req = SynthesisRequest(
        text="Xin chào Việt Nam",
        speaker_id="SPK_0003",
        ref_audio=None,
        engine_preset="Bark-v2/en_speaker_6",
    )

    result = adapter.synthesize(req)

    assert isinstance(result, SynthesisResult)
    assert result.engine_name == "Suno-Bark"
    assert result.sample_rate == 24000
    assert result.audio.ndim == 1
    assert result.duration_s == pytest.approx(1.0, rel=1e-2)
    assert result.metadata["voice_preset"] == "v2/en_speaker_6"
