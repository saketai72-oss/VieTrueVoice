import numpy as np
import pandas as pd
import pytest
import soundfile as sf
import torch
from transformers import Wav2Vec2Config

from src.models.ssl_aasist import SSLAASIST
from src.training.dataset import ViTrueVoiceDataset
from scripts.eval_ssl_aasist import filter_role, score_manifest, check_tts_labels

SR = 16000


def tiny_model():
    cfg = Wav2Vec2Config(
        hidden_size=64, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=128, conv_dim=(16,) * 7, num_conv_pos_embeddings=16,
        num_conv_pos_embedding_groups=4, apply_spec_augment=False, layerdrop=0.0)
    torch.manual_seed(0)
    return SSLAASIST(ssl_config=cfg, d_graph=32, conv_channels=(8, 16))


@pytest.fixture
def df(tmp_path):
    rng = np.random.default_rng(0)
    rows = []
    for i in range(6):
        for codec in ["clean_16khz", "g711_alaw"]:
            p = tmp_path / f"u{i}_{codec}.wav"
            sf.write(p, rng.normal(size=12000).astype("float32") * 0.1, SR)
            spoof = i % 3 == 0
            rows.append({"audio_path": p.name, "speaker_id": f"s{i % 2}",
                         "label": "spoof" if spoof else "bonafide", "codec": codec,
                         "tts_generator": "VieNeu-TTS" if spoof else "none",
                         "role": "eval" if i < 5 else "enroll", "split": "test"})
    return pd.DataFrame(rows), tmp_path


def test_filter_role_keeps_only_eval(df):
    d, _ = df
    out = filter_role(d, "eval")
    assert set(out["role"]) == {"eval"} and len(out) == 10


def test_filter_role_raises_when_empty(df):
    with pytest.raises(ValueError):
        filter_role(df[0], "nonexistent")


def test_score_manifest_schema_and_length(df):
    d, root = df
    ds = ViTrueVoiceDataset(d, audio_root=root, mode="eval", target_len=8000)
    out = score_manifest(tiny_model(), ds, "cpu", batch_size=4, num_workers=0)
    assert len(out) == len(d)
    assert {"score", "label", "speaker_id", "condition", "tts"} <= set(out.columns)
    assert set(out["label"]) <= {0, 1} and np.isfinite(out["score"]).all()
    assert set(out["condition"]) == {"clean_16khz", "g711_alaw"}


def test_check_tts_labels_flags_spoof_without_tool():
    ok = pd.DataFrame({"label": [1, 0], "tts": ["none", "VieNeu-TTS"]})
    check_tts_labels(ok)
    bad = pd.DataFrame({"label": [1, 0], "tts": ["none", "none"]})
    with pytest.raises(ValueError):
        check_tts_labels(bad)
