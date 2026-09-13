#!/usr/bin/env python3
"""Stage A0: T1-only representation and data-integrity verification.

Does not compute RQA metrics, distance matrices, thresholds, or recurrence plots.
Does not load T2/T3 rotvec arrays. Timepoint is hard-coded to 1; no CLI override.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import _bootstrap  # noqa: F401
from rqa_pilot.io_readonly import AXES, build_segment_index, load_link_config, load_rotvec
from rqa_pilot.paths import REPO_ROOT, RQA_ROOT, ensure_rqa_dirs, readonly_path, rqa_path

ALLOWED_TIMEPOINT = 1
PI = math.pi


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_wb_cfg() -> dict:
    path = RQA_ROOT / "configs" / "whole_body_rqa.yaml"
    cfg = yaml.safe_load(path.read_text())
    if int(cfg["allowed_timepoint"]) != ALLOWED_TIMEPOINT:
        raise RuntimeError("whole_body_rqa.yaml allowed_timepoint must be 1")
    return cfg


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="A0 T1-only representation verification")
    p.add_argument("--write", action="store_true", default=True, help=argparse.SUPPRESS)
    return p.parse_args()


def assert_t1_recording_id(recording_id: str) -> None:
    if "_T1_" not in str(recording_id):
        raise RuntimeError(f"refusing to load non-T1 recording_id={recording_id!r}")


def longest_true_run(mask: np.ndarray) -> tuple[int, int]:
    """Return (n_runs, longest_run_length) for a 1-D boolean mask."""
    padded = np.concatenate([[False], np.asarray(mask, dtype=bool), [False]])
    edges = np.diff(padded.astype(np.int8))
    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0]
    if starts.size == 0:
        return 0, 0
    lengths = ends - starts
    return int(starts.size), int(lengths.max())


def qc_slice(rv: np.ndarray, fps: float, cfg: dict) -> dict:
    """Per-segment QC. rv is (T, L, 3). No pairwise distances."""
    n_t, n_l, n_ax = rv.shape
    finite_link = np.isfinite(rv).all(axis=2)
    frame_ok = finite_link.all(axis=1)
    n_runs, longest = longest_true_run(frame_ok)
    valid_frac = float(frame_ok.mean()) if n_t else 0.0
    longest_s = longest / fps
    trimmed = bool(longest < n_t)
    angles = np.linalg.norm(rv, axis=2)
    near_cut = float(cfg["validity"]["near_pi_fraction_of_pi"]) * PI
    near_pi_mask = np.isfinite(angles) & (angles > near_cut)
    near_pi_frac = float(near_pi_mask.mean()) if angles.size else 0.0
    amax = float(np.nanmax(angles)) if np.isfinite(angles).any() else float("nan")
    jump_rad = float(cfg["validity"]["jump_fail_rad"])
    if n_t > 1:
        step = np.linalg.norm(np.diff(rv, axis=0), axis=2)
        jump_frac = float(np.nanmean(step > jump_rad))
        step_max = float(np.nanmax(step)) if np.isfinite(step).any() else float("nan")
        step_p99 = float(np.nanpercentile(step, 99)) if np.isfinite(step).any() else float("nan")
    else:
        jump_frac, step_max, step_p99 = float("nan"), float("nan"), float("nan")

    # Plan §8: near-π / jumps are flagged, not dropped. near_pi_fail_frac is the
    # "widespread wrapping" FAIL criterion. Isolated jumps do not fail policy.
    policy_ok = (
        valid_frac >= float(cfg["validity"]["min_valid_frame_fraction"])
        and longest_s >= float(cfg["validity"]["min_duration_s"])
        and longest >= int(cfg["validity"]["min_samples"])
        and near_pi_frac <= float(cfg["validity"]["near_pi_fail_frac"])
    )
    return {
        "n_frames": int(n_t),
        "n_links": int(n_l),
        "n_axes": int(n_ax),
        "duration_s": n_t / fps,
        "nan_frac_values": float(1.0 - np.isfinite(rv).mean()),
        "valid_frame_fraction": valid_frac,
        "n_finite_runs": n_runs,
        "longest_valid_run_frames": longest,
        "longest_valid_run_s": longest_s,
        "trimmed": trimmed,
        "angle_max_rad": amax,
        "near_pi_frac": near_pi_frac,
        "n_near_pi_link_frames": int(near_pi_mask.sum()),
        "jump_frac_step_gt_1rad": jump_frac,
        "step_max_rad": step_max,
        "step_p99_rad": step_p99,
        "policy_ok": bool(policy_ok),
    }


def main() -> int:
    parse_args()
    ensure_rqa_dirs()
    (rqa_path("outputs", "whole_body")).mkdir(parents=True, exist_ok=True)
    (rqa_path("reports", "whole_body")).mkdir(parents=True, exist_ok=True)

    cfg = load_wb_cfg()
    fps = float(cfg["native_fps"])
    yaml_path = readonly_path("canonical_links")
    yaml_cfg = yaml.safe_load(yaml_path.read_text())
    loader_ids, loader_regions = load_link_config()
    yaml_ids = tuple(link["id"] for link in yaml_cfg["links"])
    yaml_regions = {link["id"]: link["region"] for link in yaml_cfg["links"]}
    yaml_region_keys = list(yaml_cfg["regions"].keys())

    exp_path = readonly_path("experiment_config")
    exp = yaml.safe_load(exp_path.read_text())

    issues: list[str] = []
    assumptions: list[str] = []
    fail_reasons: list[str] = []

    if yaml_ids != loader_ids:
        fail_reasons.append("canonical YAML link order disagrees with load_link_config()")
    if yaml_regions != loader_regions:
        fail_reasons.append("canonical YAML per-link regions disagree with load_link_config()")
    if len(yaml_ids) != int(cfg["expected_n_links"]):
        fail_reasons.append(f"expected {cfg['expected_n_links']} links, got {len(yaml_ids)}")
    if sorted(yaml_region_keys) != sorted(cfg["expected_regions"]):
        fail_reasons.append("six-region map in YAML does not match expected_regions")
    if set(loader_regions.values()) != set(cfg["expected_regions"]):
        fail_reasons.append("loader regions are not the six expected names")

    spanning = [
        {
            "id": link["id"],
            "parent": link["parent"],
            "child": link["child"],
            "region": link["region"],
            "spans": list(link.get("spans") or []),
            "endpoint_relative_not_native_adjacent": bool(link.get("spans")),
        }
        for link in yaml_cfg["links"]
    ]
    pelvis_as_child = [s["id"] for s in spanning if s["child"] == "pelvis"]
    if pelvis_as_child:
        fail_reasons.append(f"pelvis appears as child of {pelvis_as_child}; unexpected")
    pelvis_parent_links = [s["id"] for s in spanning if s["parent"] == "pelvis"]
    if set(pelvis_parent_links) != {"pelvis_to_Ab", "pelvis_to_LThigh", "pelvis_to_RThigh"}:
        fail_reasons.append(f"unexpected pelvis-parent links: {pelvis_parent_links}")

    segs = build_segment_index(list(cfg["exercises"]))
    if segs["timepoint"].isin([2, 3]).any() and ALLOWED_TIMEPOINT == 1:
        # Index may contain other T; movement loads must not.
        pass
    t1 = segs[segs["timepoint"] == ALLOWED_TIMEPOINT].copy()
    t1 = t1[t1["participant"].astype(str).isin(cfg["participants"])]
    t1 = t1[t1["repetition"].isin(cfg["repetitions"])]
    t1 = t1[t1["exercise_id"].isin(cfg["exercises"])]
    if t1["timepoint"].nunique() != 1 or int(t1["timepoint"].iloc[0]) != 1:
        fail_reasons.append("T1 filter failed")
    n_cells = len(t1)
    if n_cells != int(cfg["expected_n_t1_cells"]):
        fail_reasons.append(f"expected {cfg['expected_n_t1_cells']} T1 cells, got {n_cells}")

    rotvec_dir = readonly_path("rotvec_dir")
    t1_rec_ids = sorted(set(t1["recording_id"].astype(str)))
    for rid in t1_rec_ids:
        assert_t1_recording_id(rid)
        if not (rotvec_dir / f"{rid}.parquet").exists():
            fail_reasons.append(f"missing T1 parquet {rid}")

    other_parquets = sorted(p.name for p in rotvec_dir.glob("*.parquet") if "_T1_" not in p.name)
    t1_parquet_names = sorted(p.name for p in rotvec_dir.glob("*_T1_*.parquet"))

    registry_path = REPO_ROOT / "data" / "immutable" / "recording_registry.csv"
    registry = pd.read_csv(registry_path)
    reg_t1 = registry[registry["timepoint"] == ALLOWED_TIMEPOINT].copy()
    t1_skeleton = (
        reg_t1[["participant", "repetition", "recording_id", "skeleton_variant", "n_bones", "root_bone", "capture_frame_rate"]]
        .assign(participant=lambda d: d["participant"].astype(str))
        .to_dict(orient="records")
    )
    # YAML `spans` documents 252/790 intermediates; 651/671 are native-adjacent
    # for the same endpoint pair (registry T1 skeleton_variant).
    t1_variant_by_pid = {}
    for row in t1_skeleton:
        pid = str(row["participant"])
        var = str(row["skeleton_variant"])
        t1_variant_by_pid.setdefault(pid, set()).add(var)
    spanning_by_template = {
        "yaml_spans_always_listed_on": [s["id"] for s in spanning if s["spans"]],
        "t1_native_adjacent_same_endpoints": sorted(
            pid for pid, vs in t1_variant_by_pid.items() if vs == {"51bone_basic"}
        ),
        "t1_spans_intermediates": sorted(
            pid for pid, vs in t1_variant_by_pid.items() if vs == {"55bone_extended"}
        ),
        "note": (
            "Ab_to_Chest and Neck_to_Head are endpoint-relative for all four T1 "
            "participants. They are native-adjacent on 51bone_basic (651, 671) and "
            "span intermediates on 55bone_extended (252, 790). YAML lists the "
            "extended-template intermediates on those two link records for all IDs."
        ),
    }
    expected_t1_variants = {"252": "55bone_extended", "651": "51bone_basic", "671": "51bone_basic", "790": "55bone_extended"}
    for pid, expected in expected_t1_variants.items():
        got = t1_variant_by_pid.get(pid, set())
        if got != {expected}:
            fail_reasons.append(f"T1 pid {pid} skeleton_variant {got} != {{{expected}}}")
    mixed = {pid: vs for pid, vs in t1_variant_by_pid.items() if len(vs) != 1}
    if mixed:
        fail_reasons.append(f"T1 participant with mixed skeleton variants: {mixed}")

    cells = []
    loaded_ids: list[str] = []
    rec_cache: dict[str, tuple[np.ndarray, int]] = {}
    for rec in t1.itertuples(index=False):
        rid = str(rec.recording_id)
        assert_t1_recording_id(rid)
        loaded_ids.append(rid)
        path = rotvec_dir / f"{rid}.parquet"
        if rid not in rec_cache:
            col_df = pd.read_parquet(path)
            n_cols = int(col_df.shape[1])
            for lid in yaml_ids:
                need = [f"{lid}_{a}" for a in AXES]
                if any(c not in col_df.columns for c in need):
                    fail_reasons.append(f"{rid} missing columns {need}")
            seen = []
            for col in col_df.columns:
                if col.endswith("_rx"):
                    seen.append(col[: -len("_rx")])
            if seen != list(yaml_ids):
                fail_reasons.append(f"{rid} parquet column link order {seen} != YAML")
            if n_cols != 54:
                issues.append(f"{rid} has {n_cols} columns, expected 54")
            rv_full = load_rotvec(rid)
            if rv_full.ndim != 3 or rv_full.shape[1:] != (18, 3):
                fail_reasons.append(f"{rid} load_rotvec shape {rv_full.shape}, expected (T, 18, 3)")
            rec_cache[rid] = (rv_full, n_cols)
            del col_df
        rv_full, n_cols = rec_cache[rid]
        sl = rv_full[int(rec.start_frame) : int(rec.end_frame)]
        q = qc_slice(sl, fps, cfg)
        q.update(
            {
                "participant": str(rec.participant),
                "timepoint": int(rec.timepoint),
                "repetition": int(rec.repetition),
                "exercise_id": int(rec.exercise_id),
                "recording_id": rid,
                "start_frame": int(rec.start_frame),
                "end_frame": int(rec.end_frame),
                "segment_id": rec.segment_id,
                "n_eval_windows": int(rec.n_windows),
                "parquet_n_frames_full_take": int(rv_full.shape[0]),
                "parquet_n_columns": int(n_cols),
            }
        )
        if int(rec.timepoint) != 1:
            fail_reasons.append(f"non-T1 cell slipped through: {rec.segment_id}")
        cells.append(q)

    if any("_T2_" in x or "_T3_" in x for x in loaded_ids):
        fail_reasons.append("loaded a T2/T3 recording_id")

    policy_fail = [c["segment_id"] for c in cells if not c["policy_ok"]]
    if policy_fail:
        fail_reasons.append(f"validity policy failed for {policy_fail}")

    near_pi_any = [c["segment_id"] for c in cells if c["n_near_pi_link_frames"] > 0]
    jump_any = [c["segment_id"] for c in cells if np.isfinite(c["jump_frac_step_gt_1rad"]) and c["jump_frac_step_gt_1rad"] > 0]
    trimmed_any = [c["segment_id"] for c in cells if c["trimmed"]]

    region_counts = {r: sum(1 for lid in yaml_ids if yaml_regions[lid] == r) for r in cfg["expected_regions"]}
    if region_counts.get("left_arm") != 4 or region_counts.get("right_arm") != 4:
        fail_reasons.append(f"unexpected arm link counts {region_counts}")

    assumptions.extend(
        [
            "Stored rotvecs are already 10 Hz order-4 zero-phase Butterworth-filtered (experiment.yaml / Layer 2); A0 does not re-filter.",
            "Units are radians (rotations.py log-map); A0 infers this from pipeline docs, not from a unit tag in parquet.",
            "Global root orientation/translation are absent because links are endpoint-relative to named bones; A0 does not reconstruct Motive global quats.",
            "Per-frame step uses Euclidean ||Δrotvec|| as a jump diagnostic only, not the planned SO(3) geodesic pairwise distance.",
        ]
    )

    # Representation interpretation checks (not RQA).
    interpretation_ok = True
    if yaml_cfg.get("root_token") != "pelvis":
        interpretation_ok = False
        fail_reasons.append("root_token is not pelvis")
    if not all(s["parent"] != "lab" for s in spanning):
        interpretation_ok = False

    if fail_reasons:
        verdict = "FAIL"
    elif near_pi_any:
        verdict = "PARTIAL"
        issues.append(
            f"T1 near-π link-frames in {near_pi_any} (below fail_frac; geodesic still defined)"
        )
    elif issues:
        verdict = "PARTIAL"
    else:
        verdict = "PASS"

    durs = [c["duration_s"] for c in cells]
    facts = {
        "stage": "A0",
        "allowed_timepoint": ALLOWED_TIMEPOINT,
        "verdict": verdict,
        "fail_reasons": fail_reasons,
        "issues": issues,
        "assumptions": assumptions,
        "n_t1_cells": n_cells,
        "expected_n_t1_cells": int(cfg["expected_n_t1_cells"]),
        "canonical_links": {
            "yaml_path": str(yaml_path.relative_to(REPO_ROOT)),
            "root_token": yaml_cfg.get("root_token"),
            "n_links": len(yaml_ids),
            "order": list(yaml_ids),
            "regions": yaml_regions,
            "region_counts": region_counts,
            "yaml_region_keys": yaml_region_keys,
            "spanning_links": spanning,
            "spanning_by_t1_template": spanning_by_template,
            "pelvis_parent_links": pelvis_parent_links,
            "loader_order_matches_yaml": yaml_ids == loader_ids,
        },
        "filter_and_rate": {
            "capture_frame_rate_hz_expected": exp.get("capture", {}).get("frame_rate_hz"),
            "filter_cutoff_hz": exp.get("filter", {}).get("cutoff_hz"),
            "filter_order": exp.get("filter", {}).get("order"),
            "filter_type": exp.get("filter", {}).get("filter_type"),
            "qc_near_pi_warning_fraction": exp.get("qc", {}).get("near_pi_warning_fraction"),
            "qc_jump_fail_rad": exp.get("qc", {}).get("jump_fail_rad"),
            "rotvec_units": "radians",
            "array_layout": "(T, 18, 3) after load_rotvec; parquet wide 54 columns {link}_{rx,ry,rz}",
        },
        "t1_skeleton_variants_from_registry": t1_skeleton,
        "t1_duration_s": {
            "min": min(durs) if durs else None,
            "median": float(np.median(durs)) if durs else None,
            "max": max(durs) if durs else None,
        },
        "t1_n_frames": {
            "min": min(c["n_frames"] for c in cells) if cells else None,
            "max": max(c["n_frames"] for c in cells) if cells else None,
        },
        "t1_qc_summary": {
            "n_policy_ok": sum(c["policy_ok"] for c in cells),
            "n_trimmed": len(trimmed_any),
            "n_near_pi_cells": len(near_pi_any),
            "n_jump_cells": len(jump_any),
            "max_angle_rad": max((c["angle_max_rad"] for c in cells), default=None),
            "max_step_rad": max((c["step_max_rad"] for c in cells if np.isfinite(c["step_max_rad"])), default=None),
            "max_nan_frac": max((c["nan_frac_values"] for c in cells), default=None),
        },
        "cells": cells,
        "filesystem_availability_no_movement": {
            "t1_parquet_files": t1_parquet_names,
            "other_parquet_filenames_not_opened": other_parquets,
            "note": "Non-T1 parquet names listed for availability only; arrays were not loaded.",
        },
        "loaded_recording_ids": sorted(set(loaded_ids)),
        "interpretation": {
            "construct": "internal endpoint-relative articulated configuration; not laboratory posture",
            "global_root_orientation_in_state": False,
            "global_translation_in_state": False,
            "challenges_planned_geodesic": fail_reasons or issues,
            "interpretation_ok": interpretation_ok and not fail_reasons,
        },
    }

    facts_path = rqa_path("outputs", "whole_body", "A0_representation_facts.json")
    facts_path.write_text(json.dumps(facts, indent=2, default=str))

    manifest = {
        "stage": "A0",
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "script": "rqa_guided_pilot/scripts/20_wb_a0_verify.py",
        "config": "rqa_guided_pilot/configs/whole_body_rqa.yaml",
        "hashes": {
            "script": _sha256_file(Path(__file__)),
            "whole_body_rqa_yaml": _sha256_file(RQA_ROOT / "configs" / "whole_body_rqa.yaml"),
            "canonical_links_yaml": _sha256_file(yaml_path),
            "experiment_yaml": _sha256_file(exp_path),
            "t1_parquets": {rid: _sha256_file(rotvec_dir / f"{rid}.parquet") for rid in t1_rec_ids},
        },
        "allowed_timepoint": ALLOWED_TIMEPOINT,
        "n_t1_cells": n_cells,
        "verdict": verdict,
        "outputs": {
            "facts": str(facts_path.relative_to(RQA_ROOT)),
            "gate": "reports/whole_body/A0_GATE.md",
        },
    }
    man_path = rqa_path("outputs", "whole_body", "A0_manifest.json")
    man_path.write_text(json.dumps(manifest, indent=2))

    gate = _render_gate(facts, manifest)
    gate_path = rqa_path("reports", "whole_body", "A0_GATE.md")
    gate_path.write_text(gate)
    print(f"A0 verdict={verdict} cells={n_cells} wrote {facts_path} {man_path} {gate_path}")
    return 0 if verdict != "FAIL" else 2


def _render_gate(facts: dict, manifest: dict) -> str:
    c = facts["canonical_links"]
    q = facts["t1_qc_summary"]
    d = facts["t1_duration_s"]
    lines = [
        "# A0 gate — whole-body configuration-space RQA",
        "",
        f"**Verdict:** `{facts['verdict']}`",
        "",
        "T1-only representation and data-integrity verification. No RQA metrics, no distance matrices, no T2/T3 rotvec loads.",
        "",
        "## Verified facts",
        "",
        f"- Canonical order ({c['n_links']} links): `{'`, `'.join(c['order'])}`",
        f"- Loader order matches YAML: **{c['loader_order_matches_yaml']}**",
        f"- Root token: `{c['root_token']}`; pelvis-parent links: {c['pelvis_parent_links']}",
        f"- Region counts: {c['region_counts']}",
        f"- YAML spanning-link IDs: {', '.join(c['spanning_by_t1_template']['yaml_spans_always_listed_on']) or '(none)'}",
        f"- T1 native-adjacent for those endpoints (51bone_basic): {c['spanning_by_t1_template']['t1_native_adjacent_same_endpoints']}",
        f"- T1 spanning intermediates (55bone_extended): {c['spanning_by_t1_template']['t1_spans_intermediates']}",
        f"- Filter/rate (from experiment.yaml, not re-applied): "
        f"{facts['filter_and_rate']['filter_type']} {facts['filter_and_rate']['filter_cutoff_hz']} Hz "
        f"order {facts['filter_and_rate']['filter_order']}; capture {facts['filter_and_rate']['capture_frame_rate_hz_expected']} Hz",
        f"- Rotvec layout: {facts['filter_and_rate']['array_layout']}; units assumed radians",
        f"- T1 cells: {facts['n_t1_cells']} / expected {facts['expected_n_t1_cells']}",
        f"- T1 duration_s min/median/max: {d['min']:.3f} / {d['median']:.3f} / {d['max']:.3f}",
        f"- T1 n_frames min/max: {facts['t1_n_frames']['min']} / {facts['t1_n_frames']['max']}",
        f"- Policy OK: {q['n_policy_ok']}/{facts['n_t1_cells']}; trimmed={q['n_trimmed']}; "
        f"near-π cells={q['n_near_pi_cells']}; jump cells={q['n_jump_cells']}",
        f"- T1 max |rotvec| angle rad: {q['max_angle_rad']}; max per-frame ||Δrotvec|| rad: {q['max_step_rad']}",
        f"- T1 max NaN fraction: {q['max_nan_frac']}",
        "",
        "### T1 skeleton variants (registry metadata, T1 rows only)",
        "",
    ]
    for row in facts["t1_skeleton_variants_from_registry"]:
        lines.append(
            f"- pid {row['participant']} R{row['repetition']}: {row['skeleton_variant']} "
            f"n_bones={row['n_bones']} root={row['root_bone']}"
        )
    lines += [
        "",
        "## Assumptions",
        "",
    ]
    for a in facts["assumptions"]:
        lines.append(f"- {a}")
    lines += [
        "",
        "## Fail reasons / issues",
        "",
    ]
    if facts["fail_reasons"]:
        for r in facts["fail_reasons"]:
            lines.append(f"- FAIL: {r}")
    else:
        lines.append("- (none)")
    if facts["issues"]:
        for r in facts["issues"]:
            lines.append(f"- ISSUE: {r}")
    lines += [
        "",
        "## Scientific consequences",
        "",
        "- Global laboratory orientation and translation are **not** in the 18-link state. "
        "A0 supports an **internal articulated configuration** claim, not unrestricted posture recurrence.",
        "- Equal-link distance would still overweight arms (4+4 links). That is a later distance-aggregator choice, not an A0 data failure.",
        "- A0 does **not** validate the 120-cell longitudinal grid. Only the 40 T1 cells were inspected.",
        "",
        f"## Manifest",
        "",
        f"- git: `{manifest.get('git_commit')}`",
        f"- utc: `{manifest.get('utc')}`",
        f"- facts: `{manifest['outputs']['facts']}`",
        "",
        "## A1 authorization",
        "",
    ]
    if facts["verdict"] == "PASS":
        lines.append("A0 PASS. A1 is eligible for **separate** authorization only. A1 was not started.")
    elif facts["verdict"] == "PARTIAL":
        lines.append("A0 PARTIAL. A1 is **not** automatically authorized; review issues first.")
    else:
        lines.append("A0 FAIL. A1 is **not** eligible.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
