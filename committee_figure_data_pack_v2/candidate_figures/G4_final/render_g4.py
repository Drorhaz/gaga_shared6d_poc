#!/usr/bin/env python3
"""G4 anatomical figure — shared pose + magnitude gradient (hot+/cool−).

Body grammar: thick rounded links + small joint nodes (reference style).
All eight bodies share ONE canonical pose.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Polygon, Rectangle

PACK = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

PID_ORDER = ["252", "651", "671", "790"]

GRAY = "#B0B0B0"
JOINT = "#303030"
LAYOUT = "#A0A0A0"
UNAVAIL_EDGE = "#555555"
BG = "#FFFFFF"
INK = "#222222"
MUTED = "#666666"

# 9-step diverging: cool (minus) → gray → hot (plus)
# indices 0..3 cool, 4 gray, 5..8 hot
GRADIENT_COLORS = [
    "#08306B",  # −−−− strong decrease
    "#2171B5",  # −−−
    "#6BAED6",  # −−
    "#C6DBEF",  # −
    GRAY,       # no clear validated change / near zero
    "#FEC44F",  # +
    "#EC7014",  # ++
    "#CC4C02",  # +++
    "#7F0000",  # ++++ strong increase
]
CMAP = ListedColormap(GRADIENT_COLORS)
# Discrete bins on signed pooled R1+R2 change (absolute JcvPCA units), symmetric
# Center gray band = non-validated / not shown as magnitude
POOLED_VMAX = 0.05  # cap for color scale (authoritative file-06 values)
BOUNDARIES = [
    -POOLED_VMAX,
    -0.75 * POOLED_VMAX,
    -0.50 * POOLED_VMAX,
    -0.25 * POOLED_VMAX,
    -1e-9,
    1e-9,
    0.25 * POOLED_VMAX,
    0.50 * POOLED_VMAX,
    0.75 * POOLED_VMAX,
    POOLED_VMAX,
]
NORM = BoundaryNorm(BOUNDARIES, CMAP.N, clip=True)

TITLE = "Body-link contribution changes are participant-specific"

EXPECTED = {
    ("D12", "252"): (3, 20, "adequate"),
    ("D12", "651"): (4, 10, "adequate"),
    ("D12", "671"): (8, 18, "adequate"),
    ("D12", "790"): (7, 20, "adequate"),
    ("D13", "252"): (12, 20, "limited"),
    ("D13", "651"): (2, 10, "limited"),
    ("D13", "671"): (9, 17, "limited"),
    ("D13", "790"): (3, 18, "adequate"),
}

ROW_SPECS = [
    ("D12", "≈4 classes"),
    ("D13", "≈10 classes"),
]

# ---------------------------------------------------------------------------
# ONE shared canonical pose (anatomical: figure right = viewer left)
# ---------------------------------------------------------------------------
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
    # participant LEFT = +x
    "LShoulder": np.array([0.20, 0.56]),
    "LUArm": np.array([0.34, 0.38]),
    "LFArm": np.array([0.44, 0.18]),
    "LHand": np.array([0.50, 0.00]),
    # participant RIGHT = −x
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


def as_bool(v) -> bool:
    return str(v).strip().lower() in {"true", "1", "yes"}


def joint_token(tok: str) -> str:
    """Map participant-root ids (252/651/…) and aliases onto canonical joints."""
    if tok in CANON:
        return tok
    if tok.isdigit() or tok in PID_ORDER:
        return "pelvis"
    # occasional aliases in tables
    alias = {
        "neck_to_head": "Head",
        "Head": "Head",
    }
    return alias.get(tok, tok)


def draw_thick_link(ax, p0, p1, *, color, lw, z=3, alpha=0.95, understroke=False):
    x0, y0 = p0
    x1, y1 = p1
    if understroke:
        ax.plot([x0, x1], [y0, y1], color="#2F2F2F", lw=lw + 2.0, solid_capstyle="round", zorder=z - 0.2, alpha=0.35)
    ax.plot([x0, x1], [y0, y1], color=color, lw=lw, solid_capstyle="round", zorder=z, alpha=alpha)


def _capsule_poly(a, b, width: float, n: int = 24) -> np.ndarray:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    half = 0.5 * width
    if L < 1e-9:
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return np.column_stack([a[0] + half * np.cos(ang), a[1] + half * np.sin(ang)])
    u = d / L
    v = np.array([-u[1], u[0]])
    ang = np.arctan2(v[1], v[0])
    t = np.linspace(-np.pi / 2, np.pi / 2, max(8, n // 2))
    cap_b = np.column_stack([b[0] + half * np.cos(ang + t), b[1] + half * np.sin(ang + t)])
    cap_a = np.column_stack([a[0] + half * np.cos(ang + np.pi + t), a[1] + half * np.sin(ang + np.pi + t)])
    return np.vstack([cap_b, cap_a])


def draw_unavailable(ax, p0, p1):
    draw_thick_link(ax, p0, p1, color=UNAVAIL_EDGE, lw=10, z=3.2, alpha=0.30)
    ax.add_patch(
        Polygon(
            _capsule_poly(p0, p1, 0.055),
            closed=True,
            facecolor="#F2F2F2",
            edgecolor=UNAVAIL_EDGE,
            linewidth=1.4,
            hatch="xxxx",
            zorder=3.5,
        )
    )


def signed_pooled_magnitude(row06: dict | None, row04: dict) -> float | None:
    """Signed pooled R1+R2 change for validated links only; None → gray."""
    if not as_bool(row04["display_highlight"]):
        return None
    if row06 is None or row06.get("pooled_R1R2_change_signed") is None:
        # fallback: mid-bin by direction from file 04
        return 0.35 * POOLED_VMAX if row04["direction_label"] == "increased_contribution" else -0.35 * POOLED_VMAX
    val = float(row06["pooled_R1R2_change_signed"])
    if not np.isfinite(val):
        return None
    return float(np.clip(val, -POOLED_VMAX, POOLED_VMAX))


def color_for_signed(val: float | None) -> str:
    if val is None:
        return GRAY
    rgba = CMAP(NORM(val))
    return matplotlib.colors.to_hex(rgba)


def load_data():
    rows04 = list(csv.DictReader(open(PACK / "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv")))
    rows03 = list(csv.DictReader(open(PACK / "03_LONGITUDINAL_LINK_EVIDENCE.csv")))
    by03 = {}
    for r in rows03:
        by03[(r["comparison_internal"], r["participant_id"], r["canonical_link_id"])] = r
    # pooled R1+R2 signed (for annotation / optional cross-check; magnitude bins use NV units)
    pack06 = json.load(open(PACK / "06_JCVPCA_ROBUSTNESS.json"))
    by_pooled = {}
    for r in pack06["link_level_robustness"]:
        by_pooled[(r["comparison_internal"], r["participant_id"], r["canonical_link_id"])] = r
    return rows04, by03, by_pooled


def verify_counts(rows04):
    for (comp, pid), (hi_e, n_e, _) in EXPECTED.items():
        sub = [r for r in rows04 if r["comparison_internal"] == comp and r["participant_id"] == pid]
        measured = [r for r in sub if as_bool(r["display_available"]) and not as_bool(r["display_excluded"])]
        hi = sum(as_bool(r["display_highlight"]) for r in measured)
        assert (hi, len(measured)) == (hi_e, n_e), f"{comp} {pid}: {hi}/{len(measured)} != {hi_e}/{n_e}"
    print("counts OK")


def draw_avatar(ax, rows, by_pooled, *, lw_gray=8.0, lw_hi=10.5, joint_s=14):
    ax.set_aspect("equal")
    ax.axis("off")

    # Base body in shared pose (quiet gray) — same for every cell
    for a, b in FULL_SKELETON:
        draw_thick_link(ax, CANON[a], CANON[b], color="#D0D0D0", lw=lw_gray - 1.5, z=1.0, alpha=0.55)

    # Data overlays on the SAME pose
    for r in rows:
        a = joint_token(r["proximal_joint"])
        b = joint_token(r["distal_joint"])
        if r["canonical_link_id"] in {"neck_to_head", "Neck2_to_Head"}:
            a, b = "Neck2", "Head"
        if r["canonical_link_id"] == "Ab_to_Chest":
            a, b = "Ab", "Chest"
        if a not in CANON or b not in CANON:
            continue
        p0, p1 = CANON[a], CANON[b]

        if as_bool(r["display_excluded"]) or not as_bool(r["display_available"]):
            draw_unavailable(ax, p0, p1)
            continue

        key = (r["comparison_internal"], r["participant_id"], r["canonical_link_id"])
        val = signed_pooled_magnitude(by_pooled.get(key), r)
        if val is None:
            draw_thick_link(ax, p0, p1, color=GRAY, lw=lw_gray, z=2.5, alpha=0.92)
        else:
            col = color_for_signed(val)
            draw_thick_link(ax, p0, p1, color=col, lw=lw_hi, z=3.4, alpha=0.96, understroke=True)

    # Joint nodes
    for p in CANON.values():
        ax.scatter([p[0]], [p[1]], s=joint_s, color=JOINT, zorder=6, edgecolors="none")

    ax.set_xlim(-0.72, 0.72)
    ax.set_ylim(-0.95, 1.05)


def draw_color_diagram(fig, left=0.16, bottom=0.04, width=0.68, height=0.07):
    """Numeric cool→hot magnitude scale (Δ body-link contribution)."""
    ax = fig.add_axes([left, bottom, width, height])
    n = len(GRADIENT_COLORS)
    for i, col in enumerate(GRADIENT_COLORS):
        ax.add_patch(Rectangle((i, 0.35), 1, 0.65, facecolor=col, edgecolor="white", linewidth=0.7))
    ax.set_xlim(0, n)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    # Numeric tick labels at bin centers / edges in Δ contribution units
    # bins: [-0.05,-0.0375,-0.025,-0.0125,0, +0.0125,+0.025,+0.0375,+0.05]
    ax.set_xticks([0.5, 2.5, 4.5, 6.5, 8.5])
    ax.set_xticklabels(["−0.05", "−0.025", "0", "+0.025", "+0.05"], fontsize=9.5, color=INK)
    ax.tick_params(length=0, pad=2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(
        0.0,
        0.08,
        "Δ body-link contribution  (cool = decrease,  hot = increase;  gray = no validated change;  hatch = unavailable)",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.5,
        color=MUTED,
    )


def caption(pid, hi, n, *, show_pid: bool) -> str:
    if show_pid:
        return f"{pid}\n{hi}/{n}"
    return f"{hi}/{n}"


def render(variant: str = "B"):
    rows04, _by03, by_pooled = load_data()
    verify_counts(rows04)

    if variant == "A":
        figsize = (14.0, 9.0)
        lw_gray, lw_hi, joint_s = 8.0, 10.5, 13
        top, bottom, hspace, wspace = 0.86, 0.14, 0.10, 0.05
    else:
        figsize = (14.2, 8.9)
        lw_gray, lw_hi, joint_s = 8.8, 11.5, 15
        top, bottom, hspace, wspace = 0.87, 0.135, 0.08, 0.035

    fig = plt.figure(figsize=figsize, dpi=150)
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 4, left=0.06, right=0.99, top=top, bottom=bottom, hspace=hspace, wspace=wspace)

    fig.suptitle(TITLE, fontsize=16.5 if variant == "A" else 17.5, fontweight="bold", color=INK, y=0.97)
    # Minimal method line: what "pooled" and R1+R2 mean
    fig.text(
        0.525,
        0.925,
        "Pooled = ex09–ex13 as one sequence   ·   R1+R2 = both repetitions aggregated",
        ha="center",
        fontsize=10.5,
        color=MUTED,
    )

    for r, (comp, row_label) in enumerate(ROW_SPECS):
        for c, pid in enumerate(PID_ORDER):
            ax = fig.add_subplot(gs[r, c])
            sub = [row for row in rows04 if row["comparison_internal"] == comp and row["participant_id"] == pid]
            hi_e, n_e, _cov = EXPECTED[(comp, pid)]
            draw_avatar(ax, sub, by_pooled, lw_gray=lw_gray, lw_hi=lw_hi, joint_s=joint_s)
            ax.set_title(
                caption(pid, hi_e, n_e, show_pid=(r == 0)),
                fontsize=10,
                color=INK,
                pad=2,
                linespacing=1.15,
                fontweight="bold" if r == 0 else "normal",
            )
            if c == 0:
                ax.annotate(
                    row_label,
                    xy=(-0.12, 0.5),
                    xycoords="axes fraction",
                    fontsize=11,
                    ha="center",
                    va="center",
                    rotation=90,
                    color=INK,
                    fontweight="bold",
                )

    draw_color_diagram(fig)

    stem = f"G4_anatomical_localization_{variant}"
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=220 if ext == "png" else None, facecolor=BG, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("wrote", stem)


def write_note():
    note = f"""# G4 anatomical design note

## 1. Title
{TITLE}

## 2. Message
Validated body-link changes localize differently across participants; color = signed pooled R1+R2 Δ contribution.

## 3. Minimal on-figure text
- Pooled = ex09–ex13 as one sequence; R1+R2 = both repetitions aggregated
- Color bar with numeric Δ (−0.05 … +0.05)
- Row labels: ≈4 / ≈10 classes; cell labels: pid + k/n only

## 4. Color (numbers)
`pooled_R1R2_change_signed` (file 06), capped ±0.05. Cool = decrease, hot = increase, gray = no validated change, hatch = unavailable.
Validation gate for coloring remains files 03/04 (own repetition variability).
"""
    (OUT / "G4_anatomical_design_note.md").write_text(note)
    print("wrote note")


if __name__ == "__main__":
    import matplotlib as mpl
    import shutil

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    render("A")
    render("B")
    write_note()
    for ext in ("png", "svg", "pdf"):
        shutil.copy2(OUT / f"G4_anatomical_localization_B.{ext}", OUT / f"G4_anatomical_localization.{ext}")
    print("canonical = B")
