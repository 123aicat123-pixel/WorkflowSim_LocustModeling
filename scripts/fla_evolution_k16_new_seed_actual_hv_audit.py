#!/usr/bin/env python3
"""Read-only independent all-block true K16 confirmation audit.
Reads ONLY archived source artifacts from frozen run 41816731197.
No optimizer, simulator, calibration, retuning, or source predictions are invoked.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

SOURCE_RUN="41816731197"
DAGS=("CyberShake_50","Sipht_60")
SEEDS=(901,902)
MODES=("old-cached","ready-cached","periodic","risk")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")

def read(path):
    with path.open(newline="",encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def pareto(points):
    return sorted(set(p for p in points if not any(
        q[0]<=p[0] and q[1]<=p[1] and (q[0]<p[0] or q[1]<p[1])
        for q in points)))

def hv(points,ref):
    prev=ref[1]
    value=0.0
    for x,y in pareto(points):
        if x<ref[0] and y<prev:
            value+=(ref[0]-x)*(prev-y)
            prev=y
    out=value/(ref[0]*ref[1])
    assert math.isfinite(out) and -1e-10<=out<=1+1e-10
    return out

def write(path,records):
    assert records
    with path.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    source={}
    shas=set()
    for dag,seed,mode in itertools.product(DAGS,SEEDS,MODES):
        name=f"fla-evolution-k16-{dag}-s{seed}-{mode}-{SOURCE_RUN}"
        folder=root/name
        assert folder.is_dir(),("Missing original source artifact",name)
        metadata=dict(item.split("=",1) for item in (folder/"block-id.txt").read_text().split())
        assert metadata==dict(DAG=dag,seed=str(seed),mode=mode,K="16",visits="3030",VM="default"),metadata
        sha=(folder/"source-sha.txt").read_text().strip()
        assert len(sha)==40
        shas.add(sha)
        summaries=read(folder/"research_summary.csv")
        replays=read(folder/"research_replays.csv")
        traces=read(folder/"research_evolution_fidelity.csv")
        assert len(summaries)==len(traces)==2 and len(replays)==32
        assert {s["algorithm"] for s in summaries}==set(SOLVERS)
        assert {t["algorithm"] for t in traces}==set(SOLVERS)
        for solver in SOLVERS:
            summ=next(s for s in summaries if s["algorithm"]==solver)
            t=next(q for q in traces if q["algorithm"]==solver)
            rr=sorted((q for q in replays if q["algorithm"]==solver),
                      key=lambda q:int(q["candidate_index"]))
            assert len(rr)==16 and len({r["mapping"] for r in rr})==16
            assert [int(r["candidate_index"]) for r in rr]==list(range(1,17))
            assert (summ["workflow"],summ["seed"])==(dag,str(seed))
            assert tuple(int(summ[k]) for k in ("population","generations","evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
            visits,cheap,ready,hits,distinct,quota=(int(t[k]) for k in
                ("visits","cheap_calls","ready_calls","cache_hits","distinct","ready_budget"))
            assert visits==3030 and hits+distinct==visits and t["mode"]==mode
            assert 0<=ready<=distinct and ready<=quota
            assert (mode!="old-cached" or (cheap==distinct and ready==0 and quota==0))
            assert (mode!="ready-cached" or (cheap==0 and ready==distinct and quota==3030))
            assert (mode not in ("periodic","risk") or (cheap==distinct and quota==378))
            points=[]
            for row in rr:
                assert (row["workflow"],row["seed"])==(dag,str(seed))
                p=tuple(float(row[z]) for z in ("sim_makespan","sim_cost"))
                assert all(math.isfinite(v) and v>0 for v in p)
                points.append(p)
            source[(dag,seed,mode,solver)]=dict(points=points,
                ready=ready,cheap=cheap,visits=visits,
                search_ms=float(summ["search_ms"]))
    assert len(shas)==1,("Source Java code differs across jobs",shas)
    results=[]
    diffs=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        all_points=[p for mode,solver in itertools.product(MODES,SOLVERS)
                    for p in source[(dag,seed,mode,solver)]["points"]]
        ref15=tuple(1.5*max(p[j] for p in all_points)+1e-6 for j in range(2))
        ref30=tuple(3.0*max(p[j] for p in all_points)+1e-6 for j in range(2))
        by={}
        for solver,mode in itertools.product(SOLVERS,MODES):
            v=source[(dag,seed,mode,solver)]
            h15=hv(v["points"],ref15)
            h30=hv(v["points"],ref30)
            row=dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                true_hv15=h15,true_hv30=h30,actual_replays=16,
                old_decoder_calls=v["cheap"],ready_decoder_calls=v["ready"],
                original_visits=v["visits"],search_ms=v["search_ms"],
                ref15_m=ref15[0],ref15_c=ref15[1],source_sha=next(iter(shas)))
            results.append(row)
            by[(solver,mode)]=row
        for solver in SOLVERS:
            for mode in ("periodic","risk"):
                a=by[(solver,mode)]
                old=by[(solver,"old-cached")]
                ready=by[(solver,"ready-cached")]
                diffs.append(dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                    delta_vs_old_15=a["true_hv15"]-old["true_hv15"],
                    delta_vs_ready_15=a["true_hv15"]-ready["true_hv15"],
                    delta_vs_old_30=a["true_hv30"]-old["true_hv30"],
                    ready_calls=a["ready_decoder_calls"],
                    full_ready_calls=ready["ready_decoder_calls"]))
    assert len(results)==32 and len(diffs)==16
    write(out/"all_32_actual_k16_hv.csv",results)
    write(out/"all_16_paired_k16_differences.csv",diffs)
    notes=["# K16 new-seed full real WorkflowSim confirmation","",
       "Development-family replication ONLY; no unseen-family generalization and no new algorithm.",
       f"Frozen source Actions run: {SOURCE_RUN}, 16 source jobs; 512 actual assignments, 3030 visits per solver and common source SHA verified.",
       "Common actual-HV reference within each exact (workflow,seed) block; primary 1.5x, sensitivity 3.0x. Negative results are preserved.",""]
    for solver in SOLVERS:
        for mode in ("periodic","risk"):
            d=[x for x in diffs if x["solver"]==solver and x["mode"]==mode]
            values=[x["delta_vs_old_15"] for x in d]
            notes.append(f"- {solver}, {mode} vs OLD-cached: mean={statistics.mean(values):+.9f}; "
                f"wins/ties/losses={sum(x>1e-10 for x in values)}/"
                f"{sum(abs(x)<=1e-10 for x in values)}/{sum(x<-1e-10 for x in values)}. "
                "Four paired DAG/seed blocks are not independent-family evidence.")
    notes+=["","No claim of CPU time parity, robust improvement, safe uncertainty calibration, or SCI readiness."]
    (out/"source_results_and_limitations.md").write_text("\n".join(notes)+"\n",encoding="utf-8")
    print("PASS immutable 16 source jobs, 32 solver-arm fronts, 512 real WorkflowSim K16 outcomes, shared-source SHA and actual Pareto HV")
if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: K16_audit.py SOURCE_ARTIFACT_ROOT REPORT_DIR"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
