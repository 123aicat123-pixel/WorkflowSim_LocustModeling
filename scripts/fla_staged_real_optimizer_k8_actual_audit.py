#!/usr/bin/env python3
"""Independent actual WorkflowSim analysis of 18 frozen original FLA/NSGA K8 jobs.

No retrospective simulator calls, no optimizer tuning, no recomputing selections.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_50","Sipht_60","Epigenomics_100")
SEEDS=(801,802)
MODES=("old-greedy","ready-greedy","staged-greedy")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
REPLAY_K=8
POOL=32
EXPECTED_SOURCE_RUN="41777916573"
TOL=1e-10

def read(path):
    with path.open(newline="",encoding="utf-8") as h:return list(csv.DictReader(h))
def write(path,data):
    if not data:raise AssertionError("No comparison data")
    with path.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(data[0]))
        w.writeheader();w.writerows(data)

def nd(points):
    return [p for p in points if not any(
         q[0]<=p[0] and q[1]<=p[1] and (q[0]<p[0] or q[1]<p[1]) for q in points)]

def hv(points,ref):
    rx,ry=ref
    p=sorted(set(nd(points)))
    prev=ry;area=0.
    for x,y in p:
        if x>=rx or y>=ry or y>=prev:continue
        area+=(rx-x)*(prev-y)
        prev=y
    z=area/(rx*ry)
    if not math.isfinite(z) or z<0 or z>1+1e-8:raise AssertionError(("Invalid actual HV",z))
    return z

def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    original={}
    expected=set(itertools.product(DAGS,SEEDS,MODES))
    for dag,seed,mode in sorted(expected):
        prefix=f"fla-staged-real-k8-{dag}-s{seed}-{mode}-{EXPECTED_SOURCE_RUN}"
        dirs=[p for p in root.iterdir() if p.is_dir() and p.name==prefix]
        if len(dirs)!=1:raise AssertionError(("Missing original job artifact",prefix))
        source=dirs[0]
        ident=dict(x.split("=",1) for x in (source/"block-id.txt").read_text().split())
        if (ident.get("DAG"),ident.get("seed"),ident.get("selector"),
            ident.get("VM"),ident.get("K"),ident.get("pool"),ident.get("T"))!=(
            dag,str(seed),mode,"default","8","32","8"):
            raise AssertionError(("Source job identity mismatch",ident))
        summary=read(source/"research_summary.csv")
        trace=read(source/"research_staged_selection.csv")
        replay=read(source/"research_replays.csv")
        if len(summary)!=2 or len(trace)!=2 or len(replay)!=16:
            raise AssertionError(("Incomplete actual simulation",dag,seed,mode))
        if {x["algorithm"] for x in trace}!={*SOLVERS} or {x["algorithm"] for x in summary}!={*SOLVERS}:
            raise AssertionError("Solver mismatch")
        original[(dag,seed,mode)]={}
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            t=next(x for x in trace if x["algorithm"]==solver)
            rows=sorted((x for x in replay if x["algorithm"]==solver),key=lambda x:int(x["candidate_index"]))
            expected_high={"old-greedy":0,"ready-greedy":32,"staged-greedy":8}[mode]
            if len(rows)!=8 or len({x["mapping"] for x in rows})!=8 or [int(x["candidate_index"]) for x in rows]!=list(range(1,9)):
                raise AssertionError(("Bad K8 real replay coverage",dag,seed,mode,solver))
            if (int(s["evaluations"]),int(s["captured_evaluations"]),int(s["replayed"]),
                int(s["population"]),int(s["generations"]))!=(3030,3030,8,30,100):
                raise AssertionError(("Unfair original optimizer evaluations",dag,seed,mode,solver))
            if (int(t["old_calls"]),int(t["ready_calls"]),int(t["pool_n"]))!=(32,expected_high,32):
                raise AssertionError(("Changed staged model budget",dag,seed,mode,solver,t))
            if len(t["canonical_pool_fingerprint"])!=64:raise AssertionError("Missing source pool SHA fingerprint")
            if len(t["selected_indices"].split("|"))!=8:raise AssertionError("Wrong K8 planned selection")
            if mode=="staged-greedy" and len(t["screened_indices"].split("|"))!=8:
                raise AssertionError("Missing T8 planned shortlist")
            points=[]
            assignments=[]
            for row in rows:
                if row["workflow"]!=dag or int(row["seed"])!=seed:raise AssertionError("Wrong replay labels")
                p=(float(row["sim_makespan"]),float(row["sim_cost"]))
                if not all(math.isfinite(z) and z>0 for z in p):
                    raise AssertionError("Invalid real objectives")
                points.append(p)
                assignments.append(row["mapping"])
            times={key:float(s[key]) for key in ("search_ms","selection_ms","replay_ms")}
            if any(not math.isfinite(x) or x<0 for x in times.values()):
                raise AssertionError("Bad original measured computation cost")
            original[(dag,seed,mode)][solver]=dict(points=points,mapping=assignments,
                fingerprint=t["canonical_pool_fingerprint"],
                evals=int(s["evaluations"]),raw_search_ms=times["search_ms"],
                selector_ms=times["selection_ms"],
                simulator_replay_ms=times["replay_ms"],
                decoder_batch_ms=int(t["batch_total_ns"])/1e6,
                old_model_ms=int(t["old_ns"])/1e6,
                ready_model_ms=int(t["ready_ns"])/1e6,
                ready_calls=int(t["ready_calls"]),old_calls=int(t["old_calls"]),
                selected_indices=t["selected_indices"])
    # One original search trajectory and ONE ordered 32-map pool per solver / workflow / seed.
    grouped=[]
    comparisons=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        for solver in SOLVERS:
            fprints={original[(dag,seed,mode)][solver]["fingerprint"] for mode in MODES}
            if len(fprints)!=1:
                raise AssertionError(("Search genotype pool changed across selectors",dag,seed,solver,fprints))
        all_actual=[p for mode in MODES for solver in SOLVERS
                    for p in original[(dag,seed,mode)][solver]["points"]]
        refs={x:(x*max(z[0] for z in all_actual)+1e-6,
                 x*max(z[1] for z in all_actual)+1e-6) for x in (1.5,3.0)}
        local={}
        for mode in MODES:
            for solver in SOLVERS:
                c=original[(dag,seed,mode)][solver]
                row=dict(workflow=dag,seed=seed,solver=solver,mode=mode,
                         source_pool_sha=c["fingerprint"],
                         source_optimizer_evaluations=c["evals"],k_actual_replays=len(c["points"]),
                         old_postsearch_decodes=c["old_calls"],
                         ready_postsearch_decodes=c["ready_calls"],
                         source_search_ms=c["raw_search_ms"],source_selection_ms=c["selector_ms"],
                         model_batch_ms=c["decoder_batch_ms"],
                         model_old_ms=c["old_model_ms"],model_ready_ms=c["ready_model_ms"],
                         simulator_replay_ms=c["simulator_replay_ms"],
                         min_actual_makespan=min(z[0] for z in c["points"]),
                         min_actual_cost=min(z[1] for z in c["points"]),
                         real_nd_count=len(set(nd(c["points"]))),
                         true_hv15=hv(c["points"],refs[1.5]),
                         true_hv30=hv(c["points"],refs[3.0]),
                         ref_m15=refs[1.5][0],ref_c15=refs[1.5][1])
                grouped.append(row)
                local[(solver,mode)]=row
        for solver in SOLVERS:
            old=local[(solver,"old-greedy")]
            full=local[(solver,"ready-greedy")]
            staged=local[(solver,"staged-greedy")]
            comparisons.append(dict(workflow=dag,seed=seed,solver=solver,
               old_true_hv15=old["true_hv15"],ready_true_hv15=full["true_hv15"],
               staged_true_hv15=staged["true_hv15"],
               staged_minus_ready_hv15=staged["true_hv15"]-full["true_hv15"],
               staged_minus_old_hv15=staged["true_hv15"]-old["true_hv15"],
               staged_minus_ready_hv30=staged["true_hv30"]-full["true_hv30"],
               selected_same_as_full_ready=int(
                   original[(dag,seed,"staged-greedy")][solver]["mapping"]==
                   original[(dag,seed,"ready-greedy")][solver]["mapping"]),
               staged_model_batch_ms=staged["model_batch_ms"],
               ready_model_batch_ms=full["model_batch_ms"],
               selector_work_ratio=staged["model_batch_ms"]/max(1e-6,full["model_batch_ms"]),
               staged_total_search_selector_ms=staged["source_search_ms"]+staged["source_selection_ms"],
               ready_total_search_selector_ms=full["source_search_ms"]+full["source_selection_ms"]))
    if len(grouped)!=36 or len(comparisons)!=12:raise AssertionError("Incomplete paired 18 original optimizer jobs")
    write(out/"all_36_paired_solver_mode_actual_hv.csv",grouped)
    write(out/"all_12_staged_vs_controls_true_hv.csv",comparisons)
    report=[
        "# Original FLA-v12 / seeded NSGA-II shared 32-candidate real simulator staged K8 experiment",
        "",
        "Original 18 jobs, 3 DAX ×2 seeds ×3 replay selectors and 2 matched solvers = 288 actual WorkflowSim simulator assignments. All 3030 original optimizer genotype objectives per solver matched. Source 32 actual evaluated Task→VM genotypes hashed and verified identical ACROSS selector modes within each solver/DAG/seed; no true labels enter selection.",
        "Selectors use identical OLD-only 1.5x predicted reference and prospective, optimizer-independent greedy HV. 32 OLD model decodes common; READY 32 for full READY, 8 for staged, 0 for cheap OLD. Real simulator K8 objective reference is fixed across all SIX solver × mode choices per workflow/seed. Independent audit reused ONLY archived source outputs, not a new run.",
        "",
        "| DAG | Seed | Solver | OLD actual K8 HV | FULL READY actual K8 HV | STAGED actual K8 HV | STAGED−READY | STAGED−OLD | Batch time staged / ready |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for x in comparisons:
        report.append(f"| {x['workflow']} | {x['seed']} | "
          f"{'FLA-v12' if x['solver']==SOLVERS[0] else 'NSGA-II'} | "
          f"{x['old_true_hv15']:.8f} | {x['ready_true_hv15']:.8f} | "
          f"{x['staged_true_hv15']:.8f} | "
          f"{x['staged_minus_ready_hv15']:+.8f} | "
          f"{x['staged_minus_old_hv15']:+.8f} | "
          f"{x['selector_work_ratio']:.3f}× |")
    report+=["","## Paired effect and runtime, no pooled independence"]
    for solver in SOLVERS:
        z=[x for x in comparisons if x["solver"]==solver]
        diff=[x["staged_minus_ready_hv15"] for x in z]
        versus=[x["staged_minus_old_hv15"] for x in z]
        ratio=[x["selector_work_ratio"] for x in z]
        report.append(f"- {solver}: staged minus FULL READY normalized actual HV average "
          f"{statistics.mean(diff):+.8f}, wins/ties/losses="
          f"{sum(x>TOL for x in diff)}/{sum(abs(x)<=TOL for x in diff)}/{sum(x< -TOL for x in diff)}; "
          f"staged minus OLD mean {statistics.mean(versus):+.8f}; "
          f"mean timed batch selection ratio {statistics.mean(ratio):.3f}×.")
    report+=["","## Scientific scope and potential failure",
        "The candidate pool is a PLANNED-ONLY Pareto-cover preselection of 32 from the visited 3030 genotype evaluations. This can bias all 3 selectors toward already-planned-good solutions and is NOT an all-visited full Pareto front.",
        "The three selector runs repeat search separately using identical seeds and checked source fingerprints. The 6 DAG/seed blocks are correlated within THREE known workflow families; nominal wins are not independent-significance evidence.",
        "The source search times vary with runner load and JIT across jobs. Batch timing and total complete search+selection/replay are reported separately; never claim actual search speedup simply because 24 READY calls were avoided.",
        "This stage re-selects K8 simulator replay candidates AFTER FLA or NSGA-II completed the original 3030-evaluation search. It is NOT yet a multi-fidelity evolutionary fitness replacement, nor an algorithmic FLA-specific search innovation.",
        "Strict local six-arm reference across each source block; do not compare historical per-job self-referenced sim_hv. No automatic promotion to master, no modification to FLA-v12, NSGA-II, FIFO defaults."
    ]
    (out/"staged_real_optimizer_true_hv_and_cost_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_18_ARTIFACT_DIR OUTPUT")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
