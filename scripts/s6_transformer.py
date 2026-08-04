#!/usr/bin/env python3
"""S6 — SharedMotionTransformer training: 2 folds × 3 seeds × 2 objectives.

Frozen from S5:
  mask_ratio=30%, window=2s, patch=10, d=32, 2 blocks, CPU, early-stop on
  held-out contiguous T1 blocks only.

Does NOT begin S7/S8 longitudinal direction analysis. Objective selection and
architecture recommendation are frozen from held-out T1 only before any
reliability / T2/T3 tables are written into the decision.
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
import yaml
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, models, provenance, train_masked, trivial  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_N = 500
BOOTSTRAP_SEED = 42


def fold_data(fold: str):
    w = data_windows.load_window_index(ROOT)
    tr = w[(w.fold == fold) & (w.role == "training") & w.usable]
    es = w[(w.fold == fold) & (w.role == "early_stop") & w.usable]
    x_tr, tr_i = data_windows.materialise_windows(tr, ROOT, "masked_6d")
    x_es, es_i = data_windows.materialise_windows(es, ROOT, "masked_6d")
    y_tr, _ = data_windows.materialise_windows(tr_i, ROOT, "masked_angular_velocity")
    y_es, _ = data_windows.materialise_windows(es_i, ROOT, "masked_angular_velocity")
    return x_tr, x_es, y_tr, y_es, tr_i, es_i


def eval_all_windows():
    w = data_windows.load_window_index(ROOT)
    ev = w[(w.role == "evaluation") & w.usable]
    x, idx = data_windows.materialise_windows(ev, ROOT, "masked_6d")
    y, _ = data_windows.materialise_windows(idx, ROOT, "masked_angular_velocity")
    return x, y, idx


def build_transformer(cfg, objective, state=None):
    target_dim = 6 if objective == "masked_6d" else 3
    m = cfg["model"]
    net = models.SharedMotionTransformer(
        n_links=m["n_links"], n_patches=m["n_patches"], patch_frames=m["patch_frames"],
        dim=m["hidden_dim"], n_blocks=m["n_blocks"], expansion=m["ffn_expansion"],
        target_dim=target_dim,
    )
    if state is not None:
        net.load_state_dict(state)
    net.eval()
    return net


def build_conv(cfg, objective, state=None):
    target_dim = 6 if objective == "masked_6d" else 3
    net = models.ConvMaskedPredictor(
        n_links=cfg["model"]["n_links"], patch_frames=cfg["model"]["patch_frames"],
        channels=cfg["s5"]["conv_channels"], target_dim=target_dim,
        embedding_dim=cfg["model"]["embedding_dim"],
    )
    if state is not None:
        net.load_state_dict(state)
    net.eval()
    return net


def shuffle_control(x6, mode: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = x6.copy()
    if mode == "time":
        for i in range(len(out)):
            out[i] = out[i][rng.permutation(out.shape[1])]
    elif mode == "link":
        for i in range(len(out)):
            out[i] = out[i][:, rng.permutation(out.shape[2])]
    return out


def trajectory_rep(cfg, fold: str) -> int:
    return int(cfg["folds"][fold]["trajectory_repetition"])


def select_objective(runs: pd.DataFrame, controls: pd.DataFrame) -> tuple[str, str, dict]:
    """Held-out T1 only. No T2/T3."""
    sel = runs.groupby("objective").skill_heldout_t1.agg(["mean", "std", "min", "max", "count"])
    fold_means = runs.groupby(["objective", "fold"]).skill_heldout_t1.mean().unstack("fold")
    means = sel["mean"]
    details = {
        "per_objective": sel.round(6).to_dict(),
        "per_fold_mean": fold_means.round(6).to_dict(),
    }
    # require positive skill in both folds for a candidate
    positive_both = {
        obj: bool((fold_means.loc[obj] > 0).all()) for obj in fold_means.index
    }
    details["positive_skill_both_folds"] = positive_both
    candidates = [obj for obj, ok in positive_both.items() if ok]
    if not candidates:
        # fall back to highest mean even if not positive both folds
        chosen = means.idxmax()
        reason = (
            "no objective positive in both folds; selected highest mean held-out T1 "
            f"skill ({chosen})"
        )
        return chosen, reason, details

    cand_means = means.loc[candidates]
    if len(candidates) == 1:
        chosen = candidates[0]
        reason = "only objective with positive skill in both folds"
    elif abs(cand_means.iloc[0] - cand_means.iloc[1]) < 0.02:
        idp = controls[controls.control == "identity_probe"]
        idp = idp[idp.objective.isin(candidates)].groupby("objective")["value"].mean()
        chosen = idp.idxmin()
        reason = (
            f"skill within 0.02 among positive-both-fold objectives; "
            f"tie-break lower identity probe ({idp.round(4).to_dict()})"
        )
    else:
        chosen = cand_means.idxmax()
        reason = "higher mean held-out T1 skill among objectives positive in both folds"
    return chosen, reason, details


def paired_bootstrap_skill_diff(
    err_tf: np.ndarray, err_cv: np.ndarray, triv: np.ndarray, n_boot: int, seed: int,
) -> dict:
    """Bootstrap CI on pooled skill(TF)-skill(Conv).

    Per-window skill ratios are unstable when trivial error is small; instead
    resample windows and recompute pooled skill on each sample, matching the
    aggregate metric used in training.
    """
    ok = np.isfinite(err_tf) & np.isfinite(err_cv) & np.isfinite(triv) & (triv > 0)
    e_tf, e_cv, t = err_tf[ok], err_cv[ok], triv[ok]
    n = len(t)
    if n < 5:
        return {"n": int(n), "mean_diff": float("nan"),
                "ci95_lo": float("nan"), "ci95_hi": float("nan"),
                "frac_positive_boot": float("nan")}

    def pooled(err, triv_arr, idx):
        return trivial.skill(float(err[idx].mean()), float(triv_arr[idx].mean()))

    base = pooled(e_tf, t, np.arange(n)) - pooled(e_cv, t, np.arange(n))
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boots[i] = pooled(e_tf, t, idx) - pooled(e_cv, t, idx)
    return {
        "n": int(n),
        "mean_diff": float(base),
        "ci95_lo": float(np.quantile(boots, 0.025)),
        "ci95_hi": float(np.quantile(boots, 0.975)),
        "frac_positive_boot": float((boots > 0).mean()),
    }


@torch.no_grad()
def window_errors(
    net, x6, y, objective, mask_ratio, span, patch_frames, seed, batch_size=32,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-window model MSE and best-trivial MSE under a shared mask stream."""
    n = len(x6)
    err_m = np.full(n, np.nan)
    err_t = np.full(n, np.nan)
    if n == 0:
        return err_m, err_t
    g = torch.Generator().manual_seed(seed)
    net.eval()
    pos = 0
    while pos < n:
        xb = torch.from_numpy(x6[pos:pos + batch_size])
        if objective == "masked_6d":
            yb = xb
        else:
            yb = torch.from_numpy(y[pos:pos + batch_size])
        b, t, l, _ = xb.shape
        p = t // patch_frames
        mask = models.structured_mask(b, l, p, mask_ratio, span, g)
        target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
        pred = net(xb, mask)
        # per-window masked MSE
        m = mask.unsqueeze(-1).unsqueeze(-1).expand_as(target)
        se = (pred - target) ** 2
        for i in range(b):
            mi = m[i]
            if mi.any():
                err_m[pos + i] = float(se[i][mi].mean().item())
            te = trivial.trivial_errors(target[i:i + 1], mask[i:i + 1], which="both")
            err_t[pos + i] = min(te["mean_motion"], te["interpolation"])
        pos += b
    return err_m, err_t


def plot_loss_curves(hist: pd.DataFrame, tag: str, best_epoch: int, fig_dir: Path):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(hist.epoch, hist.train_loss, label="train")
    ax.plot(hist.epoch, hist.val_loss, label="held-out T1")
    ax.axvline(best_epoch, color="crimson", ls="--", lw=1)
    ax.set_xlabel("epoch"); ax.set_ylabel("masked MSE")
    ax.set_title(tag); ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / f"loss_{tag}.png", dpi=120)
    plt.close(fig)


def plot_prediction_example(
    net, x6, y, objective, mask_ratio, span, patch_frames, link_ids, fig_path: Path, seed: int,
):
    """One held-out window: target vs prediction on a heavily masked link."""
    if len(x6) == 0:
        return
    idx = min(3, len(x6) - 1)
    xb = torch.from_numpy(x6[idx:idx + 1])
    yb = xb if objective == "masked_6d" else torch.from_numpy(y[idx:idx + 1])
    g = torch.Generator().manual_seed(seed)
    p = xb.shape[1] // patch_frames
    l = xb.shape[2]
    mask = models.structured_mask(1, l, p, mask_ratio, span, g)
    with torch.no_grad():
        pred = net(xb, mask)
    target = yb.reshape(1, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
    # choose link with most masked patches
    counts = mask[0].sum(dim=0).numpy()
    li = int(np.argmax(counts))
    # flatten patches×frames → time for channel 0
    tgt = target[0, :, li, :, 0].reshape(-1).numpy()
    prd = pred[0, :, li, :, 0].reshape(-1).numpy()
    m_frame = mask[0, :, li].repeat_interleave(patch_frames).numpy()
    t = np.arange(len(tgt)) / 120.0
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, tgt, label="target", color="black", lw=1.2)
    ax.plot(t, prd, label="prediction", color="C0", lw=1.0)
    ymin, ymax = ax.get_ylim()
    ax.fill_between(t, ymin, ymax, where=m_frame, color="orange", alpha=0.2, label="masked")
    ax.set_xlabel("time (s)"); ax.set_ylabel("ch0")
    ax.set_title(f"{objective} · {link_ids[li]} (example window)")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=140)
    plt.close(fig)


def main() -> int:
    torch.set_num_threads(4)
    cfg = data_windows.load_config(ROOT)
    s5 = cfg["s5"]
    ratio = float(s5["frozen_mask_ratio"])
    span = tuple(s5["mask_span_patches"])
    seeds = cfg["model"]["seeds"]
    objectives = list(cfg["model"]["objectives"])
    link_ids, regions = data_windows.load_link_config(ROOT)
    eval_ex = cfg["exercises"]["evaluation"]
    patch_frames = cfg["model"]["patch_frames"]

    out_dir = ROOT / "outputs/s6_transformer"
    fig_dir = ROOT / "figures/s6_transformer"
    ckpt_dir = out_dir / "checkpoints"
    for d in (out_dir, fig_dir, ckpt_dir):
        d.mkdir(parents=True, exist_ok=True)

    # snapshot config
    (out_dir / "experiment_snapshot.yaml").write_text(
        (ROOT / "configs/experiment.yaml").read_text(), encoding="utf-8"
    )

    print(f"S6 SharedMotionTransformer  mask_ratio={ratio:.0%}  device=CPU")
    print("loading evaluation windows once ...")
    x_eval, y_eval, eval_idx = eval_all_windows()
    print(f"  {len(x_eval)} evaluation windows")

    run_rows, control_rows, emb_rows = [], [], []
    link_err_rows = []
    t_global = time.time()

    for fold in cfg["folds"]:
        print(f"\n##### FOLD {fold} #####")
        x_tr, x_es, y_tr, y_es, tr_i, es_i = fold_data(fold)
        print(f"  train {len(x_tr)}  early_stop {len(x_es)}")

        for objective in objectives:
            for seed in seeds:
                tag = f"{fold}_{objective}_s{seed}"
                print(f"\n-- {tag} --")
                ckpt_path = ckpt_dir / f"{tag}.pt"
                hist_path = out_dir / f"history_{tag}.csv"

                if ckpt_path.exists() and hist_path.exists():
                    hist = pd.read_csv(hist_path)
                    best_epoch = int(hist.val_loss.idxmin())
                    best = hist.iloc[best_epoch].to_dict()
                    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
                    n_params = models.count_parameters(build_transformer(cfg, objective, state))
                    run_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "mask_ratio": ratio, "best_epoch": best_epoch,
                        "val_loss": float(best["val_loss"]),
                        "skill_heldout_t1": float(best["skill"]),
                        "trivial_best": float(best["trivial_best"]),
                        "n_params": n_params, "seconds": 0.0, "resumed": True,
                    })
                    print(f"  resumed ckpt  skill={best['skill']:.4f}  epoch {best_epoch}")
                    net = build_transformer(cfg, objective, state)
                    hist_df = hist
                    best_epoch_i = best_epoch
                else:
                    res = train_masked.train_transformer(
                        x_tr, x_es,
                        y_tr if objective != "masked_6d" else None,
                        y_es if objective != "masked_6d" else None,
                        objective=objective, mask_ratio=ratio, span_patches=span,
                        seed=seed,
                        batch_size=s5["batch_size"],
                        max_epochs=s5["max_epochs"], lr=s5["learning_rate"],
                        weight_decay=s5["weight_decay"],
                        patience=s5["early_stop_patience"],
                        n_links=cfg["model"]["n_links"],
                        n_patches=cfg["model"]["n_patches"],
                        patch_frames=patch_frames,
                        hidden_dim=cfg["model"]["hidden_dim"],
                        n_blocks=cfg["model"]["n_blocks"],
                        ffn_expansion=cfg["model"]["ffn_expansion"],
                    )
                    torch.save(res.best_state, ckpt_path)
                    pd.DataFrame(res.history).to_csv(hist_path, index=False)
                    best = res.history[res.best_epoch]
                    run_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "mask_ratio": ratio, "best_epoch": res.best_epoch,
                        "val_loss": res.best_val_loss,
                        "skill_heldout_t1": best["skill"],
                        "trivial_best": best["trivial_best"],
                        "n_params": res.n_params,
                        "seconds": round(res.seconds, 1), "resumed": False,
                    })
                    print(
                        f"  skill(held-out T1)={best['skill']:.4f}  "
                        f"epoch {res.best_epoch}  {res.seconds:.0f}s  "
                        f"params={res.n_params}"
                    )
                    net = build_transformer(cfg, objective, res.best_state)
                    hist_df = pd.DataFrame(res.history)
                    best_epoch_i = res.best_epoch
                    plot_loss_curves(hist_df, tag, best_epoch_i, fig_dir)

                # overfitting diagnostic
                tr_sc = train_masked.score_arrays(
                    net, x_tr[: min(128, len(x_tr))],
                    (y_tr if objective != "masked_6d" else x_tr)[: min(128, len(x_tr))],
                    objective, ratio, span, patch_frames, seed + 501,
                    trivial_which="both",
                )
                es_sc = train_masked.score_arrays(
                    net, x_es, y_es if objective != "masked_6d" else x_es,
                    objective, ratio, span, patch_frames, seed + 17_001,
                    trivial_which="both",
                )
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "train_subset_skill", "value": tr_sc["skill"], "chance": np.nan,
                })
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "heldout_t1_skill_rescored", "value": es_sc["skill"],
                    "chance": np.nan,
                })
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "overfit_gap_skill",
                    "value": tr_sc["skill"] - es_sc["skill"], "chance": np.nan,
                })

                # identity probe
                z_tr = train_masked.embed_windows(net, x_tr)
                z_es = train_masked.embed_windows(net, x_es)
                clf = LogisticRegression(max_iter=1000, random_state=0)
                clf.fit(z_tr, tr_i.participant.astype(str))
                acc = float((clf.predict(z_es) == es_i.participant.astype(str)).mean())
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "identity_probe", "value": acc, "chance": 0.25,
                })

                # shuffle controls — primary skill (best trivial) + mean-motion sanity
                for mode in ("time", "link"):
                    x_sh = shuffle_control(x_es, mode, seed + (1 if mode == "time" else 2))
                    if objective == "masked_6d":
                        y_sh = x_sh
                    else:
                        y_sh = shuffle_control(y_es, mode, seed + (1 if mode == "time" else 2))
                    sc_best = train_masked.score_arrays(
                        net, x_sh, y_sh, objective, ratio, span, patch_frames,
                        seed + 99, trivial_which="both",
                    )
                    sc_mm = train_masked.score_arrays(
                        net, x_sh, y_sh, objective, ratio, span, patch_frames,
                        seed + 99, trivial_which="mean_motion",
                    )
                    control_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "control": f"shuffle_{mode}_skill_best_trivial",
                        "value": sc_best["skill"], "chance": 0.0,
                    })
                    control_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "control": f"shuffle_{mode}_skill_mean_motion_only",
                        "value": sc_mm["skill"], "chance": 0.0,
                    })

                # overshoot sensitivity (primary skill)
                li = link_ids.index("RShoulder_to_RUArm")
                is_rec = (es_i.recording_id == "790_T1_P1_R1").to_numpy()
                x_ex = x_es.copy(); x_ex[:, :, li, :] = 0.0
                y_ex = y_es.copy(); y_ex[:, :, li, :] = 0.0
                sc0 = train_masked.score_arrays(
                    net, x_es, y_es if objective != "masked_6d" else x_es,
                    objective, ratio, span, patch_frames, seed + 3, trivial_which="both",
                )
                sc_link = train_masked.score_arrays(
                    net, x_ex, y_ex if objective != "masked_6d" else x_ex,
                    objective, ratio, span, patch_frames, seed + 3, trivial_which="both",
                )
                keep = ~is_rec
                if keep.any() and is_rec.any():
                    sc_rec = train_masked.score_arrays(
                        net, x_es[keep],
                        (y_es if objective != "masked_6d" else x_es)[keep],
                        objective, ratio, span, patch_frames, seed + 3,
                        trivial_which="both",
                    )
                else:
                    sc_rec = sc0
                for name, sc in (
                    ("overshoot_skill_baseline", sc0),
                    ("overshoot_exclude_link_skill", sc_link),
                    ("overshoot_exclude_790T1_windows_skill", sc_rec),
                ):
                    control_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "control": name, "value": sc["skill"], "chance": np.nan,
                    })

                # per-link reconstruction error on held-out T1
                link_err = train_masked.per_link_masked_error(
                    net, x_es, y_es if objective != "masked_6d" else x_es,
                    objective, ratio, span, patch_frames, seed + 7,
                    n_links=len(link_ids),
                )
                for i, lid in enumerate(link_ids):
                    link_err_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "link_id": lid, "region": regions[lid],
                        "masked_mse": float(link_err[i]),
                    })

                # prediction example (one per fold/obj/seed0)
                if seed == 0:
                    plot_prediction_example(
                        net, x_es, y_es, objective, ratio, span, patch_frames,
                        link_ids, fig_dir / f"pred_example_{fold}_{objective}.png",
                        seed=123,
                    )

                # evaluation embeddings
                z_ev = train_masked.embed_windows(net, x_eval)
                agg = data_windows.aggregate_recording_embeddings(z_ev, eval_idx, eval_ex)
                agg.insert(0, "fold", fold)
                agg.insert(1, "objective", objective)
                agg.insert(2, "seed", seed)
                emb_rows.append(agg)

    runs = pd.DataFrame(run_rows)
    runs.to_csv(out_dir / "run_summary.csv", index=False)
    controls = pd.DataFrame(control_rows)
    controls.to_csv(out_dir / "controls.csv", index=False)
    emb = pd.concat(emb_rows, ignore_index=True)
    emb.to_csv(out_dir / "recording_embeddings.csv", index=False)
    pd.DataFrame(link_err_rows).to_csv(out_dir / "link_errors_heldout_t1.csv", index=False)

    # ------------------------------------------------------------------
    # Objective selection BEFORE any T2/T3 reliability tables enter the decision
    # ------------------------------------------------------------------
    chosen, reason, sel_details = select_objective(runs, controls)
    sel_table = runs.groupby("objective").skill_heldout_t1.agg(
        ["mean", "std", "min", "max"]
    )
    sel_table.to_csv(out_dir / "objective_selection_heldout_t1.csv")
    decision = {
        "selected_objective": chosen,
        "selection_reason": reason,
        "selection_inputs": "held-out T1 skill only (+ identity probe tie-break)",
        "details": sel_details,
        "frozen_before_t2_t3_reliability": True,
    }
    (out_dir / "SELECTED_OBJECTIVE.txt").write_text(
        f"{chosen}\n{reason}\n", encoding="utf-8"
    )
    provenance.write_json(out_dir / "OBJECTIVE_SELECTION.json", decision)
    print(f"\nselected objective: {chosen}  ({reason})")
    print(sel_table.round(4).to_string())

    # ------------------------------------------------------------------
    # Transformer vs Conv comparison (same objective, same held-out T1)
    # ------------------------------------------------------------------
    print("\n##### Transformer vs Conv #####")
    conv_dir = ROOT / "outputs/s5_conv"
    conv_runs = pd.read_csv(conv_dir / "run_summary.csv")
    conv_controls = pd.read_csv(conv_dir / "controls.csv")
    compare_rows, boot_rows = [], []

    for fold in cfg["folds"]:
        x_tr, x_es, y_tr, y_es, tr_i, es_i = fold_data(fold)
        y_es_use = y_es if chosen != "masked_6d" else x_es
        for seed in seeds:
            tf_ckpt = ckpt_dir / f"{fold}_{chosen}_s{seed}.pt"
            cv_ckpt = conv_dir / "checkpoints" / f"{fold}_{chosen}_s{seed}.pt"
            net_tf = build_transformer(
                cfg, chosen, torch.load(tf_ckpt, map_location="cpu", weights_only=True)
            )
            net_cv = build_conv(
                cfg, chosen, torch.load(cv_ckpt, map_location="cpu", weights_only=True)
            )
            # paired masks via window_errors with identical seed stream
            mask_seed = seed + 17_001
            err_tf, triv = window_errors(
                net_tf, x_es, y_es_use, chosen, ratio, span, patch_frames, mask_seed,
            )
            err_cv, triv2 = window_errors(
                net_cv, x_es, y_es_use, chosen, ratio, span, patch_frames, mask_seed,
            )
            # triv should match; use average if tiny numerical drift
            triv_use = np.nanmean(np.vstack([triv, triv2]), axis=0)
            sk_tf = trivial.skill(float(np.nanmean(err_tf)), float(np.nanmean(triv_use)))
            sk_cv = trivial.skill(float(np.nanmean(err_cv)), float(np.nanmean(triv_use)))
            # also use training-history skills for reporting consistency
            tf_hist_skill = float(
                runs[(runs.fold == fold) & (runs.objective == chosen) & (runs.seed == seed)]
                .skill_heldout_t1.iloc[0]
            )
            cv_hist_skill = float(
                conv_runs[
                    (conv_runs.fold == fold) & (conv_runs.objective == chosen)
                    & (conv_runs.seed == seed)
                ].skill_heldout_t1.iloc[0]
            )
            boot = paired_bootstrap_skill_diff(
                err_tf, err_cv, triv_use, BOOTSTRAP_N, BOOTSTRAP_SEED + seed + (0 if fold == "A" else 100),
            )
            compare_rows.append({
                "fold": fold, "seed": seed, "objective": chosen,
                "skill_transformer_history": tf_hist_skill,
                "skill_conv_history": cv_hist_skill,
                "skill_diff_history": tf_hist_skill - cv_hist_skill,
                "skill_transformer_paired": sk_tf,
                "skill_conv_paired": sk_cv,
                "skill_diff_paired": sk_tf - sk_cv,
                "n_params_transformer": int(
                    runs[(runs.fold == fold) & (runs.objective == chosen) & (runs.seed == seed)]
                    .n_params.iloc[0]
                ),
                "n_params_conv": int(
                    conv_runs[
                        (conv_runs.fold == fold) & (conv_runs.objective == chosen)
                        & (conv_runs.seed == seed)
                    ].n_params.iloc[0]
                ),
                "seconds_transformer": float(
                    runs[(runs.fold == fold) & (runs.objective == chosen) & (runs.seed == seed)]
                    .seconds.iloc[0]
                ),
                "seconds_conv": float(
                    conv_runs[
                        (conv_runs.fold == fold) & (conv_runs.objective == chosen)
                        & (conv_runs.seed == seed)
                    ].seconds.iloc[0]
                ),
                **{f"boot_{k}": v for k, v in boot.items()},
            })
            boot_rows.append({"fold": fold, "seed": seed, **boot})
            print(
                f"  {fold} s{seed}: TF {tf_hist_skill:.4f}  Conv {cv_hist_skill:.4f}  "
                f"Δ={tf_hist_skill - cv_hist_skill:+.4f}  "
                f"bootΔ={boot['mean_diff']:+.4f} "
                f"[{boot['ci95_lo']:+.4f},{boot['ci95_hi']:+.4f}]"
            )

    compare = pd.DataFrame(compare_rows)
    compare.to_csv(out_dir / "transformer_vs_conv.csv", index=False)

    # identity comparison on selected objective
    id_tf = controls[
        (controls.control == "identity_probe") & (controls.objective == chosen)
    ]["value"].mean()
    id_cv = conv_controls[
        (conv_controls.control == "identity_probe") & (conv_controls.objective == chosen)
    ]["value"].mean()

    # ------------------------------------------------------------------
    # T1/T2/T3 reliability (AFTER objective selection frozen)
    # ------------------------------------------------------------------
    print("\n##### T1/T2/T3 reliability (selected objective only) #####")
    reli_rows = []
    w_all = data_windows.load_window_index(ROOT)

    for fold in cfg["folds"]:
        traj = trajectory_rep(cfg, fold)
        # held-out T1 = early_stop for this fold
        es = w_all[(w_all.fold == fold) & (w_all.role == "early_stop") & w_all.usable]
        x_es, es_i = data_windows.materialise_windows(es, ROOT, "masked_6d")
        y_es, _ = data_windows.materialise_windows(es_i, ROOT, "masked_angular_velocity")
        # eval windows for trajectory repetition at each timepoint
        ev = w_all[(w_all.role == "evaluation") & w_all.usable & (w_all.repetition == traj)]
        x_ev, ev_i = data_windows.materialise_windows(ev, ROOT, "masked_6d")
        y_ev, _ = data_windows.materialise_windows(ev_i, ROOT, "masked_angular_velocity")

        for seed in seeds:
            net = build_transformer(
                cfg, chosen,
                torch.load(ckpt_dir / f"{fold}_{chosen}_s{seed}.pt",
                           map_location="cpu", weights_only=True),
            )
            for pid in cfg["participants"]:
                # T1 heldout
                m1 = (es_i.participant.astype(str) == str(pid)).to_numpy()
                sc1 = train_masked.score_arrays(
                    net, x_es[m1],
                    (y_es if chosen != "masked_6d" else x_es)[m1],
                    chosen, ratio, span, patch_frames, seed + 700 + int(pid),
                    trivial_which="both",
                )
                row = {
                    "fold": fold, "seed": seed, "participant": pid,
                    "objective": chosen, "trajectory_repetition": traj,
                    "skill_T1_heldout": sc1["skill"],
                    "n_T1_heldout": sc1["n"],
                }
                for tp in (2, 3):
                    m = (
                        (ev_i.participant.astype(str) == str(pid))
                        & (ev_i.timepoint == tp)
                    ).to_numpy()
                    sc = train_masked.score_arrays(
                        net, x_ev[m],
                        (y_ev if chosen != "masked_6d" else x_ev)[m],
                        chosen, ratio, span, patch_frames,
                        seed + 800 + int(pid) + tp,
                        trivial_which="both",
                    )
                    row[f"skill_T{tp}"] = sc["skill"]
                    row[f"n_T{tp}"] = sc["n"]
                    row[f"skill_T{tp}_minus_T1"] = (
                        sc["skill"] - sc1["skill"]
                        if np.isfinite(sc["skill"]) and np.isfinite(sc1["skill"])
                        else float("nan")
                    )
                    # gate label
                    if not np.isfinite(sc["skill"]) or sc["skill"] <= 0:
                        gate = "fail_nonpositive"
                    elif sc["skill"] < sc1["skill"]:
                        gate = "positive_degraded"
                    else:
                        gate = "positive_stable"
                    row[f"gate_T{tp}"] = gate
                # T1 gate
                row["gate_T1_heldout"] = (
                    "fail_nonpositive"
                    if (not np.isfinite(sc1["skill"]) or sc1["skill"] <= 0)
                    else "positive"
                )
                reli_rows.append(row)
                print(
                    f"  {fold} s{seed} {pid}: T1={sc1['skill']:.4f}  "
                    f"T2={row['skill_T2']:.4f}  T3={row['skill_T3']:.4f}"
                )

    reli = pd.DataFrame(reli_rows)
    reli.to_csv(out_dir / "reliability_t1_t2_t3.csv", index=False)

    # ------------------------------------------------------------------
    # Figures
    # ------------------------------------------------------------------
    print("\n##### figures #####")
    # skill by objective/fold
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for obj, g in runs.groupby("objective"):
        for fold, gf in g.groupby("fold"):
            ax.scatter(
                [f"{obj}\nfold {fold}"] * len(gf), gf.skill_heldout_t1, alpha=0.85,
            )
    ax.axhline(0, color="grey", ls=":")
    ax.set_ylabel("held-out T1 skill")
    ax.set_title(f"Transformer skill by objective/fold (mask={ratio:.0%}, 3 seeds)")
    fig.tight_layout()
    fig.savefig(fig_dir / "skill_by_objective_fold.png", dpi=150)
    plt.close(fig)

    # TF vs Conv
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for fold, g in compare.groupby("fold"):
        ax.scatter(
            g.skill_conv_history, g.skill_transformer_history,
            label=f"fold {fold}", s=60,
        )
    lims = [
        min(compare.skill_conv_history.min(), compare.skill_transformer_history.min()) - 0.01,
        max(compare.skill_conv_history.max(), compare.skill_transformer_history.max()) + 0.01,
    ]
    ax.plot(lims, lims, "k--", lw=1, label="equality")
    ax.set_xlabel("Conv held-out T1 skill")
    ax.set_ylabel("Transformer held-out T1 skill")
    ax.set_title(f"TF vs Conv ({chosen})")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "transformer_vs_conv_skill.png", dpi=150)
    plt.close(fig)

    # paired diffs
    fig, ax = plt.subplots(figsize=(6, 3.8))
    xpos = np.arange(len(compare))
    ax.bar(xpos, compare.skill_diff_history, color="C0", alpha=0.85)
    ax.axhline(0, color="grey", ls=":")
    ax.set_xticks(xpos)
    ax.set_xticklabels([f"{r.fold}-s{r.seed}" for r in compare.itertuples()], rotation=45)
    ax.set_ylabel("skill(TF) − skill(Conv)")
    ax.set_title("Paired held-out T1 skill differences")
    fig.tight_layout()
    fig.savefig(fig_dir / "paired_skill_differences.png", dpi=150)
    plt.close(fig)

    # seed/fold stability
    fig, ax = plt.subplots(figsize=(6, 3.8))
    for fold, g in runs[runs.objective == chosen].groupby("fold"):
        ax.plot(g.seed, g.skill_heldout_t1, "o-", label=f"fold {fold}")
    ax.axhline(0, color="grey", ls=":")
    ax.set_xlabel("seed"); ax.set_ylabel("held-out T1 skill")
    ax.set_title(f"Seed/fold stability ({chosen})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "seed_fold_stability.png", dpi=150)
    plt.close(fig)

    # identity probe comparison
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    id_tf_all = controls[
        (controls.control == "identity_probe") & (controls.objective == chosen)
    ]
    id_cv_all = conv_controls[
        (conv_controls.control == "identity_probe") & (conv_controls.objective == chosen)
    ]
    ax.boxplot(
        [id_cv_all["value"], id_tf_all["value"]],
        tick_labels=["Conv", "Transformer"],
    )
    ax.axhline(0.25, color="grey", ls=":", label="chance")
    ax.set_ylabel("identity-probe accuracy")
    ax.set_title(f"Participant identity probe ({chosen})")
    fig.tight_layout()
    fig.savefig(fig_dir / "identity_probe_comparison.png", dpi=150)
    plt.close(fig)

    # shuffle controls
    fig, ax = plt.subplots(figsize=(7, 3.8))
    sh = controls[
        controls.control.isin(
            ["shuffle_time_skill_best_trivial", "shuffle_link_skill_best_trivial"]
        )
        & (controls.objective == chosen)
    ]
    base = controls[
        (controls.control == "heldout_t1_skill_rescored") & (controls.objective == chosen)
    ]
    data_box = [
        base["value"],
        sh[sh.control == "shuffle_time_skill_best_trivial"]["value"],
        sh[sh.control == "shuffle_link_skill_best_trivial"]["value"],
    ]
    ax.boxplot(data_box, tick_labels=["intact", "shuffle-time", "shuffle-link"])
    ax.axhline(0, color="grey", ls=":")
    ax.set_ylabel("held-out T1 skill (best trivial)")
    ax.set_title(f"Structure controls ({chosen})")
    fig.tight_layout()
    fig.savefig(fig_dir / "shuffle_controls.png", dpi=150)
    plt.close(fig)

    # link / region errors
    le = pd.DataFrame(link_err_rows)
    le_sel = le[le.objective == chosen]
    by_link = le_sel.groupby("link_id").masked_mse.mean().reindex(link_ids)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(by_link)), by_link.values, color="C0")
    ax.set_xticks(range(len(by_link)))
    ax.set_xticklabels(by_link.index, rotation=90, fontsize=7)
    ax.set_ylabel("masked MSE")
    ax.set_title(f"Per-link reconstruction error, held-out T1 ({chosen})")
    fig.tight_layout()
    fig.savefig(fig_dir / "error_by_link.png", dpi=150)
    plt.close(fig)

    by_reg = le_sel.groupby("region").masked_mse.mean().sort_values()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.barh(by_reg.index, by_reg.values, color="C1")
    ax.set_xlabel("masked MSE")
    ax.set_title(f"Per-region reconstruction error ({chosen})")
    fig.tight_layout()
    fig.savefig(fig_dir / "error_by_region.png", dpi=150)
    plt.close(fig)

    # reliability
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, tp in zip(axes, (2, 3)):
        for fold, g in reli.groupby("fold"):
            ax.scatter(g.skill_T1_heldout, g[f"skill_T{tp}"], label=f"fold {fold}", alpha=0.8)
        lim = [
            min(reli.skill_T1_heldout.min(), reli[f"skill_T{tp}"].min()) - 0.02,
            max(reli.skill_T1_heldout.max(), reli[f"skill_T{tp}"].max()) + 0.02,
        ]
        ax.plot(lim, lim, "k--", lw=1)
        ax.axhline(0, color="grey", ls=":", lw=0.8)
        ax.axvline(0, color="grey", ls=":", lw=0.8)
        ax.set_xlabel("skill held-out T1")
        ax.set_ylabel(f"skill T{tp}")
        ax.set_title(f"T{tp} vs held-out T1")
        ax.legend(fontsize=7)
    fig.suptitle(f"Paired reliability ({chosen})")
    fig.tight_layout()
    fig.savefig(fig_dir / "reliability_t1_t2_t3.png", dpi=150)
    plt.close(fig)

    # runtime / params
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    axes[0].bar(["Conv", "Transformer"], [
        compare.n_params_conv.iloc[0], compare.n_params_transformer.iloc[0],
    ])
    axes[0].set_ylabel("parameters")
    axes[0].set_title("Parameter count")
    tf_secs = runs[(runs.objective == chosen) & (runs.seconds > 0)].seconds
    cv_secs = conv_runs[(conv_runs.objective == chosen) & (conv_runs.seconds > 0)].seconds
    axes[1].bar(
        ["Conv", "Transformer"],
        [
            float(cv_secs.mean()) if len(cv_secs) else 0.0,
            float(tf_secs.mean()) if len(tf_secs) else 0.0,
        ],
    )
    axes[1].set_ylabel("mean wall time / run (s)")
    axes[1].set_title("Runtime (non-resumed)")
    fig.tight_layout()
    fig.savefig(fig_dir / "runtime_params.png", dpi=150)
    plt.close(fig)

    # exploratory UMAP (not for decision)
    try:
        from sklearn.decomposition import PCA
        # use selected objective, fold A, seed 0 embeddings
        sub = emb[(emb.objective == chosen) & (emb.fold == "A") & (emb.seed == 0)]
        ecols = [c for c in sub.columns if c.startswith("e") and not c.startswith("ex11")]
        X = sub[ecols].to_numpy()
        if len(X) >= 5:
            pcs = PCA(n_components=2, random_state=0).fit_transform(X)
            fig, ax = plt.subplots(figsize=(5.5, 4.5))
            for tp, g in zip(sub.timepoint, pcs):
                pass
            for tp in sorted(sub.timepoint.unique()):
                m = sub.timepoint == tp
                ax.scatter(pcs[m, 0], pcs[m, 1], label=f"T{tp}", s=50)
            ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
            ax.set_title("Exploratory PCA of recording embeddings\n(NOT used for selection)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(fig_dir / "exploratory_embedding_pca.png", dpi=140)
            plt.close(fig)
    except Exception as exc:
        print(f"  exploratory PCA skipped: {exc}")

    # ------------------------------------------------------------------
    # Architecture recommendation (from held-out T1 + controls; reliability separate)
    # ------------------------------------------------------------------
    tf_mean = float(runs[runs.objective == chosen].skill_heldout_t1.mean())
    cv_mean = float(conv_runs[conv_runs.objective == chosen].skill_heldout_t1.mean())
    diffs = compare.skill_diff_history.to_numpy()
    fold_agree = all(
        compare[compare.fold == f].skill_diff_history.mean() > 0 for f in compare.fold.unique()
    ) if (diffs > 0).mean() > 0.5 else all(
        compare[compare.fold == f].skill_diff_history.mean() < 0 for f in compare.fold.unique()
    )
    boot_ci_excludes_0 = all(
        (r.boot_ci95_lo > 0) or (r.boot_ci95_hi < 0) for r in compare.itertuples()
    )
    identity_delta = float(id_tf - id_cv)

    # advantage criteria from the brief
    consistently_higher = bool((diffs > 0).mean() >= 5 / 6 and fold_agree and tf_mean > cv_mean)
    not_one_run = bool(np.std(diffs) < abs(np.mean(diffs)) + 1e-9) if abs(np.mean(diffs)) > 1e-6 else False
    # softer: no single run accounts for all positive mean
    identity_ok = identity_delta <= 0.05  # not materially higher

    if consistently_higher and identity_ok and tf_mean > 0:
        arch_choice = "transformer"
        arch_reason = (
            "Transformer held-out T1 skill consistently higher than conv with "
            "non-material identity increase"
        )
    elif abs(tf_mean - cv_mean) < 0.01 or not consistently_higher:
        arch_choice = "conv"
        arch_reason = (
            "Transformer does not provide a clear, reliable advantage over the "
            "matched convolutional baseline; prefer the simpler model"
        )
    else:
        arch_choice = "both_sensitivity"
        arch_reason = "Mixed evidence; retain both as sensitivity analyses"

    # reliability failures
    fail_cells = reli[
        (reli.gate_T1_heldout == "fail_nonpositive")
        | (reli.gate_T2 == "fail_nonpositive")
        | (reli.gate_T3 == "fail_nonpositive")
    ][["participant", "fold", "seed", "gate_T1_heldout", "gate_T2", "gate_T3"]]

    summary = {
        **provenance.run_stamp("S6_transformer", {
            "torch": torch.__version__,
            "device": "cpu",
            "mask_ratio": ratio,
            "n_runs": len(runs),
            "selected_objective": chosen,
            "selection_reason": reason,
            "architecture_recommendation": arch_choice,
            "architecture_reason": arch_reason,
            "skill_transformer_mean": tf_mean,
            "skill_conv_mean": cv_mean,
            "mean_skill_diff": float(np.mean(diffs)),
            "identity_probe_transformer": float(id_tf),
            "identity_probe_conv": float(id_cv),
            "identity_delta_tf_minus_conv": identity_delta,
            "n_params_transformer": int(compare.n_params_transformer.iloc[0]),
            "n_params_conv": int(compare.n_params_conv.iloc[0]),
            "elapsed_s": round(time.time() - t_global, 1),
            "reliability_fail_cells": fail_cells.to_dict(orient="records"),
            "bootstrap_n": BOOTSTRAP_N,
        }),
    }
    # checksum key artifacts
    for name in (
        "run_summary.csv", "controls.csv", "transformer_vs_conv.csv",
        "reliability_t1_t2_t3.csv", "OBJECTIVE_SELECTION.json",
        "recording_embeddings.csv",
    ):
        p = out_dir / name
        if p.exists():
            summary.setdefault("artifact_sha256", {})[name] = provenance.sha256_file(p)

    provenance.write_json(out_dir / "s6_transformer_provenance.json", summary)
    provenance.write_json(out_dir / "ARCHITECTURE_RECOMMENDATION.json", {
        "choice": arch_choice,
        "reason": arch_reason,
        "selected_objective": chosen,
        "skill_transformer_mean": tf_mean,
        "skill_conv_mean": cv_mean,
        "mean_diff": float(np.mean(diffs)),
        "identity_delta": identity_delta,
        "consistently_higher": consistently_higher,
        "identity_ok": identity_ok,
    })

    # decision log
    log_path = ROOT / "reports/DECISION_LOG.md"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(
            f"\n## S6 — {summary['utc']}\n"
            f"- Selected objective: `{chosen}` ({reason})\n"
            f"- Architecture recommendation: `{arch_choice}` ({arch_reason})\n"
            f"- TF mean skill: {tf_mean:.4f}; Conv mean skill: {cv_mean:.4f}; "
            f"Δ={float(np.mean(diffs)):+.4f}\n"
            f"- Identity probe TF={id_tf:.3f}, Conv={id_cv:.3f}\n"
            f"- Stopped before S7–S8.\n"
        )

    print(f"\narchitecture recommendation: {arch_choice}")
    print(f"S6 transformer OK  ({time.time() - t_global:.0f}s total)")
    print(f"artifacts → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
