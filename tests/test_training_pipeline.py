import numpy as np
import pandas as pd
import pytest
import soundfile as sf
import torch
from torch.utils.data import DataLoader
from transformers import Wav2Vec2Config

from src.models.ssl_aasist import SSLAASIST
from src.training.dataset import (
    ViTrueVoiceDataset, fit_length, check_unseen_excluded,
)
from src.training.losses import loss_weights_from_counts
from src.training.trainer import (
    TrainConfig, Trainer, EarlyStopper, make_optimizer,
)

SR = 16000


def tiny_model():
    cfg = Wav2Vec2Config(
        hidden_size=64, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=128, conv_dim=(16,) * 7,
        num_conv_pos_embeddings=16, num_conv_pos_embedding_groups=4,
        apply_spec_augment=False, layerdrop=0.0)
    torch.manual_seed(0)
    return SSLAASIST(ssl_config=cfg, d_graph=32, conv_channels=(8, 16))


@pytest.fixture
def manifest(tmp_path):
    rng = np.random.default_rng(0)
    rows = []
    lengths = [8000, 16000, 24000]  # ngắn, vừa, dài (so với target_len test)
    for i in range(12):
        for codec in ["clean_16khz", "g711_alaw"]:
            p = tmp_path / f"u{i}_{codec}.wav"
            sf.write(p, rng.normal(size=lengths[i % 3]).astype("float32") * 0.1, SR)
            spoof = i % 3 == 0
            rows.append({
                "utt_id": f"u{i}", "audio_path": p.name,
                "speaker_id": f"s{i % 4}",
                "label": "spoof" if spoof else "bonafide",
                "codec": codec,
                "tts_generator": "F5-TTS-Vietnamese" if spoof else "none",
                "split": "train",
            })
    return pd.DataFrame(rows), tmp_path


def ds(manifest, **kw):
    df, root = manifest
    return ViTrueVoiceDataset(df, audio_root=root, target_len=16000, **kw)


# ---------- fit_length ----------
def test_fit_length_tiles_short_and_crops_long():
    rng = np.random.default_rng(0)
    assert len(fit_length(np.ones(100, np.float32), 1000, False, rng)) == 1000
    assert len(fit_length(np.ones(5000, np.float32), 1000, True, rng)) == 1000


def test_fit_length_eval_takes_first_samples():
    x = np.arange(5000, dtype=np.float32)
    out = fit_length(x, 1000, False, np.random.default_rng(0))
    assert np.array_equal(out, x[:1000])


def test_fit_length_rejects_empty():
    with pytest.raises(ValueError):
        fit_length(np.array([], np.float32), 100, False, np.random.default_rng(0))


# ---------- Dataset ----------
def test_clean_mode_keeps_only_clean_rows(manifest):
    d = ds(manifest, mode="clean")
    assert set(d.df["codec"]) == {"clean_16khz"}
    assert len(d) == 12


def test_item_shape_and_label_mapping(manifest):
    d = ds(manifest, mode="eval")
    item = d[0]
    assert item["wave"].shape == (16000,) and item["wave"].dtype == torch.float32
    assert item["label"].item() in (0, 1)
    labels = {r.label: int(l) for r, l in zip(d.df.itertuples(), d.labels)}
    assert labels == {"spoof": 0, "bonafide": 1}


def test_unknown_label_raises(manifest):
    df, root = manifest
    df = df.copy()
    df.loc[0, "label"] = "???"
    with pytest.raises(ValueError):
        ViTrueVoiceDataset(df, audio_root=root, target_len=16000, mode="eval")


def test_transform_only_applied_in_augmented_train(manifest):
    calls = []
    def tf(x, rng):
        calls.append(1)
        return x * 0.0
    d_aug = ds(manifest, mode="augmented", train=True, transform=tf)
    assert d_aug[0]["wave"].abs().sum() == 0 and len(calls) == 1
    calls.clear()
    for mode, train in [("clean", True), ("eval", False), ("augmented", False)]:
        d = ds(manifest, mode=mode, train=train, transform=tf)
        _ = d[0]
    assert calls == []


def test_random_crop_depends_on_epoch_but_is_reproducible(manifest):
    d = ds(manifest, mode="eval", train=True)  # train=True bật random crop
    idx = int(np.where(d.df["audio_path"].str.contains("u2_clean"))[0][0])  # 24000 mẫu
    d.set_epoch(0); a = d[idx]["wave"]
    d.set_epoch(0); b = d[idx]["wave"]
    d.set_epoch(1); c = d[idx]["wave"]
    assert torch.equal(a, b)
    assert not torch.equal(a, c)


def test_check_unseen_excluded():
    ok = pd.DataFrame({"tts_generator": ["none", "F5-TTS-Vietnamese"]})
    check_unseen_excluded(ok, "vieneu", "train")
    bad = pd.DataFrame({"tts_generator": ["none", "VieNeu-TTS"]})
    with pytest.raises(ValueError):
        check_unseen_excluded(bad, "vieneu", "train")


# ---------- Loss weights ----------
def test_loss_weights_from_counts_matches_project_values():
    w = loss_weights_from_counts(n_spoof=4380, n_bonafide=26947)
    assert w[0] == pytest.approx(0.8602, abs=1e-4)
    assert w[1] == pytest.approx(0.1398, abs=1e-4)
    assert sum(w) == pytest.approx(1.0)


# ---------- EarlyStopper ----------
def test_early_stopper():
    s = EarlyStopper(patience=2)
    assert s.step(0.30) is True
    assert s.step(0.31) is False and not s.should_stop
    assert s.step(0.32) is False and s.should_stop
    assert s.step(0.10) is True and not s.should_stop


# ---------- Optimizer và 2 pha ----------
def test_phase1_optimizer_excludes_frozen_encoder():
    m = tiny_model(); m.freeze_ssl()
    opt = make_optimizer(m, 1, TrainConfig())
    ids = {id(p) for g in opt.param_groups for p in g["params"]}
    assert not any(id(p) in ids for p in m.frontend.encoder.parameters())
    assert id(m.frontend.proj.weight) in ids


def test_phase2_has_two_learning_rates():
    m = tiny_model(); m.unfreeze_ssl()
    opt = make_optimizer(m, 2, TrainConfig(lr_backend=1e-5, lr_ssl=1e-6))
    assert {g["lr"] for g in opt.param_groups} == {1e-5, 1e-6}


# ---------- Trainer ----------
def loaders(manifest, bs=4):
    tr = ds(manifest, mode="clean", train=True)
    dev = ds(manifest, mode="eval", train=False)
    return (DataLoader(tr, batch_size=bs, shuffle=True),
            DataLoader(dev, batch_size=bs))


def snap(enc):
    return [p.detach().clone() for p in enc.parameters()]


def test_phase1_leaves_encoder_untouched_phase2_changes_it(manifest, tmp_path):
    m = tiny_model()
    before = snap(m.frontend.encoder)
    cfg = TrainConfig(phase1_epochs=1, phase2_epochs=0, accum_steps=1,
                      amp=False, out_dir=str(tmp_path / "o1"))
    tr, dev = loaders(manifest)
    Trainer(m, cfg).fit(tr, dev)
    assert all(torch.equal(a, b) for a, b in zip(before, snap(m.frontend.encoder)))

    cfg2 = TrainConfig(phase1_epochs=0, phase2_epochs=1, accum_steps=1,
                       amp=False, out_dir=str(tmp_path / "o2"))
    Trainer(m, cfg2).fit(tr, dev)
    assert any(not torch.equal(a, b) for a, b in zip(before, snap(m.frontend.encoder)))


def test_fit_writes_checkpoint_and_history(manifest, tmp_path):
    m = tiny_model()
    cfg = TrainConfig(phase1_epochs=1, phase2_epochs=1, accum_steps=1,
                      amp=False, out_dir=str(tmp_path / "o"))
    tr, dev = loaders(manifest)
    t = Trainer(m, cfg)
    hist = t.fit(tr, dev)
    assert len(hist) == 2 and [h["phase"] for h in hist] == [1, 2]
    assert all(np.isfinite(h["train_loss"]) and 0.0 <= h["dev_eer"] <= 1.0 for h in hist)
    ck = torch.load(tmp_path / "o" / "best_model.pt", map_location="cpu")
    assert {"model", "dev_eer", "epoch", "phase"} <= set(ck)
    assert ck["dev_eer"] == pytest.approx(min(h["dev_eer"] for h in hist))


def test_gradient_accumulation_step_count(manifest, tmp_path):
    m = tiny_model()
    cfg = TrainConfig(phase1_epochs=1, phase2_epochs=0, accum_steps=2,
                      amp=False, out_dir=str(tmp_path / "o"))
    tr, dev = loaders(manifest, bs=2)   # 12 mẫu clean / 2 = 6 batch
    t = Trainer(m, cfg); t.fit(tr, dev)
    assert t.opt_steps == 3
