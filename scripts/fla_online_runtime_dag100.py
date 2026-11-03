#!/usr/bin/env python3
"""Compare actual simulator HV and measured wall-clock for two K16 policies.

All decisions in online-observed-hv use only previously observed replay values.
Evaluation reference is from historical run 41572425682, not fit to new seeds.
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
SEEDS=(101,102)
POLICIES=("pareto-cover","online-observed-hv")
ALGOS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def load(p):
    with p.open(newline="") as f:return list(csv.DictReader(f))

def hv(points,ref):
    total,last=0.,ref[1]
    for m,c in sorted(set(points)):
        if m<ref[0] and c<last:
            total+=(ref[0]-m)*(last-c)
            last=c
    return total

def run(root,out):
    data={}
    hist={}
    for wf in REFS:
        for seed in SEEDS:
            for policy in POLICIES:
                prefix=policy+"-"+wf+"-s"+str(seed)
                files={suffix:list(root.rglob(prefix+suffix))
                    for suffix in ("_summary.csv","_replays.csv","_visited_fingerprints.csv")}
                assert all(len(v)==1 for v in files.values()),(prefix,files)
                stat=load(files["_summary.csv"][0])
                replay=load(files["_replays.csv"][0])
                digest=load(files["_visited_fingerprints.csv"][0])
                assert len(stat)==len(digest)==3 and len(replay)==48,prefix
                bystat={r["algorithm"]:r for r in stat}
                byhash={r["algorithm"]:r["history_sha256"] for r in digest}
                assert set(bystat)==set(byhash)==set(ALGOS)
                for alg in ALGOS:
                    row=bystat[alg]
                    assert int(row["evaluations"])==int(row["captured_evaluations"])==3030
                    assert int(row["replayed"])==16
                    selection=float(row["selection_ms"])
                    simulation=float(row["replay_ms"])
                    search=float(row["search_ms"])
                    reported=float(row["search_selection_replay_ms"])
                    assert all(math.isfinite(x) and x>=0 for x in (selection,simulation,search,reported))
                    assert simulation>0
                    assert abs((selection+simulation+search)-reported)<0.004
                    rr=sorted((r for r in replay if r["algorithm"]==alg),
                              key=lambda r:int(r["candidate_index"]))
                    assert len(rr)==16 and [int(r["candidate_index"]) for r in rr]==list(range(1,17))
                    assert len({r["mapping"] for r in rr})==16
                    pts=[(float(r["sim_makespan"]),float(r["sim_cost"])) for r in rr]
                    assert all(math.isfinite(v) and v>0 for p in pts for v in p)
                    data[wf,seed,alg,policy]=dict(hv=hv(pts,REFS[wf]),search=search,
                        selection=selection,simulation=simulation,total=reported,
                        first4=[r["mapping"] for r in rr[:4]],hash=byhash[alg])
                    hist[wf,seed,alg,policy]=byhash[alg]
    assert len(data)==60
    rows=[]
    for wf in sorted(REFS):
        for seed in SEEDS:
            for alg in ALGOS:
                c=data[wf,seed,alg,"pareto-cover"]
                o=data[wf,seed,alg,"online-observed-hv"]
                assert c["hash"]==o["hash"] and c["first4"]==o["first4"]
                assert c["hv"]>0 and o["hv"]>0
                rows.append(dict(workflow=wf,seed=seed,algorithm=alg,
                    cover_hv=c["hv"],observed_hv=o["hv"],
                    observed_vs_cover_hv_pct=100*(o["hv"]/c["hv"]-1),
                    cover_search_ms=c["search"],observed_search_ms=o["search"],
                    cover_selection_ms=c["selection"],observed_selection_ms=o["selection"],
                    cover_replay_ms=c["simulation"],observed_replay_ms=o["simulation"],
                    cover_total_ms=c["total"],observed_total_ms=o["total"],
                    selection_delta_ms=o["selection"]-c["selection"],
                    total_delta_ms=o["total"]-c["total"],
                    total_relative_change_pct=100*(o["total"]/c["total"]-1)))
    assert len(rows)==30
    out.mkdir(parents=True,exist_ok=True)
    with (out/"online_runtime_paired.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    report=["# Real K16 online observed-front versus Pareto coverage: HV AND runtime",
        "",
        "Five DAG100 families × two fresh seeds 101/102 × three solvers. 3030 real planner evaluations and K=16 actual independent WorkflowSim replays per algorithm/policy. Identical complete SHA256 candidate histories and first four mapped replay genotypes.",
        "Unlike prior 100-task factorial studies, this study uses timing instrumentation from its exact source SHA: search_ms, selection_ms, replay_ms and reconciled search_selection_replay_ms.",
        "The evaluation reference was fixed in prior run 41572425682. Online decisions cannot access unobserved outcomes or the evaluation reference; only already-observed real simulator outcomes are used.",
        "",
        "| Algorithm | Mean paired online HV gain | Online HV wins /10 | Median selection overhead change | Median total wall-clock change | Total-time wins /10 |",
        "|---|---:|---:|---:|---:|---:|"]
    for alg in ALGOS:
        x=[r for r in rows if r["algorithm"]==alg]
        report.append(f"| {alg} | {statistics.mean(r['observed_vs_cover_hv_pct'] for r in x):+.4f}% | "+
          f"{sum(r['observed_vs_cover_hv_pct']>0 for r in x)}/10 | "+
          f"{statistics.median(r['selection_delta_ms'] for r in x):+.3f} ms | "+
          f"{statistics.median(r['total_relative_change_pct'] for r in x):+.3f}% | "+
          f"{sum(r['total_delta_ms']<0 for r in x)}/10 |")
    report+=["","## Every paired DAG/seed/solver observation (including negative cases)","",
        "| DAG | Seed | Solver | Online HV gain | Selection-time delta | Total-time delta |",
        "|---|---:|---|---:|---:|---:|"]
    for r in rows:
        report.append(f"| {r['workflow']} | {r['seed']} | {r['algorithm']} | "+
            f"{r['observed_vs_cover_hv_pct']:+.4f}% | "+
            f"{r['selection_delta_ms']:+.3f} ms | "+
            f"{r['total_relative_change_pct']:+.3f}% |")
    report+=["","## Interpretation boundaries",
        "Equal planner evaluations and simulator replay calls are enforced. Total time is SEARCH + SELECTION + actual SIMULATOR REPLAY as instrumented, not Actions runner startup, javac compilation, I/O or CI queue time.",
        "Each policy runs in a separate JVM process, potentially with different JIT warmup and runner contention; timing results are measurement samples, not calibrated hardware benchmarks.",
        "K16 online greedy may improve HV but cost more selection CPU time. Do not call a method faster without considering the total measured budget and variability.",
        "30 algorithm-level paired comparisons share only ten workflow/seed blocks across five families. No significance from treating all 30 as independent DAG instances.",
        "No optimized feedback is returned to FLA generations. This is a general post-search selection technique and does not prove FLA v12 superiority over NSGA-II.",
        "These DAG families were involved in development. External unseen DAG instances and heterogeneous VM configurations remain essential before publication."]
    (out/"online_runtime_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_online_runtime_dag100.py ARTIFACT_ROOT REPORT_DIR")
    run(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
