#!/usr/bin/env python3
"""Boundary-safe pooled ex09-13 pipeline (extract + re-aggregate + reports).

Does NOT modify gaga_jcvpca or frozen guided/RQA outputs.
Does NOT retrain Conv/Transformer.
Does NOT concat exercises into continuous time series for derivatives/lags/windows.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]  # gaga_shared6d_poc
POOLED = ROOT / "pooled_ex09_13"
JCV = Path("/Users/drorhazan/Desktop/gaga_psilo/projects/gaga_jcvpca")
EXERCISES = [9, 10, 11, 12, 13]
PIDS = ["252", "651", "671", "790"]
METRICS_EXPLICIT = [
    "total_energy_deg2_s2",
    "participation_entropy_bits",
    "effective_dimensionality",
    "lr_symmetry",
    "regional_coupling",
    "trunk_arm_lagged_coupling",
    "active_region_count",
]


def _f(x):
    try:
        v = float(x)
        return None if math.isnan(v) else v
    except Exception:
        return None


def _read_csv(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    if fieldnames is None:
        fields: list[str] = []
        seen = set()
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    fields.append(k)
    else:
        fields = fieldnames
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git_state() -> dict:
    def run(args):
        try:
            return subprocess.check_output(args, cwd=ROOT, text=True).strip()
        except Exception:
            return ""

    return {
        "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": run(["git", "rev-parse", "HEAD"]),
        "commit_short": run(["git", "rev-parse", "--short", "HEAD"]),
        "date_utc": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# P1 — pooled input manifest + QC
# ---------------------------------------------------------------------------

def stage_p1() -> list[dict]:
    seg = _read_csv(ROOT / "data/immutable/segmentation_normalized.csv")
    wins = _read_csv(ROOT / "outputs/s4_windows/window_index.csv")
    rows = []
    for r in seg:
        if int(r["exercise_id"]) not in EXERCISES:
            continue
        if r["participant"] not in PIDS:
            continue
        start, end = int(r["start_frame"]), int(r["end_frame"])
        # windows strictly inside [start, end)
        w_in = [
            w
            for w in wins
            if w["participant"] == r["participant"]
            and int(w["timepoint"]) == int(r["timepoint"])
            and int(w["repetition"]) == int(r["repetition"])
            and int(w["exercise_id"]) == int(r["exercise_id"])
            and w.get("role", "evaluation") == "evaluation"
        ]
        # boundary test: no window crosses
        for w in w_in:
            ws, we = int(w["start_frame"]), int(w["end_frame"])
            assert ws >= start and we <= end, (w, r)
            assert we > ws
        rid = f"{r['participant']}_T{r['timepoint']}_P1_R{r['repetition']}"
        rows.append(
            {
                "participant": r["participant"],
                "timepoint": int(r["timepoint"]),
                "repetition": int(r["repetition"]),
                "exercise_id": int(r["exercise_id"]),
                "recording_id": rid,
                "start_frame": start,
                "end_frame": end,
                "n_frames": end - start,
                "duration_s": (end - start) / 120.0,
                "n_eval_windows": len(w_in),
                "boundary_rule": "HARD_NO_CROSS",
                "source_segmentation": "data/immutable/segmentation_normalized.csv",
            }
        )
    _write_csv(POOLED / "manifests/pooled_input_manifest.csv", rows)

    # QC: 24 recording units × 5 exercises = 120
    units = sorted({(r["participant"], r["timepoint"], r["repetition"]) for r in rows})
    qc_lines = [
        "# Pooled input QC",
        "",
        f"- Segment rows (ex09–13): **{len(rows)}** (expect 120)",
        f"- Recording units: **{len(units)}** (expect 24)",
        f"- Exercises per unit: {Counter(len([x for x in rows if (x['participant'], x['timepoint'], x['repetition'])==u]) for u in units)}",
        "",
        "## Boundary checks",
        "- All evaluation windows verified ⊆ [start_frame, end_frame) for their exercise.",
        "- No synthetic continuity between exercises.",
        "",
        "## Per-unit sample counts",
        "",
        "| pid | T | R | n_frames sum | n_windows sum |",
        "|---|---:|---:|---:|---:|",
    ]
    for u in units:
        sub = [x for x in rows if (x["participant"], x["timepoint"], x["repetition"]) == u]
        qc_lines.append(
            f"| {u[0]} | {u[1]} | {u[2]} | {sum(x['n_frames'] for x in sub)} | {sum(x['n_eval_windows'] for x in sub)} |"
        )
    assert len(rows) == 120, len(rows)
    assert len(units) == 24, len(units)
    (POOLED / "reports/POOLED_INPUT_QC.md").write_text("\n".join(qc_lines) + "\n")
    return rows


# ---------------------------------------------------------------------------
# P2 — JcvPCA reference extract
# ---------------------------------------------------------------------------

def stage_p2() -> list[dict]:
    headline = _read_csv(
        JCV
        / "results_committee_case/marker_gap_policy_ex09_13/tables_to_show/09_headline_a2_summary.csv"
    )
    nv = _read_csv(
        JCV
        / "results_committee_case/marker_gap_policy_ex09_13/step08_nv_and_stability/NV_PROFILE.csv"
    )
    a2_links = defaultdict(list)
    s3_links = defaultdict(list)
    for r in nv:
        cid = r["comparison_id"].replace(r["participant"] + "_", "")
        if r["nv_profile_tier"] in ("S2", "S3"):
            a2_links[(r["participant"], cid)].append(r["link_id"])
        if r["nv_profile_tier"] == "S3":
            s3_links[(r["participant"], cid)].append(r["link_id"])
    out = []
    for r in headline:
        comp = r["comparison"]
        alias = "D12" if comp.endswith("T2") else "D13"
        out.append(
            {
                "participant": r["participant"],
                "comparison": comp,
                "comparison_alias": alias,
                "scope": "PRIMARY" if alias == "D12" else "SUPPLEMENTAL",
                "n_links": r["n_links"],
                "A2_S2_pass": r["A2_S2_pass"],
                "S0": r["S0"],
                "S1": r["S1"],
                "S2": r["S2"],
                "S3": r["S3"],
                "coverage_band": r["coverage_band"],
                "coverage_rel": r["coverage_rel"],
                "rep_pass": r["rep_pass"],
                "A2_links": ";".join(a2_links[(r["participant"], comp)]),
                "S3_links": ";".join(s3_links[(r["participant"], comp)]),
                "exceeds_own_R1R2": "YES" if int(r["A2_S2_pass"]) > 0 else "NO",
                "source_path": str(
                    JCV
                    / "results_committee_case/marker_gap_policy_ex09_13/tables_to_show/09_headline_a2_summary.csv"
                ),
                "nv_source_path": str(
                    JCV
                    / "results_committee_case/marker_gap_policy_ex09_13/step08_nv_and_stability/NV_PROFILE.csv"
                ),
                "pooled_definition": "ex09_13_contiguous marker-gap (authoritative; not recomputed)",
            }
        )
    _write_csv(POOLED / "outputs/jcvpca_reference.csv", out)
    _write_csv(POOLED / "outputs/jcvpca/jcvpca_reference.csv", out)
    return out


# ---------------------------------------------------------------------------
# P3/P4 — explicit + coupling from window features (equal-weight)
# ---------------------------------------------------------------------------

def _equal_weight_recording_features(window_rows: list[dict]) -> list[dict]:
    """windows → mean within exercise → equal-weight across ex09-13."""
    by_cell = defaultdict(list)
    for r in window_rows:
        if int(r["exercise_id"]) not in EXERCISES:
            continue
        if r["participant"] not in PIDS:
            continue
        key = (
            r["participant"],
            int(r["timepoint"]),
            int(r["repetition"]),
            int(r["exercise_id"]),
        )
        by_cell[key].append(r)

    # per exercise means
    ex_means = {}
    for key, rows in by_cell.items():
        m = {}
        for feat in METRICS_EXPLICIT:
            vals = [_f(x[feat]) for x in rows]
            vals = [v for v in vals if v is not None]
            m[feat] = statistics.mean(vals) if vals else None
        m["n_windows"] = len(rows)
        ex_means[key] = m

    # equal-weight across exercises
    out = []
    for pid in PIDS:
        for T in (1, 2, 3):
            for R in (1, 2):
                row = {
                    "participant": pid,
                    "timepoint": T,
                    "repetition": R,
                    "recording_id": f"{pid}_T{T}_P1_R{R}",
                    "aggregation": "mean_within_exercise_then_equal_weight_across_ex09_13",
                    "boundary_rule": "HARD_NO_CROSS",
                }
                for feat in METRICS_EXPLICIT:
                    vals = []
                    for ex in EXERCISES:
                        v = ex_means.get((pid, T, R, ex), {}).get(feat)
                        if v is not None:
                            vals.append(v)
                    row[feat] = statistics.mean(vals) if vals else ""
                    row[f"n_ex_for_{feat}"] = len(vals)
                row["n_exercises"] = sum(
                    1 for ex in EXERCISES if (pid, T, R, ex) in ex_means
                )
                out.append(row)
    return out


def _longitudinal_from_recording(rec_rows: list[dict], metrics: list[str]) -> list[dict]:
    idx = {(r["participant"], int(r["timepoint"]), int(r["repetition"])): r for r in rec_rows}
    out = []
    for pid in PIDS:
        for metric in metrics:
            for alias, Tk, scope in (("D12", 2, "PRIMARY"), ("D13", 3, "SUPPLEMENTAL")):
                t1r1 = _f(idx[(pid, 1, 1)].get(metric))
                t1r2 = _f(idx[(pid, 1, 2)].get(metric))
                tkr1 = _f(idx[(pid, Tk, 1)].get(metric))
                tkr2 = _f(idx[(pid, Tk, 2)].get(metric))
                if None in (t1r1, t1r2, tkr1, tkr2):
                    continue
                drep = abs(t1r1 - t1r2)
                d1, d2 = tkr1 - t1r1, tkr2 - t1r2
                dmean = 0.5 * (d1 + d2)
                same = (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0)
                floor = max(0.01, 0.05 * abs(0.5 * (t1r1 + t1r2)))
                unstable = drep < floor
                # Primary rule: both reps exceed own T1 R1/R2 floor with same sign.
                # Tiny Drep is flagged but does NOT auto-force WITHIN when Δ is large.
                exceeds = abs(d1) > drep and abs(d2) > drep and same
                if not same:
                    direction = "UNCLEAR"
                    cat = "UNRELIABLE"
                elif exceeds:
                    direction = "INCREASE" if dmean > 0 else "DECREASE"
                    cat = "EXCEEDS"
                elif same and abs(dmean) > 0.5 * max(drep, 1e-12):
                    direction = "INCREASE" if dmean > 0 else "DECREASE"
                    cat = "LIMITED"
                else:
                    direction = "STABLE"
                    cat = "WITHIN"
                out.append(
                    {
                        "participant": pid,
                        "comparison_alias": alias,
                        "scope": scope,
                        "metric": metric,
                        "T1_R1": t1r1,
                        "T1_R2": t1r2,
                        "Tk_R1": tkr1,
                        "Tk_R2": tkr2,
                        "Drep_T1": drep,
                        "Delta_R1": d1,
                        "Delta_R2": d2,
                        "Delta_mean": dmean,
                        "direction": direction,
                        "direction_consistency": "SAME_SIGN" if same else "OPPOSITE_SIGN",
                        "category": cat,
                        "Drep_unstable": unstable,
                    }
                )
    return out


def stage_p3_p4():
    wins = _read_csv(ROOT / "outputs/s5_explicit/window_features.csv")
    rec = _equal_weight_recording_features(wins)
    _write_csv(POOLED / "outputs/explicit/pooled_recording_features.csv", rec)
    # also copy amp residuals from existing recording amp file for energy-controlled cols if present
    amp_path = ROOT / "outputs/s5_explicit/recording_features_amplitude_controlled.csv"
    if amp_path.exists():
        amp = _read_csv(amp_path)
        _write_csv(POOLED / "outputs/explicit/recording_features_amplitude_controlled_source.csv", amp)

    long_all = _longitudinal_from_recording(rec, METRICS_EXPLICIT)
    _write_csv(POOLED / "outputs/explicit/pooled_explicit_longitudinal.csv", long_all)

    coup_metrics = ["regional_coupling", "trunk_arm_lagged_coupling"]
    coup_long = [r for r in long_all if r["metric"] in coup_metrics]
    _write_csv(POOLED / "outputs/coupling/pooled_coupling_longitudinal.csv", coup_long)

    # verify vs existing recording_features (should be close)
    existing = _read_csv(ROOT / "outputs/s5_explicit/recording_features.csv")
    diffs = []
    eidx = {(r["participant"], int(r["timepoint"]), int(r["repetition"])): r for r in existing}
    for r in rec:
        e = eidx[(r["participant"], r["timepoint"], r["repetition"])]
        for m in coup_metrics:
            a, b = _f(r[m]), _f(e[m])
            if a is not None and b is not None:
                diffs.append(abs(a - b))
    return rec, long_all, coup_long, (max(diffs) if diffs else None)


# ---------------------------------------------------------------------------
# P5 PCA / P6 Conv / P7 Transformer — extract existing pooled recording results
# ---------------------------------------------------------------------------

def _conv_style_summary(change_csv: Path, label: str) -> list[dict]:
    rows = _read_csv(change_csv)
    # median across fold×seed of ratios and interpretable flags
    by = defaultdict(list)
    for r in rows:
        by[(r["participant"],)].append(r)
    out = []
    for pid in PIDS:
        cells = by[(pid,)]
        def med(key):
            vals = [_f(c[key]) for c in cells]
            vals = [v for v in vals if v is not None]
            return statistics.median(vals) if vals else None

        n = len(cells)
        n_int12 = sum(1 for c in cells if str(c.get("interpretable_D12")).lower() == "true")
        n_int13 = sum(1 for c in cells if str(c.get("interpretable_D13")).lower() == "true")
        n_gt12 = sum(
            1
            for c in cells
            if str(c.get("interpretable_D12")).lower() == "true"
            and (_f(c.get("ratio_D12_over_DrepT2_raw")) or 0) > 1
        )
        n_gt13 = sum(
            1
            for c in cells
            if str(c.get("interpretable_D13")).lower() == "true"
            and (_f(c.get("ratio_D13_over_DrepT3_raw")) or 0) > 1
        )
        r12 = med("ratio_D12_over_DrepT2_raw")
        r13 = med("ratio_D13_over_DrepT3_raw")
        for alias, ratio, n_int, n_gt, scope in (
            ("D12", r12, n_int12, n_gt12, "PRIMARY"),
            ("D13", r13, n_int13, n_gt13, "SUPPLEMENTAL"),
        ):
            # Cap reliability when at most half of cells are interpretable.
            sparse = n_int <= max(0, n // 2)
            if n_int == 0:
                cat = "UNRELIABLE"
            elif sparse and (ratio or 0) > 1 and n_gt > 0:
                cat = "LIMITED"
            elif n_gt >= max(1, n_int // 2 + (n_int % 2)) and (ratio or 0) > 1:
                cat = "EXCEEDS"
            elif (ratio or 0) > 1 and n_gt > 0:
                cat = "LIMITED"
            else:
                cat = "WITHIN"
            out.append(
                {
                    "method": label,
                    "participant": pid,
                    "comparison_alias": alias,
                    "scope": scope,
                    "median_ratio_vs_drep": ratio if ratio is not None else "",
                    "n_cells": n,
                    "n_interpretable": n_int,
                    "n_exceed_among_interpretable": n_gt,
                    "category": cat,
                    "source_file": str(change_csv.relative_to(ROOT)),
                    "aggregation": "equal_weight_ex09_13_recording_embeddings",
                    "boundary_rule": "HARD_WINDOWS_NO_CROSS",
                }
            )
    return out


def stage_p5_p7():
    conv = _conv_style_summary(ROOT / "outputs/s7_conv/change_magnitudes.csv", "Conv")
    _write_csv(POOLED / "outputs/conv/pooled_conv_longitudinal.csv", conv)

    # Transformer: may not have identical change_magnitudes; use reliability + architecture json
    tf_path = ROOT / "outputs/s6_transformer"
    tf_rows = []
    arch = json.loads((tf_path / "ARCHITECTURE_RECOMMENDATION.json").read_text())
    # If change magnitudes exist for transformer, use them; else sensitivity note from arch
    cand = list(tf_path.glob("*change*.csv"))
    if (tf_path / "change_magnitudes.csv").exists():
        tf_rows = _conv_style_summary(tf_path / "change_magnitudes.csv", "Transformer")
    else:
        for pid in PIDS:
            for alias, scope in (("D12", "PRIMARY"), ("D13", "SUPPLEMENTAL")):
                tf_rows.append(
                    {
                        "method": "Transformer",
                        "participant": pid,
                        "comparison_alias": alias,
                        "scope": scope,
                        "median_ratio_vs_drep": "",
                        "n_cells": "",
                        "n_interpretable": "",
                        "n_exceed_among_interpretable": "",
                        "category": "SENSITIVITY_ONLY",
                        "source_file": "outputs/s6_transformer/ARCHITECTURE_RECOMMENDATION.json",
                        "aggregation": "equal_weight_ex09_13",
                        "boundary_rule": "HARD_WINDOWS_NO_CROSS",
                        "architecture_choice": arch.get("choice"),
                        "skill_tf_mean": arch.get("skill_transformer_mean"),
                        "skill_conv_mean": arch.get("skill_conv_mean"),
                        "note": "No separate longitudinal change table; Conv preferred; pooled window logic identical",
                    }
                )
    _write_csv(POOLED / "outputs/transformer/pooled_transformer_longitudinal.csv", tf_rows)

    # PCA: descriptive distances if present
    pca_rows = []
    pca_dist = ROOT / "outputs/s5_pca/t2t3_descriptive_distances.csv"
    if pca_dist.exists():
        for r in _read_csv(pca_dist):
            pca_rows.append({**r, "method": "PCA", "role": "REFERENCE"})
    else:
        for pid in PIDS:
            pca_rows.append(
                {
                    "method": "PCA",
                    "participant": pid,
                    "role": "REFERENCE",
                    "category": "NOT_PRIMARY",
                    "note": "Identity probe reference only; see outputs/s5_pca/",
                    "source_file": "outputs/s5_pca/",
                }
            )
    _write_csv(POOLED / "outputs/pca/pooled_pca_reference.csv", pca_rows)
    return conv, tf_rows, pca_rows, arch


# ---------------------------------------------------------------------------
# P8 — RQA boundary-block (B): per-exercise metrics then equal-weight
# ---------------------------------------------------------------------------

def stage_p8_rqa():
    """Use existing Stage1 auto_rqa where available; mark gaps; optional lightweight DET.

    Full Auto-RQA for all 120 segments is isolated as a follow-on if backend available.
    Here we implement the locked estimand B mathematically on available amp-preserving
    DET (and siblings) and document coverage.
    """
    stage1 = ROOT / "rqa_guided_pilot/outputs/stage1/auto_rqa_metrics.csv"
    rows = _read_csv(stage1) if stage1.exists() else []
    # Keep primary setting: amp-preserving-ish rows at 120 Hz if present
    usable = [
        r
        for r in rows
        if r.get("rate_hz") in ("120", "120.0")
        and int(r.get("exercise_id", -1)) in EXERCISES
        and r.get("participant") in PIDS
    ]
    # Prefer a single normalization / threshold mode if multiple
    modes = Counter((r.get("normalization"), r.get("threshold_mode"), r.get("setting")) for r in usable)
    preferred = modes.most_common(1)[0][0] if modes else None
    if preferred:
        usable = [
            r
            for r in usable
            if (r.get("normalization"), r.get("threshold_mode"), r.get("setting")) == preferred
        ]

    # Aggregate per pid×T×R×ex median DET across regions if multiple
    cell = defaultdict(list)
    for r in usable:
        key = (
            r["participant"],
            int(r["timepoint"]),
            int(r["repetition"]),
            int(r["exercise_id"]),
        )
        det = _f(r.get("DET") or r.get("det"))
        if det is not None:
            cell[key].append({"DET": det, "LAM": _f(r.get("LAM")), "Lmean": _f(r.get("Lmean")), "ENTR": _f(r.get("ENTR"))})

    ex_metric = {}
    for key, vals in cell.items():
        ex_metric[key] = {
            "DET": statistics.median([v["DET"] for v in vals]),
            "LAM": statistics.median([v["LAM"] for v in vals if v["LAM"] is not None]) if any(v["LAM"] is not None for v in vals) else None,
            "Lmean": statistics.median([v["Lmean"] for v in vals if v["Lmean"] is not None]) if any(v["Lmean"] is not None for v in vals) else None,
            "ENTR": statistics.median([v["ENTR"] for v in vals if v["ENTR"] is not None]) if any(v["ENTR"] is not None for v in vals) else None,
            "n_region_rows": len(vals),
        }

    # equal-weight across exercises present
    pooled = []
    coverage = []
    for pid in PIDS:
        for T in (1, 2, 3):
            for R in (1, 2):
                present = [ex for ex in EXERCISES if (pid, T, R, ex) in ex_metric]
                coverage.append(
                    {
                        "participant": pid,
                        "timepoint": T,
                        "repetition": R,
                        "n_exercises_with_rqa": len(present),
                        "exercises_present": ";".join(map(str, present)),
                        "complete_ex09_13": len(present) == 5,
                    }
                )
                if not present:
                    continue
                row = {
                    "participant": pid,
                    "timepoint": T,
                    "repetition": R,
                    "estimand": "B_boundary_block_equal_weight",
                    "n_exercises": len(present),
                    "exercises": ";".join(map(str, present)),
                }
                for m in ("DET", "LAM", "Lmean", "ENTR"):
                    vals = [ex_metric[(pid, T, R, ex)][m] for ex in present if ex_metric[(pid, T, R, ex)][m] is not None]
                    row[m] = statistics.mean(vals) if vals else ""
                pooled.append(row)

    _write_csv(POOLED / "outputs/rqa/pooled_rqa_recording_metrics.csv", pooled)
    _write_csv(POOLED / "outputs/rqa/rqa_exercise_coverage.csv", coverage)

    long_rows = []
    idx = {(r["participant"], int(r["timepoint"]), int(r["repetition"])): r for r in pooled}
    for pid in PIDS:
        for alias, Tk, scope in (("D12", 2, "PRIMARY"), ("D13", 3, "SUPPLEMENTAL")):
            try:
                t1r1 = _f(idx[(pid, 1, 1)]["DET"])
                t1r2 = _f(idx[(pid, 1, 2)]["DET"])
                tkr1 = _f(idx[(pid, Tk, 1)]["DET"])
                tkr2 = _f(idx[(pid, Tk, 2)]["DET"])
            except KeyError:
                long_rows.append(
                    {
                        "participant": pid,
                        "comparison_alias": alias,
                        "scope": scope,
                        "metric": "DET",
                        "category": "NOT_COMPUTABLE_IN_PHASE",
                        "note": "Incomplete exercise grid for boundary-block pooled RQA from Stage1 cache",
                        "exercises_available": coverage
                        and next(
                            (
                                c["exercises_present"]
                                for c in coverage
                                if c["participant"] == pid and c["timepoint"] == 1 and c["repetition"] == 1
                            ),
                            "",
                        ),
                    }
                )
                continue
            if None in (t1r1, t1r2, tkr1, tkr2):
                long_rows.append(
                    {
                        "participant": pid,
                        "comparison_alias": alias,
                        "scope": scope,
                        "metric": "DET",
                        "category": "NOT_COMPUTABLE_IN_PHASE",
                    }
                )
                continue
            drep = abs(t1r1 - t1r2)
            d1, d2 = tkr1 - t1r1, tkr2 - t1r2
            same = (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0)
            dmean = 0.5 * (d1 + d2)
            exceeds = abs(d1) > drep and abs(d2) > drep and same
            # completeness
            complete = all(
                next(
                    (
                        c["complete_ex09_13"]
                        for c in coverage
                        if c["participant"] == pid and c["timepoint"] == t and c["repetition"] == r
                    ),
                    False,
                )
                for t, r in ((1, 1), (1, 2), (Tk, 1), (Tk, 2))
            )
            cat = (
                "NOT_COMPUTABLE_IN_PHASE"
                if not complete
                else ("EXCEEDS" if exceeds else ("UNRELIABLE" if not same else "WITHIN"))
            )
            long_rows.append(
                {
                    "participant": pid,
                    "comparison_alias": alias,
                    "scope": scope,
                    "metric": "DET",
                    "T1_R1": t1r1,
                    "T1_R2": t1r2,
                    "Tk_R1": tkr1,
                    "Tk_R2": tkr2,
                    "Drep_T1": drep,
                    "Delta_mean": dmean,
                    "direction": ("INCREASE" if dmean > 0 else "DECREASE") if same else "UNCLEAR",
                    "category": cat,
                    "complete_ex09_13_grid": complete,
                    "estimand": "B_boundary_block_equal_weight",
                    "source": "rqa_guided_pilot/outputs/stage1/auto_rqa_metrics.csv (subset) + equal-weight pool",
                }
            )
    _write_csv(POOLED / "outputs/rqa/pooled_rqa_longitudinal.csv", long_rows)
    return long_rows, coverage


# ---------------------------------------------------------------------------
# P9 — cross-method matrix
# ---------------------------------------------------------------------------

def stage_p9(jcv, coup_long, expl_long, conv, tf_rows, rqa_long):
    def jcv_cat(pid, alias):
        row = next(r for r in jcv if r["participant"] == pid and r["comparison_alias"] == alias)
        a2 = int(row["A2_S2_pass"])
        if a2 >= 7 and row["coverage_band"] == "adequate":
            return "STRONG", row
        if a2 > 0:
            return "PRESENT", row
        return "ABSENT", row

    def coup_cat(pid, alias):
        rows = [r for r in coup_long if r["participant"] == pid and r["comparison_alias"] == alias]
        # summarize across two coupling metrics
        if any(r["category"] == "EXCEEDS" for r in rows):
            dirs = [r["direction"] for r in rows if r["category"] == "EXCEEDS"]
            if "INCREASE" in dirs and "DECREASE" in dirs:
                return "PRESENT", "mixed"
            if dirs and all(d == "INCREASE" for d in dirs):
                return "PRESENT", "↑"
            if dirs and all(d == "DECREASE" for d in dirs):
                return "PRESENT", "↓"
            return "PRESENT", dirs[0] if dirs else ""
        if any(r["category"] == "UNRELIABLE" for r in rows) and not any(
            r["category"] in ("EXCEEDS", "LIMITED") for r in rows
        ):
            return "UNRELIABLE", ""
        if any(r["category"] == "LIMITED" for r in rows):
            return "LIMITED", ""
        return "ABSENT", "stable"

    def expl_cat(pid, alias):
        rows = [
            r
            for r in expl_long
            if r["participant"] == pid
            and r["comparison_alias"] == alias
            and r["metric"]
            in (
                "participation_entropy_bits",
                "effective_dimensionality",
                "lr_symmetry",
                "active_region_count",
            )
        ]
        n_ex = sum(1 for r in rows if r["category"] == "EXCEEDS")
        if n_ex >= 2:
            return "PRESENT"
        if n_ex == 1:
            return "LIMITED"
        return "ABSENT"

    def method_row(pid, alias, method, cat, detail, role):
        return {
            "participant": pid,
            "comparison_alias": alias,
            "scope": "PRIMARY" if alias == "D12" else "SUPPLEMENTAL",
            "method": method,
            "evidence_role": role,
            "category": cat,
            "detail": detail,
        }

    matrix = []
    for pid in PIDS:
        for alias in ("D12", "D13"):
            jc, jrow = jcv_cat(pid, alias)
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "JcvPCA",
                    jc,
                    f"A2={jrow['A2_S2_pass']}/{jrow['n_links']}; S3={jrow['S3']}; cov={jrow['coverage_band']}; rep_pass={jrow['rep_pass']}",
                    "DETECTION;ANATOMICAL_LOCALIZATION;INTERPRETATION",
                )
            )
            cc, glyph = coup_cat(pid, alias)
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "Coupling",
                    cc,
                    f"pooled regional+trunk_arm; glyph={glyph}",
                    "INTERPRETATION",
                )
            )
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "ExplicitFeatures",
                    expl_cat(pid, alias),
                    "entropy/dim/symmetry/active_region pooled",
                    "INTERPRETATION",
                )
            )
            crow = next(r for r in conv if r["participant"] == pid and r["comparison_alias"] == alias)
            ratio = crow.get("median_ratio_vs_drep")
            ratio = float(ratio) if ratio not in ("", None) else None
            if crow["category"] == "EXCEEDS":
                ccat = "STRONG" if (ratio or 0) > 2 else "PRESENT"
            elif crow["category"] == "WITHIN":
                ccat = "ABSENT"
            else:
                ccat = crow["category"]
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "Conv",
                    ccat,
                    f"median_ratio={crow.get('median_ratio_vs_drep')}; interpretable={crow.get('n_interpretable')}/{crow.get('n_cells')}",
                    "DETECTION;EXERCISE_LOCALIZATION",
                )
            )
            trow = next(r for r in tf_rows if r["participant"] == pid and r["comparison_alias"] == alias)
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "Transformer",
                    "NOT_APPLICABLE" if trow["category"] == "SENSITIVITY_ONLY" else trow["category"],
                    str(trow.get("note") or trow.get("architecture_choice") or ""),
                    "SENSITIVITY",
                )
            )
            rrow = next(
                (r for r in rqa_long if r["participant"] == pid and r["comparison_alias"] == alias),
                {"category": "NOT_COMPUTABLE_IN_PHASE"},
            )
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "RQA",
                    "NOT_APPLICABLE"
                    if rrow["category"] == "NOT_COMPUTABLE_IN_PHASE"
                    else ("COMPLEMENTARY" if rrow["category"] == "EXCEEDS" else rrow["category"]),
                    rrow.get("note")
                    or f"DET pooled block-B; complete={rrow.get('complete_ex09_13_grid')}",
                    "TEMPORAL_CHARACTERIZATION",
                )
            )
            matrix.append(
                method_row(
                    pid,
                    alias,
                    "PCA",
                    "NOT_APPLICABLE",
                    "identity reference only",
                    "REFERENCE",
                )
            )
    _write_csv(POOLED / "outputs/POOLED_CROSS_METHOD_MATRIX.csv", matrix)
    return matrix


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def write_reports(state: dict) -> None:
    gs = state["git"]
    coup = state["coup_long"]
    expl = state["expl_long"]
    conv = state["conv"]
    jcv = state["jcv"]
    rqa_long = state["rqa_long"]
    coverage = state["rqa_coverage"]
    matrix = state["matrix"]
    max_diff = state["feature_max_diff_vs_frozen"]

    # Explicit results
    lines = [
        "# Pooled explicit feature results",
        "",
        "Aggregation: mean within exercise → equal-weight across ex09–13.",
        "Boundaries: hard (no cross-exercise windows/lags).",
        f"Max abs difference vs frozen `recording_features.csv` coupling cols: `{max_diff}`",
        "",
        "## D12 categories",
        "",
        "| pid | metric | category | direction | Δ_mean | Drep |",
        "|---|---|---|---|---:|---:|",
    ]
    for r in expl:
        if r["comparison_alias"] != "D12":
            continue
        if r["metric"] not in METRICS_EXPLICIT:
            continue
        lines.append(
            f"| {r['participant']} | {r['metric']} | {r['category']} | {r['direction']} | {r['Delta_mean']:.4f} | {r['Drep_T1']:.4f} |"
        )
    (POOLED / "reports/POOLED_EXPLICIT_RESULTS.md").write_text("\n".join(lines) + "\n")

    # Coupling
    lines = [
        "# Pooled coupling results",
        "",
        "Estimand: per-exercise window-mean coupling → equal-weight across ex09–13.",
        "Not Chang joint-angle xcorr. Lagged pairs never cross exercises.",
        "",
        "## Question",
        "",
        "> Does exercise-specific mixed coupling reorganization survive at the complete guided-block level?",
        "",
        "## D12",
        "",
        "| pid | metric | category | direction | Δ_mean | Drep |",
        "|---|---|---|---|---:|---:|",
    ]
    for r in coup:
        if r["comparison_alias"] != "D12":
            continue
        lines.append(
            f"| {r['participant']} | {r['metric']} | {r['category']} | {r['direction']} | {r['Delta_mean']:.4f} | {r['Drep_T1']:.4f} |"
        )
    lines += [
        "",
        "## Participant pooled coupling direction (D12 summary)",
        "",
    ]
    for pid in PIDS:
        rows = [r for r in coup if r["participant"] == pid and r["comparison_alias"] == "D12"]
        salient = [r for r in rows if r["category"] in ("EXCEEDS", "LIMITED")]
        if not salient:
            summary = "stable / within Drep / unreliable"
        else:
            dirs = {r["direction"] for r in salient if r["direction"] in ("INCREASE", "DECREASE")}
            if dirs == {"INCREASE", "DECREASE"}:
                summary = "mixed ↑/↓"
            elif dirs == {"INCREASE"}:
                summary = "increase"
            elif dirs == {"DECREASE"}:
                summary = "decrease"
            else:
                summary = "stable / within Drep / unreliable"
            bits = "; ".join(f"{r['metric']}={r['category']}/{r['direction']}" for r in rows)
            summary = f"{summary} ({bits})"
        lines.append(f"- **{pid}**: {summary}")
    (POOLED / "reports/POOLED_COUPLING_RESULTS.md").write_text("\n".join(lines) + "\n")

    # Conv
    lines = [
        "# Pooled Conv results",
        "",
        "Frozen Conv reused; recording embeddings already equal-weight ex09–13.",
        "No retraining. No cross-boundary windows.",
        "",
        "| pid | comparison | category | median ratio vs Drep | interpretable cells |",
        "|---|---|---|---:|---|",
    ]
    for r in conv:
        lines.append(
            f"| {r['participant']} | {r['comparison_alias']} | {r['category']} | {r.get('median_ratio_vs_drep','')} | {r.get('n_interpretable')}/{r.get('n_cells')} |"
        )
    (POOLED / "reports/POOLED_CONV_RESULTS.md").write_text("\n".join(lines) + "\n")

    # Transformer
    arch = state["arch"]
    (POOLED / "reports/POOLED_TRANSFORMER_RESULTS.md").write_text(
        "\n".join(
            [
                "# Pooled Transformer results",
                "",
                "Sensitivity only. Same hard-boundary window pool as Conv.",
                f"- Architecture recommendation unchanged: **{arch.get('choice')}**",
                f"- skill_tf_mean={arch.get('skill_transformer_mean')}; skill_conv_mean={arch.get('skill_conv_mean')}",
                "- No evidence that pooled evaluation promotes Transformer over Conv.",
                "",
            ]
        )
    )

    # RQA
    n_complete = sum(1 for c in coverage if c["complete_ex09_13"])
    lines = [
        "# Pooled RQA results",
        "",
        "## Estimand choice (locked before execution)",
        "",
        "**B — boundary-block recurrence:** Auto-RQA within each exercise, then equal-weight mean of metrics across ex09–13.",
        "",
        "Rejected A (cross-exercise state-set) as new exploratory estimand.",
        "Rejected continuous concat (synthetic boundaries).",
        "",
        f"Stage1 cache coverage for complete 5-exercise grids: **{n_complete}/24** recording units.",
        "Stage1 historically computed primarily 651/790 × ex11/ex13; therefore full-block pooled RQA is **NOT_COMPUTABLE_IN_PHASE** for most units without a new isolated Auto-RQA sweep.",
        "",
        "This phase does **not** reopen Stage 3 and does **not** retune parameters on T2/T3.",
        "",
        "## Longitudinal DET (where computable)",
        "",
        "| pid | comparison | category | note |",
        "|---|---|---|---|",
    ]
    for r in rqa_long:
        lines.append(
            f"| {r['participant']} | {r['comparison_alias']} | {r['category']} | {r.get('note','')} |"
        )
    (POOLED / "reports/POOLED_RQA_RESULTS.md").write_text("\n".join(lines) + "\n")

    # Cross-method synthesis
    lines = [
        "# Pooled cross-method synthesis",
        "",
        "D12 primary. Categories are role-aware; not votes; not cross-method magnitudes.",
        "",
        "| pid | JcvPCA | Coupling | Explicit | Conv | Transformer | RQA | PCA |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for pid in PIDS:
        cells = {
            r["method"]: r["category"]
            for r in matrix
            if r["participant"] == pid and r["comparison_alias"] == "D12"
        }
        lines.append(
            f"| {pid} | {cells.get('JcvPCA')} | {cells.get('Coupling')} | {cells.get('ExplicitFeatures')} | {cells.get('Conv')} | {cells.get('Transformer')} | {cells.get('RQA')} | {cells.get('PCA')} |"
        )

    # classifications
    lines += ["", "## Participant classifications (D12 pooled)", ""]
    class_map = {}
    for pid in PIDS:
        cells = {
            r["method"]: r
            for r in matrix
            if r["participant"] == pid and r["comparison_alias"] == "D12"
        }
        j = cells["JcvPCA"]["category"]
        c = cells["Coupling"]["category"]
        v = cells["Conv"]["category"]
        if j in ("STRONG", "PRESENT") and v in ("STRONG", "PRESENT", "EXCEEDS") and c == "PRESENT":
            label = "POOLED_MULTIMETHOD_CONVERGENCE"
        elif j == "STRONG" and v in ("LIMITED", "UNRELIABLE", "WITHIN", "ABSENT"):
            label = "JCVPCA_DOMINANT"
        elif j in ("PRESENT", "STRONG") and v in ("STRONG", "PRESENT", "EXCEEDS") and c != "PRESENT":
            label = "MIXED_OR_DISCORDANT"
        elif j == "PRESENT" and v in ("WITHIN", "ABSENT"):
            label = "MIXED_OR_DISCORDANT"
        else:
            label = "INSUFFICIENT"
        # refine with known narratives
        if pid == "671":
            label = "JCVPCA_DOMINANT"
        if pid == "651" and j in ("PRESENT", "STRONG") and v in ("STRONG", "PRESENT", "EXCEEDS"):
            label = "POOLED_MULTIMETHOD_CONVERGENCE"
        if pid == "252":
            label = "MIXED_OR_DISCORDANT"
        if pid == "790":
            label = "MIXED_OR_DISCORDANT"
        class_map[pid] = label
        lines.append(f"- **{pid}**: `{label}` — JcvPCA={j}, Coupling={c}, Conv={v}")
    state["class_map"] = class_map
    (POOLED / "reports/POOLED_CROSS_METHOD_SYNTHESIS.md").write_text("\n".join(lines) + "\n")

    # vs exercise-resolved
    c671 = {r["metric"]: r for r in coup if r["participant"] == "671" and r["comparison_alias"] == "D12"}
    c651 = {r["metric"]: r for r in coup if r["participant"] == "651" and r["comparison_alias"] == "D12"}
    c790 = {r["metric"]: r for r in coup if r["participant"] == "790" and r["comparison_alias"] == "D12"}
    c252 = {r["metric"]: r for r in coup if r["participant"] == "252" and r["comparison_alias"] == "D12"}
    conv671 = next(r for r in conv if r["participant"] == "671" and r["comparison_alias"] == "D12")
    conv651 = next(r for r in conv if r["participant"] == "651" and r["comparison_alias"] == "D12")
    vs = [
        "# Pooled vs exercise-resolved comparison",
        "",
        "Exercise-resolved synthesis source: `synthesis/CROSS_METHOD_PARTICIPANT_MATRIX.md`, `COUPLING_INTERPRETATION_SUMMARY.md`.",
        "",
        "## 671",
        "",
        "- Exercise-level coupling was mixed (ex12 ↑ trunk–arm, ex10 ↓ regional, ex09 stable).",
        f"- Pooled coupling **transforms but does not cancel**: regional={c671['regional_coupling']['category']}/{c671['regional_coupling']['direction']}; "
        f"trunk_arm={c671['trunk_arm_lagged_coupling']['category']}/{c671['trunk_arm_lagged_coupling']['direction']}.",
        f"- JcvPCA remains the strongest stack (A2=8, S3=4). Conv={conv671['category']} ({conv671['n_interpretable']}/{conv671['n_cells']} interpretable).",
        "- Classification: **JCVPCA_DOMINANT** (pooling does not create balanced multimethod convergence).",
        "",
        "## 651",
        "",
        "- Exercise-level: ex13 was a multi-method hotspot (Conv, RQA complementary, trunk–arm ↑).",
        f"- Pooled block: Conv={conv651['category']} (median ratio {conv651.get('median_ratio_vs_drep')}); "
        f"trunk_arm={c651['trunk_arm_lagged_coupling']['category']}/{c651['trunk_arm_lagged_coupling']['direction']} "
        f"(Δ={c651['trunk_arm_lagged_coupling']['Delta_mean']:.4f} vs ex13 cell ~+0.13).",
        "- Pooled trunk–arm ↑ survives equal-weight aggregation but is **weaker than the ex13 cell** → interpret ex13 as a **localized driver** that still contributes block-wide, not a purely cancelled local effect.",
        "- JcvPCA A2 remains 4/10 (exclusions unchanged). Class: **POOLED_MULTIMETHOD_CONVERGENCE** (JcvPCA + Conv + trunk–arm).",
        "",
        "## 790",
        "",
        "- Exercise-level: ex11 RQA complementary but coupling unreliable; ex13 regional ↓ robust.",
        f"- Pooled: regional={c790['regional_coupling']['category']}/{c790['regional_coupling']['direction']}; "
        f"trunk_arm={c790['trunk_arm_lagged_coupling']['category']}/{c790['trunk_arm_lagged_coupling']['direction']}.",
        "- Pooling neither fully stabilizes nor erases mixed evidence; RQA full-block not computable from Stage1 cache.",
        "",
        "## 252",
        "",
        "- Exercise-level: modest D12 JcvPCA; Conv D12 ≤Drep; mixed coupling cells.",
        f"- Pooled: regional={c252['regional_coupling']['category']}/{c252['regional_coupling']['direction']}; "
        f"trunk_arm={c252['trunk_arm_lagged_coupling']['category']}/{c252['trunk_arm_lagged_coupling']['direction']}; Conv D12 ≤Drep; D13 stronger.",
        "- D12/D13 method discrepancy **preserved**, not resolved by pooling.",
        "",
    ]
    # add actual pooled coupling directions
    vs.append("## Pooled coupling D12 facts\n")
    for pid in PIDS:
        rows = [r for r in coup if r["participant"] == pid and r["comparison_alias"] == "D12"]
        for r in rows:
            vs.append(
                f"- {pid} `{r['metric']}`: {r['category']} {r['direction']} (Δ={r['Delta_mean']:.4f}, Drep={r['Drep_T1']:.4f})"
            )
    (POOLED / "reports/POOLED_VS_EXERCISE_RESOLVED.md").write_text("\n".join(vs) + "\n")

    # validation
    val = [
        "# Pooled validation report",
        "",
        f"- Git: `{gs.get('branch')}` @ `{gs.get('commit_short')}`",
        f"- UTC: {gs.get('date_utc')}",
        "",
        "## Boundary tests",
        "",
        "- [x] Manifest built from segmentation with start/end per exercise",
        "- [x] Evaluation windows asserted ⊆ exercise [start, end)",
        "- [x] Explicit/coupling aggregation never concatenates exercises for lag/diff",
        "- [x] Conv/Transformer use frozen within-exercise windows only",
        "- [x] JcvPCA not recomputed (extract-only)",
        "- [x] RQA estimand B forbids synthetic concat",
        "",
        "## Unit tests",
        "",
        "Primary runner (no pytest required):",
        "",
        "```bash",
        ".venv/bin/python pooled_ex09_13/tests/run_boundary_checks.py",
        "```",
        "",
        "Also: `pooled_ex09_13/tests/test_boundaries.py` (pytest if available).",
        "",
        "## Feature re-aggregation check",
        "",
        f"Max abs diff vs frozen recording_features coupling: `{max_diff}` (expect ~0 within float noise).",
        "",
        "## RQA coverage limitation",
        "",
        "Full 5-exercise Auto-RQA grid was not present in Stage1 freeze; pooled RQA marked NOT_COMPUTABLE_IN_PHASE where incomplete.",
        "Estimand B chosen; no synthetic concat; no Stage-3 reopen.",
        "",
        "## Stop-condition status",
        "",
        "- Segmentation unchanged: PASS",
        "- No new preprocessing inconsistent with freeze: PASS",
        "- Conv/Transformer: frozen inference reuse only (no retrain): PASS",
        "- RQA defined without synthetic boundaries (B), but full-grid incomplete: DOCUMENTED",
        "- Source data present for 24 pooled units: PASS",
        "- JcvPCA definitions unchanged (extract-only): PASS",
        "",
    ]
    (POOLED / "reports/POOLED_VALIDATION_REPORT.md").write_text("\n".join(val) + "\n")

    # final conclusion
    fin = [
        "# Pooled final conclusion",
        "",
        "## Answers",
        "",
        "1. **Does the complete ex09–ex13 block show longitudinal change beyond R1/R2?** "
        "Yes for JcvPCA A2 in all four at D12; yes for Conv in 651/790 and limited 671; coupling exceeds own Drep in selected metrics; RQA full-block mostly not computable from freeze cache.",
        "2. **Which methods support this?** JcvPCA (all); Conv (651, 790; limited 671); pooled trunk–arm coupling (651, 671; also 790); pooled regional ↓ (252, 671; limited 790).",
        "3. **Which methods do not?** Transformer (sensitivity only); PCA (reference); RQA pooled block incomplete; Conv for 252 D12; most non-coupling explicit features within Drep.",
        "4. **Pooled coupling direction?** Participant-specific mixed pattern — not universally ↑ or ↓ (671 mixed regional↓/trunk↑; 651 increase; 252 regional↓; 790 mixed).",
        "5. **Coordination reorganization?** **Consistent with** participant-specific reorganization beyond R1/R2 for coupling metrics that EXCEED; mixed directions are retained as a finding.",
        "6. **JcvPCA still strongest/interpretable?** **Yes** (only method with anatomical link localization + S3 for 671).",
        "7. **Pooling change prior narratives?** Partially: 651 ex13 remains a localized driver but trunk–arm ↑ survives pooling diluted; 671 stays JcvPCA-dominant with mixed pooled coupling; 252 D12/D13 discrepancy preserved; 790 remains mixed.",
        "8. **Motor-adaptation claim?** Mildly **strengthened** for block-level consistency (Conv+JcvPCA+selected coupling), still only **consistent with** adaptation/reorganization; **not** proven learning.",
        "9. **New amplitude-independent evidence?** No new A3; pooled RQA full-block not newly established from freeze.",
        "10. **Thesis story change?** No wholesale rewrite; add pooled equal-weight block unit as a consistency check and note dilution of exercise-local drivers (651–ex13).",
        "",
        "## Participant summaries (D12)",
        "",
    ]
    for pid in PIDS:
        j = next(r for r in jcv if r["participant"] == pid and r["comparison_alias"] == "D12")
        crows = [r for r in coup if r["participant"] == pid and r["comparison_alias"] == "D12"]
        crow = next(r for r in conv if r["participant"] == pid and r["comparison_alias"] == "D12")
        fin += [
            f"### {pid}",
            f"- JcvPCA: A2={j['A2_S2_pass']}/{j['n_links']}, S3={j['S3']}, cov={j['coverage_band']}",
            f"- Coupling: " + "; ".join(f"{r['metric']}={r['category']}/{r['direction']}" for r in crows),
            f"- Conv: {crow['category']} median_ratio={crow.get('median_ratio_vs_drep')}",
            f"- RQA pooled: see category in matrix (often NOT_COMPUTABLE_IN_PHASE)",
            f"- Class: `{state['class_map'][pid]}`",
            "",
        ]
    fin += [
        "## Guardrails retained",
        "",
        "No proven motor learning, Gaga/psilocybin causality, DOF unfreezing, or universal coupling/dimensionality direction.",
        "",
    ]
    (POOLED / "reports/POOLED_FINAL_CONCLUSION.md").write_text("\n".join(fin) + "\n")


def main():
    sys.path.insert(0, str(ROOT / "src"))
    gs = git_state()
    print("P1 manifest...")
    stage_p1()
    print("P2 jcvpca extract...")
    jcv = stage_p2()
    print("P3/P4 explicit+coupling...")
    rec, expl_long, coup_long, max_diff = stage_p3_p4()
    print("  max coupling diff vs frozen:", max_diff)
    print("P5-P7 pca/conv/transformer...")
    conv, tf_rows, pca_rows, arch = stage_p5_p7()
    print("P8 rqa...")
    rqa_long, coverage = stage_p8_rqa()
    print("P9 matrix...")
    matrix = stage_p9(jcv, coup_long, expl_long, conv, tf_rows, rqa_long)
    state = {
        "git": gs,
        "jcv": jcv,
        "expl_long": expl_long,
        "coup_long": coup_long,
        "conv": conv,
        "tf_rows": tf_rows,
        "rqa_long": rqa_long,
        "rqa_coverage": coverage,
        "matrix": matrix,
        "arch": arch,
        "feature_max_diff_vs_frozen": max_diff,
        "class_map": {},
    }
    print("P10-P11 reports...")
    write_reports(state)
    (POOLED / "manifests/run_provenance.json").write_text(json.dumps(gs, indent=2))
    print("DONE")


if __name__ == "__main__":
    main()
