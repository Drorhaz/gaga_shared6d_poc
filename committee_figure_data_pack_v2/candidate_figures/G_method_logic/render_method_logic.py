#!/usr/bin/env python3
"""Method logic slide — scientific-editorial composition (not a flowchart).

Variant A: ultra-minimal (three stages + thin variability strip).
Variant B: same layout + small secondary evidence formula.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, FancyArrowPatch

OUT = Path(__file__).resolve().parent

BG = "#FFFFFF"
INK = "#1C1C1A"
MUTED = "#6B6B66"
FAINT = "#B8B8B2"
TEAL = "#2A6B7C"  # longitudinal JcvPCA process
ORANGE = "#C46B2D"  # personal repetition variability
GRAY_LINK = "#B8B8B2"
JOINT = "#303030"

# Canonical pose (same grammar as G4)
CANON = {
    "pelvis": np.array([0.00, 0.00]),
    "Ab": np.array([0.00, 0.14]),
    "Spine2": np.array([0.00, 0.26]),
    "Spine3": np.array([0.00, 0.36]),
    "Spine4": np.array([0.00, 0.46]),
    "Chest": np.array([0.00, 0.56]),
    "Neck": np.array([0.00, 0.68]),
    "Neck2": np.array([0.00, 0.76]),
    "Head": np.array([0.00, 0.88]),
    "LShoulder": np.array([0.20, 0.56]),
    "LUArm": np.array([0.34, 0.38]),
    "LFArm": np.array([0.44, 0.18]),
    "LHand": np.array([0.50, 0.00]),
    "RShoulder": np.array([-0.20, 0.56]),
    "RUArm": np.array([-0.34, 0.38]),
    "RFArm": np.array([-0.44, 0.18]),
    "RHand": np.array([-0.50, 0.00]),
    "LThigh": np.array([0.10, -0.28]),
    "LShin": np.array([0.12, -0.56]),
    "LFoot": np.array([0.13, -0.80]),
    "RThigh": np.array([-0.10, -0.28]),
    "RShin": np.array([-0.12, -0.56]),
    "RFoot": np.array([-0.13, -0.80]),
}

FULL_SKELETON = [
    ("pelvis", "Ab"),
    ("Ab", "Spine2"),
    ("Spine2", "Spine3"),
    ("Spine3", "Spine4"),
    ("Spine4", "Chest"),
    ("Chest", "Neck"),
    ("Neck", "Neck2"),
    ("Neck2", "Head"),
    ("Chest", "LShoulder"),
    ("LShoulder", "LUArm"),
    ("LUArm", "LFArm"),
    ("LFArm", "LHand"),
    ("Chest", "RShoulder"),
    ("RShoulder", "RUArm"),
    ("RUArm", "RFArm"),
    ("RFArm", "RHand"),
    ("pelvis", "LThigh"),
    ("LThigh", "LShin"),
    ("LShin", "LFoot"),
    ("pelvis", "RThigh"),
    ("RThigh", "RShin"),
    ("RShin", "RFoot"),
]

# Schematic highlights (method illustration only — not participant data).
# Teal/blue = changed contribution; orange reserved for variability strip.
COOL = "#3D6FA3"
DEMO_HI = {
    ("Chest", "LShoulder"): TEAL,
    ("LShoulder", "LUArm"): TEAL,
    ("LUArm", "LFArm"): TEAL,
    ("Ab", "Spine2"): COOL,
    ("Spine2", "Spine3"): COOL,
    ("Spine3", "Spine4"): COOL,
    ("Spine4", "Chest"): COOL,
    ("pelvis", "RThigh"): TEAL,
    ("RThigh", "RShin"): TEAL,
}


def draw_thick_link(ax, p0, p1, *, color, lw, z=3, alpha=0.95):
    ax.plot(
        [p0[0], p1[0]],
        [p0[1], p1[1]],
        color=color,
        lw=lw,
        solid_capstyle="round",
        zorder=z,
        alpha=alpha,
    )


def draw_avatar(ax, *, highlight: dict | None = None, lw_gray=5.5, lw_hi=7.5, joint_s=10):
    """G4-style body-link avatar in shared canonical pose."""
    ax.set_aspect("equal")
    ax.axis("off")
    highlight = highlight or {}

    for a, b in FULL_SKELETON:
        draw_thick_link(ax, CANON[a], CANON[b], color="#D4D4D4", lw=lw_gray - 1.2, z=1.0, alpha=0.55)

    for a, b in FULL_SKELETON:
        key = (a, b)
        if key in highlight:
            draw_thick_link(ax, CANON[a], CANON[b], color=highlight[key], lw=lw_hi, z=3.4, alpha=0.96)
        else:
            draw_thick_link(ax, CANON[a], CANON[b], color=GRAY_LINK, lw=lw_gray, z=2.5, alpha=0.90)

    for p in CANON.values():
        ax.scatter([p[0]], [p[1]], s=joint_s, color=JOINT, zorder=6, edgecolors="none")

    ax.set_xlim(-0.72, 0.72)
    ax.set_ylim(-0.95, 1.05)


def pca_cloud(ax):
    """Modern PCA / point-cloud: Baseline defines axes; Follow-up in same space."""
    ax.set_aspect("equal")
    ax.axis("off")
    rng = np.random.default_rng(7)

    # Baseline cloud elongated along PC1
    n = 90
    theta = np.deg2rad(28)
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    base = rng.normal(size=(n, 2)) * np.array([0.55, 0.22])
    base = base @ R.T

    # Follow-up: same axes, modest shift + similar spread
    follow = rng.normal(size=(n, 2)) * np.array([0.48, 0.26])
    follow = follow @ R.T + np.array([0.18, -0.08])

    ax.scatter(base[:, 0], base[:, 1], s=10, c=TEAL, alpha=0.35, linewidths=0, zorder=2)
    ax.scatter(follow[:, 0], follow[:, 1], s=10, c="#8A9AA0", alpha=0.45, linewidths=0, zorder=2)

    # PCA axes from origin
    pc1 = R @ np.array([0.95, 0.0])
    pc2 = R @ np.array([0.0, 0.48])
    ax.annotate(
        "",
        xy=pc1,
        xytext=(-pc1 * 0.15),
        arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.6, mutation_scale=12),
        zorder=4,
    )
    ax.annotate(
        "",
        xy=pc2,
        xytext=(-pc2 * 0.15),
        arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.35, mutation_scale=10),
        zorder=4,
    )
    ax.text(pc1[0] * 1.08, pc1[1] * 1.08, "PC1", fontsize=8, color=TEAL, ha="center", va="center")
    ax.text(pc2[0] * 1.15, pc2[1] * 1.15, "PC2", fontsize=8, color=TEAL, ha="center", va="center")

    # Soft ellipse for Baseline reference space
    ell = Ellipse(
        (0, 0),
        width=1.55,
        height=0.62,
        angle=28,
        facecolor=TEAL,
        edgecolor=TEAL,
        alpha=0.06,
        lw=1.2,
        zorder=1,
    )
    ax.add_patch(ell)
    ell2 = Ellipse(
        (0, 0),
        width=1.55,
        height=0.62,
        angle=28,
        facecolor="none",
        edgecolor=TEAL,
        alpha=0.35,
        lw=1.1,
        linestyle=(0, (3, 2)),
        zorder=1,
    )
    ax.add_patch(ell2)

    # Legend dots
    ax.scatter([-0.95], [-0.78], s=28, c=TEAL, alpha=0.7, linewidths=0, zorder=5)
    ax.text(-0.88, -0.78, "Baseline", fontsize=8, color=INK, va="center")
    ax.scatter([0.05], [-0.78], s=28, c="#8A9AA0", alpha=0.75, linewidths=0, zorder=5)
    ax.text(0.12, -0.78, "Follow-up", fontsize=8, color=INK, va="center")

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.95, 0.95)


def flow_arrow(ax, x0, x1, y, *, color=TEAL, lw=1.7):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y),
            (x1, y),
            arrowstyle="-|>",
            mutation_scale=13,
            lw=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
            zorder=5,
            clip_on=False,
        )
    )


def up_arrow(ax, x, y0, y1, *, color=ORANGE, lw=1.35):
    ax.add_patch(
        FancyArrowPatch(
            (x, y0),
            (x, y1),
            arrowstyle="-|>",
            mutation_scale=11,
            lw=lw,
            color=color,
            alpha=0.85,
            shrinkA=0,
            shrinkB=0,
            zorder=5,
            clip_on=False,
        )
    )


def render(variant: str = "A"):
    assert variant in {"A", "B"}
    fig = plt.figure(figsize=(15.2, 8.6), dpi=160)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # ----- Title -----
    ax.text(
        0.5,
        0.955,
        "How do we identify meaningful change in whole-body coordination?",
        ha="center",
        va="center",
        fontsize=17.5,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.5,
        0.905,
        "Compare body-link contributions in a shared movement space,\n"
        "then evaluate each change against the participant’s own repetition variability.",
        ha="center",
        va="center",
        fontsize=11,
        color=MUTED,
        linespacing=1.35,
    )

    # Stage column centers
    x_left, x_mid, x_right = 0.16, 0.50, 0.84
    y_stage = 0.52
    y_arrow = 0.55

    # ========== LEFT: two recordings ==========
    ax.text(
        x_left,
        0.78,
        "Two recordings",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )

    ax_b = fig.add_axes([0.065, 0.48, 0.095, 0.26])
    draw_avatar(ax_b, highlight={}, lw_gray=4.8, lw_hi=6.5, joint_s=8)
    ax.text(0.112, 0.455, "Baseline", ha="center", fontsize=10.5, fontweight="bold", color=INK)

    ax_f = fig.add_axes([0.165, 0.48, 0.095, 0.26])
    draw_avatar(ax_f, highlight={}, lw_gray=4.8, lw_hi=6.5, joint_s=8)
    ax.text(0.212, 0.455, "Follow-up", ha="center", fontsize=10.5, fontweight="bold", color=INK)

    # Bracket: same sequence
    bx0, bx1, by = 0.085, 0.24, 0.42
    ax.plot([bx0, bx0, bx1, bx1], [by + 0.012, by, by, by + 0.012], color=FAINT, lw=1.2, solid_capstyle="round")
    ax.text(
        (bx0 + bx1) / 2,
        by - 0.018,
        "Same pooled progressive\nmovement sequence",
        ha="center",
        va="top",
        fontsize=8.5,
        color=MUTED,
        linespacing=1.25,
    )

    flow_arrow(ax, 0.275, 0.33, y_arrow)

    # ========== CENTER: shared PCA space ==========
    ax.text(
        x_mid,
        0.78,
        "Shared movement space",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    ax_pca = fig.add_axes([0.34, 0.42, 0.32, 0.32])
    pca_cloud(ax_pca)

    ax.text(
        x_mid,
        0.395,
        "Baseline defines the reference space",
        ha="center",
        fontsize=10.5,
        fontweight="bold",
        color=TEAL,
    )
    ax.text(
        x_mid,
        0.365,
        "Follow-up is expressed in the same coordinates",
        ha="center",
        fontsize=9.2,
        color=MUTED,
    )

    flow_arrow(ax, 0.67, 0.725, y_arrow)

    # ========== RIGHT: body-link contributions ==========
    ax.text(
        x_right,
        0.78,
        "Compare body-link contributions",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )
    ax_out = fig.add_axes([0.76, 0.42, 0.16, 0.32])
    draw_avatar(ax_out, highlight=DEMO_HI, lw_gray=5.2, lw_hi=7.8, joint_s=9)

    ax.text(
        x_right,
        0.375,
        "Which links changed their role\nin the movement pattern?",
        ha="center",
        va="top",
        fontsize=9.5,
        color=MUTED,
        linespacing=1.3,
    )

    # ========== PERSONAL VARIABILITY STRIP ==========
    strip_y = 0.175 if variant == "A" else 0.205
    # thin accent line
    ax.plot([0.08, 0.92], [strip_y + 0.055, strip_y + 0.055], color=ORANGE, lw=1.6, alpha=0.55, solid_capstyle="round")

    ax.text(
        0.08,
        strip_y + 0.075,
        "Personal variability reference",
        ha="left",
        fontsize=9.5,
        fontweight="bold",
        color=ORANGE,
    )

    # left
    ax.text(0.18, strip_y + 0.02, "Baseline R1  ↔  Baseline R2", ha="center", fontsize=10.5, color=ORANGE, fontweight="bold")
    ax.text(0.18, strip_y - 0.02, "Natural repetition variability", ha="center", fontsize=8.8, color=MUTED)

    # center
    ax.text(0.48, strip_y + 0.02, "How much does each link naturally vary?", ha="center", fontsize=10.2, color=INK)
    ax.text(0.48, strip_y - 0.02, "Participant-specific, per body link", ha="center", fontsize=8.5, color=MUTED)

    # right criterion
    ax.text(
        0.78,
        strip_y + 0.02,
        "Longitudinal change  >  own repetition variability",
        ha="center",
        fontsize=10.2,
        color=INK,
        fontweight="bold",
    )
    ax.text(0.78, strip_y - 0.02, "✓  direction remains stable", ha="center", fontsize=9.2, color=ORANGE)

    # Connect strip up to body map
    up_arrow(ax, 0.84, strip_y + 0.09, 0.40)

    # ========== FORMULA (variant B only) ==========
    if variant == "B":
        ax.text(
            0.5,
            0.112,
            r"$V_l = |\Delta C_l(\mathrm{Baseline\ R1},\ \mathrm{Baseline\ R2})|$",
            ha="center",
            fontsize=10,
            color=INK,
        )
        ax.text(
            0.5,
            0.082,
            r"Highlight link $l$ if  $|\Delta C_{\mathrm{long},l}| > V_l$  +  stable direction",
            ha="center",
            fontsize=9.5,
            color=TEAL,
        )
        ax.text(
            0.5,
            0.055,
            "Participant-specific evidence criterion — not a p-value",
            ha="center",
            fontsize=8.5,
            color=MUTED,
            style="italic",
        )
        cite_y = 0.02
    else:
        cite_y = 0.055

    # Citation
    ax.text(
        0.5,
        cite_y,
        "JcvPCA framework adapted from Dubois et al., PLoS ONE, 2025.",
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )

    stem = f"G_method_logic_{variant}"
    for ext in ("png", "svg"):
        fig.savefig(
            OUT / f"{stem}.{ext}",
            dpi=220 if ext == "png" else None,
            facecolor=BG,
            bbox_inches="tight",
            pad_inches=0.12,
        )
    plt.close(fig)
    print(f"wrote {stem}.{{png,svg}}")


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
    render("A")
    render("B")
