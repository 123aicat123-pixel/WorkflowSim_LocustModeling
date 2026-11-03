#!/usr/bin/env python3
"""Epsilon Pareto robustness of already-simulated K16+K12 genotypes. NO SIMULATOR."""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("Montage_100","CyberShake_50")
SEEDS=(951,952)
ALGS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
EPS=(0.0,0.0001,0.001,0.01)
TOL=1e-12

def load(path):
    with path.open(newline="",encoding="utf-8") as f:
        data=list(csv.DictReader(f))
    if len(data)!=224:
        raise AssertionError(("Expected all 224 original source simulator points",len(data)))
    grouped={}
    for r in data:
        wf=r["workflow"];seed=int(r["seed"]);alg=r["solver"]
        group=(wf,seed,alg)
        if group not in set(itertools.product(DAGS,SEEDS,ALGS)):
            raise AssertionError(("Unregistered original source group",group))
        if any(not math.isfinite(float(r[x])) or float(r[x])<=0
               for x in ("planned_makespan","planned_cost","actual_makespan","actual_cost")):
            raise AssertionError(("Invalid actual simulator objective",group))
        grouped.setdefault(group,[]).append(r)
    if set(grouped)!=set(itertools.product(DAGS,SEEDS,ALGS)):
        raise AssertionError(("Missing actual source groups",set(grouped)))
    for key,cases in grouped.items():
        if len(cases)!=28:
            raise AssertionError(("Wrong candidate total",key,len(cases)))
        ids=[int(x["candidate_index"]) for x in cases]
        if sorted(ids)!=list(range(1,29)):
            raise AssertionError(("Wrong original source K IDs",key,ids))
        if len({x["task_vm_mapping"] for x in cases})!=28:
            raise AssertionError(("Repeated original task-VM mapping",key))
        for r in cases:
            i=int(r["candidate_index"])
            expect="primary-k16" if i<=16 else "secondary-k12"
            if r["selection"]!=expect:raise AssertionError(("Bad original K partition",key,i,r["selection"]))
    return grouped

def critical_epsilon(target,primary):
    m=float(target["actual_makespan"])
    c=float(target["actual_cost"])
    distances=[max(0.0,float(p["actual_makespan"])/m-1.0,
                   float(p["actual_cost"])/c-1.0)
               for p in primary]
    result=min(distances)
    if not math.isfinite(result) or result<0:raise AssertionError(("Invalid eps threshold",result))
    return result

def write(path,rows):
    if not rows:raise AssertionError("Missing rows to save")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def run(input_path,out):
    grouped=load(input_path)
    out.mkdir(parents=True,exist_ok=True)
    detail=[]
    summary=[]
    uncovered_values=[]
    for (dag,seed,alg),raw in sorted(grouped.items()):
        byid={int(r["candidate_index"]):r for r in raw}
        primary=[byid[i] for i in range(1,17)]
        extras=[byid[i] for i in range(17,29)]
        values=[]
        for extra in extras:
            threshold=critical_epsilon(extra,primary)
            values.append(threshold)
            status=[int(threshold>e+TOL) for e in EPS]
            detail.append(dict(workflow=dag,seed=seed,solver=alg,
                source_extra_id=int(extra["candidate_index"]),
                sampling_stratum=extra["stratum"],
                original_makespan=float(extra["actual_makespan"]),
                original_cost=float(extra["actual_cost"]),
                minimum_epsilon_cover_pct=100*threshold,
                uncovered_exact=status[0],
                uncovered_at_0_01_percent=status[1],
                uncovered_at_0_1_percent=status[2],
                uncovered_at_1_percent=status[3],
                task_vm_mapping=extra["task_vm_mapping"]))
        if len(values)!=12:raise AssertionError("12 extra sources required")
        uncovered_values.extend(v for v in values if v>TOL)
        summary.append(dict(workflow=dag,seed=seed,solver=alg,
            extra_candidates=12,
            exact_nondominated=sum(v>0+TOL for v in values),
            nondominated_0_01_pct=sum(v>0.0001+TOL for v in values),
            nondominated_0_1_pct=sum(v>0.001+TOL for v in values),
            nondominated_1_pct=sum(v>0.01+TOL for v in values),
            maximum_margin_pct=max(values)*100,
            mean_margin_pct=statistics.mean(values)*100))
    if len(detail)!=96 or len(summary)!=8:
        raise AssertionError(("Missing original extra observations",len(detail),len(summary)))
    write(out/"all_96_extra_candidate_epsilon_cover_thresholds.csv",detail)
    write(out/"all_8_solver_epsilon_robustness.csv",summary)
    report=[
      "# Relative epsilon-Pareto sensitivity of 96 extra planned-dominated WorkflowSim schedules",
      "",
      "READ-ONLY: original actual Java simulation/source GitHub Actions 41693332570 (postvalidation script typo but all actual CSV saved), independent complete K16+K12 source verification 41693970902; exactly 224 real points. No additional simulator or optimizer calls.",
      "Comparison: each K12 extra candidate versus its same-solver, same-DAX, same-seed ORIGINAL K16 actual WorkflowSim plans. Original DAG task-VM maps fixed. An extra is 'robustly uncovered' at epsilon if NO original K16 plan has both Makespan and Cost ≤ (1+epsilon)× the extra candidate's actual objective values.",
      "",
      "| DAG | Seed | Solver | New true ND exactly | Remain uncovered at 0.01% | at 0.1% | at 1% | Largest relative cover margin |",
      "|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in summary:
        report.append(f"| {r['workflow']} | {r['seed']} | "
          f"{'FLA-v12' if r['solver']==ALGS[0] else 'NSGA-II'} | "
          f"{r['exact_nondominated']}/12 | {r['nondominated_0_01_pct']}/12 | "
          f"{r['nondominated_0_1_pct']}/12 | {r['nondominated_1_pct']}/12 | "
          f"{r['maximum_margin_pct']:.7f}% |")
    report+=["",
      "## All 96 observations",
      f"- Raw uncovered at epsilon=0: **{sum(r['exact_nondominated'] for r in summary)}/96**.",
      f"- Robust uncovered at 0.01% relative tolerance: **{sum(r['nondominated_0_01_pct'] for r in summary)}/96**.",
      f"- Robust uncovered at 0.1% relative tolerance: **{sum(r['nondominated_0_1_pct'] for r in summary)}/96**.",
      f"- Robust uncovered at 1% relative tolerance: **{sum(r['nondominated_1_pct'] for r in summary)}/96**.",
      f"- Largest additional-solution relative cover threshold = {max(r['maximum_margin_pct'] for r in summary):.8f}%.",
      "",
      "## Scientific cautions",
      "The thresholds are computed against each source's ORIGINAL K16 actual outcomes, not every feasible or population-visited candidate. Allowing weak epsilon dominance naturally suppresses small numeric Pareto differences; this is NOT confidence interval inference.",
      "The source workflows are historically studied, only two optimizer seeds per two DAGs, 96 highly correlated secondary samples. Very small real HV gains in the preceding audit remain the actual area-effect result.",
      "This audit cannot show which policy a future scheduler should choose without looking at actual simulator labels, and does not demonstrate FLA algorithm advantage.",
      "Every opt-in source variant remains on fla-baseline and master/default FIFO remains unchanged."
    ]
    (out/"epsilon_pareto_sensitivity_conclusions.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py IMMUTABLE_224_REPLAY_CSV OUTPUT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
