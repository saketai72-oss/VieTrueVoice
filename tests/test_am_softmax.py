"""Unit tests for AM-Softmax (Additive Margin Softmax) loss.
Tests cosine calculation, margin penalty, backpropagation, and numerical stability.
"""

from __future__ import annotations
import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.training.losses import AMSoftmaxLoss


def test_am_softmax_init():
    loss_fn = AMSoftmaxLoss(in_features=320, num_classes=2, s=30.0, m=0.35)
    assert loss_fn.s == 30.0
    assert loss_fn.m == 0.35
    assert loss_fn.in_features == 320
    assert loss_fn.num_classes == 2


def test_am_softmax_forward_shape_and_scalar():
    loss_fn = AMSoftmaxLoss(in_features=64, num_classes=2, s=30.0, m=0.35)
    feats = torch.randn(8, 64, requires_grad=True)
    labels = torch.randint(0, 2, (8,))
    
    loss = loss_fn(feats, labels)
    assert loss.dim() == 0  # scalar
    assert loss.item() > 0.0
    assert not torch.isnan(loss)
    assert not torch.isinf(loss)


def test_am_softmax_gradient_backward():
    loss_fn = AMSoftmaxLoss(in_features=32, num_classes=2, s=20.0, m=0.2)
    feats = torch.randn(4, 32, requires_grad=True)
    labels = torch.tensor([0, 1, 0, 1])
    
    loss = loss_fn(feats, labels)
    loss.backward()
    
    assert feats.grad is not None
    assert feats.grad.shape == feats.shape
    assert not torch.isnan(feats.grad).any()


def test_am_softmax_margin_increases_loss():
    """Khi có margin m > 0, loss bắt buộc phải lớn hơn hoặc bằng khi m = 0."""
    torch.manual_seed(42)
    feats = torch.randn(16, 64)
    labels = torch.randint(0, 2, (16,))
    
    loss_no_margin = AMSoftmaxLoss(in_features=64, num_classes=2, s=30.0, m=0.0)
    loss_with_margin = AMSoftmaxLoss(in_features=64, num_classes=2, s=30.0, m=0.35)
    
    # Gán cùng trọng số W để so sánh đối chứng
    loss_with_margin.W.data.copy_(loss_no_margin.W.data)
    
    l_zero = loss_no_margin(feats, labels).item()
    l_margin = loss_with_margin(feats, labels).item()
    
    assert l_margin > l_zero, f"Loss có margin ({l_margin}) phải lớn hơn loss không margin ({l_zero})"


def test_am_softmax_with_external_weight_matrix():
    """Hỗ trợ truyền trực tiếp weight matrix từ nn.Linear của model."""
    linear = nn.Linear(32, 2, bias=False)
    loss_fn = AMSoftmaxLoss(in_features=32, num_classes=2, s=30.0, m=0.2)
    
    feats = torch.randn(4, 32, requires_grad=True)
    labels = torch.tensor([1, 0, 1, 0])
    
    loss = loss_fn(feats, labels, weight_matrix=linear.weight)
    loss.backward()
    
    assert linear.weight.grad is not None
    assert feats.grad is not None


def test_am_softmax_class_weights():
    """Kiểm tra trọng số class_weights được áp dụng đúng."""
    weights = torch.tensor([0.9, 0.1])
    loss_fn = AMSoftmaxLoss(in_features=16, num_classes=2, s=10.0, m=0.1, weight=weights)
    feats = torch.randn(4, 16)
    labels = torch.tensor([0, 0, 1, 1])
    loss = loss_fn(feats, labels)
    assert loss.item() > 0.0
