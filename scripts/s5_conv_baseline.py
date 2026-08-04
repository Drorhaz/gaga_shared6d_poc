#!/usr/bin/env python3
"""S5.4 — Full convolutional baseline: 2 folds × 3 seeds × 2 objectives.

Also runs required controls (identity probe, shuffle-time/link, overshoot
sensitivity) and writes embeddings. Does NOT train the Transformer.
"""

from __future__ import annotations

import copy
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
    return x, idx


def build_net(cfg, objective, state=None):
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


def score_split(net, x6, y, objective, mask_ratio, span, patch_frames, seed,
                trivial_which: str = "mean_motion"):
    """Return error/skill on a numpy split with a fixed mask generator seed.

    Controls use ``mean_motion`` only (fast). Full interpolation skill is
    already measured during training early-stopping.
    """
    from torch.utils.data import DataLoader, TensorDataset
    if objective == "masked_6d":
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(x6))
    else:
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(y))
    loader = DataLoader(ds, batch_size=32, shuffle=False)
    net.eval()
    total, tm, n = 0.0, 0.0, 0
    g = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for xb, yb in loader:
            b, t, l, _ = xb.shape
            p = t // patch_frames
            mask = models.structured_mask(b, l, p, mask_ratio, span, g)
            target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
            pred = net(xb, mask)
            loss = models.masked_loss(pred, target, mask)
            te = trivial.trivial_errors(target, mask, which=trivial_which)
            total += float(loss) * b
            tm += te["mean_motion"] * b
            n += b
    err = total / max(n, 1)
    tm /= max(n, 1)
    return {
        "error": err, "trivial_mean": tm, "trivial_interp": float("nan"),
        "trivial_best": tm, "skill": trivial.skill(err, tm), "n": n,
    }


def shuffle_control(x6, mode: str, seed: int) -> np.ndarray:
    """Shuffle along time (axis=1) or links (axis=2). Shape (N, T, L, C)."""
    rng = np.random.default_rng(seed)
    out = x6.copy()
    if mode == "time":
        for i in range(len(out)):
            out[i] = out[i][rng.permutation(out.shape[1])]
    elif mode == "link":
        for i in range(len(out)):
            out[i] = out[i][:, rng.permutation(out.shape[2])]
    return out


def overshoot_masks(es_index: pd.DataFrame, x_es: np.ndarray, link_ids: list[str]):
    """Windows / link index for the known 790_T1_P1_R1 RShoulder_to_RUArm case."""
    lid = "RShoulder_to_RUArm"
    li = link_ids.index(lid)
    is_rec = (es_index.recording_id == "790_T1_P1_R1").to_numpy()
    return li, is_rec


def main() -> int:
    cfg = data_windows.load_config(ROOT)
    s5 = cfg["s5"]
    ratio = s5.get("frozen_mask_ratio")
    if ratio is None:
        sel = ROOT / "outputs/s5_masksweep/SELECTED_MASK_RATIO.txt"
        if not sel.exists():
            print("Run scripts/s5_masksweep.py first to freeze a mask ratio.")
            return 1
        ratio = float(sel.read_text().splitlines()[0])
    ratio = float(ratio)
    span = tuple(s5["mask_span_patches"])
    seeds = cfg["model"]["seeds"]
    objectives = cfg["model"]["objectives"]
    link_ids, _ = data_windows.load_link_config(ROOT)
    eval_ex = cfg["exercises"]["evaluation"]

    out_dir = ROOT / "outputs/s5_conv"
    fig_dir = ROOT / "figures/s5_conv"
    ckpt_dir = out_dir / "checkpoints"
    for d in (out_dir, fig_dir, ckpt_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"frozen mask_ratio={ratio:.0%}")
    print("loading evaluation windows once ...")
    x_eval, eval_idx = eval_all_windows()
    print(f"  {len(x_eval)} evaluation windows")

    run_rows, hist_all, emb_rows, control_rows = [], [], [], []
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
                    # resume from checkpoint; recover best epoch from history
                    best_epoch = int(hist.val_loss.idxmin())
                    best = hist.iloc[best_epoch].to_dict()
                    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
                    n_params = models.count_parameters(build_net(cfg, objective, state))
                    run_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "mask_ratio": ratio, "best_epoch": best_epoch,
                        "val_loss": float(best["val_loss"]),
                        "skill_heldout_t1": float(best["skill"]),
                        "trivial_best": float(best["trivial_best"]),
                        "n_params": n_params, "seconds": 0.0, "resumed": True,
                    })
                    print(f"  resumed ckpt  skill={best['skill']:.4f}  epoch {best_epoch}")
                    net = build_net(cfg, objective, state)
                else:
                    res = train_masked.train_conv(
                        x_tr, x_es,
                        y_tr if objective != "masked_6d" else None,
                        y_es if objective != "masked_6d" else None,
                        objective=objective, mask_ratio=ratio, span_patches=span,
                        seed=seed, channels=s5["conv_channels"],
                        batch_size=s5["batch_size"],
                        max_epochs=s5["max_epochs"], lr=s5["learning_rate"],
                        weight_decay=s5["weight_decay"],
                        patience=s5["early_stop_patience"],
                        n_links=cfg["model"]["n_links"],
                        patch_frames=cfg["model"]["patch_frames"],
                        embedding_dim=cfg["model"]["embedding_dim"],
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
                    print(f"  skill(held-out T1)={best['skill']:.4f}  "
                          f"epoch {res.best_epoch}  {res.seconds:.0f}s  "
                          f"params={res.n_params}")
                    net = build_net(cfg, objective, res.best_state)
                    hist = pd.DataFrame(res.history)
                    fig, ax = plt.subplots(figsize=(6, 3.5))
                    ax.plot(hist.epoch, hist.train_loss, label="train")
                    ax.plot(hist.epoch, hist.val_loss, label="held-out T1")
                    ax.axvline(res.best_epoch, color="crimson", ls="--", lw=1)
                    ax.set_xlabel("epoch"); ax.set_ylabel("masked MSE")
                    ax.set_title(tag); ax.legend(fontsize=8)
                    fig.tight_layout()
                    fig.savefig(fig_dir / f"loss_{tag}.png", dpi=120)
                    plt.close(fig)

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

                # shuffle controls: re-score held-out with shuffled inputs (no retrain)
                for mode in ("time", "link"):
                    x_sh = shuffle_control(x_es, mode, seed + (1 if mode == "time" else 2))
                    y_sh = y_es if objective != "masked_6d" else x_sh
                    if objective != "masked_6d" and mode == "time":
                        y_sh = shuffle_control(y_es, mode, seed + 1)
                    elif objective != "masked_6d" and mode == "link":
                        y_sh = shuffle_control(y_es, mode, seed + 2)
                    sc = score_split(net, x_sh, y_sh if objective != "masked_6d" else x_sh,
                                    objective, ratio, span, cfg["model"]["patch_frames"],
                                    seed + 99)
                    control_rows.append({
                        "fold": fold, "objective": objective, "seed": seed,
                        "control": f"shuffle_{mode}_skill", "value": sc["skill"],
                        "chance": 0.0,
                    })

                # overshoot sensitivity on held-out skill
                li, is_rec = overshoot_masks(es_i, x_es, link_ids)
                # exclude link: zero that link in input/target for scoring only
                x_ex = x_es.copy(); x_ex[:, :, li, :] = 0.0
                y_ex = y_es.copy(); y_ex[:, :, li, :] = 0.0
                sc0 = score_split(net, x_es, y_es if objective != "masked_6d" else x_es,
                                  objective, ratio, span, cfg["model"]["patch_frames"], seed + 3)
                sc_link = score_split(net, x_ex, y_ex if objective != "masked_6d" else x_ex,
                                      objective, ratio, span, cfg["model"]["patch_frames"], seed + 3)
                # exclude 790_T1 windows from the early-stop pool
                keep = ~is_rec
                if keep.any() and is_rec.any():
                    sc_rec = score_split(
                        net, x_es[keep],
                        (y_es if objective != "masked_6d" else x_es)[keep],
                        objective, ratio, span, cfg["model"]["patch_frames"], seed + 3,
                    )
                else:
                    sc_rec = sc0
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "overshoot_skill_baseline", "value": sc0["skill"], "chance": np.nan,
                })
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "overshoot_exclude_link_skill", "value": sc_link["skill"],
                    "chance": np.nan,
                })
                control_rows.append({
                    "fold": fold, "objective": objective, "seed": seed,
                    "control": "overshoot_exclude_790T1_windows_skill", "value": sc_rec["skill"],
                    "chance": np.nan,
                })

                # embeddings for evaluation windows (trajectory uses all eval; keep separate)
                z_ev = train_masked.embed_windows(net, x_eval)
                agg = data_windows.aggregate_recording_embeddings(z_ev, eval_idx, eval_ex)
                agg.insert(0, "fold", fold)
                agg.insert(1, "objective", objective)
                agg.insert(2, "seed", seed)
                emb_rows.append(agg)

    runs = pd.DataFrame(run_rows)
    runs.to_csv(out_dir / "run_summary.csv", index=False)
    pd.DataFrame(control_rows).to_csv(out_dir / "controls.csv", index=False)
    emb = pd.concat(emb_rows, ignore_index=True)
    emb.to_csv(out_dir / "recording_embeddings.csv", index=False)

    # skill summary figure
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for obj, g in runs.groupby("objective"):
        for fold, gf in g.groupby("fold"):
            ax.scatter([f"{obj}\nfold {fold}"] * len(gf), gf.skill_heldout_t1,
                       label=None, alpha=0.8)
    ax.axhline(0, color="grey", ls=":")
    ax.set_ylabel("held-out T1 skill")
    ax.set_title(f"Conv baseline skill by objective/fold (mask={ratio:.0%}, 3 seeds)")
    fig.tight_layout()
    fig.savefig(fig_dir / "skill_by_objective_fold.png", dpi=150)
    plt.close(fig)

    # objective selection on held-out T1 skill only (mean across folds/seeds)
    sel = runs.groupby("objective").skill_heldout_t1.agg(["mean", "std", "min", "max"])
    sel.to_csv(out_dir / "objective_selection_heldout_t1.csv")
    means = sel["mean"]
    if abs(means.iloc[0] - means.iloc[1]) < 0.02:
        # tie-break: lower identity probe accuracy
        idp = pd.DataFrame(control_rows)
        idp = idp[idp.control == "identity_probe"].groupby("objective")["value"].mean()
        chosen = idp.idxmin()
        reason = f"skill within 0.02; tie-break lower identity probe ({idp.to_dict()})"
    else:
        chosen = means.idxmax()
        reason = "higher mean held-out T1 skill"
    (out_dir / "SELECTED_OBJECTIVE.txt").write_text(f"{chosen}\n{reason}\n", encoding="utf-8")
    print(f"\nselected objective: {chosen}  ({reason})")
    print(sel.round(4).to_string())

    # param / runtime table
    rt = runs.groupby("objective").agg(seconds=("seconds", "mean"), n_params=("n_params", "first"))
    rt.to_csv(out_dir / "runtime_params.csv")

    provenance.write_json(out_dir / "s5_conv_provenance.json", {
        **provenance.run_stamp("S5_conv"),
        "mask_ratio": ratio,
        "n_runs": len(runs),
        "selected_objective": chosen,
        "selection_reason": reason,
        "n_params": int(runs.n_params.iloc[0]) if len(runs) else None,
        "elapsed_s": round(time.time() - t_global, 1),
        "run_summary": run_rows,
    })
    print(f"\nS5 conv baseline OK  ({time.time()-t_global:.0f}s total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
