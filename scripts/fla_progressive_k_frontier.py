#!/usr/bin/env python3
"""Progressive prefix-HV value under truly K24 prospective replay, using K=8/16/24 prefixes.

Selection is exclusively from planned objectives. The 24 real WorkflowSim
simulations are a single fixed ascending replay sequence; shorter-budget
outcomes are analytically evaluated on prefixes only and never use future
simulator labels to choose any item. This is not a claim that K=8 calls were
separately run.
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
    "Inspiral_100":(11044.129825,11209.86290125),
    "Montage_100":(568.6573,570.969505),
    "Sipht_100":(9127.960675000002,8822.13817375)
}
SEEDS=(72,73)
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
KVALUES=(8,16,24)

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    last=ref[1];total=0.
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def run(root,out):
    found={}
    for wf in REFS:
        for seed in SEEDS:
            label="progressive_"+wf+"_s"+str(seed)
            files=list(root.rglob(label+"_replays.csv"))
            summaries=list(root.rglob(label+"_summary.csv"))
            assert len(files)==len(summaries)==1,(label,files,summaries)
            rows=read(files[0]);stat=read(summaries[0])
            assert len(rows)==72 and len(stat)==3
            by=collections.defaultdict(list)
            for row in rows:
                assert row["workflow"]==wf and int(row["seed"])==seed
                assert row["algorithm"] in ALGOS
                assert math.isfinite(float(row["sim_makespan"])) and float(row["sim_makespan"])>0
                assert math.isfinite(float(row["sim_cost"])) and float(row["sim_cost"])>0
                by[row["algorithm"]].append(row)
            assert set(by)==set(ALGOS)
            stat={x["algorithm"]:x for x in stat}
            assert set(stat)==set(ALGOS)
            for alg in ALGOS:
                r=by[alg]
                assert len(r)==24 and sorted(int(x["candidate_index"]) for x in r)==list(range(1,25))
                assert len(set(x["mapping"] for x in r))==24
                assert int(stat[alg]["evaluations"])==int(stat[alg]["captured_evaluations"])==3030
                assert int(stat[alg]["replayed"])==24
                assert int(stat[alg]["distinct_observed"])>=24
                r.sort(key=lambda x:int(x["candidate_index"]))
                found[wf,seed,alg]=r
    records=[];marginal=[]
    for (wf,seed,alg),rows in sorted(found.items()):
        scores={}
        for k in KVALUES:
            chosen=rows[:k]
            scores[k]=hv([(float(x["sim_makespan"]),float(x["sim_cost"])) for x in chosen],REFS[wf])
            assert math.isfinite(scores[k]) and scores[k]>0,(wf,seed,alg,k)
            records.append(dict(workflow=wf,seed=seed,algorithm=alg,
                replay_prefix_k=k,true_simulator_replays_per_run=24,
                search_evaluations=3030,hv=scores[k],
                ref_m=REFS[wf][0],ref_c=REFS[wf][1]))
        assert scores[8]<=scores[16]*(1+1e-12) and scores[16]<=scores[24]*(1+1e-12)
        marginal.append(dict(workflow=wf,seed=seed,algorithm=alg,
            hv8=scores[8],hv16=scores[16],hv24=scores[24],
            gain_8_to_16_pct=100*(scores[16]/scores[8]-1),
            gain_16_to_24_pct=100*(scores[24]/scores[16]-1),
            recovery_k8_of_k24_pct=100*scores[8]/scores[24],
            recovery_k16_of_k24_pct=100*scores[16]/scores[24]))
    assert len(records)==len(found)*len(KVALUES)==90 and len(marginal)==30
    out.mkdir(parents=True,exist_ok=True)
    for name,rr in (("progressive_k_hv.csv",records),("progressive_k_marginal.csv",marginal)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rr[0]))
            w.writeheader();w.writerows(rr)
    report=["# Prospective Pareto-cover simulator-replay budget frontier, K=8/16/24",
      "",
      "Five 100-task DAG families, two FRESH optimizer seeds (72/73), three solver arms and 3030 actual planning fitness calls each.",
      "Each arm SELECTS the 24-schedule ordered Pareto-cover prefix from planned data ONLY and ACTUALLY performs 24 independent WorkflowSim replays. K=8 and K=16 values are retrospective prefix scores within the SAME real K24 run; they are not separately executed K8/K16 prospective jobs.",
      "Pre-fixed per-family HV reference originates in older independent Actions 41572425682 and was not changed based on this cohort.",
      "An 8-call extra budget can add HV but cannot decrease HV when all assignments are retained; this mathematical monotonicity alone is NOT evidence of algorithm innovation.",
      "",
      "| Algorithm | Mean K8/K24 HV | Mean K16/K24 HV | Avg HV gain K8 to K16 | Avg HV gain K16 to K24 | K16 within 99% of K24 |",
      "|---|---:|---:|---:|---:|---:|"]
    for alg in ALGOS:
        a=[x for x in marginal if x["algorithm"]==alg]
        report.append("| "+alg+" | "+f"{statistics.mean(x['recovery_k8_of_k24_pct'] for x in a):.3f}% | "+
            f"{statistics.mean(x['recovery_k16_of_k24_pct'] for x in a):.3f}% | "+
            f"+{statistics.mean(x['gain_8_to_16_pct'] for x in a):.3f}% | "+
            f"+{statistics.mean(x['gain_16_to_24_pct'] for x in a):.3f}% | "+
            f"{sum(x['recovery_k16_of_k24_pct']>=99 for x in a)}/{len(a)} |")
    report+=["","## All cases, including largest marginal benefits","",
        "| Workflow | Seed | Solver | K16 vs K24 retained HV | Gain from next 8 replays |",
        "|---|---:|---|---:|---:|"]
    for x in marginal:
        report.append(f"| {x['workflow']} | {x['seed']} | {x['algorithm']} | "+
          f"{x['recovery_k16_of_k24_pct']:.3f}% | +{x['gain_16_to_24_pct']:.3f}% |")
    report+=["","## Scientific boundaries",
       "Only 10 independent workflow/optimizer-seed cases across five DAG families; three correlated solver arms per case.",
       "Even a K16 prefix close to K24 is NOT necessarily close to the exhaustive 3030-visited oracle, because all unselected assignments lack simulator labels.",
       "The same completed K24 run produces all prefixes. Claim 24 simulator calls per solver, not 8 or 16 total calls in this validation.",
       "Wall-clock simulator cost and practical instance-dependent stopping criteria require separate validation.",
       "This only measures budget sensitivity of Pareto-cover screening and does not establish superiority of FLA v12 over NSGA-II."]
    (out/"progressive_k_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_progressive_k_frontier.py INPUT_ROOT OUTPUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
