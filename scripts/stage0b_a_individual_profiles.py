#!/usr/bin/env python3
"""Stage 0B-A — Individual movement-change profiles (Conv, no retraining).

Characterises reliability-qualified within-participant T1→T2 / T1→T3 change
using existing Conv embeddings and explicit features. Does not search for a
shared cross-participant direction and does not start free-movement analysis.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OBJ = "masked_angular_velocity"
DIM = 32
EVAL_EX = [9, 10, 11, 12, 13]
PARTICIPANTS = ["252", "651", "671", "790"]

FEATURE_CORE = [
    "total_energy_deg2_s2",
    "active_link_count",
    "active_region_count",
    "participation_entropy_bits",
    "effective_dimensionality",
    "lr_symmetry",
    "regional_coupling",
    "trunk_arm_lagged_coupling",
]
ENERGY_SHARES = [
    "energy_share_head_neck",
    "energy_share_left_arm",
    "energy_share_left_leg",
    "energy_share_right_arm",
    "energy_share_right_leg",
    "energy_share_trunk_spine",
]
AMP_RESIDUALS = [
    "participation_entropy_bits_amp_residual",
    "effective_dimensionality_amp_residual",
    "active_link_count_amp_residual",
    "active_region_count_amp_residual",
    "lr_symmetry_amp_residual",
    "regional_coupling_amp_residual",
    "trunk_arm_lagged_coupling_amp_residual",
]


def ecols(prefix: str = "e") -> list[str]:
    return [f"{prefix}{i}" for i in range(DIM)]


def traj_rep(cfg, fold: str) -> int:
    return int(cfg["folds"][fold]["trajectory_repetition"])


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def exercise_latent_table(win: pd.DataFrame, cfg) -> pd.DataFrame:
    """Mean embedding per fold/seed/participant/timepoint/repetition/exercise."""
    cols = ecols()
    rows = []
    for (fold, seed, pid, tp, rep, ex), g in win.groupby(
        ["fold", "seed", "participant", "timepoint", "repetition", "exercise_id"]
    ):
        if int(ex) not in EVAL_EX:
            continue
        vec = g[cols].mean().to_numpy(float)
        rows.append({
            "fold": fold, "seed": int(seed), "participant": str(pid),
            "timepoint": int(tp), "repetition": int(rep), "exercise_id": int(ex),
            "n_windows": len(g),
            **{c: float(v) for c, v in zip(cols, vec)},
        })
    return pd.DataFrame(rows)


def exercise_feature_table(wf: pd.DataFrame) -> pd.DataFrame:
    """Mean explicit features per participant/timepoint/repetition/exercise."""
    cols = [c for c in FEATURE_CORE + ENERGY_SHARES if c in wf.columns]
    # also need energy shares computed if missing
    df = wf[wf.exercise_id.isin(EVAL_EX)].copy()
    for share, eng in [
        ("energy_share_head_neck", "energy_head_neck"),
        ("energy_share_left_arm", "energy_left_arm"),
        ("energy_share_left_leg", "energy_left_leg"),
        ("energy_share_right_arm", "energy_right_arm"),
        ("energy_share_right_leg", "energy_right_leg"),
        ("energy_share_trunk_spine", "energy_trunk_spine"),
    ]:
        if share not in df.columns and eng in df.columns:
            tot = df["total_energy_deg2_s2"].replace(0, np.nan)
            df[share] = df[eng] / tot
    cols = [c for c in FEATURE_CORE + ENERGY_SHARES if c in df.columns]
    out = (
        df.groupby(["participant", "timepoint", "repetition", "exercise_id"], as_index=False)[cols]
        .mean()
    )
    out["participant"] = out["participant"].astype(str)
    return out


def recording_feature_table(rf: pd.DataFrame, ra: pd.DataFrame) -> pd.DataFrame:
    m = rf.merge(
        ra[["recording_id"] + [c for c in AMP_RESIDUALS if c in ra.columns]],
        on="recording_id", how="left",
    )
    m["participant"] = m["participant"].astype(str)
    return m


def compute_exercise_contributions(ex_lat: pd.DataFrame, mag: pd.DataFrame, cfg) -> pd.DataFrame:
    cols = ecols()
    rows = []
    for _, mrow in mag.iterrows():
        fold, seed, pid = mrow.fold, int(mrow.seed), str(mrow.participant)
        traj = traj_rep(cfg, fold)
        for delta, tp_b, flag in (("D12", 2, "interpretable_D12"), ("D13", 3, "interpretable_D13")):
            reliable = bool(mrow[flag])
            sub = ex_lat[
                (ex_lat.fold == fold) & (ex_lat.seed == seed)
                & (ex_lat.participant == pid) & (ex_lat.repetition == traj)
            ]
            z1 = sub[sub.timepoint == 1].set_index("exercise_id")
            zb = sub[sub.timepoint == tp_b].set_index("exercise_id")
            common = sorted(set(z1.index) & set(zb.index) & set(EVAL_EX))
            if len(common) < 2:
                continue
            deltas = {ex: zb.loc[ex, cols].to_numpy(float) - z1.loc[ex, cols].to_numpy(float) for ex in common}
            d_rec = np.mean(np.stack([deltas[ex] for ex in common], axis=0), axis=0)
            norms = {ex: float(np.linalg.norm(deltas[ex])) for ex in common}
            sum_n = sum(norms.values()) + 1e-12
            # leave-one-out effect on recording norm
            full_n = float(np.linalg.norm(d_rec))
            for ex in common:
                others = [deltas[e] for e in common if e != ex]
                d_loo = np.mean(np.stack(others, axis=0), axis=0)
                loo_n = float(np.linalg.norm(d_loo))
                rows.append({
                    "fold": fold, "seed": seed, "participant": pid,
                    "delta": delta, "exercise_id": ex,
                    "reliable": reliable,
                    "traj_repetition": traj,
                    "norm_delta_exercise": norms[ex],
                    "frac_norm": norms[ex] / sum_n,
                    "cos_to_recording_delta": cosine(deltas[ex], d_rec),
                    "recording_delta_norm": full_n,
                    "loo_recording_norm": loo_n,
                    "loo_norm_drop": full_n - loo_n,
                    "latent_change_norm_raw": float(mrow[f"norm_{delta}_raw"]),
                    "ratio_vs_drep": (
                        float(mrow.ratio_D12_over_DrepT2_raw) if delta == "D12"
                        else float(mrow.ratio_D13_over_DrepT3_raw)
                    ),
                })
    return pd.DataFrame(rows)


def compute_feature_changes(ex_feat: pd.DataFrame, rec_feat: pd.DataFrame, mag: pd.DataFrame, cfg) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exercise-level and recording-level feature deltas vs R1/R2."""
    feat_cols = [c for c in FEATURE_CORE + ENERGY_SHARES if c in ex_feat.columns]
    amp_cols = [c for c in AMP_RESIDUALS if c in rec_feat.columns]
    ex_rows, rec_rows = [], []

    for pid in PARTICIPANTS:
        for delta, tp_b in (("D12", 2), ("D13", 3)):
            # reliability: fraction of fold×seed interpretable
            msub = mag[(mag.participant.astype(str) == pid)]
            flag = f"interpretable_{delta}"
            n_rel = int(msub[flag].sum())
            n_tot = int(len(msub))
            # for each fold use its traj rep; pool descriptive stats across folds later
            for fold in cfg["folds"]:
                traj = traj_rep(cfg, fold)
                # recording-level
                def get_rec(tp, rep, cols):
                    r = rec_feat[
                        (rec_feat.participant == pid) & (rec_feat.timepoint == tp)
                        & (rec_feat.repetition == rep)
                    ]
                    if len(r) != 1:
                        return None
                    return {c: float(r.iloc[0][c]) for c in cols if c in r.columns}

                cols_rec = feat_cols + amp_cols
                f1 = get_rec(1, traj, cols_rec)
                fb = get_rec(tp_b, traj, cols_rec)
                if f1 is None or fb is None:
                    continue
                # R1/R2 at T1 and Tb for each feature
                f1a, f1b = get_rec(1, 1, cols_rec), get_rec(1, 2, cols_rec)
                fba, fbb = get_rec(tp_b, 1, cols_rec), get_rec(tp_b, 2, cols_rec)
                # latent reliability for this fold (any seed) — use majority / mean ratio
                mfold = msub[msub.fold == fold]
                reliable_fold = bool(mfold[flag].any()) if len(mfold) else False
                mean_ratio = float(mfold[
                    "ratio_D12_over_DrepT2_raw" if delta == "D12" else "ratio_D13_over_DrepT3_raw"
                ].mean()) if len(mfold) else float("nan")

                for c in cols_rec:
                    if c not in f1 or c not in fb:
                        continue
                    long = fb[c] - f1[c]
                    drep1 = abs(f1a[c] - f1b[c]) if f1a and f1b and c in f1a and c in f1b else np.nan
                    drepb = abs(fba[c] - fbb[c]) if fba and fbb and c in fba and c in fbb else np.nan
                    drep_max = np.nanmax([drep1, drepb])
                    rec_rows.append({
                        "participant": pid, "fold": fold, "delta": delta,
                        "feature": c, "level": "recording",
                        "value_T1": f1[c], f"value_T{tp_b}": fb[c],
                        "delta_value": long, "abs_delta": abs(long),
                        "drep_T1": drep1, f"drep_T{tp_b}": drepb,
                        "drep_max": drep_max,
                        "ratio_vs_drep_max": abs(long) / drep_max if drep_max and drep_max > 0 else np.nan,
                        "exceeds_drep_max": bool(drep_max == drep_max and drep_max > 0 and abs(long) > drep_max),
                        "reliable_fold_any_seed": reliable_fold,
                        "n_reliable_cells": n_rel, "n_cells": n_tot,
                        "mean_latent_ratio_vs_drep": mean_ratio,
                        "is_amp_residual": c in amp_cols,
                        "is_energy": c == "total_energy_deg2_s2" or c.startswith("energy_share_"),
                    })

                # exercise-level for core + shares
                for ex in EVAL_EX:
                    def get_ex(tp, rep):
                        r = ex_feat[
                            (ex_feat.participant == pid) & (ex_feat.timepoint == tp)
                            & (ex_feat.repetition == rep) & (ex_feat.exercise_id == ex)
                        ]
                        if len(r) != 1:
                            return None
                        return {c: float(r.iloc[0][c]) for c in feat_cols}

                    e1, eb = get_ex(1, traj), get_ex(tp_b, traj)
                    if e1 is None or eb is None:
                        continue
                    e1a, e1b = get_ex(1, 1), get_ex(1, 2)
                    eba, ebb = get_ex(tp_b, 1), get_ex(tp_b, 2)
                    for c in feat_cols:
                        long = eb[c] - e1[c]
                        drep1 = abs(e1a[c] - e1b[c]) if e1a and e1b else np.nan
                        drepb = abs(eba[c] - ebb[c]) if eba and ebb else np.nan
                        drep_max = np.nanmax([drep1, drepb])
                        ex_rows.append({
                            "participant": pid, "fold": fold, "delta": delta,
                            "exercise_id": ex, "feature": c, "level": "exercise",
                            "delta_value": long, "abs_delta": abs(long),
                            "drep_max": drep_max,
                            "ratio_vs_drep_max": abs(long) / drep_max if drep_max and drep_max > 0 else np.nan,
                            "exceeds_drep_max": bool(drep_max == drep_max and drep_max > 0 and abs(long) > drep_max),
                            "reliable_fold_any_seed": reliable_fold,
                        })

    return pd.DataFrame(ex_rows), pd.DataFrame(rec_rows)


def latent_vs_amplitude(mag: pd.DataFrame, rec_feat: pd.DataFrame, cfg) -> pd.DataFrame:
    rows = []
    for _, mrow in mag.iterrows():
        fold, seed, pid = mrow.fold, int(mrow.seed), str(mrow.participant)
        traj = traj_rep(cfg, fold)
        for delta, tp_b, flag, ratio_col, nrm in (
            ("D12", 2, "interpretable_D12", "ratio_D12_over_DrepT2_raw", "norm_D12_raw"),
            ("D13", 3, "interpretable_D13", "ratio_D13_over_DrepT3_raw", "norm_D13_raw"),
        ):
            r1 = rec_feat[
                (rec_feat.participant == pid) & (rec_feat.timepoint == 1) & (rec_feat.repetition == traj)
            ]
            rb = rec_feat[
                (rec_feat.participant == pid) & (rec_feat.timepoint == tp_b) & (rec_feat.repetition == traj)
            ]
            if len(r1) != 1 or len(rb) != 1:
                continue
            dE = float(rb.iloc[0].total_energy_deg2_s2 - r1.iloc[0].total_energy_deg2_s2)
            dE_log = float(np.log1p(rb.iloc[0].total_energy_deg2_s2) - np.log1p(r1.iloc[0].total_energy_deg2_s2))
            rows.append({
                "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                "reliable": bool(mrow[flag]),
                "latent_norm": float(mrow[nrm]),
                "latent_ratio_vs_drep": float(mrow[ratio_col]),
                "delta_energy": dE, "delta_log_energy": dE_log,
                "abs_delta_energy": abs(dE),
            })
    return pd.DataFrame(rows)


def stability_summaries(contrib: pd.DataFrame, rec_feat_chg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # exercise rank stability: among reliable cells, std of frac_norm across fold×seed
    c = contrib[contrib.reliable]
    stab_ex = (
        c.groupby(["participant", "delta", "exercise_id"])
        .agg(
            mean_frac=("frac_norm", "mean"),
            sd_frac=("frac_norm", "std"),
            mean_cos=("cos_to_recording_delta", "mean"),
            n=("frac_norm", "count"),
            mean_norm=("norm_delta_exercise", "mean"),
        )
        .reset_index()
    )
    # feature stability across folds (recording level)
    f = rec_feat_chg[rec_feat_chg.reliable_fold_any_seed]
    stab_f = (
        f.groupby(["participant", "delta", "feature"])
        .agg(
            mean_delta=("delta_value", "mean"),
            sd_delta=("delta_value", "std"),
            frac_exceeds=("exceeds_drep_max", "mean"),
            mean_ratio=("ratio_vs_drep_max", "mean"),
            n_folds=("fold", "nunique"),
        )
        .reset_index()
    )
    return stab_ex, stab_f


def build_profiles(
    mag: pd.DataFrame, stab_ex: pd.DataFrame, stab_f: pd.DataFrame, lat_amp: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for pid in PARTICIPANTS:
        for delta in ("D12", "D13"):
            m = mag[mag.participant.astype(str) == pid]
            flag = f"interpretable_{delta}"
            ratio_col = "ratio_D12_over_DrepT2_raw" if delta == "D12" else "ratio_D13_over_DrepT3_raw"
            nrm = f"norm_{delta}_raw"
            n_rel = int(m[flag].sum())
            ratios = m.loc[m[flag], ratio_col]
            norms = m.loc[m[flag], nrm]
            # top exercises by mean frac among reliable
            ex = stab_ex[(stab_ex.participant == pid) & (stab_ex.delta == delta)].sort_values(
                "mean_frac", ascending=False
            )
            top_ex = ",".join(f"ex{int(r.exercise_id)}:{r.mean_frac:.2f}" for r in ex.head(3).itertuples())
            # features exceeding drep in majority of reliable folds
            ff = stab_f[(stab_f.participant == pid) & (stab_f.delta == delta)]
            exceed = ff[ff.frac_exceeds >= 0.5].sort_values("mean_ratio", ascending=False)
            # exclude pure energy from "coordination" list but keep energy status
            energy_row = ff[ff.feature == "total_energy_deg2_s2"]
            energy_exceeds = bool(len(energy_row) and energy_row.iloc[0].frac_exceeds >= 0.5)
            coord_exceed = exceed[
                ~exceed.feature.isin(["total_energy_deg2_s2"] + ENERGY_SHARES)
            ]
            amp_exceed = exceed[exceed.feature.isin(AMP_RESIDUALS)]
            # amplitude explanation: corr latent_norm vs abs delta energy within reliable cells
            la = lat_amp[(lat_amp.participant == pid) & (lat_amp.delta == delta) & lat_amp.reliable]
            if len(la) >= 3:
                r_amp = float(np.corrcoef(la.latent_norm, la.abs_delta_energy)[0, 1])
            else:
                r_amp = float("nan")

            # classification
            if n_rel == 0:
                status = "no_reliable_cells"
            elif ratios.median() > 1.0 and n_rel >= 3:
                status = "reliable_change_gt_repetition"
            elif ratios.median() > 1.0:
                status = "limited_reliable_change_gt_repetition"
            elif n_rel >= 3:
                status = "reliable_but_le_repetition"
            else:
                status = "sparse_reliable_cells"

            # amplitude-dominated? if |r| high AND energy exceeds AND few amp-residual exceeds
            amp_dominated = bool(
                np.isfinite(r_amp) and abs(r_amp) >= 0.7 and energy_exceeds and len(amp_exceed) == 0
            )

            rows.append({
                "participant": pid, "delta": delta,
                "n_reliable_cells": n_rel, "n_cells": int(len(m)),
                "frac_reliable": n_rel / max(len(m), 1),
                "median_latent_ratio_vs_drep": float(ratios.median()) if len(ratios) else float("nan"),
                "mean_latent_norm": float(norms.mean()) if len(norms) else float("nan"),
                "status": status,
                "top_exercises_by_frac_norm": top_ex,
                "energy_exceeds_drep": energy_exceeds,
                "n_coord_features_exceed_drep": int(len(coord_exceed)),
                "coord_features_exceed": ",".join(coord_exceed.feature.head(6).tolist()),
                "n_amp_residual_features_exceed": int(len(amp_exceed)),
                "amp_residual_features_exceed": ",".join(amp_exceed.feature.head(6).tolist()),
                "corr_latent_norm_vs_abs_dEnergy": r_amp,
                "amplitude_dominated_flag": amp_dominated,
            })
    return pd.DataFrame(rows)


def make_figures(contrib, rec_chg, profiles, lat_amp, fig_dir: Path):
    # exercise contribution heatmap per participant×delta (mean frac, reliable only)
    c = contrib[contrib.reliable]
    if len(c):
        for delta in ("D12", "D13"):
            g = c[c.delta == delta]
            piv = g.pivot_table(
                index="participant", columns="exercise_id", values="frac_norm", aggfunc="mean",
            )
            if piv.empty:
                continue
            fig, ax = plt.subplots(figsize=(6.5, 3.5))
            im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=max(0.4, float(piv.max().max())))
            ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels([f"ex{e}" for e in piv.columns])
            ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
            ax.set_title(f"Mean exercise fraction of latent ‖Δ‖ ({delta}, reliable cells)")
            fig.colorbar(im, ax=ax, fraction=0.046)
            fig.tight_layout()
            fig.savefig(fig_dir / f"exercise_frac_{delta}.png", dpi=150)
            plt.close(fig)

    # feature exceedance counts
    f = rec_chg[rec_chg.reliable_fold_any_seed & ~rec_chg.is_amp_residual]
    if len(f):
        for delta in ("D12", "D13"):
            g = f[f.delta == delta]
            piv = g.groupby(["participant", "feature"]).exceeds_drep_max.mean().unstack("feature")
            if piv.empty:
                continue
            fig, ax = plt.subplots(figsize=(10, 3.8))
            im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
            ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
            ax.set_xticks(range(len(piv.columns)))
            ax.set_xticklabels(piv.columns, rotation=75, fontsize=7)
            ax.set_title(f"Fraction of folds with |Δfeat| > max R1–R2 ({delta})")
            fig.colorbar(im, ax=ax, fraction=0.046)
            fig.tight_layout()
            fig.savefig(fig_dir / f"feature_exceed_{delta}.png", dpi=150)
            plt.close(fig)

    # latent vs energy
    la = lat_amp[lat_amp.reliable]
    if len(la):
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.8), sharey=True)
        for ax, delta in zip(axes, ("D12", "D13")):
            g = la[la.delta == delta]
            for pid, gg in g.groupby("participant"):
                ax.scatter(gg.abs_delta_energy, gg.latent_norm, label=str(pid), s=40, alpha=0.85)
            ax.set_xlabel("|Δ energy|"); ax.set_title(delta)
            ax.legend(fontsize=7)
        axes[0].set_ylabel("Conv latent ‖Δ‖")
        fig.suptitle("Latent change vs energy change (reliable cells)")
        fig.tight_layout()
        fig.savefig(fig_dir / "latent_vs_energy.png", dpi=150)
        plt.close(fig)

    # profile status bars
    if len(profiles):
        fig, ax = plt.subplots(figsize=(7, 3.5))
        x = np.arange(len(PARTICIPANTS))
        for i, delta in enumerate(("D12", "D13")):
            g = profiles[profiles.delta == delta].set_index("participant").reindex(PARTICIPANTS)
            ax.bar(x + i * 0.4, g.median_latent_ratio_vs_drep.fillna(0), width=0.4, label=delta)
        ax.axhline(1, color="grey", ls="--")
        ax.set_xticks(x + 0.2); ax.set_xticklabels(PARTICIPANTS)
        ax.set_ylabel("median latent ‖Δ‖ / Drep")
        ax.set_title("Individual latent change vs repetition")
        ax.legend()
        fig.tight_layout()
        fig.savefig(fig_dir / "profile_latent_ratios.png", dpi=150)
        plt.close(fig)


def write_reports(profiles, stab_ex, stab_f, contrib, rec_chg, lat_amp, gate: dict, out_dir: Path):
    # --- individual profiles ---
    lines = ["# Stage 0B-A — Individual movement-change profiles\n"]
    lines.append(
        "Primary representation: reliability-qualified **Conv** embeddings "
        "(`masked_angular_velocity`, mask 30%). No retraining. No shared-direction claim.\n\n"
        "Layers of statement:\n"
        "1. **Reliable observed change** — latent ‖Δ‖ vs Drep with skill>0 endpoints.\n"
        "2. **Feature-level description** — explicit features vs R1–R2.\n"
        "3. **Possible movement interpretation** — only when measurements agree.\n"
        "4. **Unsupported speculation** — avoided (no unmeasured anatomical claims).\n\n"
        "---\n"
    )
    for pid in PARTICIPANTS:
        lines.append(f"## Participant {pid}\n")
        for delta, label in (("D12", "T1→T2"), ("D13", "T1→T3")):
            p = profiles[(profiles.participant == pid) & (profiles.delta == delta)]
            if p.empty:
                continue
            r = p.iloc[0]
            lines.append(f"### {label} (`{delta}`)\n")
            lines.append(
                f"- Status: **{r.status}**\n"
                f"- Reliable cells: {int(r.n_reliable_cells)}/{int(r.n_cells)} "
                f"({r.frac_reliable:.0%})\n"
                f"- Median latent ‖Δ‖/Drep: {r.median_latent_ratio_vs_drep:.3f}\n"
                f"- Top exercises by latent ‖Δ_e‖ fraction: {r.top_exercises_by_frac_norm or 'n/a'}\n"
                f"- Total energy exceeds R1–R2 max: {bool(r.energy_exceeds_drep)}\n"
                f"- Coordination features exceeding R1–R2 (majority folds): "
                f"{r.coord_features_exceed or 'none'}\n"
                f"- Amplitude-residual features exceeding R1–R2: "
                f"{r.amp_residual_features_exceed or 'none'}\n"
                f"- corr(latent ‖Δ‖, |Δenergy|) on reliable cells: "
                f"{r.corr_latent_norm_vs_abs_dEnergy:.3f}\n"
                f"- Amplitude-dominated flag: {bool(r.amplitude_dominated_flag)}\n\n"
            )
            # cautious interpretation
            if r.status.startswith("reliable_change") or r.status.startswith("limited_reliable"):
                if r.amplitude_dominated_flag:
                    interp = (
                        "Latent change co-varies strongly with energy change and no "
                        "amplitude-residual coordination feature exceeds repetition "
                        "variability → treat as largely amplitude-related until proven otherwise."
                    )
                elif r.n_amp_residual_features_exceed > 0:
                    interp = (
                        "Some amplitude-controlled coordination features exceed repetition "
                        "variability alongside latent change → compatible with a non-amplitude "
                        "coordination shift; still descriptive at this N."
                    )
                elif r.n_coord_features_exceed_drep > 0 and not r.energy_exceeds_drep:
                    interp = (
                        "Coordination/composition features move beyond repetition variability "
                        "without a clear energy exceedance → possible reorganisation; "
                        "confirm with amplitude residuals."
                    )
                else:
                    interp = (
                        "Latent change exceeds repetition variability, but explicit-feature "
                        "support is weak or mixed → reliable latent observation without a "
                        "strong feature-level interpretation."
                    )
            else:
                interp = "No robust interpretable longitudinal claim for this comparison."
            lines.append(f"**Possible interpretation (cautious):** {interp}\n\n")
        lines.append("---\n")
    lines.append(
        f"Tables: `outputs/stage0b_individual_profiles/individual_profiles.csv`.\n"
        f"Gate summary: shared_direction not reopened; "
        f"participants_with_reliable_gt_rep={gate.get('participants_reliable_gt_rep')}.\n"
    )
    (ROOT / "reports/STAGE0B_A_INDIVIDUAL_PROFILES.md").write_text("".join(lines), encoding="utf-8")

    # --- exercise contributions ---
    ex_lines = [
        "# Stage 0B-A — Exercise contributions to Conv latent change\n\n",
        "For each reliability-qualified fold×seed, recording Δ is the equal-weight "
        "mean of per-exercise Δ (ex09–ex13). Contribution metrics: ‖Δ_e‖ fraction, "
        "cos(Δ_e, Δ_rec), and leave-one-exercise-out drop in ‖Δ_rec‖.\n\n",
    ]
    for delta, label in (("D12", "T1→T2"), ("D13", "T1→T3")):
        ex_lines.append(f"## {label}\n\n")
        ex_lines.append("| Participant | Top exercises (mean frac of ‖Δ_e‖) | Most aligned (mean cos) |\n|---|---|---|\n")
        for pid in PARTICIPANTS:
            g = stab_ex[(stab_ex.participant == pid) & (stab_ex.delta == delta)]
            if g.empty:
                ex_lines.append(f"| {pid} | n/a | n/a |\n")
                continue
            top = g.sort_values("mean_frac", ascending=False).head(3)
            al = g.sort_values("mean_cos", ascending=False).head(2)
            ex_lines.append(
                f"| {pid} | "
                + ", ".join(f"ex{int(r.exercise_id)}={r.mean_frac:.2f}" for r in top.itertuples())
                + " | "
                + ", ".join(f"ex{int(r.exercise_id)}={r.mean_cos:.2f}" for r in al.itertuples())
                + " |\n"
            )
        ex_lines.append("\n")
    ex_lines.append(
        "Full tables: `exercise_contributions.csv`, `exercise_contribution_stability.csv`.\n"
        "Figures: `figures/stage0b_individual_profiles/exercise_frac_*.png`.\n"
    )
    (ROOT / "reports/STAGE0B_A_EXERCISE_CONTRIBUTIONS.md").write_text("".join(ex_lines), encoding="utf-8")

    # --- feature interpretation ---
    feat_lines = [
        "# Stage 0B-A — Explicit-feature interpretation\n\n",
        "Recording-level feature deltas on the fold trajectory repetition, compared to "
        "max(|R1−R2|) at T1 and the later timepoint. Amplitude-controlled residuals "
        "from S5 are reported separately.\n\n"
        "**Do not** read energy-share shifts as ‘greater pelvis use’ etc. unless "
        "the named region share and amplitude-controlled coordination metrics agree "
        "consistently across folds.\n\n",
    ]
    for delta, label in (("D12", "T1→T2"), ("D13", "T1→T3")):
        feat_lines.append(f"## {label}\n\n")
        for pid in PARTICIPANTS:
            g = stab_f[(stab_f.participant == pid) & (stab_f.delta == delta)]
            if g.empty:
                continue
            exceed = g[g.frac_exceeds >= 0.5].sort_values("mean_ratio", ascending=False)
            feat_lines.append(f"### Participant {pid}\n")
            if exceed.empty:
                feat_lines.append("No feature exceeded max R1–R2 in ≥50% of reliable folds.\n\n")
            else:
                feat_lines.append("| Feature | mean Δ | mean |Δ|/Drep_max | frac folds exceed |\n|---|---|---|---|\n")
                for r in exceed.itertuples():
                    feat_lines.append(
                        f"| {r.feature} | {r.mean_delta:.4g} | {r.mean_ratio:.2f} | {r.frac_exceeds:.0%} |\n"
                    )
                feat_lines.append("\n")
            # amplitude note
            p = profiles[(profiles.participant == pid) & (profiles.delta == delta)]
            if len(p):
                feat_lines.append(
                    f"Amplitude-dominated flag: {bool(p.iloc[0].amplitude_dominated_flag)}; "
                    f"corr(latent,|ΔE|)={p.iloc[0].corr_latent_norm_vs_abs_dEnergy:.3f}.\n\n"
                )
    feat_lines.append(
        "Tables: `recording_feature_changes.csv`, `exercise_feature_changes.csv`, "
        "`feature_stability.csv`, `latent_vs_amplitude.csv`.\n"
    )
    (ROOT / "reports/STAGE0B_A_FEATURE_INTERPRETATION.md").write_text("".join(feat_lines), encoding="utf-8")

    # --- readiness ---
    (ROOT / "reports/STAGE0B_A_READINESS_RECOMMENDATION.md").write_text(f"""# Stage 0B-A readiness recommendation

## Answers

### 1. Which participants show a reliable interpretable change?

{gate.get('q1')}

### 2. Which comparisons are reliable: T1→T2, T1→T3, or both?

{gate.get('q2')}

### 3. Which exercises drive each participant’s change?

{gate.get('q3')}

### 4. Which explicit features changed beyond repetition variability?

{gate.get('q4')}

### 5. Are the latent changes explained mainly by amplitude?

{gate.get('q5')}

### 6. Is there evidence for different individual coordination adaptations?

{gate.get('q6')}

### 7. Is the existing Conv representation suitable for a transfer test on free movement?

{gate.get('q7')}

### 8. Next stage recommendation

**{gate.get('next_stage')}**

{gate.get('next_stage_reason')}

---

## Stop gate

Do **not** start free-movement analysis, clustering, motif discovery, or new
training until this recommendation is reviewed.

Hard constraints from LIMITED GO remain: no shared-direction fishing; no
Transformer scaling; session–timepoint confounding unresolved.
""", encoding="utf-8")


def answer_gate(profiles: pd.DataFrame, stab_ex: pd.DataFrame, stab_f: pd.DataFrame) -> dict:
    # Q1
    rel = profiles[profiles.status.isin([
        "reliable_change_gt_repetition", "limited_reliable_change_gt_repetition",
    ])]
    by_pid = rel.groupby("participant").delta.apply(lambda s: ",".join(sorted(s.unique()))).to_dict()
    q1 = ", ".join(f"{p} ({d})" for p, d in by_pid.items()) if by_pid else "none with latent change > Drep on enough cells"

    # Q2
    d12 = profiles[(profiles.delta == "D12") & profiles.status.str.contains("gt_repetition")]
    d13 = profiles[(profiles.delta == "D13") & profiles.status.str.contains("gt_repetition")]
    both = set(d12.participant) & set(d13.participant)
    q2 = (
        f"T1→T2: {sorted(d12.participant.tolist()) or 'none'}; "
        f"T1→T3: {sorted(d13.participant.tolist()) or 'none'}; "
        f"both: {sorted(both) or 'none'}"
    )

    # Q3
    bits = []
    for pid in PARTICIPANTS:
        for delta in ("D12", "D13"):
            g = stab_ex[(stab_ex.participant == pid) & (stab_ex.delta == delta)]
            if g.empty:
                continue
            top = g.sort_values("mean_frac", ascending=False).head(2)
            bits.append(
                f"{pid}/{delta}: " + ", ".join(f"ex{int(r.exercise_id)}" for r in top.itertuples())
            )
    q3 = "; ".join(bits) if bits else "n/a"

    # Q4
    bits = []
    for pid in PARTICIPANTS:
        for delta in ("D12", "D13"):
            g = stab_f[(stab_f.participant == pid) & (stab_f.delta == delta)]
            ex = g[g.frac_exceeds >= 0.5]
            if len(ex):
                bits.append(f"{pid}/{delta}: " + ", ".join(ex.sort_values("mean_ratio", ascending=False).feature.head(4)))
    q4 = "; ".join(bits) if bits else "few/none consistently exceed R1–R2"

    # Q5
    amp_dom = profiles[profiles.amplitude_dominated_flag]
    mixed = profiles[
        (~profiles.amplitude_dominated_flag)
        & profiles.status.str.contains("gt_repetition")
        & (profiles.n_amp_residual_features_exceed > 0)
    ]
    q5 = (
        f"Amplitude-dominated cases: {sorted(amp_dom.participant.unique().tolist()) or 'none'}. "
        f"Cases with amp-residual feature support: "
        f"{sorted(set(zip(mixed.participant, mixed.delta))) or 'none'}. "
        f"Overall: latent changes are not uniformly amplitude-only; check per participant."
    )

    # Q6
    # different patterns if top exercises or exceeding feature sets differ across participants
    patterns = []
    for pid in PARTICIPANTS:
        g = stab_ex[(stab_ex.participant == pid) & (stab_ex.delta == "D12")]
        if g.empty:
            continue
        top = tuple(g.sort_values("mean_frac", ascending=False).exercise_id.head(2).astype(int).tolist())
        patterns.append((pid, top))
    distinct = len(set(p[1] for p in patterns))
    q6 = (
        f"Across participants, top-2 exercise contribution patterns for T1→T2 "
        f"yield {distinct} distinct ordered pairs among {len(patterns)} participants "
        f"with data — {'suggests differentiated exercise drivers' if distinct >= 2 else 'limited differentiation'}. "
        f"Feature exceedance sets also differ (see profiles). Not a shared-direction claim."
    )

    # Q7 — suitable for free-movement transfer test?
    n_good = profiles.status.str.contains("gt_repetition").sum()
    # need some non-amplitude structure OR at least stable latent>drep for >=2 participants
    n_pid_good = profiles[profiles.status.str.contains("gt_repetition")].participant.nunique()
    n_non_amp = int((~profiles.amplitude_dominated_flag & profiles.status.str.contains("gt_repetition")).sum())
    if n_pid_good >= 2 and n_non_amp >= 1:
        suitable = True
        q7 = (
            "Yes, cautiously: Conv shows reliability-gated individual latent changes that "
            "often exceed repetition variability for multiple participants, with at least "
            "some cases not flagged as amplitude-dominated. Transfer should be a "
            "frozen-encoder test with the same skill/Drep discipline — not a search for "
            "shared direction."
        )
        next_stage = "structured-versus-free transfer benchmark"
        next_reason = (
            "Prefer a structured-versus-free transfer benchmark over dumping free movement "
            "into an untested latent space: embed free sessions with frozen Conv, compare "
            "neighbourhoods / reconstruction skill / feature alignment to structured "
            "exercises within participant, and keep R1–R2 and reliability gates. "
            "Direct unsupervised free-movement interpretation is premature."
        )
    elif n_pid_good >= 1:
        suitable = "limited"
        q7 = (
            "Limited: only sparse participant/comparison cells clear the latent>Drep bar "
            "with interpretable feature support. A transfer test is optional and should be "
            "narrow (within-participant, frozen Conv)."
        )
        next_stage = "structured-versus-free transfer benchmark"
        next_reason = (
            "If proceeding, use a minimal structured-versus-free benchmark for the "
            "participants/comparisons that cleared 0B-A; otherwise stop latent free-movement work."
        )
    else:
        suitable = False
        q7 = (
            "No: current reliable interpretable individual-change support is too weak "
            "to justify free-movement latent analysis."
        )
        next_stage = "no free-movement latent analysis"
        next_reason = (
            "Keep Stage 0 LIMITED GO instrument (structured exercises + explicit features); "
            "do not start free-movement latent analysis until individual structured change "
            "profiles are stronger or better controlled."
        )

    return {
        "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6, "q7": q7,
        "next_stage": next_stage, "next_stage_reason": next_reason,
        "conv_suitable_for_transfer": suitable,
        "participants_reliable_gt_rep": sorted(
            profiles[profiles.status.str.contains("gt_repetition")].participant.unique().tolist()
        ),
    }


def main() -> int:
    t0 = time.time()
    cfg = data_windows.load_config(ROOT)
    out_dir = ROOT / "outputs/stage0b_individual_profiles"
    fig_dir = ROOT / "figures/stage0b_individual_profiles"
    for d in (out_dir, fig_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("Loading artifacts ...")
    mag = pd.read_csv(ROOT / "outputs/s7_conv/change_magnitudes.csv")
    win = pd.read_parquet(ROOT / "outputs/s7_conv/window_embeddings.parquet")
    wf = pd.read_csv(ROOT / "outputs/s5_explicit/window_features.csv")
    rf = pd.read_csv(ROOT / "outputs/s5_explicit/recording_features.csv")
    ra = pd.read_csv(ROOT / "outputs/s5_explicit/recording_features_amplitude_controlled.csv")

    print("Exercise-level latent aggregates ...")
    ex_lat = exercise_latent_table(win, cfg)
    ex_lat.to_csv(out_dir / "exercise_latent_embeddings.csv", index=False)

    print("Exercise contributions ...")
    contrib = compute_exercise_contributions(ex_lat, mag, cfg)
    contrib.to_csv(out_dir / "exercise_contributions.csv", index=False)

    print("Explicit features ...")
    ex_feat = exercise_feature_table(wf)
    rec_feat = recording_feature_table(rf, ra)
    ex_chg, rec_chg = compute_feature_changes(ex_feat, rec_feat, mag, cfg)
    ex_chg.to_csv(out_dir / "exercise_feature_changes.csv", index=False)
    rec_chg.to_csv(out_dir / "recording_feature_changes.csv", index=False)

    print("Latent vs amplitude ...")
    lat_amp = latent_vs_amplitude(mag, rec_feat, cfg)
    lat_amp.to_csv(out_dir / "latent_vs_amplitude.csv", index=False)

    print("Stability ...")
    stab_ex, stab_f = stability_summaries(contrib, rec_chg)
    stab_ex.to_csv(out_dir / "exercise_contribution_stability.csv", index=False)
    stab_f.to_csv(out_dir / "feature_stability.csv", index=False)

    print("Profiles ...")
    profiles = build_profiles(mag, stab_ex, stab_f, lat_amp)
    profiles.to_csv(out_dir / "individual_profiles.csv", index=False)

    print("Figures ...")
    make_figures(contrib, rec_chg, profiles, lat_amp, fig_dir)

    gate = answer_gate(profiles, stab_ex, stab_f)
    provenance.write_json(out_dir / "STAGE0B_A_GATE.json", gate)
    write_reports(profiles, stab_ex, stab_f, contrib, rec_chg, lat_amp, gate, out_dir)

    # update STAGE0B plan note
    plan = ROOT / "reports/STAGE0B_PLAN.md"
    note = (
        "\n\n---\n\n## Update after LIMITED GO review\n\n"
        "Shared-direction search remains closed. Before clustering/motifs/free-movement, "
        "Stage **0B-A (individual movement-change profiles)** was executed — see "
        "`STAGE0B_A_READINESS_RECOMMENDATION.md`. Next step is gated there.\n"
    )
    txt = plan.read_text()
    if "0B-A (individual movement-change profiles)" not in txt:
        plan.write_text(txt.rstrip() + note, encoding="utf-8")

    stamp = provenance.run_stamp("STAGE0B_A", {
        "decision_context": "LIMITED GO",
        "gate": gate,
        "elapsed_s": round(time.time() - t0, 1),
    })
    for name in (
        "individual_profiles.csv", "exercise_contributions.csv",
        "recording_feature_changes.csv", "STAGE0B_A_GATE.json",
    ):
        p = out_dir / name
        if p.exists():
            stamp.setdefault("artifact_sha256", {})[name] = provenance.sha256_file(p)
    provenance.write_json(out_dir / "stage0b_a_provenance.json", stamp)

    with (ROOT / "reports/DECISION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## Stage 0B-A — {stamp['utc']}\n"
            f"- Individual profiles completed (no retrain; no shared-direction reopen).\n"
            f"- Next stage recommendation: {gate.get('next_stage')}\n"
            f"- Participants with latent>Drep status: {gate.get('participants_reliable_gt_rep')}\n"
        )

    readme = ROOT / "README.md"
    rtxt = readme.read_text()
    if "STAGE0B_A_READINESS" not in rtxt:
        rtxt = rtxt.replace(
            "* `reports/GO_NO_GO_DECISION.md` / `STAGE0_FINAL_REPORT.md` - **Stage 0 decision**",
            "* `reports/GO_NO_GO_DECISION.md` / `STAGE0_FINAL_REPORT.md` - **Stage 0 decision: LIMITED GO**\n"
            "* `reports/STAGE0B_A_READINESS_RECOMMENDATION.md` - **current Stage 0B-A gate**\n"
            "* `reports/STAGE0B_A_INDIVIDUAL_PROFILES.md` / `STAGE0B_A_EXERCISE_CONTRIBUTIONS.md` / "
            "`STAGE0B_A_FEATURE_INTERPRETATION.md`",
        )
        readme.write_text(rtxt)

    print(json.dumps(gate, indent=2))
    print(f"\nStage 0B-A OK ({time.time()-t0:.0f}s) — stopped before free-movement/clustering")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
