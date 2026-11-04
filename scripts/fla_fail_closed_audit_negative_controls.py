#!/usr/bin/env python3
"""Negative-control unit oracle for paired diagnostic-on/off audit.

This fixture is synthetic and exercises only audit rejection behavior.
It is NEVER a WorkflowSim experiment or a scientific performance result.
"""
import csv
import pathlib
import tempfile
import fla_fail_closed_probe_nonintrusion_audit as audit


def write(prefix, suffix, records):
    path = pathlib.Path(str(prefix) + suffix)
    with path.open("w", newline="", encoding="utf-8") as handle:
        out = csv.DictWriter(handle, fieldnames=list(records[0]))
        out.writeheader()
        out.writerows(records)


def reject(task, label):
    try:
        task()
    except (AssertionError, ValueError, KeyError):
        return
    raise AssertionError("Audit accepted corrupted evidence: " + label)


def trial():
    with tempfile.TemporaryDirectory() as root:
        root = pathlib.Path(root)
        active, passive = root / "probe", root / "control"
        algs = ["DAG-Pareto-FLA[v12-hvbandit]", "NSGA-II[costseed]"]
        fingerprint = [
            dict(algorithm=a, workflow="Montage_25", seed="801",
                 distinct_visited="4", history_sha256=("%064x" % (j + 1)))
            for j, a in enumerate(algs)
        ]
        summary = [
            dict(algorithm=a, workflow="Montage_25", seed="801",
                 population="8", generations="6", evaluations="56",
                 captured_evaluations="56", distinct_observed="4",
                 replayed="2", source_archive="3",
                 distinct_planned_nondominated="2", sim_nondominated="2",
                 sim_ref_m="100", sim_ref_c="200",
                 plan_ref_m="100", plan_ref_c="200",
                 sim_hv="0.45", planned_hv="0.5", search_ms="10",
                 selection_ms="1", replay_ms="2", search_selection_replay_ms="13")
            for a in algs
        ]
        replay = [
            dict(algorithm=a, candidate_index=str(i),
                 workflow="Montage_25", seed="801",
                 mapping="1:0|2:1", planned_makespan="30",
                 planned_cost="40", independent_planned_makespan="30",
                 independent_planned_cost="40", sim_makespan="31",
                 sim_cost="41")
            for a in algs for i in (1, 2)
        ]
        probe = [
            dict(algorithm=a, pair=str(i),
                 first_assignment=f"1={i};2=0",
                 second_assignment=f"1={i};2=1",
                 decision="READY_ESTIMATES_AVAILABLE" if i == 1 else "KEEP_BOTH",
                 old_first_m="20", old_first_c="21",
                 old_second_m="30", old_second_c="31",
                 ready_calls="2", ready_budget="2",
                 old_calls=str(2*i))
            for a in algs for i in (1, 2)
        ]
        protocol = "PROSPECTIVE_REPLAY_BUDGET_K=2\nPROSPECTIVE_REPLAY_POLICY=pareto-cover\n"
        for prefix in (active, passive):
            write(prefix, "_visited_fingerprints.csv", fingerprint)
            write(prefix, "_summary.csv", summary)
            write(prefix, "_replays.csv", replay)
            pathlib.Path(str(prefix)+"_budget_protocol.txt").write_text(protocol)
        write(active, "_fail_closed_probe.csv", probe)
        audit.audit(active, passive, 2, 2)

        path = pathlib.Path(str(active)+"_fail_closed_probe.csv")
        initial = path.read_bytes()
        try:
            path.write_text("algorithm,pair\n", encoding="utf-8")
            reject(lambda: audit.audit(active, passive, 2, 2), "empty probe")
            write(active, "_fail_closed_probe.csv", probe[:2])
            reject(lambda: audit.audit(active, passive, 2, 2), "missing solver probe")
            corrupt = [dict(r) for r in probe]
            corrupt[0]["decision"] = "CONDITIONAL_FIRST_DOMINATES"
            write(active, "_fail_closed_probe.csv", corrupt)
            reject(lambda: audit.audit(active, passive, 2, 2), "uncalibrated dominance")
            corrupt = [dict(r) for r in probe]
            corrupt[0]["second_assignment"] = corrupt[0]["first_assignment"]
            write(active, "_fail_closed_probe.csv", corrupt)
            reject(lambda: audit.audit(active, passive, 2, 2), "same physical mapping")
        finally:
            path.write_bytes(initial)

        changed_summary = [dict(r) for r in summary]
        changed_summary[0]["sim_hv"] = "0.47"
        write(passive, "_summary.csv", changed_summary)
        reject(lambda: audit.audit(active, passive, 2, 2), "actual HV drift")
        write(passive, "_summary.csv", summary)

        changed_replay = [dict(r) for r in replay]
        changed_replay[0]["mapping"] = "1:1|2:0"
        write(passive, "_replays.csv", changed_replay)
        reject(lambda: audit.audit(active, passive, 2, 2), "physical mapping drift")
        write(passive, "_replays.csv", replay)
        audit.audit(active, passive, 2, 2)
    print("PASS audit negative controls: empty/missing/corrupt probe, HV and mapping drift all rejected")


if __name__ == "__main__":
    trial()
