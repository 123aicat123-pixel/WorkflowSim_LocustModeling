#!/usr/bin/env python3
"""Read every independently simulated visited assignment, quantify planner/simulator rank changes.

Inputs must be eight original zipped (or extracted) cases from the fixed
historical GitHub Actions run 41582476054. No simulation labels train or alter
any screening policy. This is a non-predictive post-hoc diagnosis.
"""
import csv
import pathlib
import statistics
import math
import sys

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def tau_b(planned,simulated):
    pos=neg=ties_x=ties_y=0
    for i in range(len(planned)):
        for j in range(i+1,len(planned)):
            a=(planned[i]>planned[j])-(planned[i]<planned[j])
            b=(simulated[i]>simulated[j])-(simulated[i]<simulated[j])
            if a==0 and b==0:continue
            if a==0:ties_x+=1
            elif b==0:ties_y+=1
            elif a==b:pos+=1
            else:neg+=1
    den=math.sqrt((pos+neg+ties_x)*(pos+neg+ties_y))
    return (pos-neg)/den if den else float("nan"),neg

def diagnose(root,out):
    paths=list(root.rglob("budget_*_screening_summary.csv"))
    assert len(paths)==8,("Need all eight oracle cases",len(paths))
    records=[]
    for audit_path in sorted(paths):
        prefix=str(audit_path)[:-len("_screening_summary.csv")]
        original=read(pathlib.Path(prefix+"_replays.csv"))
        extra=read(pathlib.Path(prefix+"_screening_samples.csv"))
        audits=read(audit_path)
        assert len(audits)==3
        for entry in audits:
            alg=entry["algorithm"]
            rows=[x for x in original+extra if x["algorithm"]==alg]
            assert len(rows)==int(entry["unique_visited"])
            assert len(rows)==len({x["mapping"] for x in rows}) and 16<=len(rows)<=80
            for obj in ("makespan","cost"):
                a="planned_"+obj;b="sim_"+obj
                xp=[float(x[a]) for x in rows]
                ys=[float(x[b]) for x in rows]
                assert all(math.isfinite(v) and v>0 for v in xp+ys)
                tau,inverted=tau_b(xp,ys)
                predicted=sorted(rows,key=lambda x:(float(x[a]),x["mapping"]))[:16]
                true=sorted(rows,key=lambda x:(float(x[b]),x["mapping"]))[:16]
                overlap=len({x["mapping"] for x in predicted}&{x["mapping"] for x in true})/16
                regret=100*(min(float(x[b]) for x in predicted)/min(ys)-1)
                mae=statistics.mean(100*abs(x/y-1) for x,y in zip(xp,ys))
                records.append(dict(workflow=rows[0]["workflow"],seed=int(rows[0]["seed"]),
                   algorithm=alg,objective=obj,distinct_visited=len(rows),
                   kendall_tau_b=tau,discordant_pairs=inverted,top16_overlap=overlap,
                   planned_top16_extreme_regret_pct=regret,mean_absolute_relative_error_pct=mae))
    assert len(records)==48,len(records)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"rank_fidelity_cases.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]))
        writer.writeheader();writer.writerows(records)
    report=["# Independent full-history planned versus simulator rank fidelity",
      "",
      "Fixed prior source: GitHub Actions run 41582476054, four 100-task DAG families, two seeds 46/47, three solver arms, complete independently simulated 80-search-budget visited histories.",
      "Each real visited genotype is counted exactly once. This is a diagnostic oracle, NOT a policy that reads simulator labels at selection time.",
      "",
      "| Objective | Mean Kendall tau-b | Mean pair inversions per solver case | Mean top16 overlap | Mean absolute relative prediction error | Missed true extreme among planned top16 |",
      "|---|---:|---:|---:|---:|---:|"]
    for obj in ("makespan","cost"):
        x=[z for z in records if z["objective"]==obj]
        report.append(f"| {obj} | {statistics.mean(z['kendall_tau_b'] for z in x):.5f} | "+
                      f"{statistics.mean(z['discordant_pairs'] for z in x):.1f} | "+
                      f"{100*statistics.mean(z['top16_overlap'] for z in x):.2f}% | "+
                      f"{statistics.mean(z['mean_absolute_relative_error_pct'] for z in x):.4f}% | "+
                      f"{sum(z['planned_top16_extreme_regret_pct']>1e-10 for z in x)}/{len(x)} |")
    report+=["","## Per-family makespan ranking",
        "",
        "| Workflow | Mean makespan tau-b | Mean makespan top16 overlap |",
        "|---|---:|---:|"]
    for wf in sorted({x["workflow"] for x in records}):
        xs=[x for x in records if x["workflow"]==wf and x["objective"]=="makespan"]
        report.append(f"| {wf} | {statistics.mean(x['kendall_tau_b'] for x in xs):.5f} | "+
                      f"{100*statistics.mean(x['top16_overlap'] for x in xs):.2f}% |")
    report+=["","## Limits",
       "This compares single-objective top-16 planned versus true simulator objectives; it is NOT the Pareto-cover K16 selection and does not directly predict Pareto HV.",
       "A perfect true-extreme retention in this 80-evaluation audit must not be extrapolated to the 3030-evaluation prospective experiments.",
       "Kendall tau-b handles objective ties; near-perfect cost order does not rule out nonzero absolute cost errors.",
       "24 solver/seed histories are correlated within four workflow families and should not be treated as 24 independent DAGs.",
       "The findings disfavor blind extreme-point quota tuning; a rank-robust screening hypothesis still requires independent, prospective validation."]
    (out/"rank_fidelity_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_rank_fidelity_diagnostic.py INPUT_ARTIFACT_ROOT OUTPUT")
    diagnose(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
