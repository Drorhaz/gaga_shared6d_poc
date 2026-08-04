#!/usr/bin/env python3
"""S1 - Scaffold ingest: recording registry, units validation, segmentation.

Builds the immutable input manifest for the Stage 0 POC. Nothing here reads
frame data; it is header-and-metadata only, plus the segmentation workbooks.

Key provenance rule enforced here: recordings are keyed by the embedded Motive
``Capture Start Time``, never by filename. ``252_T2`` is named 2026-04-26 but
was captured 2026-05-19, which on filenames alone makes its T2 appear to
precede its T1.

Usage:
    python scripts/s1_ingest.py [--source-project ../gaga_jcvpca] [--no-checksums]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import motive_io, provenance, segmentation  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW_RE = re.compile(r"(\d+)_T(\d)_P(\d)_R(\d)")


def discover_recordings(raw_dir: Path) -> list[dict]:
    found = []
    for path in sorted(raw_dir.glob("*/*.csv")):
        m = RAW_RE.match(path.name.replace(" ", "_"))
        if not m:
            print(f"  ! unparseable filename, skipped: {path.name}")
            continue
        found.append(
            {
                "participant": m.group(1),
                "timepoint": int(m.group(2)),
                "task_part": int(m.group(3)),
                "repetition": int(m.group(4)),
                "path": path,
            }
        )
    return found


def build_registry(recordings: list[dict], expected_units: str, checksums: bool) -> pd.DataFrame:
    rows = []
    for i, rec in enumerate(recordings, 1):
        hdr = motive_io.read_header(rec["path"])
        fname_date = re.search(r"(20\d\d-\d\d-\d\d)", rec["path"].name)
        capture = hdr.capture_start_time
        tokens = {motive_io.segment_token(b) for b in hdr.bone_names}
        has_spine_chain = "Spine2" in tokens
        has_neck2 = "Neck2" in tokens
        row = {
            "participant": rec["participant"],
            "timepoint": rec["timepoint"],
            "repetition": rec["repetition"],
            "recording_id": f"{rec['participant']}_T{rec['timepoint']}_P1_R{rec['repetition']}",
            "capture_start_time": capture,
            "capture_date": capture.date().isoformat(),
            "filename_date": fname_date.group(1) if fname_date else None,
            "filename_date_matches": (
                fname_date.group(1) == capture.date().isoformat() if fname_date else None
            ),
            "length_units": hdr.length_units,
            "units_as_expected": hdr.length_units == expected_units,
            "capture_frame_rate": hdr.capture_frame_rate,
            "total_frames_in_take": hdr.total_frames,
            "n_bones": len(hdr.bone_names),
            "root_bone": hdr.root_bone(),
            "has_spine_chain": has_spine_chain,
            "has_neck2": has_neck2,
            "skeleton_variant": "55bone_extended" if has_spine_chain else "51bone_basic",
            "source_file": rec["path"].name,
            "source_path": str(rec["path"]),
        }
        if checksums:
            print(f"  [{i:2d}/{len(recordings)}] sha256 {rec['path'].name[:48]}")
            row["sha256"] = provenance.sha256_file(rec["path"])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["participant", "timepoint", "repetition"]
    ).reset_index(drop=True)


def check_longitudinal_ordering(reg: pd.DataFrame) -> list[dict]:
    """Assert T1 < T2 < T3 by embedded capture time, per participant."""
    findings = []
    for pid, g in reg.groupby("participant"):
        first = g[g.repetition == 1].set_index("timepoint")["capture_start_time"]
        times = {t: first.get(t) for t in (1, 2, 3)}
        ordered = times[1] < times[2] < times[3]
        findings.append(
            {
                "participant": pid,
                "T1": times[1], "T2": times[2], "T3": times[3],
                "monotonic": bool(ordered),
                "t1_to_t2_days": (times[2] - times[1]).days,
                "t2_to_t3_days": (times[3] - times[2]).days,
                "t1_to_t3_days": (times[3] - times[1]).days,
            }
        )
    return findings


def check_repetition_sessions(reg: pd.DataFrame) -> list[dict]:
    """R1 and R2 must share a session; this is what makes the reference
    'within-session repetition variability' rather than a noise floor."""
    out = []
    for (pid, tp), g in reg.groupby(["participant", "timepoint"]):
        s = g.set_index("repetition")["capture_start_time"]
        gap_min = (s[2] - s[1]).total_seconds() / 60.0
        out.append(
            {
                "participant": pid, "timepoint": tp,
                "gap_minutes": round(gap_min, 1),
                "same_day": s[1].date() == s[2].date(),
            }
        )
    return out


def check_skeleton_topology(reg: pd.DataFrame) -> list[dict]:
    """Detect skeleton-template changes across timepoints within a participant.

    This is a confound of the first order: the Motive solved-skeleton template
    is not constant across the study. Where it changes between timepoints, any
    fixed per-participant link map silently changes meaning at exactly the
    contrast the study measures. The 18-link endpoint-relative space used here
    is invariant to it, which is the reason that design was chosen.
    """
    out = []
    for pid, g in reg.groupby("participant"):
        by_tp = g.groupby("timepoint")["skeleton_variant"].agg(lambda s: sorted(set(s)))
        variants = {int(t): v for t, v in by_tp.items()}
        distinct = {v for vs in variants.values() for v in vs}
        out.append(
            {
                "participant": pid,
                "variant_by_timepoint": {t: v[0] if len(v) == 1 else v for t, v in variants.items()},
                "changes_within_participant": len(distinct) > 1,
                "root_bone_names": sorted(set(g["root_bone"])),
            }
        )
    return out


def shared_sessions(reg: pd.DataFrame) -> list[dict]:
    out = []
    for date, g in reg.groupby("capture_date"):
        members = sorted({(r.participant, r.timepoint) for r in g.itertuples()})
        if len({m[0] for m in members}) > 1:
            out.append({"date": date, "members": [f"{p}-T{t}" for p, t in members]})
    return out


def copy_reference_tables(source: Path, out_dir: Path) -> list[dict]:
    """Copy the canonical link map and rename manifests to true link counts."""
    copied = []
    link_map = source / "data/link_mapping/canonical_link_map.csv"
    if link_map.exists():
        dest = out_dir / "canonical_link_map.csv"
        dest.write_bytes(link_map.read_bytes())
        copied.append({"source": str(link_map), "dest": dest.name,
                       "sha256": provenance.sha256_file(dest)})

    man_dir = source / "data/feature_manifests"
    for path in sorted(man_dir.glob("group4_core_*link_within_*_feature_manifest.csv")):
        df = pd.read_csv(path)
        n_links = df["canonical_link_name"].nunique() if "canonical_link_name" in df else len(df) // 3
        stated = re.search(r"_(\d+)link_", path.name)
        stated_n = int(stated.group(1)) if stated else None
        pid = re.search(r"within_(\d+)_", path.name)
        dest = out_dir / f"manifest_{pid.group(1)}_{n_links}link.csv"
        dest.write_bytes(path.read_bytes())
        copied.append(
            {
                "source": str(path), "dest": dest.name,
                "stated_link_count": stated_n, "actual_link_count": int(n_links),
                "filename_was_misleading": stated_n != n_links,
                "sha256": provenance.sha256_file(dest),
            }
        )
    return copied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-project", default="../gaga_jcvpca")
    ap.add_argument("--no-checksums", action="store_true",
                    help="skip SHA-256 of the 5.1 GB source CSVs (dev only)")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    source = (ROOT / args.source_project).resolve()
    out_dir = ROOT / "data/immutable"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"source project : {source}")
    print(f"output         : {out_dir}\n")

    print("== discovering recordings ==")
    recordings = discover_recordings(source / "data/raw_skeleton")
    print(f"found {len(recordings)} raw CSVs")
    expected = 4 * 3 * 2
    if len(recordings) != expected:
        print(f"  ! expected {expected}")

    print("\n== reading Motive headers ==")
    reg = build_registry(recordings, cfg["capture"]["expected_length_units"],
                         checksums=not args.no_checksums)

    ordering = check_longitudinal_ordering(reg)
    rep_sessions = check_repetition_sessions(reg)
    shared = shared_sessions(reg)
    topology = check_skeleton_topology(reg)

    print("\n== longitudinal ordering (embedded capture time) ==")
    for f in ordering:
        flag = "" if f["monotonic"] else "   <== NOT MONOTONIC"
        print(f"  {f['participant']}  T1->T2 {f['t1_to_t2_days']:2d}d | "
              f"T2->T3 {f['t2_to_t3_days']:2d}d | T1->T3 {f['t1_to_t3_days']:2d}d{flag}")

    bad_names = reg[~reg.filename_date_matches.astype(bool)]
    print(f"\n== filename vs embedded date: {len(bad_names)} mismatch(es) ==")
    for r in bad_names.itertuples():
        print(f"  {r.recording_id}: filename {r.filename_date} -> actual {r.capture_date}")

    bad_units = reg[~reg.units_as_expected]
    print(f"\n== length units: {len(bad_units)} deviation(s) ==")
    for r in bad_units.itertuples():
        print(f"  {r.recording_id}: {r.length_units}")

    print("\n== skeleton template by timepoint ==")
    for t in topology:
        v = t["variant_by_timepoint"]
        flag = "   <== CHANGES MID-STUDY" if t["changes_within_participant"] else ""
        print(f"  {t['participant']}  T1 {v[1]} | T2 {v[2]} | T3 {v[3]}{flag}")

    print("\n== shared sessions across participants ==")
    for s in shared:
        print(f"  {s['date']}: {', '.join(s['members'])}")
    if not shared:
        print("  none")

    print("\n== segmentation ==")
    seg, issues, repairs = segmentation.build_segmentation(
        source / "data/segmentation",
        cfg["participants"],
        cfg["exercises"]["training"],
        cfg["capture"]["frame_rate_hz"],
    )
    print(f"  {len(seg)} exercise blocks across "
          f"{seg.groupby(['participant','timepoint','repetition']).ngroups} recordings")
    print(f"  {len(issues)} unmarked-boundary rows; {len(repairs)} repaired by merge")
    for r in repairs:
        print(f"    merged {r['participant']} T{r['timepoint']} R{r['repetition']} "
              f"ex{r['merged_exercises'][0]:02d}+ex{r['merged_exercises'][1]:02d}")

    train = cfg["exercises"]["training"]
    ev = cfg["exercises"]["evaluation"]
    cov = (
        seg[seg.exercise_id.isin(ev)]
        .groupby(["participant", "timepoint", "repetition"]).size()
        .rename("n_eval_blocks").reset_index()
    )
    print(f"\n  evaluation (ex09-13) blocks per recording: "
          f"min {cov.n_eval_blocks.min()}, max {cov.n_eval_blocks.max()} of {len(ev)}")
    tr = seg[seg.exercise_id.isin(train)]
    for rep in (1, 2):
        pool = tr[(tr.timepoint == 1) & (tr.repetition == rep)]
        print(f"  fold {'AB'[rep-1]} training pool (T1-R{rep}, ex01-15): "
              f"{pool.duration_s.sum():.0f} s over {len(pool)} blocks")

    print("\n== copying reference tables ==")
    copied = copy_reference_tables(source, out_dir)
    for c in copied:
        note = ""
        if c.get("filename_was_misleading"):
            note = f"   (renamed: stated {c['stated_link_count']}, actual {c['actual_link_count']})"
        print(f"  {c['dest']}{note}")

    reg.to_csv(out_dir / "recording_registry.csv", index=False)
    seg.to_csv(out_dir / "segmentation_normalized.csv", index=False)
    pd.DataFrame(issues).to_csv(out_dir / "segmentation_issues.csv", index=False)

    provenance.write_json(
        out_dir / "INPUT_MANIFEST.json",
        {
            **provenance.run_stamp("S1_ingest"),
            "source_project": str(source),
            "source_git_commit": provenance.git_commit(source),
            "checksums_computed": not args.no_checksums,
            "n_recordings": len(reg),
            "recordings": reg.to_dict(orient="records"),
            "longitudinal_ordering": ordering,
            "repetition_sessions": rep_sessions,
            "skeleton_topology": topology,
            "shared_sessions": shared,
            "reference_tables": copied,
            "segmentation": {
                "n_blocks": int(len(seg)),
                "unmarked_boundary_rows": len(issues),
                "repairs": repairs,
                "end_frame_convention": "exclusive",
            },
        },
    )

    print(f"\nwrote {out_dir/'recording_registry.csv'}")
    print(f"wrote {out_dir/'segmentation_normalized.csv'}")
    print(f"wrote {out_dir/'INPUT_MANIFEST.json'}")

    blocking = []
    if not all(f["monotonic"] for f in ordering):
        blocking.append("non-monotonic timepoint ordering")
    if len(reg) != expected:
        blocking.append(f"expected {expected} recordings, found {len(reg)}")
    if cov.n_eval_blocks.min() < len(ev):
        blocking.append("incomplete evaluation-exercise coverage")
    print("\nS1 " + ("BLOCKED: " + "; ".join(blocking) if blocking else "OK"))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
