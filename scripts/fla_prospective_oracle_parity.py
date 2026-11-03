#!/usr/bin/env python3
"""Prove actual K limited WorkflowSim replays match offline oracle choice and labels.

Input: two independent fresh experiments from the SAME Java source commit/seed:
one full visited-history WorkflowSim audit and one prospective K replay.
The full history serves as a POST-HOC oracle, and is never used to select in
the prospective experiment. Assertions are per algorithm, not only aggregate HV.
"""
import csv
import importlib.util
import pathlib
import sys

def load(filename):
    with open(filename, newline="") as f:
        return list(csv.DictReader(f))

def oracle():
    path = pathlib.Path(__file__).with_name("fla_replay_budget_audit.py")
    spec = importlib.util.spec_from_file_location("fla_replay_budget_oracle_retest", path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = obj
    spec.loader.exec_module(obj)
    return obj

def run(full_prefix, prospective_prefix, k):
    full = load(full_prefix + "_replays.csv") + load(full_prefix + "_screening_samples.csv")
    k_rows = load(prospective_prefix + "_replays.csv")
    full_summary = {r["algorithm"]: r for r in load(full_prefix + "_summary.csv")}
    prospective_summary = {r["algorithm"]: r for r in load(prospective_prefix + "_summary.csv")}
    full_audit = {r["algorithm"]: r for r in load(full_prefix + "_screening_summary.csv")}
    assert len(full_summary) == len(prospective_summary) == len(full_audit) == 3
    assert set(full_summary) == set(prospective_summary) == set(full_audit)
    assert len(k_rows) == 3*k
    lib = oracle()
    for alg in sorted(full_summary):
        a = [r for r in full if r["algorithm"] == alg]
        b = [r for r in k_rows if r["algorithm"] == alg]
        assert len(a) == int(full_audit[alg]["unique_visited"])
        assert len(b) == k
        assert len({r["mapping"] for r in a}) == len(a)
        assert len({r["mapping"] for r in b}) == k
        assert int(full_summary[alg]["evaluations"]) == int(prospective_summary[alg]["evaluations"]) == 80
        assert int(full_summary[alg]["captured_evaluations"]) == int(prospective_summary[alg]["captured_evaluations"]) == 80
        assert int(prospective_summary[alg]["replayed"]) == k
        choices = [
            lib.Planned(r["mapping"], float(r["planned_makespan"]), float(r["planned_cost"]))
            for r in a
        ]
        expected = [x.mapping for x in lib.choose(choices, ("oracle", 0, alg), "pareto-cover", k, 0)]
        actual = [r["mapping"] for r in b]
        assert expected == actual, {
            "algorithm": alg, "python_selected": expected, "java_prospective": actual
        }
        truth = {r["mapping"]:r for r in a}
        for r in b:
            old = truth[r["mapping"]]
            for field in ("planned_makespan", "planned_cost", "sim_makespan", "sim_cost"):
                assert abs(float(old[field]) - float(r[field])) <= 1.e-8 * max(1.,abs(float(old[field]))), (alg,field,r["mapping"])
        print("PASS REAL CASE", a[0]["workflow"], "seed", a[0]["seed"],
              "algorithm", alg, "K", k,
              "same-order", True, "same actual independent WorkflowSim objective", True,
              "full-visited", len(a))
    print("PASS all 3 solver arms: exact Python-oracle selection, real K selection and simulator objectives agree")

if __name__ == "__main__":
    assert len(sys.argv) == 4, "usage: fla_prospective_oracle_parity.py FULL_PREFIX PROSPECTIVE_PREFIX K"
    run(sys.argv[1], sys.argv[2], int(sys.argv[3]))
