#!/usr/bin/env python3
"""Describe planning-makespan margin vs independent simulator pairwise rank flips.

All pair labels are from an OLD full simulator replay, never from prospectively
unobserved schedules. Pair counts are dependent and not an independent n for p-values.
"""
import csv
import pathlib
import collections
import math
import sys

BINS=((0.,.01,"<1%"),(.01,.05,"1–5%"),(.05,float("inf"),">=5%"))

def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def run(root,out):
    files=list(root.rglob("budget_*_replays.csv"))
    assert len(files)==8
    group=collections.defaultdict(lambda:collections.Counter())
    for path in files:
        rows=read(path)+read(pathlib.Path(str(path).replace("_replays.csv","_screening_samples.csv")))
        for alg in {r["algorithm"] for r in rows}:
            sub=[r for r in rows if r["algorithm"]==alg]
            assert len({r["mapping"] for r in sub})==len(sub)
            for i,r in enumerate(sub):
                pm=float(r["planned_makespan"]);sm=float(r["sim_makespan"])
                for other in sub[i+1:]:
                    pm2=float(other["planned_makespan"]);sm2=float(other["sim_makespan"])
                    if pm==pm2 or sm==sm2:continue
                    gap=abs(pm-pm2)/min(pm,pm2)
                    flipped=(pm-pm2)*(sm-sm2)<0
                    b=next(label for low,high,label in BINS if low<=gap<high)
                    for k in (("ALL",b),(r["workflow"],b)):
                        group[k]["total"]+=1
                        group[k]["flip"]+=int(flipped)
    families=sorted({x[0] for x in group if x[0]!="ALL"})
    assert len(families)==4
    cases=[]
    for wf in ["ALL",*families]:
        for _,_,label in BINS:
            s=group[wf,label]
            assert s["total"]>0,(wf,label)
            cases.append(dict(workflow=wf,planned_gap_bin=label,eligible_pairs=s["total"],
                inverted_pairs=s["flip"],flip_rate_pct=100*s["flip"]/s["total"]))
    out.mkdir(parents=True,exist_ok=True)
    with (out/"margin_rank_inversion.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cases[0]))
        w.writeheader();w.writerows(cases)
    report=["# How planned makespan margin predicts simulator rank flips (diagnostic)",
        "",
        "Complete OLD real WorkflowSim replay from Actions 41582476054; 4 DAG100 families × 2 seeds × 3 algorithms. Pair counts are WITHIN each solver-case history and highly dependent.",
        "For a pair of schedules A,B: planned gap = abs(A.plannedMakespan-B.plannedMakespan)/min(planned makespans); flip means the true independent simulator reverses their strictly ordered makespan.",
        "Exact planned or simulator ties are excluded. No candidate policy was trained or tuned from this diagnostic.",
        "",
        "| Family | Planned margin | Non-tied pairs | Reversals | Reversal frequency |",
        "|---|---|---:|---:|---:|"]
    for row in cases:
        report.append(f"| {row['workflow']} | {row['planned_gap_bin']} | "+
            f"{row['eligible_pairs']} | {row['inverted_pairs']} | {row['flip_rate_pct']:.3f}% |")
    report+=["","## Interpret carefully",
       "Small planned differences predict more reversals IN SOME DAG families, but the effect is not a monotonic, universal calibration rule.",
       "A family with substantial inversions even for >=5% planned differences (e.g. Epigenomics) cannot be corrected merely by a single close-tie tolerance.",
       "Pair counts reuse each schedule multiple times; 70,000+ pair comparisons do not mean 70,000 independent workflows.",
       "This is a retrospective mechanism diagnosis, NOT prospective K16 Pareto-screening performance and NOT proof of an improved FLA search.",
       "A probabilistic uncertainty model needs genuinely independent simulator training and new heldout DAG/VM regimes before deploying."]
    (out/"margin_rank_inversion_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_rank_inversion_margin_gate.py ORIGINAL_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
