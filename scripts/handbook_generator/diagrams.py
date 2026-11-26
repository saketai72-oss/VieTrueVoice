# -*- coding: utf-8 -*-
"""
High-resolution (300 DPI) Vietnamese visual diagrams generator for the ViTrueVoice v0.9.4 Handbook.
Generates 8 intuitive figures explaining complex math, signal processing, model architecture, and pooling.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


def _configure_vn_font() -> None:
    plt.rcParams["font.sans-serif"] = ["Segoe UI", "Arial", "Tahoma", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def _draw_box(ax, x, y, w, h, text, facecolor="#EFF6FF", edgecolor="#1D4ED8", fontsize=9, textcolor="#0F172A", bold=True):
    rect = mpatches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.5,
    )
    ax.add_patch(rect)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=textcolor,
        fontweight="bold" if bold else "normal",
        linespacing=1.25,
    )


def generate_all_handbook_diagrams(out_dir: str | Path) -> dict[str, Path]:
    """Generate all 8 300-DPI PNG diagrams into out_dir and return a dict of paths."""
    _configure_vn_font()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    figs: dict[str, Path] = {}

    # ------------------------------------------------------------------
    # FIG 1: Score Distributions, Threshold theta=0.0, APCER/BPCER & EER
    # ------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.2), dpi=300)
    x = np.linspace(-35, 35, 600)
    spoof_pdf = 0.72 * np.exp(-0.5 * ((x + 15.5) / 6.8) ** 2) + 0.12 * np.exp(-0.5 * ((x + 3.0) / 5.5) ** 2)
    bona_pdf = 0.82 * np.exp(-0.5 * ((x - 14.5) / 6.2) ** 2)

    ax1.plot(x, spoof_pdf, color="#DC2626", lw=2.2, label="Phân phối Giọng Giả (Spoof)")
    ax1.plot(x, bona_pdf, color="#16A34A", lw=2.2, label="Phân phối Giọng Thật (Bonafide)")
    ax1.fill_between(x, 0, spoof_pdf, where=(x >= 0), color="#EF4444", alpha=0.35, label="Lỗi APCER (Lọt lưới giả >= 0)")
    ax1.fill_between(x, 0, bona_pdf, where=(x < 0), color="#F59E0B", alpha=0.40, label="Lỗi BPCER (Báo nhầm thật < 0)")
    ax1.axvline(0.0, color="#1E3A8A", ls="--", lw=2.0, label="Ngưỡng quyết định θ = 0.0")
    ax1.set_title("A. Phân phối điểm thô Logit (s) & Hai vùng sai số", fontsize=10.5, fontweight="bold")
    ax1.set_xlabel("Điểm thô s = z_bonafide − z_spoof", fontsize=9.5)
    ax1.set_ylabel("Mật độ xác suất", fontsize=9.5)
    ax1.legend(loc="upper left", fontsize=7.8, framealpha=0.92)
    ax1.grid(alpha=0.25)

    thr = np.linspace(0.001, 0.45, 200)
    frr = 0.0032 / (thr + 0.012)
    frr = np.clip(frr, 0.005, 0.45)
    ax2.plot(thr * 100, frr * 100, color="#1D4ED8", lw=2.3, label="Đường đánh đổi DET (APCER vs BPCER)")
    ax2.plot([0, 45], [0, 45], color="#64748B", ls=":", lw=1.5, label="Đường phân giác APCER = BPCER")
    eer_val = 5.63
    ax2.scatter([eer_val], [eer_val], color="#DC2626", s=65, zorder=5)
    ax2.annotate(
        f"Điểm EER = {eer_val}%\n(v0.9.4 trên 15.980 mẫu)",
        xy=(eer_val, eer_val),
        xytext=(14, 16),
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.4),
        fontsize=8.8,
        fontweight="bold",
        color="#991B1B",
    )
    ax2.set_xlim(0, 35)
    ax2.set_ylim(0, 35)
    ax2.set_title("B. Ý nghĩa hình học của Điểm Cân Bằng Sai Số (EER)", fontsize=10.5, fontweight="bold")
    ax2.set_xlabel("Tỷ lệ lọt lưới giả APCER / FAR (%)", fontsize=9.5)
    ax2.set_ylabel("Tỷ lệ báo nhầm thật BPCER / FRR (%)", fontsize=9.5)
    ax2.legend(loc="upper right", fontsize=8.0)
    ax2.grid(alpha=0.25)
    fig.tight_layout()
    p1 = out / "fig1_eer_distributions.png"
    fig.savefig(p1, dpi=300)
    plt.close(fig)
    figs["fig1"] = p1

    # ------------------------------------------------------------------
    # FIG 2: Data Pipeline & 1:1 Symmetry Architecture (v0.9.4)
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.5, 4.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    ax.text(5.0, 3.95, "SƠ ĐỒ LUỒNG DỮ LIỆU & KIẾN TRÚC ĐỐI XỨNG MÔ HÌNH v0.9.4 (0% RÒ RỈ)", ha="center", fontsize=11, fontweight="bold", color="#1E3A8A")

    _draw_box(ax, 0.2, 2.5, 2.1, 1.1, "Nguồn Giọng Thật (Bonafide)\n• VIVOS (65 người nói)\n• CommonVoice 8.0 (419 SPK)\n• 6 Tình nguyện viên", "#ECFDF5", "#059669", 8.5)
    _draw_box(ax, 0.2, 0.5, 2.1, 1.5, "Ràng Buộc Cô Lập Cứng\n• Speaker-Disjoint 100%\n• Hard Text-Disjoint\n• Cô lập 5 SPK (0003..0007)\n  làm Bộ Nghiệm Thu Độc Lập", "#FEF2F2", "#DC2626", 8.3)

    _draw_box(ax, 2.8, 2.5, 2.3, 1.1, "2 Công Cụ Seen TTS (Train/Dev)\n• F5-TTS-Vietnamese (6.170)\n• OmniVoice CFM (6.445 tệp:\n  VIVOS 4.795 | CV 1.225 | SPK 425)", "#EFF6FF", "#2563EB", 8.3)
    _draw_box(ax, 2.8, 0.6, 2.3, 1.3, "Công Cụ Unseen TTS (Kiểm định H2)\n• VieNeu-TTS v3 Turbo\n  (Không xuất hiện trong Train/Dev\n   của v0.9.4 — 955 mẫu OOD)", "#FFFBEB", "#D97706", 8.3)

    _draw_box(ax, 5.6, 1.5, 1.8, 1.6, "Lọc 4 Cổng & 5 Codecs\n• WER/CER + Cosine Sim\n• Clean 16kHz\n• Zalo AAC 76k / Opus 24k\n• G.711 A-law / AMR-NB", "#F5F3FF", "#7C3AED", 8.3)

    _draw_box(ax, 7.8, 2.2, 2.0, 1.4, "5 Manifests Chuẩn 19 Cột\n• Train: 54.400 (đối chứng 54.225)\n• Dev: 12.405\n• Test In-domain: 15.980\n• Unseen VieNeu: 955", "#EFF6FF", "#1E40AF", 8.2)
    _draw_box(ax, 7.8, 0.5, 2.0, 1.3, "Kho Lưu Trữ Voice_Final\n• Tổng: 103.189 tệp âm thanh\n• Bonafide: 70.174\n• Spoof (v7 & v8): 33.015\n• 100% kiểm toán SHA-256", "#F0FDF4", "#15803D", 8.2)

    arrow_kw = dict(arrowstyle="->,head_width=0.25,head_length=0.25", color="#475569", lw=1.6)
    ax.annotate("", xy=(2.8, 3.05), xytext=(2.3, 3.05), arrowprops=arrow_kw)
    ax.annotate("", xy=(2.8, 1.25), xytext=(2.3, 1.25), arrowprops=arrow_kw)
    ax.annotate("", xy=(5.6, 2.5), xytext=(5.1, 3.0), arrowprops=arrow_kw)
    ax.annotate("", xy=(5.6, 2.0), xytext=(5.1, 1.25), arrowprops=arrow_kw)
    ax.annotate("", xy=(7.8, 2.85), xytext=(7.4, 2.45), arrowprops=arrow_kw)
    ax.annotate("", xy=(7.8, 1.2), xytext=(7.4, 2.05), arrowprops=arrow_kw)
    fig.tight_layout()
    p2 = out / "fig2_data_pipeline_v094.png"
    fig.savefig(p2, dpi=300)
    plt.close(fig)
    figs["fig2"] = p2

    # ------------------------------------------------------------------
    # FIG 3: Zero-Padding vs Repeat Padding & 5 Codecs Bandwidth
    # ------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.0), dpi=300)
    t_full = np.linspace(0, 4.0, 800)
    t_short = t_full[:450]
    wave_seg = 0.65 * np.sin(2 * np.pi * 3.5 * t_short) * np.exp(-0.25 * (t_short - 1.1) ** 2) + 0.25 * np.sin(2 * np.pi * 11 * t_short)
    zero_pad = np.concatenate([wave_seg, np.zeros(350)])
    rep_pad = np.tile(wave_seg, 2)[:800]

    ax1.plot(t_full, zero_pad + 1.1, color="#DC2626", lw=1.3, label="Zero-Padding (SAI: Vách đứt gãy về 0 tại 2.25s)")
    ax1.plot(t_full, rep_pad - 1.1, color="#16A34A", lw=1.3, label="Repeat Padding (ĐÚNG: Nối lặp liên tục đủ 4.0s)")
    ax1.axvline(2.25, color="#64748B", ls="--", lw=1.2)
    ax1.set_yticks([-1.1, 1.1])
    ax1.set_yticklabels(["Repeat\nPadding", "Zero\nPadding"], fontsize=8.5, fontweight="bold")
    ax1.set_xlabel("Thời gian (giây) — Đủ 64.000 mẫu @ 16kHz", fontsize=9.2)
    ax1.set_title("A. Tại sao bắt buộc dùng Repeat Padding thay Zero-Padding?", fontsize=10.0, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=7.8)
    ax1.grid(alpha=0.25)

    codecs = ["Clean 16kHz\n(Gốc)", "Zalo AAC-LC\n76 kbps", "Zalo Opus\n24 kbps", "G.711 A-law\n64 kbps (8kHz)", "AMR-NB\n4.75–12.2k (8kHz)"]
    low_hz = [50, 60, 60, 300, 300]
    high_hz = [8000, 7800, 7500, 3400, 3400]
    colors = ["#0EA5E9", "#2563EB", "#4F46E5", "#F59E0B", "#EF4444"]
    y_pos = np.arange(len(codecs))
    for i in range(len(codecs)):
        ax2.barh(y_pos[i], high_hz[i] - low_hz[i], left=low_hz[i], height=0.52, color=colors[i], alpha=0.88)
        ax2.text(high_hz[i] + 120, y_pos[i], f"{low_hz[i]}–{high_hz[i]} Hz", va="center", fontsize=8.3, fontweight="bold")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(codecs, fontsize=8.5)
    ax2.set_xlim(0, 9600)
    ax2.invert_yaxis()
    ax2.set_xlabel("Dải tần số âm thanh giữ lại được (Hz)", fontsize=9.2)
    ax2.set_title("B. Băng thông tần số của 5 kênh truyền trong ViTrueVoice", fontsize=10.0, fontweight="bold")
    ax2.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    p3 = out / "fig3_padding_and_codecs.png"
    fig.savefig(p3, dpi=300)
    plt.close(fig)
    figs["fig3"] = p3

    # ------------------------------------------------------------------
    # FIG 4: SSL-AASIST Architecture + 2-Phase Training & Head-Blend a0.75
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.5, 4.3), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.0)
    ax.axis("off")
    ax.text(5.0, 3.75, "KIẾN TRÚC MẠNG SSL-AASIST & HIỆU CHUẨN ĐẦU PHÂN LOẠI v0.9.4 (head_blend_a0.75)", ha="center", fontsize=10.8, fontweight="bold", color="#1E3A8A")

    _draw_box(ax, 0.2, 1.8, 1.5, 1.3, "Đầu Vào Chuẩn\nWaveform 4.0s\n(64.000 mẫu)\n+ RawBoost", "#F1F5F9", "#475569", 8.4)
    _draw_box(ax, 2.0, 1.8, 2.2, 1.3, "Khối Front-end SSL\nWav2Vec 2.0 Tiếng Việt\n(7 CNN + 12 Transformer)\nTrích xuất biểu diễn 768 chiều", "#EFF6FF", "#2563EB", 8.4)
    _draw_box(ax, 4.5, 1.8, 2.2, 1.3, "Khối Đồ Thị AASIST\nHS-GAL (Chú ý Không đồng nhất\nThời gian × Tần số)\nBắt vi nhiễu pha CFM & Vocoder", "#F5F3FF", "#7C3AED", 8.3)
    _draw_box(ax, 7.0, 1.8, 2.8, 1.3, "Đầu Phân Loại & Điểm Thô\nAM-Softmax (s=30, m=0.20)\nĐiểm s = z_thật − z_giả\n(s >= 0: Thật | s < 0: Giả)", "#ECFDF5", "#059669", 8.4)

    _draw_box(ax, 0.2, 0.25, 3.0, 1.1, "Pha 1: Đóng băng SSL (LR = 1e-4)\nLàm ấm đồ thị AASIST trước để không\nphá hỏng tri thức tiếng Việt 250 giờ", "#FFFBEB", "#D97706", 8.2)
    _draw_box(ax, 3.5, 0.25, 3.0, 1.1, "Pha 2: Mở khóa toàn mạng\nLR phân tầng: SSL 1e-6 | AASIST 1e-5\nHọc sâu đặc trưng F5-TTS & OmniVoice CFM", "#FEF2F2", "#DC2626", 8.2)
    _draw_box(ax, 6.8, 0.25, 3.0, 1.1, "Hiệu Chuẩn v0.9.4 (head_blend_a0.75)\nW = 0.25 × W_Phase2 + 0.75 × W_HeadOnly\nKhử lệch biên âm, giữ nguyên 100% SSL", "#EFF6FF", "#1D4ED8", 8.2)

    for x0, x1 in [(1.7, 2.0), (4.2, 4.5), (6.7, 7.0)]:
        ax.annotate("", xy=(x1, 2.45), xytext=(x0, 2.45), arrowprops=arrow_kw)
    ax.annotate("", xy=(3.5, 0.8), xytext=(3.2, 0.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(6.8, 0.8), xytext=(6.5, 0.8), arrowprops=arrow_kw)
    fig.tight_layout()
    p4 = out / "fig4_ssl_aasist_head_blend.png"
    fig.savefig(p4, dpi=300)
    plt.close(fig)
    figs["fig4"] = p4

    # ------------------------------------------------------------------
    # FIG 5: Consensus Asymmetric Veto Multi-Window Pooling
    # ------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.1), dpi=300)
    wins = ["Cửa sổ 1\n(0–4s)", "Cửa sổ 2\n(1–5s)", "Cửa sổ 3\n(2–6s)", "Cửa sổ 4\n(3–7s)", "Cửa sổ 5\n(4–8s)"]
    bona_w = [-18.5, 9.2, 14.1, 16.0, 12.8]
    c_b = ["#EF4444" if v < 0 else "#22C55E" for v in bona_w]
    ax1.bar(wins, bona_w, color=c_b, width=0.52, edgecolor="#1E293B")
    ax1.axhline(0, color="#0F172A", lw=1.2)
    ax1.axhline(6.0, color="#2563EB", ls="--", lw=1.3, label="Ngưỡng đồng thuận thật (+6.0)")
    ax1.axhline(-12.0, color="#DC2626", ls=":", lw=1.3, label="Ngưỡng nghi vấn giả (-12.0)")
    ax1.set_ylim(-28, 24)
    ax1.set_title("Ca A: Người thật có 1 nhịp nghỉ lấy hơi đầu câu\n→ Cửa sổ cao nhì = +14.1 >= 6.0 → BẢO VỆ THẬT (+14.1)", fontsize=9.3, fontweight="bold", color="#15803D")
    ax1.set_ylabel("Điểm từng cửa sổ", fontsize=9.0)
    ax1.legend(loc="lower right", fontsize=7.6)
    ax1.grid(axis="y", alpha=0.25)

    wins2 = ["Cửa sổ 1\n(0–4s)", "Cửa sổ 2\n(1–5s)", "Cửa sổ 3\n(2–6s)", "Cửa sổ 4\n(3–7s)"]
    spoof_w = [-24.0, -19.2, -15.4, 8.1]
    c_s = ["#EF4444" if v < 0 else "#F59E0B" for v in spoof_w]
    ax2.bar(wins2, spoof_w, color=c_s, width=0.46, edgecolor="#1E293B")
    ax2.axhline(0, color="#0F172A", lw=1.2)
    ax2.axhline(6.0, color="#2563EB", ls="--", lw=1.3)
    ax2.axhline(-12.0, color="#DC2626", ls=":", lw=1.3)
    ax2.set_ylim(-28, 24)
    ax2.set_title("Ca B: Giọng giả CFM có đoạn im lặng cuối (+8.1)\n→ Cao nhì = -15.4 < 6.0 → PHỦ QUYẾT CHẶN GIẢ (-19.5)", fontsize=9.3, fontweight="bold", color="#B91C1C")
    ax2.text(1.5, 15.0, "• Nếu dùng MAX cũ: lấy +8.1 → BỊ LỌT LƯỚI!\n• Consensus Veto: loại +8.1 → CHẶN ĐỨNG (-19.5)", ha="center", fontsize=8.3, bbox=dict(boxstyle="round", fc="#FEF2F2", ec="#DC2626"))
    ax2.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    p5 = out / "fig5_consensus_asymmetric_veto.png"
    fig.savefig(p5, dpi=300)
    plt.close(fig)
    figs["fig5"] = p5

    # ------------------------------------------------------------------
    # FIG 6: Platt Scaling Calibration Curve & NIST Clamp [0.1%, 99.9%]
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10.5, 3.8), dpi=300)
    s_grid = np.linspace(-45, 45, 500)
    naive_prob = 100.0 / (1.0 + np.exp(-s_grid))
    platt_prob = np.clip(100.0 / (1.0 + np.exp(-s_grid / 8.0)), 0.1, 99.9)

    ax.plot(s_grid, naive_prob, color="#94A3B8", ls="--", lw=1.8, label="Sigmoid thô chưa hiệu chuẩn (Quá tự tin: s=5 đã báo 99.3%!)")
    ax.plot(s_grid, platt_prob, color="#1D4ED8", lw=2.5, label="Platt Scaling đã hiệu chuẩn + Kẹp chuẩn NIST [0.1%, 99.9%]")
    ax.axvspan(-8.0, 8.0, color="#FEF3C7", alpha=0.55, label="Vùng biên thận trọng (Borderline Zone |s| <= 8.0)")
    ax.axvline(0.0, color="#DC2626", lw=1.6, ls=":", label="Ngưỡng phân định θ = 0.0 (50.0%)")
    ax.set_xlabel("Điểm thô sau gộp cửa sổ (Pooled Raw Score s)", fontsize=9.5)
    ax.set_ylabel("Xác suất là Giọng Thật (%)", fontsize=9.5)
    ax.set_title("Hiệu chuẩn xác suất Platt Scaling & Vùng cảnh báo biên chuẩn Giám định số NIST", fontsize=10.5, fontweight="bold")
    ax.legend(loc="lower right", fontsize=8.2)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    p6 = out / "fig6_platt_calibration.png"
    fig.savefig(p6, dpi=300)
    plt.close(fig)
    figs["fig6"] = p6

    # ------------------------------------------------------------------
    # FIG 8: Benchmark v0.9.4 vs V8.0 vs V7 (15,980 Test & 5 SPK Matrix)
    # ------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.1), dpi=300)
    c_labels = ["Clean", "Zalo AAC", "Zalo Opus", "G.711", "AMR-NB", "Tổng Gộp"]
    v7_eer = [13.37, 12.92, 14.92, 14.03, 13.36, 13.72]
    v80_eer = [6.46, 7.35, 6.90, 6.24, 6.11, 6.79]
    v094_eer = [5.52, 5.79, 6.02, 6.11, 4.88, 5.63]
    idx = np.arange(len(c_labels))
    w = 0.26
    ax1.bar(idx - w, v7_eer, w, label="V7 Best (13.72%)", color="#94A3B8")
    ax1.bar(idx, v80_eer, w, label="V8.0 Legacy (6.79%)", color="#60A5FA")
    ax1.bar(idx + w, v094_eer, w, label="v0.9.4 Chính thức (5.63%)", color="#16A34A")
    ax1.axhline(8.0, color="#DC2626", ls="--", lw=1.4, label="Mục tiêu KPI In-domain <= 8.0%")
    ax1.set_xticks(idx)
    ax1.set_xticklabels(c_labels, fontsize=8.3)
    ax1.set_ylabel("Tỷ lệ sai số EER (%) — Càng thấp càng tốt", fontsize=8.8)
    ax1.set_title("A. So sánh EER trên 15.980 mẫu Test qua 5 Codecs", fontsize=9.8, fontweight="bold")
    ax1.legend(fontsize=7.6)
    ax1.grid(axis="y", alpha=0.25)

    cats = ["Bonafide\n(420 mẫu)", "Chặn F5-TTS\n(375 mẫu)", "Chặn OmniVoice\n(375 mẫu)", "Chặn VieNeu\nUnseen (375)"]
    rates = [94.76, 100.0, 83.47, 92.53]
    bar_cols = ["#16A34A", "#2563EB", "#7C3AED", "#D97706"]
    bars = ax2.bar(cats, rates, color=bar_cols, width=0.50)
    for b, val in zip(bars, rates):
        ax2.text(b.get_x() + b.get_width() / 2, val + 1.5, f"{val:.2f}%", ha="center", fontsize=8.8, fontweight="bold")
    ax2.set_ylim(0, 112)
    ax2.set_ylabel("Tỷ lệ nhận diện / chặn đúng (%) — Càng cao càng tốt", fontsize=8.8)
    ax2.set_title("B. Nghiệm thu độc lập 5 SPK (1.545 tệp / 5 Codecs)", fontsize=9.8, fontweight="bold")
    ax2.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    p8 = out / "fig8_benchmark_v094.png"
    fig.savefig(p8, dpi=300)
    plt.close(fig)
    figs["fig8"] = p8

    # ------------------------------------------------------------------
    # FIG 9: 0 VND Local Docker Compose + Zero-Persistence Stream
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11.5, 4.0), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.8)
    ax.axis("off")
    ax.text(5.0, 3.52, "KIẾN TRÚC DOCKER CỤC BỘ 0 VNĐ (CHUẨN AWS GÓI A) & BẢO VỆ SINH TRẮC HỌC IN-MEMORY", ha="center", fontsize=10.3, fontweight="bold", color="#1E3A8A")

    _draw_box(ax, 0.2, 1.3, 2.0, 1.8, "Người Dùng Đầu Cuối\n• Web Playground /UI\n  (http://localhost:8000)\n• Telegram Voice Note\n  (@vitruevoice_bot)", "#F8FAFC", "#475569", 8.4)
    _draw_box(ax, 2.7, 2.0, 2.3, 1.15, "Container 1: vitruevoice-api\n• Non-root user (appuser)\n• Volume out/v0.9.4 chỉ đọc (:ro)\n• HEALTHCHECK /health 30s", "#EFF6FF", "#2563EB", 8.2)
    _draw_box(ax, 2.7, 0.45, 2.3, 1.15, "Container 2: vitruevoice-bot\n• Mạng nội bộ Docker Bridge\n• Tách bí mật qua file .env\n• Khôi phục tự động (restart)", "#F5F3FF", "#7C3AED", 8.2)
    _draw_box(ax, 5.5, 1.3, 2.1, 1.8, "Xử Lý Trên RAM (Zero-Persistence)\n1. Kiểm tra Magic Bytes\n2. Giải mã io.BytesIO trên RAM\n3. Suy luận 5 cửa sổ (~0.7s)\n4. Xóa hủy file tạm tức thì", "#ECFDF5", "#059669", 8.2)
    _draw_box(ax, 8.0, 1.3, 1.8, 1.8, "Nhật Ký Ẩn Danh\n• Chỉ lưu mã băm\n  SHA-256 + độ trễ\n• 0 byte giọng thô\n• Tuân thủ Luật\n  91/2025/QH15", "#FFFBEB", "#D97706", 8.2)

    ax.annotate("", xy=(2.7, 2.55), xytext=(2.2, 2.4), arrowprops=arrow_kw)
    ax.annotate("", xy=(2.7, 1.05), xytext=(2.2, 1.8), arrowprops=arrow_kw)
    ax.annotate("", xy=(3.85, 2.0), xytext=(3.85, 1.6), arrowprops=arrow_kw)
    ax.annotate("", xy=(5.5, 2.2), xytext=(5.0, 2.55), arrowprops=arrow_kw)
    ax.annotate("", xy=(8.0, 2.2), xytext=(7.6, 2.2), arrowprops=arrow_kw)
    fig.tight_layout()
    p9 = out / "fig9_docker_zero_persistence.png"
    fig.savefig(p9, dpi=300)
    plt.close(fig)
    figs["fig9"] = p9

    return figs
