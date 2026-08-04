#!/usr/bin/env python3
"""S5.1 — PCA baseline (d=32), fold-wise, training-T1 only."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gaga_shared6d import data_windows, provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def window_vectors(index: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Time-mean 6D flattened to 108-D per window."""
    xs, ids = [], []
    for row in index.itertuples():
        arrs = data_windows.load_recording_arrays(row.recording_id, ROOT)
        sl = arrs["sixd"][int(row.start_frame):int(row.end_frame)]
        if sl.ndim != 3 or not np.all(np.isfinite(sl)):
            continue
        xs.append(sl.mean(axis=0).reshape(-1).astype(np.float64))
        ids.append(row.window_id)
    out = index[index.window_id.isin(ids)].reset_index(drop=True)
    return np.stack(xs, axis=0), out


def main() -> int:
    cfg = data_windows.load_config(ROOT)
    out_dir = ROOT / "outputs/s5_pca"
    fig_dir = ROOT / "figures/s5_pca"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    w = data_windows.load_window_index(ROOT)
    eval_ex = cfg["exercises"]["evaluation"]
    d_req = cfg["s5"]["pca_dim"]

    var_rows, rec_rows, emb_rows, probe_rows = [], [], [], []

    for fold, spec in cfg["folds"].items():
        train_idx = w[(w.fold == fold) & (w.role == "training") & w.usable]
        early_idx = w[(w.fold == fold) & (w.role == "early_stop") & w.usable]
        # evaluation on trajectory repetition (held-out rep) + descriptive all
        traj_rep = spec["trajectory_repetition"]
        eval_idx = w[(w.role == "evaluation") & w.usable & (w.repetition == traj_rep)]

        x_tr, tr = window_vectors(train_idx)
        x_es, es = window_vectors(early_idx)
        x_ev, ev = window_vectors(eval_idx)

        # fit scaler + PCA on training-T1 only
        scaler = StandardScaler()
        x_tr_s = scaler.fit_transform(x_tr)
        d = min(d_req, x_tr_s.shape[0] - 1, x_tr_s.shape[1])
        pca = PCA(n_components=d, random_state=0)
        z_tr = pca.fit_transform(x_tr_s)
        z_es = pca.transform(scaler.transform(x_es))
        z_ev = pca.transform(scaler.transform(x_ev))

        # reconstruction error on held-out T1 (early stop blocks)
        x_es_hat = scaler.inverse_transform(pca.inverse_transform(z_es))
        mse_es = float(np.mean((x_es - x_es_hat) ** 2))
        x_tr_hat = scaler.inverse_transform(pca.inverse_transform(z_tr))
        mse_tr = float(np.mean((x_tr - x_tr_hat) ** 2))

        for i, v in enumerate(pca.explained_variance_ratio_):
            var_rows.append({"fold": fold, "component": i + 1, "explained_variance_ratio": float(v),
                             "cumulative": float(pca.explained_variance_ratio_[:i + 1].sum())})
        rec_rows.append({
            "fold": fold, "n_train": len(tr), "n_early_stop": len(es), "n_eval": len(ev),
            "pca_dim": d, "mse_train": mse_tr, "mse_heldout_t1": mse_es,
            "var_explained_total": float(pca.explained_variance_ratio_.sum()),
        })

        # aggregate embeddings
        for z, idx, role in ((z_tr, tr, "training"), (z_es, es, "early_stop"), (z_ev, ev, "evaluation")):
            agg = data_windows.aggregate_recording_embeddings(z, idx, eval_ex if role == "evaluation"
                                                              else sorted(idx.exercise_id.unique()))
            agg.insert(0, "fold", fold)
            agg.insert(1, "role", role)
            emb_rows.append(agg)

        # participant-identity probe on held-out T1 windows
        y_tr = tr.participant.astype(str).to_numpy()
        y_es = es.participant.astype(str).to_numpy()
        clf = LogisticRegression(max_iter=1000, random_state=0)
        clf.fit(z_tr, y_tr)
        acc = float((clf.predict(z_es) == y_es).mean())
        chance = 1.0 / len(np.unique(y_tr))
        probe_rows.append({"fold": fold, "accuracy": acc, "chance": chance,
                           "above_chance": acc - chance})

        # amplitude sensitivity: correlate PC1 with total energy of window
        energies = []
        for row in es.itertuples():
            rv = data_windows.load_recording_arrays(row.recording_id, ROOT)["rotvec"]
            sl = rv[int(row.start_frame):int(row.end_frame)]
            energies.append(float(np.nanmean(np.diff(sl, axis=0) ** 2)))
        energies = np.asarray(energies)
        if len(energies) == len(z_es):
            corr = float(np.corrcoef(z_es[:, 0], energies)[0, 1]) if np.std(energies) > 0 else float("nan")
        else:
            corr = float("nan")
        rec_rows[-1]["pc1_energy_corr_heldout_t1"] = corr

        print(f"fold {fold}: d={d}  var={pca.explained_variance_ratio_.sum():.3f}  "
              f"MSE held-out T1={mse_es:.4f}  identity probe={acc:.3f} (chance {chance:.3f})  "
              f"PC1~energy r={corr:.3f}")

        # figures per fold
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].plot(np.arange(1, d + 1), np.cumsum(pca.explained_variance_ratio_), "o-", color="#3b6ea5")
        ax[0].axhline(0.8, color="grey", ls=":", lw=1)
        ax[0].set_xlabel("component"); ax[0].set_ylabel("cumulative explained variance")
        ax[0].set_title(f"Fold {fold}: PCA cumulative variance")
        ax[1].bar(["train", "held-out T1"], [mse_tr, mse_es], color=["#7aa64f", "#3b6ea5"])
        ax[1].set_ylabel("MSE of 108-D time-mean 6D")
        ax[1].set_title(f"Fold {fold}: reconstruction error")
        fig.tight_layout()
        fig.savefig(fig_dir / f"pca_fold_{fold}.png", dpi=150)
        plt.close(fig)

    pd.DataFrame(var_rows).to_csv(out_dir / "explained_variance.csv", index=False)
    pd.DataFrame(rec_rows).to_csv(out_dir / "reconstruction_summary.csv", index=False)
    pd.concat(emb_rows, ignore_index=True).to_csv(out_dir / "recording_embeddings.csv", index=False)
    pd.DataFrame(probe_rows).to_csv(out_dir / "identity_probe.csv", index=False)

    # descriptive T2/T3 PC distances from T1 (trajectory rep), not for tuning
    emb = pd.concat(emb_rows, ignore_index=True)
    ecols = [c for c in emb.columns if c.startswith("e") and not c.startswith("ex11")]
    diag = []
    for fold, g in emb[emb.role == "evaluation"].groupby("fold"):
        for pid, gp in g.groupby("participant"):
            t1 = gp[gp.timepoint == 1]
            if t1.empty:
                continue
            z1 = t1[ecols].mean().to_numpy()
            for tp in (2, 3):
                tt = gp[gp.timepoint == tp]
                if tt.empty:
                    continue
                zt = tt[ecols].mean().to_numpy()
                diag.append({
                    "fold": fold, "participant": pid, "timepoint": tp,
                    "l2_from_t1": float(np.linalg.norm(zt - z1)),
                    "cosine_from_t1": float(
                        np.dot(zt, z1) / (np.linalg.norm(zt) * np.linalg.norm(z1) + 1e-12)
                    ),
                })
    pd.DataFrame(diag).to_csv(out_dir / "t2t3_descriptive_distances.csv", index=False)

    provenance.write_json(out_dir / "s5_pca_provenance.json", {
        **provenance.run_stamp("S5_pca"),
        "pca_dim_requested": d_req,
        "input": "time-mean 6D flattened (108-D) from primary filtered path",
        "fit": "StandardScaler+PCA on fold training-T1 windows only",
        "folds": rec_rows,
        "identity_probe": probe_rows,
    })
    print("\nS5 PCA OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
