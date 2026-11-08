import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.vitruevoice.base import SynthesisRequest, SynthesisResult, BaseTTSAdapter
from src.vitruevoice.adapters.kokoro_adapter import KokoroAdapter


def test_kokoro_adapter_interface():
    """Verify KokoroAdapter conforms to BaseTTSAdapter contract."""
    adapter = KokoroAdapter(preload=False)
    assert isinstance(adapter, BaseTTSAdapter)
    assert adapter.name == "Kokoro-Vietnamese"
    assert adapter.sample_rate == 24000


def test_kokoro_adapter_synthesis_mock():
    """Verify synthesis produces a valid 1D float32 SynthesisResult."""
    adapter = KokoroAdapter(preload=False)
    
    # Mock the internal engine
    mock_engine = MagicMock()
    mock_audio = np.random.randn(24000).astype(np.float32) * 0.2
    mock_phonemes = "x i n   c a o"
    mock_engine.synthesize.return_value = (mock_audio, mock_phonemes)
    adapter._engine = mock_engine
    adapter._loaded = True

    req = SynthesisRequest(
        text="Xin chào, đây là bài kiểm tra giọng nói tổng hợp Kokoro.",
        speaker_id="SPK_0004",
        ref_audio="data/bonafide_ref/SPK_0004/SPK_0004_01.wav",
        seed=42,
        engine_preset="Kokoro-diem_trinh",
    )

    result = adapter.synthesize(req)

    assert isinstance(result, SynthesisResult)
    assert result.engine_name == "Kokoro-Vietnamese"
    assert result.sample_rate == 24000
    assert result.audio.ndim == 1
    assert result.audio.dtype == np.float32
    assert result.duration_s == pytest.approx(1.0, rel=1e-2)
    assert result.latency_s >= 0.0
    assert result.metadata["voice"] == "diem_trinh"
    assert result.metadata["phonemes"] == mock_phonemes
    mock_engine.synthesize.assert_called_once()


def test_kokoro_adapter_voice_extraction():
    """Verify extraction of voice profile from preset or extra_params."""
    adapter = KokoroAdapter(preload=False)
    
    # Preset format: "Kokoro-mai_linh" -> voice "mai_linh"
    voice1 = adapter._resolve_voice("Kokoro-mai_linh", {})
    assert voice1 == "mai_linh"

    # Direct voice in preset: "hung_thinh"
    voice2 = adapter._resolve_voice("hung_thinh", {})
    assert voice2 == "hung_thinh"

    # In extra_params
    voice3 = adapter._resolve_voice(None, {"voice": "manh_dung"})
    assert voice3 == "manh_dung"

    # Default fallback
    voice_def = adapter._resolve_voice(None, {})
    assert voice_def == "diem_trinh"
