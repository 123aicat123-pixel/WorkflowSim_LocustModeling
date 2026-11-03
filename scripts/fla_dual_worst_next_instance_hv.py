#!/usr/bin/env python3
"""Read-only paired old/ready FLA & seeded NSGA-II real WorkflowSim K16 comparison.

NEVER compare distinct run-local HV reference points. Every 2-by-2 cell
within one DAG/seed is rescored under common 1.5x and 3x references.
Source: original Actions 41670356422. No further simulator or optimizer calls.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("Inspiral_50","Epigenomics_24")
SEEDS=(501,502)
DECODERS=("old","worst")
ARMS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
TOL=1e-10

def load(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def pareto(points):
    distinct=sorted(set((float(x),float(y)) for x,y in points))
    return [p for p in distinct if not any(
        q[0]<=p[0] and q[1]<=p[1] and q!=p for q in distinct)]

def hv(points,reference):
    rx,ry=reference
    nd=pareto([p for p in points if p[0]<rx and p[1]<ry])
    area=0.0
    prev_y=ry
    for x,y in nd:
        if y>=prev_y-TOL:continue
        area+=(rx-x)*(prev_y-y)
        prev_y=y
    return area/(rx*ry)

def read_originals(root):
    result={}
    for directory in root.iterdir():
        if not directory.is_dir():continue
        idfile=directory/"block-id.txt"
        if not idfile.exists():continue
        properties=dict(line.strip().split("=",1) for line in idfile.read_text().split())
        wf=properties["DAG"];seed=int(properties["seed"]);decoder=properties["decoder"]
        key=(wf,seed,decoder)
        if wf not in DAGS or seed not in SEEDS or decoder not in DECODERS or key in result:
            raise AssertionError(("Unexpected/duplicate case",key))
        summary=load(directory/"research_summary.csv")
        replays=load(directory/"research_replays.csv")
        if len(summary)!=2 or len(replays)!=32:
            raise AssertionError(("Bad original K16 file",key,len(summary),len(replays)))
        if {s["algorithm"] for s in summary}!=set(ARMS):
            raise AssertionError(("Different algorithms",key))
        per_arm={}
        for s in summary:
            arm=s["algorithm"]
            if (s["workflow"],int(s["seed"]))!=(wf,seed):
                raise AssertionError("Wrong source labels")
            if (int(s["population"]),int(s["generations"]),
                int(s["evaluations"]),int(s["captured_evaluations"]),int(s["replayed"]))!=(30,100,3030,3030,16):
                raise AssertionError(("Unfair budget",key,arm,s))
            selected=sorted((r for r in replays if r["algorithm"]==arm),
                            key=lambda r:int(r["candidate_index"]))
            if len(selected)!=16 or [int(r["candidate_index"]) for r in selected]!=list(range(1,17)):
                raise AssertionError(("Wrong replay coverage",key,arm))
            if len(set(r["mapping"] for r in selected))!=16:
                raise AssertionError(("Duplicate K16 mapping",key,arm))
            points=[]
            for row in selected:
                if row["workflow"]!=wf or int(row["seed"])!=seed:raise AssertionError("Case mismatch")
                m=float(row["sim_makespan"]);c=float(row["sim_cost"])
                if not all(math.isfinite(x) and x>0 for x in (m,c)):
                    raise AssertionError("Bad actual WorkflowSim values")
                points.append((m,c))
            per_arm[arm]=dict(summary=s,points=points)
        result[key]=per_arm
    if set(result)!=set(itertools.product(DAGS,SEEDS,DECODERS)):
        raise AssertionError(("Incomplete original eight benchmark invocations",set(result)))
    return result

def write(path,rows):
    if not rows:raise AssertionError("Empty output rows")
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def analyze(root,out):
    data=read_originals(root)
    out.mkdir(parents=True,exist_ok=True)
    cases=[]
    paired=[]
    for wf,seed in itertools.product(DAGS,SEEDS):
        all_points=[p for decoder,arm in itertools.product(DECODERS,ARMS)
                    for p in data[(wf,seed,decoder)][arm]["points"]]
        max_m=max(m for m,_ in all_points)
        max_c=max(c for _,c in all_points)
        common={factor:(factor*max_m+1e-6,factor*max_c+1e-6)
                for factor in (1.5,3.0)}
        for decoder,arm in itertools.product(DECODERS,ARMS):
            value=data[(wf,seed,decoder)][arm]
            s=value["summary"];pts=value["points"]
            c=dict(workflow=wf,seed=seed,decoder=decoder,algorithm=arm,
                   search_ms=float(s["search_ms"]),
                   replay_ms=float(s["replay_ms"]),
                   budget_evals=int(s["evaluations"]),
                   actual_replays=int(s["replayed"]),
                   real_nd_count=len(pareto(pts)),
                   common_hv15=hv(pts,common[1.5]),
                   common_hv30=hv(pts,common[3.0]),
                   min_actual_makespan=min(x for x,y in pts),
                   min_actual_cost=min(y for x,y in pts),
                   ref15_m=common[1.5][0],ref15_c=common[1.5][1],
                   ref30_m=common[3.0][0],ref30_c=common[3.0][1])
            cases.append(c)
        lookup={(c["decoder"],c["algorithm"]):c for c in cases
                if (c["workflow"],c["seed"])==(wf,seed)}
        for arm in ARMS:
            old=lookup[("old",arm)];new=lookup[("worst",arm)]
            paired.append(dict(workflow=wf,seed=seed,algorithm=arm,
                delta_hv15=new["common_hv15"]-old["common_hv15"],
                delta_hv30=new["common_hv30"]-old["common_hv30"],
                rel_hv15_pct=100*(new["common_hv15"]-old["common_hv15"])/max(1e-12,old["common_hv15"]),
                rel_hv30_pct=100*(new["common_hv30"]-old["common_hv30"])/max(1e-12,old["common_hv30"]),
                old_search_ms=old["search_ms"],ready_search_ms=new["search_ms"],
                search_time_ratio=new["search_ms"]/max(1e-6,old["search_ms"]),
                old_real_nd=old["real_nd_count"],ready_real_nd=new["real_nd_count"]))
    write(out/"common_reference_all_arms.csv",cases)
    write(out/"paired_decoder_hv_deltas.csv",paired)
    report=["# Equal-budget FLA/NSGA-II search with historical vs frozen dual-worst decoder",
        "",
        "This is an independent **read-only** recomputation of actual WorkflowSim K16 hypervolume on identical within-DAG-and-seed references.",
        "Original simulator + optimizer Actions run: 41673100999; 8 original benchmark invocations, two solvers per invocation, 3030 counted evaluations per solver, K16 true simulator calls per solver. Archived negative results are kept.",
        "",
        "## All four block × two-solver paired comparisons",
        "| DAG | Seed | Solver | Old HV 1.5x | Worst HV 1.5x | Δ HV (worst−old) | Δ HV at 3.0x | Worst/old search wall time |",
        "|---|---:|---|---:|---:|---:|---:|---:|"]
    for p in paired:
        old=next(c for c in cases if (c["workflow"],c["seed"],c["algorithm"],c["decoder"])==
                 (p["workflow"],p["seed"],p["algorithm"],"old"))
        new=next(c for c in cases if (c["workflow"],c["seed"],c["algorithm"],c["decoder"])==
                 (p["workflow"],p["seed"],p["algorithm"],"worst"))
        arm="FLA-v12" if p["algorithm"]==ARMS[0] else "NSGA-II-seeded"
        report.append(f"| {p['workflow']} | {p['seed']} | {arm} | "
            f"{old['common_hv15']:.8f} | {new['common_hv15']:.8f} | "
            f"{p['delta_hv15']:+.8f} | {p['delta_hv30']:+.8f} | "
            f"{p['search_time_ratio']:.2f}× |")
    report+=["","## Block-paired descriptive summary, NOT inferential statistics"]
    for arm in ARMS:
        subset=[x for x in paired if x["algorithm"]==arm]
        wins=sum(x["delta_hv15"]>TOL for x in subset)
        ties=sum(abs(x["delta_hv15"])<=TOL for x in subset)
        losses=len(subset)-wins-ties
        report.append(f"- {arm}: mean Δ normalized true HV(1.5×) = "
          f"{statistics.mean(x['delta_hv15'] for x in subset):+.8f}; "
          f"wins/ties/losses {wins}/{ties}/{losses}; mean search time ratio "
          f"{statistics.mean(x['search_time_ratio'] for x in subset):.2f}×.")
    report+=["","## Interpretation",
        "HV is recomputed under a single shared 1.5×/3× reference based on all four cells of each DAG/seed block, unlike the independently reported per-invocation HV.",
        "The new decoder was used identically by both FLA and seeded NSGA-II. Any gain shared by both is decoder/model impact, NOT FLA-specific innovation.",
        "K16 planned Pareto-cover replays are a small selected subset and not a complete true Pareto front; search may trade off false negatives and archive coverage.",
        "Two previously researched DAG instances and only two seeds are insufficient for independent holdout, publication, or significance claims.",
        "No default algorithm is automatically promoted by this research-only result."]
    (out/"paired_true_hv_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: study.py ORIGINAL_ARTIFACT_FOLDER OUTPUT_FOLDER")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
