#!/usr/bin/env python3
"""S2 - Common 18-link endpoint-relative extraction.

Derives the canonical 18-link parent-relative rotations directly from the raw
global bone quaternions, using one identical operation for all four
participants. No chain product is computed: because a parent-relative chain
telescopes, the endpoint-relative rotation between two bones already equals the
composed chain between them.

Two independent validations run here:

* 252/790 carry the intermediate spine and neck bones, so the composed chain
  can be built explicitly and compared against the endpoint extraction. This
  proves the telescoping identity on real data.
* 671/651 do not carry those intermediate bones, so no compose-and-compare
  control exists for them. Instead their extraction is compared against the
  trusted cached rotations from the source project, which validates the
  convention, multiplication order, axis handling and filter equivalence.

Usage:
    python scripts/s2_extract.py [--limit N] [--force]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import motive_io, provenance, rotations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AXES = ("rx", "ry", "rz")


def cache_column_name(link_id: str, root_bone: str) -> str:
    """Map a canonical link id to the source project's cached column stem.

    Pelvis links are stored under the literal root bone name, which is not
    stable across the study: 651 exports as `651:651` at T1 but `651_T2:651_T2`
    at T2, so the stem is `651_to_Ab` in one and `651_T2_to_Ab` in the other.
    """
    if link_id.startswith("pelvis_to_"):
        stem = root_bone.split(":", 1)[-1]
        return link_id.replace("pelvis", stem, 1)
    return link_id


def extract_recording(
    path: Path, links: list[dict], root_token: str, cfg: dict
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Extract all 18 links from one recording."""
    bones = motive_io.read_bones(path)
    header = bones.header
    sos = rotations.design_butterworth_sos(
        cfg["filter"]["cutoff_hz"], cfg["capture"]["frame_rate_hz"], cfg["filter"]["order"]
    )

    columns: dict[str, np.ndarray] = {}
    flag_rows = []
    for link in links:
        parent = motive_io.resolve_bone(header, link["parent"], root_token)
        child = motive_io.resolve_bone(header, link["child"], root_token)
        pi, ci = bones.index_of(parent), bones.index_of(child)

        res = rotations.extract_link_rotvec(
            bones.quaternions[:, pi, :],
            bones.quaternions[:, ci, :],
            sos,
            near_pi_fraction=cfg["qc"]["near_pi_warning_fraction"],
            jump_fail_rad=cfg["qc"]["jump_fail_rad"],
        )
        for ai, axis in enumerate(AXES):
            columns[f"{link['id']}_{axis}"] = res["rotvec"][:, ai]

        angle = res["angle_rad"]
        finite = angle[np.isfinite(angle)]
        flag_rows.append(
            {
                "link_id": link["id"],
                "region": link["region"],
                "parent_bone": parent,
                "child_bone": child,
                "spans": ",".join(link["spans"]),
                "n_frames": len(angle),
                "n_quaternion_invalid": int(res["quaternion_invalid"].sum()),
                "n_near_pi": int(res["near_pi"].sum()),
                "frac_near_pi": float(res["near_pi"].mean()),
                "n_rotation_jump": int(res["rotation_jump"].sum()),
                "n_filtered": int(res["filter_applied"].sum()),
                "angle_deg_p50": float(np.degrees(np.percentile(finite, 50))) if finite.size else np.nan,
                "angle_deg_p99": float(np.degrees(np.percentile(finite, 99))) if finite.size else np.nan,
                "angle_deg_max": float(np.degrees(finite.max())) if finite.size else np.nan,
            }
        )

    # Chain-composition control and source-alias reproduction, both available
    # only on recordings whose skeleton actually carries the intermediate bones.
    chain_checks = []
    alias_rotvecs: dict[str, np.ndarray] = {}
    for link in links:
        if not link["spans"]:
            continue
        try:
            chain_tokens = [link["parent"], *link["spans"], link["child"]]
            idx = [
                bones.index_of(motive_io.resolve_bone(header, t, root_token))
                for t in chain_tokens
            ]
        except KeyError:
            continue  # this recording lacks the intermediates; nothing to compose
        chk = rotations.verify_chain_composition(
            bones.quaternions, idx, tol=cfg["qc"]["extraction_match_tol_rad"]
        )
        chain_checks.append({"link_id": link["id"], "chain": " -> ".join(chain_tokens), **chk})
        alias_rotvecs[link["id"]] = rotations.extract_link_rotvec(
            bones.quaternions[:, idx[-2], :], bones.quaternions[:, idx[-1], :], sos
        )["rotvec"]

    return pd.DataFrame(columns), pd.DataFrame(flag_rows), {
        "n_frames": int(bones.quaternions.shape[0]),
        "n_bones": len(bones.bone_names),
        "length_units": header.length_units,
        "root_bone": header.root_bone(),
        "chain_checks": chain_checks,
        "alias_rotvecs": alias_rotvecs,
    }


def _max_diff(a: np.ndarray, b: np.ndarray) -> tuple[float, float, int]:
    both = np.all(np.isfinite(a), axis=1) & np.all(np.isfinite(b), axis=1)
    if not both.any():
        return float("nan"), float("nan"), 0
    d = np.linalg.norm(a[both] - b[both], axis=1)
    return float(d.max()), float(d.mean()), int(both.sum())


def compare_with_cache(
    extracted: pd.DataFrame,
    cache_path: Path,
    root_bone: str,
    links: list[dict],
    alias_rotvecs: dict[str, np.ndarray],
    tol: float,
) -> list[dict]:
    """Compare extracted rotvecs against the source project's trusted cache.

    Where a link disagrees, the source project's known aliasing is tested as an
    explanation: for a spanning link it stores only the FINAL sub-link under the
    canonical name (e.g. Neck2->Head labelled `Neck_to_Head`). Reproducing that
    alias bit-exactly confirms the discrepancy is a source-side labelling
    choice, not an extraction error here.
    """
    if not cache_path.exists():
        return []
    cached = pd.read_parquet(cache_path)
    out = []
    n = min(len(extracted), len(cached))
    for link in links:
        stem = cache_column_name(link["id"], root_bone)
        cols = [f"{stem}_{a}" for a in AXES]
        if not all(c in cached.columns for c in cols):
            out.append(
                {"link_id": link["id"], "cache_column": stem, "present_in_cache": False,
                 "agrees": None, "explained_by_source_alias": None}
            )
            continue

        a = extracted[[f"{link['id']}_{ax}" for ax in AXES]].to_numpy()[:n]
        b = cached[cols].to_numpy()[:n]
        mx, mean, n_cmp = _max_diff(a, b)
        row = {
            "link_id": link["id"], "cache_column": stem, "present_in_cache": True,
            "n_compared": n_cmp, "max_abs_diff_rad": mx, "mean_abs_diff_rad": mean,
            "agrees": bool(mx <= tol), "explained_by_source_alias": False,
            "alias_max_diff_rad": np.nan,
        }
        if mx > tol and link["id"] in alias_rotvecs:
            amx, amean, _ = _max_diff(alias_rotvecs[link["id"]][:n], b)
            row["alias_max_diff_rad"] = amx
            row["explained_by_source_alias"] = bool(amx <= tol)
            row["source_alias_is"] = f"{link['spans'][-1]}_to_{link['child']}"
        out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-project", default="../gaga_jcvpca")
    ap.add_argument("--limit", type=int, default=None, help="process only the first N recordings")
    ap.add_argument("--force", action="store_true", help="re-extract even if output exists")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
    links, root_token = linkcfg["links"], linkcfg["root_token"]
    assert len(links) == cfg["model"]["n_links"], (
        f"expected {cfg['model']['n_links']} links, config has {len(links)}"
    )

    source = (ROOT / args.source_project).resolve()
    reg = pd.read_csv(ROOT / "data/immutable/recording_registry.csv")
    out_dir = ROOT / "data/immutable/rotvec_18link"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = list(reg.itertuples())[: args.limit]
    tol = cfg["qc"]["extraction_match_tol_rad"]
    print(f"extracting {len(links)} endpoint-relative links from {len(rows)} recordings\n")

    all_flags, all_cache, all_chain, summaries = [], [], [], []
    t_start = time.time()

    for i, r in enumerate(rows, 1):
        dest = out_dir / f"{r.recording_id}.parquet"
        if dest.exists() and not args.force:
            print(f"[{i:2d}/{len(rows)}] {r.recording_id}  (cached, skipped)")
            continue

        t0 = time.time()
        print(f"[{i:2d}/{len(rows)}] {r.recording_id}  reading ...", end="", flush=True)
        df, flags, meta = extract_recording(Path(r.source_path), links, root_token, cfg)
        df.to_parquet(dest, index=False)

        flags.insert(0, "recording_id", r.recording_id)
        flags.insert(1, "participant", r.participant)
        all_flags.append(flags)

        cache_path = source / f"outputs/cache/matrices/{r.recording_id}.parquet"
        cmp_rows = compare_with_cache(
            df, cache_path, meta["root_bone"], links, meta["alias_rotvecs"], tol
        )
        for c in cmp_rows:
            all_cache.append({"recording_id": r.recording_id, "participant": r.participant, **c})
        for c in meta["chain_checks"]:
            all_chain.append({"recording_id": r.recording_id, "participant": r.participant, **c})

        matched = [c for c in cmp_rows if c.get("present_in_cache")]
        n_agree = sum(1 for c in matched if c["agrees"])
        n_alias = sum(1 for c in matched if c.get("explained_by_source_alias"))
        n_unexplained = len(matched) - n_agree - n_alias
        worst_chain = max((c["max_error_deg"] for c in meta["chain_checks"]), default=float("nan"))
        summaries.append(
            {
                "recording_id": r.recording_id, "participant": r.participant,
                "n_frames": meta["n_frames"], "n_bones": meta["n_bones"],
                "skeleton_variant": "55bone_extended" if meta["n_bones"] > 51 else "51bone_basic",
                "n_cache_links_compared": len(matched),
                "n_exact_agreement": n_agree,
                "n_explained_by_source_alias": n_alias,
                "n_unexplained_disagreement": n_unexplained,
                "n_chain_checks": len(meta["chain_checks"]),
                "max_chain_error_deg": worst_chain,
                "seconds": round(time.time() - t0, 1),
            }
        )
        alias_note = f" +{n_alias} alias-explained" if n_alias else ""
        bad = f"  <== {n_unexplained} UNEXPLAINED" if n_unexplained else ""
        print(
            f" {meta['n_frames']} fr | cache {n_agree}/{len(matched)} exact{alias_note} "
            f"| chain {len(meta['chain_checks'])} maxerr {worst_chain:.1e} deg "
            f"| {time.time()-t0:.0f}s{bad}"
        )

    if not summaries:
        print("\nnothing to do (all cached); use --force to re-extract")
        return 0

    val_dir = ROOT / "outputs/s2_extract"
    val_dir.mkdir(parents=True, exist_ok=True)
    pd.concat(all_flags).to_csv(val_dir / "link_qc_flags.csv", index=False)
    pd.DataFrame(all_cache).to_csv(val_dir / "cache_comparison.csv", index=False)
    pd.DataFrame(all_chain).to_csv(val_dir / "chain_composition_checks.csv", index=False)
    pd.DataFrame(summaries).to_csv(val_dir / "extraction_summary.csv", index=False)

    cache_df = pd.DataFrame(all_cache)
    chain_df = pd.DataFrame(all_chain)
    sm = pd.DataFrame(summaries)
    matched = cache_df[cache_df.present_in_cache == True] if len(cache_df) else cache_df  # noqa: E712

    print(f"\n{'='*72}\nvalidation summary   ({time.time()-t_start:.0f}s total)")
    print(f"{'='*72}")

    if len(matched):
        n_agree = int(matched.agrees.sum())
        alias = matched[matched.explained_by_source_alias == True]  # noqa: E712
        unexp = matched[(~matched.agrees) & (matched.explained_by_source_alias != True)]  # noqa: E712
        print(f"cache comparison : {len(matched)} link-recordings compared")
        print(f"    exact agreement (0 rad)     : {n_agree}")
        print(f"    explained by source alias   : {len(alias)}")
        print(f"    unexplained disagreement    : {len(unexp)}   "
              f"({'PASS' if len(unexp) == 0 else 'FAIL'})")
        for lid, g in alias.groupby("link_id"):
            print(f"      alias: {lid} <- {g.iloc[0].get('source_alias_is')} in "
                  f"{len(g)} recordings; anatomical difference up to "
                  f"{np.degrees(g.max_abs_diff_rad.max()):.1f} deg, "
                  f"alias reproduced to {g.alias_max_diff_rad.max():.1e} rad")
        for r in unexp.itertuples():
            print(f"      ! {r.recording_id} {r.link_id}: {r.max_abs_diff_rad:.3e} rad")

    if len(chain_df):
        worst_c = chain_df.max_error_deg.max()
        print(f"chain composition: {len(chain_df)} checks on "
              f"{chain_df.recording_id.nunique()} recordings, worst {worst_c:.3e} deg  "
              f"({'PASS' if chain_df.passed.all() else 'FAIL'})")

    print("\nskeleton template coverage:")
    for variant, g in sm.groupby("skeleton_variant"):
        print(f"    {variant}: {len(g)} recordings ({', '.join(sorted(g.recording_id))})")

    provenance.write_json(
        val_dir / "s2_provenance.json",
        {
            **provenance.run_stamp("S2_extract"),
            "n_links": len(links),
            "link_ids": [l["id"] for l in links],
            "filter": cfg["filter"],
            "n_recordings": len(summaries),
            "cache_exact_agreements": int(matched.agrees.sum()) if len(matched) else None,
            "cache_alias_explained": int((matched.explained_by_source_alias == True).sum())  # noqa: E712
            if len(matched) else None,
            "cache_unexplained": int(
                ((~matched.agrees) & (matched.explained_by_source_alias != True)).sum()  # noqa: E712
            ) if len(matched) else None,
            "chain_worst_error_deg": float(chain_df.max_error_deg.max()) if len(chain_df) else None,
        },
    )

    blocking = []
    if len(matched):
        n_unexp = int(((~matched.agrees) & (matched.explained_by_source_alias != True)).sum())  # noqa: E712
        if n_unexp:
            blocking.append(f"{n_unexp} unexplained disagreements with trusted cache")
    if len(chain_df) and not chain_df.passed.all():
        blocking.append("chain-composition identity failed")
    print("\nS2 " + ("BLOCKED: " + "; ".join(blocking) if blocking else "OK"))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
