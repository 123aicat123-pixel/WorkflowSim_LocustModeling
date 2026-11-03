#!/usr/bin/env python3
"""Read-only, strict 40-source-job, matched restart vs ready-policy true HV audit.

Freeze before source completion and refuse incomplete originals. All replay
points are actual WorkflowSim outputs obtained prospectively, not surrogate
oracles. This script performs NO optimizer or simulator actions.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("Inspiral_50","Epigenomics_46")
BASE_SEEDS=(821,822)
ARMS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
VM_PROFILE="staggered"
VARIANTS={
    "old_full":           ("fifo",30,16,0),
    "ready_full":         ("fifo",30,16,0),
    "shortest_full":      ("shortest",30,16,0),
    "upward_full":        ("upward",30,16,0),
    "split_fifo0":        ("fifo",10,6,0),
    "split_fifo1":        ("fifo",10,5,10000),
    "split_fifo2":        ("fifo",10,5,20000),
    "split_priority_fifo":("fifo",10,6,0),
    "split_priority_shortest":("shortest",10,5,10000),
    "split_priority_upward":("upward",10,5,20000),
}
TREATMENTS={
    "old_full":("old_full",),
    "ready_full":("ready_full",),
    "shortest_full":("shortest_full",),
    "upward_full":("upward_full",),
    "fifo_restarts":("split_fifo0","split_fifo1","split_fifo2"),
    "priority_restarts":("split_priority_fifo","split_priority_shortest","split_priority_upward"),
}
TOL=1e-8

def csv_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def nd_front(points):
    distinct=sorted(set(tuple(map(float,p)) for p in points))
    return [p for p in distinct if not any(q[0]<=p[0] and q[1]<=p[1] and q!=p for q in distinct)]

def hv(points,ref):
    rx,ry=ref
    nd=nd_front(p for p in points if p[0]<rx and p[1]<ry)
    area=0.0
    previous=ry
    for x,y in nd:
        if y>=previous:continue
        area+=(rx-x)*(previous-y)
        previous=y
    answer=area/(rx*ry)
    if not math.isfinite(answer) or not (-1e-10<=answer<=1+1e-10):
        raise AssertionError(("HV invalid",answer,ref))
    return answer

def parse_artifacts(root):
    data={}
    for directory in root.iterdir():
        if not directory.is_dir():continue
        file=directory/"block-id.txt"
        if not file.exists():continue
        tags=dict(token.split("=",1) for token in file.read_text(encoding="utf-8").split())
        workflow=tags.get("DAG")
        base=int(tags.get("base_seed","-1"))
        variant=tags.get("variant")
        key=(workflow,base,variant)
        if workflow not in DAGS or base not in BASE_SEEDS or variant not in VARIANTS or key in data:
            raise AssertionError(("unexpected/duplicate original result",key,directory))
        priority,pop,k,offset=VARIANTS[variant]
        real_seed=base+offset
        if (tags.get("runtime_priority"),int(tags.get("pop","-1")),
            int(tags.get("K","-1")),int(tags.get("source_seed","-1")),
            tags.get("profile"))!=(priority,pop,k,real_seed,VM_PROFILE):
            raise AssertionError(("changed or mislabeled source protocol",tags))
        summary=csv_rows(directory/"research_summary.csv")
        replay=csv_rows(directory/"research_replays.csv")
        if len(summary)!=2 or len(replay)!=2*k or {s["algorithm"] for s in summary}!=set(ARMS):
            raise AssertionError(("incomplete actual optimizer/simulator source",key,len(summary),len(replay)))
        solver_data={}
        for s in summary:
            arm=s["algorithm"]
            if s["workflow"]!=workflow or int(s["seed"])!=real_seed:
                raise AssertionError(("source identity mismatch",key,arm))
            expected=(pop,100,pop*101,pop*101,k)
            actual=tuple(int(s[q]) for q in
                         ("population","generations","evaluations","captured_evaluations","replayed"))
            if actual!=expected:
                raise AssertionError(("genotype evaluation/replay unfairness",key,arm,actual,expected))
            cand=sorted((r for r in replay if r["algorithm"]==arm),
                        key=lambda r:int(r["candidate_index"]))
            if len(cand)!=k or [int(c["candidate_index"]) for c in cand]!=list(range(1,k+1)):
                raise AssertionError(("bad replay sequence",key,arm))
            if len({c["mapping"] for c in cand})!=k:
                raise AssertionError(("same-priority duplicate within K",key,arm))
            for c in cand:
                if c["workflow"]!=workflow or int(c["seed"])!=real_seed:
                    raise AssertionError(("actual replay wrong source",key,arm))
                for q in ("sim_makespan","sim_cost","planned_makespan","planned_cost"):
                    if not math.isfinite(float(c[q])) or float(c[q])<=0:
                        raise AssertionError(("nonfinite/nonpositive source metric",key,arm,q,c[q]))
            timers={}
            for col in ("search_ms","selection_ms","replay_ms"):
                timer=float(s[col])
                if not math.isfinite(timer) or timer<0:raise AssertionError(("invalid source time",key,arm,col))
                timers[col]=timer
            solver_data[arm]=dict(rows=cand,times=timers,source_evals=pop*101,
                                  source_actual=k,source_seed=real_seed)
        data[key]=solver_data
    required=set(itertools.product(DAGS,BASE_SEEDS,VARIANTS))
    if set(data)!=required:
        raise AssertionError(("INCOMPLETE ORIGINAL, REFUSE PARTIAL ANALYSIS",
                             sorted(required-set(data)),sorted(set(data)-required)))
    return data

def write(path,items):
    if not items:raise AssertionError(("no data",path))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]))
        w.writeheader();w.writerows(items)

def assert_repeated_source_identity(data):
    """Independent rerun of exact first FIFO island must not falsely add evidence."""
    checked=0
    for workflow,base,arm in itertools.product(DAGS,BASE_SEEDS,ARMS):
        one=data[(workflow,base,"split_fifo0")][arm]["rows"]
        two=data[(workflow,base,"split_priority_fifo")][arm]["rows"]
        assert len(one)==len(two)==6
        for a,b in zip(one,two):
            if a["mapping"]!=b["mapping"]:
                raise AssertionError(("controlled first FIFO island not bit-deterministic",workflow,base,arm))
            for col in ("planned_makespan","planned_cost","sim_makespan","sim_cost"):
                x=float(a[col]);y=float(b[col])
                if not math.isclose(x,y,rel_tol=1e-7,abs_tol=1e-6):
                    raise AssertionError(("controlled duplicate outcome changed",workflow,base,arm,col,x,y))
            checked+=1
    return checked

def analyze(root,out):
    data=parse_artifacts(root)
    repeated=assert_repeated_source_identity(data)
    out.mkdir(parents=True,exist_ok=True)
    cases=[]
    effects=[]
    cross=[]
    duplicates=[]
    for workflow,seed in itertools.product(DAGS,BASE_SEEDS):
        block={}
        for arm in ARMS:
            for treatment,variants in TREATMENTS.items():
                sources=[data[(workflow,seed,v)][arm] for v in variants]
                assert sum(x["source_evals"] for x in sources)==3030
                assert sum(x["source_actual"] for x in sources)==16
                selected=[]
                tagged=[]
                for variant,src in zip(variants,sources):
                    policy=VARIANTS[variant][0]
                    for r in src["rows"]:
                        selected.append((float(r["sim_makespan"]),float(r["sim_cost"])))
                        tagged.append((policy,r["mapping"]))
                distinct=len(set(tagged))
                duplicates.append(dict(workflow=workflow,seed=seed,solver=arm,
                   treatment=treatment,real_simulator_calls=16,distinct_physical_policy_mapping=distinct,
                   duplicated_physical_configs=16-distinct,
                   distinct_observed_real_points=len(set(selected))))
                block[(arm,treatment)]=dict(points=selected,
                    m=min(x for x,y in selected),c=min(y for x,y in selected),
                    nd=len(nd_front(selected)),
                    search_ms=sum(x["times"]["search_ms"] for x in sources),
                    selection_ms=sum(x["times"]["selection_ms"] for x in sources),
                    replay_ms=sum(x["times"]["replay_ms"] for x in sources),
                    mapped=distinct)
        all_points=[p for c in block.values() for p in c["points"]]
        max_m=max(p[0] for p in all_points)
        max_c=max(p[1] for p in all_points)
        ref={f:(f*max_m+1e-6,f*max_c+1e-6) for f in (1.5,3.0)}
        for (arm,treatment),b in block.items():
            cases.append(dict(workflow=workflow,seed=seed,solver=arm,treatment=treatment,
                total_genotype_evaluations=3030,actual_simulator_calls=16,
                physical_distinct_policy_mappings=b["mapped"],true_nd_points=b["nd"],
                best_actual_makespan=b["m"],best_actual_cost=b["c"],
                search_ms=b["search_ms"],selection_ms=b["selection_ms"],replay_ms=b["replay_ms"],
                common_real_hv15=hv(b["points"],ref[1.5]),
                common_real_hv30=hv(b["points"],ref[3.0]),
                ref_m15=ref[1.5][0],ref_c15=ref[1.5][1],
                ref_m30=ref[3.0][0],ref_c30=ref[3.0][1]))
        for arm in ARMS:
            get=lambda t:next(x for x in cases if (x["workflow"],x["seed"],x["solver"],x["treatment"])==(workflow,seed,arm,t))
            for test,baseline in (
                ("shortest_full","ready_full"),
                ("upward_full","ready_full"),
                ("fifo_restarts","ready_full"),
                ("priority_restarts","fifo_restarts"),
                ("priority_restarts","old_full"),
                ("ready_full","old_full")):
                new=get(test);old=get(baseline)
                effects.append(dict(workflow=workflow,seed=seed,solver=arm,
                    candidate=test,baseline=baseline,
                    baseline_hv15=old["common_real_hv15"],candidate_hv15=new["common_real_hv15"],
                    delta_hv15=new["common_real_hv15"]-old["common_real_hv15"],
                    delta_hv30=new["common_real_hv30"]-old["common_real_hv30"],
                    search_time_ratio=new["search_ms"]/max(1e-6,old["search_ms"]),
                    candidate_distinct_configs=new["physical_distinct_policy_mappings"],
                    baseline_distinct_configs=old["physical_distinct_policy_mappings"]))
        for treatment in TREATMENTS:
            a=next(x for x in cases if
                (x["workflow"],x["seed"],x["solver"],x["treatment"])==
                (workflow,seed,ARMS[0],treatment))
            b=next(x for x in cases if
                (x["workflow"],x["seed"],x["solver"],x["treatment"])==
                (workflow,seed,ARMS[1],treatment))
            cross.append(dict(workflow=workflow,seed=seed,treatment=treatment,
                fla_true_hv15=a["common_real_hv15"],nsga_true_hv15=b["common_real_hv15"],
                fla_minus_nsga_hv15=a["common_real_hv15"]-b["common_real_hv15"]))
    assert len(cases)==4*2*6
    assert len(duplicates)==len(cases)
    assert repeated==4*2*6
    write(out/"all_48_six_arm_true_hv.csv",cases)
    write(out/"all_48_restart_and_policy_paired_comparisons.csv",effects)
    write(out/"all_24_solver_cross_comparisons.csv",cross)
    write(out/"all_48_duplicate_and_diversity_counts.csv",duplicates)
    comparisons=[
        ("shortest_full","ready_full"),
        ("upward_full","ready_full"),
        ("fifo_restarts","ready_full"),
        ("priority_restarts","fifo_restarts"),
        ("priority_restarts","old_full"),
        ("ready_full","old_full"),
    ]
    report=[
        "# Full-budget single-priority and restart-matched FLA/NSGA-II actual WorkflowSim HV",
        "",
        "Frozen before original data: docs/FLA_PRIORITY_RESTART_DECONFOUND_FROZEN_PROTOCOL_2026-11-04.md.",
        "Original 40 completed optimization/real WorkflowSim jobs: GitHub Actions 41689142588. This is a read-only independent audit and does not run the optimizer again.",
        f"PASS complete 40 source jobs, 48 assembled true K16 Pareto sets across 4 blocks, 768 actual simulator calls (some deliberate repeated controls), **{repeated} controlled repeated FIFO selected source mapping pairs verified identical**.",
        "All 12 solver/treatment assembled actual sets share one 1.5× and one 3.0× normalized HV reference PER DAX/seed. All treatments consume 3030 counted genotype objective calls, K16 actual WorkflowSim calls; not time-matched computation.",
        "",
        "## Per-block true normalized K16 HV (all 12 sets use shared reference)",
        "| DAG | Seed | Solver | Original FIFO insertion | Full FIFO ready | Full shortest | Full upward | Three FIFO restarts | Matched three-priority restarts |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for workflow,seed in itertools.product(DAGS,BASE_SEEDS):
        for arm in ARMS:
            z={x["treatment"]:x for x in cases if (x["workflow"],x["seed"],x["solver"])==(workflow,seed,arm)}
            report.append(f"| {workflow} | {seed} | {'FLA-v12' if arm==ARMS[0] else 'NSGA-II-seeded'} | "
             +" | ".join(f"{z[t]['common_real_hv15']:.8f}" for t in TREATMENTS)+" |")
    report+=["","## Fair paired comparisons; 4 descriptive blocks per solver (NOT inferential tests)"]
    for arm in ARMS:
        report.append("**"+("FLA v12" if arm==ARMS[0] else "Cost-seeded NSGA-II")+"**")
        for test,baseline in comparisons:
            r=[x for x in effects if x["solver"]==arm and x["candidate"]==test and x["baseline"]==baseline]
            assert len(r)==4
            vals=[x["delta_hv15"] for x in r]
            vals30=[x["delta_hv30"] for x in r]
            reversals=sum((v>TOL and w< -TOL) or (v< -TOL and w>TOL) for v,w in zip(vals,vals30))
            report.append(f"- {test} vs {baseline}: mean Δ real HV={statistics.mean(vals):+.8f}, "
              f"median Δ={statistics.median(vals):+.8f}, "
              f"wins/ties/losses={sum(v>TOL for v in vals)}/{sum(abs(v)<=TOL for v in vals)}/{sum(v<-TOL for v in vals)}, "
              f"mean search wall-time ratio={statistics.mean(x['search_time_ratio'] for x in r):.2f}×, "
              f"3× reference sign reversals={reversals}.")
    report+=["","## Solver parity and duplicate control"]
    for treatment in TREATMENTS:
        r=[x for x in cross if x["treatment"]==treatment]
        diff=[x["fla_minus_nsga_hv15"] for x in r]
        report.append(f"- FLA−NSGA-II {treatment}: mean={statistics.mean(diff):+.8f}, wins/ties/losses="
           f"{sum(v>TOL for v in diff)}/{sum(abs(v)<=TOL for v in diff)}/{sum(v<-TOL for v in diff)}.")
    dupl=[d for d in duplicates if d["duplicated_physical_configs"]>0]
    report.append(f"- {len(dupl)}/{len(duplicates)} assembled solver/treatment K16 sets contain repeated physical (priority, task→VM mapping) configurations across independent islands; the duplicates are not independent Pareto observations. Per-treatment counts are in `all_48_duplicate_and_diversity_counts.csv`.")
    report+=["","## Mandatory interpretation",
      "The three-FIFO-restart control is matched to the three-policy portfolio in population size, seed offsets and 6/5/5 true simulation quota; this helps isolate per-island policy changes, but genuine joint priority-gene search is NOT implemented.",
      "Each budget is 3030 counted genotype evaluations, yet model work per evaluation varies and multiple populations have different overhead; report search time and do not equate same genotype count to same CPU time.",
      "K16 is a planner-selected simulator subset, not the complete Pareto optimal set. A global or per-case best-priority selected AFTER seeing actual sim data is an invalid future-looking oracle.",
      "The two DAG families are historically studied and only two optimizer seeds are used; no Q1 publication or broad out-of-family claim is warranted.",
      "Preserve negative results, do not tune on these four blocks, keep all policies OFF except explicit research opt-in, and do NOT modify master."]
    (out/"full_priority_restart_true_hv_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_40_JOB_ARTIFACT_FOLDER OUTPUT_FOLDER")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
