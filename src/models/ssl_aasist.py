"""SSL-AASIST cho ViTrueVoice (back-end rút gọn).

Quy ước: logits = [z_spoof, z_bonafide]; score = z_bonafide - z_spoof.
"""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import Wav2Vec2Model

DEFAULT_SSL = "nguyenvulebinh/wav2vec2-base-vietnamese-250h"


class SSLFrontEnd(nn.Module):
    def __init__(self, model_name=DEFAULT_SSL, config=None, out_dim=128):
        super().__init__()
        if config is not None:
            self.encoder = Wav2Vec2Model(config)
        else:
            self.encoder = Wav2Vec2Model.from_pretrained(model_name)
        self.encoder.config.apply_spec_augment = False
        self.encoder.config.layerdrop = 0.0
        self.proj = nn.Linear(self.encoder.config.hidden_size, out_dim)
        self.frozen = False

    def forward(self, wav):
        wav = (wav - wav.mean(1, keepdim=True)) / torch.sqrt(
            wav.var(1, keepdim=True, unbiased=False) + 1e-7)
        with torch.set_grad_enabled(torch.is_grad_enabled() and not self.frozen):
            h = self.encoder(wav).last_hidden_state
        return self.proj(h)  # (B, T, out_dim)


class ResBlock2d(nn.Module):
    def __init__(self, c_in, c_out):
        super().__init__()
        self.bn1 = nn.BatchNorm2d(c_in)
        self.conv1 = nn.Conv2d(c_in, c_out, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(c_out)
        self.conv2 = nn.Conv2d(c_out, c_out, 3, padding=1)
        self.skip = nn.Conv2d(c_in, c_out, 1) if c_in != c_out else nn.Identity()

    def forward(self, x):
        h = self.conv1(F.selu(self.bn1(x)))
        h = self.conv2(F.selu(self.bn2(h)))
        return h + self.skip(x)


class GraphAttention(nn.Module):
    """GAT dày trên N nút. x: (B, N, D_in) -> (B, N, D_out)."""
    def __init__(self, d_in, d_out, dropout=0.2):
        super().__init__()
        self.att_proj = nn.Linear(d_in, d_in)
        self.att_w = nn.Parameter(torch.empty(d_in, 1))
        nn.init.xavier_normal_(self.att_w)
        self.w_att = nn.Linear(d_in, d_out)
        self.w_res = nn.Linear(d_in, d_out)
        self.bn = nn.BatchNorm1d(d_out)
        self.drop = nn.Dropout(dropout)
        self.scale = d_in ** 0.5

    def forward(self, x):
        pair = x.unsqueeze(2) * x.unsqueeze(1)               # (B,N,N,D)
        a = torch.tanh(self.att_proj(pair)) @ self.att_w      # (B,N,N,1)
        a = F.softmax(a.squeeze(-1) / self.scale, dim=-1)
        out = self.w_att(self.drop(a) @ x) + self.w_res(x)
        out = self.bn(out.transpose(1, 2)).transpose(1, 2)
        return F.selu(out)


class HSGAL(nn.Module):
    """Đồ thị dị thể: nút thời gian + nút phổ + master node."""
    def __init__(self, d, dropout=0.2):
        super().__init__()
        self.att_proj = nn.Linear(d, d)
        self.att_w = nn.Parameter(torch.empty(d, 3))  # tt, ss, chéo
        nn.init.xavier_normal_(self.att_w)
        self.w_att = nn.Linear(d, d)
        self.w_res = nn.Linear(d, d)
        self.bn = nn.BatchNorm1d(d)
        self.master_q = nn.Linear(d, d)
        self.master_out = nn.Linear(d, d)
        self.master_res = nn.Linear(d, d)
        self.drop = nn.Dropout(dropout)
        self.scale = d ** 0.5

    def forward(self, x_t, x_s, master):
        nt, ns = x_t.size(1), x_s.size(1)
        x = torch.cat([x_t, x_s], dim=1)                      # (B,N,D)
        B, N, _ = x.shape
        types = torch.cat([torch.zeros(nt), torch.ones(ns)]).to(x.device)
        pair_idx = torch.where(types[:, None] == types[None, :],
                               types[:, None], torch.full((N, N), 2.0, device=x.device)).long()
        pair = x.unsqueeze(2) * x.unsqueeze(1)                # (B,N,N,D)
        logits_all = torch.tanh(self.att_proj(pair)) @ self.att_w   # (B,N,N,3)
        logits = logits_all.gather(-1, pair_idx.expand(B, N, N).unsqueeze(-1)).squeeze(-1)
        a = F.softmax(logits / self.scale, dim=-1)
        out = self.w_att(self.drop(a) @ x) + self.w_res(x)
        out = F.selu(self.bn(out.transpose(1, 2)).transpose(1, 2))
        # master node attend lên toàn bộ nút
        q = self.master_q(master)                             # (B,1,D)
        w = F.softmax((x * q).sum(-1) / self.scale, dim=1)    # (B,N)
        m_new = self.master_out(torch.einsum("bn,bnd->bd", w, x)).unsqueeze(1)
        m_new = F.selu(m_new + self.master_res(master))
        return out[:, :nt], out[:, nt:], m_new


class SSLAASIST(nn.Module):
    def __init__(self, ssl_name=DEFAULT_SSL, ssl_config=None, ssl_dim=128,
                 conv_channels=(16, 32), d_graph=64, n_hs=2, dropout=0.2):
        super().__init__()
        self.model_kwargs = {
            "ssl_name": ssl_name, "ssl_dim": ssl_dim,
            "conv_channels": conv_channels, "d_graph": d_graph,
            "n_hs": n_hs, "dropout": dropout,
        }
        self.frontend = SSLFrontEnd(ssl_name, ssl_config, ssl_dim)
        self.bn_in = nn.BatchNorm2d(1)
        c1, c2 = conv_channels
        self.conv = nn.Sequential(ResBlock2d(1, c1), ResBlock2d(c1, c2))
        self.gat_s = GraphAttention(c2, d_graph, dropout)
        self.gat_t = GraphAttention(c2, d_graph, dropout)
        self.master = nn.Parameter(torch.randn(1, 1, d_graph) * 0.1)
        self.hs = nn.ModuleList([HSGAL(d_graph, dropout) for _ in range(n_hs)])
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(5 * d_graph, 2)

    def backend(self, feats):
        x = F.max_pool2d(feats.transpose(1, 2).unsqueeze(1), (3, 3))  # (B,1,D/3,T/3)
        x = self.conv(F.selu(self.bn_in(x)))                          # (B,C,F,T')
        g_s = self.gat_s(x.abs().amax(dim=3).transpose(1, 2))         # (B,F,d)
        g_t = self.gat_t(x.abs().amax(dim=2).transpose(1, 2))         # (B,T',d)
        master = self.master.expand(x.size(0), -1, -1)
        for layer in self.hs:
            g_t, g_s, master = layer(g_t, g_s, master)
        h = torch.cat([g_t.abs().amax(1), g_t.mean(1),
                       g_s.abs().amax(1), g_s.mean(1), master.squeeze(1)], dim=1)
        return self.out(self.drop(h))

    def forward(self, wav):
        return self.backend(self.frontend(wav))  # (B, 2) = [z_spoof, z_bonafide]

    def score(self, wav):
        z = self.forward(wav)
        return z[:, 1] - z[:, 0]

    # --- huấn luyện 2 pha ---
    def freeze_ssl(self):
        self.frontend.frozen = True
        for p in self.frontend.encoder.parameters():
            p.requires_grad = False
        self.frontend.encoder.eval()

    def unfreeze_ssl(self):
        self.frontend.frozen = False
        for p in self.frontend.encoder.parameters():
            p.requires_grad = True

    def train(self, mode=True):
        super().train(mode)
        if self.frontend.frozen:
            self.frontend.encoder.eval()
        return self

    def param_groups(self, lr_backend, lr_ssl):
        enc = list(self.frontend.encoder.parameters())
        enc_ids = {id(p) for p in enc}
        rest = [p for p in self.parameters() if id(p) not in enc_ids]
        return [{"params": rest, "lr": lr_backend}, {"params": enc, "lr": lr_ssl}]
