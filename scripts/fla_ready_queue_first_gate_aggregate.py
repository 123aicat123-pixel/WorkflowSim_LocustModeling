#!/usr/bin/env python3
"""Aggregate fixed-genotype ready-queue pilot, deduplicating repeated physical mappings.

Original real replay artifacts from GitHub Actions 41668888545. Read-only; no
new optimizer or simulator calls. All negative or unchanged cases preserved.
"""
import csv
import math
import pathlib
import statistics
import sys
from collections import defaultdict

FAMILIES=("Epigenomics_46","CyberShake_100")
ALGS={"DAG-Pareto-FLA[v12-hvbandit]":"v12","NSGA-II[costseed]":"nsga"}
PROFILES=("default","staggered")
METRICS=(("makespan_abs_pct","insertion_makespan_abs_pct","ready_makespan_abs_pct"),
         ("cost_abs_pct","insertion_cost_abs_pct","ready_cost_abs_pct"),
         ("task_mae_start","insertion_task_mae_start","ready_task_mae_start"),
         ("task_mae_finish","insertion_task_mae_finish","ready_task_mae_finish"))

def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def run(root,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for family in FAMILIES:
        dirs=[p for p in root.iterdir() if p.is_dir() and family in p.name]
        if len(dirs)!=1:raise AssertionError(("single artifact per family",family,dirs))
        folder=dirs[0]
        for name,tag in ALGS.items():
            for speed in PROFILES:
                raw=read(folder/f"{tag}_{speed}_ready.csv")
                if len(raw)!=2:raise AssertionError(("expected two frozen candidates",family,tag,speed))
                for r in raw:
                    if r["workflow"]!=family or r["algorithm"]!=name or r["speed"]!=speed or r["seed"]!="211":
                        raise AssertionError("scenario not frozen")
                    if int(r["candidate_index"]) not in (1,2):
                        raise AssertionError("unregistered candidate")
                    numbers=dict(
                        (k,float(v)) for k,v in r.items() if k in
                        {x for _,a,b in METRICS for x in (a,b)}
                        |{"insertion_makespan","ready_queue_makespan","actual_makespan",
                          "insertion_cost","ready_queue_cost","actual_cost"})
                    if not all(math.isfinite(x) and x>=0 for x in numbers.values()):
                        raise AssertionError("invalid source prediction")
                    for _,old,new in METRICS:
                        if old not in numbers or new not in numbers:
                            raise AssertionError("missing metric")
                    row=dict(
                        workflow=family,seed=211,algorithm=name,
                        speed=speed,candidate_index=int(r["candidate_index"]),
                        mapping=r["mapping"],**numbers)
                    for label,old,new in METRICS:
                        row["delta_"+label]=numbers[new]-numbers[old]
                    rows.append(row)
    if len(rows)!=16:raise AssertionError("missing case")
    physical=defaultdict(list)
    for r in rows:
        physical[(r["workflow"],r["seed"],r["speed"],r["mapping"])].append(r)
    conflicts=[]
    unique=[]
    for key,items in sorted(physical.items()):
        a=items[0]
        for b in items[1:]:
            for metric in (x for _,old,new in METRICS for x in (old,new)):
                if not math.isclose(a[metric],b[metric],rel_tol=1e-10,abs_tol=1e-6):
                    conflicts.append((key,metric,a[metric],b[metric]))
            for metric in ("insertion_makespan","ready_queue_makespan","actual_makespan",
                           "insertion_cost","ready_queue_cost","actual_cost"):
                if not math.isclose(a[metric],b[metric],rel_tol=1e-10,abs_tol=1e-6):
                    conflicts.append((key,metric,a[metric],b[metric]))
        unique.append(dict(a,repeated_source_arms=len(items)))
    if conflicts:raise AssertionError(("same physical assignment has inconsistent objectives",conflicts[:6]))
    with (out/"full_source_arm_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (out/"unique_physical_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(unique[0]));w.writeheader();w.writerows(unique)
    positive=sum(x["delta_makespan_abs_pct"]< -1e-8 for x in unique)
    zero=sum(abs(x["delta_makespan_abs_pct"])<=1e-8 for x in unique)
    worse=sum(x["delta_makespan_abs_pct"]>1e-8 for x in unique)
    report=["# Ready-queue vs historical stage-in insertion: frozen development pilot",
        "", "Immutable real WorkflowSim original: [Actions 41668888545](https://github.com/123aicat123-pixel/WorkflowSim_LocustModeling/actions/runs/41668888545).",
        f"**{len(rows)}** source-arm/profile cases, **{len(unique)}** unique exact physical mapping/profile cases, "
        f"**{len(rows)-len(unique)}** duplicate source-arm cases; 0 consistency conflicts.",
        "No new simulator, search, model tuning, or post-hoc case selection in this audit.",
        "", "## Deduplicated physical genotype statistics",
        "| Metric (old insertion vs alternative) | Old mean | New mean | New minus old | Improved / Tied / Worse |",
        "|---|---:|---:|---:|---:|"]
    for label,old,new in METRICS:
        a=statistics.mean(x[old] for x in unique)
        b=statistics.mean(x[new] for x in unique)
        wins=sum(x[new]<x[old]-1e-8 for x in unique)
        ties=sum(abs(x[new]-x[old])<=1e-8 for x in unique)
        losses=len(unique)-wins-ties
        units="%" if label.endswith("pct") else "s"
        report.append(f"| {label} ({units}) | {a:.6f} | {b:.6f} | {b-a:+.6f} | {wins}/{ties}/{losses} |")
    report+=["",f"**Makespan error unique-case wins/ties/losses:** {positive}/{zero}/{worse}.",
        "Development examples only; the 14 physical cases are NOT 14 independent workflow families.",
        "", "## Every unique case: makespan error differences (new − old, percentage points)"]
    for row in unique:
        report.append(f"- {row['workflow']} {row['speed']} source {ALGS[row['algorithm']]} "
            f"candidate {row['candidate_index']}, repeated-arm count {row['repeated_source_arms']}: "
            f"old={row['insertion_makespan_abs_pct']:.5f}%, "
            f"new={row['ready_makespan_abs_pct']:.5f}%, "
            f"delta={row['delta_makespan_abs_pct']:+.5f} pp; "
            f"cost delta={row['delta_cost_abs_pct']:+.5f} pp.")
    report+=["","## Boundaries",
       "Both methods are forecasts for the SAME immutable mappings, NOT two independently optimized algorithms.",
       "Solver-source labels only explain where assignments were obtained; they do NOT establish causal FLA-versus-NSGA-II effects.",
       "A decrease in forecast error is necessary but not sufficient for Pareto HV improvement.",
       "No claims of unseen-family generalization, statistical significance, or Q1 readiness follow.",
       "The ready-queue method is an opt-in read-only diagnostic; the default optimizer/decoder is untouched."]
    (out/"ready_queue_first_gate_aggregate.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: aggregate.py ORIGINAL_ARTIFACT_ROOT OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
