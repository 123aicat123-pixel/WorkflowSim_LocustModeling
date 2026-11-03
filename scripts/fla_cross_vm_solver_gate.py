#!/usr/bin/env python3
"""Search-solver v12 FLA versus equal-costseed NSGA-II on matched K16 real replay.

Consumes only a PINNED earlier reference-sensitivity artifact from genuine
WorkflowSim run 41603751878. No training, new selection, or simulator calls.
"""
import csv
import collections
import pathlib
import statistics
import sys

ALGS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
SPEEDS=("default","staggered")
POLICIES=("cover_hv","online_hv")
SCALES=(1.10,1.25,1.50,2.00,3.00)
FAMILIES=("CyberShake_50","Epigenomics_46","Inspiral_30","Montage_50","Sipht_60")

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def run(root,out):
    files=list(root.rglob("reference_sensitivity.csv"))
    assert len(files)==1,files
    raw=read(files[0])
    data={}
    for r in raw:
        k=(r["workflow"],int(r["seed"]),r["speed"],float(r["scale"]),r["algorithm"])
        assert k not in data,k
        assert r["reference_valid"]=="True" and r["cover_hv"] and r["online_hv"],r
        data[k]=r
    expected={(wf,seed,speed,factor,alg) for wf in FAMILIES for seed in (113,114)
       for speed in SPEEDS for factor in SCALES
       for alg in ("DAG-Pareto-FLA[v7-costseed]",*ALGS)}
    assert set(data)==expected,(len(data),len(expected))
    cases=[]
    for wf in FAMILIES:
        for seed in (113,114):
            for speed in SPEEDS:
                for factor in SCALES:
                    a=data[wf,seed,speed,factor,ALGS[0]]
                    b=data[wf,seed,speed,factor,ALGS[1]]
                    for column in POLICIES:
                        a_hv,b_hv=float(a[column]),float(b[column])
                        assert a_hv>0 and b_hv>0
                        cases.append(dict(workflow=wf,seed=seed,vm_speed=speed,reference_factor=factor,
                            replay_policy=("pareto-cover" if column=="cover_hv" else "online-observed-hv"),
                            fla_v12_hv=a_hv,nsga_costseed_hv=b_hv,
                            fla_v12_vs_nsga_pct=100*(a_hv/b_hv-1),
                            fla_wins=int(a_hv>b_hv)))
    assert len(cases)==200
    out.mkdir(parents=True,exist_ok=True)
    with (out/"solver_vm_reference_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]))
        w.writeheader();w.writerows(cases)
    report=["# FLA v12 versus costseed NSGA-II: real K16 simulated search comparisons under within-tier heterogeneous VM speeds",
        "",
        "Old actual WorkflowSim evidence: 41603751878. Zero new simulator calls. The input is independently confirmed reference-sensitivity CSV 41604765542, generated solely from original real selected candidate points.",
        "Each underlying solver/policy run used exactly 3030 planning evaluations plus K16 independent real WorkflowSim simulator replays. Both solvers had identical first TWO deterministic cost-seeded candidate assignments.",
        "Five DAX instance sizes from previously used DAG families; seeds 113,114; VM speed default versus staggered; same VM prices. New VM configuration is synthetic, not a measured cloud provider.",
        "Within each workflow/speed, 1.10,1.25,1.50,2.00,3.00x planned-only baseline bounds were shared by policies/algorithms and all actual points lay inside all refs.",
        "Results below measure realized K16 selected simulator front, NOT full optimizer global Pareto front and NOT optimizer quality independent of the post-search replay policy.",
        "",
        "| VM speed | Replay policy | Reference factor | Mean paired FLA-v12 HV advantage versus NSGA-II | FLA wins / 10 |",
        "|---|---|---:|---:|---:|"]
    for speed in SPEEDS:
        for policy in ("pareto-cover","online-observed-hv"):
            for factor in SCALES:
                rr=[x for x in cases if x["vm_speed"]==speed and
                    x["replay_policy"]==policy and x["reference_factor"]==factor]
                assert len(rr)==10
                report.append(f"| {speed} | {policy} | {factor:.2f} | "+
                              f"{statistics.mean(x['fla_v12_vs_nsga_pct'] for x in rr):+.4f}% | "+
                              f"{sum(x['fla_wins'] for x in rr)}/10 |")
    report+=["","## Per DAG instance, standard 1.50x reference; preserve negatives","",
        "| VM speed | Replay policy | DAX instance | Mean FLA v12 vs NSGA-II relative HV (2 seeds) | FLA wins |",
        "|---|---|---|---:|---:|"]
    for speed in SPEEDS:
        for policy in ("pareto-cover","online-observed-hv"):
            for wf in FAMILIES:
                rr=[x for x in cases if x["vm_speed"]==speed and
                    x["replay_policy"]==policy and x["reference_factor"]==1.5 and x["workflow"]==wf]
                report.append(f"| {speed} | {policy} | {wf} | "+
                              f"{statistics.mean(x['fla_v12_vs_nsga_pct'] for x in rr):+.4f}% | "+
                              f"{sum(x['fla_wins'] for x in rr)}/2 |")
    report+=["","## Research limitations",
        "This cohort shows a negative *mean* for FLA v12 in staggered VM speed scenarios under all tested references and both replay policies, but some paired cases favor v12. Do not claim the optimizer is universally inferior.",
        "There are only five DAG families, two optimizer seeds per VM regime, and they have appeared in prior exploratory development. Multiple reference scales reuse the same observations and cannot increase statistical sample size.",
        "FLA v12 has undergone many exploratory variant choices. Equal objective-call budget and equal initial seeds do not erase all differences in algorithm design or guarantee equal CPU wall-clock.",
        "This comparison is on K16 simulator-selected subsets, not the complete 3030-visited simulator oracle. Its ranking may change with replay budget.",
        "Until an independently heldout, preregistered solver-search improvement is verified, do not claim the new online screening feedback is an innovation within FLA generations."]
    (out/"solver_vm_reference_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_cross_vm_solver_gate.py REFERENCE_ARTIFACT_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
