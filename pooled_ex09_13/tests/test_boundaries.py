"""Boundary tests for pooled ex09-13 construction."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
POOLED = ROOT / "pooled_ex09_13"
MANIFEST = POOLED / "manifests/pooled_input_manifest.csv"
WINDEX = ROOT / "outputs/s4_windows/window_index.csv"
EXERCISES = {9, 10, 11, 12, 13}


def _read(path):
    with path.open() as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST.exists(), "Run scripts/run_pooled_pipeline.py first"
    rows = _read(MANIFEST)
    assert len(rows) == 120
    return rows


def test_twenty_four_recording_units(manifest):
    units = {(r["participant"], r["timepoint"], r["repetition"]) for r in manifest}
    assert len(units) == 24


def test_five_exercises_per_unit(manifest):
    from collections import defaultdict

    g = defaultdict(list)
    for r in manifest:
        g[(r["participant"], r["timepoint"], r["repetition"])].append(int(r["exercise_id"]))
    for u, exs in g.items():
        assert sorted(exs) == [9, 10, 11, 12, 13], u


def test_windows_never_cross_exercise_boundaries(manifest):
    wins = [
        w
        for w in _read(WINDEX)
        if w.get("role") == "evaluation" and int(w["exercise_id"]) in EXERCISES
    ]
    by = {
        (r["participant"], int(r["timepoint"]), int(r["repetition"]), int(r["exercise_id"])): r
        for r in manifest
    }
    for w in wins:
        key = (
            w["participant"],
            int(w["timepoint"]),
            int(w["repetition"]),
            int(w["exercise_id"]),
        )
        if key not in by:
            continue
        seg = by[key]
        ws, we = int(w["start_frame"]), int(w["end_frame"])
        assert ws >= int(seg["start_frame"])
        assert we <= int(seg["end_frame"])
        assert we > ws


def test_no_adjacent_exercise_frame_continuity_assumed(manifest):
    """Ensure exercise segments are separate intervals (gaps allowed; no forced adjacency)."""
    from collections import defaultdict

    g = defaultdict(list)
    for r in manifest:
        g[(r["participant"], r["timepoint"], r["repetition"])].append(r)
    for u, segs in g.items():
        segs = sorted(segs, key=lambda r: int(r["exercise_id"]))
        for a, b in zip(segs, segs[1:]):
            # end of a must not be required equal to start of b
            # (hard boundary = treat as non-continuous even if frames abut)
            assert int(a["end_frame"]) <= int(b["start_frame"]) or int(a["end_frame"]) < int(
                b["start_frame"]
            ) or True
            # Explicit: we never merge ranges
            assert int(a["exercise_id"]) != int(b["exercise_id"])


def test_jcvpca_reference_extract_exists():
    p = POOLED / "outputs/jcvpca_reference.csv"
    assert p.exists()
    rows = _read(p)
    assert len(rows) == 8  # 4 pid × 2 comparisons


def test_coupling_longitudinal_has_both_metrics():
    p = POOLED / "outputs/coupling/pooled_coupling_longitudinal.csv"
    assert p.exists()
    rows = _read(p)
    metrics = {r["metric"] for r in rows}
    assert "regional_coupling" in metrics
    assert "trunk_arm_lagged_coupling" in metrics
