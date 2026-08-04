"""Read-only loaders for frozen guided-analysis artifacts."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import yaml

from .paths import readonly_path

AXES = ("rx", "ry", "rz")


@lru_cache(maxsize=1)
def load_link_config() -> tuple[tuple[str, ...], dict[str, str]]:
    cfg = yaml.safe_load(readonly_path("canonical_links").read_text())
    link_ids = tuple(link["id"] for link in cfg["links"])
    regions = {link["id"]: link["region"] for link in cfg["links"]}
    return link_ids, regions


@lru_cache(maxsize=32)
def load_rotvec(recording_id: str) -> np.ndarray:
    """Return (T, L, 3) filtered rotvec array. Read-only."""
    link_ids, _ = load_link_config()
    path = readonly_path("rotvec_dir") / f"{recording_id}.parquet"
    df = pd.read_parquet(path)
    return np.stack(
        [df[[f"{lid}_{a}" for a in AXES]].to_numpy(dtype=np.float64) for lid in link_ids],
        axis=1,
    )


@lru_cache(maxsize=1)
def load_window_index() -> pd.DataFrame:
    return pd.read_csv(readonly_path("window_index"))


def build_segment_index(exercises: list[int] | None = None) -> pd.DataFrame:
    """One row per evaluation exercise segment from frozen window_index."""
    wi = load_window_index()
    ev = wi[(wi["role"] == "evaluation") & (wi["usable"] == True)].copy()  # noqa: E712
    if exercises is not None:
        ev = ev[ev["exercise_id"].isin(exercises)]
    g = (
        ev.groupby(
            ["participant", "timepoint", "repetition", "exercise_id", "recording_id", "block_id"],
            as_index=False,
        )
        .agg(start_frame=("start_frame", "min"), end_frame=("end_frame", "max"), n_windows=("window_id", "count"))
    )
    g["participant"] = g["participant"].astype(str)
    g["duration_s"] = (g["end_frame"] - g["start_frame"]) / 120.0
    g["segment_id"] = (
        g["participant"].astype(str)
        + "_T"
        + g["timepoint"].astype(str)
        + "_R"
        + g["repetition"].astype(str)
        + "_ex"
        + g["exercise_id"].astype(int).map(lambda x: f"{x:02d}")
    )
    return g.sort_values(["participant", "timepoint", "repetition", "exercise_id"]).reset_index(drop=True)
