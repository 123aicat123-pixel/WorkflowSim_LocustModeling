#!/usr/bin/env python3
"""Independent complete 256-real-WorkflowSim replay matched-cache audit.

Read-only original fixed mode archive, no optimizer calls, no simulator calls,
no data-driven re-tuning of the frozen initial treatment.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_50","Sipht_60")
SEEDS=(801,802)
MODES=("old-cached","ready-cached","periodic","risk")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
ORIGINAL_RUN="41784901304"
EPS=1e-10

def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def write(path,rows):
    if not rows:raise AssertionError(("No rows",path))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def pareto(points):
    return sorted(set(x for x in points if not any(
        y[0]<=x[0] and y[1]<=x[1] and (y[0]<x[0] or y[1]<x[1])
        for y in points)))

def hv(points,ref):
    rx,ry=ref
    prev=ry;area=0.
    for x,y in pareto(points):
        if x<rx and y<prev:
            area+=(rx-x)*(prev-y)
            prev=y
    val=area/(rx*ry)
    if not (math.isfinite(val) and 0<=val<=1+1e-8):
        raise AssertionError(("Bad real normalized HV",val))
    return val

def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    raw={}
    sha_set={}
    for dag,seed,mode in itertools.product(DAGS,SEEDS,MODES):
        name=f"fla-cache-matched-{dag}-s{seed}-{mode}-{ORIGINAL_RUN}"
        folders=[p for p in root.iterdir() if p.is_dir() and p.name==name]
        if len(folders)!=1:
            raise AssertionError(("Missing or duplicated source",name,folders))
        folder=folders[0]
        meta=dict(x.split("=",1) for x in (folder/"block-id.txt").read_text().split())
        if (meta.get("DAG"),meta.get("seed"),meta.get("mode"),
            meta.get("K"),meta.get("visits"),meta.get("VM"))!=(
            dag,str(seed),mode,"8","3030","default"):
            raise AssertionError(("Source block mislabelled",meta))
        sha=(folder/"source-sha.txt").read_text().strip()
        if len(sha)!=40:raise AssertionError("Invalid immutable Java source SHA")
        sha_set.setdefault(dag,set()).add(sha)
        summary=read(folder/"research_summary.csv")
        replay=read(folder/"research_replays.csv")
        traces=read(folder/"research_evolution_fidelity.csv")
        if len(summary)!=2 or len(traces)!=2 or len(replay)!=16:
            raise AssertionError(("Incomplete original source",name))
        if {x["algorithm"] for x in summary}!={*SOLVERS} or {x["algorithm"] for x in traces}!={*SOLVERS}:
            raise AssertionError(("Source solver names changed",name))
        raw[(dag,seed,mode)]={}
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            t=next(x for x in traces if x["algorithm"]==solver)
            rr=sorted((x for x in replay if x["algorithm"]==solver),
                      key=lambda x:int(x["candidate_index"]))
            if (int(s["evaluations"]),int(s["captured_evaluations"]),
                int(s["population"]),int(s["generations"]),int(s["replayed"]))!=(
                3030,3030,30,100,8):
                raise AssertionError(("Unmatched original genotype visits",name,solver))
            if s["workflow"]!=dag or s["seed"]!=str(seed):
                raise AssertionError(("Original source identity",name,solver))
            if len(rr)!=8 or [int(x["candidate_index"]) for x in rr]!=list(range(1,9)) or len({x["mapping"] for x in rr})!=8:
                raise AssertionError(("Wrong K8 true simulator replay",name,solver))
            points=[]
            for x in rr:
                if x["workflow"]!=dag or x["seed"]!=str(seed):
                    raise AssertionError(("Wrong true replay source",name,solver))
                p=(float(x["sim_makespan"]),float(x["sim_cost"]))
                if not all(math.isfinite(z) and z>0 for z in p):
                    raise AssertionError(("Nonfinite true simulator objectives",name,solver))
                points.append(p)
            visits=int(t["visits"]);distinct=int(t["distinct"])
            hits=int(t["cache_hits"]);old=int(t["cheap_calls"]);ready=int(t["ready_calls"])
            quota=int(t["ready_budget"])
            expected_quota=0 if mode=="old-cached" else 3030 if mode=="ready-cached" else 378
            if t["mode"]!=mode or visits!=3030 or distinct+hits!=visits or quota!=expected_quota:
                raise AssertionError(("Cache visit identity mismatch",name,solver,t))
            if mode=="old-cached" and (old!=distinct or ready!=0):
                raise AssertionError(("OLD cached objective count failure",name,solver))
            if mode=="ready-cached" and (old!=0 or ready!=distinct):
                raise AssertionError(("READY cached objective count failure",name,solver))
            if mode in ("periodic","risk") and (old!=distinct or ready>378):
                raise AssertionError(("Mixed cached objective count failure",name,solver))
            if ready>quota or distinct<1 or hits<0:
                raise AssertionError(("Impossible decoder accounting",name,solver))
            time=float(s["search_ms"])
            if not math.isfinite(time) or time<0:raise AssertionError("Invalid original search wall time")
            old_ns=int(t["cheap_ns"]);ready_ns=int(t["ready_ns"])
            if old_ns<0 or ready_ns<0:raise AssertionError("Negative measured decoder time")
            raw[(dag,seed,mode)][solver]=dict(
                points=points,visits=visits,distinct=distinct,hits=hits,
                old=old,ready=ready,quota=quota,search_ms=time,
                cheap_ns=old_ns,ready_ns=ready_ns,sha=sha)
    if len(raw)!=16:raise AssertionError("Source 16 jobs not complete")
    if any(len(v)!=1 for v in sha_set.values()):
        raise AssertionError(("Not identical original code across source arms",sha_set))
    all_rows=[];comparisons=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        actual=[p for mode in MODES for solver in SOLVERS
                for p in raw[(dag,seed,mode)][solver]["points"]]
        refs={f:(f*max(p[0] for p in actual)+1e-6,
                 f*max(p[1] for p in actual)+1e-6) for f in (1.5,3.0)}
        by={}
        for solver,mode in itertools.product(SOLVERS,MODES):
            d=raw[(dag,seed,mode)][solver]
            row=dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                source_sha=d["sha"],fitness_visits=d["visits"],unique_mappings=d["distinct"],
                cache_hits=d["hits"],old_decoder_calls=d["old"],
                ready_decoder_calls=d["ready"],quota=d["quota"],
                actual_replays=len(d["points"]),
                actual_nd_count=len(pareto(d["points"])),
                min_actual_makespan=min(p[0] for p in d["points"]),
                min_actual_cost=min(p[1] for p in d["points"]),
                measured_search_ms=d["search_ms"],
                measured_old_decoder_ns=d["cheap_ns"],measured_ready_decoder_ns=d["ready_ns"],
                real_normalized_hv15=hv(d["points"],refs[1.5]),
                real_normalized_hv30=hv(d["points"],refs[3.0]),
                shared_ref_m15=refs[1.5][0],shared_ref_c15=refs[1.5][1])
            all_rows.append(row);by[(solver,mode)]=row
        for solver in SOLVERS:
            cheap=by[(solver,"old-cached")];full=by[(solver,"ready-cached")]
            for mode in ("periodic","risk"):
                s=by[(solver,mode)]
                comparisons.append(dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                    old_hv15=cheap["real_normalized_hv15"],full_ready_hv15=full["real_normalized_hv15"],
                    adaptive_hv15=s["real_normalized_hv15"],
                    delta_vs_old=s["real_normalized_hv15"]-cheap["real_normalized_hv15"],
                    delta_vs_full_ready=s["real_normalized_hv15"]-full["real_normalized_hv15"],
                    delta_vs_old_ref30=s["real_normalized_hv30"]-cheap["real_normalized_hv30"],
                    cache_hit_rate=s["cache_hits"]/s["fitness_visits"],
                    ready_fraction_of_full=s["ready_decoder_calls"]/max(1,full["ready_decoder_calls"]),
                    old_search_ms=cheap["measured_search_ms"],
                    full_ready_search_ms=full["measured_search_ms"],
                    adaptive_search_ms=s["measured_search_ms"]))
    if len(all_rows)!=32 or len(comparisons)!=16:
        raise AssertionError(("Expected 32 source solver/modes and 16 paired comparisons",len(all_rows),len(comparisons)))
    write(out/"all_32_true_HV_solver_mode_cache_equal.csv",all_rows)
    write(out/"all_16_true_HV_adaptive_paired_vs_cached_controls.csv",comparisons)
    report=[
       "# Four-way same-cache FLA and seeded NSGA-II during-evolution actual WorkflowSim HV",
       "",
       f"Original frozen workflow run {ORIGINAL_RUN}: 16 successful original source jobs, four fixed prior modes, two DAX ×two seeds ×two solvers ×four cached modes ×K8 = 256 actual WorkflowSim simulations. All source code SHA matches across modes for each DAG; original 3030 genotype visits verified. Different measured compute costs are reported, NOT assumed equal.",
       "Every mode uses exactly the same first-write physical mapping cache. Model calls on cache misses differ deliberately by fidelity allocation. Real K8 normalized HV references are shared between all eight solver/mode arms **within each DAG and seed**, including a 3× sensitivity analysis.",
       "",
       "| DAG | Seed | Solver | OLD cached HV | FULL READY cached HV | PERIODIC HV | RISK HV | PERIODIC READY calls | RISK READY calls |",
       "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    ]
    for dag,seed in itertools.product(DAGS,SEEDS):
        for solver in SOLVERS:
            g={r["mode"]:r for r in all_rows if (r["workflow"],r["seed"],r["solver"])==(dag,seed,solver)}
            report.append(f"| {dag} | {seed} | {'FLA' if solver==SOLVERS[0] else 'NSGA-II'} | "
              f"{g['old-cached']['real_normalized_hv15']:.8f} | "
              f"{g['ready-cached']['real_normalized_hv15']:.8f} | "
              f"{g['periodic']['real_normalized_hv15']:.8f} | "
              f"{g['risk']['real_normalized_hv15']:.8f} | "
              f"{g['periodic']['ready_decoder_calls']} | {g['risk']['ready_decoder_calls']} |")
    report+=["","## Paired true HV effects with same caching"]
    for solver in SOLVERS:
        for mode in ("periodic","risk"):
            z=[x for x in comparisons if x["solver"]==solver and x["mode"]==mode]
            diff=[x["delta_vs_old"] for x in z]
            full=[x["delta_vs_full_ready"] for x in z]
            report.append(f"- {solver} {mode}: relative to CACHED OLD mean Δ={statistics.mean(diff):+.8f}, "
              f"wins/ties/losses={sum(v>EPS for v in diff)}/{sum(abs(v)<=EPS for v in diff)}/{sum(v< -EPS for v in diff)}; "
              f"relative to CACHED FULL READY mean Δ={statistics.mean(full):+.8f}; "
              f"mean READY call / FULL READY ratio={statistics.mean(x['ready_fraction_of_full'] for x in z):.3f}×; "
              f"mean measured search time={statistics.mean(x['adaptive_search_ms'] for x in z):.1f} ms.")
    report+=["","## Research decision, not a significance claim",
      "Cache matching eliminates one known *mechanism* confound from the previous pilot. Distinct genotype counts and actual READY call counts can still differ across trajectories; a shared visit budget is not a matched computational time budget.",
      "The four modes can explore different genotypes and have differing Pareto fronts; comparisons report all losses and ties. Mixed-fidelity objective scales across different genotypes remain uncalibrated. This developer trial is not sufficient for SCI Q1 generalization.",
      "All four treatments predeclared before outcomes; no risk 1% threshold or budget edits after seeing original truth. Source actual WorkflowSim Makespan and Cost were not used to select candidates.",
      "No FLA-specific algorithm superiority, no unseen DAG-family holdout, no statistical significance, no end-to-end compute-time match, no default promotion; master remains unchanged."
    ]
    (out/"cache_equal_real_hv_full_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py FROZEN_ORIGINAL_16_JOB_ARCHIVES OUTPUT_DIR")
    main(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
