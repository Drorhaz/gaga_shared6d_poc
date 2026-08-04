#!/usr/bin/env python3
"""S4 - Leakage-aware windowing and the window inventory.

Windows are 2 s (240 frames at 120 Hz) and never cross an exercise boundary.
The unit of assignment is the contiguous exercise block, never the window:
windows drawn from one block are correlated, so splitting at window level
would leak between training and early stopping.

Roles, all fixed before any model exists:

* training     - ex01-15 of the four T1 recordings of the fold's training
                 repetition, 50 percent overlap.
* early_stop   - a held-out 20 percent of those training BLOCKS, chosen per
                 participant with a fixed seed. Never used for gradient steps.
* evaluation   - ex09-13 of all 24 recordings, non-overlapping, so that
                 recording-level embeddings are averages of independent windows.

Every window records whether the fold's model saw its recording in training,
so the in-sample T1 recording can never be mistaken for a clean measurement.

Usage:
    python scripts/s4_window.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AXES = ("rx", "ry", "rz")
EARLY_STOP_SEED = 20260803


def enumerate_windows(block: pd.Series, win: int, stride: int) -> list[tuple[int, int]]:
    out = []
    start = int(block.start_frame)
    while start + win <= int(block.end_frame):
        out.append((start, start + win))
        start += stride
    return out


def finite_coverage(rot_dir: Path, recording_id: str, link_ids: list[str],
                    spans: list[tuple[int, int]]) -> np.ndarray:
    """Fraction of frames in each window with all 18 links finite."""
    df = pd.read_parquet(rot_dir / f"{recording_id}.parquet")
    cols = [f"{lid}_{a}" for lid in link_ids for a in AXES]
    ok = np.all(np.isfinite(df[cols].to_numpy()), axis=1)
    n = len(ok)
    return np.array([ok[a:min(b, n)].mean() if min(b, n) > a else 0.0 for a, b in spans])


def assign_early_stop_blocks(blocks: pd.DataFrame, fraction: float, seed: int) -> set[str]:
    """Hold out whole blocks, balanced across participants."""
    rng = np.random.default_rng(seed)
    held: set[str] = set()
    for pid, g in blocks.groupby("participant"):
        ids = sorted(g.block_id.unique())
        k = max(1, int(round(fraction * len(ids))))
        held.update(rng.choice(ids, size=k, replace=False).tolist())
    return held


def build_windows(cfg: dict, seg: pd.DataFrame, reg: pd.DataFrame,
                  link_ids: list[str], rot_dir: Path) -> tuple[pd.DataFrame, dict]:
    fps = cfg["capture"]["frame_rate_hz"]
    win = int(round(cfg["windowing"]["window_seconds"] * fps))
    train_stride = int(round(win * (1 - cfg["windowing"]["train_overlap"])))
    eval_stride = int(round(win * (1 - cfg["windowing"]["eval_overlap"])))
    train_ex = set(cfg["exercises"]["training"])
    eval_ex = set(cfg["exercises"]["evaluation"])

    seg = seg.copy()
    seg["recording_id"] = (
        seg.participant.astype(str) + "_T" + seg.timepoint.astype(str)
        + "_P1_R" + seg.repetition.astype(str)
    )

    rows: list[dict] = []
    too_short: list[dict] = []

    # --- evaluation windows: every recording, ex09-13, non-overlapping ---
    ev_blocks = seg[seg.exercise_id.isin(eval_ex)]
    for _, b in ev_blocks.iterrows():
        spans = enumerate_windows(b, win, eval_stride)
        if not spans:
            too_short.append({"block_id": b.block_id, "role": "evaluation",
                              "n_frames": int(b.n_frames)})
        for k, (s, e) in enumerate(spans):
            rows.append(
                {"role": "evaluation", "recording_id": b.recording_id,
                 "participant": b.participant, "timepoint": b.timepoint,
                 "repetition": b.repetition, "exercise_id": b.exercise_id,
                 "block_id": b.block_id, "window_in_block": k,
                 "start_frame": s, "end_frame": e}
            )

    # --- training windows: T1 of each fold's training repetition, ex01-15 ---
    fold_info = {}
    for fold, spec in cfg["folds"].items():
        rep = spec["train_repetition"]
        pool = seg[(seg.timepoint == 1) & (seg.repetition == rep)
                   & (seg.exercise_id.isin(train_ex))]
        held = assign_early_stop_blocks(pool, cfg["model"]["early_stop_block_fraction"],
                                        EARLY_STOP_SEED + ord(fold))
        for _, b in pool.iterrows():
            role = "early_stop" if b.block_id in held else "training"
            spans = enumerate_windows(b, win, train_stride)
            if not spans:
                too_short.append({"block_id": b.block_id, "role": role,
                                  "n_frames": int(b.n_frames)})
            for k, (s, e) in enumerate(spans):
                rows.append(
                    {"role": role, "fold": fold, "recording_id": b.recording_id,
                     "participant": b.participant, "timepoint": b.timepoint,
                     "repetition": b.repetition, "exercise_id": b.exercise_id,
                     "block_id": b.block_id, "window_in_block": k,
                     "start_frame": s, "end_frame": e}
                )
        fold_info[fold] = {
            "train_repetition": rep,
            "trajectory_repetition": spec["trajectory_repetition"],
            "training_recordings": sorted(pool.recording_id.unique()),
            "n_blocks": int(pool.block_id.nunique()),
            "n_early_stop_blocks": len(held),
            "early_stop_blocks": sorted(held),
        }

    w = pd.DataFrame(rows)
    w["fold"] = w.get("fold", pd.Series(index=w.index, dtype=object))
    w["duration_s"] = (w.end_frame - w.start_frame) / fps

    # Mark, per fold, whether this window's recording was in that fold's
    # training pool. Evaluation windows from an in-sample recording are not a
    # clean measurement and must be excluded from the trajectory.
    for fold, info in fold_info.items():
        w[f"seen_in_training_{fold}"] = w.recording_id.isin(info["training_recordings"])

    # --- finite-data coverage per window ---
    cov = np.zeros(len(w))
    for rid, g in w.groupby("recording_id"):
        spans = list(zip(g.start_frame, g.end_frame))
        cov[g.index.to_numpy()] = finite_coverage(rot_dir, rid, link_ids, spans)
    w["frac_finite"] = cov
    w["usable"] = w.frac_finite >= 1.0
    w = w.reset_index(drop=True)
    w.insert(0, "window_id", [f"w{i:06d}" for i in range(len(w))])

    meta = {
        "window_frames": win, "window_seconds": cfg["windowing"]["window_seconds"],
        "train_stride": train_stride, "eval_stride": eval_stride,
        "early_stop_seed": EARLY_STOP_SEED,
        "folds": fold_info,
        "blocks_too_short_for_a_window": too_short,
    }
    return w, meta


def figure_inventory(w: pd.DataFrame, out: Path) -> None:
    ev = w[w.role == "evaluation"]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))

    piv = ev.pivot_table(index="participant", columns=["timepoint", "repetition"],
                         values="window_id", aggfunc="count")
    im = ax[0].imshow(piv.to_numpy(), cmap="Blues", vmin=0)
    ax[0].set_xticks(range(piv.shape[1]))
    ax[0].set_xticklabels([f"T{t}R{r}" for t, r in piv.columns], fontsize=8)
    ax[0].set_yticks(range(piv.shape[0]))
    ax[0].set_yticklabels(piv.index)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            ax[0].text(j, i, int(piv.to_numpy()[i, j]), ha="center", va="center", fontsize=8)
    ax[0].set_title("Evaluation windows per recording\n(ex09-13, non-overlapping)")
    fig.colorbar(im, ax=ax[0], fraction=0.046)

    counts = ev.groupby(["participant", "exercise_id"]).size().unstack(fill_value=0)
    bottom = np.zeros(len(counts))
    for ex in counts.columns:
        ax[1].bar(counts.index, counts[ex], bottom=bottom, label=f"ex{ex:02d}")
        bottom += counts[ex].to_numpy()
    ax[1].set_ylabel("evaluation windows (all 6 recordings)")
    ax[1].set_title("Evaluation windows by exercise")
    ax[1].legend(fontsize=7, ncol=2)

    tr = w[w.role.isin(["training", "early_stop"])]
    g = tr.groupby(["fold", "role"]).size().unstack(fill_value=0)
    x = np.arange(len(g))
    ax[2].bar(x - 0.2, g.get("training", 0), width=0.4, label="training")
    ax[2].bar(x + 0.2, g.get("early_stop", 0), width=0.4, label="early stop (held-out blocks)")
    ax[2].set_xticks(x)
    ax[2].set_xticklabels([f"fold {i}" for i in g.index])
    ax[2].set_ylabel("windows")
    ax[2].set_title("Training pool by fold\n(T1 only, ex01-15, 50% overlap)")
    ax[2].legend(fontsize=8)

    fig.suptitle("S4.1  Window inventory", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_timelines(w: pd.DataFrame, seg: pd.DataFrame, cfg: dict, out: Path) -> None:
    """Window placement on the exercise timeline, one row per recording."""
    fps = cfg["capture"]["frame_rate_hz"]
    eval_ex = set(cfg["exercises"]["evaluation"])
    recs = sorted(w.recording_id.unique())
    seg = seg.copy()
    seg["recording_id"] = (
        seg.participant.astype(str) + "_T" + seg.timepoint.astype(str)
        + "_P1_R" + seg.repetition.astype(str)
    )

    fig, ax = plt.subplots(figsize=(13, 0.42 * len(recs) + 1.8))
    for y, rid in enumerate(recs):
        for _, b in seg[seg.recording_id == rid].iterrows():
            colour = "#c8dcf0" if b.exercise_id in eval_ex else "#eeeeee"
            ax.barh(y, b.n_frames / fps, left=b.start_frame / fps, height=0.72,
                    color=colour, edgecolor="#bbbbbb", linewidth=0.3, zorder=1)
        sub = w[(w.recording_id == rid) & (w.role == "evaluation")]
        for _, r in sub.iterrows():
            ax.barh(y, r.duration_s, left=r.start_frame / fps, height=0.44,
                    color="#1f4e79" if r.usable else "crimson", zorder=3)
        tr = w[(w.recording_id == rid) & (w.role.isin(["training", "early_stop"]))]
        for _, r in tr.iterrows():
            ax.barh(y + 0.28, r.duration_s, left=r.start_frame / fps, height=0.14,
                    color="#7aa64f" if r.role == "training" else "#d99a2b", zorder=2)

    ax.set_yticks(range(len(recs)))
    ax.set_yticklabels(recs, fontsize=7)
    ax.set_xlabel("seconds within recording")
    ax.invert_yaxis()
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="#c8dcf0"),
        plt.Rectangle((0, 0), 1, 1, color="#eeeeee"),
        plt.Rectangle((0, 0), 1, 1, color="#1f4e79"),
        plt.Rectangle((0, 0), 1, 1, color="#7aa64f"),
        plt.Rectangle((0, 0), 1, 1, color="#d99a2b"),
    ]
    ax.legend(handles,
              ["ex09-13 (evaluation scope)", "other exercises", "evaluation window",
               "training window", "early-stop window"],
              fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.set_title("S4.2  Window placement on exercise timelines "
                 "(windows never cross an exercise boundary)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
    link_ids = [l["id"] for l in linkcfg["links"]]

    seg = pd.read_csv(ROOT / "data/immutable/segmentation_normalized.csv")
    reg = pd.read_csv(ROOT / "data/immutable/recording_registry.csv")
    rot_dir = ROOT / "data/immutable/rotvec_18link"

    out_dir = ROOT / "outputs/s4_windows"
    fig_dir = ROOT / "figures/s4_windows"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    w, meta = build_windows(cfg, seg, reg, link_ids, rot_dir)
    w.to_csv(out_dir / "window_index.csv", index=False)

    ev = w[w.role == "evaluation"]
    per_rec = ev.groupby("recording_id").size()

    print(f"{'='*72}\nwindow inventory\n{'='*72}")
    print(f"window length     : {meta['window_frames']} frames "
          f"({meta['window_seconds']} s at {cfg['capture']['frame_rate_hz']:g} Hz)")
    print(f"stride            : training {meta['train_stride']} "
          f"({cfg['windowing']['train_overlap']:.0%} overlap), "
          f"evaluation {meta['eval_stride']} (non-overlapping)")
    print(f"total windows     : {len(w)}")
    for role, g in w.groupby("role"):
        print(f"    {role:12s} {len(g):5d}")

    print(f"\nevaluation windows per recording (ex09-13, independent):")
    print(f"    min {per_rec.min()}, median {int(per_rec.median())}, max {per_rec.max()} "
          f"across {len(per_rec)} recordings")
    tab = ev.pivot_table(index="participant", columns=["timepoint", "repetition"],
                         values="window_id", aggfunc="count")
    print(tab.to_string())

    print("\nper-fold training pools:")
    for fold, info in meta["folds"].items():
        tw = w[(w.fold == fold) & (w.role == "training")]
        es = w[(w.fold == fold) & (w.role == "early_stop")]
        print(f"    fold {fold}: train on T1-R{info['train_repetition']}, "
              f"trajectory on R{info['trajectory_repetition']}")
        print(f"        {len(tw)} training windows over "
              f"{info['n_blocks'] - info['n_early_stop_blocks']} blocks; "
              f"{len(es)} early-stop windows over {info['n_early_stop_blocks']} blocks")
        print(f"        in-sample recordings: {', '.join(info['training_recordings'])}")

    print("\nleakage checks:")
    crosses = 0
    seg2 = seg.copy()
    seg2["recording_id"] = (
        seg2.participant.astype(str) + "_T" + seg2.timepoint.astype(str)
        + "_P1_R" + seg2.repetition.astype(str)
    )
    bounds = seg2.set_index("block_id")[["start_frame", "end_frame"]]
    for r in w.itertuples():
        b = bounds.loc[r.block_id]
        if r.start_frame < b.start_frame or r.end_frame > b.end_frame:
            crosses += 1
    print(f"    windows crossing an exercise boundary : {crosses}")
    overlap_roles = w.groupby("block_id").apply(
        lambda g: set(g[g.role.isin(["training", "early_stop"])].role.unique()), include_groups=False
    )
    mixed = int(sum(1 for s in overlap_roles if len(s) > 1))
    print(f"    blocks split across train and early-stop : {mixed}")
    n_unusable = int((~w.usable).sum())
    print(f"    windows with missing data : {n_unusable} "
          f"({n_unusable/len(w):.2%})")
    if meta["blocks_too_short_for_a_window"]:
        print(f"    blocks too short for one window : "
              f"{len(meta['blocks_too_short_for_a_window'])}")
        for b in meta["blocks_too_short_for_a_window"][:6]:
            print(f"        {b['block_id']} ({b['n_frames']} frames, {b['role']})")

    print("\nrendering figures ...")
    figure_inventory(w, fig_dir / "s4_1_window_inventory.png")
    figure_timelines(w, seg, cfg, fig_dir / "s4_2_window_timelines.png")
    for p in sorted(fig_dir.glob("*.png")):
        print(f"    {p.relative_to(ROOT)}")

    provenance.write_json(
        out_dir / "s4_provenance.json",
        {**provenance.run_stamp("S4_windows"), **meta,
         "n_windows": int(len(w)),
         "n_by_role": {k: int(v) for k, v in w.role.value_counts().items()},
         "eval_windows_per_recording": {"min": int(per_rec.min()),
                                        "median": float(per_rec.median()),
                                        "max": int(per_rec.max())},
         "windows_crossing_boundaries": crosses,
         "blocks_split_across_roles": mixed,
         "windows_with_missing_data": n_unusable},
    )

    blocking = []
    if crosses:
        blocking.append(f"{crosses} windows cross exercise boundaries")
    if mixed:
        blocking.append(f"{mixed} blocks split across training and early stop")
    if per_rec.min() < 10:
        blocking.append(f"only {per_rec.min()} evaluation windows in the sparsest recording")
    print("\nS4 " + ("BLOCKED: " + "; ".join(blocking) if blocking else "OK"))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
