#!/usr/bin/env python3
"""Locked new-bottleneck K16 gate-vs-cover real WorkflowSim comparative score."""
import csv
import math
import pathlib
import statistics
import sys

DAG="SynthBottleneck_40"
SEEDS=(131,132,133)
SPEEDS=("default","staggered")
POLICIES=("pareto-cover","online-observed-hv","online-reliability-gated")
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
REFS=(1.5,3.0)

def rows(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    last=ref[1];result=0.
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            result+=(ref[0]-m)*(last-c);last=c
    return result

def evaluate(root,out):
    data={}
    for speed in SPEEDS:
        for seed in SEEDS:
            hashes={};warm={}
            for pol in POLICIES:
                p=f"{pol}-{speed}-{DAG}-s{seed}"
                files={s:list(root.rglob(p+s)) for s in (
                    "_summary.csv","_replays.csv","_visited_fingerprints.csv",
                    "_budget_protocol.txt")}
                assert all(len(x)==1 for x in files.values()),(p,files)
                stat=rows(files["_summary.csv"][0])
                replay=rows(files["_replays.csv"][0])
                fingerprints=rows(files["_visited_fingerprints.csv"][0])
                assert len(stat)==len(fingerprints)==3 and len(replay)==48
                assert {x["algorithm"] for x in stat}==set(ALGS)
                protocol=files["_budget_protocol.txt"][0].read_text()
                assert "PROSPECTIVE_REPLAY_BUDGET_K=16" in protocol
                assert "PROSPECTIVE_REPLAY_POLICY="+pol in protocol
                assert "VM_SPEED_PROFILE="+speed in protocol
                assert "VM_PRICE_PROFILE=default" in protocol
                hashes[pol]={x["algorithm"]:x["history_sha256"] for x in fingerprints}
                warm[pol]={}
                for s in stat:
                    alg=s["algorithm"]
                    assert int(s["evaluations"])==int(s["captured_evaluations"])==3030
                    assert int(s["replayed"])==16
                    actual=sorted((x for x in replay if x["algorithm"]==alg),key=lambda r:int(r["candidate_index"]))
                    assert len(actual)==16
                    assert [int(x["candidate_index"]) for x in actual]==list(range(1,17))
                    assert len({x["mapping"] for x in actual})==16
                    warm[pol][alg]=[x["mapping"] for x in actual[:4]]
                    predicted=[(float(x["planned_makespan"]),float(x["planned_cost"])) for x in actual]
                    real=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in actual]
                    assert all(math.isfinite(x) and x>0 for xy in predicted+real for x in xy)
                    data[speed,seed,pol,alg]=(predicted,real,float(s["search_selection_replay_ms"]))
                if pol=="online-reliability-gated":
                    tracefiles=list(root.rglob(p+"_online_trace.csv"))
                    assert len(tracefiles)==1
                    trace=rows(tracefiles[0])
                    assert len(trace)==48
                    for alg in ALGS:
                        t=sorted((x for x in trace if x["algorithm"]==alg),key=lambda x:int(x["step"]))
                        assert len(t)==16
                        assert [x["mode"] for x in t[:4]]==["warm"]*4
                        assert all(int(t[i]["observed_before"])==i for i in range(4,16))
                        assert all(x["mode"] in ("gated-cover","gated-observed") for x in t[4:])
            assert all(x==hashes[POLICIES[0]] for x in hashes.values()),(speed,seed,"history changed")
            assert all(x==warm[POLICIES[0]] for x in warm.values()),(speed,seed,"warmups changed")
    out.mkdir(parents=True,exist_ok=True)
    comparisons=[]
    for speed in SPEEDS:
        planned=[xy for seed in SEEDS for alg in ALGS
                 for xy in data[speed,seed,POLICIES[0],alg][0]]
        bound=(max(x[0] for x in planned),max(x[1] for x in planned))
        for factor in REFS:
            ref=(factor*bound[0]+1,factor*bound[1]+1)
            for seed in SEEDS:
                for alg in ALGS:
                    actual=[data[speed,seed,pol,alg][1] for pol in POLICIES]
                    assert all(x<ref[0] and y<ref[1] for pts in actual for x,y in pts),("Invalid reference",speed,seed,alg)
                    vals=[hv(points,ref) for points in actual]
                    assert min(vals)>0
                    comparisons.append(dict(speed=speed,seed=seed,solver=alg,reference=factor,
                      hv_cover=vals[0],hv_observed=vals[1],hv_gated=vals[2],
                      observed_vs_cover_pct=100*(vals[1]/vals[0]-1),
                      gated_vs_cover_pct=100*(vals[2]/vals[0]-1),
                      gated_vs_observed_pct=100*(vals[2]/vals[1]-1),
                      gated_beats_cover=int(vals[2]>vals[0]),
                      gate_runtime_ms=data[speed,seed,POLICIES[2],alg][2],
                      cover_runtime_ms=data[speed,seed,POLICIES[0],alg][2]))
    assert len(comparisons)==len(SPEEDS)*len(SEEDS)*len(ALGS)*len(REFS)
    with (out/"bottleneck_gate_cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(comparisons[0]))
        w.writeheader();w.writerows(comparisons)
    report=["# NEW synthetic bottleneck DAG40: conservative K16 reliability gate results","",
      "Locked NEW DAG generator seed 2026110317; optimization seeds 131,132,133; two VM-speed profiles; three solvers; three predeclared policies. Artificial DAG only. Every policy/solver exactly 3030 planner calls and K16 actual WorkflowSim replays, matching complete history SHA and four warmup candidates per block.",
      "Reference fixed exclusively from baseline planned cover values across seeds/algorithms for each VM speed, x1.5+1 primary, x3+1 robustness, never actual simulator values.",
      "",
      "| Speed | Solver | Reference | Mean gated vs cover | Gated wins / 3 | Mean observed vs cover | Gated vs observed |",
      "|---|---|---:|---:|---:|---:|---:|"]
    for speed in SPEEDS:
        for alg in ALGS:
            for fac in REFS:
                rr=[x for x in comparisons if x["speed"]==speed and x["solver"]==alg and x["reference"]==fac]
                report.append(f"| {speed} | {alg} | {fac:.1f}x | "+
                    f"{statistics.mean(x['gated_vs_cover_pct'] for x in rr):+.4f}% | "+
                    f"{sum(x['gated_beats_cover'] for x in rr)}/3 | "+
                    f"{statistics.mean(x['observed_vs_cover_pct'] for x in rr):+.4f}% | "+
                    f"{statistics.mean(x['gated_vs_observed_pct'] for x in rr):+.4f}% |")
    report.extend(["","## Individual primary-reference comparisons (retain all losses)","",
      "| Speed | Seed | Solver | Gate vs cover | Online observed vs cover | Gate vs observed |",
      "|---|---:|---|---:|---:|---:|"])
    for x in comparisons:
        if x["reference"]==1.5:
            report.append(f"| {x['speed']} | {x['seed']} | {x['solver']} | {x['gated_vs_cover_pct']:+.4f}% | {x['observed_vs_cover_pct']:+.4f}% | {x['gated_vs_observed_pct']:+.4f}% |")
    report.extend(["","## Limitations","",
      "Single artificial 40-task DAG topology, three solver random seeds, small n, and synthetic VM speeds. This is an exploratory falsification test, not evidence of real-world generalization.",
      "The gate is post-search replay screening and does not modify FLA optimization operations. No optimizer superiority claim follows from this result.",
      "The gate thresholds were selected after historical negative examples, so independent evidence is limited to the newly generated bottleneck case. Freeze policy before making any claims.",
      "A favorable 3x reference does not override a negative result on the predeclared 1.5x reference. The identical simulator candidates scored under multiple references are not additional independent observations."])
    (out/"bottleneck_gate_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_reliability_gate_holdout.py INPUT_ROOT OUTPUT_DIR")
    evaluate(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
