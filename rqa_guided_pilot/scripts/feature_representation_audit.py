#!/usr/bin/env python3
"""Source-data / feature-representation audit (T1-only).

Read-only vs frozen inputs. Writes under rqa_guided_pilot/outputs/feature_audit/.
Does not retune Stage 1 locks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(REPO / "src"))

from rqa_pilot.ami_fnn import (  # noqa: E402
    average_mutual_information,
    choose_m_from_fnn,
    false_nearest_neighbors,
    first_local_minimum,
)
from rqa_pilot.io_readonly import build_segment_index, load_link_config, load_rotvec  # noqa: E402
from rqa_pilot.rqa_core import auto_rqa  # noqa: E402
from rqa_pilot.signals import downsample, finite_clean, link_speed_deg_s  # noqa: E402
from rqa_pilot.surrogates import full_shuffle  # noqa: E402

OUT = ROOT / "outputs" / "feature_audit"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / "cache" / "feature_audit_positions"
CACHE.mkdir(parents=True, exist_ok=True)

FPS = 120.0
TAU = 18
M = 4
LMIN = 2
THEILER = 18
RADIUS = 0.35
BLOCK = 36

JCVPCA = REPO.parent / "gaga_jcvpca"
MANIFEST = REPO / "data" / "immutable" / "INPUT_MANIFEST.json"


def geodesic_speed_deg_s(rotvec: np.ndarray, fps: float) -> np.ndarray:
    """(T,L,3) → (T-1,L) SO(3) geodesic angular speed in deg/s from consecutive rotvecs."""
    t, l, _ = rotvec.shape
    out = np.full((t - 1, l), np.nan, dtype=np.float64)
    for li in range(l):
        r = rotvec[:, li, :]
        ok = np.isfinite(r).all(axis=1)
        # process contiguous finite runs
        if ok.sum() < 2:
            continue
        # vectorized where both frames finite
        both = ok[:-1] & ok[1:]
        if not both.any():
            continue
        idx = np.where(both)[0]
        # batch convert
        r0 = r[idx]
        r1 = r[idx + 1]
        R0 = Rotation.from_rotvec(r0)
        R1 = Rotation.from_rotvec(r1)
        ang = (R0.inv() * R1).magnitude()  # [0, π]
        out[idx, li] = np.degrees(ang) * fps
    return out


def rel_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-9)
    return np.abs(a - b) / denom


def summarize_diff(a: np.ndarray, b: np.ndarray) -> dict:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 10:
        return {"n": int(mask.sum())}
    da = np.abs(a[mask] - b[mask])
    rd = rel_diff(a[mask], b[mask])
    # exclude pathological: when both near zero, relative blows up — report abs always
    return {
        "n": int(mask.sum()),
        "median_abs_deg_s": float(np.median(da)),
        "p95_abs_deg_s": float(np.quantile(da, 0.95)),
        "p99_abs_deg_s": float(np.quantile(da, 0.99)),
        "max_abs_deg_s": float(da.max()),
        "median_rel": float(np.median(rd)),
        "p95_rel": float(np.quantile(rd, 0.95)),
        "p99_rel": float(np.quantile(rd, 0.99)),
        "median_a": float(np.median(a[mask])),
        "median_b": float(np.median(b[mask])),
        "corr": float(np.corrcoef(a[mask], b[mask])[0, 1]),
    }


def run_a1_a2_math():
    link_ids, regions = load_link_config()
    segs = build_segment_index([9, 10, 11, 12, 13])
    segs = segs[(segs["timepoint"] == 1) & (segs["participant"].isin(["252", "651", "671", "790"]))]
    per_link = {lid: {"abs": [], "rel": [], "a": [], "b": []} for lid in link_ids}
    boundary_abs = []
    interior_abs = []
    ds_rows = []
    all_a, all_b = [], []

    for rec in segs.itertuples(index=False):
        rv = load_rotvec(rec.recording_id)[int(rec.start_frame) : int(rec.end_frame)]
        if rv.shape[0] < 10:
            continue
        a1 = link_speed_deg_s(rv, FPS)
        a2 = geodesic_speed_deg_s(rv, FPS)
        for li, lid in enumerate(link_ids):
            s = summarize_diff(a1[:, li], a2[:, li])
            if s.get("n", 0) < 10:
                continue
            mask = np.isfinite(a1[:, li]) & np.isfinite(a2[:, li])
            da = np.abs(a1[mask, li] - a2[mask, li])
            rd = rel_diff(a1[mask, li], a2[mask, li])
            per_link[lid]["abs"].append(da)
            per_link[lid]["rel"].append(rd)
            per_link[lid]["a"].append(a1[mask, li])
            per_link[lid]["b"].append(a2[mask, li])
            all_a.append(a1[mask, li])
            all_b.append(a2[mask, li])
            # boundary: first/last 12 frames of segment speed series
            n = da.size
            if n > 40:
                bmask = np.zeros(n, dtype=bool)
                bmask[:12] = True
                bmask[-12:] = True
                boundary_abs.append(da[bmask])
                interior_abs.append(da[~bmask])
        # downsample effect on agreement (region trunk)
        idx = [i for i, lid in enumerate(link_ids) if regions[lid] == "trunk_spine"]
        s1 = np.nanmean(a1[:, idx], axis=1)
        s2 = np.nanmean(a2[:, idx], axis=1)
        for rate in (120, 60, 30):
            d1 = downsample(s1, FPS, rate)
            d2 = downsample(s2, FPS, rate)
            ds_rows.append(
                {
                    "recording_id": rec.recording_id,
                    "segment_id": rec.segment_id,
                    "rate": rate,
                    **{f"k_{k}": v for k, v in summarize_diff(d1, d2).items()},
                }
            )

    link_summary = {}
    for lid, d in per_link.items():
        if not d["abs"]:
            continue
        abs_all = np.concatenate(d["abs"])
        rel_all = np.concatenate(d["rel"])
        a_all = np.concatenate(d["a"])
        b_all = np.concatenate(d["b"])
        link_summary[lid] = {
            "region": regions[lid],
            "n": int(abs_all.size),
            "median_abs_deg_s": float(np.median(abs_all)),
            "p95_abs_deg_s": float(np.quantile(abs_all, 0.95)),
            "p99_abs_deg_s": float(np.quantile(abs_all, 0.99)),
            "max_abs_deg_s": float(abs_all.max()),
            "median_rel": float(np.median(rel_all)),
            "p99_rel": float(np.quantile(rel_all, 0.99)),
            "corr": float(np.corrcoef(a_all, b_all)[0, 1]),
            "median_speed_a1": float(np.median(a_all)),
        }

    aa = np.concatenate(all_a)
    bb = np.concatenate(all_b)
    overall = summarize_diff(aa, bb)
    # largest discrepancy links
    worst = sorted(link_summary.items(), key=lambda kv: kv[1]["p99_abs_deg_s"], reverse=True)[:5]

    # near-π frames in filtered rotvec (wrapping risk)
    near_pi = {}
    for pid in ["252", "651", "671", "790"]:
        for r in [1, 2]:
            rid = f"{pid}_T1_P1_R{r}"
            rv = load_rotvec(rid)
            ang = np.linalg.norm(rv, axis=2)
            near_pi[rid] = {
                "frac_angle_gt_0_9pi": float(np.nanmean(ang > 0.9 * np.pi)),
                "max_angle_rad": float(np.nanmax(ang)),
                "frac_step_gt_0_5rad": float(
                    np.nanmean(np.linalg.norm(np.diff(rv, axis=0), axis=2) > 0.5)
                ),
            }

    return {
        "overall": overall,
        "per_link": link_summary,
        "worst_links_by_p99_abs": [{k: v} for k, v in worst],
        "boundary_vs_interior": {
            "boundary_median_abs": float(np.median(np.concatenate(boundary_abs))) if boundary_abs else None,
            "interior_median_abs": float(np.median(np.concatenate(interior_abs))) if interior_abs else None,
            "boundary_p99_abs": float(np.quantile(np.concatenate(boundary_abs), 0.99)) if boundary_abs else None,
            "interior_p99_abs": float(np.quantile(np.concatenate(interior_abs), 0.99)) if interior_abs else None,
        },
        "downsample_agreement_trunk": {
            str(rate): {
                "median_of_median_abs": float(
                    np.median([r[f"k_median_abs_deg_s"] for r in ds_rows if r["rate"] == rate and f"k_median_abs_deg_s" in r])
                ),
                "median_corr": float(
                    np.median([r["k_corr"] for r in ds_rows if r["rate"] == rate and "k_corr" in r])
                ),
            }
            for rate in (120, 60, 30)
        },
        "near_pi_diagnostics_T1": near_pi,
        "n_segments": int(len(segs)),
    }


def run_a1_a2_rqa():
    link_ids, regions = load_link_config()
    segs = build_segment_index([11, 13])
    segs = segs[
        (segs["timepoint"] == 1)
        & (segs["participant"].isin(["252", "651", "671", "790"]))
    ]
    regions_use = ["trunk_spine", "left_arm", "right_arm"]
    rows = []
    for rec in segs.itertuples(index=False):
        rv_full = load_rotvec(rec.recording_id)[int(rec.start_frame) : int(rec.end_frame)]
        if rv_full.shape[0] < 200:
            continue
        a1_all = link_speed_deg_s(rv_full, FPS)
        a2_all = geodesic_speed_deg_s(rv_full, FPS)
        for region in regions_use:
            idx = [i for i, lid in enumerate(link_ids) if regions[lid] == region]
            for label, speeds in (("A1_rotvec_fd", a1_all), ("A2_geodesic", a2_all)):
                series = finite_clean(np.nanmean(speeds[:, idx], axis=1))
                if series.size < 200:
                    continue
                ami = average_mutual_information(series, max_tau=60)
                tau_hat = first_local_minimum(ami)
                fnn = false_nearest_neighbors(series, tau=TAU, max_m=8)
                m_hat = choose_m_from_fnn(fnn)
                q = auto_rqa(
                    series,
                    tau=TAU,
                    m=M,
                    theiler=THEILER,
                    lmin=LMIN,
                    mode="fixed_mean_rescaled",
                    radius_frac=RADIUS,
                )
                sh = full_shuffle(series, np.random.default_rng(0))
                qs = auto_rqa(
                    sh,
                    tau=TAU,
                    m=M,
                    theiler=THEILER,
                    lmin=LMIN,
                    mode="fixed_mean_rescaled",
                    radius_frac=RADIUS,
                )
                rows.append(
                    {
                        "feature": label,
                        "segment_id": rec.segment_id,
                        "participant": rec.participant,
                        "repetition": int(rec.repetition),
                        "exercise_id": int(rec.exercise_id),
                        "region": region,
                        "ami_tau": tau_hat,
                        "fnn_m": m_hat,
                        "RR": q["RR"],
                        "DET": q["DET"],
                        "Lmean": q["Lmean"],
                        "LAM": q["LAM"],
                        "ENTR": q["ENTR"],
                        "DET_shuffle": qs["DET"],
                        "DET_drop": (q["DET"] - qs["DET"]) if np.isfinite(q["DET"]) and np.isfinite(qs["DET"]) else np.nan,
                        "n": series.size,
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "a1_a2_rqa_cells.csv", index=False)

    # R1/R2 drep for A1 vs A2
    drep_rows = []
    for (pid, ex, region, feat), g in df.groupby(["participant", "exercise_id", "region", "feature"]):
        r1 = g[g["repetition"] == 1]
        r2 = g[g["repetition"] == 2]
        if r1.empty or r2.empty:
            continue
        for met in ("DET", "LAM", "Lmean", "RR"):
            v1, v2 = float(r1.iloc[0][met]), float(r2.iloc[0][met])
            drep_rows.append(
                {
                    "feature": feat,
                    "participant": pid,
                    "exercise_id": ex,
                    "region": region,
                    "metric": met,
                    "abs_diff": abs(v1 - v2),
                    "mean": 0.5 * (v1 + v2),
                }
            )
    drep = pd.DataFrame(drep_rows)

    summary = {}
    for feat in ("A1_rotvec_fd", "A2_geodesic"):
        sub = df[df["feature"] == feat]
        summary[feat] = {
            "median_RR": float(sub["RR"].median()),
            "median_DET": float(sub["DET"].median()),
            "median_Lmean": float(sub["Lmean"].median()),
            "median_LAM": float(sub["LAM"].median()),
            "median_ENTR": float(sub["ENTR"].median()),
            "median_DET_drop_shuffle": float(sub["DET_drop"].median()),
            "median_ami_tau": float(sub["ami_tau"].dropna().median()) if sub["ami_tau"].notna().any() else None,
            "median_fnn_m": float(sub["fnn_m"].dropna().median()) if sub["fnn_m"].notna().any() else None,
            "n_cells": int(len(sub)),
        }
        if not drep.empty:
            for met in ("DET", "LAM", "Lmean"):
                summary[feat][f"median_R1R2_absdiff_{met}"] = float(
                    drep[(drep["feature"] == feat) & (drep["metric"] == met)]["abs_diff"].median()
                )

    # pairwise A1 vs A2 on matched cells
    piv = df.pivot_table(
        index=["segment_id", "region"],
        columns="feature",
        values=["RR", "DET", "Lmean", "LAM", "ENTR", "DET_drop"],
        aggfunc="first",
    )
    pairwise = {}
    for met in ("RR", "DET", "Lmean", "LAM", "ENTR", "DET_drop"):
        if (met, "A1_rotvec_fd") not in piv.columns:
            continue
        a = piv[(met, "A1_rotvec_fd")].to_numpy(dtype=float)
        b = piv[(met, "A2_geodesic")].to_numpy(dtype=float)
        mask = np.isfinite(a) & np.isfinite(b)
        pairwise[met] = {
            "median_abs_diff": float(np.median(np.abs(a[mask] - b[mask]))),
            "median_rel_diff": float(np.median(rel_diff(a[mask], b[mask]))),
            "corr": float(np.corrcoef(a[mask], b[mask])[0, 1]) if mask.sum() > 3 else None,
            "n": int(mask.sum()),
        }
    return {"summary": summary, "pairwise_A1_vs_A2": pairwise}


# ---------- positional candidates ----------

def _load_manifest_t1():
    man = json.loads(MANIFEST.read_text())
    return [r for r in man["recordings"] if r["timepoint"] == 1]


def _bone_token(name: str) -> str:
    # "651:LHand" -> "LHand"; root "651:651" -> full
    if ":" in name:
        return name.split(":", 1)[1]
    return name


def read_selected_bone_positions(source_path: Path, tokens: list[str]) -> dict:
    """Read selected bone XYZ positions from Motive CSV. Returns meters + meta."""
    import csv

    from gaga_shared6d.motive_io import _find_row, _read_header_rows, read_header

    cache_key = CACHE / f"{source_path.stem}_pos.npz"
    header = read_header(source_path)
    units = header.length_units
    root = header.root_bone()
    name_by_token: dict[str, str] = {}
    for bn in header.bone_names:
        name_by_token[_bone_token(bn)] = bn
        name_by_token[bn] = bn
    name_by_token["pelvis"] = root
    name_by_token["root"] = root

    wanted_full = []
    for t in tokens:
        if t not in name_by_token:
            raise KeyError(
                f"{t} not in {source_path.name}; have "
                f"{[_bone_token(b) for b in header.bone_names[:20]]}..."
            )
        wanted_full.append(name_by_token[t])

    if cache_key.exists():
        z = np.load(cache_key, allow_pickle=True)
        if str(z["units"]) == units and list(z["bones"]) == wanted_full:
            return {
                "positions_m": z["positions_m"],
                "bones": list(z["bones"]),
                "units": units,
                "root": root,
                "fps": float(header.capture_frame_rate),
            }

    rows = _read_header_rows(source_path, max_rows=12)
    type_idx = _find_row(rows, 1, "Type")
    frame_idx = _find_row(rows, 0, "Frame")
    # Rotation/Position kind row is immediately above the Frame row
    kind_row = rows[frame_idx - 1]
    type_row = rows[type_idx]
    name_row = rows[type_idx + 1]
    axis_row = rows[frame_idx]

    # For each bone, collect Position X/Y/Z (second XYZ block after Rotation XYZW)
    pos_cols: dict[str, dict[str, int]] = {bn: {} for bn in wanted_full}
    for col, typ in enumerate(type_row):
        if typ.strip() != "Bone":
            continue
        bn = name_row[col].strip() if col < len(name_row) else ""
        if bn not in pos_cols:
            continue
        kind = kind_row[col].strip() if col < len(kind_row) else ""
        ax = axis_row[col].strip() if col < len(axis_row) else ""
        if kind == "Position" and ax in ("X", "Y", "Z"):
            pos_cols[bn][ax] = col

    usecols: list[int] = []
    for bn in wanted_full:
        if set(pos_cols[bn]) != {"X", "Y", "Z"}:
            raise RuntimeError(f"Missing position axes for {bn}: {pos_cols[bn]}")
        for ax in ("X", "Y", "Z"):
            usecols.append(pos_cols[bn][ax])

    df = pd.read_csv(
        source_path,
        skiprows=frame_idx + 1,
        header=None,
        usecols=sorted(set(usecols)),
        low_memory=False,
    )
    colmap = {c: i for i, c in enumerate(sorted(set(usecols)))}
    T = len(df)
    pos = np.full((T, len(wanted_full), 3), np.nan, dtype=np.float64)
    for bi, bn in enumerate(wanted_full):
        for ai, ax in enumerate(("X", "Y", "Z")):
            pos[:, bi, ai] = pd.to_numeric(
                df.iloc[:, colmap[pos_cols[bn][ax]]], errors="coerce"
            ).to_numpy(dtype=np.float64)

    u = units.strip().lower()
    if u.startswith("millimeter"):
        pos_m = pos / 1000.0
    elif u.startswith("meter"):
        pos_m = pos.copy()
    else:
        raise ValueError(f"Unknown Length Units: {units}")

    np.savez_compressed(
        cache_key,
        positions_m=pos_m,
        bones=np.array(wanted_full, dtype=object),
        units=np.array(units),
    )
    return {
        "positions_m": pos_m,
        "bones": wanted_full,
        "units": units,
        "root": root,
        "fps": float(header.capture_frame_rate),
    }


def run_positional_t1():
    """B1 global and B2 root-relative positional speed vs A1 angular."""
    tokens = ["pelvis", "Chest", "LHand", "RHand", "LFoot", "RFoot", "Ab"]
    channel_defs = {
        "root_global": ("pelvis", "global"),
        "chest_global": ("Chest", "global"),
        "LHand_global": ("LHand", "global"),
        "RHand_global": ("RHand", "global"),
        "LHand_rootrel": ("LHand", "rootrel"),
        "RHand_rootrel": ("RHand", "rootrel"),
        "LFoot_rootrel": ("LFoot", "rootrel"),
        "RFoot_rootrel": ("RFoot", "rootrel"),
        "Chest_rootrel": ("Chest", "rootrel"),
    }
    man = _load_manifest_t1()
    segs = build_segment_index([9, 10, 11, 12, 13])
    segs = segs[(segs["timepoint"] == 1)]
    link_ids, regions = load_link_config()

    metric_rows = []
    amp_rows = []
    corr_rows = []

    for rec_meta in man:
        rid = rec_meta["recording_id"]
        src = (JCVPCA / "data" / "raw_skeleton" / rec_meta["participant"] / rec_meta["source_file"]).resolve()
        if not src.exists():
            # try path from manifest relative
            src = (REPO / rec_meta["source_path"]).resolve()
        print(f"[pos] loading {rid} from {src.name} ...", flush=True)
        data = read_selected_bone_positions(src, tokens)
        bones = data["bones"]
        pos = data["positions_m"]
        bindex = { _bone_token(b) if _bone_token(b) != b.split(':')[-1] else _bone_token(b): i for i, b in enumerate(bones)}
        # fix index map
        bindex = {}
        for i, b in enumerate(bones):
            bindex[_bone_token(b)] = i
            if b == data["root"]:
                bindex["pelvis"] = i
                bindex["root"] = i

        root_i = bindex["pelvis"]
        root_pos = pos[:, root_i, :]
        # body-size proxy: mean distance hand-root over take
        lh = pos[:, bindex["LHand"], :] - root_pos
        rh = pos[:, bindex["RHand"], :] - root_pos
        size_proxy = float(np.nanmean(0.5 * (np.linalg.norm(lh, axis=1) + np.linalg.norm(rh, axis=1))))
        amp_rows.append(
            {
                "recording_id": rid,
                "participant": rec_meta["participant"],
                "repetition": rec_meta["repetition"],
                "length_units": rec_meta["length_units"],
                "skeleton_variant": rec_meta["skeleton_variant"],
                "size_proxy_m": size_proxy,
                "root_travel_m": float(np.nansum(np.linalg.norm(np.diff(root_pos, axis=0), axis=1))),
            }
        )

        sub = segs[segs["recording_id"] == rid]
        for rec in sub.itertuples(index=False):
            sl = slice(int(rec.start_frame), int(rec.end_frame))
            # A1 trunk / arms for correlation
            rv = load_rotvec(rid)[sl]
            a1 = link_speed_deg_s(rv, FPS)
            a1_trunk = np.nanmean(a1[:, [i for i, lid in enumerate(link_ids) if regions[lid] == "trunk_spine"]], axis=1)
            a1_larm = np.nanmean(a1[:, [i for i, lid in enumerate(link_ids) if regions[lid] == "left_arm"]], axis=1)
            a1_rarm = np.nanmean(a1[:, [i for i, lid in enumerate(link_ids) if regions[lid] == "right_arm"]], axis=1)

            root_seg = root_pos[sl]
            root_speed = np.linalg.norm(np.diff(root_seg, axis=0), axis=1) * FPS  # m/s

            series_map = {"A1_trunk": a1_trunk, "A1_left_arm": a1_larm, "A1_right_arm": a1_rarm, "B1_root": root_speed}
            for ch, (tok, mode) in channel_defs.items():
                p = pos[sl, bindex[tok if tok != "pelvis" else "pelvis"], :]
                if mode == "rootrel":
                    p = p - root_seg
                spd = np.linalg.norm(np.diff(p, axis=0), axis=1) * FPS
                series_map[ch] = spd

            # correlations / missingness
            # translation dominance: corr(hand_global, root)
            for hand in ("LHand_global", "RHand_global"):
                a, b = series_map[hand], series_map["B1_root"]
                m = np.isfinite(a) & np.isfinite(b)
                corr_rows.append(
                    {
                        "segment_id": rec.segment_id,
                        "pair": f"{hand}_vs_root",
                        "corr": float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 20 else None,
                        "median_hand": float(np.nanmedian(a)),
                        "median_root": float(np.nanmedian(b)),
                    }
                )
                # rootrel vs angular
                rr = hand.replace("global", "rootrel")
                a2, b2 = series_map[rr], series_map["A1_left_arm" if "L" in hand else "A1_right_arm"]
                m2 = np.isfinite(a2) & np.isfinite(b2)
                n = min(m2.sum(), a2.size, b2.size)
                corr_rows.append(
                    {
                        "segment_id": rec.segment_id,
                        "pair": f"{rr}_vs_A1_arm",
                        "corr": float(np.corrcoef(a2[m2], b2[m2])[0, 1]) if m2.sum() > 20 else None,
                        "median_hand": float(np.nanmedian(a2)),
                        "median_root": float(np.nanmedian(b2)),
                    }
                )

            # limited RQA on balanced subset: ex11/13 only
            if int(rec.exercise_id) not in (11, 13):
                continue
            for name in (
                "A1_trunk",
                "A1_left_arm",
                "B1_root",
                "LHand_global",
                "LHand_rootrel",
                "Chest_rootrel",
            ):
                series = finite_clean(series_map[name])
                if series.size < 200:
                    continue
                q = auto_rqa(
                    series,
                    tau=TAU,
                    m=M,
                    theiler=THEILER,
                    lmin=LMIN,
                    mode="fixed_mean_rescaled",
                    radius_frac=RADIUS,
                )
                sh = full_shuffle(series, np.random.default_rng(1))
                qs = auto_rqa(
                    sh,
                    tau=TAU,
                    m=M,
                    theiler=THEILER,
                    lmin=LMIN,
                    mode="fixed_mean_rescaled",
                    radius_frac=RADIUS,
                )
                metric_rows.append(
                    {
                        "feature": name,
                        "segment_id": rec.segment_id,
                        "participant": rec.participant,
                        "repetition": int(rec.repetition),
                        "exercise_id": int(rec.exercise_id),
                        "RR": q["RR"],
                        "DET": q["DET"],
                        "Lmean": q["Lmean"],
                        "LAM": q["LAM"],
                        "ENTR": q["ENTR"],
                        "DET_drop": (q["DET"] - qs["DET"]) if np.isfinite(q["DET"]) and np.isfinite(qs["DET"]) else np.nan,
                        "median_amp": float(np.nanmedian(series)),
                        "n": int(series.size),
                        "missing_frac_pre_clean": float(np.mean(~np.isfinite(series_map[name]))),
                    }
                )

    pd.DataFrame(metric_rows).to_csv(OUT / "positional_rqa_cells.csv", index=False)
    pd.DataFrame(corr_rows).to_csv(OUT / "positional_correlations.csv", index=False)
    # amp_rows has mixed — filter recording-level
    amp_df = pd.DataFrame([r for r in amp_rows if "size_proxy_m" in r])
    amp_df.to_csv(OUT / "positional_amplitude_by_recording.csv", index=False)

    mdf = pd.DataFrame(metric_rows)
    cdf = pd.DataFrame(corr_rows)
    summary = {"by_feature": {}, "translation_dominance": {}, "size_spread": {}}
    for feat, g in mdf.groupby("feature"):
        summary["by_feature"][feat] = {
            "median_RR": float(g["RR"].median()),
            "median_DET": float(g["DET"].median()),
            "median_Lmean": float(g["Lmean"].median()),
            "median_DET_drop": float(g["DET_drop"].median()),
            "median_amp": float(g["median_amp"].median()),
            "n": int(len(g)),
        }
        # R1/R2
        diffs = []
        for (pid, ex), gg in g.groupby(["participant", "exercise_id"]):
            r1, r2 = gg[gg["repetition"] == 1], gg[gg["repetition"] == 2]
            if len(r1) and len(r2):
                diffs.append(abs(float(r1.iloc[0]["DET"]) - float(r2.iloc[0]["DET"])))
        summary["by_feature"][feat]["median_R1R2_absdiff_DET"] = float(np.median(diffs)) if diffs else None

    for pair, g in cdf.groupby("pair"):
        vals = g["corr"].dropna().to_numpy(dtype=float)
        summary["translation_dominance"][pair] = {
            "median_corr": float(np.median(vals)) if vals.size else None,
            "n": int(vals.size),
        }
    if len(amp_df):
        summary["size_spread"] = {
            "size_proxy_by_participant": {
                str(pid): float(g["size_proxy_m"].mean()) for pid, g in amp_df.groupby("participant")
            },
            "root_travel_by_participant_m": {
                str(pid): float(g["root_travel_m"].mean()) for pid, g in amp_df.groupby("participant")
            },
            "cv_size_proxy": float(amp_df.groupby("participant")["size_proxy_m"].mean().std()
                                   / amp_df.groupby("participant")["size_proxy_m"].mean().mean()),
        }
    return summary


def region_link_counts():
    link_ids, regions = load_link_config()
    counts = {}
    for lid in link_ids:
        counts.setdefault(regions[lid], 0)
        counts[regions[lid]] += 1
    return counts


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-a1a2", action="store_true", help="Reuse existing A1/A2 JSON outputs")
    ap.add_argument("--skip-positional", action="store_true")
    args = ap.parse_args()

    if not args.skip_a1a2:
        print("=== A1 vs A2 mathematics ===", flush=True)
        math = run_a1_a2_math()
        (OUT / "a1_a2_math.json").write_text(json.dumps(math, indent=2))
        print(json.dumps(math["overall"], indent=2), flush=True)

        print("=== A1 vs A2 limited RQA ===", flush=True)
        rqa = run_a1_a2_rqa()
        (OUT / "a1_a2_rqa_summary.json").write_text(json.dumps(rqa, indent=2))
        print(json.dumps(rqa["pairwise_A1_vs_A2"], indent=2), flush=True)

    if not args.skip_positional:
        print("=== Positional B1/B2 T1 ===", flush=True)
        pos = run_positional_t1()
        (OUT / "positional_summary.json").write_text(json.dumps(pos, indent=2))
        print(json.dumps(pos, indent=2)[:3000], flush=True)

    meta = {
        "region_link_counts": region_link_counts(),
        "locked_params_used_for_diagnostics_only": {
            "tau": TAU,
            "m": M,
            "radius_frac": RADIUS,
            "theiler": THEILER,
            "note": "Angular-speed locks applied to positional candidates only for comparative diagnostics; not proposed as positional locks.",
        },
    }
    (OUT / "audit_meta.json").write_text(json.dumps(meta, indent=2))
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
