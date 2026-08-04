#!/usr/bin/env python3
"""S5.2 — Explicit movement features (descriptive; amplitude-controlled)."""

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
from gaga_shared6d import data_windows, explicit_features, provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cfg = data_windows.load_config(ROOT)
    linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
    link_ids = [l["id"] for l in linkcfg["links"]]
    regions = {l["id"]: l["region"] for l in linkcfg["links"]}
    mirrors = linkcfg["mirror_pairs"]
    fps = cfg["capture"]["frame_rate_hz"]
    q = cfg["s5"]["active_link_energy_quantile"]

    out_dir = ROOT / "outputs/s5_explicit"
    fig_dir = ROOT / "figures/s5_explicit"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    w = data_windows.load_window_index(ROOT)
    # All evaluation windows + a sample of training for coverage
    idx = w[w.usable & w.role.isin(["evaluation", "training"])].copy()
    # Training rows are duplicated across folds; keep unique window_ids
    idx = idx.drop_duplicates("window_id").reset_index(drop=True)

    rows = []
    print(f"computing explicit features for {len(idx)} windows ...")
    for i, row in enumerate(idx.itertuples(), 1):
        rv = data_windows.load_recording_arrays(row.recording_id, ROOT)["rotvec"]
        sl = rv[int(row.start_frame):int(row.end_frame)]
        if not np.all(np.isfinite(sl)):
            continue
        feats = explicit_features.features_for_window(
            sl, link_ids, regions, mirrors, fps, active_quantile=q,
        )
        rows.append({
            "window_id": row.window_id, "recording_id": row.recording_id,
            "participant": row.participant, "timepoint": row.timepoint,
            "repetition": row.repetition, "exercise_id": row.exercise_id,
            "role": row.role, **feats,
        })
        if i % 200 == 0:
            print(f"  {i}/{len(idx)}")

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "window_features.csv", index=False)

    # recording-level (eval exercises, equal weight)
    eval_ex = cfg["exercises"]["evaluation"]
    feat_cols = [c for c in df.columns if c not in
                 {"window_id", "recording_id", "participant", "timepoint",
                  "repetition", "exercise_id", "role"}]
    rec_rows = []
    sub = df[df.exercise_id.isin(eval_ex)]
    for keys, g in sub.groupby(["participant", "timepoint", "repetition", "recording_id"]):
        per_ex = g.groupby("exercise_id")[feat_cols].mean()
        vec = per_ex.mean()
        rec_rows.append({
            "participant": keys[0], "timepoint": keys[1], "repetition": keys[2],
            "recording_id": keys[3], **vec.to_dict(),
        })
    rec = pd.DataFrame(rec_rows)
    rec.to_csv(out_dir / "recording_features.csv", index=False)

    # amplitude control: residualise coordination features against log energy within participant
    coord = ["participation_entropy_bits", "effective_dimensionality", "lr_symmetry",
             "regional_coupling", "trunk_arm_lagged_coupling", "active_link_count",
             "active_region_count"]
    amp_rows = []
    for pid, g in rec.groupby("participant"):
        g = g.copy()
        x = g["total_energy_log"].to_numpy()
        for c in coord:
            y = g[c].to_numpy()
            ok = np.isfinite(x) & np.isfinite(y)
            resid = np.full_like(y, np.nan, dtype=float)
            if ok.sum() >= 3 and np.std(x[ok]) > 1e-12:
                coef = np.polyfit(x[ok], y[ok], 1)
                resid = y - np.polyval(coef, x)
            g[f"{c}_amp_residual"] = resid
        amp_rows.append(g)
    amp = pd.concat(amp_rows, ignore_index=True)
    amp.to_csv(out_dir / "recording_features_amplitude_controlled.csv", index=False)

    # figures: energy and entropy by participant × timepoint
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for a, col, title in (
        (ax[0], "total_energy_deg2_s2", "Total movement energy"),
        (ax[1], "participation_entropy_bits", "Participation entropy"),
    ):
        for pid, g in rec.groupby("participant"):
            means = g.groupby("timepoint")[col].mean()
            a.plot(means.index, means.values, "o-", label=str(pid))
        a.set_xlabel("timepoint"); a.set_xticks([1, 2, 3])
        a.set_ylabel(col); a.set_title(title); a.legend(fontsize=8)
    fig.suptitle("S5 explicit features (descriptive; not intervention effects)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(fig_dir / "energy_entropy_by_timepoint.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for pid, g in amp.groupby("participant"):
        means = g.groupby("timepoint")["participation_entropy_bits_amp_residual"].mean()
        ax.plot(means.index, means.values, "o-", label=str(pid))
    ax.axhline(0, color="grey", ls=":", lw=1)
    ax.set_xlabel("timepoint"); ax.set_xticks([1, 2, 3])
    ax.set_ylabel("entropy residual after log-energy")
    ax.set_title("Amplitude-controlled participation entropy")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "entropy_amplitude_controlled.png", dpi=150)
    plt.close(fig)

    # regional energy shares stacked by timepoint (pooled)
    share_cols = [c for c in rec.columns if c.startswith("energy_share_")]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    tp_means = rec.groupby("timepoint")[share_cols].mean()
    bottom = np.zeros(len(tp_means))
    for c in share_cols:
        ax.bar(tp_means.index.astype(str), tp_means[c], bottom=bottom, label=c.replace("energy_share_", ""))
        bottom += tp_means[c].to_numpy()
    ax.set_ylabel("mean energy share"); ax.legend(fontsize=7, ncol=2)
    ax.set_title("Regional energy composition by timepoint (pooled)")
    fig.tight_layout()
    fig.savefig(fig_dir / "regional_energy_shares.png", dpi=150)
    plt.close(fig)

    provenance.write_json(out_dir / "s5_explicit_provenance.json", {
        **provenance.run_stamp("S5_explicit"),
        "n_windows": len(df),
        "n_recordings": len(rec),
        "feature_columns": feat_cols,
        "amplitude_control": "within-participant linear residual vs total_energy_log",
        "note": "Descriptive only. No intervention-effect claims.",
    })
    print(f"\n{len(df)} windows, {len(rec)} recording aggregates")
    print("S5 explicit features OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
