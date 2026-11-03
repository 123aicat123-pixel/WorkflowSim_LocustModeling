#!/usr/bin/env python3
"""Strict read-only true WorkflowSim HV audit for frozen FLA-v19 first gate.

Independent original optimizer/simulator Actions source 41690669415.
Never use original run-local sim_hv; all four treatment arms in each source
DAG/seed block are rescored on one common actual reference.
"""
import csv
import itertools
import math
import pathlib
import re
import statistics
import sys

DAGS=("Inspiral_100","Sipht_100")
SEEDS=(901,902)
ARMS=("DAG-Pareto-FLA[v12-hvbandit]","DAG-Pareto-FLA[v18-disagreement]",
      "DAG-Pareto-FLA[v19-queue-risk]","NSGA-II[costseed]")
TOL=1e-8

def read(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def pareto(points):
    ps=sorted(set(tuple(map(float,x)) for x in points))
    return [x for x in ps if not any(y[0]<=x[0] and y[1]<=x[1] and y!=x for y in ps)]

def hv(points,ref):
    rx,ry=ref
    nd=pareto(x for x in points if x[0]<rx and x[1]<ry)
    area=0
    previous=ry
    for x,y in nd:
        if y>=previous:continue
        area+=(rx-x)*(previous-y)
        previous=y
    z=area/(rx*ry)
    if not math.isfinite(z) or z<0 or z>1+1e-8:
        raise AssertionError(("Bad true simulator HV",z))
    return z

def load(root):
    original={}
    shas=set()
    for dir in root.iterdir():
        if not dir.is_dir():continue
        block_file=dir/"block-id.txt"
        if not block_file.exists():continue
        tags=dict(z.split("=",1) for z in block_file.read_text().split())
        wf=tags.get("DAG")
        seed=int(tags.get("seed","-1"))
        if (wf,seed) not in set(itertools.product(DAGS,SEEDS)) or (wf,seed) in original:
            raise AssertionError(("Unregistered/duplicate block",wf,seed,dir))
        if (tags.get("vm_profile"),tags.get("policy"),
            int(tags.get("pop","-1")),int(tags.get("generations","-1")),
            int(tags.get("K","-1")))!=( "staggered","fifo",30,100,16):
            raise AssertionError(("Source changed problem resources/protocol",tags))
        sha=(dir/"source-sha.txt").read_text().strip()
        if not re.fullmatch(r"[0-9a-f]{40}",sha):raise AssertionError("Invalid source provenance SHA")
        shas.add(sha)
        ss=read(dir/"research_summary.csv")
        rr=read(dir/"research_replays.csv")
        if len(ss)!=4 or len(rr)!=64 or set(s["algorithm"] for s in ss)!=set(ARMS):
            raise AssertionError(("Incomplete original real optimization",wf,seed,len(ss),len(rr)))
        per_arm={}
        for s in ss:
            alg=s["algorithm"]
            if s["workflow"]!=wf or int(s["seed"])!=seed:
                raise AssertionError(("Unexpected source arm identity",wf,seed,alg))
            audit=tuple(int(s[x]) for x in ("population","generations","evaluations",
                                           "captured_evaluations","replayed"))
            if audit!=(30,100,3030,3030,16):
                raise AssertionError(("Unequal original optimizer/simulator K budget",wf,seed,alg,audit))
            z=sorted((x for x in rr if x["algorithm"]==alg),key=lambda x:int(x["candidate_index"]))
            if len(z)!=16 or [int(x["candidate_index"]) for x in z]!=list(range(1,17)) or len({x["mapping"] for x in z})!=16:
                raise AssertionError(("Missing/repeated original actual samples",wf,seed,alg))
            for x in z:
                if x["workflow"]!=wf or int(x["seed"])!=seed:
                    raise AssertionError(("Wrong real replay identity",wf,seed,alg))
                for col in ("sim_makespan","sim_cost","planned_makespan","planned_cost"):
                    v=float(x[col])
                    if not math.isfinite(v) or v<=0:
                        raise AssertionError(("Bad real or planned point",wf,seed,alg,col,v))
            times={}
            for col in ("search_ms","selection_ms","replay_ms"):
                t=float(s[col])
                if not math.isfinite(t) or t<0:
                    raise AssertionError(("Bad true original source wall time",wf,seed,alg,col,t))
                times[col]=t
            per_arm[alg]=dict(points=[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in z],
                              times=times,recorded_real=16,evals=3030)
        content=(dir/"v19_forecast_counter.txt").read_text().split()
        forecast=dict(item.split("=",1) for item in content)
        numbers={k:int(v) for k,v in forecast.items()}
        if set(numbers)!={"proposals","actualRelocations","internalForecasts","alternativeForecasts"}:
            raise AssertionError(("Missing FLA-v19 internal forecast accounting",wf,seed,numbers))
        p=numbers["proposals"];m=numbers["actualRelocations"]
        pred=numbers["internalForecasts"];other=numbers["alternativeForecasts"]
        if p<=0 or m<0 or m>p or pred<p or pred>3*p or pred-p!=other or other>2*p:
            raise AssertionError(("Implausible FLA-v19 actual proposal counters",wf,seed,numbers))
        original[(wf,seed)]=dict(arms=per_arm,forecast=numbers,sha=sha)
    if set(original)!=set(itertools.product(DAGS,SEEDS)):
        raise AssertionError(("INCOMPLETE ORIGINAL BLOCKS: no selected-case analysis",set(original)))
    if len(shas)!=1:
        raise AssertionError(("Original code SHA differs across matched simulator blocks",shas))
    return original,shas.pop()

def write(path,items):
    if not items:raise AssertionError("Empty audit rows")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)

def compare(root,out):
    source,source_sha=load(root)
    out.mkdir(parents=True,exist_ok=True)
    cases=[]
    diffs=[]
    reports=[]
    for wf,seed in itertools.product(DAGS,SEEDS):
        per=source[(wf,seed)]["arms"]
        points=[point for arm in ARMS for point in per[arm]["points"]]
        ref={f:(f*max(x for x,y in points)+1e-6,f*max(y for x,y in points)+1e-6)
             for f in (1.5,3.0)}
        block={}
        for arm in ARMS:
            v=per[arm]
            row=dict(workflow=wf,seed=seed,algorithm=arm,
                source_evaluations=3030,real_simulator_replays=16,
                nondominated_k16=len(pareto(v["points"])),
                best_actual_makespan=min(x for x,y in v["points"]),
                best_actual_cost=min(y for x,y in v["points"]),
                search_ms=v["times"]["search_ms"],
                selection_ms=v["times"]["selection_ms"],
                replay_ms=v["times"]["replay_ms"],
                actual_common_hv15=hv(v["points"],ref[1.5]),
                actual_common_hv30=hv(v["points"],ref[3.0]),
                reference15_m=ref[1.5][0],reference15_c=ref[1.5][1],
                reference30_m=ref[3.0][0],reference30_c=ref[3.0][1])
            cases.append(row);block[arm]=row
        a=block[ARMS[0]];b=block[ARMS[1]];v19=block[ARMS[2]];nsga=block[ARMS[3]]
        for label,base in [("v19_vs_v12",a),("v19_vs_v18",b),("v19_vs_nsga",nsga),("v18_vs_v12",a)]:
            new=v19 if label.startswith("v19") else b
            diffs.append(dict(workflow=wf,seed=seed,comparison=label,
                candidate_true_hv15=new["actual_common_hv15"],
                baseline_true_hv15=base["actual_common_hv15"],
                delta_true_hv15=new["actual_common_hv15"]-base["actual_common_hv15"],
                delta_true_hv30=new["actual_common_hv30"]-base["actual_common_hv30"],
                search_time_ratio=new["search_ms"]/max(1e-6,base["search_ms"]),
                candidate_search_ms=new["search_ms"],baseline_search_ms=base["search_ms"]))
        forecast=source[(wf,seed)]["forecast"]
        reports.append(dict(workflow=wf,seed=seed,**forecast,
                            v19_search_ms=v19["search_ms"],
                            v12_search_ms=a["search_ms"],
                            actual_replay_calls=64))
    assert len(cases)==16 and len(diffs)==16 and len(reports)==4
    write(out/"all_16_original_real_k16_arms.csv",cases)
    write(out/"all_16_paired_true_hv_deltas.csv",diffs)
    write(out/"v19_bounded_forecast_operations.csv",reports)
    lines=[
        "# FLA v19 queue conflict/risk relocation vs v12/v18/seeded NSGA-II: real K16 Pareto HV",
        "",
        "Preregistered before any new true simulator observations: docs/FLA_V19_QUEUE_CONFLICT_RISK_FROZEN_PROTOCOL_2026-11-04.md.",
        "Immutable original four-job optimization/real WorkflowSim: Actions 41690669415, same original source commit "+source_sha+".",
        "Four DAX/seed blocks, **4 solver arms per block × 3030 counted target evaluations and K16 actual simulator calls = 256 real WorkflowSim replay calls**, 48,480 target objective decodes total. The v19 operator performs EXTRA internal ready-model forecasts, explicitly counted below but NOT counted as target fitness operations.",
        "Same task→VM genetic encoding, stage-in-aware target objective, initial cost seeds and unchanged FIFO runtime. Identical common normalized 1.5× actual HV reference for all four arms within each DAG/seed block, also independently recomputed with 3.0× sensitivity.",
        "",
        "## True 1.5× common-reference K16 Pareto HV",
        "| Workflow | Seed | Original FLA-v12 | FLA-v18 disagreement | New FLA-v19 queue risk | Costseeded NSGA-II | v19−v12 | v19/v12 search time |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for wf,seed in itertools.product(DAGS,SEEDS):
        a={x["algorithm"]:x for x in cases if (x["workflow"],x["seed"])==(wf,seed)}
        old=a[ARMS[0]];new=a[ARMS[2]]
        lines.append(f"| {wf} | {seed} | "+
            " | ".join(f"{a[arm]['actual_common_hv15']:.8f}" for arm in ARMS)+
            f" | {new['actual_common_hv15']-old['actual_common_hv15']:+.8f} | "
            f"{new['search_ms']/max(1e-6,old['search_ms']):.2f}× |")
    lines+=["","## Descriptive paired differences (four blocks only; NOT statistical significance)"]
    for kind in ("v19_vs_v12","v19_vs_v18","v19_vs_nsga","v18_vs_v12"):
        z=[r for r in diffs if r["comparison"]==kind]
        delta=[r["delta_true_hv15"] for r in z]
        flip=sum((r["delta_true_hv15"]>TOL and r["delta_true_hv30"]<-TOL) or
                 (r["delta_true_hv15"]<-TOL and r["delta_true_hv30"]>TOL) for r in z)
        lines.append(f"- {kind}: mean Δ real normalized HV={statistics.mean(delta):+.8f}, median={statistics.median(delta):+.8f}, "
          f"wins/ties/losses={sum(v>TOL for v in delta)}/{sum(abs(v)<=TOL for v in delta)}/{sum(v<-TOL for v in delta)}; "
          f"mean measured search-time ratio={statistics.mean(r['search_time_ratio'] for r in z):.2f}×; "
          f"3.0× reference sign reversals={flip}.")
    lines+=["","## FLA-v19 local proposal mechanism actually executed"]
    for r in reports:
        lines.append(f"- {r['workflow']} seed {r['seed']}: triggered proposals={r['proposals']}, "
           f"actual one-gene relocations={r['actualRelocations']}, "
           f"internal uncounted ready forecasts={r['internalForecasts']}, "
           f"alternative counterfactual forecasts={r['alternativeForecasts']}, "
           f"search_wall_ratio_vs_v12={r['v19_search_ms']/max(1e-6,r['v12_search_ms']):.2f}×.")
    lines+=["","## Scientific boundaries",
      "An increase in planned fitness, exact objective count or CI success is NOT evidence of a better real Pareto scheduling algorithm. Only shared-reference *actual* K16 HV and time matter.",
      "The v19 method uses current and up to two alternative ready-model evaluations per trigger, which increase computational work relative to v12. Such calls are not counted by target genotype budget; time-matched experiments are essential before efficiency claims.",
      "DAG families are previously studied and only two seeds per family are present. No out-of-family generalization, statistical significance or SCI Q1 paper-readiness is established.",
      "Never select a best strategy by its already-seen true simulator outcome, then present it as prospective learning. Save all negative blocks and do not tune 0.35/1%/0.25 on these same block labels.",
      "Original v12, seeded NSGA-II, runtime FIFO and master branch remain untouched; FLA-v19 stays experimental OFF by default."
    ]
    (out/"v19_original_true_hv_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_COMPLETE_REAL_REPLAYS OUTPUT_FOLDER")
    compare(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
