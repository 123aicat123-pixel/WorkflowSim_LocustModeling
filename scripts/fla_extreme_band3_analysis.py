#!/usr/bin/env python3
"""Check equal-K real WorkflowSim ablation on new 100-task seeds.

Do not select winning parameters or reference using this cohort.
All reference points are inherited from Actions 41572425682, before this experiment.
"""
import collections
import csv
import math
import pathlib
import statistics
import sys

REFS={
    "CyberShake_100":(6806.24215,3280.0303),
    "Epigenomics_100":(211858.3560250001,217310.76064),
    "Inspiral_100":(11044.129825,11209.86290125),
    "Montage_100":(568.6573,570.969505),
    "Sipht_100":(9127.960675000002,8822.13817375)
}
SEEDS=(64,65)
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
POLICIES=("pareto-cover","extreme-band3","scalar-sweep")

def read(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))

def pareto(pts):
    low=float("inf");front=[]
    for m,c in sorted(set(pts)):
        if c<low:front.append((m,c));low=c
    return front

def hv(pts,ref):
    total,last=0.,ref[1]
    for m,c in pareto(pts):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def main(root,out):
    histories={}
    points=collections.defaultdict(list)
    for wf in REFS:
        for seed in SEEDS:
            for policy in POLICIES:
                prefix=policy+"_"+wf+"_s"+str(seed)
                s=list(root.rglob(prefix+"_summary.csv"))
                r=list(root.rglob(prefix+"_replays.csv"))
                h=list(root.rglob(prefix+"_visited_fingerprints.csv"))
                assert len(s)==len(r)==len(h)==1,(prefix,s,r,h)
                summaries=read(s[0]);replays=read(r[0]);hashes=read(h[0])
                assert len(summaries)==len(hashes)==3 and len(replays)==48
                by={x["algorithm"]:x for x in summaries}
                assert set(by)==set(ALGOS)
                for row in hashes:
                    alg=row["algorithm"]
                    assert alg in by
                    assert row["history_sha256"] and len(row["history_sha256"])==64
                    assert int(row["distinct_visited"])==int(by[alg]["distinct_observed"])
                    assert int(by[alg]["evaluations"])==int(by[alg]["captured_evaluations"])==3030
                    assert int(by[alg]["replayed"])==16
                    histories[wf,seed,policy,alg]=row["history_sha256"]
                for row in replays:
                    alg=row["algorithm"]
                    assert alg in ALGOS
                    m,c=float(row["sim_makespan"]),float(row["sim_cost"])
                    assert math.isfinite(m) and math.isfinite(c) and m>0 and c>0
                    points[wf,seed,policy,alg].append((m,c))
    assert len(histories)==len(points)==len(REFS)*len(SEEDS)*len(POLICIES)*len(ALGOS)
    assert all(len(v)==16 for v in points.values())
    scores=[];paired=[]
    for wf in sorted(REFS):
        for seed in SEEDS:
            for alg in ALGOS:
                assert len({histories[wf,seed,p,alg] for p in POLICIES})==1,(wf,seed,alg)
                value={}
                extreme={}
                for policy in POLICIES:
                    pts=points[wf,seed,policy,alg]
                    value[policy]=hv(pts,REFS[wf])
                    extreme[policy]=(min(v[0] for v in pts),min(v[1] for v in pts))
                    scores.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        sim_hv=value[policy],minimum_makespan=extreme[policy][0],
                        minimum_cost=extreme[policy][1],history_sha256=histories[wf,seed,policy,alg]))
                base=value["pareto-cover"];candidate=value["extreme-band3"];sweep=value["scalar-sweep"]
                paired.append(dict(workflow=wf,seed=seed,algorithm=alg,
                    band_vs_cover_pct=100*(candidate/max(base,1e-12)-1),
                    band_vs_sweep_pct=100*(candidate/max(sweep,1e-12)-1),
                    band_beats_cover=int(candidate>base),band_beats_sweep=int(candidate>sweep),
                    cover_hv=base,band_hv=candidate,sweep_hv=sweep,
                    cover_m=extreme["pareto-cover"][0],band_m=extreme["extreme-band3"][0],
                    sweep_m=extreme["scalar-sweep"][0],
                    cover_c=extreme["pareto-cover"][1],band_c=extreme["extreme-band3"][1],
                    sweep_c=extreme["scalar-sweep"][1]))
    report=[
        "# K16 extreme-band3 ablation: independent 100-task seeds 64/65",
        "",
        "Five DAX families and two new optimizer seeds per family. Exact 3030 actual planning calls and 16 WorkflowSim calls per algorithm/policy. SHA-256 of complete distinct visited genotypes and exact planned double bits was verified identical across all three policies for each algorithm/seed.",
        "Three policies: original Pareto/max-min coverage, up-to-three distinct planned points at BOTH objective extremes plus coverage, and extreme-first scalar sweep.",
        "The band quota (3 for K16) was fixed BEFORE the new seed runs, based on an observed Sipht failure at older seeds, so this study is a follow-up rather than untouched original-discovery validation.",
        "Frozen HV reference per workflow was inherited from independent earlier run 41572425682 and not adjusted for these results.",
        "",
        "| Optimizer | Mean band vs coverage | Band wins vs coverage | Mean band vs scalar | Band wins vs scalar |",
        "|---|---:|---:|---:|---:|"
    ]
    for alg in ALGOS:
        a=[x for x in paired if x["algorithm"]==alg]
        report.append("| "+alg+" | "+
            f"{statistics.mean(x['band_vs_cover_pct'] for x in a):+.4f}% | "+
            f"{sum(x['band_beats_cover'] for x in a)}/{len(a)} | "+
            f"{statistics.mean(x['band_vs_sweep_pct'] for x in a):+.4f}% | "+
            f"{sum(x['band_beats_sweep'] for x in a)}/{len(a)} |")
    report+=["","## Full per-case evidence (negative results retained)",
        "",
        "| Workflow | Seed | Solver | Band vs cover HV | Band vs scalar HV | Min makespan band/cover/sweep |",
        "|---|---:|---|---:|---:|---|"]
    for x in paired:
        report.append(f"| {x['workflow']} | {x['seed']} | {x['algorithm']} | "+
            f"{x['band_vs_cover_pct']:+.4f}% | {x['band_vs_sweep_pct']:+.4f}% | "+
            f"{x['band_m']:.4f} / {x['cover_m']:.4f} / {x['sweep_m']:.4f} |")
    report+=["","## Scientific limitations",
       "The three algorithms are correlated within each workflow-seed. The 30 algorithm-case values represent only 10 workflow-seed observations across five DAG families.",
       "Even with exact equal counts of planning and simulator evaluations, wall-clock times can differ.",
       "If band3 fails on these new seeds, report it without tuning the same sample; use a new untouched cohort for any next revision.",
       "The band only reserves planning extremes, and those need not be actual simulator extremes. There is no oracle use before selection.",
       "The study evaluates post-search simulator screening quality. It cannot establish FLA v12 superiority or an overall novel optimizer."]
    out.mkdir(parents=True,exist_ok=True)
    for name,data in (("band3_scores.csv",scores),("band3_paired.csv",paired)):
        with (out/name).open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]))
            writer.writeheader();writer.writerows(data)
    (out/"band3_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: fla_extreme_band3_analysis.py INPUT_ROOT OUTPUT_DIR")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
