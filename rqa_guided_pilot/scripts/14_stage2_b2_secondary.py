#!/usr/bin/env python3
"""Stage 2 secondary: B2 root-relative hand positional speed (not primary gate).

Owns its own T1 parameter selection — does not reuse A1 locks automatically.
Participants 651/790, ex11/ex13, L/R hand root-relative speed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.ami_fnn import (
    average_mutual_information,
    choose_m_from_fnn,
    false_nearest_neighbors,
    first_local_minimum,
)
from rqa_pilot.io_readonly import build_segment_index, load_link_config, load_rotvec
from rqa_pilot.paths import REPO_ROOT, ensure_rqa_dirs, rqa_path
from rqa_pilot.rqa_core import auto_rqa
from rqa_pilot.signals import downsample, finite_clean, link_speed_deg_s, normalize_series
from rqa_pilot.surrogates import full_shuffle, make_surrogate

# Reuse position reader from feature audit script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_representation_audit import (  # noqa: E402
    JCVPCA,
    MANIFEST,
    read_selected_bone_positions,
    _bone_token,
    _load_manifest_t1,
)

OUT = rqa_path("outputs", "stage2", "b2")
OUT.mkdir(parents=True, exist_ok=True)
FIG = rqa_path("figures", "stage2")
FIG.mkdir(parents=True, exist_ok=True)

PIDS = ["651", "790"]
EXES = [11, 13]
HANDS = ("LHand", "RHand")
NATIVE = 120.0


def _recording_meta():
    man = json.loads(MANIFEST.read_text())
    return {r["recording_id"]: r for r in man["recordings"]}


def _rootrel_hand_speed(recording_id: str, start: int, end: int, hand: str) -> np.ndarray:
    meta = _recording_meta()[recording_id]
    src = (JCVPCA / "data" / "raw_skeleton" / meta["participant"] / meta["source_file"]).resolve()
    if not src.exists():
        src = (REPO_ROOT / meta["source_path"]).resolve()
    data = read_selected_bone_positions(src, ["pelvis", hand])
    bones = data["bones"]
    bindex = {_bone_token(b): i for i, b in enumerate(bones)}
    for i, b in enumerate(bones):
        if b == data["root"]:
            bindex["pelvis"] = i
    pos = data["positions_m"]
    sl = slice(start, end)
    root = pos[sl, bindex["pelvis"], :]
    h = pos[sl, bindex[_bone_token(hand) if hand in bindex else hand], :]
    rel = h - root
    spd = np.linalg.norm(np.diff(rel, axis=0), axis=1) * NATIVE  # m/s
    return spd.astype(np.float64)


def _a1_arm_speed(recording_id: str, start: int, end: int, hand: str) -> np.ndarray:
    link_ids, regions = load_link_config()
    region = "left_arm" if hand.startswith("L") else "right_arm"
    idx = [i for i, lid in enumerate(link_ids) if regions[lid] == region]
    rv = load_rotvec(recording_id)[start:end]
    return np.nanmean(link_speed_deg_s(rv, NATIVE)[:, idx], axis=1)


def t1_diagnostics(segs: pd.DataFrame) -> dict:
    """Own AMI/FNN/rate/radius selection on T1 only."""
    rows = []
    ami_taus = []
    fnn_ms = []
    for rec in segs[segs.timepoint == 1].itertuples(index=False):
        for hand in HANDS:
            x = finite_clean(_rootrel_hand_speed(rec.recording_id, int(rec.start_frame), int(rec.end_frame), hand))
            if x.size < 200:
                continue
            ami = average_mutual_information(x, max_tau=60)
            tau = first_local_minimum(ami)
            if tau is not None:
                ami_taus.append(tau)
            fnn = false_nearest_neighbors(x, tau=tau or 18, max_m=8)
            m = choose_m_from_fnn(fnn)
            if m is not None:
                fnn_ms.append(m)
            rows.append(
                {
                    "segment_id": rec.segment_id,
                    "hand": hand,
                    "ami_tau": tau,
                    "fnn_m": m,
                    "n": int(x.size),
                    "median_amp_m_s": float(np.nanmedian(x)),
                }
            )
    pd.DataFrame(rows).to_csv(OUT / "b2_t1_ami_fnn.csv", index=False)
    tau = int(np.median(ami_taus)) if ami_taus else 18
    m = int(np.median(fnn_ms)) if fnn_ms else 4
    # rate bake-off physically matched
    tau_s = tau / NATIVE
    rate_rows = []
    for rate in (120, 60, 30):
        tau_r = max(1, int(round(tau_s * rate)))
        drops = []
        rrs = []
        for rec in segs[segs.timepoint == 1].itertuples(index=False):
            for hand in HANDS:
                x = finite_clean(_rootrel_hand_speed(rec.recording_id, int(rec.start_frame), int(rec.end_frame), hand))
                x = downsample(x, NATIVE, rate)
                if x.size < 80:
                    continue
                q = auto_rqa(
                    x,
                    tau=tau_r,
                    m=m,
                    theiler=tau_r,
                    lmin=2,
                    mode="fixed_mean_rescaled",
                    radius_frac=0.35,
                )
                qs = auto_rqa(
                    make_surrogate(x, "full_shuffle", max(2, int(round(0.3 * rate))), seed=0),
                    tau=tau_r,
                    m=m,
                    theiler=tau_r,
                    lmin=2,
                    mode="fixed_mean_rescaled",
                    radius_frac=0.35,
                )
                if np.isfinite(q["DET"]) and np.isfinite(qs["DET"]):
                    drops.append(q["DET"] - qs["DET"])
                    rrs.append(q["RR"])
        rate_rows.append(
            {
                "rate": rate,
                "tau_frames": tau_r,
                "median_DET_drop": float(np.median(drops)) if drops else None,
                "median_RR": float(np.median(rrs)) if rrs else None,
                "n": len(drops),
            }
        )
    pd.DataFrame(rate_rows).to_csv(OUT / "b2_t1_rate_bakeoff.csv", index=False)
    # choose rate with strongest shuffle disruption among usable RR
    usable = [r for r in rate_rows if r["median_RR"] and 0.01 <= r["median_RR"] <= 0.15 and r["median_DET_drop"]]
    if not usable:
        usable = [r for r in rate_rows if r["median_DET_drop"] is not None]
    primary_rate = int(max(usable, key=lambda r: r["median_DET_drop"] or -1)["rate"]) if usable else 120
    tau_primary = max(1, int(round(tau_s * primary_rate)))
    # radius scan at primary rate for target RR ~3%
    rad_rows = []
    for frac in (0.25, 0.30, 0.35, 0.40, 0.45):
        rrs = []
        for rec in segs[(segs.timepoint == 1) & (segs.participant == "651")].itertuples(index=False):
            x = finite_clean(_rootrel_hand_speed(rec.recording_id, int(rec.start_frame), int(rec.end_frame), "LHand"))
            x = downsample(x, NATIVE, primary_rate)
            q = auto_rqa(x, tau=tau_primary, m=m, theiler=tau_primary, lmin=2, mode="fixed_mean_rescaled", radius_frac=frac)
            if np.isfinite(q["RR"]):
                rrs.append(q["RR"])
        rad_rows.append({"radius_frac": frac, "median_RR": float(np.median(rrs)) if rrs else None})
    pd.DataFrame(rad_rows).to_csv(OUT / "b2_t1_radius_scan.csv", index=False)
    # pick frac closest to RR=0.03
    best_frac = min(
        (r for r in rad_rows if r["median_RR"] is not None),
        key=lambda r: abs(r["median_RR"] - 0.03),
        default={"radius_frac": 0.35},
    )["radius_frac"]
    lock = {
        "representation": "B2_root_relative_hand_speed_m_s",
        "selected_from": "T1-only 651/790 ex11/13 L/R hand",
        "primary_rate_hz": primary_rate,
        "tau_frames": tau_primary,
        "tau_seconds": tau_primary / primary_rate,
        "m": m,
        "theiler": tau_primary,
        "lmin": 2,
        "radius_frac_mean": best_frac,
        "block_shuffle_seconds": 0.30,
        "note": "B2-specific lock; not A1 Stage 1 parameters",
        "ami_tau_median_at_120": int(np.median(ami_taus)) if ami_taus else None,
        "fnn_m_median": m,
        "rate_bakeoff": rate_rows,
        "radius_scan": rad_rows,
        "t1_pass": bool(ami_taus) and bool(usable),
    }
    (OUT / "b2_parameter_lock.json").write_text(json.dumps(lock, indent=2))
    return lock


def run_metrics(segs: pd.DataFrame, lock: dict) -> pd.DataFrame:
    rate = lock["primary_rate_hz"]
    tau = lock["tau_frames"]
    m = lock["m"]
    frac = lock["radius_frac_mean"]
    block = max(2, int(round(lock["block_shuffle_seconds"] * rate)))
    rows = []
    for rec in segs.itertuples(index=False):
        for hand in HANDS:
            raw = finite_clean(_rootrel_hand_speed(rec.recording_id, int(rec.start_frame), int(rec.end_frame), hand))
            a1 = finite_clean(_a1_arm_speed(rec.recording_id, int(rec.start_frame), int(rec.end_frame), hand))
            if raw.size < 100:
                continue
            x = downsample(raw, NATIVE, rate)
            a1d = downsample(a1, NATIVE, rate)
            n = min(len(x), len(a1d))
            x, a1d = x[:n], a1d[:n]
            corr = float(np.corrcoef(x, a1d)[0, 1]) if n > 30 and np.isfinite(x).all() else None
            for norm in ("amp_preserving", "trial_zscore"):
                xn = normalize_series(x, norm)
                mode = "fixed_mean_rescaled" if norm == "amp_preserving" else "target_rr"
                q = auto_rqa(
                    xn,
                    tau=tau,
                    m=m,
                    theiler=tau,
                    lmin=2,
                    mode=mode,
                    radius_frac=frac,
                    target_rr=0.03,
                )
                qf = auto_rqa(
                    make_surrogate(xn, "full_shuffle", block, seed=11),
                    tau=tau,
                    m=m,
                    theiler=tau,
                    lmin=2,
                    mode=mode,
                    radius_frac=frac,
                    target_rr=0.03,
                )
                qb = auto_rqa(
                    make_surrogate(xn, "block_shuffle", block, seed=12),
                    tau=tau,
                    m=m,
                    theiler=tau,
                    lmin=2,
                    mode=mode,
                    radius_frac=frac,
                    target_rr=0.03,
                )
                rows.append(
                    {
                        "participant": str(rec.participant),
                        "timepoint": int(rec.timepoint),
                        "repetition": int(rec.repetition),
                        "exercise_id": int(rec.exercise_id),
                        "segment_id": rec.segment_id,
                        "hand": hand,
                        "normalization": norm,
                        "corr_vs_A1_arm": corr,
                        "duration_s": float(rec.duration_s),
                        "n_samples": float(x.size),
                        "RR": q["RR"],
                        "DET": q["DET"],
                        "Lmean": q["Lmean"],
                        "LAM": q["LAM"],
                        "ENTR": q["ENTR"],
                        "DET_full_shuffle": qf["DET"],
                        "DET_block_shuffle": qb["DET"],
                        "DET_drop_full": (q["DET"] - qf["DET"]) if np.isfinite(q["DET"]) and np.isfinite(qf["DET"]) else np.nan,
                        "median_amp": float(np.nanmedian(x)),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "b2_metrics.csv", index=False)
    return df


def classify(df: pd.DataFrame, lock: dict) -> dict:
    amp = df[df.normalization == "amp_preserving"]
    zsc = df[df.normalization == "trial_zscore"]
    # T1 R1/R2
    drep = []
    for (pid, ex, hand), g in amp[amp.timepoint == 1].groupby(["participant", "exercise_id", "hand"]):
        r1, r2 = g[g.repetition == 1], g[g.repetition == 2]
        if len(r1) and len(r2):
            drep.append(abs(float(r1.iloc[0]["DET"]) - float(r2.iloc[0]["DET"])))
    med_drep = float(np.median(drep)) if drep else None
    med_drop = float(amp["DET_drop_full"].median())
    med_corr_a1 = float(amp["corr_vs_A1_arm"].median())
    # longitudinal D12/D13 ratios on z-score
    long_hits = []
    for (pid, ex, hand), g in zsc.groupby(["participant", "exercise_id", "hand"]):
        for name, ta, tb in (("D12", 1, 2), ("D13", 1, 3)):
            ratios = []
            for rep in (1, 2):
                a = g[(g.timepoint == ta) & (g.repetition == rep)]
                b = g[(g.timepoint == tb) & (g.repetition == rep)]
                if a.empty or b.empty or med_drep is None or med_drep < 1e-12:
                    continue
                ratios.append(abs(float(b.iloc[0]["DET"]) - float(a.iloc[0]["DET"])) / med_drep)
            if ratios and float(np.median(ratios)) > 1.0:
                long_hits.append({"pid": pid, "ex": ex, "hand": hand, "delta": name, "median_ratio": float(np.median(ratios))})

    # classification
    if med_drop is None or med_drop < 0.3:
        cls = "UNSTABLE"
        reason = "Weak full-shuffle DET disruption under B2-specific params"
    elif med_drep is not None and med_drep > 0.15 and not long_hits:
        cls = "UNSTABLE"
        reason = "High T1 R1/R2 DET variability without clear longitudinal exceedance"
    elif med_corr_a1 is not None and med_corr_a1 > 0.7 and not long_hits:
        cls = "REDUNDANT"
        reason = "Strongly tracks A1 arm angular speed without independent longitudinal signal"
    elif long_hits and med_corr_a1 is not None and med_corr_a1 < 0.5:
        cls = "SECONDARY_COMPLEMENTARY_SUPPORTED"
        reason = "Distinct from A1 (moderate corr) with some z-score longitudinal exceedances"
    elif med_corr_a1 is not None and 0.15 < med_corr_a1 < 0.5 and med_drop >= 0.5:
        cls = "SECONDARY_COMPLEMENTARY_SUPPORTED"
        reason = "Construct-distinct root-relative endpoint speed with surrogate-supported structure; limited longitudinal novelty"
    else:
        cls = "NOT_INTERPRETABLE"
        reason = "Mixed/weak evidence; do not promote"

    # tighten: Stage 2 A1 already LIMITED_PASS_STOP — B2 cannot rescue; prefer conservative
    if cls == "SECONDARY_COMPLEMENTARY_SUPPORTED" and not long_hits:
        # keep as supported complementary construct for optional later use, not Stage 3 driver
        pass

    summary = {
        "classification": cls,
        "reason": reason,
        "median_corr_vs_A1_arm": med_corr_a1,
        "median_DET_drop_full_shuffle": med_drop,
        "median_T1_R1R2_absdiff_DET": med_drep,
        "zscore_longitudinal_hits": long_hits,
        "lock": lock,
        "cannot_rescue_A1_gate": True,
        "promote_to_primary": False,
    }
    (OUT / "b2_classification.json").write_text(json.dumps(summary, indent=2))
    return summary


def write_report(summary: dict, lock: dict) -> None:
    hits = summary["zscore_longitudinal_hits"]
    lines = [
        "# Stage 2 B2 secondary analysis",
        "",
        f"**Classification:** `{summary['classification']}`",
        "",
        "B2 = pelvis/root-relative hand positional-speed magnitude (m/s).",
        "Not part of the primary Stage 2 gate; cannot rescue a failed/limited A1 result.",
        "",
        "## Scope",
        "",
        "- Participants: 651, 790",
        "- Exercises: ex11, ex13",
        "- Channels: LHand / RHand root-relative speed",
        "- T1-only parameter selection, then limited longitudinal sensitivity",
        "",
        "## B2-specific parameters (T1-selected)",
        "",
        f"| Param | Value |",
        f"|---|---|",
        f"| rate | {lock['primary_rate_hz']} Hz |",
        f"| τ | {lock['tau_frames']} frames ({lock['tau_seconds']:.4f} s) |",
        f"| m | {lock['m']} |",
        f"| radius frac (mean) | {lock['radius_frac_mean']} |",
        f"| Theiler | {lock['theiler']} |",
        f"| block shuffle | {lock['block_shuffle_seconds']} s |",
        "",
        "These are **not** the A1 Stage 1 locks.",
        "",
        "## Empirical observations",
        "",
        f"- Median corr(B2 hand, A1 ipsilateral arm angular): **{summary['median_corr_vs_A1_arm']:.3f}**",
        f"- Median full-shuffle DET drop: **{summary['median_DET_drop_full_shuffle']:.3f}**",
        f"- Median T1 R1/R2 |ΔDET|: **{summary['median_T1_R1R2_absdiff_DET']}**",
        f"- Z-score longitudinal hits (|Δ|/Drep>1 descriptive): {len(hits)}",
        "",
    ]
    if hits:
        lines += ["| pid | ex | hand | delta | median ratio |", "|---|---|---|---|---|"]
        for h in hits:
            lines.append(f"| {h['pid']} | {h['ex']} | {h['hand']} | {h['delta']} | {h['median_ratio']:.2f} |")
        lines.append("")
    lines += [
        "## Interpretation",
        "",
        summary["reason"],
        "",
        "Root-relative endpoint speed measures articulated displacement relative to the pelvis,",
        "not regional joint-orientation-change intensity. Moderate correlation with A1 supports",
        "a distinct construct without replacing A1.",
        "",
        "## Comparison notes",
        "",
        "- Compared against ipsilateral A1 arm angular speed (correlation).",
        "- Surrogate disruption assessed under B2 params.",
        "- Amplitude: amp-preserving + trial z-score (target-RR) both computed.",
        "- Does not use PCA components as RQA input.",
        "",
        "## Gate interaction",
        "",
        "- `cannot_rescue_A1_gate`: true",
        "- `promote_to_primary`: false",
        "- Primary Stage 2 decision remains driven by A1 Auto-RQA.",
        "",
        "## Limitations",
        "",
        "- Bone positions require Length Units handling (T1 mm; 252_T3 meters not in this scope).",
        "- No Procrustes / body-size normalization beyond root-centering.",
        "- Small Stage 2 N; session–timepoint confounding remains.",
        "",
        f"Artifacts: `outputs/stage2/b2/`",
    ]
    rqa_path("reports", "STAGE2_B2_SECONDARY_ANALYSIS.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_rqa_dirs()
    segs = build_segment_index(EXES)
    segs = segs[segs.participant.isin(PIDS)]
    print("B2 T1 diagnostics...", flush=True)
    lock = t1_diagnostics(segs)
    if not lock.get("t1_pass"):
        summary = {
            "classification": "UNSTABLE",
            "reason": "T1 diagnostics failed to yield usable AMI/rate settings",
            "median_corr_vs_A1_arm": None,
            "median_DET_drop_full_shuffle": None,
            "median_T1_R1R2_absdiff_DET": None,
            "zscore_longitudinal_hits": [],
            "lock": lock,
            "cannot_rescue_A1_gate": True,
            "promote_to_primary": False,
        }
        (OUT / "b2_classification.json").write_text(json.dumps(summary, indent=2))
        write_report(summary, lock)
        print(json.dumps(summary, indent=2))
        return
    print("B2 metrics (T1–T3)...", flush=True)
    df = run_metrics(segs, lock)
    summary = classify(df, lock)
    write_report(summary, lock)
    print(json.dumps({k: summary[k] for k in summary if k != "lock"}, indent=2))


if __name__ == "__main__":
    main()
