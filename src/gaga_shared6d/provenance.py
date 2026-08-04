"""Provenance capture: checksums, environment, and run stamps.

Every artifact this project emits must be traceable to participant, timepoint,
repetition, exercise, source recording, original frame range, preprocessing
version and (later) model version and seed.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Bump when any transformation in extract.py or sixd.py changes meaning.
PREPROCESSING_VERSION = "s6d-0.1.0"


def sha256_file(path: str | Path, chunk_bytes: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(chunk_bytes):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_commit(repo: str | Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def environment() -> dict[str, Any]:
    import numpy, pandas, scipy  # noqa: E401

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pandas": pandas.__version__,
        "preprocessing_version": PREPROCESSING_VERSION,
    }


def run_stamp(stage: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    stamp = {
        "stage": stage,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": environment(),
    }
    if extra:
        stamp.update(extra)
    return stamp


def write_json(path: str | Path, payload: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
