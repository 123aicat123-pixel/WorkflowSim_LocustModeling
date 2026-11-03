#!/usr/bin/env python3
"""Fixed earlier-study DAG100 HV reference robustness after real K16 comparisons.

No new replay or optimizer evaluations. Reference sensitivity multipliers
1.0,1.1,1.25 are declared before these final Sipht cases are aggregated.
"""
import csv
import pathlib
import statistics
import math
import sys

REFS={
 "CyberShake_100":(6806.24215,3280.0303),
 "Epigenomics_100":(211858.3560250001,217310.76064),
 "Inspiral_100":(11044.129825,11209.86290125),
 "Montage_100":(568.6573,570.969505),
 "Sipht_100":(9127.960675000002,8822.13817375)
}
SEEDS=(95,96)
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
POLICIES=("pareto-cover","online-planned-hv","online-observed-hv","online-nearest-hv")
MULTIPLIERS=(1.0,1.1,1.25)

def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    last=ref[1];total=0.
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def main(root,out):
    points={}
    for wf in REFS:
        for seed in SEEDS:
            for policy in POLICIES:
                prefix=policy+"-"+wf+"-s"+str(seed)
                candidates=list(root.rglob(prefix+"_replays.csv"))
                assert len(candidates)==1,(prefix,candidates)
                rows=read(candidates[0])
                assert len(rows)==48
                for alg in ALGS:
                    rr=[x for x in rows if x["algorithm"]==alg]
                    assert len(rr)==16 and len({x["mapping"] for x in rr})==16
                    val=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
                    assert all(math.isfinite(q) and q>0 for row in val for q in row)
                    points[wf,seed,alg,policy]=val
    assert len(points)==len(REFS)*len(SEEDS)*len(ALGS)*len(POLICIES)
    comparisons=[]
    for wf in REFS:
        for seed in SEEDS:
            for alg in ALGS:
                for factor in MULTIPLIERS:
                    reference=tuple(q*factor for q in REFS[wf])
                    scores={p:hv(points[wf,seed,alg,p],reference) for p in POLICIES}
                    assert all(v>0 for v in scores.values()),(wf,seed,alg,factor,scores)
                    for policy in POLICIES[1:]:
                        comparisons.append(dict(workflow=wf,seed=seed,algorithm=alg,
                            reference_multiplier=factor,policy=policy,
                            improvement_vs_cover_pct=100*(scores[policy]/scores["pareto-cover"]-1),
                            change_vs_observed_pct=100*(scores[policy]/scores["online-observed-hv"]-1),
                            sim_hv=scores[policy],ref_m=reference[0],ref_c=reference[1]))
    out.mkdir(parents=True,exist_ok=True)
    with (out/"online_ref_robustness_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(comparisons[0]))
        w.writeheader();w.writerows(comparisons)
    report=["# Fixed-reference sensitivity of true K16 online feedback mechanism ablation",
        "",
        "Original real WorkflowSim source: five-family four-policy Actions run 41597521884; two new optimizer seeds 95/96, three correlated solver arms, each with 3030 planned evaluations and exactly K16 simulator replays.",
        "No simulator labels guide the reference choices: the base vector per DAG was frozen by PREVIOUS Actions 41572425682. Sensitivity factors 1.00, 1.10, 1.25 scale BOTH makespan and cost reference components and are specified in this independent script.",
        "These are post-hoc score recalculations from the ORIGINAL recorded independent WorkflowSim replays, not new simulator runs.",
        "",
        "| Optimizer | Policy | Ref multiplier | Mean relative HV vs cover | Wins out of 10 |",
        "|---|---|---:|---:|---:|"]
    for alg in ALGS:
        for policy in POLICIES[1:]:
            for factor in MULTIPLIERS:
                rows=[x for x in comparisons if x["algorithm"]==alg and x["policy"]==policy and x["reference_multiplier"]==factor]
                report.append(f"| {alg} | {policy} | {factor:.2f} | "+
                    f"{statistics.mean(x['improvement_vs_cover_pct'] for x in rows):+.4f}% | "+
                    f"{sum(x['improvement_vs_cover_pct']>0 for x in rows)}/{len(rows)} |")
    report+=["","## Interpretation and limits",
        "Both reference components are scaled to avoid invalid external truncation assumptions, but this does not constitute proof of reference-independent conclusions.",
        "A sign reversal when reference changes is a real indicator of HV sensitivity; retain negative observations and do not tune the reference to favor a method.",
        "The same 10 DAG/optimizer-seed cases and three correlated solver arms are reused at three references; do not count the scoring multipliers as new independent evidence.",
        "This only evaluates post-search K-limited simulator replay screening, not FLA optimizer search improvements."]
    (out/"online_ref_robustness_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_online_reference_robustness.py ARTIFACT_ROOT OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
