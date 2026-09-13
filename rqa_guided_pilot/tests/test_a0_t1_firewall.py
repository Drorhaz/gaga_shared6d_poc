"""A0 T1 firewall: no T2/T3 CLI, hard-coded timepoint 1, no RQA imports in the A0 script."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "20_wb_a0_verify.py"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def test_allowed_timepoint_is_one():
    import importlib.util

    spec = importlib.util.spec_from_file_location("wb_a0", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    # Do not exec the full script (would run side effects on import of argparse only).
    src = SCRIPT.read_text()
    tree = ast.parse(src)
    assigned = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "ALLOWED_TIMEPOINT":
                    assigned = ast.literal_eval(node.value)
    assert assigned == 1


def test_no_timepoint_cli_option():
    src = SCRIPT.read_text()
    assert "--timepoint" not in src
    assert "--timepoints" not in src
    tree = ast.parse(src)
    cli_flags = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None)
            if name == "add_argument":
                if node.args and isinstance(node.args[0], ast.Constant):
                    cli_flags.append(node.args[0].value)
    assert all("timepoint" not in str(f).lower() for f in cli_flags)


def test_script_does_not_import_rqa_metrics():
    src = SCRIPT.read_text()
    forbidden = (
        "auto_rqa",
        "mdrqa_metrics",
        "quantify_rp",
        "recurrence_matrix",
        "pose_mdrqa",
        "pose_distance",
        "threshold_for_target_rr",
        "pairwise_distance_matrix",
    )
    for name in forbidden:
        assert name not in src, name


def test_assert_t1_recording_id_rejects_t2_t3():
    sys.path.insert(0, str(ROOT / "scripts"))
    # Load helper without running main: exec only the function via ast is heavy;
    # import module after patching parse? Importing the script defines functions then
    # would not call main. Importing 20_wb_a0_verify as module will not run main.
    import importlib.util

    spec = importlib.util.spec_from_file_location("wb_a0_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        mod.assert_t1_recording_id("252_T2_P1_R1")
        raise AssertionError("T2 id should be rejected")
    except RuntimeError:
        pass
    try:
        mod.assert_t1_recording_id("252_T3_P1_R1")
        raise AssertionError("T3 id should be rejected")
    except RuntimeError:
        pass
    mod.assert_t1_recording_id("252_T1_P1_R1")


def test_wb_yaml_timepoint_one():
    import yaml

    cfg = yaml.safe_load((ROOT / "configs" / "whole_body_rqa.yaml").read_text())
    assert int(cfg["allowed_timepoint"]) == 1
    assert int(cfg["expected_n_t1_cells"]) == 40
