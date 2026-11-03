#!/usr/bin/env python3
"""Read-only complete holdout-ish new-instance predictor audit from true simulator Actions.

No fitted model changes. Original CI source 41682109356 contains eight blocks,
each with 3 actual WorkflowSim replay calls, 2 VM profiles x 2 placements x 2 DAGs.
"""
import csv, itertools, math, pathlib, statistics, sys

DAGS=("Inspiral_30","Epigenomics_100")
SPEEDS=("default","staggered")
MAPPINGS=("round_robin","stride7")
PRIORITIES=("fifo","shortest","upward")
EPS=1e-8
def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def analyze(root,out):
    out.mkdir(parents=True,exist_ok=True)
    allrows={}
    for dag,speed,mapping in itertools.product(DAGS,SPEEDS,MAPPINGS):
        prefix=f"fla-new-instance-priority-{dag}-{speed}-{mapping}-"
        candidates=[p for p in root.iterdir() if p.is_dir() and p.name.startswith(prefix)]
        if len(candidates)!=1:raise AssertionError(("missing/duplicate new instance",prefix,candidates))
        raw=read(candidates[0]/"three_actual_priority_forecasts.csv")
        if len(raw)!=3 or {x["priority"] for x in raw}!=set(PRIORITIES):
            raise AssertionError(("missing original priority",dag,speed,mapping))
        for row in raw:
            key=(dag,speed,mapping,row["priority"])
            if (row["workflow"],row["vm_profile"],row["placement"])!=(dag,speed,mapping) or key in allrows:
                raise AssertionError(("case identity mismatch",key,row))
            for field in ("actual_makespan","actual_cost","old_model_abs_pct",
                          "new_model_abs_pct","delta_abs_error_pp",
                          "actual_effect_pct","predicted_effect_pct","effect_error_pp",
                          "policy_start_mae_s","policy_finish_mae_s"):
                val=float(row[field])
                if not math.isfinite(val):raise AssertionError(("not finite",key,field))
            a=float(row["old_model_abs_pct"])
            b=float(row["new_model_abs_pct"])
            if not math.isclose(b-a,float(row["delta_abs_error_pp"]),rel_tol=1e-9,abs_tol=1e-7):
                raise AssertionError(("invalid model error gap",key))
            true=float(row["actual_effect_pct"])
            forecast=float(row["predicted_effect_pct"])
            if not math.isclose(forecast-true,float(row["effect_error_pp"]),rel_tol=1e-9,abs_tol=1e-7):
                raise AssertionError(("invalid signed effect gap",key))
            allrows[key]=dict(row)
    if len(allrows)!=24:
        raise AssertionError(("expected 24 true original cases",len(allrows)))
    ordered=[allrows[key] for key in sorted(allrows)]
    with (out/"all_24_actual_predictor_cases.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(ordered[0]));w.writeheader();w.writerows(ordered)
    deltas=[float(x["delta_abs_error_pp"]) for x in ordered]
    relevant=[x for x in ordered if x["priority"]!="fifo" and abs(float(x["actual_effect_pct"]))>.1]
    report=["# Frozen priority-aware decoder vs new DAX instance simulator gate",
            "", "Original immutable 24 real simulator calls: Actions 41682109356; all eight blocks frozen prior to outcomes.",
            "Two DAX instances (Inspiral_30 and Epigenomics_100) from historically known workflow FAMILIES, two VM-speed regimes and two algorithm-independent placements; all 24 original Task-ID/VM mappings verified by replay harness.",
            "No real CloudSim labels fed into prediction and no optimized policy chosen by an oracle.",
            "",
            "| DAX | VM profile | Cases | Task-ID ready mean abs Makespan error | Priority-aware mean abs Makespan error | Wins/Ties/Losses |",
            "|---|---|---:|---:|---:|---:|"]
    for dag,speed in itertools.product(DAGS,SPEEDS):
        rows=[v for k,v in allrows.items() if k[0]==dag and k[1]==speed]
        d=[float(x["delta_abs_error_pp"]) for x in rows]
        assert len(rows)==6
        report.append(f"| {dag} | {speed} | {len(rows)} | "
          f"{statistics.mean(float(x['old_model_abs_pct']) for x in rows):.5f}% | "
          f"{statistics.mean(float(x['new_model_abs_pct']) for x in rows):.5f}% | "
          f"{sum(x<-EPS for x in d)}/{sum(abs(x)<=EPS for x in d)}/{sum(x>EPS for x in d)} |")
    report+=["",
        f"All 24 cases: mean old MAPE={statistics.mean(float(x['old_model_abs_pct']) for x in ordered):.6f}%; "
        f"new MAPE={statistics.mean(float(x['new_model_abs_pct']) for x in ordered):.6f}%; "
        f"wins/ties/losses={sum(x<-EPS for x in deltas)}/{sum(abs(x)<=EPS for x in deltas)}/{sum(x>EPS for x in deltas)}.",
        "",
        f"Material priority interventions >0.1% absolute actual Makespan change: **{len(relevant)} of 16** non-FIFO paired cases."]
    for x in sorted(relevant,key=lambda q:-abs(float(q["actual_effect_pct"]))):
        report.append(f"- {x['workflow']} {x['vm_profile']} {x['placement']} {x['priority']}: "
         f"actual={float(x['actual_effect_pct']):+.6f}%, forecast={float(x['predicted_effect_pct']):+.6f}%, "
         f"prediction minus truth={float(x['effect_error_pp']):+.6f} pp.")
    if relevant:
        correct=sum((float(x["actual_effect_pct"])>0)==(float(x["predicted_effect_pct"])>0) for x in relevant)
        report.append(f"Of {len(relevant)} material effects, priority-aware model predicted correct direction in {correct}.")
    else:
        report.append("No material effects here: the new instances cannot validate prediction of large priority-sensitive changes.")
    report+=["",
      "## Decision boundaries",
      "Predictive fidelity on a new instance is not superiority of a FLA search algorithm; a priority-aware decoder used by both FLA and NSGA-II is a shared scheduling model.",
      "All observations within two DAG instances, and repeated speed/mapping cases, are highly dependent. No formal significance, independent new-family generalization or Q1 publication readiness is established.",
      "No tuning of weights or priorities is permitted on these cases before a new separately registered holdout.",
      "If priority sensitivity is inconsistent or new errors arise, do not blindly add a priority gene to FLA."
    ]
    (out/"new_instance_priority_aggregate_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: script.py ORIGINAL_ARTIFACTS REPORT_DIR")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
