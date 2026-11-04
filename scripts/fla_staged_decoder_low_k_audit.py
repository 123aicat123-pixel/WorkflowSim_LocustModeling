#!/usr/bin/env python3
"""Retrospective, frozen two-stage OLD -> READY selection using 96 actual WorkflowSim points.

Source run 41695356307. No simulation/optimizer/model fitting. All selections
consume predictions only. True objective labels are accessed AFTER selection.
"""
import csv
import hashlib
import itertools
import math
import pathlib
import random
import statistics
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import fla_algorithm_independent_same_mapping_rank_audit as base

DAGS=base.DAGS
SPEEDS=base.SPEEDS
POLICIES=base.POLICIES
N=16
KS=(2,4)
TS=(4,8)
REPLICATES=12
EPS=1e-12

def hv(points,idx,ref):
    rx,ry=ref
    p=sorted(set(points[i] for i in idx))
    prev=ry
    area=0.
    for m,c in p:
        if m<rx and c<prev:
            area+=(rx-m)*(prev-c)
            prev=c
    val=area/(rx*ry)
    if not math.isfinite(val) or val<0 or val>1+1e-9:
        raise AssertionError(("Invalid predicted or true normalized HV",val))
    return val

def best(points,k,ref):
    if len(points)!=N or k<1 or k>N:raise AssertionError("Invalid selection input")
    win=None;score=-1.
    for idx in itertools.combinations(range(N),k):
        val=hv(points,idx,ref)
        if val>score+EPS:
            score=val;win=idx
    if win is None or len(win)!=k:raise AssertionError("Empty selected set")
    return win,score

def seeded_random(dag,speed,k,t,rep):
    token=f"RANDOM_20261104|{dag}|{speed}|{k}|{t}|{rep}"
    seed=int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest(),"big")
    return tuple(sorted(random.Random(seed).sample(range(N),t)))

def write(path,rows):
    if not rows:raise AssertionError("Empty CSV")
    with path.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def execute(root,out):
    cases,sha=base.load(root)  # Validates all six sources and physical genotypes.
    out.mkdir(parents=True,exist_ok=True)
    selections=[]
    comparisons=[]
    controls=[]
    for dag,speed in itertools.product(DAGS,SPEEDS):
        rows=[cases[(dag,speed)][name] for name in POLICIES]
        old=[(float(r["old_planned_makespan"]),float(r["old_planned_cost"])) for r in rows]
        ready=[(float(r["ready_planned_makespan"]),float(r["ready_planned_cost"])) for r in rows]
        actual=[(float(r["actual_makespan"]),float(r["actual_cost"])) for r in rows]
        oldref=(1.5*max(p[0] for p in old)+1e-6,1.5*max(p[1] for p in old)+1e-6)
        truthrefs={f:(f*max(p[0] for p in actual)+1e-6,
                      f*max(p[1] for p in actual)+1e-6) for f in (1.5,3.0)}
        universe={f:hv(actual,range(N),r) for f,r in truthrefs.items()}
        if min(universe.values())<=0:raise AssertionError("Zero true candidate universe HV")

        for k in KS:
            # Neither true simulator labels nor READY values influence OLD shortlist.
            oldchoice,oldpred=best(old,k,oldref)
            readychoice,readypred=best(ready,k,oldref)
            def true_metrics(choice):
                return {f:100*hv(actual,choice,ref)/universe[f] for f,ref in truthrefs.items()}
            baseline=true_metrics(oldchoice)
            high=true_metrics(readychoice)
            def record(strategy,t,rep,choice,screen,estimate,readycalls):
                truth=true_metrics(choice)
                rec=dict(workflow=dag,vm_speed=speed,K=k,T=t,replicate=rep,
                  strategy=strategy,source_sha=sha,old_calls=16,
                  ready_calls=readycalls,
                  predicted_hv=estimate,
                  screened_indices="|".join(str(i+1) for i in screen),
                  selected_indices="|".join(str(i+1) for i in choice),
                  selected_policies="|".join(POLICIES[i] for i in choice),
                  actual_hv_recovery15_pct=truth[1.5],
                  actual_hv_recovery30_pct=truth[3.0],
                  ready_minus_strategy_recovery15_pp=high[1.5]-truth[1.5],
                  ready_minus_strategy_recovery30_pp=high[3.0]-truth[3.0],
                  exact_full_ready_selection=int(choice==readychoice))
                selections.append(rec)
                return rec
            record("old",0,0,oldchoice,(),oldpred,0)
            record("full_ready",16,0,readychoice,tuple(range(N)),readypred,16)

            for t in TS:
                shortlist,_=best(old,t,oldref)
                hybrid=list(old)
                for i in shortlist:hybrid[i]=ready[i]
                staged_choice,staged_pred=best(hybrid,k,oldref)
                staged=record("staged",t,0,staged_choice,shortlist,staged_pred,t)

                random_results=[]
                for rep in range(REPLICATES):
                    screen=seeded_random(dag,speed,k,t,rep)
                    random_hybrid=list(old)
                    for i in screen:random_hybrid[i]=ready[i]
                    choice,pred=best(random_hybrid,k,oldref)
                    random_results.append(record("random",t,rep,choice,screen,pred,t))
                controls.append(dict(workflow=dag,vm_speed=speed,K=k,T=t,
                    staged_real_hv15=staged["actual_hv_recovery15_pct"],
                    full_ready_real_hv15=high[1.5],
                    old_real_hv15=baseline[1.5],
                    random_mean_real_hv15=statistics.mean(x["actual_hv_recovery15_pct"] for x in random_results),
                    random_min_real_hv15=min(x["actual_hv_recovery15_pct"] for x in random_results),
                    random_max_real_hv15=max(x["actual_hv_recovery15_pct"] for x in random_results),
                    staged_minus_random_mean_pp=staged["actual_hv_recovery15_pct"]-statistics.mean(x["actual_hv_recovery15_pct"] for x in random_results),
                    staged_minus_old_pp=staged["actual_hv_recovery15_pct"]-baseline[1.5],
                    staged_minus_full_ready_pp=staged["actual_hv_recovery15_pct"]-high[1.5],
                    same_full_ready_indices=int(staged_choice==readychoice),
                    ready_evaluation_saved=16-t))
                comparisons.append(dict(workflow=dag,vm_speed=speed,K=k,T=t,
                  old_hv15=baseline[1.5],
                  full_ready_hv15=high[1.5],
                  staged_hv15=staged["actual_hv_recovery15_pct"],
                  staged_minus_old_pp=staged["actual_hv_recovery15_pct"]-baseline[1.5],
                  staged_minus_ready_pp=staged["actual_hv_recovery15_pct"]-high[1.5],
                  ready_calls_saved=16-t,
                  staged_selected_same=int(staged_choice==readychoice),
                  stage_screen=staged["screened_indices"],
                  staged_chosen=staged["selected_indices"],
                  ready_chosen="|".join(str(i+1) for i in readychoice)))
    expected=6*len(KS)*(2+len(TS)*(1+REPLICATES))
    if (len(selections),len(comparisons),len(controls))!=(expected,6*len(KS)*len(TS),6*len(KS)*len(TS)):
        raise AssertionError(("Missing source cases",len(selections),len(comparisons),len(controls),expected))
    write(out/"all_model_only_and_random_replay_choices.csv",selections)
    write(out/"all_24_paired_staged_vs_old_ready.csv",comparisons)
    write(out/"all_24_staged_vs_random_screening.csv",controls)
    report=[
        "# Staged OLD shortlist -> READY re-evaluation: frozen 96-source low-K experiment",
        "",
        "Original 96 actual WorkflowSim points from GitHub Actions 41695356307, unchanged SHA "+sha+
        ". All selection decisions use only old and READY planned objectives. All real HV values were read only for scoring. Exactly six known DAX/speed blocks, 16 fixed VM assignments/block, no new simulator or optimizer runs.",
        "Two-step policy: 16 OLD predictions always, exact OLD predicted-HV best-T screening, T READY replacements, exact best-K HV using hybrid estimates. FULL READY has 16 READY estimates (plus no need to compute old; this replay keeps all 16 OLD values in memory for reference parity), STAGED T4/T8 has only T READY estimates. Random-T control uses the same number of READY replacements on deterministic precommitted independent shortlist samples.",
        "",
        "| True replay K | READY screening T | OLD mean real-HV recovery | FULL READY mean | STAGED mean | STAGED − FULL READY (pp) | STAGED − RANDOM mean (pp) | Match full-ready selected K |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k,t in itertools.product(KS,TS):
        z=[x for x in controls if (x["K"],x["T"])==(k,t)]
        report.append(f"| {k} | {t} | "
          f"{statistics.mean(x['old_real_hv15'] for x in z):.7f}% | "
          f"{statistics.mean(x['full_ready_real_hv15'] for x in z):.7f}% | "
          f"{statistics.mean(x['staged_real_hv15'] for x in z):.7f}% | "
          f"{statistics.mean(x['staged_minus_full_ready_pp'] for x in z):+.7f} | "
          f"{statistics.mean(x['staged_minus_random_mean_pp'] for x in z):+.7f} | "
          f"{sum(x['same_full_ready_indices'] for x in z)}/6 |")
    report+=["",
        "## Full paired results (includes losses and cases with zero model benefit)",
        "| DAX | VM speed | K | T | OLD HV | FULL READY HV | STAGED HV | STAGED−READY (pp) | STAGED−OLD (pp) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for z in comparisons:
        report.append(f"| {z['workflow']} | {z['vm_speed']} | {z['K']} | {z['T']} | "
          f"{z['old_hv15']:.7f}% | {z['full_ready_hv15']:.7f}% | {z['staged_hv15']:.7f}% | "
          f"{z['staged_minus_ready_pp']:+.7f} | {z['staged_minus_old_pp']:+.7f} |")
    report+=["",
        "## Critical cost / causality limits",
        "Call counts are MODEL evaluation counts only. STAGED does 16 old + T READY predictions vs FULL READY 16 READY predictions. It is WRONG to claim a wall-clock speedup from the T/16 figure without directly timing Java decoders on equivalent genotypes, including old scheduling overhead.",
        "The OLD shortlist may reject high-value future READY candidates; the chosen expensive score remains hybrid OLD+READY, so model scales and associated selection bias can differ even under one normalized reference.",
        "The 16 source assignments include unrealistic extreme mappings, and there are only 3 historically researched DAX families with 2 correlated VM speeds. This is a retrospective finite-genotype falsification study; not an FLA or NSGA-II improvement or independent holdout.",
        "No data-based adjustment of T, K or random seeding after seeing these outcomes. No change to master, old FLA, seeded NSGA-II or runtime FIFO defaults."]
    (out/"staged_decoder_low_k_true_HV_report.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    print("\n".join(report))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: script.py IMMUTABLE_96_SOURCE_ARTIFACTS OUTPUT_DIR")
    execute(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]))
