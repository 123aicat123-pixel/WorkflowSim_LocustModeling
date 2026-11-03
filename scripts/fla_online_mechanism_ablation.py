#!/usr/bin/env python3
"""Factorial causal K16 replay selection ablation: fixed planner history + real simulator calls."""
import csv, pathlib, collections, statistics, math, sys

POLICIES=("pareto-cover","online-planned-hv","online-observed-hv","online-nearest-hv")
FAMILIES=("Montage_25","CyberShake_30","Inspiral_50")
SEEDS=(93,94)
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    area,last=0.,ref[1]
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            area+=(ref[0]-m)*(last-c);last=c
    return area

def main(root,out):
    data={};rows=[]
    for wf in FAMILIES:
        for seed in SEEDS:
            for policy in POLICIES:
                prefix=policy+"-"+wf+"-s"+str(seed)
                matches=list(root.rglob(prefix+"_replays.csv"))
                assert len(matches)==1,(prefix,matches)
                raw=read(matches[0])
                assert len(raw)==48,(prefix,len(raw))
                for alg in ALGS:
                    rr=[x for x in raw if x["algorithm"]==alg]
                    assert len(rr)==16
                    pts=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
                    assert all(math.isfinite(v) and v>0 for p in pts for v in p)
                    data[wf,seed,alg,policy]=pts
    assert len(data)==len(FAMILIES)*len(SEEDS)*len(ALGS)*len(POLICIES)
    paired=[]
    for wf in FAMILIES:
        for seed in SEEDS:
            union=[p for alg in ALGS for policy in POLICIES for p in data[wf,seed,alg,policy]]
            ref=(1.05*max(p[0] for p in union)+1,1.05*max(p[1] for p in union)+1)
            for alg in ALGS:
                baseline=hv(data[wf,seed,alg,"pareto-cover"],ref)
                assert baseline>0
                for policy in POLICIES:
                    area=hv(data[wf,seed,alg,policy],ref)
                    rows.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        sim_hv=area,reference_m=ref[0],reference_c=ref[1]))
                    paired.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        gain_vs_cover_pct=100*(area/baseline-1)))
    out.mkdir(parents=True,exist_ok=True)
    for name,vals in (("online_factorial_hv.csv",rows),("online_factorial_paired.csv",paired)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(vals[0]))
            w.writeheader();w.writerows(vals)
    report=["# Causal K16: separate online greedy selection, observed-front feedback and local residual correction",
        "",
        "Fresh seeds 93/94 across three DAG families and three seeded solvers. Four policies per algorithm, exact 3030 optimizer calls + K=16 independent WorkflowSim calls. The CI gate verifies identical complete planner histories and equal first four selected genotypes.",
        "Policy definitions: cover = presimulation planned Pareto/max-min; online-planned-hv = iterative HV greedy over PLANNED outcomes only; online-observed-hv = greedy HV against earlier observed true simulator outcomes, but candidate predicted with uncorrected planned objectives; online-nearest-hv = adds 1NN residual shrink/clipping to observed-front variant.",
        "Evaluation HV reference is the per-DAG/seed POST-HOC union shared across four policies and three algorithms; it is not used inside any chooser and cannot be represented as preregistered.",
        "",
        "| Algorithm | Policy | Mean relative HV vs cover | Wins / 6 paired DAG seeds |",
        "|---|---|---:|---:|"]
    for alg in ALGS:
        for policy in POLICIES:
            vals=[r["gain_vs_cover_pct"] for r in paired if r["algorithm"]==alg and r["policy"]==policy]
            report.append(f"| {alg} | {policy} | {statistics.mean(vals):+.4f}% | {sum(x>0 for x in vals)}/6 |")
    report+=["","## Full comparison (all negative cases retained)","",
        "| Workflow | Seed | Solver | Planned-greedy vs cover | Observed-front vs cover | 1NN-residual vs cover |",
        "|---|---:|---|---:|---:|---:|"]
    for wf in FAMILIES:
        for seed in SEEDS:
            for alg in ALGS:
                vals={r["policy"]:r["gain_vs_cover_pct"] for r in paired
                      if r["workflow"]==wf and r["seed"]==seed and r["algorithm"]==alg}
                report.append(f"| {wf} | {seed} | {alg} | {vals['online-planned-hv']:+.4f}% | "+
                    f"{vals['online-observed-hv']:+.4f}% | {vals['online-nearest-hv']:+.4f}% |")
    report+=["","## Scientific limits",
        "Only 6 workflow-seed observations with three correlated algorithms, plus repeated policy comparisons; this is a development-stage mechanism ablation, not a full publication validation.",
        "The post-hoc HV reference is the union of this cohort's actual observed points, solely for evaluation. Test a frozen external reference separately.",
        "Any positive observed-front effect is not by itself proof that the 1NN residual correction adds value. Compare all four policies, not just the most successful.",
        "Actual simulator calls are counted, but CPU wall-clock and predictor overhead must also be measured.",
        "The experiment is post-search replay selection; no feedback is returned to the FLA generations and it cannot be described as an optimizer search improvement."]
    (out/"online_factorial_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_online_mechanism_ablation.py INPUT_ROOT OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
