#!/usr/bin/env python3
"""Committee robustness / sensitivity figure from file 06 only.

Variant A: 8-row robustness fingerprint
Variant B: reference-inspired detail + restrained summary
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

PACK = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

BG = "#FFFFFF"
INK = "#222222"
MUTED = "#6A6A6A"
LIGHT = "#D8D8D4"
TRACK = "#EFEFEA"
ACCENT = "#2F6F8F"
COV_LIM = "#8A6D3B"

TITLE = "Sensitivity testing shows where the body-link pattern is stable — and where it is not"
SUBTITLE = "Agreement across repetition design, PC selection, and QC choices  ·  top-5 link overlap"

CASE_ORDER = [
    ("252", "D12"),
    ("252", "D13"),
    ("651", "D12"),
    ("651", "D13"),
    ("671", "D12"),
    ("671", "D13"),
    ("790", "D12"),
    ("790", "D13"),
]


def load_cases():
    j = json.load(open(PACK / "06_JCVPCA_ROBUSTNESS.json"))
    by = {(r["participant_id"], r["comparison_internal"]): r for r in j["comparison_level_robustness"]}
    cases = []
    for pid, comp in CASE_ORDER:
        r = by[(pid, comp)]
        label = "≈4 classes" if comp == "D12" else "≈10 classes"
        k_vals = [x["top5_overlap_vs_primary_m"] for x in sorted(r["k_grid_overlap_by_k"], key=lambda d: d["k"])]
        k_ks = [x["k"] for x in sorted(r["k_grid_overlap_by_k"], key=lambda d: d["k"])]
        cases.append(
            {
                "pid": pid,
                "comp": comp,
                "label": label,
                "case": f"{pid}  ·  {label}",
                "pR1": float(r["pooled_vs_R1_overlap"]),
                "pR2": float(r["pooled_vs_R2_overlap"]),
                "r12": float(r["R1_vs_R2_overlap"]),
                "qc": float(r["qc_drop_overlap"]),
                "cov": r["coverage_band"],
                "k": k_ks,
                "k_overlap": k_vals,
                "k_median": float(r["k_grid_summary"]["median_top5_overlap"]),
            }
        )
    return cases, j.get("top_k_definition_global", "")


def pct(x: float) -> str:
    return f"{int(round(100 * x))}%"


def draw_h_mark(ax, x0, x1, y, value, *, color=ACCENT, label=True):
    """Horizontal agreement track 0–1 mapped into [x0,x1]."""
    ax.plot([x0, x1], [y, y], color=LIGHT, lw=3.0, solid_capstyle="round", zorder=1)
    xv = x0 + value * (x1 - x0)
    ax.plot([x0, xv], [y, y], color=color, lw=3.2, solid_capstyle="round", zorder=2)
    ax.scatter([xv], [y], s=28, color=color, zorder=3, edgecolors="none")
    if label:
        ax.text(x1 + 0.008, y, pct(value), va="center", ha="left", fontsize=8.2, color=INK)


def draw_sparkline(ax, xs, ys, y_center, height=0.055, color=ACCENT):
    """Mini k-grid curve in data coordinates of the main axes (already transformed)."""
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    # xs, ys already in axes coords from caller
    ax.plot(xs, y_center + (ys - 0.5) * height * 2, color=LIGHT, lw=1.0, zorder=1)
    # baseline at 0
    ax.plot([xs[0], xs[-1]], [y_center - height, y_center - height], color=LIGHT, lw=0.6, zorder=0)
    ax.plot(xs, y_center - height + ys * 2 * height, color=color, lw=1.6, marker="o", ms=3.2, zorder=2)


def render_A(cases):
    """Robustness fingerprint: 8 aligned rows."""
    fig = plt.figure(figsize=(14.2, 8.6), dpi=150)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0.02, 0.08, 0.96, 0.78])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 8.6)
    ax.axis("off")

    fig.suptitle(TITLE, fontsize=15.5, fontweight="bold", color=INK, y=0.955, x=0.52)
    fig.text(0.52, 0.905, SUBTITLE, ha="center", fontsize=10.5, color=MUTED)

    # Column headers
    headers = [
        (0.02, "CASE"),
        (0.22, "REPETITION DESIGN"),
        (0.52, "PC SELECTION  (k = 4→10)"),
        (0.78, "QC"),
        (0.90, "COVERAGE"),
    ]
    for x, t in headers:
        ax.text(x, 8.25, t, fontsize=8.5, color=MUTED, fontweight="bold")

    # subtle column guides
    for x in (0.20, 0.50, 0.76, 0.88):
        ax.axvline(x, ymin=0.02, ymax=0.95, color="#F0F0EC", lw=1.0, zorder=0)

    for i, c in enumerate(cases):
        y = 7.4 - i * 0.95
        # alternating quiet band
        if i % 2 == 0:
            ax.add_patch(Rectangle((0.01, y - 0.38), 0.98, 0.78, facecolor="#FAFAF7", edgecolor="none", zorder=0))

        # CASE
        ax.text(0.02, y + 0.12, c["pid"], fontsize=12, fontweight="bold", color=INK, va="center")
        ax.text(0.02, y - 0.14, c["label"], fontsize=9.5, color=MUTED, va="center")

        # REPETITION — two marks
        ax.text(0.22, y + 0.18, "Pooled ↔ R1", fontsize=7.8, color=MUTED, va="center")
        draw_h_mark(ax, 0.335, 0.455, y + 0.18, c["pR1"])
        ax.text(0.22, y - 0.18, "Pooled ↔ R2", fontsize=7.8, color=MUTED, va="center")
        draw_h_mark(ax, 0.335, 0.455, y - 0.18, c["pR2"])

        # PC sparkline
        ks = np.array(c["k"], float)
        xs = 0.52 + (ks - 4) / 6 * 0.18
        ys = np.array(c["k_overlap"], float)
        ax.add_patch(
            FancyBboxPatch(
                (0.515, y - 0.28),
                0.195,
                0.56,
                boxstyle="round,pad=0.004,rounding_size=0.01",
                facecolor=TRACK,
                edgecolor="none",
                zorder=0,
            )
        )
        y_line = y - 0.22 + ys * 0.44
        ax.plot(xs, y_line, color=ACCENT, lw=1.7, marker="o", ms=3.4, zorder=2)
        ax.text(0.715, y - 0.32, f"med {pct(c['k_median'])}", fontsize=7.5, color=MUTED, va="top", ha="center")
        if i == 0:
            for xv, kk in zip(xs, ks):
                ax.text(xv, y + 0.34, str(int(kk)), ha="center", fontsize=6.5, color=MUTED)

        # QC — single clear mark
        ax.text(0.78, y + 0.22, "drop", fontsize=7.0, color=MUTED, va="center")
        draw_h_mark(ax, 0.78, 0.855, y, c["qc"], label=True)

        # COVERAGE badge
        if c["cov"] == "adequate":
            ax.text(0.905, y, "Adequate", fontsize=8.5, color=MUTED, va="center")
        else:
            ax.add_patch(
                FancyBboxPatch(
                    (0.900, y - 0.16),
                    0.085,
                    0.32,
                    boxstyle="round,pad=0.008,rounding_size=0.02",
                    facecolor="#FFF8EE",
                    edgecolor=COV_LIM,
                    linewidth=1.1,
                )
            )
            ax.text(0.942, y, "Limited", fontsize=8.0, color=COV_LIM, ha="center", va="center", fontweight="bold")

    # footer scale note
    fig.text(
        0.52,
        0.035,
        "Agreement = fraction of shared top-5 body links under each analytical choice  ·  "
        "0–100% scale  ·  coverage is context, not a robustness score",
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )
    # legend
    fig.text(0.02, 0.035, "Track length → agreement", fontsize=8.0, color=MUTED)

    stem = "G_robustness_fingerprint_A"
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=220 if ext == "png" else None, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", stem)
    return stem


def render_B(cases):
    """Reference-like: left detailed evidence, right restrained summary."""
    fig = plt.figure(figsize=(14.4, 8.4), dpi=150)
    fig.patch.set_facecolor(BG)
    fig.suptitle(TITLE, fontsize=15.5, fontweight="bold", color=INK, y=0.96)
    fig.text(0.5, 0.905, SUBTITLE, ha="center", fontsize=10.5, color=MUTED)

    # LEFT detailed panel
    ax = fig.add_axes([0.06, 0.10, 0.58, 0.74])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.4, 8.5)
    ax.axis("off")
    ax.text(0.0, 8.2, "Detailed evidence by participant × assessment", fontsize=10, fontweight="bold", color=INK)

    for i, c in enumerate(cases):
        y = 7.3 - i * 0.92
        if i % 2 == 0:
            ax.add_patch(Rectangle((-0.02, y - 0.36), 1.04, 0.74, facecolor="#FAFAF7", edgecolor="none", zorder=0))
        ax.text(0.0, y + 0.08, c["pid"], fontsize=11.5, fontweight="bold", color=INK, va="center")
        ax.text(0.0, y - 0.16, c["label"], fontsize=9, color=MUTED, va="center")

        # repetition dots as small paired bars
        ax.text(0.16, y + 0.16, "↔R1", fontsize=7.5, color=MUTED, va="center")
        ax.barh(y + 0.16, c["pR1"], height=0.18, left=0.22, color=ACCENT, alpha=0.85)
        ax.text(0.22 + c["pR1"] + 0.01, y + 0.16, pct(c["pR1"]), fontsize=7.5, va="center", color=INK)

        ax.text(0.16, y - 0.16, "↔R2", fontsize=7.5, color=MUTED, va="center")
        ax.barh(y - 0.16, c["pR2"], height=0.18, left=0.22, color="#7AA0B2", alpha=0.9)
        ax.text(0.22 + c["pR2"] + 0.01, y - 0.16, pct(c["pR2"]), fontsize=7.5, va="center", color=INK)

        # k sparkline
        ks = np.array(c["k"], float)
        xs = 0.55 + (ks - 4) / 6 * 0.22
        ys = y - 0.22 + np.array(c["k_overlap"]) * 0.44
        ax.plot(xs, ys, color=ACCENT, lw=1.5, marker="o", ms=3.0)
        ax.text(0.79, y, f"k-med {pct(c['k_median'])}", fontsize=7.8, va="center", color=INK)

        # QC + coverage
        ax.text(0.90, y + 0.12, f"QC {pct(c['qc'])}", fontsize=8.2, va="center", color=INK)
        cov_txt = "Adequate" if c["cov"] == "adequate" else "Limited"
        cov_col = MUTED if c["cov"] == "adequate" else COV_LIM
        ax.text(0.90, y - 0.14, cov_txt, fontsize=8.0, va="center", color=cov_col)

    ax.text(0.22, -0.25, "Repetition agreement (0–100%)", fontsize=8, color=MUTED)
    ax.text(0.55, -0.25, "PC selection k=4…10", fontsize=8, color=MUTED)

    # RIGHT summary
    axr = fig.add_axes([0.70, 0.12, 0.27, 0.70])
    axr.set_xlim(0, 1)
    axr.set_ylim(0, 1)
    axr.axis("off")
    axr.text(0.0, 0.96, "What the stress tests show", fontsize=11, fontweight="bold", color=INK)

    # compute ranges for honest summary
    pR1 = [c["pR1"] for c in cases]
    pR2 = [c["pR2"] for c in cases]
    kmed = [c["k_median"] for c in cases]
    qc = [c["qc"] for c in cases]

    blocks = [
        (
            "Repetition design",
            f"Pooled ↔ R1: {pct(min(pR1))}–{pct(max(pR1))}\n"
            f"Pooled ↔ R2: {pct(min(pR2))}–{pct(max(pR2))}\n"
            "Heterogeneous across cases",
        ),
        (
            "PC selection",
            f"Median top-5 overlap: {pct(min(kmed))}–{pct(max(kmed))}\n"
            "Some cases stay high; others\n"
            "remain clearly sensitive",
        ),
        (
            "QC removal",
            f"QC-drop overlap: {pct(min(qc))} across all 8 cases\n"
            "High agreement under QC drop",
        ),
        (
            "Coverage (context)",
            "≈4 classes: adequate (all)\n"
            "≈10 classes: limited for 252,\n"
            "651, 671; adequate for 790",
        ),
    ]
    y0 = 0.82
    for title, body in blocks:
        axr.add_patch(
            FancyBboxPatch(
                (0.0, y0 - 0.14),
                0.98,
                0.17,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                facecolor="#FAFAF7",
                edgecolor=LIGHT,
                linewidth=1.0,
            )
        )
        axr.text(0.04, y0 + 0.005, title, fontsize=9.5, fontweight="bold", color=ACCENT, va="center")
        axr.text(0.04, y0 - 0.08, body, fontsize=8.3, color=INK, va="center", linespacing=1.35)
        y0 -= 0.20

    axr.text(
        0.0,
        0.02,
        "No composite “overall robustness”\nscore — evidence is shown by dimension.",
        fontsize=8.2,
        color=MUTED,
        linespacing=1.35,
    )

    fig.text(
        0.5,
        0.03,
        "Agreement = shared top-5 body-link overlap under each analytical choice. Not the repetition-variability gate.",
        ha="center",
        fontsize=8.2,
        color=MUTED,
    )

    stem = "G_robustness_reference_B"
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=220 if ext == "png" else None, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", stem)
    return stem


def write_note(cases):
    pR1 = [c["pR1"] for c in cases]
    pR2 = [c["pR2"] for c in cases]
    kmed = [c["k_median"] for c in cases]
    note = f"""# Robustness figure design note

## 1. Exact title
{TITLE}

## 2. One-sentence intended message
We stress-tested the detected body-link pattern across repetition design, PC selection, and QC choices, revealing both stable and sensitive cases rather than claiming global invariance.

## 3. What each robustness dimension measures
- **Repetition design:** top-5 link overlap of pooled R1+R2 vs R1-only and vs R2-only (authoritative `pooled_vs_R1_overlap`, `pooled_vs_R2_overlap` in file 06).
- **PC selection:** top-5 overlap vs the primary analysis across k = 4…10 (`k_grid_overlap_by_k`).
- **QC:** top-5 overlap after QC-drop (`qc_drop_overlap`; all eight cases = 100% in v2).
- **Coverage:** subspace coverage band (adequate/limited) as context only — not a robustness score.

Observed ranges (file 06):
- Pooled ↔ R1: {int(100*min(pR1))}–{int(100*max(pR1))}%
- Pooled ↔ R2: {int(100*min(pR2))}–{int(100*max(pR2))}%
- Median k-grid overlap: {int(100*min(kmed))}–{int(100*max(kmed))}%
- QC-drop: 100% in all 8 cases

## 4. Why no composite robustness score
`overall_robustness_label` (stable/partial) comes from a specific QC-related heuristic and can disagree with moderate repetition overlaps. Replacing the three evidence tracks with one badge would hide real sensitivity. The figure therefore shows the raw dimensional evidence.

## 5. Which variant is clearer
**Variant A (fingerprint)** is clearer for a backup methods slide: aligned rows make stable vs sensitive cases scannable in seconds.  
**Variant B** is better if the audience needs an explicit verbal summary panel.

## 6. Recommendation
**BACKUP** — methodological strength / honesty slide.  
Not MAIN (the hero anatomical and variability figures carry the scientific story).  
Do **not** REMOVE: it answers a likely committee methods question without overclaiming.
"""
    (OUT / "G_robustness_design_note.md").write_text(note)
    print("wrote G_robustness_design_note.md")


if __name__ == "__main__":
    import matplotlib as mpl

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    cases, _ = load_cases()
    assert len(cases) == 8
    render_A(cases)
    render_B(cases)
    write_note(cases)
