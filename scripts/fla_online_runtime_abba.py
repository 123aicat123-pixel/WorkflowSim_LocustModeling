#!/usr/bin/env python3
"""AB/BA order crossover smoke for instrumented online-vs-coverage runtime.

Each fixed search seed is repeated twice per policy in separate Java JVMs:
AB (cover then observed) and BA (observed then cover). Repeated runs are a
measurement bias diagnostic, NOT additional independent DAG experiments.
"""
import csv
import pathlib
import statistics
import math
import sys

WORKFLOWS=("Montage_25","CyberShake_30","Inspiral_50")
SEEDS=(108,109)
POLICIES=("pareto-cover","online-observed-hv")
ALGS=("DAG-Pareto-FLA[v7-costseed]","DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))

def main(root,out):
    records=[]
    for wf in WORKFLOWS:
        for seed in SEEDS:
            summary={}
            replay={}
            sha={}
            for order in ("AB","BA"):
                for policy in POLICIES:
                    base=order+"-"+policy+"-"+wf+"-s"+str(seed)
                    sf=list(root.rglob(base+"_summary.csv"))
                    rf=list(root.rglob(base+"_replays.csv"))
                    hf=list(root.rglob(base+"_visited_fingerprints.csv"))
                    assert len(sf)==len(rf)==len(hf)==1,(base,sf,rf,hf)
                    stats=read(sf[0]);rows=read(rf[0]);fingerprints=read(hf[0])
                    assert len(stats)==len(fingerprints)==3 and len(rows)==48
                    summary[order,policy]={r["algorithm"]:r for r in stats}
                    replay[order,policy]={alg:sorted((r for r in rows if r["algorithm"]==alg),
                        key=lambda r:int(r["candidate_index"])) for alg in ALGS}
                    sha[order,policy]={r["algorithm"]:r["history_sha256"] for r in fingerprints}
                    assert set(summary[order,policy])==set(sha[order,policy])==set(ALGS)
            for alg in ALGS:
                assert len({sha[order,policy][alg] for order in ("AB","BA") for policy in POLICIES})==1
                for policy in POLICIES:
                    ra=replay["AB",policy][alg];rb=replay["BA",policy][alg]
                    assert [r["mapping"] for r in ra]==[r["mapping"] for r in rb],(wf,seed,alg,policy)
                    for a,b in zip(ra,rb):
                        for obj in ("sim_makespan","sim_cost"):
                            assert math.isclose(float(a[obj]),float(b[obj]),rel_tol=1e-8,abs_tol=1e-8),(
                                wf,seed,alg,policy,obj,a["mapping"])
                for order in ("AB","BA"):
                    for policy in POLICIES:
                        r=summary[order,policy][alg]
                        assert int(r["evaluations"])==int(r["captured_evaluations"])==3030
                        assert int(r["replayed"])==16
                        search=float(r["search_ms"]);selection=float(r["selection_ms"])
                        simulation=float(r["replay_ms"]);total=float(r["search_selection_replay_ms"])
                        assert all(math.isfinite(t) and t>=0 for t in (search,selection,simulation,total))
                        assert simulation>0 and abs(search+selection+simulation-total)<.004
                        records.append(dict(workflow=wf,seed=seed,algorithm=alg,
                            execution_order=order,policy=policy,
                            search_ms=search,selection_ms=selection,replay_ms=simulation,total_ms=total))
    assert len(records)==3*2*3*2*2==72
    out.mkdir(parents=True,exist_ok=True)
    with (out/"abba_runtime_rows.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    paired=[]
    for wf in WORKFLOWS:
        for seed in SEEDS:
            for alg in ALGS:
                for order in ("AB","BA"):
                    a=next(r for r in records if r["workflow"]==wf and r["seed"]==seed and
                        r["algorithm"]==alg and r["execution_order"]==order and r["policy"]=="pareto-cover")
                    b=next(r for r in records if r["workflow"]==wf and r["seed"]==seed and
                        r["algorithm"]==alg and r["execution_order"]==order and r["policy"]=="online-observed-hv")
                    paired.append(dict(workflow=wf,seed=seed,algorithm=alg,order=order,
                        selection_extra_ms=b["selection_ms"]-a["selection_ms"],
                        total_time_delta_pct=100*(b["total_ms"]/a["total_ms"]-1),
                        sim_time_delta_ms=b["replay_ms"]-a["replay_ms"]))
    with (out/"abba_paired.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    report=["# AB/BA JVM order-control smoke for K16 causal observed-front feedback","",
        "Three previously studied small DAG families, two deterministic optimizer seeds, three solver arms; each seed/policy executed twice from the SAME candidate history SHA under AB (cover before observed) and BA (observed before cover) JVM order.",
        "All four executions for a fixed DAG/seed/solver must replay identical genotypes and independent simulator objective labels within each policy, regardless of process order. Exactly 3030 objective evaluations + K16 true simulator calls per process.",
        "Runs test runtime noise/order sensitivity only; repeated deterministic policy runs are NOT independent workload evidence. The per-policy HV is identical by construction and no superiority claim follows.",
        "",
        "| Solver | Median online selection overhead AB | Median online selection overhead BA | Median total-time change AB | Median total-time change BA |",
        "|---|---:|---:|---:|---:|"]
    for alg in ALGS:
        ab=[r for r in paired if r["algorithm"]==alg and r["order"]=="AB"]
        ba=[r for r in paired if r["algorithm"]==alg and r["order"]=="BA"]
        report.append(f"| {alg} | {statistics.median(r['selection_extra_ms'] for r in ab):+.3f} ms | "+
            f"{statistics.median(r['selection_extra_ms'] for r in ba):+.3f} ms | "+
            f"{statistics.median(r['total_time_delta_pct'] for r in ab):+.3f}% | "+
            f"{statistics.median(r['total_time_delta_pct'] for r in ba):+.3f}% |")
    report+=["","## Interpretation",
        "Any difference in selection/replay/total wall time across AB vs BA for the SAME decisions and simulator objectives is measurement noise, JVM warmup or runner effects, not improvement of algorithm output.",
        "Four sequential JVM processes can still be affected by other runner jobs, CPU thermal state and garbage collection. Three small DAG families are a smoke, not a definitive hardware benchmark.",
        "The published runtime discussion should use ranges/medians and disclose order; do not infer statistical speedup from a single ordered comparison.",
        "The Java \`search_ms\` refers only to optimizer search, not compilation or GitHub queue time. All real actual replay timing comes from Java instrumentation."]
    (out/"abba_runtime_report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: fla_online_runtime_abba.py INPUT_ROOT OUTPUT")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
