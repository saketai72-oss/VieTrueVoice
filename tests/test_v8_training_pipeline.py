from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import torch

from scripts.train_v8_inverted_dual import (
    eval_gate1_spk0001,
    eval_gate2_acceptance_5spk,
    eval_gate3_unseen_vieneu,
    eval_gate4_omnivoice_reversal,
    update_server_default_checkpoint,
)


class MockModel:
    def __init__(self, fixed_score: float = 10.0):
        self.fixed_score = fixed_score

    def score(self, batch):
        n = batch.shape[0] if isinstance(batch, torch.Tensor) else len(batch)
        return torch.tensor([self.fixed_score] * n)


def test_eval_gate1_spk0001_mock():
    mock_model = MockModel(fixed_score=5.0)
    res = eval_gate1_spk0001(mock_model, device="cpu")
    assert res["gate"] == "Gate 1 - SPK_0001 Isolation"
    assert res["total"] == 15
    assert res["n_pass"] == 15
    assert res["pass_rate_pct"] == 100.0
    assert res["passed"] is True
    assert len(res["details"]) == 15


def test_eval_gate2_acceptance_5spk_mock():
    mock_model = MockModel(fixed_score=10.0)
    res = eval_gate2_acceptance_5spk(mock_model, device="cpu")
    assert res["gate"] == "Gate 2 - 5 Acceptance Volunteers"
    assert res["total_files"] == 84
    assert res["total_bona"] == 84
    assert res["overall_pass_rate_pct"] == 100.0
    assert res["passed"] is True
    assert len(res["by_speaker"]) == 5


def test_eval_gate3_unseen_vieneu_mock():
    mock_model = MockModel(fixed_score=-15.0)  # Predicts spoof for all
    dev_mock_df = pd.DataFrame([
        {
            "audio_path": "data/raw/SPK_0003/SPK_0003_01.wav",
            "label": "bonafide",
            "codec": "clean_16khz",
        }
    ] * 20)

    res = eval_gate3_unseen_vieneu(mock_model, dev_bona_df=dev_mock_df, device="cpu")
    assert res["gate"] == "Gate 3 - Unseen VieNeu-TTS Benchmark"
    assert res["total_unseen_spoof"] == 955
    assert res["spoof_blocked_count"] == 955
    assert res["spoof_block_rate_pct"] == 100.0


def test_eval_gate4_omnivoice_reversal_mock():
    mock_model = MockModel(fixed_score=-10.0)  # Flips to spoof
    res = eval_gate4_omnivoice_reversal(mock_model, device="cpu")
    assert res["gate"] == "Gate 4 - OmniVoice CFM Reversal"
    assert res["total_missed_v7"] == 195
    assert res["n_reversed_to_spoof"] == 195
    assert res["reversal_rate_pct"] == 100.0


def test_update_server_default_checkpoint_idempotent(tmp_path):
    server_path = tmp_path / "server.py"
    server_path.write_text(
        'DEFAULT_CHECKPOINT = (\n    Path("out/zalo_b_zalo_v7_dual_with_spk1/best_model.pt")\n    if ...\n)',
        encoding="utf-8",
    )
    with patch("scripts.train_v8_inverted_dual._ROOT", tmp_path):
        server_dir = tmp_path / "src" / "app"
        server_dir.mkdir(parents=True, exist_ok=True)
        (server_dir / "server.py").write_text(server_path.read_text(), encoding="utf-8")
        update_server_default_checkpoint("out/zalo_b_zalo_v8_inverted/best_model.pt")
        updated = (server_dir / "server.py").read_text(encoding="utf-8")
        assert "out/zalo_b_zalo_v8_inverted/best_model.pt" in updated
