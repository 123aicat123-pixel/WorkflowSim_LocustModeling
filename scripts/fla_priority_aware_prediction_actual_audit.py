#!/usr/bin/env python3
"""Independent read-only assessment of immutable priority-aware forecast outputs.

Original simulator Actions 41681448520; 36 complete actual WorkflowSim calls.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_100","Montage_100","Sipht_60")
ALLOCATIONS=("all_vm0","all_vm12","round_robin","stride7")
PRIORITIES=("fifo","shortest","upward")

def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def audit(src,out):
    out.mkdir(parents=True,exist_ok=True)
    observations=[]
    for dag in DAGS:
        folders=[f for f in src.iterdir() if f.is_dir() and f.name.startswith("fla-priority-forecast-"+dag+"-")]
        if len(folders)!=1:raise AssertionError(("Unique original simulation artifact missing",dag,folders))
        r=read(folders[0]/"all_actual_priority_forecasts.csv")
        if len(r)!=12:raise AssertionError(("Not 12 original policy cases",dag,len(r)))
        ids=set()
        for row in r:
            key=(row["mapping"],row["priority"])
            if row["workflow"]!=dag or key in ids or key not in set(itertools.product(ALLOCATIONS,PRIORITIES)):
                raise AssertionError(("Unregistered, repeated, or missing work",dag,key))
            ids.add(key)
            for name in ("actual_makespan","priority_aware_makespan","old_task_id_model_pct",
                         "priority_aware_model_pct","delta_abs_error_pp","old_task_id_model_cost_pct",
                         "priority_aware_model_cost_pct","priority_task_mae_start_s",
                         "priority_task_mae_finish_s"):
                val=float(row[name])
                if not math.isfinite(val):raise AssertionError(("Nonfinite result",name,key))
            old=float(row["old_task_id_model_pct"])
            new=float(row["priority_aware_model_pct"])
            if not math.isclose(new-old,float(row["delta_abs_error_pp"]),rel_tol=1e-8,abs_tol=1e-7):
                raise AssertionError(("Invalid reported delta",dag,key))
            observations.append(dict(row))
        if ids!=set(itertools.product(ALLOCATIONS,PRIORITIES)):
            raise AssertionError(("Incomplete original cases",dag))
    if len(observations)!=36:raise AssertionError("Missing actual simulator cases")
    with (out/"all_36_forecast_cases.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)
    results=[]
    for dag in DAGS:
        for allocation in ALLOCATIONS:
            z={x["priority"]:x for x in observations if (x["workflow"],x["mapping"])==(dag,allocation)}
            baseline=z["fifo"]
            actual_ref=float(baseline["actual_makespan"])
            predicted_ref=float(baseline["priority_aware_makespan"])
            for priority in ("shortest","upward"):
                row=z[priority]
                true_delta=100*(float(row["actual_makespan"])/actual_ref-1)
                pred_delta=100*(float(row["priority_aware_makespan"])/predicted_ref-1)
                results.append(dict(workflow=dag,mapping=allocation,priority=priority,
                                    actual_change_pct=true_delta,predicted_change_pct=pred_delta,
                                    effect_gap_pp=pred_delta-true_delta))
    with (out/"all_24_priority_effect_predictions.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    report=[
        "# Frozen 36-replay priority-aware prediction fidelity independent audit",
        "",
        "Original actual simulator source: [GitHub Actions 41681448520](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41681448520).",
        "3 DAG instances × 4 identical VM mapping policies × 3 runtime priority policies = 36 real simulator replays; all matched previous uninstrumented actual Makespan/Cost with source parity checks.",
        "All reported model quantities are BEFORE the actual simulator outcome and are not tuned to current outcomes; however the DAGs and 10.65% case were already known before the predictor, so this is development, NOT an unseen holdout.",
        "",
        "| DAG | Runtime priority | Task-ID ready model mean absolute makespan % error | Policy-aware mean absolute makespan % error | Improved / tied / worse individual mappings |",
        "|---|---|---:|---:|---:|"
    ]
    all_deltas=[]
    for dag in DAGS:
        for policy in PRIORITIES:
            z=[x for x in observations if x["workflow"]==dag and x["priority"]==policy]
            changes=[float(x["delta_abs_error_pp"]) for x in z]
            all_deltas+=changes
            report.append(f"| {dag} | {policy} | "
                f"{statistics.mean(float(x['old_task_id_model_pct']) for x in z):.6f} | "
                f"{statistics.mean(float(x['priority_aware_model_pct']) for x in z):.6f} | "
                f"{sum(v<-1e-8 for v in changes)}/{sum(abs(v)<=1e-8 for v in changes)}/{sum(v>1e-8 for v in changes)} |")
    report+=["", "## Practically relevant priority interventions (>0.1% absolute actual Makespan change)"]
    relevant=[x for x in results if abs(x["actual_change_pct"])>.1]
    for x in sorted(relevant,key=lambda z:-abs(z["actual_change_pct"])):
        report.append(f"- {x['workflow']} {x['mapping']} {x['priority']}: "
            f"actual effect {x['actual_change_pct']:+.6f}%, predicted {x['predicted_change_pct']:+.6f}%, "
            f"error {x['effect_gap_pp']:+.6f} pp.")
    report+=["",
      f"All-case mean absolute makespan error old={statistics.mean(float(x['old_task_id_model_pct']) for x in observations):.6f}%, "
      f"priority-aware={statistics.mean(float(x['priority_aware_model_pct']) for x in observations):.6f}%.",
      f"Across 36 model forecasts: improved/tied/worse = {sum(x<-1e-8 for x in all_deltas)}/"
      f"{sum(abs(x)<=1e-8 for x in all_deltas)}/{sum(x>1e-8 for x in all_deltas)}.",
      "",
      "## Interpretation / risks",
      "An accurate match of the two large Sipht priority effects is a meaningful fixed-mapping engineering result, but CyberShake shortest mispredicts the sign for its >0.1% intervention. The decoder is NOT universally reliable; arbitrary policy optimization can still exploit false ranking.",
      "A policy-aware predictor shared by FLA and seeded NSGA-II is a decoder contribution, not FLA-specific search novelty. Before joint priority + mapping search, predeclare an unseen-DAG test or a robust policy-risk screen; avoid tuning on these 36 already observed simulator labels.",
      "Task pairs/36 simulator calls are highly correlated within only three DAG instances and one seed; report no statistical significance or journal-readiness claim."
    ]
    (out/"priority_aware_forecast_conclusions.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_SIMULATOR_ARTIFACTS REPORTS_DIR")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
