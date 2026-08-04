#!/usr/bin/env python3
"""Stage 2 analysis: longitudinal, R1/R2, duration, amplitude, novelty vs Conv/explicit."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import _bootstrap  # noqa: F401
from rqa_pilot.paths import REPO_ROOT, ensure_rqa_dirs, rqa_path

CORE = ["DET", "LAM", "Lmean", "ENTR", "RR"]
STRUCT = ["DET", "LAM", "Lmean", "ENTR"]


def _drep(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["setting", "participant", "timepoint", "exercise_id", "region", "normalization"]
    for key, sub in df.groupby(keys):
        if set(sub.repetition) != {1, 2}:
            continue
        a, b = sub[sub.repetition == 1].iloc[0], sub[sub.repetition == 2].iloc[0]
        row = dict(zip(keys, key))
        for m in CORE:
            row[f"Drep_{m}"] = abs(a[m] - b[m])
            row[f"mean_{m}"] = 0.5 * (a[m] + b[m])
            row[f"{m}_R1"] = a[m]
            row[f"{m}_R2"] = b[m]
        row["duration_s"] = 0.5 * (a.duration_s + b.duration_s)
        row["N_embed"] = 0.5 * (a.N_embed + b.N_embed)
        rows.append(row)
    return pd.DataFrame(rows)


def _longitudinal(prim: pd.DataFrame, drep: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (pid, ex, region, norm, setting), sub in prim.groupby(
        ["participant", "exercise_id", "region", "normalization", "setting"]
    ):
        for rep in (1, 2):
            s = sub[sub.repetition == rep]
            tps = set(s.timepoint)
            if not {1, 2, 3}.issubset(tps):
                continue
            vals = {tp: s[s.timepoint == tp].iloc[0] for tp in (1, 2, 3)}
            dmap = {}
            for tp in (1, 2, 3):
                dd = drep[
                    (drep.participant == pid)
                    & (drep.exercise_id == ex)
                    & (drep.region == region)
                    & (drep.normalization == norm)
                    & (drep.setting == setting)
                    & (drep.timepoint == tp)
                ]
                if dd.empty:
                    dmap = None
                    break
                dmap[tp] = dd.iloc[0]
            if dmap is None:
                continue
            for name, ta, tb in (("D12", 1, 2), ("D13", 1, 3), ("D23", 2, 3)):
                row = {
                    "delta": name,
                    "participant": pid,
                    "exercise_id": ex,
                    "region": region,
                    "normalization": norm,
                    "setting": setting,
                    "repetition": rep,
                    "duration_s_a": vals[ta].duration_s,
                    "duration_s_b": vals[tb].duration_s,
                    "N_embed_a": vals[ta].N_embed,
                    "N_embed_b": vals[tb].N_embed,
                }
                for m in CORE:
                    delta = abs(vals[tb][m] - vals[ta][m])
                    drep_m = max(dmap[ta][f"Drep_{m}"], dmap[tb][f"Drep_{m}"])
                    row[f"abs_delta_{m}"] = delta
                    row[f"Drep_max_{m}"] = drep_m
                    row[f"ratio_{m}"] = delta / drep_m if drep_m > 1e-12 else np.nan
                    row[f"{m}_a"] = vals[ta][m]
                    row[f"{m}_b"] = vals[tb][m]
                rows.append(row)
    return pd.DataFrame(rows)


def _load_conv_exercise() -> pd.DataFrame:
    path = REPO_ROOT / "outputs/stage0b_guided_closeout/exercise_level_change.csv"
    df = pd.read_csv(path)
    df = df[df.participant.isin([651, 790]) & df.exercise_id.isin([11, 13]) & df.reliable]
    # aggregate across fold/seed
    g = (
        df.groupby(["participant", "delta", "exercise_id"], as_index=False)
        .agg(
            conv_ratio=("ratio_vs_drep_max", "median"),
            conv_exceed_frac=("exceeds_drep_max", "mean"),
            conv_norm_delta=("norm_delta", "median"),
        )
    )
    g["participant"] = g["participant"].astype(str)
    return g


def _load_explicit() -> pd.DataFrame:
    path = REPO_ROOT / "outputs/stage0b_individual_profiles/recording_feature_changes.csv"
    df = pd.read_csv(path)
    df = df[df.participant.isin([651, 790])]
    # recording-level features; map delta names
    keep = [
        "total_energy_deg2_s2",
        "participation_entropy_bits",
        "effective_dimensionality",
        "lr_symmetry",
        "regional_coupling",
        "trunk_arm_lagged_coupling",
        "participation_entropy_bits_amp_residual",
        "effective_dimensionality_amp_residual",
        "regional_coupling_amp_residual",
        "trunk_arm_lagged_coupling_amp_residual",
    ]
    df = df[df.feature.isin(keep) & (df.level == "recording")]
    g = (
        df.groupby(["participant", "delta", "feature"], as_index=False)
        .agg(feat_ratio=("ratio_vs_drep_max", "median"), feat_exceed=("exceeds_drep_max", "mean"), feat_abs_delta=("abs_delta", "median"))
    )
    g["participant"] = g["participant"].astype(str)
    return g


def _energy_series_proxy(metrics: pd.DataFrame) -> pd.DataFrame:
    """Proxy amplitude from mean of amp-preserving regional intensity (mean signal energy ~ RR-adjacent).
    Use mean_distance * RR context is weak; instead use recording-level total energy from explicit if available.
    Here: within RQA table, use mean of amp-preserving series via n_samples-normalized Lmean is not energy.
    Load rotvec-independent: use explicit recording energy changes only in novelty.
    """
    return pd.DataFrame()


def classify_novelty(row, feat_map, conv_map) -> str:
    """Classify one longitudinal cell."""
    # stability
    ratios = [row[f"ratio_{m}"] for m in STRUCT]
    if not np.isfinite(ratios).any():
        return "NOT_INTERPRETABLE"
    # require at least one structure metric ratio>1 and amp+zscore agreement later
    best = np.nanmax(ratios)
    if best <= 1.0:
        return "UNSTABLE"
    # redundancy with energy/entropy if those also exceed
    key = (str(row.participant), row.delta)
    feats = feat_map.get(key, {})
    energy_hit = feats.get("total_energy_deg2_s2", {}).get("exceed", 0) >= 0.5
    entropy_hit = feats.get("participation_entropy_bits", {}).get("exceed", 0) >= 0.5
    # zscore persistence checked outside via paired rows
    if row.normalization == "amp_preserving" and energy_hit and row.get("ratio_DET", 0) <= 1.2:
        # weak structure beyond energy
        if not any(row[f"ratio_{m}"] > 1 for m in ("DET", "LAM", "Lmean") if m != "RR"):
            return "REDUNDANT_WITH_EXISTING_FEATURES"
    if best > 1 and row.normalization == "trial_zscore":
        return "NOVEL_TEMPORAL_INFORMATION"
    if best > 1 and row.normalization == "amp_preserving":
        conv = conv_map.get((str(row.participant), row.delta, int(row.exercise_id)), {})
        if conv.get("exceed_frac", 0) >= 0.5:
            return "COMPLEMENTARY_INTERPRETATION"
        return "COMPLEMENTARY_INTERPRETATION"
    return "UNSTABLE"


def main() -> None:
    ensure_rqa_dirs()
    df = pd.read_csv(rqa_path("outputs", "stage2", "auto_rqa_metrics.csv"))
    prim = df[df.setting.isin(["primary_amp_preserving", "primary_trial_zscore"])].copy()
    drep = _drep(prim)
    drep.to_csv(rqa_path("outputs", "stage2", "r1r2_drep.csv"), index=False)
    longi = _longitudinal(prim, drep)
    longi.to_csv(rqa_path("outputs", "stage2", "longitudinal_deltas.csv"), index=False)

    # Surrogate drops on amp-preserving
    id_df = df[(df.setting == "primary_amp_preserving")]
    sh = df[df.setting == "surr_full_shuffle"]
    blk = df[df.setting == "surr_block_shuffle"]
    keys = ["participant", "timepoint", "repetition", "exercise_id", "region"]
    surr = id_df.merge(sh[keys + STRUCT], on=keys, suffixes=("", "_shuf"))
    surr = surr.merge(blk[keys + STRUCT], on=keys, suffixes=("", "_blk"))
    for m in STRUCT:
        surr[f"drop_{m}_shuf"] = surr[m] - surr[f"{m}_shuf"]
        surr[f"drop_{m}_blk"] = surr[m] - surr[f"{m}_blk"]
    surr.to_csv(rqa_path("outputs", "stage2", "surrogate_drops.csv"), index=False)

    # Truncation
    tr = df[df.setting == "trunc_amp_preserving"]
    trunc = id_df.merge(tr[keys + STRUCT], on=keys, suffixes=("", "_trunc"))
    for m in STRUCT:
        trunc[f"delta_trunc_{m}"] = trunc[f"{m}_trunc"] - trunc[m]
    trunc.to_csv(rqa_path("outputs", "stage2", "truncation_sensitivity.csv"), index=False)

    # Sensitivity: tau/radius/lmin vs primary
    sens_rows = []
    for setting in df.setting.unique():
        if setting in ("primary_amp_preserving", "primary_trial_zscore", "surr_full_shuffle", "surr_block_shuffle", "trunc_amp_preserving"):
            continue
        alt = df[df.setting == setting]
        mrg = id_df.merge(alt[keys + ["DET", "LAM", "Lmean"]], on=keys, suffixes=("", "_alt"))
        if mrg.empty:
            continue
        sens_rows.append(
            {
                "setting": setting,
                "median_abs_dDET": float((mrg.DET - mrg.DET_alt).abs().median()),
                "median_abs_dLAM": float((mrg.LAM - mrg.LAM_alt).abs().median()),
                "median_abs_dLmean": float((mrg.Lmean - mrg.Lmean_alt).abs().median()),
                "sign_agree_DET_frac": float(np.mean(np.sign(mrg.DET) == np.sign(mrg.DET_alt))),
            }
        )
    pd.DataFrame(sens_rows).to_csv(rqa_path("outputs", "stage2", "sensitivity_summary.csv"), index=False)

    # Amplitude control: compare ratios amp vs zscore for matched cells
    amp = longi[longi.normalization == "amp_preserving"]
    zsc = longi[longi.normalization == "trial_zscore"]
    amp_ctrl = amp.merge(
        zsc,
        on=["delta", "participant", "exercise_id", "region", "repetition"],
        suffixes=("_amp", "_z"),
    )
    amp_ctrl.to_csv(rqa_path("outputs", "stage2", "amplitude_control_pairs.csv"), index=False)

    # Comparison with Conv / explicit
    conv = _load_conv_exercise()
    feat = _load_explicit()
    conv_map = {
        (str(r.participant), r.delta, int(r.exercise_id)): {
            "ratio": r.conv_ratio,
            "exceed_frac": r.conv_exceed_frac,
        }
        for r in conv.itertuples(index=False)
    }
    feat_map = {}
    for r in feat.itertuples(index=False):
        feat_map.setdefault((str(r.participant), r.delta), {})[r.feature] = {
            "ratio": r.feat_ratio,
            "exceed": r.feat_exceed,
        }

    # Aggregate RQA exercise-level: mean ratio across regions/reps for DET
    agg_rows = []
    for (pid, ex, delta, norm), sub in longi.groupby(["participant", "exercise_id", "delta", "normalization"]):
        row = {
            "participant": pid,
            "exercise_id": ex,
            "delta": delta,
            "normalization": norm,
            "median_ratio_DET": float(sub.ratio_DET.median()),
            "median_ratio_LAM": float(sub.ratio_LAM.median()),
            "median_ratio_Lmean": float(sub.ratio_Lmean.median()),
            "median_ratio_ENTR": float(sub.ratio_ENTR.median()),
            "frac_ratio_DET_gt1": float((sub.ratio_DET > 1).mean()),
            "frac_ratio_LAM_gt1": float((sub.ratio_LAM > 1).mean()),
            "n": int(len(sub)),
        }
        c = conv_map.get((pid, delta, int(ex)), {})
        row["conv_ratio"] = c.get("ratio", np.nan)
        row["conv_exceed_frac"] = c.get("exceed_frac", np.nan)
        f = feat_map.get((pid, delta), {})
        for name in (
            "total_energy_deg2_s2",
            "participation_entropy_bits",
            "effective_dimensionality",
            "regional_coupling",
            "trunk_arm_lagged_coupling",
            "participation_entropy_bits_amp_residual",
            "effective_dimensionality_amp_residual",
        ):
            row[f"feat_exceed_{name}"] = f.get(name, {}).get("exceed", np.nan)
            row[f"feat_ratio_{name}"] = f.get(name, {}).get("ratio", np.nan)
        # novelty classification at exercise level — based on THIS normalization row
        z_sub = longi[
            (longi.participant == pid)
            & (longi.exercise_id == ex)
            & (longi.delta == delta)
            & (longi.normalization == "trial_zscore")
        ]
        amp_sub = longi[
            (longi.participant == pid)
            & (longi.exercise_id == ex)
            & (longi.delta == delta)
            & (longi.normalization == "amp_preserving")
        ]
        # Require central tendency (median ratio) > 1 for a structure metric — not only a 50% cell fraction.
        this_hit = (
            row["median_ratio_DET"] > 1.0
            or row["median_ratio_LAM"] > 1.0
            or row["median_ratio_Lmean"] > 1.0
        )
        z_hit = (
            float(z_sub.ratio_DET.median()) > 1.0
            or float(z_sub.ratio_LAM.median()) > 1.0
            or float(z_sub.ratio_Lmean.median()) > 1.0
        ) if len(z_sub) else False
        amp_hit = (
            float(amp_sub.ratio_DET.median()) > 1.0
            or float(amp_sub.ratio_LAM.median()) > 1.0
            or float(amp_sub.ratio_Lmean.median()) > 1.0
        ) if len(amp_sub) else False
        energy_hit = float(row.get("feat_exceed_total_energy_deg2_s2") or 0) >= 0.5
        ent_res = float(row.get("feat_exceed_participation_entropy_bits_amp_residual") or 0) >= 0.5
        if not this_hit:
            nov = "UNSTABLE"
        elif norm == "trial_zscore":
            # z-score persistence is the novelty gate for amplitude control
            nov = "NOVEL_TEMPORAL_INFORMATION" if not energy_hit else "COMPLEMENTARY_INTERPRETATION"
        else:
            # amp-preserving row
            if energy_hit and not z_hit:
                nov = "REDUNDANT_WITH_EXISTING_FEATURES"
            elif z_hit and not energy_hit:
                nov = "NOVEL_TEMPORAL_INFORMATION"
            elif z_hit and energy_hit:
                nov = "COMPLEMENTARY_INTERPRETATION"
            else:
                # amp hit but no z-score support
                nov = "COMPLEMENTARY_INTERPRETATION" if not energy_hit else "REDUNDANT_WITH_EXISTING_FEATURES"
        # if only ENTR moves and structure metrics don't
        if nov != "UNSTABLE" and row["frac_ratio_DET_gt1"] < 0.3 and row["frac_ratio_LAM_gt1"] < 0.3 and row["median_ratio_Lmean"] <= 1:
            if row["median_ratio_ENTR"] > 1:
                nov = "NOT_INTERPRETABLE"
        row["novelty_class"] = nov
        row["entropy_residual_exceed"] = ent_res
        row["zscore_support"] = bool(z_hit)
        row["amp_support"] = bool(amp_hit)
        agg_rows.append(row)
    agg = pd.DataFrame(agg_rows)
    agg.to_csv(rqa_path("outputs", "stage2", "exercise_level_comparison.csv"), index=False)

    # Gate summary JSON
    primary_long = longi[longi.normalization.isin(["amp_preserving", "trial_zscore"])]
    # qualified cases: pid×ex×delta with novelty novel or complementary on amp and z persistence
    # Qualified = pid×ex×delta with z-score support (novel or complementary) on D12/D13
    focus = agg[
        agg.delta.isin(["D12", "D13"])
        & (agg.normalization == "trial_zscore")
        & agg.novelty_class.isin(["NOVEL_TEMPORAL_INFORMATION", "COMPLEMENTARY_INTERPRETATION"])
    ]
    novel_z = agg[
        (agg.normalization == "trial_zscore")
        & (agg.novelty_class == "NOVEL_TEMPORAL_INFORMATION")
        & agg.delta.isin(["D12", "D13"])
    ]
    n_qualified = focus[["participant", "exercise_id", "delta"]].drop_duplicates().shape[0]

    surr_ok = float(surr.drop_DET_shuf.median()) > 0.5
    trunc_ok = float(trunc.delta_trunc_DET.abs().median()) < 0.2
    sens = pd.read_csv(rqa_path("outputs", "stage2", "sensitivity_summary.csv")) if Path(rqa_path("outputs", "stage2", "sensitivity_summary.csv")).exists() else pd.DataFrame()
    sens_ok = True if sens.empty else float(sens.median_abs_dDET.median()) < 0.15

    amp_comp = agg[
        agg.delta.isin(["D12", "D13"])
        & (agg.normalization == "amp_preserving")
        & agg.novelty_class.isin(["NOVEL_TEMPORAL_INFORMATION", "COMPLEMENTARY_INTERPRETATION"])
    ]
    n_amp_comp = amp_comp[["participant", "exercise_id", "delta"]].drop_duplicates().shape[0]

    # Decision: PASS requires multiple amplitude-controlled (z-score) qualified cases.
    # LIMITED: technical validity + some amp-preserving structure signals, but z-score novelty insufficient for Stage 3.
    if n_qualified >= 2 and surr_ok and trunc_ok and sens_ok and len(novel_z) >= 1:
        decision = "PASS_TO_STAGE3"
    elif surr_ok and trunc_ok and (n_qualified >= 1 or n_amp_comp >= 1):
        decision = "LIMITED_PASS_STOP"
    else:
        decision = "FAIL_STOP"

    gate = {
        "decision": decision,
        "n_qualified_pid_ex_delta_zscore": int(n_qualified),
        "n_amp_preserving_complementary_pid_ex_delta": int(n_amp_comp),
        "n_novel_zscore_rows": int(len(novel_z)),
        "surrogate_DET_drop_median": float(surr.drop_DET_shuf.median()),
        "surrogate_ok": surr_ok,
        "truncation_median_abs_dDET": float(trunc.delta_trunc_DET.abs().median()),
        "truncation_ok": trunc_ok,
        "sensitivity_median_abs_dDET": float(sens.median_abs_dDET.median()) if len(sens) else np.nan,
        "sensitivity_ok": sens_ok,
        "novelty_counts": agg.novelty_class.value_counts().to_dict(),
        "focus_table": focus.sort_values(["participant", "exercise_id", "delta"]).to_dict(orient="records"),
    }
    rqa_path("outputs", "stage2", "STAGE2_GATE.json").write_text(json.dumps(gate, indent=2))
    print(json.dumps({k: gate[k] for k in ("decision", "n_qualified_pid_ex_delta_zscore", "n_amp_preserving_complementary_pid_ex_delta", "n_novel_zscore_rows", "surrogate_ok", "truncation_ok", "sensitivity_ok")}, indent=2))


if __name__ == "__main__":
    main()
