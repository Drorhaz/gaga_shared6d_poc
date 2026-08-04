#!/usr/bin/env python3
"""S8 — Cross-participant direction similarity (Conv primary).

Reliability-qualified change vectors only. Co-primary raw and standardized
geometry. Exact participant-level sign-flip reference. Jackknife influence.
Stops with a readiness gate before S9/S10.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, models, provenance, train_masked  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OBJ = "masked_angular_velocity"
DIM = 32
DELTAS = ("D12", "D13", "D23")
GEOMS = ("raw", "std")


def ecols(prefix: str = "e") -> list[str]:
    return [f"{prefix}{i}" for i in range(DIM)]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def pairwise_cosines(vecs: dict[str, np.ndarray]) -> dict:
    pids = sorted(vecs.keys())
    pairs, mats = {}, {}
    for i, a in enumerate(pids):
        for b in pids[i + 1:]:
            c = cosine(vecs[a], vecs[b])
            pairs[f"{a}-{b}"] = c
            mats[(a, b)] = mats[(b, a)] = c
    for p in pids:
        mats[(p, p)] = 1.0
    vals = np.array(list(pairs.values()), dtype=float)
    vals = vals[np.isfinite(vals)]
    return {
        "participants": pids,
        "n_participants": len(pids),
        "pairwise": pairs,
        "matrix": mats,
        "mean_pairwise": float(vals.mean()) if len(vals) else float("nan"),
        "median_pairwise": float(np.median(vals)) if len(vals) else float("nan"),
        "min_pairwise": float(vals.min()) if len(vals) else float("nan"),
        "max_pairwise": float(vals.max()) if len(vals) else float("nan"),
        "n_pairs": int(len(vals)),
        "n_positive_pairs": int((vals > 0).sum()) if len(vals) else 0,
        "frac_positive_pairs": float((vals > 0).mean()) if len(vals) else float("nan"),
    }


def consensus_and_projections(vecs: dict[str, np.ndarray]) -> dict:
    pids = sorted(vecs.keys())
    units = []
    for p in pids:
        v = vecs[p]
        n = np.linalg.norm(v)
        units.append(v / n if n > 1e-12 else v)
    cons = np.mean(np.stack(units, axis=0), axis=0)
    cn = np.linalg.norm(cons)
    if cn > 1e-12:
        cons = cons / cn
    projs = {p: cosine(vecs[p], cons) for p in pids}
    return {"consensus": cons, "projections": projs}


def sign_flip_reference(vecs: dict[str, np.ndarray]) -> dict:
    pids = sorted(vecs.keys())
    n = len(pids)
    if n < 2:
        return {"n_participants": n, "insufficient": True}
    others = pids[1:]
    observed = pairwise_cosines(vecs)["mean_pairwise"]
    null_vals = []
    for signs in itertools.product([-1, 1], repeat=len(others)):
        flipped = {pids[0]: vecs[pids[0]]}
        for p, s in zip(others, signs):
            flipped[p] = s * vecs[p]
        null_vals.append(pairwise_cosines(flipped)["mean_pairwise"])
    null_vals = np.asarray(null_vals, dtype=float)
    uniq = np.unique(np.round(null_vals, decimals=12))
    n_unique = len(uniq)
    n_ge = int(np.sum(uniq >= observed - 1e-12))
    n_ge_all = int(np.sum(null_vals >= observed - 1e-12))
    rank = int(np.sum(uniq > observed + 1e-12)) + 1
    return {
        "n_participants": n,
        "n_sign_patterns_enumerated": int(2 ** (n - 1)),
        "n_unique_mean_cosine": n_unique,
        "min_attainable_p": 1.0 / n_unique if n_unique else float("nan"),
        "observed_mean_pairwise": float(observed),
        "null_mean_cosines": null_vals.tolist(),
        "unique_mean_cosines": uniq.tolist(),
        "n_unique_ge_observed": n_ge,
        "exact_tail_p_unique": float(n_ge / n_unique) if n_unique else float("nan"),
        "n_patterns_ge_observed": n_ge_all,
        "exact_tail_p_patterns": float(n_ge_all / len(null_vals)) if len(null_vals) else float("nan"),
        "observed_rank_among_unique_desc": rank,
        "insufficient": False,
    }


def jackknife(vecs: dict[str, np.ndarray]) -> list[dict]:
    pids = sorted(vecs.keys())
    full = pairwise_cosines(vecs)["mean_pairwise"]
    rows = []
    for leave in pids:
        sub = {p: v for p, v in vecs.items() if p != leave}
        if len(sub) < 2:
            continue
        m = pairwise_cosines(sub)["mean_pairwise"]
        rows.append({
            "left_out": leave,
            "n_remaining": len(sub),
            "mean_pairwise": m,
            "delta_from_full": m - full,
            "sign_flips_vs_full": bool(
                np.isfinite(m) and np.isfinite(full) and (m > 0) != (full > 0)
            ),
        })
    return rows


def load_change_vectors(change: pd.DataFrame, mag: pd.DataFrame) -> dict:
    out: dict = {}
    for fold in change.fold.unique():
        out[fold] = {}
        for seed in sorted(change.seed.unique()):
            out[fold][int(seed)] = {}
            for delta in DELTAS:
                flag = f"interpretable_{delta}"
                valid = set(
                    mag[(mag.fold == fold) & (mag.seed == seed) & mag[flag]]
                    .participant.astype(str)
                )
                sub = change[
                    (change.fold == fold) & (change.seed == seed)
                    & (change.delta == delta)
                    & (change.participant.astype(str).isin(valid))
                ]
                out[fold][int(seed)][delta] = {"raw": {}, "std": {}}
                for _, row in sub.iterrows():
                    pid = str(row.participant)
                    out[fold][int(seed)][delta]["raw"][pid] = row[ecols("e")].to_numpy(float)
                    out[fold][int(seed)][delta]["std"][pid] = row[ecols("std_e")].to_numpy(float)
    return out


def classify_participant(mag_row: pd.Series, delta: str) -> str:
    flag = mag_row[f"interpretable_{delta}"]
    if not flag:
        return "excluded_endpoint_skill_fail"
    if delta == "D12":
        gates = [mag_row.gate_T1, mag_row.gate_T2]
        ratio = mag_row.ratio_D12_over_DrepT2_raw
    elif delta == "D13":
        gates = [mag_row.gate_T1, mag_row.gate_T3]
        ratio = mag_row.ratio_D13_over_DrepT3_raw
    else:
        gates = [mag_row.gate_T2, mag_row.gate_T3]
        dmax = mag_row.Drep_max_T2T3_raw
        ratio = mag_row.norm_D23_raw / dmax if dmax and dmax > 0 else np.nan
    if any(g == "positive_degraded" for g in gates):
        if np.isfinite(ratio) and ratio > 1.0:
            return "reliable_degraded_but_change_gt_rep"
        return "reliable_but_degraded_representation"
    if np.isfinite(ratio) and ratio > 1.0:
        return "reliable_direction_change_gt_repetition"
    return "reliable_direction_change_le_repetition"


def ex11_change_vectors(rec: pd.DataFrame, mag: pd.DataFrame, cfg) -> dict:
    cols_raw = [f"ex11_e{i}" for i in range(DIM)]
    cols_std = [f"std_ex11_e{i}" for i in range(DIM)]
    if cols_std[0] not in rec.columns:
        cols_std = [f"std_{c}" for c in cols_raw]
    out = {}
    for fold in cfg["folds"]:
        traj = int(cfg["folds"][fold]["trajectory_repetition"])
        out[fold] = {}
        for seed in cfg["model"]["seeds"]:
            out[fold][int(seed)] = {d: {"raw": {}, "std": {}} for d in DELTAS}
            sub = rec[(rec.fold == fold) & (rec.seed == seed) & (rec.objective == OBJ)]
            for pid in cfg["participants"]:
                g = sub[sub.participant.astype(str) == str(pid)]
                z, zs = {}, {}
                ok = True
                for tp in (1, 2, 3):
                    row = g[(g.timepoint == tp) & (g.repetition == traj)]
                    if len(row) != 1 or row.iloc[0][cols_raw].isna().any():
                        ok = False
                        break
                    z[tp] = row.iloc[0][cols_raw].to_numpy(float)
                    zs[tp] = row.iloc[0][cols_std].to_numpy(float)
                if not ok:
                    continue
                deltas = {
                    "D12": (z[2] - z[1], zs[2] - zs[1]),
                    "D13": (z[3] - z[1], zs[3] - zs[1]),
                    "D23": (z[3] - z[2], zs[3] - zs[2]),
                }
                mrow = mag[
                    (mag.fold == fold) & (mag.seed == seed)
                    & (mag.participant.astype(str) == str(pid))
                ]
                if len(mrow) != 1:
                    continue
                mrow = mrow.iloc[0]
                for d, (vr, vs) in deltas.items():
                    if mrow[f"interpretable_{d}"]:
                        out[fold][int(seed)][d]["raw"][str(pid)] = vr
                        out[fold][int(seed)][d]["std"][str(pid)] = vs
    return out


def run_direction_block(vecs_nested, mag: pd.DataFrame, label: str = "primary"):
    sim_rows, pair_rows, flip_rows, jack_rows, proj_rows, class_rows = (
        [], [], [], [], [], [],
    )
    all_pids = ["252", "651", "671", "790"]
    for fold, seeds in vecs_nested.items():
        for seed, deltas in seeds.items():
            for delta in DELTAS:
                for geom in GEOMS:
                    vecs = deltas[delta][geom]
                    pids = sorted(vecs.keys())
                    excluded = [p for p in all_pids if p not in pids]
                    base = {
                        "analysis": label, "fold": fold, "seed": int(seed),
                        "delta": delta, "geometry": geom,
                        "n_participants": len(pids),
                        "participants_included": ",".join(pids),
                        "participants_excluded": ",".join(excluded),
                        "sufficient_for_group": len(pids) >= 3,
                    }
                    if len(pids) < 2:
                        sim_rows.append({**base, "status": "no_pairs"})
                        continue
                    pw = pairwise_cosines(vecs)
                    for k, v in pw["pairwise"].items():
                        pair_rows.append({**base, "pair": k, "cosine": v})
                    row = {
                        **base,
                        "status": "ok" if len(pids) >= 3 else "descriptive_only_lt3",
                        "mean_pairwise": pw["mean_pairwise"],
                        "median_pairwise": pw["median_pairwise"],
                        "min_pairwise": pw["min_pairwise"],
                        "max_pairwise": pw["max_pairwise"],
                        "n_pairs": pw["n_pairs"],
                        "n_positive_pairs": pw["n_positive_pairs"],
                        "frac_positive_pairs": pw["frac_positive_pairs"],
                    }
                    if len(pids) >= 3:
                        cons = consensus_and_projections(vecs)
                        for p, c in cons["projections"].items():
                            proj_rows.append({**base, "participant": p, "cos_to_consensus": c})
                        flip = sign_flip_reference(vecs)
                        flip_rows.append({**base, **{
                            k: flip[k] for k in flip
                            if k not in ("null_mean_cosines", "unique_mean_cosines")
                        }})
                        flip_rows[-1]["_null_json"] = json.dumps(flip["null_mean_cosines"])
                        for jk in jackknife(vecs):
                            jack_rows.append({**base, **jk})
                    sim_rows.append(row)
                    for pid in all_pids:
                        mrow = mag[
                            (mag.fold == fold) & (mag.seed == seed)
                            & (mag.participant.astype(str) == pid)
                        ]
                        if len(mrow) != 1:
                            continue
                        mrow = mrow.iloc[0]
                        class_rows.append({
                            "analysis": label, "fold": fold, "seed": int(seed),
                            "delta": delta, "geometry": geom, "participant": pid,
                            "included": pid in pids,
                            "class": classify_participant(mrow, delta),
                            "skill_T1": mrow.skill_T1, "skill_T2": mrow.skill_T2,
                            "skill_T3": mrow.skill_T3,
                            "norm_delta_raw": mrow[f"norm_{delta}_raw"],
                            "Drep_T2_raw": mrow.Drep_T2_raw, "Drep_T3_raw": mrow.Drep_T3_raw,
                            "ratio_vs_rep": (
                                mrow.ratio_D12_over_DrepT2_raw if delta == "D12"
                                else mrow.ratio_D13_over_DrepT3_raw if delta == "D13"
                                else (mrow.norm_D23_raw / mrow.Drep_max_T2T3_raw
                                      if mrow.Drep_max_T2T3_raw > 0 else np.nan)
                            ),
                        })
    return (
        pd.DataFrame(sim_rows), pd.DataFrame(pair_rows), pd.DataFrame(flip_rows),
        pd.DataFrame(jack_rows), pd.DataFrame(proj_rows), pd.DataFrame(class_rows),
    )


def plot_cosine_matrices(pair_df, sim_df, fig_dir):
    for delta in DELTAS:
        for geom in GEOMS:
            sub_sim = sim_df[
                (sim_df.delta == delta) & (sim_df.geometry == geom) & (sim_df.sufficient_for_group)
            ]
            if sub_sim.empty:
                continue
            pref = sub_sim[(sub_sim.fold == "A") & (sub_sim.seed == 0)]
            row = pref.iloc[0] if len(pref) else sub_sim.iloc[0]
            pairs = pair_df[
                (pair_df.fold == row.fold) & (pair_df.seed == row.seed)
                & (pair_df.delta == delta) & (pair_df.geometry == geom)
            ]
            pids = row.participants_included.split(",")
            n = len(pids)
            M = np.eye(n)
            for _, pr in pairs.iterrows():
                a, b = pr.pair.split("-")
                if a in pids and b in pids:
                    i, j = pids.index(a), pids.index(b)
                    M[i, j] = M[j, i] = pr.cosine
            fig, ax = plt.subplots(figsize=(4.5, 4))
            im = ax.imshow(M, vmin=-1, vmax=1, cmap="coolwarm")
            ax.set_xticks(range(n)); ax.set_yticks(range(n))
            ax.set_xticklabels(pids); ax.set_yticklabels(pids)
            for i in range(n):
                for j in range(n):
                    ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=8)
            ax.set_title(
                f"{delta} {geom} · fold {row.fold} seed {row.seed}\n"
                f"included={row.participants_included} excl={row.participants_excluded}"
            )
            fig.colorbar(im, ax=ax, fraction=0.046)
            fig.tight_layout()
            fig.savefig(fig_dir / f"cosine_matrix_{delta}_{geom}_f{row.fold}_s{row.seed}.png", dpi=140)
            plt.close(fig)


def plot_stability(sim_df, fig_dir):
    sub = sim_df[sim_df.sufficient_for_group]
    if sub.empty:
        return
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, delta in zip(axes, DELTAS):
        for geom, marker in (("raw", "o"), ("std", "s")):
            g = sub[(sub.delta == delta) & (sub.geometry == geom)]
            x = [f"{r.fold}{r.seed}" for r in g.itertuples()]
            ax.scatter(x, g.mean_pairwise, marker=marker, label=geom, s=50)
        ax.axhline(0, color="grey", ls=":")
        ax.set_title(delta)
        ax.set_xlabel("fold-seed")
        ax.tick_params(axis="x", rotation=45)
    axes[0].set_ylabel("mean pairwise cosine")
    axes[0].legend(fontsize=8)
    fig.suptitle("Direction similarity stability (n≥3 only)")
    fig.tight_layout()
    fig.savefig(fig_dir / "stability_mean_pairwise.png", dpi=150)
    plt.close(fig)


def plot_signflip(flip_df, fig_dir):
    sub = flip_df.dropna(subset=["observed_mean_pairwise"]) if len(flip_df) else flip_df
    if sub.empty:
        return
    shown = 0
    for _, row in sub.iterrows():
        if shown >= 6 or row.geometry != "raw":
            continue
        null = json.loads(row._null_json)
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.hist(null, bins=max(5, len(set(np.round(null, 4)))), color="C0", alpha=0.7)
        ax.axvline(row.observed_mean_pairwise, color="crimson", lw=2, label="observed")
        ax.set_xlabel("mean pairwise cosine under sign flip")
        ax.set_title(
            f"{row.delta} {row.geometry} f{row.fold}s{row.seed} "
            f"n={row.n_participants} p_unique={row.exact_tail_p_unique:.3f}"
        )
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(fig_dir / f"signflip_{row.delta}_{row.geometry}_f{row.fold}_s{row.seed}.png", dpi=140)
        plt.close(fig)
        shown += 1


def plot_jackknife(jack_df, fig_dir):
    sub = jack_df[jack_df.geometry == "raw"]
    if sub.empty:
        return
    for delta in DELTAS:
        g = sub[sub.delta == delta]
        if g.empty:
            continue
        fig, ax = plt.subplots(figsize=(7, 3.8))
        for leave, gg in g.groupby("left_out"):
            ax.scatter(
                [f"{r.fold}{r.seed}" for r in gg.itertuples()],
                gg.mean_pairwise, label=f"w/o {leave}", alpha=0.85,
            )
        ax.axhline(0, color="grey", ls=":")
        ax.set_title(f"Jackknife mean pairwise ({delta}, raw)")
        ax.set_xlabel("fold-seed"); ax.set_ylabel("mean pairwise cosine")
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(fig_dir / f"jackknife_{delta}_raw.png", dpi=140)
        plt.close(fig)


def plot_reliability_heatmap(reli: pd.DataFrame, fig_dir):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, tp, col in zip(axes, (1, 2, 3), ("skill_T1_heldout", "skill_T2", "skill_T3")):
        piv = reli.pivot_table(index="participant", columns=["fold", "seed"], values=col, aggfunc="first")
        im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdYlGn", vmin=-0.1, vmax=0.1)
        ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
        ax.set_xticks(range(len(piv.columns)))
        ax.set_xticklabels([f"{f}{s}" for f, s in piv.columns], rotation=90, fontsize=7)
        ax.set_title(f"skill T{tp}")
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("Conv reliability skill (green>0)")
    fig.tight_layout()
    fig.savefig(fig_dir / "reliability_status_heatmap.png", dpi=150)
    plt.close(fig)


def plot_projections(proj_df, fig_dir):
    sub = proj_df[proj_df.geometry == "raw"]
    if sub.empty:
        return
    for delta in DELTAS:
        g = sub[sub.delta == delta]
        if g.empty:
            continue
        fig, ax = plt.subplots(figsize=(7, 3.8))
        for pid, gg in g.groupby("participant"):
            ax.scatter(
                [f"{r.fold}{r.seed}" for r in gg.itertuples()],
                gg.cos_to_consensus, label=str(pid), s=50,
            )
        ax.axhline(0, color="grey", ls=":")
        ax.set_title(f"Cosine to consensus ({delta}, raw, n≥3 runs)")
        ax.set_xlabel("fold-seed"); ax.set_ylabel("cos(participant, consensus)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(fig_dir / f"consensus_projection_{delta}_raw.png", dpi=140)
        plt.close(fig)


def plot_mag_vs_rep(class_df, fig_dir):
    sub = class_df[(class_df.geometry == "raw") & class_df.included]
    if sub.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, delta in zip(axes, ("D12", "D13")):
        g = sub[sub.delta == delta]
        for cls, gg in g.groupby("class"):
            ax.scatter(gg.ratio_vs_rep, gg.participant.astype(str), label=cls, alpha=0.8)
        ax.axvline(1.0, color="grey", ls="--")
        ax.set_xlabel("|Δ| / Drep")
        ax.set_title(delta)
        ax.legend(fontsize=6)
    fig.suptitle("Change vs repetition (included cells only)")
    fig.tight_layout()
    fig.savefig(fig_dir / "change_vs_repetition_classes.png", dpi=150)
    plt.close(fig)


def explicit_feature_correlations(proj_df, mag, cfg, out_dir, fig_dir):
    feat = pd.read_csv(ROOT / "outputs/s5_explicit/recording_features.csv")
    amp = pd.read_csv(ROOT / "outputs/s5_explicit/recording_features_amplitude_controlled.csv")
    feat_cols = [
        "total_energy_deg2_s2", "participation_entropy_bits", "effective_dimensionality",
        "active_link_count", "active_region_count", "lr_symmetry", "regional_coupling",
    ]
    amp_cols = [
        "participation_entropy_bits_amp_residual", "effective_dimensionality_amp_residual",
        "active_link_count_amp_residual", "active_region_count_amp_residual",
        "lr_symmetry_amp_residual", "regional_coupling_amp_residual",
    ]
    rows = []
    sub = proj_df[(proj_df.analysis == "primary") & (proj_df.geometry == "raw")]
    if sub.empty:
        return pd.DataFrame()
    for (fold, seed, delta), g in sub.groupby(["fold", "seed", "delta"]):
        traj = int(cfg["folds"][fold]["trajectory_repetition"])
        for fcol in feat_cols + amp_cols:
            xs, ys, pids = [], [], []
            src = amp if fcol in amp_cols else feat
            for _, pr in g.iterrows():
                pid = str(pr.participant)
                def get_f(tp, _src=src, _fcol=fcol, _pid=pid):
                    r = _src[
                        (_src.participant.astype(str) == _pid)
                        & (_src.timepoint == tp) & (_src.repetition == traj)
                    ]
                    return float(r.iloc[0][_fcol]) if len(r) == 1 and _fcol in r.columns else np.nan
                if delta == "D12":
                    dfv = get_f(2) - get_f(1)
                elif delta == "D13":
                    dfv = get_f(3) - get_f(1)
                else:
                    dfv = get_f(3) - get_f(2)
                if np.isfinite(dfv) and np.isfinite(pr.cos_to_consensus):
                    xs.append(dfv); ys.append(pr.cos_to_consensus); pids.append(pid)
            r = float(np.corrcoef(xs, ys)[0, 1]) if len(xs) >= 3 else float("nan")
            rows.append({
                "fold": fold, "seed": int(seed), "delta": delta, "feature": fcol,
                "n": len(xs), "pearson_r": r, "participants": ",".join(pids),
            })
    corr = pd.DataFrame(rows)
    corr.to_csv(out_dir / "explicit_feature_correlations.csv", index=False)
    if not corr.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        summary = (
            corr[corr.delta.isin(["D12", "D13"])]
            .groupby(["delta", "feature"]).pearson_r
            .apply(lambda s: float(np.nanmean(np.abs(s))))
            .reset_index(name="mean_abs_r")
        )
        features = summary.feature.unique()
        x = np.arange(len(features))
        for i, delta in enumerate(("D12", "D13")):
            g = summary[summary.delta == delta].set_index("feature").reindex(features)
            ax.bar(x + i * 0.4, g.mean_abs_r.fillna(0), width=0.4, label=delta)
        ax.set_xticks(x + 0.2)
        ax.set_xticklabels(features, rotation=75, fontsize=7)
        ax.set_ylabel("mean |Pearson r| across fold×seed")
        ax.set_title("Consensus projection vs explicit-feature Δ (descriptive)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(fig_dir / "explicit_feature_vs_consensus.png", dpi=150)
        plt.close(fig)
    return corr


def region_occlusion_sensitivity(cfg, mag, out_dir, fig_dir):
    link_ids, regions = data_windows.load_link_config(ROOT)
    region_to_idx = {}
    for i, lid in enumerate(link_ids):
        region_to_idx.setdefault(regions[lid], []).append(i)
    fold, seed = "A", 0
    valid = mag[(mag.fold == fold) & (mag.seed == seed) & mag.interpretable_D12]
    pids = sorted(valid.participant.astype(str).tolist())
    if len(pids) < 3:
        return pd.DataFrame()
    traj = int(cfg["folds"][fold]["trajectory_repetition"])
    state = torch.load(
        ROOT / f"outputs/s5_conv/checkpoints/{fold}_{OBJ}_s{seed}.pt",
        map_location="cpu", weights_only=True,
    )
    net = models.ConvMaskedPredictor(
        n_links=cfg["model"]["n_links"], patch_frames=cfg["model"]["patch_frames"],
        channels=cfg["s5"]["conv_channels"], target_dim=3,
        embedding_dim=cfg["model"]["embedding_dim"],
    )
    net.load_state_dict(state); net.eval()
    w = data_windows.load_window_index(ROOT)
    ev = w[(w.role == "evaluation") & w.usable & (w.repetition == traj)]
    x_ev, ev_i = data_windows.materialise_windows(ev, ROOT, "masked_6d")
    eval_ex = cfg["exercises"]["evaluation"]

    def embed_rec(x):
        z = train_masked.embed_windows(net, x)
        return data_windows.aggregate_recording_embeddings(z, ev_i, eval_ex)

    def deltas_from_rec(rec):
        vecs = {}
        for pid in pids:
            g = rec[rec.participant.astype(str) == pid]
            z = {}
            for tp in (1, 2):
                row = g[g.timepoint == tp]
                if len(row) != 1:
                    break
                z[tp] = row.iloc[0][ecols()].to_numpy(float)
            if len(z) == 2:
                vecs[pid] = z[2] - z[1]
        return vecs

    base_vecs = deltas_from_rec(embed_rec(x_ev))
    base_mean = pairwise_cosines(base_vecs)["mean_pairwise"]
    rows = [{"region": "none", "mean_pairwise_D12": base_mean, "delta_from_base": 0.0,
             "n_participants": len(base_vecs), "fold": fold, "seed": seed}]
    for region, idxs in region_to_idx.items():
        x_m = x_ev.copy()
        x_m[:, :, idxs, :] = 0.0
        vecs = deltas_from_rec(embed_rec(x_m))
        if len(vecs) < 3:
            continue
        m = pairwise_cosines(vecs)["mean_pairwise"]
        rows.append({
            "region": region, "mean_pairwise_D12": m, "delta_from_base": m - base_mean,
            "n_participants": len(vecs), "fold": fold, "seed": seed,
        })
    tab = pd.DataFrame(rows)
    tab.to_csv(out_dir / "region_occlusion_D12_A0.csv", index=False)
    if len(tab) > 1:
        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        t = tab[tab.region != "none"]
        ax.barh(t.region, t.delta_from_base, color="C1")
        ax.axvline(0, color="grey", ls=":")
        ax.set_xlabel("Δ mean pairwise cosine (occluded − intact)")
        ax.set_title(f"Region occlusion effect on D12 (fold A seed 0; n={len(pids)})")
        fig.tight_layout()
        fig.savefig(fig_dir / "region_occlusion_D12.png", dpi=150)
        plt.close(fig)
    return tab


def transformer_sensitivity(cfg, out_dir):
    tf_reli = ROOT / "outputs/s6_transformer/reliability_t1_t2_t3.csv"
    tf_emb = ROOT / "outputs/s6_transformer/recording_embeddings.csv"
    if not tf_reli.exists() or not tf_emb.exists():
        return pd.DataFrame()
    reli = pd.read_csv(tf_reli)
    emb = pd.read_csv(tf_emb)
    emb = emb[emb.objective == OBJ]
    rows = []
    for fold in cfg["folds"]:
        traj = int(cfg["folds"][fold]["trajectory_repetition"])
        for seed in cfg["model"]["seeds"]:
            for delta, (tp_a, tp_b) in (("D12", (1, 2)), ("D13", (1, 3)), ("D23", (2, 3))):
                vecs = {}
                for pid in cfg["participants"]:
                    rcell = reli[
                        (reli.fold == fold) & (reli.seed == seed)
                        & (reli.participant.astype(str) == str(pid))
                    ]
                    if len(rcell) != 1:
                        continue
                    r = rcell.iloc[0]
                    sk = {1: r.skill_T1_heldout, 2: r.skill_T2, 3: r.skill_T3}
                    if sk[tp_a] <= 0 or sk[tp_b] <= 0:
                        continue
                    g = emb[
                        (emb.fold == fold) & (emb.seed == seed)
                        & (emb.participant.astype(str) == str(pid)) & (emb.repetition == traj)
                    ]
                    za = g[g.timepoint == tp_a]; zb = g[g.timepoint == tp_b]
                    if len(za) != 1 or len(zb) != 1:
                        continue
                    vecs[str(pid)] = zb.iloc[0][ecols()].to_numpy(float) - za.iloc[0][ecols()].to_numpy(float)
                base = {
                    "fold": fold, "seed": int(seed), "delta": delta,
                    "n_participants": len(vecs),
                    "participants_included": ",".join(sorted(vecs)),
                    "sufficient_for_group": len(vecs) >= 3,
                }
                if len(vecs) >= 2:
                    pw = pairwise_cosines(vecs)
                    base.update({
                        "mean_pairwise": pw["mean_pairwise"],
                        "frac_positive_pairs": pw["frac_positive_pairs"],
                    })
                rows.append(base)
    tab = pd.DataFrame(rows)
    tab.to_csv(out_dir / "transformer_sensitivity_direction.csv", index=False)
    return tab


def evaluate_s8_gate(sim_df, flip_df, jack_df, class_df) -> dict:
    core = sim_df[
        (sim_df.analysis == "primary") & (sim_df.sufficient_for_group)
        & (sim_df.delta.isin(["D12", "D13"]))
    ]
    gate = {"n_sufficient_runs_D12_D13": int(len(core))}
    if core.empty:
        gate.update({"pass": False, "continue_to_s9_s10": False,
                     "shared_direction_evidence": False,
                     "reason": "no fold×seed×comparison with ≥3 reliable participants"})
        return gate
    multi = core.groupby("delta").apply(lambda g: int((g.n_participants >= 3).sum()))
    gate["sufficient_runs_per_delta"] = multi.to_dict()
    agree_rows = []
    for (fold, seed, delta), g in core.groupby(["fold", "seed", "delta"]):
        if set(g.geometry) >= {"raw", "std"}:
            s_raw = float(g[g.geometry == "raw"].mean_pairwise.iloc[0])
            s_std = float(g[g.geometry == "std"].mean_pairwise.iloc[0])
            agree_rows.append({
                "same_sign": (s_raw > 0) == (s_std > 0),
                "both_positive": (s_raw > 0) and (s_std > 0),
            })
    agree = pd.DataFrame(agree_rows)
    gate["frac_raw_std_same_sign"] = float(agree.same_sign.mean()) if len(agree) else 0.0
    gate["frac_both_geometries_positive"] = float(agree.both_positive.mean()) if len(agree) else 0.0
    stab = {}
    for geom in GEOMS:
        for delta in ("D12", "D13"):
            g = core[(core.geometry == geom) & (core.delta == delta)]
            stab[f"{delta}_{geom}_frac_positive"] = float((g.mean_pairwise > 0).mean()) if len(g) else float("nan")
            stab[f"{delta}_{geom}_mean"] = float(g.mean_pairwise.mean()) if len(g) else float("nan")
    gate["stability"] = stab
    jk = jack_df[(jack_df.analysis == "primary") & (jack_df.geometry == "raw")
                 & (jack_df.delta.isin(["D12", "D13"]))] if len(jack_df) else jack_df
    gate["jackknife_sign_flip_rate"] = float(jk.sign_flips_vs_full.mean()) if len(jk) else float("nan")
    for leave in ("252", "671", "790"):
        sub = jk[jk.left_out == leave] if len(jk) else jk
        gate[f"jackknife_w_o_{leave}_frac_positive"] = (
            float((sub.mean_pairwise > 0).mean()) if len(sub) else float("nan")
        )
    cls = class_df[(class_df.analysis == "primary") & (class_df.geometry == "raw")
                   & class_df.included & class_df.delta.isin(["D12", "D13"])] if len(class_df) else class_df
    if len(cls):
        gate["class_fractions"] = cls["class"].value_counts(normalize=True).to_dict()
        gate["frac_change_gt_rep"] = float(cls["class"].isin([
            "reliable_direction_change_gt_repetition", "reliable_degraded_but_change_gt_rep",
        ]).mean())
    else:
        gate["frac_change_gt_rep"] = float("nan")
    checks = {
        "multiple_sufficient_runs": bool(multi.get("D12", 0) >= 2 or multi.get("D13", 0) >= 2),
        "mean_cosine_mostly_positive": bool(np.nanmean([
            stab.get("D12_raw_frac_positive", np.nan), stab.get("D13_raw_frac_positive", np.nan),
        ]) >= 0.5),
        "raw_std_agree_sign": gate["frac_raw_std_same_sign"] >= 0.8,
        "jackknife_not_fragile": (
            (gate["jackknife_sign_flip_rate"] <= 0.35)
            if np.isfinite(gate["jackknife_sign_flip_rate"]) else False
        ),
        "not_all_within_repetition": (
            gate.get("frac_change_gt_rep", 0) >= 0.3
            if np.isfinite(gate.get("frac_change_gt_rep", np.nan)) else False
        ),
    }
    shared_direction = all([
        checks["multiple_sufficient_runs"], checks["mean_cosine_mostly_positive"],
        checks["raw_std_agree_sign"], checks["jackknife_not_fragile"],
        checks["not_all_within_repetition"],
    ]) and gate["frac_both_geometries_positive"] >= 0.5
    continue_s9 = bool(
        checks["multiple_sufficient_runs"]
        or (sim_df[(sim_df.analysis == "primary") & (sim_df.n_participants >= 2)].shape[0] >= 6)
    )
    gate["checks"] = checks
    gate["shared_direction_evidence"] = shared_direction
    gate["continue_to_s9_s10"] = continue_s9
    gate["pass"] = continue_s9
    if shared_direction:
        gate["reason"] = "preliminary shared-direction evidence under co-primary geometries"
    elif continue_s9:
        gate["reason"] = (
            "insufficient stable shared direction, but enough reliable cells to complete "
            "Stage 0 controls and GO/NO-GO (LIMITED / METHOD path)"
        )
    else:
        gate["reason"] = "too few comparable reliability-qualified participant sets"
    return gate


def write_s8_reports(sim, pairs, flip, jack, proj, classes, corr, occ, tf_sens, gate, out_dir):
    incl = sim[sim.analysis == "primary"][
        ["fold", "seed", "delta", "geometry", "n_participants",
         "participants_included", "participants_excluded", "sufficient_for_group",
         "mean_pairwise", "frac_positive_pairs", "status"]
    ]
    incl.to_csv(out_dir / "inclusion_table.csv", index=False)
    suf = sim[(sim.analysis == "primary") & (sim.sufficient_for_group)]
    lines = []
    for delta in DELTAS:
        for geom in GEOMS:
            g = suf[(suf.delta == delta) & (suf.geometry == geom)]
            if g.empty:
                lines.append(f"| {delta} | {geom} | 0 | n/a | n/a |")
            else:
                lines.append(
                    f"| {delta} | {geom} | {len(g)} | {g.mean_pairwise.mean():.3f} | "
                    f"{(g.mean_pairwise > 0).mean():.0%} |"
                )
    (ROOT / "reports/S8_DIRECTION_SIMILARITY_REPORT.md").write_text(f"""# S8 direction similarity report

Primary representation: **ConvMaskedPredictor** / `masked_angular_velocity` / mask 30%.
Reliability-qualified inputs only (both endpoints `skill > 0`). Latent coordinates
are never averaged across folds or seeds.

## Inclusion (observed)

| Delta | Geometry | n sufficient runs | Mean of mean-pairwise | % runs with mean>0 |
|---|---|---|---|---|
{chr(10).join(lines)}

Full inclusion table: `outputs/s8_direction/inclusion_table.csv`.

## Derived — pairwise similarity

See `similarity_summary.csv`, `pairwise_cosines.csv`, `consensus_projections.csv`.

Raw vs standardized same-sign agreement: **{gate.get('frac_raw_std_same_sign', float('nan')):.0%}**.
Both positive: **{gate.get('frac_both_geometries_positive', float('nan')):.0%}**.

## Interpretation

{gate.get('reason', '')}

Shared-direction evidence flag: **{gate.get('shared_direction_evidence')}**.

Δ12, Δ13 and Δ23 are not independent (`Δ23 = Δ13 − Δ12`). N=4 forbids population inference.

## Status

S8 complete. Continuation to S9/S10: **{gate.get('continue_to_s9_s10')}**.
""", encoding="utf-8")

    flip_ok = flip.dropna(subset=["exact_tail_p_unique"]) if len(flip) and "exact_tail_p_unique" in flip.columns else flip
    with (ROOT / "reports/S8_SIGN_FLIP_REFERENCE.md").open("w", encoding="utf-8") as fh:
        fh.write("""# S8 exact sign-flip empirical reference

Assumption (explicit): under the null, each participant's observed change vector and its inverse are exchangeable.

Sign flips apply to participant vectors. First sign fixed (+1); `2^(n-1)` patterns enumerated. For n=4, minimum exact p among unique mean-cosine values is **0.125**.

| Delta | Geom | Fold | Seed | n | observed mean cos | unique configs | exact p (unique) | min p |
|---|---|---|---|---|---|---|---|---|
""")
        if len(flip_ok):
            for r in flip_ok.itertuples():
                fh.write(
                    f"| {r.delta} | {r.geometry} | {r.fold} | {r.seed} | {r.n_participants} | "
                    f"{r.observed_mean_pairwise:.3f} | {r.n_unique_mean_cosine} | "
                    f"{r.exact_tail_p_unique:.3f} | {r.min_attainable_p:.3f} |\n"
                )
        else:
            fh.write("| — | — | — | — | — | — | — | — | — |\n")
        fh.write("\nResults remain descriptive; exact nulls cannot reach conventional significance at this N.\n")

    (ROOT / "reports/S8_PARTICIPANT_INFLUENCE.md").write_text(f"""# S8 participant-influence (jackknife)

Leave-one-out mean pairwise cosine on n≥3 sets. No retraining.

Jackknife sign-flip rate (raw, D12/D13): **{gate.get('jackknife_sign_flip_rate', float('nan')):.0%}**.

| Left out | Fraction of runs with mean pairwise > 0 |
|---|---|
| 252 | {gate.get('jackknife_w_o_252_frac_positive', float('nan')):.0%} |
| 671 | {gate.get('jackknife_w_o_671_frac_positive', float('nan')):.0%} |
| 790 | {gate.get('jackknife_w_o_790_frac_positive', float('nan')):.0%} |

Table: `outputs/s8_direction/jackknife.csv`.
""", encoding="utf-8")

    cls_frac = gate.get("class_fractions", {})
    cls_lines = "\n".join(f"| {k} | {v:.0%} |" for k, v in cls_frac.items()) or "| — | — |"
    tf_note = (
        f"TF sufficient runs: {int(tf_sens.sufficient_for_group.sum())}/{len(tf_sens)}"
        if tf_sens is not None and len(tf_sens) else "no TF table"
    )
    (ROOT / "reports/S8_INTERPRETABILITY_REPORT.md").write_text(f"""# S8 interpretability report

## Change vs repetition

| Class | Fraction |
|---|---|
{cls_lines}

Fraction with change > repetition reference: **{gate.get('frac_change_gt_rep', float('nan')):.0%}**.

## Explicit features / amplitude / regions / TF

* Explicit-feature correlations: `explicit_feature_correlations.csv` (descriptive only).
* Region occlusion: `region_occlusion_D12_A0.csv` ({'present' if occ is not None and len(occ) else 'unavailable'}).
* Transformer sensitivity: {tf_note}.
""", encoding="utf-8")

    (ROOT / "reports/S8_READINESS_RECOMMENDATION.md").write_text(f"""# S8 readiness recommendation

## Shared-direction evidence?

**{gate.get('shared_direction_evidence')}**

Reason: {gate.get('reason')}

### Checks

```json
{json.dumps(gate.get('checks', {}), indent=2)}
```

## Continue to S9 / S10?

**{gate.get('continue_to_s9_s10')}**

Final GO/NO-GO label is deferred to S10 after S9 controls.
""", encoding="utf-8")


def main() -> int:
    torch.set_num_threads(4)
    t0 = time.time()
    cfg = data_windows.load_config(ROOT)
    out_dir = ROOT / "outputs/s8_direction"
    fig_dir = ROOT / "figures/s8_direction"
    for d in (out_dir, fig_dir):
        d.mkdir(parents=True, exist_ok=True)
    (out_dir / "experiment_snapshot.yaml").write_text(
        (ROOT / "configs/experiment.yaml").read_text(), encoding="utf-8",
    )
    change = pd.read_csv(ROOT / "outputs/s7_conv/change_vectors.csv")
    mag = pd.read_csv(ROOT / "outputs/s7_conv/change_magnitudes.csv")
    reli = pd.read_csv(ROOT / "outputs/s7_conv/reliability_t1_t2_t3.csv")
    rec = pd.read_csv(ROOT / "outputs/s7_conv/recording_embeddings.csv")
    rec = rec[rec.objective == OBJ]

    print("Loading reliability-qualified change vectors ...")
    vecs = load_change_vectors(change, mag)
    sim, pairs, flip, jack, proj, classes = run_direction_block(vecs, mag, "primary")
    print("ex11 sensitivity ...")
    vecs_ex11 = ex11_change_vectors(rec, mag, cfg)
    sim11, pairs11, flip11, jack11, proj11, classes11 = run_direction_block(vecs_ex11, mag, "ex11")
    sim = pd.concat([sim, sim11], ignore_index=True)
    pairs = pd.concat([pairs, pairs11], ignore_index=True)
    flip = pd.concat([flip, flip11], ignore_index=True)
    jack = pd.concat([jack, jack11], ignore_index=True)
    proj = pd.concat([proj, proj11], ignore_index=True)
    classes = pd.concat([classes, classes11], ignore_index=True)

    sim.to_csv(out_dir / "similarity_summary.csv", index=False)
    pairs.to_csv(out_dir / "pairwise_cosines.csv", index=False)
    flip_save = flip.drop(columns=[c for c in flip.columns if c.startswith("_")], errors="ignore")
    flip_save.to_csv(out_dir / "signflip.csv", index=False)
    if "_null_json" in flip.columns:
        flip[["fold", "seed", "delta", "geometry", "analysis", "_null_json"]].to_csv(
            out_dir / "signflip_nulls.csv", index=False,
        )
    jack.to_csv(out_dir / "jackknife.csv", index=False)
    proj.to_csv(out_dir / "consensus_projections.csv", index=False)
    classes.to_csv(out_dir / "participant_result_classes.csv", index=False)

    print("figures ...")
    plot_cosine_matrices(pairs[pairs.analysis == "primary"], sim[sim.analysis == "primary"], fig_dir)
    plot_stability(sim[sim.analysis == "primary"], fig_dir)
    plot_signflip(flip[flip.analysis == "primary"] if len(flip) else flip, fig_dir)
    plot_jackknife(jack[jack.analysis == "primary"] if len(jack) else jack, fig_dir)
    plot_reliability_heatmap(reli, fig_dir)
    plot_projections(proj[proj.analysis == "primary"] if len(proj) else proj, fig_dir)
    plot_mag_vs_rep(classes[classes.analysis == "primary"] if len(classes) else classes, fig_dir)

    print("explicit-feature correlations ...")
    corr = explicit_feature_correlations(proj, mag, cfg, out_dir, fig_dir)
    print("region occlusion ...")
    try:
        occ = region_occlusion_sensitivity(cfg, mag, out_dir, fig_dir)
    except Exception as exc:
        print(f"  region occlusion deferred: {exc}")
        occ = pd.DataFrame()
    print("transformer sensitivity ...")
    tf_sens = transformer_sensitivity(cfg, out_dir)

    print("evaluating S8 gate ...")
    gate = evaluate_s8_gate(
        sim,
        flip[flip.analysis == "primary"] if len(flip) else flip,
        jack[jack.analysis == "primary"] if len(jack) else jack,
        classes[classes.analysis == "primary"] if len(classes) else classes,
    )
    provenance.write_json(out_dir / "S8_GATE.json", gate)
    write_s8_reports(sim, pairs, flip, jack, proj, classes, corr, occ, tf_sens, gate, out_dir)

    stamp = provenance.run_stamp("S8_direction_similarity", {
        "objective": OBJ, "architecture": "conv", "gate": gate,
        "elapsed_s": round(time.time() - t0, 1),
    })
    for name in ("similarity_summary.csv", "pairwise_cosines.csv", "signflip.csv",
                 "jackknife.csv", "inclusion_table.csv", "S8_GATE.json"):
        p = out_dir / name
        if p.exists():
            stamp.setdefault("artifact_sha256", {})[name] = provenance.sha256_file(p)
    for name in ("change_vectors.csv", "change_magnitudes.csv", "reliability_t1_t2_t3.csv"):
        stamp.setdefault("input_sha256", {})[name] = provenance.sha256_file(
            ROOT / "outputs/s7_conv" / name
        )
    provenance.write_json(out_dir / "s8_provenance.json", stamp)
    with (ROOT / "reports/DECISION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## S8 — {stamp['utc']}\n"
            f"- Shared-direction evidence: {gate.get('shared_direction_evidence')}\n"
            f"- Continue S9/S10: {gate.get('continue_to_s9_s10')} ({gate.get('reason')})\n"
        )
    readme = ROOT / "README.md"
    txt = readme.read_text()
    txt = txt.replace(
        "| S8 | Direction similarity across participants | not started |",
        "| S8 | Direction similarity across participants | **done — review gate** |",
    )
    if "S8_READINESS_RECOMMENDATION" not in txt:
        txt = txt.replace(
            "* `reports/S7_READINESS_RECOMMENDATION.md` - **current stop gate before S8**",
            "* `reports/S8_READINESS_RECOMMENDATION.md` - **current stop gate before S9/S10**\n"
            "* `reports/S8_DIRECTION_SIMILARITY_REPORT.md` / `S8_SIGN_FLIP_REFERENCE.md` / "
            "`S8_PARTICIPANT_INFLUENCE.md` / `S8_INTERPRETABILITY_REPORT.md`\n"
            "* `reports/S7_READINESS_RECOMMENDATION.md` - prior S7 gate",
        )
    readme.write_text(txt)
    print(json.dumps(gate, indent=2, default=str))
    print(f"\nS8 OK ({time.time()-t0:.0f}s)  continue_s9={gate.get('continue_to_s9_s10')}")
    return 0 if gate.get("continue_to_s9_s10") else 3


if __name__ == "__main__":
    raise SystemExit(main())
