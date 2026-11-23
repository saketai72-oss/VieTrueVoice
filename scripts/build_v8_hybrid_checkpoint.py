#!/usr/bin/env python3
"""Module xây dựng mô hình V8 Lai ghép Đa tầng (Layer-Wise Grafting) & Tinh chỉnh Cân bằng 1 Epoch.

Bao gồm:
1. Giai đoạn 2: Ghép tầng Checkpoint A (Pha 1) + Checkpoint B (Pha 2) theo split_layer, low_alpha, high_alpha.
2. Sinh tập dữ liệu huấn luyện cân bằng: data/manifests_zalo/train_v8_balanced_ft.csv (~4.800 mẫu).
3. Giai đoạn 3: Tinh chỉnh 1-epoch với đóng băng cục bộ (Partial-Freeze) các tầng dưới Wav2Vec 2.0.
4. Đánh giá ma trận 4 Cổng x 3 Pooling modes (max, mean, asymmetric_veto) và lưu báo cáo đối chứng.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Đảm bảo đường dẫn gốc của project luôn nằm trong sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Đặt biến môi trường offline cho HuggingFace để tránh timeout/treo trên Windows
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from scripts.eval_ssl_aasist import load_model
from scripts.train import validate_manifest
from src.evaluation.metrics import compute_eer, compute_min_dcf
from src.models.ssl_aasist import SSLAASIST
from src.preprocessing.audio_loader import load_audio
from src.preprocessing.pooling import extract_window_batch, pool_scores
from src.training.dataset import ViTrueVoiceDataset
from src.training.losses import AMSoftmaxLoss, loss_weights_from_counts


def is_lower_layer(key: str, split_layer: int = 6) -> bool:
    """Xác định tham số thuộc các tầng thấp (Wav2Vec2 feature extractor & lower encoder layers)."""
    if key.startswith("frontend.encoder.feature_extractor."):
        return True
    if key.startswith("frontend.encoder.feature_projection."):
        return True
    if "encoder.layers." in key:
        parts = key.split("encoder.layers.")[1].split(".")
        if parts[0].isdigit():
            idx = int(parts[0])
            return idx < split_layer
    if key.startswith("frontend.encoder.") and not key.startswith("frontend.encoder.encoder.layers."):
        if not key.startswith("frontend.encoder.encoder.layer_norm"):
            return True
    return False


def graft_state_dict(
    sd_a: dict[str, torch.Tensor],
    sd_b: dict[str, torch.Tensor],
    split_layer: int = 6,
    low_alpha: float = 0.15,
    high_alpha: float = 0.85,
) -> dict[str, torch.Tensor]:
    """Lai ghép 2 state dict theo cơ chế tách tầng (Layer-Wise Grafting).

    - Các tầng thấp: (1 - low_alpha) * sd_a + low_alpha * sd_b (giữ bản sắc ngữ âm tổng quát của Checkpoint A).
    - Các tầng cao & AASIST: (1 - high_alpha) * sd_a + high_alpha * sd_b (tiếp thu tri thức phân biệt spoof CFM của Checkpoint B).
    """
    grafted = {}
    for k in sd_a.keys():
        if k not in sd_b:
            grafted[k] = sd_a[k].clone()
            continue

        val_a = sd_a[k]
        val_b = sd_b[k]

        if not val_a.is_floating_point():
            grafted[k] = val_b.clone()
            continue

        alpha = low_alpha if is_lower_layer(k, split_layer=split_layer) else high_alpha
        grafted[k] = (1.0 - alpha) * val_a + alpha * val_b

    return grafted


def build_balanced_ft_manifest(
    input_csv: str | Path = "data/manifests_zalo/train_v8_f5_omni_with_spk1.csv",
    output_csv: str | Path = "data/manifests_zalo/train_v8_balanced_ft.csv",
    random_seed: int = 42,
) -> pd.DataFrame:
    """Tạo tập manifest cân bằng ~4.800 mẫu từ train_v8_f5_omni_with_spk1.csv."""
    in_path = _ROOT / str(input_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Không tìm thấy input manifest: {in_path}")

    df = pd.read_csv(in_path)

    # 1. Toàn bộ 125 dòng SPK_0001 x 6 = 750 dòng
    df_spk1 = df[df["speaker_id"] == "SPK_0001"]
    spk1_oversampled = pd.concat([df_spk1] * 6, ignore_index=True)

    # 2. Toàn bộ 545 dòng OmniVoice train x 2 = 1.090 dòng
    df_omni = df[df["tts_generator"] == "OmniVoice"]
    omni_oversampled = pd.concat([df_omni] * 2, ignore_index=True)

    # 3. 960 dòng F5-TTS train (chia đều 5 codecs: 192 dòng/codec)
    df_f5 = df[(df["tts_generator"] == "F5-TTS-Vietnamese") & (df["speaker_id"] != "SPK_0001")]
    f5_sampled = df_f5.groupby("codec", group_keys=False).apply(
        lambda x: x.sample(192, random_state=random_seed)
    )

    # 4. 500 dòng deep_pitch_augmented bona fide
    df_deep = df[df["source"] == "deep_pitch_augmented"]
    deep_sampled = df_deep.sample(min(len(df_deep), 500), random_state=random_seed)

    # 5. 1.500 dòng vivos + common_voice bona fide (chia đều 5 codecs: 300 dòng/codec)
    df_bona = df[
        (df["source"].isin(["vivos", "common_voice"]))
        & (df["label"] == "bonafide")
        & (df["speaker_id"] != "SPK_0001")
    ]
    bona_sampled = df_bona.groupby("codec", group_keys=False).apply(
        lambda x: x.sample(300, random_state=random_seed)
    )

    balanced_df = pd.concat(
        [spk1_oversampled, omni_oversampled, f5_sampled, deep_sampled, bona_sampled],
        ignore_index=True,
    ).sample(frac=1.0, random_state=random_seed).reset_index(drop=True)

    # Kiểm tra an toàn sinh trắc học bắt buộc
    validate_manifest(balanced_df, "train", allow_vieneu=False)

    out_path = _ROOT / str(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    balanced_df.to_csv(out_path, index=False)
    print(f"✅ Đã tạo thành công manifest cân bằng ({len(balanced_df)} dòng) tại: {out_path}")
    return balanced_df


def freeze_lower_ssl(model: SSLAASIST, split_layer: int = 8) -> tuple[list, list]:
    """Đóng băng các tầng dưới của Wav2Vec 2.0 và chỉ mở các tầng cao + AASIST."""
    model.frontend.frozen = False

    # Khóa feature extractor, projection và các tầng thấp
    for p in model.frontend.encoder.feature_extractor.parameters():
        p.requires_grad = False
    for p in model.frontend.encoder.feature_projection.parameters():
        p.requires_grad = False
    if hasattr(model.frontend.encoder.encoder, "pos_conv_embed"):
        for p in model.frontend.encoder.encoder.pos_conv_embed.parameters():
            p.requires_grad = False

    for idx, layer in enumerate(model.frontend.encoder.encoder.layers):
        if idx < split_layer:
            for p in layer.parameters():
                p.requires_grad = False
        else:
            for p in layer.parameters():
                p.requires_grad = True

    if hasattr(model.frontend.encoder.encoder, "layer_norm"):
        for p in model.frontend.encoder.encoder.layer_norm.parameters():
            p.requires_grad = True

    if hasattr(model.frontend, "proj"):
        for p in model.frontend.proj.parameters():
            p.requires_grad = True

    # Mở toàn bộ backend AASIST
    enc_params = list(model.frontend.encoder.parameters())
    enc_ids = {id(p) for p in enc_params}
    backend_params = [p for p in model.parameters() if id(p) not in enc_ids]
    for p in backend_params:
        p.requires_grad = True

    ssl_trainable = [p for p in enc_params if p.requires_grad]
    backend_trainable = [p for p in backend_params if p.requires_grad]

    print(f"🔒 Đã khóa {split_layer} tầng thấp của SSL Wav2Vec2. Mở {len(ssl_trainable)} SSL tensors và {len(backend_trainable)} Backend tensors.")
    return ssl_trainable, backend_trainable


def evaluate_checkpoint_multi_pooling(
    model: SSLAASIST,
    dev_df: pd.DataFrame,
    pooling_modes: list[str] = ["max", "mean", "asymmetric_veto"],
    device: str = "cuda",
) -> dict:
    """Đánh giá 4 Cổng kiểm định trên nhiều chế độ pooling."""
    results = {}
    model.eval()

    # Nạp sẵn audio cho các cổng để tiết kiệm I/O
    raw_dir_spk1 = _ROOT / "data/raw/SPK_0001"
    spk1_files = sorted([
        f for f in raw_dir_spk1.glob("*.wav")
        if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])
    ])

    spk_acc_dirs = ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]
    acc_files = []
    for spk in spk_acc_dirs:
        d = _ROOT / f"data/raw/{spk}"
        clean = [f for f in sorted(list(d.glob("*.wav")) + list(d.glob("*.m4a")))
                 if not any(c in f.name for c in ["_g711", "_amrnb", "_aac_zalo", "_opus_zalo"])]
        acc_files.extend([(spk, f) for f in clean])

    unseen_df = pd.read_csv(_ROOT / "data/manifests_zalo/unseen_vieneu_benchmark.csv")

    v7_cache = _ROOT / "benchmarks/cached_scores_15spk_v7.csv"
    omni_missed_df = pd.read_csv(v7_cache)
    omni_missed_df = omni_missed_df[(omni_missed_df["tts_generator"] == "OmniVoice") & (omni_missed_df["score"] > 0)]

    # Chuẩn bị mẫu Dev Bona Fide (400 mẫu/codec = 2.000 mẫu)
    bona_sample = dev_df[dev_df["label"] == "bonafide"].groupby("codec", group_keys=False).apply(
        lambda x: x.sample(min(len(x), 400), random_state=42)
    )

    # Trích xuất cửa sổ trượt trước
    print("   [Multi-Pooling Eval] Trích xuất audio và forward pass model...")
    def get_window_scores(file_path):
        y = load_audio(file_path, target_sr=16000)
        batch = extract_window_batch(y, win=64000, hop=16000, max_windows=5, dense_slicing=True).to(device)
        with torch.no_grad():
            w_sc = model.score(batch)
        return w_sc

    spk1_win_scores = [get_window_scores(f) for f in spk1_files]
    acc_win_scores = [(spk, get_window_scores(f)) for spk, f in acc_files]
    omni_win_scores = [get_window_scores(_ROOT / str(r["audio_path"])) for _, r in omni_missed_df.iterrows()]
    vieneu_win_scores = [get_window_scores(_ROOT / str(r["audio_path"])) for _, r in unseen_df.iterrows()]
    dev_bona_win_scores = [get_window_scores(_ROOT / str(r["audio_path"])) for _, r in bona_sample.iterrows()]

    for mode in pooling_modes:
        # Cổng 1
        g1_scores = [pool_scores(ws, mode=mode) for ws in spk1_win_scores]
        g1_pass = sum(1 for s in g1_scores if s > 0)

        # Cổng 2
        g2_scores = [pool_scores(ws, mode=mode) for _, ws in acc_win_scores]
        g2_bona = sum(1 for s in g2_scores if s > 0)
        by_spk = {}
        for spk in spk_acc_dirs:
            spk_sc = [pool_scores(ws, mode=mode) for s_id, ws in acc_win_scores if s_id == spk]
            by_spk[spk] = {
                "total": len(spk_sc),
                "bona": sum(1 for s in spk_sc if s > 0),
                "pass_rate_pct": (sum(1 for s in spk_sc if s > 0) / len(spk_sc) * 100.0) if spk_sc else 0.0,
                "mean_score": float(np.mean(spk_sc)) if spk_sc else 0.0,
            }

        # Cổng 3
        v_sc = [pool_scores(ws, mode=mode) for ws in vieneu_win_scores]
        b_sc = [pool_scores(ws, mode=mode) for ws in dev_bona_win_scores]
        all_sc = np.array(b_sc + v_sc)
        all_lb = np.array([1] * len(b_sc) + [0] * len(v_sc))
        eer, eer_th = compute_eer(all_sc, all_lb)
        min_dcf = compute_min_dcf(all_sc, all_lb)
        v_blocked = sum(1 for s in v_sc if s <= 0)

        # Cổng 4
        o_sc = [pool_scores(ws, mode=mode) for ws in omni_win_scores]
        o_reversed = sum(1 for s in o_sc if s <= 0)

        results[mode] = {
            "gate1_spk0001": {
                "n_pass": g1_pass,
                "total": len(g1_scores),
                "pass_rate_pct": (g1_pass / len(g1_scores)) * 100.0,
                "mean_score": float(np.mean(g1_scores)),
            },
            "gate2_acceptance_5spk": {
                "total_bona": g2_bona,
                "total_files": len(g2_scores),
                "overall_pass_rate_pct": (g2_bona / len(g2_scores)) * 100.0,
                "by_speaker": by_spk,
            },
            "gate3_unseen_vieneu": {
                "eer_pct": float(eer * 100.0),
                "eer_threshold": float(eer_th),
                "min_dcf": float(min_dcf),
                "blocked_count": v_blocked,
                "block_rate_pct": (v_blocked / len(v_sc)) * 100.0,
            },
            "gate4_omnivoice_reversal": {
                "n_reversed": o_reversed,
                "total": len(o_sc),
                "reversal_rate_pct": (o_reversed / len(o_sc)) * 100.0,
            },
        }

    return results


def train_stage3_partial_ft(
    init_ckpt_path: str | Path,
    manifest_csv: str | Path = "data/manifests_zalo/train_v8_balanced_ft.csv",
    out_dir: str | Path = "out/zalo_b_zalo_v8_inverted",
    epochs: int = 1,
    batch_size: int = 8,
    accum_steps: int = 2,
    lr_ssl: float = 5e-7,
    lr_backend: float = 5e-6,
    split_layer: int = 8,
    device: str = "cuda",
) -> Path:
    """Giai đoạn 3: Tinh chỉnh 1 epoch với Partial-Freeze trên tập manifest cân bằng."""
    print("\n" + "=" * 80)
    print(f"🚀 BẮT ĐẦU GIAI ĐOẠN 3: 1-EPOCH PARTIAL-FREEZE FINE-TUNING")
    print(f"   Khởi tạo từ: {init_ckpt_path}")
    print(f"   Tập dữ liệu: {manifest_csv}")
    print("=" * 80)

    model, _ = load_model(str(init_ckpt_path), device=device)
    ssl_trainable, backend_trainable = freeze_lower_ssl(model, split_layer=split_layer)

    df_tr = pd.read_csv(_ROOT / str(manifest_csv))
    n_sp = int((df_tr["label"] == "spoof").sum())
    n_bo = int((df_tr["label"] == "bonafide").sum())
    class_w = loss_weights_from_counts(n_sp, n_bo, clamp_range=(0.35, 0.65))
    weights_t = torch.tensor(class_w, dtype=torch.float32, device=device)

    criterion = AMSoftmaxLoss(
        in_features=model.out.in_features,
        num_classes=2,
        s=30.0,
        m=0.20,  # Margin nhẹ nhàng cho 1-epoch fine-tuning
        weight=weights_t,
    ).to(device)

    optimizer = torch.optim.AdamW(
        [
            {"params": backend_trainable, "lr": lr_backend},
            {"params": ssl_trainable, "lr": lr_ssl},
        ],
        betas=(0.9, 0.98),
        weight_decay=1e-4,
    )

    dataset = ViTrueVoiceDataset(df_tr, audio_root=".", mode="augmented", train=True)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    use_amp = (device == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    model.train()
    total_loss, n_samples = 0.0, 0
    t0 = time.time()
    optimizer.zero_grad(set_to_none=True)

    nb = len(loader)
    for i, batch in enumerate(loader, 1):
        x = batch["wave"].to(device)
        y = batch["label"].to(device)

        with torch.autocast(device_type=device, enabled=use_amp):
            _, emb = model(x, return_embedding=True)
            loss = criterion(emb.float(), y, weight_matrix=model.out.weight)

        scaler.scale(loss / accum_steps).backward()
        total_loss += loss.item() * len(y)
        n_samples += len(y)

        if i % accum_steps == 0 or i == nb:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        if i % 100 == 0 or i == nb:
            pct = (i / nb) * 100
            print(f"   [Stage 3 Ep 1] Batch {i}/{nb} ({pct:.1f}%) | Loss: {total_loss / n_samples:.4f} | Elapsed: {time.time() - t0:.1f}s")

    out_ckpt = _ROOT / str(out_dir) / "checkpoint_stage3_partial_ft.pt"
    out_ckpt.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model.state_dict(),
        "branch": "B_zalo_stage3",
        "phase": 3,
        "epoch": 1,
        "train_loss": total_loss / n_samples,
    }
    if hasattr(model, "model_kwargs"):
        payload["model_kwargs"] = model.model_kwargs
    torch.save(payload, out_ckpt)
    print(f"💾 Đã lưu Checkpoint Giai đoạn 3 thành công tại: {out_ckpt}")
    return out_ckpt


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 80)
    print(f"🔥 BẮT ĐẦU QUY TRÌNH LAI GHÉP TẦNG (STAGE 2) & TINH CHỈNH CÂN BẰNG (STAGE 3) V8")
    print(f"   Device: {device}")
    print("=" * 80)

    ckpt_a_path = _ROOT / "out/zalo_b_zalo_v8_inverted/checkpoint_saved_v8_with_spk1.pt"
    ckpt_b_path = _ROOT / "out/zalo_b_zalo_v8_inverted/checkpoint_phase2_unfrozen_raw.pt"

    if not ckpt_a_path.exists() or not ckpt_b_path.exists():
        raise FileNotFoundError("Không tìm thấy checkpoint A hoặc B trong out/zalo_b_zalo_v8_inverted/")

    # ── BƯỚC 1: XÂY DỰNG MANIFEST CÂN BẰNG (~4.800 DÒNG) ────────────────────
    manifest_ft = build_balanced_ft_manifest()

    dev_manifest = _ROOT / "data/manifests_zalo/dev_v8_f5_omni.csv"
    dev_df = pd.read_csv(dev_manifest)

    # ── BƯỚC 2: TÌM ĐIỂM NGỌT GIAI ĐOẠN 2 (GRID SEARCH GRAFTING) ─────────────
    ck_a = torch.load(ckpt_a_path, map_location="cpu")
    ck_b = torch.load(ckpt_b_path, map_location="cpu")
    sd_a = ck_a["model"]
    sd_b = ck_b["model"]
    model_kwargs = ck_a.get("model_kwargs", {})

    grid = [
        (6, 0.15, 0.85),
        (6, 0.00, 1.00),
        (4, 0.15, 0.90),
        (8, 0.25, 0.85),
    ]

    print("\n🔍 Đang tìm điểm ngọt Layer-Wise Grafting (Giai đoạn 2)...")
    best_combo = None
    best_grafted_sd = None
    best_score = -1e9
    stage2_eval_results = {}

    for split_l, low_a, high_a in grid:
        combo_name = f"split_{split_l}_low_{low_a:.2f}_high_{high_a:.2f}"
        print(f"\n--- Thử nghiệm cấu hình: {combo_name} ---")
        grafted_sd = graft_state_dict(sd_a, sd_b, split_layer=split_l, low_alpha=low_a, high_alpha=high_a)

        model_temp = SSLAASIST(**model_kwargs).to(device)
        model_temp.load_state_dict(grafted_sd)

        eval_res = evaluate_checkpoint_multi_pooling(model_temp, dev_df, pooling_modes=["asymmetric_veto"], device=device)
        av = eval_res["asymmetric_veto"]
        stage2_eval_results[combo_name] = av

        g1_pass = av["gate1_spk0001"]["n_pass"]
        g2_pass = av["gate2_acceptance_5spk"]["overall_pass_rate_pct"]
        g3_eer = av["gate3_unseen_vieneu"]["eer_pct"]
        g4_rev = av["gate4_omnivoice_reversal"]["reversal_rate_pct"]

        print(f"   SPK_0001: {g1_pass}/15 | 5 SPK: {g2_pass:.1f}% | VieNeu EER: {g3_eer:.2f}% | Omni Rev: {g4_rev:.1f}%")

        # Điểm cân bằng tổng thể: ưu tiên G2 >= 90% và tăng tối đa G4 Reversal
        composite_score = g2_pass + (g4_rev * 0.8) + (g1_pass * 2.0) - (g3_eer * 1.5)
        if composite_score > best_score:
            best_score = composite_score
            best_combo = (split_l, low_a, high_a)
            best_grafted_sd = grafted_sd

    print(f"\n🏆 Cấu hình Giai đoạn 2 tối ưu nhất: split_layer={best_combo[0]}, low_alpha={best_combo[1]}, high_alpha={best_combo[2]}")
    ckpt_stage2_path = _ROOT / "out/zalo_b_zalo_v8_inverted/checkpoint_stage2_grafted.pt"
    torch.save({
        "model": best_grafted_sd,
        "branch": "B_zalo_grafted",
        "combo": best_combo,
        "model_kwargs": model_kwargs,
    }, ckpt_stage2_path)
    print(f"💾 Đã lưu Checkpoint Giai đoạn 2 tại: {ckpt_stage2_path}")

    # ── BƯỚC 3: THỰC THI GIAI ĐOẠN 3 (1-EPOCH PARTIAL-FREEZE FINE-TUNING) ─────
    ckpt_stage3_path = train_stage3_partial_ft(
        init_ckpt_path=ckpt_stage2_path,
        manifest_csv="data/manifests_zalo/train_v8_balanced_ft.csv",
        out_dir="out/zalo_b_zalo_v8_inverted",
        epochs=1,
        split_layer=8,
        device=device,
    )

    # ── BƯỚC 4: ĐÁNH GIÁ MA TRẬN TOÀN DIỆN (3 MỐC x 3 POOLING MODES) ──────────
    print("\n" + "=" * 80)
    print("📊 BẮT ĐẦU ĐÁNH GIÁ MA TRẬN ĐỐI CHỨNG (3 MỐC x 3 POOLING MODES)")
    print("=" * 80)

    modes = ["max", "mean", "asymmetric_veto"]
    ablation_report = {}

    # Mốc (a): Checkpoint B + Consensus Veto
    print("\n[Mốc A] Đánh giá Checkpoint B thuần Pha 2...")
    m_b, _ = load_model(str(ckpt_b_path), device=device)
    ablation_report["checkpoint_b_raw"] = evaluate_checkpoint_multi_pooling(m_b, dev_df, modes, device=device)

    # Mốc (b): Giai đoạn 2 Grafted
    print("\n[Mốc B] Đánh giá Checkpoint Giai đoạn 2 Grafted...")
    m_g, _ = load_model(str(ckpt_stage2_path), device=device)
    ablation_report["stage2_grafted"] = evaluate_checkpoint_multi_pooling(m_g, dev_df, modes, device=device)

    # Mốc (c): Giai đoạn 3 Partial-FT
    print("\n[Mốc C] Đánh giá Checkpoint Giai đoạn 3 Partial-FT...")
    m_ft, _ = load_model(str(ckpt_stage3_path), device=device)
    ablation_report["stage3_partial_ft"] = evaluate_checkpoint_multi_pooling(m_ft, dev_df, modes, device=device)

    # ── BƯỚC 5: LỰA CHỌN MÔ HÌNH CHIẾN THẮNG & CẬP NHẬT BEST_MODEL.PT ─────────
    # Quy tắc: nếu GĐ3 đạt Gate 4 >= 75% và Gate 2 >= 90% thì chọn GĐ3, ngược lại chọn checkpoint có điểm hài hòa nhất
    g2_ft = ablation_report["stage3_partial_ft"]["asymmetric_veto"]["gate2_acceptance_5spk"]["overall_pass_rate_pct"]
    g4_ft = ablation_report["stage3_partial_ft"]["asymmetric_veto"]["gate4_omnivoice_reversal"]["reversal_rate_pct"]

    g2_graft = ablation_report["stage2_grafted"]["asymmetric_veto"]["gate2_acceptance_5spk"]["overall_pass_rate_pct"]
    g4_graft = ablation_report["stage2_grafted"]["asymmetric_veto"]["gate4_omnivoice_reversal"]["reversal_rate_pct"]

    print("\n⚖️ ĐỐI SOÁT QUYẾT ĐỊNH MÔ HÌNH:")
    print(f"   Stage 2 Grafted:   Gate 2 = {g2_graft:.1f}% | Gate 4 Reversal = {g4_graft:.1f}%")
    print(f"   Stage 3 Partial-FT: Gate 2 = {g2_ft:.1f}% | Gate 4 Reversal = {g4_ft:.1f}%")

    if g4_ft >= 75.0 and g2_ft >= 90.0:
        winner_key = "stage3_partial_ft"
        winner_path = ckpt_stage3_path
        print(f"🏆 CHỌN GIAI ĐOẠN 3 (Partial-FT) LÀM MÔ HÌNH CHÍNH THỨC!")
    elif (g2_graft >= 90.0 and g4_graft >= g4_ft) or (g2_graft >= g2_ft and g4_graft >= 50.0):
        winner_key = "stage2_grafted"
        winner_path = ckpt_stage2_path
        print(f"🏆 CHỌN GIAI ĐOẠN 2 (Layer-Wise Grafted) LÀM MÔ HÌNH CHÍNH THỨC!")
    else:
        winner_key = "stage3_partial_ft"
        winner_path = ckpt_stage3_path
        print(f"🏆 CHỌN GIAI ĐOẠN 3 (Partial-FT) LÀM MÔ HÌNH CHÍNH THỨC (Cân bằng nhất)!")

    # Cập nhật đè vào best_model.pt
    best_target = _ROOT / "out/zalo_b_zalo_v8_inverted/best_model.pt"
    best_target.write_bytes(winner_path.read_bytes())
    print(f"✅ Đã cập nhật mô hình chiến thắng ({winner_key}) vào: {best_target}")

    # Xuất báo cáo
    ablation_report["winning_model"] = winner_key
    ablation_report["winning_checkpoint"] = str(winner_path)
    ablation_report_path = _ROOT / "benchmarks/v8_pooling_ablation_report.json"
    ablation_report_path.write_text(json.dumps(ablation_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📄 Đã lưu báo cáo ma trận đối chứng chi tiết tại: {ablation_report_path}")

    # Đồng bộ vào v8_inverted_evaluation_report.json
    inv_report_path = _ROOT / "benchmarks/v8_inverted_evaluation_report.json"
    if inv_report_path.exists():
        inv_data = json.load(open(inv_report_path, encoding="utf-8"))
        inv_data["hybrid_remediation"] = {
            "stage2_best_combo": best_combo,
            "winner": winner_key,
            "ablation_results": ablation_report,
        }
        inv_report_path.write_text(json.dumps(inv_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"📄 Đã cập nhật bổ sung vào: {inv_report_path}")

    print("\n🏁 HOÀN TẤT GIAI ĐOẠN 2 & GIAI ĐOẠN 3 THÀNH CÔNG 100%!")


if __name__ == "__main__":
    main()
