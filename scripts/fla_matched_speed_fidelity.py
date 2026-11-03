#!/usr/bin/env python3
"""Read-only matched-genotype VM-speed sensitivity audit of archived v17 K16 replays.

Same mapping is matched across default/staggered VM speeds; unlike arm-wise MAPE
comparisons, this holds the discrete VM assignment fixed. It does NOT control
simulator timing order, cache state, or imply an algorithm improvement.
Inputs: immutable Actions 41626382711 (real), 41631739331 (synthetic).
No optimizer/evaluator/simulator calls.
"""
import csv
import math
import pathlib
import statistics
import sys
from collections import defaultdict

ARMS = (
    "DAG-Pareto-FLA[v12-hvbandit]",
    "DAG-Pareto-FLA[v17-do-random]",
    "DAG-Pareto-FLA[v17-late-random]",
    "NSGA-II[costseed]",
)
GROUPS = (
    ("real-sizes", ("Epigenomics_46", "Inspiral_50", "CyberShake_100", "Sipht_100"), (211, 212), "v17-confirm"),
    ("synthetic-wide-deep", ("SynthNewWide_60", "SynthNewDeep_60"), (301, 302, 303), "v17-synthetic"),
)
SPEEDS = ("default", "staggered")
METRICS = ("planned_makespan", "sim_makespan", "planned_cost", "sim_cost")
TOL = 1e-8  # relative tolerance for a deterministic same-mapping consistency check


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def one_file(root, pattern):
    found = list(root.rglob(pattern))
    if len(found) != 1:
        raise AssertionError(("Expected one original file", pattern, [str(x) for x in found]))
    return found[0]


def positive_number(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise AssertionError(("Nonfinite/nonpositive replay value", value))
    return result


def load_originals(root):
    """Load all 28 scenario-seeds x 2 speeds x 4 arms x 16 distinct mappings."""
    original = {}
    for cohort, names, seeds, prefix in GROUPS:
        for dag in names:
            for speed in SPEEDS:
                for seed in seeds:
                    label = f"{prefix}-{speed}-{dag}-s{seed}"
                    summary = read_csv(one_file(root, label + "_summary.csv"))
                    replays = read_csv(one_file(root, label + "_replays.csv"))
                    if len(summary) != 4 or len(replays) != 64:
                        raise AssertionError(("Unexpected original rows", label, len(summary), len(replays)))
                    if {z["algorithm"] for z in summary} != set(ARMS):
                        raise AssertionError(("Unexpected algorithm controls", label))
                    for arm in ARMS:
                        s = next(z for z in summary if z["algorithm"] == arm)
                        if (int(s["evaluations"]), int(s["captured_evaluations"]), int(s["replayed"])) != (3030, 3030, 16):
                            raise AssertionError(("Changed evaluation/replay budget", label, arm))
                        points = sorted((z for z in replays if z["algorithm"] == arm),
                                        key=lambda z: int(z["candidate_index"]))
                        if len(points) != 16 or [int(z["candidate_index"]) for z in points] != list(range(1, 17)):
                            raise AssertionError(("Bad candidate order", label, arm))
                        if len({z["mapping"] for z in points}) != 16:
                            raise AssertionError(("Repeated assignment in K16", label, arm))
                        for point in points:
                            if not point["mapping"]:
                                raise AssertionError(("Empty mapping", label, arm))
                            key = (cohort, dag, seed, speed, arm, point["mapping"])
                            if key in original:
                                raise AssertionError(("Repeated original key", key))
                            original[key] = dict(
                                cohort=cohort, dag=dag, seed=seed, speed=speed, arm=arm,
                                mapping=point["mapping"],
                                candidate_index=int(point["candidate_index"]),
                                **{k: positive_number(point[k]) for k in METRICS}
                            )
    if len(original) != 1792:
        raise AssertionError(("Original count mismatch", len(original)))
    return original


def speed_effect(default, staggered):
    """Percentage change; compare like-for-like mapping, not separate optimizer populations."""
    pm = 100 * (staggered["planned_makespan"] / default["planned_makespan"] - 1)
    sm = 100 * (staggered["sim_makespan"] / default["sim_makespan"] - 1)
    pc = 100 * (staggered["planned_cost"] / default["planned_cost"] - 1)
    sc = 100 * (staggered["sim_cost"] / default["sim_cost"] - 1)
    return dict(
        planned_makespan_change_pct=pm, actual_makespan_change_pct=sm,
        makespan_effect_gap_pp=pm-sm,
        default_signed_makespan_bias_pct=100*(default["planned_makespan"]/default["sim_makespan"]-1),
        staggered_signed_makespan_bias_pct=100*(staggered["planned_makespan"]/staggered["sim_makespan"]-1),
        planned_cost_change_pct=pc, actual_cost_change_pct=sc,
        cost_effect_gap_pp=pc-sc,
    )


def compare_speed(original):
    """Keep solver repeated mappings explicit; separately deduplicate physical schedules."""
    rows = []
    coverage = []
    physical = defaultdict(list)
    for cohort, dags, seeds, _ in GROUPS:
        for dag in dags:
            for seed in seeds:
                for arm in ARMS:
                    keybase = (cohort, dag, seed)
                    left = {k[-1]: v for k, v in original.items()
                            if k[:3] == keybase and k[3] == "default" and k[4] == arm}
                    right = {k[-1]: v for k, v in original.items()
                             if k[:3] == keybase and k[3] == "staggered" and k[4] == arm}
                    if len(left) != 16 or len(right) != 16:
                        raise AssertionError(("Unbalanced matched inputs", keybase, arm))
                    intersection = sorted(left.keys() & right.keys())
                    coverage.append(dict(cohort=cohort, dag=dag, seed=seed, arm=arm,
                                         default_n=16, staggered_n=16,
                                         same_mapping_overlap_n=len(intersection),
                                         overlap_fraction=len(intersection)/16))
                    for mapping in intersection:
                        d, s = left[mapping], right[mapping]
                        row = dict(cohort=cohort, dag=dag, seed=seed, arm=arm, mapping=mapping,
                                   default_candidate_index=d["candidate_index"],
                                   staggered_candidate_index=s["candidate_index"],
                                   **{("default_"+metric):d[metric] for metric in METRICS},
                                   **{("staggered_"+metric):s[metric] for metric in METRICS},
                                   **speed_effect(d, s))
                        rows.append(row)
                        physical[(cohort, dag, seed, mapping)].append((d, s))
    unique = []
    for (cohort, dag, seed, mapping), observations in sorted(physical.items()):
        # Duplicate schedules selected by different optimizers are NOT independent samples.
        # Compare their original outcomes before collapsing to one physical schedule.
        d = {metric:statistics.median(x[0][metric] for x in observations) for metric in METRICS}
        s = {metric:statistics.median(x[1][metric] for x in observations) for metric in METRICS}
        max_rel_spread = max(
            (max(z[side][metric] for z in observations)-
             min(z[side][metric] for z in observations)) /
            max(1, abs(statistics.median(z[side][metric] for z in observations)))
            for side in (0, 1) for metric in METRICS
        )
        unique.append(dict(cohort=cohort, dag=dag, seed=seed, mapping=mapping,
                           repeated_arm_observations=len(observations),
                           max_relative_cross_arm_disagreement=max_rel_spread,
                           cross_arm_consistent=int(max_rel_spread <= TOL),
                           **speed_effect(d, s)))
    return rows, coverage, unique


def write_csv(path, records):
    if not records:
        raise AssertionError(("No records for CSV", str(path)))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def analysis(root, out):
    original = load_originals(root)
    rows, coverage, unique = compare_speed(original)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "matched_speed_arm_rows.csv", rows) if rows else None
    write_csv(out / "matched_speed_unique_rows.csv", unique) if unique else None
    write_csv(out / "matched_speed_coverage.csv", coverage)
    conflicts = [x for x in unique if not x["cross_arm_consistent"]]
    good = [x for x in unique if x["cross_arm_consistent"]]
    lines = [
        "# Same-genotype cross-VM-speed planned-vs-actual WorkflowSim diagnostic",
        "",
        "Read-only originals: GitHub Actions 41626382711 (real-source DAX) and 41631739331 (new synthetic). "
        "This does not execute an optimizer or simulator, invent counterfactual labels, or change the saved policies.",
        "",
        f"Validated {len(original)} original K16 replay records (28 scenario-seeds × 2 speeds × 4 arms × 16).",
        f"Matched cross-speed solver-specific replay pairs: **{len(rows)}** of 1792 source records.",
        f"Distinct physical (cohort, DAG, seed, mapping) cross-speed pairs: **{len(unique)}**.",
        f"Distinct pairs cross-arm-consistent within relative tolerance {TOL:g}: **{len(good)}**; "
        f"disagreements: **{len(conflicts)}**.",
        "",
        "Overlap is measured as exact assignment-string identity WITHIN the same DAG and optimizer seed. "
        "A different DAG, optimizer seed or discrete VM mapping is never treated as a paired schedule. "
        "Multiple optimizer arms reusing a mapping contribute only ONE physical schedule in the deduplicated analysis.",
        "",
        "| Cohort | Matched solver pairs | Mean overlap /16 per arm | Distinct physical pairs |",
        "|---|---:|---:|---:|",
    ]
    for cohort, *_ in GROUPS:
        x = [r for r in rows if r["cohort"] == cohort]
        c = [r for r in coverage if r["cohort"] == cohort]
        u = [r for r in unique if r["cohort"] == cohort]
        lines.append(f"| {cohort} | {len(x)} | {statistics.mean(z['same_mapping_overlap_n'] for z in c):.3f} | {len(u)} |")
    lines += ["", "## Error comparison on same assignments (descriptive, not independent observations)", ""]
    if good:
        lines += [
            f"- Physical matched-genotype mean actual makespan VM-speed change: "
            f"**{statistics.mean(z['actual_makespan_change_pct'] for z in good):+.4f}%**.",
            f"- Mean planner-predicted VM-speed change on the SAME schedules: "
            f"**{statistics.mean(z['planned_makespan_change_pct'] for z in good):+.4f}%**.",
            f"- Mean signed (planned minus true percentage effect): "
            f"**{statistics.mean(z['makespan_effect_gap_pp'] for z in good):+.4f} percentage points**.",
            f"- Mean absolute percentage-point effect discrepancy: "
            f"**{statistics.mean(abs(z['makespan_effect_gap_pp']) for z in good):.4f} pp**.",
            f"- Median absolute effect discrepancy: "
            f"**{statistics.median(abs(z['makespan_effect_gap_pp']) for z in good):.4f} pp**.",
        ]
    else:
        lines.append("No consistent cross-speed physical pairs: do not estimate a matched VM-speed effect.")
    if conflicts:
        lines.append(f"WARNING: {len(conflicts)} cross-arm same-mapping objective conflicts. "
                     "These are excluded from the summary; inspect unique CSV before causal interpretation.")
    lines += [
        "", "## Validity boundaries",
        "This is a FIXED-assignment cross-VM-profile contrast, not a controlled separation of execution speed "
        "from changed scheduling order, file-stage-in timing, or simulator replay state.",
        "The overlap-selected schedules are not representative of all 3030 visited plans; overlap may be "
        "dominated by the two common low-cost seeded mappings. Per-arm duplicates are correlated.",
        "Only previously observed real WorkflowSim outcomes are used, after selection. "
        "No unobserved simulator output is estimated or selected into the audit.",
        "If the exact-cross-speed intersection is sparse, treat the result as an engineering smoke test, "
        "not a general fidelity estimate or novel algorithm.",
        "Neither improved actual HV nor publication-level significance follows from this offline audit.",
    ]
    (out / "matched_speed_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: fla_matched_speed_fidelity.py ORIGINAL_ARTIFACT_ROOT OUTPUT_DIR")
    analysis(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
