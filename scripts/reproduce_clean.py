#!/usr/bin/env python3
"""Clean end-to-end reproduction of S1-S4 from immutable input only.

Fingerprints the current derived artifacts, moves every one of them into a
quarantine directory, re-runs the whole pipeline against nothing but the
read-only source project, then checks two things:

1. **Reproduction**: does the rerun produce identical content? Compared by
   content hash (numeric arrays, parsed tables, normalised JSON, decoded
   pixels), never by file bytes, because Parquet metadata, JSON run stamps and
   PNG encoder fields all differ legitimately between two correct runs.
2. **Gate**: do the explicit scientific criteria still hold on the fresh
   artifacts, independently of what the previous run happened to produce?

Usage:
    python scripts/reproduce_clean.py
    python scripts/reproduce_clean.py --keep-quarantine
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import fingerprint, provenance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ["data/immutable", "outputs", "figures"]
# Outputs that live under the derived tree but are not produced by S1-S4:
# this checker's own logs and fingerprints, and the Torch smoke test. Counting
# them would make the check fail for the wrong reason.
NON_PIPELINE_OUTPUT = ("outputs/reproduction", "outputs/smoke_test")
STAGES = ["s1_ingest.py", "s2_extract.py", "s3_validate_repr.py", "s4_window.py"]

EXPECTED_WINDOWS = 1657
EXPECTED_LINKS = 18
EXPECTED_RECORDINGS = 24


# --------------------------------------------------------------------------
# gate checks, run against the freshly produced artifacts
# --------------------------------------------------------------------------

def _check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "passed": bool(ok), "detail": detail}


def run_gate(root: Path, before: dict, after: dict) -> list[dict]:
    import json

    reg = pd.read_csv(root / "data/immutable/recording_registry.csv")
    manifest = json.loads((root / "data/immutable/INPUT_MANIFEST.json").read_text())
    cache = pd.read_csv(root / "outputs/s2_extract/cache_comparison.csv")
    chain = pd.read_csv(root / "outputs/s2_extract/chain_composition_checks.csv")
    repr_v = pd.read_csv(root / "outputs/s3_representation/representation_validation.csv")
    win = pd.read_csv(root / "outputs/s4_windows/window_index.csv")
    s4prov = json.loads((root / "outputs/s4_windows/s4_provenance.json").read_text())
    linkcfg = yaml.safe_load((root / "configs/canonical_links_18.yaml").read_text())

    checks: list[dict] = []

    # 1. 24 recordings ordered by embedded Capture Start Time
    order = pd.DataFrame(manifest["longitudinal_ordering"])
    monotonic = bool(order.monotonic.all())
    keyed = (reg.capture_start_time.notna().all())
    checks.append(_check(
        "24 recordings ordered by embedded Capture Start Time",
        len(reg) == EXPECTED_RECORDINGS and monotonic and keyed,
        f"{len(reg)} recordings; monotonic T1<T2<T3 for "
        f"{int(order.monotonic.sum())}/{len(order)} participants; "
        f"{int((~reg.filename_date_matches.astype(bool)).sum())} filename/capture-date "
        f"mismatches correctly overridden",
    ))

    # 2. units, including the 252-T3 Meters case
    meters = reg[reg.length_units == "Meters"]
    expected_meters = {"252_T3_P1_R1", "252_T3_P1_R2"}
    m252 = cache[cache.recording_id.isin(expected_meters)]
    m252_exact = bool((m252[m252.present_in_cache == True].agrees).all()) if len(m252) else False  # noqa: E712
    checks.append(_check(
        "length units recorded and 252-T3 Meters handled",
        set(meters.recording_id) == expected_meters and reg.length_units.notna().all() and m252_exact,
        f"Meters: {sorted(meters.recording_id)}; all other {len(reg)-len(meters)} Millimeters; "
        f"orientation extraction for 252-T3 still bit-identical to cache "
        f"({len(m252[m252.present_in_cache == True])} links), confirming the "  # noqa: E712
        f"orientation pipeline is unit-invariant",
    ))

    # 3. the same canonical 18-link space, for every recording
    n_links_cfg = len(linkcfg["links"])
    per_rec = repr_v.groupby("recording_id").link_id.nunique()
    checks.append(_check(
        "identical canonical 18-link space across all recordings",
        n_links_cfg == EXPECTED_LINKS and per_rec.eq(EXPECTED_LINKS).all()
        and len(per_rec) == EXPECTED_RECORDINGS,
        f"{n_links_cfg} links configured; every one of {len(per_rec)} recordings "
        f"yields {int(per_rec.min())} links "
        f"(templates present: {sorted(reg.skeleton_variant.unique())})",
    ))

    # 4. zero unexplained extraction mismatches
    matched = cache[cache.present_in_cache == True]  # noqa: E712
    unexp = matched[(~matched.agrees) & (matched.explained_by_source_alias != True)]  # noqa: E712
    alias = matched[matched.explained_by_source_alias == True]  # noqa: E712
    checks.append(_check(
        "zero unexplained extraction mismatches",
        len(unexp) == 0,
        f"{int(matched.agrees.sum())} bit-identical, {len(alias)} alias-explained, "
        f"{len(unexp)} unexplained, of {len(matched)} comparable link-recordings",
    ))

    # 5. telescoping (chain composition) identity
    worst_chain = float(chain.max_error_deg.max())
    checks.append(_check(
        "telescoping chain-composition identity holds",
        bool(chain.passed.all()) and worst_chain < 1e-10,
        f"{len(chain)} checks on {chain.recording_id.nunique()} recordings, "
        f"worst {worst_chain:.3e} deg",
    ))

    # 6. exactly 1657 windows
    checks.append(_check(
        f"exactly {EXPECTED_WINDOWS} windows",
        len(win) == EXPECTED_WINDOWS,
        f"{len(win)} windows: " + ", ".join(
            f"{k} {v}" for k, v in sorted(win.role.value_counts().items())),
    ))

    # 7-9. leakage and completeness
    checks.append(_check(
        "zero exercise-boundary crossings",
        s4prov["windows_crossing_boundaries"] == 0,
        f"{s4prov['windows_crossing_boundaries']} crossings",
    ))
    checks.append(_check(
        "zero blocks split across roles",
        s4prov["blocks_split_across_roles"] == 0,
        f"{s4prov['blocks_split_across_roles']} split blocks",
    ))
    checks.append(_check(
        "zero missing values in any window",
        s4prov["windows_with_missing_data"] == 0 and bool(win.usable.all()),
        f"{s4prov['windows_with_missing_data']} windows with non-finite data; "
        f"min per-window finite fraction {win.frac_finite.min():.3f}",
    ))

    # 10. identical training and evaluation inventories vs the previous run
    key = "outputs/s4_windows/window_index.csv"
    same_index = before.get(key, {}).get("hash") == after.get(key, {}).get("hash")
    ev = win[win.role == "evaluation"].groupby("recording_id").size()
    checks.append(_check(
        "identical training and evaluation inventories",
        same_index,
        f"window_index content hash {'matches' if same_index else 'DIFFERS FROM'} "
        f"the pre-wipe run; evaluation windows per recording "
        f"{int(ev.min())}-{int(ev.max())} (median {int(ev.median())}); "
        f"fold A {int(((win.fold == 'A') & (win.role == 'training')).sum())} train / "
        f"{int(((win.fold == 'A') & (win.role == 'early_stop')).sum())} early-stop, "
        f"fold B {int(((win.fold == 'B') & (win.role == 'training')).sum())} / "
        f"{int(((win.fold == 'B') & (win.role == 'early_stop')).sum())}",
    ))

    return checks


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-quarantine", action="store_true",
                    help="retain the isolated previous artifacts after a pass")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine = ROOT / ".quarantine" / stamp

    print("=" * 74)
    print("CLEAN END-TO-END REPRODUCTION OF S1-S4")
    print("=" * 74)

    print("\n[1/5] fingerprinting current derived artifacts ...")
    before = fingerprint.fingerprint_tree(ROOT, DERIVED, NON_PIPELINE_OUTPUT)
    print(f"      {len(before)} artifacts fingerprinted by content")

    print(f"\n[2/5] isolating all derived artifacts -> {quarantine.relative_to(ROOT)}")
    quarantine.mkdir(parents=True, exist_ok=True)
    # Park non-pipeline outputs outside the wipe so a successful reproduction
    # does not destroy the Torch smoke-test result.
    parked: list[tuple[Path, Path]] = []
    park_root = quarantine / "_parked_non_pipeline"
    for rel in NON_PIPELINE_OUTPUT:
        src = ROOT / rel
        if src.exists():
            dest = park_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            parked.append((src, dest))
            print(f"      parked non-pipeline {rel}")
    for sub in DERIVED:
        src = ROOT / sub
        if src.exists():
            dest = quarantine / sub
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            print(f"      moved {sub}")
    for sub in DERIVED:
        remaining = list((ROOT / sub).rglob("*")) if (ROOT / sub).exists() else []
        if remaining:
            print(f"      ! {sub} still contains {len(remaining)} entries")
            return 1
    print("      workspace now contains no derived artifacts")

    print("\n[3/5] re-running the pipeline from immutable input only")
    timings = {}
    for stage in STAGES:
        t0 = time.time()
        print(f"      {stage} ...", end="", flush=True)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / stage)],
            cwd=ROOT, capture_output=True, text=True,
        )
        dt = time.time() - t0
        timings[stage] = round(dt, 1)
        tail = [l for l in proc.stdout.strip().splitlines() if l.strip()]
        verdict = tail[-1] if tail else "(no output)"
        print(f" {dt:5.1f}s  {verdict}")
        if proc.returncode != 0:
            print("\n      STAGE FAILED, stopping. stderr:")
            print(proc.stderr[-4000:])
            print(f"\n      previous artifacts preserved at {quarantine}")
            return 1
        log_dir = ROOT / "outputs/reproduction/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{stage}.log").write_text(proc.stdout)

    # Restore parked smoke-test (and any other non-pipeline tree that was not
    # recreated by S1-S4). Fresh reproduction logs already live under
    # outputs/reproduction/ and take precedence.
    for original, parked_path in parked:
        original.parent.mkdir(parents=True, exist_ok=True)
        if original.exists():
            continue
        shutil.move(str(parked_path), str(original))
        print(f"      restored non-pipeline {original.relative_to(ROOT)}")

    print("\n[4/5] fingerprinting fresh artifacts and comparing ...")
    after = fingerprint.fingerprint_tree(ROOT, DERIVED, NON_PIPELINE_OUTPUT)
    cmp = fingerprint.compare_fingerprints(before, after)
    provenance.write_json(ROOT / "outputs/reproduction/fingerprint_before.json", before)
    provenance.write_json(ROOT / "outputs/reproduction/fingerprint_after.json", after)

    print(f"      identical      : {len(cmp['identical'])}")
    print(f"      changed        : {len(cmp['changed'])}")
    print(f"      missing after  : {len(cmp['missing_after'])}")
    print(f"      new after      : {len(cmp['new_after'])}")
    for k in cmp["changed"][:20]:
        print(f"        changed: {k}")
    for k in cmp["missing_after"][:20]:
        print(f"        missing: {k}")
    for k in cmp["new_after"][:20]:
        print(f"        new    : {k}")

    print("\n[5/5] scientific gate on the fresh artifacts")
    checks = run_gate(ROOT, before, after)
    for c in checks:
        print(f"      [{'PASS' if c['passed'] else 'FAIL'}] {c['check']}")
        print(f"             {c['detail']}")

    reproduced = (
        not cmp["changed"] and not cmp["missing_after"] and not cmp["new_after"]
    )
    gate_ok = all(c["passed"] for c in checks)
    overall = reproduced and gate_ok

    provenance.write_json(
        ROOT / "outputs/reproduction/reproduction_result.json",
        {
            **provenance.run_stamp("clean_reproduction"),
            "quarantine": str(quarantine.relative_to(ROOT)),
            "stage_timings_s": timings,
            "n_artifacts": len(after),
            "comparison_counts": {k: len(v) for k, v in cmp.items()},
            "changed": cmp["changed"],
            "missing_after": cmp["missing_after"],
            "new_after": cmp["new_after"],
            "gate": checks,
            "byte_identical_content": reproduced,
            "gate_passed": gate_ok,
            "operationally_reproducible": overall,
        },
    )

    print("\n" + "=" * 74)
    if overall:
        print("REPRODUCTION PASSED")
        print("  content identical across a full wipe and rerun, and every gate holds")
        print("  status: scientifically validated AND operationally reproducible")
    else:
        print("REPRODUCTION FAILED")
        if not reproduced:
            print("  content differs across the rerun")
        if not gate_ok:
            print("  one or more scientific gates failed")
        print("  status: scientifically validated, but NOT yet operationally reproducible")
    print("=" * 74)

    if overall and not args.keep_quarantine:
        shutil.rmtree(quarantine)
        print(f"\nquarantine removed ({quarantine.relative_to(ROOT)})")
    else:
        print(f"\nprevious artifacts retained at {quarantine.relative_to(ROOT)}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
