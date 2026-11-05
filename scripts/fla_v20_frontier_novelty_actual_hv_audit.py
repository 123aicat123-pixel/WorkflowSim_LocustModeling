#!/usr/bin/env python3
"""Immutable read-only v20 four-arm true WorkflowSim K16 source analysis.
The actual simulator is NOT invoked. No post-outcome tuning.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(951,952)
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]",
         "DAG-Pareto-FLA[v20-frontier-random]",
         "DAG-Pareto-FLA[v20-frontier-dag]",
         "NSGA-II[costseed]")
RUN="41969565802"

def load(p):
    with p.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def pareto(points):
    return sorted(set(p for p in points if not any(
        q[0]<=p[0] and q[1]<=p[1] and (q[0]<p[0] or q[1]<p[1])
        for q in points)))

def hv(points,ref):
    last=ref[1]
    area=0.
    for m,c in pareto(points):
        if m<ref[0] and c<last:
            area+=(ref[0]-m)*(last-c)
            last=c
    value=area/(ref[0]*ref[1])
    assert math.isfinite(value) and 0<=value<=1+1e-10,value
    return value

def write(path,rows):
    assert rows
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    original={}
    shas=set()
    for dag,seed in itertools.product(DAGS,SEEDS):
        folder=root/f"fla-v20-frontier-{dag}-s{seed}-{RUN}"
        assert folder.is_dir(),("Missing original job",str(folder))
        meta=dict(x.split("=",1) for x in (folder/"block-id.txt").read_text().split())
        assert meta==dict(DAG=dag,seed=str(seed),K="16",visits="3030",VM="default")
        sha=(folder/"source-sha.txt").read_text().strip()
        assert len(sha)==40
        shas.add(sha)
        summary=load(folder/"research_summary.csv")
        replay=load(folder/"research_replays.csv")
        fingerprint=load(folder/"research_visited_fingerprints.csv")
        assert len(summary)==len(fingerprint)==4 and len(replay)==64
        assert {s["algorithm"] for s in summary}==set(SOLVERS)
        assert {s["algorithm"] for s in fingerprint}==set(SOLVERS)
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            fg=next(x for x in fingerprint if x["algorithm"]==solver)
            rr=sorted((x for x in replay if x["algorithm"]==solver),
                      key=lambda x:int(x["candidate_index"]))
            assert len(rr)==16 and len({x["mapping"] for x in rr})==16
            assert [int(x["candidate_index"]) for x in rr]==list(range(1,17))
            assert (s["workflow"],int(s["seed"]))==(dag,seed)
            assert tuple(int(s[z]) for z in ("population","generations",
                "evaluations","captured_evaluations","replayed"))==(30,100,3030,3030,16)
            assert len(fg["history_sha256"])==64
            assert int(fg["distinct_visited"])==int(s["distinct_observed"])
            points=[]
            for x in rr:
                assert (x["workflow"],int(x["seed"]))==(dag,seed)
                pair=tuple(float(x[k]) for k in ("sim_makespan","sim_cost"))
                assert all(math.isfinite(v) and v>0 for v in pair)
                points.append(pair)
            time=float(s["search_ms"])
            assert math.isfinite(time) and time>=0
            original[dag,seed,solver]=dict(points=points,search_ms=time,
                distinct=int(s["distinct_observed"]),sha=sha,
                history=fg["history_sha256"])
    assert len(original)==24 and len(shas)==1,("Incomplete source or source-code SHA changed",shas)
    rows=[]
    pairs=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        points=[p for solver in SOLVERS for p in original[dag,seed,solver]["points"]]
        refs={f:tuple(f*max(p[k] for p in points)+1e-6 for k in range(2))
              for f in (1.5,3.0)}
        by={}
        for solver in SOLVERS:
            a=original[dag,seed,solver]
            row=dict(workflow=dag,seed=seed,solver=solver,
                true_hv15=hv(a["points"],refs[1.5]),
                true_hv30=hv(a["points"],refs[3.0]),
                nd_size=len(pareto(a["points"])),real_replays=16,
                visited_unique=a["distinct"],search_ms=a["search_ms"],
                history_sha256=a["history"],ref_m=refs[1.5][0],
                ref_c=refs[1.5][1],source_sha=a["sha"])
            rows.append(row)
            by[solver]=row
        base=by[SOLVERS[0]]
        random=by[SOLVERS[1]]
        dagop=by[SOLVERS[2]]
        nsga=by[SOLVERS[3]]
        pairs.append(dict(workflow=dag,seed=seed,
            base_hv15=base["true_hv15"],random_hv15=random["true_hv15"],
            dag_hv15=dagop["true_hv15"],nsga_hv15=nsga["true_hv15"],
            dag_minus_base=dagop["true_hv15"]-base["true_hv15"],
            dag_minus_random=dagop["true_hv15"]-random["true_hv15"],
            random_minus_base=random["true_hv15"]-base["true_hv15"],
            dag_minus_nsga=dagop["true_hv15"]-nsga["true_hv15"],
            dag_minus_base_3x=dagop["true_hv30"]-base["true_hv30"],
            dag_minus_random_3x=dagop["true_hv30"]-random["true_hv30"],
            baseline_distinct=base["visited_unique"],
            random_distinct=random["visited_unique"],
            dag_distinct=dagop["visited_unique"],
            baseline_search_ms=base["search_ms"],
            random_search_ms=random["search_ms"],
            dag_search_ms=dagop["search_ms"]))
    assert len(rows)==24 and len(pairs)==6
    write(out/"all_24_actual_v20_hv.csv",rows)
    write(out/"all_6_v20_paired_vs_controls.csv",pairs)
    summary=["# v20 novel population-Hamming candidate generation: TRUE K16 WorkflowSim",
             "",
             "Frozen 6 source jobs, four original optimizer arms, 384 physical K16 replays; no unseen workflow-family claim.",
             "Same source SHA, 3030 counted target-evaluations each, one shared actual HV reference per DAG/seed and 3x sensitivity.",
             "The proposed operator uses 4 UNCOUNTED (no decoder) non-fitness proposals per triggered offspring, and exactly 1 normal evaluation.",
             "",
             "| DAG | seed | v12 HV | random novelty HV | DAG novelty HV | NSGA-II HV | DAG-v12 | DAG-random |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for a in pairs:
        summary.append(f"| {a['workflow']} | {a['seed']} | "
            f"{a['base_hv15']:.8f} | {a['random_hv15']:.8f} | "
            f"{a['dag_hv15']:.8f} | {a['nsga_hv15']:.8f} | "
            f"{a['dag_minus_base']:+.8f} | {a['dag_minus_random']:+.8f} |")
    for field in ("dag_minus_base","dag_minus_random","random_minus_base","dag_minus_nsga"):
        v=[p[field] for p in pairs]
        summary.append(f"- {field}: mean={statistics.mean(v):+.9f}, "
            f"wins/ties/losses={sum(x>1e-10 for x in v)}/"
            f"{sum(abs(x)<=1e-10 for x in v)}/{sum(x< -1e-10 for x in v)}.")
    summary+=["","The sampled K16 fronts do not bound true feasible Pareto performance. Two seeds per three familiar families are dependent; no SCI or statistical superiority claim. Counted genotype evaluations do not imply matched CPU time. All negative results retained."]
    (out/"v20_independent_findings.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    print("\n".join(summary))

if __name__=="__main__":
    assert len(sys.argv)==3,"Usage: audit.py ORIGINAL_RUN_ARTIFACT_DIR REPORT_DIR"
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
