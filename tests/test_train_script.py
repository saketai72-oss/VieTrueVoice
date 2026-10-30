"""TDD cho scripts/train.py — viết trước khi có script thực thi."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import soundfile as sf
import torch
from torch.utils.data import DataLoader
from transformers import Wav2Vec2Config

SR = 16000


# ─────────────────────────────────────────────
# Helpers dùng chung
# ─────────────────────────────────────────────

def _tiny_ssl_config():
    return Wav2Vec2Config(
        hidden_size=64, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=128, conv_dim=(16,) * 7,
        num_conv_pos_embeddings=16, num_conv_pos_embedding_groups=4,
        apply_spec_augment=False, layerdrop=0.0,
    )


def _make_manifest(tmp_path: Path, n_speakers=4, clips_per_spk=4) -> pd.DataFrame:
    """Tạo manifest tối giản: mỗi speaker có clips_per_spk mẫu (mix spoof/bona),
    với cả 3 codec để test nhánh B0/B, và cột VieNeu cho check_unseen."""
    rng = np.random.default_rng(42)
    rows = []
    idx = 0
    for spk in range(n_speakers):
        for c in range(clips_per_spk):
            is_spoof = (c % 2 == 0)
            for codec in ["clean_16khz", "g711_alaw", "amr_nb"]:
                fname = f"spk{spk}_c{c}_{codec}.wav"
                sf.write(
                    tmp_path / fname,
                    rng.normal(size=SR).astype("float32") * 0.05,
                    SR,
                )
                rows.append({
                    "utt_id": f"u{idx}_{codec}",
                    "audio_path": fname,
                    "speaker_id": f"VIVOS_{spk:04d}",
                    "label": "spoof" if is_spoof else "bonafide",
                    "codec": codec,
                    "tts_generator": "F5-TTS-Vietnamese" if is_spoof else "none",
                    "split": "train",
                    "role": "eval",
                    "source": "vivos",
                    "duration_sec": 1.0,
                    "transcript": "test",
                    "raw_wer": 0.0, "raw_cer": 0.0,
                    "ecapa_sim": 0.9, "wavlm_sim": 0.9,
                    "derived_tier": "T1",
                    "seed": 0, "pre_codec": "none",
                })
                idx += 1
    return pd.DataFrame(rows)


def _import_train():
    """Import scripts/train.py kể cả khi nằm ngoài package."""
    spec = importlib.util.spec_from_file_location(
        "train_script",
        Path(__file__).parent.parent / "scripts" / "train.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────
# 1. Cấu hình 3 nhánh — số epoch và mode
# ─────────────────────────────────────────────

def test_branch_config_A():
    train = _import_train()
    cfg, mode, transform = train.build_branch_config("A", out_dir="out/A")
    assert cfg.phase1_epochs == 4
    assert cfg.phase2_epochs == 60   # ×3 so với B/B0
    assert cfg.branch == "A"
    assert mode == "clean"
    assert transform is None


def test_branch_config_B0():
    train = _import_train()
    cfg, mode, transform = train.build_branch_config("B0", out_dir="out/B0")
    assert cfg.phase1_epochs == 4
    assert cfg.phase2_epochs == 20
    assert cfg.branch == "B0"
    assert mode == "augmented"
    assert transform is None


def test_branch_config_B():
    train = _import_train()
    cfg, mode, transform = train.build_branch_config("B", out_dir="out/B")
    assert cfg.phase1_epochs == 4
    assert cfg.phase2_epochs == 20
    assert cfg.branch == "B"
    assert mode == "augmented"
    assert transform is not None          # make_rawboost() callable


def test_branch_config_B_zalo():
    train = _import_train()
    cfg, mode, transform = train.build_branch_config("B_zalo", out_dir="out/B_zalo")
    assert cfg.phase1_epochs == 5
    assert cfg.phase2_epochs == 0          # Conservative fine-tuning: keep backbone frozen
    assert cfg.branch == "B_zalo"
    assert mode == "augmented"
    assert transform is not None


def test_invalid_branch_raises():
    train = _import_train()
    with pytest.raises(ValueError, match="branch"):
        train.build_branch_config("C", out_dir="out/C")


# ─────────────────────────────────────────────
# 2. Trọng số loss — tính động, không hardcode
# ─────────────────────────────────────────────

def test_dynamic_class_weights_branch_A(tmp_path):
    """Nhánh A chỉ dùng clean_16khz → số mẫu nhỏ hơn B0/B."""
    train = _import_train()
    df = _make_manifest(tmp_path)
    train_df = df[df["split"] == "train"]
    w = train.compute_weights(train_df, branch="A")
    assert len(w) == 2
    assert abs(sum(w) - 1.0) < 1e-6
    # spoof nhiều hơn → w[0] < w[1]
    clean = train_df[train_df["codec"] == "clean_16khz"]
    n_spoof = (clean["label"] == "spoof").sum()
    n_bona  = (clean["label"] == "bonafide").sum()
    if n_spoof > n_bona:
        assert w[0] < w[1]


def test_dynamic_class_weights_match_formula(tmp_path):
    """w_c = N/(2·N_c) — chuẩn hóa. Nhánh B dùng toàn bộ hàng."""
    from src.training.losses import loss_weights_from_counts
    train = _import_train()
    df = _make_manifest(tmp_path)
    w = train.compute_weights(df[df["split"] == "train"], branch="B")
    n_spoof = (df[df["split"] == "train"]["label"] == "spoof").sum()
    n_bona  = (df[df["split"] == "train"]["label"] == "bonafide").sum()
    expected = loss_weights_from_counts(n_spoof, n_bona)
    assert w[0] == pytest.approx(expected[0], abs=1e-6)
    assert w[1] == pytest.approx(expected[1], abs=1e-6)


# ─────────────────────────────────────────────
# 3. check_unseen_excluded được gọi trên train
# ─────────────────────────────────────────────

def test_vieneu_in_train_raises(tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    df.loc[0, "tts_generator"] = "VieNeu-TTS"
    with pytest.raises(ValueError, match="(?i)vieneu"):
        train.validate_manifest(df[df["split"] == "train"], "train")


def test_clean_manifest_passes_validation(tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    train.validate_manifest(df[df["split"] == "train"], "train")   # không raise


# ─────────────────────────────────────────────
# 4. Checkpoint lưu đúng trường branch
# ─────────────────────────────────────────────

def test_checkpoint_contains_branch(tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    cfg, mode, transform = train.build_branch_config("B0", out_dir=str(tmp_path / "out"))
    # Tính trọng số động
    train_df = df[df["split"] == "train"]
    cfg.class_weights = tuple(train.compute_weights(train_df, branch="B0"))
    # Khởi tạo model nhỏ
    from src.models.ssl_aasist import SSLAASIST
    model = SSLAASIST(ssl_config=_tiny_ssl_config(), d_graph=32, conv_channels=(8, 16))
    from src.training.trainer import Trainer
    from src.training.dataset import ViTrueVoiceDataset
    dataset = ViTrueVoiceDataset(
        train_df, audio_root=str(tmp_path), mode=mode,
        train=True, transform=transform, target_len=SR,
    )
    loader = DataLoader(dataset, batch_size=8, shuffle=False)
    cfg.phase1_epochs = 1
    cfg.phase2_epochs = 0
    cfg.amp = False
    t = Trainer(model, cfg)
    t.fit(loader, loader)
    ck = torch.load(tmp_path / "out" / "best_model.pt", map_location="cpu")
    assert ck.get("branch") == "B0" or ck["config"].get("branch") == "B0"


# ─────────────────────────────────────────────
# 5. RawBoost được áp cho nhánh B, không áp cho B0/A
# ─────────────────────────────────────────────

def test_branch_B_transform_mutates_signal(tmp_path):
    train = _import_train()
    _, _, transform = train.build_branch_config("B", out_dir="out/B")
    rng = np.random.default_rng(0)
    x = np.ones(SR, dtype=np.float32) * 0.5
    y = transform(x, rng)
    assert not np.allclose(x, y), "Nhánh B phải biến đổi tín hiệu qua RawBoost"


def test_branch_B0_A_transform_is_none(tmp_path):
    train = _import_train()
    for branch in ("A", "B0"):
        _, _, transform = train.build_branch_config(branch, out_dir=f"out/{branch}")
        assert transform is None, f"Nhánh {branch} không được có transform"


# ─────────────────────────────────────────────
# 6. Dataset mode khớp nhánh: A → clean, B0/B → augmented
# ─────────────────────────────────────────────

def test_branch_A_dataset_only_clean(tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    train_df = df[df["split"] == "train"]
    _, mode, _ = train.build_branch_config("A", out_dir="out/A")
    from src.training.dataset import ViTrueVoiceDataset
    ds = ViTrueVoiceDataset(train_df, audio_root=str(tmp_path), mode=mode, target_len=SR)
    assert set(ds.df["codec"]) == {"clean_16khz"}


def test_branch_B_dataset_has_all_codecs(tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    train_df = df[df["split"] == "train"]
    _, mode, _ = train.build_branch_config("B", out_dir="out/B")
    from src.training.dataset import ViTrueVoiceDataset
    ds = ViTrueVoiceDataset(train_df, audio_root=str(tmp_path), mode=mode, target_len=SR)
    assert {"clean_16khz", "g711_alaw", "amr_nb"}.issubset(set(ds.df["codec"]))


def test_cli_args_override_epochs_and_limit(monkeypatch, tmp_path):
    train = _import_train()
    df = _make_manifest(tmp_path)
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    df.to_csv(manifest_dir / "train.csv", index=False)
    df.to_csv(manifest_dir / "dev.csv", index=False)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "train.py",
            "--branch", "A",
            "--manifest-dir", str(manifest_dir),
            "--audio-root", str(tmp_path),
            "--out-dir", str(tmp_path / "out"),
            "--limit", "6",
            "--phase1-epochs", "1",
            "--phase2-epochs", "2",
        ],
    )
    args = train._parse_args()
    assert args.limit == 6
    assert args.phase1_epochs == 1
    assert args.phase2_epochs == 2


# ─────────────────────────────────────────────
# 6. Giai đoạn 3: Kiểm thử đường dẫn manifest & loại trừ SPK_xxxx / VieNeu
# ─────────────────────────────────────────────

def test_resolve_manifest_paths_legacy_branches(tmp_path: Path):
    train = _import_train()
    (tmp_path / "train.csv").write_text("utt_id\nu1\n", encoding="utf-8")
    (tmp_path / "dev.csv").write_text("utt_id\nu2\n", encoding="utf-8")

    for br in ["A", "B0", "B"]:
        tr, dv = train.resolve_manifest_paths(tmp_path, branch=br)
        assert tr == tmp_path / "train.csv"
        assert dv == tmp_path / "dev.csv"


def test_resolve_manifest_paths_b_zalo_auto(tmp_path: Path):
    train = _import_train()
    (tmp_path / "train_zalo.csv").write_text("utt_id\nu1\n", encoding="utf-8")
    (tmp_path / "dev_zalo.csv").write_text("utt_id\nu2\n", encoding="utf-8")

    tr, dv = train.resolve_manifest_paths(tmp_path, branch="B_zalo")
    assert tr == tmp_path / "train_zalo.csv"
    assert dv == tmp_path / "dev_zalo.csv"


def test_resolve_manifest_paths_explicit_priority(tmp_path: Path):
    train = _import_train()
    (tmp_path / "train_zalo.csv").write_text("utt_id\nu1\n", encoding="utf-8")
    (tmp_path / "dev_zalo.csv").write_text("utt_id\nu2\n", encoding="utf-8")
    custom_tr = tmp_path / "my_train.csv"
    custom_dv = tmp_path / "my_dev.csv"
    custom_tr.write_text("utt_id\nu3\n", encoding="utf-8")
    custom_dv.write_text("utt_id\nu4\n", encoding="utf-8")

    tr, dv = train.resolve_manifest_paths(
        manifest_dir=tmp_path,
        branch="B_zalo",
        train_manifest=custom_tr,
        dev_manifest=custom_dv,
    )
    assert tr == custom_tr
    assert dv == custom_dv


def test_resolve_manifest_paths_missing_raises_informative_error(tmp_path: Path):
    train = _import_train()
    missing_tr = tmp_path / "non_existent_train.csv"
    with pytest.raises(FileNotFoundError) as exc_info:
        train.resolve_manifest_paths(
            manifest_dir=tmp_path,
            branch="B",
            train_manifest=missing_tr,
        )
    assert str(missing_tr) in str(exc_info.value)


def test_validate_manifest_rejects_spk_xxxx():
    train = _import_train()
    df_bad = pd.DataFrame({
        "speaker_id": ["VIVOS_01", "SPK_0001"],
        "tts_generator": ["none", "none"],
    })
    with pytest.raises(ValueError, match="SPK_0001"):
        train.validate_manifest(df_bad, "train")

    with pytest.raises(ValueError, match="SPK_0001"):
        train.validate_manifest(df_bad, "dev")


def test_validate_manifest_rejects_vieneu_in_dev():
    train = _import_train()
    df_bad = pd.DataFrame({
        "speaker_id": ["VIVOS_01", "VIVOS_02"],
        "tts_generator": ["none", "VieNeu-TTS v3 Turbo"],
    })
    with pytest.raises(ValueError, match="(?i)vieneu"):
        train.validate_manifest(df_bad, "dev")


