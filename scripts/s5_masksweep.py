#!/usr/bin/env python3
"""S5.3 — Mask-ratio sweep on Fold A, seed 0, held-out T1 blocks only.

Freezes one mask ratio into configs/experiment.yaml (s5.frozen_mask_ratio)
before full baseline runs. Selection uses held-out T1 skill only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, provenance, train_masked  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def load_fold_arrays(fold: str, cfg: dict):
    w = data_windows.load_window_index(ROOT)
    tr = w[(w.fold == fold) & (w.role == "training") & w.usable]
    es = w[(w.fold == fold) & (w.role == "early_stop") & w.usable]
    x_tr, tr_i = data_windows.materialise_windows(tr, ROOT, "masked_6d")
    x_es, es_i = data_windows.materialise_windows(es, ROOT, "masked_6d")
    # velocity targets aligned to the same windows
    y_tr, _ = data_windows.materialise_windows(tr_i, ROOT, "masked_angular_velocity")
    y_es, _ = data_windows.materialise_windows(es_i, ROOT, "masked_angular_velocity")
    return x_tr, x_es, y_tr, y_es, tr_i, es_i


def main() -> int:
    cfg = data_windows.load_config(ROOT)
    s5 = cfg["s5"]
    ratios = cfg["model"]["mask_ratio_sweep"]
    span = tuple(s5["mask_span_patches"])
    out_dir = ROOT / "outputs/s5_masksweep"
    fig_dir = ROOT / "figures/s5_masksweep"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("loading Fold A windows ...")
    x_tr, x_es, y_tr, y_es, _, _ = load_fold_arrays("A", cfg)
    print(f"  train {len(x_tr)}  early_stop {len(x_es)}")

    rows = []
    for objective in cfg["model"]["objectives"]:
        for ratio in ratios:
            print(f"\n== {objective}  mask={ratio:.0%}  fold=A seed=0 ==")
            res = train_masked.train_conv(
                x_tr, x_es,
                y_tr if objective != "masked_6d" else None,
                y_es if objective != "masked_6d" else None,
                objective=objective, mask_ratio=ratio, span_patches=span,
                seed=0, channels=s5["conv_channels"], batch_size=s5["batch_size"],
                max_epochs=s5["max_epochs"], lr=s5["learning_rate"],
                weight_decay=s5["weight_decay"], patience=s5["early_stop_patience"],
                n_links=cfg["model"]["n_links"], patch_frames=cfg["model"]["patch_frames"],
                embedding_dim=cfg["model"]["embedding_dim"],
            )
            best = res.history[res.best_epoch]
            rows.append({
                "objective": objective, "mask_ratio": ratio, "fold": "A", "seed": 0,
                "best_epoch": res.best_epoch, "val_loss": res.best_val_loss,
                "skill": best["skill"], "trivial_best": best["trivial_best"],
                "n_params": res.n_params, "seconds": round(res.seconds, 1),
            })
            print(f"  best epoch {res.best_epoch}  val_loss {res.best_val_loss:.5f}  "
                  f"skill {best['skill']:.4f}  ({res.seconds:.0f}s, {res.n_params} params)")
            pd.DataFrame(res.history).to_csv(
                out_dir / f"history_{objective}_r{int(ratio*100)}.csv", index=False
            )

    sweep = pd.DataFrame(rows)
    sweep.to_csv(out_dir / "mask_ratio_sweep.csv", index=False)

    # Selection uses held-out T1 skill only. Prefer ratios that give positive
    # skill on at least one objective (a negative-skill objective is a failed
    # pretext for that ratio, not a vote). Among those, maximise mean skill of
    # the positive-skill objectives. Ties within 0.02 → lowest ratio.
    pivot = sweep.pivot(index="mask_ratio", columns="objective", values="skill")
    pivot["mean_skill"] = pivot.mean(axis=1)
    pos_objs = [c for c in pivot.columns if c != "mean_skill" and (pivot[c] > 0).any()]
    if pos_objs:
        score = pivot[pos_objs].clip(lower=0).mean(axis=1)
        rule = f"mean skill over positive-skill objectives {pos_objs}"
    else:
        score = pivot["mean_skill"]
        rule = "all objectives ≤ 0; least-bad mean skill"
    pivot["selection_score"] = score
    best = score.max()
    candidates = score.index[score >= best - 0.02].tolist()
    selected = float(min(candidates))
    reason = (
        f"{rule}; best score {best:.4f}; "
        + ("unique" if len(candidates) == 1
           else f"tied within 0.02 among {candidates}, chose lowest (conservative)")
    )

    print(f"\nselected mask_ratio={selected:.0%}  ({reason})")
    print(pivot.round(4).to_string())

    # freeze into experiment.yaml
    yaml_path = ROOT / "configs/experiment.yaml"
    text = yaml_path.read_text()
    if "frozen_mask_ratio:" in text:
        import re
        text = re.sub(
            r"frozen_mask_ratio:\s*\S+",
            f"frozen_mask_ratio: {selected}",
            text,
        )
        yaml_path.write_text(text)
    print(f"froze s5.frozen_mask_ratio={selected} in configs/experiment.yaml")

    # figure
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for obj, g in sweep.groupby("objective"):
        ax.plot(g.mask_ratio * 100, g.skill, "o-", label=obj)
    ax.axvline(selected * 100, color="crimson", ls="--", label=f"selected {selected:.0%}")
    ax.set_xlabel("mask ratio (%)"); ax.set_ylabel("held-out T1 skill")
    ax.set_title("S5 mask-ratio sweep (Fold A, seed 0)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(fig_dir / "mask_ratio_sweep.png", dpi=150)
    plt.close(fig)

    provenance.write_json(out_dir / "s5_masksweep_provenance.json", {
        **provenance.run_stamp("S5_masksweep"),
        "fold": "A", "seed": 0,
        "ratios": ratios, "selected": selected, "selection_reason": reason,
        "results": rows,
        "selection_table": pivot.reset_index().to_dict(orient="records"),
    })
    (out_dir / "SELECTED_MASK_RATIO.txt").write_text(
        f"{selected}\n{reason}\n", encoding="utf-8"
    )
    print("\nS5 mask sweep OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
