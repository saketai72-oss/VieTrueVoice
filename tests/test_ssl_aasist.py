import pytest
import torch
from transformers import Wav2Vec2Config
from src.models.ssl_aasist import SSLAASIST
from src.training.losses import weighted_ce


def tiny_cfg():
    return Wav2Vec2Config(
        hidden_size=64, num_hidden_layers=2, num_attention_heads=2,
        intermediate_size=128, conv_dim=(16,) * 7,
        num_conv_pos_embeddings=16, num_conv_pos_embedding_groups=4,
        apply_spec_augment=False, layerdrop=0.0,
    )


@pytest.fixture
def model():
    torch.manual_seed(0)
    return SSLAASIST(ssl_config=tiny_cfg(), d_graph=32, conv_channels=(8, 16))


def wave(b=2, n=16000, seed=0):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(b, n, generator=g)


def test_forward_shape_and_finite(model):
    out = model(wave())
    assert out.shape == (2, 2)
    assert torch.isfinite(out).all()


def test_score_is_bonafide_minus_spoof(model):
    model.eval()
    w = wave()
    with torch.no_grad():
        z = model(w)
        s = model.score(w)
    assert s.shape == (2,)
    assert torch.allclose(s, z[:, 1] - z[:, 0])


def test_eval_is_deterministic_and_batch_independent(model):
    model.eval()
    w = wave(3)
    with torch.no_grad():
        full = model(w)
        again = model(w)
        single = torch.cat([model(w[i:i + 1]) for i in range(3)])
    assert torch.allclose(full, again)
    assert torch.allclose(full, single, atol=1e-4)


def test_gain_invariance(model):
    model.eval()
    w = wave()
    with torch.no_grad():
        assert torch.allclose(model(w), model(w * 3.0), atol=1e-3)


def test_phase1_freezes_ssl_only(model):
    model.freeze_ssl()
    enc = model.frontend.encoder
    assert all(not p.requires_grad for p in enc.parameters())
    assert all(p.requires_grad for p in model.frontend.proj.parameters())
    model(wave()).sum().backward()
    assert all(p.grad is None for p in enc.parameters())
    assert model.frontend.proj.weight.grad is not None


def test_frozen_encoder_stays_in_eval_when_model_train(model):
    model.freeze_ssl()
    model.train()
    assert model.frontend.encoder.training is False
    assert model.frontend.proj.training is True
    model.unfreeze_ssl()
    model.train()
    assert model.frontend.encoder.training is True


def test_phase2_unfreezes_and_gradients_flow(model):
    model.freeze_ssl()
    model.unfreeze_ssl()
    assert all(p.requires_grad for p in model.parameters())
    model(wave()).sum().backward()
    assert any(p.grad is not None for p in model.frontend.encoder.parameters())


def test_param_groups_cover_all_params_once(model):
    groups = model.param_groups(lr_backend=1e-4, lr_ssl=1e-6)
    assert {g["lr"] for g in groups} == {1e-4, 1e-6}
    ids = [id(p) for g in groups for p in g["params"]]
    assert len(ids) == len(set(ids)) == len(list(model.parameters()))


def test_weighted_ce_class_order():
    # chỉ số 0 = spoof, 1 = bonafide; trọng số bonafide cao hơn
    ce = weighted_ce([0.1398, 0.8602], reduction="sum")
    miss_bona = ce(torch.tensor([[2.0, -2.0]]), torch.tensor([1]))   # bonafide bị đoán spoof
    miss_spoof = ce(torch.tensor([[-2.0, 2.0]]), torch.tensor([0]))  # spoof bị đoán bonafide
    assert miss_bona.item() == pytest.approx(miss_spoof.item() * 0.8602 / 0.1398, rel=1e-5)


def test_weighted_ce_rejects_wrong_length():
    with pytest.raises(ValueError):
        weighted_ce([0.2, 0.3, 0.5])
