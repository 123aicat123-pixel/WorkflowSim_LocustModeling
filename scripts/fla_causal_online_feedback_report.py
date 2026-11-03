#!/usr/bin/env python3
"""Real K16 causal online replays versus planned-only Pareto cover on fresh seeds.

Uses prior frozen references for the 50/30/25-task families from previously
executed full visited-run evidence. Report all losses, never tune on these seeds.
"""
import csv, pathlib, collections, statistics, math, sys

REFS = {
    "CyberShake_30": (1599.5894, 1021.5735),
    "Inspiral_50": (8423.484174999998, 6833.036574999994),
    "Montage_25": (128.9026, 120.508165),
}
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
SEEDS=(81,82)

def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    low=ref[1];total=0.0
    for m,c in sorted(set(points)):
        if m<ref[0] and c<low:
            total+=(ref[0]-m)*(low-c)
            low=c
    return total

def run(root,out):
    results=[];pairs=[]
    for wf in REFS:
        for seed in SEEDS:
            by={}
            for policy in ("pareto-cover","online-nearest-hv"):
                prefix=policy+"_"+wf+"_s"+str(seed)
                matches=list(root.rglob(prefix+"_replays.csv"))
                assert len(matches)==1,(prefix,matches)
                rows=read(matches[0])
                assert len(rows)==48
                for alg in ALGOS:
                    xx=[r for r in rows if r["algorithm"]==alg]
                    assert len(xx)==16
                    points=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in xx]
                    score=hv(points,REFS[wf])
                    assert math.isfinite(score) and score>0,(wf,seed,alg,policy,score)
                    by[alg,policy]=score
                    results.append(dict(workflow=wf,seed=seed,algorithm=alg,policy=policy,
                        sim_hv=score,reference_m=REFS[wf][0],reference_c=REFS[wf][1],
                        min_sim_makespan=min(p[0] for p in points),
                        min_sim_cost=min(p[1] for p in points)))
            for alg in ALGOS:
                online=by[alg,"online-nearest-hv"];cover=by[alg,"pareto-cover"]
                pairs.append(dict(workflow=wf,seed=seed,algorithm=alg,online_hv=online,
                    cover_hv=cover,online_relative_gain_pct=100*(online/cover-1),
                    online_wins=int(online>cover),cover_wins=int(cover>online)))
    assert len(pairs)==18 and len(results)==36
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("causal_online_hv.csv",results),("causal_online_paired.csv",pairs)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
    report=["# Causal online-nearest-HV true K16 WorkflowSim smoke experiment",
        "",
        "Fresh seeds 81 and 82, three DAG families, three solver arms, 3030 planned fitness evaluations and exactly 16 actual simulator calls PER solver and policy.",
        "The online feedback arm starts with identical four planned Pareto-cover candidates, then selects candidate #5..#16 using only previously observed simulator makespan and planned cost. Its selection is NOT a pre-simulation screening method.",
        "Equal full ordered unique-genotype planner history SHA256 checked on both policy arms; post-hoc simulated objective labels were not available for candidate choice.",
        "Reference points are fixed from earlier datasets and not fitted to new results. Caveat: 30/50/25 families share earlier algorithm development exposure and are NOT untouched publication holdout.",
        "",
        "| Algorithm | Mean online vs cover relative simulator HV | Online wins | Coverage wins |",
        "|---|---:|---:|---:|"]
    for alg in ALGOS:
        xx=[p for p in pairs if p["algorithm"]==alg]
        report.append(f"| {alg} | {statistics.mean(p['online_relative_gain_pct'] for p in xx):+.4f}% | "+
            f"{sum(p['online_wins'] for p in xx)}/{len(xx)} | {sum(p['cover_wins'] for p in xx)}/{len(xx)} |")
    report+=["","## All paired outcomes","",
        "| Workflow | Seed | Algorithm | Online relative HV change |",
        "|---|---:|---|---:|"]
    for p in pairs:
        report.append(f"| {p['workflow']} | {p['seed']} | {p['algorithm']} | {p['online_relative_gain_pct']:+.4f}% |")
    report+=["","## Limits and safety of scientific conclusions",
        "This is a genuine sequential simulator-in-the-loop selector, not a new FLA optimization operator.",
        "Only six DAG/seed cases and three correlated solver arms, insufficient for inferential publication statistics.",
        "Local prediction parameters (pool=64, warm=4, residual shrink=0.5, cap=10%) were fixed before these seeds and not tuned on results.",
        "A near-zero HV difference may reflect a pre-frozen reference clipping useful points; sensitivity checks are still needed.",
        "Random-replay baselines, simulator wall-clock timing and more heterogeneous heldout DAG/VM settings remain necessary.",
        "Any algorithm deterioration stays visible and the online variant is not promoted to the default unless independently validated."]
    (out/"causal_online_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_causal_online_feedback_report.py INPUT_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
