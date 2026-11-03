#!/usr/bin/env python3
"""Rank fidelity and objective prediction error in actual K16 selected replay sets.

Reads pinned original 20 real WorkflowSim cross-VM files. Fitted models: NONE.
Selected candidate pools may differ between speed regimes; this is diagnostic,
not an identified causal estimate of VM speed on prediction error.
"""
import collections
import csv
import math
import pathlib
import statistics
import sys

WF=("CyberShake_50","Epigenomics_46","Inspiral_30","Montage_50","Sipht_60")
SEEDS=(113,114)
SPEEDS=("default","staggered")
POLICIES=("pareto-cover","online-observed-hv")
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def tau(a,b):
    pos=neg=tx=ty=0
    for i in range(len(a)):
        for j in range(i+1,len(a)):
            x=(a[i]>a[j])-(a[i]<a[j])
            y=(b[i]>b[j])-(b[i]<b[j])
            if not x and not y:continue
            if not x:tx+=1
            elif not y:ty+=1
            elif x==y:pos+=1
            else:neg+=1
    d=math.sqrt((pos+neg+tx)*(pos+neg+ty))
    return ((pos-neg)/d if d else float("nan")),neg

def run(root,out):
    rows=[]
    for wf in WF:
        for seed in SEEDS:
            for speed in SPEEDS:
                for policy in POLICIES:
                    pathlist=list(root.rglob(f"{policy}-{speed}-{wf}-s{seed}_replays.csv"))
                    assert len(pathlist)==1,pathlist
                    data=read(pathlist[0])
                    assert len(data)==48
                    for alg in ALGS:
                        rr=[r for r in data if r["algorithm"]==alg]
                        assert len(rr)==16
                        for obj in ("makespan","cost"):
                            planned=[float(r["planned_"+obj]) for r in rr]
                            sim=[float(r["sim_"+obj]) for r in rr]
                            assert all(math.isfinite(x) and x>0 for x in planned+sim)
                            rank,discordant=tau(planned,sim)
                            mae=statistics.mean(100*abs(x/y-1) for x,y in zip(planned,sim))
                            # All sampled actual labels known AFTER selection; never use them prospectively.
                            rows.append(dict(workflow=wf,seed=seed,speed=speed,policy=policy,
                                algorithm=alg,objective=obj,simulated_schedules=len(rr),
                                mean_absolute_pct_error=mae,kendall_tau_b=rank,
                                discordant_pairs=discordant))
    assert len(rows)==5*2*2*2*3*2==240
    out.mkdir(parents=True,exist_ok=True)
    with (out/"speed_rank_fidelity_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    report=["# K16 selected-schedule planner versus actual simulator fidelity in alternative VM speed configurations",
        "",
        "Real simulator evidence from Actions 41603751878, 5 different DAX instance sizes from old families × 2 seeds × 2 VM speed profiles × 2 replay policies × 3 algorithms.",
        "The 16 schedules per algorithm/policy are different selected sets; do not compare their ranking values as if they were identical input populations. This diagnostic is AFTER replay, with no trained predictor and no new simulator calls.",
        "Kendall tau-b handles ties; deviations from perfect agreement reflect planner/simulator rank inversion among the SELECTED K16 candidates, not exhaustive optimizer visitation.",
        "",
        "| VM speed | Policy | Objective | Mean absolute relative prediction error | Mean Kendall tau-b (finite cases) | Mean discordant pairs |",
        "|---|---|---|---:|---:|---:|"]
    for speed in SPEEDS:
        for policy in POLICIES:
            for obj in ("makespan","cost"):
                a=[r for r in rows if r["speed"]==speed and r["policy"]==policy and r["objective"]==obj]
                valid=[r["kendall_tau_b"] for r in a if math.isfinite(r["kendall_tau_b"])]
                assert a
                report.append(f"| {speed} | {policy} | {obj} | "+
                    f"{statistics.mean(r['mean_absolute_pct_error'] for r in a):.4f}% | "+
                    f"{statistics.mean(valid):.4f} ({len(valid)}/{len(a)}) | "+
                    f"{statistics.mean(r['discordant_pairs'] for r in a):.2f} |")
    report+=["","## FLA v12 makespan ranking by workflow, speed (Pareto-cover only)","",
        "| DAX | Speed | Mean makespan Kendall tau-b | Mean relative makespan error |",
        "|---|---|---:|---:|"]
    for wf in WF:
        for speed in SPEEDS:
            a=[r for r in rows if r["workflow"]==wf and r["speed"]==speed and
                 r["policy"]=="pareto-cover" and r["objective"]=="makespan" and
                 r["algorithm"]=="DAG-Pareto-FLA[v12-hvbandit]"]
            assert len(a)==2
            report.append(f"| {wf} | {speed} | "+
                f"{statistics.mean(r['kendall_tau_b'] for r in a):.4f} | "+
                f"{statistics.mean(r['mean_absolute_pct_error'] for r in a):.4f}% |")
    report+=["","## Research limits",
        "Only the 16 actually simulated schedules per arm are available. This is not a full-visited solution rank diagnostic. Distortion among unselected candidates is unknown.",
        "The model is unchanged; speed profiles also change solver search trajectories, selected genotypes and objective ranges. Differences in error metrics cannot be attributed causally to speed alone.",
        "The 240 objective rows are correlated within five DAX families and do not represent independent workflow samples.",
        "No claim of FLA v12 optimizer superiority can be derived from prediction-rank correlations."]
    (out/"speed_rank_fidelity_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_cross_vm_rank_fidelity.py ORIGINAL ROOT_OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
