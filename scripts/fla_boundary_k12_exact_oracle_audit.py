#!/usr/bin/env python3
"""Exact post-hoc K12+4 replacement ceiling using original TRUE simulator labels.

This is an unattainable hindsight oracle for DIAGNOSIS only. It reads the 24
immutable original source artifacts from run 41975729241; it does not call
the optimizer, READY model, or simulator, and it must not guide test selection.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

RUN = "41975729241"
WORKFLOWS = ("Montage_50", "Inspiral_50", "CyberShake_30", "Epigenomics_46")
SEEDS = (971, 972)
POLICIES = ("pareto-cover", "boundary-four", "dominated-random-four")
SOLVERS = ("DAG-Pareto-FLA[v12-hvbandit]", "NSGA-II[costseed]")
SOURCE_SHA = "197ffc5ddb828425b25280a1f83d9911cf21d3f3"
TOL = 1e-10


def records(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def dominates(a, b):
    return (a[0] <= b[0] and a[1] <= b[1] and
            (a[0] < b[0] or a[1] < b[1]))


def hv(points, ref):
    unique = set(points)
    nd = sorted(p for p in unique if not any(dominates(q, p) for q in unique))
    top = ref[1]
    area = 0.
    for m, c in nd:
        if m < ref[0] and c < top:
            area += (ref[0] - m) * (top - c)
            top = c
    value = area / (ref[0] * ref[1])
    assert math.isfinite(value) and -TOL <= value <= 1 + TOL, value
    return value


def save(path, rows):
    assert rows
    with path.open("w", newline="", encoding="utf-8") as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)


def source(root, dag, seed, policy):
    folder = root / f"fla-boundary-four-{dag}-s{seed}-{policy}-{RUN}"
    assert folder.is_dir(), ("Missing immutable source", str(folder))
    info = dict(x.split("=", 1) for x in (folder / "block-id.txt").read_text().split())
    assert info == dict(DAG=dag, seed=str(seed), policy=policy,
                        K="16", visits="3030", VM="default"), info
    assert (folder / "source-sha.txt").read_text().strip() == SOURCE_SHA
    summaries = records(folder / "research_summary.csv")
    replays = records(folder / "research_replays.csv")
    fingerprints = records(folder / "research_visited_fingerprints.csv")
    assert len(summaries) == len(fingerprints) == 2 and len(replays) == 32
    assert {x["algorithm"] for x in summaries} == set(SOLVERS)
    assert {x["algorithm"] for x in fingerprints} == set(SOLVERS)
    result = {}
    for solver in SOLVERS:
        summary = next(x for x in summaries if x["algorithm"] == solver)
        fingerprint = next(x for x in fingerprints if x["algorithm"] == solver)
        assert summary["workflow"] == dag and summary["seed"] == str(seed)
        assert tuple(int(summary[k]) for k in (
            "population", "generations", "evaluations",
            "captured_evaluations", "replayed")) == (30, 100, 3030, 3030, 16)
        assert len(fingerprint["history_sha256"]) == 64
        rs = sorted((x for x in replays if x["algorithm"] == solver),
                    key=lambda x: int(x["candidate_index"]))
        assert len(rs) == 16 and len({x["mapping"] for x in rs}) == 16
        assert [int(x["candidate_index"]) for x in rs] == list(range(1, 17))
        mapping = []
        for row in rs:
            assert row["workflow"] == dag and row["seed"] == str(seed)
            truth = (float(row["sim_makespan"]), float(row["sim_cost"]))
            planned = (float(row["planned_makespan"]), float(row["planned_cost"]))
            assert all(math.isfinite(v) and v > 0 for v in truth + planned)
            mapping.append((row["mapping"], truth, planned))
        result[solver] = (fingerprint["history_sha256"], mapping)
    return result


def audit(root, report):
    report.mkdir(parents=True, exist_ok=True)
    all_cases = {}
    for dag, seed, policy in itertools.product(WORKFLOWS, SEEDS, POLICIES):
        case = source(root, dag, seed, policy)
        for solver in SOLVERS:
            all_cases[dag, seed, solver, policy] = case[solver]
    assert len(all_cases) == 48

    results = []
    choices = []
    for dag, seed, solver in itertools.product(WORKFLOWS, SEEDS, SOLVERS):
        arms = {p: all_cases[dag, seed, solver, p] for p in POLICIES}
        assert len({v[0] for v in arms.values()}) == 1, (
            "Source optimizer visited history differs across policies", dag, seed, solver)
        base = arms["pareto-cover"][1]
        boundary = arms["boundary-four"][1]
        random = arms["dominated-random-four"][1]
        assert [x[0] for x in base[:12]] == [x[0] for x in boundary[:12]] == [
            x[0] for x in random[:12]], "K12 shared anchors differ"
        known = {}
        sources = {}
        for policy, (_, rows) in arms.items():
            for key, actual, planned in rows:
                if key in known:
                    previous, _ = known[key]
                    assert all(abs(previous[i] - actual[i]) <=
                               1e-7 * max(1, abs(previous[i]), abs(actual[i]))
                               for i in (0, 1)), ("Same map has conflicting simulator truth", dag, seed, solver)
                else:
                    known[key] = (actual, planned)
                sources.setdefault(key, set()).add(policy)
        # Reference shared ACROSS BOTH solvers and all three modes, not per algorithm.
        # Resolve actual 2D values for all solver/policy replay points.
        common = [item[1] for other_solver in SOLVERS for policy in POLICIES
                  for item in all_cases[dag, seed, other_solver, policy][1]]
        refs = {factor: tuple(factor * max(v[i] for v in common) + 1e-6
                              for i in (0, 1)) for factor in (1.5, 3.0)}

        anchors = [x[0] for x in base[:12]]
        baseline = [x[0] for x in base]
        remaining = sorted(set(x[0] for seq in (base, boundary, random)
                               for x in seq[12:]))
        assert len(remaining) >= 4
        assert all(key not in anchors for key in remaining)
        assert set(baseline[12:]).issubset(set(remaining))
        def score(keys, factor):
            return hv([known[k][0] for k in keys], refs[factor])

        prior = score(baseline, 1.5)
        boundary_hv = score([x[0] for x in boundary], 1.5)
        random_hv = score([x[0] for x in random], 1.5)
        # Exact maximizer (with deterministic lexicographic tie) of K12+4
        # among the 4 original + 4 boundary + 4 random already-tested tails.
        optimal = None
        optimal_hv = -float("inf")
        for subset in itertools.combinations(remaining, 4):
            value = score(anchors + list(subset), 1.5)
            if value > optimal_hv + 1e-12 or (
                abs(value - optimal_hv) <= 1e-12 and
                (optimal is None or subset < optimal)):
                optimal_hv = value
                optimal = subset
        assert optimal is not None
        assert optimal_hv + 1e-10 >= max(prior, boundary_hv, random_hv)
        one_swap = prior
        best_one = ("", "")
        for incoming in remaining:
            if incoming in baseline:
                continue
            for outgoing in baseline[12:]:
                swapped = [k for k in baseline if k != outgoing] + [incoming]
                value = score(swapped, 1.5)
                if value > one_swap + 1e-12:
                    one_swap = value
                    best_one = (outgoing, incoming)

        optimal3 = score(anchors + list(optimal), 3.0)
        baseline3 = score(baseline, 3.0)
        tag = "FLA" if solver == SOLVERS[0] else "NSGA-II"
        results.append(dict(workflow=dag, seed=seed, solver=solver, solver_short=tag,
            unique_tail_maps=len(remaining),
            new_alternative_tail_maps=len(set(remaining)-set(baseline[12:])),
            exact_subsets_checked=math.comb(len(remaining), 4),
            baseline_hv15=prior,
            boundary_hv15=boundary_hv,
            random_hv15=random_hv,
            hindsight_optimal_hv15=optimal_hv,
            hindsight_oracle_ceiling_above_baseline15=optimal_hv-prior,
            hindsight_oracle_ceiling_above_boundary15=optimal_hv-boundary_hv,
            best_single_exchange_delta15=one_swap-prior,
            hindsight_optimal_minus_baseline_3x=optimal3-baseline3,
            original_tail_retained_by_oracle=sum(x in optimal for x in baseline[12:]),
            source_sha=SOURCE_SHA))
        for key in optimal:
            choices.append(dict(workflow=dag, seed=seed, solver=solver,
                selection="POSTHOC_TRUE_ORACLE_NOT_DEPLOYABLE",
                mapping=key, source_policies="|".join(sorted(sources[key])),
                true_makespan=known[key][0][0], true_cost=known[key][0][1],
                planned_makespan=known[key][1][0], planned_cost=known[key][1][1]))
    assert len(results) == 16 and len(choices) == 64
    save(report/"all_16_exact_K12_plus4_hindsight_oracle.csv", results)
    save(report/"all_64_posthoc_oracle_tail_choices.csv", choices)
    summary = [
        "# Exact hindsight K12+4 headroom on 768 REAL WorkflowSim observations",
        "",
        "This is an UNDEPLOYABLE TRUE-LABEL ORACLE, not a result of a prospective policy.",
        "Every 16-choice source arm and every original search SHA is verified, including",
        "full source code SHA, physical K12 identity and repeated assignment truth.",
        "Within each workflow/seed, all arm/solver HV references are identical.",
        "Only 4 candidate replacements are allowed and original K12 is fixed;",
        "enumeration checks ALL four-subsets from the union of 12 already-replayed tails.",
        "Nothing is inferred for the unobserved 3030-visited candidates or global Pareto optimum.", "",
        "| DAG | seed | Solver | Distinct tail maps | Baseline HV15 | Exact hindsight K16 HV15 | Ceiling gain | Best 1-swap gain |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for row in results:
        summary.append(f"| {row['workflow']} | {row['seed']} | {row['solver_short']} | "
                       f"{row['unique_tail_maps']} | {row['baseline_hv15']:.9f} | "
                       f"{row['hindsight_optimal_hv15']:.9f} | "
                       f"{row['hindsight_oracle_ceiling_above_baseline15']:+.9f} | "
                       f"{row['best_single_exchange_delta15']:+.9f} |")
    for group in ("FLA", "NSGA-II"):
        cohort = [r for r in results if r["solver_short"] == group]
        gains = [r["hindsight_oracle_ceiling_above_baseline15"] for r in cohort]
        ones = [r["best_single_exchange_delta15"] for r in cohort]
        summary.append(f"- {group}: exact hindsight gain mean={statistics.mean(gains):+.9f}, "
                       f"positive / zero={sum(v>1e-10 for v in gains)}/"
                       f"{sum(v<=1e-10 for v in gains)}, "
                       f"best 1-swap positive={sum(v>1e-10 for v in ones)}, "
                       f"max={max(gains):+.9f}.")
    summary += ["",
        "This bound is exact ONLY under the frozen K12 anchor and the observed source tail union.",
        "It is not a global upper bound and it does not demonstrate a learnable gate.",
        "If the oracle margin is tiny, calibrating a replacement gate on these inspected",
        "examples is particularly unlikely to justify its complexity.",
        "No source outcomes are recomputed, no new physical simulator calls, no SCI superiority claim."]
    (report/"exact_hindsight_oracle_findings.md").write_text(
        "\n".join(summary)+"\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Usage: script.py ORIGINAL_ARTIFACT_ROOT OUTPUT_FOLDER"
    audit(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
