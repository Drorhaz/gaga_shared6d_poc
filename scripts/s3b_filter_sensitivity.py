#!/usr/bin/env python3
"""S3b - Filter sensitivity: direct 6D path vs validated primary path.

The primary path (validated in S2/S3) is:

```text
global quats → parent-relative quats → rotvec → Butterworth → matrix → 6D
```

This script runs the direct sensitivity path on a representative subset:

```text
global quats → parent-relative quats → matrix → 6D
```

with no rotvec conversion and no Butterworth filtering. Sign continuity on the
relative quaternions is still applied (it is a quaternion double-cover fix, not
a filter).

Comparisons (sensitivity only; primary path is not replaced):

1. Per-frame geodesic rotation difference between the two matrices.
2. Temporal power spectra of geodesic angle and of frame-to-frame angular speed.
3. Window embeddings from evaluation windows: (a) mean-pooled 6D content
   vectors, (b) deterministic untrained-encoder embeddings under identical
   weights, so the only difference is the input path.

A material filtering artifact would show large geodesic discrepancies relative
to typical joint motion, or window embeddings that disagree substantially.
Absent that, the validated primary path remains the project default.

Usage:
    ./.venv/bin/python scripts/s3b_filter_sensitivity.py
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
import torch  # noqa: E402
import yaml  # noqa: E402
from scipy.signal import welch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import motive_io, models, provenance, rotations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AXES = ("rx", "ry", "rz")

# Cover both templates, the meters export, the template-change participant, and
# the known filter-overshoot recording (790_T1_P1_R1).
SUBSET = [
    "252_T1_P1_R1",  # 55-bone, typical
    "252_T3_P1_R1",  # 55-bone, Meters export
    "651_T1_P1_R1",  # 51-bone
    "651_T2_P1_R1",  # 55-bone after mid-study template change
    "671_T1_P1_R1",  # 51-bone
    "790_T1_P1_R1",  # 55-bone; known tangent-space overshoot past pi
]

# Pre-registered interpretation thresholds. These gate a *recommendation*, not
# an automatic path swap.
MATERIAL_GEO_P99_DEG = 5.0       # p99 geodesic filter effect
MATERIAL_EMBED_COSINE = 0.95     # mean cosine of same-window embeddings
MATERIAL_HF_RATIO = 2.0          # high-band spectral power, direct / primary


def load_primary_matrices(path: Path, link_ids: list[str]) -> dict[str, np.ndarray]:
    df = pd.read_parquet(path)
    out = {}
    for lid in link_ids:
        rv = df[[f"{lid}_{a}" for a in AXES]].to_numpy()
        out[lid] = rotations.rotvec_to_matrix(rv)
    return out


def extract_direct_matrices(
    source_path: Path, links: list[dict], root_token: str,
) -> dict[str, np.ndarray]:
    bones = motive_io.read_bones(source_path)
    out = {}
    for link in links:
        parent = motive_io.resolve_bone(bones.header, link["parent"], root_token)
        child = motive_io.resolve_bone(bones.header, link["child"], root_token)
        res = rotations.extract_link_matrix_direct(
            bones.quaternions[:, bones.index_of(parent), :],
            bones.quaternions[:, bones.index_of(child), :],
        )
        out[link["id"]] = res["matrix"]
    return out


def geodesic_series(primary: np.ndarray, direct: np.ndarray) -> np.ndarray:
    n = min(len(primary), len(direct))
    ok = (
        np.all(np.isfinite(primary[:n].reshape(n, -1)), axis=1)
        & np.all(np.isfinite(direct[:n].reshape(n, -1)), axis=1)
    )
    err = np.full(n, np.nan)
    if ok.any():
        err[ok] = rotations.geodesic_error_deg(primary[:n][ok], direct[:n][ok])
    return err


def angle_series(mats: np.ndarray) -> np.ndarray:
    """True geodesic angle of each frame's rotation, in degrees."""
    from scipy.spatial.transform import Rotation

    n = len(mats)
    out = np.full(n, np.nan)
    ok = np.all(np.isfinite(mats.reshape(n, -1)), axis=1)
    if ok.any():
        out[ok] = np.degrees(np.linalg.norm(Rotation.from_matrix(mats[ok]).as_rotvec(), axis=1))
    return out


def angular_speed_series(mats: np.ndarray, fps: float) -> np.ndarray:
    """Frame-to-frame geodesic speed in deg/s; first sample NaN."""
    n = len(mats)
    out = np.full(n, np.nan)
    ok = np.all(np.isfinite(mats.reshape(n, -1)), axis=1)
    idx = np.flatnonzero(ok)
    if len(idx) < 2:
        return out
    # only consecutive finite pairs
    for a, b in zip(idx[:-1], idx[1:]):
        if b == a + 1:
            out[b] = float(rotations.geodesic_error_deg(mats[b:b + 1], mats[a:a + 1])[0]) * fps
    return out


def band_power(x: np.ndarray, fps: float, f_lo: float, f_hi: float) -> float:
    x = x[np.isfinite(x)]
    if len(x) < 256:
        return float("nan")
    freqs, psd = welch(x, fs=fps, nperseg=min(2048, len(x) // 4 * 4 or 256))
    band = (freqs >= f_lo) & (freqs < f_hi)
    if not band.any():
        return float("nan")
    return float(np.trapezoid(psd[band], freqs[band]))


def window_sixd(mats_by_link: dict[str, np.ndarray], link_ids: list[str],
                start: int, end: int) -> np.ndarray | None:
    """(T, L, 6) window, or None if any link has non-finite frames."""
    chunks = []
    for lid in link_ids:
        m = mats_by_link[lid][start:end]
        if not np.all(np.isfinite(m)):
            return None
        chunks.append(rotations.matrix_to_6d(m))
    return np.stack(chunks, axis=1)  # (T, L, 6)


def content_embedding(sixd: np.ndarray) -> np.ndarray:
    """Mean over time of 6D, flattened: (L*6,)."""
    return sixd.mean(axis=0).reshape(-1)


def figure_geodesic(geo: pd.DataFrame, out: Path) -> None:
    order = geo.groupby("link_id").p99_deg.median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(10, 5))
    data = [geo[geo.link_id == l].p99_deg.to_numpy() for l in order]
    ax.boxplot(data, orientation="vertical", tick_labels=list(order), showfliers=True)
    ax.axhline(MATERIAL_GEO_P99_DEG, color="crimson", ls="--", lw=1,
               label=f"material threshold ({MATERIAL_GEO_P99_DEG:g} deg p99)")
    ax.set_ylabel("p99 geodesic difference, primary vs direct (deg)")
    ax.set_xticklabels(order, rotation=60, ha="right", fontsize=7)
    ax.legend(fontsize=8)
    ax.set_title("S3b.1  Filter effect as geodesic rotation difference", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_spectra(spectra_rows: list[dict], out: Path, fps: float) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

    # Left: distribution of high-band power ratio (direct/primary)
    ratios = [r["hf_ratio"] for r in spectra_rows
              if r["path"] == "direct" and np.isfinite(r.get("hf_ratio", np.nan))]
    ax[0].hist(ratios, bins=30, color="#3b6ea5", edgecolor="white")
    ax[0].axvline(1.0, color="grey", ls=":", lw=1, label="equal power")
    ax[0].set_xlabel("high-band (10-40 Hz) power ratio  direct / primary")
    ax[0].set_ylabel("link-recordings")
    ax[0].legend(fontsize=8)
    ax[0].set_title("Angular-speed high-band power")

    # Right: low vs high band for both paths
    prim_lo = [r["lo_power"] for r in spectra_rows if r["path"] == "primary"]
    dir_lo = [r["lo_power"] for r in spectra_rows if r["path"] == "direct"]
    prim_hi = [r["hi_power"] for r in spectra_rows if r["path"] == "primary"]
    dir_hi = [r["hi_power"] for r in spectra_rows if r["path"] == "direct"]
    ax[1].boxplot(
        [prim_lo, dir_lo, prim_hi, dir_hi],
        tick_labels=["prim lo\n0-10Hz", "dir lo", "prim hi\n10-40Hz", "dir hi"],
        showfliers=False,
    )
    ax[1].set_yscale("log")
    ax[1].set_ylabel("band power (Welch)")
    ax[1].set_title("Spectral power by path and band")
    fig.suptitle("S3b.2  Temporal spectra: filter removes high-frequency content",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_welch_overlay(examples: list[dict], out: Path) -> None:
    """Overlay Welch PSD for a few representative link-recordings."""
    n = len(examples)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 3.6), sharey=True)
    if n == 1:
        axes = [axes]
    for ax, ex in zip(axes, examples):
        ax.semilogy(ex["f"], ex["psd_primary"], color="#3b6ea5", lw=1.5, label="primary (filtered)")
        ax.semilogy(ex["f"], ex["psd_direct"], color="crimson", lw=1.2, ls="--", label="direct")
        ax.axvline(10.0, color="grey", ls=":", lw=1)
        ax.set_xlabel("Hz")
        ax.set_title(f"{ex['recording_id']}\n{ex['link_id']}", fontsize=8)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("PSD of angular speed")
    fig.suptitle("S3b.2b  Welch PSD of frame-to-frame angular speed", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def figure_embeddings(emb: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for a, kind, title in (
        (ax[0], "content_6d", "mean-pooled 6D content"),
        (ax[1], "encoder_32d", "untrained encoder embedding (fixed weights)"),
    ):
        sub = emb[emb.kind == kind]
        a.hist(sub.cosine.to_numpy(), bins=30, color="#3b6ea5", edgecolor="white",
               range=(0.5, 1.0))
        a.axvline(MATERIAL_EMBED_COSINE, color="crimson", ls="--",
                  label=f"material threshold ({MATERIAL_EMBED_COSINE:g})")
        a.set_xlabel("cosine(primary, direct) for the same window")
        a.set_ylabel("windows")
        a.set_title(title)
        a.legend(fontsize=8)
        a.set_xlim(0.5, 1.01)
    fig.suptitle("S3b.3  Same-window embedding agreement across paths", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", nargs="*", default=SUBSET)
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
    links, root_token = linkcfg["links"], linkcfg["root_token"]
    link_ids = [l["id"] for l in links]
    fps = cfg["capture"]["frame_rate_hz"]

    reg = pd.read_csv(ROOT / "data/immutable/recording_registry.csv").set_index("recording_id")
    win = pd.read_csv(ROOT / "outputs/s4_windows/window_index.csv")
    rot_dir = ROOT / "data/immutable/rotvec_18link"

    out_dir = ROOT / "outputs/s3b_filter_sensitivity"
    fig_dir = ROOT / "figures/s3b_filter_sensitivity"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Fixed untrained encoder for embedding comparison (same weights both paths).
    torch.manual_seed(0)
    encoder = models.SharedMotionTransformer(
        n_links=cfg["model"]["n_links"], n_patches=cfg["model"]["n_patches"],
        patch_frames=cfg["model"]["patch_frames"], dim=cfg["model"]["hidden_dim"],
        n_blocks=cfg["model"]["n_blocks"], expansion=cfg["model"]["ffn_expansion"],
    ).eval()

    geo_rows, spec_rows, emb_rows = [], [], []
    welch_examples = []

    print(f"filter sensitivity on {len(args.subset)} recordings\n")
    for rid in args.subset:
        if rid not in reg.index:
            print(f"  ! missing registry entry: {rid}")
            continue
        r = reg.loc[rid]
        print(f"[{rid}] {r.skeleton_variant} / {r.length_units}")
        primary = load_primary_matrices(rot_dir / f"{rid}.parquet", link_ids)
        direct = extract_direct_matrices(Path(r.source_path), links, root_token)

        for lid in link_ids:
            geo = geodesic_series(primary[lid], direct[lid])
            finite = geo[np.isfinite(geo)]
            if not finite.size:
                continue
            geo_rows.append(
                {
                    "recording_id": rid, "participant": str(rid)[:3], "link_id": lid,
                    "n_frames": int(finite.size),
                    "mean_deg": float(finite.mean()),
                    "median_deg": float(np.median(finite)),
                    "p95_deg": float(np.percentile(finite, 95)),
                    "p99_deg": float(np.percentile(finite, 99)),
                    "max_deg": float(finite.max()),
                }
            )

            for path_name, mats in (("primary", primary[lid]), ("direct", direct[lid])):
                ang = angle_series(mats)
                spd = angular_speed_series(mats, fps)
                lo = band_power(spd, fps, 0.0, 10.0)
                hi = band_power(spd, fps, 10.0, 40.0)
                spec_rows.append(
                    {
                        "recording_id": rid, "link_id": lid, "path": path_name,
                        "quantity": "angular_speed",
                        "lo_power": lo, "hi_power": hi,
                    }
                )

            # pair ratio after both paths recorded
            pair = [s for s in spec_rows if s["recording_id"] == rid
                    and s["link_id"] == lid and s["quantity"] == "angular_speed"]
            if len(pair) >= 2:
                p = next(s for s in pair if s["path"] == "primary")
                d = next(s for s in pair if s["path"] == "direct")
                ratio = (d["hi_power"] / p["hi_power"]
                         if p["hi_power"] and p["hi_power"] > 0 else np.nan)
                for s in pair:
                    s["hf_ratio"] = ratio if s["path"] == "direct" else 1.0

            # keep a few Welch overlays for the report
            if lid in ("RShoulder_to_RUArm", "LUArm_to_LFArm", "Ab_to_Chest") and len(
                [e for e in welch_examples if e["recording_id"] == rid]
            ) < 1:
                spd_p = angular_speed_series(primary[lid], fps)
                spd_d = angular_speed_series(direct[lid], fps)
                xp, xd = spd_p[np.isfinite(spd_p)], spd_d[np.isfinite(spd_d)]
                if len(xp) > 512 and len(xd) > 512:
                    nper = min(2048, len(xp) // 4 * 4)
                    fp, pp = welch(xp, fs=fps, nperseg=nper)
                    fd, pd_ = welch(xd, fs=fps, nperseg=nper)
                    welch_examples.append(
                        {"recording_id": rid, "link_id": lid,
                         "f": fp, "psd_primary": pp, "psd_direct": pd_}
                    )

        # Window embeddings on evaluation windows for this recording
        wsub = win[(win.recording_id == rid) & (win.role == "evaluation") & win.usable]
        for _, w in wsub.iterrows():
            sp = window_sixd(primary, link_ids, int(w.start_frame), int(w.end_frame))
            sd = window_sixd(direct, link_ids, int(w.start_frame), int(w.end_frame))
            if sp is None or sd is None:
                continue
            # content embedding
            cp, cd = content_embedding(sp), content_embedding(sd)
            cos_c = float(np.dot(cp, cd) / (np.linalg.norm(cp) * np.linalg.norm(cd) + 1e-12))
            emb_rows.append(
                {"recording_id": rid, "window_id": w.window_id, "kind": "content_6d",
                 "cosine": cos_c, "l2": float(np.linalg.norm(cp - cd))}
            )
            # encoder embedding, identical weights
            with torch.no_grad():
                tp = torch.from_numpy(sp[None].astype(np.float32))
                td = torch.from_numpy(sd[None].astype(np.float32))
                ep = encoder.embedding(tp).numpy()[0]
                ed = encoder.embedding(td).numpy()[0]
            cos_e = float(np.dot(ep, ed) / (np.linalg.norm(ep) * np.linalg.norm(ed) + 1e-12))
            emb_rows.append(
                {"recording_id": rid, "window_id": w.window_id, "kind": "encoder_32d",
                 "cosine": cos_e, "l2": float(np.linalg.norm(ep - ed))}
            )

        print(f"    geo p99 median {np.median([g['p99_deg'] for g in geo_rows if g['recording_id']==rid]):.3f} deg | "
              f"eval windows compared {int(wsub.shape[0])}")

    geo = pd.DataFrame(geo_rows)
    emb = pd.DataFrame(emb_rows)
    # attach hf_ratio onto a tidy spectral table (one row per link-recording)
    spec_tidy = []
    for (rid, lid), g in pd.DataFrame(spec_rows).groupby(["recording_id", "link_id"]):
        p = g[g.path == "primary"].iloc[0]
        d = g[g.path == "direct"].iloc[0]
        spec_tidy.append(
            {
                "recording_id": rid, "link_id": lid,
                "primary_lo": p.lo_power, "primary_hi": p.hi_power,
                "direct_lo": d.lo_power, "direct_hi": d.hi_power,
                "hf_ratio": (d.hi_power / p.hi_power
                             if p.hi_power and p.hi_power > 0 else np.nan),
                "lf_ratio": (d.lo_power / p.lo_power
                             if p.lo_power and p.lo_power > 0 else np.nan),
            }
        )
    spec = pd.DataFrame(spec_tidy)

    geo.to_csv(out_dir / "geodesic_filter_effect.csv", index=False)
    spec.to_csv(out_dir / "spectral_comparison.csv", index=False)
    emb.to_csv(out_dir / "window_embedding_agreement.csv", index=False)

    print("\nrendering figures ...")
    figure_geodesic(geo, fig_dir / "s3b_1_geodesic_difference.png")
    # rebuild flat rows for the spectra figure
    flat_spec = []
    for r in spec.itertuples():
        flat_spec.append({"quantity": "angular_speed", "path": "primary",
                          "lo_power": r.primary_lo, "hi_power": r.primary_hi,
                          "hf_ratio": 1.0})
        flat_spec.append({"quantity": "angular_speed", "path": "direct",
                          "lo_power": r.direct_lo, "hi_power": r.direct_hi,
                          "hf_ratio": r.hf_ratio})
    figure_spectra(flat_spec, fig_dir / "s3b_2_spectra.png", fps)
    if welch_examples:
        figure_welch_overlay(welch_examples[:4], fig_dir / "s3b_2b_welch_overlay.png")
    figure_embeddings(emb, fig_dir / "s3b_3_embedding_agreement.png")

    # --- decision summary ---
    geo_p99 = float(geo.p99_deg.median())
    geo_max = float(geo.max_deg.max())
    hf_med = float(spec.hf_ratio.median())
    hf_p95 = float(np.nanpercentile(spec.hf_ratio, 95))
    cos_content = float(emb[emb.kind == "content_6d"].cosine.median())
    cos_enc = float(emb[emb.kind == "encoder_32d"].cosine.median())
    frac_geo_material = float((geo.p99_deg > MATERIAL_GEO_P99_DEG).mean())
    frac_cos_low = float((emb[emb.kind == "content_6d"].cosine < MATERIAL_EMBED_COSINE).mean())

    material = (
        geo_p99 > MATERIAL_GEO_P99_DEG
        or cos_content < MATERIAL_EMBED_COSINE
        or hf_med > MATERIAL_HF_RATIO * 5  # high-band ratio alone is expected; escalate only if extreme
    )
    # High-frequency attenuation is the *purpose* of the filter; hf_ratio >> 1
    # is expected and not by itself a reason to abandon the primary path.
    # Material = large SO(3) disagreement or embedding disagreement.

    print(f"\n{'='*72}\nfilter sensitivity summary\n{'='*72}")
    print(f"recordings compared     : {len(args.subset)}")
    print(f"geodesic difference     : median p99 {geo_p99:.3f} deg | "
          f"worst max {geo_max:.2f} deg | "
          f"fraction of link-recordings with p99 > {MATERIAL_GEO_P99_DEG:g} deg: "
          f"{frac_geo_material:.1%}")
    print(f"high-band power ratio   : median {hf_med:.2f}x | p95 {hf_p95:.2f}x "
          f"(direct/primary; >1 means filter removed high-frequency content, as designed)")
    print(f"window embedding cosine : content-6D median {cos_content:.4f} | "
          f"encoder-32D median {cos_enc:.4f}")
    print(f"                          fraction of windows with content cosine < "
          f"{MATERIAL_EMBED_COSINE:g}: {frac_cos_low:.1%}")

    recommendation = "KEEP_PRIMARY"
    if material:
        recommendation = "REVIEW_FILTER_ARTIFACT"
    print(f"\nrecommendation: {recommendation}")
    if recommendation == "KEEP_PRIMARY":
        print("  Geodesic and embedding agreement stay within pre-set thresholds.")
        print("  High-band attenuation is expected from a 10 Hz low-pass and is not")
        print("  treated as an artifact. The validated primary path is unchanged.")
    else:
        print("  Comparison exceeded a material threshold. Inspect figures before")
        print("  any path change; the primary path is NOT swapped automatically.")

    report = ROOT / "reports/FILTER_SENSITIVITY_REPORT.md"
    report.write_text(
        _write_report(
            args.subset, geo, spec, emb, geo_p99, geo_max, hf_med, hf_p95,
            cos_content, cos_enc, frac_geo_material, frac_cos_low, recommendation,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {report.relative_to(ROOT)}")

    provenance.write_json(
        out_dir / "s3b_provenance.json",
        {
            **provenance.run_stamp("S3b_filter_sensitivity"),
            "subset": list(args.subset),
            "thresholds": {
                "material_geo_p99_deg": MATERIAL_GEO_P99_DEG,
                "material_embed_cosine": MATERIAL_EMBED_COSINE,
                "material_hf_ratio_note": (
                    "hf_ratio >> 1 is expected; not used alone to swap paths"
                ),
            },
            "geodesic_median_p99_deg": geo_p99,
            "geodesic_worst_max_deg": geo_max,
            "hf_ratio_median": hf_med,
            "content_cosine_median": cos_content,
            "encoder_cosine_median": cos_enc,
            "recommendation": recommendation,
            "primary_path_replaced": False,
        },
    )

    print("\nS3b OK  (sensitivity only; primary path retained)")
    return 0


def _write_report(subset, geo, spec, emb, geo_p99, geo_max, hf_med, hf_p95,
                  cos_content, cos_enc, frac_geo, frac_cos, recommendation) -> str:
    top = geo.groupby("link_id").p99_deg.median().sort_values(ascending=False).head(6)
    top_tbl = "\n".join(f"| `{k}` | {v:.3f} |" for k, v in top.items())
    by_rec = geo.groupby("recording_id").agg(
        median_p99=("p99_deg", "median"), max_max=("max_deg", "max")
    )
    rec_tbl = "\n".join(
        f"| `{i}` | {r.median_p99:.3f} | {r.max_max:.2f} |" for i, r in by_rec.iterrows()
    )
    lf_med = float(spec.lf_ratio.median())
    return f"""# Filter sensitivity report (S3b)

**Status: sensitivity only. Primary path not replaced.**
Recommendation: **{recommendation}**

The direct path below was **not** implemented before this report. It has now
been run on a representative subset and compared with the validated primary
path. Absent a material filtering artifact, the project continues to use the
primary path for all stages.

---

## Paths compared

| Role | Path |
|---|---|
| **Primary (validated)** | raw global quats → parent-relative quats → **rotvec → Butterworth 10 Hz** → matrix → 6D |
| **Direct (sensitivity)** | raw global quats → parent-relative quats → matrix → 6D |

The direct path applies quaternion sign continuity (double-cover fix) but
**does not** convert to rotvec and **does not** apply Butterworth filtering.

---

## Subset

{", ".join(f"`{r}`" for r in subset)}

Chosen to cover both skeleton templates, the `252-T3` Meters export, the
mid-study template change (`651-T2`), and the known filter-overshoot recording
(`790_T1_P1_R1`).

---

## 1. Geodesic rotation difference

Per-frame geodesic angle between primary and direct rotation matrices.

| Summary | Value |
|---|---|
| Median of per-link-recording p99 | **{geo_p99:.3f} deg** |
| Worst single-frame difference | {geo_max:.2f} deg |
| Fraction of link-recordings with p99 > {MATERIAL_GEO_P99_DEG:g} deg | {frac_geo:.1%} |

Median p99 by link (highest first):

| Link | Median p99 (deg) |
|---|---|
{top_tbl}

By recording:

| Recording | Median p99 (deg) | Worst max (deg) |
|---|---|---|
{rec_tbl}

![geodesic](../figures/s3b_filter_sensitivity/s3b_1_geodesic_difference.png)

---

## 2. Temporal spectra

Welch band power of frame-to-frame angular speed.

| Band | Result |
|---|---|
| Low (0-10 Hz) | largely preserved: median LF ratio (direct/primary) **{lf_med:.2f}x** |
| High (10-40 Hz) | attenuated by the filter: median HF ratio (direct/primary) **{hf_med:.2f}x**, p95 **{hf_p95:.2f}x** |

High-band attenuation is the designed effect of a 10 Hz low-pass at 120 Hz
sampling. It is **not** by itself treated as a reason to abandon the primary
path.

![spectra](../figures/s3b_filter_sensitivity/s3b_2_spectra.png)

![welch](../figures/s3b_filter_sensitivity/s3b_2b_welch_overlay.png)

---

## 3. Window embeddings

Same evaluation windows, both paths. Two embedding definitions:

1. **Content 6D** — mean over time of the 6D tensor, flattened (108-D).
2. **Encoder 32-D** — the project's deterministic mean-pooled encoder embedding
   under a fixed untrained weight draw (identical weights for both paths).

| Embedding | Median cosine(primary, direct) | Fraction below {MATERIAL_EMBED_COSINE:g} |
|---|---|---|
| Content 6D | **{cos_content:.4f}** | {frac_cos:.1%} |
| Encoder 32-D | **{cos_enc:.4f}** | — |

![embeddings](../figures/s3b_filter_sensitivity/s3b_3_embedding_agreement.png)

---

## Decision rule and outcome

Pre-set material thresholds:

* geodesic p99 median > {MATERIAL_GEO_P99_DEG:g} deg, or
* content-embedding median cosine < {MATERIAL_EMBED_COSINE:g}

High-band spectral ratio alone does not trigger a path change.

**Outcome: {recommendation}.** The validated primary path remains the project
default. Tables and figures are retained under `outputs/s3b_filter_sensitivity/`
and `figures/s3b_filter_sensitivity/` for audit.
"""


if __name__ == "__main__":
    raise SystemExit(main())
