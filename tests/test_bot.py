"""Unit tests for the Telegram bot handlers."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.app.bot import build_bot_app, handle_voice_message


class StubModel:
    def __init__(self, score_val=1.5):
        self.score_val = score_val

    def score(self, waveform):
        import torch
        return torch.tensor([self.score_val], device=waveform.device)


@pytest.mark.anyio
async def test_handle_voice_message_bonafide():
    # Make mock update with a voice file
    update = MagicMock()
    context = MagicMock()

    file_mock = AsyncMock()
    # 0.5s of 16kHz sine wave
    import io, wave, numpy as np
    sample_rate = 16000
    samples = (np.sin(2 * np.pi * 220 * np.arange(8000) / sample_rate) * 12000).astype("<i2").tobytes()
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(samples)
    raw_wav = out_buf.getvalue()

    async def fake_download_to_memory(out):
        out.write(raw_wav)
        return out

    file_mock.download_to_memory = fake_download_to_memory

    voice_mock = MagicMock()
    voice_mock.get_file = AsyncMock(return_value=file_mock)
    update.message.voice = voice_mock
    update.message.audio = None
    update.message.reply_text = AsyncMock()

    model = StubModel(score_val=2.5)
    await handle_voice_message(update, context, model=model, device="cpu")

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "GIỌNG NÓI THẬT" in reply or "THẬT" in reply
    assert "Độ tin cậy" in reply


@pytest.mark.anyio
async def test_handle_voice_message_spoof():
    update = MagicMock()
    context = MagicMock()

    file_mock = AsyncMock()
    import io, wave, numpy as np
    sample_rate = 16000
    samples = (np.sin(2 * np.pi * 220 * np.arange(8000) / sample_rate) * 12000).astype("<i2").tobytes()
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate); wf.writeframes(samples)
    raw_wav = out_buf.getvalue()

    async def fake_download_to_memory(out):
        out.write(raw_wav)
        return out

    file_mock.download_to_memory = fake_download_to_memory

    voice_mock = MagicMock()
    voice_mock.get_file = AsyncMock(return_value=file_mock)
    update.message.voice = voice_mock
    update.message.audio = None
    update.message.reply_text = AsyncMock()

    model = StubModel(score_val=-2.5)
    await handle_voice_message(update, context, model=model, device="cpu")

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "GIẢ MẠO" in reply
    assert "CẢNH BÁO" in reply or "Khuyến cáo" in reply
