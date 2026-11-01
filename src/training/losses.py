import torch
import torch.nn as nn
import torch.nn.functional as F


def weighted_ce(weights, reduction="mean"):
    """CE có trọng số. weights theo thứ tự chỉ số lớp: [spoof(0), bonafide(1)]."""
    if len(weights) != 2:
        raise ValueError("Cần đúng 2 trọng số: [spoof, bonafide]")
    return nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32),
                               reduction=reduction)


def loss_weights_from_counts(n_spoof, n_bonafide, clamp_range: tuple[float, float] | None = None):
    """w_c = N / (2 N_c), chuẩn hóa tổng = 1. Thứ tự: [spoof(0), bonafide(1)].
    
    Hỗ trợ clamp_range (ví dụ [0.35, 0.65]) để tránh phạt quá cực đoan khi tỷ lệ spoof rất nhỏ.
    """
    if n_spoof <= 0 or n_bonafide <= 0:
        raise ValueError("Mỗi lớp cần ít nhất 1 mẫu")
    raw = [1.0 / n_spoof, 1.0 / n_bonafide]
    s = sum(raw)
    w = [r / s for r in raw]
    if clamp_range is not None:
        low, high = clamp_range
        w = [min(max(x, low), high) for x in w]
        s = sum(w)
        w = [r / s for r in w]
    return w


class AMSoftmaxLoss(nn.Module):
    """Additive Margin Softmax (AM-Softmax) Loss for ASVspoof / AASIST.
    
    L = -log( e^{s * (cos(theta_y) - m)} / ( e^{s * (cos(theta_y) - m)} + sum_{j != y} e^{s * cos(theta_j)} ) )
    
    Supports:
    - Internal learnable weight matrix W (shape: [num_classes, in_features])
    - External weight matrix (e.g. model.out.weight) passed at forward time
    - Optional class weights [w_spoof, w_bona] for class imbalance handling
    """

    def __init__(
        self,
        in_features: int = 320,
        num_classes: int = 2,
        s: float = 30.0,
        m: float = 0.35,
        weight: torch.Tensor | None = None,
    ):
        super().__init__()
        self.in_features = in_features
        self.num_classes = num_classes
        self.s = s
        self.m = m
        self.register_buffer("weight", weight if weight is not None else None)
        self.W = nn.Parameter(torch.randn(num_classes, in_features))
        nn.init.xavier_uniform_(self.W)
        self.eps = 1e-7

    def forward(
        self,
        feats: torch.Tensor,
        targets: torch.Tensor,
        weight_matrix: torch.Tensor | None = None,
    ) -> torch.Tensor:
        # 1. Normalize features (B, D)
        x_norm = F.normalize(feats, p=2, dim=1, eps=self.eps)

        # 2. Normalize weights (C, D)
        W = weight_matrix if weight_matrix is not None else self.W
        w_norm = F.normalize(W, p=2, dim=1, eps=self.eps)

        # 3. Compute cosine similarity (B, C)
        costheta = F.linear(x_norm, w_norm)
        costheta = torch.clamp(costheta, -1.0 + self.eps, 1.0 - self.eps)

        # 4. Subtract additive margin from target class
        target_mask = torch.zeros_like(costheta)
        target_mask.scatter_(1, targets.view(-1, 1).long(), 1.0)
        costheta_m = costheta - target_mask * self.m

        # 5. Scale by s
        scaled_logits = self.s * costheta_m

        # 6. CrossEntropy with optional class weights
        ce_weight = self.weight.to(feats.device) if self.weight is not None else None
        return F.cross_entropy(scaled_logits, targets.long(), weight=ce_weight)
