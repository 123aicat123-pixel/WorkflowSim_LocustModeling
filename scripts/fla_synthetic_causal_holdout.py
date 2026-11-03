#!/usr/bin/env python3
"""Synthetic held-aside topology real K16 three-policy causal mechanism gate.

Primary evaluation reference = 1.5 × (baseline COVER PLANNED maxima across
three solvers and two seeds) + 1 per topology / VM speed. Robustness = 3x.
Reference construction never uses simulator outcomes or online selection.
Any out-of-range actual point makes a reference invalid, not silently clipped.
"""
import csv
import collections
import pathlib
import statistics
import math
import sys

DAGS=("SynthWide_40","SynthDeep_40")
SPEEDS=("default","staggered")
SEEDS=(121,122)
POLICIES=("pareto-cover","online-planned-hv","online-observed-hv")
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
SCALES=(1.5,3.0)

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    last=ref[1];total=0.
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c);last=c
    return total

def run(root,out):
    data={}
    for dag in DAGS:
        for speed in SPEEDS:
            for seed in SEEDS:
                for policy in POLICIES:
                    prefix=f"{policy}-{speed}-{dag}-s{seed}"
                    suff=("_summary.csv","_replays.csv","_visited_fingerprints.csv","_budget_protocol.txt")
                    files={s:list(root.rglob(prefix+s)) for s in suff}
                    assert all(len(v)==1 for v in files.values()),(prefix,files)
                    stat=read(files["_summary.csv"][0])
                    replays=read(files["_replays.csv"][0])
                    hashes=read(files["_visited_fingerprints.csv"][0])
                    assert len(stat)==len(hashes)==3 and len(replays)==48
                    assert {r["algorithm"] for r in stat}=={r["algorithm"] for r in hashes}==set(ALGS)
                    digest={r["algorithm"]:r["history_sha256"] for r in hashes}
                    protocol=files["_budget_protocol.txt"][0].read_text()
                    assert f"VM_SPEED_PROFILE={speed}" in protocol
                    assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                    assert f"PROSPECTIVE_REPLAY_POLICY={policy}" in protocol
                    assert "VM_PRICE_PROFILE=default" in protocol
                    for r in stat:
                        alg=r["algorithm"]
                        assert int(r["evaluations"])==int(r["captured_evaluations"])==3030
                        assert int(r["replayed"])==16
                        selected=sorted((x for x in replays if x["algorithm"]==alg),
                            key=lambda x:int(x["candidate_index"]))
                        assert len(selected)==16 and [int(x["candidate_index"]) for x in selected]==list(range(1,17))
                        assert len({x["mapping"] for x in selected})==16
                        planned=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in selected]
                        actual=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in selected]
                        assert all(math.isfinite(z) and z>0 for p in planned+actual for z in p)
                        data[dag,speed,seed,policy,alg]=dict(planned=planned,actual=actual,
                            sha=digest[alg],warm=[x["mapping"] for x in selected[:4]],
                            total_ms=float(r["search_selection_replay_ms"]))
    assert len(data)==len(DAGS)*len(SPEEDS)*len(SEEDS)*len(POLICIES)*len(ALGS)
    refs={}
    for dag in DAGS:
        for speed in SPEEDS:
            points=[p for seed in SEEDS for alg in ALGS
                for p in data[dag,speed,seed,"pareto-cover",alg]["planned"]]
            refs[dag,speed]=(max(p[0] for p in points),max(p[1] for p in points))
    cases=[];refvalid=[]
    for dag in DAGS:
        for speed in SPEEDS:
            for factor in SCALES:
                ref=tuple(factor*x+1 for x in refs[dag,speed])
                pts=[p for seed in SEEDS for pol in POLICIES for alg in ALGS
                     for p in data[dag,speed,seed,pol,alg]["actual"]]
                invalid=[p for p in pts if p[0]>=ref[0] or p[1]>=ref[1]]
                refvalid.append(dict(topology=dag,speed=speed,scale=factor,
                    ref_m=ref[0],ref_c=ref[1],out_of_range_count=len(invalid)))
                assert not invalid,("Prechosen reference does not contain real points",dag,speed,factor)
                for seed in SEEDS:
                    for alg in ALGS:
                        source=[data[dag,speed,seed,p,alg] for p in POLICIES]
                        assert len({s["sha"] for s in source})==1
                        assert len({tuple(s["warm"]) for s in source})==1
                        c,p,o=(hv(s["actual"],ref) for s in source)
                        assert min(c,p,o)>0
                        cases.append(dict(topology=dag,speed=speed,seed=seed,
                            scale=factor,algorithm=alg,cover_hv=c,planned_greedy_hv=p,
                            observed_front_hv=o,planned_vs_cover_pct=100*(p/c-1),
                            observed_vs_cover_pct=100*(o/c-1),
                            observed_vs_planned_pct=100*(o/p-1),
                            observed_wins_cover=int(o>c),
                            observed_wins_planned=int(o>p),
                            cover_time_ms=source[0]["total_ms"],observed_time_ms=source[2]["total_ms"]))
    assert len(cases)==len(DAGS)*len(SPEEDS)*len(SEEDS)*len(ALGS)*len(SCALES)
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("synthetic_causal_cases.csv",cases),("synthetic_reference_validity.csv",refvalid)):
        with (out/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
    report=["# Truly new SYNTHETIC DAG topologies and VM speed perturbation: causal K16 replay screening",
        "",
        "Generator: scripts/fla_locked_synthetic_dax.py, fixed seed 20261103. SynthWide_40 is five 8-task layers with 2-3 incoming edges from the prior layer; SynthDeep_40 is four 10-task chains with selected cross-lane links. These are NEW constructed synthetic shapes, NOT measured real workflow datasets.",
        "Two independent optimizer seeds 121/122 and two VM speed profiles default and within-tier staggered. Three solver arms, three replay policies: original planned Pareto cover, sequential greedy HV against PLANNED front only, sequential greedy HV using already-OBSERVED true simulator front.",
        "Exact 3030 planned fitness evaluations and K16 independent actual WorkflowSim replays per solver/policy, same SHA-256 unique planned genotype history and same first four warm replay assignments across all policies in a matched scenario.",
        "PREDECLARED primary reference = 1.5× baseline planned COVER maxima +1 per topology/speed (across both seeds/algorithms), secondary 3×. Never compute reference from actual simulator values; if real points outside bound, fail rather than refit.",
        "",
        "| DAG topology | VM speed | Solver | Observed-front HV vs cover (mean of 2 seeds, primary 1.5x) | Wins / 2 | Added observed-front vs planned-only greedy (mean) |",
        "|---|---|---|---:|---:|---:|"]
    for dag in DAGS:
        for speed in SPEEDS:
            for alg in ALGS:
                rr=[r for r in cases if r["topology"]==dag and r["speed"]==speed and
                    r["algorithm"]==alg and r["scale"]==1.5]
                assert len(rr)==2
                report.append(f"| {dag} | {speed} | {alg} | "+
                    f"{statistics.mean(r['observed_vs_cover_pct'] for r in rr):+.4f}% | "+
                    f"{sum(r['observed_wins_cover'] for r in rr)}/2 | "+
                    f"{statistics.mean(r['observed_vs_planned_pct'] for r in rr):+.4f}% |")
    report+=["","## Descriptive pooled by VM speed (primary and secondary refs)","",
        "| VM speed | Solver | Ref scale | Online observed vs cover mean | Wins / 4 | Observed vs planned-only mean |",
        "|---|---|---:|---:|---:|---:|"]
    for speed in SPEEDS:
        for alg in ALGS:
            for factor in SCALES:
                rr=[r for r in cases if r["speed"]==speed and r["algorithm"]==alg and r["scale"]==factor]
                report.append(f"| {speed} | {alg} | {factor:.1f}x | "+
                    f"{statistics.mean(r['observed_vs_cover_pct'] for r in rr):+.4f}% | "+
                    f"{sum(r['observed_wins_cover'] for r in rr)}/4 | "+
                    f"{statistics.mean(r['observed_vs_planned_pct'] for r in rr):+.4f}% |")
    report+=["","## All individual primary-reference comparisons including negatives","",
        "| Topology | Speed | Seed | Algorithm | Planned greedy vs cover | Observed vs cover | Observed vs planned greedy |",
        "|---|---|---:|---|---:|---:|---:|"]
    for r in cases:
        if r["scale"]!=1.5:continue
        report.append(f"| {r['topology']} | {r['speed']} | {r['seed']} | {r['algorithm']} | "+
            f"{r['planned_vs_cover_pct']:+.4f}% | "+
            f"{r['observed_vs_cover_pct']:+.4f}% | "+
            f"{r['observed_vs_planned_pct']:+.4f}% |")
    report+=["","## Limitations",
       "Two synthetic graph structures, two optimizer seeds and two VM settings are an exploratory transfer stress test, NOT publication-grade generalization to real unseen scientific workflow families.",
       "40-task artificially generated DAGs may not preserve production task-size, file-transfer and runtime distributions. Details and generator SHA must be published.",
       "Only K16 simulated subsets are compared; no full-history simulator ground truth is available and no FLA search generations use true feedback.",
       "Within each topology/seed, the three solver arms are correlated. Reference-scale scoring reuses the same true simulator data.",
       "Do not treat a post-hoc identified positive case or alternate reference as a preregistered optimizer win. Report all negative outcomes."]
    (out/"synthetic_causal_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_synthetic_causal_holdout.py ORIGINAL_ARTIFACT_ROOT OUT")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
