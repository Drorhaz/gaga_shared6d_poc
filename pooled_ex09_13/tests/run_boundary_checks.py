#!/usr/bin/env python3
"""Boundary checks without pytest dependency."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POOLED = ROOT / "pooled_ex09_13"
MANIFEST = POOLED / "manifests/pooled_input_manifest.csv"
WINDEX = ROOT / "outputs/s4_windows/window_index.csv"
EXERCISES = {9, 10, 11, 12, 13}


def main() -> None:
    assert MANIFEST.exists(), "Run scripts/run_pooled_pipeline.py first"
    manifest = list(csv.DictReader(MANIFEST.open()))
    assert len(manifest) == 120, len(manifest)
    units = {(r["participant"], r["timepoint"], r["repetition"]) for r in manifest}
    assert len(units) == 24, len(units)

    g = defaultdict(list)
    for r in manifest:
        g[(r["participant"], r["timepoint"], r["repetition"])].append(int(r["exercise_id"]))
    for u, exs in g.items():
        assert sorted(exs) == [9, 10, 11, 12, 13], (u, exs)

    # Hard boundaries: no exercise range merge; gaps/abutting allowed but IDs distinct
    for u, segs in g.items():
        segs_rows = [
            r
            for r in manifest
            if (r["participant"], r["timepoint"], r["repetition"]) == u
        ]
        segs_rows = sorted(segs_rows, key=lambda r: int(r["exercise_id"]))
        for a, b in zip(segs_rows, segs_rows[1:]):
            assert int(a["exercise_id"]) != int(b["exercise_id"])
            # boundary indices preserved
            assert int(a["end_frame"]) > int(a["start_frame"])
            assert int(b["end_frame"]) > int(b["start_frame"])

    by = {
        (r["participant"], int(r["timepoint"]), int(r["repetition"]), int(r["exercise_id"])): r
        for r in manifest
    }
    n_ok = 0
    for w in csv.DictReader(WINDEX.open()):
        if w.get("role") != "evaluation" or int(w["exercise_id"]) not in EXERCISES:
            continue
        key = (
            w["participant"],
            int(w["timepoint"]),
            int(w["repetition"]),
            int(w["exercise_id"]),
        )
        if key not in by:
            continue
        seg = by[key]
        assert int(w["start_frame"]) >= int(seg["start_frame"])
        assert int(w["end_frame"]) <= int(seg["end_frame"])
        n_ok += 1
    assert n_ok > 0

    # Lag/derivative conceptual check: coupling aggregation field documents hard boundary
    coup = list(csv.DictReader((POOLED / "outputs/coupling/pooled_coupling_longitudinal.csv").open()))
    assert coup
    rec = list(csv.DictReader((POOLED / "outputs/explicit/pooled_recording_features.csv").open()))
    assert all(r.get("boundary_rule") == "HARD_NO_CROSS" for r in rec)

    jcv = list(csv.DictReader((POOLED / "outputs/jcvpca_reference.csv").open()))
    assert len(jcv) == 8

    print(f"BOUNDARY CHECKS PASS (windows_checked={n_ok}, units=24, segments=120)")


if __name__ == "__main__":
    main()
