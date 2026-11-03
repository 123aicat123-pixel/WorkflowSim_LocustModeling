#!/usr/bin/env python3
"""Independent 2D normalized true HV audit for 20 archived portfolio jobs.

Strict complete-source and equal-budget gating. Actual WorkflowSim labels
read ONLY after the source jobs finished, no optimizer tuning or oracle choice.
"""
import csv
import itertools
import math
import pathlib
import statistics
import sys

DAGS=("CyberShake_30","Sipht_30")
SEEDS=(711,712)
TREATMENTS=("old","ready","portfolio_fifo","portfolio_shortest","portfolio_upward")
ARMS=("DAG-Pareto-FLA[v12-hvbandit]","NSGA-II[costseed]")
RUNTIME={"old":"fifo","ready":"fifo","portfolio_fifo":"fifo",
         "portfolio_shortest":"shortest","portfolio_upward":"upward"}
REPLAY_QUOTAS={"old":16,"ready":16,"portfolio_fifo":6,
               "portfolio_shortest":5,"portfolio_upward":5}
EVALS={t:3030 if t in ("old","ready") else 1010 for t in TREATMENTS}
POPS={t:30 if t in ("old","ready") else 10 for t in TREATMENTS}
PORTFOLIO=("portfolio_fifo","portfolio_shortest","portfolio_upward")
TOL=1e-10

def rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def nondominated(points):
    p=sorted(set((float(x),float(y)) for x,y in points))
    return [x for x in p if not any(q[0]<=x[0] and q[1]<=x[1] and q!=x for q in p)]

def hv2d(points,ref):
    rx,ry=ref
    if not all(math.isfinite(x) and x>0 for x in ref):
        raise AssertionError("Bad shared actual HV reference")
    nd=nondominated(p for p in points if p[0]<rx and p[1]<ry)
    area=0.
    prev=ry
    for x,y in nd:
        if y>=prev:continue
        area+=(rx-x)*(prev-y)
        prev=y
    ans=area/(rx*ry)
    if not math.isfinite(ans) or ans<-TOL or ans>1+TOL:
        raise AssertionError(("Nonsensical normalized real HV",ans))
    return ans

def load(root):
    actual={}
    for folder in root.iterdir():
        if not folder.is_dir():continue
        ident=folder/"block-id.txt"
        if not ident.is_file():continue
        tags=dict(part.split("=",1) for part in ident.read_text(encoding="utf-8").split())
        wf=tags.get("DAG");seed=int(tags.get("seed","-1"));t=tags.get("treatment")
        key=(wf,seed,t)
        if wf not in DAGS or seed not in SEEDS or t not in TREATMENTS or key in actual:
            raise AssertionError(("Unexpected source job",key,folder))
        if tags.get("runtime_priority")!=RUNTIME[t] or int(tags.get("pop","-1"))!=POPS[t] or int(tags.get("K","-1"))!=REPLAY_QUOTAS[t]:
            raise AssertionError(("Policy, population, replay K changed",tags))
        ss=rows(folder/"research_summary.csv")
        rr=rows(folder/"research_replays.csv")
        if len(ss)!=2 or len(rr)!=2*REPLAY_QUOTAS[t]:
            raise AssertionError(("Source incompleteness",key,len(ss),len(rr)))
        if {s["algorithm"] for s in ss}!=set(ARMS):
            raise AssertionError(("Unfair solver sources",key))
        policies={}
        for s in ss:
            arm=s["algorithm"]
            if s["workflow"]!=wf or int(s["seed"])!=seed:
                raise AssertionError(("Wrong original source labels",key,arm))
            if tuple(map(int,(s["population"],s["generations"],s["evaluations"],
                        s["captured_evaluations"],s["replayed"])))!=(
                            POPS[t],100,EVALS[t],EVALS[t],REPLAY_QUOTAS[t]):
                raise AssertionError(("Failed exact-genotype evaluation budget",key,arm,s))
            cand=sorted((x for x in rr if x["algorithm"]==arm),key=lambda r:int(r["candidate_index"]))
            if len(cand)!=REPLAY_QUOTAS[t] or [int(x["candidate_index"]) for x in cand]!=list(range(1,REPLAY_QUOTAS[t]+1)):
                raise AssertionError(("Bad original replay ordering",key,arm))
            if len({x["mapping"] for x in cand})!=len(cand):
                raise AssertionError(("Repeated same-policy VM mapping",key,arm))
            for c in cand:
                if c["workflow"]!=wf or int(c["seed"])!=seed:
                    raise AssertionError(("Wrong real replay metadata",key,arm))
                for field in ("sim_makespan","sim_cost","planned_makespan","planned_cost"):
                    value=float(c[field])
                    if not math.isfinite(value) or value<=0:
                        raise AssertionError(("Bad actual or planned point",key,arm,field,value))
            search=float(s["search_ms"])
            select=float(s["selection_ms"])
            replay=float(s["replay_ms"])
            if not all(math.isfinite(z) and z>=0 for z in (search,select,replay)):
                raise AssertionError(("Invalid compute overhead",key,arm))
            policies[arm]={"points":[(float(x["sim_makespan"]),float(x["sim_cost"])) for x in cand],
                           "mappings":[x["mapping"] for x in cand],
                           "search_ms":search,"selection_ms":select,"replay_ms":replay,
                           "source_eval_count":EVALS[t],"source_replay_count":REPLAY_QUOTAS[t]}
        actual[key]=policies
    expected=set(itertools.product(DAGS,SEEDS,TREATMENTS))
    if set(actual)!=expected:
        raise AssertionError(("Original source incomplete: no partial HV analysis allowed",
                              "missing",expected-set(actual),"unexpected",set(actual)-expected))
    return actual

def write(path,objects):
    if not objects:raise AssertionError(("Empty file",path))
    with path.open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(objects[0]))
        writer.writeheader();writer.writerows(objects)

def analyze(root,out):
    original=load(root)
    out.mkdir(parents=True,exist_ok=True)
    cases=[]
    comparisons=[]
    solver_cross=[]
    for dag,seed in itertools.product(DAGS,SEEDS):
        block={}
        for arm in ARMS:
            for treatment in ("old","ready","priority-portfolio"):
                policies=(treatment,) if treatment!="priority-portfolio" else PORTFOLIO
                raw=[original[(dag,seed,t)][arm] for t in policies]
                total_n=sum(len(x["points"]) for x in raw)
                eval_n=sum(x["source_eval_count"] for x in raw)
                assert total_n==16 and eval_n==3030,("Actual total equal budget",dag,seed,arm,treatment,total_n,eval_n)
                points=[p for x in raw for p in x["points"]]
                # Cross-priority repeated mapping is a different physical
                # compound genotype because the actual runtime policy differs.
                tagged=set()
                for policy,x in zip(policies,raw):
                    for mapping in x["mappings"]:
                        compound=(RUNTIME[policy],mapping)
                        if compound in tagged:raise AssertionError(("Repeated compound genotype",dag,seed,arm,treatment))
                        tagged.add(compound)
                block[(arm,treatment)]=dict(points=points,
                    nd_count=len(nondominated(points)),
                    min_m=min(x for x,y in points),min_c=min(y for x,y in points),
                    evals=eval_n,replays=total_n,search_ms=sum(x["search_ms"] for x in raw),
                    selection_ms=sum(x["selection_ms"] for x in raw),
                    replay_ms=sum(x["replay_ms"] for x in raw),
                    policies="|".join(policies))
        union=[p for x in block.values() for p in x["points"]]
        mx=max(p[0] for p in union);my=max(p[1] for p in union)
        references={f:(mx*f+1e-6,my*f+1e-6) for f in (1.5,3.0)}
        for (arm,treatment),c in block.items():
            cases.append(dict(workflow=dag,seed=seed,solver=arm,treatment=treatment,
                              genotypes_evaluated=c["evals"],actual_sim_replays=c["replays"],
                              policy_islands=c["policies"],true_nondominated_k16=c["nd_count"],
                              min_actual_makespan=c["min_m"],min_actual_cost=c["min_c"],
                              search_ms=c["search_ms"],selection_ms=c["selection_ms"],
                              replay_ms=c["replay_ms"],
                              common_true_hv15=hv2d(c["points"],references[1.5]),
                              common_true_hv30=hv2d(c["points"],references[3.0]),
                              ref_m15=references[1.5][0],ref_c15=references[1.5][1],
                              ref_m30=references[3.0][0],ref_c30=references[3.0][1]))
        for arm in ARMS:
            original_case=next(x for x in cases if (x["workflow"],x["seed"],x["solver"],x["treatment"])==(dag,seed,arm,"old"))
            for treatment in ("ready","priority-portfolio"):
                new=next(x for x in cases if (x["workflow"],x["seed"],x["solver"],x["treatment"])==(dag,seed,arm,treatment))
                comparisons.append(dict(workflow=dag,seed=seed,solver=arm,treatment=treatment,
                    old_hv15=original_case["common_true_hv15"],candidate_hv15=new["common_true_hv15"],
                    delta_hv15=new["common_true_hv15"]-original_case["common_true_hv15"],
                    delta_hv30=new["common_true_hv30"]-original_case["common_true_hv30"],
                    rel_delta_hv15_pct=100*(new["common_true_hv15"]-original_case["common_true_hv15"])/max(1e-12,original_case["common_true_hv15"]),
                    search_time_ratio=new["search_ms"]/max(1e-6,original_case["search_ms"]),
                    old_search_ms=original_case["search_ms"],candidate_search_ms=new["search_ms"]))
        for treatment in ("old","ready","priority-portfolio"):
            fla=next(x for x in cases if (x["workflow"],x["seed"],x["solver"],x["treatment"])==(dag,seed,ARMS[0],treatment))
            nsga=next(x for x in cases if (x["workflow"],x["seed"],x["solver"],x["treatment"])==(dag,seed,ARMS[1],treatment))
            solver_cross.append(dict(workflow=dag,seed=seed,treatment=treatment,
                                     fla_hv=fla["common_true_hv15"],nsga_hv=nsga["common_true_hv15"],
                                     fla_minus_nsga=fla["common_true_hv15"]-nsga["common_true_hv15"]))
    write(out/"actual_shared_reference_six_arms_per_block.csv",cases)
    write(out/"all_16_paired_true_hv_deltas.csv",comparisons)
    write(out/"fla_vs_nsga_under_each_policy.csv",solver_cross)
    report=[
        "# FLA v12 versus costseeded NSGA-II equal-budget ready-policy portfolio true HV",
        "",
        "Original immutable full optimizer+WorkflowSim source: Actions 41683032206; 20 original jobs, 3 treatments per solver, 4 DAG/seed blocks. **NO post-hoc new simulator calls or optimization in this audit.**",
        "Every solver/treatment uses exactly **3030 counted genotype evaluations and K16 actual WorkflowSim calls**: old and ready each one 30×101 arm, priority-portfolio three 10×101 policy islands with K6+K5+K5.",
        "Within each (DAG, seed), 6 arms share ONE actual WorkflowSim normalized 1.5× or 3.0× reference based on all 96 actual M/C points, not incompatible run-local references.",
        "Total original valid 384 true simulator calls, 72,720 counted genotype fitness evaluations. The portfolio internally computes and times independently, and has three independent start populations—compute time parity is not implied by equal genotype budgets.",
        "",
        "## All four paired development blocks: normalized actual K16 HV (1.5× shared reference)",
        "| DAG | Seed | Solver | FIFO insertion old | FIFO ready | Priority portfolio | Δ portfolio−old | Portfolio / old search CPU time |",
        "|---|---:|---|---:|---:|---:|---:|---:|"
    ]
    for dag,seed in itertools.product(DAGS,SEEDS):
        for arm in ARMS:
            found={z["treatment"]:z for z in cases if (z["workflow"],z["seed"],z["solver"])==(dag,seed,arm)}
            report.append(f"| {dag} | {seed} | {'FLA-v12' if arm==ARMS[0] else 'NSGA-II-seeded'} | "
                f"{found['old']['common_true_hv15']:.8f} | {found['ready']['common_true_hv15']:.8f} | "
                f"{found['priority-portfolio']['common_true_hv15']:.8f} | "
                f"{found['priority-portfolio']['common_true_hv15']-found['old']['common_true_hv15']:+.8f} | "
                f"{found['priority-portfolio']['search_ms']/max(1e-6,found['old']['search_ms']):.2f}× |")
    report+=["","## Paired differences (descriptive only; 4 blocks, 2 previously studied DAG families)"]
    for arm in ARMS:
        for treatment in ("ready","priority-portfolio"):
            z=[r for r in comparisons if r["solver"]==arm and r["treatment"]==treatment]
            assert len(z)==4
            diffs=[r["delta_hv15"] for r in z]
            wins=sum(v>TOL for v in diffs)
            ties=sum(abs(v)<=TOL for v in diffs)
            loses=len(z)-wins-ties
            signs30=[r["delta_hv30"] for r in z]
            sign_diff=sum((d>TOL)!=(d2>TOL) and abs(d)>TOL and abs(d2)>TOL
                          for d,d2 in zip(diffs,signs30))
            report.append(f"- {'FLA-v12' if arm==ARMS[0] else 'NSGA-II-seeded'} {treatment}: "
              f"mean Δ real normalized HV(1.5×)={statistics.mean(diffs):+.8f}; "
              f"wins/ties/losses={wins}/{ties}/{loses}; "
              f"mean search-time ratio={statistics.mean(r['search_time_ratio'] for r in z):.2f}×; "
              f"3× reference sign reversals={sign_diff}.")
    report+=["","## Paired solver differences (FLA−NSGA-II)"]
    for treatment in ("old","ready","priority-portfolio"):
        z=[x for x in solver_cross if x["treatment"]==treatment]
        d=[x["fla_minus_nsga"] for x in z]
        report.append(f"- {treatment}: FLA wins/ties/losses="
          f"{sum(x>TOL for x in d)}/{sum(abs(x)<=TOL for x in d)}/{sum(x<-TOL for x in d)}; "
          f"mean normalized real HV margin={statistics.mean(d):+.8f}.")
    report+=["","## Essential limitations / decision",
      "K16 is only the preselected planned-cover simulator replay subset, not the full exact true Pareto set. Different policy islands have different population size and three independent restarts. No inference from four developer-family blocks about a new universal algorithm.",
      "Equal counted genotype evaluations DO NOT equal equal internal schedule-model operations or equal processor time. Sums of measured original per-arm search_ms are reported for each treatment; a speed-matched CPU experiment is a separate future requirement.",
      "This is a shared evaluator/runtime policy portfolio for both FLA and seeded NSGA-II; it does not establish an FLA-specific novel joint policy encoding. A priority gene and its own reproducible operators require independent design and separate unseen DAX-family test. No default promotion.",
      "A result that shows prediction improvements but poor actual HV or costs must be reported as a negative result, not tuned after outcome. `master` remains unchanged."
    ]
    (out/"actual_priority_portfolio_true_hv_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: audit.py ORIGINAL_ALL_COMPLETE_ARTIFACTS OUTDIR")
    analyze(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
