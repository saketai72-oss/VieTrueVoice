"""Chỉ số đánh giá cho ViTrueVoice.

Quy ước: nhãn bonafide = 1, spoof = 0; điểm càng cao càng giống bonafide.
"""
from __future__ import annotations
import numpy as np


def _validate(scores, labels):
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels).astype(int)
    if scores.shape != labels.shape:
        raise ValueError("scores và labels phải cùng kích thước")
    if not (np.any(labels == 1) and np.any(labels == 0)):
        raise ValueError("Cần có cả mẫu bonafide và spoof")
    return scores, labels


def compute_det_curve(scores, labels):
    """Trả về (far, frr, thresholds) tại mọi ngưỡng duy nhất.

    far: tỷ lệ spoof bị nhận nhầm là bonafide (score >= thr)
    frr: tỷ lệ bonafide bị từ chối nhầm (score < thr)
    """
    scores, labels = _validate(scores, labels)
    bona = np.sort(scores[labels == 1])
    spoof = np.sort(scores[labels == 0])
    thr = np.unique(scores)
    # thêm ngưỡng cực biên để đường cong đi từ (1,0) đến (0,1)
    thr = np.concatenate(([thr[0] - 1.0], thr, [thr[-1] + 1.0]))
    far = 1.0 - np.searchsorted(spoof, thr, side="left") / len(spoof)
    frr = np.searchsorted(bona, thr, side="left") / len(bona)
    return far, frr, thr


def compute_eer(scores, labels):
    """Trả về (eer, threshold) bằng nội suy tại điểm FAR = FRR."""
    far, frr, thr = compute_det_curve(scores, labels)
    diff = far - frr
    idx = np.where(diff <= 0)[0][0]  # FAR - FRR đổi dấu lần đầu
    if idx == 0:
        return float((far[0] + frr[0]) / 2), float(thr[0])
    d0, d1 = diff[idx - 1], diff[idx]
    w = d0 / (d0 - d1) if d0 != d1 else 0.5
    eer = far[idx - 1] + w * (far[idx] - far[idx - 1])
    eer_thr = thr[idx - 1] + w * (thr[idx] - thr[idx - 1])
    return float(eer), float(eer_thr)


def compute_min_dcf(scores, labels, c_miss=1.0, c_fa=1.0, p_spoof=0.05):
    """minDCF chuẩn hóa. 'Miss' = bonafide bị loại; 'FA' = spoof lọt qua.

    Cần đối chiếu p_spoof, c_miss, c_fa với đề cương của GVHD.
    """
    far, frr, _ = compute_det_curve(scores, labels)
    p_bona = 1.0 - p_spoof
    dcf = c_miss * p_bona * frr + c_fa * p_spoof * far
    default = min(c_miss * p_bona, c_fa * p_spoof)
    return float(dcf.min() / default)


def confusion_at_threshold(scores, labels, threshold):
    """Ma trận 2x2: hàng = nhãn thật (spoof, bonafide), cột = dự đoán."""
    scores, labels = _validate(scores, labels)
    pred = (scores >= threshold).astype(int)
    cm = np.zeros((2, 2), dtype=int)
    for t, p in zip(labels, pred):
        cm[t, p] += 1
    return cm


def cluster_bootstrap_ci(scores, labels, groups, n_boot=1000,
                         alpha=0.05, seed=0, metric="eer"):
    """Khoảng tin cậy bootstrap theo cụm (resample theo người nói)."""
    scores, labels = _validate(scores, labels)
    groups = np.asarray(groups)
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    idx_by_group = {g: np.where(groups == g)[0] for g in uniq}
    vals = []
    while len(vals) < n_boot:
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_group[g] for g in pick])
        lb = labels[idx]
        if lb.min() == lb.max():
            continue  # lần lấy mẫu thiếu 1 lớp, bỏ qua
        if metric == "eer":
            vals.append(compute_eer(scores[idx], lb)[0])
        else:
            vals.append(compute_min_dcf(scores[idx], lb))
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)
