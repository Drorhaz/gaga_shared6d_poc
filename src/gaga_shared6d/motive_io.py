"""Lean bone-only reader for Motive solved-skeleton CSV exports.

Ported from the validated parser in ``gaga_jcvpca/src/gaga_jcvpca/project_io.py``
but restricted to the bone-quaternion channels. The source files are ~225 MB
each with several thousand marker columns; reading only the ~84 bone columns
keeps the S2 extraction pass tractable.

Two provenance facts this module exists to enforce:

* ``Capture Start Time`` from the embedded header is authoritative for
  longitudinal ordering. Filenames are not: ``252_T2`` is named 2026-04-26 but
  was captured 2026-05-19.
* ``Length Units`` is read and returned so callers can assert it. ``252_T3`` is
  in Meters while all other recordings are in Millimeters.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

_BONE_AXIS = ("X", "Y", "Z", "W")  # SciPy quaternion order [x, y, z, w]


@dataclass
class MotiveHeader:
    """Header-only view of a take: cheap to read, no frame data touched."""

    path: Path
    meta: dict[str, str]
    bone_names: list[str]
    hierarchy: dict[str, str]  # bone -> parent bone; root maps to itself

    @property
    def capture_start_time(self) -> datetime:
        return _parse_motive_timestamp(self.meta["Capture Start Time"])

    @property
    def length_units(self) -> str:
        return self.meta.get("Length Units", "").strip()

    @property
    def total_frames(self) -> int:
        return int(float(self.meta.get("Total Frames in Take", "nan")))

    @property
    def capture_frame_rate(self) -> float:
        return float(self.meta.get("Capture Frame Rate", "nan"))

    def root_bone(self) -> str:
        for name, parent in self.hierarchy.items():
            if parent == name:
                return name
        raise ValueError(f"No root bone (self-parented) found in {self.path.name}")


@dataclass
class MotiveBones:
    """Bone quaternions for one take."""

    header: MotiveHeader
    bone_names: list[str]
    quaternions: np.ndarray  # (n_frames, n_bones, 4) SciPy order [x, y, z, w]

    def index_of(self, bone_name: str) -> int:
        return self.bone_names.index(bone_name)


def _parse_motive_timestamp(raw: str) -> datetime:
    """Parse Motive's ``2026-05-19 06.21.07.506 PM`` timestamp format."""
    m = re.match(
        r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2})\.(\d{2})\.(\d{2})(?:\.(\d+))?\s*([AP]M)?",
        raw.strip(),
    )
    if not m:
        raise ValueError(f"Unrecognised Motive timestamp: {raw!r}")
    y, mo, d, hh, mm, ss, frac, ampm = m.groups()
    hh = int(hh)
    if ampm == "PM" and hh != 12:
        hh += 12
    elif ampm == "AM" and hh == 12:
        hh = 0
    micro = int(round(float(f"0.{frac}") * 1e6)) if frac else 0
    return datetime(int(y), int(mo), int(d), hh, int(mm), int(ss), micro)


def _read_header_rows(path: Path, max_rows: int = 12) -> list[list[str]]:
    rows: list[list[str]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            rows.append(next(csv.reader([line])))
            if i >= max_rows:
                break
    return rows


def _find_row(rows: list[list[str]], col: int, token: str) -> int:
    for i, row in enumerate(rows):
        if len(row) > col and row[col].strip() == token:
            return i
    raise ValueError(f"Could not find Motive header row {token!r}")


def _parse_meta(row0: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for i in range(0, len(row0) - 1, 2):
        key = row0[i].strip()
        if key:
            meta[key] = row0[i + 1]
    return meta


def _group_bone_columns(
    type_row: list[str], name_row: list[str], frame_row: list[str]
) -> tuple[list[str], list[list[int]]]:
    """Group CSV column indices by bone name, ordered [X, Y, Z, W]."""
    order: list[str] = []
    by_name: dict[str, list[tuple[int, str]]] = {}
    for i, token in enumerate(type_row):
        if token.strip() != "Bone":
            continue
        name = name_row[i] if i < len(name_row) else f"col{i}"
        if name not in by_name:
            order.append(name)
            by_name[name] = []
        axis = frame_row[i].strip() if i < len(frame_row) else ""
        by_name[name].append((i, axis))

    indices: list[list[int]] = []
    for name in order:
        pairs = by_name[name]
        # A bone carries rotation (X,Y,Z,W) and then position (X,Y,Z) columns
        # under the same name, so X/Y/Z each appear twice. Take the FIRST match
        # per axis, which is the rotation channel.
        ordered: list[int] = []
        for axis in _BONE_AXIS:
            for col, ax in pairs:
                if ax == axis:
                    ordered.append(col)
                    break
        if len(ordered) < len(_BONE_AXIS):
            ordered = [col for col, _ in pairs[: len(_BONE_AXIS)]]
        indices.append(ordered)
    return order, indices


def read_header(path: str | Path) -> MotiveHeader:
    """Read metadata, bone names and hierarchy without touching frame data."""
    path = Path(path)
    rows = _read_header_rows(path)
    meta = _parse_meta(rows[0])
    type_idx = _find_row(rows, 1, "Type")
    type_row, name_row = rows[type_idx], rows[type_idx + 1]

    parent_row = None
    for r in rows:
        if len(r) > 1 and r[1].strip() == "Parent":
            parent_row = r
            break

    bone_names: list[str] = []
    hierarchy: dict[str, str] = {}
    for i, token in enumerate(type_row):
        if token.strip() != "Bone":
            continue
        name = name_row[i].strip() if i < len(name_row) else ""
        if not name or name in hierarchy:
            continue
        bone_names.append(name)
        parent = ""
        if parent_row is not None and i < len(parent_row):
            parent = parent_row[i].strip()
        hierarchy[name] = name if parent in ("", "Root") else parent

    return MotiveHeader(path=path, meta=meta, bone_names=bone_names, hierarchy=hierarchy)


def read_bones(path: str | Path, max_frames: int | None = None) -> MotiveBones:
    """Read bone quaternions only. Marker columns are never parsed."""
    path = Path(path)
    rows = _read_header_rows(path)
    header = read_header(path)
    type_idx = _find_row(rows, 1, "Type")
    frame_idx = _find_row(rows, 0, "Frame")
    bone_names, bone_cols = _group_bone_columns(
        rows[type_idx], rows[type_idx + 1], rows[frame_idx]
    )

    usecols = sorted({c for group in bone_cols for c in group})
    if not usecols:
        raise ValueError(f"No Bone columns found in {path}")
    colmap = {col: ui for ui, col in enumerate(usecols)}

    df = pd.read_csv(
        path,
        skiprows=frame_idx + 1,
        header=None,
        usecols=usecols,
        nrows=max_frames,
        low_memory=False,
    )

    n_frames = len(df)
    quats = np.full((n_frames, len(bone_names), 4), np.nan, dtype=float)
    for bi, cols in enumerate(bone_cols):
        for ai, col in enumerate(cols):
            quats[:, bi, ai] = pd.to_numeric(df.iloc[:, colmap[col]], errors="coerce")

    return MotiveBones(header=header, bone_names=bone_names, quaternions=quats)


def segment_token(bone_name: str) -> str:
    """Strip asset prefixes from a bone name down to its segment token.

    Handles ``671:Chest``, ``671_Chest`` and double-prefixed ``T3_671_Chest``,
    all of which collapse to ``Chest``.
    """
    base = bone_name.split(":", 1)[1] if ":" in bone_name else bone_name
    return base.rsplit("_", 1)[-1] if "_" in base else base


def resolve_bone(header: MotiveHeader, token: str, root_token: str = "pelvis") -> str:
    """Map a canonical segment token to this take's actual bone name.

    ``pelvis`` resolves to the skeleton root, which is named after the
    participant in the export (e.g. ``671:671``) and so cannot be matched
    by token.
    """
    if token == root_token:
        return header.root_bone()
    matches = [b for b in header.bone_names if segment_token(b) == token]
    if not matches:
        raise KeyError(f"Bone token {token!r} not found in {header.path.name}")
    if len(matches) > 1:
        raise KeyError(f"Bone token {token!r} is ambiguous in {header.path.name}: {matches}")
    return matches[0]
