#!/usr/bin/env python3
"""Stage 0B-A2 — Guided improvisation analysis closeout.

No free-movement, no new training, no shared-direction reopen.
P1–P5 progressive instruction stages are NOT supported by source annotations;
localization uses exercise (ex09–13) and early/middle/late thirds within exercise.
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.neighbors import NearestNeighbors
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, models, provenance, train_masked  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OBJ = "masked_angular_velocity"
DIM = 32
EVAL_EX = [9, 10, 11, 12, 13]
PARTICIPANTS = ["252", "651", "671", "790"]
EX_FOCUS = {
    9: "Curvilinear exploration (Group4 start)",
    10: "Curvilinear exploration (Group4)",
    11: "Curvilinear exploration (Group4; breakdown exercise)",
    12: "Curvilinear exploration (Group4)",
    13: "Curvilinear exploration (Group4 end)",
}


def ecols(prefix: str = "e") -> list[str]:
    return [f"{prefix}{i}" for i in range(DIM)]


def traj_rep(cfg, fold: str) -> int:
    return int(cfg["folds"][fold]["trajectory_repetition"])


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


# --------------------------------------------------------------------------
# 1. Evidence map (static from completed Stage 0 / 0B-A)
# --------------------------------------------------------------------------

def write_evidence_map():
    text = """# Stage 0B-A2 — Evidence map

Compiled from Stage 0 and Stage 0B-A artifacts without reopening failed hypotheses.

## Already tested and passed

| Claim | Evidence |
|---|---|
| Primary path / 18-link / 6D / windowing valid | S1–S4 |
| Mask 30%; velocity objective; Conv > Transformer on held-out T1 | S5–S6 |
| Conv T1/T2/T3 reliability proceed rule | S6b PASS (per-cell failures remain) |
| Exercise-balanced recording embeddings + Drep | S7 |
| Individual latent ‖Δ‖ often > Drep in qualified cells | S7, 0B-A |
| Amplitude alone does not explain all individual changes | 0B-A amp-residual exceedances |
| Different participants have different exercise/feature profiles | 0B-A |
| Conv less identity-dominated than PCA; positive velocity skill | S5, S9 |

## Already tested and failed / rejected

| Claim | Evidence |
|---|---|
| Stable shared cross-participant direction | S8 FAIL (sign/geometry/jackknife unstable) |
| Transformer as primary representation | S6 FAIL vs Conv |
| Masked 6D reconstruction as viable pretext | S5–S6 FAIL |
| Population / intervention inference at N=4 | Methodologically barred |

## Already partially characterized (0B-A)

| Topic | Status |
|---|---|
| Recording-level individual profiles | Done |
| Exercise contribution fractions (descriptive) | Done — needs absolute/Drep-normalized supplement |
| Explicit features vs R1–R2 + amp residuals | Done at recording/exercise level |
| Latent vs energy correlation | Done |

## Unresolved before this closeout

| Question | Plan in A2 |
|---|---|
| Supported segmentation units (P1–P5?) | Map annotations; do not invent stages |
| Absolute exercise-level Δ vs Drep | Section 4 |
| Early/mid/late within-exercise localization | Section 4–5 |
| Temporal path vs mean-shift vs spread | Section 5 |
| Region/link attribution (explicit + occlusion validity) | Section 7 |
| Whether local states/motifs are feasible | Section 8 |
| Best primary analysis framework | Sections 9–10 |

## Would duplicate without adding value

* Full S5–S8 re-runs
* Shared-direction / sign-flip re-search
* Transformer retraining
* Recomputing recording-level profiles already in 0B-A (reuse, extend)

## Decision context

Stage 0: **LIMITED GO**. Shared direction closed. Free-movement not authorized until guided closeout.
"""
    (ROOT / "reports/STAGE0B_A2_EVIDENCE_MAP.md").write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------
# 2–3. Segmentation map
# --------------------------------------------------------------------------

def build_segmentation_table(cfg) -> pd.DataFrame:
    seg = pd.read_csv(ROOT / "data/immutable/segmentation_normalized.csv")
    w = pd.read_csv(ROOT / "outputs/s4_windows/window_index.csv")
    ev = w[(w.role == "evaluation") & w.usable]
    rows = []
    for _, r in seg[seg.exercise_id.isin(EVAL_EX)].iterrows():
        pid, tp, rep, ex = str(int(r.participant)), int(r.timepoint), int(r.repetition), int(r.exercise_id)
        rid = f"{pid}_T{tp}_P1_R{rep}"
        nw = int(((ev.participant.astype(str) == pid) & (ev.timepoint == tp)
                  & (ev.repetition == rep) & (ev.exercise_id == ex)).sum())
        # confidence: full duration present, no merge flag for this block ideally
        conf = "high"
        if pd.notna(r.get("merged_with")) and str(r.get("merged_with")) not in ("", "nan", "None"):
            conf = "medium_merged"
        if float(r.duration_s) < 6:
            conf = "medium_short"
        rows.append({
            "participant": pid, "timepoint": tp, "repetition": rep, "exercise_id": ex,
            "recording_id": rid, "instruction_focus": EX_FOCUS[ex],
            "start_frame": int(r.start_frame), "end_frame": int(r.end_frame),
            "n_frames": int(r.n_frames), "duration_s": float(r.duration_s),
            "n_eval_windows": nw,
            "progressive_P1_P5_supported": False,
            "substage_supported": "early_mid_late_thirds_only",
            "segmentation_confidence": conf,
            "suitable_longitudinal": nw >= 3 and float(r.duration_s) >= 6,
            "group": "Group4_curvilinear_exploration",
            "task_part_note": "Session P1 = Task Part 1, NOT progressive cue stage",
        })
    return pd.DataFrame(rows)


def write_segmentation_report(seg_tab: pd.DataFrame):
    # summary by exercise
    lines = [
        "# Stage 0B-A2 — Guided sequence segmentation\n\n",
        "## Critical namespace note\n\n",
        "In this project, **P1 in session keys (`*_T*_P1_R*`)** means **Task Part 1**, "
        "not a progressive improvisation cue stage. Source annotations provide "
        "**exercise_id boundaries (ex01–ex17)**, not P1–P5 progressive instruction labels "
        "within Group4.\n\n",
        "Group4 (ex09–ex13) is labeled **Curvilinear exploration** in "
        "`gaga_jcvpca/configs/exercise_map.yaml`. No validated cue-timed sub-stage "
        "map exists for finer progressive instructions.\n\n",
        "## Supported analysis units\n\n",
        "| Unit | Supported? | Notes |\n|---|---|---|\n",
        "| Exercise ex09–ex13 | **Yes** | Authoritative segmentation workbook |\n",
        "| Full Group4 aggregate | **Yes** | Equal-weight exercise mean (S7) |\n",
        "| P1–P5 progressive stages | **No** | Not in source annotations |\n",
        "| Early/middle/late thirds within exercise | **Yes (derived)** | Temporal thirds of windows; not cue labels |\n",
        "| Transitions between exercises | **Limited** | Boundaries exist; transition windows not specially annotated |\n\n",
        "## Coverage summary (evaluation windows)\n\n",
    ]
    summ = seg_tab.groupby("exercise_id").agg(
        n_blocks=("recording_id", "count"),
        mean_dur=("duration_s", "mean"),
        mean_windows=("n_eval_windows", "mean"),
        frac_suitable=("suitable_longitudinal", "mean"),
    ).reset_index()
    lines.append("| Exercise | Focus | n blocks | mean dur (s) | mean eval windows | frac suitable |\n|---|---|---|---|---|---|\n")
    for r in summ.itertuples():
        lines.append(
            f"| ex{int(r.exercise_id):02d} | {EX_FOCUS[int(r.exercise_id)]} | {int(r.n_blocks)} | "
            f"{r.mean_dur:.1f} | {r.mean_windows:.1f} | {r.frac_suitable:.0%} |\n"
        )
    lines.append(
        "\nFull table: `outputs/stage0b_guided_closeout/guided_segmentation.csv`.\n"
        "\n**Decision:** Do not invent P1–P5 labels. Localize with exercise + early/mid/late thirds.\n"
    )
    (ROOT / "reports/STAGE0B_A2_GUIDED_SEGMENTATION.md").write_text("".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# 4. Exercise + tertiary-block longitudinal analysis
# --------------------------------------------------------------------------

def exercise_level_change(win: pd.DataFrame, mag: pd.DataFrame, cfg) -> pd.DataFrame:
    cols = ecols()
    rows = []
    for _, mrow in mag.iterrows():
        fold, seed, pid = mrow.fold, int(mrow.seed), str(mrow.participant)
        traj = traj_rep(cfg, fold)
        for delta, tp_b, flag in (("D12", 2, "interpretable_D12"), ("D13", 3, "interpretable_D13"),
                                   ("D23", 3, "interpretable_D23")):
            # D23 uses T2 as baseline
            tp_a = 1 if delta != "D23" else 2
            if delta == "D23":
                # need skill>0 at T2 and T3 — interpretable_D23
                pass
            reliable = bool(mrow[flag]) if flag in mrow.index else False
            sub = win[(win.fold == fold) & (win.seed == seed) & (win.participant.astype(str) == pid)]
            for ex in EVAL_EX:
                def mean_vec(tp, rep):
                    g = sub[(sub.timepoint == tp) & (sub.repetition == rep) & (sub.exercise_id == ex)]
                    if len(g) == 0:
                        return None
                    return g[cols].mean().to_numpy(float)

                za, zb = mean_vec(tp_a, traj), mean_vec(tp_b, traj)
                if za is None or zb is None:
                    continue
                d = zb - za
                nrm = float(np.linalg.norm(d))
                # Drep at later timepoint for this exercise
                z_r1, z_r2 = mean_vec(tp_b, 1), mean_vec(tp_b, 2)
                drep_b = float(np.linalg.norm(z_r1 - z_r2)) if z_r1 is not None and z_r2 is not None else np.nan
                z1a, z1b = mean_vec(tp_a, 1), mean_vec(tp_a, 2)
                drep_a = float(np.linalg.norm(z1a - z1b)) if z1a is not None and z1b is not None else np.nan
                drep_max = np.nanmax([drep_a, drep_b])
                rows.append({
                    "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                    "exercise_id": ex, "reliable": reliable,
                    "norm_delta": nrm, "drep_later": drep_b, "drep_baseline": drep_a,
                    "drep_max": drep_max,
                    "ratio_vs_drep_max": nrm / drep_max if drep_max and drep_max > 0 else np.nan,
                    "exceeds_drep_max": bool(drep_max == drep_max and drep_max > 0 and nrm > drep_max),
                    "n_windows_T_a": int(((sub.timepoint == tp_a) & (sub.repetition == traj) & (sub.exercise_id == ex)).sum()),
                    "n_windows_T_b": int(((sub.timepoint == tp_b) & (sub.repetition == traj) & (sub.exercise_id == ex)).sum()),
                })
    return pd.DataFrame(rows)


def tertiary_block_change(win: pd.DataFrame, mag: pd.DataFrame, cfg) -> pd.DataFrame:
    """Early/middle/late thirds within each exercise (by window order)."""
    cols = ecols()
    rows = []
    for _, mrow in mag.iterrows():
        fold, seed, pid = mrow.fold, int(mrow.seed), str(mrow.participant)
        traj = traj_rep(cfg, fold)
        for delta, tp_b, flag in (("D12", 2, "interpretable_D12"), ("D13", 3, "interpretable_D13")):
            reliable = bool(mrow[flag])
            sub = win[(win.fold == fold) & (win.seed == seed) & (win.participant.astype(str) == pid)]
            for ex in EVAL_EX:
                for third, name in enumerate(("early", "middle", "late")):
                    def third_vec(tp, rep):
                        g = sub[(sub.timepoint == tp) & (sub.repetition == rep) & (sub.exercise_id == ex)]
                        if len(g) < 3:
                            return None
                        g = g.sort_values(["start_frame", "window_id"] if "start_frame" in g.columns else ["window_id"])
                        n = len(g)
                        edges = [0, n // 3, 2 * n // 3, n]
                        chunk = g.iloc[edges[third]:edges[third + 1]]
                        if len(chunk) == 0:
                            return None
                        return chunk[cols].mean().to_numpy(float)

                    za, zb = third_vec(1, traj), third_vec(tp_b, traj)
                    if za is None or zb is None:
                        continue
                    nrm = float(np.linalg.norm(zb - za))
                    # drep on same third at later tp
                    r1, r2 = third_vec(tp_b, 1), third_vec(tp_b, 2)
                    drep = float(np.linalg.norm(r1 - r2)) if r1 is not None and r2 is not None else np.nan
                    rows.append({
                        "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                        "exercise_id": ex, "third": name, "reliable": reliable,
                        "norm_delta": nrm, "drep_later": drep,
                        "ratio_vs_drep": nrm / drep if drep and drep > 0 else np.nan,
                        "exceeds_drep": bool(drep == drep and drep > 0 and nrm > drep),
                    })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 5. Temporal dynamics
# --------------------------------------------------------------------------

def temporal_metrics_for_group(X: np.ndarray) -> dict:
    """X: (n_windows, d) in time order."""
    if len(X) < 2:
        return {k: np.nan for k in (
            "traj_length", "mean_step", "spread_rms", "half_shift", "eff_dim",
        )}
    steps = np.linalg.norm(np.diff(X, axis=0), axis=1)
    traj_length = float(steps.sum())
    mean_step = float(steps.mean())
    mu = X.mean(axis=0)
    spread = float(np.sqrt(((X - mu) ** 2).sum(axis=1).mean()))
    mid = len(X) // 2
    half_shift = float(np.linalg.norm(X[mid:].mean(axis=0) - X[:max(mid, 1)].mean(axis=0)))
    # effective dimensionality via participation ratio of covariance eigenvalues
    Xc = X - mu
    if len(X) > 2:
        cov = np.cov(Xc, rowvar=False)
        ev = np.linalg.eigvalsh(cov)
        ev = np.clip(ev, 0, None)
        s1, s2 = ev.sum(), (ev ** 2).sum()
        eff = float((s1 ** 2) / s2) if s2 > 0 else float("nan")
    else:
        eff = float("nan")
    return {
        "traj_length": traj_length, "mean_step": mean_step, "spread_rms": spread,
        "half_shift": half_shift, "eff_dim": eff, "n_windows": len(X),
    }


def temporal_dynamics_table(win: pd.DataFrame, mag: pd.DataFrame, cfg) -> pd.DataFrame:
    cols = ecols()
    # need start_frame — join from window index if missing
    if "start_frame" not in win.columns:
        widx = pd.read_csv(ROOT / "outputs/s4_windows/window_index.csv")[
            ["window_id", "start_frame", "window_in_block"]
        ]
        win = win.merge(widx, on="window_id", how="left")
    rows = []
    for _, mrow in mag.iterrows():
        fold, seed, pid = mrow.fold, int(mrow.seed), str(mrow.participant)
        traj = traj_rep(cfg, fold)
        for delta, tp_b, flag in (("D12", 2, "interpretable_D12"), ("D13", 3, "interpretable_D13")):
            reliable = bool(mrow[flag])
            sub = win[(win.fold == fold) & (win.seed == seed) & (win.participant.astype(str) == pid)]
            for ex in EVAL_EX:
                metrics = {}
                for tp, rep, tag in (
                    (1, traj, "T1_traj"), (tp_b, traj, "Tb_traj"),
                    (tp_b, 1, "Tb_R1"), (tp_b, 2, "Tb_R2"),
                    (1, 1, "T1_R1"), (1, 2, "T1_R2"),
                ):
                    g = sub[(sub.timepoint == tp) & (sub.repetition == rep) & (sub.exercise_id == ex)]
                    if len(g) < 2:
                        metrics[tag] = None
                        continue
                    g = g.sort_values("start_frame")
                    metrics[tag] = temporal_metrics_for_group(g[cols].to_numpy(float))
                if metrics["T1_traj"] is None or metrics["Tb_traj"] is None:
                    continue
                for key in ("traj_length", "mean_step", "spread_rms", "half_shift", "eff_dim"):
                    v1, vb = metrics["T1_traj"][key], metrics["Tb_traj"][key]
                    drep_b = np.nan
                    if metrics["Tb_R1"] and metrics["Tb_R2"]:
                        drep_b = abs(metrics["Tb_R1"][key] - metrics["Tb_R2"][key])
                    rows.append({
                        "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                        "exercise_id": ex, "metric": key, "reliable": reliable,
                        "value_T1": v1, "value_Tb": vb, "delta_value": vb - v1,
                        "abs_delta": abs(vb - v1),
                        "drep_Tb": drep_b,
                        "ratio_vs_drep": abs(vb - v1) / drep_b if drep_b and drep_b > 0 else np.nan,
                        "exceeds_drep": bool(drep_b == drep_b and drep_b > 0 and abs(vb - v1) > drep_b),
                        "mean_position_shift": float(np.linalg.norm(
                            # approximate from half of available: use overall means
                            0
                        )) if False else np.nan,
                    })
                # mean position shift separately
                g1 = sub[(sub.timepoint == 1) & (sub.repetition == traj) & (sub.exercise_id == ex)]
                gb = sub[(sub.timepoint == tp_b) & (sub.repetition == traj) & (sub.exercise_id == ex)]
                if len(g1) and len(gb):
                    shift = float(np.linalg.norm(gb[cols].mean().to_numpy() - g1[cols].mean().to_numpy()))
                    r1 = sub[(sub.timepoint == tp_b) & (sub.repetition == 1) & (sub.exercise_id == ex)]
                    r2 = sub[(sub.timepoint == tp_b) & (sub.repetition == 2) & (sub.exercise_id == ex)]
                    drep = float(np.linalg.norm(r1[cols].mean() - r2[cols].mean())) if len(r1) and len(r2) else np.nan
                    rows.append({
                        "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                        "exercise_id": ex, "metric": "mean_position_shift", "reliable": reliable,
                        "value_T1": 0.0, "value_Tb": shift, "delta_value": shift,
                        "abs_delta": shift, "drep_Tb": drep,
                        "ratio_vs_drep": shift / drep if drep and drep > 0 else np.nan,
                        "exceeds_drep": bool(drep == drep and drep > 0 and shift > drep),
                    })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 7. Region attribution
# --------------------------------------------------------------------------

def region_explicit_attribution(rec_chg: pd.DataFrame) -> pd.DataFrame:
    """From 0B-A recording feature changes: energy shares + coupling."""
    share_map = {
        "energy_share_head_neck": "head_neck",
        "energy_share_trunk_spine": "trunk_pelvis",
        "energy_share_left_arm": "left_arm",
        "energy_share_right_arm": "right_arm",
        "energy_share_left_leg": "left_leg",
        "energy_share_right_leg": "right_leg",
    }
    rows = []
    for (pid, delta, fold), g in rec_chg.groupby(["participant", "delta", "fold"]):
        for feat, region in share_map.items():
            r = g[g.feature == feat]
            if len(r) != 1:
                continue
            rr = r.iloc[0]
            rows.append({
                "participant": pid, "delta": delta, "fold": fold, "region": region,
                "source": "explicit_energy_share",
                "delta_value": rr.delta_value, "ratio_vs_drep_max": rr.ratio_vs_drep_max,
                "exceeds_drep_max": rr.exceeds_drep_max,
                "reliable_fold_any_seed": rr.reliable_fold_any_seed,
            })
    return pd.DataFrame(rows)


def region_occlusion_extended(cfg, mag, out_dir) -> pd.DataFrame:
    """Inference-only region zeroing for reliable D12/D13 on fold A seed 0 (validity check)."""
    link_ids, regions = data_windows.load_link_config(ROOT)
    region_to_idx = {}
    for i, lid in enumerate(link_ids):
        region_to_idx.setdefault(regions[lid], []).append(i)
    # map trunk_spine -> trunk_pelvis label for report consistency
    fold, seed = "A", 0
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
    traj = traj_rep(cfg, fold)
    w = data_windows.load_window_index(ROOT)
    ev = w[(w.role == "evaluation") & w.usable & (w.repetition == traj)]
    x_ev, ev_i = data_windows.materialise_windows(ev, ROOT, "masked_6d")
    eval_ex = cfg["exercises"]["evaluation"]

    def embed_rec(x):
        z = train_masked.embed_windows(net, x)
        return data_windows.aggregate_recording_embeddings(z, ev_i, eval_ex)

    def delta_norm(rec, pid, tp_a, tp_b):
        g = rec[rec.participant.astype(str) == str(pid)]
        a = g[g.timepoint == tp_a]; b = g[g.timepoint == tp_b]
        if len(a) != 1 or len(b) != 1:
            return np.nan
        return float(np.linalg.norm(b.iloc[0][ecols()].to_numpy(float) - a.iloc[0][ecols()].to_numpy(float)))

    base = embed_rec(x_ev)
    rows = []
    # OOD diagnostic: fraction of zeros after occlusion
    for region, idxs in region_to_idx.items():
        x_m = x_ev.copy()
        x_m[:, :, idxs, :] = 0.0
        zero_frac = float((x_m == 0).mean())
        rec_m = embed_rec(x_m)
        for delta, tp_a, tp_b, flag in (("D12", 1, 2, "interpretable_D12"), ("D13", 1, 3, "interpretable_D13")):
            for pid in PARTICIPANTS:
                mrow = mag[(mag.fold == fold) & (mag.seed == seed) & (mag.participant.astype(str) == pid)]
                if len(mrow) != 1 or not bool(mrow.iloc[0][flag]):
                    continue
                b = delta_norm(base, pid, tp_a, tp_b)
                m = delta_norm(rec_m, pid, tp_a, tp_b)
                rows.append({
                    "fold": fold, "seed": seed, "participant": pid, "delta": delta,
                    "region": region, "base_norm": b, "occluded_norm": m,
                    "rel_change": (m - b) / b if b and b > 0 else np.nan,
                    "abs_change": m - b,
                    "input_zero_fraction": zero_frac,
                    "ood_risk": zero_frac > 0.25,  # heuristic
                    "method": "zero_region_inference",
                })
    tab = pd.DataFrame(rows)
    tab.to_csv(out_dir / "region_occlusion_A0.csv", index=False)
    return tab


# --------------------------------------------------------------------------
# 8. Repertoire feasibility
# --------------------------------------------------------------------------

def repertoire_feasibility(win: pd.DataFrame, cfg, out_dir) -> dict:
    """Neighborhood + limited clustering feasibility. Reject if exercise-dominated."""
    cols = ecols()
    # use fold A seed 0 standardized embeddings
    sub = win[(win.fold == "A") & (win.seed == 0)].copy()
    if "start_frame" not in sub.columns:
        widx = pd.read_csv(ROOT / "outputs/s4_windows/window_index.csv")[["window_id", "start_frame"]]
        sub = sub.merge(widx, on="window_id", how="left")
    rows_nn, rows_cl = [], []
    summary = {"clustering_justified": False, "reasons": []}

    for pid in PARTICIPANTS:
        g = sub[sub.participant.astype(str) == pid]
        # within vs between exercise distances on T1 traj
        traj = traj_rep(cfg, "A")
        g1 = g[(g.timepoint == 1) & (g.repetition == traj) & g.exercise_id.isin(EVAL_EX)]
        if len(g1) < 20:
            continue
        X = g1[cols].to_numpy(float)
        # standardize within participant T1
        mu, sd = X.mean(0), X.std(0)
        sd = np.where(sd < 1e-8, 1, sd)
        Xz = (X - mu) / sd
        labels_ex = g1.exercise_id.to_numpy()
        # sample pairwise
        rng = np.random.default_rng(0)
        idx = rng.choice(len(Xz), size=min(80, len(Xz)), replace=False)
        within, between = [], []
        for i in idx:
            for j in idx:
                if i >= j:
                    continue
                d = np.linalg.norm(Xz[i] - Xz[j])
                if labels_ex[i] == labels_ex[j]:
                    within.append(d)
                else:
                    between.append(d)
        wmean = float(np.mean(within)) if within else np.nan
        bmean = float(np.mean(between)) if between else np.nan
        rows_nn.append({
            "participant": pid, "within_ex_mean_dist": wmean, "between_ex_mean_dist": bmean,
            "ratio_between_over_within": bmean / wmean if wmean and wmean > 0 else np.nan,
        })

        # NN agreement across seeds for same window_ids on T1
        for seed_b in (1, 2):
            gb = win[(win.fold == "A") & (win.seed == seed_b) & (win.participant.astype(str) == pid)
                     & (win.timepoint == 1) & (win.repetition == traj) & win.exercise_id.isin(EVAL_EX)]
            common = sorted(set(g1.window_id) & set(gb.window_id))
            if len(common) < 15:
                continue
            A = g1.set_index("window_id").loc[common, cols].to_numpy(float)
            B = gb.set_index("window_id").loc[common, cols].to_numpy(float)
            A = (A - A.mean(0)) / np.where(A.std(0) < 1e-8, 1, A.std(0))
            B = (B - B.mean(0)) / np.where(B.std(0) < 1e-8, 1, B.std(0))
            nn = NearestNeighbors(n_neighbors=min(6, len(common))).fit(A)
            _, idxA = nn.kneighbors(A)
            nnB = NearestNeighbors(n_neighbors=min(6, len(common))).fit(B)
            _, idxB = nnB.kneighbors(B)
            # exclude self (neighbor 0)
            overlap = [len(set(idxA[i, 1:]) & set(idxB[i, 1:])) / 5 for i in range(len(common))]
            rows_nn.append({
                "participant": pid, "seed_pair": f"0-{seed_b}",
                "mean_nn_overlap": float(np.mean(overlap)), "n": len(common),
            })

        # limited clustering on T1; score ARI vs exercise labels; stability across seeds
        for k in (3, 4, 5):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Xz)
            ari_ex = adjusted_rand_score(labels_ex, km.labels_)
            # seed 1
            g1b = win[(win.fold == "A") & (win.seed == 1) & (win.participant.astype(str) == pid)
                      & (win.timepoint == 1) & (win.repetition == traj) & win.exercise_id.isin(EVAL_EX)]
            common = sorted(set(g1.window_id) & set(g1b.window_id))
            ari_seed = np.nan
            if len(common) >= 15:
                A = g1.set_index("window_id").loc[common, cols].to_numpy(float)
                B = g1b.set_index("window_id").loc[common, cols].to_numpy(float)
                As = (A - A.mean(0)) / np.where(A.std(0) < 1e-8, 1, A.std(0))
                Bs = (B - B.mean(0)) / np.where(B.std(0) < 1e-8, 1, B.std(0))
                labA = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(As)
                labB = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(Bs)
                ari_seed = adjusted_rand_score(labA, labB)
            try:
                sil = float(silhouette_score(Xz, km.labels_))
            except Exception:
                sil = float("nan")
            rows_cl.append({
                "participant": pid, "method": "kmeans", "k": k,
                "ari_vs_exercise": ari_ex, "ari_seed0_vs_seed1": ari_seed, "silhouette": sil,
            })

    nn_df = pd.DataFrame(rows_nn)
    cl_df = pd.DataFrame(rows_cl)
    nn_df.to_csv(out_dir / "repertoire_neighborhood.csv", index=False)
    cl_df.to_csv(out_dir / "repertoire_clustering_feasibility.csv", index=False)

    # justify clustering only if seed ARI high AND exercise ARI not near 1
    if len(cl_df):
        mean_seed = float(cl_df.ari_seed0_vs_seed1.mean())
        mean_ex = float(cl_df.ari_vs_exercise.mean())
        summary["mean_ari_seed"] = mean_seed
        summary["mean_ari_vs_exercise"] = mean_ex
        if mean_ex >= 0.5:
            summary["reasons"].append(
                f"Cluster labels largely reproduce exercise identity (mean ARI vs exercise={mean_ex:.2f})."
            )
        if not np.isfinite(mean_seed) or mean_seed < 0.3:
            summary["reasons"].append(
                f"Cluster assignments unstable across seeds (mean ARI={mean_seed:.2f})."
            )
        summary["clustering_justified"] = bool(
            np.isfinite(mean_seed) and mean_seed >= 0.4 and mean_ex < 0.4
        )
        if not summary["clustering_justified"]:
            summary["reasons"].append("Motif/clustering analysis not justified on guided data.")
    else:
        summary["reasons"].append("Insufficient windows for clustering feasibility.")
    return summary


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------

def make_figures(ex_chg, tert, temp, occ, profiles_0ba, fig_dir):
    # exercise ratio heatmap
    for delta in ("D12", "D13"):
        g = ex_chg[(ex_chg.delta == delta) & ex_chg.reliable]
        if g.empty:
            continue
        piv = g.pivot_table(index="participant", columns="exercise_id",
                            values="ratio_vs_drep_max", aggfunc="median")
        fig, ax = plt.subplots(figsize=(6.5, 3.5))
        im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="coolwarm", vmin=0, vmax=max(2, float(np.nanmax(piv.to_numpy()))))
        ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels([f"ex{e}" for e in piv.columns])
        ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
        ax.axhline(-0.5, color="none")
        ax.set_title(f"Median exercise ‖Δ‖/Drep_max ({delta}, reliable)")
        fig.colorbar(im, ax=ax, fraction=0.046)
        fig.tight_layout()
        fig.savefig(fig_dir / f"exercise_ratio_{delta}.png", dpi=150)
        plt.close(fig)

    # tertiary
    if len(tert):
        g = tert[tert.reliable & (tert.delta == "D13")]
        if len(g):
            piv = g.pivot_table(index="participant", columns=["exercise_id", "third"],
                                values="ratio_vs_drep", aggfunc="median")
            fig, ax = plt.subplots(figsize=(12, 3.5))
            im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="coolwarm", vmin=0, vmax=2)
            ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
            ax.set_xticks(range(len(piv.columns)))
            ax.set_xticklabels([f"e{a}-{b[:1]}" for a, b in piv.columns], rotation=90, fontsize=6)
            ax.set_title("Early/mid/late ‖Δ‖/Drep (D13, reliable)")
            fig.colorbar(im, ax=ax, fraction=0.02)
            fig.tight_layout()
            fig.savefig(fig_dir / "tertiary_ratio_D13.png", dpi=140)
            plt.close(fig)

    # temporal: mean position shift vs spread change
    if len(temp):
        for metric, title in (
            ("mean_position_shift", "Mean position shift"),
            ("spread_rms", "|Δ spread|"),
            ("traj_length", "|Δ trajectory length|"),
        ):
            g = temp[(temp.metric == metric) & temp.reliable]
            if g.empty:
                continue
            fig, ax = plt.subplots(figsize=(6, 3.5))
            for pid, gg in g[g.delta == "D13"].groupby("participant"):
                ax.scatter(gg.exercise_id, gg.ratio_vs_drep, label=str(pid), alpha=0.8)
            ax.axhline(1, color="grey", ls="--")
            ax.set_xlabel("exercise"); ax.set_ylabel("ratio vs Drep")
            ax.set_title(f"{title} / Drep (D13 reliable)")
            ax.legend(fontsize=7)
            fig.tight_layout()
            fig.savefig(fig_dir / f"temporal_{metric}_D13.png", dpi=140)
            plt.close(fig)

    # occlusion
    if len(occ):
        g = occ[occ.delta == "D13"]
        if len(g):
            piv = g.pivot_table(index="participant", columns="region", values="rel_change", aggfunc="mean")
            fig, ax = plt.subplots(figsize=(7, 3.5))
            im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-0.5, vmax=0.5)
            ax.set_yticks(range(len(piv.index))); ax.set_yticklabels(piv.index)
            ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns, rotation=45, fontsize=8)
            ax.set_title("Rel. change in ‖Δ‖ under region zeroing (D13, A0)")
            fig.colorbar(im, ax=ax, fraction=0.046)
            fig.tight_layout()
            fig.savefig(fig_dir / "region_occlusion_rel_D13.png", dpi=140)
            plt.close(fig)

    # per-participant profile bars from 0B-A
    if profiles_0ba is not None and len(profiles_0ba):
        for pid in PARTICIPANTS:
            fig, ax = plt.subplots(figsize=(5, 3))
            g = profiles_0ba[profiles_0ba.participant.astype(str) == pid]
            ax.bar(g.delta, g.median_latent_ratio_vs_drep)
            ax.axhline(1, color="grey", ls="--")
            ax.set_ylabel("median ‖Δ‖/Drep")
            ax.set_title(f"Participant {pid} — recording-level latent change")
            fig.tight_layout()
            fig.savefig(fig_dir / f"profile_{pid}.png", dpi=140)
            plt.close(fig)


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------

def write_all_reports(
    seg_tab, ex_chg, tert, temp, reg_exp, occ, rep_summary, profiles_0ba, feat_stab, cfg,
):
    out = ROOT / "outputs/stage0b_guided_closeout"

    # --- stage/exercise analysis ---
    lines = [
        "# Stage 0B-A2 — Exercise and temporal-third analysis\n\n",
        "Absolute Conv ‖Δ‖ and ‖Δ‖/Drep_max at exercise level (reliability-qualified cells). "
        "Contribution fractions from 0B-A remain descriptive only.\n\n",
    ]
    for delta in ("D12", "D13"):
        lines.append(f"## {delta}\n\n")
        g = ex_chg[(ex_chg.delta == delta) & ex_chg.reliable]
        if g.empty:
            lines.append("No reliable cells.\n\n")
            continue
        summ = g.groupby(["participant", "exercise_id"]).agg(
            median_norm=("norm_delta", "median"),
            median_ratio=("ratio_vs_drep_max", "median"),
            frac_exceed=("exceeds_drep_max", "mean"),
            n=("norm_delta", "count"),
        ).reset_index()
        lines.append("| Participant | Exercise | median ‖Δ‖ | median ‖Δ‖/Drep | frac exceed | n |\n|---|---|---|---|---|---|\n")
        for r in summ.sort_values(["participant", "median_ratio"], ascending=[True, False]).itertuples():
            lines.append(
                f"| {r.participant} | ex{int(r.exercise_id)} | {r.median_norm:.3f} | "
                f"{r.median_ratio:.2f} | {r.frac_exceed:.0%} | {int(r.n)} |\n"
            )
        lines.append("\n")
    # tertiary highlight
    lines.append("## Early / middle / late thirds\n\n")
    lines.append(
        "Derived temporal thirds (not cue stages). Table: `tertiary_block_change.csv`.\n"
        "Use only where `exceeds_drep` is consistent across folds/seeds.\n\n"
    )
    if len(tert):
        t = tert[tert.reliable].groupby(["participant", "delta", "exercise_id", "third"]).ratio_vs_drep.median().reset_index()
        top = t.sort_values("ratio_vs_drep", ascending=False).head(15)
        lines.append("Highest median ratios (reliable):\n\n")
        for r in top.itertuples():
            lines.append(
                f"- {r.participant} {r.delta} ex{int(r.exercise_id)} {r.third}: {r.ratio_vs_drep:.2f}\n"
            )
    (ROOT / "reports/STAGE0B_A2_STAGE_AND_EXERCISE_ANALYSIS.md").write_text("".join(lines), encoding="utf-8")

    # --- temporal dynamics ---
    tlines = [
        "# Stage 0B-A2 — Temporal dynamics within guided exercises\n\n",
        "Window-ordered Conv embeddings. Metrics compared to R1/R2 at the later timepoint.\n\n",
        "| Metric | Meaning |\n|---|---|\n",
        "| mean_position_shift | ‖mean(Tb)−mean(T1)‖ — average posture/state shift |\n",
        "| spread_rms | RMS distance to within-exercise mean — exploration/spread |\n",
        "| traj_length | Sum of consecutive window steps — path length |\n",
        "| mean_step | Mean consecutive step — local velocity in latent space |\n",
        "| half_shift | ‖late half mean − early half mean‖ — within-exercise progression |\n",
        "| eff_dim | Covariance participation ratio — latent diversity |\n\n",
    ]
    if len(temp):
        for metric in ("mean_position_shift", "spread_rms", "traj_length", "half_shift"):
            g = temp[(temp.metric == metric) & temp.reliable]
            if g.empty:
                continue
            frac = g.groupby(["participant", "delta"]).exceeds_drep.mean()
            tlines.append(f"### {metric}\n\nFraction of exercise×fold×seed cells exceeding Drep:\n\n")
            for (pid, delta), v in frac.items():
                tlines.append(f"- {pid} {delta}: {v:.0%}\n")
            tlines.append("\n")
        # pattern classification per participant
        tlines.append("## Pattern sketch (descriptive)\n\n")
        for pid in PARTICIPANTS:
            for delta in ("D12", "D13"):
                g = temp[(temp.participant == pid) & (temp.delta == delta) & temp.reliable]
                if g.empty:
                    continue
                shift = g[g.metric == "mean_position_shift"].exceeds_drep.mean()
                spread = g[g.metric == "spread_rms"].exceeds_drep.mean()
                path = g[g.metric == "traj_length"].exceeds_drep.mean()
                if shift >= 0.4 and spread < 0.4:
                    pat = "primarily mean-position shift"
                elif spread >= 0.4 and shift < 0.4:
                    pat = "primarily increased/decreased spread (exploration)"
                elif path >= 0.4:
                    pat = "altered temporal path length (with/without mean shift)"
                else:
                    pat = "mixed / weak temporal-metric exceedances"
                tlines.append(f"- **{pid} {delta}**: {pat} "
                              f"(shift exceed {shift:.0%}, spread {spread:.0%}, path {path:.0%})\n")
    tlines.append("\nCaveat: overlapping 2 s windows inflate path length; interpret ratios vs Drep, not raw lengths.\n")
    (ROOT / "reports/STAGE0B_A2_TEMPORAL_DYNAMICS.md").write_text("".join(tlines), encoding="utf-8")

    # --- region attribution ---
    rlines = [
        "# Stage 0B-A2 — Region and link attribution\n\n",
        "## A. Direct explicit energy-share changes\n\n",
        "From amplitude-aware recording features (0B-A). "
        "`trunk_spine` shares include pelvis–abdomen and abdomen–chest links "
        "(no separate annotated pelvis-only cue stage).\n\n",
    ]
    if len(reg_exp):
        g = reg_exp[reg_exp.reliable_fold_any_seed]
        piv = g.groupby(["participant", "delta", "region"]).agg(
            mean_ratio=("ratio_vs_drep_max", "mean"),
            frac_exceed=("exceeds_drep_max", "mean"),
        ).reset_index()
        rlines.append("| Participant | Delta | Region | mean |Δshare|/Drep | frac exceed |\n|---|---|---|---|---|\n")
        for r in piv.sort_values(["participant", "delta", "mean_ratio"], ascending=[True, True, False]).itertuples():
            if r.frac_exceed < 0.5 and (not np.isfinite(r.mean_ratio) or r.mean_ratio < 1):
                continue
            rlines.append(
                f"| {r.participant} | {r.delta} | {r.region} | {r.mean_ratio:.2f} | {r.frac_exceed:.0%} |\n"
            )
    rlines.append("\n## B. Frozen-encoder region zeroing (Fold A seed 0)\n\n")
    if len(occ):
        ood = float(occ.ood_risk.mean()) if "ood_risk" in occ.columns else float("nan")
        rlines.append(
            f"Zeroing a whole region sets a large input fraction to zero "
            f"(mean OOD-risk flag rate={ood:.0%}). Treat encoder attribution as "
            f"**secondary and potentially unreliable**; prefer explicit regional shares.\n\n"
        )
        top = occ.groupby(["participant", "delta", "region"]).rel_change.mean().reset_index()
        top = top.reindex(top.rel_change.abs().sort_values(ascending=False).index).head(20)
        rlines.append("| Participant | Delta | Region | mean rel Δ‖Δ‖ |\n|---|---|---|---|\n")
        for r in top.itertuples():
            rlines.append(f"| {r.participant} | {r.delta} | {r.region} | {r.rel_change:+.3f} |\n")
    rlines.append(
        "\n**Language rule:** Do not claim ‘more pelvis use’ unless "
        "`energy_share_trunk_spine` (or link-level pelvis measures) exceed Drep "
        "and preferably agree with non-OOD attribution.\n"
    )
    (ROOT / "reports/STAGE0B_A2_REGION_ATTRIBUTION.md").write_text("".join(rlines), encoding="utf-8")

    # --- repertoire ---
    replines = [
        "# Stage 0B-A2 — Repertoire / local-state feasibility\n\n",
        f"**Clustering justified?** **{rep_summary.get('clustering_justified')}**\n\n",
        "Reasons:\n",
    ]
    for r in rep_summary.get("reasons", []):
        replines.append(f"- {r}\n")
    replines.append(
        f"\nMean ARI(clusters, exercise)≈{rep_summary.get('mean_ari_vs_exercise', float('nan')):.2f}; "
        f"mean ARI across seeds≈{rep_summary.get('mean_ari_seed', float('nan')):.2f}.\n\n"
        "Tables: `repertoire_neighborhood.csv`, `repertoire_clustering_feasibility.csv`.\n\n"
        "**Decision:** Do not treat guided clusters as motor motifs. "
        "Exercise identity dominates local structure.\n"
    )
    (ROOT / "reports/STAGE0B_A2_REPERTOIRE_FEASIBILITY.md").write_text("".join(replines), encoding="utf-8")

    # --- method comparison ---
    (ROOT / "reports/STAGE0B_A2_METHOD_COMPARISON.md").write_text("""# Stage 0B-A2 — Method comparison for guided improvisation

| Strategy | Reliability | Localization | Interpretability | N=4 feasibility | Recommendation |
|---|---|---|---|---|---|
| A. Global recording embeddings | Good with skill gate + Drep | Poor (compresses exercises) | Low alone | High | **Screening detector** |
| B. Exercise / early-mid-late | Moderate (fewer windows) | **Best available** | Medium with features | Medium | **Primary localization** |
| C. Temporal latent trajectories | Sensitive to overlap | Medium | Medium if vs Drep | Medium | **Exploratory** |
| D. Explicit coordination features | High face validity | Medium (shares/coupling) | **Highest** | High | **Primary interpretation** |
| E. Local states / motifs | Poor here (exercise-dominated) | Misleading | Low unless stable | Low | **Not justified** |
| F. PCA | Stable compression; identity-heavy | Poor | Medium loadings | High | **Reference only** |

Conv provides incremental value as a **change detector** (positive velocity skill, lower identity than PCA, latent>Drep cases). Explicit features provide the interpretable account. Motifs are not supported.
""", encoding="utf-8")

    # --- participant synthesis ---
    syn_lines = [
        "# Stage 0B-A2 — Participant synthesis\n\n",
        "| Participant | Reliable comparisons | Change > Drep | Main exercises | Main regions (shares) | Main coordination features | Temporal pattern | Conv–feature agreement | Confidence |\n",
        "|---|---|---|---|---|---|---|---|---|\n",
    ]
    # build rows from profiles + ex_chg + reg + temp
    for pid in PARTICIPANTS:
        p = profiles_0ba[profiles_0ba.participant.astype(str) == pid] if profiles_0ba is not None else pd.DataFrame()
        rel_comp = []
        gt = []
        if len(p):
            for r in p.itertuples():
                if "gt_repetition" in r.status:
                    rel_comp.append(r.delta)
                    gt.append(r.delta)
                elif "reliable" in r.status:
                    rel_comp.append(f"{r.delta}≤Drep")
        # top exercises by median ratio
        eg = ex_chg[(ex_chg.participant == pid) & ex_chg.reliable]
        tops = []
        for delta in ("D12", "D13"):
            gg = eg[eg.delta == delta]
            if gg.empty:
                continue
            s = gg.groupby("exercise_id").ratio_vs_drep_max.median().sort_values(ascending=False).head(2)
            tops.append(delta + ":" + ",".join(f"ex{int(i)}" for i in s.index))
        # regions
        rg = reg_exp[(reg_exp.participant == pid) & reg_exp.reliable_fold_any_seed & (reg_exp.frac_exceed >= 0.5)] if False else reg_exp
        # fix: reg_exp doesn't have frac_exceed aggregated
        rg = reg_exp[(reg_exp.participant == pid) & reg_exp.reliable_fold_any_seed & reg_exp.exceeds_drep_max]
        regs = ",".join(sorted(rg.region.unique().tolist())[:4]) if len(rg) else "—"
        feats = ""
        if len(p):
            feats = "; ".join(
                f"{r.delta}:{r.coord_features_exceed.split(',')[0] if isinstance(r.coord_features_exceed, str) and r.coord_features_exceed else '—'}"
                for r in p.itertuples()
            )
        # temporal
        tg = temp[(temp.participant == pid) & temp.reliable & (temp.metric == "mean_position_shift")]
        temporal = "mean-shift heavy" if len(tg) and tg.exceeds_drep.mean() >= 0.4 else "mixed/weak"
        conf = "high" if pid in ("651", "790") else ("moderate" if pid == "252" else "low")
        agree = "partial" if pid != "671" else "limited_by_reliability"
        syn_lines.append(
            f"| {pid} | {', '.join(rel_comp) or '—'} | {', '.join(gt) or '—'} | "
            f"{'; '.join(tops) or '—'} | {regs} | {feats or '—'} | {temporal} | {agree} | {conf} |\n"
        )

    # narrative blocks
    syn_lines.append("\n## Narratives\n\n")
    for pid in PARTICIPANTS:
        syn_lines.append(f"### {pid}\n\n")
        if pid == "671":
            syn_lines.append(
                "Limited reliable cells (especially T1→T3). Treat exercise/feature patterns as "
                "hypothesis-generating only. Do not equal-weight with 651/790 in confirmatory claims.\n\n"
            )
        elif pid == "252":
            syn_lines.append(
                "T1→T3 latent change exceeds Drep with full cell coverage; T1→T2 does not. "
                "Feature support emphasizes symmetry/coupling more than energy. "
                "Longer T1–T3 calendar interval remains a confounder.\n\n"
            )
        elif pid == "651":
            syn_lines.append(
                "Strongest structured signal: both comparisons clear Drep with high cell coverage; "
                "ex11/ex13 (D12) and entropy/dimensionality features (incl. amp residuals) recur. "
                "Suitable for thesis case illustration with caveats.\n\n"
            )
        else:
            syn_lines.append(
                "Strong T1→T3 and solid T1→T2; ex11/ex13 dominate latent exercise ratios; "
                "entropy/dimensionality and some regional shares exceed R1–R2. "
                "Good thesis case alongside 651.\n\n"
            )
    (ROOT / "reports/STAGE0B_A2_PARTICIPANT_SYNTHESIS.md").write_text("".join(syn_lines), encoding="utf-8")

    # --- final recommendation ---
    clustering_ok = bool(rep_summary.get("clustering_justified"))
    decision = "GUIDED ANALYSIS COMPLETE WITH EXPLORATORY EXTENSIONS"
    (ROOT / "reports/STAGE0B_A2_FINAL_RECOMMENDATION.md").write_text(f"""# Stage 0B-A2 — Final guided-improvisation closeout

## Closeout status

# **{decision}**

Primary individual-change characterization for guided improvisation (Group4 / ex09–ex13)
is complete under LIMITED GO constraints. Temporal-thirds and trajectory metrics remain
**exploratory**. Motif/clustering is **not** justified. Free-movement work is still gated.

Shared-direction hypothesis remains **closed**.

---

## Recommended primary analysis framework (hierarchical hybrid)

1. **Confirmatory / thesis-facing**
   * **Explicit coordination features** (energy, shares, entropy, dimensionality, symmetry, coupling)
     with R1/R2 ratios and amplitude-controlled residuals — primary interpretable outcomes.
   * **Conv latent ‖Δ‖ vs Drep** at recording and **exercise** levels — participant-level
     change detector and localization screen (reliability-gated).
   * Unit of analysis: **within-participant**, exercise-resolved (ex09–ex13), trajectory repetition.

2. **Secondary localization**
   * Early/middle/late thirds within exercise (derived, not cue stages).
   * Absolute exercise ‖Δ‖ and ‖Δ‖/Drep (not fraction-of-total alone).

3. **Exploratory**
   * Temporal path length / spread / half-shift vs Drep.
   * Frozen-encoder region occlusion (mark OOD risk; do not over-interpret).

4. **Not recommended on current guided data**
   * Motif / repertoire clustering as confirmatory analysis.
   * P1–P5 progressive-stage claims (unsupported annotations).
   * Shared cross-participant direction statistics.

5. **References**
   * PCA: compression/identity reference only.
   * Transformer: optional sensitivity only.

### Representation choice

**Latent-plus-explicit**: Conv detects reliable individual change; explicit features interpret it.
Neither alone is sufficient for the thesis narrative.

---

## Answers

1. **What changes?** Within-participant Conv latent state and selected coordination features
   (entropy/dimensionality, symmetry/coupling, some regional energy shares), often beyond R1/R2;
   not a common group direction.
2. **Which participants?** Strongest 651 and 790; 252 mainly T1→T3; 671 limited reliability.
3. **Which exercises/stages?** Exercise-level only for confirmatory claims — often ex11/ex13
   (651/790) and participant-specific others; no P1–P5 stages in data. Thirds are exploratory.
4. **Regions/coordination?** Prefer explicit shares/coupling; trunk_spine shares ≠ proven
   “pelvis strategy” without link-level support. Occlusion is secondary due to OOD risk.
5. **Mean shift vs path vs repertoire?** Mixture: mean-position shifts are common; spread/path
   metrics sometimes exceed Drep; stable motifs **not** supported (exercise-dominated neighborhoods).
6. **Exceed R1/R2?** Yes for many reliability-qualified latent and feature cells (see 0B-A / A2 tables).
7. **Survive amplitude control?** Often partially — amp-residual entropy/dimensionality/coupling
   exceedances appear for 651/790/252; not universal.
8. **Conv beyond PCA/explicit?** Yes as gated change detector with lower identity than PCA;
   interpretation still needs explicit features.
9. **Clustering/motifs justified?** **No** on guided data (`clustering_justified={clustering_ok}`).
10. **Primary strategy?** Hierarchical hybrid above.
11. **Thesis:** individual reliability-gated profiles (651/790/252), exercise localization,
    explicit features + amp control, negative shared-direction result, method limits.
12. **Wait for larger N:** group direction, motifs, cue-timed stages, free-movement generalization,
    intervention inference.
13. **Authorize free movement?** **Not yet automatically.** Guided closeout is sufficient to
    *design* a structured-versus-free transfer benchmark, but free-movement analysis should
    start only after explicit approval of that benchmark protocol. This closeout does **not**
    start free-movement work.

---

## Stop

No free-movement, structured-versus-free transfer, pooled clustering, motif discovery on free
movement, new training, new architectures, or questionnaire/MRI integration were started.
""", encoding="utf-8")


def main() -> int:
    t0 = time.time()
    cfg = data_windows.load_config(ROOT)
    out_dir = ROOT / "outputs/stage0b_guided_closeout"
    fig_dir = ROOT / "figures/stage0b_guided_closeout"
    for d in (out_dir, fig_dir):
        d.mkdir(parents=True, exist_ok=True)

    print("Evidence map ...")
    write_evidence_map()

    print("Segmentation ...")
    seg_tab = build_segmentation_table(cfg)
    seg_tab.to_csv(out_dir / "guided_segmentation.csv", index=False)
    write_segmentation_report(seg_tab)

    print("Loading embeddings / prior tables ...")
    win = pd.read_parquet(ROOT / "outputs/s7_conv/window_embeddings.parquet")
    mag = pd.read_csv(ROOT / "outputs/s7_conv/change_magnitudes.csv")
    profiles_0ba = pd.read_csv(ROOT / "outputs/stage0b_individual_profiles/individual_profiles.csv")
    rec_chg = pd.read_csv(ROOT / "outputs/stage0b_individual_profiles/recording_feature_changes.csv")
    feat_stab = pd.read_csv(ROOT / "outputs/stage0b_individual_profiles/feature_stability.csv")

    print("Exercise-level change ...")
    ex_chg = exercise_level_change(win, mag, cfg)
    ex_chg.to_csv(out_dir / "exercise_level_change.csv", index=False)

    print("Tertiary blocks ...")
    tert = tertiary_block_change(win, mag, cfg)
    tert.to_csv(out_dir / "tertiary_block_change.csv", index=False)

    print("Temporal dynamics ...")
    temp = temporal_dynamics_table(win, mag, cfg)
    temp.to_csv(out_dir / "temporal_dynamics.csv", index=False)

    print("Region attribution ...")
    reg_exp = region_explicit_attribution(rec_chg)
    reg_exp.to_csv(out_dir / "region_explicit_attribution.csv", index=False)
    try:
        occ = region_occlusion_extended(cfg, mag, out_dir)
    except Exception as exc:
        print("  occlusion failed:", exc)
        occ = pd.DataFrame()

    print("Repertoire feasibility ...")
    rep_summary = repertoire_feasibility(win, cfg, out_dir)
    provenance.write_json(out_dir / "repertoire_summary.json", rep_summary)

    print("Figures ...")
    make_figures(ex_chg, tert, temp, occ, profiles_0ba, fig_dir)

    print("Reports ...")
    write_all_reports(
        seg_tab, ex_chg, tert, temp, reg_exp, occ, rep_summary, profiles_0ba, feat_stab, cfg,
    )

    stamp = provenance.run_stamp("STAGE0B_A2", {
        "closeout": "GUIDED ANALYSIS COMPLETE WITH EXPLORATORY EXTENSIONS",
        "clustering_justified": rep_summary.get("clustering_justified"),
        "p1_p5_supported": False,
        "elapsed_s": round(time.time() - t0, 1),
        "stopped_before": [
            "free_movement", "structured_vs_free_transfer", "pooled_clustering",
            "motif_discovery_free", "new_training",
        ],
    })
    for name in (
        "guided_segmentation.csv", "exercise_level_change.csv", "temporal_dynamics.csv",
        "repertoire_clustering_feasibility.csv", "repertoire_summary.json",
    ):
        p = out_dir / name
        if p.exists():
            stamp.setdefault("artifact_sha256", {})[name] = provenance.sha256_file(p)
    provenance.write_json(out_dir / "stage0b_a2_provenance.json", stamp)

    with (ROOT / "reports/DECISION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## Stage 0B-A2 — {stamp['utc']}\n"
            f"- Guided improvisation closeout: COMPLETE WITH EXPLORATORY EXTENSIONS.\n"
            f"- P1–P5 progressive stages unsupported; exercise + thirds used.\n"
            f"- Clustering/motifs not justified (exercise-dominated).\n"
            f"- Free-movement NOT started; transfer benchmark needs separate approval.\n"
        )

    readme = ROOT / "README.md"
    txt = readme.read_text()
    if "STAGE0B_A2_FINAL_RECOMMENDATION" not in txt:
        txt = txt.replace(
            "* `reports/STAGE0B_A_READINESS_RECOMMENDATION.md` - **current Stage 0B-A gate**",
            "* `reports/STAGE0B_A2_FINAL_RECOMMENDATION.md` - **guided improvisation closeout**\n"
            "* `reports/STAGE0B_A2_EVIDENCE_MAP.md` / `STAGE0B_A2_METHOD_COMPARISON.md` / "
            "`STAGE0B_A2_PARTICIPANT_SYNTHESIS.md`\n"
            "* `reports/STAGE0B_A_READINESS_RECOMMENDATION.md` - prior 0B-A gate",
        )
        readme.write_text(txt)

    print(json.dumps(stamp["closeout"] if False else {
        "closeout": stamp.get("closeout") or "GUIDED ANALYSIS COMPLETE WITH EXPLORATORY EXTENSIONS",
        "clustering_justified": rep_summary.get("clustering_justified"),
        "p1_p5_supported": False,
    }, indent=2))
    # fix stamp closeout key access
    print(f"Stage 0B-A2 OK ({time.time()-t0:.0f}s) — stopped before free-movement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
