#!/usr/bin/env python3
"""Orchestrate Stage 1: segment index → T1 diagnostics → lock → Auto-RQA → gate."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RQA_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "00_build_segment_index.py",
    "02_t1_ami_fnn_rate_diagnostics.py",
    "03_lock_parameters.py",
    "04_stage1_auto_rqa.py",
    "05_stage1_gate.py",
]


def run_one(name: str) -> float:
    t0 = time.time()
    print(f"\n=== {name} ===", flush=True)
    subprocess.run([sys.executable, str(RQA_ROOT / "scripts" / name)], check=True, cwd=str(RQA_ROOT / "scripts"))
    return time.time() - t0


def main() -> None:
    timings = {}
    for script in SCRIPTS:
        timings[script] = run_one(script)
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "package": "rqa_guided_pilot",
        "stage": "stage1",
        "scripts": SCRIPTS,
        "timings_s": timings,
        "readonly_inputs": [
            "data/immutable/rotvec_18link/",
            "outputs/s4_windows/window_index.csv",
            "configs/canonical_links_18.yaml",
        ],
        "writes_confined_to": "rqa_guided_pilot/",
        "freeze_tag": "guided-analysis-freeze-v1",
        "freeze_commit": "5062e22",
    }
    out = RQA_ROOT / "manifests" / "stage1_run_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))
    print(f"\nStage 1 complete. Manifest: {out}")
    print(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
