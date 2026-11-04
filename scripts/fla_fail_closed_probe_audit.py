#!/usr/bin/env python3
"""Independent read-only audit of opt-in, pre-replay FLA/NSGA two-model probe.

No synthetic objectives are called. This validates source trace provenance,
quota, non-certification, assignment identity, and 2 actual K replays per solver.
It is NOT a calibrated-model validation or an optimizer-performance result.
"""
import argparse
import collections
import csv
import math
import pathlib
import re


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def positive(value):
    return math.isfinite(float(value)) and float(value) > 0


def mapping(value):
    result = {}
    for piece in value.split(";"):
        if not re.fullmatch(r"\d+=\d+", piece):
            raise AssertionError("Invalid canonical physical mapping: " + value[:100])
        task, vm = map(int, piece.split("="))
        assert task not in result, "Duplicate task ID"
        result[task] = vm
    assert result, "Empty mapping"
    assert list(result) == sorted(result), "Noncanonical ordering"
    return result


def audit(prefix, pairs, ready_budget, tasks, k, expected_evals):
    prefix = pathlib.Path(prefix)
    probe = rows(pathlib.Path(str(prefix) + "_fail_closed_probe.csv"))
    summary = rows(pathlib.Path(str(prefix) + "_summary.csv"))
    replays = rows(pathlib.Path(str(prefix) + "_replays.csv"))
    fingerprints = rows(pathlib.Path(str(prefix) + "_visited_fingerprints.csv"))
    protocol = pathlib.Path(str(prefix) + "_budget_protocol.txt").read_text(encoding="utf-8")
    log = pathlib.Path(str(prefix) + ".log").read_text(encoding="utf-8")
    assert len(summary) == 2, ("Expected one FLA and one NSGA-II solver", len(summary))
    algorithms = [row["algorithm"] for row in summary]
    assert len(set(algorithms)) == 2
    assert any("FLA" in s for s in algorithms) and any("NSGA-II" in s for s in algorithms)
    assert len(probe) == 2 * pairs
    assert len(replays) == 2 * k
    assert len(fingerprints) == 2
    assert set(row["algorithm"] for row in probe) == set(algorithms)
    assert set(row["algorithm"] for row in replays) == set(algorithms)
    assert set(row["algorithm"] for row in fingerprints) == set(algorithms)
    assert "PROSPECTIVE_REPLAY_BUDGET_K=" + str(k) in protocol
    assert "PROSPECTIVE_REPLAY_POLICY=pareto-cover" in protocol
    marker = log.find("PASS pre-replay uncalibrated fail-closed mapping probe frozen")
    replay_start = log.find("REPLAY Montage_25 ")
    assert marker != -1 and replay_start > marker, "Diagnostic must freeze before K real replays"
    grouped = collections.defaultdict(list)
    for row in probe:
        grouped[row["algorithm"]].append(row)
    for s in summary:
        algo = s["algorithm"]
        assert int(s["evaluations"]) == int(s["captured_evaluations"]) == expected_evals
        assert int(s["replayed"]) == k
        assert int(s["distinct_observed"]) >= pairs * 2
        ids = set()
        for i, rec in enumerate(grouped[algo]):
            assert int(rec["pair"]) == i + 1
            a, b = mapping(rec["first_assignment"]), mapping(rec["second_assignment"])
            assert len(a) == len(b) == tasks
            assert set(a) == set(b)
            assert rec["first_assignment"] != rec["second_assignment"]
            ids.update((rec["first_assignment"], rec["second_assignment"]))
            for name in ("old_first_m","old_first_c","old_second_m","old_second_c"):
                assert positive(rec[name]), (name, rec[name])
            assert int(rec["old_calls"]) == 2 * (i + 1)
            assert int(rec["old_cache_hits"]) == 0
            assert int(rec["ready_budget"]) == ready_budget
            assert int(rec["ready_calls"]) <= ready_budget
            assert int(rec["ready_cache_hits"]) == 0
            assert rec["decision"] not in (
                "CONDITIONAL_FIRST_DOMINATES","CONDITIONAL_SECOND_DOMINATES"
            ), "Uncalibrated probe must abstain from certifying truth"
            if rec["decision"] == "READY_ESTIMATES_AVAILABLE":
                for name in ("ready_first_m","ready_first_c",
                             "ready_second_m","ready_second_c"):
                    assert positive(rec[name]), (name, rec[name])
            else:
                assert rec["decision"] == "KEEP_BOTH"
                for name in ("ready_first_m","ready_first_c",
                             "ready_second_m","ready_second_c"):
                    assert rec[name] == "", "No partial READY pairs allowed in output"
        assert len(ids) == pairs * 2, "Expected disjoint original optimizer genotypes"
        assert int(grouped[algo][-1]["ready_calls"]) <= ready_budget
        assert sum(1 for r in replays if r["algorithm"] == algo) == k
        for row in replays:
            if row["algorithm"] != algo:
                continue
            assert all(positive(row[name]) for name in
                       ("planned_makespan","planned_cost","sim_makespan","sim_cost"))
            parts = row["mapping"].split("|")
            assert len(parts) == tasks and len(set(parts)) == tasks
        fingerprint = next(r for r in fingerprints if r["algorithm"] == algo)
        assert int(fingerprint["distinct_visited"]) == int(s["distinct_observed"])
        assert re.fullmatch("[0-9a-f]{64}", fingerprint["history_sha256"])
    if ready_budget == 2 and pairs == 2:
        for algo in algorithms:
            seq = grouped[algo]
            assert [r["decision"] for r in seq] == [
                "READY_ESTIMATES_AVAILABLE","KEEP_BOTH"
            ]
            assert [int(r["ready_calls"]) for r in seq] == [2,2]
    print("PASS independent pre-replay Task/VM probe audit: two original optimizers, "
          f"{pairs} physical pairs each, K{k} real replays each; no uncalibrated certificates")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix")
    parser.add_argument("--pairs", type=int, default=2)
    parser.add_argument("--ready-budget", type=int, default=2)
    parser.add_argument("--tasks", type=int, default=25)
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--expected-evals", type=int, default=56)
    opts = parser.parse_args()
    audit(opts.prefix, opts.pairs, opts.ready_budget, opts.tasks,
          opts.k, opts.expected_evals)
