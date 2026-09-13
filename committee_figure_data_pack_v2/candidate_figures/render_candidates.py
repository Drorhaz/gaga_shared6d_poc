#!/usr/bin/env python3
"""Render four story-first PhD-admissions candidate figures from pack v2."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, FancyArrowPatch, Rectangle, Arc
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

PACK = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

# ---- shared visual system ----
BG = "#F4F1EC"
INK = "#2A2A28"
MUTED = "#7A766F"
LIGHT = "#D9D4CB"
ACCENT = "#2F6F8F"  # validated / focus
INC = "#3B6B5A"  # increased contribution
DEC = "#A85A3A"  # decreased contribution
UNAVAIL = "#B0AAA0"
PANEL = "#FBF9F6"
PID_ORDER = ["252", "651", "671", "790"]
STAGES = ["ex09", "ex10", "ex11", "ex12", "ex13"]
STAGE_LABELS = ["Hands", "+ Elbows", "+ Shoulders", "+ Head/Nose", "Whole body"]

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.labelsize": 10,
        "figure.facecolor": BG,
        "axes.facecolor": PANEL,
        "savefig.facecolor": BG,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.edgecolor": LIGHT,
    }
)


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fnum(v):
    try:
        return float(v)
    except Exception:
        return None


def as_bool(v):
    return str(v).strip().lower() in ("true", "1", "yes")


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=220, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name)


# =====================================================================
# G1 — paradigm schematic
# =====================================================================
def draw_body_silhouette(ax, cx, cy, scale=1.0, highlight=None, alpha_body=0.18):
    """Simple filled scientific body silhouette (not a stick figure)."""
    highlight = set(highlight or [])
    # torso
    torso = Ellipse((cx, cy + 0.05 * scale), 0.42 * scale, 0.72 * scale, facecolor=INK, alpha=alpha_body, edgecolor="none", zorder=2)
    ax.add_patch(torso)
    head = Circle((cx, cy + 0.55 * scale), 0.13 * scale, facecolor=INK, alpha=0.22 if "head" in highlight or "all" in highlight else alpha_body, edgecolor="none", zorder=3)
    ax.add_patch(head)
    # limbs as thick capsules approximated by ellipses
    limbs = {
        "hand_L": ((cx - 0.48 * scale, cy + 0.05 * scale), 0.12 * scale, 0.12 * scale),
        "hand_R": ((cx + 0.48 * scale, cy + 0.05 * scale), 0.12 * scale, 0.12 * scale),
        "forearm_L": ((cx - 0.38 * scale, cy + 0.08 * scale), 0.16 * scale, 0.28 * scale),
        "forearm_R": ((cx + 0.38 * scale, cy + 0.08 * scale), 0.16 * scale, 0.28 * scale),
        "upper_L": ((cx - 0.28 * scale, cy + 0.18 * scale), 0.16 * scale, 0.28 * scale),
        "upper_R": ((cx + 0.28 * scale, cy + 0.18 * scale), 0.16 * scale, 0.28 * scale),
        "thigh_L": ((cx - 0.14 * scale, cy - 0.42 * scale), 0.16 * scale, 0.38 * scale),
        "thigh_R": ((cx + 0.14 * scale, cy - 0.42 * scale), 0.16 * scale, 0.38 * scale),
        "shin_L": ((cx - 0.16 * scale, cy - 0.78 * scale), 0.13 * scale, 0.32 * scale),
        "shin_R": ((cx + 0.16 * scale, cy - 0.78 * scale), 0.13 * scale, 0.32 * scale),
    }
    key_map = {
        "hands": ["hand_L", "hand_R"],
        "elbows": ["forearm_L", "forearm_R", "hand_L", "hand_R"],
        "shoulders": ["upper_L", "upper_R", "forearm_L", "forearm_R", "hand_L", "hand_R"],
        "head": ["head"],
        "all": list(limbs.keys()) + ["head", "torso"],
    }
    active = set()
    for h in highlight:
        active |= set(key_map.get(h, []))
    if "all" in highlight:
        active = set(limbs.keys()) | {"head", "torso"}
        torso.set_alpha(0.35)
        torso.set_facecolor(ACCENT)
        head.set_alpha(0.45)
        head.set_facecolor(ACCENT)
    for name, ((x, y), w, h) in limbs.items():
        on = name in active
        ax.add_patch(
            Ellipse(
                (x, y),
                w,
                h,
                facecolor=ACCENT if on else INK,
                alpha=0.55 if on else alpha_body,
                edgecolor="none",
                zorder=2,
            )
        )
    if "head" in active and "all" not in highlight:
        head.set_facecolor(ACCENT)
        head.set_alpha(0.5)


def render_g1():
    fig = plt.figure(figsize=(13.2, 7.2))
    fig.patch.set_facecolor(BG)
    # title
    fig.suptitle(
        "How do we measure change in complex improvisational movement?",
        fontsize=16,
        fontweight="bold",
        color=INK,
        y=0.97,
    )
    fig.text(
        0.5,
        0.915,
        "One progressive whole-body sequence  →  one pooled analysis object  →  anatomically interpretable body-link contributions",
        ha="center",
        fontsize=10.5,
        color=MUTED,
    )

    # progressive bodies
    ax = fig.add_axes([0.04, 0.28, 0.52, 0.58])
    ax.set_xlim(0, 5.5)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")
    accum = [
        (["hands"], "Hands"),
        (["hands", "elbows"], "+ Elbows"),
        (["hands", "elbows", "shoulders"], "+ Shoulders"),
        (["hands", "elbows", "shoulders", "head"], "+ Head/Nose"),
        (["all"], "Whole body"),
    ]
    for i, (hl, lab) in enumerate(accum):
        x = 0.55 + i * 1.05
        draw_body_silhouette(ax, x, 0.15, scale=0.85, highlight=hl)
        ax.text(x, -1.15, lab, ha="center", va="top", fontsize=9, color=INK, fontweight="medium")
        if i < 4:
            ax.annotate("", xy=(x + 0.52, 0.15), xytext=(x + 0.38, 0.15), arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    ax.text(2.65, 1.22, "Progressive body involvement", ha="center", fontsize=11, color=INK, fontweight="bold")

    # pooled bracket
    ax2 = fig.add_axes([0.56, 0.34, 0.16, 0.48])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    # funnel polygon
    verts = [(0.05, 0.92), (0.55, 0.92), (0.85, 0.55), (0.85, 0.45), (0.55, 0.08), (0.05, 0.08), (0.05, 0.92)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.LINETO, MPath.LINETO, MPath.LINETO, MPath.CLOSEPOLY]
    ax2.add_patch(PathPatch(MPath(verts, codes), facecolor=ACCENT, alpha=0.12, edgecolor=ACCENT, lw=1.5))
    ax2.text(0.42, 0.5, "ONE\nPOOLED\nPROGRESSIVE\nSEQUENCE", ha="center", va="center", fontsize=9.5, color=ACCENT, fontweight="bold", linespacing=1.25)
    ax2.text(0.42, 0.02, "not five separate\nanalyses", ha="center", va="bottom", fontsize=8, color=MUTED)

    # right: method concept
    ax3 = fig.add_axes([0.74, 0.30, 0.24, 0.54])
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis("off")
    boxes = [
        (0.72, "Matched recordings\nof the pooled sequence"),
        (0.48, "Shared movement\nstructure (JcvPCA)"),
        (0.22, "Body-link contribution\npattern"),
    ]
    for y, txt in boxes:
        ax3.add_patch(FancyBboxPatch((0.08, y - 0.08), 0.84, 0.16, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor=PANEL, edgecolor=LIGHT, lw=1.2))
        ax3.text(0.5, y, txt, ha="center", va="center", fontsize=9, color=INK)
    for y0, y1 in [(0.64, 0.56), (0.40, 0.30)]:
        ax3.annotate("", xy=(0.5, y1), xytext=(0.5, y0), arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.4))
    # mini body result — full figure, not cropped bust
    draw_body_silhouette(ax3, 0.5, -0.12, scale=0.42, highlight=["hands", "elbows", "shoulders", "head"])
    # emphasize a few contribution “hotspots” without implying physiology
    for (dx, dy) in [(-0.22, -0.02), (0.22, -0.02), (0.0, 0.12), (-0.08, -0.35)]:
        ax3.add_patch(Circle((0.5 + dx, -0.12 + dy), 0.045, facecolor=ACCENT, alpha=0.35, edgecolor="none", zorder=4))
    ax3.text(0.5, 0.95, "Interpretable output", ha="center", fontsize=11, color=INK, fontweight="bold")

    # secondary timeline strip
    ax4 = fig.add_axes([0.06, 0.07, 0.88, 0.16])
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis("off")
    ax4.add_patch(FancyBboxPatch((0.0, 0.05), 1.0, 0.9, boxstyle="round,pad=0.01,rounding_size=0.02", facecolor="#EEEBE4", edgecolor=LIGHT, lw=1))
    ax4.text(0.01, 0.78, "Study context (secondary) — movement analysis remains blinded", fontsize=8.5, color=MUTED, fontweight="bold")
    events = [
        (0.06, "Baseline"),
        (0.20, "Gaga 1–3"),
        (0.36, "Blinded\nintervention"),
        (0.52, "Class 4 +\nintegration"),
        (0.68, "≈4-class\nassessment"),
        (0.82, "Gaga 5–10"),
        (0.95, "≈10-class\nassessment"),
    ]
    ax4.plot([0.06, 0.95], [0.38, 0.38], color=MUTED, lw=1.2, alpha=0.7)
    for x, lab in events:
        accent = lab.startswith("≈")
        ax4.plot(x, 0.38, "o", color=ACCENT if accent else MUTED, ms=7 if accent else 5)
        ax4.text(x, 0.12, lab, ha="center", va="bottom", fontsize=7.2, color=INK if accent else MUTED)

    save(fig, "G1_paradigm")


# =====================================================================
# G2 — progressive NV
# =====================================================================
def render_g2():
    rows = read_csv(PACK / "02_REPETITION_VARIABILITY.csv")
    by_sess = defaultdict(dict)
    for r in rows:
        by_sess[r["session_id"]][r["exercise_id"]] = float(r["normalized_variability"])

    xs = np.arange(5)
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    fig.suptitle(
        "Natural repetition variability increases across the progressive sequence",
        fontsize=15,
        fontweight="bold",
        y=0.98,
    )
    ax.set_title(
        "Within-session repetition variability relative to each session average  ·  12 participant-sessions",
        fontsize=10,
        color=MUTED,
        pad=8,
    )

    for sess, d in by_sess.items():
        ys = [d[s] for s in STAGES]
        ax.plot(xs, ys, color=LIGHT, lw=1.0, alpha=0.9, zorder=1)

    mat = np.array([[by_sess[s][st] for st in STAGES] for s in sorted(by_sess)])
    med = np.median(mat, axis=0)
    q1 = np.percentile(mat, 25, axis=0)
    q3 = np.percentile(mat, 75, axis=0)
    ax.fill_between(xs, q1, q3, color=ACCENT, alpha=0.18, zorder=2, label="Interquartile range")
    ax.plot(xs, med, color=ACCENT, lw=2.8, marker="o", ms=7, zorder=3, label="Median across sessions")
    ax.axhline(1.0, color=MUTED, ls=":", lw=1.1, zorder=0)
    ax.text(4.05, 1.05, "Session average = 1", fontsize=8.5, color=MUTED)

    ax.set_xticks(xs)
    ax.set_xticklabels(STAGE_LABELS)
    ax.set_ylabel("Relative repetition variability")
    ax.set_xlabel("Progressive movement sequence  →  increasing body involvement")
    ax.set_ylim(0, max(3.2, mat.max() * 1.05))
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT)
    ax.spines["bottom"].set_color(LIGHT)
    ax.grid(axis="y", color=LIGHT, lw=0.7, alpha=0.8)

    # annotation
    ax.text(
        0.02,
        0.97,
        "12/12 sessions: Whole body > Hands",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=INK,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", fc=PANEL, ec=ACCENT, lw=1.2),
    )
    ax.text(
        0.98,
        0.03,
        "Descriptive protocol context. Stage order is fixed,\nso order/fatigue cannot be separated from body involvement.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=MUTED,
    )
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.86), frameon=False, fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, "G2_repetition_variability")


# =====================================================================
# G3 — longitudinal capability (Option A)
# =====================================================================
def render_g3():
    rows = read_csv(PACK / "03_LONGITUDINAL_LINK_EVIDENCE.csv")
    # evaluated only
    rows = [r for r in rows if not as_bool(r.get("excluded"))]

    fig = plt.figure(figsize=(12.5, 7.0))
    fig.suptitle(
        "Can the framework detect participant-specific change across continued practice?",
        fontsize=15,
        fontweight="bold",
        y=0.97,
    )
    fig.text(
        0.5,
        0.915,
        "Highlighted links exceed each participant’s own repetition variability and remain directionally stable  ·  not a learning-magnitude score",
        ha="center",
        fontsize=10,
        color=MUTED,
    )

    # 4 participants × 2 exposures
    for i, pid in enumerate(PID_ORDER):
        for j, (cmp_key, title, classes) in enumerate(
            [
                ("D12", "After ≈4 classes", 4),
                ("D13", "After ≈10 classes", 10),
            ]
        ):
            ax = fig.add_axes([0.07 + i * 0.23, 0.18 + (1 - j) * 0.34, 0.20, 0.28])
            sub = [r for r in rows if r["participant_id"] == pid and r["comparison_internal"] == cmp_key]
            n = len(sub)
            a2 = [r for r in sub if as_bool(r.get("a2_pass"))]
            cov = sub[0]["coverage_band"] if sub else "unknown"
            limited = cov == "limited"

            ax.set_xlim(-1.2, 1.2)
            ax.set_ylim(-1.2, 1.2)
            ax.set_aspect("equal")
            ax.axis("off")

            # ring background
            ring = Circle((0, 0), 1.0, facecolor="#EFEBE3" if not limited else "#F0E8E0", edgecolor=UNAVAIL if limited else LIGHT, lw=1.6, linestyle="--" if limited else "-")
            ax.add_patch(ring)
            # place all links as small dots on circle; A2 larger/colored
            n_all = max(n, 1)
            for k, r in enumerate(sorted(sub, key=lambda x: x["link_id"])):
                ang = 2 * np.pi * k / n_all - np.pi / 2
                rad = 0.72
                x, y = rad * np.cos(ang), rad * np.sin(ang)
                if as_bool(r.get("a2_pass")):
                    signed = fnum(r.get("longitudinal_change_signed")) or 0
                    col = INC if signed >= 0 else DEC
                    ax.plot(x, y, "o", ms=8.5, color=col, markeredgecolor=INK, markeredgewidth=0.4, zorder=3)
                else:
                    ax.plot(x, y, "o", ms=4.0, color=LIGHT, markeredgecolor=MUTED, markeredgewidth=0.3, zorder=2)

            ax.text(0, 0.08, f"{len(a2)}", ha="center", va="center", fontsize=18, fontweight="bold", color=INK)
            ax.text(0, -0.22, f"of {n}", ha="center", va="center", fontsize=9, color=MUTED)
            if j == 0:
                ax.set_title(f"Participant {pid}", fontsize=11, color=INK, pad=6)
            # coverage badge
            badge = "Coverage limited" if limited else "Coverage adequate"
            ax.text(
                0,
                -1.12,
                badge,
                ha="center",
                va="top",
                fontsize=7.5,
                color=DEC if limited else MUTED,
                fontweight="bold" if limited else "normal",
            )

    # row labels for exposures (top = ≈4 classes, bottom = ≈10 classes)
    fig.text(0.015, 0.66, "After ≈4 classes", ha="center", va="center", fontsize=10, color=INK, fontweight="bold", rotation=90)
    fig.text(0.015, 0.32, "After ≈10 classes", ha="center", va="center", fontsize=10, color=INK, fontweight="bold", rotation=90)

    # legend
    legend_elems = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=INC, markeredgecolor=INK, markersize=8, label="Validated increase in contribution"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=DEC, markeredgecolor=INK, markersize=8, label="Validated decrease in contribution"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=LIGHT, markeredgecolor=MUTED, markersize=6, label="Measured, not validated beyond own variability"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#F0E8E0", markeredgecolor=UNAVAIL, markersize=9, linestyle="None", label="Dashed ring = limited coverage"),
    ]
    fig.legend(handles=legend_elems, loc="lower center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.02))
    fig.text(
        0.5,
        0.095,
        "Center numbers = count of validated body links, not an amount-of-learning score. Patterns differ across participants.",
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )
    save(fig, "G3_longitudinal_capability")


# =====================================================================
# G4 — anatomical contribution maps (D12)
# =====================================================================
def body_joints_norm(geom):
    """Return dict joint -> (x,y) in a shared upright display frame."""
    pts = {}
    for j in geom["joints"]:
        x, y = j["x"], j["y"]
        if x is None or y is None:
            continue
        pts[j["joint_id"]] = np.array([float(x), float(y)])
    # center/scale
    arr = np.vstack(list(pts.values()))
    c = arr.mean(axis=0)
    arr = arr - c
    # Motive: Y up. Flip X for a front-facing-ish view consistency.
    scale = 1.6 / np.percentile(np.linalg.norm(arr, axis=1), 95)
    out = {}
    for k, v in pts.items():
        p = (v - c) * scale
        out[k] = np.array([-p[0], p[1]])  # x,y display
    return out


def _find_joint(joints, token):
    if token is None:
        return None
    if token in joints:
        return joints[token]
    for k, v in joints.items():
        if k.endswith(token) or k.split("_")[-1] == token:
            return v
    for k, v in joints.items():
        if token in k:
            return v
    return None


def _root_joint(joints):
    for k, v in joints.items():
        if k.isdigit() or k in PID_ORDER:
            return v
    return None


def _capsule(ax, a, b, width, color, alpha, zorder=1):
    if a is None or b is None:
        return
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, alpha=alpha, lw=width, solid_capstyle="round", zorder=zorder)


def draw_neutral_body(ax, joints, alpha=0.18):
    """Filled-limb scientific body (not a thin stick figure)."""
    find = lambda t: _find_joint(joints, t)
    root = _root_joint(joints)
    head, neck, chest, ab = find("Head"), find("Neck"), find("Chest"), find("Ab")
    # head disc
    if head is not None:
        r = 0.11
        ax.add_patch(Circle((head[0], head[1]), r, facecolor=INK, alpha=alpha + 0.05, edgecolor="none", zorder=2))
    # thick neutral limbs
    segs = [
        (head, neck, 10),
        (neck, chest, 12),
        (chest, ab, 14),
        (ab, root, 14),
        (chest, find("LShoulder"), 11),
        (find("LShoulder"), find("LUArm"), 12),
        (find("LUArm"), find("LFArm"), 11),
        (find("LFArm"), find("LHand"), 10),
        (chest, find("RShoulder"), 11),
        (find("RShoulder"), find("RUArm"), 12),
        (find("RUArm"), find("RFArm"), 11),
        (find("RFArm"), find("RHand"), 10),
        (ab if ab is not None else root, find("LThigh"), 13),
        (find("LThigh"), find("LShin"), 12),
        (find("LShin"), find("LFoot"), 10),
        (ab if ab is not None else root, find("RThigh"), 13),
        (find("RThigh"), find("RShin"), 12),
        (find("RShin"), find("RFoot"), 10),
        # optional spine chain
        (ab, find("Spine2"), 10),
        (find("Spine2"), find("Spine3"), 10),
        (find("Spine3"), find("Spine4"), 10),
        (find("Spine4"), chest, 10),
        (neck, find("Neck2"), 8),
        (find("Neck2"), head, 8),
    ]
    for a, b, w in segs:
        _capsule(ax, a, b, w, INK, alpha, zorder=1)
    # soft torso ellipse if chest+ab available
    if chest is not None and (ab is not None or root is not None):
        mid = 0.5 * (chest + (ab if ab is not None else root))
        ax.add_patch(Ellipse(mid, 0.42, 0.55, facecolor=INK, alpha=alpha * 0.7, edgecolor="none", zorder=0))


def segment_midpoint(joints, start_seg, end_seg, link_id, proximal, distal):
    """Map visual segments / bones to a display point."""
    def find_token(tok):
        if not tok:
            return None
        # direct
        if tok in joints:
            return joints[tok]
        for k, v in joints.items():
            if k.endswith(tok) or k.split("_")[-1] == tok:
                return v
        return None

    # prefer proximal/distal joint tokens from data
    a = find_token(proximal)
    b = find_token(distal)
    if a is not None and b is not None:
        return 0.5 * (a + b), a, b
    # fallback using segment names
    seg_to_tok = {
        "head": "Head",
        "neck": "Neck",
        "upper_trunk_chest": "Chest",
        "lower_trunk_abdomen": "Ab",
        "pelvis": None,
        "left_shoulder": "LShoulder",
        "left_upper_arm": "LUArm",
        "left_forearm": "LFArm",
        "left_hand": "LHand",
        "right_shoulder": "RShoulder",
        "right_upper_arm": "RUArm",
        "right_forearm": "RFArm",
        "right_hand": "RHand",
        "left_thigh": "LThigh",
        "left_shin": "LShin",
        "left_foot": "LFoot",
        "right_thigh": "RThigh",
        "right_shin": "RShin",
        "right_foot": "RFoot",
    }
    ta = seg_to_tok.get(start_seg)
    tb = seg_to_tok.get(end_seg)
    # pelvis root
    root = None
    for k in joints:
        if k.isdigit() or k in PID_ORDER:
            root = joints[k]
            break
    pa = root if start_seg == "pelvis" else find_token(ta) if ta else None
    pb = root if end_seg == "pelvis" else find_token(tb) if tb else None
    if pa is not None and pb is not None:
        return 0.5 * (pa + pb), pa, pb
    if pb is not None:
        return pb, pb, pb
    if pa is not None:
        return pa, pa, pa
    return None, None, None


def render_g4():
    paradigm = json.load(open(PACK / "01_PARADIGM_AND_METHOD.json"))
    rows = read_csv(PACK / "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv")
    d12 = [r for r in rows if r["comparison_internal"] == "D12"]

    fig = plt.figure(figsize=(12.8, 7.4))
    fig.suptitle(
        "Where do validated changes in body-link contribution occur?",
        fontsize=15,
        fontweight="bold",
        y=0.97,
    )
    fig.text(
        0.5,
        0.915,
        "Baseline → ≈4 classes  ·  color shows direction of change in contribution to movement organization  ·  not muscle activation",
        ha="center",
        fontsize=10,
        color=MUTED,
    )

    for i, pid in enumerate(PID_ORDER):
        ax = fig.add_axes([0.04 + i * 0.24, 0.14, 0.22, 0.72])
        ax.set_aspect("equal")
        ax.axis("off")
        geom = paradigm["embedded_reference_geometry"][pid]
        joints = body_joints_norm(geom)
        draw_neutral_body(ax, joints, alpha=0.16)

        sub = [r for r in d12 if r["participant_id"] == pid]
        n = sum(1 for r in sub if as_bool(r["display_available"]))
        n_a2 = sum(1 for r in sub if as_bool(r["display_highlight"]))
        # excluded
        for r in sub:
            if as_bool(r["display_excluded"]):
                mid, a, b = segment_midpoint(
                    joints,
                    r["visual_segment_start"],
                    r["visual_segment_end"],
                    r["link_id"],
                    r["proximal_joint"],
                    r["distal_joint"],
                )
                if mid is None:
                    continue
                ax.plot(mid[0], mid[1], marker="s", ms=7, color="none", markeredgecolor=UNAVAIL, markeredgewidth=1.2, zorder=4)
        # no clear change
        for r in sub:
            if as_bool(r["display_no_clear_change"]):
                mid, a, b = segment_midpoint(
                    joints,
                    r["visual_segment_start"],
                    r["visual_segment_end"],
                    r["link_id"],
                    r["proximal_joint"],
                    r["distal_joint"],
                )
                if a is None or b is None:
                    continue
                ax.plot([a[0], b[0]], [a[1], b[1]], color=MUTED, alpha=0.25, lw=3.5, solid_capstyle="round", zorder=2)
        # highlights
        for r in sub:
            if not as_bool(r["display_highlight"]):
                continue
            mid, a, b = segment_midpoint(
                joints,
                r["visual_segment_start"],
                r["visual_segment_end"],
                r["link_id"],
                r["proximal_joint"],
                r["distal_joint"],
            )
            if a is None or b is None:
                continue
            signed = fnum(r["signed_value_if_valid"]) or 0
            col = INC if signed >= 0 else DEC
            # translucent contribution overlay on the limb (not a thin stick stroke)
            ax.plot([a[0], b[0]], [a[1], b[1]], color=col, alpha=0.28, lw=16, solid_capstyle="round", zorder=4)
            ax.plot([a[0], b[0]], [a[1], b[1]], color=col, alpha=0.95, lw=8, solid_capstyle="round", zorder=5)

        ys = [p[1] for p in joints.values()]
        xs = [p[0] for p in joints.values()]
        ax.set_xlim(min(xs) - 0.35, max(xs) + 0.35)
        ax.set_ylim(min(ys) - 0.35, max(ys) + 0.45)
        ax.set_title(f"Participant {pid}", fontsize=12, color=INK, pad=8)
        ax.text(0.5, -0.02, f"Validated links  {n_a2}/{n}", transform=ax.transAxes, ha="center", va="top", fontsize=10, color=INK, fontweight="bold")
        if pid == "651":
            ax.text(0.5, -0.09, "Incomplete link set\n(marker-gap exclusions)", transform=ax.transAxes, ha="center", va="top", fontsize=7.5, color=DEC)

    legend_elems = [
        Line2D([0], [0], color=INC, lw=6, label="Increased contribution"),
        Line2D([0], [0], color=DEC, lw=6, label="Decreased contribution"),
        Line2D([0], [0], color=MUTED, lw=4, alpha=0.35, label="Measured, no clear validated change"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="none", markeredgecolor=UNAVAIL, markersize=7, label="Unavailable / excluded"),
    ]
    fig.legend(handles=legend_elems, loc="lower center", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.02))
    fig.text(
        0.5,
        0.075,
        "Patterns are participant-specific. Direction ≠ better/worse. Primary comparable coverage: Baseline → ≈4 classes.",
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )
    save(fig, "G4_anatomical_contribution")


def write_evaluation():
    text = """# Candidate figure evaluation (story-first)

## Individual figure briefs

### G1 — Paradigm
- QUESTION: What are we measuring?
- MESSAGE: A progressive whole-body improvisational sequence is analyzed as one pooled object and converted into anatomically interpretable body-link contributions.
- VISUAL ANSWER: Accumulating bodies → pooled funnel → interpretable body-link output, with secondary blinded study timeline.

### G2 — Natural variability
- QUESTION: Why can’t every longitudinal difference be called meaningful change?
- MESSAGE: Natural within-session repetition variability itself increases across the progressive sequence.
- VISUAL ANSWER: Rising session trajectories with median/IQR and the annotation “12/12 sessions: Whole body > Hands”.

### G3 — Longitudinal capability
- QUESTION: Can the framework detect participant-specific change across continued practice?
- MESSAGE: Validated body-link changes appear after ≈4 and ≈10 classes, differently across people, with honest coverage.
- VISUAL ANSWER: Dual-exposure evidence rings; center counts; dashed rings for limited coverage; no count trajectory.

### G4 — Anatomical contribution
- QUESTION: Where do validated changes occur?
- MESSAGE: Changes localize to specific body-link contributions and differ across participants.
- VISUAL ANSWER: Four contribution maps for Baseline → ≈4 classes with signed overlays and unavailable markers.

## Set-level judgment

### If only TWO visuals survive
Keep **G2 + G4**.

Why:
- G2 establishes the methodological necessity of an individual repetition reference without jargon.
- G4 shows the unique payoff: anatomical interpretability of validated change.
- Together they communicate: “improvisation varies naturally → judge change against own variability → localize where coordination contributions change.”
- G1’s paradigm can be spoken in 20 seconds or shown as a tiny slide opener.
- G3’s dual-exposure counts are important but risk being misread as learning magnitude and partially overlap G4’s “participants differ” message.

### If THREE visuals survive
Add **G1** to {G2, G4}.

Why:
- The pooled progressive-sequence idea is otherwise easy to misunderstand as five separate exercises.
- G1 also quietly places the work in the broader blinded PhD design without overclaiming.

### G3 status
Scientifically valuable, but the weakest survivor as a main figure:
- it adds longitudinal timing (≈4 vs ≈10),
- yet its strongest honest reading still depends on coverage caveats,
- and its visual object (validated-link counts) is easier to overinterpret than G4’s anatomy.

Recommendation: keep G3 as a **backup / optional third panel**, or later merge a lighter dual-exposure badge into G4 rather than giving G3 equal slide weight.

### Merge idea (if compressing later)
A future single “results” figure could show G4 anatomy for ≈4 classes with a compact under-badge row for ≈10-class validated counts + coverage. That would absorb the best of G3 without a separate count-ring graphic.

## Final candidate ranking for admissions clarity
1. G4 (hero payoff)
2. G2 (methodological necessity)
3. G1 (orientation / pooled definition)
4. G3 (useful, but most compressible)
"""
    (OUT / "CANDIDATE_FIGURE_EVALUATION.md").write_text(text)
    print("wrote evaluation")


if __name__ == "__main__":
    render_g1()
    render_g2()
    render_g3()
    render_g4()
    write_evaluation()
