#!/usr/bin/env python3
"""Independent true WorkflowSim audit of frozen active T8 K8 original optimizer runs.

Read-only, no selection recomputation or simulator labels used during search.
Fails closed if ANY source archive or source fingerprint is missing.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

SOURCE_RUN="41821482575"
DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(903,904)
MODES=("old-greedy","ready-greedy","staged-greedy","active-uniform-greedy")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
BUDGET={"old-greedy":0,"ready-greedy":32,"staged-greedy":8,"active-uniform-greedy":8}

def read(path):
    with path.open(newline="",encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def write(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def nd(points):
    return sorted(set(p for p in points if not any(
        q[0]<=p[0] and q[1]<=p[1] and (q[0]<p[0] or q[1]<p[1])
        for q in points)))

def hv(points,reference):
    prev=reference[1]
    area=0.0
    for x,y in nd(points):
        if x>=reference[0] or y>=prev:continue
        area+=(reference[0]-x)*(prev-y)
        prev=y
    value=area/(reference[0]*reference[1])
    assert math.isfinite(value) and -1e-10<=value<=1+1e-10
    return value

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    data={}
    shas=set()
    for dag,seed,mode in itertools.product(DAGS,SEEDS,MODES):
        folder=root/f"fla-active-uniform-k8-{dag}-s{seed}-{mode}-{SOURCE_RUN}"
        assert folder.is_dir(),("Missing original source",str(folder))
        metadata=dict(e.split("=",1) for e in
            (folder/"block-id.txt").read_text().split())
        assert metadata==dict(DAG=dag,seed=str(seed),selector=mode,
                              VM="default",K="8",pool="32",T="8"),metadata
        sha=(folder/"source-sha.txt").read_text().strip()
        assert len(sha)==40
        shas.add(sha)
        summary=read(folder/"research_summary.csv")
        trace=read(folder/"research_staged_selection.csv")
        replay=read(folder/"research_replays.csv")
        assert len(summary)==len(trace)==2 and len(replay)==16
        assert {x["algorithm"] for x in summary}==set(SOLVERS)
        assert {x["algorithm"] for x in trace}==set(SOLVERS)
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            t=next(x for x in trace if x["algorithm"]==solver)
            rr=sorted([r for r in replay if r["algorithm"]==solver],
                      key=lambda r:int(r["candidate_index"]))
            assert (s["workflow"],int(s["seed"]))==(dag,seed)
            assert tuple(int(s[z]) for z in ("population","generations",
                "evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,8)
            assert len(rr)==8 and len({r["mapping"] for r in rr})==8
            assert [int(r["candidate_index"]) for r in rr]==list(range(1,9))
            assert (int(t["pool_n"]),int(t["old_calls"]),int(t["ready_calls"]))==(
                32,32,BUDGET[mode])
            assert t["selection_mode"]==mode
            assert len(t["canonical_pool_fingerprint"])==64
            assert len(t["selected_indices"].split("|"))==8
            if mode in ("staged-greedy","active-uniform-greedy"):
                assert len(t["screened_indices"].split("|"))==8
            points=[]
            for r in rr:
                assert (r["workflow"],int(r["seed"]))==(dag,seed)
                p=(float(r["sim_makespan"]),float(r["sim_cost"]))
                assert all(math.isfinite(v) and v>0 for v in p)
                points.append(p)
            for field in ("search_ms","selection_ms","replay_ms"):
                assert math.isfinite(float(s[field])) and float(s[field])>=0
            data[dag,seed,mode,solver]=dict(points=points,
                fingerprint=t["canonical_pool_fingerprint"],
                source_search_ms=float(s["search_ms"]),
                source_selection_ms=float(s["selection_ms"]),
                batch_ms=int(t["batch_total_ns"])/1e6,
                ready_calls=int(t["ready_calls"]))
    assert len(data)==48 and len(shas)==1,("Incomplete jobs or source SHA changed",len(data),shas)
    all_rows=[]
    comparisons=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        for solver in SOLVERS:
            assert len({data[dag,seed,mode,solver]["fingerprint"]
                        for mode in MODES})==1,("Optimizer pool changed",dag,seed,solver)
        points=[p for mode,solver in itertools.product(MODES,SOLVERS)
                for p in data[dag,seed,mode,solver]["points"]]
        refs={f:tuple(f*max(p[j] for p in points)+1e-6 for j in range(2))
              for f in (1.5,3.0)}
        by={}
        for mode,solver in itertools.product(MODES,SOLVERS):
            d=data[dag,seed,mode,solver]
            row=dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                true_hv15=hv(d["points"],refs[1.5]),
                true_hv30=hv(d["points"],refs[3.0]),
                real_nd_size=len(nd(d["points"])),k_replays=8,
                ready_calls=d["ready_calls"],
                batch_ms=d["batch_ms"],
                search_ms=d["source_search_ms"],
                selector_ms=d["source_selection_ms"],
                pool_sha=d["fingerprint"],
                ref15_m=refs[1.5][0],ref15_c=refs[1.5][1],
                source_sha=next(iter(shas)))
            all_rows.append(row)
            by[solver,mode]=row
        for solver in SOLVERS:
            active=by[solver,"active-uniform-greedy"]
            old=by[solver,"old-greedy"]
            staged=by[solver,"staged-greedy"]
            ready=by[solver,"ready-greedy"]
            comparisons.append(dict(workflow=dag,seed=seed,solver=solver,
                active_hv15=active["true_hv15"],staged_hv15=staged["true_hv15"],
                old_hv15=old["true_hv15"],ready_hv15=ready["true_hv15"],
                delta_active_staged_15=active["true_hv15"]-staged["true_hv15"],
                delta_active_old_15=active["true_hv15"]-old["true_hv15"],
                delta_active_ready_15=active["true_hv15"]-ready["true_hv15"],
                delta_active_staged_30=active["true_hv30"]-staged["true_hv30"],
                delta_active_old_30=active["true_hv30"]-old["true_hv30"],
                active_batch_ms=active["batch_ms"],
                staged_batch_ms=staged["batch_ms"],
                full_ready_batch_ms=ready["batch_ms"]))
    assert len(all_rows)==48 and len(comparisons)==12
    write(out/"all_48_actual_k8_HV.csv",all_rows)
    write(out/"all_12_active_vs_controls.csv",comparisons)
    report=["# ACTIVE-uniform T8 original-optimizer actual K8 results","",
       f"Frozen source GitHub Actions run {SOURCE_RUN}. 24 source jobs, 48 solver-arm K8 sets, 384 actual WorkflowSim physical mappings. Source SHA and original N32 pool fingerprint matched across all four selectors.",
       "Primary: actual K8 normalized Pareto HV using shared 1.5x reference per exact DAG/seed; 3x sensitivity also archived. Three known workflow families, two seeds each; no independent-family claim.","",
       "| DAG | Seed | Solver | OLD HV | FULL READY HV | STAGED HV | ACTIVE HV | ACTIVE−STAGED | ACTIVE−OLD |",
       "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for x in comparisons:
        report.append(f"| {x['workflow']} | {x['seed']} | "
          f"{'FLA-v12' if x['solver']==SOLVERS[0] else 'NSGA-II'} | "
          f"{x['old_hv15']:.8f} | {x['ready_hv15']:.8f} | "
          f"{x['staged_hv15']:.8f} | {x['active_hv15']:.8f} | "
          f"{x['delta_active_staged_15']:+.8f} | "
          f"{x['delta_active_old_15']:+.8f} |")
    for solver in SOLVERS:
        cohort=[x for x in comparisons if x["solver"]==solver]
        for field in ("delta_active_staged_15","delta_active_old_15",
                      "delta_active_ready_15"):
            nums=[x[field] for x in cohort]
            report.append(f"- {solver}, {field}: mean {statistics.mean(nums):+.9f}, "
                 f"wins/ties/losses {sum(z>1e-10 for z in nums)}/"
                 f"{sum(abs(z)<=1e-10 for z in nums)}/"
                 f"{sum(z< -1e-10 for z in nums)}.")
    report+=["","No ranking calibration guarantee, no hidden true labels, no original optimizer search changes. Active and staged both cost 8 READY decodes; full READY costs 32 and OLD costs 0. Measured search/selection times are reported but equal total compute is NOT established.","Both favourable and negative cases must remain. Never promote to new FLA innovation until independent-family and wall-time-matched tests."]
    (out/"true_k8_active_findings.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))
if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: audit.py ARTIFACT_ROOT OUTPUT"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
