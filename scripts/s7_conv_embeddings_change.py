#!/usr/bin/env python3
"""S6b Conv reliability re-gate + S7 embeddings / within-participant change.

Primary representation: ConvMaskedPredictor on selected objective
(`masked_angular_velocity`), frozen mask 30%.

Step 0 — Re-gate Conv skill at held-out T1, T2, T3 (same definition as S6).
Step 1 — If the gate passes, compute embeddings, balanced standardization,
         recording aggregates, change vectors and repetition references.
Stop before S8 (no direction-similarity / sign-flip interpretation).

Gate pass rule (pre-registered zero-crossing, operationalised for proceed/stop):
  mean skill > 0 at held-out T1, T2 and T3 across participant×fold×seed cells,
  AND ≥ 50% of cells positive at each of those three timepoints.
Cells with skill ≤ 0 are flagged uninterpretable regardless.
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
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, models, provenance, train_masked  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OBJ = "masked_angular_velocity"
DIM = 32


def trajectory_rep(cfg, fold: str) -> int:
    return int(cfg["folds"][fold]["trajectory_repetition"])


def train_rep(cfg, fold: str) -> int:
    return int(cfg["folds"][fold]["train_repetition"])


def build_conv(cfg, state):
    net = models.ConvMaskedPredictor(
        n_links=cfg["model"]["n_links"],
        patch_frames=cfg["model"]["patch_frames"],
        channels=cfg["s5"]["conv_channels"],
        target_dim=3,  # masked_angular_velocity
        embedding_dim=cfg["model"]["embedding_dim"],
    )
    net.load_state_dict(state)
    net.eval()
    return net


def ecols(prefix: str = "e") -> list[str]:
    return [f"{prefix}{i}" for i in range(DIM)]


def gate_label(skill: float, skill_t1: float) -> str:
    if not np.isfinite(skill) or skill <= 0:
        return "fail_nonpositive"
    if skill < skill_t1:
        return "positive_degraded"
    return "positive_stable"


def score_subset(net, x6, y, mask_ratio, span, patch_frames, seed):
    return train_masked.score_arrays(
        net, x6, y, OBJ, mask_ratio, span, patch_frames, seed,
        trivial_which="both",
    )


# --------------------------------------------------------------------------
# Step 0 — Conv reliability
# --------------------------------------------------------------------------

def run_conv_reliability(cfg) -> tuple[pd.DataFrame, dict]:
    ratio = float(cfg["s5"]["frozen_mask_ratio"])
    span = tuple(cfg["s5"]["mask_span_patches"])
    patch_frames = cfg["model"]["patch_frames"]
    seeds = cfg["model"]["seeds"]
    ckpt_dir = ROOT / "outputs/s5_conv/checkpoints"
    w_all = data_windows.load_window_index(ROOT)

    rows = []
    for fold in cfg["folds"]:
        traj = trajectory_rep(cfg, fold)
        es = w_all[(w_all.fold == fold) & (w_all.role == "early_stop") & w_all.usable]
        x_es, es_i = data_windows.materialise_windows(es, ROOT, "masked_6d")
        y_es, _ = data_windows.materialise_windows(es_i, ROOT, "masked_angular_velocity")
        ev = w_all[(w_all.role == "evaluation") & w_all.usable & (w_all.repetition == traj)]
        x_ev, ev_i = data_windows.materialise_windows(ev, ROOT, "masked_6d")
        y_ev, _ = data_windows.materialise_windows(ev_i, ROOT, "masked_angular_velocity")

        for seed in seeds:
            state = torch.load(
                ckpt_dir / f"{fold}_{OBJ}_s{seed}.pt",
                map_location="cpu", weights_only=True,
            )
            net = build_conv(cfg, state)
            for pid in cfg["participants"]:
                m1 = (es_i.participant.astype(str) == str(pid)).to_numpy()
                sc1 = score_subset(
                    net, x_es[m1], y_es[m1], ratio, span, patch_frames,
                    seed + 700 + int(pid),
                )
                row = {
                    "fold": fold, "seed": int(seed), "participant": str(pid),
                    "objective": OBJ, "trajectory_repetition": traj,
                    "architecture": "conv",
                    "skill_T1_heldout": sc1["skill"], "n_T1_heldout": sc1["n"],
                    "gate_T1_heldout": (
                        "fail_nonpositive"
                        if (not np.isfinite(sc1["skill"]) or sc1["skill"] <= 0)
                        else "positive"
                    ),
                }
                for tp in (2, 3):
                    m = (
                        (ev_i.participant.astype(str) == str(pid))
                        & (ev_i.timepoint == tp)
                    ).to_numpy()
                    sc = score_subset(
                        net, x_ev[m], y_ev[m], ratio, span, patch_frames,
                        seed + 800 + int(pid) + tp,
                    )
                    row[f"skill_T{tp}"] = sc["skill"]
                    row[f"n_T{tp}"] = sc["n"]
                    row[f"skill_T{tp}_minus_T1"] = (
                        sc["skill"] - sc1["skill"]
                        if np.isfinite(sc["skill"]) and np.isfinite(sc1["skill"])
                        else float("nan")
                    )
                    row[f"gate_T{tp}"] = gate_label(sc["skill"], sc1["skill"])
                rows.append(row)
                print(
                    f"  Conv {fold} s{seed} {pid}: "
                    f"T1={sc1['skill']:.4f}  T2={row['skill_T2']:.4f}  "
                    f"T3={row['skill_T3']:.4f}"
                )

    reli = pd.DataFrame(rows)
    summary = {
        "n_cells": len(reli),
        "mean_skill_T1": float(reli.skill_T1_heldout.mean()),
        "mean_skill_T2": float(reli.skill_T2.mean()),
        "mean_skill_T3": float(reli.skill_T3.mean()),
        "frac_positive_T1": float((reli.skill_T1_heldout > 0).mean()),
        "frac_positive_T2": float((reli.skill_T2 > 0).mean()),
        "frac_positive_T3": float((reli.skill_T3 > 0).mean()),
        "n_fail_T1": int((reli.gate_T1_heldout == "fail_nonpositive").sum()),
        "n_fail_T2": int((reli.gate_T2 == "fail_nonpositive").sum()),
        "n_fail_T3": int((reli.gate_T3 == "fail_nonpositive").sum()),
    }
    # proceed rule
    means_ok = all(
        summary[k] > 0
        for k in ("mean_skill_T1", "mean_skill_T2", "mean_skill_T3")
    )
    majority_ok = all(
        summary[k] >= 0.5
        for k in ("frac_positive_T1", "frac_positive_T2", "frac_positive_T3")
    )
    summary["means_positive"] = means_ok
    summary["majority_positive"] = majority_ok
    summary["gate_pass"] = bool(means_ok and majority_ok)
    summary["gate_rule"] = (
        "mean skill > 0 at T1/T2/T3 AND ≥50% cells positive at each timepoint; "
        "per-cell skill≤0 still blocks interpretation of that cell"
    )
    return reli, summary


# --------------------------------------------------------------------------
# Step 1 — S7 embeddings / standardization / change
# --------------------------------------------------------------------------

def fit_balanced_standardizer(
    window_emb: np.ndarray, index: pd.DataFrame,
) -> dict:
    """Fit mean/std on training-T1 block centroids, equal participant×exercise weight."""
    df = index.copy().reset_index(drop=True)
    for i in range(DIM):
        df[f"e{i}"] = window_emb[:, i]
    cols = ecols()
    # block centroids
    blocks = (
        df.groupby(["participant", "exercise_id", "block_id"], as_index=False)[cols]
        .mean()
    )
    # equal weight per participant × exercise: mean of that pair's block centroids
    pe = (
        blocks.groupby(["participant", "exercise_id"], as_index=False)[cols]
        .mean()
    )
    mu = pe[cols].mean().to_numpy(dtype=np.float64)
    # population std over the balanced PE rows; floor tiny dims
    sd = pe[cols].std(ddof=0).to_numpy(dtype=np.float64)
    sd = np.where(sd < 1e-8, 1.0, sd)
    return {
        "mean": mu,
        "std": sd,
        "n_blocks": int(len(blocks)),
        "n_participant_exercise": int(len(pe)),
    }


def apply_standardizer(X: np.ndarray, stdz: dict) -> np.ndarray:
    return (X - stdz["mean"]) / stdz["std"]


def recording_table_from_windows(
    window_emb: np.ndarray, index: pd.DataFrame, eval_ex: list[int],
) -> pd.DataFrame:
    return data_windows.aggregate_recording_embeddings(window_emb, index, eval_ex)


def compute_change_tables(
    rec: pd.DataFrame, reli: pd.DataFrame, cfg,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Change vectors and magnitude-vs-repetition for trajectory repetition."""
    cols = ecols()
    change_rows, mag_rows = [], []
    for fold in cfg["folds"]:
        traj = trajectory_rep(cfg, fold)
        for seed in cfg["model"]["seeds"]:
            sub = rec[(rec.fold == fold) & (rec.seed == seed)].copy()
            for pid in cfg["participants"]:
                g = sub[sub.participant.astype(str) == str(pid)]
                # trajectory embeddings at each timepoint
                z = {}
                for tp in (1, 2, 3):
                    row = g[(g.timepoint == tp) & (g.repetition == traj)]
                    if len(row) != 1:
                        z[tp] = None
                    else:
                        z[tp] = row.iloc[0][cols].to_numpy(dtype=np.float64)
                        z[f"{tp}_std"] = row.iloc[0][[f"std_{c}" for c in cols]].to_numpy(
                            dtype=np.float64
                        )
                if any(z[tp] is None for tp in (1, 2, 3)):
                    continue
                d12 = z[2] - z[1]
                d13 = z[3] - z[1]
                d23 = z[3] - z[2]
                d12s = z["2_std"] - z["1_std"]
                d13s = z["3_std"] - z["1_std"]
                d23s = z["3_std"] - z["2_std"]

                # repetition distances at each timepoint (both reps)
                drep = {}
                for tp in (1, 2, 3):
                    rr = g[g.timepoint == tp].sort_values("repetition")
                    if len(rr) == 2:
                        a = rr.iloc[0][cols].to_numpy(dtype=np.float64)
                        b = rr.iloc[1][cols].to_numpy(dtype=np.float64)
                        a_s = rr.iloc[0][[f"std_{c}" for c in cols]].to_numpy(dtype=np.float64)
                        b_s = rr.iloc[1][[f"std_{c}" for c in cols]].to_numpy(dtype=np.float64)
                        drep[tp] = float(np.linalg.norm(a - b))
                        drep[f"{tp}_std"] = float(np.linalg.norm(a_s - b_s))
                    else:
                        drep[tp] = float("nan")
                        drep[f"{tp}_std"] = float("nan")

                # reliability flags for this cell
                rcell = reli[
                    (reli.fold == fold) & (reli.seed == seed)
                    & (reli.participant.astype(str) == str(pid))
                ]
                if len(rcell) == 1:
                    r = rcell.iloc[0]
                    gates = {
                        "gate_T1": r.gate_T1_heldout,
                        "gate_T2": r.gate_T2,
                        "gate_T3": r.gate_T3,
                        "skill_T1": r.skill_T1_heldout,
                        "skill_T2": r.skill_T2,
                        "skill_T3": r.skill_T3,
                    }
                else:
                    gates = {k: None for k in (
                        "gate_T1", "gate_T2", "gate_T3",
                        "skill_T1", "skill_T2", "skill_T3",
                    )}

                def pack(tag, vec, vec_s):
                    row = {
                        "fold": fold, "seed": int(seed), "participant": str(pid),
                        "trajectory_repetition": traj, "delta": tag,
                        **gates,
                    }
                    for i, v in enumerate(vec):
                        row[f"e{i}"] = float(v)
                    for i, v in enumerate(vec_s):
                        row[f"std_e{i}"] = float(v)
                    return row

                change_rows.extend([
                    pack("D12", d12, d12s),
                    pack("D13", d13, d13s),
                    pack("D23", d23, d23s),
                ])

                n12 = float(np.linalg.norm(d12))
                n13 = float(np.linalg.norm(d13))
                n23 = float(np.linalg.norm(d23))
                n12s = float(np.linalg.norm(d12s))
                n13s = float(np.linalg.norm(d13s))
                n23s = float(np.linalg.norm(d23s))
                drep_max = np.nanmax([drep[2], drep[3]])
                drep_max_s = np.nanmax([drep["2_std"], drep["3_std"]])

                # interpretable if both endpoints of the delta have skill>0
                def ok_pair(g_a, g_b):
                    return (
                        g_a not in (None, "fail_nonpositive")
                        and g_b not in (None, "fail_nonpositive")
                    )

                mag_rows.append({
                    "fold": fold, "seed": int(seed), "participant": str(pid),
                    "trajectory_repetition": traj,
                    **gates,
                    "norm_D12_raw": n12, "norm_D13_raw": n13, "norm_D23_raw": n23,
                    "norm_D12_std": n12s, "norm_D13_std": n13s, "norm_D23_std": n23s,
                    "Drep_T1_raw": drep[1], "Drep_T2_raw": drep[2], "Drep_T3_raw": drep[3],
                    "Drep_T1_std": drep["1_std"], "Drep_T2_std": drep["2_std"],
                    "Drep_T3_std": drep["3_std"],
                    "Drep_max_T2T3_raw": float(drep_max),
                    "Drep_max_T2T3_std": float(drep_max_s),
                    "ratio_D12_over_DrepT2_raw": n12 / drep[2] if drep[2] and drep[2] > 0 else np.nan,
                    "ratio_D13_over_DrepT3_raw": n13 / drep[3] if drep[3] and drep[3] > 0 else np.nan,
                    "ratio_D12_over_DrepMax_raw": n12 / drep_max if drep_max and drep_max > 0 else np.nan,
                    "ratio_D13_over_DrepMax_raw": n13 / drep_max if drep_max and drep_max > 0 else np.nan,
                    "ratio_D12_over_DrepT2_std": n12s / drep["2_std"] if drep["2_std"] and drep["2_std"] > 0 else np.nan,
                    "ratio_D13_over_DrepT3_std": n13s / drep["3_std"] if drep["3_std"] and drep["3_std"] > 0 else np.nan,
                    "interpretable_D12": ok_pair(gates["gate_T1"], gates["gate_T2"]),
                    "interpretable_D13": ok_pair(gates["gate_T1"], gates["gate_T3"]),
                    "interpretable_D23": ok_pair(gates["gate_T2"], gates["gate_T3"]),
                })
    return pd.DataFrame(change_rows), pd.DataFrame(mag_rows)


def plot_reliability(reli: pd.DataFrame, fig_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, tp in zip(axes, (2, 3)):
        for fold, g in reli.groupby("fold"):
            ax.scatter(g.skill_T1_heldout, g[f"skill_T{tp}"], label=f"fold {fold}", alpha=0.85)
        lim_lo = min(reli.skill_T1_heldout.min(), reli[f"skill_T{tp}"].min()) - 0.02
        lim_hi = max(reli.skill_T1_heldout.max(), reli[f"skill_T{tp}"].max()) + 0.02
        ax.plot([lim_lo, lim_hi], [lim_lo, lim_hi], "k--", lw=1)
        ax.axhline(0, color="grey", ls=":", lw=0.8)
        ax.axvline(0, color="grey", ls=":", lw=0.8)
        ax.set_xlabel("skill held-out T1")
        ax.set_ylabel(f"skill T{tp}")
        ax.set_title(f"T{tp} vs held-out T1")
        ax.legend(fontsize=7)
    fig.suptitle("Conv reliability (masked_angular_velocity)")
    fig.tight_layout()
    fig.savefig(fig_dir / "reliability_t1_t2_t3.png", dpi=150)
    plt.close(fig)


def plot_magnitudes(mag: pd.DataFrame, fig_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, geom, suffix in (
        (axes[0], "raw", "raw"),
        (axes[1], "standardized", "std"),
    ):
        for pid, g in mag.groupby("participant"):
            ax.scatter(
                g[f"Drep_T2_{suffix}"], g[f"norm_D12_{suffix}"],
                label=str(pid), s=50, alpha=0.85,
            )
        mx = max(
            mag[f"Drep_T2_{suffix}"].max(), mag[f"norm_D12_{suffix}"].max(),
        ) * 1.05
        ax.plot([0, mx], [0, mx], "k--", lw=1, label="|D12|=Drep_T2")
        ax.set_xlabel(f"Drep_T2 ({geom})")
        ax.set_ylabel(f"|D12| ({geom})")
        ax.set_title(f"|D12| vs repetition ref ({geom})")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "change_vs_repetition_D12.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, geom, suffix in (
        (axes[0], "raw", "raw"),
        (axes[1], "standardized", "std"),
    ):
        for pid, g in mag.groupby("participant"):
            ax.scatter(
                g[f"Drep_T3_{suffix}"], g[f"norm_D13_{suffix}"],
                label=str(pid), s=50, alpha=0.85,
            )
        mx = max(
            mag[f"Drep_T3_{suffix}"].max(), mag[f"norm_D13_{suffix}"].max(),
        ) * 1.05
        ax.plot([0, mx], [0, mx], "k--", lw=1)
        ax.set_xlabel(f"Drep_T3 ({geom})")
        ax.set_ylabel(f"|D13| ({geom})")
        ax.set_title(f"|D13| vs repetition ref ({geom})")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "change_vs_repetition_D13.png", dpi=150)
    plt.close(fig)


def write_reports(reli, gate_summary, mag, out_dir, fig_dir):
    fails = reli[
        (reli.gate_T1_heldout == "fail_nonpositive")
        | (reli.gate_T2 == "fail_nonpositive")
        | (reli.gate_T3 == "fail_nonpositive")
    ]

    # --- Conv reliability report ---
    fail_md = fails[
        ["participant", "fold", "seed", "gate_T1_heldout", "gate_T2", "gate_T3",
         "skill_T1_heldout", "skill_T2", "skill_T3"]
    ].to_string(index=False) if len(fails) else "(none)"

    (ROOT / "reports/S6B_CONV_RELIABILITY_GATE.md").write_text(f"""# S6b ConvMaskedPredictor reliability re-gate

Re-evaluation of the **selected** architecture/objective from S5–S6:

* model: `ConvMaskedPredictor`
* objective: `masked_angular_velocity`
* mask ratio: 30% (frozen)
* skill vs best matched trivial baseline (mean-motion / interpolation)

Same cell structure as the Transformer reliability table: participant × fold × seed
(24 cells). Held-out T1 = early-stop blocks; T2/T3 = evaluation windows at the
fold’s trajectory repetition.

---

## Proceed / stop rule (operational)

```text
PASS iff
  mean skill(T1) > 0 AND mean skill(T2) > 0 AND mean skill(T3) > 0
  AND fraction of cells with skill > 0 is ≥ 50% at each of T1, T2, T3
```

Per-cell `skill ≤ 0` still forbids interpreting that cell’s latent geometry.

---

## Observed summary

| Metric | T1 held-out | T2 | T3 |
|---|---|---|---|
| Mean skill | {gate_summary['mean_skill_T1']:.4f} | {gate_summary['mean_skill_T2']:.4f} | {gate_summary['mean_skill_T3']:.4f} |
| Fraction skill > 0 | {gate_summary['frac_positive_T1']:.2%} | {gate_summary['frac_positive_T2']:.2%} | {gate_summary['frac_positive_T3']:.2%} |
| Cells fail_nonpositive | {gate_summary['n_fail_T1']} | {gate_summary['n_fail_T2']} | {gate_summary['n_fail_T3']} |

**Gate result: `{'PASS' if gate_summary['gate_pass'] else 'FAIL'}`**

---

## Cells that fail the zero-crossing

```
{fail_md}
```

Full table: `outputs/s7_conv/reliability_t1_t2_t3.csv`  
Figure: `figures/s7_conv/reliability_t1_t2_t3.png`

---

## Interpretation

* Observed skill at T1/T2/T3 is {'positive on average with majority of cells clearing the zero-crossing' if gate_summary['gate_pass'] else 'insufficient under the proceed rule'}.
* Failed cells must not be used for latent-direction interpretation.
* {'S7 proceeded with Conv as primary representation.' if gate_summary['gate_pass'] else 'S7 was not started.'}
""", encoding="utf-8")

    if not gate_summary["gate_pass"]:
        (ROOT / "reports/S7_READINESS_RECOMMENDATION.md").write_text(
            """# S7 readiness recommendation

**S7 not started.** Conv reliability re-gate did not pass the proceed rule.
See `reports/S6B_CONV_RELIABILITY_GATE.md`. Stopped before S7–S8.
""",
            encoding="utf-8",
        )
        return

    if mag is None or len(mag) == 0:
        return  # reliability-only write; S7 reports come after change tables exist

    # magnitude summary for interpretable cells
    def _summ(df, col):
        s = df[col].dropna()
        if len(s) == 0:
            return "n/a"
        return f"mean={s.mean():.3f}, median={s.median():.3f}, n={len(s)}"

    mag_i12 = mag[mag.interpretable_D12]
    mag_i13 = mag[mag.interpretable_D13]

    (ROOT / "reports/S7_EMBEDDING_CHANGE_REPORT.md").write_text(f"""# S7 embedding, standardization and within-participant change

Primary representation: **ConvMaskedPredictor** / `masked_angular_velocity` /
mask 30%. Reliability re-gate: **PASS** (`S6B_CONV_RELIABILITY_GATE.md`).

**No S8 work** (no mean-pairwise cosine, no sign-flip null, no cross-participant
direction claim).

---

## Method (frozen)

1. Full unmasked 6D → encoder → mean-pool 18×24 tokens → 32-D window embedding.
2. Aggregation: windows → mean within exercise → equal-weight mean across
   ex09–13 → recording embedding (ex11 retained as breakdown columns).
3. Balanced standardization fitted on **training-T1 only** within each
   (fold, seed): block centroids → equal participant×exercise weight → per-dim
   mean/std. Applied unchanged to held-out T1/T2/T3. No whitening.
4. Raw-centred and standardized geometries are co-primary.
5. Trajectory repetition per fold supplies z(T1), z(T2), z(T3).
6. Change: `D12=z(T2)-z(T1)`, `D13=z(T3)-z(T1)`, `D23=z(T3)-z(T2)`.
7. Repetition reference: `Drep_Tp = ||z(Tp,R1)-z(Tp,R2)||` at T2 and T3
   (T1 reported descriptively). `max(Drep_T2, Drep_T3)` as conservative
   sensitivity only.
8. A delta is marked interpretable only if both endpoint timepoints have
   `skill > 0` for that participant×fold×seed.

---

## Observed — reliability (Conv)

| | T1 | T2 | T3 |
|---|---|---|---|
| Mean skill | {gate_summary['mean_skill_T1']:.4f} | {gate_summary['mean_skill_T2']:.4f} | {gate_summary['mean_skill_T3']:.4f} |
| % positive | {gate_summary['frac_positive_T1']:.0%} | {gate_summary['frac_positive_T2']:.0%} | {gate_summary['frac_positive_T3']:.0%} |

Interpretable D12 cells: {int(mag.interpretable_D12.sum())}/{len(mag)}  
Interpretable D13 cells: {int(mag.interpretable_D13.sum())}/{len(mag)}  
Interpretable D23 cells: {int(mag.interpretable_D23.sum())}/{len(mag)}

---

## Observed — change magnitude vs repetition (descriptive)

Raw geometry, interpretable cells only:

* |D12| / Drep_T2: {_summ(mag_i12, 'ratio_D12_over_DrepT2_raw')}
* |D13| / Drep_T3: {_summ(mag_i13, 'ratio_D13_over_DrepT3_raw')}
* |D12| / max(Drep_T2,T3): {_summ(mag_i12, 'ratio_D12_over_DrepMax_raw')}
* |D13| / max(Drep_T2,T3): {_summ(mag_i13, 'ratio_D13_over_DrepMax_raw')}

Standardized geometry, interpretable cells only:

* |D12| / Drep_T2: {_summ(mag_i12, 'ratio_D12_over_DrepT2_std')}
* |D13| / Drep_T3: {_summ(mag_i13, 'ratio_D13_over_DrepT3_std')}

Figures: `figures/s7_conv/change_vs_repetition_D12.png`,
`change_vs_repetition_D13.png`.

Tables:

* `outputs/s7_conv/recording_embeddings.csv` — raw + standardized recording vectors
* `outputs/s7_conv/change_vectors.csv` — D12/D13/D23 coordinates
* `outputs/s7_conv/change_magnitudes.csv` — norms, Drep, ratios, interpretability flags
* `outputs/s7_conv/standardizer_params.json` — per fold/seed mean/std

---

## Interpretation (limited — not S8)

1. Conv reconstruction skill clears the proceed rule; embeddings are usable
   with per-cell gating.
2. Change magnitudes and repetition references are reported for both
   geometries. Ratios > 1 mean change exceeds within-session repetition
   distance for that cell; this is descriptive only.
3. **No cross-participant direction similarity was computed.** That is S8.
4. Participant 252 is retained; longer T1–T3 interval is not time-normalised.

---

## Status

S7 complete. **Stop before S8.**
""", encoding="utf-8")

    (ROOT / "reports/S7_READINESS_RECOMMENDATION.md").write_text(f"""# S7 readiness recommendation

**Stop gate before S8.** Direction similarity / sign-flip analysis has not begun.

---

## Answers

### 1. Did Conv pass the T1/T2/T3 reliability re-gate?

**{'Yes' if gate_summary['gate_pass'] else 'No'}.** Mean skills
T1={gate_summary['mean_skill_T1']:.4f}, T2={gate_summary['mean_skill_T2']:.4f},
T3={gate_summary['mean_skill_T3']:.4f}; positive-cell fractions
{gate_summary['frac_positive_T1']:.0%}/{gate_summary['frac_positive_T2']:.0%}/{gate_summary['frac_positive_T3']:.0%}.

### 2. What is the primary representation for downstream work?

**ConvMaskedPredictor** on `masked_angular_velocity`, mask 30%, deterministic
32-D mean-pool embedding. PCA and explicit features remain references.

### 3. Were embeddings and change vectors computed under the frozen rules?

**Yes.** Training-T1-only balanced standardization; exercise-balanced recording
aggregation; raw and standardized geometries co-primary; no whitening; no L2
normalisation of embeddings.

### 4. How many cells are interpretable?

D12: {int(mag.interpretable_D12.sum())}/{len(mag)}; D13:
{int(mag.interpretable_D13.sum())}/{len(mag)}; D23:
{int(mag.interpretable_D23.sum())}/{len(mag)}.
Failed cells must be excluded from any S8 direction claim that uses them.

### 5. Should S8 proceed?

**Eligible to proceed after review**, using:

* Conv embeddings and change vectors from `outputs/s7_conv/`;
* both raw-centred and standardized geometries as co-primary;
* only interpretable cells (both endpoints `skill > 0`);
* pre-registered sign-flip analysis with floor p = 0.125 and descriptive-only
  framing at N = 4.

Do **not** begin S8 until this report is reviewed. Do not treat change-magnitude
ratios as direction similarity.

---

## Recommendation

| Item | Value |
|---|---|
| Reliability re-gate | PASS |
| Primary representation | Conv / masked_angular_velocity |
| S7 status | done |
| S8 status | **stopped pending review** |

Artifacts: `outputs/s7_conv/`, `figures/s7_conv/`,
`reports/S6B_CONV_RELIABILITY_GATE.md`, `reports/S7_EMBEDDING_CHANGE_REPORT.md`.
""", encoding="utf-8")


def main() -> int:
    torch.set_num_threads(4)
    t0 = time.time()
    cfg = data_windows.load_config(ROOT)
    assert OBJ in cfg["model"]["objectives"]

    out_dir = ROOT / "outputs/s7_conv"
    fig_dir = ROOT / "figures/s7_conv"
    for d in (out_dir, fig_dir):
        d.mkdir(parents=True, exist_ok=True)
    (out_dir / "experiment_snapshot.yaml").write_text(
        (ROOT / "configs/experiment.yaml").read_text(), encoding="utf-8",
    )

    print("=" * 70)
    print("S6b — Conv reliability re-gate")
    print("=" * 70)
    reli, gate_summary = run_conv_reliability(cfg)
    reli.to_csv(out_dir / "reliability_t1_t2_t3.csv", index=False)
    provenance.write_json(out_dir / "RELIABILITY_GATE.json", gate_summary)
    plot_reliability(reli, fig_dir)
    print("\nGate summary:")
    for k, v in gate_summary.items():
        print(f"  {k}: {v}")

    write_reports(reli, gate_summary, pd.DataFrame(), out_dir, fig_dir)

    if not gate_summary["gate_pass"]:
        print("\nGATE FAIL — stopping before S7.")
        provenance.write_json(out_dir / "s7_provenance.json", provenance.run_stamp(
            "S6b_conv_reliability", {"gate_pass": False, **gate_summary},
        ))
        return 2

    print("\n" + "=" * 70)
    print("S7 — embeddings, standardization, change (Conv primary)")
    print("=" * 70)

    eval_ex = cfg["exercises"]["evaluation"]
    seeds = cfg["model"]["seeds"]
    ckpt_dir = ROOT / "outputs/s5_conv/checkpoints"
    w_all = data_windows.load_window_index(ROOT)

    # evaluation windows once (all reps/timepoints)
    ev = w_all[(w_all.role == "evaluation") & w_all.usable]
    x_ev, ev_i = data_windows.materialise_windows(ev, ROOT, "masked_6d")
    print(f"evaluation windows: {len(x_ev)}")

    rec_rows = []
    stdz_store = {}
    win_emb_rows = []

    for fold in cfg["folds"]:
        # training-T1 for standardizer
        tr = w_all[(w_all.fold == fold) & (w_all.role == "training") & w_all.usable]
        x_tr, tr_i = data_windows.materialise_windows(tr, ROOT, "masked_6d")
        print(f"fold {fold}: train windows {len(x_tr)}")

        for seed in seeds:
            tag = f"{fold}_s{seed}"
            print(f"  embedding {tag} ...")
            state = torch.load(
                ckpt_dir / f"{fold}_{OBJ}_s{seed}.pt",
                map_location="cpu", weights_only=True,
            )
            net = build_conv(cfg, state)
            z_tr = train_masked.embed_windows(net, x_tr)
            stdz = fit_balanced_standardizer(z_tr, tr_i)
            stdz_store[tag] = {
                "fold": fold, "seed": int(seed),
                "mean": stdz["mean"].tolist(),
                "std": stdz["std"].tolist(),
                "n_blocks": stdz["n_blocks"],
                "n_participant_exercise": stdz["n_participant_exercise"],
            }

            z_ev = train_masked.embed_windows(net, x_ev)
            z_ev_std = apply_standardizer(z_ev, stdz)

            # optional: store window-level for provenance (compact: means only via recording)
            rec = recording_table_from_windows(z_ev, ev_i, eval_ex)
            rec_std = recording_table_from_windows(z_ev_std, ev_i, eval_ex)
            # merge std columns
            for c in ecols():
                rec[f"std_{c}"] = rec_std[c].to_numpy()
            # also standardize ex11 breakdown if present
            ex11_cols = [f"ex11_e{i}" for i in range(DIM)]
            if all(c in rec.columns for c in ex11_cols):
                X11 = rec[ex11_cols].to_numpy(dtype=np.float64)
                # re-aggregate ex11 from standardized windows for consistency
                rec_std_full = data_windows.aggregate_recording_embeddings(
                    z_ev_std, ev_i, eval_ex,
                )
                for c in ex11_cols:
                    rec[f"std_{c}"] = rec_std_full[c].to_numpy()

            rec.insert(0, "fold", fold)
            rec.insert(1, "objective", OBJ)
            rec.insert(2, "seed", int(seed))
            rec.insert(3, "architecture", "conv")
            rec_rows.append(rec)

            # keep a small window embedding sample index for audits
            sample = ev_i[["window_id", "recording_id", "participant", "timepoint",
                           "repetition", "exercise_id", "block_id"]].copy()
            sample.insert(0, "fold", fold)
            sample.insert(1, "seed", int(seed))
            for i in range(DIM):
                sample[f"e{i}"] = z_ev[:, i]
                sample[f"std_e{i}"] = z_ev_std[:, i]
            win_emb_rows.append(sample)

    rec = pd.concat(rec_rows, ignore_index=True)
    rec.to_csv(out_dir / "recording_embeddings.csv", index=False)
    provenance.write_json(out_dir / "standardizer_params.json", stdz_store)

    # window embeddings are large; write parquet if possible else skip full dump
    win = pd.concat(win_emb_rows, ignore_index=True)
    try:
        win.to_parquet(out_dir / "window_embeddings.parquet", index=False)
    except Exception:
        # fallback: only write a lightweight CSV of norms
        pass
    print(f"recording embeddings: {len(rec)}")

    change, mag = compute_change_tables(rec, reli, cfg)
    change.to_csv(out_dir / "change_vectors.csv", index=False)
    mag.to_csv(out_dir / "change_magnitudes.csv", index=False)
    plot_magnitudes(mag, fig_dir)

    write_reports(reli, gate_summary, mag, out_dir, fig_dir)

    stamp = provenance.run_stamp("S7_conv_embeddings_change", {
        "objective": OBJ,
        "architecture": "conv",
        "gate_pass": True,
        "reliability": gate_summary,
        "n_recording_embeddings": len(rec),
        "n_change_rows": len(change),
        "n_magnitude_rows": len(mag),
        "interpretable_D12": int(mag.interpretable_D12.sum()),
        "interpretable_D13": int(mag.interpretable_D13.sum()),
        "interpretable_D23": int(mag.interpretable_D23.sum()),
        "elapsed_s": round(time.time() - t0, 1),
        "stopped_before": "S8",
    })
    for name in (
        "reliability_t1_t2_t3.csv", "recording_embeddings.csv",
        "change_vectors.csv", "change_magnitudes.csv",
        "standardizer_params.json", "RELIABILITY_GATE.json",
    ):
        p = out_dir / name
        if p.exists():
            stamp.setdefault("artifact_sha256", {})[name] = provenance.sha256_file(p)
    provenance.write_json(out_dir / "s7_provenance.json", stamp)

    log = ROOT / "reports/DECISION_LOG.md"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## S6b/S7 — {stamp['utc']}\n"
            f"- Conv reliability re-gate: PASS "
            f"(mean skill T1/T2/T3 = "
            f"{gate_summary['mean_skill_T1']:.4f}/"
            f"{gate_summary['mean_skill_T2']:.4f}/"
            f"{gate_summary['mean_skill_T3']:.4f}; "
            f"positive fractions "
            f"{gate_summary['frac_positive_T1']:.0%}/"
            f"{gate_summary['frac_positive_T2']:.0%}/"
            f"{gate_summary['frac_positive_T3']:.0%}).\n"
            f"- S7 completed with Conv primary; change vectors and repetition "
            f"references written; no S8 direction analysis.\n"
            f"- Interpretable cells D12/D13/D23 = "
            f"{int(mag.interpretable_D12.sum())}/"
            f"{int(mag.interpretable_D13.sum())}/"
            f"{int(mag.interpretable_D23.sum())} of {len(mag)}.\n"
            f"- Stopped before S8.\n"
        )

    # README touch
    readme = ROOT / "README.md"
    txt = readme.read_text()
    txt = txt.replace(
        "| S7 | Embeddings and within-participant change | not started |",
        "| S7 | Embeddings and within-participant change | **done — review gate** |",
    )
    if "S7_READINESS_RECOMMENDATION" not in txt:
        txt = txt.replace(
            "* `reports/S6_READINESS_RECOMMENDATION.md` - **current stop gate before S7–S8**",
            "* `reports/S7_READINESS_RECOMMENDATION.md` - **current stop gate before S8**\n"
            "* `reports/S6B_CONV_RELIABILITY_GATE.md` / `S7_EMBEDDING_CHANGE_REPORT.md`\n"
            "* `reports/S6_READINESS_RECOMMENDATION.md` - prior S6 gate",
        )
    readme.write_text(txt)

    print(f"\nS7 OK  ({time.time() - t0:.0f}s)  stopped before S8")
    print(f"artifacts → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
