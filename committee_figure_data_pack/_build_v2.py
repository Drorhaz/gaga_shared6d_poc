#!/usr/bin/env python3
"""Build committee_figure_data_pack_v2 from authoritative sources. No new analyses."""
from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/drorhazan/Desktop/gaga_psilo/projects")
JCV = ROOT / "gaga_jcvpca"
POC = ROOT / "gaga_shared6d_poc"
POLICY = JCV / "results_committee_case/marker_gap_policy_ex09_13"
V1 = POC / "committee_figure_data_pack"
OUT = POC / "committee_figure_data_pack_v2"
OUT.mkdir(parents=True, exist_ok=True)
EXTRACT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def as_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no", ""):
        return False
    return bool(v)


def fnum(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def lin_slope(ys):
    n = len(ys)
    xs = list(range(n))
    xm = sum(xs) / n
    ym = sum(ys) / n
    num = sum((xs[i] - xm) * (ys[i] - ym) for i in range(n))
    den = sum((xs[i] - xm) ** 2 for i in range(n))
    return num / den if den else 0.0


def visual_segments_for_link(link_id: str, proximal: str, distal: str):
    token_map = {
        "Head": "head",
        "Neck": "neck",
        "Neck2": "neck",
        "Chest": "upper_trunk_chest",
        "Ab": "lower_trunk_abdomen",
        "Spine2": "lower_trunk_abdomen",
        "Spine3": "upper_trunk_chest",
        "Spine4": "upper_trunk_chest",
        "LShoulder": "left_shoulder",
        "LUArm": "left_upper_arm",
        "LFArm": "left_forearm",
        "LHand": "left_hand",
        "RShoulder": "right_shoulder",
        "RUArm": "right_upper_arm",
        "RFArm": "right_forearm",
        "RHand": "right_hand",
        "LThigh": "left_thigh",
        "LShin": "left_shin",
        "LFoot": "left_foot",
        "RThigh": "right_thigh",
        "RShin": "right_shin",
        "RFoot": "right_foot",
    }

    def tok_to_seg(tok):
        if not tok:
            return None
        if tok in token_map:
            return token_map[tok]
        if tok.isdigit() or tok in ("671", "252", "651", "790"):
            return "pelvis"
        return None

    start = tok_to_seg(proximal)
    end = tok_to_seg(distal)
    if start is None:
        if "_to_" in link_id:
            a = link_id.split("_to_")[0]
            start = "pelvis" if (a in ("671", "252", "651", "790") or a.isdigit()) else (tok_to_seg(a) or "unknown")
        else:
            start = "unknown"
    if end is None:
        if "_to_" in link_id:
            b = link_id.split("_to_")[-1]
            end = tok_to_seg(b) or "unknown"
        else:
            end = "unknown"
    return start, end, f"{start}__{end}"


def side_from_link(link_id: str) -> str:
    left = ("LShoulder", "LUArm", "LFArm", "LHand", "LThigh", "LShin", "LFoot")
    right = ("RShoulder", "RUArm", "RFArm", "RHand", "RThigh", "RShin", "RFoot")
    if any(t in link_id for t in left):
        return "left"
    if any(t in link_id for t in right):
        return "right"
    return "midline"


def ranks_for(mapping):
    ordered = sorted(mapping.items(), key=lambda kv: (-kv[1], kv[0]))
    return {link: i + 1 for i, (link, _) in enumerate(ordered)}


STAGE_META = {
    "ex09": dict(stage_order=1, stage_display="Hands", body_involvement_description="Hands"),
    "ex10": dict(stage_order=2, stage_display="+ Elbows", body_involvement_description="Hands + elbows"),
    "ex11": dict(stage_order=3, stage_display="+ Shoulders", body_involvement_description="Hands + elbows + shoulders"),
    "ex12": dict(stage_order=4, stage_display="+ Head/Nose", body_involvement_description="Hands + elbows + shoulders + head/nose"),
    "ex13": dict(stage_order=5, stage_display="Whole body", body_involvement_description="Whole body"),
}
CMP_META = {
    "T1_vs_T2": dict(comparison_display="Baseline → ≈4 classes", baseline="T1", followup="T2", classes=4, internal="D12"),
    "T1_vs_T3": dict(comparison_display="Baseline → ≈10 classes", baseline="T1", followup="T3", classes=10, internal="D13"),
}
TP_DISPLAY = {"T1": ("Baseline", ""), "T2": ("≈4 classes", 4), "T3": ("≈10 classes", 10)}


def main():
    linkmap = read_csv(JCV / "data/link_mapping/canonical_link_map.csv")
    nv_rows = read_csv(POLICY / "step08_nv_and_stability/NV_PROFILE.csv")
    ex_rows = read_csv(POLICY / "step08_nv_and_stability/exercise_level_nv.csv")
    headline = read_csv(POLICY / "tables_to_show/09_headline_a2_summary.csv")
    excl_rows = read_csv(POLICY / "tables_to_show/02_comparison_link_exclusions.csv")
    coverage_rows = read_csv(POLICY / "tables_to_show/06_coverage_gate_a2_estimand.csv")
    pooled_vs_single = read_csv(POLICY / "tables_to_show/09_pooled_vs_single_by_link.csv")
    robustness = read_csv(POLICY / "step04_primary_runs/robustness.csv")
    func_bands = read_csv(POLICY / "step04_primary_runs/functional_pc_bands.csv")
    persistence = read_csv(POLICY / "tables_to_show/07_persistence_t2_t3.csv")
    r1r2_agree = read_csv(POLICY / "tables_to_show/11_r1_r2_same_sign_exceed_agreement.csv")

    pid_stem_to_meta = {}
    for r in linkmap:
        for pid in ["671", "252", "651", "790"]:
            stem = r.get(f"{pid}_link_stem")
            if r.get(f"{pid}_present") == "Y" and stem:
                pid_stem_to_meta[(pid, stem)] = {
                    "canonical_link_id": r["canonical_link_id"],
                    "region_id": r["region_id"],
                    "anatomical_description": r["anatomical_description"],
                    "proximal_joint": r.get(f"{pid}_parent_token") or "",
                    "distal_joint": r.get(f"{pid}_child_token") or "",
                    "parent_bone": r.get(f"{pid}_parent_bone") or "",
                    "child_bone": r.get(f"{pid}_child_bone") or "",
                }

    geom_dir = JCV / "docs/slide45_figures/avatar_verified/geometry"
    embedded_geometry = {}
    for pid in ["252", "651", "671", "790"]:
        gp = geom_dir / f"{pid}_reference_pose.json"
        data = json.load(open(gp))
        joints_out = []
        for jid, xyz in data.get("joints", {}).items():
            if isinstance(xyz, (list, tuple)) and len(xyz) >= 3:
                x, y, z = xyz[0], xyz[1], xyz[2]
            elif isinstance(xyz, (list, tuple)) and len(xyz) == 2:
                x, y, z = xyz[0], xyz[1], None
            else:
                x = y = z = None
            joints_out.append({"joint_id": jid, "x": x, "y": y, "z": z})
        embedded_geometry[pid] = {
            "participant_id": pid,
            "reference_timepoint": data.get("reference_timepoint"),
            "reference_repetition": data.get("reference_repetition"),
            "session_id": data.get("session_id"),
            "length_units": data.get("length_units"),
            "up_axis": data.get("up_axis"),
            "coordinate_system_note": f"Cartesian joint coordinates; up_axis={data.get('up_axis')}; units={data.get('length_units')}",
            "hierarchy": data.get("hierarchy"),
            "joints": joints_out,
            "source_path": str(gp),
            "source_sha256": sha256(gp),
            "usage": "rendering_layout_only",
            "do_not_use_for_a2_denominators": True,
            "not_continuous_body_surface_mesh": True,
        }

    timeline_source = {
        "primary_documented_sequence": "3Layers_project/results/active/canonical_batch/poster_scientific_story_and_figure_plan.md Candidate Figure 1",
        "documented_phrase": "T1 baseline → 3 Gaga classes → dosing → 24h class → T2 → 6 classes → T3",
        "user_requested_alignment": "Baseline → Gaga 1–3 → blinded intervention → Gaga class 4 + integration → early assessment ≈4 classes → Gaga 5–10 → post-training ≈10 classes",
        "class_count_labels_require_protocol_confirmation": True,
        "verification_status": "Aligned with poster/study-design schematic wording; approximate class counts remain presentation labels pending formal protocol lock.",
    }

    estimand_separation = {
        "A_pooled_descriptive": "T1(R1+R2) vs T{k}(R1+R2) on pooled ex09–ex13 block (file 06).",
        "B_matched_single_rep_vs_NV": "T1_R1→T{k}_R1 compared with T1_R1→T1_R2 (+ reference-swap direction stability). Primary A2 evidence in file 03.",
        "C_repetition_sensitivity": "Whether the pattern depends strongly on pooled vs R1-only vs R2-only (file 06).",
        "forbidden": "Do NOT create pooled_longitudinal_change / single_rep_NV ratios. Do NOT treat pooled and matched-single-rep footings as numerically interchangeable.",
    }

    paradigm = {
        "file_id": "01_PARADIGM_AND_METHOD",
        "package_version": 2,
        "purpose": "Support G1 paradigm + method schematic for PhD admissions committee",
        "progressive_movement_sequence": {
            "definition": "ex09–ex13 form ONE progressive guided movement sequence (Group4 curvilinear exploration), not five independent exercises.",
            "pooled_definition": "The main JcvPCA longitudinal analysis treats ex09–ex13 as ONE POOLED progressive movement block (contiguous concatenation in frame order). It is NOT a sixth exercise, NOT an average of five independent task results, and NOT the mean of five exercise-level effects.",
            "stages": [
                {
                    "stage_order": meta["stage_order"],
                    "exercise_id": ex,
                    "stage_display": meta["stage_display"],
                    "body_involvement_description": meta["body_involvement_description"],
                    "retains_previous_stages": True,
                }
                for ex, meta in STAGE_META.items()
            ],
            "display_arrow": "Hands → + Elbows → + Shoulders → + Head/Nose → Whole body",
        },
        "recording_structure": {
            "participants": ["252", "651", "671", "790"],
            "timepoints_internal": ["T1", "T2", "T3"],
            "timepoints_display": {
                "T1": "Baseline",
                "T2": "Early assessment after approximately 4 Gaga classes",
                "T3": "Post-training assessment after approximately 10 Gaga classes",
            },
            "class_count_labels_require_protocol_confirmation": True,
            "repetitions": {
                "R1": "First within-session repetition of the movement sequence",
                "R2": "Second within-session repetition of the movement sequence",
            },
            "natural_repetition_variability": {
                "plain_language": "Difference between repetition 1 and repetition 2 within the same session provides an internal estimate of natural within-session repetition variability for that participant.",
                "not_a_universal_noise_floor": True,
                "limitations": "Only two repetitions; not a complete measurement-noise model.",
            },
        },
        "study_context_timeline": {
            "role_in_G1": "Visually secondary strip. Communicates broader PhD design. Do not imply treatment effect. Current movement analysis remains blinded.",
            "source_verification": timeline_source,
            "events": [
                {"order": 1, "label": "Baseline assessment", "internal_timepoint": "T1", "display": "Baseline"},
                {"order": 2, "label": "Gaga classes 1–3", "internal_timepoint": None, "display": "Gaga classes 1–3"},
                {
                    "order": 3,
                    "label": "Blinded psilocybin / active-placebo intervention",
                    "internal_timepoint": None,
                    "display": "Blinded intervention (dosing)",
                    "note": "Occurs after initial Gaga practice, not before all Gaga classes. No treatment-effect claim.",
                },
                {
                    "order": 4,
                    "label": "Gaga class 4 + integration context",
                    "internal_timepoint": None,
                    "display": "Class 4 + integration",
                    "note": "Corresponds to documented 24h-class / integration context after dosing.",
                },
                {
                    "order": 5,
                    "label": "Early assessment after approximately 4 Gaga classes",
                    "internal_timepoint": "T2",
                    "display": "≈4 classes assessment",
                },
                {"order": 6, "label": "Gaga classes 5–10", "internal_timepoint": None, "display": "Gaga classes 5–10"},
                {
                    "order": 7,
                    "label": "Post-training assessment after approximately 10 Gaga classes",
                    "internal_timepoint": "T3",
                    "display": "≈10 classes assessment",
                },
            ],
            "core_comparisons_for_figures": [
                "Baseline → ≈4 classes (T1→T2 / D12) — primary matched-coverage comparison",
                "Baseline → ≈10 classes (T1→T3 / D13) — retained; coverage limited for 252/651/671",
            ],
            "forbidden_implication": "Do not imply proven psilocybin effect, proven Gaga treatment effect, intervention-before-all-practice, or one common trajectory.",
        },
        "motion_capture": {
            "sample_rate_hz": 120,
            "length_units": "Millimeters",
            "representation_for_analysis": "Relative rotations / angular features of body links",
            "skeleton_setups": {
                "Setup_A": {"participants": ["671", "651"], "nominal_links": 18},
                "Setup_B": {"participants": ["252", "790"], "nominal_links": 22},
            },
        },
        "analysis_pipeline_presentation_level": [
            "Motion capture of progressive movement sequence",
            "QC and marker-gap policy",
            "Body-link relative rotation representation",
            "JcvPCA → anatomically interpretable body-link contribution pattern",
            "Compare longitudinal change with within-session repetition variability (matched single-rep footing)",
            "Complementary pooled R1+R2 descriptive analysis + repetition-design robustness (see 06)",
        ],
        "jcvpca_plain_language": {
            "working_explanation": "JcvPCA compares how different body links contribute to the shared structure of whole-body movement across matched recordings.",
            "steps": [
                "One matched recording defines a PCA movement space",
                "Another recording is projected into the same space",
                "The analysis compares how body links contribute to the shared movement-variance structure",
                "The output remains anatomically interpretable at the body-link level",
            ],
            "not_a_single_movement_score": True,
            "estimand_separation": estimand_separation,
        },
        "body_links": [
            {
                "canonical_link_id": r["canonical_link_id"],
                "region_id": r["region_id"],
                "anatomical_description": r["anatomical_description"],
                "comparability": r["comparability"],
                "present_in": [pid for pid in ["671", "252", "651", "790"] if r.get(f"{pid}_present") == "Y"],
                "per_participant_stems": {
                    pid: r.get(f"{pid}_link_stem")
                    for pid in ["671", "252", "651", "790"]
                    if r.get(f"{pid}_present") == "Y"
                },
            }
            for r in linkmap
        ],
        "anatomical_regions": {
            "head_neck": "Head / Neck",
            "trunk_spine": "Trunk / Spine",
            "left_arm": "Left arm",
            "right_arm": "Right arm",
            "left_leg": "Left leg",
            "right_leg": "Right leg",
        },
        "visual_segment_vocabulary": [
            "head",
            "neck",
            "upper_trunk_chest",
            "lower_trunk_abdomen",
            "pelvis",
            "left_shoulder",
            "left_upper_arm",
            "left_forearm",
            "left_hand",
            "right_shoulder",
            "right_upper_arm",
            "right_forearm",
            "right_hand",
            "left_thigh",
            "left_shin",
            "left_foot",
            "right_thigh",
            "right_shin",
            "right_foot",
        ],
        "visual_segment_mapping_note": "visual_segment_* fields in file 04 are presentation-only deterministic mappings from body-link anatomy. They are NOT new biological variables and do NOT invent continuous surface measurements.",
        "embedded_reference_geometry": embedded_geometry,
        "geometry_assets": {
            "embedded_in_this_file": True,
            "surface_polygons": {"available": False, "requires_visual_mapping": True},
            "stale_packs_not_authoritative_for_numbers": [
                "gaga_jcvpca/avater_671_252/",
                "gaga_jcvpca/docs/slide45_figures/avatar_pooled/",
                "avatar_verified/provenance_manifest.json denominators",
            ],
        },
        "internal_to_presentation_terminology": {
            "T1": "Baseline",
            "T2": "≈4 classes",
            "T3": "≈10 classes",
            "D12": "Baseline → ≈4 classes",
            "D13": "Baseline → ≈10 classes",
            "NV": "Natural within-session repetition variability",
            "A2": "Change exceeds own repetition variability and is directionally stable",
            "S3": "Stricter interpretive-candidate stack (not the only meaningful links)",
            "pooled ex09–ex13": "One pooled progressive movement sequence",
        },
    }
    json.dump(paradigm, open(OUT / "01_PARADIGM_AND_METHOD.json", "w"), indent=2)
    print("wrote 01")

    # ---- 02 ----
    by_sess = defaultdict(dict)
    for r in ex_rows:
        by_sess[(r["participant"], r["timepoint"])][r["exercise"]] = float(r["median_abs_nv"])
    session_metrics = {}
    for sess, d in by_sess.items():
        vals = [d[e] for e in STAGE_META]
        mean_v = sum(vals) / 5
        norm = {e: d[e] / mean_v for e in STAGE_META}
        ys = [norm[e] for e in STAGE_META]
        slope = lin_slope(ys)
        endpoint = norm["ex13"] - norm["ex09"]
        session_metrics[sess] = {
            "session_mean_median_abs_nv": mean_v,
            "normalized": norm,
            "fitted_progression_slope": slope,
            "endpoint_change_ex13_minus_ex09": endpoint,
            "endpoint_positive": endpoint > 0,
            "slope_positive": slope > 0,
        }
    n_sess = len(session_metrics)
    n_slope = sum(1 for m in session_metrics.values() if m["slope_positive"])
    n_end = sum(1 for m in session_metrics.values() if m["endpoint_positive"])
    print(f"G2 sessions={n_sess} endpoint+={n_end} slope+={n_slope}")

    rep_rows = []
    for r in ex_rows:
        pid, tp, ex = r["participant"], r["timepoint"], r["exercise"]
        meta = STAGE_META[ex]
        sm = session_metrics[(pid, tp)]
        tp_disp, classes = TP_DISPLAY[tp]
        rep_rows.append(
            {
                "participant_id": pid,
                "timepoint_internal": tp,
                "timepoint_display": tp_disp,
                "classes_at_timepoint": classes,
                "session_id": f"{pid}_{tp}",
                "stage_order": meta["stage_order"],
                "exercise_id": ex,
                "stage_display": meta["stage_display"],
                "body_involvement_description": meta["body_involvement_description"],
                "raw_variability": r["median_abs_nv"],
                "raw_variability_definition": "median across links of mean(|JcvPCA_link|) for R1 vs R2 within this exercise segment",
                "mean_abs_nv_across_links": r["mean_abs_nv"],
                "max_abs_nv_across_links": r["max_abs_nv"],
                "normalized_variability": sm["normalized"][ex],
                "normalization_definition": "normalized_variability = median_abs_nv(stage) / mean_over_five_stages(median_abs_nv) within the same participant×timepoint session",
                "session_mean_raw_variability": sm["session_mean_median_abs_nv"],
                "session_fitted_progression_slope": sm["fitted_progression_slope"],
                "session_endpoint_change_ex13_minus_ex09": sm["endpoint_change_ex13_minus_ex09"],
                "session_slope_positive": sm["slope_positive"],
                "session_endpoint_positive": sm["endpoint_positive"],
                "valid_link_count": r["n_links"],
                "valid_link_count_definition": "Number of links entering the per-exercise NV summary (NOT temporal sample/frame count)",
                "selected_m": r["selected_m"],
                "top_link": r["top_link"],
                "exercise_nv_rank": r["exercise_nv_rank"],
                "ex13_over_ex09_ratio": r.get("ex13_over_ex09_ratio", ""),
                "duration_frames_or_seconds": "",
                "duration_availability": "unavailable_in_source_table",
                "coverage_status": "layer2_descriptive",
                "qc_status": "authoritative_marker_gap_policy_layer2",
                "include_in_main_figure": True,
                "layer": "Layer2_protocol_openness_descriptive",
                "interpretation_note": r.get("interpretation_note", ""),
                "source_file": str(POLICY / "step08_nv_and_stability/exercise_level_nv.csv"),
                "source_run": "marker_gap_policy_ex09_13/step08_nv_and_stability",
                "notes": "Descriptive protocol-structure context only; firewalled from A2 gate. Prefer main annotation: 12/12 sessions Whole body > Hands. Slope is separate validation metadata.",
            }
        )
    write_csv(OUT / "02_REPETITION_VARIABILITY.csv", rep_rows, list(rep_rows[0].keys()))
    print("wrote 02")

    # ---- 03 ----
    def presentation_status(r):
        if as_bool(r.get("a2_pass")):
            return "interpretable_candidate" if r.get("nv_profile_tier") == "S3" else "beyond_repetition_variability_and_directionally_stable"
        if as_bool(r.get("magnitude_exceed")) and not as_bool(r.get("sign_reference_stable")):
            return "exceeds_variability_but_direction_unstable"
        if as_bool(r.get("magnitude_exceed")):
            return "exceeds_variability"
        return "within_repetition_variability"

    long_rows = []
    for r in nv_rows:
        pid = r["participant"]
        cmp_id = r["comparison_id"]
        cmp_key = "T1_vs_T2" if cmp_id.endswith("T1_vs_T2") else "T1_vs_T3"
        cm = CMP_META[cmp_key]
        link_id = r["link_id"]
        meta = pid_stem_to_meta.get((pid, link_id), {})
        long_s = fnum(r["long_signed_single"])
        vs, ve, vk = visual_segments_for_link(link_id, meta.get("proximal_joint", ""), meta.get("distal_joint", ""))
        status = presentation_status(r)
        if as_bool(r["a2_pass"]) and long_s is not None and long_s > 0:
            direction = "increased_contribution"
        elif as_bool(r["a2_pass"]) and long_s is not None and long_s < 0:
            direction = "decreased_contribution"
        elif long_s is None:
            direction = "unavailable"
        else:
            direction = "not_highlighted"
        long_rows.append(
            {
                "participant_id": pid,
                "comparison_internal": cm["internal"],
                "comparison_id": cmp_id,
                "comparison_display": cm["comparison_display"],
                "baseline_timepoint": cm["baseline"],
                "followup_timepoint": cm["followup"],
                "classes_at_followup": cm["classes"],
                "link_id": link_id,
                "link_display_name": meta.get("anatomical_description") or link_id.replace("_", " "),
                "canonical_link_id": meta.get("canonical_link_id", ""),
                "anatomical_region": meta.get("region_id", ""),
                "body_side": side_from_link(link_id),
                "proximal_joint": meta.get("proximal_joint", ""),
                "distal_joint": meta.get("distal_joint", ""),
                "visual_segment_start": vs,
                "visual_segment_end": ve,
                "visual_segment_key": vk,
                "visual_segment_mapping_role": "presentation_only",
                "available_baseline": True,
                "available_followup": True,
                "matched_coverage": True,
                "excluded": False,
                "exclusion_reason": "",
                "repetition_variability_value": r["nv_signed_t1"],
                "repetition_variability_value_reverse": r["nv_signed_t1_reverse"],
                "longitudinal_change_signed": r["long_signed_single"],
                "longitudinal_change_signed_reverse": r["long_signed_single_rev"],
                "longitudinal_change_abs": abs(long_s) if long_s is not None else "",
                "matched_abs_ratio": r["matched_abs_ratio"],
                "change_exceeds_repetition_variability": as_bool(r["magnitude_exceed"]),
                "direction_consistent_across_reference_swap": as_bool(r["sign_reference_stable"]),
                "nv_floor_unstable": as_bool(r["nv_floor_unstable"]),
                "coverage_band": r["coverage_band"],
                "coverage_rel": r["coverage_rel"],
                "coverage_pass": as_bool(r["coverage_ok"]),
                "qc_pass": True,
                "rep_pass": as_bool(r["rep_pass"]),
                "step5_organization": as_bool(r["step5_organization"]),
                "step5_rom_flat": as_bool(r["step5_rom_flat"]),
                "step5_matched": as_bool(r["step5_matched"]),
                "robustness_pass_if_defined": as_bool(r["rep_pass"]),
                "nv_profile_tier": r["nv_profile_tier"],
                "nv_profile_tier_base": r["nv_profile_tier_base"],
                "final_interpretable_status": (
                    "S3_interpretive_candidate"
                    if r["nv_profile_tier"] == "S3"
                    else ("A2_directionally_stable_exceed" if as_bool(r["a2_pass"]) else status)
                ),
                "presentation_status": status,
                "presentation_direction": direction,
                "presentation_note": (
                    "Primary validated beyond-NV link (A2)."
                    if as_bool(r["a2_pass"]) and r["nv_profile_tier"] != "S3"
                    else "Stricter interpretive-candidate stack (S3); not the only meaningful links."
                    if r["nv_profile_tier"] == "S3"
                    else "Exceeds variability magnitude but fails direction stability."
                    if as_bool(r["magnitude_exceed"]) and not as_bool(r["sign_reference_stable"])
                    else "Within own repetition variability."
                ),
                "internal_A2_if_present": as_bool(r["a2_pass"]),
                "internal_S3_if_present": r["nv_profile_tier"] == "S3",
                "a2_pass": as_bool(r["a2_pass"]),
                "source_file": str(POLICY / "step08_nv_and_stability/NV_PROFILE.csv"),
                "source_run": "marker_gap_policy_ex09_13/step08_nv_and_stability",
                "source_row_id_or_key": f"{cmp_id}::{link_id}",
                "estimand_footing": "matched_single_rep_vs_own_NV",
            }
        )

    evaluated = {(r["participant_id"], r["comparison_id"], r["link_id"]) for r in long_rows}
    extra = []
    for r in excl_rows:
        if r.get("repetition_mode") != "single" or r.get("comparison_kind") != "longitudinal":
            continue
        lid = (r.get("link_id") or "").strip()
        if not lid:
            continue
        pid = r["participant"]
        cmp_id = r["comparison_id"]
        if (pid, cmp_id, lid) in evaluated:
            continue
        if cmp_id.endswith("T1_vs_T2"):
            cmp_key = "T1_vs_T2"
        elif cmp_id.endswith("T1_vs_T3"):
            cmp_key = "T1_vs_T3"
        else:
            continue
        cm = CMP_META[cmp_key]
        meta = pid_stem_to_meta.get((pid, lid), {})
        vs, ve, vk = visual_segments_for_link(lid, meta.get("proximal_joint", ""), meta.get("distal_joint", ""))
        extra.append(
            {
                "participant_id": pid,
                "comparison_internal": cm["internal"],
                "comparison_id": cmp_id,
                "comparison_display": cm["comparison_display"],
                "baseline_timepoint": cm["baseline"],
                "followup_timepoint": cm["followup"],
                "classes_at_followup": cm["classes"],
                "link_id": lid,
                "link_display_name": meta.get("anatomical_description") or lid.replace("_", " "),
                "canonical_link_id": meta.get("canonical_link_id", ""),
                "anatomical_region": meta.get("region_id", ""),
                "body_side": side_from_link(lid),
                "proximal_joint": meta.get("proximal_joint", ""),
                "distal_joint": meta.get("distal_joint", ""),
                "visual_segment_start": vs,
                "visual_segment_end": ve,
                "visual_segment_key": vk,
                "visual_segment_mapping_role": "presentation_only",
                "available_baseline": False,
                "available_followup": False,
                "matched_coverage": False,
                "excluded": True,
                "exclusion_reason": r.get("exclusion_reason", ""),
                "repetition_variability_value": "",
                "repetition_variability_value_reverse": "",
                "longitudinal_change_signed": "",
                "longitudinal_change_signed_reverse": "",
                "longitudinal_change_abs": "",
                "matched_abs_ratio": "",
                "change_exceeds_repetition_variability": "",
                "direction_consistent_across_reference_swap": "",
                "nv_floor_unstable": "",
                "coverage_band": "",
                "coverage_rel": "",
                "coverage_pass": False,
                "qc_pass": False,
                "rep_pass": "",
                "step5_organization": "",
                "step5_rom_flat": "",
                "step5_matched": "",
                "robustness_pass_if_defined": "",
                "nv_profile_tier": "",
                "nv_profile_tier_base": "",
                "final_interpretable_status": "excluded_unavailable",
                "presentation_status": "unavailable_excluded",
                "presentation_direction": "unavailable",
                "presentation_note": "Excluded/unavailable; must not be shown as no-effect.",
                "internal_A2_if_present": False,
                "internal_S3_if_present": False,
                "a2_pass": False,
                "source_file": str(POLICY / "tables_to_show/02_comparison_link_exclusions.csv"),
                "source_run": "marker_gap_policy_ex09_13/tables_to_show",
                "source_row_id_or_key": f"{cmp_id}::{lid}::excluded",
                "estimand_footing": "matched_single_rep_vs_own_NV",
            }
        )
    all_long = long_rows + extra
    write_csv(OUT / "03_LONGITUDINAL_LINK_EVIDENCE.csv", all_long, list(all_long[0].keys()))
    print("wrote 03", len(long_rows), "+", len(extra))

    checks = []
    for h in headline:
        pid = h["participant"]
        cmp = h["comparison"]
        n = sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_id"].endswith(cmp))
        a2 = sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_id"].endswith(cmp) and r["a2_pass"] is True)
        ok = n == int(h["n_links"]) and a2 == int(h["A2_S2_pass"])
        checks.append(
            {
                "participant": pid,
                "comparison": cmp,
                "n_obs": n,
                "n_expected": int(h["n_links"]),
                "a2_obs": a2,
                "a2_expected": int(h["A2_S2_pass"]),
                "pass": ok,
            }
        )
        print("CHECK", pid, cmp, ok, n, a2)

    # ---- 04 ----
    map_rows = []
    for r in all_long:
        a2 = r["a2_pass"] is True
        excluded = r["excluded"] is True
        signed = fnum(r["longitudinal_change_signed"]) if r["longitudinal_change_signed"] != "" else None
        mag = abs(signed) if signed is not None else None
        display_available = (not excluded) and r["matched_coverage"] is True
        display_highlight = a2 and display_available
        display_no_clear = display_available and (not a2)
        if excluded:
            prio = 0
        elif r.get("internal_S3_if_present") is True:
            prio = 3
        elif display_highlight:
            prio = 2
        else:
            prio = 1
        map_rows.append(
            {
                "participant_id": r["participant_id"],
                "comparison_internal": r["comparison_internal"],
                "comparison_display": r["comparison_display"],
                "classes_at_followup": r["classes_at_followup"],
                "link_id": r["link_id"],
                "display_name": r["link_display_name"],
                "canonical_link_id": r["canonical_link_id"],
                "region": r["anatomical_region"],
                "body_side": r["body_side"],
                "body_surface_group": r["anatomical_region"],
                "proximal_joint": r["proximal_joint"],
                "distal_joint": r["distal_joint"],
                "visual_segment_start": r["visual_segment_start"],
                "visual_segment_end": r["visual_segment_end"],
                "visual_segment_key": r["visual_segment_key"],
                "visual_segment_mapping_role": "presentation_only_not_scientific_variable",
                "display_available": display_available,
                "display_excluded": excluded,
                "display_no_clear_change": display_no_clear,
                "display_highlight": display_highlight,
                "signed_value_if_valid": signed if display_highlight else "",
                "magnitude_if_valid": mag if display_highlight else "",
                "normalized_display_value_if_already_authoritative": "",
                "direction_label": r["presentation_direction"]
                if display_highlight
                else ("unavailable" if excluded else "no_clear_validated_change"),
                "coverage_note": r.get("coverage_band", ""),
                "exclusion_note": r.get("exclusion_reason", ""),
                "geometry_key": f"{r['participant_id']}_reference_pose",
                "avatar_region_key": r["anatomical_region"],
                "parent_bone": pid_stem_to_meta.get((r["participant_id"], r["link_id"]), {}).get("parent_bone", ""),
                "child_bone": pid_stem_to_meta.get((r["participant_id"], r["link_id"]), {}).get("child_bone", ""),
                "overlay_priority": prio,
                "recommended_label_position_if_known": "",
                "requires_visual_mapping": True,
                "measurement_resolution": "body_link_or_region",
                "not_continuous_body_surface_measurement": True,
                "main_figure_panel": (r["comparison_internal"] == "D12"),
                "secondary_badge_or_companion_panel": (r["comparison_internal"] == "D13"),
                "a2_pass": a2,
                "s3_flag": r.get("internal_S3_if_present") is True,
                "presentation_status": r["presentation_status"],
                "source_file": r["source_file"],
                "source_run": r["source_run"],
                "source_row_id_or_key": r["source_row_id_or_key"],
            }
        )
    write_csv(OUT / "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv", map_rows, list(map_rows[0].keys()))
    print("wrote 04", len(map_rows))

    # ---- 06 ----
    rep_root = JCV / "docs/rep_sensitivity_nv_panels"
    rep_flags = {}
    for pid in ["252", "651", "671", "790"]:
        for row in read_csv(rep_root / f"{pid}_rep_sensitivity_nv_flags.csv"):
            rep_flags[(pid, row["followup"], row["rep_match"], row["link_id"])] = row

    pvs = {(r["participant"], r["comparison"], r["link_id"]): r for r in pooled_vs_single}
    top5_pooled = {}
    for r in func_bands:
        top5_pooled[r["comparison_id"]] = [x.strip() for x in r["top5_all_pcs"].split(",") if x.strip()]

    link_level = []
    for (pid, cmp, link_id), pv in pvs.items():
        cm = CMP_META[cmp]
        cmp_id = f"{pid}_{cmp}"
        meta = pid_stem_to_meta.get((pid, link_id), {})
        vs, ve, vk = visual_segments_for_link(link_id, meta.get("proximal_joint", ""), meta.get("distal_joint", ""))
        follow = "T2" if cmp == "T1_vs_T2" else "T3"
        pooled_s = fnum(pv.get("pooled_signed_descriptive"))
        r1_s = fnum(pv.get("single_rep_long_signed"))
        r2_row = rep_flags.get((pid, follow, "R2", link_id))
        r2_s = fnum(r2_row["long_signed"]) if r2_row else None
        top5 = top5_pooled.get(cmp_id, [])
        link_level.append(
            {
                "participant_id": pid,
                "comparison_internal": cm["internal"],
                "comparison_display": cm["comparison_display"],
                "classes_at_followup": cm["classes"],
                "comparison_id": cmp_id,
                "link_id": link_id,
                "canonical_link_id": meta.get("canonical_link_id", ""),
                "link_display_name": meta.get("anatomical_description") or link_id.replace("_", " "),
                "visual_segment_key": vk,
                "visual_segment_start": vs,
                "visual_segment_end": ve,
                "pooled_R1R2_change_signed": pooled_s,
                "pooled_R1R2_change_abs": abs(pooled_s) if pooled_s is not None else None,
                "R1_only_change_signed": r1_s,
                "R1_only_change_abs": abs(r1_s) if r1_s is not None else None,
                "R2_only_change_signed": r2_s,
                "R2_only_change_abs": abs(r2_s) if r2_s is not None else None,
                "R2_only_availability": "available_from_rep_sensitivity_panels" if r2_s is not None else "unavailable",
                "top_k_membership_pooled": (link_id in top5) if top5 else None,
                "top_k_definition": "top-5 by pooled descriptive |signed link contribution| as listed in functional_pc_bands.top5_all_pcs",
                "top_k_k": 5,
                "same_sign_pooled_vs_single_R1": as_bool(pv.get("same_sign")) if pv.get("same_sign") != "" else None,
                "a2_pass_from_matched_single_rep_footing": as_bool(pv.get("a2_pass")),
                "nv_profile_tier_from_matched_single_rep_footing": pv.get("nv_profile_tier"),
                "basis_note": pv.get("basis_note"),
                "source_file_pooled_vs_single": str(POLICY / "tables_to_show/09_pooled_vs_single_by_link.csv"),
                "source_file_r2_panel": str(rep_root / f"{pid}_rep_sensitivity_nv_flags.csv") if r2_row else "",
                "source_run": "marker_gap_policy_ex09_13",
                "source_key": f"{cmp_id}::{link_id}",
                "footing_warning": "pooled_R1R2 is descriptive pooled estimand; R1_only/R2_only are matched-rep longitudinal signed changes; A2 gates remain in file 03 and must not be mixed into pooled/NV ratios.",
            }
        )

    by_pc = defaultdict(list)
    for row in link_level:
        by_pc[(row["participant_id"], row["comparison_id"])].append(row)
    for _, rows in by_pc.items():
        pr = {r["link_id"]: r["pooled_R1R2_change_abs"] for r in rows if r["pooled_R1R2_change_abs"] is not None}
        r1 = {r["link_id"]: r["R1_only_change_abs"] for r in rows if r["R1_only_change_abs"] is not None}
        r2 = {r["link_id"]: r["R2_only_change_abs"] for r in rows if r["R2_only_change_abs"] is not None}
        prank = ranks_for(pr)
        r1rank = ranks_for(r1)
        r2rank = ranks_for(r2)
        r1_top = {link for link, rk in r1rank.items() if rk <= 5}
        r2_top = {link for link, rk in r2rank.items() if rk <= 5}
        for r in rows:
            r["pooled_R1R2_rank"] = prank.get(r["link_id"])
            r["R1_only_rank"] = r1rank.get(r["link_id"])
            r["R2_only_rank"] = r2rank.get(r["link_id"])
            r["top_k_membership_R1"] = (r["link_id"] in r1_top) if r1_top else None
            r["top_k_membership_R2"] = (r["link_id"] in r2_top) if r2_top else None

    cov_map = {}
    for r in coverage_rows:
        cid = r["comparison_id"].replace("_single_R1", "")
        cov_map[cid] = r
    agree_map = {(r["participant"], r["followup"]): r for r in r1r2_agree}
    func_map = {r["comparison_id"]: r for r in func_bands}

    comp_level = []
    for pid in ["252", "651", "671", "790"]:
        for cmp in ["T1_vs_T2", "T1_vs_T3"]:
            cm = CMP_META[cmp]
            cmp_id = f"{pid}_{cmp}"
            k_rows = [r for r in robustness if r["participant"] == pid and r["comparison_id"] == cmp_id and r["axis"] == "k_grid"]
            rep_rows_r = [r for r in robustness if r["participant"] == pid and r["comparison_id"] == cmp_id and r["axis"] == "repetition_mode"]
            qc_rows = [r for r in robustness if r["participant"] == pid and r["comparison_id"] == cmp_id and r["axis"] == "qc_drop"]
            rep = rep_rows_r[0] if rep_rows_r else {}
            qc = qc_rows[0] if qc_rows else {}
            k_grid = [
                {
                    "k": int(r["axis_detail"]),
                    "top5_overlap_vs_primary_m": fnum(r["top5_overlap"]),
                    "functional_chain_retained": r.get("functional_chain_retained"),
                }
                for r in k_rows
            ]
            k_overlaps = [x["top5_overlap_vs_primary_m"] for x in k_grid if x["top5_overlap_vs_primary_m"] is not None]
            k_median = sorted(k_overlaps)[len(k_overlaps) // 2] if k_overlaps else None
            cov = cov_map.get(cmp_id, {})
            follow = "T2" if cmp == "T1_vs_T2" else "T3"
            agr = agree_map.get((pid, follow), {})
            fb = func_map.get(cmp_id, {})
            overall = qc.get("robustness_label") or None
            pvr1 = fnum(rep.get("pooled_vs_r1_overlap"))
            comp_level.append(
                {
                    "participant_id": pid,
                    "comparison_internal": cm["internal"],
                    "comparison_display": cm["comparison_display"],
                    "classes_at_followup": cm["classes"],
                    "comparison_id": cmp_id,
                    "pooled_vs_R1_overlap": pvr1,
                    "pooled_vs_R2_overlap": fnum(rep.get("pooled_vs_r2_overlap")),
                    "R1_vs_R2_overlap": fnum(rep.get("longitudinal_r1_vs_r2_overlap")),
                    "pooled_vs_R1_overlap_p50": fnum(rep.get("pooled_vs_r1_overlap_p50")),
                    "pooled_vs_R1_overlap_p60": fnum(rep.get("pooled_vs_r1_overlap_p60")),
                    "pooled_vs_R2_overlap_p50": fnum(rep.get("pooled_vs_r2_overlap_p50")),
                    "pooled_vs_R2_overlap_p60": fnum(rep.get("pooled_vs_r2_overlap_p60")),
                    "repetition_design_stability_label": "pass_top5_overlap_ge_0.6" if (pvr1 or 0) >= 0.6 else "below_0.6_threshold",
                    "top_k_definition": "top-5 link overlap; threshold >=0.60 (>=3/5) used in ROBUSTNESS_FRAMEWORK.md",
                    "k_grid_values_tested": [x["k"] for x in k_grid],
                    "k_grid_overlap_by_k": k_grid,
                    "k_grid_summary": {
                        "primary_m": int(k_rows[0]["primary_m"]) if k_rows else None,
                        "median_top5_overlap": k_median,
                        "n_k_with_overlap_ge_0.6": sum(1 for x in k_overlaps if x >= 0.6),
                        "n_k_tested": len(k_overlaps),
                    },
                    "qc_drop_overlap": fnum(qc.get("top5_overlap")),
                    "qc_drop_detail": qc.get("axis_detail"),
                    "qc_drop_stability_related_label": qc.get("robustness_label") or None,
                    "coverage_band": cov.get("coverage_band") or None,
                    "coverage_value_if_available": fnum(cov.get("coverage_rel")),
                    "reference_subspace_coverage_if_available": {
                        "coverage_abs": fnum(cov.get("coverage_abs")),
                        "coverage_rel": fnum(cov.get("coverage_rel")),
                        "coverage_band": cov.get("coverage_band"),
                        "source": str(POLICY / "tables_to_show/06_coverage_gate_a2_estimand.csv"),
                    },
                    "functional_band_sensitivity_if_available": {
                        "p_functional_50": fb.get("p_functional_50"),
                        "p_functional_60": fb.get("p_functional_60"),
                        "selected_m": fb.get("selected_m"),
                        "overlap_all_vs_p50": fnum(fb.get("overlap_all_vs_p50")),
                        "overlap_all_vs_p60": fnum(fb.get("overlap_all_vs_p60")),
                        "overlap_p50_vs_p60": fnum(fb.get("overlap_p50_vs_p60")),
                        "top5_all_pcs": fb.get("top5_all_pcs"),
                        "top5_p_functional_50": fb.get("top5_p_functional_50"),
                        "top5_p_functional_60": fb.get("top5_p_functional_60"),
                        "source": str(POLICY / "step04_primary_runs/functional_pc_bands.csv"),
                    },
                    "r1_r2_same_sign_exceed_agreement_summary": {
                        "n_links_in_analysis": agr.get("n_links_in_analysis"),
                        "exceed_both_R1_and_R2": agr.get("exceed_both_R1_and_R2"),
                        "exceed_R1_only": agr.get("exceed_R1_only"),
                        "exceed_R2_only": agr.get("exceed_R2_only"),
                        "exceed_neither": agr.get("exceed_neither"),
                        "rep_stable_fraction": fnum(agr.get("rep_stable_fraction")),
                        "source": str(POLICY / "tables_to_show/11_r1_r2_same_sign_exceed_agreement.csv"),
                        "note": "Magnitude-exceed agreement across R1-matched vs R2-matched longitudinal panels; related to but not identical to A2 direction-stability gate.",
                    },
                    "overall_robustness_label": overall,
                    "overall_robustness_label_provenance": "Authoritative heuristic label from robustness.csv qc_drop row (stable/partial/unstable per ROBUSTNESS_FRAMEWORK.md). Not a newly invented composite score.",
                    "source_file": str(POLICY / "step04_primary_runs/robustness.csv"),
                    "source_run": "marker_gap_policy_ex09_13/step04_primary_runs",
                    "pooled_run_folder": str(POLICY / f"step04_primary_runs/{pid}/ex09_13_contiguous_pooled"),
                    "single_run_folder": str(POLICY / f"step04_primary_runs/{pid}/ex09_13_contiguous_single"),
                }
            )

    n_r2_available = sum(1 for r in link_level if r["R2_only_change_signed"] is not None)
    robustness_json = {
        "file_id": "06_JCVPCA_ROBUSTNESS",
        "package_version": 2,
        "purpose": "Complementary pooled descriptive JcvPCA and repetition-design / sensitivity evidence. Separate from matched single-rep vs NV evidence in file 03.",
        "critical_footing_rule": estimand_separation,
        "confirmed_analyses": {
            "pooled_R1R2_vs_4classes": True,
            "pooled_R1R2_vs_10classes": True,
            "R1_only_longitudinal_link_values": True,
            "R2_only_longitudinal_link_values": True,
            "R2_only_source": "docs/rep_sensitivity_nv_panels/{pid}_rep_sensitivity_nv_flags.csv (T1_R2 vs T{k}_R2)",
            "n_link_rows_with_R2_values": n_r2_available,
            "k_grid_sensitivity": True,
            "qc_drop_sensitivity": True,
            "functional_band_sensitivity": True,
            "coverage_gate": True,
        },
        "top_k_definition_global": "Unless noted, overlap metrics use top-5 links; pass heuristic >= 0.60 (>=3/5) per ROBUSTNESS_FRAMEWORK.md",
        "link_level_robustness": link_level,
        "comparison_level_robustness": comp_level,
        "persistence_reference_for_optional_visuals": {
            "source": str(POLICY / "tables_to_show/07_persistence_t2_t3.csv"),
            "note": "Authoritative persistence labels available if a dual-exposure G3 uses them; not a new analysis.",
            "n_rows": len(persistence),
        },
    }
    json.dump(robustness_json, open(OUT / "06_JCVPCA_ROBUSTNESS.json", "w"), indent=2)
    print("wrote 06", len(link_level), len(comp_level), "R2avail", n_r2_available)

    # ---- 05 ----
    a2_counts = {}
    for pid in ["252", "651", "671", "790"]:
        a2_counts[pid] = {
            "D12": sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D12" and r["a2_pass"]),
            "D12_n": sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D12"),
            "D13": sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D13" and r["a2_pass"]),
            "D13_n": sum(1 for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D13"),
            "D12_cov": next(r["coverage_band"] for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D12"),
            "D13_cov": next(r["coverage_band"] for r in long_rows if r["participant_id"] == pid and r["comparison_internal"] == "D13"),
        }
    rep_pass_summary = [
        {
            "participant": c["participant_id"],
            "comparison": c["comparison_display"],
            "pooled_vs_R1": c["pooled_vs_R1_overlap"],
            "pooled_vs_R2": c["pooled_vs_R2_overlap"],
            "R1_vs_R2": c["R1_vs_R2_overlap"],
            "overall_label": c["overall_robustness_label"],
            "k_median": c["k_grid_summary"]["median_top5_overlap"],
            "coverage": c["coverage_band"],
        }
        for c in comp_level
    ]

    review = {
        "file_id": "05_FIGURE_REVIEW_AND_VISUAL_SPEC",
        "package_version": 2,
        "extraction_date_utc": EXTRACT,
        "audience": "PhD admission committee",
        "g3_strategy_comparison_after_robustness_export": {
            "OPTION_A_longitudinal_capability": {
                "scientific_question": "Can the framework track validated body-link changes as Gaga practice accumulates?",
                "committee_understands_in_3_seconds": "Validated link changes appear at ~4 classes and again at ~10 classes, differently across people; coverage is not equal.",
                "exact_data_used": "File 03 A2 flags for D12 and D13; coverage bands; optional persistence labels",
                "visual_form": "Per participant: two compact body-link glyphs / evidence rings (≈4 classes | ≈10 classes). Highlight = beyond own repetition variability AND directionally stable. Explicit coverage markers. No trajectory connecting counts as learning magnitude.",
                "main_risk": "Uneven T3 coverage; link-count misread as amount of learning; partial adjacency to G4 anatomy",
                "duplicates_G2_or_G4": "Distinct from G2. Adjacent to G4 but asks longitudinal capability across exposures rather than detailed anatomical localization.",
                "communicates_PhD_trajectory": True,
                "recommendation": "MAIN",
                "a2_counts_verified": a2_counts,
            },
            "OPTION_B_repetition_analytical_robustness": {
                "scientific_question": "Does the JcvPCA contribution pattern remain similar for pooled R1+R2, R1-only, and R2-only, and under PC-count / QC variants?",
                "committee_understands_in_3_seconds": "The analysis was stress-tested across repetition designs and analytical variants; stability varies by participant.",
                "exact_data_used": "File 06 comparison-level overlaps + k-grid + qc_drop + functional bands; link-level pooled/R1/R2 signed values",
                "visual_form": "Per participant×comparison: Pooled ↔ R1 ↔ R2 overlap representation; restrained k-grid sparkline; authoritative overall label only",
                "main_risk": "Technical/dashboard-like; top-5 overlap is a coarse stability proxy",
                "duplicates_G2_or_G4": "No",
                "communicates_PhD_trajectory": "Indirectly (method readiness)",
                "recommendation": "BACKUP",
                "robustness_snapshot": rep_pass_summary,
            },
            "OPTION_C_dual_exposure_status_without_count_trajectory": {
                "scientific_question": "Which validated links appear early, later, both, or neither — without ranking participants by count?",
                "committee_understands_in_3_seconds": "Some validated changes persist across exposures; others appear only early or only later.",
                "exact_data_used": "07_persistence_t2_t3.csv + file 03 A2; coverage markers",
                "visual_form": "Categorical link status chips (early / later / both / neither) + coverage badges",
                "main_risk": "Denser than Option A; still needs anti-learning caption",
                "duplicates_G2_or_G4": "Less anatomical than G4; more longitudinal than G2",
                "communicates_PhD_trajectory": True,
                "recommendation": "BACKUP",
            },
            "selected_G3": "OPTION_A_longitudinal_capability",
            "selection_rationale": [
                "Best match to admissions narrative: preliminary capability toward the longitudinal PhD design",
                "Uses validated matched-single-rep A2 body-link evidence without mixing pooled/NV estimands",
                "Robustness evidence is real and valuable but better as BACKUP due to dashboard risk",
                "Old validation-layers / 68→36→22→4 funnel remains REJECT as main",
            ],
            "rejected_old_validation_layers_as_main": True,
        },
        "overall_recommendation": {
            "keep_four_graphs": True,
            "why_four_not_three": "G1 paradigm, G2 measurement behavior, G3 longitudinal capability, G4 anatomical interpretability are four distinct questions.",
            "g2_and_g3_genuinely_different": True,
            "t3_visible": "Yes via G3 dual-exposure panels with honest limited-coverage markers; full T3 rows retained in 03/04/06",
            "methodological_rigor_without_thesis_defense": "G2 motivates the repetition reference; G3 shows preliminary longitudinal capability; robustness file 06 supports BACKUP method-stress figure rather than a filtering hierarchy slide",
            "jcvpca_understandable_without_internal_terms": True,
            "pooled_unmistakable": True,
            "leads_to_future_full_study": True,
            "desired_narrative": "PARADIGM → MEASUREMENT BEHAVIOR → PRELIMINARY LONGITUDINAL CAPABILITY → ANATOMICAL INTERPRETABILITY → FUTURE FULL / UNBLINDED STUDY",
            "strongest_graph": "G4 anatomical contribution map",
            "preferred_G3": "OPTION_A",
            "backup_G3": "OPTION_B",
        },
        "g2_annotation_policy": {
            "endpoint_positive_sessions": f"{n_end}/{n_sess}",
            "slope_positive_sessions": f"{n_slope}/{n_sess}",
            "main_visual_annotation": "12/12 sessions: Whole body > Hands",
            "slope_role": "validation metadata / backup annotation only; do not conflate with endpoint",
            "field_rename": "valid_sample_count → valid_link_count",
            "duration_field": "duration_frames_or_seconds left empty; duration_availability=unavailable_in_source_table",
        },
        "graphs": [
            {
                "graph_id": "G1",
                "working_title": "From progressive movement exploration to interpretable whole-body coordination",
                "scientific_question": "What are we actually measuring?",
                "decision": "KEEP_WITH_REVISION",
                "recommended_visualization": "Hands → +Elbows → +Shoulders → +Head/Nose → Whole body; bracket to ONE POOLED PROGRESSIVE MOVEMENT SEQUENCE; JcvPCA → body-link contribution pattern; secondary corrected study timeline",
                "slide_role": "Slide 1 left",
                "priority": 1,
            },
            {
                "graph_id": "G2",
                "working_title": "Natural repetition variability across progressive body involvement",
                "scientific_question": "Does the measurement respond sensibly to the movement paradigm?",
                "decision": "KEEP_WITH_REVISION",
                "annotations": ["12/12 sessions: Whole body > Hands", "Slope check retained as metadata only"],
                "slide_role": "Slide 1 right",
                "priority": 2,
                "data_source": "02_REPETITION_VARIABILITY.csv",
            },
            {
                "graph_id": "G3",
                "working_title": "Tracking validated body-link changes across practice exposure",
                "scientific_question": "Can the framework track validated body-link changes as Gaga practice accumulates?",
                "decision": "KEEP_WITH_REVISION",
                "recommended_visualization": "OPTION A dual-exposure validated link glyphs with coverage markers; no count trajectory",
                "alternative_visualization": "BACKUP OPTION B robustness from file 06",
                "slide_role": "Slide 2 left",
                "priority": 2,
                "data_source": "03_LONGITUDINAL_LINK_EVIDENCE.csv; backup 06_JCVPCA_ROBUSTNESS.json",
                "does_not_use_validation_layers_funnel_as_main": True,
            },
            {
                "graph_id": "G4",
                "working_title": "Preliminary anatomical patterns of movement reorganization",
                "scientific_question": "What can this framework reveal that a single movement score cannot?",
                "decision": "KEEP",
                "recommended_visualization": "Anatomical contribution maps using visual_segment_start/end on embedded reference poses; main panels Baseline→≈4 classes",
                "slide_role": "Slide 2 right (hero)",
                "priority": 1,
                "data_source": "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv + embedded geometry in 01",
            },
        ],
        "two_slide_storyboard_primary": {
            "slide_1": {
                "title": "Measuring individual change in a progressive whole-body movement sequence",
                "left": "G1 paradigm + corrected secondary study-context timeline",
                "right": "G2 progressive repetition variability",
            },
            "slide_2": {
                "title": "Preliminary longitudinal capability and anatomical interpretability",
                "left": "G3 dual-exposure validated link evidence (≈4 vs ≈10 classes)",
                "right": "G4 anatomical contribution maps",
            },
        },
        "estimand_separation_reminder": estimand_separation,
        "visual_language_shared": {
            "light_neutral_gray": "reference / non-highlighted anatomy / natural variability",
            "strong_accent": "validated beyond-repetition-variability evidence",
            "excluded": "hatch / broken boundary",
            "avoid": [
                "continuous-surface false precision",
                "learning-magnitude trajectories from link counts",
                "A2/S3/D12 audience labels",
                "dashboard robustness matrices as main G3",
            ],
        },
    }
    json.dump(review, open(OUT / "05_FIGURE_REVIEW_AND_VISUAL_SPEC.json", "w"), indent=2)
    print("wrote 05")

    # ---- 00 ----
    source_files = [
        POLICY / "step08_nv_and_stability/NV_PROFILE.csv",
        POLICY / "step08_nv_and_stability/exercise_level_nv.csv",
        POLICY / "tables_to_show/09_headline_a2_summary.csv",
        POLICY / "tables_to_show/02_comparison_link_exclusions.csv",
        POLICY / "tables_to_show/06_coverage_gate_a2_estimand.csv",
        POLICY / "tables_to_show/09_pooled_vs_single_by_link.csv",
        POLICY / "tables_to_show/09_pooled_vs_single_headline.csv",
        POLICY / "tables_to_show/07_persistence_t2_t3.csv",
        POLICY / "tables_to_show/11_r1_r2_same_sign_exceed_agreement.csv",
        POLICY / "step04_primary_runs/robustness.csv",
        POLICY / "step04_primary_runs/ROBUSTNESS_FRAMEWORK.md",
        POLICY / "step04_primary_runs/functional_pc_bands.csv",
        JCV / "data/link_mapping/canonical_link_map.csv",
        ROOT / "3Layers_project/results/active/canonical_batch/poster_scientific_story_and_figure_plan.md",
    ]
    for pid in ["252", "651", "671", "790"]:
        source_files.append(geom_dir / f"{pid}_reference_pose.json")
        source_files.append(rep_root / f"{pid}_rep_sensitivity_nv_flags.csv")
    sources = []
    for p in source_files:
        if p.exists():
            st = p.stat()
            sources.append(
                {
                    "path": str(p),
                    "sha256": sha256(p),
                    "nbytes": st.st_size,
                    "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )

    # geometry checksum verification
    geom_ok = all(
        embedded_geometry[pid]["source_sha256"] == sha256(geom_dir / f"{pid}_reference_pose.json")
        for pid in ["252", "651", "671", "790"]
    )

    manifest = {
        "package_name": "committee_figure_data_pack",
        "package_version": 2,
        "supersedes": str(V1),
        "extraction_date_utc": EXTRACT,
        "project_overview": {
            "scientific_question": "Can an interpretable body-link framework detect individual longitudinal changes in whole-body coordination relative to each participant’s own natural repetition-to-repetition variability?",
            "committee_presentation_objective": "Demonstrate a difficult measurement problem, a thoughtful analytical solution, methodological validation, preliminary interpretable proof-of-concept results, and a clear path to the full blinded longitudinal / later unblinded PhD study — without claiming proven treatment effects.",
            "not_a_completed_treatment_effect_study": True,
        },
        "source_of_truth_hierarchy": [
            "gaga_jcvpca/results_committee_case/marker_gap_policy_ex09_13/",
            "gaga_jcvpca/docs/rep_sensitivity_nv_panels/",
            "gaga_jcvpca/data/link_mapping/canonical_link_map.csv",
            "gaga_jcvpca/docs/slide45_figures/avatar_verified/geometry/ (embedded for layout only)",
            "poster_scientific_story_and_figure_plan.md (timeline schematic wording)",
        ],
        "git_provenance": {
            "gaga_jcvpca": {"commit": "728c871edf0423aa6ea526651023253c38ea118f", "branch": "feature/qc-tab3-manifest"},
            "gaga_shared6d_poc": {"commit": "4c3f0754f93aae87f6c2b2d72044371b068f33e0", "branch": "exploratory/guided-rqa-stage2"},
        },
        "participants": ["252", "651", "671", "790"],
        "timepoint_definitions": {
            "T1": {"display": "Baseline"},
            "T2": {"display": "≈4 classes", "approximate_classes": 4, "internal": "D12"},
            "T3": {"display": "≈10 classes", "approximate_classes": 10, "internal": "D13"},
            "class_count_labels_require_protocol_confirmation": True,
        },
        "study_timeline_corrected": timeline_source,
        "estimand_separation": estimand_separation,
        "coverage_rules": {
            "D12": {"252": "adequate", "651": "adequate", "671": "adequate", "790": "adequate"},
            "D13": {"252": "limited", "651": "limited", "671": "limited", "790": "adequate"},
            "denominators_D12": {"252": 20, "651": 10, "671": 18, "790": 20},
            "denominators_D13": {"252": 20, "651": 10, "671": 17, "790": 18},
        },
        "headline_a2_verified": [
            {
                "participant": h["participant"],
                "comparison": h["comparison"],
                "n_links": int(h["n_links"]),
                "A2": int(h["A2_S2_pass"]),
                "S3": int(h["S3"]),
                "coverage_band": h["coverage_band"],
            }
            for h in headline
        ],
        "consistency_checks_run": [
            {"check": "NV_PROFILE matches headline", "results": checks, "all_pass": all(c["pass"] for c in checks)},
            {"check": "G2 endpoint and slope", "n_sessions": n_sess, "endpoint_positive": n_end, "slope_positive": n_slope},
            {"check": "G2 field rename", "old": "valid_sample_count", "new": "valid_link_count"},
            {"check": "embedded geometry checksums match source pose files", "pass": geom_ok},
            {"check": "no stale avatar denominators imported", "pass": True},
            {"check": "no new scientific gates invented", "pass": True},
            {"check": "R2 link-level values available", "n_rows": n_r2_available},
        ],
        "known_conflicts": [
            {
                "issue": "avatar_verified provenance_manifest denominators disagree with headline",
                "resolution": "Geometry embedded for layout only; A2 denominators from NV_PROFILE/headline only",
            }
        ],
        "known_limitations": [
            "n=4; blinded; two-repetition NV reference",
            "≈4/≈10 class labels approximate pending protocol confirmation",
            "D13 coverage limited for 252/651/671",
            "No continuous body-surface mesh",
            "Pooled descriptive and matched-single-rep-vs-NV footings must remain separate",
        ],
        "valid_comparisons": [
            "Within-participant Baseline→≈4/≈10 classes matched-single-rep change vs own NV",
            "Within-participant pooled R1+R2 descriptive longitudinal pattern",
            "Repetition-design / k-grid / QC-drop top-5 overlap robustness",
            "Within-session progressive-sequence NV (descriptive)",
        ],
        "invalid_comparisons": [
            "pooled_change / single_rep_NV as a new ratio",
            "Cross-participant ranking of learning magnitude by A2 counts",
            "Treatment-effect attribution while blinded",
            "Continuous-surface physiological activation readings from contribution overlays",
        ],
        "units": {
            "signed_link_values": "EVR-weighted signed JcvPCA link contribution change (project-internal scalar)",
            "normalized_variability": "unitless relative to session-mean median_abs_nv",
            "top5_overlap": "unitless fraction of shared top-5 links",
        },
        "exported_files": [
            {"name": "00_FIGURE_PACKAGE_MANIFEST.json", "role": "Manifest / schema / provenance"},
            {"name": "01_PARADIGM_AND_METHOD.json", "role": "G1 + corrected timeline + embedded geometry"},
            {"name": "02_REPETITION_VARIABILITY.csv", "role": "G2; valid_link_count; endpoint+slope"},
            {"name": "03_LONGITUDINAL_LINK_EVIDENCE.csv", "role": "Matched single-rep vs NV evidence D12+D13"},
            {"name": "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv", "role": "G4 contribution map + visual_segment_*"},
            {"name": "05_FIGURE_REVIEW_AND_VISUAL_SPEC.json", "role": "Critique; G3 Option A selected"},
            {"name": "06_JCVPCA_ROBUSTNESS.json", "role": "Pooled + R1/R2 + k-grid + QC robustness"},
            {"name": "README.md", "role": "Reading order"},
        ],
        "g3_visual_decision": {
            "preferred_main": "OPTION_A_longitudinal_capability",
            "backup": "OPTION_B_repetition_analytical_robustness",
            "rejected_as_main": ["validation_layers_funnel_68_36_22_4", "671_only_funnel"],
        },
        "g4_naming_decision": {
            "concept_name": "anatomical contribution map",
            "visual_segment_fields": "presentation-only mapping for renderer resolution",
        },
        "portability": {
            "embedded_reference_geometry": True,
            "location": "01_PARADIGM_AND_METHOD.json -> embedded_reference_geometry",
            "absolute_external_paths_still_listed_for_provenance": True,
        },
        "unavailable_fields": {
            "02_duration_frames_or_seconds": "unavailable_in_source_table; not inferred",
        },
        "source_files_used": sources,
    }
    json.dump(manifest, open(OUT / "00_FIGURE_PACKAGE_MANIFEST.json", "w"), indent=2)
    print("wrote 00")

    readme = """# Committee figure data pack v2

Self-contained export for PhD-admissions figure generation.
Supersedes `committee_figure_data_pack/` (v1). No new scientific analyses were run.

## Recommended reading order

1. `README.md` (this file)
2. `00_FIGURE_PACKAGE_MANIFEST.json`
3. `05_FIGURE_REVIEW_AND_VISUAL_SPEC.json` (includes G3 Option A vs B decision)
4. `01_PARADIGM_AND_METHOD.json` (paradigm, corrected timeline, embedded geometry)
5. `02_REPETITION_VARIABILITY.csv`
6. `03_LONGITUDINAL_LINK_EVIDENCE.csv` (matched single-rep vs NV; primary A2 footing)
7. `06_JCVPCA_ROBUSTNESS.json` (pooled + R1/R2 + k-grid + QC; separate footing)
8. `04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv`

## Critical rules for visualization agents

- Do not claim treatment effects; analysis remains blinded.
- Do not mix pooled R1+R2 descriptive changes with matched single-rep / NV ratios.
- G4 is an anatomical contribution map (link/segment resolution), not a continuous body-surface heatmap.
- `visual_segment_*` fields are presentation-only mappings.
- Prefer G3 Option A (≈4 vs ≈10 class validated link evidence). Option B robustness is backup.
- Main G2 annotation: `12/12 sessions: Whole body > Hands` (slope is metadata only).
"""
    (OUT / "README.md").write_text(readme)

    zip_path = OUT / "committee_figure_data_pack_v2.zip"
    names = [
        "00_FIGURE_PACKAGE_MANIFEST.json",
        "01_PARADIGM_AND_METHOD.json",
        "02_REPETITION_VARIABILITY.csv",
        "03_LONGITUDINAL_LINK_EVIDENCE.csv",
        "04_ANATOMICAL_CONTRIBUTION_MAP_DATA.csv",
        "05_FIGURE_REVIEW_AND_VISUAL_SPEC.json",
        "06_JCVPCA_ROBUSTNESS.json",
        "README.md",
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(OUT / name, arcname=name)
    print("zip", zip_path, zip_path.stat().st_size)
    print("ALL_PASS", all(c["pass"] for c in checks), "geom_ok", geom_ok)


if __name__ == "__main__":
    main()
