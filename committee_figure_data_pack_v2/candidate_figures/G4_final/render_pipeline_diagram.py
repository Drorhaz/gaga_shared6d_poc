#!/usr/bin/env python3
"""Visual pipeline figure: rotvec → shared PCA → JcvPCA_link → EVR-weighted Δ."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle, FancyBboxPatch as FBP
from matplotlib.collections import LineCollection
import numpy as np

OUT = Path(__file__).resolve().parent

BG = "#FFFFFF"
INK = "#222222"
MUTED = "#6A6A6A"
SOFT = "#F3F4F6"
SOFT_BLUE = "#E8F1F8"
ACCENT = "#1F6AA5"
COOL = "#2F6F9F"
WARM = "#C44E3A"
EDGE = "#C8C8C4"
GRAY_LINK = "#B0B0B0"


def arrow(ax, x0, y0, x1, y1, lw=2.0):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=16,
            lw=lw,
            color=ACCENT,
            shrinkA=0,
            shrinkB=0,
            zorder=5,
        )
    )


def card(ax, x, y, w, h, face=SOFT):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.01,rounding_size=0.028",
            facecolor=face,
            edgecolor=EDGE,
            linewidth=1.25,
            zorder=1,
        )
    )


def draw_skeleton(ax, cx, cy, scale=1.0, highlight=None, alpha=1.0):
    """Minimal front-view stick figure. highlight: set of segment keys."""
    highlight = highlight or set()
    # joints in local coords
    joints = {
        "head": (0, 0.42),
        "neck": (0, 0.30),
        "chest": (0, 0.18),
        "ab": (0, 0.02),
        "l_sh": (-0.16, 0.22),
        "r_sh": (0.16, 0.22),
        "l_el": (-0.26, 0.06),
        "r_el": (0.26, 0.06),
        "l_wr": (-0.30, -0.10),
        "r_wr": (0.30, -0.10),
        "l_hip": (-0.08, -0.02),
        "r_hip": (0.08, -0.02),
        "l_kn": (-0.10, -0.22),
        "r_kn": (0.10, -0.22),
        "l_an": (-0.11, -0.40),
        "r_an": (0.11, -0.40),
    }
    segs = [
        ("torso", "neck", "ab"),
        ("l_arm", "l_sh", "l_wr"),
        ("r_arm", "r_sh", "r_wr"),
        ("l_leg", "l_hip", "l_an"),
        ("r_leg", "r_hip", "r_an"),
        ("shoulders", "l_sh", "r_sh"),
    ]

    def xy(name):
        x, y = joints[name]
        return cx + x * scale, cy + y * scale

    for key, a, b in segs:
        active = key in highlight or "all" in highlight
        col = ACCENT if active else GRAY_LINK
        lw = 2.6 if active else 1.7
        ax.plot(*zip(xy(a), xy(b)), color=col, lw=lw, alpha=alpha, solid_capstyle="round", zorder=2)
    # head
    hx, hy = xy("head")
    ax.add_patch(Circle((hx, hy), 0.055 * scale, fc=INK if "all" in highlight else "#888888", alpha=0.85 * alpha, ec="none", zorder=3))
    for name in ("l_sh", "r_sh", "l_el", "r_el", "l_wr", "r_wr", "l_hip", "r_hip", "l_kn", "r_kn", "ab", "chest", "neck"):
        px, py = xy(name)
        ax.add_patch(Circle((px, py), 0.018 * scale, fc=INK, alpha=0.55 * alpha, ec="none", zorder=4))


def icon_rotvec(ax, cx, cy):
    """Parent→child joint with curved rotation arrow."""
    draw_skeleton(ax, cx - 0.01, cy + 0.04, scale=0.48, highlight={"r_arm"})
    t = np.linspace(0.35, 2.35, 40)
    r = 0.055
    ex, ey = cx + 0.105, cy + 0.05
    ax.plot(ex + r * np.cos(t), ey + r * np.sin(t), color=ACCENT, lw=2.0, zorder=5)
    ax.annotate(
        "",
        xy=(ex + r * np.cos(2.35), ey + r * np.sin(2.35)),
        xytext=(ex + r * np.cos(2.15), ey + r * np.sin(2.15)),
        arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.5, mutation_scale=11),
        zorder=6,
    )
    ax.text(cx, cy - 0.175, "parent → child", ha="center", va="top", fontsize=9, color=MUTED)


def icon_pca(ax, cx, cy):
    """Shared PCA axes + two clouds (baseline / later)."""
    ax.annotate(
        "",
        xy=(cx + 0.13, cy),
        xytext=(cx - 0.13, cy),
        arrowprops=dict(arrowstyle="<->", color=EDGE, lw=1.3),
    )
    ax.annotate(
        "",
        xy=(cx, cy + 0.12),
        xytext=(cx, cy - 0.12),
        arrowprops=dict(arrowstyle="<->", color=EDGE, lw=1.3),
    )
    ax.text(cx + 0.14, cy, "PC1", fontsize=7.5, color=MUTED, va="center")
    ax.text(cx, cy + 0.135, "PC2", fontsize=7.5, color=MUTED, ha="center")
    rng = np.random.default_rng(0)
    b = rng.normal(size=(16, 2)) * np.array([0.04, 0.028]) + np.array([cx - 0.035, cy])
    ax.scatter(b[:, 0], b[:, 1], s=11, c="#8A8A8A", alpha=0.55, zorder=3)
    l = rng.normal(size=(16, 2)) * np.array([0.04, 0.028]) + np.array([cx + 0.05, cy + 0.03])
    ax.scatter(l[:, 0], l[:, 1], s=11, c=ACCENT, alpha=0.75, zorder=3)
    ax.text(cx - 0.05, cy - 0.155, "baseline", fontsize=8, color=MUTED, ha="center")
    ax.text(cx + 0.06, cy - 0.155, "later", fontsize=8, color=ACCENT, ha="center")


def icon_delta_pc(ax, cx, cy):
    """Two bars: later − baseline → Δ."""
    ax.add_patch(Rectangle((cx - 0.09, cy - 0.06), 0.05, 0.15, fc="#B0B0B0", ec="none", zorder=2))
    ax.add_patch(Rectangle((cx - 0.01, cy - 0.06), 0.05, 0.22, fc=ACCENT, ec="none", zorder=2))
    ax.text(cx - 0.065, cy - 0.11, "base", fontsize=8, color=MUTED, ha="center")
    ax.text(cx + 0.015, cy - 0.11, "later", fontsize=8, color=ACCENT, ha="center")
    ax.annotate(
        "",
        xy=(cx + 0.12, cy + 0.05),
        xytext=(cx + 0.06, cy + 0.05),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.35, mutation_scale=11),
    )
    ax.text(cx + 0.14, cy + 0.05, r"$\Delta$", fontsize=15, color=ACCENT, fontweight="bold", va="center")


def icon_evr(ax, cx, cy):
    """Weighted PC bars → one Δ."""
    heights = [0.20, 0.13, 0.07]
    colors = [ACCENT, "#5B93C1", "#9BB8D4"]
    labels = ["PC1", "PC2", "PC3"]
    x0 = cx - 0.12
    for i, (hh, c, lab) in enumerate(zip(heights, colors, labels)):
        ax.add_patch(Rectangle((x0 + i * 0.05, cy - 0.06), 0.038, hh, fc=c, ec="none", zorder=2))
        ax.text(x0 + i * 0.05 + 0.019, cy - 0.11, lab, fontsize=7.2, color=MUTED, ha="center")
    ax.annotate(
        "",
        xy=(cx + 0.10, cy + 0.03),
        xytext=(cx + 0.04, cy + 0.03),
        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.35, mutation_scale=11),
    )
    ax.add_patch(
        FancyBboxPatch(
            (cx + 0.105, cy - 0.03),
            0.08,
            0.11,
            boxstyle="round,pad=0.008,rounding_size=0.018",
            facecolor="#FFFFFF",
            edgecolor=ACCENT,
            lw=1.4,
            zorder=3,
        )
    )
    ax.text(cx + 0.145, cy + 0.025, r"$\Delta$", fontsize=15, color=ACCENT, fontweight="bold", ha="center", va="center", zorder=4)


def render():
    fig, ax = plt.subplots(figsize=(13.2, 6.4), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title — short
    ax.text(
        0.5,
        0.94,
        "How one colored body-link value is computed",
        ha="center",
        va="center",
        fontsize=17.5,
        fontweight="bold",
        color=INK,
    )

    # Four visual cards
    stages = [
        ("1", "Relative rotations", icon_rotvec, SOFT),
        ("2", "Shared PCA space", icon_pca, SOFT),
        ("3", "Link change per PC", icon_delta_pc, SOFT_BLUE),
        ("4", "EVR-weighted sum", icon_evr, SOFT_BLUE),
    ]
    w, h = 0.195, 0.48
    y = 0.28
    xs = [0.045, 0.285, 0.525, 0.765]

    for i, ((num, label, drawer, face), x) in enumerate(zip(stages, xs)):
        card(ax, x, y, w, h, face=face)
        ax.add_patch(
            Circle(
                (x + 0.028, y + h - 0.032),
                0.017,
                fc=ACCENT if i >= 2 else "#888888",
                ec="none",
                zorder=3,
            )
        )
        ax.text(
            x + 0.028,
            y + h - 0.032,
            num,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
            zorder=4,
        )
        ax.text(
            x + w / 2,
            y + h - 0.028,
            label,
            ha="center",
            va="top",
            fontsize=11.5,
            fontweight="bold",
            color=INK if i < 2 else ACCENT,
        )
        drawer(ax, x + w / 2, y + 0.20)
        if i < 3:
            arrow(ax, x + w + 0.008, y + h / 2, xs[i + 1] - 0.008, y + h / 2)

    # Bottom formula strip — compact
    ax.add_patch(
        FancyBboxPatch(
            (0.10, 0.055),
            0.80,
            0.18,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor="#FAFBFC",
            edgecolor=ACCENT,
            linewidth=1.5,
            zorder=1,
        )
    )
    ax.text(
        0.50,
        0.175,
        r"$\Delta \;=\; \sum_{\mathrm{PC}} \mathrm{EVR}_{\mathrm{PC}} \times (later - baseline)_{\mathrm{link,\,PC}}$",
        ha="center",
        va="center",
        fontsize=15.5,
        color=INK,
        zorder=2,
    )

    # Tiny legend chips
    ax.add_patch(FancyBboxPatch((0.18, 0.075), 0.025, 0.035, boxstyle="round,pad=0.002", fc=WARM, ec="none"))
    ax.text(0.215, 0.092, r"$+\Delta$  increase", fontsize=10, color=INK, va="center")
    ax.add_patch(FancyBboxPatch((0.40, 0.075), 0.025, 0.035, boxstyle="round,pad=0.002", fc=COOL, ec="none"))
    ax.text(0.435, 0.092, r"$-\Delta$  decrease", fontsize=10, color=INK, va="center")
    ax.text(0.72, 0.092, "unitless  ·  not degrees", fontsize=10, color=MUTED, va="center", ha="center")

    for ext in ("png", "svg", "pdf"):
        fig.savefig(
            OUT / f"G4_pipeline_rotvec_to_delta.{ext}",
            dpi=220 if ext == "png" else None,
            facecolor=BG,
            bbox_inches="tight",
            pad_inches=0.28,
        )
    plt.close(fig)
    print("wrote G4_pipeline_rotvec_to_delta.{png,svg,pdf}")


if __name__ == "__main__":
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    render()
