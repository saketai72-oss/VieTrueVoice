#!/usr/bin/env python3
"""Chạy toàn bộ 4 Folds thử nghiệm thăm dò Leave-One-Speaker-Out (LOSO).
Tuân thủ nghiêm ngặt Đặc tả tiên nghiệm: docs/SPEC_loso_exploratory_ablation.md (v1.1.0).

Ma trận thử nghiệm (48 lượt chạy):
- 4 Folds:
    Fold 1: Giữ SPK_0001 (15 câu gốc) | Train: Replay + {SPK_0003, 0004, 0005, 0006, 0007}
    Fold 2: Giữ SPK_0003 (20 câu gốc) | Train: Replay + {SPK_0001, 0004, 0005, 0006, 0007}
    Fold 3: Giữ SPK_0004 (14 câu gốc) | Train: Replay + {SPK_0001, 0003, 0005, 0006, 0007}
    Fold 4: Giữ SPK_0006 (10 câu gốc) | Train: Replay + {SPK_0001, 0003, 0004, 0005, 0007}
- 2 Cấu hình:
    Config 1 (Standard Head Tuning — Primary): lr=5e-5, weight_decay=1e-4, s=30, m=0.20, steps=600, bs=8
    Config 2 (Aggressive Head Adaptation — Secondary): lr=2e-4, weight_decay=1e-4, s=30, m=0.20, steps=600, bs=8
- 3 Seeds: 42, 123, 2026
- 2 Nhánh:
    Experimental (2 vol bona + 2 vol spoof F5 + 2 replay bona + 2 replay spoof)
    Control Replay-only (4 replay bona + 4 replay spoof)

Thước đo và Tiêu chí thành công cho Config 1 (Standard):
1. Mean Delta s_utt >= +3.0
2. Bootstrap 95% CI lower > 0
3. Pass rate (s_utt > theta_cal) tăng >= +15.0 percentage points tuyệt đối vs baseline
4. An ninh không thoái lui: Dev EER <= 2.05%, APCER nom delta <= +1.5%, APCER worst delta <= +3.0%
5. Thành công khi >= 3/4 folds đạt đồng thời các tiêu chí trên.
"""

import sys
import time
import copy
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.eval_ssl_aasist import load_model
from src.training.losses import AMSoftmaxLoss
from src.evaluation.metrics import compute_eer


class SSLHead(nn.Module):
    """Mô-đun Head có thể huấn luyện (458.950 tham số) tách biệt khỏi encoder."""
    def __init__(self, m):
        super().__init__()
        self.proj = copy.deepcopy(m.frontend.proj)
        self.bn_in = copy.deepcopy(m.bn_in)
        self.conv = copy.deepcopy(m.conv)
        self.gat_s = copy.deepcopy(m.gat_s)
        self.gat_t = copy.deepcopy(m.gat_t)
        self.master = nn.Parameter(m.master.data.clone())
        self.hs = copy.deepcopy(m.hs)
        self.drop = copy.deepcopy(m.drop)
        self.out = copy.deepcopy(m.out)

    def backend(self, feats, return_embedding: bool = False):
        x = F.max_pool2d(feats.transpose(1, 2).unsqueeze(1), (3, 3))  # (B,1,D/3,T/3)
        x = self.conv(F.selu(self.bn_in(x)))                          # (B,C,F,T')
        g_s = self.gat_s(x.abs().amax(dim=3).transpose(1, 2))         # (B,F,d)
        g_t = self.gat_t(x.abs().amax(dim=2).transpose(1, 2))         # (B,T',d)
        master = self.master.expand(x.size(0), -1, -1)
        for layer in self.hs:
            g_t, g_s, master = layer(g_t, g_s, master)
        h = torch.cat([g_t.abs().amax(1), g_t.mean(1),
                       g_s.abs().amax(1), g_s.mean(1), master.squeeze(1)], dim=1)
        emb = self.drop(h)
        logits = self.out(emb)
        if return_embedding:
            return logits, emb
        return logits

    def forward(self, h, return_embedding: bool = False):
        # h: (B, 199, 768)
        x_proj = self.proj(h)
        return self.backend(x_proj, return_embedding=return_embedding)

    def score(self, h):
        logits = self.forward(h)
        return logits[:, 1] - logits[:, 0]


def evaluate_features_through_head(head, features, device, batch_size=32):
    """Tính điểm suy luận qua Head cho tensor đặc trưng (N, 199, 768)."""
    head.eval()
    scores = []
    n = len(features)
    with torch.no_grad():
        for i in range(0, n, batch_size):
            batch_h = features[i : i + batch_size].to(device).float()
            sc = head.score(batch_h).cpu().numpy().tolist()
            if isinstance(sc, float):
                sc = [sc]
            scores.extend(sc)
    return np.array(scores, dtype=np.float32)


def evaluate_dev_cached(head, cache_dir, device, batch_size=32):
    """Đánh giá toàn bộ 11.450 mẫu Dev Zalo bằng mmap."""
    all_scores = []
    for p_idx in range(4):
        p_path = cache_dir / f"dev_zalo_part{p_idx}.pt"
        p_data = torch.load(p_path, weights_only=False, mmap=True)
        feats = p_data["features"]
        scs = evaluate_features_through_head(head, feats, device, batch_size=batch_size)
        all_scores.append(scs)
    return np.concatenate(all_scores)


def evaluate_dev_offsets_cached(head, cache_dir, device, batch_size=32):
    """Đánh giá toàn bộ 10.560 mẫu Dev Spoof Offsets bằng mmap."""
    all_scores = []
    for p_idx in range(3):
        p_path = cache_dir / f"dev_spoof_offsets_part{p_idx}.pt"
        p_data = torch.load(p_path, weights_only=False, mmap=True)
        feats = p_data["features"]
        scs = evaluate_features_through_head(head, feats, device, batch_size=batch_size)
        all_scores.append(scs)
    return np.concatenate(all_scores)


def compute_calibrated_threshold(bona_scores, max_bpcer=0.01):
    """Tính ngưỡng hiệu chỉnh theta_cal sao cho BPCER <= max_bpcer (1.0%)."""
    bona_sorted = np.sort(bona_scores)
    idx = int(np.floor(max_bpcer * len(bona_sorted)))
    idx = min(idx, len(bona_sorted) - 1)
    return float(bona_sorted[idx])


def compute_metrics(dev_bona_scores, dev_spoof_scores, dev_spoof_offset_dict=None):
    """Tính toán toàn diện chỉ số Dev: EER, theta_cal, APCER danh định, APCER worst-case."""
    all_scores = np.concatenate([dev_bona_scores, dev_spoof_scores])
    all_labels = np.concatenate([np.ones(len(dev_bona_scores), dtype=int), np.zeros(len(dev_spoof_scores), dtype=int)])
    eer, thresh_eer = compute_eer(all_scores, all_labels)
    theta_cal = compute_calibrated_threshold(dev_bona_scores, max_bpcer=0.01)
    
    # APCER tại theta_cal (tỷ lệ spoof bị nhận nhầm là bona fide, tức score > theta_cal)
    apcer_nom = float(np.mean(dev_spoof_scores > theta_cal) * 100)
    
    apcer_worst = apcer_nom
    if dev_spoof_offset_dict is not None and len(dev_spoof_offset_dict) > 0:
        apcer_list = []
        for off, scs in dev_spoof_offset_dict.items():
            apcer_list.append(float(np.mean(scs > theta_cal) * 100))
        apcer_worst = max(apcer_list)

    return {
        "eer": eer * 100,
        "thresh_eer": thresh_eer,
        "theta_cal": theta_cal,
        "apcer_nom": apcer_nom,
        "apcer_worst": apcer_worst,
    }


def bootstrap_ci(deltas, n_boot=1000, seed=42):
    """Tính khoảng tin cậy Bootstrap 95% cho trung bình delta theo câu thoại."""
    if len(deltas) == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    boot_means = []
    n = len(deltas)
    for _ in range(n_boot):
        sample = rng.choice(deltas, size=n, replace=True)
        boot_means.append(np.mean(sample))
    mean_val = float(np.mean(deltas))
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return mean_val, ci_lower, ci_upper


def train_head_run(
    initial_head_state,
    base_head_template,
    train_data_dict,
    config,
    seed,
    branch,
    device,
):
    """Huấn luyện 1 lượt Head trong 600 steps với AM-Softmax Loss."""
    # Khởi tạo mô hình Head từ trọng số gốc
    head = copy.deepcopy(base_head_template).to(device)
    head.load_state_dict(initial_head_state)
    head.train()

    torch.manual_seed(seed)
    np.random.seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)

    criterion = AMSoftmaxLoss(
        in_features=320,
        num_classes=2,
        s=config["am_s"],
        m=config["am_m"],
        weight=None,
    ).to(device)

    optimizer = torch.optim.AdamW(
        head.parameters(),
        lr=config["lr"],
        betas=(0.9, 0.999),
        weight_decay=config["weight_decay"],
    )

    rng = np.random.default_rng(seed)
    steps = config["steps"]
    batch_size = config["batch_size"]

    # Dữ liệu Replay
    replay_bona_feats = train_data_dict["replay_bona_feats"]
    replay_spoof_feats = train_data_dict["replay_spoof_feats"]
    n_rb = len(replay_bona_feats)
    n_rs = len(replay_spoof_feats)

    # Dữ liệu Volunteer (cho experimental branch)
    vol_bona_feats = train_data_dict.get("vol_bona_feats", None)
    vol_spoof_feats = train_data_dict.get("vol_spoof_feats", None)
    n_vb = len(vol_bona_feats) if vol_bona_feats is not None else 0
    n_vs = len(vol_spoof_feats) if vol_spoof_feats is not None else 0

    t0 = time.time()
    for step in range(steps):
        if branch == "experimental":
            # 2 vol bona + 2 vol spoof + 2 replay bona + 2 replay spoof
            vb_idx = rng.integers(0, n_vb, size=2)
            vs_idx = rng.integers(0, n_vs, size=2)
            rb_idx = rng.integers(0, n_rb, size=2)
            rs_idx = rng.integers(0, n_rs, size=2)

            b_feats = torch.cat([
                vol_bona_feats[vb_idx],
                vol_spoof_feats[vs_idx],
                replay_bona_feats[rb_idx],
                replay_spoof_feats[rs_idx],
            ], dim=0)
            b_targets = torch.tensor([1, 1, 0, 0, 1, 1, 0, 0], dtype=torch.long, device=device)
        else:
            # Replay-only: 4 replay bona + 4 replay spoof
            rb_idx = rng.integers(0, n_rb, size=4)
            rs_idx = rng.integers(0, n_rs, size=4)

            b_feats = torch.cat([
                replay_bona_feats[rb_idx],
                replay_spoof_feats[rs_idx],
            ], dim=0)
            b_targets = torch.tensor([1, 1, 1, 1, 0, 0, 0, 0], dtype=torch.long, device=device)

        b_feats = b_feats.to(device).float()
        optimizer.zero_grad()
        _, emb = head(b_feats, return_embedding=True)
        loss = criterion(emb.float(), b_targets, weight_matrix=head.out.weight)
        loss.backward()
        nn.utils.clip_grad_norm_(head.parameters(), max_norm=1.0)
        optimizer.step()

    train_dt = time.time() - t0
    head.eval()
    return head, train_dt


def run_full_loso():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("=" * 80)
    print("🚀 BẮT ĐẦU CHẠY TOÀN DIỆN THỬ NGHIỆM THĂM DÒ LOSO 4 FOLDS (SPEC v1.1.0)")
    print(f"   Thiết bị: {device}")
    print("=" * 80)

    # 1. Nạp Baseline Checkpoint
    ckpt_path = "out/best_model_B_zalo.pt"
    base_model, _ = load_model(ckpt_path, device=device)
    base_model.eval()
    base_model.freeze_ssl()

    base_head_template = SSLHead(base_model).to(device)
    initial_head_state = copy.deepcopy(base_head_template.state_dict())
    print(f"✅ Đã trích xuất Head ban đầu: {sum(p.numel() for p in base_head_template.parameters())} tham số.", flush=True)

    cache_dir = Path("data/cache_loso_fp16")
    assert cache_dir.exists(), "Thư mục cache không tồn tại!"

    # 2. Đọc metadata Dev Zalo
    print("📥 Đọc metadata Dev Zalo...", flush=True)
    dev_meta_list = []
    for p_idx in range(4):
        p_data = torch.load(cache_dir / f"dev_zalo_part{p_idx}.pt", weights_only=False, mmap=True)
        dev_meta_list.extend(p_data["metadata"])
    dev_df = pd.DataFrame(dev_meta_list)
    dev_bona_mask = (dev_df["label"] == 1).values
    dev_spoof_mask = (dev_df["label"] == 0).values

    # 3. Đọc metadata Dev Spoof Offsets
    print("📥 Đọc metadata Dev Spoof Offsets...", flush=True)
    off_meta_list = []
    for p_idx in range(3):
        p_data = torch.load(cache_dir / f"dev_spoof_offsets_part{p_idx}.pt", weights_only=False, mmap=True)
        off_meta_list.extend(p_data["metadata"])
    dev_spoof_off_df = pd.DataFrame(off_meta_list)

    # 4. Nạp Replay Features vào RAM (1.40 GB)
    print("📥 Nạp dữ liệu bộ đệm Replay Buffer...", flush=True)
    replay_data = torch.load(cache_dir / "replay_buffer.pt", weights_only=False)
    replay_features = replay_data["features"]
    replay_df = pd.DataFrame(replay_data["metadata"])
    replay_bona_feats = replay_features[replay_df["label"] == 1]
    replay_spoof_feats = replay_features[replay_df["label"] == 0]

    # 5. Nạp Volunteers Features vào RAM (392 MB)
    print("📥 Nạp dữ liệu bộ đệm Volunteers...", flush=True)
    vol_data = torch.load(cache_dir / "volunteers.pt", weights_only=False)
    vol_features = vol_data["features"]
    vol_df = pd.DataFrame(vol_data["metadata"])

    # 6. Đánh giá Baseline Checkpoint ban đầu
    print("\n🔍 Đánh giá Baseline Checkpoint (ckpt-49k-pitchaug)...", flush=True)
    base_dev_scores = evaluate_dev_cached(base_head_template, cache_dir, device)
    base_dev_bona = base_dev_scores[dev_bona_mask]
    base_dev_spoof = base_dev_scores[dev_spoof_mask]

    base_dev_spoof_off_scores = evaluate_dev_offsets_cached(base_head_template, cache_dir, device)
    dev_spoof_off_df["score"] = base_dev_spoof_off_scores
    base_off_dict = {
        off: dev_spoof_off_df[dev_spoof_off_df["offset_sec"] == off]["score"].values
        for off in dev_spoof_off_df["offset_sec"].unique()
    }

    base_metrics = compute_metrics(base_dev_bona, base_dev_spoof, base_off_dict)
    theta_cal_base = base_metrics["theta_cal"]
    print(f"   Baseline Dev EER:        {base_metrics['eer']:.2f}%", flush=True)
    print(f"   Baseline theta_cal:      {theta_cal_base:+.4f}", flush=True)
    print(f"   Baseline APCER nom:      {base_metrics['apcer_nom']:.2f}%", flush=True)
    print(f"   Baseline APCER worst:    {base_metrics['apcer_worst']:.2f}%", flush=True)

    # Baseline điểm câu thoại của các tình nguyện viên
    base_vol_scores = evaluate_features_through_head(base_head_template, vol_features, device)
    vol_df["base_score"] = base_vol_scores

    # Định nghĩa 4 Folds
    FOLDS = {
        1: {"held_out": "SPK_0001", "train_spks": ["SPK_0003", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]},
        2: {"held_out": "SPK_0003", "train_spks": ["SPK_0001", "SPK_0004", "SPK_0005", "SPK_0006", "SPK_0007"]},
        3: {"held_out": "SPK_0004", "train_spks": ["SPK_0001", "SPK_0003", "SPK_0005", "SPK_0006", "SPK_0007"]},
        4: {"held_out": "SPK_0006", "train_spks": ["SPK_0001", "SPK_0003", "SPK_0004", "SPK_0005", "SPK_0007"]},
    }

    CONFIGS = {
        "Config 1 (Standard - Primary)": {
            "lr": 5e-5, "weight_decay": 1e-4, "am_s": 30.0, "am_m": 0.20, "steps": 600, "batch_size": 8, "role": "primary"
        },
        "Config 2 (Aggressive - Secondary)": {
            "lr": 2e-4, "weight_decay": 1e-4, "am_s": 30.0, "am_m": 0.20, "steps": 600, "batch_size": 8, "role": "secondary"
        },
    }

    SEEDS = [42, 123, 2026]

    # Lưu kết quả chi tiết từng run
    records = []

    print("\n" + "=" * 80, flush=True)
    print("🏃 TIẾN HÀNH CHẠY 48 LƯỢT HUẤN LUYỆN VÀ ĐÁNH GIÁ ĐỐI CHỨNG...", flush=True)
    print("=" * 80, flush=True)

    total_runs = len(FOLDS) * len(CONFIGS) * len(SEEDS) * 2
    run_idx = 0

    for fold_id, fold_info in FOLDS.items():
        held_out_spk = fold_info["held_out"]
        train_spks = fold_info["train_spks"]

        # Tập train volunteer (bona + F5-TTS spoof, cấm tuyệt đối VieNeu-TTS)
        vol_train_bona_mask = (vol_df["speaker"].isin(train_spks)) & (vol_df["kind"] == "bonafide")
        vol_train_spoof_mask = (vol_df["speaker"].isin(train_spks)) & (vol_df["kind"] == "spoof_f5tts")

        train_data_dict = {
            "replay_bona_feats": replay_bona_feats,
            "replay_spoof_feats": replay_spoof_feats,
            "vol_bona_feats": vol_features[vol_train_bona_mask],
            "vol_spoof_feats": vol_features[vol_train_spoof_mask],
        }

        # Tập kiểm thử của held-out speaker
        held_bona_mask = (vol_df["speaker"] == held_out_spk) & (vol_df["kind"] == "bonafide")
        held_bona_feats = vol_features[held_bona_mask]
        held_bona_meta = vol_df[held_bona_mask].copy()

        held_vn_mask = (vol_df["speaker"] == held_out_spk) & (vol_df["kind"] == "spoof_vieneu")
        held_vn_feats = vol_features[held_vn_mask]

        # Đo baseline rate P0 trên held-out bona fide
        held_bona_meta["s_base"] = held_bona_meta["base_score"]
        base_utt_scores_base = held_bona_meta.groupby("base_utt")["s_base"].mean()
        p0_base_pass_rate = float(np.mean(base_utt_scores_base > theta_cal_base) * 100)

        for cfg_name, cfg in CONFIGS.items():
            for seed in SEEDS:
                # 1. Huấn luyện Experimental Branch
                run_idx += 1
                head_exp, dt_exp = train_head_run(initial_head_state, base_head_template, train_data_dict, cfg, seed, "experimental", device)
                
                # 2. Huấn luyện Control Replay Branch
                run_idx += 1
                head_rep, dt_rep = train_head_run(initial_head_state, base_head_template, train_data_dict, cfg, seed, "replay_control", device)

                # 3. Đánh giá trên Dev Zalo cho cả 2 nhánh
                # Exp
                exp_dev_scores = evaluate_dev_cached(head_exp, cache_dir, device)
                exp_dev_bona = exp_dev_scores[dev_bona_mask]
                exp_dev_spoof = exp_dev_scores[dev_spoof_mask]
                # Offsets
                exp_dev_spoof_off = evaluate_dev_offsets_cached(head_exp, cache_dir, device)
                dev_spoof_off_df["score_exp"] = exp_dev_spoof_off
                exp_off_dict = {
                    off: dev_spoof_off_df[dev_spoof_off_df["offset_sec"] == off]["score_exp"].values
                    for off in dev_spoof_off_df["offset_sec"].unique()
                }
                exp_metrics = compute_metrics(exp_dev_bona, exp_dev_spoof, exp_off_dict)
                theta_cal_exp = exp_metrics["theta_cal"]

                # Control Replay
                rep_dev_scores = evaluate_dev_cached(head_rep, cache_dir, device)
                rep_dev_bona = rep_dev_scores[dev_bona_mask]
                rep_dev_spoof = rep_dev_scores[dev_spoof_mask]
                rep_dev_spoof_off = evaluate_dev_offsets_cached(head_rep, cache_dir, device)
                dev_spoof_off_df["score_rep"] = rep_dev_spoof_off
                rep_off_dict = {
                    off: dev_spoof_off_df[dev_spoof_off_df["offset_sec"] == off]["score_rep"].values
                    for off in dev_spoof_off_df["offset_sec"].unique()
                }
                rep_metrics = compute_metrics(rep_dev_bona, rep_dev_spoof, rep_off_dict)
                theta_cal_rep = rep_metrics["theta_cal"]

                # 4. Đánh giá trên Held-out Speaker Bona Fide
                held_bona_meta["s_exp"] = evaluate_features_through_head(head_exp, held_bona_feats, device)
                held_bona_meta["s_rep"] = evaluate_features_through_head(head_rep, held_bona_feats, device)

                # Tính s_utt (trung bình qua các codecs của từng base_utt)
                utt_df = held_bona_meta.groupby("base_utt")[["s_exp", "s_rep", "s_base"]].mean().reset_index()
                utt_df["delta_s"] = utt_df["s_exp"] - utt_df["s_rep"]

                mean_delta, ci_lower, ci_upper = bootstrap_ci(utt_df["delta_s"].values, n_boot=1000, seed=seed)
                pass_rate_exp = float(np.mean(utt_df["s_exp"] > theta_cal_exp) * 100)
                pass_rate_rep = float(np.mean(utt_df["s_rep"] > theta_cal_rep) * 100)
                delta_pass_rate_abs = pass_rate_exp - p0_base_pass_rate

                # 5. Đánh giá H2 VieNeu-TTS (Unseen TTS trade-off)
                held_vn_scores = evaluate_features_through_head(head_exp, held_vn_feats, device)
                apcer_h2_vn = float(np.mean(held_vn_scores > theta_cal_exp) * 100)

                # 6. Kiểm tra các điều kiện thành công (cho Config 1 Standard)
                cond1_mean_delta = bool(mean_delta >= 3.0)
                cond2_ci_lower = bool(ci_lower > 0.0)
                cond3_pass_rate = bool(delta_pass_rate_abs >= 15.0)
                cond4_security = bool(
                    (exp_metrics["eer"] <= 2.05) and
                    ((exp_metrics["apcer_nom"] - base_metrics["apcer_nom"]) <= 1.5) and
                    ((exp_metrics["apcer_worst"] - base_metrics["apcer_worst"]) <= 3.0)
                )
                fold_passed = bool(cond1_mean_delta and cond2_ci_lower and cond3_pass_rate and cond4_security)

                rec = {
                    "fold": fold_id,
                    "held_out": held_out_spk,
                    "config": cfg_name,
                    "role": cfg["role"],
                    "seed": seed,
                    "p0_base_pass_rate": p0_base_pass_rate,
                    "mean_delta_s": mean_delta,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "pass_rate_exp": pass_rate_exp,
                    "pass_rate_rep": pass_rate_rep,
                    "delta_pass_rate_abs": delta_pass_rate_abs,
                    "dev_eer_exp": exp_metrics["eer"],
                    "theta_cal_exp": theta_cal_exp,
                    "apcer_nom_exp": exp_metrics["apcer_nom"],
                    "apcer_worst_exp": exp_metrics["apcer_worst"],
                    "dev_eer_rep": rep_metrics["eer"],
                    "theta_cal_rep": theta_cal_rep,
                    "apcer_nom_rep": rep_metrics["apcer_nom"],
                    "apcer_worst_rep": rep_metrics["apcer_worst"],
                    "apcer_h2_vn": apcer_h2_vn,
                    "cond1_mean_delta": cond1_mean_delta,
                    "cond2_ci_lower": cond2_ci_lower,
                    "cond3_pass_rate": cond3_pass_rate,
                    "cond4_security": cond4_security,
                    "fold_passed": fold_passed,
                }
                records.append(rec)
                log_line = (
                    f"[{run_idx:2d}/{total_runs:2d}] Fold {fold_id} ({held_out_spk}) | {cfg_name[:8]} | Seed {seed:4d} | "
                    f"Δs: {mean_delta:+5.2f} (CI [{ci_lower:+5.2f}, {ci_upper:+5.2f}]) | "
                    f"Pass: {pass_rate_exp:4.1f}% (Δ {delta_pass_rate_abs:+4.1f}pp) | "
                    f"EER: {exp_metrics['eer']:.2f}% | Pass? {fold_passed}"
                )
                print(log_line, flush=True)
                with open("out/loso_live_progress.txt", "a", encoding="utf-8") as f_prog:
                    f_prog.write(log_line + "\n")

    res_df = pd.DataFrame(records)
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    res_csv = out_dir / "loso_4folds_results.csv"
    res_df.to_csv(res_csv, index=False)
    print(f"\n📁 Đã lưu toàn bộ kết quả 48 lượt chạy vào: {res_csv}", flush=True)

    # 7. Tổng hợp kết quả theo từng cấu hình
    print("\n" + "=" * 80, flush=True)
    print("📊 TỔNG HỢP KẾT QUẢ THỬ NGHIỆM THEO TIÊU CHÍ TIÊN NGHIỆM SPEC v1.1.0", flush=True)
    print("=" * 80, flush=True)

    summary_lines = []
    summary_lines.append("# BÁO CÁO TỔNG HỢP THỬ NGHIỆM THĂM DÒ LOSO 4 FOLDS (SPEC v1.1.0)\n")
    summary_lines.append(f"- **Ngày thực hiện**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append(f"- **Thiết bị**: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    summary_lines.append(f"- **Baseline Checkpoint**: `out/best_model_B_zalo.pt` (`ckpt-49k-pitchaug`)")
    summary_lines.append(f"  * Baseline Dev EER: {base_metrics['eer']:.2f}% | θ_cal = {theta_cal_base:+.4f} | APCER nom = {base_metrics['apcer_nom']:.2f}%\n")

    for cfg_name, cfg in CONFIGS.items():
        sub_df = res_df[res_df["config"] == cfg_name]
        is_primary = cfg["role"] == "primary"
        role_label = "PRIMARY (QUYẾT ĐỊNH CHÍNH)" if is_primary else "SECONDARY (THAM CHIẾU PHỤ)"
        print(f"\n📌 CẤU HÌNH: {cfg_name} — [{role_label}]", flush=True)
        summary_lines.append(f"## Cấu hình: {cfg_name} — [{role_label}]\n")

        # Bảng tổng hợp theo fold (trung bình qua 3 seeds)
        summary_lines.append("| Fold | Held-out | P0 Baseline | Mean Δs | CI 95% Cận Dưới | Tỷ lệ Vượt Ngưỡng (Exp) | Mức tăng Tuyệt đối (Δpp) | Dev EER | APCER Nom | APCER Worst | H2 VieNeu APCER | Đạt Cả 4 Tiêu Chí? |")
        summary_lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")

        passed_folds = 0
        for fold_id in FOLDS:
            f_df = sub_df[sub_df["fold"] == fold_id]
            held_spk = f_df["held_out"].iloc[0]
            p0 = f_df["p0_base_pass_rate"].mean()
            m_delta = f_df["mean_delta_s"].mean()
            ci_l = f_df["ci_lower"].mean()
            p_exp = f_df["pass_rate_exp"].mean()
            d_pp = f_df["delta_pass_rate_abs"].mean()
            eer = f_df["dev_eer_exp"].mean()
            apc_nom = f_df["apcer_nom_exp"].mean()
            apc_worst = f_df["apcer_worst_exp"].mean()
            h2_vn = f_df["apcer_h2_vn"].mean()

            # Pass nếu đa số seeds pass
            fold_pass_count = f_df["fold_passed"].sum()
            fold_ok = fold_pass_count >= 2
            if fold_ok:
                passed_folds += 1

            status_str = f"✅ ĐẠT ({fold_pass_count}/3 seeds)" if fold_ok else f"❌ KHÔNG ({fold_pass_count}/3 seeds)"
            line_str = (
                f"| Fold {fold_id} | `{held_spk}` | {p0:.1f}% | {m_delta:+.2f} | {ci_l:+.2f} | "
                f"{p_exp:.1f}% | {d_pp:+.1f} pp | {eer:.2f}% | {apc_nom:.2f}% | {apc_worst:.2f}% | {h2_vn:.2f}% | {status_str} |"
            )
            print("   " + line_str, flush=True)
            summary_lines.append(line_str)

        rule5_passed = (passed_folds >= 3)
        conclusion_str = (
            f"🎉 **KẾT LUẬN TIÊN NGHIỆM**: ĐẠT MỤC TIÊU ({passed_folds}/4 folds pass >= 3/4) -> Có tín hiệu chuyển giao tổng quát hóa."
            if rule5_passed else
            f"⚠️ **KẾT LUẬN TIÊN NGHIỆM**: KHÔNG ĐẠT ({passed_folds}/4 folds pass < 3/4) -> Giả thuyết chuyển giao bị bác bỏ; việc vá theo từng cá nhân không tổng quát hóa."
        )
        print(f"\n   -> Kết quả: {passed_folds}/4 folds đạt.", flush=True)
        print(f"   -> {conclusion_str}\n", flush=True)
        summary_lines.append(f"\n**Kết quả tổng hợp**: {passed_folds}/4 folds đạt tiêu chuẩn.")
        summary_lines.append(f"**Kết luận**: {conclusion_str}\n")

    summary_md = out_dir / "loso_4folds_summary.md"
    summary_md.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\n📝 Đã lưu báo cáo tổng hợp Markdown vào: {summary_md}", flush=True)


if __name__ == "__main__":
    run_full_loso()
