import torch
import torch.nn as nn


def weighted_ce(weights, reduction="mean"):
    """CE có trọng số. weights theo thứ tự chỉ số lớp: [spoof(0), bonafide(1)]."""
    if len(weights) != 2:
        raise ValueError("Cần đúng 2 trọng số: [spoof, bonafide]")
    return nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32),
                               reduction=reduction)


def loss_weights_from_counts(n_spoof, n_bonafide):
    """w_c = N / (2 N_c), chuẩn hóa tổng = 1. Thứ tự: [spoof(0), bonafide(1)]."""
    if n_spoof <= 0 or n_bonafide <= 0:
        raise ValueError("Mỗi lớp cần ít nhất 1 mẫu")
    raw = [1.0 / n_spoof, 1.0 / n_bonafide]
    s = sum(raw)
    return [r / s for r in raw]
