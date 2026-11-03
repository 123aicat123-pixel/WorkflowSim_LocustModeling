#!/usr/bin/env python3
"""Post-hoc HV reference sensitivity for pinned real cross-VM K16 replays.

All reference points derive exclusively from the original planned Pareto
coverage selection, with scales fixed in code. No reference is silently
rescued based on simulator scores. Scores are withheld for any factor that
fails to enclose every real point in that matched workflow/speed group.
This reuses old observations: zero new simulator calls or independent data.
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
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
POLICIES=("pareto-cover","online-observed-hv")
SCALES=(1.10,1.25,1.50,2.00,3.00)

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    last=ref[1];total=0.
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total

def dominates(a,b,strict=True):
    return a[0]<=b[0] and a[1]<=b[1] and (
        not strict or a[0]<b[0] or a[1]<b[1])

def run(root,out):
    archive={}
    for wf in WF:
        for seed in SEEDS:
            for speed in SPEEDS:
                for policy in POLICIES:
                    prefix=f"{policy}-{speed}-{wf}-s{seed}"
                    names=list(root.rglob(prefix+"_replays.csv"))
                    assert len(names)==1,(prefix,names)
                    rr=read(names[0])
                    assert len(rr)==48
                    for alg in ALGS:
                        rows=[r for r in rr if r["algorithm"]==alg]
                        assert len(rows)==16
                        planner=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in rows]
                        simulator=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rows]
                        assert all(math.isfinite(v) and v>0 for p in planner+simulator for v in p)
                        archive[wf,seed,speed,policy,alg]=(planner,simulator)
    assert len(archive)==5*2*2*2*3
    bound={}
    for wf in WF:
        for speed in SPEEDS:
            base=[p for seed in SEEDS for alg in ALGS
                for p in archive[wf,seed,speed,"pareto-cover",alg][0]]
            bound[wf,speed]=(max(p[0] for p in base),max(p[1] for p in base))
    validity=[]
    valid_scale={}
    for wf in WF:
        for speed in SPEEDS:
            candidates=[p for seed in SEEDS for policy in POLICIES for alg in ALGS
                for p in archive[wf,seed,speed,policy,alg][1]]
            for factor in SCALES:
                ref=tuple(factor*z+1 for z in bound[wf,speed])
                exceed=sum(p[0]>=ref[0] or p[1]>=ref[1] for p in candidates)
                valid_scale[wf,speed,factor]=exceed==0
                validity.append(dict(workflow=wf,speed=speed,scale=factor,
                    reference_m=ref[0],reference_c=ref[1],out_of_range_actual_points=exceed))
    sensitivities=[]
    extremes=[]
    for wf in WF:
        for seed in SEEDS:
            for speed in SPEEDS:
                for alg in ALGS:
                    a=archive[wf,seed,speed,"pareto-cover",alg][1]
                    b=archive[wf,seed,speed,"online-observed-hv",alg][1]
                    assert len(a)==len(b)==16
                    strictCoverToOnline=sum(any(dominates(p,q) for p in a) for q in b)
                    strictOnlineToCover=sum(any(dominates(p,q) for p in b) for q in a)
                    extremes.append(dict(workflow=wf,seed=seed,speed=speed,algorithm=alg,
                        online_min_m_gain_pct=100*(min(p[0] for p in a)/min(p[0] for p in b)-1),
                        online_min_c_gain_pct=100*(min(p[1] for p in a)/min(p[1] for p in b)-1),
                        cover_strictly_dominates_online_points=strictCoverToOnline,
                        online_strictly_dominates_cover_points=strictOnlineToCover))
                    for factor in SCALES:
                        ref=tuple(factor*z+1 for z in bound[wf,speed])
                        valid=valid_scale[wf,speed,factor]
                        av,bv=(hv(a,ref),hv(b,ref)) if valid else (None,None)
                        if valid:assert av>0 and bv>0
                        sensitivities.append(dict(workflow=wf,seed=seed,speed=speed,
                            algorithm=alg,scale=factor,reference_valid=valid,
                            cover_hv=av,online_hv=bv,
                            online_gain_pct=(100*(bv/av-1) if valid else None)))
    assert len(sensitivities)==60*len(SCALES) and len(extremes)==60
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("reference_validity.csv",validity),
                      ("reference_sensitivity.csv",sensitivities),
                      ("reference_free_extremes.csv",extremes)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
    report=["# Offline reference sensitivity and reference-free quality: K16 cross-VM study",
        "",
        "Original actual independent WorkflowSim simulations: Actions 41603751878. This audit retrieves those SAME observations and does NOT run any new optimizer, candidate selection or simulator.",
        "References are (factor × max planned Pareto-cover makespan+1, factor × max planned Pareto-cover cost+1) across BOTH optimizer seeds and three solvers per workflow / VM speed. Online choices and real labels never influence construction.",
        "A factor with ANY actual point on/outside its reference is flagged invalid and its HV scores are deliberately withheld (not silently clipped). Factor 3 is identical to original report.",
        "",
        "| Scale | Valid workflow-speed reference groups / 10 | Out-of-range actual points |",
        "|---|---:|---:|"]
    for factor in SCALES:
        a=[r for r in validity if r["scale"]==factor]
        report.append(f"| {factor:.2f} | {sum(r['out_of_range_actual_points']==0 for r in a)}/10 | "+
                      f"{sum(r['out_of_range_actual_points'] for r in a)} |")
    report+=["","## Within-family paired relative HV gain, by profile and scale","",
       "| Speed | Algorithm | Reference factor | Valid cases / 10 | Mean gain among valid pairs | Wins / valid |",
       "|---|---|---:|---:|---:|---:|"]
    for speed in SPEEDS:
        for alg in ALGS:
            for factor in SCALES:
                rows=[r for r in sensitivities if r["speed"]==speed
                    and r["algorithm"]==alg and r["scale"]==factor]
                valid=[r for r in rows if r["reference_valid"]]
                mean=(f"{statistics.mean(r['online_gain_pct'] for r in valid):+.5f}%" if valid else "NA")
                report.append(f"| {speed} | {alg} | {factor:.2f} | {len(valid)}/10 | "+
                    f"{mean} | {sum(r['online_gain_pct']>0 for r in valid)}/{len(valid)} |")
    report+=["","## Reference-free extreme and strict-dominance comparison","",
        "Positive min-M gain means ONLINE obtained a smaller minimum ACTUAL makespan; positive min-C gain means ONLINE obtained a smaller minimum ACTUAL cost.",
        "Strict domination counts include distinct individual selected solutions, not all full-history schedules.",
        "",
        "| Speed | Solver | Average relative improvement in minimum actual makespan | Average relative improvement in minimum actual cost | Strictly dominated points, cover→online vs online→cover |",
        "|---|---|---:|---:|---|"]
    for speed in SPEEDS:
        for alg in ALGS:
            x=[r for r in extremes if r["speed"]==speed and r["algorithm"]==alg]
            report.append(f"| {speed} | {alg} | "+
                f"{statistics.mean(r['online_min_m_gain_pct'] for r in x):+.5f}% | "+
                f"{statistics.mean(r['online_min_c_gain_pct'] for r in x):+.5f}% | "+
                f"{sum(r['cover_strictly_dominates_online_points'] for r in x)} / "+
                f"{sum(r['online_strictly_dominates_cover_points'] for r in x)} |")
    report+=["","## Limitations",
       "HV gain depends on reference placement, even when the selected real candidates do not change. A favorable scale cannot be chosen post-hoc as though preregistered.",
       "The strict dominance and extreme measures are descriptive for two K16 sets, not the complete simulator Pareto frontier.",
       "Only five previously used DAG families and two seeds per VM setting; profile scales are fixed experiments, not independent workflows.",
       "No claim about FLA v12 optimizer advantage follows from post-search feedback screening."]
    (out/"reference_sensitivity_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_cross_vm_reference_audit.py ORIGINAL_ARTIFACTS OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
