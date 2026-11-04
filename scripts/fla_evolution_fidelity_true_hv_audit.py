#!/usr/bin/env python3
"""Read-only scientific audit of 128 true WorkflowSim evolutionary fidelity points.

Strict original source complete / no fitted policy / common reference per DAG.
"""
import csv,itertools,math,pathlib,statistics,sys
DAGS=("CyberShake_50","Sipht_60")
MODES=("old","full-ready","periodic","risk")
SOLVERS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
ORIGINAL_RUN="41780754595"
EPS=1e-10

def read(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def save(path,data):
    if not data:raise AssertionError("No source data")
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(data[0]))
        writer.writeheader();writer.writerows(data)
def non_dominated(pts):
    return sorted(set(x for x in pts if not any(
        y[0]<=x[0] and y[1]<=x[1] and (y[0]<x[0] or y[1]<x[1]) for y in pts)))
def hv(pts,ref):
    rx,ry=ref
    nd=non_dominated(pts)
    bottom=ry;area=0.
    for a,b in nd:
        if a<rx and b<bottom:
            area+=(rx-a)*(bottom-b)
            bottom=b
    result=area/(rx*ry)
    if not (0<=result<=1+1e-8):raise AssertionError(("invalid HV",result))
    return result
def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    raw={}
    for dag,mode in itertools.product(DAGS,MODES):
        name=f"fla-evolution-fidelity-{dag}-{mode}-{ORIGINAL_RUN}"
        directories=[p for p in root.iterdir() if p.is_dir() and p.name==name]
        if len(directories)!=1:
            raise AssertionError(("Missing or duplicate source original",name))
        directory=directories[0]
        tags=dict(x.split("=",1) for x in (directory/"block-id.txt").read_text().split())
        if (tags.get("DAG"),tags.get("seed"),tags.get("treatment"),
            tags.get("K"),tags.get("fitness_visits"),tags.get("ready_quota"))!=(
            dag,"801",mode,"8","3030","378"):
            raise AssertionError(("Source provenance changed",name,tags))
        summary=read(directory/"research_summary.csv")
        replays=read(directory/"research_replays.csv")
        if len(summary)!=2 or len(replays)!=16 or {x["algorithm"] for x in summary}!=set(SOLVERS):
            raise AssertionError(("Incomplete actual simulator source",name))
        fidelity=read(directory/"research_evolution_fidelity.csv") if mode in ("periodic","risk") else []
        if mode in ("periodic","risk") and (len(fidelity)!=2 or {x["algorithm"] for x in fidelity}!=set(SOLVERS)):
            raise AssertionError(("Incomplete fidelity trace",name))
        raw[(dag,mode)]={}
        for solver in SOLVERS:
            s=next(x for x in summary if x["algorithm"]==solver)
            if (int(s["evaluations"]),int(s["captured_evaluations"]),
                int(s["population"]),int(s["generations"]),int(s["replayed"]))!=(
                3030,3030,30,100,8):
                raise AssertionError(("Search budget changed",name,solver))
            if s["workflow"]!=dag or s["seed"]!="801":
                raise AssertionError(("Wrong original source",name))
            records=sorted([x for x in replays if x["algorithm"]==solver],
                          key=lambda r:int(r["candidate_index"]))
            if len(records)!=8 or len({r["mapping"] for r in records})!=8 or [int(x["candidate_index"]) for x in records]!=list(range(1,9)):
                raise AssertionError(("Wrong real replay K8",name,solver))
            points=[]
            for r in records:
                if r["workflow"]!=dag or r["seed"]!="801":
                    raise AssertionError("Wrong replay metadata")
                pair=(float(r["sim_makespan"]),float(r["sim_cost"]))
                if not all(math.isfinite(x) and x>0 for x in pair):
                    raise AssertionError(("Invalid simulator result",name,solver))
                points.append(pair)
            trace=next((x for x in fidelity if x["algorithm"]==solver),None)
            if trace:
                if trace["mode"]!=mode or int(trace["visits"])!=3030 or int(trace["ready_budget"])!=378:
                    raise AssertionError(("Fidelity mode or budget changed",name,solver))
                ready=int(trace["ready_calls"])
                cheap=int(trace["cheap_calls"])
                repeat=int(trace["cache_hits"])
                if not (0<=ready<=378 and cheap+repeat==3030 and int(trace["distinct"])==cheap):
                    raise AssertionError(("Impossible decoder trace",name,solver))
                cheap_ns=int(trace["cheap_ns"]);ready_ns=int(trace["ready_ns"])
            else:
                ready=cheap=repeat=cheap_ns=ready_ns=0
            time=float(s["search_ms"])
            if not math.isfinite(time) or time<0:raise AssertionError("Invalid timing")
            raw[(dag,mode)][solver]=dict(points=points,search_ms=time,
                 ready_calls=ready,cheap_calls=cheap,cache_hits=repeat,
                 cheap_ns=cheap_ns,ready_ns=ready_ns)
    all_rows=[];paired=[]
    for dag in DAGS:
        pts=[p for mode in MODES for solver in SOLVERS for p in raw[(dag,mode)][solver]["points"]]
        ref={k:(k*max(p[0] for p in pts)+1e-6,
                 k*max(p[1] for p in pts)+1e-6) for k in (1.5,3.0)}
        lookup={}
        for mode in MODES:
            for solver in SOLVERS:
                x=raw[(dag,mode)][solver]
                row=dict(workflow=dag,seed=801,solver=solver,mode=mode,
                    original_genotype_evaluations=3030,actual_simulator_replays=8,
                    actual_nd_count=len(non_dominated(x["points"])),
                    real_min_makespan=min(p[0] for p in x["points"]),
                    real_min_cost=min(p[1] for p in x["points"]),
                    ready_evolution_calls=x["ready_calls"],
                    cheap_evolution_calls=x["cheap_calls"],
                    cached_repeat_fitness_visits=x["cache_hits"],
                    high_fidelity_quota=378 if mode in ("risk","periodic") else "",
                    original_search_ms=x["search_ms"],
                    ready_evolution_ns=x["ready_ns"],
                    cheap_evolution_ns=x["cheap_ns"],
                    actual_normalized_hv15=hv(x["points"],ref[1.5]),
                    actual_normalized_hv30=hv(x["points"],ref[3.0]),
                    true_shared_ref15_m=ref[1.5][0],
                    true_shared_ref15_c=ref[1.5][1])
                all_rows.append(row);lookup[(mode,solver)]=row
        for solver in SOLVERS:
            old=lookup[("old",solver)]
            high=lookup[("full-ready",solver)]
            for mode in ("periodic","risk"):
                z=lookup[(mode,solver)]
                paired.append(dict(workflow=dag,solver=solver,mode=mode,
                    real_hv15=z["actual_normalized_hv15"],
                    original_hv15=old["actual_normalized_hv15"],
                    full_ready_hv15=high["actual_normalized_hv15"],
                    delta_vs_old=z["actual_normalized_hv15"]-old["actual_normalized_hv15"],
                    delta_vs_full_ready=z["actual_normalized_hv15"]-high["actual_normalized_hv15"],
                    delta_vs_old_hv30=z["actual_normalized_hv30"]-old["actual_normalized_hv30"],
                    ready_calls=z["ready_evolution_calls"],
                    actual_search_ms=z["original_search_ms"],
                    old_search_ms=old["original_search_ms"],
                    ready_search_ms=high["original_search_ms"]))
    if len(all_rows)!=16 or len(paired)!=8:raise AssertionError("Incomplete 128-replay pilot")
    save(out/"all_16_original_solver_mode_true_hv.csv",all_rows)
    save(out/"all_8_paired_fidelity_true_hv_differences.csv",paired)
    report=[
       "# During-evolution dual-fidelity: actual WorkflowSim FLA vs seeded NSGA-II developer pilot",
       "",
       f"Immutable original run {ORIGINAL_RUN}: 8 whole jobs, 2 DAG ×4 modes ×2 solvers ×8 actual replays = 128 real WorkflowSim outcomes. Original counted genotype fitness evaluations 3030 per solver/run. Four modes OLD, FULL READY, PERI0DIC budgeted and RISK gate budgeted were locked before any outcomes.",
       "Both experimental modes use identical first-write Task→VM objective caching, OLD stage-in evaluation on first-seen mapping, quota 378 READY calls with cumulative budget tokens, and FIFO runtime. The periodic and Pareto risk gate can consume fewer than the limit. Mixed-fidelity fitness is not a globally calibrated or consistent physical objective across different assignments.",
       "",
       "| DAG | Solver | OLD actual HV | FULL READY actual HV | PERIODIC actual HV | RISK actual HV | PERIODIC READY calls | RISK READY calls |",
       "|---|---|---:|---:|---:|---:|---:|---:|"]
    for dag in DAGS:
        for solver in SOLVERS:
            group={r["mode"]:r for r in all_rows if (r["workflow"],r["solver"])==(dag,solver)}
            report.append(f"| {dag} | {'FLA' if solver==SOLVERS[0] else 'NSGA-II'} | "
             f"{group['old']['actual_normalized_hv15']:.8f} | "
             f"{group['full-ready']['actual_normalized_hv15']:.8f} | "
             f"{group['periodic']['actual_normalized_hv15']:.8f} | "
             f"{group['risk']['actual_normalized_hv15']:.8f} | "
             f"{group['periodic']['ready_evolution_calls']} | "
             f"{group['risk']['ready_evolution_calls']} |")
    report+=["","## All eight true HV deltas and source search time"]
    for x in paired:
        report.append(f"- {x['workflow']} {x['solver']} {x['mode']}: "
          f"HV−OLD={x['delta_vs_old']:+.8f}, HV−FULL_READY={x['delta_vs_full_ready']:+.8f}; "
          f"READY calls={x['ready_calls']}, search_ms={x['actual_search_ms']:.1f} "
          f"(OLD {x['old_search_ms']:.1f}, FULL READY {x['ready_search_ms']:.1f}).")
    report+=["",
      "## Scope and conclusion guardrail",
      "This is TWO already-known DAG families and ONE seed, not an independent experiment with useful statistical power. The experimental methods may distort Pareto ranking due to uncalibrated old-vs-ready objective mixture, and a cache changes revisit cost relative to original OLD/FULL READY modes.",
      "Do not confuse matched counted 3030 fitness VISITS with matched decoder computational cost or wall-clock time. Under budgeted modes duplicates reuse prior fitness and may lower actual model calls. A fair CPU-time-matched baseline is still needed.",
      "Simulator HV is from K8 prospectively selected *planned* assignments, not the complete true Pareto front; all 8 arms within each DAG share one true reference. The 3.0× sensitivity, true points and failures are preserved.",
      "A successful CI run certifies code execution and data integrity only, NOT robust or novel FLA optimization. No mode becomes default; `master` remains unchanged."
    ]
    (out/"evolution_fidelity_true_hv_pilot_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_COMPLETE_EIGHT_JOBS OUTPUT")
    audit(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
