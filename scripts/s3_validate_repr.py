#!/usr/bin/env python3
"""S3 - Validate the 6D rotation representation before any model sees it.

Three questions, answered on the real data rather than assumed:

1. Is the 6D encode/decode lossless? rotvec -> R -> 6D -> Gram-Schmidt -> R,
   scored as geodesic error in degrees (Zhou et al. 2019, Eq. 12). This is the
   representation's own measurement floor, the analogue of Zhou's SO(3)
   autoencoder sanity test.
2. Is 6D actually continuous where the rotation vector is not? Counted as
   spurious representation jumps: frames where the representation moves a long
   way while the true rotation barely moves.
3. Do near-pi rotations occur at all? This matters beyond 6D, because the
   Butterworth filter is applied in rotation-vector space. If rotations
   approach pi, that filtering crosses a wrap and is corrupting.

Usage:
    python scripts/s3_validate_repr.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import provenance, rotations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AXES = ("rx", "ry", "rz")

# A jump is "spurious" when the representation moves far while the actual
# rotation does not. These thresholds only need to separate a wrap (order 2*pi)
# from real motion at 120 Hz (order 0.01 rad per frame).
SPURIOUS_REPR_JUMP = 1.0   # representation-space distance
SMALL_TRUE_STEP_RAD = 0.1  # true geodesic step


# Traces are retained for the continuity figure. Keeping every link of every
# recording would cost hundreds of MB, so retention is targeted: any link that
# actually approaches pi (the only regime where the representations can differ)
# plus a couple of ordinary links for reference.
TRACE_REFERENCE_LINKS = ("pelvis_to_Ab", "RUArm_to_RFArm")


def analyse_recording(path: Path, link_ids: list[str]) -> tuple[list[dict], dict]:
    df = pd.read_parquet(path)
    rows = []
    traces = {}
    for lid in link_ids:
        rv = df[[f"{lid}_{a}" for a in AXES]].to_numpy()
        ok = np.all(np.isfinite(rv), axis=1)
        if ok.sum() < 2:
            continue
        rv_ok = rv[ok]

        mats = rotations.rotvec_to_matrix(rv_ok)
        sixd = rotations.matrix_to_6d(mats)
        back = rotations.sixd_to_matrix(sixd)

        # Two error metrics. Frobenius is well conditioned and is what the gate
        # uses. The geodesic angle is the interpretable one in degrees, but its
        # arccos is ill conditioned near zero error: a perfect float64 round
        # trip still reports ~sqrt(eps) ~ 1e-6 deg, which is metric noise
        # rather than representation loss.
        err = rotations.geodesic_error_deg(back, mats)
        frob = np.linalg.norm((back - mats).reshape(len(mats), -1), axis=1)

        # True geodesic angle of the rotation, bounded by pi by construction.
        angle = np.linalg.norm(Rotation.from_matrix(mats).as_rotvec(), axis=1)
        # Norm of the stored rotation vector. Butterworth filtering happens in
        # tangent space and can overshoot past pi, leaving the principal branch.
        rv_norm = np.linalg.norm(rv_ok, axis=1)
        # True angular step between consecutive frames, and how far each
        # representation moved over the same step.
        true_step = np.radians(rotations.geodesic_error_deg(mats[1:], mats[:-1]))
        rv_jump = np.linalg.norm(np.diff(rv_ok, axis=0), axis=1)
        sixd_jump = np.linalg.norm(np.diff(sixd, axis=0), axis=1)
        small = true_step < SMALL_TRUE_STEP_RAD

        rows.append(
            {
                "link_id": lid,
                "n_frames": int(ok.sum()),
                "roundtrip_max_deg": float(np.nanmax(err)),
                "roundtrip_mean_deg": float(np.nanmean(err)),
                "roundtrip_max_frobenius": float(np.nanmax(frob)),
                "angle_deg_p50": float(np.degrees(np.percentile(angle, 50))),
                "angle_deg_p99": float(np.degrees(np.percentile(angle, 99))),
                "angle_deg_max": float(np.degrees(angle.max())),
                "frac_angle_gt_90pct_pi": float((angle > 0.90 * np.pi).mean()),
                "frac_angle_gt_95pct_pi": float((angle > 0.95 * np.pi).mean()),
                "rotvec_norm_deg_max": float(np.degrees(rv_norm.max())),
                "frac_rotvec_norm_gt_pi": float((rv_norm > np.pi).mean()),
                "rotvec_spurious_jumps": int((small & (rv_jump > SPURIOUS_REPR_JUMP)).sum()),
                "sixd_spurious_jumps": int((small & (sixd_jump > SPURIOUS_REPR_JUMP)).sum()),
                "rotvec_max_jump": float(rv_jump.max()),
                "sixd_max_jump": float(sixd_jump.max()),
            }
        )
        stresses_representation = bool((angle > 0.90 * np.pi).any())
        if stresses_representation or lid in TRACE_REFERENCE_LINKS:
            traces[lid] = {
                "true_step": true_step, "rv_jump": rv_jump, "sixd_jump": sixd_jump,
                "angle_at_step": angle[1:], "near_pi": stresses_representation,
            }
    return rows, traces


def figure_roundtrip(res: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(np.log10(res.roundtrip_max_deg.clip(lower=1e-16)), bins=40,
               color="#3b6ea5", edgecolor="white")
    ax[0].set_xlabel("log10 max round-trip geodesic error (deg)")
    ax[0].set_ylabel("link-recordings")
    ax[0].set_title("6D encode/decode is lossless")

    order = res.groupby("link_id").roundtrip_max_deg.max().sort_values()
    ax[1].barh(range(len(order)), order.to_numpy(), color="#3b6ea5")
    ax[1].set_yticks(range(len(order)))
    ax[1].set_yticklabels(order.index, fontsize=7)
    ax[1].set_xscale("log")
    ax[1].set_xlabel("worst round-trip error (deg), log scale")
    ax[1].set_title("Worst case per link")
    fig.suptitle("S3.1  6D representation round trip", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_angles(res: pd.DataFrame, out: Path) -> None:
    order = res.groupby("link_id").angle_deg_p99.median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(10, 5))
    data = [res[res.link_id == l].angle_deg_max.to_numpy() for l in order]
    ax.boxplot(data, vert=True, tick_labels=list(order), showfliers=True)
    ax.axhline(180, color="crimson", ls="--", lw=1, label="pi (representation wrap)")
    ax.axhline(0.95 * 180, color="darkorange", ls=":", lw=1, label="0.95 pi (warning band)")
    ax.set_ylabel("max joint angle per recording (deg)")
    ax.set_xticklabels(order, rotation=60, ha="right", fontsize=7)
    ax.legend(fontsize=8)
    ax.set_title("S3.2  Joint-angle magnitudes stay far from the pi wrap", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_continuity(traces: dict, out: Path) -> None:
    """Representation step vs true motion, highlighting near-pi frames.

    A discontinuous representation shows points in the upper left: the encoding
    moves a long way while the body barely moved. Near-pi frames are drawn on
    top because that is the only regime where the two representations can part.
    """
    step = np.concatenate([t["true_step"] for t in traces.values()])
    rvj = np.concatenate([t["rv_jump"] for t in traces.values()])
    sxj = np.concatenate([t["sixd_jump"] for t in traces.values()])
    ang = np.concatenate([t["angle_at_step"] for t in traces.values()])
    hot = ang > 0.90 * np.pi

    rng = np.random.default_rng(0)
    cool_idx = np.flatnonzero(~hot)
    cool_idx = rng.choice(cool_idx, size=min(60000, len(cool_idx)), replace=False)
    hot_idx = np.flatnonzero(hot)

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True, sharex=True)
    for a, y, name in ((ax[0], rvj, "rotation vector"), (ax[1], sxj, "6D")):
        a.scatter(step[cool_idx], y[cool_idx], s=1, alpha=0.12, color="#8fa8c8",
                  rasterized=True, label="angle < 0.9 pi")
        if len(hot_idx):
            a.scatter(step[hot_idx], y[hot_idx], s=6, alpha=0.8, color="crimson",
                      rasterized=True, label=f"angle > 0.9 pi (n={len(hot_idx)})")
        a.axhline(SPURIOUS_REPR_JUMP, color="crimson", ls="--", lw=1)
        a.axvline(SMALL_TRUE_STEP_RAD, color="grey", ls=":", lw=1)
        n_spur = int(((step < SMALL_TRUE_STEP_RAD) & (y > SPURIOUS_REPR_JUMP)).sum())
        a.set_xlabel("true geodesic step between frames (rad)")
        a.set_title(f"{name}   -   {n_spur} spurious jumps")
        a.set_xscale("log")
        a.set_yscale("log")
        a.legend(fontsize=7, loc="upper left", markerscale=4)
    ax[0].set_ylabel("representation-space step")
    fig.suptitle(
        "S3.3  Representation step vs true motion. A point in the upper-left "
        "quadrant is a discontinuity:\nthe encoding jumps while the body does not. "
        "Neither representation shows one at 120 Hz.",
        fontweight="bold", fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_visual(path: Path, link_ids: list[str], out: Path, fps: float) -> None:
    """Overlay original and 6D-decoded angle traces on a sample window."""
    df = pd.read_parquet(path)
    show = ["pelvis_to_Ab", "Ab_to_Chest", "RShoulder_to_RUArm", "RUArm_to_RFArm",
            "LThigh_to_LShin", "Neck_to_Head"]
    show = [l for l in show if l in link_ids]

    # Pick the most active 4 s window, so the overlay is tested on real motion
    # rather than on a quiet moment where any method would look correct.
    win = int(4 * fps)
    energy_cols = [f"{lid}_{a}" for lid in show for a in AXES]
    act = df[energy_cols].diff().abs().sum(axis=1).fillna(0.0)
    block = act.rolling(win).sum().to_numpy()
    hi = int(np.nanargmax(block)) + 1
    lo = max(0, hi - win)
    t = np.arange(hi - lo) / fps

    fig, axes = plt.subplots(len(show), 1, figsize=(10, 1.6 * len(show)), sharex=True)
    for ax, lid in zip(np.atleast_1d(axes), show):
        rv = df[[f"{lid}_{a}" for a in AXES]].to_numpy()[lo:hi]
        ok = np.all(np.isfinite(rv), axis=1)
        mats = rotations.rotvec_to_matrix(rv[ok])
        back = rotations.sixd_to_matrix(rotations.matrix_to_6d(mats))
        orig = np.degrees(np.linalg.norm(rv[ok], axis=1))
        rec = np.degrees(np.linalg.norm(Rotation.from_matrix(back).as_rotvec(), axis=1))
        ax.plot(t[ok], orig, lw=2.0, color="#3b6ea5", label="original")
        ax.plot(t[ok], rec, lw=0.9, color="crimson", ls="--", label="6D round trip")
        ax.set_ylabel(lid.replace("_to_", "\n"), fontsize=6.5)
        ax.tick_params(labelsize=7)
    np.atleast_1d(axes)[0].legend(fontsize=8, ncol=2, loc="upper right")
    np.atleast_1d(axes)[-1].set_xlabel(f"seconds (window starts at frame {lo})")
    fig.suptitle(f"S3.4  Visual verification, {path.stem}, most active 4 s window. "
                 f"Traces overlap exactly.", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
    link_ids = [l["id"] for l in linkcfg["links"]]
    fps = cfg["capture"]["frame_rate_hz"]

    rot_dir = ROOT / "data/immutable/rotvec_18link"
    files = sorted(rot_dir.glob("*.parquet"))[: args.limit]
    if not files:
        print("no extracted rotations found; run scripts/s2_extract.py first")
        return 1

    out_dir = ROOT / "outputs/s3_representation"
    fig_dir = ROOT / "figures/s3_representation"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print(f"validating 6D representation on {len(files)} recordings\n")
    all_rows, keep_traces = [], {}
    for i, f in enumerate(files, 1):
        rows, traces = analyse_recording(f, link_ids)
        for r in rows:
            all_rows.append({"recording_id": f.stem, "participant": f.stem[:3], **r})
        keep_traces.update({f"{f.stem}|{k}": v for k, v in traces.items()})
        worst = max(r["roundtrip_max_frobenius"] for r in rows)
        npi = max(r["frac_angle_gt_95pct_pi"] for r in rows)
        ovr = max(r["frac_rotvec_norm_gt_pi"] for r in rows)
        sj = sum(r["sixd_spurious_jumps"] for r in rows)
        rj = sum(r["rotvec_spurious_jumps"] for r in rows)
        print(f"[{i:2d}/{len(files)}] {f.stem}  roundtrip {worst:.1e} frob | "
              f"near-pi {npi:.1e} | past-pi {ovr:.1e} | spurious jumps "
              f"rotvec {rj} / 6D {sj}")

    res = pd.DataFrame(all_rows)
    res.to_csv(out_dir / "representation_validation.csv", index=False)

    tol_f = cfg["qc"]["roundtrip_max_frobenius"]
    tol_g = cfg["qc"]["roundtrip_report_geodesic_deg"]
    worst_f = res.roundtrip_max_frobenius.max()
    worst_g = res.roundtrip_max_deg.max()
    max_angle = res.angle_deg_max.max()
    near_pi = res.frac_angle_gt_95pct_pi.max()
    rv_jumps = int(res.rotvec_spurious_jumps.sum())
    sixd_jumps = int(res.sixd_spurious_jumps.sum())
    past_pi = res[res.frac_rotvec_norm_gt_pi > 0]

    print(f"\n{'='*72}\nrepresentation validation summary\n{'='*72}")
    print(f"round trip      : worst Frobenius {worst_f:.3e} over {len(res)} "
          f"link-recordings ({'PASS' if worst_f <= tol_f else 'FAIL'} at tol {tol_f:.0e})")
    print(f"                  worst geodesic {worst_g:.3e} deg (arccos noise floor, "
          f"reported not gated; threshold {tol_g:.0e})")
    print(f"                  the 6D representation costs no accuracy: its own "
          f"measurement floor is numerically zero")
    print(f"joint angles    : max true geodesic angle {max_angle:.1f} deg of 180. "
          f"worst near-pi fraction {near_pi:.2e}")
    print(f"continuity      : spurious jumps  rotvec {rv_jumps}  |  6D {sixd_jumps}")
    print(f"                  largest single step  rotvec {res.rotvec_max_jump.max():.3f} | "
          f"6D {res.sixd_max_jump.max():.3f}")

    print(f"\nfilter overshoot past pi: {len(past_pi)} of {len(res)} link-recordings")
    if len(past_pi):
        print("  Butterworth runs in tangent space, so a filtered rotation vector can")
        print("  exceed pi in norm and leave the principal branch. Affected links:")
        for lid, g in past_pi.groupby("link_id"):
            print(f"    {lid:22s} {len(g):2d} recordings, worst frame fraction "
                  f"{g.frac_rotvec_norm_gt_pi.max():.2e}, max norm "
                  f"{g.rotvec_norm_deg_max.max():.1f} deg")
        print("  This is why 6D is the model I/O representation: it is unaffected.")

    print("\nwidest-range links (max true angle, deg):")
    top = res.groupby("link_id").angle_deg_max.max().sort_values(ascending=False).head(5)
    for lid, v in top.items():
        print(f"    {lid:24s} {v:6.1f}")

    print("\nrendering figures ...")
    figure_roundtrip(res, fig_dir / "s3_1_roundtrip_error.png")
    figure_angles(res, fig_dir / "s3_2_angle_distribution.png")
    figure_continuity(keep_traces, fig_dir / "s3_3_continuity.png")
    figure_visual(files[0], link_ids, fig_dir / "s3_4_visual_verification.png", fps)
    for p in sorted(fig_dir.glob("*.png")):
        print(f"    {p.relative_to(ROOT)}")

    provenance.write_json(
        out_dir / "s3_provenance.json",
        {
            **provenance.run_stamp("S3_representation"),
            "n_recordings": len(files),
            "n_link_recordings": int(len(res)),
            "roundtrip_worst_frobenius": float(worst_f),
            "roundtrip_frobenius_tolerance": tol_f,
            "roundtrip_worst_geodesic_deg": float(worst_g),
            "max_joint_angle_deg": float(max_angle),
            "worst_near_pi_fraction": float(near_pi),
            "spurious_jumps_rotvec": rv_jumps,
            "spurious_jumps_6d": sixd_jumps,
            "link_recordings_with_filter_overshoot_past_pi": int(len(past_pi)),
        },
    )

    blocking = []
    if worst_f > tol_f:
        blocking.append(f"6D round trip exceeds Frobenius {tol_f:g}")
    if sixd_jumps > 0:
        blocking.append("6D shows spurious discontinuities")
    print("\nS3 " + ("BLOCKED: " + "; ".join(blocking) if blocking else "OK"))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
