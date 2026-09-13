#!/usr/bin/env python3
"""Render G2: progressive repetition variability with median/IQR + labeled trajectories."""
from __future__ import annotations

import csv
import shutil
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch

PACK = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

BG = "#FFFFFF"
PANEL = "#FFFFFF"
INK = "#222222"
MUTED = "#6B6B6B"
LIGHT = "#D0D0D0"
TRAJ = "#9A9A9A"
ACCENT = "#1F6AA5"

STAGES = ["ex09", "ex10", "ex11", "ex12", "ex13"]
LABELS = ["Hands", "+ Elbows", "+ Shoulders", "+ Head/Nose", "Whole body"]

# Distinct-enough colors per participant; T distinguished by linestyle
PID_COLOR = {
    "252": "#4C78A8",
    "651": "#F58518",
    "671": "#54A24B",
    "790": "#E45756",
}
T_STYLE = {
    "T1": "-",
    "T2": "--",
    "T3": ":",
}


def load_series():
    rows = list(csv.DictReader(open(PACK / "02_REPETITION_VARIABILITY.csv")))
    by = defaultdict(dict)
    meta = {}
    for r in rows:
        sid = r["session_id"]
        by[sid][r["exercise_id"]] = float(r["normalized_variability"])
        meta[sid] = (r["participant_id"], r["timepoint_internal"])
    sessions = sorted(by, key=lambda s: (meta[s][0], meta[s][1]))
    mat = np.array([[by[s][st] for st in STAGES] for s in sessions])
    labels = [f"{meta[s][0]} · {meta[s][1]}" for s in sessions]
    ids = [meta[s] for s in sessions]
    return sessions, mat, labels, ids


def body_cue(ax, x, y, stage_idx, h=0.72):
    on = {
        "hands": stage_idx >= 0,
        "elbows": stage_idx >= 1,
        "shoulders": stage_idx >= 2,
        "head": stage_idx >= 3,
        "torso": stage_idx >= 4,
        "legs": stage_idx >= 4,
    }

    def c(active: bool):
        return (ACCENT, 0.75) if active else (INK, 0.14)

    col, a = c(on["head"])
    ax.add_patch(
        Circle((x, y + 0.34 * h), 0.055 * h * 2.2, fc=col, alpha=a, ec="none", clip_on=False, zorder=2)
    )
    col, a = c(on["torso"])
    ax.add_patch(
        FancyBboxPatch(
            (x - 0.07 * h, y - 0.02 * h),
            0.14 * h,
            0.28 * h,
            boxstyle="round,pad=0.01,rounding_size=0.03",
            fc=col,
            alpha=a,
            ec="none",
            clip_on=False,
            zorder=1,
        )
    )
    col, a = c(on["shoulders"])
    ax.plot(
        [x - 0.16 * h, x + 0.16 * h],
        [y + 0.22 * h, y + 0.22 * h],
        color=col,
        alpha=a,
        lw=2.2,
        solid_capstyle="round",
        clip_on=False,
        zorder=2,
    )
    ax.plot(
        [x - 0.16 * h, x - 0.20 * h],
        [y + 0.22 * h, y + 0.08 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )
    ax.plot(
        [x + 0.16 * h, x + 0.20 * h],
        [y + 0.22 * h, y + 0.08 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )
    col, a = c(on["elbows"])
    ax.plot(
        [x - 0.20 * h, x - 0.24 * h],
        [y + 0.08 * h, y - 0.05 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )
    ax.plot(
        [x + 0.20 * h, x + 0.24 * h],
        [y + 0.08 * h, y - 0.05 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )
    col, a = c(on["hands"])
    ax.add_patch(
        Circle((x - 0.24 * h, y - 0.08 * h), 0.028 * h * 2.0, fc=col, alpha=a, ec="none", clip_on=False, zorder=3)
    )
    ax.add_patch(
        Circle((x + 0.24 * h, y - 0.08 * h), 0.028 * h * 2.0, fc=col, alpha=a, ec="none", clip_on=False, zorder=3)
    )
    col, a = c(on["legs"])
    ax.plot(
        [x - 0.04 * h, x - 0.07 * h],
        [y - 0.02 * h, y - 0.32 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )
    ax.plot(
        [x + 0.04 * h, x + 0.07 * h],
        [y - 0.02 * h, y - 0.32 * h],
        color=col,
        alpha=a,
        lw=2.0,
        solid_capstyle="round",
        clip_on=False,
    )


def style_axes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(LIGHT)
    ax.spines["bottom"].set_color(LIGHT)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.tick_params(axis="both", length=0, pad=7)
    ax.grid(axis="y", color="#E8E8E8", lw=0.8, alpha=1.0)
    ax.set_axisbelow(True)


def _nudge_labels(ys: list[float], min_gap: float = 0.085) -> list[float]:
    """Spread end labels vertically so they do not collide."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    placed = [0.0] * len(ys)
    prev = None
    for i in order:
        y = ys[i]
        if prev is not None and y < prev + min_gap:
            y = prev + min_gap
        placed[i] = y
        prev = y
    # If we pushed past the top, compress slightly from the top down
    top = 2.45
    if placed[order[-1]] > top:
        overflow = placed[order[-1]] - top
        for i in order:
            placed[i] -= overflow * (placed[i] - placed[order[0]]) / max(
                1e-9, placed[order[-1]] - placed[order[0]]
            )
    return placed


def render(variant: str):
    sessions, mat, labels, ids = load_series()
    assert mat.shape == (12, 5)
    assert int(np.sum(mat[:, 4] > mat[:, 0])) == 12

    xs = np.arange(5)
    med = np.median(mat, axis=0)
    q1 = np.percentile(mat, 25, axis=0)
    q3 = np.percentile(mat, 75, axis=0)

    fig, ax = plt.subplots(figsize=(13.333, 7.5), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    # Individual trajectories — colored by participant, styled by T
    for row, (pid, t) in zip(mat, ids):
        ax.plot(
            xs,
            row,
            color=PID_COLOR[pid],
            ls=T_STYLE[t],
            lw=1.35,
            alpha=0.70,
            solid_capstyle="round",
            zorder=1,
        )

    # IQR + median (kept)
    ax.fill_between(xs, q1, q3, color=ACCENT, alpha=0.14, zorder=2, linewidth=0)
    ax.plot(xs, med, color=ACCENT, lw=3.6, zorder=4, solid_capstyle="round")
    ax.scatter(xs, med, s=72, color=ACCENT, edgecolors=BG, linewidths=1.8, zorder=5)

    # Quiet reference at 1 (no text)
    ax.axhline(1.0, color="#8A8A8A", ls=(0, (2.2, 2.4)), lw=1.15, zorder=0)

    ymax = 2.55
    ax.set_xlim(-0.35, 4.55)
    ax.set_ylim(-0.05, ymax)
    ax.set_xticks(xs)
    ax.set_xticklabels([])
    ax.set_ylabel(
        "R1 vs R2 difference\n(higher = more different)",
        fontsize=13,
        color=INK,
        labelpad=12,
    )
    ax.set_yticks([0.0, 0.5, 1.0, 1.5, 2.0, 2.5])
    ax.tick_params(axis="y", labelsize=11, colors=INK)
    ax.tick_params(axis="x", length=0)
    style_axes(ax)

    for i, (lab, ex) in enumerate(zip(LABELS, STAGES)):
        ax.text(i, -0.10, lab, ha="center", va="top", fontsize=12.5, color=INK, clip_on=False)
        ax.text(i, -0.28, ex, ha="center", va="top", fontsize=10, color=MUTED, clip_on=False)

    ax.text(
        2.0,
        -0.52,
        "Increasing body involvement  →",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=11.5,
        color=MUTED,
        clip_on=False,
    )

    # End-point labels: Participant · T on each trajectory
    end_ys = [float(row[4]) for row in mat]
    label_ys = _nudge_labels(end_ys, min_gap=0.095)
    for y_end, y_lab, (pid, t) in zip(end_ys, label_ys, ids):
        ax.plot([4.0, 4.12], [y_end, y_lab], color=PID_COLOR[pid], lw=0.7, alpha=0.55, zorder=3)
        ax.text(
            4.15,
            y_lab,
            f"{pid} · {t}",
            fontsize=9.0,
            color=PID_COLOR[pid],
            va="center",
            ha="left",
            fontweight="bold",
            clip_on=False,
            zorder=6,
        )

    # Compact legend: participant color + T linestyle (identity key)
    from matplotlib.lines import Line2D

    handles = [
        Line2D([0], [0], color=PID_COLOR[p], lw=2.2, label=f"Participant {p}") for p in ("252", "651", "671", "790")
    ] + [
        Line2D([0], [0], color=INK, lw=1.6, ls=T_STYLE[t], label=t) for t in ("T1", "T2", "T3")
    ] + [
        Line2D([0], [0], color=ACCENT, lw=3.0, label="Average"),
        Line2D([0], [0], color=ACCENT, lw=8.0, alpha=0.25, label="IQR"),
    ]
    leg = ax.legend(
        handles=handles,
        loc="upper left",
        frameon=False,
        fontsize=9.2,
        ncol=2,
        columnspacing=1.2,
        handlelength=2.2,
        borderaxespad=0.4,
    )
    for text in leg.get_texts():
        text.set_color(INK)

    fig.suptitle(
        "Repetition variability increases across the progressive movement sequence",
        fontsize=18.5,
        fontweight="bold",
        color=INK,
        y=0.975,
        x=0.5,
    )
    fig.text(
        0.5,
        0.925,
        "Same movement done twice (R1 and R2): how different were those two repetitions?   ·   Each line = one participant × one timepoint",
        ha="center",
        fontsize=11.2,
        color=MUTED,
    )

    if variant == "B":
        cue_ax = fig.add_axes([0.16, 0.80, 0.62, 0.065])
        cue_ax.set_xlim(-0.28, 4.55)
        cue_ax.set_ylim(0, 1)
        cue_ax.axis("off")
        for i in range(5):
            body_cue(cue_ax, i, 0.48, i, h=0.95)
            if i < 4:
                cue_ax.annotate(
                    "",
                    xy=(i + 0.62, 0.48),
                    xytext=(i + 0.38, 0.48),
                    arrowprops=dict(arrowstyle="->", color=LIGHT, lw=1.15),
                )
        top = 0.78
    else:
        top = 0.88

    # Symmetric side margins so the figure reads centered on the slide
    fig.subplots_adjust(left=0.12, right=0.88, top=top, bottom=0.18)

    stem = f"G2_repetition_variability_{variant}"
    png = OUT / f"{stem}.png"
    svg = OUT / f"{stem}.svg"
    fig.savefig(png, dpi=220, facecolor=BG, bbox_inches="tight", pad_inches=0.45)
    fig.savefig(svg, facecolor=BG, bbox_inches="tight", pad_inches=0.45)
    plt.close(fig)
    print("wrote", stem)
    return png, svg


def write_note():
    note = """# G2 design note

## Layout
Single progressive plot with **average + IQR**, and all 12 trajectories drawn.

## Identity
- Each trajectory is labeled at the right end: `{participant} · {T#}`
- Color = participant; linestyle = T1 / T2 / T3
- Legend includes Average and IQR

## Removed clutter
- “Median” callout arrow
- “normalized within each session…”
- “Session average” text
- “12/12 sessions…”
- “Fixed sequence order…”
"""
    (OUT / "G2_design_note.md").write_text(note)
    print("wrote G2_design_note.md")


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
    png_a, svg_a = render("A")
    render("B")
    write_note()
    shutil.copy2(png_a, OUT / "G2_repetition_variability.png")
    shutil.copy2(svg_a, OUT / "G2_repetition_variability.svg")
    print("wrote canonical G2_repetition_variability.{png,svg} (= A)")
