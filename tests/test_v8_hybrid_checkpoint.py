from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest
import torch

from scripts.build_v8_hybrid_checkpoint import (
    build_balanced_ft_manifest,
    freeze_lower_ssl,
    graft_state_dict,
    is_lower_layer,
)
from src.models.ssl_aasist import SSLAASIST


def test_is_lower_layer_logic():
    # Lower layers
    assert is_lower_layer("frontend.encoder.feature_extractor.conv_layers.0.conv.weight", split_layer=6) is True
    assert is_lower_layer("frontend.encoder.feature_projection.projection.weight", split_layer=6) is True
    assert is_lower_layer("frontend.encoder.encoder.layers.0.attention.k_proj.weight", split_layer=6) is True
    assert is_lower_layer("frontend.encoder.encoder.layers.5.attention.k_proj.weight", split_layer=6) is True
    assert is_lower_layer("frontend.encoder.masked_spec_embed", split_layer=6) is True

    # Higher layers & AASIST
    assert is_lower_layer("frontend.encoder.encoder.layers.6.attention.k_proj.weight", split_layer=6) is False
    assert is_lower_layer("frontend.encoder.encoder.layers.11.attention.k_proj.weight", split_layer=6) is False
    assert is_lower_layer("frontend.encoder.encoder.layer_norm.weight", split_layer=6) is False
    assert is_lower_layer("conv.0.bn1.weight", split_layer=6) is False
    assert is_lower_layer("out.weight", split_layer=6) is False
    assert is_lower_layer("master", split_layer=6) is False


def test_graft_state_dict_mock():
    sd_a = {
        "frontend.encoder.encoder.layers.2.weight": torch.tensor([10.0, 10.0]),
        "frontend.encoder.encoder.layers.8.weight": torch.tensor([10.0, 10.0]),
        "out.weight": torch.tensor([10.0, 10.0]),
        "bn_in.num_batches_tracked": torch.tensor(100, dtype=torch.int64),
    }
    sd_b = {
        "frontend.encoder.encoder.layers.2.weight": torch.tensor([20.0, 20.0]),
        "frontend.encoder.encoder.layers.8.weight": torch.tensor([20.0, 20.0]),
        "out.weight": torch.tensor([20.0, 20.0]),
        "bn_in.num_batches_tracked": torch.tensor(200, dtype=torch.int64),
    }

    grafted = graft_state_dict(sd_a, sd_b, split_layer=6, low_alpha=0.10, high_alpha=0.90)

    # Layer 2 (lower): (1 - 0.1) * 10 + 0.1 * 20 = 9 + 2 = 11.0
    torch.testing.assert_close(grafted["frontend.encoder.encoder.layers.2.weight"], torch.tensor([11.0, 11.0]))

    # Layer 8 (higher): (1 - 0.9) * 10 + 0.9 * 20 = 1 + 18 = 19.0
    torch.testing.assert_close(grafted["frontend.encoder.encoder.layers.8.weight"], torch.tensor([19.0, 19.0]))

    # Out (AASIST): (1 - 0.9) * 10 + 0.9 * 20 = 19.0
    torch.testing.assert_close(grafted["out.weight"], torch.tensor([19.0, 19.0]))

    # Integer tensor kept intact
    assert grafted["bn_in.num_batches_tracked"].item() == 200


def test_freeze_lower_ssl_mock():
    model = SSLAASIST()
    ssl_active, backend_active = freeze_lower_ssl(model, split_layer=8)

    # Check lower layers are frozen
    for p in model.frontend.encoder.feature_extractor.parameters():
        assert p.requires_grad is False
    for p in model.frontend.encoder.feature_projection.parameters():
        assert p.requires_grad is False
    for idx, layer in enumerate(model.frontend.encoder.encoder.layers):
        for p in layer.parameters():
            if idx < 8:
                assert p.requires_grad is False
            else:
                assert p.requires_grad is True

    # Check backend is trainable
    assert model.out.weight.requires_grad is True
    assert len(ssl_active) > 0
    assert len(backend_active) > 0


def test_balanced_ft_manifest_structure(tmp_path):
    out_file = tmp_path / "train_balanced.csv"
    df = build_balanced_ft_manifest(output_csv=out_file)
    assert len(df) == 4800
    assert "label" in df.columns
    assert "speaker_id" in df.columns
    # Check 0% acceptance volunteer leakage
    forbidden = {"SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"}
    assert set(df["speaker_id"].unique()).intersection(forbidden) == set()
    # Check 0% VieNeu
    assert not df["tts_generator"].astype(str).str.contains("vieneu", case=False).any()
