#!/usr/bin/env python3
"""Pinned cross-cohort synthesis of causal online-observed K16 WorkflowSim results.

Both source cohorts already underwent independently successful real Java
WorkflowSim runs and share historical frozen per-DAG-family HV reference,
but were executed from different Java source commits. This is an exploratory
synthesis and NOT a preregistered inferential meta-analysis.
"""
import csv
import pathlib
import statistics
import collections
import sys

FAMILIES=("CyberShake_100","Epigenomics_100","Inspiral_100","Montage_100","Sipht_100")
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
SEEDS=(95,96,101,102)

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def run(root,out):
    old=list(root.rglob("online_factorial_paired.csv"))
    new=list(root.rglob("online_runtime_paired.csv"))
    assert len(old)==len(new)==1,(old,new)
    data=[]
    for row in read(old[0]):
        if row["policy"]!="online-observed-hv":continue
        data.append(dict(workflow=row["workflow"],seed=int(row["seed"]),
            algorithm=row["algorithm"],cohort="95-96",
            observed_minus_cover_hv_pct=float(row["gain_vs_cover_pct"])))
    for row in read(new[0]):
        data.append(dict(workflow=row["workflow"],seed=int(row["seed"]),
            algorithm=row["algorithm"],cohort="101-102",
            observed_minus_cover_hv_pct=float(row["observed_vs_cover_hv_pct"])))
    expected={(wf,seed,alg) for wf in FAMILIES for seed in SEEDS for alg in ALGS}
    assert len(data)==60 and {(r["workflow"],r["seed"],r["algorithm"]) for r in data}==expected
    family=[]
    lofo=[]
    summary=[]
    for alg in ALGS:
        a=[r for r in data if r["algorithm"]==alg]
        values=[r["observed_minus_cover_hv_pct"] for r in a]
        summary.append(dict(algorithm=alg,cases=len(a),mean_gain_pct=statistics.mean(values),
            median_gain_pct=statistics.median(values),positive=sum(v>0 for v in values),
            negative=sum(v<0 for v in values),minimum_gain_pct=min(values),maximum_gain_pct=max(values)))
        for wf in FAMILIES:
            group=[r["observed_minus_cover_hv_pct"] for r in a if r["workflow"]==wf]
            assert len(group)==4
            family.append(dict(algorithm=alg,workflow=wf,mean_gain_pct=statistics.mean(group),
                wins=sum(v>0 for v in group),cases=4))
            remain=[r["observed_minus_cover_hv_pct"] for r in a if r["workflow"]!=wf]
            lofo.append(dict(algorithm=alg,excluded_workflow=wf,
                mean_gain_remaining_pct=statistics.mean(remain),cases_remaining=len(remain)))
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("online_two_cohorts_cases.csv",data),
                      ("online_two_cohorts_solvers.csv",summary),
                      ("online_two_cohorts_families.csv",family),
                      ("online_two_cohorts_leave_one_family_out.csv",lofo)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=["# Real WorkflowSim online-observed-front selector: two DAG100 seed cohorts",
        "",
        "Original independently simulated cohort 95/96: GitHub Actions 41597521884, four policies but only online-observed-hv versus pareto-cover included.",
        "Original independently simulated cohort 101/102: GitHub Actions 41600766954, two policies, same K16 budget, frozen evaluation references and timing instrumentation.",
        "Five 100-task DAG families x four optimizer seeds x three correlated solver arms = 60 ALGORITHM-case comparisons, but only 20 DAG/seed blocks and five distinct families.",
        "Both cohorts enforce 3030 planner objective calls and exactly 16 true independent WorkflowSim replay calls per arm, with identical search histories per policy. Both use prior fixed references from Actions 41572425682.",
        "Both source commits and exact archives are preserved. This synthesis was computed after seeing results; not a preregistered final publication holdout.",
        "",
        "| Solver | Mean online HV gain over original cover | Median gain | Positive / 20 | Minimum |",
        "|---|---:|---:|---:|---:|"]
    for x in summary:
        lines.append(f"| {x['algorithm']} | {x['mean_gain_pct']:+.4f}% | "+
            f"{x['median_gain_pct']:+.4f}% | {x['positive']}/{x['cases']} | "+
            f"{x['minimum_gain_pct']:+.4f}% |")
    lines+=["","## By DAG family; negative cases remain","",
        "| Workflow | v7 mean (wins/4) | v12 mean (wins/4) | NSGA-II mean (wins/4) |",
        "|---|---:|---:|---:|"]
    for wf in FAMILIES:
        row=[next(x for x in family if x["algorithm"]==alg and x["workflow"]==wf) for alg in ALGS]
        lines.append("| "+wf+" | "+" | ".join(
            f"{r['mean_gain_pct']:+.4f}% ({r['wins']}/4)" for r in row)+" |")
    lines+=["","## Leave one entire DAG family out",
        "If a positive overall mean vanishes after excluding one family, the apparent method benefit is family-sensitive. This is a diagnostic, not a confidence interval.","",
        "| Excluded family | v7 remaining mean | v12 remaining mean | NSGA-II remaining mean |",
        "|---|---:|---:|---:|"]
    for wf in FAMILIES:
        r=[next(x for x in lofo if x["algorithm"]==alg and x["excluded_workflow"]==wf) for alg in ALGS]
        lines.append("| "+wf+" | "+" | ".join(f"{x['mean_gain_remaining_pct']:+.4f}%" for x in r)+" |")
    lines+=["","## Boundaries",
        "The online-observed-front method does not modify the search algorithm. Its policy-level benefit also applies to NSGA-II, so it is NOT a unique FLA improvement.",
        "Only five distinct families are present and they have appeared in algorithm development. Conditional random optimizer seeds are not new unseen workflow structures.",
        "The 95/96 study and 101/102 study use different source commits; although the same policy names and scoring references were used, this synthesis cannot prove byte-for-byte identical code or external transferability.",
        "Runtime was measured only in the 101/102 cohort; there is no legitimate pooled 20-case runtime speedup claim.",
        "No p-values are calculated by treating 60 algorithm arms as independent workflow draws."]
    (out/"online_two_cohorts_report.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_online_cohort_synthesis.py ORIGINAL_ARTIFACTS OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
