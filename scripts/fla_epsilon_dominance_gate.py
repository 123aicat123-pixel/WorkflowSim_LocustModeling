#!/usr/bin/env python3
"""Retrospective pre-simulation epsilon-Pareto makespan dominance ablation.

Reads ONLY previously independently simulated 80-evaluation histories from
Actions 41582476054. No new optimizer or prospective K16 claim. Fixed thresholds
{0,0.5%,1%,2%,3%,5%}; all negative cases are reported.
"""
import collections
import csv
import math
import pathlib
import statistics
import sys

REFS = {
    "CyberShake_100":(6806.24215,3280.0303),
    "Epigenomics_100":(211858.3560250001,217310.76064),
    "Montage_100":(568.6573,570.969505),
    "Sipht_100":(9127.960675000002,8822.13817375)
}
EPS=(0.,.005,.01,.02,.03,.05)
K=16

def read(path):
    with path.open(newline="") as f: return list(csv.DictReader(f))

def hv(points,ref):
    area,last=0.,ref[1]
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            area+=(ref[0]-m)*(last-c);last=c
    return area

def select(items,epsilon):
    remaining=sorted(items,key=lambda r:(r["m"],r["c"],r["mapping"]))
    assert len(remaining)>=K
    lowm=min(x["m"] for x in items);lowc=min(x["c"] for x in items)
    dm=max(1e-12,max(x["m"] for x in items)-lowm)
    dc=max(1e-12,max(x["c"] for x in items)-lowc)
    chosen=[]
    while remaining and len(chosen)<K:
        if epsilon==0:
            layer=[x for x in remaining if not any(
                (y["m"]<=x["m"] and y["c"]<=x["c"] and
                 (y["m"]<x["m"] or y["c"]<x["c"])) for y in remaining)]
        else:
            # A candidate is robustly worse only when another has an
            # epsilon-small makespan AND no more cost. This broadens the first
            # front; it deliberately does not use simulator values.
            layer=[x for x in remaining if not any(
                (y["m"]*(1+epsilon)<x["m"] and y["c"]<=x["c"])
                for y in remaining)]
        assert layer
        while layer and len(chosen)<K:
            if not chosen:
                nxt=min(layer,key=lambda x:(x["m"],x["c"],x["mapping"]))
            else:
                def nearest_sq(x):
                    return min(
                        ((x["m"]-y["m"])/dm)**2+
                        ((x["c"]-y["c"])/dc)**2
                        for y in chosen)
                nxt=min(layer,key=lambda x:(-nearest_sq(x),x["m"],x["c"],x["mapping"]))
            chosen.append(nxt)
            layer.remove(nxt)
        seen={x["mapping"] for x in chosen}
        remaining=[x for x in remaining if x["mapping"] not in seen]
    assert len(chosen)==K and len({x["mapping"] for x in chosen})==K
    return chosen

def run(root,out):
    files=list(root.rglob("budget_*_replays.csv"))
    assert len(files)==8,len(files)
    cases=[]
    for p in sorted(files):
        rows=read(p)+read(pathlib.Path(str(p).replace("_replays.csv","_screening_samples.csv")))
        for alg in sorted({x["algorithm"] for x in rows}):
            sub=[x for x in rows if x["algorithm"]==alg]
            assert len(sub)==len({x["mapping"] for x in sub}) and len(sub)>=K
            wf=sub[0]["workflow"]
            assert wf in REFS
            items=[dict(m=float(x["planned_makespan"]),c=float(x["planned_cost"]),
                mapping=x["mapping"],sim_m=float(x["sim_makespan"]),sim_c=float(x["sim_cost"])) for x in sub]
            full=hv([(x["sim_m"],x["sim_c"]) for x in items],REFS[wf])
            assert full>0
            for eps in EPS:
                result=select(items,eps)
                value=hv([(x["sim_m"],x["sim_c"]) for x in result],REFS[wf])
                cases.append(dict(workflow=wf,seed=int(sub[0]["seed"]),algorithm=alg,
                    epsilon=eps,visited=len(items),oracle_hv=full,selected_hv=value,
                    hv_recovery_pct=100*value/full))
    expected=8*3*len(EPS)
    assert len(cases)==expected,(len(cases),expected)
    base={(x["workflow"],x["seed"],x["algorithm"]):x for x in cases if x["epsilon"]==0}
    assert len(base)==24
    for x in cases:
        key=(x["workflow"],x["seed"],x["algorithm"])
        x["delta_recovery_pp"]=x["hv_recovery_pct"]-base[key]["hv_recovery_pct"]
    out.mkdir(parents=True,exist_ok=True)
    with (out/"epsilon_pareto_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]))
        w.writeheader();w.writerows(cases)
    report=["# Epsilon-makespan dominance uncertainty ablation (retrospective negative control)",
        "",
        "Original independent full-history simulator oracle: GitHub Actions 41582476054, 4 DAG families, 2 optimizer seeds per DAG, 3 solver arms; 24 correlated arm/seed observations.",
        "Full simulator labels are used ONLY for post-hoc scoring, never selection. The K16 choice comes strictly from the same planned makespan/cost + mapping on each fixed history.",
        "Epsilon here relaxes makespan dominance: a candidate A is declared robustly makespan-better than B only if A.makespan*(1+epsilon) < B.makespan and A.cost <= B.cost. Epsilon zero reproduces ordinary Pareto-layer selection. These are exploratory fixed-threshold ablations, not new validated algorithms.",
        "Reference points were inherited from the earlier five-seed 100-task study, fixed before this analysis; outcomes are normalized as within-case HV recovered from the full visited-history simulator front.",
        "",
        "| Makespan tolerance | Mean HV recovery | Change vs epsilon=0 (percentage points) | Improvement/loss/tie counts |",
        "|---|---:|---:|---|"]
    for eps in EPS:
        a=[x for x in cases if x["epsilon"]==eps]
        up=sum(x["delta_recovery_pp"]>1e-10 for x in a)
        down=sum(x["delta_recovery_pp"]< -1e-10 for x in a)
        report.append(f"| {100*eps:g}% | "+
          f"{statistics.mean(x['hv_recovery_pct'] for x in a):.4f}% | "+
          f"{statistics.mean(x['delta_recovery_pp'] for x in a):+.4f} pp | "+
          f"{up}/{down}/{len(a)-up-down} |")
    report+=["","## Per-family mean recovery change from epsilon=0","",
      "| DAG | epsilon=0.5% | epsilon=1% | epsilon=2% | epsilon=3% | epsilon=5% |",
      "|---|---:|---:|---:|---:|---:|"]
    for wf in sorted(REFS):
        fields=[statistics.mean(x["delta_recovery_pp"] for x in cases if x["workflow"]==wf and x["epsilon"]==eps) for eps in EPS[1:]]
        report.append("| "+wf+" | "+" | ".join(f"{z:+.4f} pp" for z in fields)+" |")
    report+=["","## Boundaries",
       "This selection is neither a trained confidence model nor a prospective WorkflowSim experiment. It is a deterministic diagnostic on a small existing simulator-labeled oracle.",
       "The same workloads were used in prior algorithm exploration; this is NOT an untouched validation cohort.",
       "No parameter was chosen and promoted after looking at the best epsilon. All epsilon results, positive and negative, remain visible.",
       "A tolerance that improves individual Sipht cases while hurting Epigenomics or Montage cannot support a universal screening improvement.",
       "The 24 arm/seed cases share only four DAG families; avoid naive p-values treating them as independent."]
    (out/"epsilon_pareto_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_epsilon_dominance_gate.py ORIGINAL_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
