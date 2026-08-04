#!/usr/bin/env python3
"""Orchestrate Stage 2 pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RQA_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "10_stage2_auto_rqa.py",
    "11_stage2_analyze.py",
    "12_stage2_mdrqa_crqa.py",
    "13_stage2_write_reports.py",
]


def main() -> None:
    timings = {}
    for name in SCRIPTS:
        print(f"\n=== {name} ===", flush=True)
        t0 = time.time()
        subprocess.run([sys.executable, str(RQA_ROOT / "scripts" / name)], check=True, cwd=str(RQA_ROOT / "scripts"))
        timings[name] = time.time() - t0
    manifest_path = RQA_ROOT / "manifests" / "stage2_run_manifest.json"
    if manifest_path.exists():
        man = json.loads(manifest_path.read_text())
        man["timings_s"] = timings
        man["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(man, indent=2))
    print(json.dumps(timings, indent=2))


if __name__ == "__main__":
    main()
