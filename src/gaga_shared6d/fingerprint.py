"""Content fingerprints for reproduction checking.

Binary file hashes are not usable here. Parquet embeds a writer version and
schema metadata, JSON provenance carries a run timestamp, one CSV records
wall-clock runtime, and PNG encoders are free to vary. All of those differ
between two correct runs.

So every artifact is hashed by its *content*: numerical arrays as raw IEEE-754
bytes, text columns as their string values, JSON as a normalised tree with
volatile keys removed, and images as their decoded pixel arrays.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Runtime measurements are content, but not reproducible content.
VOLATILE_COLUMNS = {"seconds"}
# Wall-clock stamps in provenance JSON.
VOLATILE_JSON_KEYS = {"utc"}


def _hash_series(h: hashlib._Hash, name: str, s: pd.Series) -> None:
    h.update(name.encode())
    h.update(str(s.dtype).encode())
    arr = s.to_numpy()
    if arr.dtype.kind in "fiub":
        # Raw bytes: exact for float64, and NaN has a stable bit pattern.
        h.update(np.ascontiguousarray(arr).tobytes())
    else:
        h.update("\x1f".join("" if v is None else str(v) for v in arr.tolist()).encode())


def frame_content_hash(df: pd.DataFrame, drop: set[str] | None = None) -> str:
    """Hash a table by its values, independent of column order and file format."""
    drop = (drop or set()) | VOLATILE_COLUMNS
    cols = sorted(c for c in df.columns if c not in drop)
    h = hashlib.sha256()
    h.update(f"rows={len(df)}|cols={len(cols)}".encode())
    for c in cols:
        _hash_series(h, str(c), df[c])
    return h.hexdigest()


def _strip_volatile(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in sorted(obj.items())
                if k not in VOLATILE_JSON_KEYS}
    if isinstance(obj, list):
        return [_strip_volatile(v) for v in obj]
    return obj


def json_content_hash(path: Path) -> str:
    payload = _strip_volatile(json.loads(Path(path).read_text()))
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def parquet_content_hash(path: Path) -> str:
    return frame_content_hash(pd.read_parquet(path))


def csv_content_hash(path: Path) -> str:
    return frame_content_hash(pd.read_csv(path))


def image_content_hash(path: Path) -> str:
    """Hash decoded pixels, so encoder metadata does not matter."""
    import matplotlib.image as mpimg

    arr = np.ascontiguousarray(mpimg.imread(path))
    h = hashlib.sha256()
    h.update(str(arr.shape).encode())
    h.update(arr.tobytes())
    return h.hexdigest()


def fingerprint_path(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".parquet":
            kind, digest = "parquet_content", parquet_content_hash(path)
        elif suffix == ".csv":
            kind, digest = "csv_content", csv_content_hash(path)
        elif suffix == ".json":
            kind, digest = "json_content", json_content_hash(path)
        elif suffix == ".png":
            kind, digest = "image_pixels", image_content_hash(path)
        else:
            kind = "bytes"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"kind": kind, "hash": digest}
    except Exception as exc:  # a readable artifact that will not parse is a finding
        return {"kind": "error", "hash": None, "error": f"{type(exc).__name__}: {exc}"}


def fingerprint_tree(
    root: Path, subdirs: list[str], exclude_prefixes: tuple[str, ...] = ()
) -> dict[str, dict]:
    """Fingerprint every artifact under the given subdirectories of ``root``.

    ``exclude_prefixes`` skips paths written by the reproduction checker itself,
    which would otherwise appear as spurious new artifacts in its own run.
    """
    out: dict[str, dict] = {}
    for sub in subdirs:
        base = root / sub
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.name == ".DS_Store":
                continue
            rel = str(path.relative_to(root))
            if rel.startswith(exclude_prefixes):
                continue
            out[rel] = fingerprint_path(path)
    return out


def compare_fingerprints(before: dict, after: dict) -> dict[str, list[str]]:
    b, a = set(before), set(after)
    changed = [
        k for k in sorted(b & a)
        if before[k].get("hash") != after[k].get("hash") or before[k].get("kind") != after[k].get("kind")
    ]
    return {
        "identical": sorted(k for k in (b & a) if k not in changed),
        "changed": changed,
        "missing_after": sorted(b - a),
        "new_after": sorted(a - b),
    }
