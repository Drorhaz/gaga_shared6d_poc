"""Load validated primary-path 6D windows for S5+.

Primary path (unchanged):
    rotvec_18link parquet (filtered) → rotation matrix → 6D

Angular velocity for the motion objective is derived from the same filtered
rotvecs by finite difference, in degrees per second.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from . import rotations

ROOT = Path(__file__).resolve().parents[2]
AXES = ("rx", "ry", "rz")

_CACHE: dict[str, dict] = {}


def load_config(root: Path | None = None) -> dict:
    root = root or ROOT
    return yaml.safe_load((root / "configs/experiment.yaml").read_text())


def load_link_config(root: Path | None = None) -> tuple[list[str], dict[str, str]]:
    root = root or ROOT
    cfg = yaml.safe_load((root / "configs/canonical_links_18.yaml").read_text())
    link_ids = [l["id"] for l in cfg["links"]]
    regions = {l["id"]: l["region"] for l in cfg["links"]}
    return link_ids, regions


def load_rotvec(recording_id: str, root: Path | None = None) -> np.ndarray:
    """(T, L, 3) filtered rotvecs in link order."""
    root = root or ROOT
    link_ids, _ = load_link_config(root)
    key = f"rotvec:{recording_id}"
    if key not in _CACHE:
        df = pd.read_parquet(root / "data/immutable/rotvec_18link" / f"{recording_id}.parquet")
        arr = np.stack(
            [df[[f"{lid}_{a}" for a in AXES]].to_numpy() for lid in link_ids], axis=1
        )
        _CACHE[key] = arr
    return _CACHE[key]


def rotvec_to_sixd(rotvec: np.ndarray) -> np.ndarray:
    """(T, L, 3) → (T, L, 6)."""
    t, l, _ = rotvec.shape
    mats = rotations.rotvec_to_matrix(rotvec.reshape(-1, 3))
    return rotations.matrix_to_6d(mats).reshape(t, l, 6)


def angular_velocity_deg_s(rotvec: np.ndarray, fps: float) -> np.ndarray:
    """(T, L, 3) angular velocity in deg/s; frame 0 zero-filled for training."""
    out = np.zeros_like(rotvec)
    out[1:] = np.degrees(np.diff(rotvec, axis=0)) * fps
    return out


def load_recording_arrays(recording_id: str, root: Path | None = None) -> dict:
    root = root or ROOT
    cfg = load_config(root)
    key = f"arrays:{recording_id}"
    if key not in _CACHE:
        rv = load_rotvec(recording_id, root)
        sixd = rotvec_to_sixd(rv)
        vel = angular_velocity_deg_s(rv, cfg["capture"]["frame_rate_hz"])
        _CACHE[key] = {"rotvec": rv, "sixd": sixd, "velocity": vel}
    return _CACHE[key]


def load_window_index(root: Path | None = None) -> pd.DataFrame:
    root = root or ROOT
    return pd.read_csv(root / "outputs/s4_windows/window_index.csv")


def materialise_windows(
    index: pd.DataFrame, root: Path | None = None, objective: str = "masked_6d",
) -> tuple[np.ndarray, pd.DataFrame]:
    """Stack windows to (N, T, L, C) float32 plus the filtered index."""
    root = root or ROOT
    cfg = load_config(root)
    t_len = int(round(cfg["windowing"]["window_seconds"] * cfg["capture"]["frame_rate_hz"]))
    link_ids, _ = load_link_config(root)
    n_links = len(link_ids)
    key = "sixd" if objective == "masked_6d" else "velocity"

    xs, keep_ids = [], []
    for row in index.itertuples():
        arrs = load_recording_arrays(row.recording_id, root)
        sl = arrs[key][int(row.start_frame):int(row.end_frame)]
        if sl.shape != (t_len, n_links, arrs[key].shape[-1]):
            continue
        if not np.all(np.isfinite(sl)):
            continue
        xs.append(sl.astype(np.float32))
        keep_ids.append(row.window_id)

    out_index = index[index.window_id.isin(keep_ids)].drop_duplicates("window_id")
    # preserve keep_ids order
    out_index = out_index.set_index("window_id").loc[keep_ids].reset_index()
    if not xs:
        c = 6 if objective == "masked_6d" else 3
        return np.zeros((0, t_len, n_links, c), dtype=np.float32), out_index
    return np.stack(xs, axis=0), out_index


def aggregate_recording_embeddings(
    window_emb: np.ndarray, index: pd.DataFrame, eval_exercises: list[int],
) -> pd.DataFrame:
    """windows → mean within exercise → equal-weight mean across exercises."""
    df = index.copy().reset_index(drop=True)
    for i in range(window_emb.shape[1]):
        df[f"e{i}"] = window_emb[:, i]
    ecols = [f"e{i}" for i in range(window_emb.shape[1])]

    rows = []
    for (pid, tp, rep, rid), g in df.groupby(
        ["participant", "timepoint", "repetition", "recording_id"]
    ):
        ge = g[g.exercise_id.isin(eval_exercises)] if eval_exercises else g
        if ge.empty:
            continue
        per_ex = ge.groupby("exercise_id")[ecols].mean()
        vec = per_ex.mean(axis=0).to_numpy()
        ex11 = ge[ge.exercise_id == 11]
        vec11 = ex11[ecols].mean().to_numpy() if len(ex11) else np.full(len(ecols), np.nan)
        row = {
            "participant": pid, "timepoint": int(tp), "repetition": int(rep),
            "recording_id": rid, "n_windows": len(ge),
            "n_exercises": int(per_ex.shape[0]),
        }
        for i, v in enumerate(vec):
            row[f"e{i}"] = float(v)
        for i, v in enumerate(vec11):
            row[f"ex11_e{i}"] = float(v)
        rows.append(row)
    return pd.DataFrame(rows)
