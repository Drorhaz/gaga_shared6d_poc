"""Normalise the four per-participant segmentation workbooks into one table.

The source workbooks are not schema-consistent and one is actively malformed:

* Most sheets carry ``end_frame``; ``671 - T1P1R1`` carries
  ``end_frame_exclusive`` and is 35 rows x 25 columns with three duplicated
  parallel column blocks and literal ``'blank'`` strings in frame cells.
* ex16/ex17 have unmarked boundaries in nearly every recording. They fall
  outside both the training (ex01-15) and evaluation (ex09-13) scope.
* ``790-T1-R1`` has an unmarked ex04/ex05 boundary, which *is* inside the
  training scope. The two are merged into one contiguous block, which is sound
  because self-supervised training does not require exercise matching.

All ends are normalised to EXCLUSIVE (python slice) semantics.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

_SHEET_RE = re.compile(r"T(\d)P(\d)R(\d)")


def _parse_sheet_name(sheet: str) -> tuple[int, int, int]:
    m = _SHEET_RE.search(sheet.replace(" ", "").replace("-", ""))
    if not m:
        raise ValueError(f"Unparseable segmentation sheet name: {sheet!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _pick_frame_columns(df: pd.DataFrame) -> tuple[str, str, str]:
    """Return (exercise_col, start_col, end_col), tolerating schema drift."""
    end_col = "end_frame" if "end_frame" in df.columns else "end_frame_exclusive"
    if end_col not in df.columns:
        raise ValueError(f"No end-frame column among {list(df.columns)}")
    return "exercise_id", "start_frame", end_col


def load_workbook(path: str | Path, participant: str) -> tuple[pd.DataFrame, list[dict]]:
    """Read one workbook into tidy rows plus a list of repaired/dropped issues."""
    path = Path(path)
    xl = pd.ExcelFile(path)
    rows: list[dict] = []
    issues: list[dict] = []

    for sheet in xl.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet)
        timepoint, task_part, repetition = _parse_sheet_name(sheet)
        ex_col, start_col, end_col = _pick_frame_columns(raw)

        sub = raw[[ex_col, start_col, end_col]].copy()
        sub.columns = ["exercise_id", "start_frame", "end_frame"]
        for c in sub.columns:
            sub[c] = pd.to_numeric(sub[c], errors="coerce")

        # The malformed 671 sheet repeats its column block; keep the first
        # occurrence of each exercise.
        sub = sub.dropna(subset=["exercise_id"]).drop_duplicates(subset=["exercise_id"])

        for _, r in sub.iterrows():
            ex = int(r["exercise_id"])
            record = {
                "participant": participant,
                "timepoint": timepoint,
                "task_part": task_part,
                "repetition": repetition,
                "exercise_id": ex,
                "source_sheet": sheet,
                "source_end_column": end_col,
            }
            if pd.isna(r["start_frame"]) or pd.isna(r["end_frame"]):
                issues.append(
                    {**record, "issue": "unmarked_boundary",
                     "start_frame": r["start_frame"], "end_frame": r["end_frame"]}
                )
                continue
            rows.append(
                {**record, "start_frame": int(r["start_frame"]), "end_frame": int(r["end_frame"])}
            )

    return pd.DataFrame(rows), issues


def repair_unmarked_pairs(
    seg: pd.DataFrame, issues: list[dict], training_exercises: set[int]
) -> tuple[pd.DataFrame, list[dict]]:
    """Merge an adjacent pair whose shared boundary is unmarked.

    Applies only when the gap is inside the training scope and the pair brackets
    a single missing boundary: exercise k has a start but no end, and k+1 has an
    end but no start. Outside the training scope the rows are simply dropped.
    """
    repairs: list[dict] = []
    by_recording: dict[tuple, list[dict]] = {}
    for it in issues:
        by_recording.setdefault(
            (it["participant"], it["timepoint"], it["repetition"]), []
        ).append(it)

    new_rows = []
    for key, items in by_recording.items():
        starts = {i["exercise_id"]: i for i in items if pd.notna(i["start_frame"])}
        ends = {i["exercise_id"]: i for i in items if pd.notna(i["end_frame"])}
        for ex, first in starts.items():
            second = ends.get(ex + 1)
            if second is None:
                continue
            if ex not in training_exercises and (ex + 1) not in training_exercises:
                continue
            new_rows.append(
                {
                    "participant": key[0], "timepoint": key[1],
                    "task_part": first["task_part"], "repetition": key[2],
                    "exercise_id": ex,
                    "start_frame": int(first["start_frame"]),
                    "end_frame": int(second["end_frame"]),
                    "source_sheet": first["source_sheet"],
                    "source_end_column": first["source_end_column"],
                    "merged_with": ex + 1,
                }
            )
            repairs.append(
                {
                    **key_to_dict(key), "merged_exercises": [ex, ex + 1],
                    "reason": "unmarked shared boundary inside training scope",
                    "start_frame": int(first["start_frame"]),
                    "end_frame": int(second["end_frame"]),
                }
            )

    if new_rows:
        seg = pd.concat([seg, pd.DataFrame(new_rows)], ignore_index=True)
    return seg.sort_values(
        ["participant", "timepoint", "repetition", "exercise_id"]
    ).reset_index(drop=True), repairs


def key_to_dict(key: tuple) -> dict:
    return {"participant": key[0], "timepoint": key[1], "repetition": key[2]}


def build_segmentation(
    seg_dir: str | Path, participants: list[str], training_exercises: list[int],
    frame_rate_hz: float = 120.0,
) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    """Normalise every workbook in ``seg_dir`` into one tidy table."""
    seg_dir = Path(seg_dir)
    frames, all_issues = [], []
    for pid in participants:
        matches = list(seg_dir.glob(f"{pid}_*.xlsx"))
        if not matches:
            raise FileNotFoundError(f"No segmentation workbook for participant {pid}")
        df, issues = load_workbook(matches[0], pid)
        frames.append(df)
        all_issues.extend(issues)

    seg = pd.concat(frames, ignore_index=True)
    seg, repairs = repair_unmarked_pairs(seg, all_issues, set(training_exercises))

    if "merged_with" not in seg.columns:
        seg["merged_with"] = pd.NA

    seg["n_frames"] = seg["end_frame"] - seg["start_frame"]
    seg["duration_s"] = seg["n_frames"] / frame_rate_hz
    seg["block_id"] = (
        seg["participant"].astype(str) + "_T" + seg["timepoint"].astype(str)
        + "_R" + seg["repetition"].astype(str) + "_ex" + seg["exercise_id"].astype(str).str.zfill(2)
    )
    return seg, all_issues, repairs
