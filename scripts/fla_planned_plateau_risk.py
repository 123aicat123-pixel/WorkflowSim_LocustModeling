#!/usr/bin/env python3
"""Quantify why planned HV plateau may not safely determine a real K16/K24 stop.

This is post-hoc counterfactual analysis of an already completed, genuinely
prospective 24-replay experiment. No threshold is promoted as a final policy.
The first 24 candidate ORDER is frozen using planner objectives alone.
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
    "Sipht_100":(9127.960675000002,8822.13817375)}
THRESHOLDS=(0.01,0.05,0.1,0.2)

def load(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(pts,ref):
    last=ref[1];area=0.
    for m,c in sorted(set(pts)):
        if m<ref[0] and c<last:
            area+=(ref[0]-m)*(last-c);last=c
    return area

def run(root,out):
    paths=list(root.rglob("progressive_*_replays.csv"))
    assert len(paths)==10,len(paths)
    cases=[]
    for p in sorted(paths):
        rows=load(p)
        by=collections.defaultdict(list)
        for x in rows:
            by[x["algorithm"]].append(x)
        assert len(by)==3
        for alg,rr in by.items():
            assert len(rr)==24
            rr.sort(key=lambda x:int(x["candidate_index"]))
            assert [int(r["candidate_index"]) for r in rr]==list(range(1,25))
            wf=rr[0]["workflow"];seed=int(rr[0]["seed"]);ref=REFS[wf]
            planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in rr]
            actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in rr]
            p16,p24=hv(planned[:16],ref),hv(planned,ref)
            s16,s24=hv(actual[:16],ref),hv(actual,ref)
            assert min(p16,p24,s16,s24)>0
            cases.append(dict(workflow=wf,seed=seed,algorithm=alg,
                planned_gain_pct=100*(p24/p16-1),actual_gain_pct=100*(s24/s16-1),
                planned_hv16=p16,planned_hv24=p24,sim_hv16=s16,sim_hv24=s24))
    assert len(cases)==30
    outcomes=[]
    for threshold in THRESHOLDS:
        stopped=[x for x in cases if x["planned_gain_pct"]<threshold]
        losses=[x["actual_gain_pct"] for x in stopped]
        outcomes.append(dict(planned_threshold_pct=threshold,stops=len(stopped),
            total=len(cases),actual_replays_saved=8*len(stopped),
            cases_missed_gt_0_1pct=sum(x>0.1 for x in losses),
            mean_actual_gain_foregone_pct=statistics.mean(losses) if losses else 0,
            max_actual_gain_foregone_pct=max(losses) if losses else 0))
    out.mkdir(parents=True,exist_ok=True)
    for name,items in (("planned_plateau_cases.csv",cases),("planned_plateau_thresholds.csv",outcomes)):
        with (out/name).open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(items[0]))
            writer.writeheader();writer.writerows(items)
    report=["# Planner-only HV plateau can mispredict actual WorkflowSim K16-to-K24 returns",
        "",
        "Original NEW-SEED prospective experiment: Actions 41592705525, DAG100 families CyberShake, Epigenomics, Inspiral, Montage and Sipht × seeds 72/73 × FLA v7/v12/NSGA-II.",
        "The real experiment ALWAYS executed K24 independent WorkflowSim replays per solver; K16 is the first 16 in a planned-objective-only ordered selection. This evaluation is post-hoc. It is not a prospectively executed early-stop policy.",
        "The same frozen objective reference was inherited from earlier run 41572425682 for planned and simulated prefix HV within each DAG. Planner-only HV gain is knowable before replay; actual gain is measured only afterward.",
        "",
        "| Rule: stop at K16 when planned K16→K24 HV gain below | Stops / 30 | Hypothetical simulator calls saved | Stops hiding >0.1% actual HV gain | Max missed actual HV gain |",
        "|---|---:|---:|---:|---:|"]
    for x in outcomes:
        report.append(f"| {x['planned_threshold_pct']:.2f}% | {x['stops']}/30 | "+
            f"{x['actual_replays_saved']} | {x['cases_missed_gt_0_1pct']} | "+
            f"{x['max_actual_gain_foregone_pct']:.3f}% |")
    suspect=sorted(cases,key=lambda x:(x["actual_gain_pct"]-x["planned_gain_pct"]),reverse=True)
    report+=["","## Largest planner/real marginal HV disagreements","",
        "| Workflow | Seed | Solver | Planned HV gain from 8 extra replays | Actual simulator HV gain |",
        "|---|---:|---|---:|---:|"]
    for x in suspect[:8]:
        report.append(f"| {x['workflow']} | {x['seed']} | {x['algorithm']} | "+
          f"{x['planned_gain_pct']:.5f}% | {x['actual_gain_pct']:.5f}% |")
    report+=["","## Interpretation",
        "A small planned marginal HV is only a heuristic signal; it is NOT an upper bound on actual simulator HV gain. Epigenomics has counterexamples.",
        "Thresholds are exploratory on this ALREADY INSPECTED cohort, not a pre-registered prospective stopping rule or an accepted novel algorithm.",
        "The within-case 30 arm observations are correlated across only 10 workflow/optimizer-seed cases and five DAG families.",
        "No new simulator calls are claimed by this analysis; every record derives from the original independently performed K24 runs.",
        "A trustworthy early-stop rule must be predeclared from separate training data and validated on NEW workload/VM regimes; report worst-case missed HV and real time/call savings."]
    (out/"planned_plateau_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_planned_plateau_risk.py ACTIONS_ARTIFACT_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
